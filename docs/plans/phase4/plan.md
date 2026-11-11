# Phase 4, Simulator and dispatcher: plan (v2, 10 Nov 2026)

**Status:** in progress. M0–M3 done and verified. **D-59 and D-60 approved 10 Nov. M4 done 10 Nov; G built and reviewed 10 Nov; M5a passed 10 Nov (M5b with 30 nights); high-load probe 11 Nov (≈ 2–4 h per night); D-61 run order and stopping rule approved 11 Nov; M5b preregistration drafted, next: team freezes it, then M5b group A.**

**Authority.** This plan only sequences the work. What to build is in `docs/technical/scenario_spec.md` v0.9 §17 (build contract) and `docs/technical/model_design.md` v0.6 (G is defined in §6.1); decisions are in `docs/technical/decision_log.md`; the milestone list and its reasons are in `docs/technical/scenario_methodology.md` v1.7 §8.

**Previous versions:** `versions/v1_2026-10-22.md`. Why it changes: `log.md` (10 Nov: M4–M5 detailed; M5 widened from a compute benchmark to compute + a C-vs-greedy comparison, to answer the instructor's open question).

## Scope fixed by the team (22 Oct 2026)
- Dispatcher C (restricted route-selection MILP, HiGHS) is provisionally the dispatcher held fixed (D-51), conditional on the M5 benchmark. T is a contingency or later robustness variant, never a runtime fallback.
- No financial modelling (D-45). Lyft tracking keeps operational outcomes and resource counts.
- Frozen inputs are read, never changed; routing data is not rebuilt.

## Milestones
| Milestone | Content | Status |
|---|---|---|
| M0 | Event engine reproduces L1–L3 answer keys and the L4 pre-18:15 Lyft mechanics | **Done 22 Oct** (methodology §7) |
| M1 | C on L4 under R0, with event and epoch logs and a readable narrative | **Done 22 Oct** |
| M1.5 | D-53 decision experiment (original / A / B pending price) and curb-wait convention D-54 | **Done 22 Oct**; A approved provisionally |
| M2 | Lyft rules all evening with C on L4 | **Done 22 Oct** (D-55) |
| M3 | L5, 30 nights × 6 rules: pairing, metrics, bootstrap CIs, pilot variance | **Done**: batch 22 Oct (D-56, D-57); D-50 approved and paired-interval rehearsal 10 Nov (D-58) |
| M4 | L6 builder, 64 / 50 / 54 (new scenario generation) | **Done 10 Nov** (D-59; `research_notes/m4_l6_build_2026-11-10.md`) |
| M5 | First hour, 5 vans, 64 requests: (a) compute benchmark of C; (b) C vs greedy G | **Planned** (below); D-60 approved 10 Nov |
| M6 | Full 168-request, five-van demonstration | Not started; after M5, if time allows before the preview |
| M7 | Experiment grid | Not started; no Lyft-rule comparison before then. Expected after the 26 Nov preview |

Not in Phase 4 scope until decided: heuristic T, hindsight H, calibration, the L7 taper and shift ends, R4(14, 6) (P-13).

---

## M4 and M5 in detail (v2, 10 Nov)

### Why this, and why now
- **The instructor's main open question** (proposal comment, `docs/proposal/feedback_proposal_kearsley.md` point 2): *under what demand and fleet conditions does the rolling-horizon MILP beat greedy assignment?* Our answer today is "not tested".
- **Our own open condition:** C is held fixed only provisionally, "conditional on the M5 benchmark" (D-51). The M5 written in methodology v1.7 §8 and Appendix D measures only whether C *fits the compute budget*. It does not ask whether C is *better than something simpler*.
- **Deadlines:** a most-complete preview to the instructor before 26 Nov; the final presentation on 1 Dec. M5 is the result that preview most needs.
- **Mentor note:** a tie between C and G is a real, presentable finding (it would mean that, at this scale and density, re-optimizing adds little). The plan is written so that either outcome is defensible.

### What each part claims, and what it does not
| Part | Supports the claim | Does **not** show |
|---|---|---|
| M4 | "The L6 nights follow the agreed recipe (D-35, D-36), are reproducible byte for byte, and are the same for every policy" | That 168 requests is April's real demand (it is a derived workload) |
| M5a | "C solves every epoch of a five-van first hour within its budget, deterministically" | Anything about rider outcomes |
| M5b | "On the same first-hour nights, C vs G differ by X (95% CI) in the share not reached within 20 min, and the gap moves (or not) with fleet, load and re-plan interval" | Whole-evening results; the real TransLoc dispatcher; that C is optimal over the night (per-epoch optimality ≠ whole-night optimality) |

### M4: the L6 builder (first-hour slice used by M5)
**D-59 approved (team, 10 Nov).** The spec reserves new scenario generation for a team go-ahead.

**What is built.** One builder, `build_l6(pattern, replicate)` in `src/scenario/generator_v2.py`, following spec §3 and §10–11 exactly:
- fleet: 5 vans, 14 seats, at the depot, on duty from 18:00 to the end of the backlog (D-36); the 6-van case adds one van at the depot and **reuses the same requests** (D-37);
- volume: 64 / 50 / 54 = 168 for the base pattern; high load ρ × 1.3, giving 83 / 66 / 70 = 219 (largest-remainder rule, recomputed by the builder and checked against a hand calculation);
- timing: a fixed count per clock hour, at uniform random times within the hour;
- O–D from the gravity × IPF table; party sizes; latent draws (patience, presence, consent, Lyft delay), all as in L5;
- seeds: `SeedSequence(master, spawn_key=(level, pattern, replicate, component))`, with the fleet level, rule and dispatcher **not** in the key.

**What is generated:** `data/scenarios/v2/L6/{base,high}/r00..r29/` (60 nights), frozen with content hashes in `FROZEN_v2.json`. Burst and far-trip are deferred to M7: M5 does not need them.

**The first-hour slice.** M5 runs the requests with `t_request_s < 3600` from each L6 night (64 base, 83 high), with vans on duty until the backlog is finished. Because counts are fixed per hour, the slice is exactly the first block of the full night; nothing is regenerated for M6.

**Checks (all must pass before M5):**
1. Hour counts are exactly 64 / 50 / 54 (base) and 83 / 66 / 70 (high).
2. Party-size, O–D-zone and patience distributions over the 30 nights match the recipe, using the same validation as L5 (`validate.py`).
3. Rebuilding any night gives the same content hash; changing one component seed changes only that component's file.
4. The base and high patterns differ by design: the comparison is not paired across them (D-49). The 5- and 6-van versions of a night have identical requests and latent draws.
5. A map of one night (reusing `map_levels_v2.py`) for a visual sanity check.

### M5a: compute benchmark of C (as already defined in methodology Appendix D)
**Runs:** C under R0 on the base first-hour slice, **3 nights** (r00–r02), 5 vans, run twice each for determinism.

**Measures:** Appendix D's list: epochs per night; open requests and candidates per van per epoch; MILP size; solve time (median, P99, max); the share of epochs at the node limit or with a non-zero gap; wall time and peak memory per night; identical event logs on repeat; a K = 4 coverage check on a sample of epochs.

**Blind rule:** M5a reports **compute only**. Rider outcomes from these runs are not looked at or tabulated until M5b's criteria are frozen. That keeps any change made after M5a (K, cadence, budget) independent of which dispatcher looks better.

**Gate (thresholds approved with D-60):**
- **STOP and report** if any plan audit fails, a repeat run differs, or more than 5% of epochs end at the node limit.
- **STOP and decide the night count** if the median C first-hour night takes more than 15 min of wall time, because the M5b grid has six C cells. The count is then set from compute alone and recorded before M5b runs.
- Otherwise, M5b runs with 30 nights.

**Reference point:** L5 nights (2 vans, 28 requests an hour) took a median of 16 s, P90 71 s and max 253 s per night. The five-van first hour has ~2.3× the open requests, so candidate counts per van (subsets of ≤ 3) rise steeply. That is why M5a comes first.

### M5b: C vs greedy G
**D-60 approved (team, 10 Nov):** adds G and this comparison to M5, with the pre-registered criteria below.

**G, as defined in model_design §6.1:** insert each new request, on arrival, at its cheapest feasible position (pickup and drop-off) in some van's current route, using the **same** route-cost function, guardrail and capacity rules as C; **never reassign**. A request with no feasible insertion stays pending and is retried at each later epoch. G keeps its own assignment state inside the dispatcher wrapper; the engine, observation and Lyft module are unchanged. G returns the same `Plan` object as C (routes, predicted pickups), so the time-based Lyft rule works identically for both.

**Built and reviewed 10 Nov** (`research_notes/m5_greedy_build_2026-11-10.md`). Designed differences from C, stated in advance: G has no K cap; an insertion may not push an aboard rider above max(guardrail, their ride in G's current plan), where C's reference is its committed-only route; G refuses R2/R3 (no ETA for pending requests).

**Fairness:** same nights, same latent draws, same objective terms used to score insertions, same capacity and guardrail, same event engine. The one designed difference is the algorithm, and with it reassignment. The comparison therefore measures *re-optimizing all open work with the MILP* against *myopic insertion that never revisits a decision*. That is the contrast the instructor asked about.

**Cells (first-hour slice, 30 paired nights each unless the M5a gate says otherwise):**
| # | Condition | Dispatchers | Lyft rule | Answers |
|---|---|---|---|---|
| 1 | Base, 5 vans, 120 s re-plan | C, G | R0 | **Primary:** does C beat G at the planned scale? |
| 2 | Base, 6 vans (same requests, D-37) | C, G | R0 | Fleet size: does the gap shrink with slack? |
| 3 | High load ×1.3, 5 vans | C, G | R0 | Demand intensity: does the gap grow under pressure? |
| 4 | Base, 5 vans, re-plan 60 s and 300 s | C only (vs cell 1's G) | R0 | "Horizon": our C has no look-ahead, so the knob that exists is how often it re-plans |
| 5 | Base, 5 vans | C, G | R1(10) | Lyft overflow: with a time-based rule (it fires on elapsed time, not on the dispatcher's prediction, so it is equally fair to both), how many bookings per 100 requests does each dispatcher leave? |

Cell 4 holds G fixed because G acts on arrival; its re-plan interval changes nothing. Cell 3 is compared within its pattern (C vs G on the same high-load nights), never against cell 1.

**Pre-registered criteria (frozen before the first M5b run):**
- **Primary:** cell 1, share of all requests not reached within 20 min, paired C − G, 95% paired percentile bootstrap (10,000 resamples of nights, seed 20261110), as approved for D-50.
  - **C better** if the upper bound < 0.
  - **Practically equivalent** if the whole interval lies within ±2 pp (the D-50 margin).
  - Otherwise **inconclusive at this scale**.
- **Secondary (descriptive, 95% CIs, labelled exploratory):** P90 passenger wait; P90 ride time; van-km per completed ride; cancellations; for cell 5, Lyft bookings per 100 requests. Cells 2–4: the same C − G difference per cell, and whether it changes against cell 1.
- **No tuning after outcomes:** K = 3, the node budget, the objective weights and the guardrail stay at their D-52 / D-29 values unless the M5a compute gate changes them, and that is decided blind to outcomes.

**What M5b means for D-51:**
- If C is better or equivalent, D-51 stands and the M7 grid runs on C.
- If G is better, that is reported as found and the team decides before M7 whether to change the fixed dispatcher (D-51 already provides for this).

### Deliverables
- `src/scenario/generator_v2.py` (`build_l6`), `build_levels_v2.py` (an L6 section), and tests for counts, determinism and seed isolation.
- `src/sim/dispatch_greedy.py` (G) with tests: a hand-checkable insertion case on L1, a never-reassigns check, and identical outputs on repeat.
- `src/sim/m5.py`: runs the cells (resumable, with per-run checks, reusing `batch.py`'s pattern); `outputs/sim/m5/` with `compute.md` (M5a) and `comparison.md` (M5b).
- `docs/technical/research_notes/m5_preregistration_2026-11.md`: the M5b criteria above, frozen with a date before the first run.
- At the end: the D-51 outcome logged; methodology v1.8, spec and model_design bumped per the versioning rule; one figure for the preview (C − G with CIs by cell).

### Schedule (to the 26 Nov preview)
| Dates | Step | Gate |
|---|---|---|
| 10–11 Nov | Team reviews D-59 and D-60 | Approvals logged |
| 11–12 Nov | M4: builder, 60 nights, checks, frozen hashes | Checks 1–5 pass |
| ~~12–14 Nov~~ **10 Nov** | G built and tested (done); M5 runner (next) | Tests pass; independent review done, one defect fixed |
| ~~14–15 Nov~~ **10 Nov** | M5a: 3 nights × 2 repeats (done; `research_notes/m5a_compute_2026-11-10.md`) | Compute gate: passed (median night 3.6 min, 0 node-limit epochs, repeats identical) |
| 15 Nov | Freeze `m5_preregistration` (drafted 11 Nov, with D-61) | Dated before the first M5b run; the runner refuses M5b until it reads FROZEN |
| 15–19 Nov | M5b runs: group A (cells 1, 2, 5, 4) then group B (cell 3, ≤ 2 workers), fixed order (D-61) | Per-run checks; pause on failure; preview cutoff 19 Nov 12:00 ET, final cutoff 28 Nov 12:00 ET |
| 19–21 Nov | Analysis, figure, docs update | Independent check of the numbers |
| 22–25 Nov | Preview package to the instructor | — |
| After 26 Nov | M6 (full evening), then M7 | — |

**Slack:** about two days. If M5a shows C is slow, the first thing to cut is cell 4 (the re-plan interval), then cell 5; cells 1–3 are the answer to the instructor's question.

### Risks
- **C is too slow at five vans.** The M5a gate catches this before outcomes exist. Options then (team choice): fewer nights, a smaller K, or the `fix_existing_drop_order` setting already reserved for M5 (D-52 amendment).
- **G's implementation biases the result.** Mitigation: G scores insertions with C's own route evaluator; it gets a hand-checked test and an independent review before any comparison run.
- **First hour only.** Results are stated for the 18:00–19:00 peak with the backlog finished; whole-evening results wait for M6/M7.
- **Placeholder behaviour** (patience, presence, Lyft delay are ASSUMED until calibration). This affects C and G equally, but absolute levels are not Hopkins facts.
