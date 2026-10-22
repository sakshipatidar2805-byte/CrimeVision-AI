
import streamlit as st
import pandas as pd
from PIL import Image
from pathlib import Path
from datetime import datetime
import cv2
import io
import json

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_DIR = BASE_DIR / "reports"

UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="CrimeVision AI",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {
    background: #0b1120;
    color: #e5e7eb;
}
[data-testid="stSidebar"] {
    background: #111827;
}
.hero {
    padding: 25px;
    border-radius: 16px;
    background: linear-gradient(120deg, #172554, #164e63);
    border: 1px solid #334155;
    margin-bottom: 22px;
}
.metric {
    background: #111827;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px;
}
.small-note {
    color: #94a3b8;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

if "evidence" not in st.session_state:
    st.session_state.evidence = []

if "events" not in st.session_state:
    st.session_state.events = []

with st.sidebar:
    st.title("🔎 CrimeVision AI")
    st.caption("Multimodal Forensic Workspace")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Evidence Analysis",
            "Forensic Timeline",
            "Reports",
            "About Project"
        ]
    )

    st.divider()
    st.caption("Prototype • Local workspace")
    st.caption("Evidence processing status is shown explicitly.")

if page == "Dashboard":
    st.markdown("""
    <div class="hero">
      <h1>Intelligent Forensic Analysis</h1>
      <p>Upload multimedia evidence, organize case materials
      and prepare structured forensic records.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Evidence Files", len(st.session_state.evidence))
    with c2:
        st.metric("Timeline Events", len(st.session_state.events))
    with c3:
        st.metric("Reports Generated", len(list(REPORT_DIR.glob("*.pdf"))))

    st.subheader("Quick Start")
    st.write("1. Open Evidence Analysis.")
    st.write("2. Upload an image, video or audio file.")
    st.write("3. Review the available preview and metadata.")
    st.write("4. Record verified observations in the timeline.")
    st.info(
        "This initial prototype does not automatically detect "
        "weapons, identify people or establish criminal activity."
    )

elif page == "Evidence Analysis":
    st.title("Evidence Analysis")
    st.write("Upload a file to register it in the local workspace.")

    case_id = st.text_input("Case Reference", placeholder="e.g. CASE-001")

    uploaded = st.file_uploader(
        "Upload image, video or audio",
        type=[
            "jpg", "jpeg", "png", "bmp",
            "mp4", "avi", "mov",
            "wav", "mp3", "m4a"
        ]
    )

    if uploaded:
        st.write("**Filename:**", uploaded.name)
        st.write("**Size:**", f"{uploaded.size / 1024:.1f} KB")

        suffix = Path(uploaded.name).suffix.lower()
        is_image = suffix in [".jpg", ".jpeg", ".png", ".bmp"]
        is_video = suffix in [".mp4", ".avi", ".mov"]
        is_audio = suffix in [".wav", ".mp3", ".m4a"]

        if is_image:
            st.image(uploaded, caption="Uploaded evidence preview",
                     use_container_width=True)

        elif is_video:
            st.video(uploaded)

        elif is_audio:
            st.audio(uploaded)

        if st.button("Register Evidence", type="primary"):
            if not case_id.strip():
                st.error("Enter a case reference first.")
            else:
                file_bytes = uploaded.getvalue()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = Path(uploaded.name).name.replace(" ", "_")
                destination = UPLOAD_DIR / f"{timestamp}_{safe_name}"

                destination.write_bytes(file_bytes)

                record = {
                    "case_id": case_id.strip(),
                    "filename": uploaded.name,
                    "stored_file": destination.name,
                    "type": (
                        "Image" if is_image else
                        "Video" if is_video else "Audio"
                    ),
                    "size_bytes": len(file_bytes),
                    "registered_at": datetime.now().isoformat(
                        timespec="seconds"
                    )
                }

                metadata_file = UPLOAD_DIR / "evidence_index.json"
                records = []

                if metadata_file.exists():
                    try:
                        records = json.loads(
                            metadata_file.read_text(encoding="utf-8")
                        )
                    except (ValueError, OSError):
                        st.error("Existing evidence index is unreadable.")
                        st.stop()

                records.append(record)
                metadata_file.write_text(
                    json.dumps(records, indent=2),
                    encoding="utf-8"
                )

                st.session_state.evidence.append(record)
                st.success("Evidence registered successfully.")
                st.json(record)

    st.subheader("Registered in this session")

    if st.session_state.evidence:
        st.dataframe(
            pd.DataFrame(st.session_state.evidence),
            use_container_width=True
        )
    else:
        st.caption("No evidence registered in this session yet.")

elif page == "Forensic Timeline":
    st.title("Forensic Timeline")
    st.write("Record observations for later forensic review.")

    with st.form("event_form", clear_on_submit=True):
        event_case = st.text_input("Case Reference")
        event_time = st.text_input(
            "Event Time",
            placeholder="e.g. 2026-10-22 10:30:00"
        )
        description = st.text_area("Observation / Event Description")
        source = st.text_input("Evidence Source")
        submit = st.form_submit_button("Add Timeline Event")

    if submit:
        if not all([
            event_case.strip(),
            event_time.strip(),
            description.strip()
        ]):
            st.error("Case reference, event time and description are required.")
        else:
            event = {
                "case_id": event_case.strip(),
                "event_time": event_time.strip(),
                "description": description.strip(),
                "source": source.strip() or "Not specified",
                "recorded_at": datetime.now().isoformat(
                    timespec="seconds"
                )
            }

            st.session_state.events.append(event)
            st.success("Observation added to the session timeline.")

    if st.session_state.events:
        timeline = pd.DataFrame(st.session_state.events)
        st.dataframe(timeline, use_container_width=True)

        if st.button("Export Timeline CSV"):
            csv_data = timeline.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                data=csv_data,
                file_name="forensic_timeline.csv",
                mime="text/csv"
            )
    else:
        st.info("No timeline observations have been recorded.")

elif page == "Reports":
    st.title("Forensic Reports")
    st.write("Generate a PDF summary of registered evidence and observations.")

    report_case = st.text_input("Case Reference for Report")

    if st.button("Generate PDF Report", type="primary"):
        if not report_case.strip():
            st.error("Enter a case reference.")
        else:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table
            )
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors

            output = io.BytesIO()
            doc = SimpleDocTemplate(
                output,
                pagesize=A4,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40
            )
            styles = getSampleStyleSheet()
            story = [
                Paragraph("CrimeVision AI", styles["Title"]),
                Paragraph("Forensic Evidence Summary", styles["Heading2"]),
                Spacer(1, 12),
                Paragraph(
                    f"Case Reference: {report_case.strip()}",
                    styles["Normal"]
                ),
                Paragraph(
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    styles["Normal"]
                ),
                Spacer(1, 16)
            ]

            evidence_rows = [["Filename", "Type", "Size (bytes)"]]
            for item in st.session_state.evidence:
                if item["case_id"] == report_case.strip():
                    evidence_rows.append([
                        item["filename"],
                        item["type"],
                        str(item["size_bytes"])
                    ])

            story.append(Paragraph("Registered Evidence", styles["Heading2"]))
            story.append(Table(
                evidence_rows,
                repeatRows=1,
                style=[
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP")
                ]
            ))
            story.append(Spacer(1, 16))
            story.append(Paragraph("Timeline Observations", styles["Heading2"]))

            matching_events = [
                event for event in st.session_state.events
                if event["case_id"] == report_case.strip()
            ]

            if matching_events:
                for event in matching_events:
                    story.append(Paragraph(
                        f"{event['event_time']} — {event['description']}",
                        styles["Normal"]
                    ))
                    story.append(Paragraph(
                        f"Source: {event['source']}",
                        styles["Normal"]
                    ))
                    story.append(Spacer(1, 8))
            else:
                story.append(Paragraph(
                    "No timeline observations available in this session.",
                    styles["Normal"]
                ))

            story.append(Spacer(1, 18))
            story.append(Paragraph(
                "Important: This report summarizes manually registered "
                "records. It is not an automated forensic conclusion.",
                styles["Italic"]
            ))

            doc.build(story)
            pdf_bytes = output.getvalue()

            report_path = REPORT_DIR / (
                "report_" +
                datetime.now().strftime("%Y%m%d_%H%M%S") +
                ".pdf"
            )
            report_path.write_bytes(pdf_bytes)

            st.success("PDF summary generated.")
            st.download_button(
                "Download Forensic PDF",
                data=pdf_bytes,
                file_name=report_path.name,
                mime="application/pdf"
            )

elif page == "About Project":
    st.title("About CrimeVision AI")
    st.write("""
    CrimeVision AI is a prototype workspace for organizing multimedia
    evidence and recording forensic observations.

    Current prototype capabilities:
    - Image, video and audio upload and preview
    - Local evidence registration
    - Manually recorded event timeline
    - PDF summary report generation

    Not yet implemented:
    - AI-based object and weapon detection
    - Speech-to-text transcription
    - Automated multimodal event correlation
    - Persistent AI evidence question-answering
    - Validated forensic scene reconstruction
    """)
    st.warning(
        "Use synthetic or authorized test evidence. Uploaded files are "
        "stored locally and no authentication or access-control system "
        "is implemented in this prototype."
    )
