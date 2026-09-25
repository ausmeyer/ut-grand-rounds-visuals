# Slide 21: Texas forecasts with wastewater lags

## Display

Same renderer as slide 19: four horizon views, observed admissions in black,
forecast median in dashed teal, 50% interval (25th–75th percentiles), and
90% interval (5th–95th percentiles). Dates, observations, and axes are identical
across the two slides. Both y-axes run from 0 to 14,000. No scorecard, caveat
badge, or extra explanatory text is shown.

Suggested Slides.com title: **Adding wastewater to the forecast**.
The visible subtitle is **Texas · MIGHTE-Base + wastewater lags**.

## Source identity and comparison

Inspected September 25, 2026 in `joint_twostage_distribution_study`:

- Forecast model: `distributional_gaussian_nll_joint_base_no_donors_wastewaterscan_lags124_revised_visualization`.
- Saved source: `outputs/visualization_rolling_revised/wastewater_lags/forecasts.csv`.
- Configuration and runtime: that run's frozen `manifest.json`, with comparator
  `distributional_gaussian_nll_joint_base_no_donors_wastewaterscan_lags124`.
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
that combines wastewater and NSSP. No model fitting, tuning, interpolation,
or new forecast generation occurs here. The saved forecasts are scored as
described below; no general performance-gain claim is made from this example.

The same frozen Texas truth as slide 19 is retained, October 5, 2024 to
April 25, 2026. The completed run has 82 weekly origins, 53 locations, four
horizons, and 23 quantiles. Within the observed target window, 81/80/79/78
Texas forecasts are plotted at horizons 0/1/2/3. Every eligible week is present,
including the January 25, 2025 reference week at all four horizons.

Each rolling fit restricts training origins and training target dates to its
anchor, using the frozen revised hospitalization history. This replaces the
entire previous forecast dataset; no old checkpoints or interpolated values
are mixed in. Run manifest, completion record, and date coverage are retained.

The supplied wide `forecast_intervals.csv` contains 50%, 80%, and 95% intervals.
The plotted 90% bounds are taken from the exact 0.05 and 0.95 quantiles in the
companion long `forecasts.csv`. The median and 50% bounds are verified against
the wide export. The largest plotted 95th percentile is 12,765.73, inside the
shared 14,000 axis limit.

## Texas-only relative WIS

The fifth, right-aligned legend entry displays rWIS for the selected horizon.
It uses all 23 quantiles from this exact run against submitted FluSight-baseline
forecasts on the same 50/49/48/47 Texas weeks used for slide 19. The plotted
curves retain every week. See the shared [scoring design and verification](slide-19-evidence.md#texas-only-rwis-design)
for the raw-count WIS definition, matched-key scope, score values, independent
checks, and retrospective interpretation. Full scoring quantiles and baseline
rows are retained in `scoring-source.csv` and `baseline-source.csv`, with hashes
in `sources.json`. The readout changes with every horizon control and direct URL.

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

It also checks continuous weekly coverage, labels, animations, keyboard/buttons/dropdown, direct
hash entry, reduced motion, and offline rendering. Screenshots are visually
reviewed before publishing.
