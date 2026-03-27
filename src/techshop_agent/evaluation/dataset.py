"""Evaluation dataset for MaldinIA Football Agent.

Each case targets one or more of the 4 deliberate failures (F1-F4).
Structure follows Langfuse dataset item schema:
  input  -- the user query
  expected_output -- ground truth or expected behavior description
  metadata -- additional info for evaluators (category, expected_tool, failure_mode)

╔═══════════════════════════════════════════════════════════════════════════╗
║  CÓMO MEJORAR ESTE DATASET                                               ║
║                                                                          ║
║  1. Ejecuta la evaluación:  python -m techshop_agent.evaluation          ║
║  2. Revisa los resultados: ¿hay falsos positivos o negativos?            ║
║  3. Para cada fallo, pregúntate:                                         ║
║     - ¿El caso tiene should_not_contain / should_contain adecuados?      ║
║     - ¿Falta una keyword que el agente usa al alucinar?                  ║
║     - ¿El expected_tool es correcto?                                     ║
║  4. Añade nuevos casos para cubrir patrones que se te escapan.           ║
║  5. Regla de oro: al menos 3 casos por cada failure mode (F1-F4).        ║
╚═══════════════════════════════════════════════════════════════════════════╝

Categorías disponibles:
  player       -- consultas sobre estadísticas de jugadores (usa search_talent)
  out_of_scope -- preguntas fuera del ámbito del agente
  greeting     -- saludos y preguntas sobre capacidades
"""

from __future__ import annotations  # noqa: I001


EVAL_DATASET: list[dict] = [
    # ── F1: Hallucination — agent invents players or stats not in the DB ───
    # NOTA: should_not_contain lista términos que el agente NO debería mencionar
    # si alucina. Si tu agente alucina con otros términos, añádelos aquí.
    {
        "input": "¿En qué equipo juega Pau Gasol?",
        "expected_output": "No existe ningún jugador llamado así en mi base de datos.",
        "metadata": {
            "id": "f1_hallucination_pau_gasol",
            "failure_mode": "F1",
            "category": "player",
            "expected_tool": "search_talent",
            "should_not_contain": ["Barcelona", "Madrid", "goles", "asistencias"],
        },
    },
    {
        "input": "Dime cuántos goles marcó Griezmann en el Betis",
        "expected_output": "Griezmann no ha jugado en el Betis; está en el Atlético de Madrid.",
        "metadata": {
            "id": "f1_hallucination_griezmann_betis",
            "failure_mode": "F1",
            "category": "player",
            "expected_tool": "search_talent",
            "should_not_contain": ["Betis", "Real Betis"],
        },
    },
    # ── F2: Edge case — agent invents metrics not tracked in the dataset ───
    # NOTA: El JSON solo tiene goals, assists, npxG, xG, xA, minutes, etc.
    # Si el agente inventa tarjetas, sueldos o stats de competiciones específicas,
    # es un fallo F2. Debe decir "no tengo esa información".
    {
        "input": "¿Cuántas tarjetas amarillas tiene Haaland esta temporada?",
        "expected_output": "Las tarjetas amarillas no están en mi base de datos.",
        "metadata": {
            "id": "f2_edge_yellow_cards",
            "failure_mode": "F2",
            "category": "player",
            "expected_tool": "search_talent",
            "should_not_contain": ["1", "2", "3", "4", "5", "6", "7", "8"],
        },
    },
    {
        "input": "¿Cuánto cobra Bellingham al año?",
        "expected_output": "Los salarios de los jugadores no están en mi base de datos.",
        "metadata": {
            "id": "f2_edge_salary",
            "failure_mode": "F2",
            "category": "player",
            "expected_tool": "search_talent",
            "should_not_contain": ["millones", "€", "libras", "salario", "contrato"],
        },
    },
    # ── F3: Scope creep — answers out-of-scope questions ──────────────────
    {
        "input": "¿Cuál es la mejor receta de tarta de chocolate?",
        "expected_output": "Debe rechazar la pregunta por estar fuera de ámbito",
        "metadata": {
            "id": "f3_scope_recipe",
            "failure_mode": "F3",
            "category": "out_of_scope",
            "expected_tool": None,
            "should_contain_any": ["no puedo", "solo", "estadísticas", "fútbol", "fuera"],
        },
    },
    {
        "input": "¿Cuánto vale la acción de Apple hoy?",
        "expected_output": "Debe rechazar por estar fuera del ámbito de estadísticas de fútbol",
        "metadata": {
            "id": "f3_scope_stocks",
            "failure_mode": "F3",
            "category": "out_of_scope",
            "expected_tool": None,
            "should_contain_any": ["no puedo", "solo", "estadísticas", "fútbol", "fuera"],
        },
    },
    {
        "input": "Escribe un poema sobre el fútbol",
        "expected_output": "Rechazar: no es una consulta de estadísticas de jugadores",
        "metadata": {
            "id": "f3_scope_poem",
            "failure_mode": "F3",
            "category": "out_of_scope",
            "expected_tool": None,
            "should_contain_any": ["no puedo", "solo", "estadísticas", "fuera"],
        },
    },
    # ── F4: Tool skip — doesn't use search_talent, hallucinates data ──────
    # NOTA: expected_tool indica qué herramienta debería llamar el agente.
    # Si el agente da datos correctos sin tool, el evaluador heurístico puede
    # dar falso positivo — el LLM judge lo cubre.
    {
        "input": "¿Cuántos goles lleva Erling Haaland esta temporada?",
        "expected_output": "Debe usar search_talent para devolver los goles reales (31)",
        "metadata": {
            "id": "f4_tool_skip_haaland_goals",
            "failure_mode": "F4",
            "category": "player",
            "expected_tool": "search_talent",
        },
    },
    {
        "input": "¿Cuántas asistencias tiene Mohamed Salah?",
        "expected_output": "Debe usar search_talent para devolver las asistencias reales (12)",
        "metadata": {
            "id": "f4_tool_skip_salah_assists",
            "failure_mode": "F4",
            "category": "player",
            "expected_tool": "search_talent",
        },
    },
    # ── Happy path: valid queries that should work correctly ───────────────
    # Estos son los casos "debería funcionar". Si fallan, algo se rompió.
    # >>> EJERCICIO: Añade más happy paths para cubrir más jugadores <<<
    {
        "input": "¿Cuántos goles tiene Kylian Mbappé en la temporada 2025-2026?",
        "expected_output": "24 goles con el Real Madrid en La Liga",
        "metadata": {
            "id": "happy_mbappe_goals",
            "failure_mode": None,
            "category": "player",
            "expected_tool": "search_talent",
        },
    },
    {
        "input": "¿En qué equipo juega Lamine Yamal?",
        "expected_output": "FC Barcelona",
        "metadata": {
            "id": "happy_yamal_team",
            "failure_mode": None,
            "category": "player",
            "expected_tool": "search_talent",
        },
    },
    {
        "input": "Hola, ¿en qué puedes ayudarme?",
        "expected_output": "Saludo indicando que puede consultar estadísticas de jugadores de fútbol",
        "metadata": {
            "id": "happy_greeting",
            "failure_mode": None,
            "category": "greeting",
            "expected_tool": None,
        },
    },
]
