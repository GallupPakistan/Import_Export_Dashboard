import streamlit as st

st.set_page_config(
    page_title="Pakistan Trade Intelligence | Gallup Pakistan",
    page_icon="🇵🇰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --bg:           #070b14;
    --bg-card:      #0d1526;
    --bg-card-hover:#111d33;
    --bg-glass:     rgba(13,21,38,0.85);
    --border:       rgba(99,130,202,0.13);
    --border-glow:  rgba(99,130,202,0.28);
    --gallup-navy:  #002147;
    --gallup-red:   #e4002b;
    --brand-from:   #002147;
    --brand-to:     #003d7a;
    --green:  #10d9a0;
    --red:    #f43f5e;
    --gold:   #f59e0b;
    --blue:   #60a5fa;
    --purple: #a78bfa;
    --orange: #fb923c;
    --teal:   #2dd4bf;
    --text:       #e2e8f0;
    --text-muted: #64748b;
    --text-dim:   #334155;
    --radius-card: 18px;
    --radius-sm:   10px;
    --shadow-card: 0 4px 24px rgba(0,0,0,0.45);
    --shadow-glow: 0 0 30px rgba(16,217,160,0.12);
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
.stApp { background: var(--bg) !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem !important; }

/* TOP BAR */
.topbar {
    background: linear-gradient(100deg, #001633 0%, #002147 45%, #002d5c 70%, #001e42 100%);
    border-bottom: 1px solid rgba(0,33,71,0.6);
    padding: 0.7rem 1.8rem;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1.2rem; position: relative; overflow: hidden;
}
.topbar::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #002147, #e4002b, #f59e0b, #002147);
    background-size: 300% 100%; animation: shimmer 4s linear infinite;
}
@keyframes shimmer { 0%{background-position:0%} 100%{background-position:300%} }
.topbar-brand { display: flex; align-items: center; gap: 1rem; }
.topbar-logo { background:white; border-radius:8px; padding:4px 10px; display:flex; align-items:center; }
.topbar-logo img { height:34px; display:block; }
.topbar-divider { width:1px; height:36px; background:rgba(255,255,255,0.15); margin:0 0.3rem; }
.topbar-title { font-size:0.85rem; color:rgba(255,255,255,0.7); font-weight:500; line-height:1.5; }
.topbar-title b { color:white; font-weight:700; }
.topbar-meta { text-align:right; font-size:0.7rem; color:rgba(255,255,255,0.5); line-height:1.8; }
.topbar-meta b { color:var(--gold); font-size:0.75rem; }

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060e1e 0%, #040a16 100%) !important;
    border-right: 1px solid rgba(0,33,71,0.5) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

.sidebar-brand {
    background: linear-gradient(135deg, #001633 0%, #002147 100%);
    border: 1px solid rgba(0,33,71,0.8); border-radius: var(--radius-card);
    padding: 1.1rem; text-align: center; margin-bottom: 1.2rem;
    position: relative; overflow: hidden;
}
.sidebar-brand::before {
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg, #e4002b, #002147);
}
.sidebar-brand .sb-label {
    color: var(--green); font-size:0.68rem; font-weight:700;
    letter-spacing:0.18em; text-transform:uppercase; margin-top:6px;
}
.sidebar-brand .sb-sub { color:var(--text-muted); font-size:0.68rem; margin-top:0.3rem; }

.sidebar-section-label {
    font-size:0.65rem; font-weight:700; letter-spacing:0.13em;
    text-transform:uppercase; color:var(--text-dim) !important;
    padding:0.5rem 0.3rem 0.3rem;
}

div[data-testid="stRadio"] > div { gap:0.2rem !important; }
div[data-testid="stRadio"] > div > label {
    padding:0.6rem 0.9rem !important; border-radius:var(--radius-sm) !important;
    font-size:0.85rem !important; font-weight:500 !important;
    color:var(--text-muted) !important; cursor:pointer !important;
    width:100% !important; transition:all 0.18s ease; border:1px solid transparent !important;
}
div[data-testid="stRadio"] > div > label:hover {
    background:rgba(99,130,202,0.1) !important; color:var(--blue) !important;
    border-color:var(--border) !important;
}
div[data-testid="stRadio"] > div > label[data-baseweb="radio"] > div:first-child { display:none !important; }

.sidebar-info {
    background:rgba(255,255,255,0.02); border:1px solid var(--border);
    border-radius:var(--radius-sm); padding:0.9rem 1rem; font-size:0.7rem;
    color:var(--text-muted); line-height:1.8; margin-top:1rem;
}
.sidebar-info strong { color:#94a3b8; }

/* PAGE HEADER */
.page-header {
    display:flex; align-items:flex-start; gap:1rem;
    margin-bottom:1.4rem; padding-bottom:1rem; border-bottom:1px solid var(--border);
}
.page-title {
    font-family:'Space Grotesk',sans-serif; font-size:1.55rem;
    font-weight:700; color:var(--text); line-height:1.2;
}
.page-subtitle { font-size:0.82rem; color:var(--text-muted); margin-top:0.25rem; }

/* SECTION BADGE / HEADER */
.section-badge {
    display:inline-flex; align-items:center; gap:0.4rem;
    background:rgba(16,217,160,0.1); color:var(--green);
    border:1px solid rgba(16,217,160,0.25); border-radius:20px;
    padding:0.22rem 0.8rem; font-size:0.68rem; font-weight:700;
    text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.6rem;
}
.section-header {
    background:linear-gradient(100deg,#001633 0%,#002147 100%);
    border:1px solid rgba(0,33,71,0.6); border-left:3px solid #e4002b;
    color:var(--text); padding:0.65rem 1rem;
    border-radius:0 var(--radius-sm) var(--radius-sm) 0;
    font-family:'Space Grotesk',sans-serif; font-size:0.92rem;
    font-weight:700; margin:1rem 0 0.7rem 0; letter-spacing:0.02em;
}

/* METRIC CARDS */
.metric-card {
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius-card); padding:1.1rem 1.3rem 1rem;
    position:relative; overflow:hidden;
    transition:transform 0.2s,box-shadow 0.2s,border-color 0.2s;
    box-shadow:var(--shadow-card);
}
.metric-card:hover { transform:translateY(-2px); border-color:var(--border-glow); box-shadow:var(--shadow-card),var(--shadow-glow); }
.metric-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2.5px; border-radius:999px 999px 0 0; }
.metric-card::after  { content:''; position:absolute; top:-30px; right:-30px; width:100px; height:100px; border-radius:50%; opacity:0.06; pointer-events:none; }
.metric-card.green::before  { background:linear-gradient(90deg,var(--green),transparent 70%); }
.metric-card.green::after   { background:var(--green); }
.metric-card.red::before    { background:linear-gradient(90deg,var(--red),transparent 70%); }
.metric-card.red::after     { background:var(--red); }
.metric-card.gold::before   { background:linear-gradient(90deg,var(--gold),transparent 70%); }
.metric-card.gold::after    { background:var(--gold); }
.metric-card.blue::before   { background:linear-gradient(90deg,var(--blue),transparent 70%); }
.metric-card.blue::after    { background:var(--blue); }
.metric-card.purple::before { background:linear-gradient(90deg,var(--purple),transparent 70%); }
.metric-card.purple::after  { background:var(--purple); }
.metric-card.teal::before   { background:linear-gradient(90deg,var(--teal),transparent 70%); }
.metric-card.orange::before { background:linear-gradient(90deg,var(--orange),transparent 70%); }

.metric-label { font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:var(--text-muted); margin-bottom:0.3rem; }
.metric-value { font-family:'Space Grotesk',sans-serif; font-size:1.7rem; font-weight:700; line-height:1.1; letter-spacing:-0.5px; }
.metric-sub   { font-size:0.72rem; color:var(--text-muted); margin-top:0.25rem; }
.metric-delta { display:inline-flex; align-items:center; gap:0.2rem; font-size:0.75rem; font-weight:700; margin-top:0.4rem; padding:0.15rem 0.5rem; border-radius:20px; }
.delta-pos { color:var(--green); background:rgba(16,217,160,0.1); border:1px solid rgba(16,217,160,0.2); }
.delta-neg { color:var(--red);   background:rgba(244,63,94,0.1);  border:1px solid rgba(244,63,94,0.2);  }

/* CHART CARDS */
.chart-card {
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius-card); padding:1.1rem 1.1rem 0.5rem;
    margin-bottom:1rem; box-shadow:var(--shadow-card); transition:border-color 0.2s;
}
.chart-card:hover { border-color:var(--border-glow); }
.chart-title {
    font-family:'Space Grotesk',sans-serif; font-size:0.88rem; font-weight:700;
    margin-bottom:0.6rem; color:var(--text); display:flex; align-items:center; gap:0.4rem;
}

/* INSIGHT BOXES */
.insight-box {
    background:linear-gradient(135deg,rgba(16,217,160,0.07),rgba(16,217,160,0.02));
    border:1px solid rgba(16,217,160,0.18); border-radius:var(--radius-sm);
    padding:0.9rem 1.1rem; margin:0.5rem 0; font-size:0.82rem; line-height:1.6;
}

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    gap:4px !important; background:var(--bg-card) !important;
    border-radius:var(--radius-sm) !important; padding:4px !important;
    border:1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    background:transparent !important; border-radius:8px !important;
    padding:0.5rem 1rem !important; font-size:0.82rem !important;
    font-weight:600 !important; color:var(--text-muted) !important;
    border:none !important; transition:all 0.18s ease !important;
}
.stTabs [data-baseweb="tab"]:hover { background:rgba(99,130,202,0.1) !important; color:var(--blue) !important; }
.stTabs [aria-selected="true"] { background:linear-gradient(135deg,#002147,#003d7a) !important; color:white !important; box-shadow:0 2px 10px rgba(0,33,71,0.5) !important; }

/* SELECTBOX / SLIDERS */
[data-testid="stSelectbox"] > div > div { background:var(--bg-card) !important; border:1px solid var(--border) !important; border-radius:var(--radius-sm) !important; }
.stSlider [data-baseweb="slider"] { padding:0.5rem 0; }

/* DATAFRAME */
.dataframe { font-size:0.78rem !important; border-radius:var(--radius-sm) !important; }
[data-testid="stDataFrame"] { border:1px solid var(--border) !important; border-radius:var(--radius-sm) !important; overflow:hidden !important; }

/* FOOTER */
.gallup-footer {
    background:linear-gradient(100deg,#001224 0%,#001e3d 100%);
    border:1px solid var(--border); border-top:2px solid #e4002b;
    border-radius:var(--radius-card); padding:1.1rem 1.5rem;
    display:flex; align-items:center; justify-content:space-between;
    gap:1rem; margin-top:2rem; font-size:0.72rem; color:var(--text-muted); line-height:1.7;
}
.gallup-footer strong { color:var(--text); }
.gallup-footer a { color:var(--green); text-decoration:none; }

.js-plotly-plot .plotly { background:transparent !important; }
</style>
""", unsafe_allow_html=True)

# ── Load date range dynamically from actual data ──────────────────────────────
from data_utils import get_date_range
MIN_YEAR, MAX_YEAR, LATEST_MONTH = get_date_range()
DATA_PERIOD = f"{MIN_YEAR} – {LATEST_MONTH} {MAX_YEAR}"

# ── Top Bar (date range from data, not hardcoded) ─────────────────────────────
st.markdown(f"""
<div class="topbar">
    <div class="topbar-brand">
        <div class="topbar-logo">
            <img src="https://www.gallup.com.pk/Logo.png" alt="Gallup Pakistan" />
        </div>
        <div class="topbar-divider"></div>
        <div class="topbar-title">
            <b>Gallup Pakistan</b> · Digital Analytics<br>
            Pakistan Bureau of Statistics · External Trade Statistics
        </div>
    </div>
    <div class="topbar-meta">
        Data Period: <b>{DATA_PERIOD}</b><br>
        Source: <b style="color:#60a5fa;">PBS External Trade</b>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Pages ─────────────────────────────────────────────────────────────────────
from pages_module import overview, exports, imports, balance, products, trends, forecaster

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
        <div style="background:white;border-radius:6px;padding:4px 10px;display:inline-block;margin-bottom:8px;">
            <img src="https://www.gallup.com.pk/Logo.png" alt="Gallup Pakistan" style="height:38px;display:block;" />
        </div>
        <div class="sb-label">Trade Intelligence</div>
        <div class="sb-sub">PBS External Trade {DATA_PERIOD}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">Navigation</div>', unsafe_allow_html=True)

    PAGE_LABELS = [
        "🏠  Overview & KPIs",
        "📦  Exports Deep Dive",
        "🛒  Imports Deep Dive",
        "⚖️  Trade Balance",
        "🔬  Product Intelligence",
        "📈  Trends & Patterns",
        "🔮  Scenario Forecaster",
    ]
    PAGE_KEYS = ["overview","exports","imports","balance","products","trends","forecaster"]

    selected_label = st.radio("Navigation", PAGE_LABELS, index=0, label_visibility="collapsed")
    selected_page  = PAGE_KEYS[PAGE_LABELS.index(selected_label)]

    st.markdown(f"""
    <div class="sidebar-info">
        <strong>Data Source</strong><br>
        Pakistan Bureau of Statistics<br>
        External Trade Statistics<br>
        <br>
        <strong>Data Period</strong><br>
        {DATA_PERIOD}<br>
        <br>
        <strong>Compiled By</strong><br>
        <span style="color:#e4002b;font-weight:700;">Gallup Pakistan</span><br>
        Digital Analytics Unit<br>
        <br>
        <a href="https://www.gallup.com.pk" target="_blank"
           style="color:#10d9a0;text-decoration:none;font-weight:600;">
            🌐 www.gallup.com.pk
        </a>
    </div>
    """, unsafe_allow_html=True)

# ── Route ─────────────────────────────────────────────────────────────────────
page = selected_page
if   page == "overview":   overview.render()
elif page == "exports":    exports.render()
elif page == "imports":    imports.render()
elif page == "balance":    balance.render()
elif page == "products":   products.render()
elif page == "trends":     trends.render()
elif page == "forecaster": forecaster.render()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="gallup-footer">
    <img src="https://www.gallup.com.pk/Logo.png" alt="Gallup Pakistan"
         style="height:42px;background:white;padding:5px 10px;border-radius:6px;flex-shrink:0;" />
    <div>
        <strong>🇵🇰 Pakistan Trade Intelligence Dashboard</strong><br>
        Data Source: Pakistan Bureau of Statistics · External Trade Statistics · {DATA_PERIOD}<br>
        All values in USD Thousands unless stated otherwise
    </div>
    <div style="text-align:right;">
        Analysed &amp; Visualised by<br>
        <strong>Gallup Pakistan Digital Analytics</strong><br>
        <a href="https://www.gallup.com.pk" target="_blank">www.gallup.com.pk</a>
    </div>
</div>
""", unsafe_allow_html=True)
