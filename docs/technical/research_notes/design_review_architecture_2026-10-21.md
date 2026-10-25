# Independent design review: simulator architecture and feasibility (21 Oct 2026)

**Reviewer scope:** can the documented design be turned into an event-driven simulator that is deterministic, checkable against the L1–L4 answer keys, and fast enough for the 5-van, 18:00–21:00, 168-request demonstration? Read-only review. No code written, nothing else edited.

**Files read:** `model_design.md` (§3, §5–§8), `scenario_spec.md` (§1, §4–§8, §10–§12), `decision_log.md` (D-25, D-29, D-36–D-44, design-trail sections 7–10), `compute_feasibility.md`, `team_config.v2.json`, `data/scenarios/v2/L1–L4` (`HANDCHECK.md`, `handcheck.csv`, `availability.csv`, `latent.csv`, `requests.csv`), `src/scenario/generator_v2.py`, `requirements-lock.txt`. I also skimmed `transloc_operations.md` §3.2 and `math_literature.md` §2.2 for the candidate-route and TransLoc facts.

**Labels used:** [FACT] read in a file or exact arithmetic; [ESTIMATE] reasoned, assumptions stated, never measured; [UNKNOWN] nobody can say yet. Finding classes: **resolved**, **base assumption** (transparent, keep and state), **deferred sensitivity**, **BLOCKER** (must be settled before the code that depends on it is written).

---

## 0. Bottom line (plain words)

The design is sound and nearly complete for a first working simulator. The hand-check answer keys quietly settle several things the prose documents leave open (the pickup event is the curb arrival, a cancelled committed stop is still driven to, same-second epochs are merged). What is missing is a short list of rules that every event handler needs, mainly: what exactly happens to a rider between a Lyft decision and the Lyft booking, a complete same-second event order, whether solver time costs simulated time, and what "at most 2 new requests per route" does to the ETAs the Lyft rules read. None needs new research; each needs one written rule. I give a recommended rule for each below.

Answer to "which dispatcher is approved": **only the direction is approved** (D-25: a TransLoc-like re-planning dispatcher is the fixed baseline). The specific algorithm (insertion plus local search heuristic "T" versus the route-selection MILP "C"), the 120-s cadence, the commit rule and the latency rule are still **proposals** in the decision log. Details in §7.

Smallest milestone that shows real optimization: **L4 under R0 with the real dispatcher**: 2 vans, 16 requests, nine of them already waiting when the vans come on duty at 18:15, route-selection MILP versus greedy insertion on the identical inputs, with a ~100-row event log. Details in §8.

**Blockers (for code that depends on them):** B1 same-second event order and epoch rule (§3); B2 transfer commitment rule (§2); B3 solver-latency contradiction (§4); B4 meaning of `max_new_per_route` (affects R1u, R2, R3 at L6; not the first milestone); B5 no L6 scenario builder and no output or policy schemas (§5, §6). Everything else is resolved or a labelled assumption.

---

## 1. Request state machine

### 1.1 Reconstructed machine (what the documents and answer keys jointly imply)

| State | Meaning | Source |
|---|---|---|
| (not revealed) | before `t_request_s`; invisible to every policy | `model_design.md` §3.1 |
| PENDING | revealed, not in any van's current route | §3.2 "pending", §3.3 `u_r` |
| ASSIGNED | in some van's route, not yet the frozen next stop; reassignable | §3.2 R(τ), §5 Reassignment |
| COMMITTED | pickup is the frozen next stop of a van that has departed toward it | §3.2 C_v; L3 key |
| AT_CURB | van arrived; presence test done; boarding dwell or the up-to-3-min wait running | D-40; L2 key |
| ONBOARD | boarded; fixed to the van | §3.2 O_v |
| XFER_HOLD | Lyft decided and consent given; booking not yet placed (lag ℓ) | D-43, `scenario_spec.md` §6 |
| LYFT_BOOKED | booking placed; Lyft vehicle on its way; patience still running | D-43 |
| LYFT_AT_CURB | Lyft arrived; presence test; boarding or ≤3-min wait | D-40, D-41 |
| LYFT_ONBOARD | in the Lyft | D-43 |

Terminals: `van_completed`, `lyft_completed`, `cancel_pending_van`, `cancel_after_transfer`, `noshow_van`, `noshow_lyft`, `lyft_failed` (sensitivity, f = 0 in base), `unresolved_close` (must be 0).

### 1.2 Transitions and the guard that keeps each path to exactly one terminal

| From | Event | To | Guard / note |
|---|---|---|---|
| PENDING / ASSIGNED | plan changes | PENDING / ASSIGNED | attribute flips every epoch; not a lifecycle state. R1u needs `unassigned_since` (see F-19) |
| ASSIGNED | van departs toward it | COMMITTED | commitment = departure (rule in §2.3) |
| PENDING / ASSIGNED / COMMITTED | patience deadline reached, no vehicle yet arrived | **cancel_pending_van** | L3 key uses this label even when a van is already driving (committed). Van still finishes the leg, free on arrival, no dwell (L3 `HANDCHECK.md`) |
| COMMITTED | van arrives (curb arrival) | AT_CURB | arrival ends the patience clock; arrival wins a same-second tie (D-39) |
| AT_CURB | present, dwell done | ONBOARD | |
| AT_CURB | absent (U_r < p_van), 180 s elapsed | **noshow_van** | van released at the curb; re-plan (D-40; L2 key) |
| ONBOARD | van reaches destination | **van_completed** | `dropoff_s` in the keys = arrival at the destination; van free 30 s later |
| PENDING / ASSIGNED (not COMMITTED) | Lyft pass fires AND consent_u < p_c | XFER_HOLD | leaves van planning here (rule R-XFER, §2) |
| PENDING / ASSIGNED | Lyft pass fires, consent declined | unchanged | "offered, declined, not offered again" (L4 key) |
| XFER_HOLD | lag ℓ elapsed | LYFT_BOOKED | no-op if the rider already cancelled |
| XFER_HOLD / LYFT_BOOKED | patience deadline reached | **cancel_after_transfer** | `model_design.md` §7 "during lag or the Lyft wait" |
| LYFT_BOOKED | Lyft arrives | LYFT_AT_CURB | arrival wins ties; Lyft failure draw (sensitivity) would give `lyft_failed` here |
| LYFT_AT_CURB | present / absent after ≤180 s | LYFT_ONBOARD / **noshow_lyft** | no automatic rebooking (D-43 simplification) |
| LYFT_ONBOARD | reaches destination | **lyft_completed** | key: pickup arrival + 30 s boarding dwell + direct time |

**Does every path reach exactly one terminal?** Yes on paper, provided three guards are implemented: (a) every scheduled event (patience, booking, Lyft arrival, van arrival) re-checks the request's current state and is a no-op if the state moved on (lazy invalidation, not queue deletion); (b) the transferred state is excluded from every van candidate route (§2); (c) a terminal request ignores all later events. Violating (b) is the only way to get two terminals (a van completes a rider who is also Lyft-booked).

### 1.3 Gaps found

| ID | Gap | Class | Consequence / resolution |
|---|---|---|---|
| F-1 | `lyft_failed` is in D-43 but missing from the terminal lists in `scenario_spec.md` §5 and `model_design.md` §7; the accounting identity as written would not balance if f > 0 | Doc sync (resolved by listing it) | Add to both lists; identity: requests = Σ of all eight terminal counts |
| F-2 | The label `cancel_pending_van` also covers a committed rider whose van is en route | Resolved by L3 key | State it in the spec; analyses that mean "never had a van near" need the `committed_at` field in `outcomes.csv` |
| F-3 | Van shift end: riders assigned to a van that goes off duty must return to PENDING; shift-end grace period g is "ASSUMED" in `model_design.md` §3.3 but has no number anywhere | **BLOCKER (small)** for L5/L6 | Pick g (suggest 0 for the first run, so "no new pickup after `avail_end_s`") and write it down. See F-10 |
| F-4 | Pending riders with no van on duty ever again (R0) wait for patience. Terminates because every rider has a finite deadline (designed levels use 36,000 s) | Resolved | Simulation end = queue empty; `unresolved_close` only if a hard time cap is hit; set the cap explicitly (suggest 02:00 + 3 h) and log it |

---

## 2. Transfer commitment: decision or booking?

### 2.1 What the documents say
- `model_design.md` §3.2 defines open requests R(τ) as "not committed, not cancelled, **not transferred**". `scenario_spec.md` §6 eligibility is "still pending (not onboard, not committed)". D-43: "After a transfer the request leaves van planning, but its service is still evaluated", with the sequence decision → booking (after ℓ) → arrival.
- The L4 answer key (`handcheck.csv`, `HANDCHECK.md`) charges the wait from the original request and uses decision + ℓ for the Lyft request, so the clock is consistent either way.
- **Not stated:** whether "transfer" means the decision or the booking. During the 2-minute lag there are two legal readings, and one of them allows a van to pick the rider up while a Lyft is about to be booked.

### 2.2 The duplicate-service risk, concretely
[FACT] ℓ = 120 s and Δ = 120 s, so at least one tick falls inside every lag. If the request is still in the van pool during the lag, that tick can assign it, and a van two minutes away can commit to it. Then either the Lyft is booked for a rider already on a van (two terminals) or the simulator needs an abort path that nobody has specified.

### 2.3 Recommended single rule (R-XFER)
1. **The request leaves van planning at the transfer decision**, atomically, in the same epoch. At that instant: consent is applied, state becomes XFER_HOLD, the request is removed from R(τ) and from every van's route, and a re-solve is triggered (this is the "Lyft transfer" trigger in `model_design.md` §5; it fires at the decision, not at the booking).
2. The booking event at decision + ℓ is a pure state change (XFER_HOLD → LYFT_BOOKED). The Lyft arrival is scheduled at decision + ℓ + `lyft_delay_s` (matches `scenario_spec.md` §6).
3. **Patience during the lag:** if the deadline falls inside the lag, outcome `cancel_after_transfer`; the booking event becomes a no-op; the cost ledger (D-44) records a transfer offer but **no booking and no fee**.
4. **Patience after the booking:** `cancel_after_transfer`; the Lyft vehicle is cancelled; the ledger records a booking and a rider-cancellation fee category (price scenario decides the amount).
5. **Plan audit invariant, checked at every epoch:** no request id appears both in a van route and in XFER_HOLD / LYFT_*. A violation stops the run.
6. The Lyft pass runs **after** the dispatcher solve and reads commit flags from that same solve, so a request committed in this epoch is already ineligible (consistent with "not committed").

**Class:** BLOCKER until written (B2); then a **base assumption**. **Consequence:** during the lag a rider is in neither pool, which is slightly pessimistic for Lyft rules (a real dispatcher might still let a van arrive first). **Deferred sensitivity:** a "soft hold" variant where a van can still win until the booking, with abort and ledger rules. Not needed for the pre-registered comparison.

---

## 3. Event ordering at equal timestamps

### 3.1 What exists
Config `simulation.simultaneous_event_order` = `[dropoff, pickup, new_request, patience_check, dispatch_tick]` (`team_config.v2.json`; the `architecture/p3_engine_loop.svg` diagram repeats it). Conventions: arrival ends the patience clock, arrival wins a same-second tie, arrival does not guarantee boarding, and request, curb arrival and boarding are separate events (D-39, D-40).

### 3.2 Is "pickup" arrival or boarding?
[FACT] In the answer keys, `pickup_s` and `pickup_arrival_s` are **curb arrival** times; `wait_s = pickup_arrival_s − t_request_s`; `ride_s = dropoff_s − pickup_s` therefore **includes the 30 s boarding dwell** (e.g. L1 R001: ride 143 s = 30 + T). `dropoff_s` is arrival at the destination; the van is free 30 s later. So in the config order, `pickup` must be read as **curb arrival**; only then does "pickup before patience_check" implement "arrival wins". If it meant boarding completion, a rider could cancel 20 s after the van parked.

**Class:** resolved by the keys, but the prose is ambiguous. **Recommendation:** rename the event `curb_arrival` and add `boarding_done`. Report two waits: `wait_to_curb` (the keys' `wait_s`, which the dispatcher objective also uses) and `wait_to_board` (curb + dwell). D-39 already forbids silently redefining one as the other; `model_design.md` §3.4's "actual pickup time" must say which.

### 3.3 Where the missing events fit
Absent from the config order: no-show expiry, boarding/dwell completion, Lyft booking, Lyft arrival, Lyft drop-off, van shift start/end, the transfer decision, and re-solve.

### 3.4 Proposed complete order (smaller class number runs first; ties inside a class by ascending van id, then request id, then insertion sequence)

| Class | Event | Why here |
|---|---|---|
| 10 | `dropoff_arrive` (van) and `lyft_dropoff` | Terminal completions first; frees seats (config: dropoff) |
| 20 | `curb_arrival` (van) and `lyft_arrival` | Ends the patience clock before any cancellation is evaluated; runs the presence test (config: pickup) |
| 30 | `service_done`: boarding dwell end, drop-off dwell end (van becomes free), `noshow_expiry` (180 s after arrival) | After arrivals; marks vans free but does **not** send them yet (see class 90) |
| 40 | `van_on_duty` / `van_off_duty` | A van that starts at τ must be visible to the epoch at τ |
| 50 | `new_request` | Reveal (config) |
| 60 | `patience_check` | Cancels only if no vehicle has arrived (class 20 already ran). Also beats a same-second Lyft decision and a same-second booking |
| 70 | `lyft_book` (lag expiry) | After patience, so a rider whose deadline equals the lag end cancels with no booking and no fee. A base choice; the opposite order only changes the fee ledger |
| 80 | **epoch** (tick, or any flagged trigger): solve → commit-flag update → Lyft pass (once) → apply transfers → if any transfer, re-solve (no second Lyft pass) | Config: dispatch_tick, last |
| 90 | `departure sweep`: every free van with a non-empty plan departs now (this is the commitment instant) | Lets a van that frees up at τ use the fresh plan from τ's epoch |

Deterministic-clock hygiene: integer seconds everywhere; every travel time goes through one shared lookup function with one rounding rule (the generator's `T()` uses Python `round`, which rounds .5 to even, applied to matrix seconds × multiplier; the simulator must import or replicate that exactly); sorted iteration over vans and requests; priority-queue key `(time, class, id, seq)`.

### 3.5 Epoch rule (merges several documents)
- [FACT] The L4 key defines decision epochs as the **set** of tick times and request arrival times, so two requests at the same second (R007/R008 at 580) give **one** epoch. Adopt: **one epoch per distinct timestamp**, run if a tick is due or any trigger flag was raised by classes 10–70.
- Ticks are anchored at 0 s in service time (L4 epochs start with 0) and continue every 120 s even with nobody waiting; R1 therefore fires at the first epoch ≥ t_r + θ (L4 key), which couples R1's effective timing to incidental event times. Base assumption; it is the same for every compared arm only if event epochs do not depend on the dispatcher. They do (no-shows, cancellations), so R1 timing differs slightly between dispatchers. State it.
- Triggers per `model_design.md` §5: request, cancellation, no-show, transfer, tick. **Additions needed:** van on duty (F-5) and van off duty. A cancellation or `cancel_after_transfer` of a request that is not in any van plan changes nothing and need not trigger a solve.
- Stop arrivals and dwell ends are not triggers (`model_design.md` §3.1), except `noshow_expiry` (D-40).

| ID | Finding | Class | Resolution |
|---|---|---|---|
| F-5 | Van shift start is listed as an event but is not a re-solve trigger. In L4 the vans start at 900 s, which is **not** on the tick grid (840, 960), so nine waiting riders and two idle vans would wait 60 s for the next tick | **BLOCKER (small)** | Make `van_on_duty` a trigger |
| F-6 | Commitment instant not defined. `model_design.md` §3.2 "next stop frozen" could mean "as soon as it is planned" or "at departure" | Resolved here | Commitment = **departure** (class 90). A van in its 30 s dwell can still be re-planned; a van on a leg cannot |
| F-7 | Simultaneous versus sequential Lyft decisions inside one pass: R2/R3 all read the same post-solve ETAs, so several riders can be transferred for one congestion event even though removing the first would have cured the rest | Base assumption | Simultaneous in one pass; one pass per epoch; re-solve after. Sequential-with-re-solve is a **deferred sensitivity** |

---

## 4. Re-planning triggers and solver latency

### 4.1 The contradiction
- `team_config.v2.json` `solver.delay_accounting_rule`: "decisions instantaneous in simulated time; solve time logged; solve > W flagged".
- `model_design.md` §5 Latency rule: "wall-clock safety cap of ≤ Δ/4. If a solve overruns: keep the previous plan, insert new requests greedily, and log it. **Simulated time is not frozen while a solver thinks.**"

These are not the same rule. If decisions are instantaneous, simulated time cannot advance during a solve, so "overrun" has no simulated meaning. Worse, an overrun test on **wall-clock** makes the outcome depend on machine speed and load, which breaks the determinism requirement in `compute_feasibility.md` §5 (identical output hashes, 1 versus 4 workers) and the instruction in §3 to use a node limit as the primary stop.

**Class:** B3, genuine contradiction. **Recommended resolution (one rule):**
1. Decisions take effect at the epoch time τ (zero simulated latency). This is the config rule and is what the answer keys assume.
2. Budgets are **deterministic** only (iterations for T; node limit for HiGHS). When the budget is hit, the incumbent is used and `status`, `gap`, `nodes` are logged. If HiGHS returns no feasible incumbent, fall back to the always-present "committed work only" route plus greedy insertion of new requests, and log `fallback=1`. This replaces the wall-clock rule.
3. Wall time is logged for diagnostics and the "solve > W" flag is a **reporting flag**, never an input to the simulation.
4. Deferred sensitivity: latency as simulated delay (decisions land at τ + δ), which needs plan staleness handling.

### 4.2 Other trigger questions
- **One Lyft pass per epoch** (§3.5, F-7). A re-solve caused by a transfer does not start a new pass; the next pass is the next epoch. Resolved here.
- **Re-solve after transfer:** needed at the decision, because van routes containing the transferred request are stale (R-XFER step 1).
- **Equal-cost plans:** the L1 key breaks ties to V1; hand-check costs are rounded to 6 decimals (`generator_v2._best_van`). The simulator needs a deterministic tie rule in **both** T and the MILP (suggest lexicographic perturbation by van id then request id, or a documented epsilon) or a repeat run can pick a different optimal plan after a solver upgrade. `highspy` is pinned (1.15.1) in the lock file, which helps but does not remove ties.

---

## 5. Interfaces, hidden information, outputs

### 5.1 What each component may observe

| Component | Observes | Must not see |
|---|---|---|
| Van dispatcher | Revealed requests (t_r, o, d, party, status); van position node, next node, arrival time, onboard parties, committed stops, seats, shift end of vans **already on duty**; travel matrix; its own parameters | `patience_s`, `noshow_u`, `consent_u`, `lyft_delay_s`, `lyft_noshow_u` (unused), `eta_noise`, future requests, vans not yet on duty (L4 key: predicted pickup is infinite before 900 s) |
| Lyft rule | Per open request: t_r, party, assignment state, `unassigned_since`, plan ETA P̂_r, board totals; fixed parameters (θ, ℓ, typical Lyft delay 8 min for R3, dispatcher capacity) | Same hidden list. Consent is learned only as the offer outcome ("declined", L4 key) |
| Lyft service model | Decision time, ℓ, the request's `lyft_delay_s`, presence draw, travel matrix × m_L | Van state |

New findings:
- **F-8 [base assumption].** Travel times are deterministic (`stochastic_spec: null`) and the dispatcher uses the same matrix as the world. Plan ETAs are therefore exact except for later re-plans and no-shows. R2 and R3 act on near-perfect predictions, which a real dispatcher does not have. Report it beside any R2/R3 advantage; **deferred sensitivity:** travel-time noise.
- **F-9 [BLOCKER (small)].** Presence leak at the curb. The rider's absence is hidden until the van waits. The dispatcher must plan the van as freed at arrival + 30 s (dwell) and learn of absence only when the rider has not boarded by then; it must never read `noshow_u`. State this in the observation builder spec.
- **F-10 [BLOCKER for L5/L6 availability].** `availability.csv` for L5 ends at 3600 s, the same second the request window closes, while D-36 says vans stay on duty until all work is resolved, and the config says "run until every accepted rider is dropped off". Under the shift-end rule (no new pickups after `avail_end_s`) L5 riders still waiting at 3600 s get no van. L1–L4 have long end times and are unaffected. Decide the rule and make the L6 builder emit it.
- **F-11 [base assumption].** The L4 key gives Lyft a 30 s boarding dwell (`lyft_dropoff = pickup + 30 + T`) and no drop-off dwell. Nothing in the spec or decision log says so. Add `lyft_pickup_dwell_s = 30` as a named assumption.
- **F-12 [BLOCKER (small)].** Machine-readable policy and run configuration does not exist in usable form. `team_config.v2.json` is v2.1 of 1 Oct, status `PILOT_DEFAULTS_NOT_FROZEN`: players are N/A/B/C/H, `windows_s` 30/60/120, `overflow_rule` null, `fallback` "shared_immediate_greedy". It has no tick Δ, lag ℓ, no-show wait (180 s lives as a constant in `generator_v2.py`), Lyft parameters, φ, β, γ, guardrail, p_van or p_lyft. `policy.json` (`scenario_spec.md` §10) is named but not specified. Minimum fix: one versioned `policy.json` schema with every parameter and its decision id, written into every run manifest.

### 5.2 Outputs: specified versus existing

| Output | Specified? | Exists? |
|---|---|---|
| `events.csv`, `outcomes.csv`, `run_manifest.json` | Names only (`scenario_spec.md` §10); no columns | No simulator, so none |
| Scenario inputs, MANIFEST, content hashes | Yes | Yes (`FROZEN_v2.json`, `MANIFEST.json`) |
| Answer-key rows (`handcheck.csv`) | Yes (columns above) | Yes (L1–L4). **Reuse its columns as the first `outcomes.csv` schema** |
| Epoch/decision records, ETA history, van-km, ledger | Metrics named in `model_design.md` §7 and D-44; no schema | No |

Recommended minimum (fields, not a final schema): **events.csv** `seq,t_s,class,event,request_id,van_id,from_state,to_state,detail`; **epochs.csv** `t_s,trigger,n_open,n_candidates,solver,status,gap,nodes,wall_s,fallback,objective,n_transfers`; **lyft_decisions.csv** one row per request evaluated in each pass, with the rule inputs it read (elapsed, `unassigned_since`, P̂_r, board size), the verdict and the consent result (this is what §9.3 "traced nights" needs); **outcomes.csv** the handcheck columns plus `committed_at`, `curb_arrival_s`, `board_s`, `n_reassignments`, `n_eta_moves_gt_60s`, `first_assigned_s`, `mode`; **vans.csv** loaded and empty km, idle time; **lyft_ledger.csv** per D-44 categories; **run_manifest.json** git commit and dirty flag, lock-file hash, scenario content hash, policy hash, seeds, solver version and options.

**F-13 [genuine conflict, small].** `compute_feasibility.md` §1 says not to store per-epoch plans, but ETA churn (a reported metric) and R2/R3 traces need predicted pickups over time. Resolution: store compact `eta_update` rows (request, epoch, P̂ before/after) only when the ETA moves by more than 1 min, plus the P̂ actually used in each Lyft decision, rather than full plans.

---

## 6. Implementation gaps and computational bottlenecks

### 6.1 What exists
[FACT] Scenario generation (L1–L5), travel matrix and hashes, tests for the scenario code (`tests/test_scenario_v2.py`: L1–L3 arithmetic, L4 bookkeeping, L5 design), a locked environment (`requirements-lock.txt`: Python 3.12.3, numpy 2.5.4, pandas 3.0.6, scipy 1.18.1, **highspy 1.15.1**; no numba, no OR-Tools). Note `compute_feasibility.md` §3 and §5 still say "no solver in the venv" and "Python 3.10": stale, the lock file supersedes them.
[FACT] There is **no** simulator, dispatcher, Lyft module, event log, metrics code, or L6/L7 scenario builder. `generator_v2.py` defines level ids 6 and 7 but has no function that builds them; the D-35 largest-remainder hourly counts are not implemented. `P_NOSHOW = 0.047` in the generator is stale (superseded by D-40/D-41) and unused for L1–L4.

### 6.2 Design consequences of using only the 188×188 matrix
- Every drive is one matrix leg between two request locations. A van "mid-edge" has no position the matrix can price. So the committed next stop is the whole leg, and legs can be long (Homewood to Peabody). **Base assumption:** no mid-leg diversion (`model_design.md` §3.2, L3 key). It is stricter than a real dispatcher, which can reroute a van mid-street; it makes vans less responsive than reality.
- **F-14 [deferred sensitivity, spec ambiguity].** The commit-rule variant "ETA ≤ 5 min" (`scenario_spec.md` §4) cannot be built without a mid-leg position model. Its meaning (when is a request locked to a van?) also needs one sentence. Do not promise it until a position model exists.

### 6.3 The `max_new_per_route` problem (B4)
`team_config.v2.json` `solver.max_new_per_route = 2`; `model_design.md` §3.3 says a route "may add at most a few new requests per epoch". But §3.2/§3.3 also put previously assigned, uncommitted requests back in R(τ) at every epoch and let routes pick any subset S_k of R. If "new" means "any request in S_k not already frozen", a van can plan at most 2 pickups ahead of its frozen stop, so with 5 vans at most 10 requests have an assigned van; every other open request is PENDING and has **no ETA**.
- Consequence: R1u (continuously unassigned ≥ 10 min), R2 (predicted pickup) and R3 (predicted pickup versus Lyft) all read assignment and ETA. Under load they would fire because of the planner's truncation, not the rider's real prospects (the L4 key already treats "no van" as infinite ETA). Rule comparisons at L6 would partly measure `max_new_per_route`.
- **Class:** BLOCKER for L6 (not for the first milestone). **Resolution options:** (a) interpret the cap as "at most 2 changes to the existing plan per van per epoch" and keep a persistent plan so every open request keeps a planned slot and ETA; (b) keep the cap for the MILP only and give the Lyft rule a separate cheapest-insertion ETA estimate for requests the MILP left pending, labelled as the dispatcher's tentative ETA. State which one in the spec before any L6 run.

### 6.4 Candidate generation is the bottleneck (not the MILP)
[FACT] Exact arithmetic. For one van whose route already has m non-frozen stops, adding two new requests with pickup before drop-off gives (m+1)(m+2)(m+3)(m+4)/4 orderings, and one new request gives (m+1)(m+2)/2. Unpruned counts for subsets of size ≤ 2 (one van | five vans), R = open requests:

| R | m = 2 | m = 4 | m = 6 |
|---|---|---|---|
| 10 | 4,111 \| 20,555 | 19,051 \| 95,255 | 56,981 \| 284,905 |
| 15 | 9,541 \| 47,705 | 44,326 \| 221,630 | 132,721 \| 663,605 |
| 25 | 27,151 \| 135,755 | 126,376 \| 631,880 | 378,701 \| 1,893,505 |

(m counts stops that new stops can interleave with: onboard drop-offs plus planned stops. These are upper bounds; the docs prescribe keeping "the best few sequences per subset", which needs pruning before or during generation.)

[ESTIMATE] How many open requests at 5 vans? By Little's law, open ≈ arrival rate × mean time open. At 64 requests/h (D-36 first hour) the rate is about 1.07/min; if the mean time open is 10–15 min (April waits ~10–13 min median; unknown in the simulator) that is about 11–16 open on average, more in a burst. `compute_feasibility.md` §2 lists "8–15 open" for 30–60 requests/h; our first hour is above that row's scale, so its "borderline" label should be read as "probably beyond plain enumeration".

[ESTIMATE] Epochs per 3-hour night: ticks are exactly 10,800/120 = 90 [FACT]; event epochs ≈ distinct request seconds (~168) plus cancellations, no-shows, transfers and shift events (outcome-dependent), so roughly 260–450 epochs before the post-21:00 tail. Pure-Python route evaluation (matrix lookups, load and precedence checks, cost with φ) is unmeasured; at an assumed 0.1–0.5 ms per route, 10⁴–10⁵ routes per epoch means seconds to tens of seconds per epoch, i.e. minutes to hours per run before pruning. Treat this as the reason to prune, not as a forecast. The 1,440-run L6 grid (`scenario_spec.md` §9.1) multiplies whatever the per-run time is.

Mitigations to design in, not yet measured: per-van candidate request filter (nearest k by deadhead time); pairwise shareability filter (Santi et al., in `math_literature.md`); build pair routes from the best single-request insertion; numpy arrays indexed by integer location id for the matrix (not pandas dicts in the inner loop); avoid pandas in the event loop.

### 6.5 MILP size
Set partitioning with V + R rows (5 vans, ~15–25 open → ~20–30 equality rows) and one binary per kept route plus R slack binaries. With a few thousand kept columns this is a small MILP [ESTIMATE: the LP relaxation of such structures is usually strong, so solves are likely well under a second, but **nothing has been measured and B2 in `compute_feasibility.md` only covers 2-van instances**]. Real risks are column count, the big-M pending price (numerical range M versus φ values), and tie-breaking, not branching.

### 6.6 What the later benchmark must measure (additions to B1–B5)
1. Distribution of open requests R and of m per van over an actual 5-van run (needs the simulator; synthetic states under-represent bursts).
2. Candidate count and generation wall time per epoch, before and after pruning; share of epochs where the pruning discards the unpruned optimum (check against full enumeration on sampled small states).
3. HiGHS wall time, nodes, status and gap for the **5-van route-selection** MILP versus column count (B2 does not cover this).
4. Frequency with which `max_new_per_route` binds and how many requests are left PENDING per epoch (ties directly to B4).
5. Whole-run wall time and memory for 2 vans/28 requests, 5 vans/64 requests (one hour), 5 vans/168 requests (3 h), then the projected cost of the 1,440-run L6 grid; apply the existing decision rule (`compute_feasibility.md` §6) before launching seeds.
6. Determinism: same run twice, 1 versus 4 workers, identical output hashes.
7. Solver-versus-heuristic gap on identical states (B5), reported with status and gap, never as "optimal" without a closed gap.

---

## 7. Which dispatcher is currently approved?

Exactly as recorded:
- **D-25 (12 Oct, "Team decision (direction)"):** "A TransLoc-like re-planning dispatcher (events + periodic re-plan, reassignment, convex wait penalty) is the fixed baseline. Greedy and small-instance exact solvers are references, not the status quo. **Details are proposals** (`model_design.md`)." It does **not** say heuristic or MILP.
- **D-29 (20 Oct):** accepts the objective (convex piecewise-linear φ with slopes 1/2.5/5/10/20, β = 0.5, γ = 0.1 min/km, elastic guardrail). Objective only; not the solver.
- **Decision log, line after D-32:** "Still proposals: **P-05** (rolling-horizon details: Δ = 120 s, next stop frozen, pending price π_r, latency rule), P-08, P-09 details, **P-11** (HiGHS + lock file)". No later decision (D-33 to D-44) accepts P-05 or P-11.
- `scenario_spec.md` §4 says "Dispatcher: **T, TransLoc-like heuristic (D-25)**" under a heading "Base (decided D-29 unless noted)". The word "heuristic" is therefore **not backed by a decision row**; it comes from the proposal in `model_design.md` §6.1 (T = insertion plus local search; C = same model solved exactly over enumerated candidates, small instances only; H = hindsight, L1 only). `preregistration_v2.md` (DRAFT, unfrozen) also names T.
- `team_config.v2.json` `dispatch.players` (N/A/B/C/H, C = periodic route-selection MILP) is stale and predates D-25.

**Verdict:** approved = a TransLoc-like re-planning dispatcher as the fixed baseline (direction). Not approved: T as an insertion/local-search heuristic, MILP versus heuristic as the engine behind R-comparisons, the 120-s cadence as a decision, the commit rule, the pending price, the latency rule. **Class:** decision gap. It does not block the first milestone (build the shared route model and both solvers), but it blocks freezing the pre-registration: add a decision row (suggested D-45) that names T, its objective (shared with C), Δ, commit rule (R-XFER and §3.4 here), pending price and the latency rule (§4.1), so "the fixed dispatcher" has one definition.

---

## 8. Recommended milestone ladder

### 8.1 Smallest milestone that shows real optimization (M1)
**M0 (prerequisite, days not weeks): the referee.** Event loop with the class order of §3.4, the state machine of §1, integer-second clock, van legs and dwell, cancel, no-show, event log and `outcomes.csv`, and a deliberately trivial dispatcher ("cheapest idle van" using the D-29 cost). Gate: reproduce **L1, L2, L3 to the second** (`pickup_s`, `dropoff_s`, `event_s`, `van_free_s`, outcome) and the accounting identity; same hash on a repeat run. This proves the engine but not optimization (L1–L3 have one open request at a time by design, `scenario_spec.md` §8).

**M1: real dispatcher on overlapping requests, no Lyft.** Scenario: **L4 under R0** (2 vans on duty at 900 s, 14 seats, 16 requests, no cancellations or no-shows).
- Why it is the smallest: [FACT] nine requests (R001–R009, including a party of 3 and a party of 5) are already waiting when the vans arrive, and seven more arrive within the next 300 s, so every epoch is a genuine multi-request decision. It already exists, is tiny (event log of roughly 100 rows, readable end to end), and needs no new generator work.
- Dispatchers on the identical inputs: (G) cheapest-insertion greedy, (T) insertion plus a bounded local search, (C) route-selection over enumerated candidates solved with HiGHS (node limit, deterministic tie rule). Same objective, cadence, commit rule.
- Deliverables: event log, `epochs.csv` (candidates, status, gap, nodes), a per-epoch plan audit (capacity incl. party of 5 needing 5 free seats, precedence, frozen stops, no duplicate service), and a one-page comparison: total passenger-weighted objective and mean/max wait for G, T, C, plus one worked epoch showing why C chose a pooled route G did not.
- Honest limits to state: 2 vans and 16 requests will show small differences; the point is correctness and visible optimization, not a result. Run with `max_new_per_route` set so it does not bind, and again at 2, to expose B4 early.

**M2: Lyft pipeline against the L4 key.** Add the Lyft module and service model (R-XFER). Gate: reproduce all hand-checkable transfers (R1(10): 3, R1u(10): 3, R2(15): 8, R3(2): 8; 22 decisions), decline path, party of 5 as XL, "wait = Lyft pickup − request time", and the four identities in L4 `HANDCHECK.md`.

### 8.2 Growth to the demonstration
| Step | Scenario | New work | Gate |
|---|---|---|---|
| M3 | L5, 30 paired seeds, 2 vans, burst (`data/scenarios/v2/L5/r00…r29`) | Random latent draws, patience cancels, no-show with shared presence draw, metrics pipeline, paired comparison scaffolding | Determinism; identity on all 30 nights; CRN pairing check (R0 vs R1 share every rider) |
| M4 | **L6 builder**: 5 vans constant availability, hourly counts 64/50/54 = 168 (D-35, D-36; largest-remainder rounding), fixed `avail_end` rule (F-10) | The missing generator function and its tests | Counts and hashes frozen; first-hour slice of 64 requests usable alone |
| M5 | 5 vans, **first hour only (64 requests)**, one seed | Candidate pruning, B1/B3 benchmark at this scale | Per-run time known; B4 resolved; decide the T-versus-C role at 5 vans from measured numbers |
| M6 | **Demonstration night: 5 vans, 18:00–21:00, 168 requests, one seed**, R0 and one predictive Lyft rule | Traced-night timeline generator (spec §9.3.7) | Full event log, epoch log, ledger; plan audit clean; one decisive transfer explained |
| M7 | 30 seeds × rules, then patterns and 6th van | Parallel runner (8 workers, `OMP_NUM_THREADS=1`), run manifest | Grid cost projected from M5/M6 before launch |

---

## 9. Consolidated findings table

| ID | Finding | Class | Recommended resolution |
|---|---|---|---|
| B1 | Same-second order incomplete; "pickup" ambiguous (arrival vs boarding); no epoch-merging rule in prose | **BLOCKER** | Adopt §3.4 order and §3.5 epoch rule; rename `curb_arrival`, add `boarding_done` |
| B2 | Transfer commitment point (decision vs booking) unstated; duplicate-service risk; cancel during lag | **BLOCKER** | R-XFER (§2.3): leaves planning at decision; cancel during lag = `cancel_after_transfer`, no booking, no fee; audit invariant |
| B3 | Latency: config (instantaneous) vs `model_design.md` §5 (not frozen, wall-clock cap); wall-clock rule breaks determinism | **BLOCKER (small)** | Zero simulated latency; deterministic budgets only; wall time diagnostic (§4.1) |
| B4 | `max_new_per_route = 2` leaves requests PENDING with no ETA; R1u/R2/R3 would read truncation | **BLOCKER for L6**, not M1 | Persistent plan or separate tentative ETA (§6.3); decide before any L6 run |
| B5 | No L6/L7 builder; no `policy.json` or output schemas; `team_config.v2.json` stale | **BLOCKER for M4/M6** (policy and output schema needed already for M0) | §5.2 minimum schemas; D-45 for dispatcher definition |
| F-5 | `van_on_duty` is not a trigger; L4 vans start off the tick grid | BLOCKER (small) | Make shift start and end triggers |
| F-3, F-10 | Shift-end grace g has no value; L5 `avail_end` = window end conflicts with D-36 | BLOCKER (small) | Set g = 0 for first runs; fix `avail_end` rule in L6 builder |
| F-9 | Dispatcher must not read presence draw; plan van as free at arrival + 30 s | BLOCKER (small, easy) | Observation builder spec |
| F-1 | `lyft_failed` missing from spec terminal lists | Doc sync | Add |
| F-2 | `cancel_pending_van` includes cancels while a van is en route | Resolved (L3 key) | State in spec; log `committed_at` |
| F-6 | Commitment = departure | Resolved here | §3.5 |
| F-7 | Simultaneous Lyft decisions in one pass | Base assumption | One pass per epoch; sequential variant deferred |
| F-8 | Deterministic travel makes R2/R3 predictions unrealistically good | Base assumption + deferred sensitivity | Report beside any R2/R3 result; travel-time noise later |
| F-11 | Lyft 30 s boarding dwell exists only in the L4 key | Base assumption | Name `lyft_pickup_dwell_s = 30` |
| F-12 | Config stale; many parameters have no machine-readable home | BLOCKER (small) | Versioned `policy.json` |
| F-13 | "No per-epoch plans" vs ETA churn and R2/R3 traces | Genuine conflict, small | Compact `eta_update` rows |
| F-14 | Commit variant "ETA ≤ 5 min" needs a mid-leg position model | Deferred sensitivity | Do not promise yet |
| F-15 | Candidate generation unpruned is 10⁴–10⁶ routes per epoch at 5 vans (exact arithmetic); runtime unmeasured | Implementation risk (main bottleneck) | Prune by design; benchmark list §6.6 |
| F-16 | Dispatcher approval: direction only (D-25); algorithm, cadence, commit, latency still proposals | Decision gap | Add a decision row naming T and its definition (§7) |
| F-17 | Tie-breaking in T and MILP (L1 key ties go to V1) | Implementation | Deterministic perturbation; shared cost function; shared `T()` rounding |
| F-18 | `compute_feasibility.md` and `P_NOSHOW` stale (no solver in venv, Python 3.10; 0.047) | Doc sync | Update after the lock file; ignore stale constants |
| F-19 | Dispatcher capacity "k per 10 min": offers or acceptances? R1u "continuously unassigned": does a brief assignment reset it? | Deferred (not in the base: capacity unlimited) | Define before R1u runs at L6: reset on any assignment in any epoch |
