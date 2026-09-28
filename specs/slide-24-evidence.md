# Slide 24: vaccination timing and remaining burden

Standalone slide 24 is Section III's second planned slide. Poll #3 replaces the
first. The Slides.com deck had 47 sections on September 28, 2026; this would
follow its Poll #3 results slide, ID `77acc8adaf65`. That deck position does not
determine the standalone filename. Slides.com integration is a later step.

## Files and preview

- `src/slide-24.html`: editable HTML, SVG, and controls.
- `data/slide-24/inputs.json`: frozen source curve, parameters, selection rule,
  and SHA-256 fingerprints of the manuscript sources.
- `data/slide-24/slide-24.json`: calculated protection, residual burden, and
  totals for 29 dates.
- `scripts/build_slide_24.py`: reproducible build using only the frozen inputs
  and Python's standard library.
- `docs/slide-24.html`: complete 1280 × 720 standalone slide. Its visualization
  occupies the established 1240 × 540 area, and the title is a separate element.

Run `python3 scripts/build_slide_24.py`, then serve `docs/` locally. The page
includes all data and code and requires no external libraries or network calls.
Use `#state=1`, `#state=2`, or `#state=3` for the three resting views. A click
on “Find minimum” sweeps all candidate weeks and then settles on the minimum.
The slider also supports direct exploration and `#week=48`-style links.
Arrow keys, Page Up/Down, and Space advance the narrative when the slider is
not focused. Home and the reset button return to the first view. Reduced-motion
preferences skip the sweep and date transitions.

## Scientific source

The manuscript project is the sibling Faculty directory
`flu_optimal_vaccine_estimate`. No analysis files there were modified or fitted.

The national 2017/18 population-weighted fitted ILI curve comes from
`outputs/primary/figure_source_data/figure_s3_national_surveillance_densities_source_data.csv`.
Select `measure=ILI`, `season=2017/18`, and `source_week_present=TRUE`, then sort
by `elapsed_week`. All 39 weeks, MMWR 36–52 and 1–22, enter the calculation.

The one illustrative protection setting uses the marginal medians of the
5,000 saved all-age primary draws: initial VE 0.5677509714861295 and Ray
waning coefficient 0.14854546674470043 per 28 days, with a fixed two-week lag.
These are an explicit teaching setting, not a representative individual or a
new estimate of vaccine effectiveness.

Protection is zero before the lag, then
`max(0, min(1, 1 - (1 - initial_ve) * exp(beta * weeks_after_response / 4)))`.
Residual weekly burden is baseline burden times one minus protection. The
baseline is normalized to total 1 for this single season. The displayed total
is the sum of the residual over the whole season, including time before the
dose and the response lag. It is not an individual infection probability.

The weekly burden curves are linear between week centers with a constant
half-week extension at each end. Consequently, the filled polygon's integral
equals the sum of the weekly heights. The protection plot shows the onset
step explicitly. Animation interpolates adjacent precomputed date scenarios;
all resting states use the exact weekly calculation.

| Teaching state | Vaccination date | Remaining seasonal burden |
| --- | --- | ---: |
| Early | September 17–23, 2017; week 38 | 79.2993734212% |
| Late | February 4–10, 2018; week 6 | 86.5444377168% |
| Example minimum | November 26–December 2, 2017; week 48 | 68.4277340838% |

The example minimum is not the pooled manuscript's decision estimate, even
though its date is within the primary result's broad trough.

## Verification

- Independently evaluated all 29 dates with the manuscript's existing
  `R/decision_engine.R::evaluate_candidate_utilities`, using raw burden values.
  The normalized residual totals agreed within 2.22e-16; both implementations
  selected week 48 for this example.
- Inspected all three rendered views at the deck's 1280 × 720 dimensions.
- Exercised the sweep, slider endpoints, reset, and keyboard advance.
- Read the rendered SVG polygon area independently: the minimum view's area
  ratio was 68.4278%, agreeing with the displayed 68.4% after rounding.
- No browser warnings or errors were recorded during these checks.

The handoff should preserve the fixed epidemic curve, the two-week response
lag, the full seasonal sum, and the distinction between an illustrative
one-season optimum and the manuscript's decision across uncertain seasons.
