# Midterm speaking script (content draft v0.4, 23 Oct 2026)

**Format.** The presentation is planned at about 27 minutes (estimate; unrehearsed) and must stay under 30. Questions are not assumed to fit inside the same 30 minutes.

**Deck.** [BlueJay_Midterm_v0.4.pptx](BlueJay_Midterm_v0.4.pptx) has 28 main slides; backups B1–B9 are slides 30–38.

**How to read this file.**
- Each slide has a short **context** (why it is here in the journey), the **spoken** narration (quoted, `>`), and the spoken **transition**. Only quoted text is said aloud.
- Evidence, assumptions, design choices, likely questions and links to the technical documents are in the preparation handbook, [slide_explanations.md](slide_explanations.md), under the same anchor (`#s01`–`#s28`).

**Timing (an estimate, not a rehearsal).** Default delivery leaves out the sentences marked *(optional)*: about 2,880 spoken words, 23.1 min at 125 words per minute. Adding about 4 s of visual pause per slide (1.9 min) and about 15 s per handoff (1 min) gives **about 26 min**. Reading the many numbers and clock times slowly adds roughly a minute, so plan for **about 27 min**. With every optional sentence included (3,060 words) the estimate rises to about 28 min, still under 30. Per-slide budgets below include the optional sentences. A timed full rehearsal should replace these estimates.

**Speakers.** Not yet assigned. Natural handoffs are marked **⇄** after slides 5, 13, 20 and 25, giving five sections:

| Section | Slides | Spoken (all sentences) + pauses (approx.) |
|---|---|---|
| Question and starting point | 1–5 | 4.3 min |
| From aggregates to scenario inputs | 6–13 | 7.7 min |
| Model and experiment | 14–20 | 7.3 min |
| Findings | 21–25 | 4.7 min |
| Limits and next steps | 26–28 | 1.8 min |

Any split of two to five speakers works along these boundaries. At each ⇄ the outgoing speaker says the transition; the incoming speaker starts with the next slide's first sentence.

**Words.**
- A *request* (booking) is one Night Ride request. A *Lyft order* is the separate order placed after a transfer decision.
- In files the Lyft order is called a "booking" and the ordering lag the "booking lag" (D-43).
- Rule codes (R0…R3) appear only in the presenter reference below, in backup B1 and in slide notes.

## Presenter reference
| Say | Code in files |
|---|---|
| Vans only | R0 |
| Wait ten minutes | R1(10) |
| Wait fifteen minutes | R1(15) |
| Unassigned for ten minutes | R1u(10) |
| Predicted total wait exceeds fifteen minutes | R2(15) |
| Lyft arrives sooner | R3(2) |
| small designed evenings | L1–L4 |
| the two-van pilot | L5 |
| the van optimizer | dispatcher C |
| the adopted postponement price | pending price A |

**Q&A jump table.** In PowerPoint slide show, type the number and press Enter. Type 28 and press Enter to return to the close.

| Question is about | Go to |
|---|---|
| Codes in files | B1 (30) |
| The MILP, the M bound, "optimal" | B2 (31) |
| Event order, triggers, commitments | B3 (32) |
| Where an input comes from | B4 (33) |
| Postponement prices | B5 (34) |
| Any metric by rule | B6 (35) |
| Pareto night by night | B7 (36) |
| Diagnostics, run times, ride-time excesses | B8 (37) |
| Proposal corrections | B9 (38) |

---

<a id="s01"></a>
## 1 · When should Night Ride move a waiting request to Lyft? (42 s)
**Context.** Opens the talk with the decision, before any data or model.

> We began with a dispatch problem. The data led us first to a modelling problem. Good afternoon, we are Team FourSight. Our question is simple to state: when a rider has been waiting for a Night Ride van, when should that request be moved to Lyft instead? *(optional)* Today we will show what April's aggregate data let us build, how we turned it into constructed evenings, and what our first simulations revealed.

**Transition** > First, the service itself, and one request.

<a id="s02"></a>
## 2 · The service and one request (55 s)
**Context.** Gives the vocabulary that every later number depends on.

> Homewood-area Night Ride pools requests in shared vans. A dispatcher can move waiting riders to Lyft. We are studying when that transfer should happen. Here is one request's journey: request, wait, the vehicle reaches the curb, boarding, drop-off. It breaks if the rider gives up while waiting, a cancellation, or is absent when the van arrives, a no-show after a three-minute wait. Four words matter later, and they are on the tiles: booking, Lyft order, curb arrival, and pickup, the rider boarding. Each Lyft order is an extra trip Hopkins pays for, so moving riders to Lyft has a price.

**Transition** > Our September proposal approached this differently.

<a id="s03"></a>
## 3 · Where we started (52 s)
**Context.** The mandatory recap, shown with the proposal's own slides.

> Our original plan was to reconstruct service nights and study dispatch decisions using an optimization model. These are two slides from that proposal. On the left, the data plan: aggregate dashboards were available, and de-identified trip-level extracts were coming, with request, pickup and drop-off times for each ride. Trip-level data would let us replay actual service nights. On the right, the method: compare fast heuristics, a rolling-horizon optimization model and a hybrid, all on the same request stream. Those trip-level extracts never arrived, so real nights could not be replayed.

**Transition** > The proposal also contained numbers we later had to correct.

<a id="s04"></a>
## 4 · Where we started: numbers we later corrected (50 s)
**Context.** Corrects superseded numbers instead of silently repeating them.

> Four numbers on these original slides were wrong or misread. One: "about 5,100 rides per hour at 6 pm" is a total over thirty days, so about 170 rides in one evening's six o'clock hour. Two: "about 28 vans" is the dashboard's all-services average, not a Homewood-only count. *(optional)* Three: the 7 pm bar shows 4,900; our digitized value is about 3,960. Four: "one in four trips overflow to Lyft" is really a share of riders: 24.5 percent of riders rode Lyft. These corrections shaped everything after.

**Transition** > With aggregate data only, we narrowed the question.

<a id="s05"></a>
## 5 · We narrowed the question to one controllable decision (54 s)
**Context.** States the pivot as a scope choice, not as a claim about what synthetic data forbid.

> We now hold one specified van dispatcher fixed and change only the Lyft transfer rule. This lets us study how the timing and information used by that rule change service and Lyft use. It is the question we chose; we don't know the internals of Hopkins' real dispatcher; and a controlled comparison needs everything else held fixed. Our van dispatcher re-plans every two minutes and at each new request, cancellation or no-show while waiting, or van coming on duty, modelled on the vendor TransLoc's published design from 2016. That is our modelling choice, not verified current Hopkins practice.

**Transition** > So what exactly do April's dashboards contain? **⇄**

---

<a id="s06"></a>
## 6 · April describes totals—not individual journeys (58 s)
**Context.** The evidence boundary that forces every later assumption.

> We know how many requests ended in each status, where pickups and drop-offs accumulated, and how activity varied by hour. We cannot reconstruct each rider's journey. *(optional)* On the left is what April gives; on the right, what it never gives: when a rider asked, where they went, how long they waited, and what happened next. Throughout the talk we label inputs. Observed means read from the dashboards. Derived means computed from observed numbers. Assumed means our choice, to be tested; designed means an experiment setting we chose. We therefore built plausible evenings from the evidence, while keeping the missing pieces visible.

**Transition** > The first piece is how busy an evening should be.

<a id="s07"></a>
## 7 · How busy should a constructed evening be? (64 s)
**Context.** Volume, derived step by step, with its assumptions in plain view.

> We estimated a workload from April's completed rides, request-to-completion ratio and reported vehicle availability. About 5,100 completed rides at six o'clock over thirty days is about 170 in one evening. April had about 2.09 requests for every completed ride, so roughly 355 requests in that hour. Divided by 27.6 vehicles on duty, that is about 12.85 requests per vehicle per hour. This assumes the monthly request-to-completion ratio applies within the hour, and uses vehicle availability reported across services. It is an estimated workload, not observed arrivals. Our planned evening uses five vans, a team design choice; each hour then gets its own count, 64, 50 and 54: 168 requests. That five-van evening is planned, not yet run.

**Transition** > What we actually ran is smaller, and deliberately harder.

<a id="s08"></a>
## 8 · We started with a smaller, deliberately demanding hour (56 s)
**Context.** Says exactly which experiment produced the results.

> The current results come from two vans and 28 requests in one hour, repeated across 30 constructed nights. Each van has fourteen seats. Requests arrive between six and seven, and eleven of the 28 are placed in a burst between 6:20 and 6:30. Each of the 30 nights is different, and each is run under six transfer rules, defined shortly. This is a controlled pilot, not a reconstruction of a typical April night. Its load, fourteen requests per van-hour, is close to the 12.85 we estimated per vehicle across all services, but the burst concentrates demand on purpose, to stress the transfer decision.

**Transition** > Next, where those requests go.

<a id="s09"></a>
## 9 · Knowing the endpoints does not identify the journeys (49 s)
**Context.** Geography: the maps give totals per place, never pairs.

> Two different sets of trips can produce exactly the same pickup and drop-off totals. In this toy example, both versions have identical green totals, which are all the maps show, yet different trips. So pairing pickups with drop-offs is a modelling choice. We assumed nearby journeys were more likely, then balanced the synthetic trips to preserve the observed location totals. The rate at which distance lowers a pair's weight is our assumption; the data cannot identify it. *(optional)* The map shows one constructed hour built this way.

**Transition** > The next input is who travels together.

<a id="s10"></a>
## 10 · One average can hide very different groups (61 s)
**Context.** Party sizes affect seats and passenger-weighted waiting.

> April helps identify an average group size. It does not tell us the full distribution of groups. April gives about 1.39 van passengers per completed van request. Examples A and B have exactly that average, yet one has eight percent of requests with three or more riders and the other over twelve. That matters for seats in the van, and because our waiting penalty counts every passenger. Our mix covers all requests, so its mean is slightly higher. Our chosen group-size mix is an assumption informed by the average—not a distribution recovered from April. A party of five that is moved to Lyft rides together in one larger XL vehicle.

**Transition** > The hardest label on the dashboard is "Cancelled".

<a id="s11"></a>
## 11 · One status label hides different events (62 s)
**Context.** Separates an observation, an assumed status mapping and hidden patience.

> ‘Cancelled’ does not tell us whether a rider gave up or a dispatcher moved the request to Lyft. Almost half of April's requests ended "Canceled". We assume that requests moved to Lyft also close as "Canceled" in the van system, and we keep the share that is riders giving up as a range to test, fifty to seventy-five percent. To let riders give up in the simulator, each rider gets a private deadline the dispatcher cannot see, with a median of eighteen minutes. The patience distribution is provisional. It lets the simulator represent abandonment; it is not a behavioural distribution measured from April. *(optional)* Many patience distributions could produce the same cancellation share.

**Transition** > A similar puzzle hides in "No Show".

<a id="s12"></a>
## 12 · The simulator needs a probability at vehicle arrival (55 s)
**Context.** Same count, two denominators; the simulator needs the per-arrival one.

> The share of all requests marked ‘No Show’ is different from the chance of a no-show when a vehicle actually arrives. 2,359 no-shows out of all 50,297 requests is 4.7 percent. But a no-show can only happen when a vehicle arrives, and most cancelled requests never saw one. Out of van arrivals, completed rides plus no-shows, it is about 8.9 percent. That figure holds only if "No Show" was recorded after a real van arrival, "Completed" counts van trips, and Lyft hand-offs sit in "Canceled". Our arrival-based probability is provisional because it depends on how the dashboard statuses were recorded.

**Transition** > Together, these pieces form a scenario.

<a id="s13"></a>
## 13 · The evidence becomes a scenario blueprint (62 s)
**Context.** Gathers every input, with its status, before the model appears.

> A scenario combines evidence-based inputs, explicit assumptions and hidden rider behaviour. Demand: arrival times, locations, trip pairing and party sizes. Resources: vans, their fourteen seats and travel times, which we inflate by twenty percent as a placeholder. Hidden behaviour: patience, presence at the curb and Lyft delay; a transfer takes two minutes to order, then the Lyft takes about eight minutes typically. And experiment settings: the van dispatcher, held fixed, and the transfer rule, which we vary. Many inputs carry two labels, derived and assumed. One point matters for what follows: inputs are fixed before a run, but cancellations, no-shows and transfers are not. They are outcomes of the run, not counts we impose.

**Transition** > Now, the machinery that runs a scenario. **⇄**

---

<a id="s14"></a>
## 14 · Three components have different jobs (65 s)
**Context.** The full architecture, with the information boundary visible.

> Three components have different jobs. The simulator advances time and reveals events. The van optimizer chooses among feasible candidate plans. The transfer rule decides whether an eligible request moves to Lyft. *(optional)* The simulator holds the clock, the vans and every request's state; it reveals a request only when it arrives, and applies a hidden draw only when its event happens. The decision step, on the right, sees only what has happened: the van dispatcher generates candidate routes, an optimizer—a mixed-integer linear program—picks one per van, and the transfer rule reads those plans. Then the vans execute, and every event is recorded. Future requests, each rider's patience and presence, and the real Lyft delay stay hidden from the dispatcher.

**Transition** > These parts work together in one repeating cycle.

<a id="s15"></a>
## 15 · The same decision cycle repeats as the evening unfolds (58 s)
**Context.** The verified implementation order of one decision moment.

> The dispatcher sees requests that have arrived. It does not see future requests. Every two minutes, and at each new request, waiting-time cancellation or no-show, or van coming on duty, the same cycle runs. Reveal and update. Generate feasible routes for each van. Select one route per van. Evaluate the transfer rule for each request still waiting. Apply accepted transfers: those requests leave van planning, and the Lyft is ordered two minutes later. If anything was transferred, re-plan once. Then vans execute and commit to their next stop. The rule runs once per decision moment, so there is no cascade of transfers in the same second.

**Transition** > How does the optimizer pick a route?

<a id="s16"></a>
## 16 · The optimizer compares the consequences of candidate plans (76 s)
**Context.** The objective in blocks, one worked example, and what "optimal" means.

> Waiting, riding, driving and unresolved requests enter the model in different ways. Waiting is weighted by party size and is convex: each extra minute costs more the longer someone has waited. Riding, at half a point per passenger-minute, and driving, at a tenth per kilometre, always count less than waiting. A request given to no van in this round is postponed; postponing has a price, plus a large constant, so the plan first serves as many requests as its candidates allow. Seats and pickup-before-drop-off are hard constraints; ride time has a softer guardrail. In this example, picking up the rider who has waited eight minutes first costs 66.5 points; the other order costs 81. *(optional)* That rider would pass fifteen minutes. ‘Optimal’ means best among the candidate plans generated at that decision moment—not the best possible whole evening.

**Transition** > The van optimizer stays fixed. What we change is the transfer rule.

<a id="s17"></a>
## 17 · We changed the transfer decision, not the van dispatcher (69 s)
**Context.** Defines all six rules from the code, before any result.

> We tested six rules, one at a time. Vans only never transfers. Wait ten minutes and Wait fifteen minutes move a request once it has waited that long. Unassigned for ten minutes moves a request left out of every van plan for ten minutes in a row. Predicted total wait exceeds fifteen minutes uses the van plan: predicted total wait equals predicted pickup clock time minus request clock time. And Lyft arrives sooner fires if the predicted van pickup is later than now plus the two-minute ordering lag, an eight-minute typical Lyft delay and a two-minute margin. We call these last two the predictive rules; the first ones use only time. Only requests still waiting, not committed to a van, are eligible. The thresholds were specified before any run.

**Transition** > Here is that last rule, worked through.

<a id="s18"></a>
## 18 · What does ‘Lyft arrives sooner’ actually compare? (64 s)
**Context.** One verified case, on a small designed evening.

> The rule compares predicted van pickup with expected Lyft pickup, including the ordering delay. On a small designed evening, a request arrives at about 6:16. At 6:17 the van plan predicts pickup at 6:30 and eight seconds. A Lyft ordered then is expected at 6:27: two minutes to place the order plus a typical eight-minute delay. That is three minutes eight seconds sooner, more than the two-minute margin, so the request moves. The Lyft is ordered at 6:19 and reaches the curb at 6:27, ten and a half minutes after the request. The van pickup time is a prediction. We do not observe what that van would have done after choosing a different action.

**Transition** > Testing at this level of detail also exposed a weakness.

<a id="s19"></a>
## 19 · A cheap postponement price could keep a rider waiting (60 s)
**Context.** A flaw found by testing, compared, and only partly fixed.

> The first formulation could price postponement more cheaply than a physically possible pickup. At 6:15 on the designed evening, a party of five had waited fifteen minutes. Postponing them was priced at 262.5 points, but the earliest pickup any van could actually make was worth about 436. We compared three versions over that whole evening and adopted the one that removes the flaw without adding variables: price postponement at the earliest time any van could physically arrive. The adopted approximation reduced the worst wait in this designed case. It did not reduce average waiting. And it is still optimistic, because it ignores the nearest van's other work.

**Transition** > With the model settled, how do we compare rules fairly?

<a id="s20"></a>
## 20 · Replay the same night; change one rule (44 s)
**Context.** The experimental design behind every result.

> Each rule faces the same requests and hidden rider inputs, so differences reflect the rule within this specified model. We replay each constructed night six times, with the same requests, hidden traits, Lyft delays and vans, changing only the rule. Thirty nights replayed six ways are thirty paired scenarios—not 180 independent nights. Pairing removes night-to-night differences from each comparison; it does not make the nights representative of April. The settings are provisional, including the placeholder patience.

**Transition** > Before trusting any result, we checked the implementation. **⇄**

---

<a id="s21"></a>
## 21 · We checked implementation before interpreting outcomes (54 s)
**Context.** Verification versus validation, and who wrote the code.

> Verification asks whether the code implements the specified model. Validation asks whether the model represents the real service. On verification: three small designed evenings reproduce hand-computed event times to the second. A separate brute-force program checked about 290,000 plan combinations on a designed evening and always agreed with the optimizer. 253 automated tests pass, and the reruns we sampled were byte-identical. We should be clear: AI wrote the simulator code and the checks, under our direction. Separate implementations are useful checks, but they share our assumptions and do not replace our own understanding. Validation against real riders is still ahead.

**Transition** > Now, what the rules did.

<a id="s22"></a>
## 22 · The predictive rules reached more requests promptly—and used more Lyft (64 s)
**Context.** The main result, with its conditions in the subtitle.

> These are thirty constructed burst-demand nights with provisional rider behaviour. Each bar is the share of all requests a vehicle reached at the curb within fifteen minutes—curb arrival, not boarding or a completed trip. In this two-van pilot, the predictive rules reached about three quarters of requests within fifteen minutes, compared with about half under vans only. They also used roughly nine to ten and a half Lyft orders per night. The waiting-time rules added little, partly because a rider moved after ten minutes almost never counts within fifteen; on requests picked up, the order is the same. This comparison does not isolate the benefit of prediction at an equal Lyft budget.

**Transition** > But reaching a rider with a Lyft is not the end of the story.

<a id="s23"></a>
## 23 · Moving a request to Lyft does not end its wait (58 s)
**Context.** What happens after transfer, stated no more strongly than the evidence.

> The rider still waits through ordering and Lyft arrival. Their original patience clock continues running. Under Wait ten minutes, 95 of 196 transferred requests cancelled before their Lyft arrived, some before it was even ordered; under the prediction rules, about a third. Riders moved by the prediction rules had usually waited less when they were moved. With our placeholder patience, where giving up becomes likelier the longer someone has waited, that is consistent with their lower share lost after transfer. It is a possible contributing mechanism, not an isolated cause, and whether the gap survives other patience assumptions is untested.

**Transition** > So rules trade service against Lyft use. How do we compare them?

<a id="s24"></a>
## 24 · Better service and lower Lyft use can point to different choices (66 s)
**Context.** Pareto dominance, used descriptively.

> A tested rule is dominated if another tested rule is at least as good on both selected objectives and strictly better on one. In the small picture, A dominates B; A and C do not dominate each other. On the thirty-night means, five of our six rules are not dominated. Vans only stays nondominated simply because it uses no Lyft. Unassigned for ten minutes differs from vans only by about one request in 840, so it is effectively a tie that uses slightly more Lyft; we apply no noise margin yet. Nondominated does not mean recommended. This is the nondominated set among six tested rules under these two objectives—not the complete frontier of possible policies. *(optional)* Adding objectives or criteria could change the assessment.

**Transition** > Which raises a natural question.

<a id="s25"></a>
## 25 · Could we choose the transfer policy systematically? (66 s)
**Context.** Leader–follower as a proposed extension, stated precisely.

> One possible extension is to optimize transfer policy while anticipating how the routing dispatcher responds. A policy designer chooses the rule and threshold; the dispatcher responds by re-planning; the outcomes inform the choice. This is proposed, not implemented. It would be bilevel because the dispatcher optimizes its own routing points, which differ from the designer's service and Lyft criteria. A finite search does find the best option in a finite set for the average over our sampled nights, but not over all policies or every continuous threshold. *(optional)* To state it precisely, we would still need to define the leader's choices, the follower's problem and timing, how ties are treated, the expectation over nights, and the weight on Lyft use.

**Transition** > Before choosing anything, we need to know which assumptions matter. **⇄**

---

<a id="s26"></a>
## 26 · Which assumptions could change the answer? (54 s)
**Context.** Limits ranked by how they could change the interpretation.

> The findings are conditional on the evenings and behaviours we constructed. Patience is the assumption we most expect to matter, though we have not tested that: it sets how many riders give up and the losses after transfer. Lyft delay: a slower or more variable Lyft could weaken transfers; under our placeholder patience, late transfers most. Workload: the pilot is deliberately heavy; at lighter load the rules may barely differ. Geography changes van reach and predictions. *(optional)* And the candidate restriction, three new pickups per van, shapes both van performance and the predictions the rules read.

**Transition** > That ordering tells us what to test next.

<a id="s27"></a>
## 27 · Test robustness before fine-tuning a winner (40 s)
**Context.** Proposed next steps, in order.

> Next, we should test whether the findings survive different rider-patience and Lyft-delay assumptions, while checking feasibility at the larger fleet size. Then the team must agree how much extra Lyft use one more rider reached is worth, compute confidence intervals across the paired nights, and only then search over thresholds. Order matters: a threshold tuned to placeholder behaviour would be tuned to our assumptions, not to the service.

**Transition** > So, what can we defend today?

<a id="s28"></a>
## 28 · What we can defend today (28 s)
**Context.** The conditional answer; no universal recommendation.

> Aggregate data did not give us individual journeys. It gave us constraints for building plausible evenings. Within our specified pilot, predictive transfer rules improved timely curb arrival while using more Lyft. Choosing a policy requires testing the assumptions and deciding what trade-off is acceptable. Thank you; we welcome your questions.
