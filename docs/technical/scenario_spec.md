# Scenario specification v0.1 (DRAFT, 12 Oct 2026)

**Status:** draft for team agreement (Phase 3 step 3B). **No scenario data may be generated from it until the team approves it in writing**, and the decisions in §14 are settled.

**What it supersedes, once approved:** the v1 scenario contract (`scenario_contract.md`, paused) and the v1 pre-registration (`preregistration.md`, paused). Both are kept unchanged for the record.

**It builds on:**
- `research_review.md` (scope, assumptions);
- `model_design.md` (mathematics, players, metrics);
- `compute_feasibility.md`.

---

## 1. Three things kept apart
| Kind | Examples | Who produces it | Rule |
|---|---|---|---|
| **Scenario inputs** | Request times, origins, destinations, party sizes; vehicle availability; **latent rider and Lyft randomness** (patience, no-show, consent, Lyft delay, ETA noise) | The scenario generator | Policy-independent. Identical across every policy compared on the same night |
| **Policies** | Van dispatcher (T, G, …), objective settings (φ, β, guardrail), cadence and commit rule, **Lyft transfer rule** and its parameters | A policy config file | The only thing that differs between paired arms |
| **Outcomes** | Actual waits, pickups, drop-offs, cancellations, no-shows, transfers, Lyft completions, van-km | The simulator | **Never pre-assigned.** A latent draw (e.g. patience) becomes an outcome only through the simulated events |

**Latent draws are traits, not outcomes.** A rider's patience is drawn in advance. Whether they cancel depends on how long *this* policy makes them wait.

---

## 2. Scope and geography
- **Service:** Homewood Night Ride only; East Baltimore is excluded. Curb-to-curb inside the service area; both trip ends inside it.
- **Boundary: decision D-A (§14).** Recommended: Homewood + Peabody area, as April's dashboard was operated. That area holds ~20% of origins and destinations, and ~34% of model trips touch it. Alternative: Homewood core only.
- **Locations:** the 188 digitized hotspot points (`locations_v1.csv`). They are **demand-generation points** that stand for nearby addresses, **not stops**. Vans stop at each point's snapped road position (`locations_snap_v2.csv`). Documented exception: `p04_b037` at 95 m.
- **Travel times:** **proposed switch to `tt_locations_v2.csv`** (local OSRM v6.0.0, Maryland extract md5 `ff90439c…`, matrix sha256 `b24c0bc6…`), recorded in a `MANIFEST.json`. Decision D-C.
  - Van time = matrix seconds × m_v; Lyft time = matrix seconds × m_L.
  - The multipliers are calibrated: m ∈ [1.0, 1.5], base 1.2 (ASSUMED).
- **Units:** integer **seconds** internally, with t = 0 at 18:00. Minutes are used only in reports.

---

## 3. Scenario inputs

### 3.1 Demand (requests, not completed rides)
- **Volume.** April's request population per day ≈ Completed 803 + Canceled 795 + No-show 79 ≈ **1,680**.
  - This counts every request, including those that become Lyft transfers. Duplicates and rebookings are inside "Canceled", unknown in size.
  - **Base** = 1,680 requests per night. **Variant** = 1,500 (assuming ~10% duplicates).
- **Timing.** Requests are proportional to the completed-rides-by-hour shape, read as **request hour** (AS-25).
  - This is ASSUMED: cancellations may concentrate at peaks, which would tilt the real request profile further toward early evening.
  - Within an hour, arrivals are Poisson, with fixed n per scenario for clean pairing.
- **Bursts (core factor).** A burst variant concentrates 40% of an hour's requests in 10 minutes (ASSUMED), placed at a fixed hour.
- **Geography.** O–D pairs come from the gravity × IPF table (`demand.py`, β = 0.1/min base; D-18), restricted to the chosen boundary.
  - **Spatial-imbalance variant:** the campus-outbound tilt (D-19).
- **Party size.** P(1, 2, 3, 4) = .72/.19/.06/.03 (mean 1.40). **Parties of 5 appear with a small probability** (variant 1%, ASSUMED), because they are the Lyft-ineligible group.

### 3.2 Vehicle availability over the night
This is **an input (supply), distinct from rides per van-hour, which is an outcome.**
- **Profile.** One availability window [start, end] per van. The *shape* follows the April "All services" taper (27.6 → 4.5 vans by clock hour). The *level* is scaled by f.
  - **f is uncertain: 0.65–1.0** (about 18–27.6 vans at 6 pm), because the chart may mix services. It is calibrated (§12) and kept as a factor.
- **Shift ends.** No new pickups after the van's end, beyond a grace period; it finishes riders already on board. Breaks are deferred.
- **Start positions:** the depot (D-17) or hotspots. Capacity 10–14 (base 14; AS-15).

### 3.3 Latent per-request draws (seeded, policy-independent)
| Draw | Distribution (ASSUMED until calibration) | Used when |
|---|---|---|
| `patience_s` | Base: a rising abandonment hazard (e.g. Weibull, shape > 1), calibrated so rider cancellations ≈ 2/3 of "Canceled" | The rider is still unpicked when patience runs out (with the van or after a transfer) |
| `noshow_u` | Uniform(0, 1); the rider no-shows if below p_ns = 0.047 | The van arrives |
| `consent_u` | Uniform(0, 1); the rider accepts a Lyft if below p_c (base 1.0) | A transfer is decided |
| `lyft_delay_s` | Lognormal, median 8 min, P90 ~15 min (ASSUMED); scarcity variant | A transfer is placed |
| `lyft_noshow_u` | Uniform(0, 1); Lyft no-show below p_lns (base = p_ns) | The Lyft arrives |
| `eta_noise` | Per-request multiplier on the displayed ETA (variant) | Only if patience depends on the shown ETA |

**Every draw is made for every request,** whether it is used or not. That way every policy sees identical riders: these are **common random numbers**.

---

## 4. Policies (configuration, not data)
| Setting | Base | Variants |
|---|---|---|
| Dispatcher | **T** (TransLoc-like heuristic) | T− (no reassignment / 300 s), G (greedy); C and H on L1–L4 only |
| Cadence Δ | 120 s + events | 60 / 300 s (sensitivity only) |
| Commit rule | Next stop frozen; at the curb | ETA ≤ 5 min |
| Wait penalty φ | Piecewise linear, slopes 1 / 2.5 / 5 / 10 / 20 per min at breaks 5/10/15/20 | Gentler, steeper |
| Ride weight β; distance γ | 0.5; 0.1 min/km | β 0.25 / 1; lexicographic variant |
| Ride guardrail | max(25 min, 2·direct + 5 min), elastic | 20 (hard target), 35 |
| **Lyft rule** | **The factor under study** (§6) | — |
| Dispatcher lag ℓ | 2 min | 0 / 5 |
| Dispatcher capacity | Unlimited | k = 3 per 10 min |

---

## 5. Outcomes (produced by the simulator; schema in §10)
Every request has **exactly one terminal state**:
- `van_completed`;
- `lyft_completed`;
- `cancel_pending_van`;
- `cancel_after_transfer`;
- `noshow_van`;
- `noshow_lyft`;
- `unresolved_close` (must be 0).

**A Lyft transfer is an event, not a terminal state.** Wait is always **actual pickup (either mode) − request time**.

**Derived, for calibration only:** a dashboard view, where "Completed" = van-completed and "Canceled" = rider cancellations + transfers. A variant leaves transfers out of "Canceled".

---

## 6. Lyft transfer strategies (compact set)
**Common to all rules:**
- **eligibility:** party ≤ 4, pending (not onboard, not committed);
- consent;
- dispatcher lag ℓ;
- **Lyft pickup time** = decision time + ℓ + `lyft_delay_s`;
- the rider's patience keeps running.

The rule is evaluated after every dispatcher solve, at time τ.

| Rule | Fires when | Clock origin | Information needed | Notes |
|---|---|---|---|---|
| **R0 Never** | — | — | — | Reference only; not the status quo |
| **R1(θ) Elapsed wait** | τ − t_r ≥ θ | The **request time** | The request time | θ ∈ {10, 15}. "Waited 15 min, then transfer". Total wait ≥ θ + ℓ + Lyft delay |
| **R1u(θ) Elapsed unassigned** | Time continuously **without an assigned van** ≥ θ | The **moment it became unassigned** (initially t_r) | Assignment status | Closest documented form (East Baltimore FAQ: "within ten minutes without a van assigned"); HYPOTHESIS for Homewood. θ = 10 |
| **R2(θ) Predicted total wait** | P̂_r(τ) − t_r > θ, where P̂_r is the plan's predicted pickup time (∞ if unassigned) | The **request time**; the test looks **forward** | Plan ETAs | Acts as soon as the plan predicts a breach, possibly at request time. θ = 15. Sensitive to ETA churn |
| **R3(m) Van vs Lyft** | P̂_r(τ) > τ + ℓ + L̄ + m, where L̄ is the dispatcher's typical Lyft delay (median 8 min) | **Now** | Plan ETAs, a typical Lyft delay, the lag | Transfers when a Lyft would plausibly arrive earlier by margin m (m = 2 min) |
| **R4 Congestion-gated** (optional) | R2 or R3, applied only when the congestion index (pending requests ÷ available vans, or the median predicted wait) > κ | — | Board totals | Represents "peak service hours". Include only if R2/R3 transfer heavily off-peak |

**"Waiting 15 minutes before transferring" (R1) differs from "acting when total predicted van wait exceeds 15 minutes" (R2).**
- R1 always lets the rider wait θ first.
- R2 can transfer at minute 1.
- Both count waiting from the original request time.

---

## 7. Fair comparison rules
1. **Paired nights:** every policy runs on the identical scenario file (requests + latent draws + availability).
2. **One factor at a time:** when comparing Lyft rules, the dispatcher, objective, cadence and commit rule are held fixed (base T). Dispatcher and objective appear only as **supporting** dimensions (SQ1/SQ3).
3. **Common random numbers:** latent draws are per request, from named seed streams (§11). No policy can change which draw a rider gets.
4. **No post-hoc tuning:** thresholds and settings are fixed in the pre-registration (to be re-written from this spec) before any comparison run.
5. **Report frontiers,** not single winners: rider outcome vs Lyft trips (and van-km).

---

## 8. The level ladder (validation first, then the research question)
**Cancellations and no-shows enter separately.**
- A no-show happens **at the curb**: the van waits 3 min, then a re-plan.
- A cancellation happens **while pending**: it removes a request from plans and from the Lyft rule.
- Mixing them would hide which accounting is wrong.

| Level | Size | Adds | Purpose | Tests Lyft? |
|---|---|---|---|---|
| **L1** | 2 vans, 16 requests | Automatic re-planning dispatcher; deterministic times; no cancellations, no-shows or Lyft. Arrivals spaced (≤ 2 open at a time) | **Hand-checkable**: every pickup and drop-off time is computed by hand (spreadsheet) **and** by the exact solver; T, G and C must agree, or the difference must be explained | No |
| **L2** | 2 vans, 16 | No-shows: 2 designated requests (deterministic) | The 3-min wait, the no-show event, re-plan, accounting | No |
| **L3** | 2 vans, 16 | Rider cancellations: designated patience values so that 2–3 requests cancel | The pending-state cancel path; dispatcher reaction | No |
| **L4** | 2 vans, 16, compressed into 20 min | Lyft rules R0/R1/R2/R3 with a deterministic lag and Lyft delay | **Lyft mechanics**: the clock is not reset, transfer ≠ completion, eligibility (one party of 5), consent; hand-traceable differences between rules | **Mechanics** |
| **L5** | 2 vans, 24–32, with a burst | Stochastic latent draws (patience, Lyft delay, no-show), lag, 30 paired seeds | Pilot of the full pipeline: pairing, metrics, frontiers. Small, so **not** a basis for conclusions | Pilot |
| **L6** | Homewood peak window 18:00–21:00; availability scaled by f; calibrated demand | Everything; driver-response and capacity variants as sensitivity | **Main Lyft-policy experiments** (starts empty at 18:00, the first hour of service) | **Yes** |
| **L7** | Full night 18:00–02:00 with the taper and the post-02:00 backlog | Everything | **Confirmatory** subset; shift ends and the night's tail | **Yes** |

**Expected results, stated in advance:**
- **L1–L4 are correctness levels.** Algorithm differences are expected to be ~0 at L1–L4 (low load).
- **L5 is a pipeline pilot.** Credible policy conclusions come only from L6–L7.

---

## 9. Compact experiment matrix (replacing the paused 330-scenario grid)
**Primary (L6), varying only the Lyft rule and the conditions:**
- **Lyft rule (6):** R0, R1(15), R1u(10), R2(15), R3(2), plus R1(10) as a threshold check;
- **demand condition (3):** base; high (+30%); burst;
- **fleet level (2):** f_low and f_high from the calibrated range.

That is 6 × 3 × 2 = **36 cells × 30 paired seeds = 1,080 three-hour runs**. Runtime is estimated in `compute_feasibility.md`, to be measured by benchmark B3 before this is fixed.

**Confirmatory (L7):** 6 rules × base demand × mid fleet level × 30 seeds = 180 full nights.

**Robustness blocks** (L6, base condition, rules R0/R1(15)/R2(15)/R3, one factor at a time, 30 seeds):
- **dispatcher:** T, T−, G (SQ1);
- **Lyft delay:** median 5 / 8 / 12 min, plus a scarcity variant;
- **dispatcher lag:** 0 / 2 / 5; consent 1.0 / 0.8; capacity unlimited / 3 per 10 min;
- **patience:** low / mid / high, taken from the identified calibration set;
- **objective:** wait-heavy / base / ride-heavy (SQ3);
- **travel multiplier:** 1.0 / 1.2 / 1.5;
- **boundary**, if D-A chooses "factor";
- **targets:** report at 10 min and 15 min.

**Algorithm references:** L1–L4 with G, T, C (and H on L1).

**Seeds:** 30 per cell. A power check on L5/L6 pilot variance decides whether 30 is enough, before the main runs.

---

## 10. File schemas (to be generated only after approval)
`data/scenarios/v2/<level>/<cell>/r<NN>/`:

| File | Columns / fields | Units |
|---|---|---|
| `requests.csv` | request_id, t_request_s, o_loc, d_loc, o_zone, d_zone, party, direct_s (v2 matrix, unscaled) | s |
| `latent.csv` | request_id, patience_s, noshow_u, consent_u, lyft_delay_s, lyft_noshow_u, eta_noise | s / unitless |
| `availability.csv` | van_id, start_loc, capacity, avail_start_s, avail_end_s | s, seats |
| `scenario.json` | level, cell, params (all, with evidence labels), seeds (master seed + named spawn keys), `MANIFEST.json` hash (pbf md5, image digests, matrix and snap sha256, platform), generator code version, content hash | — |
| `policy.json` (separate, per arm) | dispatcher, objective settings, cadence, commit rule, Lyft rule + parameters | — |
| Simulator outputs (Phase 4): `events.csv`, `outcomes.csv`, `run_manifest.json` | per-event log; per-request terminal state, times, mode, transfer time, ETA churn; environment and solve statistics | s |

---

## 11. Seeds
- `SeedSequence(master_seed, spawn_key=(level_id, cell_id, replicate, component_id))`.
- **Named components:** count, times, od, party, availability, patience, noshow, consent, lyft_delay, lyft_noshow, eta_noise, solver.
- **Adding a component must never shift the others.**
- Factors that should not change the riders (fleet level, Lyft rule, dispatcher) **share the demand and latent streams**. The demand condition (base / high / burst) changes the demand streams by design.

---

## 12. Validation and calibration
**Validation (each level, before moving on):**
- **L1:** exact agreement with the hand schedule, to the second.
- **Accounting identity:** requests = Σ terminal states; no request in two states; transfers ≤ eligible requests.
- **Constraints:** every plan is audited for capacity, precedence, commitments, shift ends and guardrail violations, which are logged.
- **Determinism:** the same inputs give an identical output hash; 1 worker vs 4 workers give identical results.
- **Clock:** a transferred rider's wait equals the Lyft pickup time minus the request time (checked on L4 by hand).

**Calibration (L7, base settings, before any policy comparison):**
- **Targets (loose bands, not exact fits):**
  - completed rides per night ≈ 803 (±10%);
  - "Canceled" share 0.31–0.68 by day, ~0.47 pooled;
  - Lyft rider share 10–46% by day, ~24.5% pooled;
  - no-show ~4.7%;
  - completed-ride wait median ~10–13 min and P90 ~17–21 min;
  - ride P90 ~24 min;
  - the hourly shape of completed rides.
- **Knobs:** fleet level f, the patience scale, the travel multiplier, the base Lyft rule threshold (the "status-quo" rule).
- **Limits:**
  - waits and rides are survivor-biased (completed only);
  - the wait–cancellation link is correlational;
  - the vehicle counts are mixed-service;
  - there is no hourly Lyft or cancellation data.

  Several knob combinations will pass. **Keep the set that passes (the identified set)**, and re-run the main comparison across its extremes. A single "calibrated point" is not claimed.

---

## 13. What changes from v1 (paused)
| v1 | v2 (proposed) | Why |
|---|---|---|
| 5 vans / 30 requests, one hour | L1–L7 ladder; L6 peak window and L7 full night | Mechanisms first; credible conclusions need Homewood scale |
| 4 seats (D-22) | 10–14, base 14 | 2018 evidence |
| Hard 20/25 limits (D-04) | Homewood 15/20 as reporting thresholds; elastic guardrail | 20/25 are East Baltimore's figures; the targets are soft and moved in 2024 |
| No Lyft; no driver response | Lyft rule as the primary factor; driver response as sensitivity | Research question |
| Patience median 12 min, exponential | Rising hazard, calibrated to ~2/3 of "Canceled" | The placeholder explained all cancellations |
| Demand matrix v1 (demo server) | v2 (local, pinned) | Reproducibility |
| 11 cells × 30 grid | 36 primary cells + robustness blocks | Focus on the Lyft question |

---

## 14. Decisions needed before generating data
| ID | Decision | Recommendation |
|---|---|---|
| **D-A** | Boundary: Homewood + Peabody, core only, or a factor | **Homewood + Peabody** (as April was operated) |
| **D-B** | Accept the scope and question: Homewood only, door-to-door, Lyft rules as the primary factor with the dispatcher fixed at T | Accept |
| **D-C** | Switch the travel matrix to v2 (local) and adopt MANIFEST/matrix-as-canonical | Accept |
| **D-D** | Objective: weighted with convex φ and an elastic guardrail (lexicographic as a variant) | Accept |
| **D-E** | Lyft rule set R0–R3 (R4 optional) and their parameters | Accept, or trim |
| **D-F** | Fleet as a calibrated range f ∈ [0.65, 1.0], not a fixed 22 | Accept |
| **D-G** | Ladder L1–L7 with no-shows and cancellations separate | Accept |

Smaller parameter values (slopes, β, lag, Lyft delay) are proposals. They are fixed in the re-written pre-registration after these decisions.
