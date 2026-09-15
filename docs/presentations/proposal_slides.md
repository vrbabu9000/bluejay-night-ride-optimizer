# Blue Jay Night Ride — Proposal Presentation (Content + Speaker Notes)

**Team FourSight** · EN.553.602 Research and Design in Mathematics: Data Mining · Johns Hopkins University
**Format:** 11 core slides, ~12 min + Q&A. Design is owned by the designer teammate — this file is **content + notes only**.

**How to read this file:** each slide has three parts —
- **On-slide** = the terse text/visual the designer lays out (keep it sparse).
- **Notes** = what the presenter says out loud (~conversational).
- **Time** = target pacing.

All quantitative claims trace to `HW Night Ride Data April 2026.pdf` (aggregate TransLoc/JHU dashboards) unless flagged as synthetic/illustrative.

---

## Slide 1 — Title

**On-slide**
- Title: **Optimizing Blue Jay Night Ride: Rolling-Horizon Mixed-Integer Dispatch for an On-Demand Campus Shuttle**
- Team FourSight — Irfan Setiadi, Miles Zhou, Youzhi Zhang, Vignesh Rajesh Babu
- EN.553.602 · Proposal Presentation · Fall 2026
- (Optional) small de-identified shuttle / service-area image

**Notes**
- One sentence: "We're studying how JHU's late-night on-demand shuttle assigns riders to vans, and whether an optimization model can cut the long waits and the overflow onto Lyft — using the operation's own data."
- Don't preview the math yet; just plant the problem and that it's data-driven.

**Time:** 0:30

---

## Slide 2 — The service: what Blue Jay Night Ride is

**On-slide**
- On-demand, shared, **curb-to-curb** shuttle; book in the TransLoc app
- Operates ~**6 pm–2 am** around Homewood; pools multiple riders per van
- Published service targets → these become our **constraints**:
  - Pickup within **20 min** (up to **25** when busy)
  - Ride no longer than **25 min**
  - Van waits **3 min** at pickup; max group size **5**
- Overflow: dispatch may hand a trip to **Lyft** when no van can serve in time

**Notes**
- Frame it as a real operational system with real rules, not a toy routing problem.
- Emphasize the last two bullets: "The published targets aren't just nice-to-haves — we treat them as hard/soft constraints in the model. And the Lyft handoff is important: it's the pressure-release valve, and it costs money."
- This slide sets up every constraint we'll reference later, so keep it clean.

**Time:** 1:15

---

## Slide 3 — Motivation, from the operation's own data (the hook)

**On-slide** (designer: this is the money slide — a few big numbers + 1–2 of the April charts)
- **44,374 riders** in April 2026; ~800–1,400 completed van trips/night
- Sharp demand peak: **~27 vans in service at 6 pm**, **5,098 rides in the 6 pm hour** (30-day total)
- **The problem is in the tail, not the average:**
  - Wait (request→pickup): median ~10–13 min, but **P90 ≈ 17–21 min** — brushing/breaking the 20-min target
  - Ride duration: median ~10–12 min, but **P90 ≈ 21–30 min** — over the 25-min target
- **Overflow is large and volatile:** cancellations often rival completed rides; the operator's own note — *"many cancelled become Lyfts"* — ~0.3–0.5K Lyft trips/night

**Notes**
- This is the "why now / why it matters" slide — slow down here.
- "The median rider has a fine experience. But one in ten waits 17–21 minutes, and one in ten is on the van for 21–30 minutes — past the published targets. And a big, spiky share of demand never gets a van at all: it spills to Lyft."
- Key move: we are **not** claiming the operation is badly run. We're saying the data shows a specific, addressable failure mode — tail waits and overflow — that a smarter assignment policy could target.
- Cite the source out loud: "These are the operation's April 2026 TransLoc dashboards, shared by JHU Transportation."

**Time:** 1:45

---

## Slide 4 — Why it's hard: initial formulation

**On-slide**
- This is a **dynamic Dial-a-Ride Problem (DARP) with time windows** — not a plain vehicle-routing problem
- What makes it harder than CVRP:
  - Each request = a **paired pickup → drop-off**, served by the **same** van, pickup **before** drop-off
  - Van load **changes mid-route** (boardings/alightings), capped at capacity
  - Requests **arrive during service** (online), while vans are already moving
  - Some actions are **already committed** and can't be undone
- Visual: side-by-side **CVRP vs. DARP** (depot-and-deliver vs. paired pickup/drop-off with precedence)

**Notes**
- "If this were just 'visit these stops cheaply,' it'd be a classic routing problem. It's not."
- Walk the four bullets as the reasons a textbook CVRP doesn't fit: pairing + precedence, live capacity, online arrivals, commitment.
- Land the class name clearly — "dynamic Dial-a-Ride with time windows" — because it justifies the technique choices on the next slides and there's real literature behind it.

**Time:** 1:20

---

## Slide 5 — Data sources (rubric requirement: cite origin + how used)

**On-slide**
- **What we have now** — JHU Transportation / **TransLoc aggregate dashboards** (April 2026):
  - Origin & destination **density maps** (+ campus-proximate)
  - Rides by **hour**, **status** (completed/cancelled/no-show), vans **in service by hour**, wait-time & ride-duration **percentiles**, van+Lyft ridership
- **What's expected soon** — de-identified **trip-level extracts**: request/assign/arrival/pickup/drop-off timestamps, pickup & destination zones or protected coords, party size, pseudonymous vehicle IDs & capacities
- **How we use each:** aggregates → calibrate demand & validate; trip-level → reconstruct/replay actual nights
- **Privacy:** de-identified only; aggregate stats & maps in outputs; no rider names, IDs, contacts, or exact addresses

**Notes**
- Be scrupulously honest here — this slide is graded on it. "Today we have aggregate dashboards, not per-trip rows. Trip-level de-identified data has been requested and is expected."
- Explain the two-track use: "Aggregates already tell us the demand shape and where service breaks. Trip-level data lets us replay actual nights and compare policies fairly."
- Say the privacy sentence plainly — it signals we've thought about governance, which the stakeholder cares about.

**Time:** 1:15

---

## Slide 6 — Technical strategy: a spectrum of methods

**On-slide** (designer: one horizontal axis — quality vs. decision-time budget)
- We compare a **spectrum**, not three rival ideas:
  1. **Fast heuristics** — nearest-feasible + greedy pickup/drop-off insertion *(reuses our prior CVRP work, VehiPathOptimizer)*
  2. **Exact rolling-horizon MILP** — the **centerpiece**: optimal per-snapshot dispatch under the service constraints
  3. **Hybrid** — MILP core + local search, for scale at the ~27-van peak
- Axis: **← faster / simpler … more optimal / heavier →**
- All three run on the **same request stream** so the comparison is apples-to-apples

**Notes**
- "The professor's target is the mixed-integer model, and that's our centerpiece. But it only means something against a baseline, and it needs a fallback at scale — so we frame one spectrum from fast heuristics to exact optimization to a hybrid."
- Credit the prior repo briefly: "The heuristic end reuses routing code we've already built and validated."
- The hybrid is the honest scaling answer: "At 27 vans in the 6 pm hour, the exact model may be too slow to solve every few seconds — the hybrid keeps the MILP's logic but stays fast."

**Time:** 1:30

---

## Slide 7 — The MILP core (kept high-level)

**On-slide** (designer: small pickup/drop-off network diagram + a compact variable/objective box)
- **Decisions:** binary route arcs (van goes event i→j) + request→van assignment (or overflow); continuous event times, van load, wait, excess ride time
- **Objective (service-first, in priority order):** minimize overflow → passenger wait → excess ride time → van travel
- **Constraint families:** same-van pickup+drop-off, pickup-before-drop-off, capacity, service time windows, max ride time, committed actions
- *Full notation → backup slide*

**Notes**
- Do **not** read equations. "Discrete choices — which van, which route — plus continuous quantities like arrival time and wait. Linear constraints tie them together; that's what makes it a mixed-integer program."
- Stress the objective ordering: "Service first. We minimize overflow and waiting before we shave van miles — a safety-oriented service shouldn't trade rider waits for mileage."
- Point at the diagram, name two constraints (pairing + precedence), and move on. Depth is in the backup slide for Q&A.

**Time:** 2:00

---

## Slide 8 — Making it dynamic: rolling horizon

**On-slide** (designer: 4-step loop)
1. **Observe** current van positions, onboard riders, committed stops, known pending requests
2. **Freeze** actions already underway
3. **Re-solve** the remaining assignment/routing under a short time limit (warm-started)
4. **Commit** the next action → new request arrives → repeat

**Notes**
- "The MILP solves a snapshot. Real dispatch is a moving target, so we wrap it in a rolling-horizon loop: re-solve as requests arrive, but never rip out a pickup a van has already started."
- Mention the two knobs we'll tune: re-optimization trigger (per request vs. fixed interval) and the solver time limit.
- This is the bridge from "a model" to "a dispatcher."

**Time:** 1:15

---

## Slide 9 — Simulation & live demo

**On-slide**
- Our **OSRM + folium** prototype (clearly labeled **synthetic**, calibrated to April data):
  - ~20–40 requests over a simulated evening, sampled to match the **O-D density** + **6 pm-peaked** demand
  - **Naive/greedy dispatch vs. optimized** routing, side-by-side on a Homewood/Baltimore map
  - Annotate: total wait + trips that would have spilled to **Lyft**
- Figure: before/after route maps (screenshot / short GIF)

**Notes**
- "To make this concrete — and to prove we can build the pipeline — here's a small simulation on real map geometry."
- Narrate the contrast: "Left: greedy assignment, longer detours, some requests overflow. Right: optimized assignment, tighter routes, fewer overflows and shorter waits — on the same requests."
- Be explicit it's illustrative: "This is synthetic demand calibrated to April's patterns, not a results claim — the real evaluation comes once we have trip-level data."

**Time:** 1:15

---

## Slide 10 — Evaluation plan

**On-slide**
- **Same request stream, fleet, and travel times for every policy**
- Baselines & methods: **reconstructed historical** (primary, once trip-level data arrives) · nearest-feasible · greedy insertion · **rolling-horizon MILP** · hybrid
- **Metrics:** wait P50/P90, % pickups within target, ride time & % within 25 min, **% overflow/Lyft**, total & empty miles, van utilization, **solver time & optimality gap**
- **Fallback:** if trip-level data is late → evaluate on **synthetic streams calibrated** to aggregates (multiple seeds + sensitivity)
- Honest stance: **a heuristic matching the MILP is still a valid finding**

**Notes**
- "Every method sees identical inputs, so differences are the policy, not luck."
- Emphasize the tail + overflow metrics — those match the problem we opened with on slide 3.
- Own the negative-result possibility: "If a simple rule ties the MILP, that's a real, reportable result — the validated model and replay environment still stand."

**Time:** 1:30

---

## Slide 11 — Timeline, deliverables, risks, team

**On-slide**
- **Milestones:** data audit → travel-time matrix → replay simulator → baselines → static MILP → rolling horizon → experiments → progress report → final analysis
- **Deliverables:** formulation + validated model, reproducible replay/sim environment, comparative results & maps, stakeholder-facing summary
- **Risks → fallbacks:** data late → synthetic calibration · MILP too slow → prune arcs / warm-start / hybrid · historical policy not reconstructable → compare to transparent heuristics
- **Team FourSight** · decision-support study, **not** a deployment claim · AI-use disclosed in the written proposal

**Notes**
- Move quickly — this is the "we have a plan and we've de-risked it" slide.
- Close on scope + value: "This is retrospective decision support for JHU Transportation — where waits and overflow come from, and whether optimization can move them. We won't touch live vans or TransLoc."
- Hand to Q&A.

**Time:** 1:10

---

## Backup slides (for Q&A — build only if time allows)

- **B1 — Full MILP notation:** sets, parameters, all decision variables, objective, every constraint family with the conditional/time-propagation forms.
- **B2 — VehiPathOptimizer lessons:** what the prior CVRP repo reused (OSRM matrix, capacity tracking, folium) and what had to be added (pairing, precedence, online arrivals, MILP); note the lat/lon-order pitfall we fixed.
- **B3 — Data-field request table:** desired vs. minimum-viable fields, and the derived/simulated fallbacks.
- **B4 — Solver strategy:** Gurobi (academic) with SCIP/HiGHS fallback; arc pruning, warm-starting, horizon length, time limits.
- **B5 — Prepared answers:** privacy/governance; how Lyft overflow is modeled vs. observed; whether historical dispatch can be reconstructed; "why not just use OR-Tools?" (it's CP/heuristic routing, not the explicit MILP the course asks for, and doesn't expose the passenger-DARP structure directly).

---

## Pacing check

| Section | Slides | Target |
| --- | --- | ---: |
| Problem + motivation | 1–3 | ~3:30 |
| Formulation + data | 4–5 | ~2:35 |
| Technical strategy | 6–8 | ~4:45 |
| Demo + evaluation + close | 9–11 | ~3:55 |
| **Total** | 11 | **~14:45 → trim to ~12 in run-through** |

**Trim levers if long:** merge slides 7+8; tighten slide 11 to a single timeline graphic; cut slide 9 narration to 45 s.
