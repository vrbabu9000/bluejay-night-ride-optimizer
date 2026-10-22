# Conflicts and gaps between the source documents

Found while preparing `BlueJay_Scenario_Methodology.pdf` (21–22 Oct 2026). **The PDF resolved none of them.** The coordinating session settled them in the authoritative documents on 22 Oct 2026, and the PDF now follows those documents (Appendix C). Authority order: the decision log, then `scenario_spec.md`, then the rest. Source versions are listed in `SOURCES.md`.

## Status after reconciliation (22 Oct 2026)

| # | Topic | Original disagreement | Status | Where settled |
|---|---|---|---|---|
| C1 | D-52 referenced but absent | D-46/D-47 statuses cited a D-52 row that did not exist | **Resolved** | `decision_log.md`: D-52, amendment, amendment 2, D-53 and its update |
| C2 | Held-fixed dispatcher | D-51 update (C provisional) vs older text making T the baseline or fallback | **Resolved** | spec v0.5 §4, §9.2; model_design v0.3 §6.1; preregistration §1–2 and H4; methodology v1.1 §8 |
| C3 | Implementation status | methodology §7 said "not started"; D-46 said "implemented" | **Resolved** | methodology v1.1 §7 (verified M0–M1 status; the source for PDF §7) |
| C4 | Co-primary P90 wait | prereg §3 "co-primary" vs D-50(2) "secondary" | **Resolved** | preregistration §3: P90 wait is secondary |
| C5 | Shift-end rule | pickup must *start* before the end (spec §17.6) vs *drop-off* must end before it (model_design §3.3) | **Marked open** (L7 only, not implemented); the PDF takes no side | spec §3.1, §17.6; model_design §3.3 |
| C6 | Design trail §8 (no-shows) | mode-specific thresholds; predates D-48 | **Resolved** (annotated in place) | `decision_log.md` trail §8 |
| C7 | Design trail §1, §2 | closing rule "unspecified"; range ~145–205 | **Resolved** (annotated in place) | `decision_log.md` trail §1, §2 |
| C8 | Candidate cap wording | "relative to the previous plan" (D-47(3), model_design §3.3) vs D-52 | **Resolved** | D-47(3) annotated as superseded by D-52; model_design v0.3 §3.3 |
| C9 | Epoch triggers | spec §17.4 had every cancellation/no-show trigger; D-52 says van-side only | **Resolved** | spec v0.5 §17.4 |
| G1 | Can a `committed` rider cancel? | spec §17.3 patience checks omitted `committed` | **Resolved**: yes (the L3 key relies on it); Fig. 8 now shows the arrow and its caption says so | spec v0.5 §17.3 class 60 |
| G2 | Pickup instant | spec §6 vs §17.5 vs D-39 | **Resolved**: pickup = curb arrival of the boarding vehicle; the 30-s dwell follows and is part of the ride | spec v0.5 §17.5 |
| G3 | L4 rule set | "five rules" not named | **Resolved**: R0 plus R1(10), R1(15), R1u(10), R2(15), R3(2); 22 transfers (3/3/8/8, 4 XL) and 4 declines summed across rule runs | methodology v1.1 §7 |
| G4 | K = 3 candidate rule | first given in a coordinator message | **Resolved**: D-52 and its amendment (all of a van's stops reordered freely) | `decision_log.md` |

## Residues noticed in the final check (wording only)

| # | Where | What remained | Status |
|---|---|---|---|
| R1 | `scenario_spec.md` §17 heading | Still says "not implemented", although §17.9 records the M0–M1 implementation | **Settled**: heading now says implemented for L1–L4 in M0–M1 |
| R2 | `model_design.md` opening status line | "Nothing here is implemented"; v0.3 now describes C as built and verified | **Settled** (status line updated) |
| R3 | `model_design.md` §6.1, last bullet | Still says "The dispatcher algorithm is not yet approved … needs a team decision" (contradicts its own table and the D-51 update) | **Settled** (§6.1 updated) |
| R4 | `model_design.md` §5 Triggers row | Still lists every cancellation and no-show; not narrowed to match spec §17.4 (van-side only) | **Settled** (trigger row narrowed) |
| R5 | `scenario_spec.md` §8 L4 row | Still lists "R0/R1/R2/R3"; methodology v1.1 §7 names the five active cases | **Settled**: lists R0, R1(10), R1(15), R1u(10), R2(15), R3(2) |
| R6 | `decision_log.md` design trail §8, "Why ~8.9% is not adopted" row | Still says p_van is calibrated "jointly with patience"; D-48(2) says the mapping pins p regardless of patience (the annotation added covers adoption status, not this clause) | **Settled**: trail §8 annotated (≈ 8.9% follows from the mapping regardless of patience; van path implemented) |
| R7 | `preregistration_v2.md` title line | Still reads "revised 21 Oct" although the change log has a 22 Oct entry | **Settled**: title reads "revised 22 Oct" |
| R8 | `scenario_methodology.md` v1.1 §8 ("a failed solve executes committed work only and is logged") | D-52 amendment 3: a HiGHS error or infeasible model **stops the run**; only at the node budget is the best incumbent executed (labelled `feasible_unproven`). The PDF follows the decision log (§5.5) and lists this in Appendix C | **Settled**: §8 now matches D-52 amendments 2–3 (failed → committed work only; node budget → incumbent, `feasible_unproven`; error, infeasible model or wall-clock stop → run ends) |

## Verification wording corrected in the PDF (22 Oct, integrated review)
- Best-order check: for 40 van states of the L4 R0 run, every subset with |S| ≤ 2 plus a **sample** of 80 subsets with |S| = 3 (1,130 subsets, 113,879 orders). The PDF no longer says "each candidate".
- Full-enumeration check: all 46 L4 R0 epochs (151,710 combinations) under the current default. The math review's "370 epochs" (its run table shows 414; earlier fixed drop order) is no longer quoted.
- The test count (105 pass on 22 Oct: 46 + 32 + 27) and the integrated-review verdict are now sourced in methodology v1.1 §7 and quoted in PDF Table 12.

## Arithmetic checked (no conflict)

- Worked route example (methodology §6): waits, rides, φ values and totals 66.5 vs 81.0 recomputed.
- Volume: 5ρ_h = 64.25 / 50.50 / 53.55 → 168 → 64/50/54; taper 64/50/48 = 162; R/C = 2.087; range 168/0.8 = 210, 168/0.65 ≈ 258, 168 × 0.9 ≈ 151.
- No-shows: 24,095 + 2,359 = 26,454; 2,359/26,454 = 8.92%; 2,359/50,297 = 4.69%.
- Party mean 1.405; 1% of 168 = 1.68. φ(5/10/15/20) = 5/17.5/42.5/92.5; TransLoc check 2.5 > 2.
- PDF Table 13 (L4 R0, 18:15 plan): waiting 546.58, riding 53.25, driving 1.65 and pending price 295.83 (total 897.32), re-derived independently from `outputs/sim/L4_R0/epochs.jsonl` and matching `narrative.md`. R002's earliest pickup 18:19:28 → 5·φ(19.47) ≈ 435.8 vs 262.5 pending, a 173-point gap matching the D-53 update.
