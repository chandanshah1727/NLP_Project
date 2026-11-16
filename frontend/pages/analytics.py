"""Detailed records-based waste and compliance analysis."""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import plotly.express as px
import streamlit as st
from frontend.api_client import get_categories, get_locations, get_summary, get_trends
from frontend.components import CATEGORY_COLORS, api_error, empty_state, fetch_all_records, filter_panel, records_frame, metric_row
from frontend.theme import chart_layout

def render():
    st.markdown('<div class="page-eyebrow">Evidence-based insights</div><h1>Analytics</h1><div class="page-description">Understand category mix, activity patterns, model confidence, and recorded segregation performance.</div>',unsafe_allow_html=True)
    filters=filter_panel("analytics")
    if filters is None: return
    granularity=st.radio("Activity interval",["Daily","Weekly","Monthly"],horizontal=True,key="analytics_interval")
    summary=api_error(get_summary,**filters)
    if summary is None: return
    if not summary["total_records"]:
        empty_state("There are no records in the selected period to analyze.")
        return
    metric_row([
        ("Total events",f"{summary['total_records']:,}","Saved records in this selection"),
        ("Correct segregation",f"{summary['compliance_percentage']:.1f}%","Recorded bin choices matching recommendations"),
        ("Incorrect decisions",f"{summary['incorrect_records']:,}","Recorded bin choices needing review"),
        ("Most recorded category",max(summary["category_distribution"],key=summary["category_distribution"].get).title(),"Derived from the selected records"),
    ])
    categories=api_error(get_categories,**filters)
    location_filters={k:v for k,v in filters.items() if k!="location"}
    locations=api_error(get_locations,**location_filters)
    daily=api_error(get_trends,**filters,days=365)
    records=fetch_all_records(**filters)

    first,second=st.columns([1,1],gap="large")
    with first,st.container(border=True):
        st.subheader("Waste categories")
        counts=(categories or {}).get("categories",{})
        if counts:
            fig=px.pie(names=[x.title() for x in counts],values=list(counts.values()),hole=.62,
                       color=list(counts),color_discrete_map=CATEGORY_COLORS)
            fig.update_traces(textposition="inside",textinfo="percent",marker=dict(line=dict(color="white",width=2)))
            fig.update_layout(showlegend=True,legend_title_text="Category",height=320,paper_bgcolor="rgba(0,0,0,0)",font=dict(family="DM Sans, sans-serif"))
            st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})
    with second,st.container(border=True):
        st.subheader("Waste types")
        types=(categories or {}).get("types",{})
        if types:
            fig=px.bar(x=list(types.values()),y=list(types.keys()),orientation="h",text=list(types.values()),
                       labels={"x":"Records","y":"Waste type"},color_discrete_sequence=["#4b8b69"])
            fig.update_traces(textposition="outside")
            st.plotly_chart(chart_layout(fig,320),width="stretch",config={"displayModeBar":False})

    trend_frame=pd.DataFrame(daily or [])
    if not trend_frame.empty:
        trend_frame["date"]=pd.to_datetime(trend_frame["date"])
        activity=trend_frame.set_index("date")["records"]
        rule={"Daily":"D","Weekly":"W-MON","Monthly":"MS"}[granularity]
        aggregated=activity.resample(rule).sum().rename("records").reset_index()
        with st.container(border=True):
            st.subheader(f"{granularity} waste activity")
            fig=px.area(aggregated,x="date",y="records",markers=granularity=="Daily",
                        labels={"date":"Period","records":"Recorded events"})
            fig.update_traces(line_color="#21845a",fillcolor="rgba(33,132,90,.14)")
            st.plotly_chart(chart_layout(fig,330),width="stretch",config={"displayModeBar":False})

    location_frame=pd.DataFrame(locations or [])
    if filters.get("location") and not location_frame.empty:
        location_frame=location_frame[location_frame.location==filters["location"]]
    location_frame=location_frame[location_frame.total_records>0] if not location_frame.empty else location_frame
    if not location_frame.empty:
        a,b=st.columns(2,gap="large")
        with a,st.container(border=True):
            st.subheader("Recorded events by location")
            fig=px.bar(location_frame.sort_values("total_records"),x="total_records",y="location",orientation="h",text="total_records",
                       labels={"total_records":"Events","location":""},color_discrete_sequence=["#4385bd"],hover_data=["compliance_percentage"])
            st.plotly_chart(chart_layout(fig,300),width="stretch",config={"displayModeBar":False})
        with b,st.container(border=True):
            st.subheader("Location compliance")
            fig=px.bar(location_frame.sort_values("compliance_percentage"),x="compliance_percentage",y="location",orientation="h",text=location_frame.sort_values("compliance_percentage")["compliance_percentage"].map(lambda v:f"{v:.1f}%"),range_x=[0,100],
                       labels={"compliance_percentage":"Correct decisions (%)","location":""},color_discrete_sequence=["#21845a"])
            st.plotly_chart(chart_layout(fig,300),width="stretch",config={"displayModeBar":False})

    frame=records_frame(records or [])
    if frame.empty:
        return
    frame["created_at"]=pd.to_datetime(frame["created_at"])
    frame["recorded_day"]=frame["created_at"].dt.floor("D")
    compliance=frame.groupby("recorded_day")["correct_segregation"].mean().mul(100).rename("compliance").reset_index()
    first,second=st.columns(2,gap="large")
    with first,st.container(border=True):
        st.subheader("Recorded compliance trend")
        if len(compliance)>1:
            fig=px.line(compliance,x="recorded_day",y="compliance",markers=True,range_y=[0,100],labels={"recorded_day":"Date","compliance":"Correct decisions (%)"})
            fig.update_traces(line_color="#21845a")
            st.plotly_chart(chart_layout(fig,300),width="stretch",config={"displayModeBar":False})
        else:
            st.caption("A compliance trend needs records from more than one day.")
    with second,st.container(border=True):
        st.subheader("AI confidence distribution")
        fig=px.histogram(frame,x="confidence",nbins=12,range_x=[0,100],labels={"confidence":"Model confidence (%)","count":"Saved predictions"},color_discrete_sequence=["#8870b7"])
        st.plotly_chart(chart_layout(fig,300),width="stretch",config={"displayModeBar":False})
    st.caption("Trends count saved records; confidence is the model score stored at classification time. Neither indicates physical waste weight.")

if __name__ == "__main__": render()
