# Image-Assisted Sportfish Reporting QA Demo

## Purpose

This prototype is a public-data-safe demonstration of how image-assisted species suggestions and report-quality checks could support recreational fisheries reporting workflows. It does not use internal HRI/CSSC data, does not replace expert review, and does not claim management-grade species identification. The goal is to demonstrate a human-in-the-loop workflow for cleaner, more reviewable citizen-science reports.

## HRI / CSSC alignment

Citizen-science platforms like iSnapper let anglers report catch data to improve harvest estimates. This prototype explores how image quality assessment and candidate species labels could speed up manual review of those submissions — without replacing the human reviewer.

## What the prototype does

- Lets a user upload a fish-report photo and enter catch metadata.
- Checks image quality (blur, brightness, contrast, resolution, fish visibility).
- Suggests candidate species labels with confidence scores.
- Compares image suggestion against user-entered species and flags mismatches.
- Validates report completeness and flags implausible values.
- Assigns review priority (High / Medium / Low).
- Generates reviewer-ready summaries.
- Exports structured CSV/JSON for downstream analysis.

## What it does NOT do

- **Does not** identify fish species for fisheries management.
- **Does not** replace expert human review.
- **Does not** use internal HRI/CSSC data or private imagery.
- **Does not** claim management-grade accuracy.

## Human-in-the-loop design

The model only **suggests**:

- Possible species (candidate label)
- Confidence level
- Quality issues
- Review priority

A human reviewer confirms the final species and inclusion decision.

## Species scope

Limited to 8 Gulf-relevant species:

1. Red Snapper
2. Southern Flounder
3. Spotted Seatrout
4. Red Drum
5. Black Drum
6. King Mackerel
7. Cobia
8. Shark (broad category)

## Data privacy

- **Reports:** `data/sample_reports.csv` is synthetic only (no real angler submissions).
- **Photos:** `data/demo_images/` uses **real fish photographs** from [Wikimedia Commons](https://commons.wikimedia.org) with documented licenses — see [`data/demo_images/SOURCES.md`](data/demo_images/SOURCES.md). They are for UI demonstration only, not from HRI/CSSC or any private program.
- Demo images avoid faces, boat registrations, and personal locations; do not upload identifiable private photos into a public fork without consent.

## Tech stack

- Python, Streamlit, OpenCV, Pillow, Pandas, Plotly, scikit-learn

## Project structure

```text
species-report-quality-assistant-demo/
├── app.py                        Main Streamlit application
├── src/
│   ├── image_quality.py          Photo quality scoring (OpenCV)
│   ├── species_suggest.py        Candidate species labels (stub classifier)
│   ├── report_validator.py       Metadata completeness and range checks
│   ├── review_priority.py        Composite scoring and priority assignment
│   └── export_utils.py           CSV/JSON/summary generation
├── data/
│   ├── sample_reports.csv        25 synthetic report records
│   ├── species_reference.csv     Species length ranges and habitat info
│   └── demo_images/              8 Commons-licensed species photos + SOURCES.md
├── outputs/                      Generated exports
├── scripts/
│   ├── smoke_test.py             Automated pipeline validation
│   └── generate_demo_images.py   Optional solid-color placeholders (offline only)
├── screenshots/                  UI screenshots (placeholder)
├── requirements.txt
├── Makefile
├── LICENSE
└── CONTRIBUTING.md
```

## Run locally

1. Clone and enter the project:

   ```bash
   git clone https://github.com/ranjithguggilla/species-report-quality-assistant-demo.git
   cd species-report-quality-assistant-demo
   ```

2. Install dependencies:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. Start the app:

   ```bash
   streamlit run app.py
   ```

Or use `make`:

```bash
make setup
make run
```

## Quality checks

```bash
make smoke
```

GitHub Actions runs `scripts/smoke_test.py` on push/PR to `main`.

## Scoring logic

### Image Quality Score

```
quality_score =
  0.30 * sharpness +
  0.20 * brightness +
  0.20 * contrast +
  0.20 * resolution +
  0.10 * fish_visibility
```

### Report Confidence

```
report_confidence =
  0.40 * model_confidence +
  0.30 * image_quality_score +
  0.20 * metadata_completeness +
  0.10 * consistency_score
```

### Review Priority

- **High:** report confidence < 60
- **Medium:** report confidence 60–79
- **Low:** report confidence >= 80

## Future improvements

- Replace stub classifier with MobileNetV2 fine-tuned on public fish dataset.
- Add duplicate image detection (perceptual hashing).
- Add EXIF metadata extraction for geolocation validation.
- Integrate Grad-CAM for model explanation overlays.
- Support batch upload of multiple reports.

## Screenshots

*(Placeholder — add screenshots after first run.)*
