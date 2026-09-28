# Slide 25: plausible seasons and waning scenarios

Standalone slide 25 follows the single-scenario illustration on slide 24.
Its title is “We compare vaccination dates across many plausible seasons and
waning scenarios.” A static landing view precedes three builds showing one
pair, ten sampled pairs, and the mean remaining burden across all 5,000
original primary-analysis simulations.

## Files and build

- `src/slide-25.html`: editable HTML, SVG charts, and presentation controls.
- `data/slide-25/inputs.json`: ten saved scenario pairs, the full-simulation
  mean, validation results, selection seed, and source SHA-256 fingerprints.
- `scripts/extract_slide_25.R`: optional extraction from the read-only
  manuscript project and its cached fitted models.
- `scripts/build_slide_25.py`: standalone build using the frozen inputs and
  Python's standard library; checks all 290 displayed candidate-date totals.
- `data/slide-25/slide-25.json`: complete display data including protection
  curves and the first scenario's residual curves.
- `docs/slide-25.html`: self-contained 1280 × 720 standalone page, with the
  separate title and established 1240 × 540 visualization area.

Build with `python3 scripts/build_slide_25.py`. Data, charts, and code are
embedded in the HTML; no runtime network requests or external libraries are
needed. The manuscript project is not needed to rebuild the HTML.

To repeat the optional scientific extraction, run
`Rscript scripts/extract_slide_25.R /path/to/flu_optimal_vaccine_estimate data/slide-25`
from this repository. It reads the cached fit identified by the publication
manifest and checks the manifest's input hashes. It never fits models or
writes to the manuscript directory. It requires the manuscript's R packages.

## Scientific meaning

The primary all-age analysis samples epidemic seasons and vaccine parameters
independently. A `draw` ID connects the sampled national epidemic with the
complete protection-parameter row used for that simulation. Each row keeps
its saved initial VE, Ray waning coefficient, and immune-response lag together.
Protection is zero before that lag, then follows the bounded exponential
effect-ratio model used by `R/decision_engine.R`.

The displayed ten draw IDs are 2269, 3840, 4653, 2050, 3434, 3929, 4028, 37,
644, and 2496. They are a simple random sample without replacement, selected
with R seed 20260928. Selection occurs after the national simulation replay
so it cannot change the original RNG sequence. These examples are not a
confidence band and are not used alone to calculate the final mean.

The extractor replays the original epidemic sampling seed 20260507 and each
state's original coefficient-draw RNG sequence. It reads all 51 cached state
fits, uses the same linear timing shifts and population weights, and sums the
national protected burden with the original decision engine. Matrix evaluation
and streaming avoid materializing a large table of all state/draw/week rows.
Both 52- and 53-week calendars and each historical season's available burden
weeks are retained. The first displayed season, 2010/11, begins at week 40 in
the original prediction grid; the plot leaves the earlier interval blank.

For each candidate date, remaining burden is that simulation's total national
burden minus its modeled protected burden. The mean is calculated across all
5,000 simulations before choosing the minimum. No scenario is normalized by
its own total burden, and individual optimum dates are not averaged.

The output plot uses one common linear scale in raw seasonal sums of national
population-weighted ILI proportions. It is labeled qualitatively (“More” and
“Less”) because this slide explains the calculation; numerical encounter units
are introduced with the manuscript results on slide 26. This quantity is not
an individual probability of influenza. The epidemic and protection input
plots use calendar position and weeks since vaccination, respectively.

## Numerical verification

- All 29 national mean-regret values agree with the saved primary publication
  table: maximum absolute difference 2.775558e-17.
- All 5,000 per-simulation maximum protected-burden values agree with the
  saved national optimal-week draws: maximum absolute difference 2.220446e-16.
- An independent Python calculation of the ten displayed scenarios across
  all 29 dates agrees with the R engine: maximum difference 1.332268e-15.
- The full mean remaining-burden curve selects week 47. Subtracting the mean
  of each simulation's minimum remaining burden yields the mean-regret curve
  without changing that optimum.

## Presenter behavior

The four states are:

1. **Start** (`#state=1`): one epidemic/protection pair, held still, with an
   empty date-comparison plot.
2. **One scenario** (`#state=2`): entering this state traces the date comparison
   and returns to an example date.
3. **Sample scenarios** (`#state=3`): entering this state reveals the ten paired
   inputs and outputs over five seconds.
4. **Average outcomes** (`#state=4`): the mean from all 5,000 simulations and
   its minimum appear immediately. The exact week label is reserved for the
   following slide.

Right arrow, Page Down, or Space advances one state. Left arrow and Page Up
move back. Reset and Home return to the static landing state. The numbered
buttons select their states directly. Loading any hash opens a resting view;
animations play on transitions into states 2 and 3. Reduced-motion preferences
show their completed views. No week slider is included because the preceding
slide already provides date exploration.

For integration, use ordinary state transitions through `setStage(value)`.
The original three states are now numbered 2–4. There is no pending-animation
flag or separate first-advance action.

The regression check `node --test tests/slide-25-animation.test.mjs` verifies
that animation progress stays in [0, 1], including when a frame timestamp
precedes the timer's starting value.

Local browser checks cover the four states, both
animation completions, arrow-key navigation, interruption of an animation by
the next build, and reset. The rendered mean path contains 29 points and its
minimum marker agrees with point 12 (week 47). All ten input/output paths are
present in the final view; no visible SVG text falls outside the canvas, and
the title fits above the visualization. No browser warnings or errors were
recorded. JavaScript syntax and the standalone build also passed checks.

Publication verification should compare the served page and index to this
committed build. Slides.com integration remains a separate task.
