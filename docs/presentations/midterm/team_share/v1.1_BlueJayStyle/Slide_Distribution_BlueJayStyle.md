# Slide distribution and scripts: BlueJayStyle deck

**Deck:** [BlueJay_Midterm_v0.4_BlueJayStyle.pptx](BlueJay_Midterm_v0.4_BlueJayStyle.pptx), the restyled version (42 slides), saved here unchanged.  
**Script text:** copied word for word from `v0.4/speaking_script.md`. Only the slide numbers are new. Handoff sentences come from the team pack (`team_share/src/content.py`).  
**Rule of thumb:** new slide number = old slide number + 3 for slides 4–31; backups B1–B9 are now slides 34–42.

## Overview: who presents which slides

| Presenter | New slides | Old slides (v1.0 pack) | Scripted time |
|---|---|---|---|
| Irfan Setiadi | 1–3 (intro), 4–8 | 1–5 | about 4:13 |
| Miles Zhou | 9–16 | 6–13 | about 7:47 |
| Youzhi Zhang | 17–24 | 14–21 | about 8:10 |
| Vignesh Rajesh Babu | 25–31, 32 (thank you) | 22–28 | about 6:16 |

Total scripted narration about 26:26 plus pauses and handoffs (about 27 min, an estimate, not rehearsed). Slides 1–3 and 32 are new and have no script yet.

> **Please confirm:** the new intro slides 1–3 are placed with Irfan (opening presenter) and the thank-you slide 32 with Vignesh (closing presenter). This is a suggestion, not a team decision.

## Slide-by-slide map

| New # | Old # | Title | Presenter |
|---|---|---|---|
| 1 | — (new) | Team logo (4SIGHT) | Irfan Setiadi |
| 2 | — (new) | Team introduction (four presenters, course, Prof. Kearsley) | Irfan Setiadi |
| 3 | — (new) | OPTIMIZING: The Blue Jay Night Ride Shuttle (project title) | Irfan Setiadi |
| 4 | 1 | When should Night Ride move a waiting request to Lyft? | Irfan Setiadi |
| 5 | 2 | The service and one request | Irfan Setiadi |
| 6 | 3 | Where we started | Irfan Setiadi |
| 7 | 4 | Where we started: numbers we later corrected | Irfan Setiadi |
| 8 | 5 | We narrowed the question to one controllable decision | Irfan Setiadi |
| 9 | 6 | April describes totals—not individual journeys | Miles Zhou |
| 10 | 7 | How busy should a constructed evening be? | Miles Zhou |
| 11 | 8 | We started with a smaller, deliberately demanding hour | Miles Zhou |
| 12 | 9 | Knowing the endpoints does not identify the journeys | Miles Zhou |
| 13 | 10 | One average can hide very different groups | Miles Zhou |
| 14 | 11 | One status label hides different events | Miles Zhou |
| 15 | 12 | The simulator needs a probability at vehicle arrival | Miles Zhou |
| 16 | 13 | The evidence becomes a scenario blueprint | Miles Zhou |
| 17 | 14 | Three components have different jobs | Youzhi Zhang |
| 18 | 15 | The same decision cycle repeats as the evening unfolds | Youzhi Zhang |
| 19 | 16 | The optimizer compares the consequences of candidate plans | Youzhi Zhang |
| 20 | 17 | We changed the transfer decision, not the van dispatcher | Youzhi Zhang |
| 21 | 18 | What does ‘Lyft arrives sooner’ actually compare? | Youzhi Zhang |
| 22 | 19 | A cheap postponement price could keep a rider waiting | Youzhi Zhang |
| 23 | 20 | Replay the same night; change one rule | Youzhi Zhang |
| 24 | 21 | We checked implementation before interpreting outcomes | Youzhi Zhang |
| 25 | 22 | The predictive rules reached more requests promptly—and used more Lyft | Vignesh Rajesh Babu |
| 26 | 23 | Moving a request to Lyft does not end its wait | Vignesh Rajesh Babu |
| 27 | 24 | Better service and lower Lyft use can point to different choices | Vignesh Rajesh Babu |
| 28 | 25 | Could we choose the transfer policy systematically? | Vignesh Rajesh Babu |
| 29 | 26 | Which assumptions could change the answer? | Vignesh Rajesh Babu |
| 30 | 27 | Test robustness before fine-tuning a winner | Vignesh Rajesh Babu |
| 31 | 28 | What we can defend today | Vignesh Rajesh Babu |
| 32 | — (new) | THANK YOU (closing image) | Vignesh Rajesh Babu |
| 33 | 29 | Backup slides (divider) | Q&A, any |
| 34 | 30 | B1 Code key: plain rule names and file codes | Q&A, any |
| 35 | 31 | B2 The route-selection MILP and the M bound | Q&A, any |
| 36 | 32 | B3 Event order, triggers and commitments | Q&A, any |
| 37 | 33 | B4 Where each input comes from | Q&A, any |
| 38 | 34 | B5 Three postponement prices compared | Q&A, any |
| 39 | 35 | B6 All metrics by rule, 30 nights | Q&A, any |
| 40 | 36 | B7 Trade-off night by night | Q&A, any |
| 41 | 37 | B8 Numerical diagnostics | Q&A, any |
| 42 | 38 | B9 Corrected proposal claims | Q&A, any |

## Q&A jump table (new numbers)

In PowerPoint slide show, type the number and press Enter. Type **31** and press Enter to return to the close.

| Question is about | Go to |
|---|---|
| Codes in files | B1 (34) |
| The MILP, the M bound, "optimal" | B2 (35) |
| Event order, triggers, commitments | B3 (36) |
| Where an input comes from | B4 (37) |
| Postponement prices | B5 (38) |
| Any metric by rule | B6 (39) |
| Pareto night by night | B7 (40) |
| Diagnostics, run times, ride-time excesses | B8 (41) |
| Proposal corrections | B9 (42) |

## Things to know about the restyled deck

- **The number badge printed on each slide still shows the old number** (for example new slide 13 shows "10"). Use the new numbers in this sheet when speaking or jumping.
- **Text references on slides use old numbers too**: "back to slide 17", "slide 16" (on the group-size slide), "slides 6–27". The click-through links themselves still go to the right slides.
- **Old slide 1's script says "Good afternoon, we are Team FourSight"**, but the team is now introduced on new slide 2. Irfan may want to adjust the wording when speaking.
- The Q&A ownership and backup slides in the v1.0 guide and briefs use old numbers; add 3 (main) or 4 (backups) to convert.

---

## Scripts by presenter

### Irfan Setiadi

#### Slide 1 · Team logo (4SIGHT)
_New slide. No script yet._

#### Slide 2 · Team introduction (four presenters, course, Prof. Kearsley)
_New slide. No script yet._

#### Slide 3 · OPTIMIZING: The Blue Jay Night Ride Shuttle (project title)
_New slide. No script yet._

#### Slide 4 · When should Night Ride move a waiting request to Lyft? (42 s) <sub>old slide 1</sub>

**Context.** Opens the talk with the decision, before any data or model.

> We began with a dispatch problem. The data led us first to a modelling problem. Good afternoon, we are Team FourSight. Our question is simple to state: when a rider has been waiting for a Night Ride van, when should that request be moved to Lyft instead? *(optional)* Today we will show what April's aggregate data let us build, how we turned it into constructed evenings, and what our first simulations revealed.

**Transition** > First, the service itself, and one request.

#### Slide 5 · The service and one request (55 s) <sub>old slide 2</sub>

**Context.** Gives the vocabulary that every later number depends on.

> Homewood-area Night Ride pools requests in shared vans. A dispatcher can move waiting riders to Lyft. We are studying when that transfer should happen. Here is one request's journey: request, wait, the vehicle reaches the curb, boarding, drop-off. It breaks if the rider gives up while waiting, a cancellation, or is absent when the van arrives, a no-show after a three-minute wait. Four words matter later, and they are on the tiles: booking, Lyft order, curb arrival, and pickup, the rider boarding. Each Lyft order is an extra trip Hopkins pays for, so moving riders to Lyft has a price.

**Transition** > Our September proposal approached this differently.

#### Slide 6 · Where we started (52 s) <sub>old slide 3</sub>

**Context.** The mandatory recap, shown with the proposal's own slides.

> Our original plan was to reconstruct service nights and study dispatch decisions using an optimization model. These are two slides from that proposal. On the left, the data plan: aggregate dashboards were available, and de-identified trip-level extracts were coming, with request, pickup and drop-off times for each ride. Trip-level data would let us replay actual service nights. On the right, the method: compare fast heuristics, a rolling-horizon optimization model and a hybrid, all on the same request stream. Those trip-level extracts never arrived, so real nights could not be replayed.

**Transition** > The proposal also contained numbers we later had to correct.

#### Slide 7 · Where we started: numbers we later corrected (50 s) <sub>old slide 4</sub>

**Context.** Corrects superseded numbers instead of silently repeating them.

> Four numbers on these original slides were wrong or misread. One: "about 5,100 rides per hour at 6 pm" is a total over thirty days, so about 170 rides in one evening's six o'clock hour. Two: "about 28 vans" is the dashboard's all-services average, not a Homewood-only count. *(optional)* Three: the 7 pm bar shows 4,900; our digitized value is about 3,960. Four: "one in four trips overflow to Lyft" is really a share of riders: 24.5 percent of riders rode Lyft. These corrections shaped everything after.

**Transition** > With aggregate data only, we narrowed the question.

#### Slide 8 · We narrowed the question to one controllable decision (54 s) <sub>old slide 5</sub>

**Context.** States the pivot as a scope choice, not as a claim about what synthetic data forbid.

> We now hold one specified van dispatcher fixed and change only the Lyft transfer rule. This lets us study how the timing and information used by that rule change service and Lyft use. It is the question we chose; we don't know the internals of Hopkins' real dispatcher; and a controlled comparison needs everything else held fixed. Our van dispatcher re-plans every two minutes and at each new request, cancellation or no-show while waiting, or van coming on duty, modelled on the vendor TransLoc's published design from 2016. That is our modelling choice, not verified current Hopkins practice.

**Transition** > So what exactly do April's dashboards contain? **⇄**

**⇄ Handoff, Irfan Setiadi → Miles Zhou** (from the team pack) > That gives us the question. Miles will now explain how April's aggregate data became the ingredients of our scenarios.

### Miles Zhou

#### Slide 9 · April describes totals—not individual journeys (58 s) <sub>old slide 6</sub>

**Context.** The evidence boundary that forces every later assumption.

> We know how many requests ended in each status, where pickups and drop-offs accumulated, and how activity varied by hour. We cannot reconstruct each rider's journey. *(optional)* On the left is what April gives; on the right, what it never gives: when a rider asked, where they went, how long they waited, and what happened next. Throughout the talk we label inputs. Observed means read from the dashboards. Derived means computed from observed numbers. Assumed means our choice, to be tested; designed means an experiment setting we chose. We therefore built plausible evenings from the evidence, while keeping the missing pieces visible.

**Transition** > The first piece is how busy an evening should be.

#### Slide 10 · How busy should a constructed evening be? (64 s) <sub>old slide 7</sub>

**Context.** Volume, derived step by step, with its assumptions in plain view.

> We estimated a workload from April's completed rides, request-to-completion ratio and reported vehicle availability. About 5,100 completed rides at six o'clock over thirty days is about 170 in one evening. April had about 2.09 requests for every completed ride, so roughly 355 requests in that hour. Divided by 27.6 vehicles on duty, that is about 12.85 requests per vehicle per hour. This assumes the monthly request-to-completion ratio applies within the hour, and uses vehicle availability reported across services. It is an estimated workload, not observed arrivals. Our planned evening uses five vans, a team design choice; each hour then gets its own count, 64, 50 and 54: 168 requests. That five-van evening is planned, not yet run.

**Transition** > What we actually ran is smaller, and deliberately harder.

#### Slide 11 · We started with a smaller, deliberately demanding hour (56 s) <sub>old slide 8</sub>

**Context.** Says exactly which experiment produced the results.

> The current results come from two vans and 28 requests in one hour, repeated across 30 constructed nights. Each van has fourteen seats. Requests arrive between six and seven, and eleven of the 28 are placed in a burst between 6:20 and 6:30. Each of the 30 nights is different, and each is run under six transfer rules, defined shortly. This is a controlled pilot, not a reconstruction of a typical April night. Its load, fourteen requests per van-hour, is close to the 12.85 we estimated per vehicle across all services, but the burst concentrates demand on purpose, to stress the transfer decision.

**Transition** > Next, where those requests go.

#### Slide 12 · Knowing the endpoints does not identify the journeys (49 s) <sub>old slide 9</sub>

**Context.** Geography: the maps give totals per place, never pairs.

> Two different sets of trips can produce exactly the same pickup and drop-off totals. In this toy example, both versions have identical green totals, which are all the maps show, yet different trips. So pairing pickups with drop-offs is a modelling choice. We assumed nearby journeys were more likely, then balanced the synthetic trips to preserve the observed location totals. The rate at which distance lowers a pair's weight is our assumption; the data cannot identify it. *(optional)* The map shows one constructed hour built this way.

**Transition** > The next input is who travels together.

#### Slide 13 · One average can hide very different groups (61 s) <sub>old slide 10</sub>

**Context.** Party sizes affect seats and passenger-weighted waiting.

> April helps identify an average group size. It does not tell us the full distribution of groups. April gives about 1.39 van passengers per completed van request. Examples A and B have exactly that average, yet one has eight percent of requests with three or more riders and the other over twelve. That matters for seats in the van, and because our waiting penalty counts every passenger. Our mix covers all requests, so its mean is slightly higher. Our chosen group-size mix is an assumption informed by the average—not a distribution recovered from April. A party of five that is moved to Lyft rides together in one larger XL vehicle.

**Transition** > The hardest label on the dashboard is "Cancelled".

#### Slide 14 · One status label hides different events (62 s) <sub>old slide 11</sub>

**Context.** Separates an observation, an assumed status mapping and hidden patience.

> ‘Cancelled’ does not tell us whether a rider gave up or a dispatcher moved the request to Lyft. Almost half of April's requests ended "Canceled". We assume that requests moved to Lyft also close as "Canceled" in the van system, and we keep the share that is riders giving up as a range to test, fifty to seventy-five percent. To let riders give up in the simulator, each rider gets a private deadline the dispatcher cannot see, with a median of eighteen minutes. The patience distribution is provisional. It lets the simulator represent abandonment; it is not a behavioural distribution measured from April. *(optional)* Many patience distributions could produce the same cancellation share.

**Transition** > A similar puzzle hides in "No Show".

#### Slide 15 · The simulator needs a probability at vehicle arrival (55 s) <sub>old slide 12</sub>

**Context.** Same count, two denominators; the simulator needs the per-arrival one.

> The share of all requests marked ‘No Show’ is different from the chance of a no-show when a vehicle actually arrives. 2,359 no-shows out of all 50,297 requests is 4.7 percent. But a no-show can only happen when a vehicle arrives, and most cancelled requests never saw one. Out of van arrivals, completed rides plus no-shows, it is about 8.9 percent. That figure holds only if "No Show" was recorded after a real van arrival, "Completed" counts van trips, and Lyft hand-offs sit in "Canceled". Our arrival-based probability is provisional because it depends on how the dashboard statuses were recorded.

**Transition** > Together, these pieces form a scenario.

#### Slide 16 · The evidence becomes a scenario blueprint (62 s) <sub>old slide 13</sub>

**Context.** Gathers every input, with its status, before the model appears.

> A scenario combines evidence-based inputs, explicit assumptions and hidden rider behaviour. Demand: arrival times, locations, trip pairing and party sizes. Resources: vans, their fourteen seats and travel times, which we inflate by twenty percent as a placeholder. Hidden behaviour: patience, presence at the curb and Lyft delay; a transfer takes two minutes to order, then the Lyft takes about eight minutes typically. And experiment settings: the van dispatcher, held fixed, and the transfer rule, which we vary. Many inputs carry two labels, derived and assumed. One point matters for what follows: inputs are fixed before a run, but cancellations, no-shows and transfers are not. They are outcomes of the run, not counts we impose.

**Transition** > Now, the machinery that runs a scenario. **⇄**

**⇄ Handoff, Miles Zhou → Youzhi Zhang** (from the team pack) > Those inputs define the constructed evening. Youzhi will explain how the model makes decisions as that evening unfolds.

### Youzhi Zhang

#### Slide 17 · Three components have different jobs (65 s) <sub>old slide 14</sub>

**Context.** The full architecture, with the information boundary visible.

> Three components have different jobs. The simulator advances time and reveals events. The van optimizer chooses among feasible candidate plans. The transfer rule decides whether an eligible request moves to Lyft. *(optional)* The simulator holds the clock, the vans and every request's state; it reveals a request only when it arrives, and applies a hidden draw only when its event happens. The decision step, on the right, sees only what has happened: the van dispatcher generates candidate routes, an optimizer—a mixed-integer linear program—picks one per van, and the transfer rule reads those plans. Then the vans execute, and every event is recorded. Future requests, each rider's patience and presence, and the real Lyft delay stay hidden from the dispatcher.

**Transition** > These parts work together in one repeating cycle.

#### Slide 18 · The same decision cycle repeats as the evening unfolds (58 s) <sub>old slide 15</sub>

**Context.** The verified implementation order of one decision moment.

> The dispatcher sees requests that have arrived. It does not see future requests. Every two minutes, and at each new request, waiting-time cancellation or no-show, or van coming on duty, the same cycle runs. Reveal and update. Generate feasible routes for each van. Select one route per van. Evaluate the transfer rule for each request still waiting. Apply accepted transfers: those requests leave van planning, and the Lyft is ordered two minutes later. If anything was transferred, re-plan once. Then vans execute and commit to their next stop. The rule runs once per decision moment, so there is no cascade of transfers in the same second.

**Transition** > How does the optimizer pick a route?

#### Slide 19 · The optimizer compares the consequences of candidate plans (76 s) <sub>old slide 16</sub>

**Context.** The objective in blocks, one worked example, and what "optimal" means.

> Waiting, riding, driving and unresolved requests enter the model in different ways. Waiting is weighted by party size and is convex: each extra minute costs more the longer someone has waited. Riding, at half a point per passenger-minute, and driving, at a tenth per kilometre, always count less than waiting. A request given to no van in this round is postponed; postponing has a price, plus a large constant, so the plan first serves as many requests as its candidates allow. Seats and pickup-before-drop-off are hard constraints; ride time has a softer guardrail. In this example, picking up the rider who has waited eight minutes first costs 66.5 points; the other order costs 81. *(optional)* That rider would pass fifteen minutes. ‘Optimal’ means best among the candidate plans generated at that decision moment—not the best possible whole evening.

**Transition** > The van optimizer stays fixed. What we change is the transfer rule.

#### Slide 20 · We changed the transfer decision, not the van dispatcher (69 s) <sub>old slide 17</sub>

**Context.** Defines all six rules from the code, before any result.

> We tested six rules, one at a time. Vans only never transfers. Wait ten minutes and Wait fifteen minutes move a request once it has waited that long. Unassigned for ten minutes moves a request left out of every van plan for ten minutes in a row. Predicted total wait exceeds fifteen minutes uses the van plan: predicted total wait equals predicted pickup clock time minus request clock time. And Lyft arrives sooner fires if the predicted van pickup is later than now plus the two-minute ordering lag, an eight-minute typical Lyft delay and a two-minute margin. We call these last two the predictive rules; the first ones use only time. Only requests still waiting, not committed to a van, are eligible. The thresholds were specified before any run.

**Transition** > Here is that last rule, worked through.

#### Slide 21 · What does ‘Lyft arrives sooner’ actually compare? (64 s) <sub>old slide 18</sub>

**Context.** One verified case, on a small designed evening.

> The rule compares predicted van pickup with expected Lyft pickup, including the ordering delay. On a small designed evening, a request arrives at about 6:16. At 6:17 the van plan predicts pickup at 6:30 and eight seconds. A Lyft ordered then is expected at 6:27: two minutes to place the order plus a typical eight-minute delay. That is three minutes eight seconds sooner, more than the two-minute margin, so the request moves. The Lyft is ordered at 6:19 and reaches the curb at 6:27, ten and a half minutes after the request. The van pickup time is a prediction. We do not observe what that van would have done after choosing a different action.

**Transition** > Testing at this level of detail also exposed a weakness.

#### Slide 22 · A cheap postponement price could keep a rider waiting (60 s) <sub>old slide 19</sub>

**Context.** A flaw found by testing, compared, and only partly fixed.

> The first formulation could price postponement more cheaply than a physically possible pickup. At 6:15 on the designed evening, a party of five had waited fifteen minutes. Postponing them was priced at 262.5 points, but the earliest pickup any van could actually make was worth about 436. We compared three versions over that whole evening and adopted the one that removes the flaw without adding variables: price postponement at the earliest time any van could physically arrive. The adopted approximation reduced the worst wait in this designed case. It did not reduce average waiting. And it is still optimistic, because it ignores the nearest van's other work.

**Transition** > With the model settled, how do we compare rules fairly?

#### Slide 23 · Replay the same night; change one rule (44 s) <sub>old slide 20</sub>

**Context.** The experimental design behind every result.

> Each rule faces the same requests and hidden rider inputs, so differences reflect the rule within this specified model. We replay each constructed night six times, with the same requests, hidden traits, Lyft delays and vans, changing only the rule. Thirty nights replayed six ways are thirty paired scenarios—not 180 independent nights. Pairing removes night-to-night differences from each comparison; it does not make the nights representative of April. The settings are provisional, including the placeholder patience.

**Transition** > Before trusting any result, we checked the implementation. **⇄**

#### Slide 24 · We checked implementation before interpreting outcomes (54 s) <sub>old slide 21</sub>

**Context.** Verification versus validation, and who wrote the code.

> Verification asks whether the code implements the specified model. Validation asks whether the model represents the real service. On verification: three small designed evenings reproduce hand-computed event times to the second. A separate brute-force program checked about 290,000 plan combinations on a designed evening and always agreed with the optimizer. 253 automated tests pass, and the reruns we sampled were byte-identical. We should be clear: AI wrote the simulator code and the checks, under our direction. Separate implementations are useful checks, but they share our assumptions and do not replace our own understanding. Validation against real riders is still ahead.

**Transition** > Now, what the rules did.

**⇄ Handoff, Youzhi Zhang → Vignesh Rajesh Babu** (from the team pack) > We then replayed the same evenings under different transfer rules. Vignesh will explain what changed, what it means and what remains uncertain.

### Vignesh Rajesh Babu

#### Slide 25 · The predictive rules reached more requests promptly—and used more Lyft (64 s) <sub>old slide 22</sub>

**Context.** The main result, with its conditions in the subtitle.

> These are thirty constructed burst-demand nights with provisional rider behaviour. Each bar is the share of all requests a vehicle reached at the curb within fifteen minutes—curb arrival, not boarding or a completed trip. In this two-van pilot, the predictive rules reached about three quarters of requests within fifteen minutes, compared with about half under vans only. They also used roughly nine to ten and a half Lyft orders per night. The waiting-time rules added little, partly because a rider moved after ten minutes almost never counts within fifteen; on requests picked up, the order is the same. This comparison does not isolate the benefit of prediction at an equal Lyft budget.

**Transition** > But reaching a rider with a Lyft is not the end of the story.

#### Slide 26 · Moving a request to Lyft does not end its wait (58 s) <sub>old slide 23</sub>

**Context.** What happens after transfer, stated no more strongly than the evidence.

> The rider still waits through ordering and Lyft arrival. Their original patience clock continues running. Under Wait ten minutes, 95 of 196 transferred requests cancelled before their Lyft arrived, some before it was even ordered; under the prediction rules, about a third. Riders moved by the prediction rules had usually waited less when they were moved. With our placeholder patience, where giving up becomes likelier the longer someone has waited, that is consistent with their lower share lost after transfer. It is a possible contributing mechanism, not an isolated cause, and whether the gap survives other patience assumptions is untested.

**Transition** > So rules trade service against Lyft use. How do we compare them?

#### Slide 27 · Better service and lower Lyft use can point to different choices (66 s) <sub>old slide 24</sub>

**Context.** Pareto dominance, used descriptively.

> A tested rule is dominated if another tested rule is at least as good on both selected objectives and strictly better on one. In the small picture, A dominates B; A and C do not dominate each other. On the thirty-night means, five of our six rules are not dominated. Vans only stays nondominated simply because it uses no Lyft. Unassigned for ten minutes differs from vans only by about one request in 840, so it is effectively a tie that uses slightly more Lyft; we apply no noise margin yet. Nondominated does not mean recommended. This is the nondominated set among six tested rules under these two objectives—not the complete frontier of possible policies. *(optional)* Adding objectives or criteria could change the assessment.

**Transition** > Which raises a natural question.

#### Slide 28 · Could we choose the transfer policy systematically? (66 s) <sub>old slide 25</sub>

**Context.** Leader–follower as a proposed extension, stated precisely.

> One possible extension is to optimize transfer policy while anticipating how the routing dispatcher responds. A policy designer chooses the rule and threshold; the dispatcher responds by re-planning; the outcomes inform the choice. This is proposed, not implemented. It would be bilevel because the dispatcher optimizes its own routing points, which differ from the designer's service and Lyft criteria. A finite search does find the best option in a finite set for the average over our sampled nights, but not over all policies or every continuous threshold. *(optional)* To state it precisely, we would still need to define the leader's choices, the follower's problem and timing, how ties are treated, the expectation over nights, and the weight on Lyft use.

**Transition** > Before choosing anything, we need to know which assumptions matter. **⇄**

#### Slide 29 · Which assumptions could change the answer? (54 s) <sub>old slide 26</sub>

**Context.** Limits ranked by how they could change the interpretation.

> The findings are conditional on the evenings and behaviours we constructed. Patience is the assumption we most expect to matter, though we have not tested that: it sets how many riders give up and the losses after transfer. Lyft delay: a slower or more variable Lyft could weaken transfers; under our placeholder patience, late transfers most. Workload: the pilot is deliberately heavy; at lighter load the rules may barely differ. Geography changes van reach and predictions. *(optional)* And the candidate restriction, three new pickups per van, shapes both van performance and the predictions the rules read.

**Transition** > That ordering tells us what to test next.

#### Slide 30 · Test robustness before fine-tuning a winner (40 s) <sub>old slide 27</sub>

**Context.** Proposed next steps, in order.

> Next, we should test whether the findings survive different rider-patience and Lyft-delay assumptions, while checking feasibility at the larger fleet size. Then the team must agree how much extra Lyft use one more rider reached is worth, compute confidence intervals across the paired nights, and only then search over thresholds. Order matters: a threshold tuned to placeholder behaviour would be tuned to our assumptions, not to the service.

**Transition** > So, what can we defend today?

#### Slide 31 · What we can defend today (28 s) <sub>old slide 28</sub>

**Context.** The conditional answer; no universal recommendation.

> Aggregate data did not give us individual journeys. It gave us constraints for building plausible evenings. Within our specified pilot, predictive transfer rules improved timely curb arrival while using more Lyft. Choosing a policy requires testing the assumptions and deciding what trade-off is acceptable. Thank you; we welcome your questions.

#### Slide 32 · THANK YOU (closing image)
_New slide. No script yet; slide 31 already ends with "Thank you; we welcome your questions."_
