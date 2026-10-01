# Slide 30: When can forecasts improve the decision?

This slide is explicitly a **Next study** with **Illustrative** data. It
connects current surveillance to possible epidemic trajectories and then to
a candidate timing action. It does not report a tested forecast-informed
vaccination policy or claim that the manuscript demonstrated clinical gains
from forecasts. The chance of receiving a later dose enters the decision,
but no numerical uptake probability is assigned.

## Synthetic inputs

`data/slide-30/inputs.json` freezes two illustrative scenarios. Six small
observations are followed by one rising observation. Each forecast contains
33 half-weekly points from the current observation through 16 weeks ahead.
The center begins at the corresponding final observation. The initial curve
peaks later; the updated curve peaks earlier. Activity is dimensionless.

The center was generated as `b(t) + (last_observation - b(0))*exp(-t/2)`,
where `b(t) = .12 + h*exp(-.5*((t-peak)/width)^2)`. The initial
`(peak, h, width)` is `(9, .52, 3.1)` and the updated values are `(4, .64, 2.8)`.
The illustrative half-width is `.14*(1-exp(-t/2)) + .05*t/16`, clipped with
the center to [0, 1]. The envelope is not a calibrated prediction interval,
and there is no interval percentage or numeric activity scale on the slide.

The example actions, “Keep planned date” and “Vaccinate now,” are assigned
for storytelling. They are not calculated by an implemented decision rule.
The data records `synthetic: true`, `decision_rule_validated: false`, and
an explicit null later-dose receipt probability. The on-slide action heading
is “Candidate action to test.”

## Presenter states and handoff

1. **Start**: static surveillance → forecast → decision scaffold.
2. **Initial plan**: reveal low observed activity, a later epidemic forecast,
   and the candidate action to keep the planned date.
3. **New surveillance**: add the rising observation, move the forecast earlier,
   and highlight the illustrative candidate action to vaccinate now.
4. **Compare rules**: propose comparing a fixed preseason rule with a rule
   updated during the season. Ask whether updated decisions improve clinical outcomes.

The forecast update morphs over one second. Load and backward navigation
are static; reduced motion disables animation. Right/Page Down/Space advance;
Left/Page Up go back; Home/Reset return to Start. Buttons and `#state=1`–`4`
are directly addressable; `setStage(value)` supports later Slides.com work.

Keep evaluation prospective in meaning: only information available at each
decision date, with clinical outcomes and vaccination uptake evaluated.
No such evaluation is performed in this slide. Hospitalization, outpatient
ILI, and infection outcomes should not silently substitute for one another.

Spoken closing line: “Surveillance tells us what is happening. Forecasts
describe what could happen next. Their clinical value comes from helping
us decide when to act.”

Editable source: `src/slide-30.html`. Offline build:
`python3 scripts/build_closing_slides.py`. Output: `docs/slide-30.html`.
The build verifies bounded ordered envelopes and continuity at the observed
anchor. All four views were rendered at 1280 × 720, with keyboard advance,
back, reset, rapid advances, and direct state loading checked. No browser
warnings or errors were reported.
