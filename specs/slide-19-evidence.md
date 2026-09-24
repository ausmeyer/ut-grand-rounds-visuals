# Slide 19: Texas forecasts without additional covariates

## Display and teaching purpose

One fixed 1240 × 540 chart, with four views selected by `#state=1` through
`#state=4`. These map to the saved FluSight horizons 0, 1, 2, and 3. The chart
compares rolling forecasts with observed Texas weekly influenza hospital
admissions. It does not present a single forecast issued at the start of a season.

- Observations: solid black, drawn above the forecast bands.
- Forecast median: dashed teal, the saved 0.50 quantile.
- 50% prediction interval: saved 0.25 to 0.75 quantiles.
- 90% prediction interval: saved 0.05 to 0.95 quantiles.
- Axes and observations remain fixed as the forecast layer crossfades.
- No internal slide title, scorecards, or editorial footers. Suggested title
  in Slides.com: **Forecasting influenza hospitalizations in Texas**.

## Source identity

Inspected September 24, 2026. All inputs are local to the supplied
`joint_twostage_distribution_study` project. No model fitting, recalibration,
data downloading, averaging of intervals, or forecast reconstruction occurs.

| Item | Source and interpretation |
| --- | --- |
| No-covariate model | `configs/study_config.json`, `corrected_nll_ablation_defaults` plus recipe `distributional_gaussian_nll_joint_base_spatial_no_donors`. `feature_recipe.spatial_mode` is `none`; there is no `external_covariates` block. Hospitalization history, calendar/regime terms, and the national hospitalization aggregate remain. Shared-location training is retained. |
| Saved predictions | `outputs/checkpoint_distributional_gaussian_nll_joint_base_spatial_no_donors_conditional_gaussian_log_sigma_v2.csv`. Select Texas FIPS 48, target `wk inc flu hosp`, horizons 0–3, and the five requested quantiles. Retain all rows with target dates inside the configured evaluation period and present in the truth snapshot. |
| Observed values | `data/imputed_sets/imputed_and_stitched_hosp_2026-04-25.csv`, `location_name == Texas`, fields `date` and `total_hosp`. Use the study's frozen observation vintage, not an independently refreshed series. The displayed dates are in the observed hospitalization era, not the earlier reconstructed training history. |
| Evaluation scope | Configuration requests October 1, 2024 to May 1, 2026, clipped to available truth. Texas observations run October 5, 2024 through April 25, 2026: 82 weekly observations. Forecast counts are 57, 56, 55, and 54 at horizons 0, 1, 2, and 3. |
| Forecast-time alignment | `scripts/joint_model.py` uses reference date = data cutoff + 7 days and hub horizon = model horizon minus 1. `target_end_date = reference_date + 7 * horizon days`. Thus the four views are 1–4 weeks beyond the data cutoff but 0–3 weeks beyond the hub reference date. Display the latter convention, consistent with saved output. |
| Archived data origins | Selected rows of `outputs/asof_anchor_audit.csv` verify an exact archived input vintage at every displayed reference date's data cutoff. The study uses revised pre-October-2024 training data and exact weekly vintages during evaluation. |

### Important naming boundary

The user requested MIGHTE-Base without additional covariates. The saved
hospitalization-only no-donor ablation uses **20 season bags**. The current
production name MIGHTE-Base maps to a **100-bag** model with wastewater and NSSP
covariates. This slide uses the former existing results; it is not a newly fitted
100-bag model with only the covariates removed. This distinction is recorded in
the generated data, source metadata, and accessible chart description.

The study's README and production-lineup configuration explicitly state that
the final production choice followed inspection of the 2024/25 and 2025/26
ablations. These forecasts are rolling-origin out-of-sample predictions, but
the period is not an independent confirmation set for that later selection.
The slide makes no comparative performance or operational-utility claim.

### Rendering integrity

The selected source rows are retained verbatim by field in
`data/slide-19/*-source.csv`. `sources.json` records original and selected-file
SHA-256 hashes, model configuration, runtime, scope, and source paths.
Forecasts are placed at target dates, without calendar shifts or smoothing.
Missing forecast weeks remain unfilled; separate line/band segments do not
bridge gaps. The shared y-axis includes every 95th-percentile bound in all
four views. There is no season, week, or curve selection based on apparent fit.

## Rebuild and verify

Offline rebuild from retained snapshots:

```bash
python3 scripts/build_slide_19.py
python3 -m unittest discover -s tests -p 'test_*.py'
SLIDE_PLAYWRIGHT=/absolute/path/to/playwright/index.mjs node tests/slide-19.browser.mjs
```

Explicitly refresh snapshots only when intended:

```bash
python3 scripts/build_slide_19.py --source-root /absolute/path/to/joint_twostage_distribution_study
```

Tests compare every plotted observation and quantile with the retained original
rows, check horizon/cutoff alignment and ordered intervals, and verify the
rendered SVG coordinates of all medians and bands. Browser checks cover all
four views, invariant observations/axes, missing-week boundaries, label layout,
navigation, interrupted fades, reduced motion, and offline rendering. Inspect
all four screenshots and verify live HTML equality after Pages deployment.
