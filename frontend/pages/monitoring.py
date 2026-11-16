"""Database-derived monitoring view for the four campus locations."""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import plotly.express as px
import streamlit as st
from frontend.api_client import get_locations, get_records
from frontend.components import LOCATIONS, api_error, filter_panel, CATEGORY_COLORS
from frontend.theme import chart_layout

def render():
    st.markdown('<div class="page-eyebrow">Campus performance</div><h1>Campus Monitoring</h1><div class="page-description">Compare recorded activity and segregation decisions across the four supported campus locations.</div>',unsafe_allow_html=True)
    st.markdown('<div class="subtle-note">Monitoring is based on submitted records. There are no connected bin sensors, fill-level readings, GPS tracking, or inferred waste weights.</div>',unsafe_allow_html=True)
    filters=filter_panel("monitoring",include_location=False)
    if filters is None: return
    locations=api_error(get_locations,**filters)
    if locations is None: return
    location_frame=pd.DataFrame(locations)
    cols=st.columns(4)
    for col,location in zip(cols,locations):
        common=max(location["category_distribution"],key=location["category_distribution"].get).title() if location["category_distribution"] else "No records yet"
        with col,st.container(border=True):
            st.markdown(f'<div class="location-title">{location["location"]}</div>',unsafe_allow_html=True)
            st.metric("Recorded events",f"{location['total_records']:,}")
            st.metric("Segregation compliance",f"{location['compliance_percentage']:.1f}%")
            st.caption(f"{location['incorrect_records']} incorrect decisions · Most common: {common}")
    active=location_frame[location_frame.total_records>0] if not location_frame.empty else location_frame
    if active.empty:
        st.info("No location data is available for these filters yet.")
        return

    st.markdown("### Location comparison")
    left,right=st.columns(2,gap="large")
    with left,st.container(border=True):
        st.subheader("Segregation compliance")
        fig=px.bar(active.sort_values("compliance_percentage"),x="compliance_percentage",y="location",orientation="h",
                   range_x=[0,100],text=active.sort_values("compliance_percentage")["compliance_percentage"].map(lambda x:f"{x:.1f}%"),
                   color_discrete_sequence=["#21845a"],labels={"compliance_percentage":"Compliance","location":""},hover_data=["total_records","incorrect_records"])
        st.plotly_chart(chart_layout(fig,300),width="stretch",config={"displayModeBar":False})
    with right,st.container(border=True):
        st.subheader("Recorded events")
        fig=px.bar(active.sort_values("total_records"),x="total_records",y="location",orientation="h",text="total_records",
                   color_discrete_sequence=["#578b70"],labels={"total_records":"Events","location":""},hover_data=["compliance_percentage","incorrect_records"])
        st.plotly_chart(chart_layout(fig,300),width="stretch",config={"displayModeBar":False})

    composition=[]
    for row in locations:
        for category,count in row["category_distribution"].items(): composition.append({"Location":row["location"],"Category":category.title(),"Records":count})
    if composition:
        with st.container(border=True):
            st.subheader("Waste composition by location")
            frame=pd.DataFrame(composition)
            fig=px.bar(frame,x="Location",y="Records",color="Category",barmode="stack",color_discrete_map={k.title():v for k,v in CATEGORY_COLORS.items()},
                       hover_data={"Location":True,"Category":True,"Records":True})
            st.plotly_chart(chart_layout(fig,330),width="stretch",config={"displayModeBar":False})

    st.markdown("### Inspect one campus location")
    selected=st.radio("Select location",LOCATIONS,horizontal=True,key="monitor_selected_location")
    selected_data=next((row for row in locations if row["location"]==selected),None)
    if selected_data:
        a,b,c=st.columns(3)
        a.metric("Recorded events",selected_data["total_records"])
        b.metric("Correct segregation",f"{selected_data['compliance_percentage']:.1f}%")
        c.metric("Incorrect decisions",selected_data["incorrect_records"])
        records=api_error(get_records,**filters,location=selected,limit=10,offset=0)
        if records and records["items"]:
            st.dataframe(pd.DataFrame(records["items"])[["id","waste_category","confidence","selected_bin","correct_segregation","created_at"]],width="stretch",hide_index=True)
        else:
            st.caption("No records for this location in the chosen period.")

if __name__ == "__main__": render()
