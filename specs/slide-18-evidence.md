# Slide 18: from separate models to shared learning

## Teaching and display

Two views in a fixed 1240 × 540 iframe. Keep the title in Slides.com:
**From separate models to shared learning**.

Objective: identify the progression from regularized VAR through separate
state-specific LightGBM fits to shared multi-location training, and distinguish
the center and spread used to derive forecast quantiles. The setting is the
presenter's influenza hospitalization forecasting research, not patient care.

- `#state=1`: three model blocks, straight arrows, and “Ensembling throughout.”
- `#state=2`: the same pooled-model block moves into the center. Location
  inputs and a schematic distribution fade in. Center, spread, and “Derive 23
  forecast quantiles” label the distribution. The density is turned sideways
  at a future point on a short schematic time series: time is horizontal,
  forecast values and spread are vertical. All text stays upright.
- Forward, backward, direct-entry, keyboard, and dropdown navigation work.
  Reduced motion skips transitions. Direct entry to state 2 plays the build.
- No dates, model rankings, accuracy improvements, formulas, extra controls,
  clinical cases, or speaker-note text are displayed.

## Source and interpretation ledger

Paths below are relative to the parent SantillanaLab directory unless indicated.
Sources were inspected September 24, 2026. No model is fitted by this slide.

| Visible content | Supporting source | Scope |
| --- | --- | --- |
| Regularized VAR | `flusight_2022/var_experimental/flu_var_all.Rmd`, `constructModel` with `struct = 'HLAGOO'`, `cv.BigVAR`, and `VAR_regularized` outputs | One part of the earlier modeling program, not an exhaustive model inventory. VAR itself can link locations; the title does not imply all earlier models were independent. |
| State-specific LightGBM, separate fits | `flusight_2024/flu-forecast-2024/src/lgbm-predict_future-production_individual.py`, `generate_prospective_forecasts`, lines 77–108 | Loops over locations, constructs a model using location-specific parameters, and fits it to that location's series. |
| Pooled LightGBM, shared training across locations | `flusight_2025_meyer_ensemble/joint_twostage_pool_test/README.md`; `joint_twostage_pool.py`, pooled feature construction with location indicators and `fit_two_stage_one_bag` | Shared training, not a joint probability distribution across locations. No claim about deployment start date or comparative skill. |
| Center and spread | Same pooled script, two-stage fit, lines 366–411, and `predict_quantiles`, lines 431–456 | Stage 1 uses squared-error LightGBM for the transformed center; Stage 2 estimates spread with the center frozen. These are prediction-specific distribution parameters, not two coefficients for the entire model. |
| Derive 23 forecast quantiles | Same pooled script uses `norm.ppf` with predicted center and spread and transforms back with `expm1`; `scripts/build_forecast_scores.py` supplies the 23 quantile levels already used on slide 15 | The count is reused directly from the existing verified slide-15 builder. Its pinned CDC source is recorded in `specs/forecast-scores-evidence.md`. |
| Ensembling throughout | User's stated development history and accepted `UT_grand_rounds/PRESENTATION_OUTLINE.md`; later implementation in `flusight_2025_mighte_joint/src/generate_joint_adaptive_ensemble.R` | A qualitative research-history statement, not a claim that identical components or weighting were used every year. |

The bell curve is a schematic standard-normal density on an illustrative
transformed scale, not synthetic hospitalization observations or a measured
forecast. It is identified as schematic in the generated metadata and accessible
description. There are no numerical axes or performance results. The displayed
spread marker spans one standard deviation on each side of the center solely
to locate spread; it is not labeled as a prediction interval. The gray trace
and dashed continuation are unscaled schematic context, not additional
hospitalization data. The sideways density represents one future time point;
its horizontal width encodes density, not another segment of the time series.

Pooling and distributional fitting are distinct choices. This graphic does not
claim pooling made distributional fitting possible, that Gaussian assumptions
hold without validation, or that a final ensemble must be a single Gaussian.
The named states are examples of shared training inputs, not an exhaustive
location list or one aggregated prediction for all states.

## Rebuild and verify

```bash
python3 scripts/build_slide_18.py
python3 -m unittest discover -s tests -p 'test_*.py'
SLIDE_PLAYWRIGHT=/absolute/path/to/playwright/index.mjs node tests/slide-18.browser.mjs
```

The standard-normal illustration is computed analytically, saved in
`data/slide-18/slide-18.json`, and embedded in the self-contained HTML. No network
request, package download, data refresh, or model fit occurs in the iframe.

Tests check reproducibility, symmetry and values of the schematic density,
agreement with slide 15's quantile count, all curve vertices, center/spread
alignment, label bounds and overlap, navigation, stable pooled-model identity,
forward/reverse and direct-entry animation, interrupted transitions, and reduced
motion. Inspect screenshots at 1240 × 540 before publishing. Verify the Pages
deployment and exact live HTML against the tested build before handing off.
