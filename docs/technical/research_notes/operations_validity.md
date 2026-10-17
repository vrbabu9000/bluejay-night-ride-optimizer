# Operations and validity review: Homewood Night Ride, TransLoc dispatch, Lyft overflow

**Author:** research agent (workstream: Homewood operations, missing angles, experiment validity). **Date:** 12 Oct 2026.
**Reviews:** `docs/technical/transloc_operations.md` v1.0, `docs/plans/phase3/plan.md` v2. **Writes nothing else.**
**Labels:** VERIFIED (I read the primary text myself) / SECONDARY (second-hand or a search snippet) / INFERENCE / HYPOTHESIS.
**Scope reminders:** Homewood only; Peabody is flagged, not decided; targets, software constraints and modelling choices are kept apart.

## 0. Headlines (what disagrees with the project docs)

1. **The "hard ceiling" is not evidence.** TransLoc's own blog (2 Sep 2026) says "The wait time has a hard ceiling built into the system". It is a paraphrase of a student column (News-Letter, 23 Aug 2026) that says only "if the shuttle doesn't come within fifteen minutes, the University will send a Lyft". No JHU or TransLoc document says the software enforces a wait cap. Do not cite it either way (VERIFIED text; claim UNSUPPORTED).
2. **The Homewood targets are a moving policy parameter, not a fixed fact.** The JHU page said pickup in **10 min**, ride ≤20, busy up to **15** (capture 26 Aug 2023, same through 3 Mar 2024). By the 20 Apr 2024 capture it said **15 / 20 / 20**. The East Baltimore FAQ block on the same page still says "ten minutes on average, goal of 15 maximum" in an Oct 2025 capture, so the page contradicts itself (VERIFIED, Wayback). That the targets were loosened is a stronger sign they are goals than the doc's argument "April P90 exceeds them".
3. **April waits understate violations.** p11 waits exist only for picked-up riders. Riders who cancelled or were moved to Lyft are missing (p11 brief). "P90 ≈ 18 min vs 15" is therefore a lower bound on how often the target was missed, and it cannot say anything about enforcement.
4. **Peabody evidence is weaker than §4.2 states.** The sentence "in term time combined with the Peabody area" is in the **Apr 2023** page (`ts.jhu.edu`), not in the July 2026 page the doc cites. The Aug 2023–Jul 2026 `jhfre.jhu.edu` page has **no** Peabody sentence in the Night Ride block (VERIFIED, six captures, plus grep of the July 2026 snapshot). "Both trip ends must be in the zone" comes from the **Jan 2018 Hub** article (about Lyft rides), not from 2026.
5. **Lyft trigger is probably "time without an assigned van", not "expected wait".** The JHU East Baltimore FAQ on the same page says the ETA "almost always changes prior to a vehicle assignment", that dispatchers "review pending trip assignments", and that a Lyft "generally occurs within ten minutes without a van assigned". That is East Baltimore wording, so it cannot be copied to Homewood, but it suggests a Pending-and-unassigned state that §3.3 lists as UNKNOWN. It changes how AS-06 and AS-02 should be coded.
6. **The East-Baltimore-in-the-vehicle-chart inference has a hole.** East Baltimore also runs 5–9 am on TransLoc (JHU page). If "All services" included it, the chart would show bars at 5–8 am. It shows none from 3 am to 5 pm (p06). So either the filter excludes at least that service, or the 6 pm count is limited in some other way. AS-14's "27.6 − 5.6 = 22" is one hypothesis among several, not a default.
7. **AS-25 (hour = pickup hour) is in tension with p09.** Requests are honoured until 2 am, but the 2 am completed-ride bar is ≤29 in 30 days, against ~1,560 in the 1 am hour. Under a pickup-hour (or completion-hour) reading about 150–260 rides would fall after 2:00. A request-hour reading fits (INFERENCE, see §H).
8. **Fri–Sat-only peak variant (AS-23) is contradicted for 2026.** Lyft carried riders on every weekday in April (Sunday mean 229/day, p10).

---

## A. The 2016 TransLoc TechLog post, and newer primary evidence

### A.1 What the post is (VERIFIED, archive snapshot 28 Apr 2018, `0028088450.txt`)
- **Title:** "Ridesharing Algorithms in TransLoc OnDemand", TransLoc TechLog (Medium). **Byline:** Michael Fogleman, Software Engineer at TransLoc (he lists TransLoc 2013–2016 on his own site, SECONDARY).
- **Date:** no date printed in the extract. The archive banner says 17 captures from **11 Sep 2016**, so it was published on or before that date. It says "six universities are using the product" and "Since August [2015]... 60,000 passengers", so it is early or mid 2016 (INFERENCE). The doc's "2016" is right, but "published ≤ 11 Sep 2016" is the defensible statement.
- **What it says:**
  - Inputs: vehicles (location, load, capacity); rides (origin/destination, party size, desired time only if booked in advance, and a **"Candidate Vehicles (determined by other parts of our system)"** list).
  - Decision: which vehicle serves which ride, and the stop order. Pickup precedes drop-off.
  - Method: simulated annealing. Moves: reassign a ride's vehicle, or move a stop. "Millions of states" per schedule. A 12-ride, 1-vehicle test converged in under 15 s per run.
  - Score: wait time, ride duration, vehicle mileage, with weights "not necessarily linear". Example: prefer cutting 1 min from a 10-min wait over 2 min from a 5-min wait.
  - Triggers (quote): "runs whenever a new ride is submitted, a ride is canceled, or a driver reports a no-show. It also runs every two minutes to refine the schedule."
  - Marketing claim: "always provides a globally optimal schedule". This contradicts the same post (a randomized heuristic, "fairly certain" only on a 12-ride case). Treat it as hype.
  - Results quoted: 60,000 passengers, 8-minute average wait, one client +32% riders and −15% wait.
- **What it does NOT say (important for the doc):**
  - Nothing on hard wait or ride limits. The doc's "no hard limit mentioned" is accurate, but that is absence of mention, not evidence of absence.
  - Nothing on driver accept/decline, on dispatcher override, or on **whether an assigned-but-not-picked-up ride may be moved**. The doc's §3.2 sentence "a ride that has been assigned but not yet picked up can move to another van" is an **inference** from the mutation set (vehicle reassignment moves) plus the 2-minute rerun. It is a good inference (annealing on all open rides can only work that way), but the post never states it. It also does not say whether rides already promised an ETA are "frozen".
  - Nothing on the candidate-vehicle rule.
  - The "every two minutes" refers to the 2016 product; whether the cadence, the objective or the algorithm survived the Ford (2018) and Modaxo (2022) ownership changes is UNKNOWN.
- Doc §3.2 is a faithful summary except for the reassignment point above and "(VENDOR) 2016; current version UNKNOWN", which is correctly hedged.

### A.2 Search for newer primary evidence (2018–2026): result is thin
| Search | Finding | Label |
|---|---|---|
| Google Patents, assignee TransLoc (query run through the Patents search endpoint) | 3 results total; the one I opened (US 8,510,043 B1, granted 13 Aug 2013, inventor Joshua Whiton) is about displaying route information on a map. Search snippets list US 7,920,967 and US 9,007,238 as route-information patents. **No dispatch or scheduling patent.** No hits for Modaxo or Ford Global Technologies on microtransit dispatch | VERIFIED (query), SECONDARY (the other two) |
| US 8,781,726 B2 "Method and system for adjusting a demand-response transit schedule", Trapeze Software Inc., granted 15 Jul 2014 | Related company, not TransLoc. I did not read its claims. It cannot be used to describe OnDemand | VERIFIED (exists), UNREAD |
| TransLoc OnDemand Driver app, App Store version history to v1008.9.4 (16 Dec 2024) | Notes are mostly "bug fixes". Substantive entries: walk-up rider entry and loading/unloading workflow (May 2019), "rider can't see you" message within 200 m and no-show message (Mar 2019), **interactive wait timer for services with an agency wait standard (Apr 2021)**, improved navigation (Aug 2023). **No mention of accepting or declining rides**, and nothing about dispatch logic after 2021 | VERIFIED |
| TransLoc blog, "Solving Dispatcher Challenges Through Technology", 6 Apr 2022 | Fixed-route dispatch; says nothing on OnDemand assignment or overrides | VERIFIED (via fetch tool summary) |
| TransLoc "MicroTransit Simulator" (Metro Magazine, 3 Aug 2017) and the SIMPO/Rides MTD 2020 report (in repo `simpo.txt`) | The simulator "runs the same scheduling algorithm that is used in the TransLoc OnDemand production system" (2020 report). Outputs: wait, ride time, share of rides under 15 min. Confirms the production algorithm is a dynamic optimizer and is the only post-2016 statement about it | VERIFIED (2020 report text), SECONDARY (2017 article) |
| TransLoc help centre, agency RFP/contract language on "automatic dispatch / driver accept / manual assignment / max wait" | **Not found.** Searches returned marketing and third-party listings (dispatchers can monitor pending/in-progress/completed rides and book call-in rides; driver "automatically notified"). The help centre and operations manuals are not public. `covidinfo.jhu.edu` and `transloc.com` returned Cloudflare blocks to scripted fetches | NOT FOUND |
| Vanderbilt/CARTA "Mobility-On-Demand" paper (NSF PAR 10466140) | Different system, not TransLoc. Ignore | VERIFIED (read) |

**Current vs historical.** Everything on the engine is 2016 or marketing. The only post-2016 primary statements are: JHU pages (2023–2026) saying dispatchers "review pending trip assignments" and that the ETA changes before assignment (East Baltimore FAQ), and the 2021 driver-app wait timer. Treat "re-plan every 120 s with reassignment" as the **best-documented historical behaviour**, not as verified 2026 behaviour.

**One more soft datum:** an anonymous student in the News-Letter (9 Oct 2025) says "Shuttles will accept a ride almost at the 15-minute mark, but they can take an additional 5 to 10 minutes to arrive". This is one anecdote using the word "accept". It is weak support for the contact's account (HYPOTHESIS), and equally consistent with the rider-facing words "your trip was accepted/assigned".

---

## B. Homewood service boundary, Peabody, both ends, hours

| Question | Evidence | Label |
|---|---|---|
| Is Peabody merged into the Homewood Night Ride in term time? | **Apr 2023** `ts.jhu.edu` page: "During the Fall and Spring Academic Terms, the Homewood Night Ride service is operated in conjunction with the Peabody Escort Van service, combining the two regions into one service area. The Peabody service area is loosely bound by 20th Street to the north, Guilford Avenue and South Street to the east, Pratt Street to the south, and Howard Street to the west." | VERIFIED (2023) |
| Is it still stated in 2024–2026? | The Aug 2023–Jul 2026 `jhfre.jhu.edu` page says only "a service area which is proximate to the Homewood campus", with no Peabody sentence (six captures checked: 26 Aug 2023, 20 Apr 2024, 14 Jan 2025, 6 Oct 2025, 30 Apr 2026, 22 Jul 2026). The East Baltimore block lists Peabody as a valid East Baltimore destination (separate service) | VERIFIED (absence on the page) |
| Term vs breaks | **Dec 2021 Hub**: Peabody Escort Van area served until 18 Dec; from 19 Dec "Night Ride availability will be limited to the Homewood service area only"; Peabody zone resumes 22 Jan. So the Peabody zone has historically been **switched off in breaks** | VERIFIED (2021) |
| History | News-Letter 27 Sep 2022 (Molly Green): "the Peabody Institute service zone was reintegrated into the Homewood Night Ride service area on Sept. 18" and the Night Ride radius was reduced (students lost Inner Harbor access). Aug 2019 Hub: Night Ride extended to Peabody Institute 6 pm–3:45 am | VERIFIED (2022, 2019) |
| Does April 2026 data show Peabody-zone demand? | Digitized city-view cluster bubbles (completed rides): one bubble at 39.2966, −76.6158 (Peabody / Mount Vernon Pl) holds **1,577 origins (6.6%)** and 1,575 destinations; further bubbles near 39.287–39.290 (Pratt St / Inner Harbor side; 1,163 origins, 4.8%) and 39.306 (Mount Vernon/Charles, 1,218). **11–16% of completed rides start or end south of ~39.305 N.** Cluster centres have ~100 m uncertainty and bubbles are cluster positions, not points. Late April is in term | INFERENCE |
| Both trip ends inside the zone? | Jan 2018 Hub (about Lyft): "Both pickup and drop-off points must be within the service area." 2023 and 2026 pages: "curb-to-curb service **to and from** locations within the service area", and the app "won't allow you to book" an out-of-area address (East Baltimore FAQ). Consistent with both ends in zone, but there is no 2026 sentence that says so | VERIFIED (2018), INFERENCE (2026) |
| Hours | Requests accepted from 6 pm; requests before 2 am honoured (2023, 2026 pages); JHU Student Affairs presentation (uploaded Jun 2025, J. Jackson): "starts at 6:00 p.m. and meets all requests in by 2:00 a.m."; News-Letter Aug 2026: 6 pm–2 am. Seven days a week except holidays. How long past 2 am vans finish is not stated | VERIFIED |
| Maps | An interactive service-area map exists in the TransLoc app (not captured). The only published geometry is the 2023 Peabody street list and the 2018 Hub image (not machine readable) | VERIFIED |

**Flag for the team (not a decision).** Three defensible scopes: (i) Homewood core only, (ii) Homewood + Peabody (the 2023 and 2022 rule, and what April demand looks like), (iii) both as a scenario factor. Under (i), ~7–16% of April completed rides would fall outside the scope and the calibration to 24,095 completed rides / 1,115 vans-hours must be rescaled. The Peabody sub-zone also sits ~2.5 km from the campus core, so it affects travel times, depot choices and where Lyft is cheapest. Also note: the original Peabody Escort Van was a **separate service** and may have separate vehicles in "All services".

---

## C. The 15/20 targets

- **Wording (VERIFIED, July 2026 capture, block "What to Expect"):** "Service parameters include picking up passengers within 15 minutes of request and ride lengths not exceeding 20 minutes. During busy times (rush hours), shuttles may take up to 20 minutes to arrive. Dispatchers track the shuttles, and if a ride cannot be provided in a timely manner, a free Lyft will be dispatched."
- **Page / date:** `jhfre.jhu.edu/ts/transportation/shuttle-services/`, captured 22 Jul 2026; present in captures since Apr 2024. Earlier (26 Aug 2023–3 Mar 2024) it read 10 / 20 / 15.
- **Caveats on applicability:**
  1. The block sits above the campus-specific blocks and says "Blue Jay Shuttle". It is not labelled Homewood. The East Baltimore block has its own numbers (12 avg / 20 max wait; 12 avg / 25 max ride). Reading the 15/20 as Homewood is reasonable (INFERENCE) but not stated.
  2. "Busy times (rush hours)" is East Baltimore vocabulary (8–9 am, 5:30–6:30 pm). For a 6 pm–2 am service the phrase is undefined.
  3. JHU's June 2025 presentation says "We average 12 minutes from request to pick-up, and get everyone within 20 minutes!" The April medians are 9.4–12.9 min and P90 16.9–21.2 min (p11). "Everyone within 20" is promotional.
  4. Ride "not exceeding 20 minutes": April P90 is ≈24 min and the daily P90 reaches 29 min (p12).
- **Software constraint or not?** No source says so. The 2024 loosening from 10 to 15 suggests a policy dial. The vendor blog's "hard ceiling" is unsupported (Headline 1). Observed breaches are consistent with soft targets, but they would also be consistent with a hard constraint that is relaxed under infeasibility, and with the dispatcher's Lyft rule acting as the enforcement (the thing the project is studying). **Keep three layers separate in the model:** (a) published target (reporting threshold), (b) dispatch-engine objective/constraints (unknown), (c) human Lyft rule. Do not fit (b) to make (a) look soft.

---

## D. Lyft program status (2024–2026)

| Aspect | Evidence | Label |
|---|---|---|
| Who triggers | "Dispatchers may transfer a pending ride from a Blue Jay Shuttle to Lyft during peak service hours. A Lyft driver will be sent directly by the dispatcher" (identical in Apr 2023, Aug 2023, Oct 2025, Jul 2026 pages). Also "Dispatchers track the shuttles, and if a ride cannot be provided in a timely manner, a free Lyft will be dispatched." | VERIFIED |
| Criteria | Homewood: "peak service hours" and "timely manner", no numbers. Students: 15 min (News-Letter 23 Aug 2026; "more often than not"); 25–30 min in total to get a van or a Lyft (anonymous, Oct 2025). East Baltimore FAQ: dispatch a Lyft "when necessary to meet our service guidelines. This generally occurs within ten minutes without a van assigned". Search snippet of `covidinfo.jhu.edu` (blocked to me): Lyft "called automatically through the TransLoc app when the wait exceeds 10 minutes" (COVID-era, unverified; SECONDARY). 2018: Fri/Sat only, rider asked first; 5+ riders always get a van (News-Letter Feb 2018, quoted in the doc, not re-read by me) | VERIFIED / SECONDARY |
| Consent | 2018: dispatcher "may ask if a rider will accept" (Hub). 2023–2026 pages: no mention of asking. Consent is **UNKNOWN today** | VERIFIED (2018) |
| Lyft wait | 2018: driver waits ≤5 min; 2023–2026: ≤3 min after arrival. Time to arrive: not published. One anecdote: a cancelled shuttle "can lead to a Lyft with about 10 more minutes of waiting" | VERIFIED / anecdote |
| Capacity limits | No public statement of a cap, budget, or Lyft pool size. The Lyft is paid by JHU, so a budget is plausible (HYPOTHESIS). Lyft supply during peaks (surge, storms, Friday nights) is outside all data | UNKNOWN |
| Service area for Lyft | 2018: same as the van service; both ends in area | VERIFIED (2018) |
| In TransLoc status data | Not documented anywhere. The project's inference (transfer shows as "Canceled", r = 0.88 with Lyft riders) is plausible. Alternatives not excluded: dispatcher marks the ride "Completed" when booking the Lyft; the Lyft is booked outside TransLoc and the van ride is cancelled by the dispatcher or by the rider; or the rider cancels after being texted. Slide annotation by Hopkins ("many cancelled become Lyfts") is the strongest single piece of evidence | INFERENCE |
| Lyft's share | 24.5% of April riders (p10) | DATA |
| Rider experience | 50% / 16.7% / 33.3% "prompt Lyft" in a News-Letter survey whose percentages are multiples of 1/6 (so n is probably 6; not stated). Do not use as a rate | SECONDARY |

---

## E. Fleet: what the evidence can and cannot say

- **Fleet counts:** 12 vans in 2018 (Hub, 7 nights). No later public count. Fleet IDs in the 700s–900s (705, 980) are identifiers, not counts. Capacity: "14-seat vans" is from a 2018 press quote that I did not re-read here (SECONDARY); with a booking cap of 5 and average load ~1.8, capacity rarely binds, so this matters little.
- **What the "All services" chart can show (p06):** a shape of the supply of logged-in vehicles through the night, averaged over 29 days (the day count differs from 30). Taper: 27.6 (6 pm), 24.6 (8 pm), 19.4 (9 pm), 16.6 (11 pm), 11.1 (midnight), 9.3 (1 am), 4.5 (2 am), 0 (3 am).
- **What it cannot identify:**
  1. Which service each vehicle belongs to. Candidates for non-Homewood vehicles in the hours 6 pm–midnight: East Baltimore PM Blue Jay Shuttle (5:30 pm–midnight, JHU page), the Peabody Escort Van (if still a separate TransLoc service), Giant Night Ride (6–10 pm, circulator-type), spares and training.
  2. The **absence** of any bar from 3 am to 5 pm is also unexplained: East Baltimore AM service (5–9 am daily) and weekday daytime vans are on TransLoc too. So "All services" is not literally all JHU services, and the project cannot say which are included. The inference "the −5.6 at midnight is East Baltimore leaving" (§1 finding 9) is therefore HYPOTHESIS, and so is the "~22 Homewood vans at 6 pm". Note East Baltimore PM leaving at midnight would also not explain the −5.2 at 21:00.
  3. What "active" means (logged in vs on a trip vs dispatchable), vehicles in transit to or from the depot, drivers on breaks.
  4. Hours 2–3 am: 4.5 vehicles with ≤29 completed rides at 2 am implies vehicles finishing, returning, or non-Homewood.
- **Effect on the experiment:** rides per van-hour (6.2 vs 7.7) and thus the fleet size at which waits appear are both exposed to a ±20% fleet uncertainty. Better to **calibrate fleet-by-hour so the baseline reproduces the observed wait median/P90 and Lyft share**, and treat 22 and 27.6 as the ends of a range, not as data.

---

## F. Assumption register AS-01..AS-25: classification

Status: supported / outdated / uncertain / contradicted / needs-sensitivity. **R** = could reverse a Lyft-policy conclusion (must be varied in the main design); **W** = can wait (fixed or minimal sensitivity).

| ID | Status | Recommended default | Reason | R/W |
|---|---|---|---|---|
| AS-01 assignment | supported (auto) / uncertain (driver response) | Automatic central assignment; driver decline as variant, not default | Vendor 2015–16 and JHU pages. But a Pending-and-unassigned state exists (East Baltimore FAQ, USC), so assignment is not instantaneous | R (via what the dispatcher sees) |
| AS-02 re-plan 120 s, reassignment | outdated-risk (2016 only), needs-sensitivity | Event-driven + 120 s, reassignment of unpicked rides allowed; sweep {none, 60, 120, 300} | Only source is the 2016 post. The post does not say assigned rides can be swapped; ETA-change complaints support it | R (baseline strength) |
| AS-03 objective | uncertain, needs-sensitivity | Convex wait penalty > ride > miles; sweep wait-heavy/ride-heavy | Weights unknown; "safety first" is a JHU wording about order of service, not weights | R |
| AS-04 engine method | uncertain | Insertion + local search stand-in; MILP as upper reference | Method matters less than objective and trigger, per plan | W |
| AS-05 targets soft | needs-sensitivity (doc's "supported" overstated) | 15/20 as reporting thresholds, not constraints; hard-cap variants | Observed breaches are survivor-biased; targets changed 2023→2024; "soft" is not proved | R (a hard cap acts like a built-in Lyft trigger) |
| AS-06 Lyft trigger | uncertain, needs-sensitivity | Trigger on **elapsed time pending/unassigned** (and projected ETA as a variant), threshold {10, 15, 20}; lag {0, 2, 5}; consent {1, 0.8}; whole night | 10 min (East Baltimore FAQ, COVID-era snippet), 15 min (students, targets), "peak hours" undefined | R (core factor) |
| AS-07 dispatcher capacity | uncertain, needs-sensitivity | Unlimited baseline; cap and a delay distribution for stress | 'Trained dispatchers review pending trips' implies attention is finite. Matters when a policy raises transfer volume | R |
| AS-08 Lyft supply/wait | uncertain | Lognormal, median ~8 min, tail to 20; plus a peak-supply scarcity variant; no pooling | No data at all; the policy's benefit is the gap between van wait and Lyft wait | R |
| AS-09 patience | needs-sensitivity | Hazard rising with shown ETA and time waited; calibrate to ≈2/3 of Canceled | Aggregate correlation of wait and cancellation is not causal (§H) | R |
| AS-10 content of Canceled | uncertain | Lyft ≈ 1/3 (range 23–46%), plus a variant where transfers are not in Canceled | Derived from party-size assumptions, not observed. Unknown whether Completed includes Lyft | R (calibration) |
| AS-11 rebooking | uncertain | Base 0; variant 0.2–0.5 with delay | Student says a cancelled shuttle then gets a Lyft; duplicates inflate Canceled | R (moderate) |
| AS-12 no-show | supported (rate) | 4.7% of requests, independent of wait | Steady daily; dependence on wait unknown | W |
| AS-13 denial | supported | None in area and hours | App blocks out-of-area bookings (FAQ); Denied≈0 | W |
| AS-14 fleet by hour | **uncertain, partly contradicted** | Treat Homewood fleet as a calibrated range (18–27.6 at 6 pm); do not subtract East Baltimore as fact | AM East Baltimore absent from chart; Peabody van may be separate; 21:00 drop unexplained | R |
| AS-15 capacity 14 | uncertain (2018) | 10–14 seats; check binding | Booking cap 5 and mean load 1.8; "safety first" can fill vans at peaks | W |
| AS-16 party size | supported | mean 1.39, cap 5; party≥5 never Lyft; Lyft cap 4 | JHU and 2018 quote | W (but defines Lyft eligibility) |
| AS-17 dwell | uncertain | 30 s + 3-min wait | No data | W |
| AS-18 curb-to-curb | supported | Curb-to-curb at hotspot points; stops excluded by scope | JHU | W |
| AS-19 walk-ups | uncertain | None | Driver app has a walk-up feature (2019); Hopkins use unknown | W |
| AS-20 area | **needs-sensitivity (Peabody)** | Flag: run Homewood-only and Homewood+Peabody | Merger documented 2022–2023, silent 2024–2026; 7–16% of April rides near/south of Mount Vernon | R (changes distances, Lyft attractiveness) |
| AS-21 travel times | needs-sensitivity | OSRM × [1.0, 1.5] | No evening speed data | W (moderate) |
| AS-22 ETA shown | uncertain, needs-sensitivity | Initial ETA estimate that changes at assignment, noise sweep | JHU FAQ says it "almost always changes prior to assignment" (East Baltimore) | R (drives cancellations) |
| AS-23 peak definition | **partly contradicted** | Whole night, trigger-based; "Fri–Sat only" dropped | Lyft in April on all weekdays; "peak service hours" undefined | R |
| AS-24 phone bookings | uncertain | Same as app | No data | W |
| AS-25 hour meaning | **contradicted-leaning** (pickup hour) | Request hour as default, completion-hour as variant | 2 am bar ≈0 vs expected 150–260 | W for Lyft policy, but R for demand timing |

---

## G. Candidate angles: core / sensitivity / deferred

| Angle | Class | One-line reason (tied to "Which Lyft transfer strategies improve rider outcomes, when, at what cost") |
|---|---|---|
| Demand timing and spatial bursts | **core** | A transfer rule only matters when demand bursts exceed supply; April hourly counts are completed-only and supply-limited, so burst structure must be a scenario factor |
| Idle repositioning | deferred | Not documented for TransLoc OnDemand; a separate algorithm lever, not Lyft policy |
| Reassignment stability and ETA changes near pickup | sensitivity (promote to core if ETA-driven cancellation is modelled) | It sets who is "pending too long" and when riders cancel; affects rider outcomes beyond waits |
| Cancellation, no-show, rebooking | **core** (cancellation/rebooking); sensitivity (no-show) | Canceled is 47% of requests and mixes Lyft transfers with rider behaviour; the Lyft rule acts on the same population |
| Lyft availability and pickup uncertainty at peaks | **core** | The benefit of a transfer is the gap between van and Lyft wait; both are uncertain and Lyft supply may fall exactly when it is needed |
| Dispatcher delay, transfer capacity, consent | **core** | These are the operating-policy knobs and the resource cost (dispatcher attention, Lyft spend) |
| Fleet changes, breaks, shift ends, after-close completion | **core** (fleet-by-hour level); sensitivity (breaks, after-close tail) | Utilization sets how often a Lyft trigger fires; the 2 am tail is a small share of rides |
| Travel-time uncertainty, dwell, snapping | sensitivity (travel/dwell); deferred (snapping) | Shifts both van and Lyft waits similarly; unlikely to reorder policies |
| Tail outcomes and equity (location, party size) | **core** (as outcome metrics) | Policy effects are in the P90/P95 and in who is eligible (party ≥5 never Lyft; edge locations wait longest per JHU FAQ) |
| Optimization latency / time budget overrun | deferred | 2022 JHU "technical issues from growth" is the only hint; no data; engine speed is a software problem |

---

## H. Calibration limits of the April aggregates

What they **can** constrain (loosely): monthly Completed (~24.1k) and Lyft rider share (24.5%, 10–46% by day); the hourly shape of completed rides; wait and ride quantiles (P10/median/P90, daily) for picked-up riders; Canceled share (~47%); No-show (~4.7%); Denied≈0.

What they **cannot**:
1. **Cancellation-wait link is aggregate and not causal.** Day-level correlation (Apr 17 spike) can come from a common cause (a congested night produces both long waits and Lyft hand-offs and rider cancellations). Penn's reported effect (stops reduce waits and cancellations) is not evidence for Hopkins. The "0.55 Lyft riders per extra cancellation" slope is a regression across 30 days, dominated by one day.
2. **Wait and ride quantiles are survivor-selected** (completed only). Riders moved to Lyft, cancelled or no-show are excluded, so the baseline is understated at the tail, and the "target breach" rate cannot be computed.
3. **Maps count completed rides only** (24,056 origins). Where cancelled demand originates is unobserved; cluster centres have ~100 m uncertainty. No O-D pairs.
4. **Mixed-service vehicle counts** (p06) do not identify Homewood supply (Section E). Rides per van-hour is thus a range.
5. **Lyft vs cancellations** link (r = 0.88) is a day-level correlation; the status mapping of a transfer is unverified, and whether Completed includes Lyft rides is unstated (p07). The "Lyft ≈ 1/3 of Canceled" depends on assumed Lyft party size.
6. **No hourly Lyft or cancellation data.** Peak-hour behaviour of the Lyft rule cannot be fitted; only monthly/daily moments can.
7. **Hour semantics** (AS-25): 2 am bar ≈ 0 although requests are honoured to 2:00. Under pickup-hour about 150–260 rides (≈ 52 rides/day in the 1 am hour × share still waiting at 2:00 × 30 days) should land at 2 am; the extraction says ≤29. Check p09's 2 am bar directly before using hourly counts as pickup-time targets.
8. **29 vs 30 days** between p06 and the other charts; April 30 contributes only part of the after-midnight service.
9. **One month, one term, one anomaly (Apr 17).** No seasonality, breaks, or weather.
10. **Survey and press data are anecdotes** (the Oct 2025 survey has ~6 respondents for the Lyft question).

---

## Threats to validity (short list)

1. **Baseline realism:** if the true engine has weaker reassignment or different objective weights, a policy that "helps" in our T-baseline may not in practice (AS-02/03).
2. **Trigger mis-specification:** coding Lyft transfer on projected ETA rather than elapsed unassigned time (AS-06, East Baltimore FAQ).
3. **Calibration identifiability:** fleet (AS-14), patience (AS-09), Lyft share of Canceled (AS-10) trade off against each other; several parameter sets reproduce the same aggregates. Report the identified set, not a point.
4. **Survivor bias** in waits and ride times; **hour-semantics** mismatch (AS-25).
5. **Scope boundary:** Peabody in or out changes the distance distribution, depots and what fraction of the 24k rides is "in scope".
6. **Model-of-Lyft realism:** unlimited, unpooled, 3–10 min arrival is the optimistic corner. Policies that route more riders to Lyft look better exactly when Lyft capacity is assumed infinite.
7. **Targets treated as truth:** the 2024 change from 10→15 shows they move. Results scored against 15/20 may reverse against 10/20.
8. **Citing marketing as fact:** TransLoc's "hard ceiling" blog; the "globally optimal" claim in the 2016 post; JHU's "everyone within 20 minutes".
9. **Old evidence presented as current** (2016 engine, 2018 Lyft rules and vans, 2018 Fri–Sat-only).
10. **Single-month overfit** and day-level correlation read as mechanism.
11. **Algorithm vs policy conflation:** results that change both the dispatch engine and the Lyft rule cannot be attributed. Vary them in separate factors.

---

## Source table

| # | Source | URL | Date read / date of source | What I actually read |
|---|---|---|---|---|
| 1 | TransLoc TechLog, Ridesharing Algorithms in TransLoc OnDemand (M. Fogleman) | web.archive.org/web/20180428193225/https://techlog.transloc.com/ridesharing-algorithms-in-transloc-ondemand-7acfeddbfe1f | Archived 28 Apr 2018; first capture 11 Sep 2016 | Full text (repo extract) |
| 2 | JHU Shuttle Services (jhfre.jhu.edu), captures 26 Aug 2023, 20 Apr 2024, 14 Jan 2025, 6 Oct 2025, 30 Apr 2026, 22 Jul 2026; four more 2023–24 captures for the 10/20/15 parameter | web.archive.org/web/\<ts\>id_/https://jhfre.jhu.edu/ts/transportation/shuttle-services/ | Read 12 Oct 2026 | Full text of 22 Jul 2026 (repo extract); key-line comparison of the others |
| 3 | JHU Night Ride (ts.jhu.edu) | web.archive.org/web/20230419220530/https://ts.jhu.edu/Shuttles/Night_Ride/index.html | Apr 2023 | Full text |
| 4 | Hub: Lyft partnership (D. O'Shea) | hub.jhu.edu/2018/01/26/blue-jay-shuttle-lyft-night-ride/ (archive 2019) | 26 Jan 2018 | Full text |
| 5 | Hub: evening routes and Night Ride changes | hub.jhu.edu/announcements/2019/08/22/shuttle-evening-routes-night-ride-changes/ | 22 Aug 2019 | Full text |
| 6 | Hub: Peabody service reminder | hub.jhu.edu/announcements/2021/12/13/night-ride-service-reminder-last-day-for-fall-2021-peabody-service-is-saturday-december-18th/ (archive) | 13 Dec 2021 | Relevant paragraph |
| 7 | JHU Student Affairs "Safety and Transportation Presentation" (J. Jackson) | studentaffairs.jhu.edu/stfe/wp-content/uploads/sites/4/2025/06/Safety-and-Transportation-Presentation.pdf | Uploaded Jun 2025 (URL path) | Night Ride slide text |
| 8 | News-Letter, Students critique transportation changes (M. Green) | jhunewsletter.com/article/2022/09/students-critique-the-changes-to-the-university-transportation-services | 27 Sep 2022 | Summary from fetch tool |
| 9 | News-Letter survey (M. Saeed) | jhunewsletter.com/article/2025/10/n-l-survey-highlights-student-opinions-on-university-transportation-quality-efficiency-and-safety | 9 Oct 2025 | Summary from fetch tool |
| 10 | News-Letter, Baltimore transit 101 (H. Serringer) | jhunewsletter.com/article/2026/08/baltimore-transit-101-a-guide-to-going-carless-in-charm-city | 23 Aug 2026 | Full relevant paragraph (repo extract) |
| 11 | TransLoc blog, Johns Hopkins' layered campus transit | transloc.com/blog/what-a-student-newspapers-transit-guide-reveals-about-layered-campus-mobility/ | 2 Sep 2026 | Summary from fetch tool ("hard ceiling" sentence) |
| 12 | TransLoc OnDemand Driver, App Store version history | apps.apple.com/us/app/transloc-ondemand-driver/id1049416262 | to v1008.9.4, 16 Dec 2024 | Release notes |
| 13 | TransLoc blog, Solving Dispatcher Challenges | transloc.com/blog/solving-dispatcher-challenges-through-technology/ | 6 Apr 2022 | Summary from fetch tool |
| 14 | Metro Magazine, TransLoc MicroTransit Simulator | metro-magazine.com/10033809/transloc-deploys-microtransit-simulator | 3 Aug 2017 | Text |
| 15 | SIMPO / Rides MTD Microtransit Study 2020 | repo `docs/evidence/context/transloc_sources/simpo.txt` | 2020 | Simulation section |
| 16 | Google Patents (assignee TransLoc; US 8,510,043 B1; US 8,781,726 B2) | patents.google.com | Query 12 Oct 2026 | Result list and metadata only |
| 17 | April 2026 evidence briefs p06, p07, p09, p10, p11, p12, p02-p05; `data/processed/map_clusters.csv`, `obs_p09`, `obs_p06` | repo | Apr 2026 data | Read; bubble shares computed by me |
| 18 | JHU `covidinfo.jhu.edu` transportation page | covidinfo.jhu.edu/messages-and-announcements/transportation/ | n/d | **Blocked**; only a search snippet (10-min Lyft rule) |
| 19 | Vanderbilt/CARTA MoD paper | par.nsf.gov/servlets/purl/10466140 | 2023 | Title, abstract (irrelevant to TransLoc) |

**Not re-verified in this note:** News-Letter Feb 2018 (5+ riders always van; 14-seat vans), the News-Letter 2018 "Lyft partnership" quote, and every peer-campus row in §5 of the project doc.
