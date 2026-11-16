# First-time reader review: midterm draft deck and speaking script

**Reviewer stance:** a classmate in EN.553.602 with general maths background (linear algebra, probability, basic optimisation) and no knowledge of ride-sharing, dispatch or this project. I read only `BlueJay_Midterm_draft_preview.pdf` (22 pages) and `speaking_script.md`. This review judges clarity and logic only; numbers were not fact-checked. It is a simulation of a newcomer, a useful check rather than proof of how a real audience will react.

**Numbering note (affects Q&A):** the slide footers are PDF page numbers, so "Slide 1" in the script shows "2" in the corner, and "Slide 12" shows "13". If someone in the audience asks about "slide 7", presenters and audience will mean different slides. Either drop the title page from the footer count or renumber the script.

---

## Title

- **Undefined terminology:** "synthetic evenings" (not explained until slide 3). "Aggregate data" is fine for this audience.
- **Missing steps:** the title never says what the project is *about* (rider waiting, Lyft transfers). The second half of the talk is about transfer rules, which the title does not mention, so the title describes only slides 2–4.
- **Unsupported implications:** none.
- **Why this choice:** n/a.
- Spoken: 40 words is about 18 s at the script's 130 wpm, but the slot is 10 s.

## Slide 1 (footer 2): service and September proposal

- **Undefined terminology:** "greedy rules", "rolling-horizon", "hybrid" (a hybrid of what?), "dispatch methods". MILP is expanded, which is good. "Homewood" is fine for JHU students. "Published service targets": targets for what (wait time? which percentile?) is not said here, and on slide 2 they appear only as numbers.
- **Confusing units:** "about 1 in 4 April riders (24.5%) rode Lyft": riders = people or trips? The footer says 44,374 riders, but slide 4 later uses 50,297 *requests* and 24,095 *completed*. I could not reconcile riders, requests and completions across slides 1, 3 and 4.
- **Wording:** the callout says "Most of these **assumptions** changed", but the bullets are plans, not assumptions.
- **Why this choice:** why did the team first plan to treat Lyft as "paid overflow inside the optimizer"? I only learn on slide 2 that this was dropped.

## Slide 2 (footer 3): how the research question changed

- **Undefined terminology:** "guardrail max(25 min, 2 × direct + 5 min)": "direct" (direct ride time?) is undefined, and it is unclear whether 25 min is a ride time or a wait. "Reporting thresholds" is vague. "Van dispatcher held fixed": which dispatcher? It is described only on slides 5–6.
- **Missing steps (most important on this slide):** the script says that without real nights "a head-to-head comparison of dispatch algorithms is not very meaningful". But the team then compares *transfer rules* on synthetic nights. As a newcomer I cannot see why synthetic nights are good enough to compare transfer rules but not dispatch algorithms. This is the pivot of the whole talk and needs one sentence of justification.
- **Confusing numbers:** the corrections bullet says the April-era pages said "15 / 20 / 20", but the script says "15 and 20". Three numbers versus two, with no statement of what each target measures.
- **Why this choice:** "no money modelled (cost unknown)": why not a range of costs, as was done for other unknowns? Why are the targets now reporting thresholds rather than constraints, while the guardrail stays a hard constraint?

## Slide 3 (footer 4): building an evening from aggregate data

- **Undefined terminology:** "tooltip: 5,098" (dashboard UI jargon), "vehicle-hour", "Gravity prior", "iterative fitting" (naming it as IPF/Sinkhorn would help a maths audience), "0.1 per minute" (a decay rate in exp(−0.1·t)? the script says "about 10% per minute", which is a different reading), "L5, r00" in the map title (L5 is defined only on slide 9), "spread-out variant", "frozen".
- **Missing steps:** "5 vans" appears from nowhere: why five? The box is labelled "Load per van" but the number (64) is for five vans together. The chain divides by 27.6 vehicles across *all* services while listing "Homewood's share of the vehicles" as unknown, so I could not tell whether 12.85 is a Homewood load or a system-wide average. The "~150–260" range: of what? The script says "per three-hour evening", but the slide does not, and slide 1 defined the service as 6 pm–2 am (8 hours). Is an "evening" in the model 3 hours?
- **Confusing graphs:** the map shows "188 April demand points" and 28 requests: what is a demand point? Lines run from Homewood to Inner Harbor; the caption helps ("not road routes").
- **Unsupported implications:** "Tested:" suggests that a sensitivity test was run, but no result is shown. Is it tested, or planned?
- **Why this choice:** why multiply by 2.087 requests per completion (that is, model requests rather than completed rides)? The script mentions cancellations and Lyft handoffs, but the slide does not.

## Slide 4 (footer 5): assumptions that complete the evening

- **Undefined terminology:** "XL" (explained in words, fine), "status mapping"/"(mapping)", "hidden personal deadline" against the chart label "Patience", Weibull (only in backup; fine to omit).
- **Missing steps:** the "Canceled" paragraph gives a 50–75% range for riders who gave up, but I could not see how that range is *used*. Does it calibrate the patience curve, or is it just a caveat? The patience median (18 min) is then called a placeholder, so the link between the observed 47% and the assumed curve is missing. Group size: the derived mean is 1.386 but "ours is assumed (mean 1.405)". Why does the model's mean differ from the data's mean?
- **Confusing graphs/denominators:** in the no-show bar diagram, the second bar treats Completed + No Show as "van arrivals". But some completed trips were Lyft (24.5% on slide 1), so are they van arrivals? This needs one line. The Lyft-delay chart has two unlabelled dashed lines (the median 8 and the 90th percentile 15 appear only in the text). The badge "DERIVED" on group size conflicts with the text "ours is assumed".
- **Why this choice:** why is the Lyft booked 2 minutes *after* the decision? This lag later drives a key finding (riders cancel "in the 2-min lag", slide 9), but its reason is never given.
- **Timing:** four charts, a two-bar diagram and four badges in 90 s is dense.

## Slide 5 (footer 6): how the algorithm operates

- **Undefined terminology:** "MILP" (slide 1 only, inside a bullet), "candidate routes", "accepted transfers" (accepted by whom? can a rider refuse?), "L4", "R2(15)" (the script never says the code aloud, but it is on the slide), timeline symbols t_r, τ, ℓ, λ_r and the code name **"xfer_hold"**, "board 30 s".
- **Confusing units (high impact):** "wait 18:50 > 15" and "wait 13:30" sit next to clock times (18:16:30, 18:35:20). I first read "18:50" as 6:50 pm. Write waits as "18 min 50 s" or "18.8 min".
- **Missing steps:** why re-plan only *once* after transfers (step 6), and why every 2 minutes? The R011 example shows the predicted van wait (18:50) against the actual Lyft wait (13:30). Without the van's *actual* arrival, I cannot tell whether the transfer helped.
- **Unsupported implications:** the example reads as "the transfer saved about 5 minutes", but it compares a prediction with an outcome.
- **Timing:** 7 steps, two boxes, a timeline and a worked example in 2 minutes is the densest slide in the deck.

## Slide 6 (footer 7): how the mathematics chooses a plan

- **Undefined terminology:** "compatible set" (each request in at most one van's route, I assume), φ (explained in the caption, good), "dwell", "r1"/"r2" (the script says r1 waited 8 minutes and r2 is a party of two, but the slide does not; the bar chart is not readable without that).
- **Missing steps:** the objective covers only routes. Nothing says what happens to a request that is in *no* route. Slide 7 then talks about "a price for leaving it waiting" that never appeared in this formula. The pending term (and the "serve as many as possible first" priority mentioned on slide 7) belongs here.
- **Confusing graphs:** the y-axis "points per passenger" is cumulative, while the caption gives per-minute slopes (1, 2.5, 5, 10, 20). The script says "the first minutes cost one point each, after 15 … 10, after 20 … 20" and skips 2.5 and 5, which do not match what is on screen.
- **Why this choice:** why these breakpoints, why 0.5 per passenger-minute and 0.1 per km, and why at most 3 new pickups per van (compute time? only stated as a limitation on slide 12)?
- **Unsupported implications:** handled well; the "Optimal means …" box is exactly what a maths audience needs.

## Slide 7 (footer 8): the pending-price weakness

- **Undefined terminology:** "pending price" (the script title uses it; the slide does not define it), "next 2-minute tick", "L4, 16 requests", "R002", "serve as many as possible first" (never introduced), "MILP variables".
- **Ambiguous sentence (high impact):** the italic line in the Decision box, "**Not chosen because one rider was served sooner.**", reads as "A was not chosen". Rewrite it as "We did not choose A because one rider was served sooner."
- **Confusing units:** "waited 22:18 / 19:28 / 20:39" again looks like clock times. Does "waited" mean total wait or extra wait after the 15 minutes?
- **Missing steps:** the decision is justified by design reasons (a clear meaning, no new variables), so what was the experiment for? I read it as "to check that A does not make things worse", but please say so. Under A the median wait *rose* (17.1 to 18.6) while the max fell, which the footnote acknowledges.
- **Unsupported implications:** the title says "found, tested and **fixed**", while the slide body says "still an approximation" and "provisional". "Fixed" overclaims. The evidence is one designed evening of 16 requests, a single run.
- **Why this choice:** clear enough once the ambiguous line is fixed.

## Slide 8 (footer 9): verification

- **Undefined terminology:** "declined offers" (first appearance of riders declining anything), "L1–L3", "epoch" (first appearance; never defined in the core deck), "frozen inputs", "byte for byte".
- **Confusing denominators:** "the MILP's choice matched on every epoch checked": how many epochs were checked? "Summed over five rule runs": why five when there are six rules? (I guess R0 never transfers, but the six rules have not been introduced yet at this point.) "Two thirds (168) written by independent reviewers": who are they?
- **Unsupported implications:** this slide shows *verification* (the code does what the spec says), not *validation* (the model resembles the real service). Slide 12's "verified way" could be heard as the latter. Say explicitly that the evenings are not validated against real nights.
- "to the second" as a big headline number is odd; it is a precision, not a count.

## Slide 9 (footer 10): thirty synthetic nights

- **Undefined terminology:** this is the first time the six rules appear together, *as results*. R1(10), R1(15), R1u(10), R2(15), R3(2), R0 and L5 are labelled, but the audience has not been told what the treatments are or why these six were picked. "10-minute burst" (how large?), "Provisional settings" (which?), "Lyft no-show", "attribution check", "predicted-wait rules" (meaning R2 and R3, I think).
- **Confusing graph (high impact):** the x-axis (0 to 1) has no label. It is the share of transferred riders, with counts printed inside. R1u(10) has only **8** transfers but draws as a full-width bar like R3(2) with 330, so normalisation hides the sample size. R0 is absent without comment, so the chart shows five bars while the text speaks of "six rules". The script never walks through the colours.
- **Contradiction:** slide 2 calls the ride guardrail "the one hard limit", yet "36 rides exceeded the ride guardrail". A newcomer needs one line on how a hard limit can be exceeded (no-show waits after planning). "36 rides" is also given without a denominator.
- **Missing steps:** "16 of 28 [picked up] under never-transfer" means that 43% of requests are never picked up. Is this scenario deliberately overloaded? Why 2 vans and 28 requests per hour, and how does that relate to slide 3's 64/50/54 for 5 vans? The paired design ("same riders, same hidden traits"; "not 180 independent nights") is said aloud but is missing from the slide, and it is what makes the comparison credible.
- **Riders/requests/passengers:** "95 of 196 riders transferred" vs requests (a party of 3 is one request?), with "Wait 90th pct (passengers)" in backup B5. Pick one unit, or define both once.
- **Unsupported implications:** "36 … each coincided with a no-show wait": the script correctly says "not a proof of cause"; the slide says only "attribution check". Bring the script wording onto the slide.

## Slide 10 (footer 11): service versus Lyft use

- **Undefined terminology:** "reached within 15 min" (does a vehicle arriving count if the rider then no-shows? why 15?), "nondominated", "frontier" (fine for maths), "Decision criteria with margins … (D-50)" ("margins" and "D-50" mean nothing to the audience), "Weights inside the routing objective are a different trade-off" (cryptic without slide 6 in mind).
- **Confusing graph/units:** the definition says "reaches at least as many **riders**" while the y-axis is the "share of all **requests**". The y-axis starts at 0.40, which is acceptable but should be noted. There are no error bars, although backup B5 shows a night-to-night SD of about 0.08. The R0/R1u(10) labels overlap.
- **Unsupported implications:** "R1u(10) is dominated by R0, by a hair (0.476 vs 0.477)": a 0.001 difference against an SD of about 0.09 is noise, and calling it "dominated" over-reads it. Either add uncertainty or say "indistinguishable from never-transfer".
- **Missing headline:** the visually striking result (the predicted-wait rules reach about 0.74 against about 0.48–0.51 for the others) is not stated as a takeaway on the slide. The title "a trade-off among tested rules" hides it. The "not a recommendation" caveat is right, but say what the chart *does* show.

## Slide 11 (footer 12): leader–follower reading

- **Undefined terminology:** θ (defined as a threshold, good), λ, y ("routes"? undefined), "service loss", E[·] over what, argmin, "per epoch, restricted", "bilevel". Stackelberg is in the citation only.
- **Missing steps:** why is this slide here? The script's transition ("Our professor asked …") is the only motivation; the slide needs one line saying so. In the implemented loop on slide 5, the *follower* (MILP) moves first and the rule then reads its plan. That order looks reversed relative to "leader decides first", and a sharp classmate will ask about it.
- **Unsupported implications:** handled honestly ("possible, but not what we solved").
- **Timing:** 154 words for a 1-minute slot is about 71 s, so over.

## Slide 12 (footer 13): limitations, next steps, contribution

- **Undefined terminology:** "D-50", "paired intervals", "one night pattern", "benchmark the MILP" (against what? the question no longer compares algorithms).
- **Missing steps:** why "some runs take minutes" is a limitation (does it block the five-van run?).
- **Unsupported implications:** "a transparent, **verified** way": see slide 8. Add "not yet validated against real service". The absence of any comparison to reality is the biggest limitation for a newcomer and is listed only implicitly ("aggregate data only").

---

## Top 5 fixes (ranked)

1. **Introduce the experiment before the results.** Add a short panel or slide between 5 and 9 with the six transfer rules in plain words (the code key is only in backup B3), why these six, and the pilot design: 2 vans, 28 requests per hour, a burst, 30 nights, paired replay. Explain why the pilot is so overloaded (16 of 28 picked up under never-transfer) and how it relates to slide 3's five-van numbers. Remove or define codes on core slides: L4, L5, r00, R002, R011, D-50, epoch, xfer_hold, tooltip.
2. **Justify the pivot on slide 2.** Explain why synthetic nights support comparing transfer rules but not dispatch algorithms. Without that sentence, the research question looks arbitrary.
3. **Fix units and denominators.** Show waits as "18 min 50 s", not "18:50" next to clock times (slides 5 and 7). Pick riders, requests or passengers and use it consistently (slides 1, 4, 9 and 10). Label slide 9's x-axis, show n per bar (R1u(10) has n = 8), explain why R0 is missing, and give the denominator for "36 rides". Define "reached within 15 min" on the slide.
4. **Bridge slides 6 and 7, and fix the slide 7 wording.** Put the "left waiting" (pending) term and the "serve as many as possible first" priority into slide 6's objective, so slide 7's "price" has a home. Rewrite "Not chosen because one rider was served sooner" (it reads as the opposite), and soften "fixed" in the title.
5. **Resolve apparent contradictions and overclaims.** The guardrail is "the one hard limit" yet is exceeded 36 times. "Accepted transfers" and "declined offers" are never explained. "Verified" means code verification, not validation against the real service (slides 8 and 12). "Dominated by a hair" (0.476 vs 0.477) needs uncertainty shown, or should be called a tie. State slide 10's actual takeaway (the predicted-wait rules reach far more requests per booking).

## Does the 12-slide story hang together for a newcomer?

**Partly.** The opening arc (we planned X, the data did not allow it, here is how we built honest synthetic evenings) is clear and persuasive, and the closing honesty about what is not claimed is a strength. The middle loses a newcomer. Slides 6–8 spend about 4 minutes on dispatcher internals (penalty curve, pending price, verification), although slide 2 said the dispatcher is "held fixed" and the question is about transfer rules. The transfer rules themselves, the actual treatments, are never introduced; they first appear as bar labels in the results on slide 9. So when the findings arrive, I know a lot about how a van picks a route but not what was being compared, or why the pilot uses two heavily overloaded vans. The leader–follower slide feels like an inserted answer to an outside question rather than part of the story. Reordering (rules and pilot design before verification, pending price compressed or moved to backup) would make it hang together.

## Is the spoken timing realistic?

Mostly, in words: the script totals about 2,215 words, roughly 17 minutes at 130 wpm against an 18½-minute plan. Per slide (words, then the time they take against the slot):

- Title: 40 words, about 18 s against 10 s (**over**).
- Slide 1: 127 words, about 58 s against 50 s (slightly over).
- Slide 2: 209 words, about 96 s against 90 s (tight).
- Slide 3: 269 words, about 124 s against 150 s. The words fit, but the arithmetic chain needs pauses.
- Slide 4: 170 words, about 78 s against 90 s, with five visuals (dense).
- Slide 5: 223 words, about 103 s against 120 s. This is the densest slide, and reading the R011 timestamps aloud is slow.
- Slide 6: 169 words, about 78 s against 90 s (OK).
- Slide 7: 191 words, about 88 s against 90 s (no slack, and a 12-number table).
- Slide 8: 90 words, about 42 s against 60 s (spare time).
- Slide 9: 251 words, about 116 s against 120 s (no slack). The chart is never talked through.
- Slide 10: 181 words, about 84 s against 90 s (OK).
- Slide 11: 154 words, about 71 s against 60 s (**over**).
- Slide 12: 141 words, about 65 s against 90 s (spare time).

The risk is visual density on slides 4, 5, 7 and 9 rather than word count. Spare time on slides 8 and 12 could go to explaining the slide 9 chart.

Minor: the script header says "9 backup slides", but the PDF has 8 plus a divider. The Q&A table cites "168 requests", a number that never appears on a core slide.
