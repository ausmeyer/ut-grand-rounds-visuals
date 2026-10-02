# Slide 32: Can the shape of the rise guide timing?

This exploratory diagnostic examines the proposed relationship between
vaccination timing and the transition from accelerating to approximately
linear epidemic growth. It reuses existing pre-pandemic national ILI / VE
pairs. No model, decision threshold, or vaccination rule is fitted here.
Slides 30–31 and the manuscript inputs are unchanged.

## Source and definitions

- `data/august-baseline/training-draws.json.gz`: all 5,000 existing paired
  draws from eight historical seasons. SHA-256:
  `91a5921c4d8cfec5f27cb395953395c097375d38ec949e74a1e48107f6a25b03`.
- `data/august-baseline/alignment.json`: existing slide 30 AUC-overlap
  horizontal shifts. SHA-256:
  `b1c27a8d8860998ac52d4fd0fbfca1034ad7bd2a93867a4a49b2be5797a5427e`.
- The first 50 pairs appear in their saved order, without selection on
  agreement with the hypothesis. The season summary uses all 5,000.

Activity is the saved latent ILI probability multiplied by 100. We neither
subtract nor divide by an August or September baseline. The optima remain
those of the original saved utility, including its original outcome and
seasonal window; removing background from the plot does not redefine that
utility. Optimal vaccination is the unique utility maximum among weeks
36–52 and 1–12. Modeled protection onset adds the pair's saved 1–3-week
immune-response delay. It is an onset in the assumed protection model,
not a measured immune response.

The first derivative is estimated on the weekly grid by the centered
two-week secant `(ILI[t+1] - ILI[t-1]) / 2`, in percentage points per week.
No further smoothing or derivative-model fitting is performed. Lines
interpolate these values. A constant additive background cancels from
this operation; a time-varying background would not necessarily cancel.

For the mean and ensemble views, only the saved horizontal shifts are
reused. Cached baseline-scaled heights are not used. Aligned week zero is
the earliest shifted start of the 50 displayed September–May curves.
The mean uses common support with equal weight per pair; its derivative
uses common interior support. Separate median aligned vaccination and
onset dates are placed on the mean. These are population summaries,
not the dates of a representative pair.

The individual and season-summary views use each draw's **fastest rise**:
the maximum positive centered weekly derivative from week 36 through
week 21, with the earliest time chosen for an exact tie. This is a simple
retrospective descriptive reference, defined without using an optimum to
select a nearby local maximum. It may represent a later upswing in a
multi-wave season. It is **not necessarily the first exponential-to-linear
transition**, and does not exhaust possible definitions of that transition.

## What the diagnostic shows

For the 50 aligned curves, median vaccination is at aligned week 15.25;
median protection onset and the largest derivative of the mean are both
at 17.25. This neat relationship in the mean does not hold consistently
within every historical season.

Each row below is relative to each pair's **own** fastest rise, before any
pooling. Negative values indicate an earlier date. Intervals describe the
middle 50% of conditional draws within that historical season, not
confidence intervals across independent seasons.

| Season | Pairs | Median dose (weeks) | Median onset (weeks) | Onset middle 50% |
| --- | ---: | ---: | ---: | --- |
| 2011/12 | 599 | −9 | −7 | −8 to −5 |
| 2012/13 | 632 | −3 | −1 | −2 to −1 |
| 2013/14 | 610 | −3 | −1 | −2 to −1 |
| 2014/15 | 682 | −3 | −1 | −2 to 0 |
| 2015/16 | 628 | −8 | −6 | −8 to −2 |
| 2016/17 | 604 | −8 | −6 | −7 to −5 |
| 2017/18 | 609 | −3 | −1 | −1 to 0 |
| 2018/19 | 636 | −8 | −6 | −7 to −5 |

Across the saved mixture of 5,000 pairs, median onset is two weeks before
the fastest rise (middle 50%: six to one week before); 51.84% fall within
two weeks on either side. This is eight seasons with conditional Monte
Carlo variability, not 5,000 independent epidemic seasons. No claim is made
that the proposed shape relationship has been established or disproved
by this particular maximum-slope reference.

The existing curves are retrospective full-season latent estimates. Both
the centered derivative and identification of the seasonal maximum use
future information. Neither constitutes a tested nowcasting trigger.
The slide supports inspecting the hypothesis before proposing a real-time
rule; it does not establish a clinical recommendation.

## Presenter states and handoff

1. **Start:** static aligned mean, activity above weekly change.
2. **Mean timing:** reveal median vaccination and onset in both panels.
3. **50 draws:** all 50 paired curves and their own markers appear together
   over eight seconds. No resampling occurs in the browser.
4. **Each draw:** select any of the same 50 pairs or use previous/next draw
   buttons. Calendar time is restored. A dashed line marks its fastest rise.
   Vertical axes rescale per draw, retaining the original units.
5. **By season:** medians and middle-50% intervals for vaccination and
   onset offsets, using all 5,000 pairs grouped by season.

ArrowRight, PageDown, and Space advance; ArrowLeft and PageUp go back;
Home and Reset return to the static landing view. Loading `#state=N`
shows that completed state without animation. Reduced-motion preference
also suppresses animation. Native select arrow keys are reserved for the
draw selector. The accessible description contains the calculation and
scope, keeping projected copy short.

Rebuild with `python3 scripts/build_slide_32.py`; independently check with
`Rscript scripts/check_slide_32.R`. The source is `src/slide-32.html`, data
are `data/slide-32/diagnostic.json`, and the standalone output is
`docs/slide-32.html`. Slides.com integration remains separate.

The independent R calculation uses adjacent first differences and type-7
quantiles. It checks all 5,000 optima/offsets, all 50 displayed curves and
markers, reused shifts, mean curves, and every displayed seasonal interval.
Maximum disagreement is 1.78e−15; all timing and interval checks agree
exactly. The build also checks additive-background cancellation and the
equivalence of differencing the mean and averaging the differences.
Results are saved in `data/slide-32/independent-validation.json`.

Local browser checks at 1280 × 720 verified all five states, initial
stillness, first-advance marker animation, the completed 50-pair animation,
direct state loading, draw selection and endpoint controls, clicker keys,
and Reset during a transition. All 50 pairs had matching date coordinates
in the two panels and the saved 1–3-week onset delay. No browser errors or
viewport overflow were observed. Slides 24–31 remained byte-identical to
their preceding committed versions.
