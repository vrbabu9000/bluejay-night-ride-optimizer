# M5c preregistration: C-F (fixed drop order for riders aboard) vs C

**Status: FROZEN 2026-11-17** (frozen on the user's instruction, "Freeze and run M5c", before the first M5c run). The runner refuses the `m5c` stage until this line reads `**Status: FROZEN <date>**`. Once frozen, this file is not edited. Every M5c manifest records its SHA-256.

**Decision:** D-63 (proposed 17 Nov). **Feeds:** D-51 (confirmation, proposed).
**Why this test:**
- C as tested in M5b is clearly better than greedy, but too slow at high load (high-load first hour: median 1.0 h, worst 23.3 h per night). Nearly all of that time is spent reordering the drop-offs of riders already aboard (M5a addendum; `m5b_run_record_2026-11.md`).
- Before C is changed to make high-load nights affordable, we test whether the faster variant gives up rider outcomes.

**Outcomes seen before writing:**
- **M5b's C and G outcomes are known** (`m5b_preview_2026-11-16.md`).
- **No C-F rider outcome has been read.** The only C-F runs before the freeze are the compute-only probe (`probe_cf`, high load r00–r03), and their outcomes are not read.
- **Probe compute (17 Nov):**
  - **Wall time:** C-F took 4.4 / 15.5 / 10.6 / 25.6 min on high_5 r00–r03, against C's 76 / 250 / 103 / 1,396 min on the same nights. That is 16–55× faster; median of the four ≈ 13 min.
  - **Memory:** peak ≤ 1.6 GB.
  - **Solver:** every epoch was solved optimally, and every run check passed.
  - **The gate is borderline:** on 4 nights it sits just under the 15-min threshold. The gate is **not** changed in light of this; it stays the D-60 threshold.

## 1. Hypothesis
- **H (the team's):** keeping the aboard riders' drop order fixed makes high-load nights affordable, at no practically important cost in riders reached within 20 min.
- **The test:** two parts, both stated before any C-F outcome exists.
  - a compute gate;
  - a non-inferiority test against C.

## 2. What is compared
- **C-F:** C exactly as in M5b (K = 3, pending price A, node budget 100,000, threads 1, seed 0, D-52 and amendments), with one change: `fix_existing_drop_order` on.
  - Riders already aboard keep the drop-off order of the van's committed-only route.
  - New pickups and drop-offs are still placed in the best positions around them.
  - This changes the candidate set, not the objective.
- **C:** the M5b runs, reused unchanged (`outputs/sim/m5/m5b/`).
- **G:** the M5b greedy runs, for a descriptive C-F − G only.
- **Shared:** the engine, settings, nights (first hour of frozen L6 r00–r29), code fingerprint `8670e44b3619…` (`dispatch.py` is unchanged; the variant is a setting) and run checks.

## 3. Runs
- **Order:** C-F on high_5 r00 → r29, then base_5 r00 → r29. 60 runs, 1 rep each, folder `m5c`.
- **No cutoff:** every night that finishes is used.
- **Failures:** a run that fails or fails a check pauses new launches, and the cause is reported (as in D-61).
- **Which nights count:** nights where **both** C-F and C passed every run check. high_5 r26 is therefore excluded, because its C run keeps status `checks_failed` (D-62). The count is reported.

## 4. Criteria
**Compute gate** (reuses the D-60 threshold): C-F passes if its median high-load first-hour night takes ≤ 15 min of wall time. The maximum is reported.

**Primary quality test:** high load, 5 vans, R0.
- **Measure:** the per-night C-F − C difference in the share of requests not reached within 20 min, in pp, with the same definition as M5b.
- **Interval:** 95% paired percentile bootstrap over nights, 10,000 resamples, `numpy.random.default_rng(20261110)`.
- **Margin:** 2 pp (the D-50 margin).
- **Readings:**
  - **C-F non-inferior** if the upper bound is < +2 pp. If the upper bound is also < 0, the reading says C-F is also better.
  - **C-F worse by more than the margin** if the lower bound is > +2 pp.
  - Otherwise, **inconclusive at this scale**.

**Secondary (descriptive, no test):**
- the same reading at base load, 5 vans;
- C-F − G at both loads;
- the M5b secondary measures for C-F − C;
- compute at base load.

## 5. What each result leads to (the team decides; nothing is switched automatically)
| Compute gate | High-load reading | Proposed consequence for D-51 |
|---|---|---|
| pass | non-inferior | Use C-F for high-load M6/M7 nights. Report that C was changed to accommodate high load, with this test as the evidence. Whether to also use C-F at base load (one dispatcher everywhere) depends on the base reading |
| pass | inconclusive or worse | Keep C as tested. High-load full evenings stay a compute limitation |
| fail | any | Keep C as tested. C-F does not solve the compute problem |

## 6. What does not change after C-F outcomes are seen
- **Settings:** the margin, the measure, the night rule, the bootstrap and the gate.
- **Analysis code:** `python -m sim.m5 m5c compare`, written and tested on synthetic values and a self-comparison before any M5c run.
- **Changes:** any later change is a new, labelled analysis.

## 7. What a result here does and does not show
- **Shows:** whether fixing the aboard drop order costs riders on the first-hour slice, at high and base load.
- **Does not show:**
  - full-evening behaviour;
  - anything about TransLoc;
  - that C-F is optimal over the free-order candidate set. By construction it is not; it is optimal over its own, smaller set.
