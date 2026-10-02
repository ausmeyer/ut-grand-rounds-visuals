# Slide 31: Can the same rule adapt to an early season?

**Current revision:** both slides now use the refitted August baseline and
a 2.3× threshold. See [August-baseline evidence](august-baseline-evidence.md)
for the active methods, results, and presenter states. The September analysis
below is retained as a historical record; it does not describe the current HTML.

This standalone slide follows slide 30's later-season comparison with the
early 2022/23 season, first nationally and then in Texas, California,
Minnesota, and New York. The user selected those four states for geographic
coverage before their results were calculated. Every selected state is
retained. This is a new exploratory simulation, separate from the
manuscript's reported results. Slide 30 and its data are unchanged.

## Frozen rule and evaluation

The threshold is **1.7 times the evaluated location's own September mean**
(weeks 36–39), a 70% increase. Vaccination occurs at the first candidate week
after week 39 meeting or exceeding that value. The comparator is **week
47**. Both rules were chosen using only the pre-pandemic national pairs in
slide 30 and remain unchanged. There is no state-specific calibration.

The state panels also compare **vaccination in week 44**, selected by the
user to match the manuscript's end-of-October comparator. This addition is
recorded separately in `guidance-comparator.json`, preserving the original
draw design and source hashes. The manuscript's Results (lines 142, 164,
and 166 in `manuscript/overleaf_repo/manuscript.tex`) use week 44 for regret
and retained-protection comparisons. [CDC timing guidance](https://www.cdc.gov/flu/vaccines/keyfacts.html)
allows vaccination during September and October for most people requiring
one dose and aims for completion by the end of October (checked October 1,
2026). The plotted comparator models a dose **in week 44**, near the end
of that window; it does not represent every vaccination date permitted
within the window or simulate a campaign's timing distribution.

The multiplier is learned from pre-pandemic seasons; the baseline is
estimated separately in the evaluated season and location. Neither policy
uses a future peak or full-season AUC in its decision formula.

This is an out-of-period evaluation of a frozen decision rule, **not an
as-of-data surveillance backtest**. Epidemic curves, including the baseline
and crossing dates, come from retrospective full-season GAM fits. Reporting
delays, revisions, contemporaneous estimation error, and vaccine uptake
are not modeled. It is also not a geographic holdout: the selected states
contribute to the national training data. Applying a national rule locally
without recalibration tests its local behavior, not independence from the
training geography.

## Paired draws and source trace

`data/slide-31/design.json` records the selected states, frozen rules,
5,000-pair sample size per location, first-50 display selection, and SHA-256
pins to all reused slide 30 inputs. The national view reads the existing
`early-results.json.gz` without recalculation or changes.

For each selected state, `extract_slide_31_states.R` replays that state's
component of the previously generated national 2022/23 ensemble. It uses
the same cached fit, the same posterior seed plus the state's original
index in the full model list, and the same 5,000 VE parameter pairs and
timing shifts. There is no new fit or independent resampling. Each
state/draw is optimized separately. The posterior covariance, coefficient
draws, interpolation, and protection calculations are the same as in the
national analysis. The model cache SHA-256 is
`3cdb38369f61f85e2feb94411657bdf20348d77e9a4203bf314d6142f076c879`.

The separate slide-only model cache was fitted to pre-pandemic data plus
complete CDC 2022/23 weeks 36–22. Its inputs, diagnostics, and provenance
are documented in [slide 30's evidence notes](slide-30-evidence.md) and
`data/slide-30/threshold-example/early-model-manifest.json`. All VE source
seasons are 2010/11–2018/19. The exponential effect-ratio protection model,
Ray 2019 waning distribution, eight-week reference, and 1–3-week immune
response delay are unchanged. No manuscript source or checkpoint is edited.

The first 50 pairs are plotted in each location, without selection on the
result or appearance. All numerical summaries use **5,000 pairs per
location**. Shared VE and timing-shift draws support paired comparisons;
20,000 state pairs are not 20,000 independent epidemic seasons.

## Metrics and results

The optimum maximizes the sum of weekly burden times protection among
candidate weeks 36–52 and 1–12. The full observed seasonal window, through
week 22, is used to calculate benefit. The timing gap is absolute elapsed
weeks from the policy date to the nearest optimum within that same pair.
Exact tied optima are treated as a set.

“Benefit vs. optimum” is **the sum of policy benefit divided by the sum of
per-draw optimal benefit**, expressed as a percentage. It is not absolute
vaccine effectiveness, the fraction of infections prevented, or the mean
of per-draw ratios. The modeled outcome is outpatient ILI.

The national view retains its original two-rule comparison: median gaps
of 6 weeks for week 47 and 2 weeks for the threshold, retaining 74.6519%
and 96.7760% of modeled optimum benefit, respectively.

| State | Week 44 gap | Week 47 gap | Threshold gap | Week 44 benefit / optimum | Week 47 benefit / optimum | Threshold benefit / optimum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Texas | 5 weeks | 8 weeks | 4 weeks | 83.6674% | 66.6195% | 87.9671% |
| California | 2 weeks | 5 weeks | 1 week | 96.4838% | 82.8040% | 99.0815% |
| Minnesota | 3 weeks | 6 weeks | 2 weeks | 92.9233% | 69.4183% | 96.0256% |
| New York | 2 weeks | 5 weeks | 1 week | 95.6120% | 80.6589% | 99.0606% |

All timing gaps in the table are medians across the same 5,000 pairs.
The added week-44 calculations reuse the existing utilities and per-draw
optima; all prior fixed-week and threshold outcomes remain identical.

All 5,000 pairs in every location cross the threshold. Threshold benefit
exceeds week 47 benefit in 5,000 national, 5,000 Texas, 4,986 California,
4,992 Minnesota, and 4,882 New York pairs. This result supports adaptation
to this early season under the specified model; it does not establish
superiority across all future seasons.

The national **six weeks** refers to the median gap between week 47 and
the per-draw optimal dose date. It is not a measured six-week peak shift.

Texas is a useful limitation: 3,204 of 5,000 pairs have an optimum during
the weeks 36–39 baseline window, before the rule permits a trigger. Its
median threshold date is four weeks late relative to its own draw's
optimum. In 462 Texas pairs the optimum is the first candidate, week 36,
so an earlier allowed date could alter the benchmark. Six Minnesota pairs
also have an optimum at week 36; California and New York have none. These
finite-grid limitations are retained rather than dropping those draws.

## Presenter states and rendering

1. **Start:** hold the 50 national 2022/23 curves still.
2. **Early US season:** reveal the same frozen 1.7× line, fixed week 47,
   optimal-date dots, threshold-date rings, and national results in 0.7 s.
3. **Week 44:** crossfade over 0.9 s into four matched panels for Texas,
   California, Minnesota, and New York. Show only week 44's vertical line
   and its median-gap and retained-benefit column, with red optimal dates.
4. **Week 47:** add the fixed week's vertical line and comparison column
   over 0.7 s. Keep the week-44 results and all curves in place.
5. **Threshold:** add the 1.7× line, threshold-date rings, their legend,
   and the final comparison column over 0.7 s. Both earlier columns remain.

The national plot preserves slide 30 state 5's 796 × 370 frame and 0–7×
vertical scale. State panels share a 0–8× scale, selected from the largest
displayed value across all four states. Every curve is scaled to its own
September baseline. The red optimal-date dots and teal threshold rings
are placed at the actual weekly curve values; no date is jittered or moved
onto the threshold line. Weekly crossings can therefore lie above it.

The state-view axis label has been removed as requested. Curves, dots,
panel locations, and column positions remain fixed through states 3–5;
only the next policy's annotation and values fade in.

Start and direct hash loads are static. Right/PageDown/Space advance;
Left/PageUp go back; Home and Reset return to Start. Backward navigation
shows the complete state without replay. State changes cancel any active
animation, and reduced-motion preference skips animation. The title and
plot remain separable for the later Slides.com integration, which is not
part of this standalone build.

## Reproduction and checks

From the `ut-grand-rounds-visuals` directory:

```sh
python3 scripts/build_slide_31.py
/usr/local/bin/Rscript --vanilla scripts/check_slide_31.R
```

The builder uses frozen inputs and runs without network or manuscript
access. It recalculates all **580,000 state candidate utilities** in Python
and checks them against the R decision engine outputs. The observed maximum
absolute difference is **4.440892098500626e-16**. The separate R check
independently verifies baseline values, optima, trigger dates, timing gaps,
benefit, losses, and summary statistics for all **20,000 state pairs**.

To replay the state posterior extraction, provide the read-only manuscript
directory and repository root to `scripts/extract_slide_31_states.R`. This
requires the pinned, ignored slide-only model cache and checks its hash
before sampling. `states-draws.json.gz` freezes the extracted burden and
utility matrices; `states-results.json.gz` saves every evaluated pair;
`states-summary.json` saves aggregate outcomes and validation; and
`slide-31.json` contains the display subset and all-pair summaries.

The standalone source is `src/slide-31.html`; the generated, self-contained
page is `docs/slide-31.html`. Local browser checks at 1280 × 720 confirmed a
still Start, animated first advance, completed state panels, static reverse
navigation, Reset during animation, and direct state links. All four state
panels contain exactly 50 curves, 50 optimal dots, and 50 threshold rings;
there were no invalid paths or browser console warnings/errors. All 64
protected prior slide/data files remain byte-identical.
