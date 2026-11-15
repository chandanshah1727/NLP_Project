"""Executive overview dashboard backed exclusively by API data."""
from datetime import date, datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from frontend.api_client import get_categories, get_locations, get_records, get_summary, get_trends
from frontend.components import api_error, empty_state, filter_panel, metric_row, records_frame, CATEGORY_COLORS
from frontend.theme import chart_layout

def render():
    today = date.today()
    left, right = st.columns([3.2, 1.8], vertical_alignment="top")
    with left:
        st.markdown('<h1>Overview</h1><div class="page-description">A clear picture of recorded waste activity and segregation performance across campus.</div>', unsafe_allow_html=True)
    with right:
        st.caption(f"Today · {today.strftime('%A, %d %B %Y')}")
        if st.button("Refresh data", icon=":material/refresh:", use_container_width=True):
            st.session_state["overview_refresh_time"] = datetime.now().strftime("%H:%M:%S")
            st.rerun()
        st.caption(f"Last data refresh · {st.session_state.get('overview_refresh_time','On page load')}")

    filters = filter_panel("overview")
    if filters is None:
        return
    summary = api_error(get_summary, **filters)
    if summary is None:
        return
    if summary.get("total_records", 0) == 0:
        empty_state("There are no recorded waste events for this period yet. Start with an image classification.")
        return

    metric_row([
        ("Total waste records", f"{summary['total_records']:,}", "Recorded waste events in the selected period"),
        ("Recyclable records", f"{summary['recyclable_records']:,}", "Cardboard, glass, metal, paper, and plastic records"),
        ("Segregation compliance", f"{summary['compliance_percentage']:.1f}%", "Share of recorded choices matching the recommended bin"),
        ("Average AI confidence", f"{summary['average_confidence']:.1f}%", "Mean model confidence for saved predictions"),
    ])
    st.progress(summary["compliance_percentage"] / 100, text=f"Recorded segregation compliance · {summary['compliance_percentage']:.1f}%")

    category_data = summary.get("category_distribution", {})
    trend_data = api_error(get_trends, **filters, days=90)
    location_filters = {k:v for k,v in filters.items() if k != "location"}
    location_data = api_error(get_locations, **location_filters)
    first, second = st.columns([1, 1.25], gap="large")
    with first, st.container(border=True):
        st.subheader("Waste composition")
        if category_data:
            fig = px.pie(names=[x.title() for x in category_data], values=list(category_data.values()),
                         hole=.66, color=list(category_data), color_discrete_map=CATEGORY_COLORS)
            fig.update_traces(textposition="inside", textinfo="percent", marker=dict(line=dict(color="white", width=2)))
            fig.update_traces(hovertemplate="%{label}<br>Records: %{value}<br>Share: %{percent}<extra></extra>")
            fig.update_layout(showlegend=True, legend_title_text="Waste category", height=330, margin=dict(t=12,b=8,l=8,r=8),
                              paper_bgcolor="rgba(0,0,0,0)", font=dict(family="DM Sans, sans-serif", color="#43574d"))
            st.plotly_chart(fig, width="stretch", config={"displayModeBar":False})
        else:
            st.caption("Category data will appear after records are saved.")

    with second, st.container(border=True):
        st.subheader("Daily waste activity")
        trend_frame = pd.DataFrame(trend_data or [])
        if not trend_frame.empty:
            fig = px.area(trend_frame, x="date", y="records", markers=True,
                          labels={"date":"Date", "records":"Recorded events"})
            fig.update_traces(line_color="#23815a", fillcolor="rgba(35,129,90,.14)", marker_color="#23815a")
            st.plotly_chart(chart_layout(fig, 330), width="stretch", config={"displayModeBar":False})
        else:
            st.caption("No activity is available for the selected dates.")

    first, second = st.columns(2, gap="large")
    with first, st.container(border=True):
        st.subheader("Campus location comparison")
        location_frame = pd.DataFrame(location_data or [])
        if filters.get("location") and not location_frame.empty:
            location_frame = location_frame[location_frame["location"] == filters["location"]]
        if not location_frame.empty:
            location_frame = location_frame[location_frame.total_records > 0]
            if not location_frame.empty:
                fig = px.bar(location_frame.sort_values("total_records"), x="total_records", y="location", orientation="h",
                             text="total_records", labels={"total_records":"Records", "location":""},
                             color_discrete_sequence=["#23815a"], hover_data=["compliance_percentage","incorrect_records"])
                fig.update_traces(textposition="outside", cliponaxis=False)
                st.plotly_chart(chart_layout(fig, 280), width="stretch", config={"displayModeBar":False})
            else:
                st.caption("No location records match the selected filters.")

    with second, st.container(border=True):
        st.subheader("Correct and incorrect segregation")
        fig = px.bar(x=["Correct","Incorrect"], y=[summary["correct_records"],summary["incorrect_records"]],
                     color=["Correct","Incorrect"], color_discrete_map={"Correct":"#278554","Incorrect":"#c76758"},
                     labels={"x":"Decision","y":"Recorded events"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(chart_layout(fig, 280), width="stretch", config={"displayModeBar":False})

    st.markdown("### Recent waste activity")
    recent = api_error(get_records, **filters, limit=8, offset=0)
    recent_frame = records_frame(recent.get("items",[]) if recent else [])
    if recent_frame.empty:
        st.caption("No recent activity is available.")
    else:
        view = recent_frame[["id","waste_category","waste_type","confidence","location","selected_bin","segregation_status","created_at"]].rename(columns={
            "id":"ID","waste_category":"Category","waste_type":"Waste type","confidence":"AI confidence %",
            "location":"Location","selected_bin":"Selected bin","segregation_status":"Segregation","created_at":"Recorded at"})
        st.dataframe(view, width="stretch", hide_index=True, column_config={"ID":st.column_config.NumberColumn(format="%d"),"AI confidence %":st.column_config.NumberColumn(format="%.1f%%")})
        st.page_link("pages/records.py", label="View all waste records", icon=":material/arrow_forward:")

if __name__ == "__main__": render()
