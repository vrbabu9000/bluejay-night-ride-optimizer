# Decision log (plan v2)

One row per decision that sets a number or a rule. Status: OBSERVED / DERIVED / ASSUMED / PROVISIONAL. Owner/reviewer to be filled in by the team.

| ID | Date | Decision | Value | Status | Basis / source | Alternatives | Owner / reviewer |
|---|---|---|---|---|---|---|---|
| D-01 | 2026-09-29 | Map population | O/D maps count COMPLETED rides | DERIVED | City maps sum to O 24,056 / D 24,057 (two independent readers agree on 214 of 215 bubbles), equal within reading error to the p09 hourly and p07 daily completed totals; they do not match requests (~48k) or passengers (~33k) | Requests; passengers (rejected by the totals) | |
| D-02 | 2026-09-29 | Scope | No replay of April; build an April-shaped base scenario | Team decision | Plan v2, A1 (no night-level inputs exist) | Monthly reproduction (rejected) | |
| D-03 | 2026-09-29 | Service night | Rides after 00:00 belong to the previous service night | ASSUMED | Service runs 6 pm to about 2 am (p06, p09); calendar-day charts split nights | Calendar day | |
| D-04 | 2026-09-29 | Service limits | Wait 20 min, ride 25 min | PROVISIONAL | Earlier team discussion; not a verified Hopkins rule | Sensitivity 15/20 and 25/30 | |
| D-05 | 2026-09-29 | Base window | 18:00-19:00 | DERIVED | Peak hour (5,098/30 ≈ 170 completed rides/h) and first hour of service (no backlog, no warm-up) | 19:00-20:00 as a check | |
| D-06 | 2026-09-29 | Base load | 5 vans, 30 requests ("as served"); 60 requests ("as requested") | DERIVED | ≈6.2 completed rides per van-hour at 6 pm (p09/p06); cancellations roughly double requests (p07) | ρ grid {4, 6, 9, 12} | |
| D-07 | 2026-09-29 | Van start positions | At hotspots or a depot | ASSUMED | No data | Both, as variants | |
| D-08 | 2026-09-29 | Party size | Mean 1.39; shape P(1..4) = .72/.19/.06/.03 | Mean DERIVED; shape ASSUMED | p08 passengers / p07 completed | Poisson-shifted shape | |
| D-09 | 2026-09-29 | Cut/hidden map bubbles | Enter at their lower bound, then O and D margins scaled to the city-map fence (~24,056; O ×1.020, D ×0.986) | ASSUMED rule | Bubbles cut by the frame have unreadable counts; the city totals are exact | Midpoint of bounds (rejected: overshoots the fence) | |
| D-10 | 2026-09-29 | Calibration split | Physics (speed factor, dwell) on ride P10; behaviour (median, P90, waits) held out | Design choice | T6: short trips are nearly direct; the tail is routing-driven | Fit all quantiles (rejected: validates by construction) | |
| D-11 | 2026-09-29 | Georeference, city view | Scale fixed at campus/4 (two Google zoom levels); offsets from 7 weighted POI pins | DERIVED | Free fits give a ratio of 4.04; weights = 1/(quarter of the OSM bbox diagonal)^2 | Free 3-parameter fit (RMS 191 m) | |
| D-12 | 2026-09-29 | Direct travel times | OSRM demo server, car, free-flow | OBSERVED (external) | Retrieved 2026-09-29; cached | Local OSRM; Google (not used) | |
| D-13 | 2026-09-29 | Zones v0 | 16 zones by count-weighted k-means of bubble points (campus bubbles inside the campus frame, city bubbles outside) | Design choice | Zone level ≈ 150-300 m spread; georeference error 17-57 m | k = 12 or 20 as sensitivity | |
| D-14 | 2026-09-30 (renamed 2026-10-01) | Directions after G1, called approaches 1-3 from 1 Oct | Line 1 (simulation + dispatch) is the project. Line 2, renamed Approach 2 "Events, zones and traffic" on 1 Oct (when, where and how a night strains: an event-aware forecast of daily load and slowdowns, scored on each new monthly report; Apr 17 was a slow night, not a busy one) is a time-boxed side-branch: a brief only, after G2. Line 3 (what we do not see) is left open for Prof. Kearsley's view. Line 0 (trip-level replay) stays abandoned; its node-arc MILP survives as H | Team decision | Prof. Kearsley (29 Sep): location analysis and a dispatch survey are each project-sized; April holds one outlier night (Apr 17), so an event effect is not estimable from April alone (n = 1) | Make line 2 a second main line (rejected: splits a four-person team before G2) | |
| D-15 | 2026-09-30 | The data wish list | Kept, reframed as "the value of the next extract": each item names the ASSUMED value or caveat it retires and the result it sharpens, ranked by cost; one line in guide ch. 5, detail in Reference E; not raised with Prof. Kearsley | Team decision | Prof. Kearsley's first note: it is rare to get exactly the data you want; the list is for Hopkins and TransLoc (the client and vendor), where instrumentation advice is a normal deliverable | Drop it (rejected: it is useful to the client); keep it as a wish list (rejected: reads as a complaint) | |
| D-16 | 2026-10-01 | Request endpoints | Requests start at origin bubbles and end at destination bubbles, weighted by count; jitter is for display only | Design choice | Keeps every travel time an exact OSRM value; the georeference error (17-57 m) is below the bubble spread | Jittered, road-snapped points (rejected: every new point needs a new routing call and adds no information) | |
| D-17 | 2026-10-01 | Depot | The heaviest origin bubble in Z08, Homewood campus (`p04_b040`) | ASSUMED | The real depot is not known | Hotspot starts (the base); a known Hopkins depot if one is supplied | |
| D-18 | 2026-10-01 | O-D model | Gravity × IPF at bubble level: seed = w_o · w_d · exp(-β · t/60), β ∈ {0, 0.1, 0.2}/min (base 0.1); pairs under 60 s of driving are structural zeros (189 of 8,800) | Design choice; β ASSUMED | Bubble-level IPF reproduces both point and zone margins (residual ~1e-10) and keeps distance deterrence inside zones; T6 brackets β | Zone-level IPF then proportional split (rejected: ignores distance inside zones) | |
| D-19 | 2026-10-01 | Direction variant | `campus_outbound_6pm`: Z08 origin weights × 1.5, then all origins rescaled to the April total | ASSUMED | The maps are monthly totals, so the 6 pm direction is unobserved | The month average (the base) | |
| D-20 | 2026-10-01 | Requests per scenario | Exactly n per scenario (M = 30); Poisson(n) as a variant. Arrivals: Poisson, or a burst with 40% of requests in 18:00-18:10. Frozen: ladder hashes in `data/scenarios/FROZEN.json` (M `28c143c2…`), grid hashes in `data/scenarios/grid/manifest.csv` | Design choice; burst ASSUMED | A fixed n keeps the comparisons paired and the base easy to explain | Poisson count as the base | |
| D-21 | 2026-10-01 | Patience | Exponential, median 12 min, drawn once per request | ASSUMED placeholder; calibrated in Phase 6 | Under April's daily waits (lognormal through the median and P90) it implies 46.6% abandonment against a reported cancel share of 46.8% (r 0.74 by day). That treats nearly every cancellation as impatience, but "Canceled" also counts rebookings and Lyft hand-offs (T2), so true patience is probably longer | Fix it now from T3 (rejected: it would treat cancellations as abandonments) | |
| D-22 | 2026-10-01 | Van capacity, base | 4 seats; 7 as a sweep cell | ASSUMED | No source; 4 is the tighter, more conservative case | 7 as the base | |

## Accepted on 12 Oct 2026 (team instruction)
| ID | Date | Decision | Value | Status | Basis / source | Alternatives | Owner / reviewer |
|---|---|---|---|---|---|---|---|
| D-23 | 2026-10-12 | Study scope | Homewood Night Ride only. East Baltimore demand, policies and service targets are excluded | Team decision | User instruction, 12 Oct | Include East Baltimore (rejected) | |
| D-24 | 2026-10-12 | Pickup policy | Door-to-door / curb-to-curb within the service area. Designated-stop consolidation is out of scope. Digitized hotspots are demand-generation points, not stops | Team decision | User instruction, 12 Oct; JHU service description | Stop consolidation, the Penn model (out of scope) | |
| D-25 | 2026-10-12 | Baseline direction | A TransLoc-like re-planning dispatcher (events + periodic re-plan, reassignment, convex wait penalty) is the fixed baseline. Greedy and small-instance exact solvers are references, not the status quo. Details are proposals (`model_design.md`) | Team decision (direction) | `research_review.md` §2: the 2016 vendor description is historical, not confirmed current | Greedy as the status quo (rejected: straw man) | |
| D-26 | 2026-10-12 | Primary research question | Which dispatcher-initiated Lyft transfer rules improve Homewood rider outcomes, under which conditions, and at what resource cost, with the van dispatcher held fixed | Team decision (direction; wording refined in `research_review.md` §3) | User's preferred question | Greedy vs MILP as the primary question (rejected) | |

## Status changes to earlier decisions (12 Oct 2026; the rows above are unchanged)
| ID | New status | Why | Replacement (proposal) |
|---|---|---|---|
| D-04 | **Under revision** | 20/25 are East Baltimore figures; Homewood publishes 15/20 (busy-time 20), changed from 10/20/15 in Apr 2024 | P-03 |
| D-06 | **Under revision** | The load anchor divides by a mixed-service vehicle count | P-06 |
| D-12 | **Superseded if P-02 is accepted** | A local pinned OSRM matrix exists (v2) | P-02 |
| D-20 | **Paused** | The v1 ladder and grid are paused (Phase 3 v2), not deleted | `scenario_spec.md` §8–9 |
| D-21 | **Under revision** | The placeholder explained nearly all cancellations; the Lyft transfers inside "Canceled" must be left out | P-08 |
| D-22 | **Under revision** | Hopkins vans were 14-seat in 2018 | P-07 |

## Proposals awaiting team agreement (12 Oct 2026; NOT decisions)
| ID | Proposal | Where |
|---|---|---|
| P-01 | Boundary: Homewood + Peabody area, as April was operated (scenario_spec D-A) | `research_review.md` §4.2 |
| P-02 | Travel matrix v2 (local OSRM) + `MANIFEST.json`; the matrix is the canonical cross-machine artifact | `compute_feasibility.md` §4 |
| P-03 | 15/20 (and busy-time 20) as reporting thresholds and penalty break-points; ride guardrail max(25, 2·direct + 5) min, elastic; report at 10 and 15 min | `model_design.md` §4 |
| P-04 | Weighted objective: piecewise-linear convex φ (slopes 1/2.5/5/10/20), β = 0.5, γ = 0.1 min/km; lexicographic as a variant | `model_design.md` §4 |
| P-05 | Rolling horizon: Δ = 120 s, the same for all compared players; next stop frozen; pending price π_r with large M; latency rule | `model_design.md` §3, §5 |
| P-06 | Fleet availability: April taper shape × a calibrated level f ∈ [0.65, 1.0] | `scenario_spec.md` §3.2 |
| P-07 | Capacity 14 base (10 variant) | `research_review.md` §5 |
| P-08 | Patience: rising hazard, calibrated so rider cancellations ≈ 2/3 of "Canceled"; identified-set calibration | `scenario_spec.md` §3.3, §12 |
| P-09 | Lyft rules R0, R1(θ), R1u(θ), R2(θ), R3(m), with R4 optional; a separate module, not integrated into the solve | `scenario_spec.md` §6 |
| P-10 | Ladder L1–L7 (no-shows and cancellations separate) and a compact experiment matrix (36 primary cells) | `scenario_spec.md` §8–9 |
| P-11 | HiGHS as the exact solver, deterministic settings; a lock file before Phase 4 | `compute_feasibility.md` §3, §5 |
| P-12 | Hourly chart read as request hour (AS-25) | `research_review.md` §5 |

## Accepted on 20 Oct 2026 (team decisions on scenario_spec v0.1 §14)
| ID | Date | Decision | Value | Status | Basis / source | Alternatives | Owner / reviewer |
|---|---|---|---|---|---|---|---|
| D-27 | 2026-10-20 | Service boundary (D-A) | Homewood **including the Peabody area**, as April was operated | Team decision | `research_review.md` §4.2; ~20% of April O/D in the Peabody/downtown zones | Homewood core only; boundary as a factor (both rejected) | |
| D-28 | 2026-10-20 | Lyft rule set (D-E) | Keep all of R0, R1(10), R1(15), R1u(10), R2(15), R3(2) (R4 optional). Run **one rule at a time** per scenario, everything else fixed; explain why the best rule won (spec §9.3) | Team decision | User, 20 Oct | Trim the set (rejected) | |
| D-29 | 2026-10-20 | Objective (D-D) | Weighted: convex PWL wait penalty (slopes 1/2.5/5/10/20), β = 0.5, γ = 0.1 min/km, elastic guardrail max(25, 2·direct + 5) min; 15/20 (busy 20) as reporting thresholds | Team decision (accepts P-03, P-04) | `model_design.md` §4 | Lexicographic (kept as a variant) | |
| D-30 | 2026-10-20 | Fleet (D-F) | **5–6 vans with 14 seats** at 18:00, as a per-scenario factor, tapering in April's shape; demand **scaled to the fleet** so requests per van-hour match April (~11 average, ~13 at 6 pm); the load ratio ρ is the calibration knob | Team decision (replaces P-06; accepts P-07 at 14 seats) | User, 20 Oct: "proportional to the problem we are solving" | f × 27.6-van range (replaced) | |
| D-31 | 2026-10-20 | Travel matrix (D-C) | `tt_locations_v2.csv` (local OSRM) + `MANIFEST.json`; the matrix is the canonical cross-machine artifact | Team decision (accepts P-02; supersedes D-12 for v2 scenarios) | `compute_feasibility.md` §4 | Demo-server v1 matrix (kept for v1 only) | |
| D-32 | 2026-10-20 | Ladder (D-G) | L1–L7; no-shows (L2) and cancellations (L3) separate; Lyft mechanics at L4; L5 pilot; L6 main; L7 confirmatory | Team decision (accepts P-10, modified for 5–6 vans and 4 patterns) | `scenario_spec.md` §8–9 | — | |

Still proposals: P-05 (rolling-horizon details), P-08 (patience form), P-09 details (parameters as in spec §6), P-11 (HiGHS + lock file, Phase 4), P-12 (request-hour reading). These are fixed in `preregistration_v2.md` once the team confirms generation.

## Added on 21 Oct 2026
| ID | Date | Decision | Value | Status | Basis / source | Alternatives | Owner / reviewer |
|---|---|---|---|---|---|---|---|
| D-33 | 2026-10-21 | Lyft eligibility of parties of 5 | Parties of 5 are Lyft-eligible through a larger vehicle (e.g. Lyft XL) and stay together; parties of 1–4 use a standard Lyft. XL trips are counted separately. XL availability, pickup delay and cost are UNKNOWN: the base uses the same latent Lyft delay and no surcharge | **Accepted modelling instruction**, from **user-supplied operational knowledge** (not independently verified Hopkins policy) | User correction, 21 Oct. Replaces the 2018 News-Letter rule ("5+ riders always get a van, Lyft gives us four seats"), which referred to standard 4-seat Lyft cars. The 2018 evidence is kept, dated, in `transloc_operations.md` | Keep parties of 5 ineligible (rejected: contradicts current operational knowledge); split the party (rejected: the party stays together) | |
| D-34 | 2026-10-21 | Geographic representation | The **reference** keeps point-based clusters (188 points; unchanged, frozen). A **dispersed variant** `dispersed_v1` spreads the 19 coarse city-view clusters over 6 road satellites each (400 m disk, snap ≤ 75 m, inside the approximate modelled region, outside the campus frame, ≥ 100 m apart, equal weights) | Variant **implemented and verified**; whether it becomes the base geography for L6 is **provisional** | Resolution criterion: city view 4× coarser than the campus view (position uncertainty 101 m vs ~28 m); one coarse point received ~11 Mount Vernon pickups per 162-request night | Spread only the 10 downtown points (rejected: inconsistent with the resolution criterion); per-request jitter (rejected: unbounded new routing points) | |
| D-35 | 2026-10-21 | Request volume formula | N_h = ρ_h × v_h with ρ_h = (C_h/30)·(R/C)/V_h hour by hour; largest-remainder rounding; 18:00–21:00 at 5 vans → 64/50/48 = 162 (April taper) or 64/50/54 = 168 (constant) | **Provisional** (depends on the unresolved constant-vs-taper availability choice and on calibration of ρ) | `scenario_spec.md` §3.2; p06/p07/p09 | Night-average ρ ≈ 11 (rejected: hides the 6 pm peak); one 5/27.56 factor for every hour (rejected: correct only under the April taper) | |

## Scenario design trail (report-ready, 21 Oct 2026)
This section explains, in plain terms, the choices that build a scenario's *inputs*. Outcomes (waits, cancellations, Lyft transfers, completions) are produced by the simulator and are not chosen here.

**Status words used below:**
- **accepted:** the team decided;
- **provisional:** a working value that may change;
- **implemented:** in code;
- **verified:** checked by tests.

### 1. When requests can arrive
| | |
|---|---|
| **Question** | Over which window do requests arrive in the main experiments? |
| **Approach** | 18:00–21:00. After 21:00 no new requests arrive; the simulation continues until every request is resolved |
| **Why** | The busiest three hours; 18:00 is the first hour of service, so there is no inherited backlog |
| **Evidence / instruction** | Team decision (ladder level L6); hourly completed rides peak at 6 pm (p09) |
| **Alternatives** | 18:00–20:00 (rejected by the team); the full night (kept for the confirmatory level L7) |
| **Limitations** | The closing and van-availability rules after 21:00 are still to be specified |
| **Sensitivity** | Not a factor |
| **Status** | Accepted |
| **Files** | `scenario_spec.md` §8 |

### 2. How many requests arrive in each hour
| | |
|---|---|
| **Question** | How many requests should five vans face from 18:00 to 21:00? |
| **Approach** | Copy April's workload per vehicle, hour by hour, and give the scenario's vans that workload: requests in hour h = ρ_h × vans in hour h |
| **How ρ_h is built** | ρ_h = completed rides in that hour per night × recorded requests per completed ride (2.087) ÷ average vehicles in that hour. This gives 12.85, 10.10 and 10.71 for 18:00, 19:00 and 20:00 |
| **Rounding** | Hourly values are rounded so that they add up to the rounded total (largest-remainder rule) |
| **Result** | **64 / 50 / 48 = 162** if vans taper as in April; **64 / 50 / 54 = 168** with a constant five vans |
| **Why** | The data give workload per vehicle, not demand for a five-van system. Matching hour by hour keeps the 6 pm peak, which a night average would flatten |
| **Evidence** | April status totals (p07), completed rides by hour (p09), vehicles by hour (p06) |
| **Alternatives** | A night-average load of ≈ 11 (rejected); one scaling factor for every hour (correct only under the April taper) |
| **Assumptions** | Every status is one request, and Denied is zero. The request-to-completion ratio is the same in every hour. The hourly chart counts completed rides by request hour. The vehicle chart ("All services") stands in for Homewood vans |
| **Limitations** | April gives a plausible range, not a precise count. ~145–205 is an **illustrative sensitivity range, not a confidence interval**: fewer true Homewood vehicles push the count up, rebookings push it down. Scaling demand down with the fleet keeps the workload per van but not the density of requests, so pooling chances are lower than in the real system |
| **Sensitivity** | The calibration setting ρ; a high-load pattern (+30%) |
| **Status** | **Provisional**. The constant-vs-tapering availability choice is **not decided**, and this section does not decide it |
| **Files** | `scenario_spec.md` §3.2; decision D-35 |

### 3. When requests arrive within an hour
| | |
|---|---|
| **Question** | At what times within an hour do requests arrive? |
| **Approach** | A fixed count per hour, at uniformly random times. This is a Poisson process *conditional on its count* |
| **Seeds** | A named "times" stream per level, pattern and night. Every policy replays identical times |
| **Why** | Clean paired comparisons |
| **Alternatives** | A random hourly count (Poisson); kept as a variant |
| **Limitations** | Night-to-night variation in volume is removed. April's daily requests varied ~11% (1,434–2,145) |
| **Sensitivity** | The random-count variant; the burst pattern |
| **Status** | Accepted design; implemented for L5 |
| **Files** | `generator_v2.py`; `scenario_spec.md` §3.2, §11 |

### 4. Where requests start and end: representation
| | |
|---|---|
| **Question** | At which exact places do requests appear? |
| **Approach** | **Reference:** each request sits at its April map-cluster point (188 points), snapped to the nearest road. **Dispersed variant:** each of the 19 coarse city-view clusters is spread over 6 road locations within ~400 m |
| **Dispersed details** | Each satellite carries one sixth of the cluster's weight. The variant shares the reference's request times, cluster-level pairs, party sizes and rider traits |
| **Why** | City-view bubbles are 4× coarser than campus-view bubbles. Each stands for a whole neighbourhood, so the reference stacks many requests on one spot (~11 Mount Vernon pickups per 162-request night). That flatters pooling exactly where long, isolated trips make Lyft attractive |
| **Evidence** | Map digitization and georeferencing (p02–p05); OSRM snapping |
| **Alternatives** | Spread only the 10 downtown points (inconsistent criterion); jitter every request (unbounded routing) |
| **Assumptions** | The 400 m radius. The region boundary (convex hull of the April points + 100 m) is an **approximation, not a verified service boundary**. Satellites are synthetic locations, not recovered addresses |
| **Limitations** | With 6 random satellites, each cluster's effective centre shifts 30–243 m. Clusters next to the campus frame or the region edge lose candidates on one side |
| **Sensitivity** | Reference vs dispersed; radius 250 / 600 m |
| **Status** | Variant **implemented and verified** (6 tests). Choosing which geography is the L6 base is **provisional** |
| **Files** | `spread.py`, `build_dispersed_v2.py`, `tests/test_spread.py`; decision D-34 |

### 5. Which origin goes with which destination
| | |
|---|---|
| **Question** | The maps give separate totals of pickups and drop-offs per place. How are they paired into trips? |
| **Approach** | Gravity × IPF. Pairs start with weight pickups(o) × drop-offs(d) × e^(−β_geo × drive minutes), with β_geo = 0.1 per minute; pairs under 60 s of driving are excluded. Iterative scaling then makes every place's totals equal April's |
| **Why** | Standard in transport planning; reproduces both observed margins exactly (largest error ~10⁻¹⁰) |
| **Evidence** | April map margins (completed rides only) |
| **Alternatives** | β_geo = 0 (no distance preference) or 0.2 |
| **Assumptions** | Requests share the geography of completed rides (cancelled requests' locations are unobserved). The pairing rule itself. The same geography in every hour |
| **Limitations** | The data cannot distinguish β_geo values: all of them reproduce the margins. In the dispersed variant the 60-s rule is applied at cluster level, and the 2 satellite pairs (out of 840 requests) that fell under 60 s were redrawn |
| **Sensitivity** | β_geo = 0 / 0.1 / 0.2; the campus-outbound direction variant |
| **Status** | Accepted (D-18); β_geo provisional; implemented and verified |
| **Files** | `demand.py`; decision D-18 |
| **Note** | β_geo (distance decay) is unrelated to the ride-cost weight β = 0.5 in the dispatcher's objective |

### 6. Lyft for parties of five
| | |
|---|---|
| **Question** | Can a party of five be transferred to Lyft? |
| **Approach** | Yes, as one party in a larger vehicle (Lyft XL); parties of 1–4 use a standard Lyft. XL trips are reported separately |
| **Why** | User-supplied operational knowledge (21 Oct). The 2018 rule excluding 5+ riders referred to standard 4-seat Lyft cars |
| **Alternatives** | Exclude parties of five; split the party (both rejected) |
| **Assumptions** | XL is available like standard Lyft, with the same pickup delay and no cost difference. **All unknown**; nothing is invented |
| **Limitations** | About 1% of requests (≈ 1.6 per 162-request night), so effects are small but visible in the subgroup report |
| **Sensitivity** | XL delay longer than standard; XL scarcity at peaks |
| **Status** | Accepted modelling instruction (not verified Hopkins policy) |
| **Implemented** | In the L4 answer key (the party of 5 is transferred whole by XL under four rules) and the tests. The simulator itself is not built |
| **Files** | `generator_v2.py`, L4 `handcheck.csv`, `tests/test_scenario_v2.py`; decision D-33 |
