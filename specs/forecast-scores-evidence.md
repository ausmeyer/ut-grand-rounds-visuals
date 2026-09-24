# Slides 14–15: forecast distributions, targets, and scoring

Slide 15 revised September 24, 2026. Slide 14 is unchanged.
Both pages are self-contained 1240 × 540 iframes with their titles in Slides.com.

## Slide 14: unchanged archived example

All-age Texas influenza hospital admissions for the week ending December 21,
2024, from the forecast due December 11. This is a real public aggregate example.

- `#state=1`: ensemble median, 692 admissions.
- `#state=2`: central 50% prediction interval, 512–855.
- `#state=3`: central 95% prediction interval, 300–1,095.

The source is the [original FluSight ensemble submission](https://github.com/cdcepi/FluSight-forecast-hub/blob/b758798766336111d3ae0151a3bf4aea383d5d6c/model-output/FluSight-ensemble/2024-12-14-FluSight-ensemble.csv),
cached in `data/forecasting-intro/sources/ensemble.gz`. Selection: location 48,
reference date 2024-12-14, target `wk inc flu hosp`, horizon 1,
target end date 2024-12-21, output type `quantile`.
The [weekly summary](https://github.com/cdcepi/FluSight-forecast-hub/blob/b758798766336111d3ae0151a3bf4aea383d5d6c/weekly-summaries/2024-12-14/2024-12-14_flu_forecasts_data.csv)
establishes the due date. No eventual observation or score appears in Slide 14.

## Slide 15: synthetic targets and scoring illustration

Suggested Slides.com title: **What do we predict, and what counts as better?**
About 1.25 minutes. The intended audience should recognize the four primary
weekly horizons, distinguish quantiles from a point prediction, and interpret
relative WIS below 1 as better than the matched persistence baseline.

1. `#state=1`: synthetic hospital-admission history and a current-week through
   three-week-ahead forecast. Show the median and central 50%/95% intervals,
   with the label “23 quantiles per location and target week.”
2. `#state=2`: keep the entire plot fixed and reveal the WIS explanation and
   relative-WIS reference at 1. There is no plotted model score or outcome.

Controls: dropdown, previous/next buttons, and left/right keys when a form
control is not focused. Direct hash links work without visiting the first view.
The scoring text fades between views; reduced-motion preferences disable the
transition. There is no autoplay and no assumed cross-origin control of the
Slides.com parent. Use separate hash URLs in successive slides if desired.

### Synthetic data construction

The hypothetical history is 110, 155, 230, 305, and 390 admissions for weeks
-5 through -1. The four forecast medians are 470, 520, 550, and 570; specified
log-scale standard deviations are 0.13, 0.19, 0.24, and 0.28.

`build_forecast_scores.target_example()` generates all 23 quantiles from each
specified lognormal marginal using the standard-normal inverse CDF:
`Q(p) = median * exp(log_scale_sd * normal_inverse_cdf(p))`.
Values are retained to three decimals because this is a continuous teaching
illustration, not a submission file. The plot displays only the 0.025, 0.25,
0.5, 0.75, and 0.975 quantiles. The other tails are not drawn. All displayed
bounds fit the axis, remain positive, are nested, and widen with horizon.
Lines join discrete weekly marginals; the bands are not simultaneous
trajectory intervals. No parameters were fitted and no empirical forecast
performance or actual patient data are represented. “Synthetic example” is
visible in both views.

### Claim ledger

| Displayed claim | Evidence |
| --- | --- |
| Weekly laboratory-confirmed influenza admissions; horizons 0–3 | [Pinned 2026/27 hub README, primary target](https://github.com/cdcepi/FluSight-forecast-hub/blob/b758798766336111d3ae0151a3bf4aea383d5d6c/README.md), inspected from `data/forecasting-intro/sources/hub-readme.gz`. Optional preceding-week hindcasts are outside this core illustration. |
| 23 quantiles per location/target week | [Pinned hub tasks configuration](https://github.com/cdcepi/FluSight-forecast-hub/blob/b758798766336111d3ae0151a3bf4aea383d5d6c/hub-config/tasks.json), cached with the forecasting introduction; matches `QUANTILES` in the builder. |
| WIS evaluates interval width and missed observations; lower is better | [Bracher et al., PLOS Computational Biology 2021, equations 1–4](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1008618). The display is a plain-language summary, not a full formula; WIS also includes median absolute error. |
| Relative WIS below 1 is better than the matched persistence baseline | [CDC 2024/25 evaluation, Scoring](https://www.cdc.gov/flu-forecasting/evaluation/2024-2025-report.html), rechecked September 24, 2026. Comparisons require consistent scoring scale and matched cases; the page shows no calculated score. |
| Persistence carries forward the latest observed count, with uncertainty | Same CDC report, FluSight Operations: baseline median is the latest observation and uncertainty is based on observation noise. |

The scale at 1 is a conceptual comparison, not a performance finding. Interval
width alone and coverage alone do not establish accuracy. No hospital-use,
clinical-benefit, calibration, or age-specific claim is made.

## Build and verify

```sh
python3 scripts/build_forecast_scores.py
python3 -m unittest discover -s tests -p 'test_*.py'
SLIDE_PLAYWRIGHT=/absolute/path/to/playwright/index.mjs node tests/forecasting-intro.browser.mjs
```

Normal builds are offline. Source manifests retain decompressed SHA-256 hashes.
The existing archived-baseline and later-truth fixtures remain used by the
builder's numerical WIS regression tests, but do not supply the new Slide 15.
The tests independently recompute those archived scores as quantile losses.
Additional tests verify the synthetic distributions, generated HTML, unchanged
Slide 14, all 11 states across Slides 12–15, navigation, reduced motion, fixed
plot geometry, label bounds/collisions, and no external runtime requests.
Inspect rendered screenshots before publishing. No backend changes are needed.
