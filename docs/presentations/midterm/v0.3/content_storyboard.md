# Content storyboard (midterm, content draft v0.3, 22 Oct 2026)

This is the designer's brief. Each slide has:
- **Purpose:** one message.
- **On-slide content:** exact and minimal. It is what `BlueJay_Midterm_v0.3.pptx` currently shows; reword only with the team.
- **Visual:** what the designer may restyle.
- **Time:** spoken seconds.
- **Transition:** into the next slide.

**Rules for every slide.**
- "Booking" means the rider's Night Ride request only; the Lyft side is a "Lyft order" (ordering lag, Lyft orders per night).
- Use plain rule names only: "Vans only", "Wait ten minutes", "Wait fifteen minutes", "Unassigned for ten minutes", "Predicted total wait exceeds fifteen minutes", "Lyft arrives sooner".
- Keep codes (R0, L5, C, A, D-xx) and file labels off the visual area. Source footers may cite files.
- Every input or result carries a status badge (OBSERVED, DERIVED, ASSUMED, DESIGNED, SIMULATED, CHOSEN, ILLUSTRATIVE, NOT IMPLEMENTED), as text and colour, never colour alone.
- Charts are native and editable.
- Palette: blue 2A78D6, orange EB6834, aqua 1BAF7A, yellow EDA100, magenta E87BA4, violet 6250D6 (validated). Every series is direct-labelled.
- No screenshots of the restricted April dashboard.

**Time budget.**

| Section | Slides | Spoken |
|---|---|---|
| Opening | 1–4 | 2:59 |
| Investigating the data | 5–10 | 4:39 |
| Model and experiment | 11–16 | 6:28 |
| Findings | 17–20 | 3:54 |
| Limits and direction | 21–22 | 2:00 |
| **Total** | | **20:00**: about 19.1 min of spoken text at 125 wpm; budgets proportional to spoken length |

Natural speaker handoffs come after slides 4, 10, 16 and 20.

---

## Opening

### 1 · Testing Lyft transfer decisions for Blue Jay Night Ride (22 s)
- **Purpose:** name the decision.
- **On-slide content:**
  - title;
  - subtitle: "What aggregate data can tell us · how we built synthetic evenings · what replaying them showed";
  - team and course line;
  - "Content draft v0.3 · 20 min presentation + 10 min questions · speakers to be assigned".
- **Visual:** dark title slide; no imagery needed.
- **Transition:** "Here is what that decision looks like for one booking."

### 2 · One booking, several possible outcomes (58 s)
- **Purpose:** the outcome vocabulary.
- **On-slide content:**
  - a tree: Booking (1–5 passengers), "the dispatcher decides (a person today; a rule in our model)", splitting into two branches;
    - Stays with vans: Van reaches the curb → rider boards → dropped off / Rider cancels while waiting / No-show after a 3-min curb wait;
    - Transferred to Lyft: Lyft reaches the curb → rider boards → dropped off / Rider cancels before the Lyft arrives / Lyft no-show: rider absent when the Lyft arrives;
  - five definition tiles: Booking, Passenger, Curb arrival, Pickup, Cancellation;
  - the question in accent colour.
- **Visual:**
  - The tree is the talk's backbone. Slides 18 and 19 should visibly reuse the van (blue) and Lyft (orange) branch colours.
  - Simple icons per outcome are welcome.
- **Transition:** "We first tried to answer this with a different plan."

### 3 · What we originally proposed (51 s)
- **Purpose:** continuity, and the three corrected numbers.
- **On-slide content:**
  - left: the four proposal ambitions, numbered;
  - right: three struck-through quotes with corrections ("About 5,100 rides per hour at 6 pm" → 30-day total, about 170 per evening; "About 28 vans" → "All services" average 27.6; "1 in 4 trips overflow to Lyft" → 24.5% of riders);
  - a link to B9.
- **Visual:** keep the strike-through and correction pairing.
- **Transition:** "So what did the data actually contain?"

### 4 · What April's dashboards actually contain (48 s)
- **Purpose:** the evidence boundary.
- **On-slide content:**
  - green panel "Totals and shares": six items with sample values;
  - orange panel "Never a single journey": four ✗ items;
  - closing line.
- **Visual:**
  - A two-column contrast.
  - Optionally a stylized dashboard silhouette, never a screenshot.
- **Transition:** "That became our first task." **⇄ handoff**

## Investigating the data

### 5 · First, we investigated the numbers (26 s)
- **Purpose:** signpost three questions.
- **On-slide content:**
  - three cards, each with a question, a big number (≈ 5,100 / 188 / 23,843), a caption and a pointer to its slides (the first card also points to slide 8, group size);
  - the line "Each answer supplied one part of a synthetic evening, and exposed one assumption.";
  - a one-line legend of the status labels (OBSERVED, DERIVED, ASSUMED, DESIGNED, SIMULATED).
- **Visual:** the three numbers reappear on slides 6, 7 and 9; echo their style.
- **Transition:** "Start with volume."

### 6 · How many requests should our scenario contain? (60 s)
- **Purpose:** derive a per-van workload.
- **On-slide content:**
  - left: a native column chart of completed rides by hour (30-day totals, digitized), badge OBSERVED;
  - right: a four-step chain, all DERIVED (≈ 5,100 ÷ 30 ≈ 170 → × 2.09 ≈ 355 bookings in that hour → ÷ 27.6 ≈ 12.85 → × 5 vans = 64 / 50 / 54, 168 in all, each hour with its own rides and vehicles);
  - an "Unknown" note and the pilot's scale.
- **Visual:** the chain could become a funnel. Highlight the 18:00 bar.
- **Transition:** "Knowing how many bookings arrive, we needed to know where they go."

### 7 · Pickup and drop-off maps do not identify trips (56 s)
- **Purpose:** pairing is an assumption.
- **On-slide content:**
  - two toy 2×2 tables with identical green totals;
  - the caption "Green cells are all the maps show";
  - an ASSUMED box with three bullets on the pairing choice;
  - a map: "One synthetic hour: 28 bookings".
- **Visual:**
  - The toy tables are the demonstration. Consider animating Table 1 → Table 2.
  - The map is a figure from `make_map.py`; the designer may restyle it.
- **Transition:** "The next input is who travels together."

### 8 · An average group size leaves many possibilities (39 s)
- **Purpose:** a mean does not fix a distribution.
- **On-slide content:**
  - a native clustered bar chart: H1, H2 (hypothetical) and our assumption by party size 1–5;
  - a DERIVED tile "1.386 van passengers per completed van booking" (ratio of two observed totals);
  - the 3+ shares 8% / 12.3% / 9%;
  - an ASSUMED box.
- **Visual:** label H1 and H2 "hypothetical" wherever they appear.
- **Transition:** "Then the hardest word on the dashboard."

### 9 · What does "Canceled" mean? (52 s)
- **Purpose:** "Canceled" is not abandonment.
- **On-slide content:**
  - a stacked status bar (24,095 / 23,843 / 2,359);
  - the headline count;
  - two event boxes ("Rider gave up", assumed 50–75%; "Moved to Lyft by the dispatcher", assumed to close as "Canceled", not confirmed);
  - "The data cannot separate the two.";
  - an ASSUMED patience box.
- **Visual:** split the orange segment visually into two hatched halves of *unknown* size, with no proportions implied.
- **Transition:** "The last puzzle is a denominator."

### 10 · Why the no-show denominator matters (46 s)
- **Purpose:** one count, two rates.
- **On-slide content:**
  - two fraction cards: 2,359 / 50,297 = 4.7% and 2,359 / 26,454 = 8.9% (DERIVED);
  - a one-line reason under each;
  - an ASSUMED condition bar.
- **Visual:** big fractions; the 8.9% in accent.
- **Transition:** "With these pieces we could assemble an evening." **⇄ handoff**

## Model and experiment

### 11 · Our synthetic evening is assembled (59 s)
- **Purpose:** inputs → simulator → what the dispatcher sees vs what is hidden.
- **On-slide content:**
  - seven input tiles with badges, including travel times (road network × 1.2); hidden ones tinted violet;
  - the Simulator ("the referee");
  - two panels, "Dispatcher sees" and "Hidden from the dispatcher";
  - "Dispatcher sees (in our model: van optimizer + transfer rule)";
  - a line on the two kinds of evening; links to B4 (inputs) and B3 (event order).
- **Visual:**
  - A flow diagram.
  - Keep the violet "hidden" colour consistent with the predicted-van marker on slides 13 and 14.
- **Transition:** "Inside the simulator, a van optimizer makes the plans."

### 12 · How the van optimizer chooses a plan (81 s)
- **Purpose:** the loop, and one worked route choice.
- **On-slide content:**
  - an eight-step loop strip, coloured by part (grey simulator, blue optimizer, orange rule);
  - the title "Step 3: a mixed-integer linear program (MILP) picks one route per van";
  - an ILLUSTRATIVE candidate table: Route A 52.5 / 13.0 / 1.0 = 66.5 ✓; Route B 67.5 / 12.5 / 1.0 = 81.0; postponement row ("serves as many bookings as the candidates allow");
  - the panel "Points, not money": the waiting schedule with its breakpoints, riding and driving points, hard limits (seats, pickup before drop-off) and the ride-time guardrail;
  - the box defining "Optimal";
  - a link to B2.
- **Visual:**
  - The strip could become a circular loop.
  - The candidate comparison could show the two route orders on a tiny map.
- **Transition:** "The transfer rule sits in step four. Here are the six we tested."

### 13 · The six transfer decisions we tested (64 s)
- **Purpose:** define every rule before results.
- **On-slide content:**
  - a table (Rule / What it reads / Moves the booking to Lyft when), rows tinted by information type;
  - the "Lyft arrives sooner" mini timeline (now → 2-min ordering lag → typical 8-min delay → expected Lyft; predicted van later; gap > 2 min → transfer) with three bullets, defining the ordering lag;
  - a link to B1.
- **Visual:** the mini timeline is the key demonstration; keep its proportions (2 : 8).
- **Transition:** "Here is one rider through the last rule."

### 14 · One request: compare van versus Lyft (60 s)
- **Purpose:** a verified worked transfer.
- **On-slide content:**
  - DESIGNED badge and caption;
  - a timeline 18:15–18:32: Request 18:16:30, Decision 18:17:00, Lyft ordered 18:19:00, Lyft at the curb 18:27:00, Dropped off by the Lyft 18:30:25;
  - Predicted van pickup 18:30:08, hollow, violet, dashed: "a prediction only";
  - the bracket "3 min 8 s sooner > 2 min → transfer";
  - the wait band "10 min 30 s";
  - the explanatory bar.
- **Visual:** predictions must look different from realized events (hollow, dashed).
- **Transition:** "Testing the optimizer this closely also exposed a weakness."

### 15 · Testing exposed an optimistic postponement price (69 s)
- **Purpose:** find → compare → choose → limitation.
- **On-slide content:**
  - the aside line "A check on the optimizer before we compare rules";
  - numbered panels 1–4 (underpricing, controlled comparison, chosen approximation, remaining limitation);
  - a bar comparison in points: 262.5 charged against 435.8 at the earliest real pickup (18:19:28);
  - a whole-evening table (longest 44.4 → 35.6; mean 18.8 = 18.8; median 17.1 → 18.6; extra variables 0 / 0; the third version in B5);
  - "Waiting was redistributed, not reduced on average.";
  - CHOSEN and limitation boxes;
  - a link to B5.
- **Visual:** the four chips are the narrative spine; the designer may turn them into a horizontal storyline.
- **Transition:** "With the optimizer settled, we could compare rules fairly."

### 16 · Replaying the same evening fairly (55 s)
- **Purpose:** paired design and scale.
- **On-slide content:**
  - one night feeding six rule copies;
  - "Only the rule changes, so differences come from the rule.";
  - fact tiles: 30 nights replayed six ways, not 180 independent nights; 2 vans, 28 bookings in a one-hour night (14 per van-hour vs April-derived 12.85, plus a burst); 5 vans designed, not yet run;
  - an ASSUMED settings box.
- **Visual:** consider six thumbnail copies of the same night.
- **Transition:** "Before reading results, what do our checks establish?" **⇄ handoff**

## Findings

### 17 · What our verification establishes (43 s)
- **Purpose:** verification ≠ validation.
- **On-slide content:**
  - a green panel with four big facts (to the second; 292,181 on the designed evening over the same candidates; 253 tests, 168 by separate AI review agents; 6 of 6 sampled reruns identical);
  - an orange panel "Not yet validation" with four bullets;
  - a link to B8.
- **Visual:** a check vs open-question contrast.
- **Transition:** "Now, what did the rules do?"

### 18 · Earlier prediction changed service and Lyft use (69 s)
- **Purpose:** finding 1.
- **On-slide content:**
  - a native horizontal bar chart: share of all bookings reached at the curb within 15 min, one bar per rule, Lyft orders per night in the label, SIMULATED badge;
  - the "Prediction rules" box (73–75% vs 48–51%, 9–10.5 Lyft orders a night);
  - the "Assigned is not picked up" box;
  - a link to B6.
- **Visual:** prediction rules in blue, others grey. Do not add rank numbers or "best" labels.
- **Transition:** "But reaching a rider with a Lyft is not the end of the story."

### 19 · A transfer does not end the rider's wait (59 s)
- **Purpose:** finding 2.
- **On-slide content:**
  - a wait-continues strip (waiting for a van → transfer → ordering lag 2 min → Lyft travelling → curb), with the patience clock line;
  - a native 100% stacked bar of the fates of transferred bookings per rule, with n = transfers ("too few to compare" for n = 8);
  - the "95 of 196" callout;
  - the prediction-rules note;
  - the ASSUMED caveat.
- **Visual:**
  - Keep the orange "after booking" segment prominent.
  - The bar for "Unassigned for ten minutes" (n = 8) may be greyed with its n visible.
- **Transition:** "So rules trade service against Lyft use. How do we compare them?"

### 20 · Choosing between service and resource use (63 s)
- **Purpose:** Pareto dominance, used descriptively.
- **On-slide content:**
  - a toy dominance diagram (A, B, C);
  - a scatter of the six rules (filled = nondominated);
  - five bullets: the objectives; five of six (the dominated rule: same service, slightly more Lyft); not a recommendation; not a frontier; separate from routing points (ties are explained in B7);
  - a link to B7.
- **Visual:**
  - The scatter is drawn with shapes for label control; the designer may rebuild it as a native chart.
  - Keep "lower is better" and "higher is better" on the axes.
- **Transition:** "Which raises a natural question." **⇄ handoff**

## Limits and direction

### 21 · Could we optimize the transfer policy itself? (58 s)
- **Purpose:** leader–follower as an extension.
- **On-slide content:**
  - NOT IMPLEMENTED badge;
  - Leader and Follower boxes with "threshold" and "anticipated response" arrows;
  - the formulation in words with θ and λ;
  - two lists, "We have" and "Still missing".
- **Visual:** a hierarchy diagram; keep the badge.
- **Transition:** "To close, what we learned and what comes next."

### 22 · What we learned and what must be tested next (62 s)
- **Purpose:** close the journey.
- **On-slide content:** a top line answering slide 2's question provisionally, a "Backups →" link, then three columns.
  - **Learned:** three lessons.
  - **Limits:** five items, including 36 ride-time excesses (16 distinct bookings, 10 nights), attribution only.
  - **Next:** four steps.
- **Visual:** dark or tinted closing slide, with an optional "Thank you · questions".
- **Transition:** none; questions.

---

## Backups (slides 23–32)

| Slide | Content | Linked from |
|---|---|---|
| 23 | Divider with links to B1–B9 | — |
| 24 · B1 | Code key: plain names ↔ codes | 13 |
| 25 · B2 | MILP formulation, candidates, M bound, guardrail, solver settings | 12 |
| 26 · B3 | Same-second event order and a booking's life | 11 |
| 27 · B4 | Provenance of each input (status, value, decision) | 11 |
| 28 · B5 | Three postponement prices compared | 15 |
| 29 · B6 | All metrics by rule, mean (SD) over 30 nights | 18 |
| 30 · B7 | Night-by-night nondominance and paired counts | 20 |
| 31 · B8 | Numerical diagnostics | 17 |
| 32 · B9 | Corrected proposal claims | 3 |

Every backup carries a "← back to slide N" link.
