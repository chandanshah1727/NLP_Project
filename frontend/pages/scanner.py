"""Image classification and user-confirmed segregation recording workflow."""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from frontend.api_client import APIError, create_record, predict_image
from frontend.components import LOCATIONS, WASTE_BINS, api_error, page_header

def render():
    page_header("AI-powered classification", "AI Waste Scanner", "Upload one clear waste item, review the model recommendation, then record the bin decision.")
    st.markdown('<div class="subtle-note">The trained EfficientNetB0 model classifies the uploaded item. This does not verify physical disposal.</div>', unsafe_allow_html=True)
    saved = st.session_state.get("scanner_saved")
    if saved:
        st.success(f"Record #{saved['record_id']} saved · {saved['segregation']}")
        a,b=st.columns(2)
        if a.button("Start another scan", type="primary", icon=":material/center_focus_strong:"):
            st.session_state["scanner_cycle"] = st.session_state.get("scanner_cycle",0)+1
            st.session_state.pop("scanner_saved",None)
            st.session_state.pop("scanner_prediction",None)
            st.rerun()
        b.page_link("pages/records.py", label="Open Waste Records", icon=":material/table_view:")
        return

    cycle = st.session_state.get("scanner_cycle",0)
    image = st.file_uploader("Upload a clear image of an individual waste item for AI classification.",
                             type=["jpg","jpeg","png","webp"], key=f"scanner_upload_{cycle}",
                             help="Supported formats: JPG, JPEG, PNG, WEBP · Maximum size: 10 MB")
    if image is None:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### 1 · Upload image")
            st.write("Choose a well-lit image focused on one item. The model supports nine material categories.")
        return

    image_bytes = image.getvalue()
    fingerprint = (image.name, hash(image_bytes))
    if st.session_state.get("scanner_fingerprint") != fingerprint:
        st.session_state["scanner_fingerprint"] = fingerprint
        st.session_state.pop("scanner_prediction",None)
        st.session_state.pop("scanner_saved",None)

    st.markdown("#### 1 · Review image")
    left,right=st.columns([.9,1.1],gap="large")
    with left:
        st.image(image_bytes, caption=image.name, width="stretch")
        st.caption("A clear, close image of one item usually gives the model the best chance to classify it.")
    with right:
        st.markdown("#### 2 · AI classification")
        if st.button("Analyze waste", type="primary", icon=":material/auto_awesome:", use_container_width=True):
            with st.spinner("Analyzing image with the trained EfficientNetB0 model…"):
                prediction=api_error(predict_image,image.name,image_bytes,image.type or "application/octet-stream")
            if prediction:
                st.session_state["scanner_prediction"]={**prediction,"filename":image.name}
        result=st.session_state.get("scanner_prediction")
        if not result:
            st.caption("Your prediction and confidence will appear here after analysis.")
            return
        st.markdown(f"### {result['predicted_class'].title()}")
        st.progress(result["confidence"]/100, text=f"AI confidence · {result['confidence']:.2f}%")
        st.caption(f"Waste type · {result['waste_type']}")
        st.markdown(f'<div class="scanner-recommendation"><div class="section-kicker">Recommended disposal bin</div><strong style="font-size:1.18rem;color:#153b2e">{result["recommended_bin"]}</strong></div>', unsafe_allow_html=True)
        st.info(result.get("guidance","Follow your institution’s waste handling policy."))

    st.markdown("#### 3 · Confirm campus details")
    recommended=result["recommended_bin"]
    if recommended not in WASTE_BINS:
        st.warning("The recommended bin is not in the configured campus list. Please review the local policy before saving.")
    with st.form("scanner_confirm_save", clear_on_submit=False):
        location=st.radio("Campus location",LOCATIONS,horizontal=True,key="scanner_location")
        st.caption(f"Recommended bin: **{recommended}**")
        selected=st.selectbox("Actual bin used",WASTE_BINS,index=WASTE_BINS.index(recommended) if recommended in WASTE_BINS else 0)
        notes=st.text_input("Notes (optional)",max_chars=500)
        with st.expander("Add measured weight (optional)"):
            weight=st.number_input("Weight in kg",min_value=0.0,step=.1,value=0.0,help="Enter a manually measured value. Weight is never estimated from the image.")
        confirm=st.form_submit_button("Confirm and save record",type="primary",icon=":material/save:",use_container_width=True)
    if confirm:
        payload={"waste_category":result["predicted_class"],"confidence":result["confidence"],"location":location,
                 "selected_bin":selected,"image_filename":result["filename"],"notes":notes or None,"weight_kg":weight or None}
        with st.spinner("Saving the confirmed segregation record…"):
            response=api_error(create_record,payload)
        if response:
            correct=response["record"]["correct_segregation"]
            st.session_state["scanner_saved"]={"record_id":response["record_id"],"segregation":"Correctly segregated" if correct else "Bin choice needs review"}
            st.rerun()

if __name__ == "__main__": render()
