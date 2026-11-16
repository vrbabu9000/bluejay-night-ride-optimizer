# Midterm report review: cohesion and alignment with the presented deck

Reviewed: `docs/report/midterm/BlueJayNightRide_Midterm.tex` and the rendered PDF (17 pages), against the final deck text (42 slides), `speaking_script.md` and `slide_explanations.md` (v0.4).

Slide numbering below uses the numbers printed on the slides as presented (S1 to S28, B1 to B9). In the deck text file, main slide Sn is "Slide n+3" and B1 to B9 are "Slide 34" to "Slide 42".

## Overall verdict

The report is cohesive. Every section carries the same central idea (one controllable decision, the Lyft transfer rule, with a fixed van dispatcher on synthetic evenings built from April aggregates; a service vs Lyft trade-off; verified, not validated; no recommendation), and the hand-offs between sections are clear. All numbers checked against the deck agree: Table 11 matches B6 cell for cell, Appendix A matches B7, Table 10 matches B8, Table 9 matches B5, Table 2 matches S4/B9, and the worked example (Table 8) matches S16. Rule names, the evidence labels and the main caveats are the same as on the slides.

The gaps are few but some touch the main result. (1) The limitations table drops two of the five assumptions the deck put on S26 (geography/pairing and the candidate restriction). (2) The report never says what the predictive rules read for a postponed request (the deck's "tentative estimate", S17), although the main result depends on it. (3) The abstract states the main result without the "early transfer, not prediction" caveat that Section 8.1 itself develops. (4) Section 4.5 promises that "calibrating patience" is the first step of the plan, but the plan's first step is sensitivity testing. The plan also goes beyond the deck: it adds a matched-budget baseline and a dispatcher benchmark. These extras are consistent with the deck, but the report does not yet link the benchmark to the transfer-rule question. The other findings are minor: inconsistent terms ("booking", "pickup"), a label mismatch, and a few repetitions and loose threads.

## Section by section

| Section (PDF page) | Deck slides | Cohesion | Deck coverage |
|---|---|---|---|
| Abstract (p.1) | S1, S22, S24, S28 | OK | Issue: main result lacks the early-transfer / no-equal-budget caveat of S22 (F3) |
| 1 Introduction (p.1-2) | S1, S2, S5, S14 | OK; extra motivation (wait 90th pct 17-21 min) is used | Issue: S2's "pickup = boarding" not defined; "booking" later used two ways (F6) |
| 2 Changes to the Original Plan (p.2-4) | S3, S4, S5, B9 | OK; feedback table (report-only extra) hands off well to Sec 11 | OK; Tables 1-2 match B9 and S4. Feedback table promises "candidate cap" as a benchmark lever that Sec 11 item 6 does not vary (F5) |
| 3 Data (p.3-4) | S6 (and S7, S9, S12 numbers) | OK | Minor: 1.386 labelled OBSERVED in Table 4, DERIVED in Sec 4.4 and S10 (F8); label set differs from slides (F15) |
| 4.1 Volume (p.3) | S7 | OK | Minor: drops S7's 150-260 illustrative range and the "designed, not yet run" flag (F9) |
| 4.2 Pilot (p.3) | S8 | OK | OK |
| 4.3 Pairing (p.3-4) | S9 | OK | OK (IPF tolerance is an extra) |
| 4.4 Group sizes (p.4) | S10 | OK | OK |
| 4.5 Patience (p.4) | S11 | Issue: promises "calibrating patience" as first plan step; never delivered (F4) | OK; the 38.6% vs 23.7-35.5% check is a consistent extra |
| 4.6 No-shows (p.5) | S12 | OK | OK |
| 4.7 Blueprint (p.6) | S13, B4 | OK | Minor: omits the "Van dispatcher (fixed)" and "Transfer rule (varied)" rows that tie the blueprint to the central idea (F10) |
| 5 Simulator and dispatcher (p.6-11) | S14, S15, S16, S19, B2, B3, B5 | Minor: second system diagram (Fig 8 repeats Fig 1); Table 7 floats into Sec 5; K=3 rationale repeated in Sec 9 (F14); one sentence misattributes April's ride tail (F17) | OK; matches S15 cycle, S16 objective and example, B2, B5 |
| 6 Transfer rules (p.10-12) | S17, S18, B1 | Minor: "two groups" leaves R1u unclassified (F7) | Issue: missing the tentative estimate for postponed requests (F2); colour coding differs from deck (F7) |
| 7 Design and verification (p.11) | S20, S21, B8 | OK | Minor: AI-test wording differs; "3 designed evenings, to the second" dropped (F16) |
| 8 Results (p.11-14) | S22, S23, S24, B6, B7 | OK; strongest section; the early-transfer analysis is a consistent extra that sets up plan item 4 | OK; all numbers match B6/B7. Minor: S24's "adding objectives or criteria can change the assessment" only implicit |
| 9 What did not work (p.13) | S4, S19 (partly); otherwise report-only | Minor: node-arc "hindsight benchmark" introduced and never used (F13) | Extra, consistent |
| 10 Limitations (p.13-14) | S26 | OK | Issue: two of S26's five assumptions missing; workload row reframed (F1) |
| 11 Plan (p.14-15) | S25, S27 | Issue: benchmark not linked to transfer-rule question; timeline order (F5, F12) | Extras (matched-budget baseline, dispatcher benchmark) beyond S27; leader-follower definition list shorter than S25 (F11) |
| 12 Conclusion (p.15) | S28 | OK | OK; wording refines S28 ("moved requests early, guided by...") consistently |
| App A (p.17) | B7 | OK | OK, identical |
| App B (p.17) | B2 | OK | OK; minor differences in detail (Σ b_r^max vs Σ b_r; gap "below one unit" vs 0.5) are refinements |
| App C (p.17) | B3 | OK | OK; omits B3's note that van off-duty and Lyft events never trigger a decision moment (harmless) |

## Findings

**F1. Major. Sec 10, Table 12 (p.14); deck S26.**
Quote: Table 12 rows are "Rider patience", "Lyft delay", "Workload", "Fleet size", "Dispatcher"; Workload: "a different load changes how often vans fall behind".
Problem: S26 presented five assumptions: patience, Lyft delay, workload and burst, geography and pairing, and the candidate restriction. The report drops "Geography and pairing" ("longer or more scattered trips change van reach and predicted pickups") and "Candidate restriction" ("a richer search could change van performance and the rules' predictions"). The second matters most because the predictive rules read predictions the cap shapes. The workload row also drops the deck's directional claim: "at lighter load the rules may barely differ". Fleet size and Dispatcher are good additions, but the report should not lose what the deck said.
Fix: Add the two rows (Trip pairing, ASSUMED; Candidate cap K=3, DESIGNED) with the deck's wording, and restore "at lighter load the rules may barely differ" to the workload row.

**F2. Major. Sec 6 and Table 7 caption (p.8, p.10); deck S17.**
Quote: "'Predicted total wait' is the van plan's predicted pickup clock time minus the request clock time; a request with no feasible van counts as infinitely late".
Problem: S17 also says what the rule reads for a postponed request: "the van plan's time, or a tentative estimate if the request is postponed" (spec: cheapest feasible insertion, computed outside the MILP). The report leaves this out. Yet Sec 8.1 explains the main result by the predictive rules firing "at the first decision moment at which the plan already predicted a long wait" (median 0 s waited). Many of those requests are likely to be postponed ones, so readers cannot tell what the rule actually compared.
Fix: Add one sentence to the Table 7 caption or Sec 6: "For a request postponed in the current plan, the rule reads a tentative pickup estimate (cheapest feasible insertion into the chosen routes, computed outside the MILP); it is not a promised pickup."

**F3. Major. Abstract (p.1); deck S22, S28.**
Quote: "the two rules that read the van plan's predicted pickup reached about three quarters of requests within 15 minutes, against about half with vans only, while ordering roughly 9 to 10.5 Lyft rides per night."
Problem: As written, the abstract invites the reader to credit the prediction. S22 carries the caveat "does not isolate the benefit of prediction at an equal Lyft budget", and Sec 8.1 goes further: the gain "largely reflects transferring early". The conclusion reflects this ("moved requests early, guided by the van plan's predicted pickup"). The abstract, which most readers see first, does not.
Fix: Append a clause such as "a gain that largely reflects transferring early and is not yet compared at an equal Lyft budget."

**F4. Major. Sec 4.5 (p.4) vs Sec 11 (p.14); deck S27.**
Quote: "Calibrating patience is the first step of our plan (Section 11)."
Problem: Plan item 1 (and deck S27 step 1) is behavioural sensitivity: rerunning saved nights under other patience shapes. Calibration appears nowhere in Sec 11. This is a promise the report does not keep. Calibrating to April's give-up share and testing robustness across shapes are different activities, and the deck's ordering argument ("test robustness before fine-tuning") applies to the difference.
Fix: Change to "Testing other patience shapes is the first step of our plan", or add an explicit calibration check (for example, match the 23.7-35.5% give-up share) to plan item 1.

**F5. Minor. Sec 11 item 6 and Abstract (p.1, p.15); Table 3 row 2 (p.4); deck S27, S5.**
Quotes: Abstract: "the report closes with the robustness tests and the dispatcher benchmark planned for the final". Item 6: "the same service measure and Lyft count as above". Table 3: "so the levers are re-planning interval and candidate cap".
Problem: The deck's plan (S27) has four steps and no dispatcher benchmark or matched-budget baseline. These report extras are consistent with S5's "scope choice" framing and answer the feedback, so they are fine. But (a) item 6 does not say which transfer rule is held fixed while dispatchers are compared, or whether the transfer-rule comparison is repeated under greedy insertion. That is the link back to the central question. (b) Table 3 names the candidate cap as a benchmark lever, but item 6 varies only fleet, demand and re-planning interval. (c) The abstract's last sentence gives the benchmark equal billing with robustness, which the deck did not.
Fix: In item 6, state the transfer rule(s) used during the benchmark and whether rule rankings are rechecked under greedy. Add the candidate cap (K = 2, 3) to item 6, or drop it from Table 3. Consider "closes with robustness tests, then a dispatcher benchmark" in the abstract.

**F6. Minor (affects meaning). Fig 6 caption (p.7) vs Fig 1 (p.2), Fig 12 (p.12), Sec 8.2 (p.12), Fig 14 caption (p.13); Intro; deck S2, B1.**
Quotes: Fig 6: "a 'booking' here is one Night Ride request". Sec 8.2: "18 during the ordering lag, 77 after booking". Fig 14: "cancelled after booking". Fig 12 axis label: "booking τ + ℓ".
Problem: "Booking" means a Night Ride request in one place and a Lyft order in others (the file convention, B1). S2 defined booking as a Night Ride request and said "Lyft order" for the other. Relatedly, S2 defined "pickup" as the rider boarding, distinct from curb arrival. The report never defines pickup, yet uses "requests picked up" (boarding) in Table 11 and "predicted pickup" (vehicle at the curb) in the rules.
Fix: Use "Lyft order" (and "after the Lyft order was placed") in Sec 8.2, Fig 14 and Fig 12, or drop the definition in Fig 6. Add S2's one-line definition of pickup (boarding) to the Intro's "One request" paragraph.

**F7. Minor. Sec 6 (p.10), Fig 13 caption (p.12), Sec 8.1; deck S17, S22.**
Quote: "Two groups matter: the waiting-time rules ... the predictive rules"; Fig 13: "Green: predictive rules".
Problem: "Unassigned for ten minutes" fits neither group. S17 made it a third category ("continuously unassigned time"). Sec 8.1's "waiting-time rules barely moved it (0.50-0.51)" silently excludes it (0.48). The deck coloured the predictive rules blue and the unassigned rule green, while the report's Fig 13 colours the predictive rules green, which could confuse anyone holding both.
Fix: Say "three kinds of information" (time waited, time unassigned, the plan's prediction), as on S17. Align colours or name them consistently.

**F8. Minor. Table 4 (p.4) vs Sec 4.4 (p.4); deck S10.**
Quote: Table 4 caption "All are OBSERVED except the last block", with "Van passengers per completed request 1.386" in the observed block.
Problem: Sec 4.4 and S10 label 1.386 DERIVED (a ratio of two observed totals).
Fix: Move the 1.386 row into the DERIVED block.

**F9. Minor. Sec 4.1 (p.3); deck S7.**
Quote: "For a planned evening of five vans ... gives 64 / 50 / 54 = 168 requests".
Problem: S7 also said "Illustrative range about 150-260 (unknown Homewood share of vehicles, repeat requests)" and flagged "PLANNED, NOT YET RUN: the five-van, 168-request evening is designed but has not been run". The report gives a single point value with no range, and the "not yet run" status appears only in Sec 11.
Fix: Add the range with its two reasons, and one clause saying the evening has not yet been run.

**F10. Minor. Sec 4.7, Table 6 (p.6); deck S13.**
Problem: S13's blueprint ended with "Van dispatcher (fixed) DESIGNED" and "Transfer rule (varied) DESIGNED", which tie the scenario to the central idea. Table 6 omits both.
Fix: Add the two rows.

**F11. Minor. Sec 11, "A possible extension" (p.15); deck S25.**
Quote: "we would still need to define the leader's choices, whether the follower is one decision moment or a whole evening, how ties are treated, the expectation, and the loss."
Problem: S25 listed six items. The report omits "the weight on Lyft use" and "any budget or service-floor constraints". It also omits S25's caveat that a finite search optimizes "the average over our sampled nights, not the true expectation, not continuous thresholds", and the script's reason it is bilevel (the dispatcher optimizes its own routing points, not the designer's criteria).
Fix: Restore the two items and one sentence giving the reason it is bilevel.

**F12. Minor. Sec 11 Timeline (p.15) and Fig 16; deck S27.**
Quote: "Late November: paired intervals, threshold search, robustness checks."
Problem: Placing "robustness checks" after the threshold search reads against the section's own principle and S27's title ("test robustness before fine-tuning a winner"). The matched-budget baseline (item 4) has no slot in the timeline.
Fix: Rename the late-November item (for example "out-of-sample checks on fresh seeds") and place the matched-budget baseline explicitly.

**F13. Minor. Sec 9, node-arc paragraph (p.13).**
Quote: "The node-arc form survives only as a possible offline hindsight benchmark on tiny nights."
Problem: This idea is introduced and never used: it is not in the plan or in the dispatcher benchmark.
Fix: Either add it to plan item 6 as an optional check or drop the sentence.

**F14. Minor. Sec 1 Fig 1 (p.2) vs Sec 5 Fig 8 (p.8); Table 7 placement (p.8); Sec 5.1 (p.10) vs Sec 9 (p.13).**
Problem: The report repeats three things. Two system diagrams show the same architecture, while the deck used one (S14). The six-rule table floats into Section 5, two pages before Section 6 defines the rules. The K = 3 rationale is stated almost verbatim twice ("exact ordering with four new pickups took minutes per decision moment in Python").
Fix: Keep one architecture figure, or make Fig 1 explicitly the overview and Fig 8 the decision-step detail. Move Table 7 to Section 6. In Sec 9, cite Sec 5.1 instead of repeating it.

**F15. Minor. Sec 3 (p.4), label set; deck S8, S10, S20, S25, S27.**
Quote: "Every number then received one of four labels, used on every slide and throughout this report ... Outputs of the simulator are labelled SIMULATED."
Problem: The deck labels results "TESTED IN SIMULATION" and also uses "PLANNED, NOT YET RUN", "PROPOSED, NOT IMPLEMENTED" and "ILLUSTRATIVE". A reader who compares the two sees different vocabularies. The report's SIMULATED is fine on its own.
Fix: Add one clause: "(the slides' 'tested in simulation')". Optionally reuse "planned, not yet run" in Fig 16 (it already says "all planned, not yet run").

**F16. Minor. Sec 7 (p.11); deck S21.**
Quote: "168 of them written by separate AI review agents that did not write the simulator."
Problem: S21 says the agents "did not reuse the simulator's code", which is a narrower claim. The report also drops S21's concrete item: "3 small designed evenings reproduce hand-computed event times to the second".
Fix: Use the deck's wording and restore the three-evening, to-the-second check.

**F17. Minor (meaning). Sec 5.1, "Weighted, not lexicographic" (p.10).**
Quote: "A strict priority on waiting can buy a tiny wait saving with an unbounded on-board detour, the long-ride tail behind April's 24-minute ride percentile."
Problem: This reads as if April's ride-time tail were caused by a wait-first dispatcher. Sec 3 attributes the tail only, and cautiously, to shared-ride detours ("consistent with detours").
Fix: Write "the kind of long-ride tail April's 24-minute percentile warns about", or drop the clause.

## Resolution (main session, 3 Nov 2026)

Checked against the deck text and the source; the report was rebuilt (18 pages).

- **Applied:** F1 (Table 12 now carries the deck's five assumptions plus fleet size and dispatcher; workload row reads "at lighter load the rules may barely differ"), F2 (Sec 6 states the tentative estimate for postponed requests), F3 (abstract caveat on early transfer and equal Lyft budget), F4 (Sec 4.5 now points to the sensitivity step, and plan item 1 checks the vans-only give-up share against April's range), F6 (Lyft "booking" now "order" in text and Fig 14; Fig 6 caption scopes "booking"), F7 (three rule groups; Fig 13 recoloured to the deck: blue predictive, green unassigned, grey waiting-time), F8 (1.386 moved to the derived block), F9 (150 to 260 range and "not yet run" added), F10 (dispatcher and transfer-rule rows added to Table 6), F11 (bilevel paragraph lists all six open definitions and the sampled-nights caveat), F12 (timeline reordered, baseline added), F16 ("did not reuse the simulator's code"; three designed evenings to the second), F17 (ride-tail claim softened), F5 (benchmark now states the transfer rule held fixed).
- **Held:** F5, the candidate cap as a benchmark lever (adding it is a new plan commitment for the team to decide); F13 (the hindsight benchmark is a stated possibility, not a promise); F14 (Fig 1 is the conceptual system and Fig 8 the software layout; Table 9 now sits in Sec 6); F15 (SIMULATED kept as the report's label; the deck's PLANNED and PROPOSED tags are carried in wording).
