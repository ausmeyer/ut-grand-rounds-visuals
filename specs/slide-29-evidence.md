# Slide 29: A later date only helps if vaccination still happens

This is a conceptual decision tree, not an additional numerical result.
The manuscript compares dates conditional on receiving the dose. Scheduling
a later dose introduces another possible outcome: vaccination is missed.
No missed-dose probability, threshold, or expected benefit is supplied.
Branch spacing, stroke width, and colors carry no quantitative meaning.

The final practice note paraphrases the CDC's September 1, 2026
[seasonal influenza vaccine administration guidance](https://www.cdc.gov/flu/hcp/vax-summary/seasonal-influenza-vaccines.html),
checked October 1, 2026: September–October for most one-dose recipients,
with attention to avoiding missed opportunities. The full guidance also
supports vaccination after October while viruses circulate and unexpired
vaccine remains available. The slide does not replace that guidance with a
recommendation to defer an available vaccination opportunity.

`data/slide-29/inputs.json` records the source, date, study assumption,
conceptual scope, and explicit null missed-dose probability. The editable
source is `src/slide-29.html`. Build all closing slides offline with
`python3 scripts/build_closing_slides.py`; the output is `docs/slide-29.html`.

## Presenter states

1. **Start**: one patient with choices to vaccinate today or schedule a later dose.
2. **Study assumption**: the later-dose path ends with dose received.
3. **A missed dose**: add the missed-vaccination branch.
4. **Clinical decision**: complete the today path and show the clinical
   takeaway and concise CDC practice note.

New branches fade in over 0.45 seconds; loading and backward navigation are
static, as is playback with reduced motion. Right/Page Down/Space advance;
Left/Page Up go back; Home/Reset return to Start. Direct buttons and
`#state=1`–`4` are supported, as is `setStage(value)` for later integration.

Say: “This analysis estimates timing for someone who receives one dose.
A clinical rule also has to account for the chance of missing vaccination.”
Handoff: “Can information arriving during the season help us improve that
decision while preserving the chance that the patient is vaccinated?”

The complete diagram and sequential reveals were inspected at 1280 × 720.
Keyboard advance, back, reset, rapid advances, and direct state loading were
checked. The console reported no warnings or errors.
