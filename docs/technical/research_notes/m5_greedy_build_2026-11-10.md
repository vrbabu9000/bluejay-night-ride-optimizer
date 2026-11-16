# M5: greedy dispatcher G, build and independent review (10 Nov 2026)

**Decision:** D-60 (approved 10 Nov). **Plan:** `docs/plans/phase4/plan.md` v2, M5b.
**Status:** G is built, tested and reviewed. No C-vs-G comparison has been run on L6, and no L6 outcome has been read.

## What was built
- **`src/sim/greedy.py`:** G, as defined in model_design §6.1. Each epoch it does three things:
  1. **Keep:** each van's earlier sequence, reconciled with the observation.
  2. **Repair:** release an assigned request only if drift makes the kept plan break its guardrail. This never happened in 4,731 L5 epochs, and is tested by forcing the case.
  3. **Insert:** each unassigned request, in arrival order, at the cheapest feasible (van, pickup position, drop-off position). Cost and feasibility come from C's own `dispatch.evaluate`. Ties go to the lower van ID, then the earlier positions.
- **`src/sim/engine.py`:**
  - `Policy.algorithm`, either "C" (default) or "G";
  - `Engine._solve`, which replaces the two `D.solve` calls;
  - G refuses the prediction-based rules R2 and R3, because G gives pending requests no ETA, so those rules would be meaningless.
- **`tests/test_greedy.py` (12 tests):**
  - G equals C on L1–L3, where only one request is open at a time;
  - G never reassigns or reorders;
  - determinism;
  - the forced repair;
  - the same-epoch re-solve, across all 30 L5 nights;
  - unknown algorithms and R2/R3 are refused.

## C is unchanged
The engine edit changes the code fingerprint of `engine.py`. To show this matters only on paper, C was re-run on four saved L5 runs:
- r00 under R0 and R2(15);
- r04 under R3(2);
- r07 under R1u(10).

All four reproduced `outcomes.csv` and `events.csv` byte for byte. The saved L5 runs remain valid. A resume of the old batch would refuse to run, because the fingerprint differs, but the batch is complete.

## Independent review (a separate agent, given the code and spec, not our conclusions)
**Coverage:**
- 360 L5 runs: all 30 nights × R0, R1(10), R1u(10) and R2(15) × three presence and curb-wait settings, about 30,500 epochs.
- No crash, audit failure, missing drop-off, reordering or reassignment.
- The reconciliation was found sound in every case: picked up, committed, cancelled en route, transferred, curb wait under both conventions.

| # | Finding | Action |
|---|---|---|
| 1 | **Defect, handicapped G.** After a Lyft transfer the engine re-solves at the same epoch, but G kept choices from the discarded first plan. In 22 of 177 same-epoch re-solves (R1(10), 30 nights) the plan differed from a clean restart. C re-solves from scratch | **Fixed.** G restores its state from before the first plan at that epoch; that plan was never executed, so this is not a reassignment. The test covers all 30 nights, and a mutation check (fix disabled) reproduces 22/177 |
| 2 | An insertion may not push an aboard rider above max(guardrail, ride in G's **current** route). C's reference is the committed-only route. Slightly looser for G (5 of 1,680 chosen insertions would fail C's rule) | **Kept, as designed.** It is the same principle as C's ("a plan may not create or increase a violation" relative to the plan the dispatcher is bound to). G is bound to its own earlier plan because it never reorders, and using C's reference would block every insertion on a van once G's own plan exceeded it. Stated in the `greedy.py` docstring |
| 3 | Repair checks only riders not yet picked up. An aboard rider over the guardrail in a kept plan is charged Ψ in the cost but not released | **Kept, as designed** (G cannot reorder to fix it). Stated in the docstring |
| 4 | No K cap in G: K = 3 belongs to C's restricted candidate set | **Kept, as designed.** Stated in the docstring and in plan v2 M5b |
| 5 | G could be run with R2/R3, which would be meaningless | **Fixed:** the engine refuses it |
| 6 | Harness wiring: `batch.config` and the `l5_pilot` status check are L5/C-specific | To do in the M5 runner: record `algorithm` in every manifest, and accept the status "greedy" |

## What this does not show
- **Anything about whether C beats G.** That is M5b, under criteria frozen before its first run.
- **That G represents any real dispatcher.** It is a floor: myopic insertion that never revisits a decision.
