# Slide 20: Additional surveillance signals

## Design

Three views in the established 1240 × 540 iframe:

1. Hospitalization history alone.
2. Add influenza ED visits and influenza A wastewater.
3. Add RSV ED visits.

The calendar is fixed. Rows resize between views with a 450 ms crossfade, and
each signal retains its own labeled scale. Black, blue, purple, and orange
curves are directly labeled. No editorial footers, geographic badges, results
claims, title inside the iframe, or additional methodological callouts.

Suggested Slides.com title: **Can other surveillance signals improve the forecast?**

## Sources and transformation ledger

Inspected September 24, 2026 in `joint_twostage_distribution_study`.
Every signal has 82 weekly observations from October 5, 2024 to April 25, 2026.
These are illustrative observed signal histories, not a reconstruction of
exactly what was available at every forecast origin.

| Signal | Exact source and selection | Displayed units and geography |
| --- | --- | --- |
| Hospitalizations | Same retained `data/slide-19/truth-source.csv` as the forecast slides, from the study's `data/imputed_sets/imputed_and_stitched_hosp_2026-04-25.csv`. | Weekly influenza admissions, Texas. |
| Influenza ED visits | `data/surveillance_covariates/nssp_influenza_national.csv`, `nssp_influenza_pct_ed_visits`; choose the latest available issue for each source week. Each retained row has issue May 30, 2026. | Percent of ED visits, United States. |
| Influenza A wastewater | `data/surveillance_covariates/wastewaterscan_flu_a_national.csv`, `wastewaterscan_flu_a_log10_pmmov`. No further transformation. | National equal-site median of within-site weekly medians of log10(PMMoV-normalized influenza A concentration + 0.00001). Require at least 10 sites. |
| RSV ED visits | `data/surveillance_covariates/nssp_rsv_national.csv`, `nssp_rsv_pct_ed_visits`; choose the latest available issue for each source week. Each retained row has issue May 30, 2026. | Percent of ED visits, United States. |

National covariates are the actual source scope used by the study's models,
not Texas-specific measurements. This scope is retained in the source metadata
and accessible description. The visible slide uses only short signal labels
and units, as requested.

No calendar shifting, min-max scaling, smoothing, gap interpolation, or new
averaging occurs in this slide builder. Missing values remain missing, not zero.
NSSP percentages are already percentage points. Wastewater is already on the
study's log10 scale, so its negative values must not be labeled as raw RNA counts.
The log10 pseudocount floor is retained exactly as supplied.

The study's `COVARIATE_STUDY_DESIGN.md` and
`data/surveillance_covariates/surveillance_covariate_sources.json` establish
the units, national aggregation, and source vintage policies. The slide does
not claim that any signal leads influenza consistently or improves forecasts.

Primary source attribution: [CDC NSSP through CMU Delphi](https://api.delphi.cmu.edu/epidata/covidcast/)
and [CDC NWSS / WastewaterSCAN](https://data.cdc.gov/resource/ymmh-divb.json).
The frozen source metadata records WastewaterSCAN's CC BY-NC 4.0 attribution
and research-use guidance. No external data were downloaded in this build.

## Rebuild and checks

`python3 scripts/build_slide_20.py` rebuilds offline from retained CSVs.
Add `--source-root /absolute/path/to/joint_twostage_distribution_study` only
to intentionally refresh them. `data/slide-20/sources.json` retains source
and snapshot hashes, selected rows, and original signal metadata.

Python tests verify every source value, date, unit, scale, geography, wastewater
minimum-site rule, and equality with slide 19's observations. Browser checks
verify every rendered vertex, all three views, calendar invariance, bounds,
label overlap, navigation, animation, reduced motion, and offline operation.
