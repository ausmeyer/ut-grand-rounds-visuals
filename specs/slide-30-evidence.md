# Slide 30: When can forecasts improve the decision?

The redesigned closing slide reuses slide 25's three-panel visual language:
paired epidemic and protection curves generate a regret curve for each
scenario. Each curve appears with three red dots marking its calculated best
vaccination date. This motivates the future forecasting question without
claiming that a forecast-informed decision rule has been evaluated.

## Source and mathematical meaning

`data/slide-30/inputs.json` pins `data/slide-30/source-draws/inputs.json` by
SHA-256 and records 50 draw IDs. The sample uses the same R seed 20260928
and sampling without replacement as slide 25, extended from ten to fifty.
Its first ten paired scenarios match slide 25's frozen inputs exactly, in
the same order. The full 50 are saved in the slide-30 source file; slide 25
retains its original ten. These are primary-analysis model simulations.

The extraction replay uses the unchanged cached manuscript fits and original
RNG sequences. All 13 source fingerprints match the earlier extraction.
The full 5,000-draw mean-regret curve agrees with the saved publication table
to 2.78e-17, and all 5,000 optimal utilities agree to 2.22e-16. Additional
source and validation provenance is in [slide 25's notes](slide-25-evidence.md).

For each of the 29 candidate dates, regret is the scenario's remaining burden
minus the smallest remaining burden in that same scenario. The minimum is
therefore zero, and its date is unchanged from the minimum of remaining
burden. This is an absolute difference in modeled seasonal burden, not the
relative loss fraction on slide 27. The plot uses one common linear scale
with qualitative vertical labels; burden units are seasonal sums of national
population-weighted outpatient ILI proportions.

The first ten examples remain:

| Draw | Best vaccination week |
| --- | ---: |
| 2269 | 47 |
| 3840 | 50 |
| 4653 | 49 |
| 2050 | 49 |
| 3434 | 52 |
| 3929 | 46 |
| 4028 | 47 |
| 37 | 46 |
| 644 | 44 |
| 2496 | 3 |

All fifty minima are unique among the saved weekly candidates. All 1,450 saved
candidate-date totals were checked against the protection calculation;
maximum absolute difference was 1.33e-15. No models were fitted and no
manuscript files were changed.

## Matching the dates across panels

All three panels use calendar position. The original 52- or 53-week calendar
is retained for each scenario, including its candidate-date coordinates.
Month labels are approximate; the underlying dates use MMWR weeks.
The epidemic dot is the actual burden value at the selected week. The
regret dot is the actual zero minimum of that scenario's calculated curve.

The lower plot shifts each protection curve to the scenario's best dose
date, preserving its complete saved parameter row and immune-response lag.
The protection dot marks the dose date itself and consequently lies at zero:
protection begins only after the response delay. The subtitle explicitly
states “Aligned to each optimal vaccination date.” This avoids interpreting
weeks since vaccination as if they were calendar dates. Its alignment is a
visualization of the selected date, not another optimization input.

Markers retain their exact coordinates without jitter; overlapping minima
remain overlapping. All three matching markers and curves appear together.
Prior examples fade while the active scenario is emphasized, then all fifty
remain visible at the end. These are scenario-specific best dates with the
scenario known. The fourth state summarizes their relative positions after
epidemic alignment; it does not turn the fifty optima into a clinical rule.

## Alignment by shared area

State 4 asks whether the optimal dates cluster more closely when the seasons
are aligned by epidemic shape. Translating a curve cannot change its own
AUC, so the alignment maximizes the **shared area**, the integral of the
pointwise minimum of two curves.

Each of the same fifty weekly epidemic profiles is linearly interpolated,
given flat half-week caps at its endpoints, and normalized to AUC 1. The caps
make the interpolated area equal to the original sum of weekly values before
normalization. For each pair of curves, the builder searches shifts from
−20 to +20 weeks in quarter-week increments and integrates shared area
exactly, including crossings between linear segments. No selected shift is
at a search boundary. It chooses the representative curve with the largest
sum of pairwise maximum overlaps (draw 511), then shifts each season to
maximize its overlap with that common reference. This is alignment to a
representative profile, not a global optimization of all simultaneous
pairwise overlaps. Ties prefer the smallest absolute shift.

The alignment uses only epidemic profiles. Optimal vaccination dates and
waning curves play no role in selecting the reference or shifts. Each red
dot is carried by exactly its epidemic curve's shift; its normalized height
is unchanged. The original weekly optimization is not rerun. All fifty
shifts are stored with their draw IDs in `data/slide-30/slide-30.json`.

The teal mean uses all fifty curves only over their common modeled support.
There is no extrapolation or zero imputation of missing tails in that mean.
The horizontal axis is recentered on the peak of the aligned mean. The large
red marker evaluates this mean at the median of the fifty shifted optimal
**dates**; it is not an optimum obtained by optimizing the mean epidemic.
The pale band shows the middle 50% of shifted dates.

| Spread measure | Calendar dates | After overlap alignment |
| --- | ---: | ---: |
| Interquartile range | 2.75 weeks | 2.125 weeks |
| Sample standard deviation | 2.818 weeks | 2.382 weeks |
| Full range | 14 weeks | 13.75 weeks |

The median shifted optimal date is 9.25 weeks before the aligned mean peak,
displayed as **~9 weeks**. Quartiles use linear interpolation (R type 7).
Some narrowing occurs but outliers remain. These are descriptive summaries
of the fifty illustrated scenarios, not results for all 5,000 simulations or
an evaluated timing rule. Normalization removes total-burden differences;
the vertical axis therefore says “Relative influenza activity.”

## Archived nowcasts on the rising limb

State 5 switches to **observed US influenza hospitalizations**, a different
outcome from the simulated outpatient ILI profiles in states 1–4. It shows
three season examples, 2023–24, 2024–25, and 2025–26, with actual FluSight
ensemble **horizon-0 nowcasts**. All seven source CSV files are frozen under
`data/slide-30/forecast-example/`; `sources.json` records each exact commit,
original URL, uncompressed SHA-256, and historical release time where
applicable. The offline builder verifies every hash before using the inputs.

The comparison week remains the first reported week with at least **four
times the early-November level**. The reference is the second Saturday in
November, using its value from the last archived target-data release on or
before November 19. This reference was available before each nowcast. The
rule does not use a future peak, full-season total, or seasonal mean. The
threshold and three target weeks were fixed before inspecting the original
forecast values. At the user's request, the displayed horizon changed from
2 to 0, keeping those target weeks and reference counts unchanged; that
choice also preceded inspection of the replacement nowcasts.

Later revised observations locate the comparison week retrospectively.
That week is placed at zero on the horizontal axis, and the preceding four
weeks are displayed. Each nowcast's **reference date and target end date
both equal the comparison week**. Each original archived file was released
two days before its reference Saturday. These are contemporaneous
current-week estimates, not the horizon-0 values from the earlier
horizon-2 submissions. No forecast model is refitted here.

All observed and nowcast values are divided by the same frozen reference
count within season. The left plot uses gray observed curves and red
comparison-week markers. The right panel uses the **same vertical scale**,
with a separate column for each season: teal points are nowcast medians,
vertical whiskers join the original 0.05 and 0.95 quantiles, and red points
show the subsequently observed values. These are 90% prediction intervals
for the current week's count, not intervals for the date of crossing a
threshold. No time jitter or joint forecast trajectory is introduced.
Weekly jumps explain why the three observed marker heights differ even
though each is the first reported week above the same relative level. No
point is asserted to be an inflection point, and no peak is displayed or
used in the calculation.

| Season | Frozen reference date / count | Nowcast reference and comparison week | Archive release | Observed | Nowcast median | 90% interval |
| --- | --- | --- | --- | ---: | ---: | --- |
| 2023–24 | Nov 11 / 2,763 | Dec 23, 2023 | Dec 21, 2023 | 15,755 | 11,531 | 8,692.702–14,528 |
| 2024–25 | Nov 9 / 2,481 | Dec 21, 2024 | Dec 19, 2024 | 16,127 | 10,669 | 7,345–14,153 |
| 2025–26 | Nov 8 / 1,672 | Dec 6, 2025 | Dec 4, 2025 | 7,451 | 5,777 | 3,868–8,127 |

All three nowcast medians underpredict the observed count; two observations
exceed the displayed upper interval. These discrepancies are retained.
Three retrospective examples do not measure general nowcast skill or
establish reliable detection of a vaccination window. **Four times the
reference is an illustrative level, not an estimate from the vaccine model
or a validated vaccination trigger.** This is not a test of nowcasting the
state-4 median optimal date. A broad timing window motivates investigating
whether current-week estimates could be sufficient; the displayed spread
alone does not establish that conclusion. A future study must derive a
trigger on a compatible outcome and scale, freeze it using training data,
and evaluate it at historical origins with contemporaneous data, suitable
uncertainty, comparator rules, and uptake.

The plot occupies the same x=64–860, y=150–443 frame as state 4, with the
same gray, teal, and burgundy palette and legend baseline. The comparison
panel occupies the previous right-hand summary area. A 1.4-second crossfade
replaces the simulated profiles with observed rises, then reveals the
nowcast comparisons. The curves do not morph into one another: the two
states use different datasets, outcomes, and vertical normalization.
The source label updates to US hospitalizations. The previously removed
question, footer, scenario-count label, and hospitalization-axis heading
remain absent.

Primary documentation: [FluSight forecast hub](https://github.com/cdcepi/FluSight-forecast-hub)
and [target data](https://github.com/cdcepi/FluSight-forecast-hub/tree/main/target-data).
The exact source versions used here are pinned in the local source ledger.

## Presenter states

1. **Start**: one epidemic and its calendar-aligned protection curve, held
   still, with an empty regret plot and no red markers.
2. **One scenario**: reveal the regret curve and its synchronized marker trio,
   at the actual selected week 47.
3. **Sample scenarios**: reveal all fifty pairs and their marker trios over
   eight seconds. Each new example arrives every 0.16 seconds, five times
   faster than the former ten-example cadence of 0.8 seconds.
4. **Align seasons**: enlarge the epidemic plot, normalize each season to
   equal total area, and translate each curve and its dot together over
   1.8 seconds. Then reveal the aligned mean and median date, with the
   median-date summary centered vertically beside the plot. The spread
   comparison remains in these notes rather than on the slide.
5. **Nowcast the rise**: crossfade into the three observed hospitalization
   rises aligned at the common illustrative level. Reveal the horizon-0
   nowcasts and their 90% intervals in the right panel. Direct loading and
   reduced motion display the completed comparison.

Loading any state or navigating backward gives a completed static view;
reduced motion also skips animation. The first arrow from Start enters state
2 and plays its reveal. Right/Page Down/Space advance, Left/Page Up go back,
and Home/Reset restore Start. Advancing past state 5 leaves it in place.
Changing state cancels an ongoing animation. Alignment summaries remain
hidden until the shifts finish; a direct state-4 link shows the completed view.
`setStage(value)` remains available for later Slides.com integration.

The projected “Next study” label and state-specific source label keep the
closing question separate from a demonstrated forecast benefit. Evaluation
of a future rule must still use information available at each decision date
and account for the chance of receiving a later dose, as discussed on slide
29. This slide performs no such evaluation and adds no uptake probabilities.

Say: “Different futures favor different vaccination dates. Can forecasts
help us distinguish those futures early enough to improve the decision?
When we align these fifty seasons by their epidemic shape, the middle group
of optimal dates comes closer together, though some outliers remain.”

For state 5: “If the useful timing window is broad enough, estimating where
we are now might be sufficient. Here are actual same-week ensemble
nowcasts from three seasons at one illustrative rising level. The next
project is to test whether such estimates can guide vaccination timing.”

## Build and verification

Run `python3 scripts/build_slide_30.py` to build only slide 30, or
`python3 scripts/build_closing_slides.py` for slides 28–30. The builder reads
the pinned local fifty-draw inputs, recomputes and checks candidate totals,
and uses `scripts/build_slide_30_forecast.py` to verify and normalize the
seven archived source files. That module recomputes the frozen example
selection and checks 69 quantile rows for unique values, ordering, target
dates, and horizons. The build writes `data/slide-30/slide-30.json` and
`docs/slide-30.html`. It does not
modify slide 25. The editable source is `src/slide-30.html`.

To repeat the read-only manuscript extraction, use
`Rscript --vanilla scripts/extract_slide_25.R /path/to/flu_optimal_vaccine_estimate data/slide-30/source-draws 50 30`.
The shared extractor's optional final arguments select the example count and
slide number; its two-argument defaults remain ten examples for slide 25.
Extraction replays cached fits and never refits or writes to the manuscript.

Browser verification covers the static landing state, first-advance reveal,
sequential scenario animation, all fifty matching marker trios, exact plotted
minima, alignment motion, reset/back navigation, interruption, and static
direct links. Independent midpoint quadrature at 0.01-week spacing selected
the same maximizing shift for all fifty profiles across the 161-point shift
grid; mean overlap differed from the exact integration by 4.8e-8. Every
mean point uses fifty observed segments, and the median marker lies on the
mean curve. The final rendered view is checked at 1280 × 720 before publication.

For the nowcast revision, the first four states retain their prior data.
Verification covers the nine displayed quantiles against the source CSVs,
matching horizon-0 reference and target dates, the shared plot scale,
forward crossfade, direct loading, back/reset, and animation interruption.
