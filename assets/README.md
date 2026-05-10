# Dashboard media (`assets/`)

Repository visuals live here so the root **`README.md`** can stay fast-loading while still showcasing the Streamlit app.

| Path | Role |
|------|------|
| **`screenshots/`** | Full-page PNGs per sidebar page (`01-` … `05-`), used in the README **Demo gallery** (collapsible table). |
| **`gifs/`** | **`demo-overview.gif`** — centered hero animation in the README **Overview** section. |

Commit PNGs + GIF when you refresh captures so GitHub renders the latest demo.

## Automated PNG capture (Playwright)

1. Install dev tools (once):

   ```bash
   pip install -r requirements-dev.txt
   playwright install chromium
   ```

2. Start the app in another terminal (pick a free port):

   ```bash
   make run
   # or: .venv/bin/streamlit run app.py --server.port 8520
   ```

3. Capture all sidebar pages:

   ```bash
   make capture-media STREAMLIT_URL=http://127.0.0.1:8501
   ```

   Override the URL if your port differs.

Output files:

- `assets/screenshots/01-upload-submit.png`
- `assets/screenshots/02-ai-assistance.png`
- `assets/screenshots/03-review-queue.png`
- `assets/screenshots/04-data-export.png`
- `assets/screenshots/05-model-limits.png`

## GIFs (screen recording)

**Quick rebuild from PNGs** (after `make capture-media`):

```bash
cd assets/screenshots
ffmpeg -y -framerate 1 -pattern_type glob -i '*.png' \
  -vf "scale=1200:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3" \
  ../gifs/demo-overview.gif
```

Or record the browser and convert:

```bash
ffmpeg -y -i recording.mov -vf "fps=8,scale=1200:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" assets/gifs/demo-overview.gif
```

Keep GIFs **under ~5–8 MB** so GitHub README loads quickly (shorter clip or lower fps/width if needed).

## Manual capture

If you prefer no Playwright: open the running app, walk each sidebar page, use OS screenshot (or browser full-page capture), and save PNGs using the same filenames as above so the README links stay valid.
