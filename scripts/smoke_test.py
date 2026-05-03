"""Non-UI smoke test for the Species Report Quality Assistant pipeline."""
from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.image_quality import assess_quality
from src.species_suggest import suggest_species, SPECIES_LIST
from src.report_validator import validate_report, validate_reports_df
from src.review_priority import compute_priority
from src.export_utils import export_csv, export_json, export_summary_md


def main() -> None:
    data_dir = PROJECT_ROOT / "data"
    demo_images_dir = data_dir / "demo_images"

    ref = pd.read_csv(data_dir / "species_reference.csv")
    assert len(ref) == 8, f"Expected 8 species in reference, got {len(ref)}"

    reports = pd.read_csv(data_dir / "sample_reports.csv")
    assert len(reports) >= 20, f"Expected >=20 sample reports, got {len(reports)}"

    test_img = demo_images_dir / "red_snapper.jpg"
    assert test_img.exists(), f"Demo image missing: {test_img}"

    quality = assess_quality(image_path=str(test_img))
    assert 0 <= quality.quality_score <= 100, f"Quality score out of range: {quality.quality_score}"

    suggestions = suggest_species(image_path=str(test_img))
    assert len(suggestions) == len(SPECIES_LIST), "Should return suggestion for each species"
    assert suggestions[0].confidence >= suggestions[-1].confidence, "Should be sorted descending"

    v = validate_report(
        species_reported="Red Snapper",
        catch_date="2026-03-15",
        length_inches=24.0,
        kept_or_released="kept",
        photo_uploaded="yes",
    )
    assert v.completeness_pct == 100.0, f"Expected 100% completeness, got {v.completeness_pct}"

    v_bad = validate_report(
        species_reported=None,
        catch_date="2030-01-01",
        length_inches=None,
        kept_or_released=None,
        photo_uploaded="no",
    )
    assert len(v_bad.issues) > 0, "Should flag multiple issues for bad report"

    validated = validate_reports_df(reports)
    assert len(validated) == len(reports), "Should validate all rows"

    p = compute_priority(
        model_confidence=45,
        image_quality_score=40,
        metadata_completeness=60,
        has_mismatch=True,
    )
    assert p.priority == "High", f"Expected High priority, got {p.priority}"

    p_good = compute_priority(
        model_confidence=90,
        image_quality_score=85,
        metadata_completeness=100,
        has_mismatch=False,
    )
    assert p_good.priority == "Low", f"Expected Low priority, got {p_good.priority}"

    export_df = reports.head(5)
    export_df["priority"] = "Medium"
    csv_path = export_csv(export_df, "smoke_test_export.csv")
    json_path = export_json(export_df, "smoke_test_export.json")
    md_path = export_summary_md(export_df, "smoke_test_summary.md")
    assert csv_path.exists(), "CSV export failed"
    assert json_path.exists(), "JSON export failed"
    assert md_path.exists(), "Summary export failed"

    csv_path.unlink()
    json_path.unlink()
    md_path.unlink()

    print("Smoke test passed: all modules load, data validates, pipeline runs end-to-end.")


if __name__ == "__main__":
    main()
