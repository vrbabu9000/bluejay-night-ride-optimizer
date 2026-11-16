# Review: presenter and preparation (midterm content draft v0.3)

**Reviewer role:** independent presenter and preparation reviewer. **Date:** 23 Oct 2026.
**Objects reviewed:** `speaking_script.md` (primary); `BlueJay_Midterm_v0.3_preview.pdf` (all 32 pages); `slide_explanations.md`; `content_storyboard.md`; `README.md`. I checked claims against `docs/technical/` (decision log, `scenario_spec.md` v0.8, `scenario_methodology.md` v1.4, `preregistration_v2.md`) and `docs/ai_use_log.md`. No project file was edited.

## Verdict

The package is close to deliverable. The spoken text is plain, the six rule names are used consistently, no codes slip into what is said, the anchors resolve, and the handoffs work for two to five speakers. A presenter who has read the script and the explanations could deliver most slides confidently.

It is **not yet ready for the 10 minutes of questions** from a professor who emphasises Pareto analysis and leader–follower modelling. Four problems carry high risk:
1. **Slide 19's comparison depends on the patience shape.** The claim that earlier transfers lose fewer riders, and the line "the mechanism does not [depend on patience]", hold only because the placeholder patience has an increasing hazard (Weibull shape 1.5). Under the exponential shape that D-39 keeps as a sensitivity, the gap between rules would disappear.
2. **"Independent reviewers" on slide 17 are AI review agents.** The AI-use log records this, but the slide and the script do not say it plainly. Asked directly, a presenter could easily misstate who wrote the checks.
3. **The threshold answer on slide 13 cites "operating targets of 10–15 min".** No source supports this. The sources give 15/20/20 (April era) or 20/25/25 (live page).
4. **The Pareto and leader–follower Q&A is thin.** The script has one prepared question for each. It is missing supported versus unsupported points (no weighting of the two objectives would ever choose the waiting-time rules), the marginal service per Lyft booking ("is it just more Lyft?"), dominance on means versus per night, and "isn't a threshold sweep already the leader's problem?".

Timing works overall: the section times sum to exactly 20:00, and the spoken text is about 18.1 min, or about 18.9 min once numbers are spoken in full. Within that, slides 6, 12, 15 and 14 run over their budgets, and slides 17, 19, 20 and 22 run 9–13 s under. The budgets should be rebalanced, not the text cut.

---

## 1 · Per-slide timing

Method: I counted the words in each quoted Spoken block plus its spoken transition. Each estimate expands every number into the words a speaker says ("18:30:08" counts as five or six words, "23,843" as five). Speed is 125 wpm. A flag marks a slide more than 5 s off its budget. The raw (unexpanded) total is 2,263 words, 18.1 min; the expanded total is about 2,364 words, 18.9 min.

| Slide | Budget s | Words (raw / spoken) | Est. s | Flag |
|---|---|---|---|---|
| 1 | 25 | 43 / 43 | 21 | ok |
| 2 | 55 | 129 / 129 | 62 | **over +7** |
| 3 | 50 | 101 / 103 | 49 | ok |
| 4 | 50 | 92 / 92 | 44 | under −6 |
| 5 | 30 | 52 / 52 | 25 | ok |
| 6 | 60 | 124 / 146 | 70 | **over +10** (ten numbers in one breath) |
| 7 | 55 | 112 / 112 | 54 | ok |
| 8 | 45 | 76 / 80 | 38 | under −7 |
| 9 | 55 | 95 / 106 | 51 | ok |
| 10 | 55 | 89 / 100 | 48 | under −7 |
| 11 | 50 | 94 / 94 | 45 | ok |
| 12 | 75 | 168 / 172 | 83 | **over +8** (densest slide) |
| 13 | 60 | 112 / 112 | 54 | under −6 |
| 14 | 60 | 116 / 135 | 65 | over +5 (seven clock times) |
| 15 | 60 | 129 / 141 | 68 | **over +8** |
| 16 | 55 | 96 / 98 | 47 | under −8 |
| 17 | 50 | 80 / 86 | 41 | under −9 |
| 18 | 65 | 131 / 133 | 64 | ok |
| 19 | 60 | 93 / 98 | 47 | under −13 |
| 20 | 65 | 114 / 114 | 55 | under −10 |
| 21 | 55 | 109 / 109 | 52 | ok |
| 22 | 65 | 108 / 109 | 52 | under −13 |
| **Total** | **1,200 (20:00)** | **2,263 / ≈2,364** | **≈1,135 (18.9 min)** | |

**Section sums.** Each section matches its storyboard budget: opening 1–4 = 180 s, investigation 5–10 = 300 s, model 11–16 = 360 s, findings 17–20 = 240 s, direction 21–22 = 120 s. The total is 20:00 exactly.

**Observations.**
- The per-slide time windows (for example "8:50–10:05") give all 20 minutes to speech and none to the four handoffs. The real slack is about 1.1 min (with numbers spoken in full), not the 1.5 min stated in the header and README.
- At 125 wpm the script is safe. Nervous speakers usually run at 140–150 wpm, which would finish around 16 min. That is a reason to prepare one optional sentence per section; see correction T3.

---

## 2 · Findings

Severity: **high** means a likely wrong or indefensible answer in front of the professor; **medium** means visible confusion or a weak answer; **low** means polish.

| # | Slide | Severity | Finding | Correction (concrete replacement text) |
|---|---|---|---|---|
| 1 | 19 | **high** | The spoken text says "Transferring earlier leaves more time for the Lyft to arrive. Note that these sizes depend on our placeholder patience; the mechanism does not." The slide's ASSUMED box says the same. The *existence* of losses after a transfer does not depend on patience. The *gap* between "Wait ten minutes" (about half lost) and the prediction rules (about a third) comes from the assumed increasing impatience (Weibull shape 1.5, D-39). With constant-hazard (exponential) patience, which D-39 keeps as a sensitivity shape, the chance of cancelling during the same 2 + 8 minutes would be equal whenever the transfer happened. Check from the placeholder: a 10-min Lyft wait loses ≈ 41% of riders who have already waited 10 min, against ≈ 27% of riders who have waited 1 min; an exponential with the same median gives ≈ 32% for both. The explanations (§19, "Scope") repeat the overclaim. | **Spoken:** "…Under the two prediction rules, about a third cancelled. In our model, impatience grows the longer a rider has waited, so a rider moved early has more patience left for the Lyft. That a transfer starts a new wait does not depend on our patience assumption; how many riders it loses, and the gap between rules, does." **Slide ASSUMED box:** "The losses exist under any patience; their size and the gap between rules depend on the placeholder (impatience rising with time waited)." Add a likely question to the script; see Q&A entry P3. |
| 2 | 17 | **high** | The slide says "253 automated tests pass (168 written by independent reviewers)". The script answers "Separate review agents". `ai_use_log.md` (entries of 1 Oct and 22 Oct) shows that the coordinating session wrote the simulator and that the independent tests and the brute-force checker came from Claude Code subagents. "Independent reviewers" reads as people. If the professor asks "who are the reviewers?", the honest answer must come first and without hedging. | **Slide:** "253 automated tests pass (168 written by separate AI review agents that saw only the specification)". **Script, Likely questions:** "**Who wrote the code and the checks?** The simulator and optimizer were written with an AI coding assistant under our direction, and every use is logged in `docs/ai_use_log.md`. The 168 independent tests and the brute-force checker were written by separate AI agents that worked from the specification, not the simulator code. We reviewed the results; independence here means separate derivation, not a different human team." |
| 3 | 13 | **high** | The script answer and explanations §13 both say "They are the operating targets of 10–15 min". No source gives a 10–15-min target. Methodology §1/D-49 give 15/20/20 (pages captured around April) and 20/25/25 (live page, 21 Oct). D-29 uses 15 and 20 as reporting thresholds. The professor knows the targets from the proposal. | **Script:** "**Why these thresholds?** Fifteen minutes is the first April-era service target; ten is an earlier trigger, to see the effect of acting sooner; two minutes is a margin against prediction error. All were fixed in pre-registration v2 before any run (spec §7.4) and not tuned. A threshold sweep is the next step." Make the same correction in explanations §13 ("Thresholds"). |
| 4 | 20 | **high** | There is only one prepared Pareto question ("Is this the Pareto frontier?"). The script has nothing on supported versus unsupported nondominated points, weighted sums or λ, dominance on means versus per night, or "is it just more Lyft?". These are the professor's emphasis. | Add Q&A entries P1, P2, P4, P5 and P6 below to the script's slide 20 (and P2 to slide 18). |
| 5 | 21 | **high** | There is only one prepared leader–follower question ("Isn't your loop already leader–follower?"). The script is missing "isn't a threshold sweep the upper level by enumeration?", "who is the leader in reality?", "why bilevel if one organization runs both levels?" and "why is the follower per-epoch?". | Add Q&A entries L1–L4 below. Recommend that whoever presents slide 21 also takes the leader–follower questions. |
| 6 | 14 | medium | "…and the rider was dropped at 18:30:25, a wait of ten and a half minutes from the original request." This attaches the 10 min 30 s wait to the drop-off. It is request to curb (18:16:30 → 18:27:00). The clock times with seconds are also hard to say. A sharp listener will notice that the drop-off (18:30:25) is 17 s after the van's *predicted pickup* (18:30:08); the script does not prepare that. | **Spoken (replace the last three sentences):** "The Lyft was booked two minutes later, at 6:19, reached the curb at 6:27, ten and a half minutes after the request, and had the rider at their destination by about 6:30, roughly when the van was predicted to arrive. But the van time was only a prediction; we never see what the van would actually have done." Say "six sixteen and thirty seconds" or "about 6:16", never "eighteen sixteen thirty". |
| 7 | 6 | medium | The spoken text ends "So treat 168 as a derived workload", but 168 is not on the slide. The slide shows 64 / 50 / 54. The chain caption under "× 2.09 ≈ 355" reads "bookings per completed ride (all statuses)", which describes the 2.09, not the 355. The slide is also 10 s over budget. | **Spoken (last two sentences):** "What stays unknown is how many of those vehicles served Homewood, and how many bookings were repeats. So these 168 bookings in three hours are a derived workload, not a measurement." Optionally add "= 168 in three hours" to the fourth chain card. **Slide caption 2:** "bookings in that hour (2.09 bookings per completed ride)". **To recover time:** replace "About 27.6 vehicles were on duty. That gives 12.85 bookings per vehicle per hour." with "With 27.6 vehicles on duty, that is 12.85 bookings per vehicle per hour." |
| 8 | 4–6 | medium | Three versions of one quantity appear on consecutive slides: 5,098 (slide 4, tooltip), 5,089 (slide 5 and the chart, digitized) and "≈ 5,100" (slide 6 chain, spoken). The script explains this only in a slide-4 answer. | **Slide 5 preparation note:** "5,089 is our digitized bar; the dashboard tooltip says 5,098 (slide 4); we round to 5,100 when speaking. The 0.2% difference changes nothing downstream." |
| 9 | 12 | medium | The slide is 8 s over budget. Reading eight step names aloud costs about 35 words. "A large constant makes serving everyone come first" (spoken and on the slide) overstates D-47/D-52, which say the constant makes the optimizer serve *as many bookings as possible*; some can still wait when routes compete or the three-pickup cap excludes them. | **Spoken (steps):** "The strip along the top is the loop that runs every two minutes and at every new event: reveal what happened, generate each van's feasible routes, choose one route per van, apply the transfer rule, re-plan once if needed, and drive." **Spoken and slide (postponement):** "…but a large constant makes serving as many bookings as possible come first." |
| 10 | 15 | medium | The spoken text says "We compared three versions over the whole evening", but the slide shows two columns; the third is in B5. The evidence that *is* on the slide (longest wait 44.4 → 35.6, mean unchanged) is never said, while "It adds nothing to the model" is. There is no prepared answer to the obvious challenge: "the median got worse and, per explanations §15.4, the youngest booking waited 35.6 min instead of 9.8; why is this a fix?" The slide is 8 s over budget. Spoken 262 and 436 against displayed 262.5 and 435.8 is acceptable rounding. | **Spoken (replace from "We compared three versions…"):** "We compared alternatives over the whole evening and chose the simplest: price the earliest physically possible pickup, with no extra variables. The longest wait fell from 44 to 36 minutes, but the average stayed the same; waiting was redistributed, not reduced. And the price is still optimistic, because it ignores the work the nearest van is already doing." **Add a likely question:** "**Your fix made the median worse?** Yes, slightly (17.1 → 18.6 min). We did not choose it for outcomes on one evening; we chose it because the old price was provably below any service a van could give, and the fix costs nothing. The third, route-based version was worse on mean wait (21.8) and can err either way (B5, slide 28)." |
| 11 | 13 → 18–20 | medium | Slides 18–20 speak of "the two prediction rules" and "the two waiting-time rules", but slide 13 never names these groups aloud (only the colour legend does). | **Spoken, slide 13, after the six rules:** "We'll call the first two transfer rules the waiting-time rules, and the last two the prediction rules." (+15 words; slide 13 has 6 s spare.) |
| 12 | 11 | medium | The storyboard says B3 and B4 are linked from slide 11, but slide 11 has no forward link (`build_deck.js` has no `link()` call on slide 11), and the script mentions neither backup. B4 is the backup for every "where does this input come from?" question. | **Slide 11:** add "Inputs: B4 → · Event order: B3 →". **Script slide 11, Deeper:** "backups B3 (slide 26) and B4 (slide 27)". **Script slide 3, Deeper:** add "backup B9 (slide 32)". |
| 13 | Q&A | medium | Every backup's "← back to slide N" link returns to its origin slide, not to the closing slide. Slide 22 has no link to the divider (23). During Q&A the presenter has no one-click route from slide 22 to a backup or back. The script has no question-to-backup jump table. | Add a link "Backups →" (to 23) on slide 22. Add the **Q&A jump table** in §4 below to the top of the script. Brief every presenter that in PowerPoint slide show, typing the number and pressing Enter jumps to that slide (24–32). |
| 14 | B4 (27) | medium | "Travel times · OBSERVED road network · Local OSRM routing; van times × 1.2 in the pilot". The ×1.2 multiplier is ASSUMED (spec §5 and §13: "base 1.2 (ASSUMED; calibrated)"), and the script nowhere explains it. | **B4 status cell:** "OBSERVED network; ASSUMED × 1.2 slowdown". **Script, slide 11, Likely questions:** "**Are travel times real?** Road-network times from a local OSRM router, multiplied by an assumed 1.2 for traffic and stops; the multiplier is a placeholder to calibrate (spec §5)." |
| 15 | 10 | medium | The slide and script state two conditions for 8.9%; explanations §10 states three (the third: Lyft hand-offs sit in "Canceled"). The script does not prepare the obvious challenge that 8.9% comes from *van* arrivals but is applied to *Lyft* arrivals too (D-48, one p for all modes). It also does not mention that the frozen inputs still carry `p_noshow: 0.047` (D-48 errata), which a reader of the repository could raise. | **Script, Likely questions:** "**Why use a van rate for Lyft?** It is an assumption (D-48): one presence draw per rider, the same probability for every mode. Separate rates are a deferred sensitivity." and "**Your scenario files say 4.7%?** A known erratum (D-48): those fields are all-booking shares; the simulator does not read them; 8.9% is set in the run configuration." |
| 16 | 16 | medium | The answer to "Are 30 nights enough?" is vague. Pre-registration v2 has a concrete criterion: a CI half-width ≤ 0.7 δ, otherwise 60 nights. The spec also calls this level a "dress rehearsal… too small for conclusions" (§8), which is the best answer to "why two vans?", but the script never uses it. | Replace with Q&A entries S1 and S2 below. |
| 17 | 2 | low | The slide is 7 s over budget. The definitions sentence duplicates the five tiles on screen. | **Spoken:** "…Four words matter later, and they are on the tiles: booking, passenger, curb arrival, and pickup, the rider boarding. So our question is…" |
| 18 | 8 | low | The spoken text says "the other twelve"; the slide shows 12.3%. The text also never says that our own distribution's mean is 1.405, not 1.386, which the legend shows and which invites "why doesn't your mean match?" | **Spoken:** "…one has eight percent of bookings with three or more riders and the other just over twelve." The preparation note already answers the mean question; promote it to a Likely question: "**Why is your mean 1.405, not 1.386?** Ours describes all bookings; April's 1.386 covers completed van bookings only, so they are different quantities." |
| 19 | 18 | low | "With nine to ten" Lyft bookings: the values are 9.3 and 10.5. | "…reach about three quarters, with nine to ten and a half Lyft bookings a night." |
| 20 | 22 | low | "Rides can still exceed our ride limit after an unexpected no-show wait; we saw 36 such cases, each matching a no-show wait on that van" is hard to say and to follow. The slide is 13 s under budget, so there is room to say it more simply. | **Spoken:** "And one honest wrinkle: 36 times, a rider's trip ran past our ride-time limit. Each time, the van had stopped to wait three minutes for a rider who never came out. Our plans never cause that; an unexpected no-show does." |
| 21 | 21 | low | The spoken "still need" list has three items; the slide lists four (it adds "An agreed value λ for Lyft use"). | **Spoken, end:** "…a treatment of uncertainty across nights, and an agreed value on Lyft use." |
| 22 | 1 / handoffs | low | The handoffs work for any split; five segments of 3/5/6/4/2 min combine for two to five speakers. But the script never shows a split, and slide 1 has no line for introducing names. | Add to the script header: "**Suggested splits.** 2 speakers: 1–10 / 11–22 (8 + 12 min) or 1–16 / 17–22. 3 speakers: 1–10 / 11–16 / 17–22 (8 / 6 / 6). 4 speakers: 1–10 / 11–16 / 17–20 / 21–22 (8 / 6 / 4 / 2), or 1–4 / 5–10 / 11–16 / 17–22. 5: one per segment. At each ⇄ the outgoing speaker says the transition line; the incoming speaker begins with the next slide's first sentence, with no re-introduction." Slide 1 spoken: "Good afternoon, we are Team FourSight: [names]." |
| 23 | Timing | low | The per-slide windows leave no seconds for handoffs, and the under-budget slides (17, 19, 20, 22) are exactly where questions of method come up. | Rebalance budgets: 6 → 68 s, 12 → 82 s, 15 → 66 s, 14 → 63 s; 17 → 42 s, 19 → 50 s, 20 → 58 s, 22 → 55 s; then recompute the windows. Keep the 20:00 total. Mark one optional sentence per section to add if running fast (for example finding 1's mechanism sentence on slide 19, the λ sentence on slide 21). |

**Checks that passed (no finding).**
- **Rule names.** All six plain names are spelled identically in the spoken text, the slides, B1, B6, B7 and the explanations. No code (R0, R1…, L4, L5, C, A, D-xx) occurs in any Spoken block or spoken transition; "MILP" is said once and defined.
- **Anchors.** `#s01`–`#s22` exist in both the script and the explanations, and every cross-link resolves.
- **Backup numbers.** Every backup number the script cites matches the deck: B1 = 24, B2 = 25, B5 = 28, B6 = 29, B7 = 30, B8 = 31 (`BK` map in `build_deck.js`).
- **Slide numbers.** Footer numbers match actual positions.
- **Spoken numbers.** The spoken numbers match the slides and the explanations, apart from the rounding noted in findings 7, 10, 18 and 19. Spot checks: 95/196; about a third (93/294, 104/330); 0.477 vs 0.476; 6 of 30 nights; 292,181 → "about 290,000"; 66.5 vs 81.
- **Preparation notes.** They mostly give choice, alternative and caveat (slides 6, 7, 12 and 15 are good models). Slides 5, 11, 13, 16 and 19 have no *alternative* or *rationale* line; the Q&A entries below supply the missing material.

---

## 3 · Missing Q&A entries (proposed short answers)

All answers are grounded in the package or in `docs/technical/`. Numbers marked *(reviewer arithmetic)* are computed from B6/B7 values and should be checked once by the team before use.

### Pareto (slide 20; backups B6, B7)
- **P1. Would any weighting of the two objectives pick "Wait ten minutes" or "Wait fifteen minutes"?** No. They are nondominated but *unsupported*: they lie below the straight line from "Vans only" to "Predicted total wait exceeds fifteen minutes". Minimising "−service + λ × Lyft" picks only "Vans only", "Predicted total wait…" or "Lyft arrives sooner", depending on λ. That is a further reason a rule's being nondominated is weak evidence on its own. *(reviewer arithmetic from B7 means)*
- **P2. Do the prediction rules simply buy service with more Lyft?** Not only. Per Lyft booking, relative to vans only, the prediction rules add about 0.7–0.8 bookings reached within 15 min; the waiting-time rules add about 0.16–0.17. The prediction rules use Lyft more efficiently as well as more often. *(reviewer arithmetic: Δservice × 28 ÷ Lyft bookings, from B7)*
- **P3. Isn't slide 19's difference just your patience assumption?** Partly, yes. That riders can be lost after a transfer holds under any patience model. The *gap* between rules comes from assuming impatience grows with time already waited. Under constant-hazard patience (the sensitivity shape kept in D-39) it would vanish. Testing patience is step 4 of our next steps.
- **P4. Why compare means? What about variability?** The means are descriptive. Night by night (B7, slide 30), the prediction rules reach more than vans only on all 30 nights, and "Wait ten minutes" on 19 (fewer on 6). Intervals wait for the agreed criteria (D-50).
- **P5. Isn't "Vans only" trivially nondominated?** Yes. Any rule with zero Lyft use is nondominated unless another zero-Lyft rule serves more. That is why we say nondominated is not recommended.
- **P6. Why Lyft bookings, not dollars?** The cost per Lyft trip is unknown, and the base model deliberately has no money (D-45). Bookings are an operational count. The same five rules stay nondominated with van-km as a third objective.
- **P7. How would you get an actual frontier?** Sweep each rule's threshold and trace the curves (methodology §7b). A frontier of *all* policies would need the policy optimization of slide 21.

### Leader–follower (slide 21)
- **L1. Isn't a threshold sweep already solving the leader's problem?** For a one-parameter rule, a sweep evaluates the upper level by enumeration, with our simulator as the follower. It approximates "choose θ", but it is not a solved bilevel program: our follower optimizes one decision moment at a time over restricted candidates, not over the whole evening, and λ is not agreed.
- **L2. Who is the leader in reality?** Whoever sets the transfer policy for the service (the policy designer on the slide). The follower is the routing dispatcher, which re-plans vans for the bookings left after transfers. Riders and Lyft are not modelled as optimizing players.
- **L3. Why bilevel, if one organization runs both levels?** The levels have different objectives. The leader weighs service against Lyft use (λ); the follower minimises routing points (slide 12). Collapsing them into one level would need specific assumptions, such as optimality conditions written as constraints, which are hard with an integer follower. We claim no such reduction.
- **L4. Your rule reads the optimizer's plan. Isn't that anticipation?** It is reaction, not anticipation. The rule reads the current plan, then the optimizer re-plans once. Nothing chooses the rule *by* evaluating the optimizer's response.

### Synthetic data, validity and scale
- **V1. Your evenings match April by construction, so what does that prove?** Nothing about validity. They reproduce April's totals (place totals to about 10⁻¹⁰, load per vehicle), which makes them plausible inputs, not validated ones. Validation means matching April's outcome shares and wait and ride percentiles. Those calibration targets are listed in the methodology, and calibration has not started.
- **V2. Why not just compare dispatch algorithms, as proposed?** On synthetic nights, an algorithm comparison would mostly compare our own assumptions. Holding the van optimizer fixed and changing only the transfer rule isolates the decision we care about (B9, slide 32; D-25, D-51).
- **V3. Why 18 minutes median patience?** It is a placeholder (D-39). Weibull shape 1.5 encodes impatience rising with time waited; nothing calibrates the median yet. The calibration target is the share of "Canceled" that riders caused, 50–75%. Slide 19's sizes depend on it.
- **V4. Is no-show related to how long the rider waited?** Not in our model. Presence is one draw per rider, independent of the wait. The data cannot identify a dependence (D-48).
- **S1. Why two vans, not five?** In our level ladder, the two-van night is the dress rehearsal for the pipeline: pairing, metrics and checks (spec §8). It is "too small for conclusions" by design. Its load (14 per van-hour) is close to April's 12.85. The five-van evening (168 bookings, three hours) is built into the design and needs solve times benchmarked first (D-51). The pilot already took up to 253 s per run with two vans.
- **S2. Are 30 nights enough? Why not 180?** The 180 runs are 30 nights × 6 rules, paired, so they are not 180 independent observations. Whether 30 is enough is decided by pre-registration: if the expected interval half-width exceeds 0.7 δ, we use 60 nights per cell (`preregistration_v2.md`). That calculation waits on the margins in D-50.
- **O1. Optimal in what sense, given 41 incomplete tie searches?** The main solve was proven optimal at all 13,663 decision moments. The 41 incomplete *tie* searches only looked for equally good alternatives, and full enumeration shows a unique optimum in each (B8, slide 31).
- **O2. Why are the prediction-rule runs ten times faster (B6 run time)?** We have not analysed it. A likely reason is fewer bookings left waiting in van planning, so fewer candidate routes. Say so only as a hypothesis.

### Slide-specific additions
- **Slide 14:** "**Wasn't the rider dropped off before the van would even have arrived?**" Yes: drop-off at 18:30:25, against a predicted van pickup at 18:30:08. But that van time is a prediction; the run never shows what the van would have done. This is a designed evening, not evidence of a saving.
- **Slide 17:** "**Who wrote the code and the checks?**" See finding 2.
- **Slide 15:** "**Your fix made the median worse?**" See finding 10.

---

## 4 · Proposed Q&A jump table (add to the top of the script)

| Question is about | Go to | Slide |
|---|---|---|
| Codes in files, R0…R3, L4/L5 | B1 | 24 |
| The MILP, the M bound, solver settings, "optimal" | B2 | 25 |
| Event order, commitment, curb wait, presence draw | B3 | 26 |
| Where an input comes from (patience, Lyft delay, ×1.2) | B4 | 27 |
| Postponement price alternatives | B5 | 28 |
| Any metric by rule (pickups, cancellations, van-km) | B6 | 29 |
| Pareto per night, paired counts | B7 | 30 |
| Solver diagnostics, run times, guardrail excesses | B8 | 31 |
| Proposal corrections, why the study changed | B9 | 32 |
| Pareto picture | main | 20 |
| Leader–follower | main | 21 |

Return to the closing slide by typing 22 and pressing Enter.
