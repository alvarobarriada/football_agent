import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
import streamlit as st

from techshop_agent.agent import create_agent


@st.cache_resource
def get_agent():
    return create_agent()

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
.stChatInput textarea {
    background-color: #2d3449 !important;
    border: 1px solid rgba(144, 144, 151, 0.3) !important;
    border-radius: 1rem !important;
    color: #dae2fd !important;
    font-family: 'Inter', sans-serif !important;
}
.stChatInput textarea:focus {
    border-color: #4ae176 !important;
    box-shadow: 0 0 0 2px rgba(74, 225, 118, 0.25) !important;
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

# ─── DATA ────────────────────────────────────────────────────────────────────────
PLAYERS_DATA = {
    "LaLiga": [
        {"name": "Robert Lewandowski", "team": "FC Barcelona", "pos": "DC", "goals": 18, "xg": 13.4, "eff": 4.6, "apps": 24, "assists": 5},
        {"name": "Jude Bellingham",    "team": "Real Madrid",  "pos": "MC", "goals": 16, "xg": 12.1, "eff": 3.9, "apps": 22, "assists": 8},
        {"name": "Antoine Griezmann",  "team": "Atlético",     "pos": "SD", "goals": 13, "xg": 10.5, "eff": 2.5, "apps": 23, "assists": 6},
        {"name": "Vinícius Jr.",        "team": "Real Madrid",  "pos": "EI", "goals": 12, "xg": 10.1, "eff": 1.9, "apps": 21, "assists": 9},
        {"name": "Artem Dovbyk",       "team": "Girona FC",    "pos": "DC", "goals": 11, "xg":  9.2, "eff": 1.8, "apps": 23, "assists": 3},
    ],
    "Premier League": [
        {"name": "Erling Haaland",  "team": "Man City",   "pos": "DC", "goals": 22, "xg": 18.1, "eff": 3.9, "apps": 25, "assists": 4},
        {"name": "Mohamed Salah",   "team": "Liverpool",  "pos": "ED", "goals": 19, "xg": 14.8, "eff": 4.2, "apps": 26, "assists": 10},
        {"name": "Cole Palmer",     "team": "Chelsea",    "pos": "MC", "goals": 17, "xg": 13.0, "eff": 4.0, "apps": 24, "assists": 9},
        {"name": "Alexander Isak",  "team": "Newcastle",  "pos": "DC", "goals": 15, "xg": 13.5, "eff": 1.5, "apps": 23, "assists": 3},
        {"name": "Ollie Watkins",   "team": "Aston Villa","pos": "DC", "goals": 14, "xg": 12.2, "eff": 1.8, "apps": 25, "assists": 8},
    ],
    "Serie A": [
        {"name": "Lautaro Martínez", "team": "Inter",     "pos": "DC", "goals": 20, "xg": 15.5, "eff": 4.5, "apps": 25, "assists": 5},
        {"name": "Duván Zapata",     "team": "Torino",    "pos": "DC", "goals": 14, "xg": 11.2, "eff": 2.8, "apps": 22, "assists": 2},
        {"name": "Federico Chiesa",  "team": "Juventus",  "pos": "ED", "goals": 12, "xg":  9.8, "eff": 2.2, "apps": 24, "assists": 7},
        {"name": "Ademola Lookman",  "team": "Atalanta",  "pos": "ED", "goals": 11, "xg":  8.9, "eff": 2.1, "apps": 23, "assists": 6},
        {"name": "Victor Osimhen",   "team": "Napoli",    "pos": "DC", "goals": 10, "xg":  9.5, "eff": 0.5, "apps": 20, "assists": 3},
    ],
}

CHAT_RESPONSES = {
    "default": {
        "text": "Basado en los datos de telemetría de **KINETIC INTEL** para la temporada 23/24, aquí tienes los finalizadores más eficientes. El líder supera significativamente su producción esperada.",
        "insight": "**Insight Táctico:** Los atacantes que superan en mayor medida su xG tienden a disparar desde posiciones de alta calidad dentro del área pequeña, promediando una probabilidad de gol por tiro un 20-25% superior a la media histórica.",
        "show_table": True,
    },
    "xg": {
        "text": "El **Expected Goals (xG)** es una métrica que mide la probabilidad de que un disparo acabe en gol, basándose en la posición, el tipo de remate y el contexto defensivo. Un xG de 1.0 significa que, estadísticamente, ese disparo debería convertirse una vez de cada una.",
        "insight": "**Dato clave:** En LaLiga 23/24 el promedio de xG por partido es de **1.28**, el más alto en 5 temporadas.",
        "show_table": False,
    },
    "real madrid": {
        "text": "**Real Madrid** genera el 42% de su xG total mediante transiciones rápidas de menos de 8 segundos. Bellingham lidera la producción desde segunda línea con 3.9 goles sobre esperado.",
        "insight": "**Insight Táctico:** Las transiciones rápidas del Madrid se inician mayoritariamente desde el centro del campo izquierdo, aprovechando los espacios que dejan los rivales al presionar alto.",
        "show_table": False,
    },
    "lewandowski": {
        "text": "**Robert Lewandowski** lidera LaLiga con +4.6 sobre su xG. Su rendimiento se explica por una mejora en la calidad de sus disparos desde el semicírculo del área.",
        "insight": "**Insight Táctico:** Lewandowski promedia una probabilidad de gol por tiro un 22% superior a su media histórica, fruto de un movimiento sin balón más preciso que en temporadas anteriores.",
        "show_table": False,
    },
}

QUICK_INSIGHTS = {
    "LaLiga": {
        "avg_xg": 1.28, "pct": 64,
        "trend": "Las defensas bajas están permitiendo un 12% más de xG desde media distancia en comparación con la temporada 22/23.",
        "premium": "Real Madrid genera el 42% de su xG total mediante transiciones rápidas de menos de 8 segundos.",
    },
    "Premier League": {
        "avg_xg": 1.54, "pct": 77,
        "trend": "El pressing alto del Liverpool genera un 18% más de xG desde transiciones, liderando la estadística de calidad ofensiva.",
        "premium": "Haaland convierte el 60% de sus ocasiones de área pequeña, casi el doble de la media de la liga.",
    },
    "Serie A": {
        "avg_xg": 1.35, "pct": 68,
        "trend": "La Serie A registra el mayor aumento de xG por remate de cabeza (+9%) respecto a la temporada anterior.",
        "premium": "El Inter genera más xG en los primeros 15 minutos que cualquier otro equipo europeo de élite.",
    },
}

# ─── SESSION STATE ───────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "user",
            "content": "¿Qué delantero de la liga española está rindiendo por encima de sus goles esperados (xG) esta temporada?",
        },
        {
            "role": "assistant",
            "content": CHAT_RESPONSES["default"],
        },
    ]
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
                             use_container_width=True):
            st.session_state.active_page = page
            st.rerun()

    st.markdown("<div style='margin-top:auto;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div class="ki-card" style="margin-top:1rem;">
        <div style="font-size:0.75rem;color:#b9c7e0;margin-bottom:0.75rem;">Power user?</div>
    </div>
    """, unsafe_allow_html=True)
    st.button("⚡ Upgrade to Elite", use_container_width=True)
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
    tabs_nav = st.tabs(["Season 23/24", "Live Telemetry", "**Scouting**"])

with col_mode:
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        st.button("🎮 Modo Fan", use_container_width=True)
    with mode_col2:
        st.button("📊 Modo Pro", use_container_width=True)

st.markdown("<hr style='border-color:rgba(144,144,151,0.15);margin:0.5rem 0 1rem 0;'>",
            unsafe_allow_html=True)

# ─── LEAGUE SELECTOR ─────────────────────────────────────────────────────────────
league_col, spacer = st.columns([3, 7])
with league_col:
    st.session_state.league = st.selectbox(
        "Liga",
        list(PLAYERS_DATA.keys()),
        index=list(PLAYERS_DATA.keys()).index(st.session_state.league),
        label_visibility="collapsed",
    )

# ─── MAIN LAYOUT ─────────────────────────────────────────────────────────────────
chat_col, insights_col = st.columns([6, 3], gap="large")

# ══ CHAT INTERFACE ══════════════════════════════════════════════════════════════
with chat_col:
    st.markdown('<div class="ki-card" style="min-height:520px;">', unsafe_allow_html=True)

    # Render existing messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="🟢"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="⚡"):
                resp = msg["content"]
                if isinstance(resp, dict):
                    st.markdown(resp["text"])
                    if resp.get("show_table"):
                        df = pd.DataFrame(PLAYERS_DATA[st.session_state.league])
                        df_display = df[["name", "team", "goals", "xg", "eff"]].copy()
                        df_display.columns = [
                            "Jugador", "Equipo", "Goles", "xG", "Eficiencia (+xG)"
                        ]
                        st.dataframe(df_display, use_container_width=True, hide_index=True)
                    st.markdown(f"""
                    <div class="ki-insight-box" style="margin-top:1rem;">
                        {resp['insight'].replace("**", "<b>", 1).replace("**", "</b>", 1)
                         .replace("**", "<b>", 1).replace("**", "</b>", 1)
                         .replace("**", "<b>", 1).replace("**", "</b>", 1)}
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(resp)

    st.markdown("</div>", unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Pregunta sobre jugadores, tácticas o xG..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant", avatar="⚡"):
            with st.spinner("Analizando telemetría..."):
                agent = get_agent()
                result = agent(prompt)
                response_text = str(result)
            st.markdown(response_text)

        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()

# ══ QUICK INSIGHTS SIDEBAR ══════════════════════════════════════════════════════
with insights_col:
    qi = QUICK_INSIGHTS[st.session_state.league]

    # ── Stats card ──
    st.markdown('<div class="ki-card">', unsafe_allow_html=True)
    st.markdown('<div class="ki-card-title">Insights Rápidos</div>', unsafe_allow_html=True)

    st.metric(f"Promedio xG · {st.session_state.league}", f"{qi['avg_xg']}")
    st.progress(qi["pct"] / 100)

    st.markdown(f"""
    <div class="ki-trend-box" style="margin-top:1rem;">
        <div class="ki-trend-title">📈 Tendencia Global</div>
        <div style="font-size:0.75rem;color:#b9c7e0;line-height:1.6;">{qi['trend']}</div>
    </div>
    <div class="ki-trend-box" style="margin-top:0.75rem;">
        <div class="ki-trend-title" style="color:#dec29a;">⚡ Dato Premium</div>
        <div style="font-size:0.75rem;color:#b9c7e0;line-height:1.6;">{qi['premium']}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Top performers mini-table ──
    st.markdown('<div class="ki-card" style="margin-top:0.5rem;">', unsafe_allow_html=True)
    st.markdown('<div class="ki-card-title">🏆 Top Eficiencia</div>', unsafe_allow_html=True)

    players = PLAYERS_DATA[st.session_state.league]
    top3 = sorted(players, key=lambda x: x["eff"], reverse=True)[:3]
    for i, p in enumerate(top3):
        medal = ["🥇", "🥈", "🥉"][i]
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:0.5rem 0;border-bottom:1px solid rgba(144,144,151,0.1);">
            <div style="font-size:0.8rem;font-weight:600;color:#dae2fd;">
                {medal} {p['name']}
            </div>
            <span class="ki-pill-green">+{p['eff']}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

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

df_full = pd.DataFrame(PLAYERS_DATA[st.session_state.league])
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("Goles líder", df_full["goals"].max())
with m2:
    best = df_full.loc[df_full["eff"].idxmax()]
    st.metric("Mejor eficiencia", f"+{best['eff']}", best["name"])
with m3:
    st.metric("xG promedio", f"{df_full['xg'].mean():.1f}")
with m4:
    st.metric("Total goles", df_full["goals"].sum())
with m5:
    over_xg = (df_full["eff"] > 0).sum()
    st.metric("Sobre su xG", f"{over_xg}/{len(df_full)}")

# ─── FULL TABLE ──────────────────────────────────────────────────────────────────
with st.expander(f"📋 Ver tabla completa — {st.session_state.league}", expanded=False):
    df_show = df_full[["name", "team", "pos", "apps", "goals", "xg", "eff", "assists"]].copy()
    df_show.columns = ["Jugador", "Equipo", "Pos.", "PJ", "Goles", "xG", "Efic. (+xG)", "Asist."]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:1.5rem 0 0.5rem;font-size:0.65rem;
            color:rgba(185,199,224,0.4);letter-spacing:0.1em;text-transform:uppercase;">
    KINETIC INTEL · Director AI Pro Analytics · Temporada 23/24 · Datos simulados para demo
</div>
""", unsafe_allow_html=True)