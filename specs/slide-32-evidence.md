# Slide 32: Where are we now?

Slide 32 now shows current reported ILINet curves and introduces the existing
candidate vaccination threshold. It replaces the derivative exploration at the
user’s request. The earlier version is recoverable at Git commit `575e77b`;
its saved `data/slide-32/diagnostic.json` and independent validation are retained
as historical data and are not used by the current build. Slides 30–31 and their
model outputs are unchanged.

## Current source and reporting date

CDC FluView was downloaded on **October 2, 2026, at 18:39:58 UTC**. Its latest
national and selected-state observations end **September 26, 2026 (MMWR week
38)**. This presentation focuses on the current fall’s run-up: 13 weekly
observations from July 4 through September 26, 2026 (weeks 26–38).

- [CDC FluView Interactive](https://gis.cdc.gov/grasp/fluview/fluportaldashboard.html)
- [CDC surveillance methods](https://www.cdc.gov/fluview/overview/index.html)
- Metadata: `https://gis.cdc.gov/flu2/GetPhase02InitApp?appVersion=Public`
- Download: `https://gis.cdc.gov/flu2/PostPhase02DataDownload`

`data/slide-32/current-ilinet/` retains the metadata, request JSON, original ZIP
responses, extracted CSVs, provenance with SHA-256 fingerprints, plotted data,
and independent numerical validation. Requests cover CDC download seasons
2024–25 and 2025–26; only the current 2026 window is displayed. The metadata
and returned CSVs agree on the latest week.

The national curve uses CDC’s **population-weighted percent ILI**. State curves
use the published **unweighted percent ILI** for each named jurisdiction. These
are reported observations, with no GAM fit, extra smoothing, posterior sampling,
forecast, or extension beyond the last report. Missing values are not converted
to zero or connected across a gap. Current displayed series are complete.

New York City is a separate ILINet reporting jurisdiction. Its current export
contains `X` for ILI percentages and counts, and the metadata flags its current
ILI series as unavailable. Thus the fourth panel is explicitly **New York
(excl. NYC)**. No city values are imputed or added as zero. The separate NY/NYC
jurisdictions and the count-based combination needed for a statewide total are
also documented in [Delphi’s ILINet ingestion specification](https://cmu-delphi.github.io/delphi-epidata/api/v5-signals/fluview_ilinet.html).
This geographic scope differs from the combined New York model in slide 31.

## Frozen threshold, applied to current reported observations

The multiplier is the existing **2.3** from
`data/august-baseline/threshold-fit.json`, pinned to SHA-256
`97b6e6d4c614d693c6aedf601a7ee60118b8220e9c5607caa9685dda000e2dd7`.
It is not refitted to the current curves.

For each displayed location, the baseline is the arithmetic mean of its four
reported ILI percentages in **MMWR weeks 32–35 of 2026**. Those observations
end August 15, August 22, August 29, and September 5. “August” retains the
week-window convention used in slides 30–31; it is not an exact calendar-month
average. The horizontal line is **2.3 × that local baseline**, in percent ILI.
Potential crossings are evaluated only from week 36, as in the frozen rule.

| Location | Latest reported ILI (%) | Local baseline (%) | Candidate threshold (%) |
| --- | ---: | ---: | ---: |
| United States | 1.742360 | 1.24323025 | 2.859429575 |
| Texas | 1.831650 | 1.77305250 | 4.078020750 |
| California | 2.619510 | 1.98706750 | 4.570255250 |
| Minnesota | 0.957166 | 0.45171600 | 1.038946800 |
| New York (excl. NYC) | 1.431190 | 0.65933875 | 1.516479125 |

No displayed location has crossed its candidate line in the eligible reported
weeks 36–38. This does not establish when it will cross or identify an optimal
vaccination date. The original rule was calibrated and explored using latent
epidemic curves. Applying the multiplier to reported weekly values is an
**exploratory illustration of a possible operational rule**, not a replication
of that latent-curve evaluation or a validated vaccination recommendation.
The candidate line is not CDC’s official seasonal ILI baseline or an influenza
laboratory-positivity threshold. ILINet measures visits for influenza-like
illness and can reflect other respiratory pathogens.

All observations are preliminary and subject to revision. The page is a
**dated snapshot**, not an automatically updating feed. It shows the latest
reported week available at retrieval, not a nowcast of October 2.

## Presenter states

1. **Start:** static US ILINet curve; no threshold visible.
2. **US threshold:** draw the dashed candidate line and reveal its value.
3. **States:** crossfade to Texas, California, Minnesota, and New York
   excluding NYC, initially without threshold lines.
4. **State thresholds:** draw all four local candidate lines together.

The reporting date stays visible. Each state has a separately labeled vertical
scale to make its distance from its own line legible; calendar axes are shared.
Thresholds are included when determining those scales, so revealing a line does
not rescale or move the observed curves. Every curve ends at the latest report.

ArrowRight, PageDown, and Space advance; ArrowLeft and PageUp go back; Home and
Reset return to the static opening. Loading `#state=N` shows that completed
state without autoplay. Reduced-motion preference suppresses animation.

## Build and validation

- Refresh source snapshot deliberately: `python3 scripts/fetch_slide_32_ilinet.py`.
  Inspect the resulting reporting dates and geographic availability before
  republishing. The current build is scoped to the 2026 summer-to-fall window.
- Rebuild offline: `python3 scripts/build_slide_32.py`.
- Independent numerical check: `Rscript scripts/check_slide_32.R`.
- Editable source: `src/slide-32.html`; standalone output: `docs/slide-32.html`.
- Active plotted data: `data/slide-32/current-ilinet/slide.json`.
- Validation: `data/slide-32/current-ilinet/validation.json`.

The R check independently reads the original CDC CSVs, verifies all 65 plotted
values, checks week-ending dates with `MMWRweek`, recomputes the five baselines
and thresholds, confirms the frozen multiplier and source hashes, and checks
state percentages against the raw ILI/total-visit counts within published
rounding precision. It confirms NYC is missing and excluded. Maximum numerical
disagreement with the builder is zero.

Browser checks at 1280 × 720 confirmed all four builds, all 65 plotted points,
correct threshold endpoints and labels, forward/back navigation, Reset, rapid
advances during animation, and direct loading of a completed state. Screenshots
were inspected for clipping and overlap; no console errors or warnings occurred.
