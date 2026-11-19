# M5d preregistration: C-S6 (fixed drop order only in vans with 6+ parties) vs C, on fresh nights

**Status: FROZEN 2026-11-18** (frozen on the user's instruction, 18 Nov: "lets take the gamble and build this anyway", before any run on r30–r59). The runner refuses the `m5d_C` and `m5d_rest` stages until this line reads `**Status: FROZEN <date>**`. Once frozen, this file is not edited. Every M5d manifest records its SHA-256.

**Decision:** D-64 (proposed 18 Nov). **Feeds:** D-51 (confirmation, proposed), the future-work section of the report.
**Asked by:** the user, 18 Nov: build and run the switch "anyway", with the laptop reserved for it until Tuesday 24 Nov. The compute cost and the clash with M6 are recorded in `compute_constraints_2026-11-18.md`.

**Why this test:**
- **M5c:** fixing the drop order everywhere (C-F) cost about 2 pp of riders and still missed the compute gate.
- **The diagnostic** (`m5c_diagnostic_results_2026-11-18.md`, exploratory) rebuilt C's re-plans on r00–r29:
  - Re-plans with a van carrying 6+ parties are 11% of re-plans but 65% of C's time, and hold about 9% of the value of exact reordering.
  - It estimated that fixing the order only in those vans keeps about 91% of the value, at an estimated median 38 min per high-load night (worst ≈ 1.6 h, against C's 23 h).
- **Why fresh nights:** the threshold of 6 was chosen by looking at r00–r29. Testing it on those nights would overstate how well it works. So the test uses 30 new nights per load that no dispatcher has run on.

**Outcomes seen before writing:**
- **On r00–r29:** C, G and C-F outcomes are known (M5b, M5c), and so is the diagnostic.
- **On r30–r59:** no outcome of any kind. The nights were generated on 18 Nov and no run has used them.
- **C-S6 before the freeze:** the only runs are the development probe `probe_cs6` on the old nights high_5 r00 and r03. It is compute only: wall time, memory, solver status and checks; its rider outcomes are not read. Its results are recorded in §8 below at the freeze.

## 1. Hypothesis
- **H:** fixing the aboard riders' drop order only in vans with 6 or more parties aboard or committed removes most of C's compute tail at no practically important cost in riders reached within 20 min.
- **The test:** a non-inferiority test against C on fresh nights, plus the compute gate. The diagnostic already predicts the gate will fail at high load (estimated median 38 min). The gate is kept as stated and is **not** relaxed, so a result is reported against the same bar as C-F.

## 2. What is compared
- **C-S6:** C exactly as in M5b (K = 3, pending price A, node budget 100,000, threads 1, seed 0, D-52 and amendments), with one change, setting `fix_drop_order_min_parties = 6`:
  - in each re-plan, a van with **6 or more rider parties aboard or committed** (`len(van.riders) >= 6`, public state only) keeps the drop-off order of its committed-only route, as in C-F;
  - every other van reorders freely, as in C;
  - new pickups and drop-offs are still placed in the best positions. The objective is unchanged; only the candidate set of full vans shrinks.
- **C and G:** re-run on the same fresh nights (not reused from M5b), so all three arms share nights, code and machine conditions.
- **Code:** fingerprint `1f318cef8ad4…`, which covers the D-62 check fix and the switch. With the switch off, the new code reproduces the saved M5b/M5c event logs byte for byte (checked 18 Nov on base_5 r00 for C, G and C-F). The fixed check passes all 360 saved M5b/M5c runs, including high_5 r26.

## 3. Nights and runs
- **Nights:**
  - L6 high_5 and base_5, replicates r30–r59, first hour (83 / 64 requests).
  - Built 18 Nov by `src/scenario/build_l6_v2.py` with the same generator and seed scheme; r00–r29 rebuilt to identical hashes.
  - The 60 new content hashes are in `FROZEN_v2_L6.json` (data/ is not in git). The SHA-256 of their sorted JSON is `83c0620f97a5…` (r30 high `fa7e13a6fb2b…`, r59 base `762b61064a7e…`).
- **Runs:** two queues side by side, folder `outputs/sim/m5/m5d`, 1 rep each:
  - `m5d_C`: C at high load, r30 → r59, at most 2 workers (memory: up to 6 GB per night).
  - `m5d_rest`: C-S6 and G at high load, night by night r30 → r59; then C-S6, C and G at base load, night by night.
- **Cutoff:** **24 Nov 2026 12:00 ET.** Runs finishing later are not used.
- **Which nights count:**
  - the longest unbroken run r30…rk in which **all three arms** finished by the cutoff (any check status);
  - minus the nights on which any arm failed a run check. Both counts are reported.
- **Failures:**
  - A crash pauses its queue. The cause is reported before resuming.
  - A failed run check does **not** pause the queue (so an unattended queue isn't lost to a pause). The night is excluded by the rule above.

## 4. Criteria
**Compute gate** (D-60 threshold): C-S6 passes if its median high-load first-hour night, over the nights finished by the cutoff, takes ≤ 15 min of wall time. Also reported, without a threshold:
- C-S6's maximum;
- C's median and maximum on the same fresh nights.

**Primary quality test:** high load, 5 vans, R0.
- **Measure:** the per-night C-S6 − C difference in the share of requests not reached within 20 min, in pp, with the M5b definition.
- **Interval:** 95% paired percentile bootstrap over nights, 10,000 resamples, `numpy.random.default_rng(20261110)`.
- **Margin:** 2 pp.
- **Readings:**
  - **C-S6 non-inferior** if the upper bound is < +2 pp. If it is also < 0, C-S6 is also better.
  - **C-S6 worse by more than the margin** if the lower bound is > +2 pp.
  - Otherwise, **inconclusive at this scale**.
  - With fewer than 5 nights used, a point estimate only.

**Secondary (no decision rests on these):**
- the same reading at base load;
- **C − G on the fresh nights:** a replication of M5b on new nights, reported with its interval;
- C-S6 − G;
- the M5b secondary measures for C-S6 − C.

## 5. What each result leads to (the team decides; nothing is switched automatically)
| Compute gate | High-load reading | Proposed consequence |
|---|---|---|
| pass | non-inferior | The team may use C-S6 for high-load M6/M7 nights, reported as a change to C with this test as the evidence |
| fail | non-inferior | C-S6 is reported as a validated safety valve: it keeps riders and cuts the worst nights, but does not make high load affordable. The D-51 scope is unchanged |
| any | inconclusive | Keep C as tested. The switch's rider cost is not settled |
| any | worse by more than the margin | Keep C as tested. The switch costs riders |

## 6. What does not change after M5d outcomes are seen
- **Settings:** the threshold (6), the margin, the measure, the night rule, the cutoff, the bootstrap and the gate.
- **Analysis code:** `python -m sim.m5 m5d compare`, tested on a self-comparison and on the night rule before any M5d run. Progress during the runs is checked with `python -m sim.m5 m5d status`, which reads wall time and check status only.
- **Changes:** any later change is a new, labelled analysis.

## 7. What a result here does and does not show
- **Shows:** whether this one threshold rule, chosen on old nights, keeps riders on new nights, and what it does to compute.
- **Does not show:**
  - whether 6 is the best threshold. Other thresholds were not preregistered and are not tested;
  - full evenings;
  - anything about TransLoc.

## 8. Development probe (old nights, compute only; recorded at the freeze)
- **high_5 r00:** C-S6 took 28.5 min (C 76 min, C-F 6 min on the same night in M5b/M5c). Peak memory 1.0 GB, all 147 epochs solved optimally, every run check passed.
- **high_5 r03** (C's 23.3-h night): still running at the freeze. Its compute is reported in the M5d run record, not here. It changes nothing above.
- **No rider outcome of either probe run was read.**
