"""TechShop Agent — interfaz Streamlit."""

from __future__ import annotations

import os
import time
import uuid

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# .env está en la raíz del repo, no en streamlit_app/
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_FILE, override=True)

# Si el .env trae credenciales explícitas, eliminar AWS_PROFILE para que
# boto3 no intente usar un perfil con nombre que puede no existir.
if os.getenv("AWS_ACCESS_KEY_ID"):
    os.environ.pop("AWS_PROFILE", None)

# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------
st.set_page_config(page_title="TechShop Agent", page_icon="🛒", layout="centered")

_CSS = """
<style>
#MainMenu, footer, header { visibility: hidden; }
.latency { font-size: 0.72rem; color: #9CA3AF; }
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Ejemplos de consulta
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
# Entornos de prompt (label → display)
# ---------------------------------------------------------------------------
ENVIRONMENTS: dict[str, str] = {
    "🟢 Production": "production",
    "🟡 Staging": "staging",
    "🔵 Development": "latest",
}


# ---------------------------------------------------------------------------
# Agentes (cacheados a nivel de servidor, uno por modo)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _build_base_agent() -> object:
    from techshop_agent import create_agent

    return create_agent()


@st.cache_resource(show_spinner=False)
def _build_instrumented_agent() -> object:
    from techshop_agent.solution.observability import create_observed_agent

    return create_observed_agent()


# ---------------------------------------------------------------------------
# Estado de sesión
# ---------------------------------------------------------------------------
def _init_session() -> None:
    defaults: dict = {
        "messages": [],
        "session_id": f"streamlit-{uuid.uuid4().hex[:8]}",
        "agent_mode": "base",
        "prompt_env": "🟢 Production",
        "langfuse_enabled": bool(
            os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
        ),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Llamada al agente (con tracing Langfuse opcional)
# ---------------------------------------------------------------------------
def _call_agent(user_input: str) -> tuple[str, float]:
    start = time.monotonic()
    mode: str = st.session_state.agent_mode

    if mode == "instrumented":
        # ── Modo instrumentado: tracing completo con Langfuse ──────────────
        # Si hay selección de entorno, usa process_query_with_prompt para
        # enlazar la versión del prompt con la traza.
        try:
            prompt_label = ENVIRONMENTS.get(st.session_state.prompt_env, "production")
            from techshop_agent.solution.prompt_provider import process_query_with_prompt

            response = process_query_with_prompt(
                user_input,
                prompt_label=prompt_label,
                user_id="streamlit-student",
                session_id=st.session_state.session_id,
                source="streamlit_app",
            )
        except ImportError:
            # Fallback si prompt_provider no tiene process_query_with_prompt
            from techshop_agent.solution.observability import process_query

            response = process_query(
                user_input,
                user_id="streamlit-student",
                session_id=st.session_state.session_id,
                source="streamlit_app",
            )
        except Exception as exc:
            response = f"Error: {type(exc).__name__} — {exc}"
    else:
        # ── Modo base: agente sin instrumentación (o con tracing mínimo) ───
        agent = _build_base_agent()

        if st.session_state.langfuse_enabled:
            try:
                from langfuse.decorators import langfuse_context, observe

                @observe(name="streamlit_query")
                def _traced(query: str) -> str:
                    langfuse_context.update_current_trace(
                        user_id="streamlit-student",
                        session_id=st.session_state.session_id,
                        metadata={"source": "streamlit_app", "mode": "base"},
                    )
                    return str(agent(query))

                response = _traced(user_input)
            except Exception:
                response = str(agent(user_input))
        else:
            response = str(agent(user_input))

    latency_ms = (time.monotonic() - start) * 1000
    return response, latency_ms


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def main() -> None:
    _init_session()

    st.title("🛒 TechShop Agent")
    st.caption("Asistente de atención al cliente — Curso LLMOps")

    # Sidebar: sesión + modo de agente + ejemplos
    with st.sidebar:
        st.markdown(f"**Sesión** `{st.session_state.session_id}`")

        if st.button("↻ Nueva sesión", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = f"streamlit-{uuid.uuid4().hex[:8]}"
            st.rerun()

        # ── Toggle de modo de agente ────────────────────────────────────────
        st.divider()
        st.markdown("**Modo del agente**")
        new_mode = st.radio(
            label="Selecciona modo:",
            options=["base", "instrumented"],
            format_func=lambda x: (
                "🤖 Base (sin tracing)" if x == "base" else "📊 Instrumentado (Langfuse)"
            ),
            index=0 if st.session_state.agent_mode == "base" else 1,
            key="_mode_radio",
            label_visibility="collapsed",
        )
        if new_mode != st.session_state.agent_mode:
            st.session_state.agent_mode = new_mode
            st.session_state.messages = []
            st.session_state.session_id = f"streamlit-{uuid.uuid4().hex[:8]}"
            st.rerun()

        if st.session_state.agent_mode == "instrumented":
            if st.session_state.langfuse_enabled:
                st.success("✅ Langfuse activo", icon="📊")
            else:
                st.warning("⚠️ Langfuse no configurado\n\nDefine LANGFUSE_PUBLIC_KEY y LANGFUSE_SECRET_KEY en .env", icon="⚠️")

            # ── Selector de entorno de prompt ───────────────────────────────
            st.divider()
            st.markdown("**Entorno de prompt**")
            env_names = list(ENVIRONMENTS.keys())
            current_idx = env_names.index(st.session_state.prompt_env) if st.session_state.prompt_env in env_names else 0
            new_env = st.radio(
                label="Selecciona entorno:",
                options=env_names,
                index=current_idx,
                key="_env_radio",
                label_visibility="collapsed",
            )
            if new_env != st.session_state.prompt_env:
                st.session_state.prompt_env = new_env
                st.session_state.messages = []
                st.session_state.session_id = f"streamlit-{uuid.uuid4().hex[:8]}"
                st.rerun()

            label = ENVIRONMENTS[st.session_state.prompt_env]
            st.caption(f"Label: `{label}`")

            # Mostrar versión actual del prompt
            if st.session_state.langfuse_enabled:
                try:
                    from techshop_agent.solution.prompt_provider import get_prompt_client
                    pc = get_prompt_client(label=label, cache_ttl_seconds=0)
                    if not pc.is_fallback:
                        st.caption(f"Versión: **v{pc.version}**")
                    else:
                        st.caption("⚠️ Usando fallback local")
                except Exception:
                    st.caption("—")
        else:
            st.info("Sin tracing profundo.\nCambia a **Instrumentado** para ver trazas en Langfuse.", icon="ℹ️")

        # ── Preguntas de ejemplo ────────────────────────────────────────────
        st.divider()
        st.caption("Prueba con estos ejemplos:")
        for ej in EXAMPLES:
            if st.button(ej, key=f"ex_{ej}", use_container_width=True):
                st.session_state._quick = ej
                st.rerun()

    # Historial
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "latency_ms" in msg:
                st.markdown(
                    f'<span class="latency">{msg["latency_ms"]:.0f} ms</span>',
                    unsafe_allow_html=True,
                )

    # Input
    prefill = st.session_state.pop("_quick", None)
    user_input = st.chat_input("Escribe tu pregunta…") or prefill

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner(""):
                try:
                    response, latency_ms = _call_agent(user_input)
                except Exception as exc:
                    response = f"Error: {type(exc).__name__} — {exc}"
                    latency_ms = 0.0
                    st.error(response)

            st.markdown(response)
            st.markdown(
                f'<span class="latency">{latency_ms:.0f} ms</span>',
                unsafe_allow_html=True,
            )

        st.session_state.messages.append(
            {"role": "assistant", "content": response, "latency_ms": latency_ms}
        )
        st.rerun()


if __name__ == "__main__":
    main()
