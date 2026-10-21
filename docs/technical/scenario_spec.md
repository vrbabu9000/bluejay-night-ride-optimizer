# Scenario specification v0.3 (21 Oct 2026)

**Built 20 Oct:** L1–L5 are generated in `data/scenarios/v2/` (34 scenarios; hashes in `FROZEN_v2.json`), with hand-check sheets for L1–L4 (`handcheck.csv` + `HANDCHECK.md`). L6–L7 wait for calibration.

**Status:** the specification is **approved by the team** (decisions D-27–D-32, decision log, 20 Oct). v0.3 (21 Oct) adds the corrections in §16:
- Lyft XL for parties of 5 (D-33);
- the dispersed-geography variant (D-34);
- the exact volume formula with hourly rounding (D-35, provisional).

The report-ready reasoning for each scenario-design choice is in the decision log, section "Scenario design trail".
- v0.1 (12 Oct) and v0.2 (20 Oct) are archived in `archive/`.
- It supersedes, for new work, the paused v1 scenario contract and v1 pre-registration. Both are kept unchanged.

---

## 0. In plain words: what a scenario is and how one is made
**A scenario is one simulated night (or evening window) of Night Ride.** It is a list of ride requests: when each comes in, where it starts and ends, and how many riders it carries. Add which vans are on duty and when, plus each rider's hidden traits (how patient they are, whether they'll be at the curb). It is the *same night* replayed for every policy we compare. Only the policy changes, so any difference in results is caused by the policy.

**How long it lasts:**
- **evening window, 18:00–21:00:** the busiest three hours, and the main experiments;
- **full night, 18:00–02:00:** the confirmatory runs;
- small validation levels: 20–60 minutes.

In every case the simulation keeps running after the last request until every rider is resolved (dropped off, cancelled or no-show).

**What happens inside a night (the events):**
1. A request arrives.
2. The van dispatcher re-plans: on that event, and every 2 minutes.
3. A van drives to its next stop and arrives.
4. The rider boards, or after 3 minutes is marked a no-show.
5. Riders are dropped off.
6. A waiting rider runs out of patience and cancels.
7. The Lyft rule moves a waiting rider to Lyft. After the dispatcher's lag a Lyft is called; it arrives, picks up and drops off.
8. Vans go off duty as the night tapers.
9. At 02:00 requests stop, and the backlog is finished.

**How the base scenario is built (once the team says go):**
1. **Fleet:** 5 or 6 vans (14 seats each) on duty at 18:00, tapering through the night in April's shape.
2. **Demand volume:** the number of requests is set so each van faces the same load as April, about **11 requests per van-hour** on average and ~13 at the 6 pm peak.
   - At 5 vans that is ~64 requests in the first hour, ~162 for 18:00–21:00 and ~304 for the night.
   - At 6 vans: ~77, ~195 and ~365.
   - This "load ratio" is then fine-tuned in calibration.
3. **Timing:** requests per hour follow April's hourly shape (highest at 6 pm); within an hour they arrive at random times.
4. **Where:** each request's pickup and drop-off are drawn from the 188 April hotspot points, using the demand model that reproduces April's map totals. **Homewood and Peabody are both included.** Pickups are door-to-door at the snapped curb point, never at a forced stop.
5. **Party size:** 1–4 riders, sometimes 5. A party of 5 can use Lyft through a larger vehicle (Lyft XL) and stays together (D-33).
6. **Hidden rider traits,** drawn once per request: patience, no-show chance, whether they'd accept a Lyft, how long a Lyft would take to arrive.
7. **Save everything** with its fingerprints (seeds, data versions), so the night can be rebuilt byte for byte.

**One base, a few named patterns.** The *recipe* has a base version and a few deliberately stressed versions (§3.4):
- **burst:** a bulk of requests in a short time;
- **far-trip:** more long trips between Homewood and Peabody/downtown;
- **high load:** +30% requests.

Each recipe is turned into **30 different nights** using 30 seed numbers.

**How the random seed works.** A seed is a starting number for the random generator. The same recipe with the same seed always produces exactly the same night. Each ingredient has its **own** random stream: times, places, party sizes, patience, no-shows, Lyft delays. Changing one ingredient never reshuffles the others. When we compare Lyft rules, **every rule gets the identical 30 nights, with identical riders and identical hidden traits**; this is called "common random numbers". The only thing that differs is the rule.

**One Lyft rule at a time (team decision).** For each night we run every Lyft rule separately, with everything else held constant. We then explain *why* the best rule won on that night (§9.3):
- when it transferred riders;
- whom it transferred;
- what that freed up for the riders left on the vans;
- what it cost in Lyft trips.

---

## 1. Three things kept apart
| Kind | Examples | Produced by | Rule |
|---|---|---|---|
| **Scenario inputs** | Request times, origins, destinations, party sizes; vehicle availability; latent rider and Lyft randomness | The scenario generator | Policy-independent; identical for every policy on the same night |
| **Policies** | Van dispatcher, objective settings, cadence and commit rule, **Lyft transfer rule** | A policy config file | The only thing that differs between paired arms |
| **Outcomes** | Actual waits, cancellations, no-shows, transfers, Lyft completions, van-km | The simulator | Never pre-assigned. Latent traits turn into outcomes only through simulated events |

## 2. Scope and geography (decided)
- **Service:** Homewood Night Ride **including the Peabody area** (D-27), as April was operated. East Baltimore is excluded (D-23). Curb-to-curb; both trip ends inside the area.
- **Locations:** the 188 hotspot points (`locations_v1.csv`), used as demand-generation points that stand for nearby addresses, **not stops** (D-24). Vans stop at the snapped road point (`locations_snap_v2.csv`; one documented exception, `p04_b037`, 95 m).
- **Travel:** `tt_locations_v2.csv` (local OSRM v6.0.0; Maryland extract md5 `ff90439c…`; matrix sha256 `b24c0bc6…`), recorded in `MANIFEST.json` (D-31).
  - Van time = matrix seconds × m_v; Lyft time = matrix seconds × m_L. m ∈ [1.0, 1.5], base 1.2 (ASSUMED), calibrated.
- **Units:** integer seconds from 18:00.

## 3. Scenario inputs

### 3.1 Fleet (decided, D-30)
- **5 or 6 vans on duty at 18:00, 14 seats each.** This is the scenario's **fleet level** and can be set per scenario (a factor in §9).
- **Why fewer vans than Hopkins runs.** We study a *scaled* Homewood system: demand is scaled to the fleet so that the load per van matches April (§3.2), rather than simulating ~20+ vans and ~1,700 requests.
- **Taper:** each van gets an availability window. The number on duty follows April's shape, scaled to the 18:00 level:
  - **5-van level:** ≈ 5, 5, 4.5, 3.5, 3, 3, 2, 2 vans through the hours 18:00–01:00;
  - **6-van level:** ≈ 6, 6, 5.5, 4, 3.5, 3.5, 2.5, 2.
  - Fractions are realised by staggered shift ends.
- **Shift end:** no new pickups after the van's end (beyond a grace period); it finishes riders on board. Breaks are deferred.
- **Start position:** the depot (D-17).
- **Known limitation of scaling down:** fewer requests per square mile means fewer pooling chances than the real system. Results are stated "at the scaled system's density". A larger-fleet check is deferred.

### 3.2 Demand volume and timing
- **Load ratio ρ_h = requests per available van in hour h.** It is matched to April **hour by hour** (D-35, provisional):

  ρ_h = (C_h / 30) × (R / C) ÷ V_h

  - C_h = completed rides in clock hour h over 30 days (p09);
  - R / C = 50,297 recorded requests (Completed + Canceled + No-show, with Denied read as 0) ÷ 24,095 completed = 2.087 (p07);
  - V_h = average "All services" vehicles in hour h (p06).

  This gives **ρ = 12.85, 10.10, 10.71** for 18:00, 19:00 and 20:00. ρ is the **calibration knob** for volume (§12).
- **Requests per hour:** N_h = ρ_h × v_h, where v_h is the scenario's vans in hour h. Hourly values are rounded by the **largest-remainder rule**: round the total first, floor each hour, then give the leftover units to the hours with the largest fractions.
  - With April-shaped availability (5, 4.95, 4.46 vans): **64 / 50 / 48 = 162**.
  - With constant 5 vans: **64 / 50 / 54 = 168**.
  - **Constant vs tapering availability is not decided**, so both counts are provisional.
- **Illustrative sensitivity range:** ~145–205 requests for 18:00–21:00. This is **not a confidence interval**: it shows how far the count moves if Homewood had ~22–25 rather than 27.6 vehicles at 6 pm, and if ~10% of recorded requests were rebookings.
- **Hourly shape:** requests are proportional to April's completed-rides-by-hour shape, read as request hour (P-12). ASSUMED: cancellations may concentrate at peaks, tilting the true request profile earlier.
- **Within an hour:** a fixed count per hour, at uniformly random times, which gives clean pairing.

### 3.3 Geography, party size, latent draws
- **O–D pairs:** from the gravity × IPF table (`demand.py`, distance-decay β_geo = 0.1 per minute of drive; D-18) over Homewood + Peabody. β_geo is unrelated to the ride-cost weight β = 0.5 in the objective (§4).
- **Geography representation:** the **reference** places each request at its map-cluster point (188 points). The **dispersed variant** `dispersed_v1` (D-34) spreads the 19 coarse city-view clusters over 6 road satellites each (400 m disk, snapped ≤ 75 m), with the same request times, cluster-level O–D, parties and traits. Files: `locations_dispersed_v1.csv`, `tt_locations_dispersed_v1.csv`, `data/scenarios/v2_dispersed/`.
- **Party size:** P(1, 2, 3, 4, 5) = .73/.18/.055/.025/.01 (sums to 1; mean 1.405, near April's 1.39). The base mean is 1.40, and 1% are parties of 5 (ASSUMED); they need a Lyft XL if transferred (D-33).
- **Latent per-request draws** (seeded, policy-independent; ASSUMED until calibration):

| Draw | Distribution | Used when |
|---|---|---|
| `patience_s` | Rising abandonment hazard (Weibull, shape > 1); scale calibrated so rider cancellations ≈ 2/3 of "Canceled" | The rider is still unpicked when it runs out (with the van or after a transfer) |
| `noshow_u` | U(0,1) < 0.047 → no-show | A van arrives |
| `consent_u` | U(0,1) < p_c (base 1.0) → accepts Lyft | A transfer is decided |
| `lyft_delay_s` | Lognormal, median 8 min, P90 ~15 min; scarcity variant. Used for standard and XL alike in the base (ASSUMED; an XL-specific delay is a sensitivity variant) | A transfer is placed |
| `lyft_noshow_u` | U(0,1) < 0.047 | The Lyft arrives |
| `eta_noise` | Multiplier on the displayed ETA (variant) | Patience-depends-on-ETA variant only |

All draws are made for every request, used or not.

### 3.4 Demand patterns (the named variants of the recipe)
| Pattern | What changes | Why it matters for Lyft rules |
|---|---|---|
| **Base** | §3.2–3.3 as stated | Reference |
| **Burst** ("bulk requests") | 40% of the 18:00–19:00 requests fall inside one 10-minute block (the same block for all seeds, e.g. 18:20–18:30) | A sudden queue: do rules that act early beat rules that wait? |
| **Far-trip** | The probability of trips with an end in the Peabody/downtown zones is doubled (re-normalised); everything else is unchanged | Long, isolated trips tie up vans, and are the natural Lyft candidates |
| **High load** | ρ × 1.3 | Sustained overload: the cost side of transferring |

Patterns change only demand. Fleet, policies and latent-draw *rules* are untouched. Demand streams are re-drawn by design for each pattern, and the 30 seeds are shared across patterns.

## 4. Policies (configuration, not data)
| Setting | Base (decided D-29 unless noted) | Variants |
|---|---|---|
| Dispatcher | **T**, TransLoc-like heuristic (D-25) | T− (no reassignment / 300 s), G greedy; C and H on L1–L4 |
| Cadence Δ | 120 s + events | 60 / 300 s (sensitivity) |
| Commit rule | Next stop frozen; at the curb | ETA ≤ 5 min |
| Wait penalty φ | Piecewise linear, slopes 1/2.5/5/10/20 per min, breaks at 5/10/15/20 | Gentler / steeper |
| Ride weight β; distance γ | 0.5; 0.1 min/km | β 0.25 / 1; lexicographic |
| Ride guardrail | max(25 min, 2·direct + 5 min), elastic | 20 hard / 35 |
| Targets | 15 min pickup, 20 min ride, busy-time 20 min: **reporting thresholds** | Also report at 10 min |
| **Lyft rule** | **The factor under study** (§6) | — |
| Dispatcher lag ℓ | 2 min | 0 / 5 |
| Dispatcher capacity | Unlimited | 3 per 10 min |

## 5. Outcomes (simulator output; schema in §10)
**Terminal states,** exactly one per request:
- `van_completed`;
- `lyft_completed`;
- `cancel_pending_van`;
- `cancel_after_transfer`;
- `noshow_van`;
- `noshow_lyft`;
- `unresolved_close` (must be 0).

**Rules that apply to every rule and mode:**
- A transfer is an event, not a completion.
- **Wait = actual pickup (either mode) − request time.**
- For calibration only, a dashboard view is derived: "Completed" = van-completed; "Canceled" = rider cancellations + transfers (variant without transfers).

## 6. Lyft transfer rules (all kept, run one at a time; D-28)
**Common to all rules:**
- eligibility: still pending (not onboard, not committed). Parties of 1–4 go by **standard Lyft**, parties of 5 by **Lyft XL**, kept together (D-33). XL trips are counted separately in the resource measures; XL availability, delay and cost are unknown, so no surcharge or extra wait is assumed in the base;
- consent;
- dispatcher lag ℓ;
- Lyft pickup = decision + ℓ + `lyft_delay_s`;
- the rider's patience keeps running.

The rule is evaluated after every dispatcher solve, at time τ.

| Rule | Fires when | Clock origin | Information |
|---|---|---|---|
| **R0 Never** | — | — | — (reference, not the status quo) |
| **R1(θ) Elapsed wait** | τ − t_r ≥ θ; θ ∈ {10, 15} | Request time | Request time |
| **R1u(10) Elapsed unassigned** | Continuously without an assigned van ≥ 10 min | When it became unassigned | Assignment status |
| **R2(15) Predicted total wait** | Plan's predicted pickup − request time > 15 min | Request time (looks forward) | Plan ETAs |
| **R3(2) Van vs Lyft** | Predicted van pickup > τ + ℓ + 8 min + 2 min | Now | Plan ETAs, typical Lyft delay, lag |
| **R4 Congestion-gated** (optional) | R2 or R3 only when pending ÷ available vans > κ | — | Board totals |

R1 always lets the rider wait θ first. R2 can transfer at minute 1. Both count waiting from the original request.

## 7. Fair comparison rules
1. **Paired nights:** every rule runs on the identical scenario file.
2. **One factor at a time:** when comparing Lyft rules, the dispatcher, objective, cadence, commit rule, fleet and pattern are held fixed.
3. **Common random numbers:** latent draws are per request, from named streams.
4. **No post-hoc tuning:** thresholds are fixed in pre-registration v2 before any comparison run.
5. **Frontiers,** not single winners: rider outcome vs Lyft trips (and van-km).

## 8. The level ladder (reminder: L1–L4 check correctness; L5 is a dress rehearsal; L6–L7 answer the question)
| Level | Size and length | Adds | Purpose | Lyft? |
|---|---|---|---|---|
| **L1** | 2 vans, 16 requests, ~150 min (built 20 Oct): each request arrives only when **both vans are idle**, so one request is open at a time | Re-planning dispatcher; fixed travel times; no cancellations, no-shows or Lyft | **Checked by hand:** every pickup and drop-off time computed in a spreadsheet and by the exact solver | No |
| **L2** | Same 16 requests | 2 designated no-shows | The 3-min curb wait, no-show handling, re-plan, accounting | No |
| **L3** | Same 16 requests | Designated patience values so 2–3 riders cancel | The cancel-while-waiting path | No |
| **L4** | 2 vans, 16 requests packed into ~20 min; **vans come on duty at 18:15**, so every rule's earlier decisions are traceable by hand | Lyft rules R0/R1/R2/R3 with a fixed lag and Lyft delay; one party of 5 | **Lyft bookkeeping, checked by hand:** the clock is not reset, transfer ≠ completion, eligibility, consent | Mechanics |
| **L5** | 2 vans, 28 requests in 60 min, ≥ 40% in a burst at 18:20–18:30 (built 20 Oct) | Random latent draws, lag, 30 paired seeds | **Dress rehearsal** of the pipeline (pairing, metrics, explanations); too small for conclusions | Pilot |
| **L6** | 5–6 vans, 18:00–21:00 (~160–200 requests) | Everything; base + 3 patterns | **Main Lyft-rule experiments** | **Yes** |
| **L7** | 5–6 vans, 18:00–02:00 + backlog (~300–365 requests) | Everything, with the night's taper and shift ends | **Confirmatory** | **Yes** |

**Expected results, stated in advance:**
- L1–L4 should show ~no algorithm differences, because the load is low.
- Conclusions come only from L6–L7.

## 9. Experiment design
### 9.1 Primary (L6)
**One Lyft rule at a time** within each condition:
- **Lyft rule (6):** R0, R1(10), R1(15), R1u(10), R2(15), R3(2);
- **pattern (4):** base, burst, far-trip, high load;
- **fleet level (2):** 5, 6 vans.

That is 6 × 4 × 2 = **48 cells × 30 paired nights = 1,440 three-hour runs.** The runtime must be measured by benchmark B3 before launch.

### 9.2 Confirmatory (L7) and robustness
- **Confirmatory (L7):** 6 rules × base pattern × {5, 6} vans × 30 nights = 360 full nights.
- **Robustness (L6, base pattern, 5 vans, rules R0/R1(15)/R2(15)/R3, one factor at a time, 30 nights each):**
  - dispatcher T / T− / G;
  - Lyft delay median 5 / 8 / 12 min, plus scarcity;
  - lag 0 / 2 / 5;
  - consent 1.0 / 0.8;
  - dispatcher capacity;
  - patience low / mid / high (from the identified set);
  - objective wait-heavy / base / ride-heavy;
  - travel multiplier 1.0 / 1.2 / 1.5.

### 9.3 Explaining why a rule won (per condition)
For each condition, the best rule is the best point on the frontier, relative to R0 and the others. **Explanation metrics, all paired on the same nights:**
1. **Transfer timing:** minutes from request to the transfer decision; how many were transferred, and at which minute of the night.
2. **Who was transferred:** party size, trip length, zone (Homewood vs Peabody), and the van ETA they were spared.
3. **Wait split:** the wait of transferred riders (their own Lyft delay included) vs riders who stayed on vans.
4. **Spill-over:** how much the riders who stayed with the vans gained, because transfers freed van time (wait and cancellation change for non-transferred riders vs R0).
5. **Cancellations avoided** and no-shows (van vs Lyft).
6. **Cost:** Lyft trips and Lyft km per minute of P90-wait reduction; van-km and empty km.
7. **Traced nights:** for 2–3 representative nights, an event timeline of the decisive transfers (e.g. "at 18:24 R2 moved 6 riders whose predicted wait was 22 min; the vans then reached the 18:25–18:35 burst 7 min earlier").

## 10. File schemas (generated only on go-ahead)
`data/scenarios/v2/<level>/<pattern>_<fleet>/r<NN>/`:
| File | Contents | Units |
|---|---|---|
| `requests.csv` | request_id, t_request_s, o_loc, d_loc, o_zone, d_zone, party, direct_s | s |
| `latent.csv` | request_id, patience_s, noshow_u, consent_u, lyft_delay_s, lyft_noshow_u, eta_noise | s / unitless |
| `availability.csv` | van_id, start_loc, capacity, avail_start_s, avail_end_s | s, seats |
| `scenario.json` | level, pattern, fleet level, all params with evidence labels, seeds (master + named spawn keys), `MANIFEST.json` hash, generator version, content hash | — |
| `policy.json` (per arm) | Dispatcher, objective, cadence, commit, Lyft rule + parameters | — |
| Phase 4 outputs | `events.csv`, `outcomes.csv`, `run_manifest.json` | s |

## 11. Seeds
- `SeedSequence(master_seed, spawn_key=(level_id, pattern_id, replicate, component_id))`.
- **Named components:** count, times, od, party, availability, patience, noshow, consent, lyft_delay, lyft_noshow, eta_noise, solver.
- **Not in the key:** the fleet level, the Lyft rule and the dispatcher. So 5- and 6-van runs and every rule see the same riders; the 6-van case simply has more requests, drawn as an extension of the same streams.
- **Patterns differ by design** but share replicate numbers.

## 12. Validation and calibration
**Validation:**
- L1 hand schedule exact to the second;
- the accounting identity;
- plan audits (capacity, precedence, commitments, shift ends, guardrail violations logged);
- determinism (same inputs → same output hash; 1 vs 4 workers);
- L4 hand check that a transferred rider's wait equals Lyft pickup − request time.

**Calibration (L7, base pattern, before any comparison):**
- **Bands:**
  - completed share of requests ≈ 48%;
  - "Canceled" ≈ 47% pooled (31–68% by day);
  - Lyft rider share ≈ 24.5% (10–46%);
  - no-show ≈ 4.7%;
  - completed-ride wait median ~10–13 min and P90 ~17–21 min;
  - ride P90 ~24 min;
  - completed rides per van-hour ≈ 5.1 (6.2 at 6 pm).
- **Knobs:** load ratio ρ, patience scale, travel multiplier, and the "status-quo" rule threshold.
- **Limits:**
  - survivor-biased waits;
  - correlational cancellation link;
  - mixed-service vehicle counts;
  - no hourly Lyft data;
  - scaled-down density.

  **Keep the identified set** (all knob settings that pass), not one point.

## 13. Pre-registration
`preregistration_v2.md` (draft, written from this spec) fixes the rules, thresholds, metrics, hypotheses and seeds before any comparison run.

## 14. Decisions (all settled 20 Oct)
| ID | Decision | Outcome |
|---|---|---|
| D-A | Boundary | Homewood + Peabody (D-27) |
| D-B | Scope and question | Accepted (D-23–D-26) |
| D-C | Travel matrix v2 + MANIFEST | Accepted (D-31) |
| D-D | Objective | Accepted (D-29) |
| D-E | Lyft rules | All kept; run one at a time (D-28) |
| D-F | Fleet | 5–6 vans, 14 seats, a per-scenario factor; demand scaled to the fleet (D-30) |
| D-G | Ladder L1–L7 | Accepted (D-32) |

## 15. Changes from v0.1
| v0.1 | v0.2 | Why |
|---|---|---|
| Fleet as a calibrated fraction f ∈ [0.65, 1.0] of ~27.6 vans | **5–6 vans, 14 seats**, demand scaled to April's load per van; ρ is the calibration knob | Team decision: size the problem to what we solve |
| Demand 1,680 requests per night | ~160–200 (18:00–21:00) / ~300–365 (night) | Proportional to the fleet |
| Patterns: base / high / burst | Base / **burst / far-trip** / high | Team question about bulk and far-away requests |
| Primary matrix 36 cells | 48 cells (4 patterns × 2 fleet levels × 6 rules) | As above |
| No explanation metrics | §9.3 explanation metrics and traced nights | Team wants to explain why a rule won |
| Boundary open | Homewood + Peabody | D-27 |

## 16. Changes from v0.2 (21 Oct 2026)
| v0.2 | v0.3 | Why |
|---|---|---|
| A party of 5 cannot use Lyft (from the 2018 rule "5+ riders always get a van", which referred to standard 4-seat Lyft cars) | Parties of 5 are Lyft-eligible via Lyft XL, kept together; XL counted separately | D-33: user-supplied operational correction, accepted as a modelling instruction (not independently verified Hopkins policy) |
| Load ratio "~11 on average" | Hour-by-hour formula ρ_h × v_h, largest-remainder rounding; 162 (taper) / 168 (constant), both provisional | D-35: makes the count follow whatever availability is chosen, and avoids using the night average |
| Point-based geography only | Reference kept; dispersed variant `dispersed_v1` added | D-34: coarse city clusters stacked many requests on one spot |
| "Scenario data are not generated yet" | Removed (L1–L5 were generated on 20 Oct) | Stale line |
