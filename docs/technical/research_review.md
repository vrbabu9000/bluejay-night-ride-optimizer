# Critical review of the research direction (v1.0, 12 Oct 2026)

**Status:** for team review. *21 Oct 2026: a few lines are annotated in place (D-39, D-45, D-49); the text is otherwise unchanged.* It reviews `transloc_operations.md` (v1.0, 2 Oct) and the Phase 3 v2 direction before the scenarios are finalised. It changes no data and no code.

**What it draws on:**
- three research notes, written in parallel by separate agents and checked by the main session:
  - `research_notes/math_literature.md` (formulation and literature; 37 sources);
  - `research_notes/operations_validity.md` (Homewood operations, the assumption audit, validity);
  - `research_notes/compute_feasibility.md` (computing, solvers, reproducibility);
- the main session's own checks, marked **[checked]**.

**Companion documents:** `model_design.md` (mathematics and architecture), `compute_feasibility.md` (PC plan) and the draft `scenario_spec.md`.

**Evidence labels:** as in `transloc_operations.md` (JHU, VENDOR, PRESS, PEER, DATA, INFERRED, UNKNOWN), plus HYPOTHESIS for untested ideas.

---

## 1. What exists and what is only proposed
| Component | State (12 Oct) |
|---|---|
| Digitized April evidence; insights T1–T10 | **Implemented** (Phases 1–2) |
| Locations, zones, gravity × IPF demand model, sampler with per-component seeds and content hashes, 32 tests | **Implemented** (Phase 3 v1, `src/scenario/`) |
| Ladder S0–L, 330-scenario grid, `preregistration.md`, `scenario_contract.md` | Implemented, then **paused** on 2 Oct (not deleted). They assume 5 vans/30 requests, 4 seats, hard 20/25 limits and no Lyft |
| Local OSRM (`infra/osrm/`), travel-time matrix v2, route shapes, snap distances | **Implemented** (2 Oct). Simulations need only the matrix file, not the server |
| Event simulator, dispatchers, Lyft module, rider behaviour, evaluation | **Not implemented.** Proposed in `model_design.md` (Phase 4, needs separate approval) |
| Scenario definition v2 | **Draft** (`scenario_spec.md` v0.1, this review) |

---

## 2. Assessing the framing statement
> "TransLoc already reassigns rides across the whole fleet every two minutes, so greedy versus a smarter dispatcher would be a straw man. A fairer baseline is TransLoc-like…"

### 2.1 The evidence behind it
**Source:** a post on TransLoc's engineering blog by Michael Fogleman. The page shows no date. The Internet Archive's first capture is **11 Sep 2016**, and the text mentions "six universities" and "60,000 passengers since August [2015]", which places it in early to mid 2016. [checked: snapshot text; agent: capture list]

**What the post actually says (VENDOR, 2016):**
- automatic dispatch;
- inputs are vehicles (location, load, capacity) and rides (O/D, party size, desired time, *candidate vehicles*);
- simulated annealing over vehicle assignment and stop order;
- a score made of wait, ride time and mileage, with weights "not necessarily linear";
- the solver runs **on a new ride, a cancellation, or a driver no-show, and every two minutes**;
- it claims the schedule is "globally optimal". That is a marketing claim; annealing gives no such guarantee.

**What it does not say:**
- It never says that **an assigned ride can be moved to another van**. That is our inference: each solve re-plans "the entire system", and its mutations change vehicle assignments.
- Nothing about hard wait or ride limits.
- Nothing about drivers accepting or declining.

**Newer primary evidence:** none found for 2018–2026. There is no TransLoc dispatch patent and no current help documentation. Driver-app release notes to Dec 2024 contain no accept or decline feature. [agent, operations note §A]

Two newer facts do exist:
- JHU pages (2023–2026) say dispatchers **review pending trips**, and that an ETA "almost always changes prior to assignment". This is East Baltimore wording.
- The driver app has had a configurable **wait timer since 2021**.

A ride can therefore sit **pending and unassigned**, so assignment is not always instantaneous.

**Verdict:** the 2-minute re-plan with reassignment is the **best-documented historical behaviour of the vendor's product**. It is **not confirmed current Hopkins behaviour**. Hopkins' settings (weights, candidate rules, dispatcher overrides) are unknown.

### 2.2 Why it is still a reasonable modelling basis
1. It is the only primary technical description, and it comes from the vendor's own engineer.
2. Nothing newer contradicts it, and the 2023–2026 rider complaints about changing ETAs fit re-planning.
3. It describes the problem class (dynamic dial-a-ride, re-solved on events plus a periodic tick), which the literature treats as standard. Re-implementing that class does not require the vendor's exact code.
4. **The consequential alternatives can be tested instead of assumed.** No reassignment, a slower re-plan and different weights all become variants of the baseline (§5, AS-02/AS-03).

### 2.3 Straw man: what it means here
A **straw man baseline** is weaker than what is really used, so that beating it proves nothing.
- Presenting greedy "insert and never move" as Hopkins' status quo would be a straw man, if Hopkins actually runs a re-planning engine.
- Any "improvement" over greedy would then mostly measure the gap between greedy and re-planning, which TransLoc already captures.

### 2.4 Why greedy vs MILP is still informative
- **It brackets the value of coordination in our simulated world.** Greedy is a floor; an epoch-exact MILP is a per-decision ceiling on small instances. Where the bracket is narrow, the choice of dispatch algorithm barely matters, and **any Lyft-rule conclusion is then robust to not knowing TransLoc's algorithm.** That is the main reason to keep it.
- **It shows when coordination matters.** The literature finds greedy close to optimal at low load and far from it at high load. Bertsimas, Jaillet & Martin 2019, full text read by the agent, is a no-pooling, advance-information setting, so this transfers only as a qualitative expectation.
- **It tests our heuristic.** If the TransLoc-like heuristic ties the exact MILP on small instances, the baseline is credible.

### 2.5 What such comparisons cannot establish
1. That any method **beats TransLoc**. Our "TransLoc-like" player is an approximation of a ~2016 description with unknown weights.
2. That an epoch-optimal decision is **optimal over the night**. Future requests are unknown, and re-planning is myopic.
3. Real Hopkins magnitudes. The data are aggregates; several mechanisms fit the same aggregates.
4. Dollar savings. There are no Lyft prices.

### 2.6 What we can defensibly claim
> "In a simulation of the Homewood Night Ride whose dispatcher has the structure TransLoc published (event-plus-periodic re-planning with reassignment and a convex waiting penalty), and whose outputs fall within April 2026's observed ranges, Lyft transfer rule X changes rider outcome Y by Z (paired, N nights, confidence interval) using K Lyft bookings and V van-km *[wording 21 Oct: resource use, not cost; D-45]*, and this ranking holds across dispatcher variants D and assumption ranges S."

The claim is **relative, conditional and robustness-qualified**. It is about **operating policies under a realistic dispatcher**, not about beating the vendor's algorithm.

### 2.7 Revised framing (recommended)
> "Hopkins' dispatching is automated. The best public description (TransLoc, 2016) is a re-planning engine, so our baseline re-plans too. Whether rides are reassigned, how often, and with what priorities are uncertain, so they become baseline variants. The question we answer is not 'can a better algorithm beat TransLoc?' but **'which Lyft transfer rule should Homewood's dispatchers use, and when does it matter?'** — an operating decision Hopkins controls today."

---

## 3. Research questions
**Algorithm vs policy:**
- Improving an **algorithm** means a better solver for the same goal: dispatch, with the same rules.
- Improving an **operating policy** means changing a rule Hopkins controls: the Lyft trigger, targets, fleet by hour.

A comparison that changes both at once cannot attribute the effect.

**Primary question (accepted direction; wording refined):**
> **Which dispatcher-initiated Lyft transfer rules improve Homewood rider outcomes, under which demand and fleet conditions, and at what resource use (Lyft bookings, van-km; no money, D-45), when the van dispatcher is held fixed at a TransLoc-like re-planning baseline?**

**Supporting questions:**
- **SQ1, robustness to the dispatcher:** does the ranking of Lyft rules hold under the dispatcher variants (no reassignment, a slower re-plan, greedy, and small-instance exact)?
- **SQ2, conditions:** how do demand pressure, bursts and vehicle availability over the night change the value of each rule?
- **SQ3, priorities:** how does the wait-vs-ride weighting interact with the rule? It changes who is "late" and when.
- **SQ4, behavioural sensitivity:** do the conclusions survive plausible ranges of the parameters below?
  - dispatcher lag, consent and capacity;
  - Lyft pickup time;
  - rider patience.

**Explicitly excluded:**
- East Baltimore;
- designated-stop consolidation;
- fleet purchase decisions, dollar budgets and Lyft prices (we report resource use as counts only; superseded wording 21 Oct, D-45: no illustrative prices either);
- claims about beating TransLoc's algorithm;
- idle-vehicle repositioning (deferred);
- events forecasting (Approach 2);
- physical-safety outcomes (we measure service-quality proxies);
- real-time deployment.

---

## 4. Service scope
### 4.1 Homewood only, door-to-door
- **Homewood only.** East Baltimore demand, policies and targets are excluded.
- **Door-to-door.** Pickups and drop-offs are at the requested curb. **The digitized hotspots are a demand-generation device**: each is a point with April counts that stands for many nearby addresses. They are **not mandatory pickup stops.**
- **The approximation is documented.** Using hotspot points as request locations lumps nearby addresses together. The snap file records the road point that stands for each hotspot (median 11 m from the bubble; one at 95 m).

### 4.2 The service boundary, and Peabody — **decision needed before generating data**

| Evidence | Grade |
|---|---|
| Apr 2023 JHU page: in the Fall and Spring terms, Homewood Night Ride is combined with the Peabody Escort Van area, roughly 20th St / Guilford Ave–South St / Pratt St / Howard St | JHU 2023 |
| Aug 2023–Jul 2026 pages (six captures): only "proximate to the Homewood campus"; **no Peabody sentence** | JHU (absence) |
| Sep 2022: Peabody re-merged; Dec 2021: Peabody zone off over the break | PRESS / JHU |
| "Both trip ends must be inside the zone": Jan 2018 Hub article (about Lyft rides); the 2023/2026 "to and from locations within the service area" wording is consistent with it | JHU 2018; INFERENCE 2026 |
| **April 2026 "HW Night Ride" maps contain Peabody and downtown bubbles** | DATA |

**Correction to `transloc_operations.md` v1.0.** It cited the 2026 page for the Peabody merger. The merger sentence is only on the 2023 page.

**How much demand is at stake** depends on the definition [checked]:
- zones south of about 20th St (Mount Vernon, Midtown/Penn Station, Station North, Inner Harbor, Downtown) hold **~20% of April's origins and destinations**;
- under our gravity model, **~34% of trips touch them** (6% with both ends there; this split is an ASSUMED model consequence);
- the operations agent finds 6.6% of origins in the single Peabody bubble and 7–16% of rides near or south of Mount Vernon.

**Options:**
1. **Homewood + Peabody, as April was operated.** Consistent with the dashboard we calibrate to. **(Recommended.)**
2. Homewood core only. Removes 7–20% of demand, so April totals must be rescaled; the calibration becomes weaker.
3. Both, as a scenario factor. Costs a doubled design.

**Why it matters for Lyft.** Long Homewood–Peabody trips set the minimum feasible ride cap. They are also the natural candidates for Lyft: isolated and long.

### 4.3 Service targets: three layers, kept separate
| Layer | Content | Status |
|---|---|---|
| **Published target** | Pickup within **15 min** of request; ride **≤ 20 min**; "during busy times (rush hours), shuttles may take up to **20 min** to arrive"; dispatchers send a free Lyft "if a ride cannot be provided in a timely manner" | JHU, on the page since Apr 2024. Aug 2023–Mar 2024 it read **10 / 20 / 15**. **The targets were loosened in 2024**, which is evidence they are policy goals, not software limits |
| **Software constraint** | Unknown. No source says the engine enforces 15/20. TransLoc's 2026 blog calls the 15-minute Lyft rule a "hard ceiling"; it paraphrases a student column, so it is not evidence | UNKNOWN |
| **Our modelling choice (proposed)** | 15/20 are **reporting thresholds** and break-points of the waiting penalty. The ride limit is a **hard-but-elastic guardrail** in dispatch, set above 20 min (model_design §4). The busy-period allowance (20 min) is reported as a second threshold, not a different rule | PROPOSED |

**Caveats on the targets:**
- **Which service the 15/20 belongs to.** The block sits in the page's general "What to Expect" Blue Jay Shuttle section. The East Baltimore block gives its own figures, and its FAQ still shows 10/15 in Oct 2025. Attributing 15/20 to Homewood is therefore the most plausible reading (INFERRED), not an explicit statement.
- **Breaches show soft targets, not how the software works.** April's P90 wait and ride exceed the targets. That shows the targets are not met. It does not show how the software treats them: such breaches are also consistent with a hard limit relaxed under infeasibility, or with the Lyft rule acting as the enforcement.
- **The April quantiles are biased low.** They are computed on **completed rides only**. Riders who cancelled or went to Lyft are missing, so the tails are understated.

### 4.4 Vans by hour vs rides per van-hour
| Measure | Definition | Role |
|---|---|---|
| **Vehicle availability over the night** ("vans by hour") | How many vans are logged in and dispatchable at each time, e.g. 27.6 → 4.5 averaged by clock hour | **Scenario input** (supply) |
| **Rides per van-hour** | Completed rides in an hour ÷ vans available in that hour | **Outcome / calibration check** (productivity). It depends on demand, dispatch and Lyft transfers |

**The vehicle chart counts "All services".** It may mix services; which ones is unknown:
- It shows **no vehicles from 3 am to 5 pm**, although East Baltimore's 5–9 am service also runs on TransLoc. So "All services" is not literally every service.
- The v1.0 inference "~22 Homewood vans at 6 pm (East Baltimore leaving at midnight)" is therefore **downgraded to HYPOTHESIS**.
- **Excluding East Baltimore from the simulation does not fix this.** The measurement is still ambiguous.

**Proposed treatment:**
- Homewood availability at 6 pm is an **uncertain range of about 18–27.6 vans** with the observed taper shape;
- the level is **calibrated** so the baseline reproduces April's wait quantiles and Lyft share, and stays a sensitivity factor.

---

## 5. Audit of assumptions AS-01…AS-25 (`transloc_operations.md` §9)
**Classes:** supported / outdated / uncertain / contradicted / needs-sensitivity.
**Rev?** = could **reverse** a Lyft-policy conclusion, so it must be varied in the main design. Otherwise it can wait.
Built from the operations note §F and the literature note §7, reconciled by the main session.

| ID | Topic | Status | Recommended default (reason) | Rev? |
|---|---|---|---|---|
| AS-01 | Assignment | Supported (automatic); uncertain (driver response) | Automatic central assignment. A pending-unassigned state is allowed (JHU FAQ, USC). Driver delay/decline is a **sensitivity variant**, not a level | Yes, through what the dispatcher sees |
| AS-02 | Re-plan cadence, reassignment | Outdated risk (2016 only); needs sensitivity | Event + 120 s; reassignment of unpicked, uncommitted rides allowed; commit at "next stop". Variants: none / 300 s | **Yes** |
| AS-03 | Objective | Uncertain → **decide now** (literature note R-3) | **Weighted** convex wait penalty > ride > miles, with an elastic ride guardrail; lexicographic as a named variant (model_design §4) | **Yes** |
| AS-04 | Engine method | Uncertain | Insertion + local search on the same objective as the exact model ("T = C's model with a heuristic solver") | No |
| AS-05 | Targets soft | Needs sensitivity (v1.0's "supported" overstated) | Reporting thresholds; hard-cap variant | **Yes** (a hard cap acts like a built-in trigger) |
| AS-06 | Lyft trigger | Uncertain; **the core factor** | **Elapsed time pending/unassigned** is the closest documented form (East Baltimore FAQ: "within ten minutes without a van assigned"; HYPOTHESIS for Homewood). It is one of the compared rules (scenario_spec §6), not the default | **Yes** |
| AS-07 | Dispatcher capacity | Uncertain | Unlimited in the base; capacity and lag stress variants | **Yes** at high transfer volume |
| AS-08 | Lyft supply and wait | Uncertain; no data | Pickup delay with median ~8 min and a tail to 20 (ASSUMED), unpooled. **Peak-scarcity variant is required**: unlimited Lyft favours aggressive rules | **Yes** |
| AS-09 | Patience | Needs sensitivity | Abandonment hazard rising with time waited (and the shown ETA, as a variant). Calibrated so rider cancellations are about two thirds of "Canceled" *[21 Oct: superseded by D-39, a provisional 50–75% sensitivity range, not exhaustive (D-49)]* | **Yes** |
| AS-10 | What "Canceled" contains | Uncertain | Lyft transfers ≈ 1/3 (range 23–46%); variant with transfers not in "Canceled" | Yes (calibration) |
| AS-11 | Rebooking | Uncertain | None in the base; variant 0.2–0.5 with a delay | Moderate |
| AS-12 | No-show | Supported (rate) | 4.7% of requests; the van waits 3 min | No |
| AS-13 | Denial | Supported | None inside the area and hours | No |
| AS-14 | Fleet by hour | **Uncertain, partly contradicted** | Calibrated range 18–27.6 at 6 pm with the observed taper; not "22" as fact | **Yes** |
| AS-15 | Capacity 14 | Uncertain (2018) | 10–14 seats; check whether it binds (booking cap 5, mean load ~1.8) | No |
| AS-16 | Party size | Supported | Mean 1.39, max 5. ~~Party ≥ 5 is never sent to Lyft (Lyft seats 4)~~ **Corrected 21 Oct (D-33): parties of 5 go by Lyft XL, kept together** | No (but it defines the XL class) |
| AS-17 | Dwell | Uncertain | 30 s per stop + the 3-min no-show wait | No |
| AS-18 | Curb-to-curb | Supported; stops out of scope | Curb-to-curb at hotspot points | No |
| AS-19 | Walk-ups | Uncertain | None | No |
| AS-20 | Service area | **Needs a decision** (Peabody, §4.2) | Homewood + Peabody (recommended) | **Yes** |
| AS-21 | Travel times | Needs sensitivity | OSRM free-flow × multiplier in [1.0, 1.5], calibrated | Moderate |
| AS-22 | ETA shown to the rider | Uncertain | Dispatcher plan ETA plus noise; matters if cancellations depend on the shown ETA | **Yes** for predicted-wait rules |
| AS-23 | Peak definition | **Partly contradicted** (Lyft riders on every weekday in April) | Whole night, trigger-based; "Fri–Sat only" dropped | Yes |
| AS-24 | Phone bookings | Uncertain | Same as app bookings | No |
| AS-25 | Hourly chart = pickup hour | **Contradicted-leaning** [checked: the 2 am bar is 0–29 rides for the month, although requests are honoured to 2 am] | **Request hour** as the default reading; completion hour as a variant | Matters for demand timing |

**The uncertainties that can reverse conclusions** are the ones that move the *gap between van wait and Lyft wait*, or *which riders are pending when a rule fires*:
- Lyft pickup time and supply at peaks (AS-08);
- dispatcher lag and capacity (AS-06/07);
- Homewood fleet level (AS-14);
- patience and ETA behaviour (AS-09/22);
- re-plan and reassignment (AS-02);
- the objective weighting (AS-03);
- the Peabody boundary (AS-20).

These go in the main design or a mandatory robustness block. The rest can wait or take one-at-a-time sensitivity runs.

---

## 6. Missing angles: classified
| Candidate | Class | Why (tied to the Lyft question) |
|---|---|---|
| Demand timing and spatial imbalance (bursts) | **Core** (scenario factor) | Transfer rules matter only when demand outruns supply locally; April's hourly counts are completed-only and supply-limited |
| Idle-vehicle repositioning | **Deferred** | Not documented for TransLoc; an algorithm lever, not a Lyft policy |
| Reassignment stability, ETA churn, commitments near pickup | **Core** (engine rule + metric) | A predicted-wait rule acts on ETAs that churn; commit rules decide what can be transferred. Report ETA churn |
| Cancellation, no-show, rebooking | **Core** (cancellation, no-show); sensitivity (rebooking) | The Lyft rule acts on the same pending population that cancels |
| Lyft availability and pickup uncertainty at peaks | **Core** | The benefit of a transfer is the gap between van and Lyft wait; Lyft may be scarce exactly at peaks |
| Dispatcher delay, transfer capacity, consent | **Core** (lag); sensitivity (capacity, consent) | These are the policy's operating knobs |
| Fleet changes, breaks, shift ends, after-close completion | **Core** (availability profile, shift ends); sensitivity (breaks); reported (after-close tail) | Utilisation sets how often a trigger fires; a van leaving mid-plan strands assignments |
| Travel-time uncertainty, dwell, snapping | Sensitivity (travel multiplier, dwell); documented (snapping) | Shifts van and Lyft waits similarly; unlikely to reorder rules |
| Tail outcomes, equity across locations and party sizes | **Core metrics** | Policy effects live in P90/P95; parties of 5 need a Lyft XL (D-33, 21 Oct); edge locations wait longest |
| Optimization latency and budget overrun | **Engine rule now; measurement deferred** | Rule: if a solve exceeds its budget, keep the last plan and insert new requests greedily, and log it. Matters little at our sizes |

**Omissions that could flip the Lyft conclusions:**
1. Lyft scarcity at peaks.
2. Dispatcher lag.
3. Patience depending on the shown ETA.
4. The fleet level.
5. ETA churn. It weakens the predicted-wait rules if ETAs are noisy.

---

## 7. Calibration: what the April data can and cannot constrain
**Can constrain (loosely):**
- monthly completed rides (~24.1k);
- the Lyft rider share (24.5%; 10–46% by day);
- the hourly *shape* of completed rides;
- daily wait and ride quantiles for picked-up riders;
- the "Canceled" share (~47%), no-shows (~4.7%) and "Denied" (≈0).

**Cannot:**
- **Individual cancellation behaviour or causality.** The wait–cancellation link is day-level and correlational, and Apr 17 dominates it.
- **Homewood supply.** The vehicle counts are mixed-service.
- **Where cancelled demand comes from.** The maps count completed rides only.
- **How a Lyft transfer is recorded.** Nor whether "Completed" includes Lyft.
- **Hourly Lyft or cancellation patterns.** There are none.
- **True wait tails.** The quantiles are survivor-biased.

**Identifiability.** Fleet level, patience and the Lyft share of "Canceled" trade off against one another. Several parameter sets reproduce the same aggregates. **Calibration should report the set of parameter combinations that pass, not a single point. Each Lyft-policy result is then re-run across that set.**

---

## 8. Threats to validity (short)
1. **Baseline realism** (AS-02/03): vary it (SQ1).
2. **Trigger misspecification** (elapsed vs predicted): both are compared rules.
3. **Identifiability:** report the identified set.
4. **Survivor-biased targets:** model the full request population.
5. **Scope boundary** (Peabody).
6. **Optimistic Lyft:** add a scarcity variant.
7. **Moving targets** (10 → 15 in 2024): report at both 10 and 15 min.
8. **Marketing cited as fact:** fixed below.
9. **Old evidence as current:** 2016 engine; 2018 vans and rules.
10. **Single-month overfit.**
11. **Algorithm–policy conflation:** separate factors.

## 9. Corrections applied to `transloc_operations.md` (v1.1)
Recorded in that document's review block; the v1.0 text is archived at `archive/transloc_operations_v1.0_2026-10-02.md`.
1. **Peabody:** cited to the 2023 page, not 2026.
2. **Reassignment:** an inference from the 2016 post, not stated in it.
3. **The 22-van estimate:** downgraded to hypothesis.
4. **Targets:** their 2024 history added.
5. **"Hard ceiling":** the TransLoc blog claim marked as unsupported.
6. **Peak definition:** "Fri–Sat only" marked as contradicted.
7. **Hourly chart:** AS-25 reading flagged.
8. **The 2016 post:** dated as "on or before 11 Sep 2016".
