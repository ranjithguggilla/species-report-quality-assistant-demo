"""Species suggestion stub classifier.

Analyzes basic image features (dominant hue, aspect ratio, brightness) and
returns simulated confidence scores for 8 Gulf species. This is a demonstration
stub — not a production species classifier.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

SPECIES_LIST: list[str] = [
    "Red Snapper",
    "Southern Flounder",
    "Spotted Seatrout",
    "Red Drum",
    "Black Drum",
    "King Mackerel",
    "Cobia",
    "Shark (broad category)",
]

_HUE_PROFILES: dict[str, tuple[float, float]] = {
    "Red Snapper": (0, 15),
    "Southern Flounder": (20, 40),
    "Spotted Seatrout": (35, 70),
    "Red Drum": (10, 25),
    "Black Drum": (0, 180),
    "King Mackerel": (90, 130),
    "Cobia": (15, 35),
    "Shark (broad category)": (80, 140),
}


@dataclass
class SpeciesPrediction:
    species: str
    confidence: float


def _extract_features(img_bgr: np.ndarray) -> dict[str, float]:
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    h, w = img_bgr.shape[:2]
    dominant_hue = float(np.median(hsv[:, :, 0]))
    mean_saturation = float(hsv[:, :, 1].mean()) / 255.0
    mean_value = float(hsv[:, :, 2].mean()) / 255.0
    aspect_ratio = w / max(h, 1)
    return {
        "dominant_hue": dominant_hue,
        "mean_saturation": mean_saturation,
        "mean_value": mean_value,
        "aspect_ratio": aspect_ratio,
    }


def suggest_species(
    image_path: str | None = None, image_bytes: bytes | None = None
) -> list[SpeciesPrediction]:
    """Return ranked species suggestions with confidence scores."""
    if image_bytes is not None:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    elif image_path is not None:
        img = cv2.imread(str(image_path))
    else:
        raise ValueError("Provide image_path or image_bytes")

    if img is None:
        return [SpeciesPrediction(s, 0.0) for s in SPECIES_LIST]

    features = _extract_features(img)
    hue = features["dominant_hue"]

    raw_scores: dict[str, float] = {}
    for species, (low, high) in _HUE_PROFILES.items():
        if low <= high:
            dist = min(abs(hue - low), abs(hue - high))
            spread = high - low
        else:
            dist = min(abs(hue - low), abs(hue - high), abs(hue - 90))
            spread = 180
        affinity = max(0, 1.0 - dist / max(spread, 1))
        noise = np.random.default_rng(int(hue * 100) + hash(species) % 1000).uniform(0.05, 0.20)
        raw_scores[species] = affinity + noise

    total = sum(raw_scores.values())
    predictions = [
        SpeciesPrediction(species=sp, confidence=round(100 * score / total, 1))
        for sp, score in raw_scores.items()
    ]
    predictions.sort(key=lambda p: p.confidence, reverse=True)
    return predictions
