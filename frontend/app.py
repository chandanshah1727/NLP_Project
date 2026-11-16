"""Smart Waste Management System application shell and navigation."""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from frontend import theme
from frontend.api_client import APIError, health

st.set_page_config(page_title="Smart Waste Management System", page_icon="♻️", layout="wide", initial_sidebar_state="expanded")
theme.install_theme()

logo_path = Path(__file__).resolve().parent / "assets" / "smart_waste_management_logo.svg"
st.logo(str(logo_path), size="large")

pages = [
    st.Page("pages/overview.py", title="Overview", icon=":material/space_dashboard:", default=True),
    st.Page("pages/scanner.py", title="AI Waste Scanner", icon=":material/center_focus_strong:"),
    st.Page("pages/records.py", title="Waste Records", icon=":material/table_view:"),
    st.Page("pages/monitoring.py", title="Campus Monitoring", icon=":material/location_city:"),
    st.Page("pages/analytics.py", title="Analytics", icon=":material/analytics:"),
    st.Page("pages/reports.py", title="Reports", icon=":material/description:"),
    st.Page("pages/alerts.py", title="Alerts", icon=":material/notifications_active:"),
]

page = st.navigation(pages, position="sidebar")

with st.sidebar:
    st.divider()
    st.markdown('<div class="section-kicker">System status</div>', unsafe_allow_html=True)
    try:
        status = health()
        checks = [("Backend API", status.get("status") == "ok"),
                  ("AI model", status.get("model_configured") is True),
                  ("Database", status.get("database_connected") is True)]
    except APIError:
        checks = [("Backend API", False), ("AI model", False), ("Database", False)]
    for label, ready in checks:
        text = "Operational" if ready else "Unavailable"
        tone = "status-ok" if ready else "status-bad"
        mark = "●" if ready else "●"
        st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;margin:.5rem 0;font-size:.82rem"><span>{label}</span><span class="status-pill {tone}">{mark} {text}</span></div>', unsafe_allow_html=True)
    st.divider()
    st.caption("CSE472 · Application v1.0.0")

page.run()
