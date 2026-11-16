# Midterm report versions

Each folder is a frozen snapshot: the `.tex`, the built PDF, the figure script and the figures it used.
The working copy is one level up (`../BlueJayNightRide_Midterm.tex`); edit only that.

| Version | Date | Pages | What changed |
|---|---|---|---|
| v1_2026-11-02 | 2 Nov 2026 | 17 | First draft after the professor-persona review (`../reviews/professor_review.md`). |
| v2_2026-11-03 | 3 Nov 2026 | 18 | Page-1 affiliation/venue footnote removed; "instructor" to "professor" (Table 3, Sec 2, timeline); fixes from the cohesion/deck, contradiction and definitions reviews (`../reviews/`). |

v1 was reconstructed on 3 Nov by reversing the recorded, scripted v2 edits on the v2 source, then rebuilt (17 pages, as delivered).
The `make_report_figures.py` in each folder resolves paths from the working folder; to rerun an old version, point `HERE`/`REPO` at that folder and the repo root.
| v3_2026-11-03 | 3 Nov 2026 | 17 | Figures standardized: every figure drawn at printed size and included at natural size, text 7 to 9 pt (`../fig_style.py`, which also checks font range and text overlap). Report-only copies of the shared methodology figures (`../fig_diagrams.py`: Figs 1, 9, 12; `../fig_charts.py`: Figs 3, 5, 6, 7, 10, 11); `../make_report_figures.py` restyled (Figs 2, 4, 8, 13 to 16). Crowded labels fixed (Fig 1 "booking" now "Lyft order", Fig 8 "plan and transfers", Fig 9 "deadline passes"). Methodology PDF figures unchanged. |
