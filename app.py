"""Image-Assisted Sportfish Reporting QA Demo — Streamlit application."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.export_utils import dataframe_to_csv_bytes, dataframe_to_json_bytes, export_summary_md
from src.image_quality import assess_quality
from src.report_validator import validate_report, validate_reports_df
from src.review_priority import compute_priority
from src.species_suggest import SPECIES_LIST, suggest_species

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

st.set_page_config(
    page_title="Image-Assisted Sportfish Reporting QA Demo",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Image-Assisted Sportfish Reporting QA Demo")
st.caption(
    "A photo-quality and species-suggestion assistant for recreational fisheries reports. "
    "Designed to support cleaner citizen-science submissions and faster manual review. "
    "This is a prototype using synthetic/public data only."
)

pages = [
    "Upload & Submit",
    "AI Assistance",
    "Review Queue",
    "Data Export",
    "Model Limits & Disclaimers",
]
page = st.sidebar.radio("Navigate", pages)


def _load_sample_reports() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "sample_reports.csv")


if "submitted_reports" not in st.session_state:
    st.session_state.submitted_reports = []
if "last_image_bytes" not in st.session_state:
    st.session_state.last_image_bytes = None
if "last_quality" not in st.session_state:
    st.session_state.last_quality = None
if "last_suggestions" not in st.session_state:
    st.session_state.last_suggestions = None
if "last_metadata" not in st.session_state:
    st.session_state.last_metadata = {}


if page == "Upload & Submit":
    st.subheader("Upload Fish Photo & Enter Report Details")

    col_img, col_form = st.columns([1, 1])

    with col_img:
        uploaded = st.file_uploader("Upload a fish photo", type=["jpg", "jpeg", "png"])
        if uploaded:
            st.image(uploaded, caption="Uploaded image", use_container_width=True)
            st.session_state.last_image_bytes = uploaded.getvalue()

    with col_form:
        with st.form("report_form"):
            species = st.selectbox("Species (your identification)", [""] + SPECIES_LIST)
            catch_date = st.date_input("Catch date")
            area = st.text_input("General area")
            depth = st.number_input("Depth range (ft)", min_value=0, max_value=500, value=0)
            length = st.number_input("Length (inches)", min_value=0.0, max_value=200.0, value=0.0)
            kept_released = st.selectbox("Kept or released", ["", "kept", "released"])
            gear = st.text_input("Gear type")
            notes = st.text_input("Notes")
            submitted = st.form_submit_button("Submit Report")

        if submitted:
            metadata = {
                "species_reported_by_user": species if species else None,
                "catch_date": str(catch_date),
                "general_area": area,
                "depth_range_ft": depth if depth > 0 else None,
                "length_inches": length if length > 0 else None,
                "kept_or_released": kept_released if kept_released else None,
                "photo_uploaded": "yes" if st.session_state.last_image_bytes else "no",
                "gear_type": gear,
                "notes": notes,
            }
            st.session_state.last_metadata = metadata

            quality = None
            suggestions = None
            if st.session_state.last_image_bytes:
                quality = assess_quality(image_bytes=st.session_state.last_image_bytes)
                suggestions = suggest_species(image_bytes=st.session_state.last_image_bytes)

            st.session_state.last_quality = quality
            st.session_state.last_suggestions = suggestions

            model_top = suggestions[0].species if suggestions else None
            model_conf = suggestions[0].confidence if suggestions else 0.0
            img_score = quality.quality_score if quality else 0.0

            validation = validate_report(
                species_reported=metadata["species_reported_by_user"],
                catch_date=metadata["catch_date"],
                length_inches=metadata["length_inches"],
                kept_or_released=metadata["kept_or_released"],
                photo_uploaded=metadata["photo_uploaded"],
                model_top_species=model_top,
            )

            has_mismatch = (
                model_top is not None
                and metadata["species_reported_by_user"] is not None
                and model_top.lower() != metadata["species_reported_by_user"].lower()
            )
            priority = compute_priority(
                model_confidence=model_conf,
                image_quality_score=img_score,
                metadata_completeness=validation.completeness_pct,
                has_mismatch=has_mismatch,
            )

            report_record = {
                **metadata,
                "report_id": f"RPT-{1000 + len(st.session_state.submitted_reports):04d}",
                "model_top_species": model_top,
                "model_confidence": model_conf,
                "image_quality_score": img_score,
                "completeness_pct": validation.completeness_pct,
                "priority": priority.priority,
                "report_confidence": priority.report_confidence,
                "issues": "; ".join(validation.issues) if validation.issues else "None",
            }
            st.session_state.submitted_reports.append(report_record)
            st.success(f"Report submitted. Priority: **{priority.priority}**. Go to AI Assistance for details.")


elif page == "AI Assistance":
    st.subheader("AI Assistance Results")

    if st.session_state.last_image_bytes is None:
        st.info("Upload an image and submit a report first.")
    else:
        col_preview, col_results = st.columns([1, 1])

        with col_preview:
            st.image(st.session_state.last_image_bytes, caption="Last uploaded image", use_container_width=True)

        with col_results:
            quality = st.session_state.last_quality
            if quality:
                st.markdown("### Image Quality Score")
                st.metric("Overall Quality", f"{quality.quality_score}/100")
                cols = st.columns(5)
                cols[0].metric("Sharpness", f"{quality.sharpness}")
                cols[1].metric("Brightness", f"{quality.brightness}")
                cols[2].metric("Contrast", f"{quality.contrast}")
                cols[3].metric("Resolution", f"{quality.resolution}")
                cols[4].metric("Visibility", f"{quality.fish_visibility}")
                for note in quality.notes:
                    st.write(f"- {note}")

            suggestions = st.session_state.last_suggestions
            if suggestions:
                st.markdown("### Species Suggestions (candidate labels)")
                top3 = suggestions[:3]
                df_sug = pd.DataFrame([{"Species": s.species, "Confidence (%)": s.confidence} for s in top3])
                fig = px.bar(df_sug, x="Species", y="Confidence (%)", text="Confidence (%)")
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
                st.caption("These are candidate labels only. A human reviewer confirms the final species.")

            metadata = st.session_state.last_metadata
            if metadata and suggestions:
                user_sp = metadata.get("species_reported_by_user")
                model_sp = suggestions[0].species if suggestions else None
                if user_sp and model_sp and user_sp.lower() != model_sp.lower():
                    st.warning(
                        f"**Species mismatch:** You reported *{user_sp}* but model suggests *{model_sp}* "
                        f"({suggestions[0].confidence}% confidence). Manual review recommended."
                    )


elif page == "Review Queue":
    st.subheader("Review Queue")

    sample_df = _load_sample_reports()
    validated = validate_reports_df(sample_df)
    queue = sample_df.merge(validated, on="report_id", how="left")
    queue["priority"] = queue.apply(
        lambda r: compute_priority(
            model_confidence=70.0,
            image_quality_score=75.0 if r.get("photo_uploaded") == "yes" else 30.0,
            metadata_completeness=r["completeness_pct"],
            has_mismatch=False,
        ).priority,
        axis=1,
    )

    if st.session_state.submitted_reports:
        user_df = pd.DataFrame(st.session_state.submitted_reports)
        st.markdown("### Your Submitted Reports")
        st.dataframe(user_df, use_container_width=True, hide_index=True)
        st.markdown("---")

    st.markdown("### Sample Reports Queue (synthetic data)")
    priority_filter = st.multiselect("Filter by priority", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
    filtered = queue[queue["priority"].isin(priority_filter)]
    display_cols = ["report_id", "species_reported_by_user", "catch_date", "length_inches", "completeness_pct", "issue_count", "priority", "issues"]
    st.dataframe(filtered[display_cols].sort_values("issue_count", ascending=False), use_container_width=True, hide_index=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(filtered))
    c2.metric("High Priority", int((filtered["priority"] == "High").sum()))
    c3.metric("Low Priority", int((filtered["priority"] == "Low").sum()))


elif page == "Data Export":
    st.subheader("Data Export")

    sample_df = _load_sample_reports()
    validated = validate_reports_df(sample_df)
    export_df = sample_df.merge(validated, on="report_id", how="left")

    if st.session_state.submitted_reports:
        user_df = pd.DataFrame(st.session_state.submitted_reports)
        export_df = pd.concat([export_df, user_df], ignore_index=True)

    col1, col2 = st.columns(2)
    col1.download_button(
        "Download CSV",
        data=dataframe_to_csv_bytes(export_df),
        file_name="review_queue.csv",
        mime="text/csv",
    )
    col2.download_button(
        "Download JSON",
        data=dataframe_to_json_bytes(export_df),
        file_name="review_queue.json",
        mime="application/json",
    )

    if st.button("Generate Summary Report"):
        path = export_summary_md(export_df)
        st.success(f"Summary written to `{path.name}`.")
        st.code(path.read_text(encoding="utf-8"), language="markdown")


else:
    st.subheader("Model Limits & Disclaimers")
    st.markdown("""
### What this prototype does

- Suggests **candidate species labels** based on basic image features.
- Checks **photo quality** (blur, brightness, contrast, resolution).
- Validates **report completeness** (missing fields, implausible values).
- Assigns **review priority** (High / Medium / Low).
- Generates **reviewer-ready summaries** and structured exports.

### What this prototype does NOT do

- It does **not** identify fish species for fisheries management.
- It does **not** replace expert human review.
- It does **not** use internal HRI/CSSC data.
- It does **not** claim management-grade accuracy.

### Human-in-the-loop design

The model only **suggests** — a human reviewer confirms the final species, quality assessment,
and inclusion decision. This is a triage and review-support tool, not an automated decision system.

### Data privacy

- Uses only synthetic sample reports and public-domain placeholder images.
- No faces, boat registrations, exact personal locations, or identifiable information.
- No real catch data from any monitoring program.

### Species scope

Limited to 8 Gulf-relevant species for this prototype:

1. Red Snapper
2. Southern Flounder
3. Spotted Seatrout
4. Red Drum
5. Black Drum
6. King Mackerel
7. Cobia
8. Shark (broad category)

### Technical notes

- Species suggestion uses a **demonstration stub classifier** based on color/shape heuristics.
  It is not a trained deep-learning model and should not be evaluated for biological accuracy.
- Image quality scoring uses OpenCV (Laplacian variance, LAB luminance, grayscale std).
- The tool is positioned as "image-assisted review support" — not "AI fish identification."
""")
