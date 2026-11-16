"""Preview and download filtered CSV and PDF reports."""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import date
import io
import pandas as pd
import plotly.express as px
import streamlit as st
from frontend.api_client import get_summary
from frontend.components import CATEGORY_COLORS,api_error,empty_state,fetch_all_records,filter_panel
from frontend.theme import chart_layout
from frontend.theme import PRODUCT_NAME

def build_pdf(start: date,end: date,records: list[dict],summary: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
    output=io.BytesIO()
    document=SimpleDocTemplate(output,pagesize=letter,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42)
    styles=getSampleStyleSheet()
    story=[Paragraph(f"{PRODUCT_NAME} · Campus Waste Report",styles["Title"]),
           Paragraph(f"Generated {date.today().isoformat()} · Period {start} to {end}",styles["Normal"]),Spacer(1,16),
           Paragraph(f"Total records: {summary['total_records']} · Correct: {summary['correct_records']} · Incorrect: {summary['incorrect_records']} · Compliance: {summary['compliance_percentage']:.1f}%",styles["Heading2"]),Spacer(1,10),
           Paragraph("Waste category summary",styles["Heading2"])]
    table_style=TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#153b2e")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                            ("GRID",(0,0),(-1,-1),.4,colors.HexColor("#d6e0d8")),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f1f5f1")]),("PADDING",(0,0),(-1,-1),7)])
    rows=[["Category","Records"]]+[[name.title(),count] for name,count in summary["category_distribution"].items()]
    if len(rows)==1: rows.append(["No records","0"])
    story.extend([Table(rows,style=table_style),Spacer(1,13),Paragraph("Campus location summary",styles["Heading2"])])
    grouped={}
    for record in records:
        row=grouped.setdefault(record["location"],{"records":0,"correct":0,"incorrect":0})
        row["records"]+=1
        row["correct"]+=int(bool(record["correct_segregation"]))
        row["incorrect"]+=int(not bool(record["correct_segregation"]))
    location_rows=[["Location","Records","Correct","Incorrect","Compliance"]]
    for name,counts in grouped.items():
        ratio=100*counts["correct"]/counts["records"] if counts["records"] else 0
        location_rows.append([name,counts["records"],counts["correct"],counts["incorrect"],f"{ratio:.1f}%"])
    if len(location_rows)==1: location_rows.append(["No records",0,0,0,"0.0%"])
    story.extend([Table(location_rows,style=table_style),Spacer(1,13),Paragraph("Key observation",styles["Heading2"])])
    if summary["total_records"]:
        common=max(summary["category_distribution"],key=summary["category_distribution"].get).title()
        story.append(Paragraph(f"Most frequently recorded category: {common}. The report describes recorded events and user-selected bins; it does not independently verify physical disposal or infer waste weight.",styles["BodyText"]))
    else:
        story.append(Paragraph("No waste records were found for the selected filters.",styles["BodyText"]))
    document.build(story)
    return output.getvalue()

def render():
    st.markdown('<div class="page-eyebrow">Export and share</div><h1>Reports</h1><div class="page-description">Preview the actual records behind your report, then download a CSV or a formatted PDF.</div>',unsafe_allow_html=True)
    filters=filter_panel("reports")
    if filters is None: return
    records=fetch_all_records(**filters)
    summary=api_error(get_summary,**filters)
    if records is None or summary is None: return
    if not records:
        empty_state("No records match this report period. Adjust the filters or classify a waste item.")
        return
    first_category=max(summary["category_distribution"],key=summary["category_distribution"].get).title()
    cols=st.columns(4)
    cols[0].metric("Total records",f"{summary['total_records']:,}")
    cols[1].metric("Correct decisions",f"{summary['correct_records']:,}")
    cols[2].metric("Incorrect decisions",f"{summary['incorrect_records']:,}")
    cols[3].metric("Compliance",f"{summary['compliance_percentage']:.1f}%")
    st.caption(f"Most recorded category in this report: **{first_category}** · Generated from live database records")
    categories=pd.DataFrame([{"Category":k.title(),"Records":v} for k,v in summary["category_distribution"].items()])
    locations={}
    for row in records: locations[row["location"]]=locations.get(row["location"],0)+1
    left,right=st.columns(2,gap="large")
    with left:
        fig=px.bar(categories,x="Category",y="Records",color="Category",color_discrete_map={k.title():v for k,v in CATEGORY_COLORS.items()})
        st.plotly_chart(chart_layout(fig,250),width="stretch",config={"displayModeBar":False})
    with right:
        fig=px.bar(x=list(locations.values()),y=list(locations.keys()),orientation="h",labels={"x":"Records","y":"Location"},color_discrete_sequence=["#23815a"])
        st.plotly_chart(chart_layout(fig,250),width="stretch",config={"displayModeBar":False})
    st.markdown("### Download report")
    left,right=st.columns(2)
    csv_data=pd.DataFrame(records).to_csv(index=False).encode("utf-8-sig")
    left.download_button("Download CSV",csv_data,file_name="smart-waste-management-report.csv",mime="text/csv",type="primary",icon=":material/download:",use_container_width=True)
    try:
        pdf_data=build_pdf(date.fromisoformat(filters["start"]),date.fromisoformat(filters["end"]),records,summary)
    except Exception:
        st.error("The PDF could not be generated. Check the ReportLab installation and try again.")
    else:
        right.download_button("Download PDF",pdf_data,file_name="smart-waste-management-report.pdf",mime="application/pdf",icon=":material/picture_as_pdf:",use_container_width=True)
    st.caption("Report totals describe saved records only. No image-based weight estimate is included.")

if __name__ == "__main__": render()
