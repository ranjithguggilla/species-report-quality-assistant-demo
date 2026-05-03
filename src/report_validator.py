"""Report completeness and validity checks.

Validates catch-report metadata against species reference ranges and required
field rules. Returns a completeness percentage and list of issues found.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SPECIES_REF_PATH = ROOT / "data" / "species_reference.csv"


@dataclass
class ValidationResult:
    completeness_pct: float
    issues: list[str] = field(default_factory=list)
    is_valid: bool = True


def _load_species_ref() -> pd.DataFrame:
    return pd.read_csv(SPECIES_REF_PATH)


def validate_report(
    species_reported: str | None,
    catch_date: str | None,
    length_inches: float | None,
    kept_or_released: str | None,
    photo_uploaded: str | None,
    model_top_species: str | None = None,
) -> ValidationResult:
    """Check a single report record for completeness and plausibility."""
    issues: list[str] = []
    required_fields = {
        "species": species_reported,
        "catch_date": catch_date,
        "length_inches": length_inches,
        "kept_or_released": kept_or_released,
        "photo_uploaded": photo_uploaded,
    }
    filled = sum(1 for v in required_fields.values() if v is not None and str(v).strip() != "")
    completeness = round(100 * filled / len(required_fields), 1)

    if not species_reported or str(species_reported).strip() == "":
        issues.append("Missing species.")

    if catch_date:
        try:
            dt = pd.to_datetime(catch_date).date()
            today = date.today()
            if dt > today:
                issues.append("Catch date is in the future.")
            elif dt < today - timedelta(days=730):
                issues.append("Catch date is older than 2 years.")
        except (ValueError, TypeError):
            issues.append("Invalid catch date format.")
    else:
        issues.append("Missing catch date.")

    if length_inches is not None and species_reported:
        ref = _load_species_ref()
        match = ref[ref["species"] == species_reported]
        if not match.empty:
            row = match.iloc[0]
            if length_inches < row["min_length_in"] * 0.5:
                issues.append(f"Length {length_inches}\" is unusually small for {species_reported}.")
            elif length_inches > row["max_length_in"] * 1.5:
                issues.append(f"Length {length_inches}\" is unusually large for {species_reported}.")
    elif length_inches is None:
        issues.append("Missing length measurement.")

    if not kept_or_released or str(kept_or_released).strip() == "":
        issues.append("Missing kept/released status.")

    if not photo_uploaded or str(photo_uploaded).strip().lower() != "yes":
        issues.append("No photo uploaded.")

    if model_top_species and species_reported:
        if model_top_species.lower() != species_reported.lower():
            issues.append(
                f"Species mismatch: user reported '{species_reported}' but model suggests '{model_top_species}'."
            )

    is_valid = len(issues) == 0
    return ValidationResult(completeness_pct=completeness, issues=issues, is_valid=is_valid)


def validate_reports_df(df: pd.DataFrame) -> pd.DataFrame:
    """Validate all rows in a reports DataFrame, adding issue columns."""
    results = []
    for _, row in df.iterrows():
        r = validate_report(
            species_reported=row.get("species_reported_by_user"),
            catch_date=row.get("catch_date"),
            length_inches=row.get("length_inches") if pd.notna(row.get("length_inches")) else None,
            kept_or_released=row.get("kept_or_released"),
            photo_uploaded=row.get("photo_uploaded"),
        )
        results.append({
            "report_id": row.get("report_id", ""),
            "completeness_pct": r.completeness_pct,
            "issues": "; ".join(r.issues) if r.issues else "None",
            "issue_count": len(r.issues),
            "is_valid": r.is_valid,
        })
    return pd.DataFrame(results)
