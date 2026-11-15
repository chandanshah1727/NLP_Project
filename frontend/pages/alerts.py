"""Campus alerts generated from actual recorded segregation decisions."""
import streamlit as st
from frontend.api_client import get_alerts
from frontend.components import LOCATIONS,api_error

ACTION_TEXT={
    "low_compliance":"Review recent records at this location and refresh disposal guidance with the campus team.",
    "repeated_issues":"Check the affected waste stream and reinforce bin-selection guidance at this location.",
    "category_attention":"Review campus policy for this material and confirm that the recommended stream is appropriate.",
    "increasing_incorrect_records":"Compare the recent period with the prior week and investigate the increase in incorrect choices.",
}
TITLE_TEXT={"low_compliance":"Segregation compliance below threshold","repeated_issues":"Repeated segregation issues","category_attention":"Waste category needs attention","increasing_incorrect_records":"Incorrect decisions increased"}

def render():
    st.markdown('<div class="page-eyebrow">Record-based monitoring</div><h1>Alerts</h1><div class="page-description">Warnings are generated from recorded bin choices and campus compliance rules.</div>',unsafe_allow_html=True)
    st.markdown('<div class="subtle-note">The system monitors submitted records only. It has no real-time sensor or physical bin-fill alerts.</div>',unsafe_allow_html=True)
    left,right=st.columns([1,1])
    location=left.selectbox("Campus location",["All locations"]+LOCATIONS,key="alerts_location")
    severity=right.selectbox("Severity",["All severities","high","medium","low"],key="alerts_severity")
    params={}
    if location!="All locations": params["location"]=location
    if severity!="All severities": params["severity"]=severity
    response=api_error(get_alerts,**params)
    if response is None: return
    st.metric("Active alerts",response["count"],help="Generated from current records; the low-compliance threshold is 70%.")
    alerts=response.get("alerts",[])
    if not alerts:
        st.success("No alerts match these filters.")
        return
    for alert in alerts:
        tone={"high":"status-bad","medium":"status-warn","low":"status-warn"}.get(alert["severity"],"status-warn")
        with st.container(border=True):
            a,b=st.columns([4,1])
            with a:
                st.markdown(f"#### {TITLE_TEXT.get(alert['type'],'Segregation monitoring alert')}")
                st.write(alert["message"])
                st.caption(f"Location: {alert['location']} · Related incorrect records: {alert['count']}")
                st.markdown(f"**Recommended action:** {ACTION_TEXT.get(alert['type'],'Review relevant campus waste guidance and recorded decisions.')}")
            with b:
                st.markdown(f'<span class="status-pill {tone}">{alert["severity"].title()} severity</span>',unsafe_allow_html=True)

if __name__ == "__main__": render()
