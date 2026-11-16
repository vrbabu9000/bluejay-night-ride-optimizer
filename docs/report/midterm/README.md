# Mid-semester written report (first draft, 2 Nov 2026)

`BlueJayNightRide_Midterm.pdf` is the team's Mid-Semester Update (written). It follows the presented deck (`BlueJay_Midterm_v0.4_BlueJayStyle.pptx`, 28 slides + backups B1–B9) and the formatting of the proposal (`docs/proposal/BlueJayNightRide_Proposal.tex`: ICML 2026 style, same title block, numbered references, AI-use disclosure).

## Build

```bash
docs/report/midterm/build.sh
```

Runs `make_report_figures.py`, then pdflatex three times (TinyTeX). The ICML style files are copied here from the course template. Courier is missing from this TinyTeX, so the typewriter font is set to Computer Modern (`\ttdefault`).

## Where the content comes from

| Report part | Source |
|---|---|
| Story and section order | the presented deck, slides 1–28 and B1–B9 |
| Numbers (results, April aggregates) | `docs/presentations/midterm/v0.4/derived/numbers.json`, `outputs/sim/batch_L5_v1/per_night_metrics.csv` |
| Method explanations | `docs/technical/methodology_pdf/methodology.tex` v1.6, `model_design.md`, `slide_explanations.md` |
| Proposal-feedback table | `docs/proposal/feedback_proposal_kearsley.md` |

## Figures

| File | Made by | Shows |
|---|---|---|
| `f1`–`f9` | copied from `docs/technical/methodology_pdf/figures/` (`make_figures.py`) | system, hourly rounding, no-show denominators, assumed distributions, φ, worked example, request lifecycle, transfer timeline, trade-off |
| `r1_workload` … `r6_roadmap` | `make_report_figures.py` | workload chain, pilot arrivals, reach by rule, transfer fates, architecture, plan |
| `map_synthetic_hour.png` | `docs/presentations/midterm/v0.4/make_map.py` | one constructed pilot hour (night r00) |

## Review

`reviews/professor_review.md`: an independent page-by-page review written by a reviewer agent in Prof. Kearsley's role. Each finding was checked by the main session before being applied or declined.

## Figures (v3 onward)
All figures follow `fig_style.py`: drawn at printed width (6.75 in full width, 3.25 in one column), included without `width=`, text 7 to 9 pt; `save()` reports fonts out of range and text overlaps. Scripts: `make_report_figures.py` (r1 to r7), `fig_diagrams.py` (d_system, d_lifecycle, d_transfer), `fig_charts.py` (c_volume, c_assumed, c_noshow, c_example, c_phi, c_map). The f1 to f9 PDFs in `figures/` are the methodology originals, no longer used by the report. Earlier versions: `versions/`.
