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

## Figure C: `figures/fig_c_speed_vs_riders` — "Exact re-planning costs computing time; the shortcuts cost riders"
Drawn 24 Nov 2026 with the wording approved on 19 Nov, after the frozen M5d analysis.

**Say:** on a busy night the exact MILP needs about an hour of computing per hour of service, four times the 15-minute budget. The two shortcuts we tested sit between it and greedy. Fixing every van's drop order is fast enough but costs about 2 points of riders. Fixing it only in full vans costs nothing measurable but is still too slow. Greedy is instant and costs 12 points. No tested option is both fast enough and free.

**Numbers (notes only):**
| Point | Busy-night compute, median per first hour | Extra not reached within 20 min vs MILP, pp (95% CI) | Nights | Source |
|---|---|---|---|---|
| MILP (exact) | 60.6 min (M5d fresh nights: 58.0) | 0 (reference) | 30 | M5b |
| Fixed drop order (C-F) | 15.2 min | +2.08 [+0.50, +3.78] | 29 (r26 excluded, D-62) | M5c, r00–r29 |
| Fixed when van is full (C-S6) | 38.2 min | +0.12 [−0.68, +0.92] | 30 | M5d, r30–r59 |
| Greedy (G) | 0.24 s | +12.47 [+10.10, +14.78] | 26 (D-62 stopping rule) | M5b, r00–r25 |

- **Pairing:** each shortcut is compared with the MILP on its own nights, so the vertical gaps come from three separate paired analyses. The x positions are medians over 30 nights.
- **Grey band:** the ±2 pp non-inferiority margin.
- **Scope:** first hour of a busy (high-load) night, 5 vans. Normal nights are about ten times cheaper: the MILP's base median is 4.5–8 min per first hour, and 8.5 min per full evening (M6).
- **Check:** the script recomputes every interval and stops if it doesn't match the frozen results notes.

## Figure D: "Lyft rules matter with 5 vans, barely with 6" (`fig_d_lyft_rules`)
**Source:** M7, 30 full base evenings per fleet size, dispatcher C (`research_notes/m7_results_2026-11-24.md`; data `outputs/sim/m7/per_night.csv` and `pair_intervals.csv`). The layout was approved by the user on 25 Nov. Every plotted mean is asserted against the results note.

**Speaker notes:**
- Each dot is one Lyft rule, averaged over the same 30 evenings. Left is the five vans we have; right is the same evenings with a sixth van.
- With five vans, every step along the line reaches more riders and books more Lyfts. The best rule cuts riders not reached within 20 min from 24% to 16%, at about 12 bookings per 100 requests.
- "After 10 min" is off the line: it reaches no more riders than "After 15 min" but books four times as many Lyfts. Rules that look at the *predicted* wait spend bookings better than rules that look at time already waited.
- With six vans, every rule sits within about two points of "Never". The sixth van does more than any Lyft rule does at five vans.

**How the line is drawn (be ready for the question):**
- A rule is on the line if it reaches more riders than every rule with fewer bookings. "More" means the paired 95% bootstrap interval of the difference lies below 0.
- This is descriptive. The preregistered dominance rule (non-inferior on share, P90 wait and bookings, better on one) finds no rule dominating another at five vans. At six vans, practically tied rules dominate each other in both directions: the rule's wording needs a tie clause, which is a team decision (M7 results §4, §8).
- "After 10 min with no van assigned" (R1u(10)) never fired, so it is identical to "Never" (M7 results §3).

| Rule | 5 vans: not reached ≤ 20 min, % | bookings / 100 | 6 vans: % | bookings / 100 |
|---|---|---|---|---|
| Never (R0) | 23.8 | 0.0 | 14.2 | 0.0 |
| After 15 min (R1(15)) | 22.4 | 1.9 | 14.3 | 0.3 |
| After 10 min (R1(10)) | 22.4 | 7.6 | 14.5 | 2.1 |
| Predicted wait > 15 min (R2(15)) | 17.5 | 8.8 | 13.3 | 2.2 |
| Lyft sooner by 2 min (R3(2)) | 15.6 | 12.1 | 12.4 | 3.4 |

**Caveat to say aloud:** the levels rest on assumed patience and Lyft delay, and 28–47% of transferred riders cancel before the Lyft arrives under those assumptions. M8 (running) tests how the picture moves when the assumptions change.

