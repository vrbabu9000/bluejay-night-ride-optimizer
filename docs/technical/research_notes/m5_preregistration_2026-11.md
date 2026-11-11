# M5b preregistration: C vs greedy G on the first-hour L6 slice

**Status: DRAFT (not frozen).** The runner refuses M5b until the line above reads `**Status: FROZEN <date>**`. Once frozen, this file is not edited. Every M5b manifest records its SHA-256, and a resume refuses runs made under a different version.

**Decisions:** D-60 (scope and criteria, approved 10 Nov), D-61 (run order and stopping rule, approved 11 Nov).
**Plan:** `docs/plans/phase4/plan.md` v2, M5b. **Compute basis:** `m5a_compute_2026-11-10.md` and its 11 Nov addendum.
**Outcomes seen before writing:** none from L6. No L6 rider outcome had been read when this note was written. L5 C-vs-G outcomes were seen in G's build smoke runs; L5 is the rehearsal level, and these criteria were fixed by D-60 before that.

## 1. What is compared
- **C:** the restricted route-selection MILP (`dispatch.py`), exactly as held fixed (D-51, D-52 and its amendment):
  - K = 3, exact reordering of all stops, `fix_existing_drop_order` off;
  - pending price A, node budget 100,000, threads 1, random seed 0.
- **G:** greedy insertion that never reassigns (`greedy.py`, model_design §6.1), with the designed differences stated in its build note:
  - no K cap;
  - the aboard-rider reference is G's current plan;
  - repair scope is limited to riders not yet picked up;
  - G refuses R2/R3.
- **Shared by both:**
  - engine, observation, cost function (D-29), capacity and guardrail;
  - travel multiplier 1.2, lag 120 s, consent 1.0, presence p = 0.089 (provisional), curb-wait "possible_boarding".
- **Nights:** the first hour of frozen L6 nights r00–r29 (`FROZEN_v2_L6.json`, digest `b5088e58…`): 64 requests (base) or 83 (high). Vans stay on duty until all accepted work is resolved.
- **Code:** simulator fingerprint (inputs, engine, dispatch, lyft, greedy, l5_pilot) `8670e44b3619…`, recorded in every manifest. A resume refuses a different fingerprint.

## 2. Cells
| # | Condition | Runs (folder names) | Comparison |
|---|---|---|---|
| 1 | Base, 5 vans, R0, 120 s | `base5_C_R0_t120`, `base5_G_R0_t120` | C − G (**primary**) |
| 2 | Base, 6 vans, R0 (same requests, D-37) | `base6_C_R0_t120`, `base6_G_R0_t120` | C − G |
| 3 | High load ×1.3, 5 vans, R0 | `high5_C_R0_t120`, `high5_G_R0_t120` | C − G, within the high pattern only (never against cell 1) |
| 4 | Base, 5 vans, R0, C re-planning at 60 s and at 300 s | `base5_C_R0_t60`, `base5_C_R0_t300` | each C − cell 1's G (G acts on arrival; its re-plan interval changes nothing) |
| 5 | Base, 5 vans, R1(10) | `base5_C_R1-10_t120`, `base5_G_R1-10_t120` | C − G |

## 3. Run order and stopping rule (D-61)
- **Group A, first:** cells 1, 2, 5, 4, in that order. Within a cell, nights go r00 → r29, with both runs of a night launched together.
- **Group B, after A:** cell 3, nights r00 → r29 in order. It runs with at most 2 parallel workers, because peak memory is up to 5 GB.
- **Cutoffs:** preview analysis, **19 Nov 2026 12:00 ET**; final analysis, **28 Nov 2026 12:00 ET**.
- **Nights used:** for each cell and cutoff, the analysis uses the longest unbroken run of nights r00…rk for which every run in that comparison finished (by its manifest time) at or before the cutoff and passed all run checks. Runs that finish later are not used in that analysis, and nights outside the unbroken run are not used either. The number of nights is reported for every cell.
- **Failures:** a run that fails or fails a check pauses new launches. The cause is found and reported. No night is ever dropped because it failed. If a code fix is needed, every affected run is re-run under the new fingerprint, and the fix is logged.
- **Intervals:** cells with fewer than 5 usable nights get point estimates only, with no interval.

## 4. Measures
Per night, from each run's outcomes. These are the same definitions as the L5 batch (`batch.metrics`), over all requests in the slice.
- **Primary:**
  - **Not reached within 20 min:** the share of all requests whose first vehicle curb arrival is more than 1,200 s after the request, or never happens. It is given in percentage points (pp).
  - **Comparison:** cell 1, the per-night difference C − G, averaged over nights.
  - **Interval:** a 95% paired percentile bootstrap over nights, 10,000 resamples, `numpy.random.default_rng(20261110)`.
  - **Decision (D-50 margin):**
    - **C better** if the upper bound is < 0.
    - **Practically equivalent** if the whole interval lies within ±2 pp.
    - Otherwise, **inconclusive at this scale**.

    If the interval is both below 0 and within ±2 pp, the reading is "C better, and within ±2 pp". If the interval is wholly above 0, the result is **G better**. That is reported as found, and the team decides under D-51 before M7.
- **Secondary** (descriptive, 95% bootstrap CIs on the mean per-night C − G, same method and seed, labelled exploratory):
  - P90 passenger wait (passengers picked up), in minutes;
  - P90 van ride time (van-completed requests), in minutes;
  - van-km per van-completed ride;
  - cancellations (while waiting for a van, plus after transfer) per night;
  - cell 5 only: Lyft bookings per 100 requests;
  - cells 2–4: the primary measure's C − G, and its difference from cell 1, stated descriptively (no test).
- **Compute** (reported, not compared): wall time and peak memory per run, solver statuses, and node-limit epochs.

## 5. What does not change after outcomes are seen
- **Settings:** K, the node budget, the objective weights, the guardrail, the pending price, the curb-wait convention, the Lyft settings and the night set.
- **Analysis:** the measures and thresholds above. The analysis code (`m5.py m5b compare`) is written and tested on synthetic per-night values before the first M5b run.
- **Changes:** any later change is a new, labelled analysis. It never replaces this one.

## 6. What a result here does and does not show
- **Shows:** on the first-hour peak (18:00–19:00, backlog finished) of derived L6 nights, how re-optimizing all open work with C compares with myopic, never-revisiting insertion, by fleet, load, re-plan interval and one time-based Lyft rule.
- **Does not show:**
  - whole-evening results (M6/M7);
  - the real TransLoc dispatcher;
  - whole-night optimality of C;
  - Hopkins facts about absolute levels, because patience, presence and the Lyft delay are ASSUMED placeholders.
