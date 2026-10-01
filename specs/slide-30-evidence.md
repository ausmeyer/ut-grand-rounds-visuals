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
Month labels are approximate; the active week label gives the MMWR week.
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
scenario known; the ten optima are not averaged into a clinical rule.

## Presenter states

1. **Start**: one epidemic and its calendar-aligned protection curve, held
   still, with an empty regret plot and no red markers.
2. **One scenario**: reveal the regret curve and its synchronized marker trio,
   with the actual selected week 47 displayed.
3. **Sample scenarios**: reveal all ten pairs and their marker trios over
   eight seconds. Finish with “Could forecasts help choose among these dates?”

There is no fourth state. Loading an old `#state=4` link clamps to state 3.
Loading any state or navigating backward gives a completed static view;
reduced motion also skips animation. The first arrow from Start enters state
2 and plays its reveal. Right/Page Down/Space advance, Left/Page Up go back,
and Home/Reset restore Start. Advancing past state 3 leaves it in place.
`setStage(value)` remains available for later Slides.com integration.

The projected “Next study” label and simulated-scenario count keep the
closing question separate from a demonstrated forecast benefit. Evaluation
of a future rule must still use information available at each decision date
and account for the chance of receiving a later dose, as discussed on slide
29. This slide performs no such evaluation and adds no uptake probabilities.

Say: “Different futures favor different vaccination dates. Can forecasts
help us distinguish those futures early enough to improve the decision?”

## Build and verification

Run `python3 scripts/build_slide_30.py` to build only slide 30, or
`python3 scripts/build_closing_slides.py` for slides 28–30. The builder reads
the pinned local slide-25 inputs, recomputes and checks candidate totals,
and writes `data/slide-30/slide-30.json` and `docs/slide-30.html`. It does not
modify slide 25. The editable source is `src/slide-30.html`.

Browser verification covers the static landing state, first-advance reveal,
sequential scenario animation, all ten matching marker trios, exact plotted
minima, reset/back navigation, interruption, and static direct links. The
final rendered view is checked at 1280 × 720 before publication.
