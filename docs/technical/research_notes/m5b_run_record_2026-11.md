# M5b run record and deviation note (11–15 Nov 2026)

**Preregistration:** `m5_preregistration_2026-11.md`, FROZEN 2026-11-11, sha256 `ed2e7d71c937…`. It is not edited; this note records how the runs went against it.
**Decisions:** D-60, D-61, D-62. **Code fingerprint:** `8670e44b3619…`. It was unchanged for every run.
**Blind rule:** this note covers compute and run checks only. No C-vs-G measure was computed or read. The r26 diagnosis read one C run's events for one van. It did not read the G run or any comparison measure.

## Runs
| Group | Cells | Runs | Launched | Finished | Status |
|---|---|---|---|---|---|
| A | 1, 2, 5, 4 | 240 | 11 Nov 02:41 ET, 6 workers | 11 Nov 06:31 ET | all pass |
| B | 3 (high load) | 60 | 11 Nov 10:00 ET, 2 workers | 15 Nov 13:28 ET | 59 pass; r26 C failed one check |

- **Group B pause:** it paused on 12 Nov 13:22 ET when r26 C failed a check, as D-61 requires. It resumed on 15 Nov 12:00 ET with the code unchanged (D-62).
- **Group A compute:** C median per night was 1.6–8.0 min by cell, with the slowest at 45 min. Peak memory was ≤ 2.5 GB. G took under 1 s per night.
- **Group B compute:**
  - C median per night was 1.0 h.
  - The slowest was r03 at 23.3 h, using 0.9 GB.
  - About 60 CPU-h in total.
- **r03:**
  - **Diagnosed by a compute-only rerun:** the C run was deterministic, so the rerun followed the live run's path.
  - **The heavy stretch:** around minute 40, 15–17 requests were open while one van carried 6 riders, and each re-plan then took 9–12 min. This is the riders-aboard effect described in the M5a addendum.

## r26: the failed check and its cause
- **Check that failed:** "no unexplained van ride over the guardrail (excesses only from no-show waits, D-47/D-52)". On van V5, R048 was 24 s over its 1,500-s guardrail and R054 177 s over; both are one-person parties.
- **Sequence (from the C run's events and epoch plans):**
  1. **Within the guardrail until the no-show.** Every plan up to the curb arrival at 4,074 s kept both riders within their guardrail (R054 planned at 1,497 s).
  2. **No-show wait.** Rider R056 was absent, so V5 waited the full 180 s and the no-show was recorded at 4,254 s.
  3. **Drop order swapped.** At the 4,080-s epoch, during that wait, the committed-only route (exempt from the guardrail rule by design, D-52) put R048's drop before R054's. Both riders were already over the guardrail, and both orders cost the same: 261 passenger-seconds over the guardrail either way. The documented tie-break chose R048 first.
  4. **Excess.** R054's 177 s = 150 s (no-show wait beyond the planned dwell) + 30 s (R048's drop dwell, now first) − 3 s of matrix rounding.
- **Why the check missed it:**
  - **R048:** the check counts no-shows strictly before the drop. The leg from the no-show stop to R048's drop is 0 s, so they share the timestamp 4,254 s and the no-show was not counted.
  - **R054:** the check allows 150 s per no-show + 13 s. It has no allowance for an equal-cost re-sequencing after the unplanned wait.
- **Conclusion:**
  - **The simulator worked as designed.** The plan audit passed at every epoch, and the excess comes only from the unplanned no-show wait.
  - **The check's attribution rule is too narrow.** It is a defect in `l5_pilot.guardrail_excesses`, not in C, G or the engine.

## Handling (D-62)
- **Code:** not changed. `l5_pilot.py` is in the frozen fingerprint, and a fix would mean re-running all 300 runs after the freeze.
- **r26 C keeps its recorded status** (`checks_failed`).
- **Preregistered analysis:** under D-61, cell 3 uses nights r00–r25 (26 nights). Cells 1, 2, 4 and 5 are unaffected (30 nights each).
- **Labelled deviation analysis:** cell 3 over r00–r29, reported separately as an extra analysis. It never replaces the preregistered one (preregistration §5).
- **The check fix:**
  - count no-shows at or before the drop;
  - attribute excess from equal-cost re-sequencing after an unplanned wait.

  It is made after M5b and before M6, under a new fingerprint, with a test built from this case.
