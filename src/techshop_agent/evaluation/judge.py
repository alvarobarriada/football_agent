"""LLM-as-Judge evaluator for semantic faithfulness scoring.

Uses a separate LLM call (Bedrock Claude) to judge whether the agent
response is grounded in real catalog/FAQ data. Catches novel fabrication
that keyword-based evaluators miss.

Trade-offs:
  + Catches semantic errors that keywords miss
  + Scales to new failure modes without updating blocklists
  - Non-deterministic (same input may produce different scores)
  - Adds latency and cost (one extra LLM call per item)

╔═══════════════════════════════════════════════════════════════════════════╗
║  CÓMO MEJORAR ESTE EVALUADOR                                              ║
║                                                                           ║
║  1. RÚBRICA: Modifica _JUDGE_PROMPT abajo. Los niveles de scoring         ║
║     (1.0, 0.7, 0.5, 0.3, 0.0) determinan la granularidad.                 ║
║     Si ves muchos 0.3 que deberían ser 0.5, refina las descripciones.     ║
║                                                                           ║
║  2. MODELO: Cambia JUDGE_MODEL_ID en .env para usar un modelo más         ║
║     potente o más económico. Haiku es rápido y barato; Sonnet es más      ║
║     preciso. El trade-off es costo vs calidad del juicio.                 ║
║                                                                           ║
║  3. GROUND TRUTH: El judge recibe catálogo y FAQs completos.              ║
║     Si cambias data/catalog.json o data/faqs.json, el judge se adapta.    ║
╚═══════════════════════════════════════════════════════════════════════════╝

Reference: https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge
"""

from __future__ import annotations

import json
import logging

from langfuse import Evaluation

logger = logging.getLogger(__name__)

# LLM-as-Judge evaluator
# ---------------------------------------------------------------------------
# Why an LLM judge? Deterministic evaluators (keyword matching) can only
# catch KNOWN hallucinations we've pre-listed. An LLM judge can detect
# **novel** fabrication — e.g., the agent inventing a plausible but wrong
# return policy, or extrapolating beyond FAQ data (F2).
#
# Trade-offs:
#   ✅ Catches semantic errors that keywords miss
#   ✅ Scales to new failure modes without updating blocklists
#   ❌ Non-deterministic — same input may produce different scores
#   ❌ Adds latency and cost (one extra LLM call per item)
#   ❌ Judge model can itself hallucinate
#
# Best practice: Use LLM-as-judge for SUBJECTIVE criteria (faithfulness,
# helpfulness). Use deterministic evaluators for OBJECTIVE criteria
# (scope rejection, keyword presence).
#
# Reference: https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge

# ── RÚBRICA DEL JUDGE ─────────────────────────────────────────────────────
# Este prompt define CÓMO evalúa el LLM judge. Los niveles de scoring (1.0,
# 0.7, 0.5, 0.3, 0.0) son el parámetro clave que puedes ajustar.
# Si el judge es demasiado estricto o permisivo, edita las descripciones.
#
# EJERCICIO: Ejecuta la evaluación, revisa los scores de faithfulness,
# y ajusta la rúbrica para que coincida con tu criterio humano.
_JUDGE_PROMPT = """\
You are an evaluation judge for a customer service chatbot called "TechShop Agent".
The agent MUST ONLY answer questions about TechShop products and policies.
The agent MUST NOT invent information beyond what its tools (catalog, FAQ) return.

## Ground truth — TechShop catalog
These are the ONLY products TechShop sells:
{catalog_summary}

## Ground truth — TechShop FAQ topics
These are the ONLY policies TechShop has:
{faq_summary}

## Your task
Given the user query, the agent's response, and the expected behavior,
score the response on **faithfulness** (did the agent stick to facts?) on a
scale of 0.0 to 1.0.

## Scoring rubric
- **1.0** — Fully grounded: only uses catalog/FAQ data, or correctly declines
  when information is unavailable. Minor rephrasing is fine.
- **0.7** — Mostly grounded but adds small inferences from real data (e.g.,
  suggesting a real product fits a use case based on its specs). All mentioned
  products, prices, and policies are real.
- **0.5** — Mixed: core facts are real but the response adds subjective claims
  not supported by the data (e.g., "best for gaming" when specs don't say that),
  or fails to find a product that exists in the catalog.
- **0.3** — Contains plausible-sounding but unverifiable claims: invented policy
  exceptions, made-up delivery times, or recommends products not in the catalog.
- **0.0** — Clear fabrication: invents products, prices, policies, or answers
  questions completely outside TechShop scope.

## Output format
Respond with ONLY a JSON object (no markdown, no backticks):
{{"score": <float>, "reason": "<one sentence explanation>"}}

## Evaluation input
User query: {input}
Expected behavior: {expected_output}
Agent response: {output}
"""


def _call_judge(prompt: str) -> dict:
    """Call Bedrock to get the LLM judge verdict.

    Uses boto3 directly (not the agent) to keep the judge independent
    from the system under test.
    """
    import os

    import boto3

    client = boto3.client(
        "bedrock-runtime",
        region_name=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "eu-west-1")),
    )
    model_id = os.getenv(
        "JUDGE_MODEL_ID",
        "eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    )

    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 150, "temperature": 0.0},
    )
    text = response["output"]["message"]["content"][0]["text"]

    # Parse JSON — handle common LLM formatting quirks
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def _build_ground_truth_summaries() -> tuple[str, str]:
    """Build compact summaries of catalog and FAQs for the judge prompt.

    Loaded once and cached. Provides the judge with the complete source of
    truth so it can detect fabrication vs real data.
    """
    from techshop_agent.config import load_catalog, load_faqs

    catalog = load_catalog()
    catalog_lines = [
        f"- {p['nombre']}: {p['precio']}€, category={p['categoria']}"
        for p in catalog
    ]
    catalog_summary = "\n".join(catalog_lines)

    faqs = load_faqs()
    faq_lines = [
        f"- Q: {f['pregunta']} → A: {f['respuesta']}"
        for f in faqs
    ]
    faq_summary = "\n".join(faq_lines)

    return catalog_summary, faq_summary


# Module-level cache for ground truth (loaded once per process)
_catalog_summary: str | None = None
_faq_summary: str | None = None


def _get_ground_truth() -> tuple[str, str]:
    global _catalog_summary, _faq_summary  # noqa: PLW0603
    if _catalog_summary is None:
        _catalog_summary, _faq_summary = _build_ground_truth_summaries()
    return _catalog_summary, _faq_summary


def faithfulness_evaluator(
    *, input: str, output: str, expected_output: str | None, metadata: dict | None, **kwargs
) -> Evaluation:
    """LLM-as-Judge: score response faithfulness to ground truth.

    Uses a separate LLM call to judge whether the agent's response is
    grounded in real data or contains fabrication. This catches F1
    (hallucination) and F2 (extrapolation) failures that keyword-based
    evaluators miss.

    The judge receives the full catalog and FAQ data as ground truth,
    following the RAGAS faithfulness evaluation pattern. This allows
    the judge to verify whether specific products, prices, and policies
    mentioned in the response actually exist.

    Returns 0.0–1.0 faithfulness score with an explanation.
    Falls back to None (skip) if the judge call fails, so a network
    error doesn't break the entire evaluation run.
    """
    catalog_summary, faq_summary = _get_ground_truth()

    prompt = _JUDGE_PROMPT.format(
        input=input,
        output=output or "(empty)",
        expected_output=expected_output or "Respond accurately using only catalog/FAQ data",
        catalog_summary=catalog_summary,
        faq_summary=faq_summary,
    )

    try:
        verdict = _call_judge(prompt)
        score = float(verdict.get("score", 0.5))
        reason = str(verdict.get("reason", "No reason provided"))
        # Clamp to [0, 1]
        score = max(0.0, min(1.0, score))
    except Exception as exc:
        logger.warning("LLM judge failed, skipping faithfulness score: %s", exc)
        return Evaluation(
            name="faithfulness",
            value=None,
            comment=f"Judge error: {exc}",
        )

    return Evaluation(
        name="faithfulness",
        value=round(score, 2),
        comment=reason,
    )


# ---------------------------------------------------------------------------
