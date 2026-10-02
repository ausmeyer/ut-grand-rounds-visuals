# Slides 30–31: August-baseline sensitivity analysis

This is the active analysis for both standalone slides. The earlier
September results remain unchanged under `data/slide-30/` and
`data/slide-31/`; their source implementation is preserved at commit
`962bbbb52882dd830e8b3da00b15b681602e837f`. New data and results live in
`data/august-baseline/`. Manuscript files and checkpoints are unchanged.

## Definition and calibration

The baseline is each sampled location/season curve's arithmetic mean in
**MMWR weeks 32–35**, used as an August window. A dose is triggered at the
first eligible week, starting with **week 36**, whose activity reaches
**2.3 times that baseline**. This is a 130% increase over baseline, not a
2.3-fold increase added to baseline. The same definition is used for
pre-pandemic calibration, the later US seasons, and the four states.

The design was saved before fitting these variants. The separate
pre-pandemic model was fitted using 2010/11–2018/19 only; 5,000 paired
draws sample 2011/12–2018/19 because 2010/11 lacks the baseline window.
The median activity/baseline ratio at the per-draw optimum is
**2.329045518878403**, rounded to **2.3**. For exactly tied optima, each
pair contributes its median ratio. The multiplier was frozen in
`threshold-fit.json` before fitting/extracting the new post-pandemic draws.
No post-pandemic result was used to choose the numerical multiplier.

The fixed comparator remains the previously selected **week 47**. The
August-inclusive pre-pandemic refit gives week 48 the highest mean utility:
0.2544969243 versus 0.2543412228 for week 47, a **0.0612%** advantage.
We retain week 47 for continuity with the prior comparison, rather than
calling it the exact optimum of the refitted training model.

**Week 44** is the manuscript's end-of-guidance-window comparator. It
models a dose in that week; it does not represent every date allowed by
September–October guidance or a population campaign's timing distribution.

## Scope and source data

**This is a post hoc exploratory sensitivity analysis.** The decision to
examine August was made after reviewing the September-baseline 2022/23
results. It must not be described as an untouched temporal holdout.
Freezing the new numerical multiplier before recomputing test outcomes
does not erase that design history.

All curves, including baseline activity and trigger dates, are derived
from full-season latent GAMs using revised surveillance data. The rule's
formula does not need a future peak, but these activity estimates use
later observations. This is not an as-of-data surveillance backtest.
Reporting delays, real-time baseline estimation, uptake, and missed-dose
risks require future evaluation. The outcome is modeled outpatient ILI,
not hospitalization, death, or influenza-specific infection probability.

The original quasibinomial state GAM structure is retained: season
intercepts, a global cubic-regression smooth (k=14), season smooths (k=12),
gamma=1, REML. The modeled window now begins at week 32. Separate fits use
pre-pandemic seasons alone, pre-pandemic plus 2022/23, and pre-pandemic
plus 2023/24–2025/26. All **153 state fits** converged and their coefficient
covariance matrices were positive definite.

Source CSVs, code hashes, population weights, and missingness are recorded
in `data-provenance.json`. The previously missing August 2022 observations
were acquired through the official CDC FluView download endpoint on
October 1, 2026 (October 2 UTC). The data retain missing observation rows
with zero likelihood weight, matching the original GAM. Delaware 2011/12
and DC 2015/16 have no observed August baseline weeks; their latent
baselines are inferred from the model. Colorado 2013/14, Oklahoma 2011/12,
and Utah 2018/19 each lack one observed August week. The selected four
states and all post-pandemic baseline windows have all four weeks observed.
These gaps are retained and disclosed; no outcome-based exclusions occur.

The saved draw IDs, season assignments, timing shifts, and pre-pandemic VE
parameters are replayed from the September analysis. New epidemic
coefficient draws use the original seeded procedure against the refitted
models. The four state curves are the corresponding components of the
national 2022/23 ensemble, using the same VE draws and shifts. National
weights retain the original fixed 2025 Census population target. Texas,
California, Minnesota, and New York were selected before their original
state results were calculated; there is no local threshold calibration.
They contribute to national training, so this is not a geographic holdout.

## Metrics and observed results

The outcome window remains weeks 36–52/53 and 1–22; candidate dose weeks
remain 36–52 and 1–12. August is used to establish baseline, not added to
the scored burden window. Each draw has its own optimum, maximizing the
sum of weekly burden times vaccine protection. The timing gap is absolute
elapsed weeks to the closest exactly tied optimum. “Benefit vs. optimum”
is the sum of policy utilities divided by the sum of per-draw optimum
utilities, not the mean of per-draw ratios or absolute vaccine effectiveness.

Each location uses 5,000 pairs; the first 50 seeded pairs are plotted.
More draws improve Monte Carlo precision without adding independent seasons.

| Evaluation | Week 44 gap | Week 47 gap | Threshold gap | Week 44 benefit | Week 47 benefit | Threshold benefit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| US 2022/23 | 3 wk | 6 wk | 2 wk | 91.6% | 74.5% | 96.1% |
| Texas 2022/23 | 5 wk | 8 wk | 4 wk | 83.7% | 66.5% | 90.9% |
| California 2022/23 | 2 wk | 5 wk | 1 wk | 96.4% | 82.8% | 98.6% |
| Minnesota 2022/23 | 3 wk | 6 wk | 1 wk | 92.9% | 69.5% | 98.7% |
| New York 2022/23 | 2 wk | 5 wk | 1 wk | 95.7% | 80.4% | 99.1% |
| US 2023/24–2025/26 mixture | 3 wk | 1 wk | 2 wk | 95.2% | 98.1% | 96.0% |

Every evaluation pair crosses the threshold. In the early season it
retains more pooled benefit than both calendar comparators. In the later
mixture, week 47 performs better than the threshold. The August change
does not improve every result relative to September. Texas still has a
four-week median threshold gap. Its 545 earliest-candidate optima indicate
a remaining limitation of the dose-date grid; corresponding counts are
5 nationally, 0 in California, 7 in Minnesota, and 1 in New York.

The national six-week gap is between week 47 and the per-draw optimal dose
date; it is not an estimated six-week shift in the epidemic peak.

## Slide behavior

Slide 30 keeps five states: static Start; one computed optimum; 50 paired
draws over eight seconds; alignment by maximum shared area; later-season
threshold comparison. Alignment uses unit-AUC curves only to choose
horizontal shifts. Display heights are divided by August baseline, and
optimal-date dots move with their curves without influencing the shifts.
The displayed mean uses only common modeled support. The threshold is
calibrated on all 5,000 original-calendar training draws, not on the 50
aligned display curves.

Slide 31 now has seven states: static Start; US week 44; add US week 47;
add US threshold; four states with week 44; add week 47; add threshold.
Earlier columns remain visible. Each change fades in the corresponding
rule, summary column, and—at the threshold step—crossing rings. The
national/state transition crossfades. Back, direct hashes, reset, and
reduced-motion entry show completed states without replaying animations.
The removed activity-axis caption remains absent.

## Reproduction and checks

`prepare_august_baseline.R`, `fit_august_baseline.R`, and
`extract_august_baseline.R` record acquisition, separate fitting, and
posterior extraction. `analyze_august_baseline.py fit` performs training
calibration and refuses to replace a different frozen fit. Evaluation
fitting/extraction require the frozen threshold file. The `evaluate` mode
produces all three policies' results and summaries.

Python independently recomputed **1,015,000 candidate utilities** across
5,000 training plus 30,000 evaluation pairs, agreeing with the original R
decision engine to less than 1e-12. `check_august_baseline.R` independently
confirmed training calibration and every evaluated baseline, optimum,
trigger date, timing gap, benefit, plotted height, and pooled/season summary.
It also confirmed that all **75** pinned prior data and unrelated slide
files remain byte-identical. Results are in `independent-validation.json`.

Rebuild only the published HTML from saved data with
`python3 scripts/build_slide_30.py` and `python3 scripts/build_slide_31.py`,
or both with `python3 scripts/build_august_slides.py`. These commands do not
refit models or contact the network. Edit the corresponding `src/` HTML
files. Expensive model caches are ignored; the public CSVs, paired draws,
results, specifications, model manifests, and scripts are versioned.
