# Slide 21: Texas forecasts with wastewater lags

## Display

Same renderer as slide 19: four horizon views, observed admissions in black,
forecast median in dashed teal, 50% interval (25th–75th percentiles), and
90% interval (5th–95th percentiles). Dates, observations, and axes are identical
across the two slides. Both y-axes run from 0 to 12,000. No scorecard, caveat
badge, or extra explanatory text is shown.

Suggested Slides.com title: **Adding wastewater to the forecast**.
The visible subtitle is **Texas · MIGHTE-Base + wastewater lags**.

## Source identity and comparison

Inspected September 24, 2026 in `joint_twostage_distribution_study`:

- Model: `distributional_gaussian_nll_joint_base_no_donors_wastewaterscan_lags124`.
- Saved source: `outputs/checkpoint_distributional_gaussian_nll_joint_base_no_donors_wastewaterscan_lags124_conditional_gaussian_log_sigma_v2.csv`.
- Configuration: `corrected_nll_ablation_defaults` plus that exact recipe in
  `configs/study_config.json`.
- Texas FIPS 48; target `wk inc flu hosp`; hub horizons 0–3; five saved quantiles.
- 20 season bags, 80% seasonal sampling, 250 center-fitting rounds,
  120 spread-fitting rounds, corrected Gaussian NLL, no spatial donors.
- The runtime, fitting profile, spatial recipe, and paired seed match the
  hospitalization-only model used for slide 19.
- The only added signal block is the available national WastewaterSCAN
  influenza A level plus backward 1-, 2-, and 4-source-week lags, with the
  configured availability features. NSSP and RSV are not included in this arm.

The forecast-time policy is the study's latency-constrained revised wastewater
snapshot, not a complete historical revision archive. Its source metadata
marks availability at source week plus two weeks. The backward lag block is
relative to that available source week. The config's `source_lag_weeks: 1`
is interpreted with the model's anchor/reference convention; it does not
override the source's own `available_date` restriction.

This is the paired 20-bag ablation, not the later 100-bag production lineup
that combines wastewater and NSSP. No model fitting, scoring, tuning,
interpolation, or new forecast generation occurs here. No performance-gain
claim is made from a visual comparison.

The same frozen Texas truth and archived hospitalization-origin audit as
slide 19 are retained. Target dates span October 5, 2024 to April 25, 2026,
with 57/56/55/54 plotted forecasts at horizons 0/1/2/3. The source has the
same missing-origin pattern as the currently available no-covariate output.

## Rebuild and checks

`python3 scripts/build_slide_21.py` rebuilds from retained source snapshots.
Use `--source-root /absolute/path/to/joint_twostage_distribution_study` only
for an intentional refresh. Source paths, SHA-256 hashes, model recipe,
runtime, vintage policy, and selected CSVs are retained in `data/slide-21/`.

Python tests check every saved quantile, interval ordering, horizon/date
alignment, matched configuration, date coverage, truth, and axes. The shared
browser test checks all four views and every rendered observation/quantile:

```bash
SLIDE_NUMBER=21 SLIDE_PLAYWRIGHT=/absolute/path/to/playwright/index.mjs node tests/slide-19.browser.mjs
```

It also checks gaps, labels, animations, keyboard/buttons/dropdown, direct
hash entry, reduced motion, and offline rendering. Screenshots are visually
reviewed before publishing.
