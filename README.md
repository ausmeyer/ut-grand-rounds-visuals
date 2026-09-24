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

Slides 2, 4, the surveillance-data section (slides 5–11), and the forecasting
introduction (slides 12–13) are implemented.

Polls 1–3 are implemented in `docs/poll-01.html`, `docs/poll-02.html`, and
`docs/poll-03.html`, each with question, voting, results, and presenter views.
All three use one shared backend, with poll-specific validation and separate
sessions. Run the single [unified setup/migration](specs/polls-setup.md) to
upgrade the existing Supabase installation without changing session links.
Question and chart details are in the [Poll 1 specification](specs/poll-01-setup.md)
and [Polls 2–3 specification](specs/polls-02-03-setup.md).
The existing surveillance builds do not modify the polls.

Local visual previews, which never submit responses:

- `http://localhost:8000/poll-01.html?mode=question&preview=1`
- `http://localhost:8000/poll-01.html?mode=vote&preview=1`
- `http://localhost:8000/poll-01.html?mode=results&preview=1`
- `http://localhost:8000/poll-02.html?mode=vote&preview=1`
- `http://localhost:8000/poll-02.html?mode=results&preview=1`
- `http://localhost:8000/poll-03.html?mode=vote&preview=1`
- `http://localhost:8000/poll-03.html?mode=results&preview=1`

The preview histogram contains explicitly labeled sample responses. For a real
session, open the appropriate `poll-0N.html?mode=admin` on the deployed site,
sign in, create a session, and copy its generated iframe and audience URLs. Do not embed preview
URLs or localhost URLs in the live presentation.

Poll dependencies and database/model tests:

```bash
npm ci --ignore-scripts
node scripts/vendor_poll_libraries.mjs
npm test
```

Browser checks are in `tests/poll-01.browser.mjs` and
`tests/poll-02-03.browser.mjs`. Serve `docs/` on port 8765
and run those scripts with Playwright installed, or set `POLL_PLAYWRIGHT` to the
absolute path of an installed Playwright `index.mjs`. The tests use isolated
Chrome contexts and mocked HTTP responses, not the live Supabase database.
Run both scripts again with `POLL_LEGACY_BACKEND=1` to check the transition
period before the unified SQL has been installed. Old SQL lives only in
`tests/fixtures/` for migration tests; `supabase/polls.sql` is the sole setup script.

## Build

```bash
python3 scripts/build_slide_02.py
python3 scripts/build_slide_04.py
python3 scripts/build_surveillance_section.py
python3 scripts/build_forecasting_intro.py
python3 scripts/build_forecast_scores.py
python3 scripts/build_slide_17.py
python3 scripts/build_slide_18.py
```

`build_surveillance_section.py` reads the already-downloaded CSV files from
`../data/processed/` and embeds compact chart data directly into the published
HTML pages.

Slides 5–10 share the system descriptions in `SYSTEMS` inside the same build
script. Season ranges/counts and the selected season's location counts are
calculated from the plotted curves. History describes the national/network
seasons view, with older system origins and reporting changes noted separately.
All plotted curves combine ages; the age groups describe available reporting
detail. Source checks and coverage caveats are recorded in
[`specs/surveillance-metadata-evidence.md`](specs/surveillance-metadata-evidence.md).

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
Thick lines are week-specific medians across the matching scaled national or
network aggregate seasons, rather than summaries that weight locations equally.

Slides 12 and 13 each support `#state=1` through `#state=3`:

- Slide 12: observed Texas admissions, individual forecasts, then the official
  ensemble and hospital planning.
- Slide 13: the historical shift to hospital admissions, the primary weekly
  target, then the four other 2026–27 targets. No participation chart.

Slide 14 supports `#state=1` through `#state=3`: one forecast median, its 50%
prediction interval, then its 95% prediction interval. Slide 15 supports two
views: `#state=1` shows a synthetic current-week through three-week-ahead
forecast with 23 quantiles; `#state=2` adds brief definitions of WIS and relative
WIS, with “Below 1 is better.” The plot stays fixed. Use the dropdown or arrows to move between views,
or use the hash URLs on successive Slides.com slides. Both views fit 1240 × 540;
keep the slide title in Slides.com, outside the iframe.

The forecasting introduction builds offline from pinned CDC archive snapshots
in `data/forecasting-intro/`. The [evidence notes](specs/forecasting-intro-evidence.md)
record the forecast vintage, model-week counting rule, source attribution,
rebuild instructions, and tests. No source-fetching or forecasting runs in the iframe.

The [Slides 14–15 evidence notes](specs/forecast-scores-evidence.md) distinguish
Slide 14's real archived example from Slide 15's synthetic illustration.
Both build offline with `python3 scripts/build_forecast_scores.py`. The new
Slide 15 displays no measured model score or performance claim.

Slide 17 shows the Texas hospitalization reconstruction in four views:
`#state=1` displays the short observed record; `#state=2` adds the ILINet-based
historical estimates as a dashed line. The original calendar dates are restored
from the model's shifted time index. `#state=3` animates a 728-day forward shift
and joins the reconstruction to retained observations from July 2021. Axes and
retained observations stay fixed across these first three views; earlier
observations fade out. `#state=4` adds reported observations through June 27,
2026, expanding the time axis to July 1, 2026 and the admission axis to 5,000. Use a
1240 × 540 iframe, with the title in Slides.com. This builds offline with
`python3 scripts/build_slide_17.py`; see the [source and date-handling notes](specs/slide-17-evidence.md).

Slide 18 supports three views: `#state=1` shows the model progression;
`#state=2` animates the pooled model into a shared-learning diagram and fits
the center using squared-error loss; `#state=3` keeps that center fixed and
reveals the spread fit using negative log-likelihood, then the derived quantiles.
Use a 1240 × 540 iframe and keep
“From separate models to shared learning” as the title in Slides.com. Build with
`python3 scripts/build_slide_18.py`; see the [source and interpretation notes](specs/slide-18-evidence.md).


## Slide 4 claymation

The finished animation and editable Blender project are in
`docs/slide-04-claymation/`. The video is 2 minutes 12 seconds at 1920 × 1080
and 24 fps. Only the opening title (first six seconds) and surveillance information
cards appear over the animation; there are no bottom or later top banners.
Clay signs use consistent black lettering, and the NSSP sign is raised above
the ED entrance to remain visible behind the ambulance.
The standalone player preserves the eight chapter shortcuts,
video and Blender downloads, and expandable system descriptions and sources.

- [Standalone player](https://www.meyerlab.io/ut-grand-rounds-visuals/slide-04-claymation/)
- [Compact iframe player](https://www.meyerlab.io/ut-grand-rounds-visuals/slide-04-claymation/embed.html)

Use the compact player URL in a Slides.com Iframe block, sized to 16:9, or
embed it in a webpage:

```html
<iframe
  src="https://www.meyerlab.io/ut-grand-rounds-visuals/slide-04-claymation/embed.html"
  title="Following influenza through U.S. surveillance"
  style="display:block;width:100%;aspect-ratio:16/9;border:0"
  allow="fullscreen"
  allowfullscreen>
</iframe>
```

Playback starts when the viewer presses Play. Both players use the same MP4;
GitHub Pages serves the video directly without running Blender on the server.
The `.blend` download opens in Blender for editing. The original interactive
`slide-04.html` remains available at its existing address.

The published assets are the approved render from the local
`../animations/slide-04-claymation-2026-09-23-v2/` project: `watch.html` is
copied to `index.html`, alongside `surveillance_claymation.mp4`,
`surveillance_claymation.blend`, and `poster.png`. Update those four files
together after rendering a revision. Intermediate frames and older render
versions are not included in this repository.
