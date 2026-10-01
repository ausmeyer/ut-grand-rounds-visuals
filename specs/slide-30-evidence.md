# Slide 30: When can forecasts improve the decision?

The redesigned closing slide reuses slide 25's three-panel visual language:
paired epidemic and protection curves generate a regret curve for each
scenario. Each curve appears with three red dots marking its calculated best
vaccination date. This motivates the future forecasting question without
claiming that a forecast-informed decision rule has been evaluated.

## Source and mathematical meaning

`data/slide-30/inputs.json` pins `data/slide-25/inputs.json` by SHA-256 and
records the ten draw IDs. These are the same saved primary-analysis
simulations already shown on slide 25, in the same order, originally sampled
with seed 20260928. They are neither newly invented example curves nor
operational forecasts. The source and validation provenance are in
[slide 25's evidence notes](slide-25-evidence.md).

For each of the 29 candidate dates, regret is the scenario's remaining burden
minus the smallest remaining burden in that same scenario. The minimum is
therefore zero, and its date is unchanged from the minimum of remaining
burden. This is an absolute difference in modeled seasonal burden, not the
relative loss fraction on slide 27. The plot uses one common linear scale
with qualitative vertical labels; burden units are seasonal sums of national
population-weighted outpatient ILI proportions.

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

All ten minima are unique among the saved weekly candidates. All 290 saved
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
Prior examples fade while the active scenario is emphasized, then all ten
remain visible at the end. These are scenario-specific best dates with the
scenario known. The fourth state summarizes their relative positions after
epidemic alignment; it does not turn the ten optima into a clinical rule.

## Alignment by shared area

State 4 asks whether the optimal dates cluster more closely when the seasons
are aligned by epidemic shape. Translating a curve cannot change its own
AUC, so the alignment maximizes the **shared area**, the integral of the
pointwise minimum of two curves.

Each of the same ten weekly epidemic profiles is linearly interpolated,
given flat half-week caps at its endpoints, and normalized to AUC 1. The caps
make the interpolated area equal to the original sum of weekly values before
normalization. For each pair of curves, the builder searches shifts from
−20 to +20 weeks in quarter-week increments and integrates shared area
exactly, including crossings between linear segments. No selected shift is
at a search boundary. It chooses the representative curve with the largest
sum of pairwise maximum overlaps (draw 3434), then shifts each season to
maximize its overlap with that common reference. This is alignment to a
representative profile, not a global optimization of all simultaneous
pairwise overlaps. Ties prefer the smallest absolute shift.

The alignment uses only epidemic profiles. Optimal vaccination dates and
waning curves play no role in selecting the reference or shifts. Each red
dot is carried by exactly its epidemic curve's shift; its normalized height
is unchanged. The original weekly optimization is not rerun. The ten shifts,
in the source order above, are 0, 0, 2, 0.75, 0, 3, 3.75, 3.25, 0, and −1 weeks.

The teal mean uses all ten curves only over their common modeled support.
There is no extrapolation or zero imputation of missing tails in that mean.
The horizontal axis is recentered on the peak of the aligned mean. The large
red marker evaluates this mean at the median of the ten shifted optimal
**dates**; it is not an optimum obtained by optimizing the mean epidemic.
The pale band shows the middle 50% of shifted dates.

| Spread measure | Calendar dates | After overlap alignment |
| --- | ---: | ---: |
| Interquartile range | 3.5 weeks | 1.875 weeks |
| Sample standard deviation | 3.240 weeks | 2.731 weeks |
| Full range | 11 weeks | 10 weeks |

The median shifted optimal date is 9.125 weeks before the aligned mean peak,
displayed as **~9 weeks**. Quartiles use linear interpolation (R type 7).
Some narrowing occurs but outliers remain. These are descriptive summaries
of the ten illustrated scenarios, not results for all 5,000 simulations or
an evaluated timing rule. Normalization removes total-burden differences;
the vertical axis therefore says “Relative influenza activity.”

## Presenter states

1. **Start**: one epidemic and its calendar-aligned protection curve, held
   still, with an empty regret plot and no red markers.
2. **One scenario**: reveal the regret curve and its synchronized marker trio,
   at the actual selected week 47.
3. **Sample scenarios**: reveal all ten pairs and their marker trios over
   eight seconds.
4. **Align seasons**: enlarge the epidemic plot, normalize each season to
   equal total area, and translate each curve and its dot together over
   1.8 seconds. Then reveal the aligned mean, median date, and spread summary.

Loading any state or navigating backward gives a completed static view;
reduced motion also skips animation. The first arrow from Start enters state
2 and plays its reveal. Right/Page Down/Space advance, Left/Page Up go back,
and Home/Reset restore Start. Advancing past state 4 leaves it in place.
Changing state cancels an ongoing animation. Alignment summaries remain
hidden until the shifts finish; a direct state-4 link shows the completed view.
`setStage(value)` remains available for later Slides.com integration.

The projected “Next study” label and simulated-scenario count keep the
closing question separate from a demonstrated forecast benefit. Evaluation
of a future rule must still use information available at each decision date
and account for the chance of receiving a later dose, as discussed on slide
29. This slide performs no such evaluation and adds no uptake probabilities.

Say: “Different futures favor different vaccination dates. Can forecasts
help us distinguish those futures early enough to improve the decision?
When we align these ten seasons by their epidemic shape, the middle group
of optimal dates comes closer together, though some outliers remain.”

## Build and verification

Run `python3 scripts/build_slide_30.py` to build only slide 30, or
`python3 scripts/build_closing_slides.py` for slides 28–30. The builder reads
the pinned local slide-25 inputs, recomputes and checks candidate totals,
and writes `data/slide-30/slide-30.json` and `docs/slide-30.html`. It does not
modify slide 25. The editable source is `src/slide-30.html`.

Browser verification covers the static landing state, first-advance reveal,
sequential scenario animation, all ten matching marker trios, exact plotted
minima, alignment motion, reset/back navigation, interruption, and static
direct links. Independent midpoint quadrature at 0.01-week spacing selected
the same maximizing shift for all ten profiles across the 161-point shift
grid; mean overlap differed from the exact integration by 2.5e-8. Every
mean point uses ten observed segments, and the median marker lies on the
mean curve. The final rendered view is checked at 1280 × 720 before publication.
