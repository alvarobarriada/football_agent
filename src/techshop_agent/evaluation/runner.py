"""Evaluation runner -- orchestrates dataset, evaluators, and reporting.

Provides:
  - EvalResult: container for evaluation results with quality gate logic
  - run_evaluation: full evaluation suite runner using Langfuse experiments
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from langfuse import Evaluation, get_client, observe

from .dataset import EVAL_DATASET
from .evaluators import (
    average_faithfulness_evaluator,
    average_hallucination_evaluator,
    average_score_evaluator,
    average_tool_usage_evaluator,
    hallucination_evaluator,
    response_quality_evaluator,
    scope_adherence_evaluator,
    tool_usage_evaluator,
)
from .judge import faithfulness_evaluator


@dataclass
class EvalResult:
    """Container for evaluation results with quality gate logic."""

    label: str
    total_cases: int = 0
    passed_cases: int = 0
    avg_scope_adherence: float | None = None
    avg_hallucination: float | None = None
    avg_response_quality: float | None = None
    avg_tool_usage: float | None = None
    avg_faithfulness: float | None = None
    details: list[dict] = field(default_factory=list)
    duration_seconds: float = 0.0

    def passes_threshold(self, threshold: float = 0.7) -> bool:
        """Check if all average scores meet the minimum threshold."""
        scores = [
            s
            for s in [
                self.avg_scope_adherence,
                self.avg_hallucination,
                self.avg_response_quality,
                self.avg_tool_usage,
                self.avg_faithfulness,
            ]
            if s is not None
        ]
        return all(s >= threshold for s in scores) if scores else False

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "avg_scope_adherence": self.avg_scope_adherence,
            "avg_hallucination": self.avg_hallucination,
            "avg_response_quality": self.avg_response_quality,
            "avg_tool_usage": self.avg_tool_usage,
            "avg_faithfulness": self.avg_faithfulness,
            "passes_threshold": self.passes_threshold(),
            "duration_seconds": round(self.duration_seconds, 2),
        }

    def summary(self) -> str:
        lines = [
            f"{'=' * 60}",
            f"  Evaluation Results — label: {self.label}",
            f"{'=' * 60}",
            f"  Total cases:          {self.total_cases}",
            f"  Duration:             {self.duration_seconds:.1f}s",
            f"{'─' * 60}",
            f"  DETERMINISTIC EVALUATORS",
            f"  Scope adherence:      {self._fmt(self.avg_scope_adherence)}",
            f"  Hallucination check:  {self._fmt(self.avg_hallucination)}",
            f"  Response quality:     {self._fmt(self.avg_response_quality)}",
            f"  Tool usage:           {self._fmt(self.avg_tool_usage)}",
            f"{'─' * 60}",
            f"  LLM-AS-JUDGE",
            f"  Faithfulness:         {self._fmt(self.avg_faithfulness)}",
            f"{'─' * 60}",
            f"  Quality Gate:         {'✅ PASS' if self.passes_threshold() else '❌ FAIL'}",
            f"{'=' * 60}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _fmt(val: float | None) -> str:
        return f"{val:.1%}" if val is not None else "N/A"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


@observe(name="prompt_evaluation")
def run_evaluation(
    *,
    label: str = "staging",
    threshold: float = 0.7,
    dataset: list[dict] | None = None,
) -> EvalResult:
    """Run the full evaluation suite against a prompt label.

    This function:
    1. Creates or reuses the TechShop agent with the specified prompt label
    2. Runs every case in the evaluation dataset
    3. Applies all evaluators to each response
    4. Computes aggregate scores
    5. Returns an EvalResult with quality gate verdict

    Args:
        label: Langfuse prompt label to evaluate ("staging", "production", etc.)
        threshold: Minimum score to pass the quality gate (0.0–1.0)
        dataset: Override the default EVAL_DATASET (useful for testing)

    Returns:
        EvalResult with scores and quality gate verdict.
    """
    from techshop_agent.solution.prompt_provider import get_system_prompt

    eval_data = dataset or EVAL_DATASET
    start = time.monotonic()

    # Get the system prompt for this label
    system_prompt = get_system_prompt(label, cache_ttl_seconds=0)

    # Create agent with this prompt
    from techshop_agent.agent import create_agent

    agent = create_agent(system_prompt=system_prompt)

    print(f"▶ Running {len(eval_data)} dataset items against label '{label}'…\n")

    # Define task function for Langfuse experiment runner
    task_counter = {"n": 0}

    def agent_task(*, item, **kwargs):
        task_counter["n"] += 1
        query = item["input"] if isinstance(item, dict) else item.input
        meta = item.get("metadata", {}) if isinstance(item, dict) else (item.metadata or {})
        item_id = meta.get("id", f"item_{task_counter['n']}")
        failure_mode = meta.get("failure_mode", "?")

        print(f"  [{task_counter['n']}/{len(eval_data)}] {item_id} ({failure_mode})")
        print(f"    Input:  {query[:90]}{'…' if len(query) > 90 else ''}")

        output = str(agent(query))

        print(f"    Output: {output[:120]}{'…' if len(output) > 120 else ''}")
        print()
        return output

    # Run with Langfuse experiment runner
    lf_client = get_client()

    result = lf_client.run_experiment(
        name=f"techshop-eval-{label}",
        description=f"Evaluation of prompt label '{label}'",
        data=eval_data,
        task=agent_task,
        evaluators=[
            # Deterministic evaluators — fast, reproducible, keyword-based
            scope_adherence_evaluator,
            hallucination_evaluator,
            response_quality_evaluator,
            tool_usage_evaluator,
            # LLM-as-Judge — semantic, catches novel fabrication (F1, F2)
            faithfulness_evaluator,
        ],
        run_evaluators=[
            average_score_evaluator,
            average_hallucination_evaluator,
            average_tool_usage_evaluator,
            average_faithfulness_evaluator,
        ],
        metadata={"prompt_label": label, "threshold": threshold},
    )

    duration = time.monotonic() - start

    # Parse results
    eval_result = EvalResult(
        label=label,
        total_cases=len(eval_data),
        duration_seconds=duration,
    )

    # Extract run-level scores
    for ev in result.run_evaluations:
        if ev.name == "avg_scope_adherence":
            eval_result.avg_scope_adherence = ev.value
        elif ev.name == "avg_hallucination":
            eval_result.avg_hallucination = ev.value
        elif ev.name == "avg_faithfulness":
            eval_result.avg_faithfulness = ev.value
        elif ev.name == "avg_tool_usage":
            eval_result.avg_tool_usage = ev.value

    # Calculate average response quality from item results
    quality_scores = [
        ev.value
        for item_result in result.item_results
        for ev in item_result.evaluations
        if ev.name == "response_quality" and ev.value is not None
    ]
    if quality_scores:
        eval_result.avg_response_quality = round(sum(quality_scores) / len(quality_scores), 3)

    # Count passed cases (all evaluators returned 1.0)
    for item_result in result.item_results:
        all_passed = all(ev.value == 1.0 for ev in item_result.evaluations if ev.value is not None)
        if all_passed:
            eval_result.passed_cases += 1

    lf_client.flush()
    return eval_result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

