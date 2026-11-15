"""Reusable Streamlit components and API-backed filters."""
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from frontend.api_client import APIError, get

LOCATIONS = ["Hostel", "Canteen", "Academic Block", "Library"]
CATEGORIES = ["battery", "cardboard", "glass", "metal", "organic", "paper", "plastic", "textile", "trash"]
WASTE_BINS = ["Recyclable", "Biodegradable", "E-waste Collection", "Textile Collection", "Residual Waste"]
CATEGORY_COLORS = {"battery":"#8870b7", "cardboard":"#b4865a", "glass":"#50a2a0", "metal":"#768795", "organic":"#5e9c69", "paper":"#89a95d", "plastic":"#4385bd", "textile":"#d3924f", "trash":"#69736d"}

def api_error(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except APIError as exc:
        st.error(str(exc))
        return None

def page_header(section: str, title: str, description: str, right=None):
    left, *rest = st.columns([4, 1.15]) if right is not None else (st.container(),)
    with left:
        st.markdown(f'<div class="page-eyebrow">{section}</div><h1>{title}</h1><div class="page-description">{description}</div>', unsafe_allow_html=True)
    if right is not None and rest:
        with rest[0]: right()

def filter_panel(key: str, *, include_location: bool = True, include_category: bool = True, expanded: bool = True):
    columns = 2 + int(include_location) + int(include_category)
    with st.container(border=True):
        cols = st.columns(columns)
        start = cols[0].date_input("From", date.today()-timedelta(days=30), key=f"{key}_from")
        end = cols[1].date_input("To", date.today(), key=f"{key}_to")
        params = {"start":start.isoformat(), "end":end.isoformat()}
        idx = 2
        if include_location:
            location = cols[idx].selectbox("Campus location", ["All locations"]+LOCATIONS, key=f"{key}_location")
            idx += 1
            if location != "All locations": params["location"] = location
        if include_category:
            category = cols[idx].selectbox("Waste category", ["All categories"]+CATEGORIES, key=f"{key}_category")
            if category != "All categories": params["category"] = category
    if start > end:
        st.error("Choose a start date that is on or before the end date.")
        return None
    return params

def empty_state(message: str = "No records match these filters yet."):
    st.info(message)
    st.page_link("pages/scanner.py", label="Open AI Waste Scanner", icon=":material/center_focus_strong:")

def metric_row(metrics: list[tuple[str, str, str]]):
    cols = st.columns(len(metrics))
    for column, (label, value, help_text) in zip(cols, metrics):
        column.metric(label, value, help=help_text)

def status_class(severity: str) -> str:
    return {"high":"status-bad", "incorrect":"status-bad", "medium":"status-warn", "low":"status-warn", "correct":"status-ok", "ok":"status-ok"}.get(severity.lower(), "status-warn")

def status_badge(label: str, tone: str = "ok"):
    cls = status_class(tone)
    st.markdown(f'<span class="status-pill {cls}">{label}</span>', unsafe_allow_html=True)

def fetch_all_records(**filters) -> list[dict] | None:
    items = []
    offset = 0
    page_size = 500
    while True:
        response = api_error(get, "/records", **filters, limit=page_size, offset=offset)
        if response is None:
            return None
        batch = response.get("items", [])
        items.extend(batch)
        offset += len(batch)
        if not batch or offset >= response.get("total", 0):
            return items

def records_frame(records: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    frame["segregation_status"] = frame["correct_segregation"].map({True:"Correct", False:"Incorrect"})
    frame["confidence"] = pd.to_numeric(frame["confidence"], errors="coerce")
    return frame
