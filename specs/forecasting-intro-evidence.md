# Slides 12 and 13: FluSight introduction

Prepared September 23, 2026. Fixed 1240 × 540 iframe pages; titles stay in Slides.com. Each page supports `#state=1`, `#state=2`, and `#state=3`, plus dropdown, previous/next buttons, and keyboard arrows. No future observations, performance rankings, or accuracy claims appear in these two visuals.

## Slide 12: from surveillance to a forecast

Suggested Slides.com title: **Forecasting seasonal epidemics with FluSight**.

1. Texas weekly influenza hospital admissions available at the December 11, 2024 forecast deadline. The future region is empty.
2. Add individual models' submitted medians; show forecasting teams feeding the hub.
3. Fade individual forecasts and reveal the official FluSight ensemble median and central 95% prediction interval. Connect the ensemble to hospital planning.

The horizontal and vertical scales remain unchanged. All 35 participant models with Texas hospitalization median forecasts for this reference date are displayed; all four horizons are present. One large forecast is deliberately retained, and the y-axis accommodates it rather than clipping or silently omitting it. Lines connect discrete weekly marginal medians; these are not sampled epidemic trajectories. The band connects the weekly 2.5th and 97.5th percentiles, not a simultaneous interval for the entire trajectory.

### Source ledger

| Item | Evidence and implementation |
| --- | --- |
| Observed admissions | [Hospital target data at commit 47f7699](https://github.com/cdcepi/FluSight-forecast-hub/blob/47f76990a0cfba1cf226c7bc0087200777e77766/target-data/target-hospital-admissions.csv). Git commit timestamp December 11, 2024, 18:40:47 UTC, before the submission deadline. Texas FIPS 48, latest ten nonmissing observations ending December 7, 2024. No finalized or subsequent truth values are substituted. |
| Individual forecasts | [Official model archive, pinned commit](https://github.com/cdcepi/FluSight-forecast-hub/tree/b758798766336111d3ae0151a3bf4aea383d5d6c/model-output). Reference date December 14, 2024; target `wk inc flu hosp`; horizons 0–3; quantile 0.5; Texas. Model IDs and values are retained in `data/forecasting-intro/slide-12.json`. All dated CSV and Parquet submissions were inspected, including models not designated for the hub ensemble. |
| Official ensemble | [Original ensemble submission](https://github.com/cdcepi/FluSight-forecast-hub/blob/b758798766336111d3ae0151a3bf4aea383d5d6c/model-output/FluSight-ensemble/2024-12-14-FluSight-ensemble.csv). The submitted quantiles are used directly, not recomputed from the displayed model lines. Median values for Dec 14, Dec 21, Dec 28, Jan 4 are 584, 692, 769, 804. |
| Independent cross-check | [Weekly summary](https://github.com/cdcepi/FluSight-forecast-hub/blob/b758798766336111d3ae0151a3bf4aea383d5d6c/weekly-summaries/2024-12-14/2024-12-14_flu_forecasts_data.csv). Confirms the December 11 due date and medians for horizons 0–2. This summary omits horizon 3, which is taken from the original submissions. |
| 33 teams, 46 models in 2024–25 | [CDC 2024–25 evaluation, Results](https://www.cdc.gov/flu-forecasting/evaluation/2024-2025-report.html). These are published whole-season totals, not the number of Texas curves on the example date and not the Slide 13 participation measure. |
| Hospital planning | [CDC About Flu Forecasting, How flu forecasts can be used](https://www.cdc.gov/flu-forecasting/about/index.html). Forecasts can inform staffing, hospital beds, and treatment resources. The slide illustrates intended use; it does not claim that this particular forecast improved outcomes. |

Speaker note: models submitted forecasts to the hub, but not every submitted model was designated for ensemble inclusion. The official ensemble shown is the archived hub product. Its band is nominal forecast uncertainty, not a guarantee of 95% empirical coverage. Forecasts from this date were archived, not necessarily publicly communicated on the CDC forecasting webpage at that time.

## Slide 13: history, participation, and current targets

Suggested Slides.com title: **The forecasting target changed after COVID-19**.

1. A compact timeline establishes the early outpatient illness focus and the 2021–22 hospitalization focus.
2. Add the number of models contributing in at least half the scheduled weeks in each season.
3. Add the 2026–27 target set.

### Historical and target claims

| Claim | Evidence |
| --- | --- |
| FluSight began in 2013–14 | [CDC About Flu Forecasting](https://www.cdc.gov/flu-forecasting/about/index.html), background on the Predict the Influenza Season Challenge. |
| Earlier outpatient ILI focus; hospitalization focus in 2021–22 | [Mathis et al., Nature Communications 2024](https://www.nature.com/articles/s41467-024-50601-9), introduction and methods. The slide does not claim hospitalization forecasting first existed in 2021: earlier FluSurv-NET forecasts existed, as noted by CDC. |
| Current primary target: weekly laboratory-confirmed influenza admissions | [Pinned 2026–27 hub README](https://github.com/cdcepi/FluSight-forecast-hub/blob/b758798766336111d3ae0151a3bf4aea383d5d6c/README.md), Requested Forecasts. National and jurisdiction-specific quantiles, current week and three following weeks; optional preceding-week hindcasts are outside this introductory diagram. |
| Other targets | Same README: ED influenza visit proportion; category probabilities for direction and magnitude of admission-rate changes; peak-week probabilities; peak admission-count quantiles. All targets are optional. The panel does not imply that these targets were all introduced in 2026–27 or that each model submits every target. |

### Reproducible model-participation measure

This is a presentation-specific calculation, not a reproduction of CDC's performance-evaluation cohort or a team count. The unit is the archived **model identifier**, which can represent an individual model or a team's ensemble. One team can have multiple model identifiers. Model renamings are not retrospectively merged.

For each season:

1. Generate one scheduled date per week within the boundaries below.
2. Inspect the pinned repository tree for original `data-forecasts/MODEL/DATE-MODEL.csv` files (legacy) or `model-output/MODEL/DATE-MODEL.csv|parquet` files (modern).
3. Exclude identifiers beginning with `FluSight-`, case-insensitively; the old repository spells this `Flusight-`. This removes the hub's reference baseline and ensemble products, including other hub-reference variants. Retain participant-submitted ensembles.
4. Count each model-date once, irrespective of file format, targets, horizons, or locations. Include models with at least `ceil(scheduled_weeks / 2)` dates.
5. Include any official target. Thus the later seasons may include ED-only models; the bars are not restricted to hospitalization forecasts. Experimental-directory forecasts are excluded.

| Season | First dated round | Last dated round | Scheduled weeks | Required weeks | Included models |
| --- | --- | --- | ---: | ---: | ---: |
| 2021–22 | 2022-01-10 | 2022-06-20 | 24 | 12 | 23 |
| 2022–23 | 2022-10-17 | 2023-05-15 | 31 | 16 | 21 |
| 2023–24 | 2023-10-07 | 2024-05-04 | 31 | 16 | 34 |
| 2024–25 | 2024-11-23 | 2025-05-31 | 28 | 14 | 43 |
| 2025–26 | 2025-11-22 | 2026-05-30 | 28 | 14 | 49 |

Schedule sources:

- 2021–22 and 2022–23: [Mathis et al., Methods: FluSight operations](https://www.nature.com/articles/s41467-024-50601-9), January 10–June 20 and October 17–May 17 submission periods. Legacy filenames use the Monday of the forecast week even after due dates moved to Tuesday in January 2023. May 15 is the final Monday in the described period.
- 2023–24: [CDC season evaluation](https://www.cdc.gov/flu-forecasting/evaluation/2023-2024-report.html), October 1–May 1 solicitation interval; reference Saturdays October 7–May 4. The configuration also accepts May 11, but that lies outside this reported challenge interval.
- 2024–25: [CDC season evaluation](https://www.cdc.gov/flu-forecasting/evaluation/2024-2025-report.html), November 20–May 31; reference Saturdays November 23–May 31. The pre-challenge November 16 reference round is excluded. January 25 remains in the scheduled denominator even though CDC excluded that round from its performance evaluation.
- 2025–26: all 28 reference Saturdays for the season in the [pinned hub round configuration](https://github.com/cdcepi/FluSight-forecast-hub/blob/b758798766336111d3ae0151a3bf4aea383d5d6c/hub-config/tasks.json). This includes the configured late-May rounds.

An archived file's presence does not establish that its initial submission met the live deadline, that every requested forecast was present, or that all values were valid for scoring. Git history is not used here to reconstruct the original arrival time of every submission. These are archive-based model-week participation counts, not on-time, scoreable-forecast counts. CDC's 75%-of-targets evaluation rule is different from the requested 50%-of-weeks rule. The 2022–23 season is included here; the user-requested exclusion applies only to Slide 11's surveillance overlay.

The per-model dates, denominators, and decisions are retained in `data/forecasting-intro/participation-audit.json`. Both original recursive Git trees are saved, not just the resulting bars. Legacy tree: `c42804d2507ac590b4d900c28143db289f7d5645`; modern tree: `b758798766336111d3ae0151a3bf4aea383d5d6c`. `sources.json` lists exact URLs and decompressed SHA-256 checksums. The Parquet original and its CSV conversion are both retained. Public CDC archive and contributing-model attribution are preserved by source URL and model identifier.

## Build, verify, and release

```sh
python3 scripts/build_forecasting_intro.py
python3 -m unittest discover -s tests -p 'test_*.py'
npm test
SLIDE_PLAYWRIGHT=/absolute/path/to/playwright/index.mjs node tests/forecasting-intro.browser.mjs
```

The normal build is offline and uses only the pinned cached inputs. To re-download those same pinned inputs, `uv run --with pyarrow python scripts/build_forecasting_intro.py --refresh`. PyArrow is needed only to convert the single Parquet source during refresh, not for a normal build.

The browser test checks all six states at 1240 × 540, hash/direct links, controls, keyboard navigation, plot counts, finite paths, bounds, local cartoon loading, and no external runtime requests. Screenshot inspection checks label spacing and visual hierarchy separately. Eight Python checks across the repository and 46 existing poll checks pass locally. These changes have no backend or schema dependency and do not alter other numbered slide pages.

Release checklist: rebuild from cached inputs, run tests, inspect all six screenshots, compare the staged diff, publish through the existing Pages workflow, and verify both served HTML files match the generated files. If either page is broken after publishing, revert the dedicated introduction commit and republish; no data migration or poll rollback is required.
