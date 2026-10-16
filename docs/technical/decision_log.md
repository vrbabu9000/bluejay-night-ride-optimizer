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
