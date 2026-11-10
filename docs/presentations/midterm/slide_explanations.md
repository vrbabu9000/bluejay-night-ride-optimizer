# Midterm presentation: slide-by-slide explanation (draft v0.2, 22 Oct 2026)

This document teaches the reasoning behind each slide of `BlueJay_Midterm_draft.pptx`, in more depth than the spoken script. It is written for a teammate who must answer questions about any slide.

For each slide it covers:
- the slide's purpose;
- what a listener needs to know first;
- the evidence and its source;
- the derivations behind the numbers and figures;
- the assumptions;
- how to interpret the slide;
- the limitations.

**The three kinds of statement.** Every number in the talk is one of three kinds, and the slides keep them apart:
- **observed:** read from the April 2026 dashboard;
- **assumed:** our modelling choice, labelled as such;
- **simulated:** produced by our simulator on synthetic inputs.

A fourth kind, **designed**, marks the small evenings we built on purpose so that their answers could be checked by hand.

**Sources.** The authoritative sources are:
- the decision log (`docs/technical/decision_log.md`; entries D-xx);
- the build contract (`scenario_spec.md` v0.8);
- the mathematical design (`model_design.md` v0.5);
- the methodology (`scenario_methodology.md` v1.4);
- the saved simulation outputs under `outputs/sim/`.

---

## How the slides connect

```
1 service + proposal ──► 2 why the question changed ──► 3 build an evening from aggregates
                                                          │
                                                          ▼
                                       4 assumptions that the aggregates cannot fix
                                                          │
                   ┌──────────────────────────────────────┘
                   ▼
5 the planning loop ──► 6 the objective inside it ──► 7 a flaw in that objective, tested and fixed
                   │
                   ▼
8 verification ──► 9 thirty-night pilot: what happened ──► 10 service vs Lyft trade-off
                                                             │
                                                             ▼
                              11 leader–follower: a reading, not yet a model ──► 12 limits, next, contribution
```

The narrative logic runs in four stages:
1. **Data limited the question.** The aggregate data limited what we could ask (slides 1–2).
2. **The limits shaped the scenarios.** The same limits decided how the scenarios were built, and which parts had to be assumed (slides 3–4).
3. **A decision method on synthetic nights.** Those scenarios feed a decision method whose behaviour we can explain and verify (slides 5–8).
4. **Descriptive results.** Only then do we look at results, and we read them descriptively (slides 9–10). The professor's two framings come in at slides 10 and 11, followed by an honest close (slide 12).

---

## Slide 1: the service, and what we proposed in September

**Purpose.** Introduce the service in the proposal's own words, so the class recognizes the project, and state plainly that the plan changed.

**Prerequisites.** None.

**Evidence.**
- The April 2026 JHU/TransLoc dashboard shows 44,374 riders in the month, counting van and Lyft riders together, of whom 24.5% rode Lyft (`transloc_operations.md`, April data row).
- These are *riders* (passengers), not requests and not trips.
- The proposal is the September deck (`docs/presentations/BlueJayNightRide_Proposal.pptx`). We did not modify it; note that the working copy shows an uncommitted change made before this work.

**Interpretation.** "About one rider in four rode Lyft" is the dashboard's rider share. It is not the share of requests or of trips transferred. Those are different denominators: a Lyft trip can carry several riders, and many requests never become trips.

**Limitations.** The dashboard does not say how Lyft trips were decided.

---

## Slide 2: how the research question changed

**Purpose.** Explain the pivot and correct outdated proposal claims, so that nothing in the talk repeats them.

**Prerequisites.** What a dispatch algorithm is: a method that decides which van serves which rider, and in what order.

**Evidence.**
- Decision log D-23 (Homewood scope), D-25 (a re-planning dispatcher in the style TransLoc describes), D-27 (Homewood plus Peabody).
- D-45: no financial modelling, because Hopkins' cost per Lyft trip is unknown, and a rider's app showing no charge only means Hopkins pays.
- D-49: the service targets, with dated sources.
- `research_review.md`: the critical review that motivated the new question.

**Derivations.**
- **"5,100 rides per hour at 6 pm."** The dashboard chart sums completed rides by clock hour over the 30 days of April. Its tooltip for 18:00 reads 5,098, our digitized value is 5,089, and either way that is about 170 completed rides in the 6 pm hour of an average evening.
- **"28 vans."** The vehicle chart is labelled "All services" and averages 27.6 vehicles on duty at 18:00, over 29 days. It is not a Homewood-only count.
- **Targets.** Archived copies of the JHU page captured between April 2024 and July 2026 state 15 / 20 / 20 minutes. The live page read on 21 Oct 2026 states 20 / 25 / 25. We keep the two distinct, and neither proves what was operating policy in April.

**The six rules (introduced on this slide).**
- **R0:** never transfer (the reference).
- **R1(10), R1(15):** transfer after 10 or 15 minutes of waiting.
- **R1u(10):** transfer after 10 minutes with no van assigned in the plan.
- **R2(15):** transfer if the predicted total wait exceeds 15 minutes.
- **R3(2):** transfer if the van is predicted to arrive later than a Lyft could (2-minute lag + 8-minute typical delay + a 2-minute margin).

They span three kinds of information: elapsed time (R1), assignment status (R1u) and the dispatcher's predictions (R2, R3).

**Interpretation.** Without trip-level records we cannot replay real nights, so comparing dispatch algorithms on synthetic nights would mostly compare our own assumptions about the fine detail of demand. A policy question works better on synthetic but carefully built nights: hold a reasonable dispatcher fixed, and change only the rule for transferring riders to Lyft. Paired replay of the same nights then isolates the effect of the rule.

**Assumptions.** The held-fixed dispatcher, C, is a reasonable stand-in for a re-planning dispatcher. It is not a reproduction of Hopkins' proprietary system (D-51).

**Limitations.** The new question does not say how the real service would respond to a rule change.

---

## Slide 3: building an evening from aggregate data

**Purpose.** Show the central method: observed, then derived, then unknown, then chosen, with two worked blocks.

**Prerequisites.**
- A *request* is one booking, possibly for several riders.
- A *completed ride* is a request a van actually delivered.

**Evidence.**
- Completed rides by hour (obs_p09).
- Vehicles on duty by hour (obs_p06).
- Statuses (obs_p07): 50,297 recorded requests, 24,095 completed, 2,359 no-shows.
- Map bubbles of pickups and drop-offs per place.
- Decisions D-35 and D-36 (volume), D-18 (trip pairing), D-49 (range).

**Derivation: how many requests.**
1. Completed rides in the 6 pm hour over 30 days: C₁₈ ≈ 5,089 (digitized; the tooltip reads 5,098). Per evening: C₁₈ / 30 ≈ 170.
2. Recorded requests per completed ride: R/C = 50,297 / 24,095 = 2.087. That gives about 355 requests in an evening's 6 pm hour.
3. Load per vehicle: ρ₁₈ = (C₁₈ / 30) × (R/C) ÷ V₁₈ = 170 × 2.087 ÷ 27.6 ≈ 12.85 requests per vehicle per hour. The same formula gives ρ₁₉ = 10.10 and ρ₂₀ = 10.71.
4. For a planned five-van evening, N_h = 5 × ρ_h = 64.25, 50.50 and 53.55. Rounding hour by hour with the largest-remainder rule: round the total, 168.3, to 168; floor each hour to 64, 50, 53; give the leftover unit to the largest fraction (0.55). The result is **64 / 50 / 54 = 168** (D-35, D-36).

**Derivation: the range.** The count is a range because two quantities are unknown.
- **Homewood's share of the vehicles.** If Homewood had 20–35% fewer vehicles than the "All services" count, each van carried more load, and the count rises to about 168 / 0.8 ≈ 210 up to 168 / 0.65 ≈ 258.
- **Rebookings.** If about 10% of recorded requests were rebookings of the same trip, it falls to about 151.

The range of about 150–260 is illustrative, not a confidence interval (D-49).

**Derivation: where trips go.** The maps give pickup totals Oₒ and drop-off totals D_d per place, never the pairs.
1. **Gravity prior.** Start from wₒ_d = Oₒ · D_d · e^(−β·tₒ_d), with tₒ_d the driving minutes and β = 0.1 per minute, so each extra minute multiplies the weight by about 0.905. Pairs under 60 s of driving are excluded.
2. **Iterative proportional fitting.** Alternately rescale rows and columns until the table reproduces both sets of April totals; the largest error is about 10⁻¹⁰.

The result matches the observed totals exactly. But it is *one* table chosen by an assumption, the gravity prior and its decay rate: every β reproduces the totals, so the data cannot choose β (trail §5).

**Assumptions.**
- Requests share the geography of completed rides, because cancelled requests' locations are unobserved.
- Within an hour, requests arrive at uniform random times.
- The same geography holds in every hour.

**Interpretation.** The 168 requests are a derived workload for a planned five-van evening, not a measurement of April demand.

**Which levels actually ran.**
- The **pilot that ran, L5**, uses two vans and 28 requests in one hour, with 40% of them in a 10-minute burst. It is a designed rehearsal level at roughly the 6 pm load per van: 14 requests per van-hour, against ρ₁₈ = 12.85.
- The **five-van evening (L6)** is designed but not yet run.

**Limitations.**
- Mixed-service vehicle counts.
- A 29-day vehicle average, which moves ρ by about ±3%.
- Unknown rebookings.
- An assumed pairing.

---

## Slide 4: assumptions that complete the evening

**Purpose.** Make visible the inputs that the dashboard cannot determine, and how each one was chosen.

**Prerequisites.**
- A distribution versus its mean.
- What "Canceled" and "No Show" mean as dashboard statuses.

**Evidence.**
- Statuses (obs_p07).
- Passengers per day (obs_p08): passengers who boarded and completed van rides.
- JHU page: Lyft is sent by a dispatcher, and a van waits up to 3 minutes at the curb.
- Decisions D-33 (XL), D-38 (group sizes), D-39 (patience), D-40/D-48 (no-shows), D-43 (Lyft service).

**Derivations.**
- **Group size.** April van passengers ÷ completed van bookings = 33,394 / 24,095 = **1.386** van passengers per completed van booking. It is a mean over *completed van* trips only.
  - Our assumed distribution is P(1, 2, 3, 4, 5) = 0.73 / 0.18 / 0.055 / 0.025 / 0.01, with mean 0.73 + 0.36 + 0.165 + 0.10 + 0.05 = 1.405.
  - The two numbers measure different things; the second is not estimated from the first.
  - In this *assumed* distribution, parties of 5 are 1% of bookings (about 1.7 per 168-request evening). The XL rule itself comes from a team correction (D-33): a transferred party of 5 goes as one XL booking.
- **"Canceled".** 50,297 − 24,095 − 2,359 = 23,843 requests (47.4%) ended "Canceled". That label mixes riders who gave up with requests the dispatcher handed to Lyft (D-39).
  - We do not know the split, so the riders' share of "Canceled" is a provisional *sensitivity range* of 50–75% (D-39), to be used in calibration; it is not established by the data. It is not exhaustive: it ignores duplicates and transfers recorded as completed.
  - Patience is a hidden personal deadline per rider, drawn from a Weibull distribution with shape 1.5 and median 18 minutes. Its scale is 18 / (ln 2)^(1/1.5) ≈ 23.0 minutes. This is a placeholder until calibration.
- **No-shows.**
  - Over all requests: 2,359 / 50,297 = 4.7%.
  - Per van arrival: 2,359 / (24,095 + 2,359) = 2,359 / 26,454 ≈ 8.9%.

  The per-arrival figure holds *only if* three things are true: "Completed" means van-completed, "No Show" is recorded only after a real van arrival, and Lyft hand-offs sit in "Canceled". The arithmetic is exact; the uncertainty is entirely in this status mapping (D-48). We use p = 8.9% per arrival, provisionally. One shared presence draw per rider means the same rider is absent or present whichever vehicle arrives.
- **Lyft.** The booking is placed 2 minutes after the transfer decision. Arrival follows after a lognormal delay with median 8 and 90th percentile 15 minutes, so σ = ln(15/8) / 1.2816 ≈ 0.49 (D-43).

**Interpretation.** These are the knobs that later results depend on most. Any result is "under these assumptions".

**Limitations.** None of patience, presence or the Lyft delay is calibrated yet.

---

## Slide 5: how the algorithm operates

**Purpose.** Explain the decision loop and the information boundary between what the dispatcher knows and what the simulator knows.

**Prerequisites.**
- *Epoch*: a moment when the dispatcher re-plans.
- *Candidate route*: an ordered list of stops for one van.

**Evidence.**
- Build contract, `scenario_spec.md` §17: event order, epochs, transfers.
- D-46, D-52, D-54, D-55.
- The transfer timeline in `outputs/sim/m2_L4_report.md`, an L4 run under rule R2(15).

**What happens in an epoch.** Epochs occur at every new request, every cancellation or no-show of a request in van planning, every van coming on or off duty, and every 2 minutes.
1. Update the observable state.
2. Generate candidate routes per van. Each candidate covers a subset of at most three new pickups, with the best order of all its stops.
3. The MILP chooses one candidate per van.
4. The Lyft rule reads each waiting request's predicted pickup. That is the plan's estimated arrival time if the request is in a van plan; otherwise a *tentative* arrival estimate computed outside the MILP.
5. Accepted transfers leave van planning at once.
6. The dispatcher re-plans exactly once; the rule is not re-evaluated in the same second.
7. Vans depart. A van commits to a stop when it departs toward it.

The planning takes zero simulated time.

**What the dispatcher sees and what stays hidden.**
- **Sees:** revealed requests (time, origin, destination, party size), van positions, riders aboard, committed stops, travel times.
- **Hidden:** each rider's patience deadline, the shared presence draw and the actual Lyft delay.

The simulator applies the hidden traits only when the corresponding event happens. So the dispatcher's predictions and the simulator's actual events can differ.

**Derivation: the transfer timeline.** Request R011 under R2(15) on L4:

| Step | Time |
|---|---|
| Request | 18:16:30 |
| At the 18:20 epoch, the plan predicts a van at | 18:35:20 (predicted total wait 18:50, over 15:00, so the rule fires) |
| Transfer decision | 18:20 |
| Booking (after the 2-min lag) | 18:22 |
| Lyft at the curb (a delay of 8 min, set by the L4 design) | 18:30 |
| Boarding, then direct ride; drop-off | 18:33:25 |

The wait counted from the original request is 13:30.

**Interpretation.** The Lyft rule is a separate policy layered on the dispatcher, which is what lets us vary it while holding the dispatcher fixed. In the R011 example, the 18 min 50 s is the dispatcher's *prediction*, while the 13 min 30 s is the simulated Lyft *outcome*. The van's actual arrival under no transfer is not observed in that run, so the example shows the mechanism, not a saving.

**Limitations.**
- The dispatcher is myopic: it plans only for requests that have arrived.
- The tentative arrival estimate of a waiting request is optimistic, because it ignores the cap on new pickups and other waiting requests.

---

## Slide 6: how the mathematics chooses a plan

**Purpose.** Show the objective and one worked choice; qualify "optimal".

**Prerequisites.** A convex function: one whose slope keeps increasing.

**Evidence.** `model_design.md` v0.5 §3–§4; D-29 (objective); D-52 (candidates, solver); the methodology's worked example (§6).

**The route score.** In points, for one candidate route:

  c = Σ q·φ(W) + 0.5 · Σ q·H + 0.1 · km  (+ Ψ for guardrail excesses no candidate can avoid)

Here q is party size, W the wait (curb arrival minus request time, in minutes) and H the ride time (drop-off minus pickup, including the 30-s boarding dwell).

**The waiting penalty φ.** Piecewise linear, with slopes 1, 2.5, 5, 10 and 20 points per minute after 0, 5, 10, 15 and 20 minutes of waiting.
- φ(5) = 5; φ(10) = 5 + 2.5×5 = 17.5; φ(15) = 17.5 + 5×5 = 42.5; φ(20) = 42.5 + 10×5 = 92.5.
- Its convexity encodes the documented TransLoc example: cutting 1 minute from a 10-minute wait matters more than cutting 2 minutes from a 5-minute wait, and φ(10) − φ(9) = 2.5 > φ(5) − φ(3) = 2.
- The ride weight β = 0.5 is below every slope of φ, so a waiting minute always outweighs a riding minute.

**The guardrail.** No candidate may create or increase a ride longer than max(25 min, 2 × direct time + 5 min).

**Derivation: the worked example** (the 30-s dwell is omitted for clarity, as in the methodology). One van; r1 (1 rider, waited 8 min) and r2 (2 riders, waited 1 min).
- **Route A** (r1 first): W1 = 12, W2 = 8, H1 = 8, H2 = 9.
  - Waiting = 1·φ(12) + 2·φ(8) = 27.5 + 2×12.5 = 52.5.
  - Riding = 0.5 × (8 + 2×9) = 13.0.
  - Driving = 1.0.
  - **Total 66.5.**
- **Route B** (r2 first): W2 = 6, W1 = 16, H1 = 5, H2 = 10.
  - Waiting = 52.5 + 2×7.5 = 67.5.
  - Riding = 0.5 × (5 + 20) = 12.5.
  - Driving = 1.0.
  - **Total 81.0.**

A wins, because in B r1's wait crosses 15 minutes, where each minute costs 10 points.

**Points and optimality.**
- **Points are not money.** They are an explicit exchange rate between priorities.
- **What "optimal" means.** The MILP picks one candidate per van so that each waiting request is served once or left waiting, minimising total points (backup B1). HiGHS proves optimality *over the candidates generated at that epoch*: every subset of up to three new pickups per van. That is not optimality over all routes, nor over the evening.

**Limitations.**
- The weights are choices (D-29).
- Optimizing one epoch at a time is not optimizing the evening.

---

## Slide 7: the pending-price weakness, tested and addressed

**Purpose.** Show the scientific loop on our own model: find a flaw, test alternatives, decide with stated reasons.

**Prerequisites.** In the MILP, a request may be left waiting ("pending") at a price.

**Evidence.**
- D-53 (discovery, update 2, approval).
- `outputs/sim/d53_experiment/d53_comparison.md`.
- Independent review `research_notes/d53_pending_price_review_2026-10-22.md`, with 29 tests.

**The three prices.**
- **Original.** A pending request r is charged b_r = q·φ(next tick − t_r), as if a van reached it at the next 2-minute tick. When vans are far away this is physically impossible, so postponing looks cheaper than any real service. The gap is largest for long waiters and large parties.
- **A.** b_r = q·φ(max(next tick, L_r) − t_r), where L_r is the earliest time any on-duty van could reach the pickup. This is a lower bound on any future service, with three exceptions: a ≤ 13-s inconsistency on 3 of 35,344 matrix pairs, vans not yet on duty, and the next-tick floor.
- **B.** The price after a chosen van's route, linearised with continuous variables. It can err in both directions: it is optimistic when several waiting riders claim the same van's free time, and pessimistic when a later epoch inserts the rider earlier.

**The M bound.** A large constant M, computed per epoch, makes every proven-optimal plan leave as few requests waiting as the candidates allow. It is valid for all three formulations, because each price lies between 0 and its maximum.

**The experiment.** On the designed L4 evening under R0 (no transfers), each formulation evolves from its own decisions:

| | Original | A | B |
|---|---|---|---|
| Wait median / 90th percentile / max (min) | 17.1 / 31.0 / 44.4 | 18.6 / 31.2 / 35.6 | 21.1 / 34.3 / 38.6 |
| Mean wait (min) | 18.8 | 18.8 | 21.8 |
| Extra variables | 0 | 0 | up to 9,828 |

In a synthetic five-van epoch, B needed about 135,000 extra variables and took 19.6 s, against 3.0 s.

**Decision (approved provisionally).** A was chosen for its meaning, its zero added size and its preservation of the request-count priority, *not* because R002 was served sooner.

**Interpretation and limitations.**
- A still under-prices postponing when the nearest van is busy.
- It does not guarantee oldest-first service.
- On L4 it redistributed waiting: the youngest request, R009, waited 35.6 minutes instead of 9.8.

---

## Slide 8: implementation verification

**Purpose.** Establish that the results come from a correct implementation of the stated rules.

**Evidence.**
- Phase 4 log; D-52, D-55, D-57.
- Tests: `tests/test_sim_engine.py`, `test_curb_wait.py`, `test_sim_independent.py`, `test_pending_price_independent.py`, `test_m2_independent.py`.

**What each claim means.**
- **"To the second."** L1–L3 are small designed evenings whose every event time was computed by hand. The simulator computes events independently and matches every van, curb arrival, pickup, drop-off, cancellation and no-show time exactly.
- **"22 + 4".** On L4, before the vans come on duty, the Lyft decisions of the five rules that transfer (R0 never does) match the hand key: 22 transfers, 4 of them XL, and 4 declined offers. On L4 a rider accepts a Lyft offer with probability 0.9, and one designed rider declines under each of four rules. These are *totals over five separate rule runs*, not counts for one night.
- **"292,181".** An independently written brute-force program enumerated every compatible pair of candidate routes at every epoch of two L4 runs: 151,710 combinations under the original pending price and 140,471 under the approved price A. It found the same optimum and the same tie-break as the MILP every time.
- **"253 tests".** 46 test scenario generation and 207 test the simulator. Of the 207, 168 were written by independent verification agents that did not reuse the simulator's own logic.

**Limitations.**
- Verification shows the code implements the stated rules. It is not *validation*: nothing here compares the synthetic evenings with real service nights.

---

## Slide 9: thirty synthetic nights, findings and mechanisms

**Purpose.** Report what the pilot showed, as mechanisms we can explain, not as rankings.

**Prerequisites.**
- *Paired replay*: the same night run under each rule, with the same riders and the same hidden traits.

**Evidence.**
- `outputs/sim/batch_L5_v1/`: per-run outcomes, summary.md and per_night_metrics.csv.
- Decisions D-56 (pilot settings) and D-57 (batch).

**Design.** 30 synthetic nights, each replayed under 6 rules: 180 runs, but *not* 180 independent nights. The load is heavy by design: 28 requests per hour on 2 vans is 14 per van-hour, against April's 12.85 at 6 pm, with a 10-minute burst. That is why under R0 only about 16 of 28 requests are picked up: the rest cancel (placeholder patience) or no-show.
- Each night has 2 vans, 28 requests in one hour and a 10-minute burst.
- Settings: lag 2 min; consent 1.0, meaning every offered transfer is accepted (a simplification); presence p = 0.089 (provisional); frozen placeholder patience.
- Every run passed every check.

**Derivation: what happened to transferred riders.** Totals over 30 nights. Each row reconciles: transfers = Lyft completed + Lyft no-show + cancelled in the lag + cancelled after booking.

| Rule | Transfers | Lyft completed | Lyft no-show | Cancelled in lag | Cancelled after booking |
|---|---|---|---|---|---|
| R1(10) | 196 | 94 | 7 | 18 | 77 |
| R1(15) | 104 | 55 | 4 | 11 | 34 |
| R1u(10) | 8 | 4 | 0 | 1 | 3 |
| R2(15) | 294 | 187 | 14 | 14 | 79 |
| R3(2) | 330 | 211 | 15 | 16 | 88 |

**Mechanisms, with their scope.**
1. **A transfer does not stop the patience clock.** A rider transferred after 10 minutes of waiting still waits 2 minutes of lag plus a Lyft delay of about 8 minutes. With placeholder patience (median 18 min), 95 of 196 such riders cancelled before the Lyft arrived. Under the rules that read predicted pickups, about a third did. The magnitude depends on the placeholder patience; the mechanism does not.
2. **Assignment is not pickup.** R1u(10) fires only when a request has been continuously absent from every van plan for 10 minutes.
   - On the designed L4 evening it never fired after the vans came on duty, because C assigned every waiting request within about 4 minutes.
   - In L5 it fired 8 times on 6 of 30 nights, all for requests made during the burst (between 18:21 and 18:28; the transfers came at 18:35–18:38), when 2 vans × 3 planned pickups could not absorb the queue.
   - The rule measures assignment, which can be quick even when the pickup is far away.
3. **Guardrail excesses.** There were 36 excess events across the 180 runs, from 16 distinct requests on 10 nights (the same request repeats under rules that made the same decisions). The attribution check finds that each coincided with a van no-show on the same van while the rider was aboard, and that the excess was at most 150 s per no-show (the extra wait over a normal 30-s boarding dwell) plus a 13-s matrix tolerance.
   - Plans never create a violation; the plan audit checks this at every epoch.
   - This is evidence *consistent with* the no-show wait causing the delay, not a proof.
4. **Denominators.**
   - Wait percentiles are computed over requests *picked up*: about 16 of 28 under R0, 20 under R2(15). A rule whose riders cancel more drops its longest waits from the denominator.
   - We therefore report "reached by a vehicle within 15 min" over *all* 28 requests. Here "reached" means a vehicle's curb arrival, not boarding.

**Limitations.**
- Two vans.
- One demand pattern.
- Placeholder behaviour.
- Descriptive only: no intervals have been computed, because the decision criteria (D-50) are unresolved.

---

## Slide 10: service versus Lyft use

**Purpose.** Introduce Pareto dominance and apply it descriptively to the tested rules.

**Prerequisites.** Two objectives that pull against each other.

**Evidence.** `outputs/sim/batch_L5_v1/tradeoff.md`, computed by `src/sim/tradeoff.py` from saved outputs only.

**Definitions.**
- **Service:** S = share of all requests reached within 15 min. Larger is better.
- **Lyft use:** B = bookings per night. Smaller is better.
- **Dominance:** P dominates Q if S_P ≥ S_Q and B_P ≤ B_Q, with at least one inequality strict. A rule is *nondominated among the tested rules* if no other tested rule dominates it.

**Derivation: the means over 30 nights.**

| Rule | S | B |
|---|---|---|
| R0 | 0.477 | 0.00 |
| R1u(10) | 0.476 | 0.23 |
| R1(15) | 0.495 | 3.10 |
| R1(10) | 0.514 | 5.93 |
| R2(15) | 0.735 | 9.33 |
| R3(2) | 0.750 | 10.47 |

On these means, R1u(10) is technically dominated by R0, but the gap (0.001) is far inside the night-to-night spread (SD about 0.09): in practice a tie. The other five are nondominated. The same five remain nondominated with van-km as a third objective.

**Derivation: night by night.**
- **Nights each rule is nondominated:** R0 30, R2(15) 24, R1u(10) 26, R1(15) 14, R3(2) 12, R1(10) 11. R1u(10)'s count is inflated by 24 nights on which it made no transfer and tied R0 exactly.
- **Paired comparison with R0** (nights above / below): R2(15) and R3(2) reach more on all 30 nights; R1(10) on 19, but fewer on 6.

**Three different trade-offs, kept separate.**
1. **Inside the routing objective.** The weights (φ, 0.5, 0.1) are a fixed exchange rate that C uses to choose routes within one epoch. They are not a point on this chart.
2. **Between transfer rules.** This chart, an empirical and descriptive comparison of six policies.
3. **Decision criteria.** How to choose a rule from this comparison: margins, confidence intervals, a value judgement on Lyft use. These are provisional (D-50) and not applied here.

**Interpretation.**
- The rules that read predicted pickups buy far more reach per booking than the elapsed-time rules on these nights.
- Nondominated does not mean recommended.
- Six tested rules are not a frontier: an untested rule, or another threshold, could dominate them all.

**What would be needed for more.**
- Paired intervals, once D-50 is decided.
- Threshold sweeps, to trace curves.
- Calibrated behaviour.
- Five vans.

**Limitations.**
- Means hide night-to-night variation; see backup B6.

---

## Slide 11: a leader–follower interpretation

**Purpose.** Address the professor's question precisely: what the interpretation would be, what we implement, and what is missing.

**Prerequisites.** Optimization with an objective and constraints.

**Concept.** A leader–follower (Stackelberg) model has a leader who chooses first, anticipating the follower's optimal response (von Stackelberg 1934). A bilevel program writes the follower's problem as a constraint of the leader's (Colson, Marcotte & Savard 2007; Dempe 2002).

**One reading of our problem.**
- **Leader:** the policy designer, choosing rule parameters θ (for example the threshold of R2).
- **Follower:** the routing optimizer, responding to the requests left after transfers.

A formal version:

  min over θ of  E[ L(θ, y) + λ · B(θ) ]
  subject to  y ∈ argmin over y′ ∈ Y(θ) of f(y′; θ)

Here L is service loss, B is Lyft bookings, λ is a trade-off weight, and Y(θ) and f are the follower's feasible plans and routing cost given the transfers that θ causes.

**What we implement.** A *sequential policy simulation*. At each epoch the dispatcher plans; the rule reads that plan; transfers are applied; the dispatcher re-plans once. Across rules, we replay nights and compare six fixed rules.

**What is missing for a solved bilevel model.**
1. An upper-level optimization over θ. We only enumerate six rules.
2. The follower's optimal response stated as constraints over the evening. Our follower optimizes one epoch at a time, over a restricted candidate set, and the evening's outcome emerges from many such solves.
3. A treatment of the expectation over random nights.

**On simplifying the hierarchy.** Any reduction to a single-level problem needs specific assumptions and justification. Examples are a lower level whose optimality conditions can be written as constraints, or a value-function reformulation, each with its own requirements, notably for integer lower levels. We do not claim such a reduction.

**Riders and Lyft are not players.** Riders follow assumed patience rules and Lyft is a delay distribution; neither is modelled as optimizing. A model in which they respond strategically would be a further extension.

**Interpretation.**
- Choosing a policy offline by simulating candidate rules is not the same as solving a bilevel program.
- Formal leader–follower optimization is a feasible extension, not impossible and not done.

---

## Slide 12: limitations, next experiments and contribution

**Purpose.** Close honestly and point forward.

**Limitations.**
- Aggregate-only evidence.
- Placeholder patience; provisional presence p, which rests on a status mapping.
- Two-van pilot; the five-van evening is not run.
- At most three new pickups per van per epoch.
- Runs of up to about 4 minutes.
- One demand pattern.
- The designed evenings are small.

**Next steps, in order.**
1. Agree the decision criteria (D-50), then compute paired intervals on the saved 30 nights, to size the main experiment rather than to conclude (L5 is a rehearsal). No new simulation is needed.
2. Sweep rule thresholds to trace trade-off curves.
3. Build the five-van evening (L6) and benchmark the MILP. Its suitability as the fixed dispatcher depends on this benchmark (D-51).
4. Test sensitivity to patience and Lyft delay.

**Contribution.** A method that turns aggregate dashboards into paired synthetic experiments, labels every input as observed, derived or assumed, and is verified to the second, so that conclusions can be stated with their conditions attached.

---

## Glossary

| Term | Meaning |
|---|---|
| Epoch | A moment when the dispatcher re-plans |
| Candidate route | One van's ordered stops for a chosen set of requests |
| MILP | Mixed-integer linear program |
| HiGHS | The open-source solver used |
| φ (phi) | Convex waiting penalty |
| Guardrail | Ride-time limit max(25, 2×direct + 5) min |
| Pending price | What the MILP charges for leaving a request waiting |
| Paired replay | The same synthetic night run under each rule |
| Dominance | No worse on every objective, better on one |
| Bilevel program | An optimization whose constraints include another optimization's optimal response |
| R0…R3(2), L1–L5, C, A, D-xx | See backup B3 |
