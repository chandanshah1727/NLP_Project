"""Shared visual system for Smart Waste Management System."""
import streamlit as st

PRODUCT_NAME = "Smart Waste Management System"
PRODUCT_SUBTITLE = "CAMPUS WASTE INTELLIGENCE"
APP_VERSION = "1.0.0"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --forest:#153b2e; --emerald:#21845a; --mint:#e7f2eb; --cream:#f6f7f2; --ink:#1c2b25; --muted:#718078; --line:#e3e9e3; --amber:#b7791f; --red:#ba4b45; }
.stApp { background:var(--cream); color:var(--ink); font-family:'DM Sans','Segoe UI',sans-serif; }
main .block-container { max-width:1500px; padding-top:1.6rem; padding-bottom:2.5rem; }
h1,h2,h3 { font-family:'Manrope','Segoe UI',sans-serif; letter-spacing:-.025em; color:var(--forest); }
h1 { font-size:2rem !important; font-weight:750 !important; }
h2 { font-size:1.25rem !important; font-weight:700 !important; }
h3 { font-size:1.04rem !important; font-weight:700 !important; }
[data-testid="stSidebar"] { background:var(--forest); border-right:1px solid #254a3d; }
[data-testid="stSidebar"] * { color:#eef5ef; }
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] { box-sizing:border-box; height:108px !important; min-height:108px !important; overflow:visible !important; }
[data-testid="stSidebar"] img[data-testid="stSidebarLogo"] { display:block !important; width:258px !important; height:90px !important; max-width:calc(100% - 42px) !important; max-height:none !important; object-fit:contain !important; object-position:left center !important; }
[data-testid="stSidebarCollapseButton"] { position:absolute !important; top:0 !important; right:0 !important; z-index:2; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:#a9c0b3; }
[data-testid="stSidebar"] hr { border-color:#315647; }
[data-testid="stSidebarNav"] { padding-top:.55rem; }
[data-testid="stSidebarNav"] a { border-radius:8px; margin:.16rem .3rem; transition:background .15s ease; }
[data-testid="stSidebarNav"] a:hover { background:#244b3c; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background:#2a614a; color:white; font-weight:700; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:12px; padding:1rem 1.1rem; box-shadow:0 3px 12px rgba(21,59,46,.045); }
[data-testid="stMetricLabel"] { color:var(--muted); font-weight:600; }
[data-testid="stMetricValue"] { color:var(--forest); font-family:'Manrope','Segoe UI',sans-serif; font-weight:750; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--line); border-radius:12px; background:#fff; box-shadow:0 3px 12px rgba(21,59,46,.035); }
div[data-testid="stButton"] button[kind="primary"] { background:var(--emerald); border-color:var(--emerald); color:white; border-radius:8px; font-weight:650; }
div[data-testid="stButton"] button { border-radius:8px; transition:all .15s ease; }
div[data-testid="stButton"] button:hover { border-color:var(--emerald); color:var(--emerald); }
[data-testid="stDownloadButton"] button { border-radius:8px; font-weight:600; }
[data-testid="stTextInput"] input,[data-testid="stSelectbox"] div[data-baseweb="select"],[data-testid="stDateInput"] input { border-radius:8px; }
[data-testid="stProgress"] > div > div { background:var(--emerald); }
.brand-name { font:750 .92rem 'Manrope','Segoe UI',sans-serif; line-height:1.15; letter-spacing:-.02em; color:white; }
.brand-subtitle { font:600 .58rem 'DM Sans','Segoe UI',sans-serif; letter-spacing:.1em; color:#a9c0b3; margin-top:1px; }
.page-eyebrow { color:var(--emerald); text-transform:uppercase; letter-spacing:.13em; font-size:.68rem; font-weight:750; margin-bottom:.3rem; }
.top-product-name { color:var(--forest); text-align:right; font:750 .88rem 'Manrope','Segoe UI',sans-serif; line-height:1.25; margin:0 0 .35rem; }
.page-description { color:var(--muted); margin-top:-.45rem; margin-bottom:1.2rem; font-size:.94rem; }
.section-kicker { color:var(--muted); font-size:.76rem; text-transform:uppercase; letter-spacing:.1em; font-weight:700; }
.status-pill { display:inline-flex; align-items:center; gap:.38rem; border-radius:99px; padding:.24rem .62rem; font-size:.75rem; font-weight:700; }
.status-ok { color:#246b45; background:#e7f3e9; }
.status-warn { color:#946114; background:#fbf1dc; }
.status-bad { color:#a23e38; background:#fae9e6; }
.subtle-note { color:var(--muted); background:#edf2ed; padding:.72rem .9rem; border-radius:8px; font-size:.86rem; }
.scanner-recommendation { border-left:4px solid var(--emerald); padding:.8rem 1rem; background:#edf5ef; border-radius:0 8px 8px 0; }
.location-title { color:var(--forest); font:750 1.03rem 'Manrope','Segoe UI',sans-serif; }
@media (max-width: 900px) { main .block-container { padding:1rem .8rem 2rem; } h1 { font-size:1.65rem !important; } }
</style>
"""

def install_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

def chart_layout(fig, height: int = 310):
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=12, t=30, b=12), font=dict(family="DM Sans, sans-serif", color="#43574d"),
        hoverlabel=dict(bgcolor="white", font_color="#1c2b25"),
        xaxis=dict(showgrid=False, zeroline=False, linecolor="#e3e9e3"),
        yaxis=dict(showgrid=True, gridcolor="#edf0eb", zeroline=False, linecolor="#e3e9e3"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig
