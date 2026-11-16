"""Search, inspect, edit, export, and delete recorded waste events."""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
from frontend.api_client import delete_record, get_record, get_records, update_record
from frontend.components import LOCATIONS, WASTE_BINS, api_error, empty_state, fetch_all_records, filter_panel, records_frame

def render():
    st.markdown('<div class="page-eyebrow">Record management</div><h1>Waste Records</h1><div class="page-description">Search and manage the campus events recorded through the AI scanner.</div>', unsafe_allow_html=True)
    filters=filter_panel("records")
    if filters is None: return
    a,b,c=st.columns([2,1,1])
    search=a.text_input("Search records",placeholder="Record ID, category, location, or selected bin",key="record_search")
    status=b.selectbox("Segregation status",["All statuses","Correct","Incorrect"],key="record_status")
    page_size=c.selectbox("Rows per page",[10,25,50,100],index=1,key="record_page_size")
    params={**filters,"limit":page_size}
    if search.strip(): params["search"]=search.strip()
    if status!="All statuses": params["status"]=status.lower()
    signature=tuple(sorted(params.items()))
    if st.session_state.get("record_filter_signature") != signature:
        st.session_state["record_filter_signature"]=signature
        st.session_state["record_offset"]=0
    offset=st.session_state.get("record_offset",0)
    response=api_error(get_records,**params,offset=offset)
    if response is None: return
    total=response["total"]
    if total and offset>=total:
        st.session_state["record_offset"]=max(0,((total-1)//page_size)*page_size)
        st.rerun()
    records=response.get("items",[])
    if not records:
        empty_state("No records match the selected search and filters.")
        return

    sort_label=st.radio("Sort this page",["Newest first","Oldest first","Highest confidence","Lowest confidence","Category A–Z"],horizontal=True)
    frame=records_frame(records)
    if sort_label=="Oldest first": frame=frame.sort_values("created_at",ascending=True)
    elif sort_label=="Highest confidence": frame=frame.sort_values("confidence",ascending=False)
    elif sort_label=="Lowest confidence": frame=frame.sort_values("confidence",ascending=True)
    elif sort_label=="Category A–Z": frame=frame.sort_values("waste_category",ascending=True)
    view=frame[["id","waste_category","waste_type","confidence","location","selected_bin","segregation_status","created_at"]].rename(columns={
        "id":"ID","waste_category":"Waste category","waste_type":"Waste type","confidence":"AI confidence %",
        "location":"Location","selected_bin":"Selected bin","segregation_status":"Segregation","created_at":"Date and time"})
    st.caption(f"Showing {offset+1}–{offset+len(records)} of {total:,} records")
    st.dataframe(view,width="stretch",hide_index=True,column_config={
        "ID":st.column_config.NumberColumn(format="%d"),
        "AI confidence %":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%.1f%%"),
        "Segregation":st.column_config.TextColumn(help="A recorded bin decision compared with the configured recommendation."),
    })

    page_count=max(1,(total+page_size-1)//page_size)
    prev,next_=st.columns([1,1])
    if prev.button("Previous page",disabled=offset<=0,icon=":material/arrow_back:"):
        st.session_state["record_offset"]=max(0,offset-page_size); st.rerun()
    if next_.button("Next page",disabled=offset+page_size>=total,icon=":material/arrow_forward:"):
        st.session_state["record_offset"]=offset+page_size; st.rerun()

    st.markdown("### Export filtered records")
    csv_records=fetch_all_records(**{**filters,**({"search":search.strip()} if search.strip() else {}),**({"status":status.lower()} if status!="All statuses" else {})})
    if csv_records is not None:
        csv_frame=pd.DataFrame(csv_records)
        st.download_button("Download filtered CSV",csv_frame.to_csv(index=False).encode("utf-8-sig"),
                           file_name="smart-waste-management-records.csv",mime="text/csv",icon=":material/download:")

    st.markdown("### Record details and actions")
    selected_id=st.selectbox("Choose a record",[r["id"] for r in records],format_func=lambda rid:f"Record #{rid} · {next((r['waste_category'].title() for r in records if r['id']==rid),'Waste')} · {next((r['location'] for r in records if r['id']==rid),'')}")
    detail=api_error(get_record,selected_id)
    if detail is None: return
    with st.container(border=True):
        left,right=st.columns([1,2])
        with left:
            st.markdown(f"#### Record #{detail['id']}")
            st.write(f"**Category:** {detail['waste_category'].title()} · {detail['waste_type']}")
            st.write(f"**AI confidence:** {detail['confidence']:.2f}%")
            st.write(f"**Recommended bin:** {detail['recommended_bin']}")
            st.write(f"**Recorded:** {detail['created_at']}")
        with right:
            with st.form(f"edit_record_{selected_id}"):
                col1,col2=st.columns(2)
                new_location=col1.selectbox("Campus location",LOCATIONS,index=LOCATIONS.index(detail["location"]))
                bins=WASTE_BINS if detail["selected_bin"] in WASTE_BINS else WASTE_BINS+[detail["selected_bin"]]
                new_bin=col2.selectbox("Actual bin used",bins,index=bins.index(detail["selected_bin"]))
                new_notes=st.text_input("Notes",value=detail.get("notes") or "",max_chars=500)
                current_weight=detail.get("weight_kg") or 0.0
                new_weight=st.number_input("Measured weight in kg (optional)",min_value=0.0,value=float(current_weight),step=.1)
                submitted=st.form_submit_button("Save changes",type="primary",icon=":material/save:")
            if submitted:
                result=api_error(update_record,selected_id,{"location":new_location,"selected_bin":new_bin,"notes":new_notes or None,"weight_kg":new_weight or None})
                if result: st.success("Record updated and segregation compliance recalculated."); st.rerun()
    with st.expander("Delete this record"):
        st.warning("This permanently removes the record from the project database.")
        confirmed=st.checkbox(f"Confirm deletion of record #{selected_id}",key=f"delete_confirm_{selected_id}")
        if st.button("Delete record",disabled=not confirmed,type="secondary",icon=":material/delete:"):
            if api_error(delete_record,selected_id): st.success(f"Record #{selected_id} deleted."); st.rerun()

if __name__ == "__main__": render()
