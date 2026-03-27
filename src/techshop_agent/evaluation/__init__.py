"""Evaluation package for TechShop Agent.

Re-exports all public names so existing imports continue to work:
  from techshop_agent.evaluation import EVAL_DATASET, run_evaluation, ...

Archivos del paquete:
  dataset.py    — Casos de evaluación (TUNEABLE: añade/edita casos)
  evaluators.py — Evaluadores deterministas (TUNEABLE: listas de keywords arriba)
  judge.py      — LLM-as-Judge faithfulness (TUNEABLE: rúbrica de scoring)
  runner.py     — Orquestador que conecta todo con Langfuse run_experiment()
"""

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
from .runner import EvalResult, run_evaluation

__all__ = [
    "EVAL_DATASET",
    "EvalResult",
    "average_faithfulness_evaluator",
    "average_hallucination_evaluator",
    "average_score_evaluator",
    "average_tool_usage_evaluator",
    "faithfulness_evaluator",
    "hallucination_evaluator",
    "response_quality_evaluator",
    "run_evaluation",
    "scope_adherence_evaluator",
    "tool_usage_evaluator",
]
