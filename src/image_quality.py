"""Image quality assessment using OpenCV.

Computes sharpness, brightness, contrast, resolution, and a fish-visibility
proxy. Returns a composite quality score (0-100) with per-dimension breakdown.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class QualityResult:
    sharpness: float
    brightness: float
    contrast: float
    resolution: float
    fish_visibility: float
    quality_score: float
    notes: list[str]


def _sharpness_score(gray: np.ndarray) -> float:
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    score = min(100.0, lap_var / 5.0)
    return round(score, 1)


def _brightness_score(img_bgr: np.ndarray) -> float:
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0].astype(float)
    mean_l = l_channel.mean()
    if mean_l < 40:
        score = mean_l * 1.5
    elif mean_l > 200:
        score = max(0, 100 - (mean_l - 200) * 2)
    else:
        score = 50 + (mean_l - 40) * (50 / 160)
    return round(min(100.0, max(0.0, score)), 1)


def _contrast_score(gray: np.ndarray) -> float:
    std = gray.astype(float).std()
    score = min(100.0, std * 1.8)
    return round(score, 1)


def _resolution_score(h: int, w: int) -> float:
    pixels = h * w
    if pixels >= 2_000_000:
        return 100.0
    if pixels >= 640 * 480:
        return 60.0 + 40.0 * (pixels - 640 * 480) / (2_000_000 - 640 * 480)
    return max(0.0, 60.0 * pixels / (640 * 480))


def _fish_visibility_proxy(gray: np.ndarray) -> float:
    """Estimate how much of the image is a non-background subject."""
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    foreground_ratio = thresh.sum() / (255.0 * thresh.size)
    score = min(100.0, foreground_ratio * 200)
    return round(score, 1)


def assess_quality(image_path: str | Path | None = None, image_bytes: bytes | None = None) -> QualityResult:
    """Run full quality assessment on an image file or raw bytes."""
    if image_bytes is not None:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    elif image_path is not None:
        img = cv2.imread(str(image_path))
    else:
        raise ValueError("Provide image_path or image_bytes")

    if img is None:
        return QualityResult(
            sharpness=0, brightness=0, contrast=0, resolution=0,
            fish_visibility=0, quality_score=0, notes=["Could not decode image"],
        )

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    sharpness = _sharpness_score(gray)
    brightness = _brightness_score(img)
    contrast = _contrast_score(gray)
    resolution = _resolution_score(h, w)
    visibility = _fish_visibility_proxy(gray)

    quality_score = round(
        0.30 * sharpness + 0.20 * brightness + 0.20 * contrast + 0.20 * resolution + 0.10 * visibility,
        1,
    )

    notes: list[str] = []
    if sharpness < 40:
        notes.append("Image may be blurry.")
    if brightness < 30:
        notes.append("Image is too dark.")
    elif brightness > 95:
        notes.append("Image is overexposed.")
    if resolution < 50:
        notes.append("Resolution is below recommended minimum.")
    if visibility < 30:
        notes.append("Fish may not be clearly visible.")
    if not notes:
        notes.append("Image quality is acceptable.")

    return QualityResult(
        sharpness=sharpness,
        brightness=brightness,
        contrast=contrast,
        resolution=resolution,
        fish_visibility=visibility,
        quality_score=quality_score,
        notes=notes,
    )
