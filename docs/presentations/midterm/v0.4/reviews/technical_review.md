# Technical review of disputed interpretations (v0.3 → v0.4)

Reviewer: technical-review agent, 23 Oct 2026. Read-only: no files edited, no simulations run. The only computations were on saved outcome CSVs and latent draws in `outputs/sim/batch_L5_v1` and `data/scenarios/v2/L5`.

## A. Rider patience: v0.3 claim unsupported; correction adopted

**Implementation.**
- Each request gets one hidden deadline, request time + `patience_s`, scheduled once (`src/sim/engine.py:92`).
- The draws are identical across the six rules (D-39; D-57).
- A transfer does not change the deadline. It can cancel a rider waiting for the Lyft order or for the Lyft itself (`engine.py:179-181`, D-46).
- Only a vehicle's curb arrival stops the clock (`engine.py:173`).
- The Lyft delay is one draw per rider, independent of when the transfer happens (`engine.py:235`).

**Saved pilot, riders transferred.** Totals over 30 nights.

| Rule | n | Median wait already elapsed at transfer | Cancelled before the Lyft arrived |
|---|---|---|---|
| Wait ten minutes | 196 | 629 s | 48.5% |
| Wait fifteen minutes | 104 | 932 s | 43.3% |
| Unassigned for ten minutes | 8 | 698 s | 4 of 8 |
| Predicted total wait exceeds fifteen minutes | 294 | 0 s | 31.6% |
| Lyft arrives sooner | 330 | 0 s | 31.5% |

**Conditional calculation on those same riders**, using each rider's actual elapsed wait, lag and Lyft delay:
- Under the Weibull placeholder, the expected loss is 44–47% for the waiting-time rules and 29–30% for the prediction rules, which matches the observed shares.
- A constant-hazard (exponential) patience with the same median gives 33–34% for every rule.

**Scope.** This is a conditional probability calculation on fixed riders and delays, not a whole-policy experiment. Different patience would change who survives, the van waits, who is transferred and the van cancellations. "Wait fifteen minutes" loses fewer than "Wait ten minutes" despite transferring later, so selection matters too.

**Adopted wording.**
> Under constant-hazard patience, elapsed waiting alone does not change the probability of surviving an equal additional waiting period. That does not establish that the cancellation gap between entire policies disappears. A transfer does not end waiting; riders may still cancel before Lyft arrives. Under our placeholder, the riders moved by prediction rules had waited less, which is consistent with their lower loss; whether the policy gap survives other patience shapes is untested.

## B. Research pivot: v0.3 citation unsupported; narrower wording adopted

**What the sources say.**
- **D-25** (`decision_log.md:35`) fixes a TransLoc-like re-planning baseline.
- **D-51** (`decision_log.md:288, 296`) makes dispatcher C provisional.
- Neither says that algorithm comparisons on synthetic nights "mostly compare our assumptions". That phrase appears only in methodology §1a, as uncited reasoning, and the same objection applies to rule comparisons.

**Current operations.** TransLoc's 2016 vendor post describes re-solving on every new ride, cancellation, driver-reported no-show and every 2 minutes (`transloc_operations.md:46, 98, 119`). The current version is UNKNOWN, and Hopkins dispatcher overrides are UNKNOWN (`:168`).

**Our model's triggers:**
- a new request;
- a cancellation while waiting for a van;
- a van no-show;
- a van coming on duty;
- a 120-s tick.

A van going off duty returns no trigger (`engine.py:165-169`), although the spec lists it. Lyft events do not trigger an epoch (`engine.py:182`).

**Adopted wording.**
> We specify one van dispatcher, modelled on TransLoc's published 2016 design, and hold it fixed so that we can isolate the effect of changing the Lyft transfer rule. Whether Hopkins' current dispatcher works this way is not verified.

## C. Leader–follower: v0.3 overstated both points; correction adopted

**(i) A threshold need not be a leader–follower problem.** It can be tuned by simulation-based search with the dispatcher as a black box. A bilevel formulation is a modelling choice.

**(ii) Enumeration can solve a finite problem.** If the follower is *defined* as our deterministic per-epoch restricted MILP with its canonical tie rule, exhaustive search over a finite set of thresholds solves that finite problem exactly, for the defined objective averaged over the sampled nights. It does not give optimality over continuous thresholds or over all policies.

**Adopted wording.**
> One possible extension is to optimize transfer policy while anticipating how the routing dispatcher responds.

**Definitions still needed for a precise bilevel model:**
1. The leader's decision space: rule family, discrete or continuous threshold, bounds.
2. The follower: a sequence of per-epoch restricted MILPs whose state depends on earlier epochs and random outcomes, or one whole-evening problem; its information and timing.
3. How non-unique follower optima are handled: optimistic or pessimistic (Colson, Marcotte & Savard 2007; Dempe 2002). Ours is a fixed lexicographic tie rule (D-52), which is neither.
4. The expectation: a scenario distribution, or a sample average over N nights.
5. The loss and λ (D-50 open).
6. Upper-level constraints, such as a Lyft budget or a service floor.

## Implementation facts confirmed for the slides

**1. One decision epoch** (`engine.py:305-351`).
- Same-second events are processed first; patience checks come before the epoch.
- The epoch: solve; update the unassigned timer; apply the rule to each request still waiting for a van; apply declines and transfers (Lyft order at now + lag); re-solve **once** only if a transfer happened, with no second rule pass; then departures.
- At most one epoch per second, so there are no cascades.

**2. Rules** (`lyft.py:13-30`; `engine.py:312-327`).
- **Eligibility:** state `pending_van` (not committed to a van, never declined).
- **Predicted pickup:** the plan ETA if assigned, otherwise the tentative ETA. If neither exists, it is infinite and the rule fires.
- **Wait ten / fifteen minutes:** τ − t_r ≥ θ.
- **Unassigned for ten minutes:** τ − unassigned_since ≥ 600 s.
  - The timer is set at the request.
  - It resets whenever the request is in a chosen route and restarts if the request drops out (`engine.py:406-414`).
  - It is updated before the rule and after the re-solve, so it is continuous only at epoch granularity.
- **Predicted total wait exceeds fifteen minutes:** predicted pickup clock − request clock > 900 s.
- **Lyft arrives sooner:** predicted pickup > τ + 120 + 480 + 120 s, i.e. now + 12 min.

**3. Scope.** Homewood only (D-23), including the Peabody area (D-27).

**4. Pilot.**
- Arrivals 18:00–19:00.
- The generator places round(0.4 × 28) = 11 requests in 18:20–18:30, plus uniform background (`generator_v2.py:305-312`).
- Realized per night: 11–17 requests in that window (mean 13.7) and 34–51 passengers.
- The spec's "≥ 40%" is slightly off: 11/28 = 39%.

**5. Postponement price A** (`dispatch.py:355-359`) changes cost coefficients only, with no new variables. Computing L_r takes |open| × |vans| lookups per epoch. No runtime comparison was measured.

**6. Stale methodology text.** Pushback item 1 (no Lyft-rule comparison run) is stale after D-56/D-57. Item 2's "must be settled" is stale after A's provisional approval.

---

## Second pass: final technical wording (23 Oct 2026)

**Confirmed accurate.**
- Slide 5's scope wording.
- Slide 8's pilot facts.
- Slide 15 and B3: order and triggers.
- Slide 18: the R011 timeline (990 / 1020 / 1140 / 1620 / 1825 s).
- Slide 19 and B5.
- Slide 22: the per-Lyft-order ratios.
- Slide 23: 196 = 94 + 7 + 18 + 77.
- Slide 25.
- B2 and B8.
- Methodology v1.5: the diff is limited to the header, Pushback items 1–2 and the §1a row, and is accurate.

**Must fix.**
1. Slide 3 still said comparing dispatch methods "could not be carried out"; missing data blocked only replaying real nights.
2. Slide 17's "no feasible van counts as never" reads as "never transfers". In the code, the pickup is infinite and the rule fires.
3. Script 26 ranked patience as the most important assumption, which is untested. Its Lyft-delay statement holds only under rising impatience.
4. A reported broken link to `reviews/technical_review.md`. *Not a defect: the file is at that path and the link checker passes.*

**Should fix.**
5. Script 5 overstated the triggers ("whenever something new happens").
6. "Thresholds were fixed before any run": pre-registration v2 is still a draft. Say "specified before any run (spec §6) and not changed after seeing results".
7. Script 17 omitted the 2-min margin in the "Lyft arrives sooner" rule.
8. Handbook §23 called the transfer mechanism "structural"; restate it as built into the model.
9. Handbook §22: the 8 "Unassigned" transfers concern requests *made* during the burst; they were moved at 18:35–18:38.

**Minor.**
10. The unassigned timer is also updated after a re-solve.
11. "Follows that design" should read "is modelled on that design; its triggers differ slightly".
