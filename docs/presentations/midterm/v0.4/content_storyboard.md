# Content storyboard (midterm, content draft v0.4, 23 Oct 2026)

This is the designer's and team's brief for [BlueJay_Midterm_v0.4.pptx](BlueJay_Midterm_v0.4.pptx). For each slide it gives:
- the purpose;
- the exact lead sentence;
- the minimal on-slide content;
- the visual;
- the time, in seconds (spoken plus about 4 s pause; see [speaking_script.md](speaking_script.md));
- where the material came from in v0.3.

## Narrative spine
We wanted to study dispatch decisions → discovered that April contains aggregates rather than individual journeys → built plausible evenings block by block → checked the simulator → replayed identical evenings under different transfer rules → found a conditional service–Lyft trade-off → identified which assumptions must be tested next.

## Visual language (keep when restyling)
- **Evidence labels:** soft filled pills with dark text — OBSERVED, DERIVED, ASSUMED, DESIGNED, SIMULATED, ILLUSTRATIVE, and combinations such as DERIVED + ASSUMED. Original proposal material carries an ORIGINAL PROPOSAL pill and a gold frame.
- **Execution status:** white bands with a coloured border, square corners, in a separate visual system.
  - TESTED IN SIMULATION: solid green.
  - PLANNED — NOT YET RUN: dashed amber.
  - PROPOSED — NOT IMPLEMENTED: dashed red.
  - Never imply that "tested" means validated against Hopkins.
- **Components, the same everywhere:**
  - simulator: grey;
  - van optimizer: blue;
  - transfer rule: orange;
  - hidden information: violet, dashed.
- **Qualifications** sit beside the claim, not only in footers.
- **Rule names:** plain throughout. Codes appear only in notes, B1 and the presenter reference.
- **Charts:** native and editable. Palette 2A78D6 / EB6834 / 1BAF7A / EDA100 / E87BA4 / 6250D6, with direct labels.

## Old-to-new mapping
| v0.4 | Title | From v0.3 |
|---|---|---|
| 1 | When should Night Ride move a waiting request to Lyft? | new (replaces title 1) |
| 2 | The service and one request | 2, simplified journey |
| 3 | Where we started | new: original proposal slides 10–11 (replaces the reconstructed 3) |
| 4 | Where we started: numbers we later corrected | new: original slides 7–8 with markers (3's corrections, plus the 7 pm bar) |
| 5 | We narrowed the question to one controllable decision | new; pivot reworded (technical review B) |
| 6 | April describes totals—not individual journeys | 4 and 5 merged; label definitions moved here |
| 7 | How busy should a constructed evening be? | 6, with units and stated assumptions |
| 8 | We started with a smaller, deliberately demanding hour | new (pilot facts were on 16) |
| 9 | Knowing the endpoints does not identify the journeys | 7 |
| 10 | One average can hide very different groups | 8 (H1/H2 → Examples A/B) |
| 11 | One status label hides different events | 9, restructured into three layers |
| 12 | The simulator needs a probability at vehicle arrival | 10 |
| 13 | The evidence becomes a scenario blueprint | 11, inputs grouped |
| 14 | Three components have different jobs | 11 and 12, expanded to full architecture |
| 15 | The same decision cycle repeats as the evening unfolds | 12's strip, as a full loop |
| 16 | The optimizer compares the consequences of candidate plans | 12's objective and example |
| 17 | We changed the transfer decision, not the van dispatcher | 13, code-level definitions |
| 18 | What does ‘Lyft arrives sooner’ actually compare? | 14 |
| 19 | A cheap postponement price could keep a rider waiting | 15 |
| 20 | Replay the same night; change one rule | 16 |
| 21 | We checked implementation before interpreting outcomes | 17 |
| 22 | The predictive rules reached more requests promptly—and used more Lyft | 18 |
| 23 | Moving a request to Lyft does not end its wait | 19, patience claim corrected (technical review A) |
| 24 | Better service and lower Lyft use can point to different choices | 20 |
| 25 | Could we choose the transfer policy systematically? | 21, corrected (technical review C) |
| 26 | Which assumptions could change the answer? | new (limits were a column of 22) |
| 27 | Test robustness before fine-tuning a winner | new (next steps were a column of 22) |
| 28 | What we can defend today | 22's top line, as the closing answer |
| 29–38 | Backup divider, B1–B9 | 23–32, regenerated from v0.4 numbers |

---

## Per slide

### 1 · When should Night Ride move a waiting request to Lyft? (42 s)
- **Purpose:** state the decision.
- **On slide:**
  - title;
  - subtitle "What April's aggregate data helped us build—and what our first simulations revealed.";
  - team line.
- **Visual:** one waiting request branching to "Shared van" or "Lyft", with a "?". Nothing else.
- **Narration opens:** "We began with a dispatch problem. The data led us first to a modelling problem."

### 2 · The service and one request (55 s)
- **Lead:** "Homewood-area Night Ride pools requests in shared vans. A dispatcher can move waiting riders to Lyft. We are studying when that transfer should happen."
- **On slide:**
  - scope line (Homewood including Peabody; East Baltimore excluded);
  - journey: request → wait → vehicle reaches curb → boarding → drop-off, with cancellation and no-show branches and a dashed transfer branch;
  - four definition tiles (Booking, Lyft order, Curb arrival, Pickup);
  - a line on why Lyft use has a price (each order is an extra trip Hopkins pays for).
- **Visual:** a simple left-to-right flow. Keep operational detail off this slide.

### 3 · Where we started (52 s)
- **Spoken lead:** "Our original plan was to reconstruct service nights and study dispatch decisions using an optimization model."
- **On slide:**
  - original proposal slides 10 (Data Sources) and 11 (Technical Strategy) as images, each labelled ORIGINAL PROPOSAL, with captions;
  - a "What changed" band.
- **Visual:** the originals are reproduced unmodified from the committed proposal deck, except that the dashboard maps are masked (restricted imagery).

### 4 · Where we started: numbers we later corrected (50 s)
- **On slide:** original slides 7 (Demand) and 8 (Gap), with four numbered red markers and four correction cards:
  1. 5,100 per hour → a 30-day total, ≈ 170 per evening;
  2. 28 vans → the "All services" average;
  3. the 7 pm bar 4,900 → digitized 3,957;
  4. 1 in 4 trips → 24.5% of riders.
- **Link:** B9.
- **Visual:** the markers sit on the false numbers, so nothing false is repeated without its correction.

### 5 · We narrowed the question to one controllable decision (54 s)
- **Lead:** "We now hold one specified van dispatcher fixed and change only the Lyft transfer rule."
- **On slide:**
  - three panels: original ambition → evidence available → current controlled experiment;
  - "This lets us study how the timing and information used by that rule change service and Lyft use.";
  - a "Why" band: a scope choice; the cadence (2-min tick plus new requests, cancellations or no-shows while waiting, van on duty) is modelled on TransLoc's 2016 design, not verified Hopkins practice.

### 6 · April describes totals—not individual journeys (58 s)
- **Lead:** "We know how many requests ended in each status, where pickups and drop-offs accumulated, and how activity varied by hour. We cannot reconstruct each rider's journey."
- **On slide:**
  - observed panel and missing panel;
  - one-line definitions of OBSERVED, DERIVED, ASSUMED and DESIGNED;
  - the transition sentence in italics.

### 7 · How busy should a constructed evening be? (64 s)
- **Lead:** "We estimated a workload from April's completed rides, request-to-completion ratio and reported vehicle availability."
- **On slide:**
  - a four-stage chain with units and labels;
  - the ASSUMED band, with the exact sentence on the monthly ratio and cross-service availability;
  - the five-van 64 / 50 / 54 = 168 card (five vans is a team design choice), marked **PLANNED — NOT YET RUN**.

### 8 · We started with a smaller, deliberately demanding hour (56 s)
- **Lead:** "The current results come from two vans and 28 requests in one hour, repeated across 30 constructed nights."
- **On slide:**
  - an 18:00–19:00 timeline with the 18:20–18:30 burst (11 of 28 placed; 11–17 arrive there in total);
  - fact tiles (2 vans × 14 seats, 28 requests, 30 nights, × 6 rules) and TESTED IN SIMULATION;
  - "This is a controlled pilot, not a reconstruction of a typical April night." and the load comparison.

### 9 · Knowing the endpoints does not identify the journeys (49 s)
- **Lead:** "Two different sets of trips can produce exactly the same pickup and drop-off totals."
- **On slide:**
  - two toy tables;
  - the ASSUMED box: "We assumed nearby journeys were more likely, then balanced the synthetic trips to preserve the observed location totals.";
  - the map of one constructed hour.

### 10 · One average can hide very different groups (61 s)
- **Lead:** "April helps identify an average group size. It does not tell us the full distribution of groups."
- **On slide:**
  - a native clustered bar chart (Example A, Example B, ours);
  - the DERIVED 1.386 tile;
  - the ASSUMED box with "Our chosen group-size mix is an assumption informed by the average—not a distribution recovered from April.", why groups matter, and the XL rule.

### 11 · One status label hides different events (62 s)
- **Lead:** "‘Cancelled’ does not tell us whether a rider gave up or a dispatcher moved the request to Lyft."
- **On slide:**
  - three layers: observation → assumed status mapping → hidden rider patience;
  - the patience statement, verbatim.

### 12 · The simulator needs a probability at vehicle arrival (55 s)
- **Lead:** "The share of all requests marked ‘No Show’ is different from the chance of a no-show when a vehicle actually arrives."
- **On slide:**
  - two fraction cards;
  - a condition box *next to* 8.9%, with "Our arrival-based probability is provisional because it depends on how the dashboard statuses were recorded."

### 13 · The evidence becomes a scenario blueprint (62 s)
- **Lead:** "A scenario combines evidence-based inputs, explicit assumptions and hidden rider behaviour."
- **On slide:**
  - four groups (Demand, Resources, Behaviour (hidden), Experiment settings), with labels; locations are DERIVED + ASSUMED (observed place totals, assumed sampling);
  - the outcomes-are-not-inputs band;
  - a link to B4.

### 14 · Three components have different jobs (65 s)
- **On slide:**
  - the three exact role sentences;
  - the full architecture: generator → inputs and hidden draws → simulator ↔ decision-step region (van dispatcher: route generation → MILP; then the transfer rule) → execution → recorded outcomes;
  - a "Hidden from the dispatcher" panel;
  - a link to B3.
- **Visual:** grouped regions and arrows; keep every component.

### 15 · The same decision cycle repeats as the evening unfolds (58 s)
- **Lead:** "The dispatcher sees requests that have arrived. It does not see future requests."
- **On slide:**
  - an eight-step loop in two rows, coloured by component;
  - four notes: when it runs; transfers; no cascades; commitments.

### 16 · The optimizer compares the consequences of candidate plans (76 s)
- **Lead:** "Waiting, riding, driving and unresolved requests enter the model in different ways."
- **On slide:**
  - four objective blocks;
  - the hard-constraint and guardrail line;
  - the ILLUSTRATIVE two-route table (66.5 vs 81.0);
  - the "Optimal" box, verbatim;
  - a link to B2.

### 17 · We changed the transfer decision, not the van dispatcher (69 s)
- **On slide:**
  - a rule table with code-level conditions;
  - the predicted-total-wait definition box;
  - the eligibility box;
  - "The six thresholds were specified before any run (spec §6) and not changed after seeing results.";
  - the groups named: waiting-time rules and the predictive rules;
  - a link to B1.

### 18 · What does ‘Lyft arrives sooner’ actually compare? (64 s)
- **Lead:** "The rule compares predicted van pickup with expected Lyft pickup, including the ordering delay."
- **On slide:**
  - the DESIGNED label;
  - the timeline, with expected vs realized marked and the hollow violet predicted van pickup;
  - the 3 min 8 s bracket;
  - the wait band;
  - a closing sentence on prediction vs the unobserved counterfactual.

### 19 · A cheap postponement price could keep a rider waiting (60 s)
- **Lead:** "The first formulation could price postponement more cheaply than a physically possible pickup."
- **On slide:**
  - 1 the flaw (cost charged to postpone, 262.5, against the cost of serving at the earliest possible pickup, 435.8 points);
  - 2 the controlled comparison (worst, mean and median);
  - "The adopted approximation reduced the worst wait in this designed case. It did not reduce average waiting.";
  - 3 adopted; 4 still optimistic;
  - a link to B5.

### 20 · Replay the same night; change one rule (44 s)
- **Lead:** "Each rule faces the same requests and hidden rider inputs, so differences reflect the rule within this specified model."
- **On slide:**
  - one night branching to six rule runs;
  - "Thirty nights replayed six ways are thirty paired scenarios—not 180 independent nights.";
  - TESTED IN SIMULATION and the provisional settings.

### 21 · We checked implementation before interpreting outcomes (54 s)
- **Lead:** "Verification asks whether the code implements the specified model. Validation asks whether the model represents the real service."
- **On slide:**
  - evidence with its scope (hand checks, 292,181 over the same candidates, 253 tests, 6 of 6 reruns);
  - a "Not validation" panel;
  - the AI-authorship statement in bold.

### 22 · The predictive rules reached more requests promptly—and used more Lyft (64 s)
- **Subtitle (prominent):** "30 constructed burst-demand nights; provisional rider behaviour."
- **On slide:**
  - a horizontal bar chart of reach per rule, with Lyft orders in the labels;
  - the result sentence;
  - the metric definition, plus the caveat that the 15-minute measure favours early transfer;
  - "This comparison does not isolate the benefit of prediction at an equal Lyft budget.";
  - a link to B6.

### 23 · Moving a request to Lyft does not end its wait (58 s)
- **Lead:** "The rider still waits through ordering and Lyft arrival. Their original patience clock continues running."
- **On slide:**
  - the wait-continues strip;
  - a 100% stacked fates chart (totals over 30 nights, n = transfers);
  - "95 of 196";
  - the mechanism box (possible, not isolated);
  - "Whether the gap between policies survives other patience shapes is untested."

### 24 · Better service and lower Lyft use can point to different choices (66 s)
- **Lead:** the dominance definition.
- **On slide:**
  - the toy A/B/C picture *before* the empirical plot;
  - the scatter of six rules;
  - five bullets, including "Nondominated does not mean recommended.", the six-rules-not-frontier sentence, and the means-only, no-noise-margin qualification for the dominated rule;
  - a link to B7.

### 25 · Could we choose the transfer policy systematically? (66 s)
- **Lead:** "One possible extension is to optimize transfer policy while anticipating how the routing dispatcher responds."
- **On slide:**
  - **PROPOSED — NOT IMPLEMENTED**;
  - policy designer → dispatcher responds → outcomes → back to the choice;
  - a "Today" box on finite search (best within a finite set for the sample average, not the true expectation, continuous thresholds or all policies);
  - six definitions still needed.

### 26 · Which assumptions could change the answer? (54 s)
- **Lead:** "The findings are conditional on the evenings and behaviours we constructed."
- **On slide:** a table (assumption, status, how it could change the interpretation) in priority order, plus the "Also open" line.

### 27 · Test robustness before fine-tuning a winner (40 s)
- **Lead:** the next-experiments sentence.
- **On slide:**
  - four ordered lanes, each PLANNED — NOT YET RUN;
  - the "order matters" line.

### 28 · What we can defend today (28 s)
- **On slide:**
  - the two closing statements, verbatim;
  - a TESTED IN SIMULATION band;
  - "not a policy recommendation";
  - a link to the backups.

## Backups (29–38)
| Slide | Content | Linked from |
|---|---|---|
| 29 | Divider with links | 28 |
| 30 · B1 | Code key | 17 |
| 31 · B2 | MILP and M bound | 16 |
| 32 · B3 | Event order, triggers, commitments | 14 |
| 33 · B4 | Input provenance | 13 |
| 34 · B5 | Three postponement prices | 19 |
| 35 · B6 | All metrics by rule | 22 |
| 36 · B7 | Night by night | 24 |
| 37 · B8 | Diagnostics | 21 |
| 38 · B9 | Corrected proposal claims | 3, 4 |

Every backup has a "← back to slide N" link.
