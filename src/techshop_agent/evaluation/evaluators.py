"""Evaluadores deterministas y agregadores run-level.

Cada evaluador sigue la firma que espera Langfuse run_experiment():
  def evaluator(*, input, output, expected_output, metadata, **kwargs) -> Evaluation

Los evaluadores item-level reciben la respuesta del agente y devuelven un
Evaluation con score 0.0-1.0. Los agregadores run-level reciben todos los
resultados del experimento y calculan métricas globales (medias).
"""

from __future__ import annotations

from langfuse import Evaluation


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  CONFIGURACIÓN TUNEABLE — Modifica estas listas para mejorar detección    ║
# ║                                                                           ║
# ║  Estas constantes separan los DATOS de la LÓGICA.                         ║
# ║  Los evaluadores de abajo las consumen; tú solo necesitas editar aquí.    ║
# ║                                                                           ║
# ║  EJERCICIO: Ejecuta la evaluación, revisa los falsos positivos/           ║
# ║  negativos en los resultados, y ajusta estas listas iterativamente.       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


# -- Scope adherence (F3) --------------------------------------------------
# Frases que indican que el agente RECHAZÓ una consulta fuera de ámbito.
# Si el agente usa una frase diferente para rechazar, añádela aquí.
#
# CUIDADO: No añadir palabras genéricas como "techshop" que aparecen en
# respuestas normales — solo frases que impliquen RECHAZO explícito.
OOS_REJECTION_PHRASES: list[str] = [
    "no puedo",
    "solo puedo",
    "fuera de",
    "no estoy",
    "no tengo información",
    "no está en mi",
    "no dispongo",
    "solo estadísticas",
    "mi ámbito",
    # >>> AÑADE más frases de rechazo que descubras en los resultados <<<
]

# Frases que indican rechazo INDEBIDO de una consulta legítima.
# Si el agente rechaza preguntas sobre jugadores de fútbol, añade la frase aquí.
IN_SCOPE_FALSE_REJECTION_PHRASES: list[str] = [
    "no puedo ayudar",
    "solo puedo ayudarte con consultas",
    "fuera de mi ámbito",
    # >>> AÑADE más si el agente rechaza queries legítimas de jugadores <<<
]


# -- Tool usage (F4) -------------------------------------------------------
# Indicadores de que search_talent fue llamado y devolvió datos reales.
# Si el agente muestra datos de jugadores con otro formato, añade el indicador.
PLAYER_EVIDENCE_KEYWORDS: list[str] = [
    "goles", "asistencias", "minutos", "partidos",
    "temporada", "liga", "equipo", "xg", "xa", "npxg",
    # >>> AÑADE más indicadores de datos de jugadores si el formato cambia <<<
]

# Frase genérica que indica que el tool se llamó pero no encontró resultados.
TOOL_NO_RESULTS_PHRASES: list[str] = [
    "no encontr",
    "no he encontrado",
    # >>> AÑADE más variantes de "no encontré nada" <<<
]


# -- Response quality -------------------------------------------------------
# Umbrales de longitud para la calidad de respuesta.
MIN_RESPONSE_LENGTH: int = 10       # chars — por debajo → score 0.0
MAX_RESPONSE_WORDS: int = 500       # words — por encima → score 0.5


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  LÓGICA DE EVALUADORES — Lee, entiende, pero no necesitas tocar aquí.   ║
# ║  La lógica consume las constantes de arriba.                            ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


def scope_adherence_evaluator(
    *, input: str, output: str, expected_output: str | None, metadata: dict | None, **kwargs
) -> Evaluation:
    """Detecta el fallo F3 (scope creep): ¿el agente respeta sus límites?

    Lógica:
    - Si metadata.category == "out_of_scope" → el agente DEBE rechazar.
      Busca frases de rechazo en OOS_REJECTION_PHRASES. Si las
      encuentra → 1.0, si no → 0.0 (el agente contestó algo que no debía).
    - Si la categoría es otra (product, faq) → el agente NO debe rechazar.
      Si rechaza una consulta legítima → 0.0.

    Es determinista: solo busca palabras clave, no llama a ningún LLM.
    """
    meta = metadata or {}
    category = meta.get("category", "")
    output_lower = output.lower() if output else ""

    if category == "out_of_scope":
        is_rejected = any(phrase in output_lower for phrase in OOS_REJECTION_PHRASES)
        return Evaluation(
            name="scope_adherence",
            value=1.0 if is_rejected else 0.0,
            comment="Correctly rejected" if is_rejected else "Failed to reject out-of-scope query",
        )
    else:
        is_rejected = any(phrase in output_lower for phrase in IN_SCOPE_FALSE_REJECTION_PHRASES)
        return Evaluation(
            name="scope_adherence",
            value=0.0 if is_rejected else 1.0,
            comment="Incorrectly rejected in-scope query" if is_rejected else "Correctly handled",
        )


def hallucination_evaluator(
    *, input: str, output: str, expected_output: str | None, metadata: dict | None, **kwargs
) -> Evaluation:
    """Detecta los fallos F1 (alucinación) y F2 (extrapolación FAQ).

    Usa dos listas del metadata de cada caso del dataset:
    - should_not_contain: palabras que NO deben aparecer en la respuesta.
      Ejemplo: ["iPhone", "Apple"] → si el agente menciona iPhone, está
      inventando un producto que no existe en el catálogo (F1).
    - should_contain: palabras que SÍ deben aparecer.
      Ejemplo: ["30"] → si el agente habla de la política de devolución
      pero no menciona "30" días, probablemente inventó otra cifra (F2).

    NOTA: Las listas should_not_contain / should_contain se definen POR CASO
    en dataset.py, no aquí. Para mejorar la detección de F1/F2, edita el
    metadata de cada caso en EVAL_DATASET.

    Es determinista: solo busca palabras clave, no llama a ningún LLM.
    """
    meta = metadata or {}
    should_not_contain = meta.get("should_not_contain", [])
    should_contain = meta.get("should_contain", [])
    output_lower = output.lower() if output else ""

    # Check for forbidden content (hallucinated products, prices, etc.)
    violations = [word for word in should_not_contain if word.lower() in output_lower]
    if violations:
        return Evaluation(
            name="hallucination_check",
            value=0.0,
            comment=f"Hallucination detected: contains {violations}",
        )

    # Check for required content (e.g., "30" for 30-day policy)
    missing = [word for word in should_contain if word.lower() not in output_lower]
    if missing:
        return Evaluation(
            name="hallucination_check",
            value=0.0,
            comment=f"Missing required facts: {missing}",
        )

    return Evaluation(
        name="hallucination_check",
        value=1.0,
        comment="No hallucination detected",
    )


def response_quality_evaluator(
    *, input: str, output: str, expected_output: str | None, metadata: dict | None, **kwargs
) -> Evaluation:
    """Verificación básica de calidad: ¿la respuesta es razonable?

    Comprueba dos cosas simples:
    - Que la respuesta no esté vacía ni sea demasiado corta (< MIN_RESPONSE_LENGTH).
    - Que no sea excesivamente larga (> MAX_RESPONSE_WORDS → 0.5).

    No detecta ningún fallo F1–F4 en particular; es una red de seguridad
    para respuestas degeneradas (vacías, truncadas o incontrolablemente largas).
    """
    if not output or len(output.strip()) < MIN_RESPONSE_LENGTH:
        return Evaluation(
            name="response_quality",
            value=0.0,
            comment="Response is empty or too short",
        )

    word_count = len(output.split())
    if word_count > MAX_RESPONSE_WORDS:
        return Evaluation(
            name="response_quality",
            value=0.5,
            comment=f"Response too long: {word_count} words",
        )

    return Evaluation(
        name="response_quality",
        value=1.0,
        comment=f"Good quality: {word_count} words",
    )


def tool_usage_evaluator(
    *, input: str, output: str, expected_output: str | None, metadata: dict | None, **kwargs
) -> Evaluation:
    """Detecta el fallo F4 (omisión de herramienta): ¿el agente usó su tool?

    Cada caso del dataset puede indicar metadata.expected_tool (por ejemplo,
    "search_talent"). Si el agente debía llamar a una herramienta pero respondió
    de memoria, la respuesta será genérica y no contendrá datos concretos
    (goles, asistencias, minutos...).

    Heurística: busca indicadores en PLAYER_EVIDENCE_KEYWORDS.

    Limitación: es una heurística basada en la respuesta, no inspecciona
    los spans de la traza. En producción se verificaría directamente
    en los spans de Langfuse.
    """
    meta = metadata or {}
    expected_tool = meta.get("expected_tool")
    output_lower = output.lower() if output else ""

    if expected_tool is None:
        return Evaluation(name="tool_usage", value=1.0, comment="No tool expected")

    # Check for "no results" phrases (valid for search_talent)
    no_results = any(phrase in output_lower for phrase in TOOL_NO_RESULTS_PHRASES)

    if expected_tool == "search_talent":
        has_evidence = any(kw in output_lower for kw in PLAYER_EVIDENCE_KEYWORDS) or no_results
        return Evaluation(
            name="tool_usage",
            value=1.0 if has_evidence else 0.0,
            comment="Player data found in response" if has_evidence else "No evidence of search_talent usage",
        )

    return Evaluation(name="tool_usage", value=1.0, comment=f"Unknown tool: {expected_tool}")




# ---------------------------------------------------------------------------
# Run-level evaluators (aggregators)
# ---------------------------------------------------------------------------

# Run-level evaluators
# ---------------------------------------------------------------------------


def average_score_evaluator(*, item_results, **kwargs) -> Evaluation:
    """Agregador run-level: media de scope_adherence sobre todos los casos."""
    scores = [
        ev.value
        for result in item_results
        for ev in result.evaluations
        if ev.name == "scope_adherence" and ev.value is not None
    ]
    if not scores:
        return Evaluation(name="avg_scope_adherence", value=None)
    avg = sum(scores) / len(scores)
    return Evaluation(
        name="avg_scope_adherence",
        value=round(avg, 3),
        comment=f"Average over {len(scores)} items: {avg:.1%}",
    )


def average_hallucination_evaluator(*, item_results, **kwargs) -> Evaluation:
    """Agregador run-level: media de hallucination_check sobre todos los casos."""
    scores = [
        ev.value
        for result in item_results
        for ev in result.evaluations
        if ev.name == "hallucination_check" and ev.value is not None
    ]
    if not scores:
        return Evaluation(name="avg_hallucination", value=None)
    avg = sum(scores) / len(scores)
    return Evaluation(
        name="avg_hallucination",
        value=round(avg, 3),
        comment=f"Average over {len(scores)} items: {avg:.1%}",
    )


def average_faithfulness_evaluator(*, item_results, **kwargs) -> Evaluation:
    """Agregador run-level: media de faithfulness (LLM-as-Judge) sobre todos los casos."""
    scores = [
        ev.value
        for result in item_results
        for ev in result.evaluations
        if ev.name == "faithfulness" and ev.value is not None
    ]
    if not scores:
        return Evaluation(name="avg_faithfulness", value=None)
    avg = sum(scores) / len(scores)
    return Evaluation(
        name="avg_faithfulness",
        value=round(avg, 3),
        comment=f"LLM-as-judge average over {len(scores)} items: {avg:.1%}",
    )


def average_tool_usage_evaluator(*, item_results, **kwargs) -> Evaluation:
    """Agregador run-level: media de tool_usage sobre todos los casos."""
    scores = [
        ev.value
        for result in item_results
        for ev in result.evaluations
        if ev.name == "tool_usage" and ev.value is not None
    ]
    if not scores:
        return Evaluation(name="avg_tool_usage", value=None)
    avg = sum(scores) / len(scores)
    return Evaluation(
        name="avg_tool_usage",
        value=round(avg, 3),
        comment=f"Average over {len(scores)} items: {avg:.1%}",
    )


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

