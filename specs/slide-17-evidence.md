# Slide 17: borrowing history from outpatient surveillance

## Teaching and display

One Texas hospitalization plot, two addressable views, fixed 1240 × 540 frame.
Keep the title in Slides.com: **Borrowing history from outpatient surveillance**.

- `#state=1`: reported admissions, January 11, 2020 through October 1, 2022.
- `#state=2`: add ILINet-based reconstructed admissions, October 9, 2010 through
  June 29, 2019, with a dashed teal line. Observations remain solid gray.
- Both views have identical axes: September 2009 to October 2022, 0–2,500
  admissions per week. No smoothing, rescaling, synthetic points, interpolation,
  or connecting line across the gap between the two sources.
- Texas is chosen to match the lecture's earlier local examples, not by fit.
- Takeaway: “A longer training history, not new observations.”

## Source of truth

Meyer AG, Lu F, Clemente L, Santillana M. A prospective real-time transfer learning
approach to estimate influenza hospitalizations with limited data. *Epidemics*
50:100816 (2025). [DOI](https://doi.org/10.1016/j.epidem.2025.100816), PMID 39985955.
The [full-text XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13261820/fullTextXML)
was inspected September 24, 2026, especially Data augmentation approach and its
description of date stitching.

| Shown claim or quantity | Exact supporting source | Interpretation limits |
| --- | --- | --- |
| 456 reconstructed Texas weeks | `flusight_2023/imputed_and_stitched_hosp.csv`, Texas rows with nonmissing `pred_hosp`; `total_hosp` used without adjustment | Saved output from the published-method project, not a newly fitted reconstruction or a frozen October 2022 vintage |
| 143 observed Texas weeks | `flusight_2022/Flusight-forecast-data/data-truth/truth-Incident Hospitalizations.csv`, Texas, January 11, 2020 through October 1, 2022 | Archived reported counts include early underreporting and the pandemic period; not every displayed observation was retained in the model's training set |
| Reconstruction from ILINet | Paper, Data augmentation approach; local `flusight_2023/stitch.Rmd`, Combined Model and Make Historical Time Series | Pooled transformed ILI/EIP mapping transferred across locations, not direct equivalence between ILI percentages and observed hospitalization counts |
| Original calendar dates | Paper and `flusight_2023/stitch.Rmd`, Compare To Current Data, `date + days(728)` | The display reverses this modeling-index shift for reconstructed rows only; observed dates are never shifted |
| Reconstructed admissions are counts | `flusight_2023/stitch.Rmd`, population conversion; stored `pred_hosp`, `population`, and `total_hosp` | The saved Texas population is 29,527,941; counts match rates × population / 100,000 rounded to integers |

The original modeling pipeline excluded 2019/20 and 2020/21, retained reconstructed
history through June 2019 and observed history from July 2021, then shifted the
reconstructed date index forward 728 days. This slide shows the reconstructed
history on its original calendar alongside the available observed record, not
the literal stitched training matrix. The short observed record intentionally
includes 2020/21 to connect to slide 16; it is not presented as entirely used for
training. These implementation details belong in presenter documentation, not
extra explanatory paragraphs on the slide.

The 2023 project's normalized-ILI reconstruction is used rather than the older
2022 saved output, whose `ili` column contains unnormalized percentages and whose
values differ. The 2023 source's script explicitly normalizes ILI, fits the pooled
mapping before July 2019, reconstructs, and joins the histories. Neither source
is represented as an unrevised real-time October 2022 snapshot. No performance,
calibration, or exact counterfactual hospitalization claim is made.

## Reproducibility

`data/slide-17/` retains the selected original CSV rows, their original shifted
dates, full-source and subset SHA-256 digests in `sources.json`, and the derived
chart JSON. Source paths in the manifest are relative to the SantillanaLab
directory; all values are public surveillance aggregates.

Normal offline rebuild:

```bash
python3 scripts/build_slide_17.py
python3 -m unittest discover -s tests -p 'test_*.py'
SLIDE_PLAYWRIGHT=/absolute/path/to/playwright/index.mjs node tests/slide-17.browser.mjs
```

To intentionally refresh the selected source rows from the original project
files, run `python3 scripts/build_slide_17.py --import-sources ../..` from this
repository. Do not do this as part of a routine rebuild.

Tests verify all 599 source-to-chart values, date reversal, rate-to-count
conversion, weekly uniqueness and continuity within each source, frame bounds,
label collisions, unchanged axes and observations across builds, navigation,
reduced motion, and absence of runtime network requests. Visual review is also
required at the actual iframe size before publishing. Deployment verification
checks the Pages run and exact live HTML against the local generated file.
