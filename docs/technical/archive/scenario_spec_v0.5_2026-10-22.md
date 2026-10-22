# Scenario specification v0.5 (22 Oct 2026)

**Built 20 Oct:** L1–L5 are generated in `data/scenarios/v2/` (34 scenarios; hashes in `FROZEN_v2.json`), with hand-check sheets for L1–L4 (`handcheck.csv` + `HANDCHECK.md`). L6–L7 wait for calibration.

**Status:** the specification is **approved by the team** (decisions D-27–D-32, decision log, 20 Oct). v0.3 (21 Oct) adds the corrections in §16:
- Lyft XL for parties of 5 (D-33);
- the dispersed-geography variant (D-34);
- the exact volume formula with hourly rounding (D-35, provisional).

v0.4 (21 Oct, documentation consolidation; §18):
- financial modelling removed (D-45);
- **simulator build rules added as §17** (D-46–D-48);
- stale counts, pairing and evidence wording corrected (D-49).

v0.5 (22 Oct): reconciled with D-51 (C provisionally held fixed) and D-52 (M0–M1 implementation); §17 gains the conventions the implementation needed (§17.9); stale or ambiguous items found while writing the explanatory PDF are corrected (§19).

**Authoritative documents for implementation:**
- **this file is the build contract** (inputs, states, events, outcomes, §17);
- `model_design.md` gives the mathematics, as corrected by D-47;
- `scenario_methodology.md` explains *why* each design choice was made;
- where they disagree, the decision log wins, then this file.

The report-ready reasoning for each scenario-design choice is in the decision log, section "Scenario design trail".
- v0.1 (12 Oct), v0.2 (20 Oct), v0.3 and v0.4 (21 Oct) are archived in `archive/`.
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
8. Vans go off duty as the night tapers (later cases only; the first demonstration keeps all five vans on duty, D-36).
9. Requests stop at the end of the window (21:00 for the evening window, 02:00 for the full night), and the backlog is finished.

**How the base scenario is built (once the team says go):**
1. **Fleet:** 5 vans (14 seats each), on duty from 18:00 to 21:00 and then until the backlog is finished (D-36). A sixth van and April-shaped tapering are later cases.
2. **Demand volume:** the number of requests is set so each van faces the same load as April, about **11 requests per van-hour** on average and ~13 at the 6 pm peak.
   - With 5 vans on duty for all three hours: **64 / 50 / 54 = 168 requests** for 18:00–21:00 (D-36). This is a **derived, provisional workload**, not measured April demand.
   - The sixth-van comparison uses the **same** 168 requests (D-37). Full-night counts are not derived yet.
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
- how many Lyft bookings (standard and XL) it used. No money is modelled (D-45).

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
- **Shift end:** the exact rule is **open** (§17.6); it matters only for tapering cases (L7) and is not implemented. Riders on board are always finished. Breaks are deferred.
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
  - ~~Constant vs tapering availability is not decided~~ **Decided 21 Oct (D-36):** the first demonstration uses **constant five vans, 64 / 50 / 54 = 168** (provisional; a derived workload, not measured April demand). Tapering (162) is a later case.
  - **Sixth van (D-37):** the benefit of one more van is measured on the **same** requests. Scaling demand with the fleet is a separate experiment.
- **Illustrative sensitivity range:** ~150–260 requests for 18:00–21:00 (D-49, replacing "~145–205"). This is **not a confidence interval**. If Homewood had 20–35% fewer vehicles than the "All services" count, the load per van, and so the count, would rise to ≈ 210–260; if ~10% of recorded requests were rebookings it would fall to ≈ 150.
- **29 days, not 30:** the vehicle chart averages over 29 days, so ρ moves by about ±3% depending on how the missing day is treated (D-49).
- **Hourly shape:** requests are proportional to April's completed-rides-by-hour shape, read as request hour (P-12). ASSUMED: cancellations may concentrate at peaks, tilting the true request profile earlier.
- **Within an hour:** a fixed count per hour, at uniformly random times, which gives clean pairing.

### 3.3 Geography, party size, latent draws
- **O–D pairs:** from the gravity × IPF table (`demand.py`, distance-decay β_geo = 0.1 per minute of drive; D-18) over Homewood + Peabody. β_geo is unrelated to the ride-cost weight β = 0.5 in the objective (§4).
- **Geography representation:** the **reference** places each request at its map-cluster point (188 points). The **dispersed variant** `dispersed_v1` (D-34) spreads the 19 coarse city-view clusters over 6 road satellites each (400 m disk, snapped ≤ 75 m), with the same request times, cluster-level O–D, parties and traits. Files: `locations_dispersed_v1.csv`, `tt_locations_dispersed_v1.csv`, `data/scenarios/v2_dispersed/`.
- **Party size:** P(1, 2, 3, 4, 5) = .73/.18/.055/.025/.01 (sums to 1; mean 1.405). This is an **assumed** distribution chosen near April's **derived** 1.386 passengers per completed booking; the two are different quantities. The average-April shape is the base (D-38); a weekend shape (mean 1.49) is a sensitivity case. The base mean is 1.40, and 1% are parties of 5 (ASSUMED); they are **potential** XL demand: only those actually transferred need a Lyft XL (D-33). A van can take a party of five only when five seats are free.
- **Latent per-request draws** (seeded, policy-independent; ASSUMED until calibration):

| Draw | Distribution | Used when |
|---|---|---|
| `patience_s` | Personal deadline (D-39): Weibull, shape 1.5, median 18 min, a labelled placeholder. Scale calibrated later so rider cancellations fall within a **provisional 50–75%** of the dashboard "Canceled" share (a sensitivity range, not an interval established by the data) | The rider is still unpicked when it runs out (with the van or after a transfer) |
| `noshow_u` | **Shared presence draw** U_r (D-41, simplified by D-48): absent iff U_r < p at the first vehicle arrival. **One p for every mode** (van, standard Lyft, XL), **conditional on arrival** and provisional: ≈ 8.9% under the dashboard status mapping (D-48), not the 4.7%-of-all-requests share. **Errata:** the frozen `scenario.json` label "DERIVED rate 4.7%" and the `p_noshow: 0.047` params are all-request shares; the simulator must not read them | An active vehicle (van or Lyft) reaches the curb |
| `consent_u` | U(0,1) < p_c (base 1.0) → accepts Lyft | A transfer is decided |
| `lyft_delay_s` | Lognormal, median 8 min, P90 ~15 min; scarcity variant. Used for standard and XL alike in the base (ASSUMED; an XL-specific delay is a sensitivity variant) | A transfer is placed |
| `lyft_noshow_u` | Generated in the frozen L1–L5 inputs but **unused** under the shared-presence convention (D-41); kept for compatibility | — |
| `eta_noise` | Multiplier on the displayed ETA (variant) | Patience-depends-on-ETA variant only |

All draws are made for every request, used or not.

### 3.4 Demand patterns (the named variants of the recipe)
| Pattern | What changes | Why it matters for Lyft rules |
|---|---|---|
| **Base** | §3.2–3.3 as stated | Reference |
| **Burst** ("bulk requests") | 40% of the 18:00–19:00 requests fall inside one 10-minute block (the same block for all seeds, e.g. 18:20–18:30) | A sudden queue: do rules that act early beat rules that wait? |
| **Far-trip** | The probability of trips with an end in the Peabody/downtown zones is doubled (re-normalised); everything else is unchanged | Long, isolated trips tie up vans, and are the natural Lyft candidates |
| **High load** | ρ × 1.3 | Sustained overload: the resource side of transferring |

Patterns change only demand. Fleet, policies and latent-draw *rules* are untouched. Each pattern has its own demand streams (the pattern is in the seed key), so replicate numbers are shared but the nights are **different**: comparisons **between** patterns are **not paired** (D-49). Rule comparisons **within** a pattern are paired.

## 4. Policies (configuration, not data)
| Setting | Base (decided D-29 unless noted) | Variants |
|---|---|---|
| Dispatcher | **C**, restricted route-selection MILP (HiGHS) with the candidate rule of D-52: **provisionally selected** (D-51), conditional on the M5 benchmark; not a reproduction of Hopkins' dispatcher | T (insertion + local search) as a later robustness variant or development contingency, **never a runtime fallback**; G greedy; H on L1 only |
| Cadence Δ | 120 s + events | 60 / 300 s (sensitivity) |
| Commit rule | Next stop frozen; at the curb | ETA ≤ 5 min |
| Wait penalty φ | Piecewise linear, slopes 1/2.5/5/10/20 per min, breaks at 5/10/15/20 | Gentler / steeper |
| Ride weight β; distance γ | 0.5; 0.1 min/km | β 0.25 / 1; lexicographic |
| Ride guardrail | max(25 min, 2·direct + 5 min); no candidate may create or increase a violation; an unavoidable one is logged and penalised by Ψ (D-47) | 20 hard / 35 |
| Targets | 15 min pickup, 20 min ride, busy-time 20 min: **reporting thresholds**, taken from the page wording captured around April 2026 (not proof of operating policy). The live page read on 21 Oct 2026 states 20 / 25 / 25; kept distinct (D-49) | Also report at 10 and 20 min |
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
- `lyft_failed` (sensitivity only; base probability f = 0, D-43);
- `unresolved_close` (must be 0).

**Rules that apply to every rule and mode:**
- A transfer is an event, not a completion.
- **Wait = actual pickup (either mode) − request time.**
- For calibration only, a dashboard view is derived: "Completed" = van-completed; "Canceled" = rider cancellations + transfers (variant without transfers).

## 6. Lyft transfer rules (all kept, run one at a time; D-28)
**Common to all rules:**
- eligibility: still pending (not onboard, not committed). Parties of 1–4 go by **standard Lyft**, parties of 5 by **Lyft XL**, kept together (D-33). XL bookings are counted separately in the resource measures; XL availability and delay are unknown, so no extra wait is assumed in the base, and no prices are modelled (D-45);
- consent (base p_c = 1: a decision is a booking request; there is no separate offer stage, D-45);
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
5. **Frontiers,** not single winners: rider outcome vs Lyft bookings (and van-km).

## 8. The level ladder (reminder: L1–L4 check correctness; L5 is a dress rehearsal; L6–L7 answer the question)
| Level | Size and length | Adds | Purpose | Lyft? |
|---|---|---|---|---|
| **L1** | 2 vans, 16 requests, ~150 min (built 20 Oct): each request arrives only when **both vans are idle**, so one request is open at a time | Re-planning dispatcher; fixed travel times; no cancellations, no-shows or Lyft | **Checked by hand:** every pickup and drop-off time computed in a spreadsheet and by the exact solver | No |
| **L2** | Same 16 requests | 2 designated no-shows | The 3-min curb wait, no-show handling, re-plan, accounting | No |
| **L3** | Same 16 requests | Designated patience values so 2–3 riders cancel | The cancel-while-waiting path | No |
| **L4** | 2 vans, 16 requests packed into ~20 min; **vans come on duty at 18:15**, so every rule's earlier decisions are traceable by hand | Lyft rules R0, R1(10), R1(15), R1u(10), R2(15), R3(2) with a fixed lag and Lyft delay; one party of 5 | **Lyft bookkeeping, checked by hand:** the clock is not reset, transfer ≠ completion, eligibility, consent | Mechanics |
| **L5** | 2 vans, 28 requests in 60 min, ≥ 40% in a burst at 18:20–18:30 (built 20 Oct) | Random latent draws, lag, 30 paired seeds | **Dress rehearsal** of the pipeline (pairing, metrics, explanations); too small for conclusions | Pilot |
| **L6** | 5 vans constant, 18:00–21:00 + backlog (168 requests, D-36); sixth van on the same requests (D-37) | Everything; base + 3 patterns | **Main Lyft-rule experiments** | **Yes** |
| **L7** | 5–6 vans, 18:00–02:00 + backlog (counts not yet derived) | Everything, with the night's taper and shift ends | **Confirmatory** | **Yes** |

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
  - dispatcher C (base) vs T, if T is built, and G (robustness of the ranking; D-51);
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
6. **Resource use:** Lyft bookings and completed Lyft trips (standard and XL separately), Lyft km, van-km and empty km, reported beside the rider-outcome change. No money is modelled (D-45).
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
- **Named components:** count, times, od, party, availability, patience, noshow, consent, lyft_delay, lyft_noshow, eta_noise, solver, spread (12; dispersed variant only). The site layout uses key (0, 0, 0, 13).
- **Not in the key:** the fleet level, the Lyft rule and the dispatcher. So 5- and 6-van runs and every rule see the same riders; the 6-van case simply has more requests, drawn as an extension of the same streams. *[Superseded 21 Oct by D-37: for measuring the benefit of a sixth van, the requests are held fixed; this constant-workload extension is kept for a separate, later experiment.]*
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
  - no-show ≈ 4.7% **of all requests** (≈ 8.9% per van arrival under the status mapping; D-48);
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
| Demand 1,680 requests per night | ~160–200 (18:00–21:00) / ~300–365 (night) *[superseded: 168 at constant 5 vans, D-36]* | Proportional to the fleet |
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

## 17. Simulator build rules (build contract; D-46–D-48, D-52; implemented for L1–L4 in Phase 4 M0–M1, 22 Oct)
These rules are what the Phase 4 simulator must implement. They are written so that two people building it independently would produce the same event log for the same inputs.

### 17.1 Time and travel
- **Clock:** integer seconds from 18:00. Every event time is an integer.
- **Travel:** one base table t₀(i,j), the matrix seconds. Van time = t₀ × m_v, Lyft ride time = t₀ × m_L, each multiplier applied **exactly once**, then rounded to whole seconds with the **same rule as the generator** (Python `round`, half-to-even, `generator_v2.T()`), so the L1–L4 answer keys reproduce exactly (D-47). `direct_s` in `requests.csv` is t₀ and is used only for reporting; the ride guardrail uses t₀(o,d) × m_v.
- **Base values:** m_v = m_L = 1.2 (ASSUMED; calibrated). L1–L4 answer keys use m = 1.0 as written in their `scenario.json`.

### 17.2 Request states
`pending_van` → (`committed` → `onboard` → `van_completed`) or `noshow_van` or `cancel_pending_van`, or → `xfer_hold` (transfer decided, booking lag running) → `lyft_booked` → `lyft_completed` / `noshow_lyft` / `cancel_after_transfer` / `lyft_failed`.
- **Committed:** a van has departed toward the rider's pickup. Commitment happens at **departure** (D-46).
- **Audit invariant:** no request is ever in a van route **and** in a Lyft state at the same time.

### 17.3 Same-second event order (D-46)
When several events share a second, they run in this class order:

| Order | Class | Notes |
|---|---|---|
| 10 | Drop-offs (van and Lyft) | Frees seats first |
| 20 | Curb arrivals (van and Lyft) | **Ends the patience clock** (arrival wins a same-second tie with the deadline); the presence test is made here |
| 30 | Service ends | Boarding dwell ends; no-show expiry after the 180-s curb wait |
| 40 | Van on duty / off duty | |
| 50 | New requests | |
| 60 | Patience checks | A rider still `pending_van`, `committed` (van driving to the curb, not yet arrived), `xfer_hold` or `lyft_booked` whose deadline has passed cancels |
| 70 | Lyft bookings | `xfer_hold` → `lyft_booked` at decision + ℓ |
| 80 | **Epoch** | Van solve → evaluate the Lyft rule once → apply transfers → re-solve once if any transfer |
| 90 | Departures | Vans leave toward their next stop; commitment |

Ties inside a class are broken by request ID, then van ID.

### 17.4 Epochs and solver timing
- **One epoch per distinct second** that has a trigger. Triggers: a new request, a cancellation or no-show **of a request in van planning**, a transfer (handled inside the epoch by the re-solve), a van going on or off duty, and the 120-s tick anchored at t = 0. Lyft-side events (booking, Lyft arrival, Lyft no-show, Lyft drop-off) do not trigger an epoch, because they cannot change a van plan (D-52).
- **Zero simulated latency.** A plan computed at τ takes effect at τ. The solver is limited by deterministic node or iteration budgets; wall time is logged as a diagnostic and never changes a plan (D-46).
- **Pending requests** (served by no route in the current plan) keep a **tentative ETA**: the cheapest feasible insertion, computed outside the solver. Lyft rules that read ETAs read this value; the log records why the request is pending (competition or candidate cap) (D-47).

### 17.5 Transfers and the Lyft service (D-43, D-45, D-46)
- **Consent.** In the base p_c = 1, so every decision is a booking request and there is no offer stage. Where p_c < 1 (L4 uses 0.9; the consent sensitivity uses 0.8), a rule's decision is an **offer**: a rider with `consent_u` > p_c declines, stays with the vans, is never offered again, and the decline is counted (D-45).
- A (consented) transfer decision at τ removes the request from van planning **at τ**, atomically, and puts it in `xfer_hold`.
- At τ + ℓ the booking is placed (`lyft_booked`). If the rider's deadline falls inside the lag, the result is `cancel_after_transfer` and **no booking** is counted.
- Lyft arrival = booking + `lyft_delay_s`. Presence uses the same draw U_r and the same p as for the van (D-48). Present → boarding dwell s = 30 s (the same as for vans, as in the L4 answer key) → direct ride of t₀(o,d) × m_L → `lyft_completed` at drop-off. Absent → `noshow_lyft` after the 180-s wait.
- Parties of 1–4 book standard Lyft, parties of 5 book XL. Every count is kept separately for standard and XL.
- **Pickup instant (both modes):** pickup time = the curb arrival of the vehicle the rider boards; the 30-s boarding dwell follows. So wait W = curb arrival − request time and ride H = drop-off arrival − curb arrival (H includes the boarding dwell). This is the convention of the L1–L4 answer keys. For riders who do not board, the curb arrival is still recorded separately (`curb_arrival_s`), and no wait-to-pickup is reported for them.
- No automatic rebooking after a Lyft no-show or failure (simplification, D-43).

### 17.6 Shifts and closing
- **Closing rule:** after the arrival window, vans stay on duty until every accepted request is resolved (D-36). For L5 the frozen `avail_end_s` = 3600 is read as the end of the arrival window, not a shift end.
- **Shift-end rule (open; L7 only; not implemented):** g = 0. The documents differ on whether a new pickup must *start* before the van's end (this section, v0.4) or its *drop-off* must end before it (`model_design.md` §3.3). To be settled before L7 is built. Riders already on board are always finished.
- `unresolved_close` must be 0 at the end of every run.

### 17.7 Inputs the simulator must not read
- `p_noshow` in `scenario.json` params and the "DERIVED rate 4.7%" label (errata, D-48); p comes from the behaviour configuration.
- `lyft_noshow_u` (unused, D-41).
- `eta_noise` except in the ETA-dependent patience variant.

### 17.8 Required logs
- **Event log:** every event with time, class, request, van, old and new state.
- **Epoch log:** trigger, open requests, candidates per van, solver status and gap, the chosen plan, pending requests with their reason and tentative ETA, and Lyft rule decisions with the quantity the rule read.
- **Plan audit** after every epoch: capacity, precedence, commitments, shift ends, guardrail (no new or increased violation), and the transfer invariant.
- **Run manifest:** input hashes (`FROZEN_*.json`), policy file, code version, solver version and settings.

### 17.9 Conventions fixed by the M0–M1 implementation (D-52)
- **Moving vans:** a van is re-routable only at a stop; once it departs toward a stop it completes that leg.
- **Cancelled pickup:** if the rider cancels while the van is driving, the van still reaches the curb, finds no rider and is free at once (no dwell).
- **No-show:** recorded 180 s after curb arrival; the van then leaves without dwell. During the wait the dispatcher sees the van free at arrival + 180 s without the rider; this is what the driver observes (no late boarding is assumed).
- **Planning a committed pickup:** the dispatcher plans as if the rider boards (it cannot see the presence draw).
- **0-s legs** (consecutive stops at the same point): the arrival is processed in the same second, after that second's departures; this is the one exception to the class order of §17.3.
- **Ties inside a class:** by key, so request IDs (R…) sort before van IDs (V…).
- **Dispatcher C:** candidates, units, pending price and its M bound, solver settings, status handling (no fallback) and tie-breaking are as recorded in D-52 and its amendment; the code is `src/sim/dispatch.py`.
- **M0 Lyft harness:** in L4 the rules act only before 900 s (the hand-checkable window). General post-18:15 Lyft integration is M2.

## 19. Changes from v0.4 (22 Oct 2026)
| v0.4 | v0.5 | Why |
|---|---|---|
| Dispatcher T as base; algorithm undecided | C provisionally held fixed; T a later robustness variant, never a runtime fallback | D-51 update |
| Patience checks omitted `committed` riders | Included (a rider can cancel while the van drives to the curb, as in the L3 key) | PDF review gap G1 |
| Triggers included every cancellation and no-show | Only those of requests in van planning; Lyft-side events never trigger | D-52; PDF review C9 |
| "Pickup" instant not stated | Curb arrival of the boarding vehicle; dwell follows | PDF review gap G2 |
| Shift-end rule stated two ways | Marked open (L7 only) | PDF review C5 |
| No implementation conventions | §17.9 | D-52 |

## 18. Changes from v0.3 (21 Oct 2026)
| v0.3 | v0.4 | Why |
|---|---|---|
| Lyft "cost" wording; §9.3 "cost per minute of P90 reduction" | Operational counts only; "resource use" | D-45 |
| §0 counts 162 / ~304 (taper) and 6-van scaling | 168 at constant 5 vans; sixth van on the same requests | D-36, D-37 (left stale in v0.3) |
| "30 seeds shared across patterns" | Cross-pattern comparisons are not paired | D-49 |
| Range ~145–205 | ~150–260, depending mainly on the fleet denominator; 29-day note | D-49 |
| Mode-specific no-show thresholds; frozen 0.047 unflagged | One p for all modes; errata for 0.047 | D-48 |
| No `lyft_failed` in the terminal list | Added (sensitivity only) | D-43 |
| Targets without dates | April-era wording vs live 21 Oct reading kept distinct | D-49 |
| No build rules | §17 build contract | D-46–D-48 |
