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

Inspected September 25, 2026. All inputs are local to the supplied
`joint_twostage_distribution_study` project. No model fitting, recalibration,
data downloading, averaging of intervals, or forecast reconstruction occurs.

| Item | Source and interpretation |
| --- | --- |
| No-covariate model | `outputs/visualization_rolling_revised/no_covariates/manifest.json`, comparator `distributional_gaussian_nll_joint_base_spatial_no_donors`. `feature_recipe.spatial_mode` is `none`; there is no `external_covariates` block. Hospitalization history, calendar/regime terms, and the national hospitalization aggregate remain. Shared-location training is retained. The saved forecast model ID appends `_revised_visualization`. |
| Saved predictions | `outputs/visualization_rolling_revised/no_covariates/forecasts.csv`. Select Texas FIPS 48, target `wk inc flu hosp`, horizons 0–3. Retain the five plotted quantiles in `forecast-source.csv` and all 23 in `scoring-source.csv`, with target dates inside the evaluation period and present in the truth snapshot. The companion `forecast_intervals.csv` is also retained for the selected instances. |
| Observed values | `outputs/visualization_rolling_revised/inputs/imputed_and_stitched_hosp_2026-04-25.csv`, `location_name == Texas`, fields `date` and `total_hosp`. Use the run's frozen input, verified against the manifest hash. It is identical to the previously plotted truth. |
| Evaluation scope | Frozen configuration requests October 1, 2024 to May 1, 2026, clipped to available truth. Texas observations run October 5, 2024 through April 25, 2026: 82 weekly observations. Forecast counts are 81, 80, 79, and 78 at horizons 0, 1, 2, and 3. |
| Forecast-time alignment | `scripts/joint_model.py` uses reference date = data cutoff + 7 days and hub horizon = model horizon minus 1. `target_end_date = reference_date + 7 * horizon days`. Thus the four views are 1–4 weeks beyond the data cutoff but 0–3 weeks beyond the hub reference date. Display the latter convention, consistent with saved output. |
| Rolling origins | `outputs/visualization_rolling_revised/no_covariates/date_coverage.csv` and `completion.json` record 82 complete weekly origins, 53 locations, four horizons, and all 23 quantiles: 17,384 instances and 399,832 quantile rows. Each origin is refitted with origin and training target dates no later than its anchor. Hospitalization inputs are frozen revised history, not historical release vintages. |

### Important naming boundary

The user requested MIGHTE-Base without additional covariates. This completed
hospitalization-only no-donor rolling run uses **20 season bags**. The study's
production name MIGHTE-Base maps to a **100-bag** model with wastewater and NSSP
covariates. This slide uses the isolated visualization results; it is not a
100-bag model with only the covariates removed. This distinction is recorded in
the generated data and source metadata, not an on-slide caveat.

The study's README and production-lineup configuration explicitly state that
the final production choice followed inspection of the 2024/25 and 2025/26
ablations. These forecasts are rolling-origin out-of-sample predictions, but
the period is not an independent confirmation set for that later selection.
The slide makes no comparative performance or operational-utility claim.

### Rendering integrity

The selected source rows are retained verbatim by field in
`data/slide-19/*-source.csv`. `sources.json` records original and selected-file
SHA-256 hashes, frozen run manifest, completion record, model configuration,
runtime, scope, and source paths.
Forecasts are placed at target dates, without calendar shifts or smoothing.
Every eligible weekly forecast is present, so each horizon renders as one
continuous segment. The January 25, 2025 reference week is included at all four
horizons, with target dates January 25, February 1, February 8, and February 15.
No values are interpolated or patched from the older checkpoint. The entire
forecast dataset was replaced with the completed rolling run.
The shared y-axis includes every 95th-percentile bound in all four views.
Both slides run to 14,000; slide 21's largest displayed 95th percentile is
12,765.73, compared with 10,805.20 on slide 19.
There is no season, week, or curve selection based on apparent fit.

The supplied wide `forecast_intervals.csv` contains 50%, 80%, and 95% intervals,
not a 90% interval. The plotted 90% bounds use the exact 0.05 and 0.95 quantiles
from its companion `forecasts.csv`. Median and 50% bounds are cross-checked
against the wide export. No interval-width conversion is used.

## Texas-only rWIS design

Score the two displayed revised-history runs without refitting or tuning. The
unit is a Texas reference-date/target-date/horizon forecast. Use raw weekly
hospital admissions, all 23 submitted quantiles, and the same frozen Texas
truth as the curves. Score horizons 0–3 separately over the plotted target
window. Compare against submitted `FluSight-baseline` predictions in the
study's `outputs/benchmark_forecasts.csv`.

Restrict both models and baseline to the identical complete forecast keys
available for all three at each horizon. Do not interpolate baseline forecasts,
drop plotted weeks, select seasons by fit, or reuse the study's older aggregate
scores. Baseline coverage is 50/49/48/47 matched weeks by horizon; the plots
retain 81/80/79/78 weeks. In particular, the submitted baseline archive lacks
the January 25, 2025 reference week, although it remains plotted.

Compute WIS as the mean of twice the pinball loss across the 23 quantiles.
Use the study's raw-count Reich Lab/scoringutils relative-skill definition,
not its log1p CDC variant. On identical support, the baseline-scaled pairwise
geometric-mean calculation equals mean model WIS / mean baseline WIS.
Verify that equivalence against the study implementation, and independently
verify WIS with its interval-score formulation. Values below 1 indicate lower
WIS than the baseline on the matched Texas weeks.

The visible addition is a right-aligned `rWIS: 0.xx` legend item. Coverage,
baseline identity, and revised-history provenance remain in accessible text,
hover detail, and source records. This is a descriptive retrospective
comparison, not independent prospective validation, a significance test, or
an estimate of operational benefit. No uncertainty interval for the aggregate
score is claimed. Method reference:
[scoringutils pairwise comparisons](https://epiforecasts.io/scoringutils/reference/get_pairwise_comparisons.html).

Verified September 25, 2026: all eight values agree with the study's
`pinball_wis` and `scoringutils_scaled_relative_skill` functions within 1e-12.
The functions were executed from the study source without modifying it
(`scripts/study_common.py` SHA-256
`845176becb5f9a5c02de941259eac0c51eae98dad0c13c6789934e9c6c13c4f9`).
Tests independently recompute every WIS via interval scores and scaled skill
via the three-model pairwise geometric mean. All plotted data match the
previous commit; only score metadata and legend presentation change.

| Hub horizon | Matched Texas weeks | No added covariates rWIS | Wastewater lags rWIS |
| --- | ---: | ---: | ---: |
| 0 | 50 | 0.66706835 | 0.66885190 |
| 1 | 49 | 0.60015470 | 0.59681535 |
| 2 | 48 | 0.59868959 | 0.60124833 |
| 3 | 47 | 0.58314931 | 0.58215779 |

Both models therefore display 0.67, 0.60, 0.60, and 0.58 at two-decimal
precision. This does not imply identical unrounded scores; hover detail gives
four decimals and the matched-week count.

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
four views, invariant observations/axes, continuous weekly coverage, label layout,
navigation, interrupted fades, reduced motion, and offline rendering. Inspect
all four screenshots and verify live HTML equality after Pages deployment.
