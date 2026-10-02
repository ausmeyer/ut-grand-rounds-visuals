# Slide 30: When can forecasts improve the decision?

**Current revision:** both slides now use the refitted August baseline and
a 2.3× threshold. See [August-baseline evidence](august-baseline-evidence.md)
for the active methods, results, and presenter states. The September analysis
below is retained as a historical record; it does not describe the current HTML.

This is a new exploratory simulation for the closing slide, separate from
the manuscript's reported results. States 1–4 show pre-pandemic epidemic / VE
pairs. State 5 applies two frozen pre-pandemic rules to later seasons, with
each paired draw's own optimum as the benchmark. The rejected FluSight
nowcast prototype has been removed. Slides 25, 28, and 29 are unchanged.

## Frozen training and evaluation

The design is recorded in `data/slide-30/threshold-example/design.json` and
`analysis-plan.json`. Training uses 5,000 seeded pairs from eight complete
pre-pandemic seasons, 2011/12–2018/19. The 2010/11 series begins at week 40
and has no September baseline; it was excluded before calibration rather
than extrapolating those weeks. All eight eligible seasons have weeks 36–39
and complete follow-up through week 22. The first 50 seeded training pairs
are displayed, without selecting on their optimum or visual appearance.

Each draw pairs a population-weighted national outpatient ILI curve with a
VE/waning/immune-delay draw. The curves come from the manuscript's cached
statewise quasibinomial GAMs, with coefficient uncertainty and a normal
0.75-week SD timing shift. Training uses the separate pre-pandemic model
cache. The state weights are the manuscript's fixed 2025 Census population
weights: this targets a common US population, not the historical population
as known before 2020. No manuscript source or checkpoint is changed.

The saved manuscript pre-pandemic sensitivity VE table includes later
source seasons, so it was **not** reused here. Instead, both training and
evaluation draw from only the 2010/11–2018/19 CDC VE source estimates using
the original exponential-effect-ratio model, Ray 2019 waning distribution,
eight-week VE reference, and 1–3-week response delay. The source VE season
for every draw is saved and checked. The 2010/11 VE estimate remains eligible
even though that season's epidemic curve lacks the required baseline.

For each draw:

- Baseline is mean latent national ILI in weeks 36–39.
- Benefit is the seasonal sum of burden times protection, with zero
  protection before the immune-response delay.
- Candidate dose weeks are 36–52 and 1–12, preserving each actual 52/53-week
  calendar. Each draw's optimum maximizes this benefit.
- The crude threshold is the median ratio of activity at the optimal date
  to baseline across the **5,000 training pairs**, rounded to the nearest
  0.1. Exact tied optima use their median ratio; zero-benefit draws would not
  identify a training date. All 5,000 training pairs are informative here.
- The fixed week maximizes mean benefit across those same 5,000 pairs.
- Threshold vaccination occurs at the first candidate week after week 39
  whose activity reaches the frozen threshold. A non-crossing would have
  no trigger date and no modeled vaccine benefit; none occurred in these
  completed evaluations.

The unrounded training median is **1.691351423986592**, so the frozen rule is
**1.7× September baseline**, a 70% increase. The fixed comparator is **week
47**. The exact results and source hashes were written to
`threshold-fit.json` before generating evaluation draws. This simple median
rule does not optimize threshold-policy performance on either training or
test seasons. Neither rule uses a future peak or full-season area at the
point of application.

The initial evaluation had 50 pairs from 2023/24–2025/26. After reviewing it,
the user requested a larger evaluation and the unusually early 2022/23
season. `extended-evaluation.json` documents that sequence. The two rules
remain frozen; sample-size expansion is not represented as a previously
prespecified analysis. There are now 5,000 draws across 2023/24–2025/26 and
a separate 5,000-draw 2022/23 stress test. The original 50-pair result remains
saved for provenance. Stage 5 shows the first 50 of the expanded later-season
run; its numerical summaries use **all 5,000**, not only the visible curves.

## What the reported metrics mean

Timing gap is the absolute elapsed-week distance to the closest optimal
candidate in the same paired draw. Signed errors in the data are negative
for early vaccination. Exact tied optima are treated as a set.

“Benefit vs. optimum” is the **sum of policy benefit divided by the sum of
per-draw optimal benefit**, expressed as a percentage. It is not absolute
VE, the fraction of infections prevented, or the mean of per-draw percentages.
The complement is pooled relative modeled loss. Per-draw relative loss and
its mean and median are also saved, so timing distance is not used as a
substitute for decision performance.

### Expanded later-season result: 5,000 pairs

| Rule | Median absolute gap | Mean absolute gap | Within 2 weeks | Benefit / optimum |
| --- | ---: | ---: | ---: | ---: |
| Fixed week 47 | 1 week | 1.5082 weeks | 4,029 / 5,000 | 98.2218% |
| 1.7× baseline | 1 week | 1.6120 weeks | 4,061 / 5,000 | 97.6034% |

All 5,000 draws cross the threshold. The threshold is one week late at the
median; fixed week 47 has median signed error zero. This comparison slightly
favors the fixed week in pooled benefit, while absolute timing medians match.

| Season | Draws | Fixed week loss | Threshold loss | Fixed median gap | Threshold median gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023/24 | 1,707 | 2.5405% | 1.3971% | 2 weeks | 1 week |
| 2024/25 | 1,662 | 1.6200% | 2.3796% | 1 week | 1 week |
| 2025/26 | 1,631 | 1.1162% | 3.5304% | 1 week | 2 weeks |

The threshold helps in the earlier 2023/24 pattern and tends to trigger
later than optimal in the other two seasons. This is not one universally
failing epidemic curve: VE and waning also change the optimal date within
each season. The initial 50-draw result had median gaps of 1 and 2 weeks,
with 98.7% and 97.7% retained benefit for fixed and threshold rules. The larger
run supersedes those numerical summaries. More draws reduce Monte Carlo
variation; they do not create more independent historical seasons.

## Additional 2022/23 stress test

2022/23 is excluded from the manuscript's primary analysis. Its original raw
cache also lacked September 2022, so the slide analysis downloaded complete
weeks 36/2022–22/2023 from the official CDC FluView service. The frozen CSV,
endpoint, retrieval time, and SHA-256 are in `early-data-source.json`. New
statewise models are fitted only in the slide workspace to pre-pandemic data
plus 2022/23, using the original quasibinomial formula, global k=14, season
k=12, gamma=1, REML, denominator weights, and missing-data treatment.

`early-model-manifest.json` records fit inputs and software. The reproducible
model cache is ignored by Git; the derived 5,000 paired draws and their
results are frozen. This is a separately fitted stress test of the unchanged
rules, not an addition to the manuscript's primary analysis.

### Early-season result: 2022/23, 5,000 pairs

| Rule | Median absolute gap | Mean absolute gap | Within 2 weeks | Benefit / optimum |
| --- | ---: | ---: | ---: | ---: |
| Fixed week 47 | 6 weeks | 6.3010 weeks | 7 / 5,000 | 74.6519% |
| 1.7× baseline | 2 weeks | 1.9348 weeks | 3,598 / 5,000 | 96.7760% |

All 5,000 pairs cross the threshold. In 4,762 pairs (95.24%), the trigger is
week 42 or 43. The median optimum is week 41. Both rules are late at the
median, by six and two weeks respectively. Threshold benefit exceeds fixed
week 47 benefit in every one of these 5,000 draws. The threshold's pooled
relative loss is 3.2240%, compared with 25.3481% for fixed week 47. Five
scenario optima lie on the earliest candidate, week 36; the finite candidate
grid is therefore relevant for this small tail.

These results support adaptation to this early season under the specified
simulation. They do not establish superiority across all future seasons.
The 2022 result is kept separate from the 2023–26 mixture rather than
implicitly changing its season weights. `early-results.json.gz` contains
all per-draw outcomes and `early-summary.json` the summaries. This additional
stress test is in the evidence notes; stage 5 continues to display the
2023–26 comparison pending further slide design decisions.

All 51 newly fitted models reached full outer convergence, and their
coefficient covariance matrices were positive definite. The repeated-1D-
smooth warning comes from the original global plus season-specific smooth
formula. A separate Alabama refit reproduced coefficients exactly.
`early-fit-diagnostics.json` records these checks.

## Scientific scope

This is a **chronologically separated retrospective simulation using
revised-data latent epidemic curves**. Full-season GAM fits help estimate
the activity curve, including its September baseline and crossing date.
Those smooth latent estimates are not necessarily available in real time.
No historical release-lag, backfill, real-time nowcast error, vaccine uptake,
missed-vaccination chance, or transmission effect is modeled here. The
results are conditional on the VE/waning distribution, one-dose model,
season mix, candidate grid, and modeled outpatient ILI outcome.

The rule is frozen before later-season evaluation, but that alone does not
make this a prospective surveillance evaluation. A next study must test
as-of-date inputs, reporting delays, and uptake. These results do not
establish that forecasts or nowcasts improve clinical decisions or that
patients should delay an available dose. No actual FluSight forecasts are
used in this version.

## Visual construction and alignment

The first three states retain slide 25's three-panel language. Regret is
remaining burden minus the minimum remaining burden in the same draw, so
its minimum is zero. All three red points mark the same dose date: at the
actual epidemic height, zero protection before immune response, and the
calculated minimum of regret. Protection curves are shifted to their own
optimal dates on a calendar axis. Nothing is hand-positioned or jittered.

State 4 uses the same 50 **pre-pandemic** profiles. Alignment maximizes the
shared area, the integral of the pointwise minimum, after normalizing each
curve's AUC to one. Linear interpolation and flat half-week caps preserve
the sum-of-weekly-values area. Pairwise shifts range from −20 to +20 weeks
in quarter-week increments. The representative profile maximizes the sum of
pairwise best overlaps; ties prefer smaller shifts. The selected reference
is draw 19, with no boundary shifts. Optimal dates and VE never choose the
alignment. Their red dots move by exactly the same shifts as their curves.

**Display heights** use each draw's September baseline, not AUC, so the
horizontal 1.7× threshold has the same meaning in states 4 and 5. Alignment
itself is unnecessary for calculating that activity ratio. The teal mean
uses only common modeled support, without extrapolated or zero-filled tails.
Its peak centers the descriptive state-4 axis; the threshold rule does not
use this peak. The pale band spans the middle half of aligned optimal dates.
The displayed dates' IQR changes from 2.75 to 2.4375 weeks; these values are
kept in notes rather than adding slide text.

State 5 uses a calendar axis with the same 796×370-pixel plot frame and common
vertical scale. Gray curves are the first 50 expanded evaluation pairs;
burgundy dots are their exact optima, teal rings their first eligible
threshold crossings, and the dashed vertical line is fixed week 47. The
same horizontal threshold remains visible. Weekly crossing markers can lie
above the line; they are not moved onto it or interpolated into earlier
fractional weeks. The summary compares all 5,000 evaluation pairs.

## Presenter states and reproducibility

1. **Start:** hold one pre-pandemic epidemic and protection curve still.
2. **One scenario:** reveal the actual regret minimum and matching markers.
3. **Sample scenarios:** add all 50 training pairs in eight seconds.
4. **Align seasons:** translate their curves and markers over 1.8 seconds,
   then reveal the mean, date band, and frozen training threshold.
5. **Test a threshold:** crossfade into the later-season curves and reveal
   policy markers and the comparison. This is a dataset change, not a morph
   implying a one-to-one relation between training and evaluation curves.

Direct loading and backward navigation are static. Start does not autoplay;
the first advance enters state 2. Right/PageDown/Space advance;
Left/PageUp return; Home/Reset restore Start. Changing state cancels an
ongoing animation. Reduced motion skips animation. `setStage(value)` remains
available for Slides.com integration.

Build offline with `python3 scripts/build_slide_30.py`. The extraction and
calculation scripts are `extract_slide_30_threshold.R`,
`build_slide_30_threshold.py`, and `fit_slide_30_early_season.R`. The initial
training fit is immutable when rerun. SHA-256 links the design, paired
inputs, frozen rules, and evaluation draws. Both languages independently
verify candidate utility, threshold dates, timing gaps, and losses;
`check_slide_30_threshold.R` is the independent R check. The main builder
checks that its displayed pre-pandemic pairs are exactly the first 50
training pairs and recalculates their 1,450 candidate totals.
