# Slide 26: the primary model favors weeks 47–48

This is the main result after slide 25's decision-model explanation. One large
national, all-age curve shows the mean burden left avoidable because of timing.
The title remains separate from the visualization for Slides.com integration.
The standalone slide uses the established 1280 × 720 canvas with a taller
plot filling the space below the title. Its editable source is `src/slide-26.html`.

## Sources and build

- `data/slide-26/inputs.json`: the 29 US/all-age rows from the saved
  `outputs/primary/tables/gam_primary_regret_curve.csv`, with all reported
  summary statistics retained. It records SHA-256 fingerprints for that
  table, the primary analysis manifest, `scripts/build_results_figures.R`,
  and `manuscript/overleaf_repo/manuscript.tex` in the manuscript project.
- `scripts/build_slide_26.py`: validates the frozen data, multiplies the mean
  regret values by 10,000, and writes the display JSON and self-contained HTML.
- `data/slide-26/slide-26.json`: display values and their provenance.
- `docs/slide-26.html`: the published standalone page.
- `tests/test_slide_26.py`: checks the 29-week curve, numerical comparisons,
  selected minimum, and its mathematical relationship to slide 25.

Build with `python3 scripts/build_slide_26.py`. Run focused checks with
`python3 -m unittest discover -s tests -p test_slide_26.py`.
The default build uses only the frozen local inputs. Extraction read the
saved manuscript results; it did not fit models or modify that project.

The all-age panel of manuscript Figure 2 is the source figure. The scaling
matches `scripts/build_results_figures.R` lines 453–470. The manuscript's
Decision Model subsection, national timing Results, and Figure 2 caption
define the quantity and its encounter denominator.

CDC's [Who Needs a Flu Vaccine](https://www.cdc.gov/flu/vaccines/vaccinations.html)
was checked September 28, 2026. It identifies September–October as generally
appropriate for most recipients needing one dose. The gray band follows the
manuscript's approximate weeks 36–44 display, clipped to the plotted range.
Month ticks are approximate calendar guides, not dates in one chosen year.

## Scientific meaning

The plotted quantity is mean absolute regret across 5,000 original simulations.
For a candidate date, each simulation's regret is its remaining burden minus
the remaining burden at that simulation's best date. The plotted average
retains the same preferred fixed date as the average remaining-burden curve
on slide 25. It differs only by a constant vertical shift and the 10,000-fold
display scaling. It does not subtract the minimum of the mean curve, so the
minimum is positive: no single fixed date is best in every simulated scenario.

The units are seasonal standardized ILI visits in a system with 10,000
outpatient encounters **each week**, not risk per 10,000 people. The display
uses the complete 29-date range, weeks 36–52 and 1–12, on linear axes beginning
at zero. Straight segments join the weekly saved means; no curve is refitted,
smoothed, or normalized for this slide.

| Vaccination week | Mean standardized avoidable ILI visits | Display |
| --- | ---: | ---: |
| 40 | 497.566582658 | 498 |
| 44 | 189.169858969 | 189 |
| 47 | 54.667818543 | ≈55 |
| 48 | 54.717128241 | ≈55 |

Week 40 matches the current manuscript's early-October comparison in its
national timing Results and Discussion. Its value was checked against the
US/all-age row of the saved primary regret table.

Week 47 is the numerical minimum. The teal band and two points emphasize
the nearly equivalent results at weeks 47–48; this is not an uncertainty
interval or the distribution of individually optimal dates. The scene shows
the mean curve without simulation-variation ribbons. The result uses the
primary waning model. Sensitivity to other waning models is reserved for
slide 28. The subtitle and all state prompts above the chart are omitted;
the plot fills the space previously reserved for that prompt row.

## Presenter states and handoff

1. **Start** (`#state=1`): static axes and September–October guidance band.
2. **Show the result** (`#state=2`): entering the state draws the mean curve
   over 2.2 seconds, then holds. The first forward advance from Start enters
   this state and plays the curve reveal.
3. **Highlight the window** (`#state=3`): show the full curve, weeks 47–48
   band and points, late-November/early-December label, and 498/189 versus ≈55
   comparison. Advancing during the reveal completes the curve immediately.

Right arrow, Page Down, and Space advance one state. Left arrow and Page Up
move back. Home and Reset return to Start. Numbered buttons select states
directly. Loading a hash opens its completed static view; page load does not
start animation. Reduced-motion preferences show the completed curve. Each
state updates the URL, selected control, chart description, and live status.
Integration can use `setStage(value)` for ordinary state transitions.

The transition to slide 27 is: “How much modeled protection is lost by
choosing a different date?” Slides.com integration is a separate step.
