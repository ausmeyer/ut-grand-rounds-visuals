# Slide 28: The answer depends on how protection wanes

The left panel shows the mean protection curve for each of three saved waning
analyses. The right panel gives the selected fixed vaccination week from that
analysis's complete US/all-age decision calculation. The mean protection
curve provides intuition; the calendar result is not an optimization of that
mean curve alone. Month labels are approximate; week numbers are authoritative.

## Frozen sources and calculation

`data/slide-28/inputs.json` holds 197 daily values from day 0 through day 196
for each model, plus the selected weeks and ten SHA-256 source fingerprints.
The source project is the sibling `flu_optimal_vaccine_estimate` repository.
The source files are the three saved `_ve_waning_draws.csv` files and their
analysis manifests, `outputs/sensitivity/summary/tables/robustness_suite_us_summary.csv`,
`R/decision_engine.R`, `R/protection_models.R`, and the manuscript source.

Each curve averages all 5,000 saved all-age draws. Each complete saved row
retains its calibrated initial protection, waning parameter, and response lag.
For time after the sampled response lag, the primary model uses
`1 - (1 - initial_ve) * exp(beta_wane_per_28d * elapsed_weeks / 4)`.
The alternative models multiply saved initial protection by the bounded
Spencer retention curve. With `u = elapsed_weeks / 2`, retention is
`(55 - 1.37*u + 0.18*u^2 - 0.03*u^3)/55` for the fast model and
`(55 - 0.50*u + 0.05*u^2 - 0.01*u^3)/55` for the hypothetical slow model.
Protection is zero before response and bounded to [0, 1] before averaging.

| Projected label | Saved analysis | Selected week |
| --- | --- | ---: |
| Primary | `gam_primary` | 47 |
| Alternative | `gam_spencer_ferdinands_fast_waning` | 46 |
| Sustained protection · Hypothetical | `gam_spencer_slow_waning` | 40 |

These are actual mean absolute-protection curves, with their different
back-calibrated initial values. They are not normalized to a common initial
effectiveness. The alternative model is not uniformly below the primary
model over time. The sustained-protection curve is explicitly hypothetical,
not another equally established empirical estimate.

On October 1, 2026, the independently implemented Python curve calculation
was checked against the production R `evaluate_candidate_utilities()`
function: a unit of burden at each elapsed week 0–28, every saved draw,
and vaccination at week 36 with the source calendar wrapping convention.
All 29 weekly means per model matched (maximum absolute differences
6.94e-17, 5.55e-17, and 8.33e-17). All 197 primary daily means also matched
the published Figure S4 source table within 1.11e-16. The saved selected-week
fields were checked independently of these curves. No fits or production
analysis pipeline were rerun; manuscript files were read only.

## Build, delivery, and presenter notes

To re-extract from the same saved manuscript outputs:

```sh
python3 scripts/extract_slide_28.py /absolute/path/to/flu_optimal_vaccine_estimate
python3 scripts/build_closing_slides.py
```

The usual offline build needs only the second command. Editable HTML is
`src/slide-28.html`; the standalone output is `docs/slide-28.html`.

1. **Start**: static axes and muted model labels.
2. **Primary**: reveal the teal protection curve and week 47.
3. **Alternative**: add the gray-blue curve and week 46.
4. **Sustained protection**: add the dashed hypothetical curve and week 40,
   then the takeaway: longer-lasting protection reduces the benefit of waiting.

Forward transitions reveal the new curve over one second. Load, backward
navigation, and reduced motion are static. Right/Page Down/Space advance;
Left/Page Up go back; Home/Reset return to Start. Buttons and `#state=1`–`4`
provide direct access. The title is a separate HTML element, and
`setStage(value)` remains available for later Slides.com integration.

Say: “If protection lasts longer, there is less to gain by waiting. This is
an empirical uncertainty that can move the decision.” The corroborating
surveillance sensitivities and the onset-aligned week 45 remain in notes or
questions rather than adding more marks to this comparison.

Handoff: “There is another consideration before turning a timing optimum
into clinical advice: will the person still receive the vaccine?”

The four views were rendered at 1280 × 720. Keyboard advance, back, reset,
rapid advances, and direct state loading were checked in the browser; the
console reported no warnings or errors.
