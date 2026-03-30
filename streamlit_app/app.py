import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import contextlib
import io
import os
import time
import uuid

import dotenv
import pandas as pd
import streamlit as st
from app_config import TRACING_SOURCE, TRACING_USER_ID
from langfuse import Langfuse, get_client
from numpy import dot

from techshop_agent.agent import create_agent
from techshop_agent.solution.observability import create_observed_agent, process_query
from techshop_agent.solution.prompt_provider import process_query_with_prompt
from techshop_agent.schemas.schemas import InputLeaguePerformers, InputLeagueStats
from techshop_agent.tools import get_league_top_performers, get_league_stats

dotenv.load_dotenv(override=True, dotenv_path='../.env')
get_client()

@st.cache_resource
def get_agent():
    return create_observed_agent()


def _init_session() -> None:
    print(os.getenv("LANGFUSE_PUBLIC_KEY"))
    print(os.getenv("LANGFUSE_SECRET_KEY"))
    defaults: dict = {
        "messages": [],
        "session_id": f"streamlit-{uuid.uuid4().hex[:8]}",
        "agent_mode": "base",
        "prompt_env": "🟢 Production",
        "langfuse_enabled": bool(
            os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
        ),
        "eval_result": None,
        "eval_running": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
_init_session()
# ─── CALL AGENT  ────────────────────────────────────────────────────────────────

def _call_agent(user_input:str)->tuple[str,float,dict[str,float]]:
    start = time.monotonic()
    mode: str = st.session_state.agent_mode
    scores: dict[str, float] = {}

    if mode == "instrumented":
        try:

            with contextlib.redirect_stdout(io.StringIO()):
                response, scores = process_query_with_prompt(
                    user_input,
                    prompt_label=prompt_label,
                    user_id=TRACING_USER_ID,
                    session_id=st.session_state.session_id,
                    source=TRACING_SOURCE,
                )
        except ImportError:

            with contextlib.redirect_stdout(io.StringIO()):
                response = process_query(
                    user_input,
                    user_id=TRACING_USER_ID,
                    session_id=st.session_state.session_id,
                    source=TRACING_SOURCE,
                )
        except Exception as exc:
            response = f"Error: {type(exc).__name__} — {exc}"
    else:
        agent = get_agent()

        if st.session_state.langfuse_enabled:
            try:

                @observe(name="streamlit_query")
                def _traced(query: str) -> str:
                    langfuse_context.update_current_trace(
                        user_id=TRACING_USER_ID,
                        session_id=st.session_state.session_id,
                        metadata={"source": TRACING_SOURCE, "mode": "base"},
                    )
                    with contextlib.redirect_stdout(io.StringIO()):
                        return str(agent(query))

                response = _traced(user_input)
            except Exception:
                response = str(agent(user_input))
        else:
            with contextlib.redirect_stdout(io.StringIO()):
                response = str(agent(user_input))

    latency_ms = (time.monotonic() - start) * 1000
    return response, latency_ms, scores




# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kinetic Intel · Director AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

/* ── GLOBAL ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0b1326 !important;
    color: #dae2fd !important;
}
.stApp { background-color: #0b1326 !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background-color: #131b2e !important;
    border-right: none !important;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
}

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── TYPOGRAPHY ── */
h1, h2, h3, .display-text {
    font-family: 'Manrope', sans-serif !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #4ae176 0%, #009542 100%) !important;
    color: #003915 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 0.75rem !important;
    padding: 0.5rem 1.5rem !important;
    transition: transform 0.15s ease;
}
.stButton > button:hover {
    transform: scale(1.03) !important;
    filter: brightness(1.1);
}

/* ── CHAT INPUT ── */
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div {
    background-color: #2d3449 !important;
    border-radius: 1rem !important;
}
[data-testid="stChatInput"] {
    border: 1px solid rgba(144, 144, 151, 0.3) !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #4ae176 !important;
    box-shadow: 0 0 0 2px rgba(74, 225, 118, 0.15) !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea:focus {
    background-color: #2d3449 !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    caret-color: #4ae176 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: rgba(218, 226, 253, 0.5) !important;
    opacity: 1 !important;
}
[data-testid="stChatInputSubmitButton"] button {
    background: linear-gradient(135deg, #4ae176 0%, #009542 100%) !important;
    border-radius: 0.5rem !important;
    border: none !important;
}
[data-testid="stChatInputSubmitButton"] button:hover {
    filter: brightness(1.15) !important;
}

/* ── CHAT MESSAGES ── */
.stChatMessage {
    background: rgba(45, 52, 73, 0.4) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(144, 144, 151, 0.1) !important;
    border-radius: 1.25rem !important;
}
/* Force all text inside chat messages to white */
.stChatMessage p,
.stChatMessage span,
.stChatMessage div,
.stChatMessage li,
.stChatMessage strong,
.stChatMessage em,
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] strong {
    color: #ffffff !important;
}
/* Keep the primary green accent for bold highlights */
[data-testid="stChatMessage"] strong {
    color: #4ae176 !important;
}
/* Chat input text white */
.stChatInput textarea,
.stChatInput input {
    color: #ffffff !important;
}
.stChatInput textarea::placeholder,
.stChatInput input::placeholder {
    color: #ffffff !important;
    opacity: 1 !important;
}

/* ── METRICS ── */
[data-testid="metric-container"] {
    background: rgba(45, 52, 73, 0.4) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(144, 144, 151, 0.1) !important;
    border-radius: 1rem !important;
    padding: 1rem !important;
}
[data-testid="metric-container"] label {
    color: #b9c7e0 !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #4ae176 !important;
    font-family: 'Manrope', sans-serif !important;
    font-weight: 800 !important;
}

/* ── DATAFRAME / TABLE ── */
.stDataFrame, [data-testid="stDataFrame"] {
    border-radius: 0.75rem !important;
    overflow: hidden !important;
    border: 1px solid rgba(144, 144, 151, 0.2) !important;
}

/* ── SELECTBOX / SELECT ── */
.stSelectbox > div > div {
    background-color: #2d3449 !important;
    border: 1px solid rgba(144, 144, 151, 0.3) !important;
    border-radius: 0.75rem !important;
    color: #dae2fd !important;
}

/* ── PROGRESS BAR ── */
.stProgress > div > div > div {
    background: linear-gradient(135deg, #4ae176 0%, #009542 100%) !important;
    border-radius: 999px !important;
}
.stProgress > div > div {
    background-color: #2d3449 !important;
    border-radius: 999px !important;
}

/* ── DIVIDER ── */
hr { border-color: rgba(144, 144, 151, 0.15) !important; }


/* ── GLOBAL TEXT FALLBACKS ── */
.stMarkdown p, .stMarkdown span, .element-container p,
.stText, [data-testid="stMarkdownContainer"] p {
    color: #dae2fd !important;
}
/* Metric values */
[data-testid="stMetricValue"] { color: #4ae176 !important; }
[data-testid="stMetricDelta"] { color: #b9c7e0 !important; }
/* Widget labels (selectbox, etc.) */
[data-testid="stWidgetLabel"], .stSelectbox label,
.stRadio label, .stCheckbox label {
    color: #dae2fd !important;
}
/* Expander header */
.streamlit-expanderHeader, [data-testid="stExpander"] summary {
    color: #dae2fd !important;
}
/* Spinner text */
.stSpinner p, .stSpinner span { color: #dae2fd !important; }
/* Tab label text */
.stTabs [data-baseweb="tab"] span { color: inherit !important; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent !important;
    gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    background-color: #2d3449 !important;
    border-radius: 0.5rem !important;
    color: #b9c7e0 !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4ae176 0%, #009542 100%) !important;
    color: #003915 !important;
    font-weight: 700 !important;
}

/* ── CARD COMPONENT ── */
.ki-card {
    background: rgba(45, 52, 73, 0.4);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(144, 144, 151, 0.1);
    border-radius: 1.25rem;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.ki-card-title {
    font-family: 'Manrope', sans-serif;
    font-size: 0.65rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #b9c7e0;
    margin-bottom: 1rem;
}
.ki-pill-green {
    display: inline-block;
    background: rgba(74,225,118,0.15);
    color: #4ae176;
    font-weight: 900;
    font-size: 0.7rem;
    padding: 0.15rem 0.5rem;
    border-radius: 0.25rem;
}
.ki-pill-gold {
    display: inline-block;
    background: rgba(222,194,154,0.15);
    color: #dec29a;
    font-weight: 900;
    font-size: 0.65rem;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.ki-insight-box {
    border-left: 3px solid #4ae176;
    background: rgba(74, 225, 118, 0.05);
    border-radius: 0 0.75rem 0.75rem 0;
    padding: 0.75rem 1rem;
    font-size: 0.78rem;
    color: #b9c7e0;
    line-height: 1.6;
}
.ki-insight-box .label { color: #4ae176; font-weight: 700; }
.ki-trend-box {
    background: rgba(45, 52, 73, 0.5);
    border: 1px solid rgba(144, 144, 151, 0.1);
    border-radius: 1rem;
    padding: 1rem;
    font-size: 0.75rem;
    color: #b9c7e0;
    line-height: 1.6;
}
.ki-trend-title {
    font-size: 0.62rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #dae2fd;
    margin-bottom: 0.3rem;
}
.nav-logo-gradient {
    background: linear-gradient(135deg, #4ae176 0%, #009542 100%);
    border-radius: 0.5rem;
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>
""", unsafe_allow_html=True)

# Nombres legibles para los scores
_SCORE_LABELS: dict[str, str] = {
    "response_quality": "Calidad",
    "scope_adherence": "Ámbito",
}


def _render_scores_html(scores: dict[str, float]) -> str:
    if not scores:
        return ""
    parts = []
    for name, value in scores.items():
        label = _SCORE_LABELS.get(name, name)
        css_class = "score-good" if value >= 0.8 else ("score-warn" if value >= 0.5 else "score-bad")
        parts.append(f'<span class="{css_class}">{label}: {value:.0%}</span>')
    return f'<span class="scores">📊 {" · ".join(parts)}</span>'



LEAGUES = ["LaLiga", "Premier League", "Bundesliga", "Serie A", "Ligue 1"]


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_league_players(league: str) -> list[dict]:
    result = get_league_top_performers(InputLeaguePerformers(league=league, top_n=5, metric="Gls"))
    if isinstance(result, str):
        return []
    # normalise to the shape the UI expects
    for p in result:
        p.setdefault("eff", p["goals"])
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_league_stats(league: str) -> dict:
    result = get_league_stats(InputLeagueStats(league=league))
    if isinstance(result, str):
        return {}
    return result


# ─── SESSION STATE ───────────────────────────────────────────────────────────────
if "league" not in st.session_state:
    st.session_state.league = "LaLiga"
if "active_page" not in st.session_state:
    st.session_state.active_page = "Players"

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:2.5rem;">
        <div style="background:linear-gradient(135deg,#4ae176,#009542);border-radius:0.5rem;
                    width:2.5rem;height:2.5rem;display:flex;align-items:center;justify-content:center;">
            <span style="color:#003915;font-size:1.1rem;">⚡</span>
        </div>
        <div>
            <div style="font-family:Manrope,sans-serif;font-size:1.1rem;font-weight:800;color:#dae2fd;">Director AI</div>
            <div style="font-size:0.6rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:#4ae176;">Pro Analytics</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    pages = {"Dashboard": "📊", "Leagues": "🏆", "Players": "👤", "Teams": "👥"}
    for page, icon in pages.items():
        is_active = st.session_state.active_page == page
        style = ("background:linear-gradient(135deg,#4ae176,#009542);color:#003915;font-weight:700;"
                 if is_active else "color:#b9c7e0;")
        if st.sidebar.button(f"{icon}  {page}", key=f"nav_{page}",
                             width="stretch"):
            st.session_state.active_page = page
            st.rerun()

    st.markdown("<div style='margin-top:auto;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div class="ki-card" style="margin-top:1rem;">
        <div style="font-size:0.75rem;font-weight:700;color:#dae2fd;margin-bottom:0.4rem;">¿Power user?</div>
        <div style="font-size:0.68rem;color:#b9c7e0;line-height:1.5;">Accede a +100 funcionalidades en la versión Pro</div>
    </div>
    """, unsafe_allow_html=True)
    st.button("⚡ Upgrade to Elite", width="stretch")
    st.markdown("---")
    st.markdown("<span style='color:#b9c7e0;font-size:0.8rem;'>❓ Support &nbsp;&nbsp; 🚪 Logout</span>",
                unsafe_allow_html=True)

# ─── MAIN HEADER ─────────────────────────────────────────────────────────────────
col_logo, col_nav, col_mode = st.columns([2, 4, 3])

with col_logo:
    st.markdown("""
    <h2 style="font-family:Manrope,sans-serif;font-size:1.4rem;font-weight:900;
               color:#4ae176;letter-spacing:0.05em;margin:0;padding-top:0.3rem;">
        KINETIC INTEL
    </h2>""", unsafe_allow_html=True)

with col_nav:
    tabs_nav = st.tabs(["Season 25/26", "Live Telemetry", "Scouting"])

with col_mode:
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        st.button("🎮 Modo Fan", width="stretch")
    with mode_col2:
        st.button("📊 Modo Pro", width="stretch")

st.markdown("<hr style='border-color:rgba(144,144,151,0.15);margin:0.5rem 0 1rem 0;'>",
            unsafe_allow_html=True)

# ─── MAIN LAYOUT ─────────────────────────────────────────────────────────────────
chat_col, insights_col = st.columns([6, 3], gap="large")

# ══ CHAT INTERFACE ══════════════════════════════════════════════════════════════
with chat_col:
    # st.container con height contiene realmente los elementos Streamlit dentro del panel
    messages_pane = st.container(height=520, border=False)
    with messages_pane:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                with st.chat_message("user", avatar="🟢"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant", avatar="⚡"):
                    st.markdown(msg["content"])

    # Chat input debajo del panel
    if prompt := st.chat_input("Pregunta sobre jugadores, tácticas o xG..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Analizando telemetría..."):
            try:
                response_text, latency_ms, scores = _call_agent(prompt)
            except Exception as exc:
                response_text = f"**Error:** {type(exc).__name__} — {exc}"
                latency_ms, scores = 0.0, {}
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()

# ══ QUICK INSIGHTS SIDEBAR ══════════════════════════════════════════════════════
with insights_col:
    # ── League selector ──
    st.session_state.league = st.selectbox(
        "Liga",
        LEAGUES,
        index=LEAGUES.index(st.session_state.league),
        label_visibility="collapsed",
    )

    qi = _fetch_league_stats(st.session_state.league)
    players = _fetch_league_players(st.session_state.league)

    # ── Stats card ──
    st.markdown('<div class="ki-card-title" style="margin-top:0.5rem;">Insights Rápidos</div>',
                unsafe_allow_html=True)

    avg_g90 = qi.get("avg_goals_per_90", 0.0)
    pct = min(int(avg_g90 * 250), 100)
    st.metric(f"Media goles/90 · {st.session_state.league}", f"{avg_g90:.3f}")
    st.progress(pct / 100)

    top_scorer = qi.get("top_scorer", "—")
    top_goals = qi.get("top_scorer_goals", 0)
    top_team = qi.get("top_scorer_team", "")
    avg_eff = qi.get("avg_shooting_efficiency", 0.0)
    total_goals = qi.get("total_goals", 0)
    trend_text = (
        f"Máximo goleador: {top_scorer} ({top_team}) con {top_goals} goles. "
        f"Total de goles en la liga: {total_goals}."
    )
    premium_text = (
        f"Eficiencia media de disparo (G/Sh) en {st.session_state.league}: "
        f"{avg_eff:.1%}. Los mejores finalizadores superan el 20%."
    )
    st.markdown(f"""
    <div class="ki-trend-box" style="margin-top:1rem;">
        <div class="ki-trend-title">📈 Tendencia Global</div>
        <div style="font-size:0.75rem;color:#b9c7e0;line-height:1.6;">{trend_text}</div>
    </div>
    <div class="ki-trend-box" style="margin-top:0.75rem;">
        <div class="ki-trend-title" style="color:#dec29a;">⚡ Dato Premium</div>
        <div style="font-size:0.75rem;color:#b9c7e0;line-height:1.6;">{premium_text}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Top performers mini-table ──
    top3 = sorted(players, key=lambda x: x["goals"], reverse=True)[:3]
    rows_html = ""
    for i, p in enumerate(top3):
        medal = ["🥇", "🥈", "🥉"][i]
        rows_html += (
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:0.5rem 0;border-bottom:1px solid rgba(144,144,151,0.1);">'
            f'<div style="font-size:0.8rem;font-weight:600;color:#dae2fd;">{medal} {p["name"]}</div>'
            f'<span class="ki-pill-green">{p["goals"]} goles</span></div>'
        )
    st.markdown(
        f'<div class="ki-card" style="margin-top:1rem;">'
        f'<div class="ki-card-title">🏆 Top Goleadores</div>'
        f'{rows_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── VIP Analysis card ──
    st.markdown("""
    <div class="ki-card" style="margin-top:0.5rem;position:relative;overflow:hidden;
         background:linear-gradient(135deg,rgba(45,52,73,0.6),rgba(11,19,38,0.9));">
        <span class="ki-pill-gold">Análisis VIP</span>
        <div style="font-family:Manrope,sans-serif;font-size:1rem;font-weight:800;
                    color:#dae2fd;margin:0.75rem 0 0.5rem 0;line-height:1.3;">
            Mapa de Calor: Lewandowski vs LaLiga
        </div>
        <div style="font-size:0.72rem;color:#b9c7e0;line-height:1.6;margin-bottom:1rem;">
            Visualiza dónde el delantero polaco está rompiendo los esquemas defensivos.
        </div>
        <div style="font-size:0.75rem;font-weight:700;color:#4ae176;cursor:pointer;">
            Explorar Telemetría →
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── BOTTOM STATS ROW ────────────────────────────────────────────────────────────
st.markdown("<hr style='border-color:rgba(144,144,151,0.1);margin:1.5rem 0 1rem 0;'>",
            unsafe_allow_html=True)
st.markdown(f'<div class="ki-card-title">📊 Estadísticas · {st.session_state.league}</div>',
            unsafe_allow_html=True)

_league_stats = _fetch_league_stats(st.session_state.league)
_league_players = _fetch_league_players(st.session_state.league)
df_full = pd.DataFrame(_league_players)
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("Goles líder", _league_stats.get("top_scorer_goals", 0))
with m2:
    st.metric("Máximo goleador", _league_stats.get("top_scorer", "—"))
with m3:
    st.metric("Media goles/jugador", f"{_league_stats.get('avg_goals_per_player', 0):.2f}")
with m4:
    st.metric("Total goles", _league_stats.get("total_goals", 0))
with m5:
    st.metric("Efic. disparo (G/Sh)", f"{_league_stats.get('avg_shooting_efficiency', 0):.1%}")

# ─── FULL TABLE ──────────────────────────────────────────────────────────────────
with st.expander(f"📋 Ver tabla completa — {st.session_state.league}", expanded=False):
    if not df_full.empty:
        df_show = df_full[["name", "team", "pos", "apps", "goals", "assists", "g_per_sh"]].copy()
        df_show.columns = ["Jugador", "Equipo", "Pos.", "PJ", "Goles", "Asist.", "G/Disparo"]
        st.dataframe(df_show, width="stretch", hide_index=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:1.5rem 0 0.5rem;font-size:0.65rem;
            color:rgba(185,199,224,0.4);letter-spacing:0.1em;text-transform:uppercase;">
    KINETIC INTEL · Director AI Pro Analytics · Temporada 23/24 · Datos simulados para demo
</div>
""", unsafe_allow_html=True)