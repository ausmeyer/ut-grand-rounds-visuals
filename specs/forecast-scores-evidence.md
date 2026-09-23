# Slides 14–15: one forecast, then its evaluation

## Teaching purpose

For the grand rounds audience, use about 1.25 minutes for Slide 14 and 1.75 minutes for Slide 15. By the end, learners should identify a median and two central prediction intervals, distinguish one absolute error from MAE/RMSE, and interpret a relative WIS below 1 for the displayed comparison. Keep equations and methodological detail here, not on the projected slides.

This is a real public aggregate example, not synthetic patient data. Population: all-age Texas weekly influenza hospital admissions. It neither estimates an individual's risk nor supports age-specific conclusions or clinical advice.

## Visual sequence and presenter script

Suggested native Slides.com titles: **A forecast is a distribution, not just a line** and **Accuracy includes both the center and the uncertainty**. The iframes do not duplicate them.

Slide 14:

1. `#state=1`: “For this one week in Texas, the ensemble median was 692 admissions.”
2. `#state=2`: “The central 50% prediction interval ran from 512 to 855.”
3. `#state=3`: “The wider 95% interval ran from 300 to 1,095. The dot alone does not tell us the uncertainty.”

Slide 15 keeps precisely the same admissions axis and ensemble position:

1. `#state=1`: reveal 1,169 observed admissions. “This outcome fell outside both intervals.” Briefly explain that coverage is the fraction of many realized outcomes contained in their corresponding intervals. One miss does not establish poor calibration.
2. `#state=2`: “The median missed by 477 admissions. MAE averages absolute misses across forecasts. RMSE squares errors before averaging and taking a square root, so larger misses matter more.” The plotted quantity is absolute error, not an aggregate MAE or RMSE.
3. `#state=3`: “Weighted interval score evaluates the uncertainty too. Narrow intervals reduce width, but missing the observation incurs a penalty.” The width bracket and highlighted 95% miss illustrate two ingredients, not the entire numerical computation. All 23 quantiles enter the score, including the median and intervals not drawn.
4. `#state=4`: add the actual archived baseline. “For this forecast the ensemble's score was 319.3 versus 508.8 for the baseline, giving relative WIS 0.63. Lower is better; 1 means equal scores.” This is one case, not a season-wide ranking. The baseline median is 493, the last observed count in the forecast-time vintage, with its own archived uncertainty.

## Pinned data and claim ledger

| Quantity or claim | Source and exact selection |
| --- | --- |
| Ensemble's 23 quantiles | [Original FluSight-ensemble submission](https://github.com/cdcepi/FluSight-forecast-hub/blob/b758798766336111d3ae0151a3bf4aea383d5d6c/model-output/FluSight-ensemble/2024-12-14-FluSight-ensemble.csv), already cached in `data/forecasting-intro/sources/ensemble.gz`. Select reference date 2024-12-14, location 48, horizon 1, target `wk inc flu hosp`, target end date 2024-12-21, output type `quantile`. |
| Matching baseline quantiles | [Original FluSight-baseline submission](https://github.com/cdcepi/FluSight-forecast-hub/blob/b758798766336111d3ae0151a3bf4aea383d5d6c/model-output/FluSight-baseline/2024-12-14-FluSight-baseline.csv), same filters. Sample rows are excluded. |
| Forecast due date | [CDC weekly summary](https://github.com/cdcepi/FluSight-forecast-hub/blob/b758798766336111d3ae0151a3bf4aea383d5d6c/weekly-summaries/2024-12-14/2024-12-14_flu_forecasts_data.csv): forecast_due_date 2024-12-11. A due date is not a reconstructed submission timestamp. |
| Later observed count 1,169 | [Target data, June 18, 2025 repository snapshot](https://github.com/cdcepi/FluSight-forecast-hub/blob/adc3e7d4cd98a53f9233c188fd9024b81fd90f0a/target-data/target-hospital-admissions.csv), date 2024-12-21, location 48. This is not the June 25 final evaluation vintage cited by CDC. No later observations are included in Slide 14's embedded data. |
| MAE and RMSE | [Hyndman and Athanasopoulos, Forecasting: Principles and Practice, §5.8](https://otexts.com/fpp3/accuracy.html), scale-dependent errors. MAE targets the median; squared error targets the mean. Finite quantiles do not identify an exact forecast mean. |
| WIS | [Bracher et al., PLOS Computational Biology 2021, §2.2, equations 1–4](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1008618). Also checked the [2022 correction](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1010592), which corrects example values and figures, not these definitions. |
| Published CDC evaluation differs from this example | [CDC 2024–25 evaluation, Scoring](https://www.cdc.gov/flu-forecasting/evaluation/2024-2025-report.html): log-transformed counts and geometric-mean comparisons across matched forecasts. Here, arithmetic remains on the admissions-count scale to match the visual, and the ratio applies to one forecast only. Do not cite 0.63 as CDC's published ensemble relative WIS. |

Source CSVs are immutable-commit downloads; their decompressed SHA-256 checksums are in the corresponding `sources.json` manifests. The plotted and scored quantiles are in `data/forecast-scores/slide-14.json` and `slide-15.json`. The case continues Slide 12's dated Texas forecast; it is a teaching selection, not a representative performance sample.

## Worked calculations

For this outcome, `y = 1169`, median `m = 692`, so absolute error is `|1169 - 692| = 477 admissions`.

Across N forecasts, `MAE = sum(|y_i - f_i|) / N` and `RMSE = sqrt(sum((y_i - f_i)^2) / N)`. No separate numeric MAE and RMSE are shown for this single case: with N = 1 both would equal the absolute error and obscure their different behavior across cases.

For each of K = 11 central intervals `[l_k, u_k]` with noncoverage probability `alpha_k`:

```text
IS_k = (u_k - l_k)
       + (2 / alpha_k) * max(l_k - y, 0)
       + (2 / alpha_k) * max(y - u_k, 0)

WIS = [0.5 * |y - m| + sum((alpha_k / 2) * IS_k)] / (K + 0.5)
```

Intervals use quantile pairs from 0.01/0.99 through 0.45/0.55, including 0.025/0.975. The 95% interval alone has width `1095 - 300 = 795` and an upper-tail miss of `1169 - 1095 = 74`, hence interval score `795 + (2 / 0.05) * 74 = 3755`. That is not WIS. Combining all intervals and the median gives ensemble WIS **319.2778260869565**, baseline WIS **508.77217391304356**, and ratio **0.6275457708925836**. WIS has admission-count units here; its ratio is dimensionless.

An independent test recomputes WIS as the average of twice the pinball loss over all 23 quantiles. The build rejects missing/duplicated/crossing quantiles and missing truth. No density curve or missing quantiles are invented.

## Common misconceptions and quick checks

- A prediction interval describes uncertainty about the future observed count, not a confidence interval for an estimated mean. A nominal 95% interval is not a guarantee.
- A median is not necessarily a mean. This example labels it explicitly.
- Wider intervals are not automatically better: WIS trades width against misses. Coverage alone does not assess sharpness.
- One relative score below 1 does not establish superior seasonal performance, nor does one uncovered observation establish miscalibration.

Optional oral check: “If all intervals were made extremely wide, would WIS necessarily improve?” Answer: no; covering the outcome avoids miss penalties but adds width cost.

Optional oral check: “What would relative WIS of 1.2 mean?” Answer: for the same scored cases and scoring convention, the model's summarized score is 1.2 times the baseline's and is worse. It is not a probability or a 20% increase in admissions.

## Rebuild and verify

```sh
python3 scripts/build_forecasting_intro.py
python3 scripts/build_forecast_scores.py
python3 -m unittest discover -s tests -p 'test_*.py'
SLIDE_PLAYWRIGHT=/absolute/path/to/playwright/index.mjs node tests/forecasting-intro.browser.mjs
```

Normal builds are offline. `python3 scripts/build_forecast_scores.py --refresh` re-fetches only the two additional pinned inputs. Tests verify source hashes, exact forecast values, score equivalence, generated HTML, unchanged Slide 12, fixed geometry, reveals, navigation, text bounds/collisions, and no external runtime requests. Inspect the rendered states as well as test results before publishing. The iframes need no backend or database changes.
