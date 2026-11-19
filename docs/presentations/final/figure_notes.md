# Result figures: speaker notes and sources

Built by `make_result_figures.py` (run from the repository root). Wording approved by the user on 19 Nov 2026. Figure B's count was corrected from the data, from the sketch's "28 of 30" to 27 of 30.
Source for A and B: the M5b preview analysis (`docs/technical/research_notes/m5b_preview_2026-11-16.md`), frozen preregistration `m5_preregistration_2026-11.md`. The script recomputes every interval with the preregistered bootstrap and stops if it doesn't match the note.

## Figure A: `figures/fig_a_gap_by_condition` — "The busier each van, the more re-planning pays"
**Say:** each row compares our MILP dispatcher with a simple greedy one on the same nights. Left of zero means the MILP leaves fewer people waiting more than 20 minutes. The grey band is the ±2-point zone we agreed in advance would count as "no real difference". Every row is clearly outside it, and the gap grows as each van gets busier.

**Numbers (notes only, not on the slide):**
| Row | Nights | MILP − greedy, pp (95% CI) |
|---|---|---|
| 6 vans, normal night | 30 | −4.17 [−5.68, −2.71] |
| 5 vans, normal night (primary test) | 30 | −6.35 [−8.65, −4.17] |
| 5 vans, busy night | 26 (r00–r25; D-62) | −12.47 [−14.78, −10.10] |

- **Intervals:** 95% paired percentile bootstrap over nights, 10,000 resamples.
- **Primary row:** the only preregistered test. The others are descriptive, and rows are not compared with each other (D-49).
- **Busy row:** uses 26 nights because of the D-62 stopping rule. Including r26 gives −11.89 [−14.22, −9.48].
- **Scope:** first hour of service, synthetic nights built from the April aggregates.

## Figure B: `figures/fig_b_every_night` — "MILP did better on 27 of 30 nights"
**Say:** each dot is one night (5 vans, normal load). Dots below the dashed line are nights where the MILP left fewer people waiting. The result isn't carried by a few nights: 27 better, 1 tie, 2 worse.

**Notes:**
- **Overlapping dots:** nights with the same values are nudged apart slightly along the diagonal so every night shows. Each night has 64 requests, so the values come in steps of 1.56%.
- **Dot colours:** dark blue = MILP better; grey = greedy better; light grey on the line = tie.
- **Placeholder levels:** the axes show raw percentages, which rest on ASSUMED placeholders (patience, presence, Lyft delay). Say "the difference is the claim", not "22% go unreached".

## Figure C: speed vs riders (not drawn yet)
- **When:** drawn after the frozen M5d analysis runs (`python -m sim.m5 m5d compare`).
- **Approved wording:**
  - title: "Exact re-planning costs computing time; the shortcuts cost riders";
  - x axis: "Computing time per busy-night hour (log scale)";
  - y axis: "Extra requests not reached vs MILP (percentage points)";
  - dashed line: "15-min budget";
  - points: MILP (exact), Fixed drop order, Fixed when van is full, Greedy.
- **Data sources:**
  - each shortcut's gap is measured against the MILP on its own nights: fixed drop order on M5c (r00–r29), full-van switch on M5d (r30–r59);
  - greedy from M5b.
