# Midterm speaking script (draft v0.2, 22 Oct 2026)

**Deck:** `BlueJay_Midterm_draft.pptx` (12 core slides after the title, 9 backup slides).
**Timing:** about 18½ minutes speaking plus about 10 minutes of questions. *Awaiting confirmation from the course.*
**Presenters:** roles **P1, P2, P3** until the team confirms who speaks. P1 covers slides 1–4 (the data story), P2 slides 5–8 (the method), P3 slides 9–12 (the findings). A fourth teammate can take questions on the backup slides.
**Pace:** about 2,460 spoken words in all, so 18.2–18.9 minutes at 130–135 words per minute. Rehearse with a timer; slides 2, 3 and 9 have the least slack.

**Codes used out loud.** Always say the plain meaning with the code, at least the first time on each slide:

| Code | Say it as |
|---|---|
| R0 | "never transfer" |
| R1(10), R1(15) | "transfer after 10 (or 15) minutes of waiting" |
| R1u(10) | "transfer after 10 minutes with no van assigned" |
| R2(15) | "transfer when the predicted total wait passes 15 minutes" |
| R3(2) | "transfer when the van is predicted to arrive later than a Lyft could, plus 2 minutes" |
| L4 | "a small designed evening we checked by hand" |
| L5 | "the pilot: 30 synthetic one-hour nights with two vans" |
| MILP | "a mixed-integer linear program, the optimization model" |

---

## Title (P1) · 0:00–0:10

> Good afternoon, we are Team FourSight. We set out to optimize the Night Ride shuttle; first we had to learn what the data can and cannot tell us.

---

## Slide 1 · Service problem and original proposal (P1) · 0:10–1:00 · 1 min

> Blue Jay Night Ride is Hopkins' evening shuttle. A rider books in the app, a dispatcher assigns a shared van, and the van picks the rider up at the curb and drops them at the destination, roughly six in the evening to two in the morning around Homewood. Hopkins can also send a Lyft instead: in April, about one rider in four rode Lyft.
>
> In September we proposed to replay real nights from trip records and compare dispatch methods: simple greedy rules against an optimization model re-solved as requests arrive. Lyft was to be paid overflow inside the optimizer, and the published targets hard constraints. Most of that changed once we saw what data exists. We also corrected three proposal numbers: "5,100 rides per hour at 6 pm" was a 30-day total, about 170 per evening; "28 vans" counted all services; and "one in four overflow to Lyft" is a share of riders, not of requests.

**Handoff:** continue directly to slide 2.

---

## Slide 2 · How the research question changed (P1) · 1:00–2:30 · 1½ min

> The trip records never arrived. We have only aggregate dashboards: monthly totals, shares and percentiles, so we cannot replay a real night.
>
> So we changed the question. On synthetic nights, a ranking of dispatch algorithms would mostly reflect our guesses about the fine detail of demand. What we *can* do is replay the same synthetic night many times and change one lever, the rule that decides when to transfer a waiting rider to Lyft, which is the decision Hopkins' dispatchers actually make. We hold one reasonable van dispatcher fixed. The question is: which transfer rule gives riders the best service for the Lyft use it requires, and why?
>
> The six rules we compare are listed on the right: never transfer; transfer after 10 or 15 minutes of waiting; transfer after 10 minutes with no van assigned; transfer when the predicted total wait passes 15 minutes; and transfer when the van is predicted to arrive later than a Lyft could, plus two minutes.
>
> Lyft is now a separate, explicit rule, and we do not model money, because Hopkins' cost per Lyft trip is unknown. And the wait targets are thresholds we report against. The one limit built into planning is on ride length: no plan may create a ride longer than 25 minutes, or twice the direct drive plus 5 minutes if that is longer.
>

**Transition:** "So what can aggregate data tell us? That is how we built each evening."

---

## Slide 3 · Building an evening from aggregate data (P1) · 2:30–5:00 · 2½ min

> Every block of the scenario follows the same four steps along the top: what we observed, what we derived, what stayed unknown, and what we chose.
>
> First, how many requests. The dashboard shows about 5,100 completed rides in the 6 pm hour, summed over 30 days, so about 170 per evening. April had about 2.09 recorded requests per completed ride, because many requests were cancelled or handed to Lyft, so that is about 355 requests in an evening's 6 pm hour. The dashboard also shows about 27.6 vehicles on duty at 6 pm, so 12.85 requests per vehicle per hour. Five vans would therefore face 64 requests at 6 pm, then 50 and 54 in the next two hours.
>
> What stays unknown? We do not know how many of those vehicles served Homewood rather than other services, or how many requests were rebookings. So the count is a range of about 150 to 260 per three-hour evening. That range is illustrative, not a confidence interval.
>
> Second, where trips go. The maps tell us how many pickups and how many drop-offs each place had, but never which pickup went with which drop-off. We start from an assumption, a gravity prior: nearby trips are more common, with the weight falling by about 10% for each extra minute of driving. Then we rescale the table until it reproduces both sets of April totals exactly. The data cannot tell us the decay rate, since any rate reproduces the totals, so that choice is ours; we have built a spread-out geography variant for later tests. The map on the right is one synthetic night built this way.

**Transition:** "Some inputs the dashboard cannot pin down at all. Those are assumptions, and we want to show them openly."

---

## Slide 4 · Assumptions that complete the evening (P1) · 5:00–6:30 · 1½ min

> The badges say how each number is known.
>
> Group size: dividing van passengers by completed van bookings gives 1.386 van passengers per completed van booking. That is a mean, not a distribution. Many distributions have that mean, and ours is an assumption. In it, one percent of bookings are parties of five; a transferred party of five rides together in a larger Lyft, an XL.
>
> "Canceled" is our favourite lesson. Almost half of April's requests ended "Canceled". That sounds like impatient riders, but the label also includes requests the dispatcher moved to Lyft. So we model each rider with a hidden personal deadline, a placeholder for now, and treat the share of "Canceled" that is really riders giving up as a range of 50 to 75 percent.
>
> No-shows: 4.7% of *all* requests were no-shows. But many requests never had a van arrive. Per van arrival the rate is about 8.9%, and only if the status labels mean what we assume. We use 8.9% per arrival, provisionally.
>
> Lyft: booked two minutes after the decision, then a random arrival delay, typically eight minutes.

**Handoff to P2:** "With the evening built, P2 will show how our dispatcher plans on it."

---

## Slide 5 · How our algorithm operates (P2) · 6:30–8:30 · 2 min

> The loop on the left runs whenever something happens — a request, a cancellation, a no-show — and every two minutes. First, new requests are revealed and the state is updated. Second, for each van we generate candidate routes that are feasible: seats available, pickup before drop-off, no ride over the guardrail. Third, the optimization model picks one route per van. Fourth, the separate Lyft rule reads the predicted pickup times from that plan. Fifth, riders it transfers leave the van plan immediately. Sixth, the dispatcher re-plans once. Seventh, vans drive to their next stop. Then it repeats.
>
> Notice the two boxes. The dispatcher sees the requests that have arrived, where the vans are and who is aboard. It does not see each rider's patience, whether the rider will actually be at the curb, or how long a Lyft will really take. Those are revealed only when they happen. So the pickup times the rule reads are predictions; the simulator's actual events can differ.
>
> Here is one actual transfer, on a small designed evening. Rider R011 asked at 18:16:30. At 18:20 the plan predicted a van at 18:35:20, a total wait of 18 minutes 50 seconds, over the rule's 15. The rider was transferred, the Lyft was booked two minutes later, arrived at 18:30, and the rider's wait, counted from the original request, was 13 minutes 30 seconds. That is the Lyft outcome; we cannot know what the van would actually have done, only what it was predicted to do.

**Transition:** "How does the model choose between candidate routes?"

---

## Slide 6 · How the mathematics chooses a plan (P2) · 8:30–10:00 · 1½ min

> Each candidate route gets penalty points. These are priorities, not money. Waiting points use the curve on the left: each minute costs 1 point for the first 5 minutes, then 2.5, 5, 10, and 20 points per minute after 20 minutes. So the model cares most about riders who have already waited long. Riding costs half a point per passenger-minute, and driving a tenth of a point per kilometre, as a tie-breaker.
>
> The small example has one van and two requests. Picking up the rider who has already waited 8 minutes first costs 66.5 points. Picking up the party of two first costs 81, because the first rider's wait would cross 15 minutes. So the model chooses route A.
>
> A request in no chosen route is left waiting at a price, which matters on the next slide; a large constant makes the model first serve as many requests as it can.
>
> One careful word. When we say "optimal", we mean optimal among the candidate routes generated at that moment. We allow up to three new pickups per van, and the solver proves optimality over those. That is not optimal over every possible route, and not optimal over the whole evening.

**Transition:** "Checking the model's logic, we found a weakness."

---

## Slide 7 · Pending-price weakness, experiment and decision (P2) · 10:00–11:30 · 1½ min

> That price for leaving a request waiting is the "pending price". Our original version assumed a van could reach the rider at the next two-minute re-plan, even when no van physically could. That made postponement look cheap, cheapest of all for riders who would be picked up late, often the longest waiters. On our designed evening, a party of five who had already waited 15 minutes was left waiting.
>
> We ran a controlled experiment: three versions of that price, each run through the whole evening on identical inputs. Version A charges the earliest pickup any van could physically make. Version B charges a pickup after a van's planned route. B made the model much larger, about 9,800 extra variables here, and its estimate can be wrong in either direction.
>
> The experiment's job was to check behaviour over a whole evening. We chose A, provisionally, because its meaning is clear and it adds nothing to the model, not because one rider was served sooner. It is still an approximation: it ignores the work the nearest van is already doing. It also redistributed waiting rather than improving everything: the longest waits fell, but the median rose and the most recent request waited longer. So: addressed, not fixed.

**Transition:** "Before trusting any result, we checked that the simulator does what we say."

---

## Slide 8 · Implementation verification (P2) · 11:30–12:30 · 1 min

> Three small designed evenings have answers we computed by hand, and the simulator reproduces every pickup, drop-off, cancellation and no-show time to the second. On a fourth designed evening, where riders accept a Lyft offer with probability 0.9, it matched all 22 Lyft transfers and 4 declined offers, summed over the five rules that transfer. For the optimization model, an independent brute-force program enumerated every compatible combination of candidate routes, about 290,000 over two runs of a designed evening, and agreed with the solver every time. In all, 253 automated tests, 168 of them written by independent reviewers who did not reuse the simulator's logic. This checks the code against our rules; it does not check our rules against real nights.

**Handoff to P3:** "With the machinery checked, P3 will show what thirty synthetic nights revealed."

---

## Slide 9 · Thirty synthetic nights: findings and mechanisms (P3) · 12:30–14:30 · 2 min

> Our pilot uses two vans, not the planned five. It has 30 synthetic one-hour nights of 28 requests each, with a ten-minute burst: a heavy load by design, 14 requests per van-hour against April's 12.85 at 6 pm. Each night is replayed under all six rules with the same riders and the same hidden traits, so differences come from the rule. That is 30 synthetic nights replayed six times, not 180 independent nights.
>
> Four mechanisms stood out. First, a transfer is not a rescue: the patience clock keeps running through the two-minute lag and the Lyft's travel. Under "transfer after ten minutes waited", 95 of 196 transferred requests cancelled before the Lyft arrived, 77 of them after the booking was placed. Under the two rules that read predicted pickups, about a third.
>
> Second, being assigned is not being picked up. The rule "transfer after ten minutes with no van assigned" only fires when a request stays unassigned that long, which happened 8 times on 6 of the 30 nights, all for requests made during the burst.
>
> Third, plans never exceed the ride limit, but rides did, 36 times across the 180 runs, from 16 distinct requests on 10 nights. Each coincided with a no-show wait on that van while the rider was aboard, a three-minute wait the plan had not expected. That is consistent with the timing, not a proof of cause; none was unexplained.
>
> Fourth, mind the denominator. Average wait figures only cover riders who were picked up, so a rule that loses riders to cancellation can look better than it is. That is why we measure the share of *all* requests that a vehicle reaches within 15 minutes.

**Transition:** "That measure lets us compare service with Lyft use."

---

## Slide 10 · Service versus Lyft use (P3) · 14:30–16:00 · 1½ min

> Two objectives. Service is the share of all requests reached within 15 minutes; higher is better. Lyft use is bookings per night; lower is better. One rule dominates another if it reaches at least as large a share of requests within 15 minutes with no more Lyft bookings, and is strictly better in one.
>
> Each point is a rule's average over the 30 nights. Never transferring uses no Lyft and reaches about 48%. The rules based on time waited buy little extra reach per booking. The two rules that read predicted pickups reach about three quarters of requests, with nine to ten bookings per night. Among these six tested rules, five are not dominated on the averages. The unassigned-time rule is technically dominated, but its gap from never transferring is a thousandth, far inside the night-to-night spread: in practice it is a tie.
>
> Four cautions. We tested six policies, so this is not a frontier of all possible policies. Not dominated does not mean recommended: choosing a point requires a value judgement about how much Lyft use a unit of service is worth. The weights inside the routing model are a different trade-off from this one. And our statistical decision criteria are still a proposal.

**Transition:** "Our professor asked about leader–follower models. Here is where that fits."

---

## Slide 11 · Leader–follower interpretation (P3) · 16:00–17:00 · 1 min

> Our professor asked about leader–follower models. The leader decides first, anticipating the follower's response. Here the leader would be the policy designer choosing the rule and its threshold, and the follower the routing optimizer re-planning the vans for the riders who remain. Formally that is a bilevel program: choose the threshold to minimise expected service loss plus a weight times Lyft use, subject to the routes being optimal for the routing problem. The leader decides offline, before the evening; within each re-plan the rule then reads the dispatcher's plan.
>
> We have not solved that. We run a sequential policy simulation and compare six fixed rules. A solved version needs an optimization over the threshold, the follower's response imposed over the whole evening, and the expectation over nights. Riders and Lyft follow assumed rules here, not optimizing behaviour. A possible extension, not something done.

**Transition:** "So where does that leave us?"

---

## Slide 12 · Limitations, next experiments and contribution (P3) · 17:00–18:30 · 1½ min

> Our limitations are real. We have aggregate data only, and no comparison with real nights yet. Rider patience is a placeholder, and the no-show rate depends on how statuses were recorded. Results so far come from a two-van pilot; the five-van evening is designed but not yet run. We plan at most three new pickups per van at a time, and some runs take minutes.
>
> Next: agree the decision criteria and compute paired comparisons on the 30 saved nights, to size the main experiment; sweep the rule thresholds to turn six points into curves; build the five-van evening and check the optimization model is fast enough there; and test sensitivity to patience and Lyft delay.
>
> Our intended contribution is not a claim that one rule wins. It is a transparent, code-verified way to turn aggregate dashboards into paired synthetic experiments that say clearly what was observed, what was assumed, and what the simulation produced. Thank you; we welcome your questions.

---

## Question handling (about 10 min)

| Likely question | Who | Where to go |
|---|---|---|
| Why not compare algorithms anymore? | P1 | Slide 2; we could not replay real nights |
| How sure are the 168 requests? | P1 | Slide 3; backup B4 |
| Exactly what is the MILP? Is it really optimal? | P2 | Backup B1; candidate-set qualification |
| Why pending price A? | P2 | Slide 7; backup B7 |
| How do you know the code is right? | P2 | Slide 8; backup B8 |
| Which rule is best? | P3 | Slide 10: no winner; criteria provisional (D-50) |
| Is this a Stackelberg game? | P3 | Slide 11: a possible extension, not implemented |
| Are 30 nights enough? | P3 | Backup B6; power check pending once criteria agreed |
