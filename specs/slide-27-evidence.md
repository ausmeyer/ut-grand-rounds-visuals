# Slide 27: Timing changes how much protection we keep

Three horizontal bars put slide 26's timing comparisons on a relative scale.
The standalone 1280 × 720 slide has a separate title and a tall chart, matching
slide 26. Its editable source is `src/slide-27.html`.

## Source and definition

The source is `outputs/primary/tables/gam_primary_near_optimal_curve.csv` in
the sibling `flu_optimal_vaccine_estimate` project, restricted to US/all ages.
`data/slide-27/inputs.json` freezes the summary rows for weeks 40, 44, 47, and 48
and SHA-256 fingerprints for the source CSV, primary analysis manifest,
`R/decision_engine.R`, and `manuscript/overleaf_repo/manuscript.tex`.

Each week appears at three near-optimality tolerances (0.01, 0.05, and 0.10).
All relative-regret summary fields were checked for equality across those
rows before retaining one copy. Tolerance probabilities are not plotted.
The table contains the mean of 5,000 original primary-model simulations.
Extraction and construction read saved results; no models were rerun.

`summarise_near_optimal_curve()` in `R/decision_engine.R`, lines 246–276,
calculates each scenario's loss as the best protected burden minus the
candidate week's protected burden, divided by that same scenario's best
protected burden (zero when the best protected burden is nonpositive).
The chart shows the average of these relative losses, multiplied by 100.
It is not a ratio of the mean absolute losses displayed on slide 26.

| Week | Mean relative loss × 100 | Display |
| --- | ---: | ---: |
| 40 | 21.840529324902487 | 21.8% |
| 44 | 9.208826598271532 | 9.2% |
| 48 | 2.257486040040622 | 2.3% |

These rounded values match the manuscript's Consequences of Vaccination
During Common Calendar Windows subsection (line 166, checked October 1,
2026). Calendar labels are approximate and follow that passage.

The denominator is achievable modeled direct protection against outpatient
ILI surveillance burden. These percentages are neither vaccine effectiveness
nor individual influenza-risk reductions. The on-slide line states:
“Relative to the best vaccination date in each scenario.” Full interpretation
is retained in the accessible description and these notes.

Week 47 loses 2.779118275289502% by this relative measure. The original primary
decision minimizes mean absolute regret and selects week 47; relative regret
weights scenarios differently and is slightly lower at week 48. This slide
compares the manuscript's calendar examples without redefining the primary
objective. Waning sensitivity remains the subject of slide 28.

## Build and presenter states

Run `python3 scripts/build_slide_27.py` to validate the frozen inputs and
regenerate `data/slide-27/slide-27.json` and `docs/slide-27.html`.
The axis starts at zero and ends at 25%; bar widths use the unrounded means.

1. **Start** (`#state=1`): static date labels and the common percentage scale.
2. **Week 40** (`#state=2`): reveal 21.8% in gray.
3. **Week 44** (`#state=3`): add 9.2% in gray.
4. **Week 48** (`#state=4`): add 2.3% in teal.

Forward advances animate the newly added bar over 0.8 seconds. Previous bars
remain complete. Backward navigation, page load, and reduced motion show
static states. Fast advances finish earlier bars before adding the next.
Right/Page Down/Space advance; Left/Page Up go back; Home/Reset return to
Start. Buttons jump directly to a state. `setStage(value)` is available for
integration. There are no changing prompts or automatic page-load animations.

The handoff to slide 28 is: “How much we gain by waiting depends on how quickly
protection wanes.” Slides.com integration is a separate step.
