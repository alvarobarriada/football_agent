"""Configuración personalizable de la interfaz Streamlit.

"""


# ---------------------------------------------------------------------------
# Metadatos de tracing (aparecen en Langfuse)
# ---------------------------------------------------------------------------
TRACING_USER_ID = "streamlit-student"
TRACING_SOURCE = "streamlit_app"

# ---------------------------------------------------------------------------
# Preguntas de ejemplo (sidebar)
# ---------------------------------------------------------------------------
EXAMPLES: list[str] = [
    "¿Qué portátiles tenéis por menos de 1000 €?",
    "¿Cuál es la política de devoluciones?",
    "Auriculares con cancelación de ruido",
    "¿Hacéis envíos internacionales?",
    "Recomiéndame un smartphone gama alta",
    "¿Tenéis garantía extendida?",
]

# ---------------------------------------------------------------------------
# Entornos de prompt (label de Langfuse)
# Los alumnos pueden añadir entornos custom si crean labels adicionales.
# Formato: { "Nombre visible en UI": "label_en_langfuse" }
#
# Labels habituales en Langfuse:
#   "production"  — prompt activo en producción
#   "staging"     — candidato bajo evaluación
#   "development" — experimentación libre de los alumnos
#   "latest"      — label especial de Langfuse, siempre apunta a la última
#                    versión creada (NO usar como entorno, solo para debug)
# ---------------------------------------------------------------------------
ENVIRONMENTS: dict[str, str] = {
    "🟢 Production": "production",
    "🟡 Staging": "staging",
    "🔵 Development": "development",
}
