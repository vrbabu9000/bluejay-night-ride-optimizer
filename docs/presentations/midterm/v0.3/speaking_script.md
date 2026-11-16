# Midterm speaking script (content draft v0.3, 22 Oct 2026)

**Format:** 30 minutes in total: 20 minutes of presentation, then 10 minutes of questions.
**Deck:** `BlueJay_Midterm_v0.3.pptx` has 22 main slides; backups B1–B9 are slides 24–32.
**Speakers:** not yet assigned. Natural handoff points are marked **⇄** (after slides 4, 10, 16 and 20), so any split of the team works.
**Suggested splits.**
- 2 speakers: 1–10 / 11–22 (8 + 12 min), or 1–16 / 17–22.
- 3 speakers: 1–10 / 11–16 / 17–22 (8 / 6 / 6 min).
- 4 speakers: 1–10 / 11–16 / 17–20 / 21–22, or 1–4 / 5–10 / 11–16 / 17–22.
- 5 speakers: one per section.

At each ⇄ the outgoing speaker says the transition line; the incoming speaker starts with the next slide's first sentence, with no re-introduction. Whoever presents slide 21 should also take the leader–follower questions.
**Running long?** Drop these optional sentences: slide 6 "What stays unknown…"; slide 12 "because the long waiter would pass fifteen minutes"; slide 21 "and an agreed value on Lyft use"; slide 16 "That is fourteen bookings per van-hour…".
**Words.** "Booking" always means the rider's Night Ride request; the Lyft side is a "Lyft order". In files the Lyft order is called a booking, and the 2-min ordering lag is the "booking lag" (D-43).
**Reading this file.**
- Only the text in **Spoken** blocks (quoted, `>`) is said aloud. Including the spoken transitions, it is about 2,390 words: 19.1 min at 125 words per minute, leaving about 0.9 min for pauses, clicks and handoffs. Per-slide budgets are proportional to spoken length.
- *Preparation*, *Likely questions* and *Deeper* are for the presenter and are not spoken.
- Deeper teaching material is in [slide_explanations.md](slide_explanations.md), linked per slide.

## The whole journey in one paragraph
A rider who books Night Ride and waits can either stay with the van system or be transferred to a Lyft, and we wanted to understand that decision. April's dashboards showed demand and outcomes only as totals, never one rider's journey, so before testing any policy we first investigated what the numbers really meant: how many requests a van faces, which pickups go with which drop-offs, what a group-size average does and does not say, what "Canceled" counts, and which denominator a no-show rate uses. Each investigation supplied one part of a synthetic evening and exposed one assumption. We assembled those parts into a reproducible simulator with a route optimizer and a separate transfer rule, checked the code against hand-computed answers, fixed a weakness we found in its postponement price, and replayed the same synthetic evenings under six transfer rules. The replays showed that being assigned a van is not being picked up, that a transfer is not a completed trip, and that rules acting on predictions changed both service and Lyft use. They also showed what the model cannot yet claim, which tells us what to test next.

## Q&A jump table
In PowerPoint slide show, type the slide number and press Enter to jump; type 22 and Enter to return to the close.

| Question is about | Go to | Slide |
|---|---|---|
| Codes in files (R0…R3, L4, L5) | B1 | 24 |
| The MILP, the M bound, solver settings, "optimal" | B2 | 25 |
| Event order, commitment, curb wait, presence draw | B3 | 26 |
| Where an input comes from (patience, Lyft delay, × 1.2) | B4 | 27 |
| Postponement price alternatives | B5 | 28 |
| Any metric by rule (pickups, cancellations, van-km) | B6 | 29 |
| Pareto night by night, paired counts | B7 | 30 |
| Solver diagnostics, run times, ride-time excesses | B8 | 31 |
| Proposal corrections, why the study changed | B9 | 32 |
| Pareto picture / leader–follower | main | 20 / 21 |

## Codes (presenter reference only; never required of the audience)
| Say | Code in files |
|---|---|
| Vans only | R0 |
| Wait ten minutes | R1(10) |
| Wait fifteen minutes | R1(15) |
| Unassigned for ten minutes | R1u(10) |
| Predicted total wait exceeds fifteen minutes | R2(15) |
| Lyft arrives sooner | R3(2) |
| "a small designed evening" | L4 (L1–L3: answer-key evenings) |
| "the thirty-night pilot" | L5 |
| "the van optimizer" | dispatcher C (restricted route-selection MILP) |
| "the postponement price we chose" | pending price A |

---

<a id="s01"></a>
## Slide 1 · Testing Lyft transfer decisions for Blue Jay Night Ride · 0:00–0:22 (22 s)
**Context.** Opening; nothing assumed.

**Spoken**
> Good afternoon, we are Team FourSight: [names]. Our project is about one decision in Hopkins' Night Ride service: when a rider has been waiting for a van, should they be moved to a Lyft? Here is what that decision looks like for one booking.

*Preparation.* Keep it to one breath. The subtitle previews the three parts: what the data can tell us, how we built evenings, what replaying them showed.

*Deeper:* [explanations §1](slide_explanations.md#s01).

---

<a id="s02"></a>
## Slide 2 · One booking, several possible outcomes · 0:22–1:20 (58 s)
**Context.** We need the vocabulary of outcomes before any number.

**Spoken**
> A rider books in the app. One booking can carry several passengers. The booking can stay with the van system: a van reaches the curb and the rider boards, or the rider gives up first, which is a cancellation, or the rider isn't at the curb, which is a no-show after a three-minute wait. Or the dispatcher can transfer the booking to Lyft, and the same three outcomes appear again on the Lyft side. Four words matter later, and they are on the tiles: booking, passenger, curb arrival, and pickup, the rider boarding. So our question is: when should a waiting booking be moved to Lyft?

*Preparation.* The tree is the backbone of the talk: slides 18–19 return to its two branches. "Transfer" here means a dispatcher's decision; today a person sends the Lyft (JHU page), in our model a rule decides. In our model, a rider who is offered a Lyft accepts (an automatic-acceptance simplification); a small designed evening uses 90% acceptance.

*Likely questions.*
- **Can a rider refuse the Lyft?** In reality, yes. In the pilot we assume they accept; the designed evening includes refusals.
- **Is the three-minute wait real?** Yes, it is the published curb-wait policy.

*Deeper:* [explanations §2](slide_explanations.md#s02). *Sources:* JHU service page (via `transloc_operations.md`); spec §5–§6.

**Transition (spoken)** > We first tried to answer this with a different plan.

---

<a id="s03"></a>
## Slide 3 · What we originally proposed · 1:20–2:11 (51 s)
**Context.** Continuity with the proposal the class saw.

**Spoken**
> In September we proposed to replay real service nights from trip records and compare dispatch methods: simple rules against a mathematical optimization model re-solved as requests arrive. Lyft was to be overflow chosen inside that optimizer, and the published targets hard limits. Those were ambitions that depended on trip-level records. Three proposal numbers also needed correcting. "5,100 rides per hour at six" was a thirty-day total, about 170 per evening. "28 vans" counted all services, not only Homewood. And "one in four trips overflow to Lyft" is a share of riders, not of trips.

*Preparation.* Don't apologise; this is the starting point of the investigation. The proposal deck itself is unchanged in the repository.

*Likely questions.*
- **Why did you trust 5,100 at first?** It is the dashboard's hourly bar; its subtitle says "summed over 30 days", which we initially read as hourly.
- **Why not just compare dispatch algorithms, as proposed?** On synthetic nights an algorithm comparison would mostly compare our own assumptions. Holding the van optimizer fixed and changing only the transfer rule isolates the decision we care about (B9; D-25, D-51).

*Deeper:* [explanations §3](slide_explanations.md#s03); backup B9 (slide 32). *Sources:* proposal deck; methodology §1a.

**Transition (spoken)** > So what did the data actually contain?

---

<a id="s04"></a>
## Slide 4 · What April's dashboards actually contain · 2:11–2:59 (48 s)
**Context.** The trip records never arrived; the dashboards are our only evidence.

**Spoken**
> The trip records never arrived. What we have are April's dashboards, and they are informative: monthly bookings by status, completed rides by hour, vehicles on duty by hour, maps of pickup and drop-off counts, wait-time percentiles, and riders by van and by Lyft. What they never show is a single journey: who asked when, from where, how long they waited, and what happened next. Every number is a total or a share. So before testing any policy, we had to work out what those totals really meant.

*Preparation.* The April dashboard file is restricted; show only aggregate numbers we digitized, never screenshots.

*Likely questions.*
- **How were numbers read?** Charts were digitized pixel by pixel and cross-checked against tooltips (for example 5,089 digitized vs 5,098 tooltip).

*Deeper:* [explanations §4](slide_explanations.md#s04). *Sources:* `data/processed/obs_*` (restricted source, aggregate copies); methodology §3–§4.

**Transition (spoken)** > That became our first task. **⇄ natural handoff**

---

<a id="s05"></a>
## Slide 5 · First, we investigated the numbers · 2:59–3:25 (26 s)
**Context.** A breathing slide that sets three questions for the next five slides.

**Spoken**
> We asked three questions of the dashboards. How many requests does a van actually face? Which pickups go with which drop-offs? And what do "Canceled" and "No Show" really count? Each answer gave us one part of a synthetic evening, and each exposed one assumption we had to make.

*Preparation.*
- **The chips** reappear on slides 6, 7 and 9; the first card also covers group size (slide 8).
- **Status labels** (OBSERVED, DERIVED, ASSUMED, DESIGNED, SIMULATED) are defined in the bottom line; point at it once.
- **One number, three spellings:** 5,089 is our digitized bar, the dashboard tooltip says 5,098, and we say "about 5,100". The 0.2% difference changes nothing downstream.

*Deeper:* [explanations §5](slide_explanations.md#s05).

**Transition (spoken)** > Start with volume.

---

<a id="s06"></a>
## Slide 6 · How many requests should our scenario contain? · 3:25–4:25 (60 s)
**Context.** Volume is the first input; it must be per van, because we simulate a small fleet.

**Spoken**
> The bars are completed rides by hour, summed over thirty days. At six o'clock that is about 5,100, so about 170 completed rides in one evening's six o'clock hour. April recorded about 2.09 bookings for every completed ride, so roughly 355 bookings arrived in that hour. With 27.6 vehicles on duty, that is about 12.85 bookings per vehicle per hour. A five-van evening would therefore face 64, 50 and 54 bookings in its first three hours. What stays unknown is how many of those vehicles served Homewood, and how many bookings were repeats. So these 168 bookings in three hours are a derived workload, not a measurement.

*Preparation.*
- **Choice:** load per van, so the scenario scales with the fleet we simulate.
- **Alternative:** total April demand, which is far beyond a five-van model.
- **Caveat:** the illustrative range is about 150–260 per three-hour evening. It is not a confidence interval.
- **The pilot (slide 16)** uses 2 vans and 28 bookings in an hour, a heavier load by design.
- **Why five vans?** It is the planned reference evening of the design (spec §8), not an observed Homewood fleet.
- **Why 54 after 50?** Each hour uses its own rides and its own vehicles on duty (fewer vehicles at 8 pm).

*Likely questions.*
- **Why 2.09?** 50,297 bookings ÷ 24,095 completed.
- **Why per vehicle?** We simulate five vans, not the whole fleet.
- **Rounding?** Hour by hour, with the largest-remainder rule.

*Deeper:* [explanations §6](slide_explanations.md#s06). *Sources:* obs_p09, obs_p06, obs_p07; decision log D-35, D-36, D-49.

**Transition (spoken)** > Knowing how many bookings arrive, we needed to know where they go.

---

<a id="s07"></a>
## Slide 7 · Pickup and drop-off maps do not identify trips · 4:25–5:21 (56 s)
**Context.** Geography is the second input; the maps give totals per place, not pairs.

**Spoken**
> The maps tell us how many pickups and how many drop-offs each place had. They never say which pickup went with which drop-off. On the left: two places send two riders each, and two places receive two each. Both tables match those totals exactly, yet they describe different trips. So pairing is a choice. We assumed nearby trips are more common, with the weight shrinking about ten percent per extra minute of driving, and then scaled the table until it matched April's totals exactly. The map shows one synthetic hour built this way. The data cannot tell us the shrink rate; that is our assumption.

*Preparation.*
- **Method:** a gravity prior plus iterative proportional fitting. The decay is e^(−0.1 × minutes), about 0.905 per minute.
- **Alternatives:** no distance preference (decay 0), or 0.2.
- **Not yet tested:** a spread-out geography variant is built but no experiment has used it.

*Likely questions.*
- **Why is distance decay reasonable?** It is the standard transport-planning prior. The fitting then reproduces both April totals to about 10⁻¹⁰.

*Deeper:* [explanations §7](slide_explanations.md#s07). *Sources:* decision log D-18; design trail §5.

**Transition (spoken)** > The next input is who travels together.

---

<a id="s08"></a>
## Slide 8 · An average group size leaves many possibilities · 5:21–6:00 (39 s)
**Context.** Group size decides seats and Lyft vehicle size.

**Spoken**
> April gives one number: 1.386 van passengers per completed van booking. That is an average. These two hypothetical distributions both have exactly that average, yet one has eight percent of bookings with three or more riders and the other just over twelve. That matters for seats, and a party of five needs a larger Lyft. So our distribution is an assumption chosen near the average, with one percent parties of five.

*Preparation.*
- **Our input** describes all bookings, with mean 1.405. The April figure covers completed van bookings only, so the two are different quantities.
- **XL:** a transferred party of five rides together in an XL. That rule came from a team correction, not from the data.

*Likely questions.*
- **Why not fit the distribution?** One mean cannot identify five probabilities.
- **Why is your mean 1.405, not 1.386?** Ours describes all bookings; April's 1.386 covers completed van bookings only, so they are different quantities.

*Deeper:* [explanations §8](slide_explanations.md#s08). *Sources:* obs_p08/p07; D-38, D-33.

**Transition (spoken)** > Then the hardest word on the dashboard.

---

<a id="s09"></a>
## Slide 9 · What does "Canceled" mean? · 6:00–6:52 (52 s)
**Context.** "Canceled" drives the patience assumption.

**Spoken**
> Almost half of April's bookings, 23,843 of 50,297, ended "Canceled". It is tempting to read that as impatient riders. But the label probably also includes bookings the dispatcher moved to Lyft; we assume those close as "Canceled" in the van system. The data cannot separate the two. To let riders give up in the model, each rider gets a hidden personal deadline, a placeholder for now, and keep the share of "Canceled" that is truly riders giving up as a range, fifty to seventy-five percent, to check later. The point is that "Canceled" does not mean abandonment.

*Preparation.* The patience placeholder is a Weibull distribution with median 18 minutes. It is a placeholder until calibration, and results depend on it (slide 19).

*Likely questions.*
- **Why 50–75%?** It is a sensitivity range reconstructed from the Lyft rider share and assumed party sizes. It is not established by the data.

*Deeper:* [explanations §9](slide_explanations.md#s09). *Sources:* obs_p07; D-39, D-49.

**Transition (spoken)** > The last puzzle is a denominator.

---

<a id="s10"></a>
## Slide 10 · Why the no-show denominator matters · 6:52–7:38 (46 s)
**Context.** The no-show rate enters every vehicle arrival.

**Spoken**
> There were 2,359 no-shows. Divided by all bookings, that is 4.7 percent. But a no-show can only happen when a vehicle reaches the curb, and most cancelled bookings never had one. Divided by van arrivals, completed rides plus no-shows, it is about 8.9 percent. That only holds if "No Show" is recorded after a real van arrival and "Completed" counts van trips. We use 8.9 percent per arrival, provisionally. The same count gives two rates, depending on what you divide by.

*Preparation.*
- **The status mapping is assumed, not verified.** Three conditions: "Completed" means van-completed; "No Show" follows a real van arrival; Lyft hand-offs sit in "Canceled". If any fails, p moves.
- **Shared presence draw:** one draw per rider, used whichever vehicle arrives.

*Likely questions.*
- **Why does it matter?** 4.7% per arrival would undercount no-shows by about half.
- **Why use a van rate for Lyft?** An assumption (D-48): one presence draw per rider, the same probability for every mode. Separate rates are a deferred sensitivity.
- **Your scenario files say 4.7%?** A known erratum (D-48): those fields are all-booking shares that the simulator does not read; 8.9% is set in the run configuration.
- **Is no-show related to how long the rider waited?** Not in our model; presence is one draw per rider, independent of the wait. The data cannot identify a dependence.

*Deeper:* [explanations §10](slide_explanations.md#s10). *Sources:* obs_p07; D-40, D-48; methodology Appendix C.

**Transition (spoken)** > With these pieces we could assemble an evening. **⇄ natural handoff**

---

<a id="s11"></a>
## Slide 11 · Our synthetic evening is assembled · 7:38–8:37 (59 s)
**Context.** The five investigations become inputs; now they run inside a simulator.

**Spoken**
> Here are the pieces together. Bookings with times, places and party sizes, and vans on duty, are what a dispatcher can see once they happen. Each rider also carries hidden traits: a patience deadline, whether they will be at the curb, and how long their Lyft would take. The simulator is the referee. It moves the vans and reveals a hidden trait only when its moment comes. The dispatcher, which in our model is the van optimizer plus the transfer rule, never sees the hidden traits, only predictions. We use two kinds of evening: small designed ones with hand-computed answers, and thirty randomized one-hour nights for the pilot.

*Preparation.* Two kinds of evening:
- **Designed evenings:** small, with hand-computed answers.
- **Randomized nights:** the thirty-night pilot.

All inputs are frozen and hash-checked.

*Likely questions.*
- **Are travel times real?** Road-network times from a local OSRM router on OpenStreetMap, multiplied by an assumed 1.2 for the vans; the multiplier is a placeholder to calibrate (spec §5).
- **Your evenings match April by construction, so what does that prove?** Nothing about validity. They reproduce April's totals, which makes them plausible inputs, not validated ones; calibration against outcome shares and wait percentiles has not started.

*Deeper:* [explanations §11](slide_explanations.md#s11); backups B3 (slide 26) and B4 (slide 27). *Sources:* spec §1, §17; methodology §2–§3.

**Transition (spoken)** > Inside the simulator, a van optimizer makes the plans.

---

<a id="s12"></a>
## Slide 12 · How the van optimizer chooses a plan · 8:37–9:58 (81 s)
**Context.** Before comparing transfer rules we must show the fixed thing they act on.

**Spoken**
> The top strip is the loop, run every two minutes and at every new event: reveal what happened, generate each van's feasible routes, choose one route per van, apply the transfer rule, re-plan once if needed, and drive. The choice of routes is a mixed-integer linear program, MILP for short. It scores each feasible route in points, not money: each waiting minute costs more the longer someone has waited, plus half a point per passenger-minute riding and a tenth per kilometre. In this small example, picking up the long waiter first costs 66.5 points, the other order 81, because the long waiter would pass fifteen minutes. Leaving a booking waiting is also priced, but a large constant makes serving as many bookings as possible come first. "Optimal" here means optimal among the routes we generated at that moment, not over every route, and not over the evening.

*Preparation.*
- **Constraints:** seats and pickup before drop-off are hard. The ride-time limit max(25 min, 2 × direct + 5 min) is a guardrail: no plan may create or worsen an excess, but a no-show wait can still push a ride over (slide 22).
- **The candidate set:** every subset of at most 3 new pickups per van, each ordered exactly.
- **The example is illustrative**, with dwell omitted.
- **Alternative:** a heuristic dispatcher, kept as a contingency.

*Likely questions.*
- **Why up to 3 new pickups?** Exact ordering with 4 took minutes per decision in Python.
- **Is it truly optimal?** Yes over the generated candidates, proven by the solver at each decision moment.
- **Optimal, given 41 incomplete tie searches?** The main solve was proven optimal at all 13,663 decision moments. The 41 incomplete searches only looked for equally good alternatives, and full enumeration shows a unique optimum in each (B8).

*Deeper:* [explanations §12](slide_explanations.md#s12); backup B2 (slide 25). *Sources:* model_design v0.5 §3–§4; D-29, D-47, D-52.

**Transition (spoken)** > The transfer rule sits in step four. Here are the six we tested.

---

<a id="s13"></a>
## Slide 13 · The six transfer decisions we tested · 9:58–11:02 (64 s)
**Context.** The audience must know the six rules before seeing results.

**Spoken**
> We compared six rules, one at a time, with everything else fixed. "Vans only" never transfers. "Wait ten minutes" and "Wait fifteen minutes" transfer once a booking has waited that long. "Unassigned for ten minutes" transfers if no van has had the booking in its plan for ten minutes. "Predicted total wait exceeds fifteen minutes" adds the time already waited to the van's predicted pickup. And "Lyft arrives sooner" compares two predictions. A Lyft ordered now would arrive after a two-minute ordering lag plus a typical eight-minute delay. If that is more than two minutes sooner than the predicted van pickup, the rider moves. Call the first two the waiting-time rules, and the last two the prediction rules.

*Preparation.*
- **Three kinds of information:** elapsed time, assignment, and prediction.
- **Eligibility:** only bookings still waiting, with no van already driving to them.
- **The rule reads** the van plan's predicted pickup, or a tentative estimate if the booking is unplanned.

*Likely questions.*
- **Why these thresholds?** Fifteen minutes echoes the published pickup-target wording around April 2026; ten is an earlier trigger, to see the effect of acting sooner; two minutes is a margin against prediction error. The published targets are wording, not verified operating policy (D-49). All thresholds were fixed in pre-registration v2 before any run and not tuned; a threshold sweep is the next step.
- **What is the ordering lag?** The assumed 2 minutes between deciding to transfer and the Lyft order being placed (D-43).

*Deeper:* [explanations §13](slide_explanations.md#s13); code key B1 (slide 24). *Sources:* spec §6; `src/sim/lyft.py`.

**Transition (spoken)** > Here is one rider through the last rule.

---

<a id="s14"></a>
## Slide 14 · One request: compare van versus Lyft · 11:02–12:02 (60 s)
**Context.** A concrete case of the last rule, on a small designed evening.

**Spoken**
> This is a small designed evening, not the random pilot. A rider booked at 6:16 and thirty seconds. At 6:17 the van plan predicted pickup at 6:30 and eight seconds. A Lyft ordered then would arrive at 6:27: two minutes of ordering lag plus eight minutes of delay. That is three minutes eight seconds sooner, more than the two-minute margin, so the rider was transferred. The Lyft was ordered at 6:19, reached the curb at 6:27, ten and a half minutes after the request, and had the rider at the destination by about 6:30. The van time was only a prediction; we never see what the van would actually have done.

*Preparation.* On this evening the Lyft delay is fixed at 8 min by design, so the realized time equals the expected one. In the pilot, delays are random. Acceptance probability here is 0.9, and this rider accepts.

*Likely questions.*
- **Did the transfer help?** We can't say from one prediction. The pilot compares whole evenings instead (slide 16).
- **Wasn't the rider dropped off before the van would even have arrived?** Yes: drop-off at 18:30:25 against a predicted van pickup at 18:30:08. But that van time is a prediction; this is a designed evening, not evidence of a saving.

*Delivery.* Say "six sixteen and thirty seconds" or "about 6:16", never "eighteen sixteen thirty".

*Deeper:* [explanations §14](slide_explanations.md#s14). *Sources:* `outputs/sim/L4_R3-2/` (epochs at 1020 s; outcomes R011).

**Transition (spoken)** > Testing the optimizer this closely also exposed a weakness.

---

<a id="s15"></a>
## Slide 15 · Testing exposed an optimistic postponement price · 12:02–13:11 (69 s)
**Context.** The optimizer's price for leaving a booking waiting was biased.

**Spoken**
> Leaving a booking waiting has a price. Our first version priced it as if a van could pick the rider up at the next two-minute re-plan, even when no van physically could. At 6:15 on the designed evening, a party of five had waited fifteen minutes. Postponing them cost 262.5 points. The earliest any van could actually reach them was about 6:19, worth about 436. So postponing looked cheaper than any real service, and they were left waiting. We compared alternatives and chose the simplest: price the earliest physically possible pickup. The longest wait fell from 44 to 36 minutes, but the average stayed the same; waiting was redistributed, not reduced. And the price is still optimistic, because it ignores the work the nearest van is already doing.

*Preparation.*
- **Results over the whole evening:**

  | | First version | Chosen |
  |---|---|---|
  | Longest wait (min) | 44.4 | 35.6 |
  | Mean wait (min) | 18.8 | 18.8 |
  | Median wait (min) | 17.1 | 18.6 |

  The waiting was redistributed. The third version added up to 9,828 variables and could err either way.
- **Why chosen:** for its meaning and its zero cost, not because this party was served sooner.

*Likely questions.*
- **Why not the most accurate version?** It wasn't reliably more accurate, and it multiplied the model size.
- **Your fix made the median worse?** Yes, slightly (17.1 → 18.6 min), and the youngest booking waited 35.6 min instead of 9.8. We did not choose it for outcomes on one evening; we chose it because the old price was provably below any service a van could give, and the fix costs nothing. The third, route-based version was worse on mean wait (21.8) and can err either way (B5).

*Deeper:* [explanations §15](slide_explanations.md#s15); backup B5 (slide 28). *Sources:* D-53; `outputs/sim/d53_experiment/`; review note d53_pending_price_review.

**Transition (spoken)** > With the optimizer settled, we could compare rules fairly.

---

<a id="s16"></a>
## Slide 16 · Replaying the same evening fairly · 13:11–14:06 (55 s)
**Context.** The experimental design behind every result that follows.

**Spoken**
> To compare rules fairly, we replay the same synthetic night six times: the same bookings, the same hidden patience and presence, the same Lyft delays. Only the rule changes, so differences come from the rule. Our pilot has thirty such nights, each one hour with two vans and twenty-eight bookings, including a ten-minute burst. That is fourteen bookings per van-hour, against April's derived 12.85, plus the burst: a heavy load by design. So it is thirty nights replayed six ways, not 180 independent nights. And this is a two-van pilot; the five-van evening is designed but not yet run.

*Preparation.*
- **Settings:** ordering lag 2 min; automatic acceptance; no-show 8.9% per arrival (provisional); placeholder patience.
- **Load:** 14 bookings per van-hour, against April's 12.85.

*Likely questions.*
- **Why replay instead of new random nights?** Pairing removes night-to-night noise from the comparison.
- **Are 30 nights enough? Why not 180?** The 180 runs are 30 nights × 6 rules, paired, not 180 independent observations. Pre-registration decides sample size: if the expected interval half-width exceeds 0.7 δ, we use 60 nights per cell. That calculation waits on the margins in D-50.
- **Why two vans, not five?** The two-van night is the dress rehearsal for the pipeline (spec §8), "too small for conclusions" by design. The five-van evening needs solve times benchmarked first (D-51); the pilot already took up to 253 s per run with two vans.

*Deeper:* [explanations §16](slide_explanations.md#s16). *Sources:* D-56, D-57; `outputs/sim/batch_L5_v1/summary.md`.

**Transition (spoken)** > Before reading results, what do our checks establish? **⇄ natural handoff**

---

<a id="s17"></a>
## Slide 17 · What our verification establishes · 14:06–14:49 (43 s)
**Context.** Results are only as good as the code that produces them.

**Spoken**
> Our checks establish that the code does what we specified. On three small designed evenings, the simulator reproduces hand-computed answers to the second. An independent brute-force program checked about 290,000 plan combinations on a designed evening and always agreed with the optimizer. 253 automated tests pass, and the reruns we sampled were byte-identical. What the checks do not establish is that our rules match real riders or the real service. That is validation, and it is still ahead of us.

*Preparation.*
- **Designed evening:** 22 transfers and 4 refusals matched the hand key, summed over five rules.
- **Tests:** 168 of the 253 were written by separate AI review agents that did not reuse the simulator's code.
- **Pilot:** every run passed per-run checks.

*Likely questions.*
- **Who wrote the code and the checks?** Say this first and plainly. The simulator and optimizer were written with an AI coding assistant under our direction, and every use is logged in `docs/ai_use_log.md`. The 168 independent tests and the brute-force checker were written by separate AI agents that worked from the specification, not from the simulator's code. We reviewed the results. Independence here means separate derivation, not a different human team.

*Deeper:* [explanations §17](slide_explanations.md#s17); diagnostics B8 (slide 31). *Sources:* Phase 4 log; tests/.

**Transition (spoken)** > Now, what did the rules do?

---

<a id="s18"></a>
## Slide 18 · Earlier prediction changed service and Lyft use · 14:49–15:58 (69 s)
**Context.** The first finding, across the thirty nights.

**Spoken**
> Each bar is the share of all bookings a vehicle reached at the curb within fifteen minutes, over thirty nights. Lyft orders per night are in each label. Vans only reaches about 48 percent with no Lyft. The two waiting-time rules add little, 50 to 51 percent, with three to six Lyft orders. The two prediction rules reach about three quarters, with nine to ten and a half. Acting on a prediction moves riders earlier, before the long wait has happened. And "Unassigned for ten minutes" was mostly inactive. Bookings were usually in some van's plan within minutes, even when the pickup was far off; only during the burst did some stay unplanned for ten minutes. Being assigned is not being picked up.

*Preparation.*
- **"Reached" means a vehicle's curb arrival**, not boarding.
- **"Unassigned for ten minutes"** was identical to vans-only on 24 nights, with 8 transfers in all, all for bookings made during the burst.
- **These numbers are descriptive.** They are not ranked and carry no intervals.

*Likely questions.*
- **Is the prediction rule better?** It reaches more riders and uses more Lyft. Which is better needs a value judgement (slide 20).
- **Do the prediction rules simply buy service with more Lyft?** Not only. Relative to vans only, they add about 0.7–0.8 bookings reached within 15 min per Lyft order; the waiting-time rules add about 0.16. (Δ share × 28 ÷ Lyft orders, from B7.)
- **Why is Lyft use per night lower than the transfers on slide 19?** A transfer cancelled during the 2-min ordering lag never becomes a Lyft order (196 − 18 = 178 = 5.93 × 30).

*Deeper:* [explanations §18](slide_explanations.md#s18); full table B6 (slide 29). *Sources:* `tradeoff.md`; `summary.md`.

**Transition (spoken)** > But reaching a rider with a Lyft is not the end of the story.

---

<a id="s19"></a>
## Slide 19 · A transfer does not end the rider's wait · 15:58–16:57 (59 s)
**Context.** The second finding: what happened after transfer.

**Spoken**
> A transfer starts a new wait. There is a two-minute ordering lag, then the Lyft's own travel, while the rider's patience clock keeps running. Under "Wait ten minutes", 196 bookings were transferred. 95 of them, almost half, cancelled before the Lyft arrived, 77 after the Lyft was already ordered. Under the two prediction rules, about a third cancelled. In our model impatience grows the longer a rider has waited, so a rider moved early has more patience left for the Lyft. That a transfer starts a new wait does not depend on our patience assumption; how many riders it loses, and the gap between rules, does.

*Preparation.*
- **Counts are totals over 30 nights.** Bars show shares, with n per rule.
- **Cancellations before the Lyft order** happen inside the 2-min ordering lag.
- **Wait percentiles** only count riders picked up. This is why we report "reached within 15 min" over all bookings.

*Likely questions.*
- **Are Lyft no-shows included?** Yes, as a separate segment (0 to 15 per rule over 30 nights).
- **Isn't the gap between rules just your patience assumption?** Partly, yes. Losses after a transfer exist under any patience model. The gap comes from assuming impatience grows with time already waited (Weibull shape 1.5); under constant-hazard patience, the sensitivity shape kept in D-39, it would vanish. Testing patience is a next step. The rules also differ in more than timing; no experiment isolated the cause.

*Deeper:* [explanations §19](slide_explanations.md#s19). *Sources:* per-run outcomes in `batch_L5_v1`.

**Transition (spoken)** > So rules trade service against Lyft use. How do we compare them?

---

<a id="s20"></a>
## Slide 20 · Choosing between service and resource use · 16:57–18:00 (63 s)
**Context.** The professor's Pareto lens, applied honestly.

**Spoken**
> We compare two objectives: service, the share reached within fifteen minutes, higher is better; and Lyft orders, lower is better. One rule dominates another if it is at least as good on both and strictly better on one. In the small example, A dominates B; A and C each win on one objective, so neither dominates. Applied to our six rules on the averages, five are not dominated. "Unassigned for ten minutes" is dominated by vans only: it reaches about the same share and orders a few Lyfts that vans only does not. Not dominated does not mean recommended. Choosing a point needs a judgement about Lyft use, and we tested six rules, not every possible one.

*Preparation.*
- **Ties:** on a night when a rule makes no transfer it replays vans-only exactly; both count as not dominated.
- **Per night:** the prediction rules beat vans-only on all 30 nights.
- **Three trade-offs:** the routing weights (slide 12), the policy trade-off here, and the decision criteria (not yet agreed).

*Likely questions.*
- **Is this the Pareto frontier?** No. It is the nondominated set among six tested policies; untested thresholds could do better. A frontier would come from sweeping each rule's threshold; a frontier of *all* policies would need the policy optimization of slide 21.
- **Would any weighting of the objectives pick a waiting-time rule?** No. Both are nondominated but *unsupported*: they lie below the line from vans only to "Predicted total wait…". Minimising "−service + λ × Lyft" picks only vans only, "Predicted total wait…" or "Lyft arrives sooner", depending on λ. Another reason nondominated is weak evidence on its own.
- **Why compare means? What about variability?** The means are descriptive. Night by night (B7), the prediction rules reach more than vans only on all 30 nights; "Wait ten minutes" on 19 (fewer on 6). Intervals wait for the agreed criteria (D-50).
- **Isn't "Vans only" trivially nondominated?** Yes; any zero-Lyft rule is, unless another zero-Lyft rule serves more. That is why nondominated is not recommended.
- **Why Lyft orders, not dollars?** The cost per Lyft trip is unknown and the model deliberately has no money (D-45). The same five rules stay nondominated with van-km as a third objective.

*Deeper:* [explanations §20](slide_explanations.md#s20); per-night B7 (slide 30). *Sources:* `src/sim/tradeoff.py`; `tradeoff.md`.

**Transition (spoken)** > Which raises a natural question. **⇄ natural handoff**

---

<a id="s21"></a>
## Slide 21 · Could we optimize the transfer policy itself? · 18:00–18:58 (58 s)
**Context.** From comparing six rules to designing the best one.

**Spoken**
> So far we compared six fixed rules. Could we instead choose the rule itself optimally? That is a leader–follower problem. The leader, a policy designer, picks the rule and its threshold, anticipating how the follower, the route optimizer, will re-plan the vans for whoever remains. Formally it is a bilevel program: choose the threshold to minimise service loss plus a weight times Lyft use, subject to the routes being optimal. We have not solved that. We still need an optimization over the threshold, the follower's response written as constraints over the whole evening, a treatment of uncertainty across nights, and an agreed value on Lyft use.

*Preparation.*
- **What we run** is a sequential policy simulation: plan, rule, transfers, re-plan.
- **Riders and Lyft** are not optimizing players here.
- **No reduction to one level** is claimed; that would need specific assumptions.

*Likely questions.*
- **Isn't your loop already leader–follower?** No. Within an epoch, one decision follows another, but nothing optimizes the rule with the follower's response as constraints. The rule reads the current plan, then the optimizer re-plans once: reaction, not anticipation.
- **Isn't a threshold sweep already solving the leader's problem?** For a one-parameter rule, a sweep evaluates the upper level by enumeration, with our simulator as the follower. It approximates "choose θ" but is not a solved bilevel program: our follower optimizes one decision moment at a time over restricted candidates, and λ is not agreed.
- **Who is the leader in reality?** Whoever sets the service's transfer policy. The follower is the routing dispatcher. Riders and Lyft are not modelled as optimizing players.
- **Why bilevel, if one organization runs both levels?** The levels have different objectives: the leader weighs service against Lyft use (λ); the follower minimises routing points. Collapsing them needs specific assumptions, such as optimality conditions written as constraints, which are hard with an integer follower. We claim no such reduction.

*Deeper:* [explanations §21](slide_explanations.md#s21). *Sources:* Colson, Marcotte & Savard (2007); Dempe (2002); von Stackelberg (1934); methodology §7b.

**Transition (spoken)** > To close, what we learned and what comes next.

---

<a id="s22"></a>
## Slide 22 · What we learned and what must be tested next · 18:58–20:00 (62 s)
**Context.** Close the journey; be honest about limits.

**Spoken**
> So, to our question: in our pilot, deciding earlier on a prediction reached about three in four bookings instead of one in two, at about ten Lyft orders a night; whether that is worth it needs a value on Lyft use. Three lessons. Being assigned is not being picked up. A transfer is not a completed trip; the rider is still waiting. And rules that act on predictions changed both service and Lyft use. Our limits are real: aggregate data only, placeholder patience, a two-van pilot, and code verification rather than validation. Next, we will agree how to judge the rules and compute paired comparisons on the saved nights, sweep the thresholds, run the five-van evening, and test patience and Lyft delay. Thank you.

*Preparation.*
- **Ride-time excesses (on the slide; say if asked or if time allows):** "36 times a ride ran past our ride-time limit, each time after the van waited for an absent rider." The 36 excesses come from 16 distinct bookings on 10 nights. The attribution is consistent with the timing; it is not proof.
- **The next experiments** need no new data, only agreed criteria and runs.

*Likely questions.*
- **What would change your conclusions?** Calibrated patience and the five-van scale.
- **36 rides over the limit?** 36 excess events across 180 runs, from 16 distinct bookings on 10 nights, repeated under rules that made the same decisions (B8).

*Deeper:* [explanations §22](slide_explanations.md#s22). *Sources:* methodology §7–§9; D-57.
