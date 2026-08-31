# UT Grand Rounds visuals

Self-contained interactive visuals for the UT Internal Medicine Grand Rounds
presentation. GitHub Pages should serve the `docs/` directory from the `main`
branch.

## Repository layout

```text
docs/       Published HTML files used by Slides.com iframes
specs/      Design and behavior specifications
data/       Source data for the visuals
src/        HTML source templates
scripts/    Reproducible build scripts
```

Slides 2, 4, and the surveillance-data section (slides 5–11) are implemented.

## Build

```bash
python3 scripts/build_slide_02.py
python3 scripts/build_slide_04.py
python3 scripts/build_surveillance_section.py
```

`build_surveillance_section.py` reads the already-downloaded CSV files from
`../data/processed/` and embeds compact chart data directly into the published
HTML pages.

## Preview locally

From the repository root:

```bash
python3 -m http.server 8000 --directory docs
```

Then open `http://localhost:8000/slide-02.html` or
`http://localhost:8000/slide-04.html`. Slides 5–11 use the corresponding
numbered filenames.

## Publish and embed

1. In the GitHub repository settings, select **Pages** and publish from the
   `main` branch using the `/docs` folder.
2. After pushing, the slide-2 page will be available at:

   `https://ausmeyer.github.io/ut-grand-rounds-visuals/slide-02.html`

   The slide-4 page will be available at:

   `https://ausmeyer.github.io/ut-grand-rounds-visuals/slide-04.html`

3. Add an **Iframe** block in Slides.com and paste that URL.
4. Resize the iframe to the available slide area. The page is responsive and
   is optimized for a 1240 × 540 pixel frame.

Optional URL fragments can set the opening state:

- `#day=0&view=all` starts at June 1 with all annotation categories.
- `#day=364&view=all` opens with the full season revealed through May 31.
- `view=vaccine`, `view=clinical`, or `view=public-health` filters markers.

Slide 4 also supports URL fragments:

- `#layer=all` opens with all surveillance systems visible.
- `layer=outpatient`, `layer=inpatient`, `layer=virologic`, or
  `layer=mortality` emphasizes one surveillance layer.
- Add `system=ilinet` (or another system ID) to open with that system selected.

Slides 5–9 each support three addressable views for duplication in Slides.com:

- `#state=signal` shows one selected 2024/25 curve.
- `#state=seasons` adds historical seasons for the selected location.
- `#state=geography` shows the 2024/25 reporting locations and highlights one.

Slide 6 (NSSP) also supports `#state=history`, a four-era timeline from the
2003 BioSense early-warning system through the diagnosis-based influenza
measure used in the current public product.

Slide 11 supports `#state=1` through `#state=5`, sequentially adding ILINet,
NSSP, NREVSS, NHSN, and FluSurv-NET. Within each surveillance system-season,
all included locations share one min-max scale; calendar weeks are never shifted.
