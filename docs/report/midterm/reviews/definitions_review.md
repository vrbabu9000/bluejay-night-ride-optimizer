# Definition-before-use review: BlueJayNightRide_Midterm (17 pp.)

Reviewed: `BlueJayNightRide_Midterm.tex` and the rendered PDF, in reading order (title, abstract, body, floats where they land on the page, appendices). Figure-internal text was also checked, because a professor reads the labels inside a figure as part of the figure.

## Verdict

The report is in good shape on its core vocabulary: curb arrival, cancellation, no-show, the evidence labels, the rule codes (Table 7 is a full key and lands before every code use), the MILP variables, phi, Psi, K, G_r, T_r, pi_r, b_r and dominance are all defined clearly, mostly at first use. The problems cluster in three places:

1. **Front-loaded floats.** Table 1 (p. 2) and especially Table 3 (p. 4, the feedback table) use about ten technical terms (MILP, guardrail, greedy, decision moment, candidate cap, postponement, constant M, re-planning interval, "reached") that are defined only in Sections 5 to 11.
2. **Symbols inside figures** (Figures 1, 9, 12) that never appear in the text: t_0, l (lag), lambda_r, tau, t_r, ETA, state names.
3. **A few symbol and word collisions:** M (postponement constant vs big-M), S (route subset S_vk vs service S), "booking" (Night Ride request vs Lyft order), "paired/pairing" (three meanings), r1/r2 (riders) vs R1 (rule code), and the status of 1.386 (OBSERVED in Table 4, DERIVED in Section 4.4).

None of these is fatal; most are fixed with a parenthetical gloss or a one-line caption addition. The highest-value fixes are items 1, 2, 3, 9, 10, 11 and 14 below.

## Term and symbol table

Page numbers are PDF pages. "Abs" = abstract. Status key: OK; used before defined (UBD); never defined (ND); defined twice (D2); ambiguous (AMB).

### Acronyms and short forms

| Term | First use (page, section, quote) | Where defined | Status |
|---|---|---|---|
| MILP | p1, Abs: "mixed-integer linear program (MILP)" | Abs only; body first use p1 Sec 2 "a rolling-horizon MILP" is never expanded | UBD (body never re-expands) |
| OR | not used | n/a | OK |
| OSRM | p2, Fig 1 box: "(local OSRM, hashed)"; text p3 Sec 3 "locally hosted OSRM routing server [9]" | never expanded (only "(OSRM.)" in ref 9) | ND |
| TransLoc | p1, Sec 1: "books through the TransLoc app" | role as vendor of the dispatch platform implied p6 ("its engine"), stated p14 Table 12 "vendor" | OK (minor: say "vendor" at first use) |
| JHU | p3, Sec 3: "JHU Transportation shared" | never expanded (title block spells out Johns Hopkins University) | ND (minor) |
| PWL, KPI, p90, D-numbers, L5, M0 to M5, CI, OR | not used in the report | n/a | OK |
| 90th percentile / "90th pct." | p1, Abs-adjacent Sec 1: "90th-percentile wait" | self-explanatory; "pct." abbreviation in Tables 4, 9, 11 not expanded | OK (minor) |
| SD | p12, Fig 13 caption: "mean +/- SD across 30 nights" | p13, Table 11 caption "standard deviation" | UBD |
| HiGHS | p7, Sec 5.1: "open-source HiGHS solver [8]" | at first use | OK |
| ETA / ETAs | p2, Fig 1: "routes, ETAs", "gives ETAs" | never | ND |
| van-km | p2, Fig 1: "Lyft counts, van-km"; Fig 8; Table 11 row | never (meaning implied) | ND (minor) |
| Lyft XL / "XL" | p4, Sec 4.4: "rides together in one Lyft XL"; Fig 6 label "XL" | never glossed | ND (minor) |
| AI | p11, Sec 7: "separate AI review agents" | common usage | OK |
| n | p10, Sec 5.2: "one run per formulation, n = 1"; p13 Fig 14: "(n)" = transfers | each locally defined, two meanings | AMB (minor) |

### Rule codes

| Term | First use | Where defined | Status |
|---|---|---|---|
| R0, R1(10), R1(15), R1u(10), R2(15), R3(2) | p8, Table 7 (floats into Sec 5, before Sec 6 on p10) | Table 7 itself is the key; all later uses (Fig 13 p12, Table 11 p13, Fig 15 p14, Table 13 p17) follow it | OK |
| Meaning of the parenthesised number and of "u" | p8, Table 7 | not stated (10 / 15 are thresholds in minutes, 2 is a margin in minutes; "u" = unassigned) | AMB (minor) |
| "assigned / unassigned" (R1u) | p8, Table 7: "continuously unassigned >= 10 min (resets when assigned)" | never tied to the model (presumably: not in any van's selected route, u_r = 1) | ND |
| "expected Lyft pickup", "typical Lyft delay" (R3) | p8, Table 7 | p11, Sec 6: "decision time + 2-minute ordering lag + 8-minute typical delay" | UBD |
| waiting-time rules / predictive rules | p4, Table 3: "Rules that read the plan's prediction" | p11, Sec 6 | OK (Table 3 wording is self-explanatory) |

### Evidence labels

| Term | First use | Where defined | Status |
|---|---|---|---|
| OBSERVED (label) | p1, Sec 1: "24.5% of all riders travelled by Lyft OBSERVED" | p3, Sec 3 bullet list | UBD |
| DERIVED, ASSUMED, DESIGNED | p3, Sec 3 ("multiplied by 1.2 ... ASSUMED" just before the list) | p3, Sec 3 list, same paragraph | OK |
| SIMULATED | p3, Sec 3: "Outputs of the simulator are labelled SIMULATED" | at first use | OK |
| "fitted" (status) | p6, Table 6: "ASSUMED + fitted" | not one of the five labels; never explained | AMB (minor) |
| Status of 1.386 passengers per completed request | p4, Table 4 (block labelled OBSERVED) | p4, Sec 4.4: "1.386 ... DERIVED"; Table 6 "mean DERIVED" | D2 (conflicting labels) |

### Mathematical symbols

| Symbol | First use | Where defined | Status |
|---|---|---|---|
| t_0 | p2, Fig 1: "Travel table t_0" | never | ND |
| rho_h | p5, Fig 3 legend and caption "5 rho_h" | p5 caption: "five vans times April's load per vehicle-hour" (h = hour implied) | OK |
| v, k, r (indices) | p7, Sec 5.1 | p7, "for each van v ... candidate routes k ... request r" | OK (sets of r not named: see below) |
| Set over which r runs in Eq (1) and Eq (2) | p7, Eq (1), Eq (2) | Eq (1) text: "each waiting request"; Eq (2) sum over r is over requests on route k (implied, not stated) | AMB |
| S_vk | p7, Sec 5.1: "every subset S_vk of at most K = 3 waiting requests" | at first use | OK, but letter reused (see S) |
| K | p7, Sec 5.1: "K = 3"; concept used earlier p4 Table 3 "candidate cap" | p7 | UBD (concept), OK (symbol) |
| y_vk, u_r | p7, Eq (1) | just before Eq (1) | OK |
| c_vk | p7, Eq (1) | p7 "route cost ... defined below", Eq (2) | OK |
| pi_r | p7, Eq (1) | p7 "postponement price", formula p9 | OK |
| q_r, W_r, H_r | p7, Eq (2) | directly after Eq (2) | OK, but W_r and H_r depend on the route (v,k) with no index | AMB |
| km_k | p7, Eq (2) | implied by "a kilometre is a small tie-breaker" | ND (minor) |
| (x)^+ | p7, Eq (2) | never (standard positive part) | ND (minor) |
| Psi | p7, Eq (2) | directly after Eq (2); repeated consistently p8, p17 | OK |
| G_r, T_r | p7, Eq (2) "G_r the ride guardrail (below)" | p8, Sec 5.1 "Time windows" | OK (forward pointer given) |
| phi (written varphi) | p7, Eq (2) | p7 to p8, "Waiting is convex" paragraph; Fig 11 | OK |
| "points", "base slope" | p7, "One point is one passenger-minute of waiting at the base slope" | base slope = 1 point/min, given one paragraph later | OK (minor ordering) |
| b_r | p9, Sec 5.1 "Postponement price" | at first use (refers forward to Sec 5.2 for the adopted rule) | OK |
| W_r^early | p9 | at first use | OK |
| M | p4, Table 3: "the postponement constant M" | p9 Sec 5.1 (role); p17 App B (formula) | UBD (glossed in Table 3), and reused, see next row |
| big-M | p13, Sec 9: "big-M precedence and time constraints" | standard term, different meaning from the report's M | D2 / AMB (symbol reuse) |
| b_r^max, j | p17, App B | at first use | OK |
| S, B | p12, Sec 8.3: "service S ... Lyft use B" | at first use; S already means the route subset S_vk; neither letter is used again | AMB (symbol reuse, unused) |
| l (ell, ordering lag) | p9, Fig 9: "after lag l"; p12 Fig 12 "tau + l" | never (text says "2-minute ordering lag") | ND |
| lambda_r | p9, Fig 9: "after lambda_r"; p12 Fig 12 "Lyft delay lambda_r" | never | ND |
| tau, t_r | p12, Fig 12: "request at t_r", "decision tau" | never | ND |
| r1, r2 (riders) | p10, Fig 10: "Route A: r1 first", "pick r2" | text says "rider 1" and "a party of two"; r2 never named | AMB (also clashes visually with rule code R1) |
| r00 | p6, Fig 5: "night r00" | never (night identifier) | ND (minor) |
| theta / thresholds | no theta used; thresholds are numbers in rule codes | Table 7 | OK |

### Technical terms

| Term | First use | Where defined | Status |
|---|---|---|---|
| curb arrival | p1, Sec 1 | p1, at first use | OK |
| cancellation | p1, Sec 1 | p1, at first use | OK |
| no-show | p1, Sec 1 | p1, at first use ("absent after a 3-minute curb wait") | OK |
| "reached within 15 minutes" | p1, Abs: "reached about three quarters of requests within 15 minutes"; body p4 Table 3 "reached more requests in 15 min" | p11, Sec 8.1: share of all 28 requests reached by a vehicle (curb arrival, not boarding) | UBD (abstract and Table 3) |
| postponement / postpone | p4, Table 3: "makes the solver postpone as few requests" | p7, Sec 5.1: "u_r = 1 if request r is postponed to a later decision moment" | UBD |
| postponement price ("pending price") | p7, Sec 5.1 | p7 and p9 | OK |
| candidate route / candidate set | p1, Abs; body p4 Table 3 "restricted candidate set", "candidate cap"; p6 decision cycle "feasible candidate routes are generated" | p7, Sec 5.1 | UBD |
| rolling horizon | p1, Abs; body p1 Sec 1 contributions "rolling-horizon MILP dispatcher" | partly p4 Table 3 ("all known work with no look-ahead"), mechanism p6 decision cycle, but the name is never attached to the mechanism | UBD / never explicitly defined |
| decision moment | p4, Table 3: "optimal over its candidates at each decision moment" | p6, Sec 5 decision cycle | UBD |
| re-planning interval | p4, Table 3 | p6 implicitly ("every 2 minutes") | UBD (minor) |
| greedy (rules / assignment / insertion) | p1, Sec 2: "compare greedy rules"; p2 "greedy assignment"; p4 Table 3 "greedy insertion" | p14, Sec 11 item 6: "insert each new request at its cheapest position on arrival; never reassign" | UBD; three different phrasings |
| Dial-a-Ride Problem | p4, Table 3 | p6, Sec 5 "The problem class" | UBD (Table 3 points to Sec 5; acceptable) |
| guardrail (ride-time) | p2, Table 1: "plus a ride-time guardrail" | p8, Sec 5.1 "Time windows" (G_r formula) | UBD (minor; term self-suggestive) |
| published targets / reporting thresholds | p2, Table 1 | p8, Sec 5.1 | UBD (minor) |
| "busy-time arrival" | p8, Sec 5.1 | never | ND (minor) |
| eligible (for transfer) | p6, Sec 5: "whether an eligible request moves to Lyft" | p10 to p11, Sec 6 | UBD |
| commit / committed | p6, Sec 5 decision cycle | at first use | OK |
| ordering lag | p6, Table 6 "Ordering lag 2 min (pilot)" | p6, decision cycle step (5) same page | OK |
| Lyft acceptance / declined offer | p6, Table 6 "Lyft acceptance: Always (pilot)" | p11 Sec 6 ("never declined a Lyft offer") and Sec 7 ("every Lyft offer accepted") | AMB (acceptance by rider or by Lyft is not said at first use) |
| "lyft_failed (sensitivity)" | p9, Fig 9 | caption: "dashed box is used only in a sensitivity case" (case not described) | ND (minor) |
| booking | p7, Fig 6 caption: "a 'booking' here is one Night Ride request"; same figure, right panel "minutes, booking to Lyft arrival" | Fig 6 caption; elsewhere (Fig 1, Fig 9 "lyft_booked", Fig 14 "after the Lyft was booked") booking = Lyft order | D2 (two meanings, one inside the same figure) |
| paired / pairing | p4, Table 3: "paired pickups and drop-offs"; p3 to p4 Sec 4.3 "The pairing is therefore not identified" (origin-destination matching); p11 Sec 7 "paired scenarios" | each meaning is locally clear | AMB (three meanings) |
| paired nights / paired replay | p11, Sec 7 | p11, at first use | OK |
| common random numbers | p3, Sec 4 | at first use | OK |
| burst | p3, Sec 4.2 | at first use (18:20 to 18:30, 11 requests) | OK |
| largest-remainder rule | p3, Sec 4.1 | p5, Fig 3 caption explains by example | OK (minor) |
| dominance / nondominated | p12, Sec 8.3 | p12, at first use | OK |
| verification vs validation | p1, Abs and Sec 1 contributions "A verified event simulator" | p11, Sec 7 | UBD (the word is plain English, but the report uses it as a technical term) |
| non-inferiority margins / margins / noise margin | p12, Sec 8.3 "No noise margin is applied yet"; p13 "the margins"; p14 Sec 11 item 3 "non-inferiority margins" | never | ND |
| matched-budget baseline | p14, Sec 11 item 4 | at first use | OK |
| hindsight benchmark, node-arc | p13, Sec 9 | not defined (standard OR terms) | OK for this reader (minor) |
| dwell | p10, Fig 10 / Table 8: "dwell omitted" | never | ND (minor) |
| van plan / predicted pickup / predicted total wait | p1, Abs "van plan's predicted pickup" | p8, Table 7 caption | OK |
| "reads the board" | p2, Fig 1 | never | ND (minor) |

## Problems and suggested fixes

1. **MILP not re-expanded in the body.** First body use p1, Sec 2 ("a rolling-horizon MILP"). Fix: in Sec 1 Contributions (iii) write "a rolling-horizon mixed-integer linear programming (MILP) dispatcher".

2. **Evidence label OBSERVED used before its key.** p1, Sec 1 "24.5% of all riders travelled by Lyft OBSERVED"; key is p3, Sec 3. Fix: after the label in Sec 1 add "(evidence labels such as OBSERVED are explained in Section 3)", or drop the label in Sec 1 and write "read directly from the April dashboards".

3. **Table 3 (p4) and Table 1 (p2) use terms defined only in Sections 5 to 11.** Affected: decision moment, candidate set / candidate cap, postponement and constant M, re-planning interval, greedy insertion, guardrail, "reached ... in 15 min", published targets. Fix (one sentence in Sec 2, before the Table 3 reference): "Terms used in Table 3 are defined later: the dispatcher re-plans at decision moments (Section 5), choosing among a capped set of candidate routes; requests it does not assign are postponed at a price; greedy insertion places each new request at its cheapest position on arrival and never reassigns (Section 11)." Alternatively add a short glossary footnote to the Table 3 caption.

4. **"Greedy" used three ways before it is defined.** p1 "greedy rules", p2 "greedy assignment", p4 "greedy insertion"; defined only p14, Sec 11 item 6. Fix: use "greedy insertion" everywhere and define it at first use in Sec 2: "greedy insertion (each new request is inserted at its cheapest position in a van's route on arrival and never reassigned)".

5. **"Rolling horizon" never explicitly defined.** Abstract and p1 use it; the mechanism is described p6 without the name. Fix: at the end of the p6 decision-cycle paragraph add "This is what we mean by rolling horizon: the plan is re-optimized at every decision moment over all known requests, with no forecast of future requests, and only its first move is executed." Also give a one-clause gloss at first body use (p1).

6. **"Candidate route" used before defined in the body.** p4 Table 3 and p6 decision cycle; defined p7, Sec 5.1. Fix: in the p6 decision cycle step (2), write "a small set of feasible candidate routes (defined in Section 5.1) is generated for each van".

7. **"Eligible" used before defined.** p6, Sec 5 "whether an eligible request moves to Lyft"; defined p10 to p11, Sec 6. Fix: "decides whether an eligible request (one still waiting for a van, not yet committed, and never having declined Lyft; Section 6) moves to Lyft".

8. **"Reached within 15 minutes" undefined in the abstract and used early in Table 3.** Defined p11, Sec 8.1. Fix in abstract: "reached about three quarters of requests within 15 minutes (a van or Lyft at the curb within 15 minutes of the request; cancelled requests count as not reached)". Same parenthesis, or a pointer "(defined in Section 8.1)", in Table 3.

9. **Symbol M used for two things.** p4/p9/p17: postponement constant M. p13, Sec 9: "big-M precedence and time constraints" (standard big-M of the node-arc model). Fix: in Sec 9 write "large-constant (big-M) precedence and time constraints, unrelated to our postponement constant M", or rename the postponement constant (for example to Gamma) throughout.

10. **Symbol S used for two things.** S_vk is the route's request subset (p7); "service S" is introduced p12, Sec 8.3 and never used again (same for B). Fix: delete the letters: "We keep two objectives separate: service (share reached within 15 minutes, higher is better) and Lyft use (orders per night, lower is better)."

11. **Figure-only symbols never defined: l, lambda_r, tau, t_r (Fig 9 p9, Fig 12 p12) and t_0 (Fig 1 p2).** Fix: add to the Fig 12 caption "t_r: request time; tau: transfer decision time; l: ordering lag (2 min in the pilot); lambda_r: the rider's hidden Lyft delay (lognormal, median 8 min)." Add to Fig 9 caption "l is the ordering lag and lambda_r the rider's hidden Lyft delay (Figure 12)." Since Fig 9 comes before Fig 12, put the definitions in Fig 9 and have Fig 12 refer back. For Fig 1, either remove "t_0" and "hashed" from the box or add to the caption "t_0 is the fixed table of travel times between all 188 places (OSRM x 1.2); 'hashed' means its content is fingerprinted so every run uses the same table."

12. **"Booking" means two different things, inside the same figure.** Fig 6 (p7) caption says a booking is one Night Ride request (left panel), but the right panel axis "booking to Lyft arrival" means the Lyft order; Fig 1, Fig 9 ("lyft_booked") and Fig 14 ("after the Lyft was booked") also use booking = Lyft order. Fix: in Fig 6 relabel the left axis "share of requests" and "riders in the request", drop the "booking" sentence from the caption, and in the right panel and caption write "Lyft delay from the Lyft order to its arrival". Then "booking" consistently means a Lyft order, which matches "Lyft orders" in Table 11; better still, replace "booking/booked" with "order/ordered" everywhere.

13. **ETA never defined (Fig 1, p2).** Fix: replace "ETAs" with "predicted pickup times" in the figure, or add to the caption "ETA: estimated (predicted) time of arrival at the curb".

14. **Status of 1.386 passengers per completed request labelled two ways.** Table 4 (p4) puts it in the OBSERVED block; Sec 4.4 (p4) and Table 6 (p6) call it DERIVED. Fix: decide which is right (if it is computed as passengers / completed van requests, it is DERIVED) and move the row into Table 4's DERIVED block, or change Sec 4.4 to OBSERVED if the dashboard prints 1.386 directly.

15. **SD used before expansion.** Fig 13 caption (p12) "mean +/- SD"; "standard deviation" first spelled out in Table 11 (p13). Fix: Fig 13 caption "mean +/- standard deviation (SD) across 30 nights".

16. **OSRM never expanded.** First use Fig 1 (p2) and Sec 3 (p3). Fix in Sec 3: "a locally hosted Open Source Routing Machine (OSRM) server [9]".

17. **Rule R1u(10): "assigned/unassigned" is not tied to the model, and code notation is not explained.** Table 7 (p8). Fix: add to the Table 7 caption "A request is unassigned at a decision moment if no selected van route contains it (u_r = 1 in Eq. (1)). The number in a code is the rule's threshold in minutes; for R3 it is the margin by which the van must be later than Lyft." Note: Table 7 floats ahead of Eq. (1); if so, say "it was postponed by the dispatcher (Section 5.1)".

18. **R3(2) row uses "expected Lyft pickup" and "typical Lyft delay" before Sec 6 defines them.** Table 7 (p8) vs p11. Fix: in the Table 7 caption add "Expected Lyft pickup = decision time + 2-minute ordering lag + 8-minute median Lyft delay."

19. **Index set and route dependence in Eq. (1) and Eq. (2) are implicit.** Eq. (1) sums over r without naming the set; in Eq. (2) the sums over r run over requests on route k, and W_r, H_r depend on the route but carry no (v,k) index. Fix: after Eq. (1): "Here R is the set of waiting (unassigned, uncommitted) requests and r ranges over R." After Eq. (2): "sums run over the requests served by route k (new and committed); W_r and H_r are the wait and ride time that route k would give request r. km_k is the route's driving distance in km, and (x)^+ = max(x, 0)."

20. **Riders r1, r2 in Fig 10 (p10) are not named in the text and look like rule code R1.** Fix: relabel the figure "rider 1" and "pair" (or "P"), matching the text "rider 1 ... a party of two", and Table 8 "A: rider 1 first / B: pair first".

21. **"Paired/pairing" carries three meanings.** p4 Table 3 and p6 "paired pickups and drop-offs" (DARP precedence), p3 to p4 Sec 4.3 "pairing" of origins with destinations, p11 Sec 7 "paired scenarios" (same night under every rule). Fix: keep "paired" only for the experimental design; write "each pickup matched to its drop-off" in Table 3 and Sec 5, and "origin-destination matching" in Sec 4.3 and the Table 6 row "Trip pairing".

22. **Verification used before it is defined.** Abstract and p1 contributions ("verified simulation results", "A verified event simulator"); defined p11, Sec 7. Fix in Sec 1 (iii): "A verified event simulator (checked against hand-computed cases that the code implements the specified model; Section 7)". The abstract can stay as is if the body defines it at first body use.

23. **Margins never defined.** p12 "No noise margin is applied yet", p13 "the margins", p14 "non-inferiority margins". Fix at p12: "No noise margin (a minimum difference below which two rules are treated as tied) is applied yet". At p14: "non-inferiority margins (the largest loss in service we would accept in exchange for less Lyft use)".

24. **Route-based postponement price never described.** Table 9 (p11) column "Route-based, priced as served at: after a route" with "up to 9,828" extra variables; Sec 5.2 text names only the first and the adopted formulations. Fix: add after "We provisionally adopted the second" a sentence such as "The third prices postponement as if the request were served after the van finishes a route, which needs extra variables (up to 9,828 here)." Adjust to what the code actually does.

25. **Lyft acceptance ambiguous at first use.** Table 6 (p6) "Lyft acceptance: Always (pilot)". Fix: "Rider accepts Lyft offer: always (pilot)", matching Sec 6 "never declined a Lyft offer".

26. **Minor undefined terms (one-phrase glosses suffice).**
    - JHU (p3): "Johns Hopkins University (JHU) Transportation".
    - Lyft XL (p4): "one Lyft XL (a larger Lyft vehicle seating up to six)".
    - van-km (Fig 1, Fig 8, Table 11): "Van-km (kilometres driven by vans)" in Table 11.
    - dwell (Fig 10 and Table 8): "dwell (time stopped at the curb for boarding) omitted".
    - busy-time arrival (p8): add "(the target for busy periods)", or quote the page's own wording.
    - night r00 (Fig 5): "(night r00, the first of the 30)".
    - "fitted" in Table 6: replace with "ASSUMED + DERIVED (fitted to map totals)", or add "fitted" to the label list.
    - lyft_failed "sensitivity case" (Fig 9): "used only in a sensitivity case where a Lyft order can fail".
    - "reads the board" (Fig 1): "reads open requests and predicted pickups".
    - "pct." in Tables 4, 9 and 11: write "percentile".
    - n (p10 runs vs Fig 14 transfers): both are defined locally; consider "one run each" at p10 and keep n for Fig 14.

## Resolution (main session, 3 Nov 2026)

- **Applied in text:** 1, 2, 3 (Table 3 caption points to where each term is defined), 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 21 (pairing now "matching" outside the experimental design), 22, 23, 24, 25, 26 (JHU, Lyft XL, van-km, dwell, busy-time arrival, night r00, "fitted", lyft_failed, "reads the board", "percentile").
- **Applied through captions, figures not redrawn:** 11, 12 and 20. Figures 1, 6, 9, 10 and 12 are shared with the methodology PDF, so their symbols (t_0, ETA, l, lambda_r, tau, t_r, r1, r2, "booking") are now defined in the report's captions instead.
- **Held:** 26, the reuse of n (each use is defined where it appears).
