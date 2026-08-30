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

Only slide 2 is implemented currently.

## Build

```bash
python3 scripts/build_slide_02.py
```

## Preview locally

From the repository root:

```bash
python3 -m http.server 8000 --directory docs
```

Then open `http://localhost:8000/slide-02.html`.

## Publish and embed

1. In the GitHub repository settings, select **Pages** and publish from the
   `main` branch using the `/docs` folder.
2. After pushing, the slide-2 page will be available at:

   `https://ausmeyer.github.io/ut-grand-rounds-visuals/slide-02.html`

3. Add an **Iframe** block in Slides.com and paste that URL.
4. Resize the iframe to the available slide area. The page is responsive and
   is optimized for a wide 16:9 frame.

Optional URL fragments can set the opening state:

- `#day=0&view=all` starts at June 1 with all annotation categories.
- `#day=364&view=all` opens with the full season revealed through May 31.
- `view=vaccine`, `view=clinical`, or `view=public-health` filters markers.
