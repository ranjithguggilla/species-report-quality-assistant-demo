"""Review priority engine.

Assigns High / Medium / Low review priority to each report based on a composite
confidence score combining model confidence, image quality, metadata completeness,
and consistency.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PriorityResult:
    report_confidence: float
    priority: str
    reason: str


def compute_priority(
    model_confidence: float,
    image_quality_score: float,
    metadata_completeness: float,
    has_mismatch: bool = False,
) -> PriorityResult:
    """Compute review priority for a single report.

    All input scores should be on a 0-100 scale.
    """
    consistency = 0.0 if has_mismatch else 100.0

    report_confidence = round(
        0.40 * model_confidence
        + 0.30 * image_quality_score
        + 0.20 * metadata_completeness
        + 0.10 * consistency,
        1,
    )

    reasons: list[str] = []
    if model_confidence < 60:
        reasons.append("low model confidence")
    if image_quality_score < 50:
        reasons.append("poor image quality")
    if metadata_completeness < 80:
        reasons.append("incomplete metadata")
    if has_mismatch:
        reasons.append("species mismatch between user and model")

    if report_confidence < 60:
        priority = "High"
    elif report_confidence < 80:
        priority = "Medium"
    else:
        priority = "Low"

    reason = "; ".join(reasons) if reasons else "Report looks complete and consistent."
    return PriorityResult(
        report_confidence=report_confidence,
        priority=priority,
        reason=reason,
    )
