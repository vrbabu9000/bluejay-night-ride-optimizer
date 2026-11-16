# Referee report: "Optimizing the Night Ride: Mid-Semester Update"

Reviewer stance: Prof. A. J. Kearsley (EN.553.402/602), read as an ORSA/TIMS referee. Report read page by page from the compiled PDF (16 pp.), checked against the .tex source, the deck text, `numbers.json` and `outputs/sim/batch_L5_v1/per_night_metrics.csv` (180 rows recomputed with pandas).

## Overall verdict

A well organized, unusually honest midterm. The story holds together: data did not arrive, the team says so, builds labelled synthetic evenings, and narrows to one decision. The MILP is stated correctly, the "exact" language is now right, and every simulated number I recomputed matches the files.
Three things keep it from the top band. First, the headline result (predictive rules reach about 3/4 within 15 min) is close to mechanical: those rules transfer at a median of 0 s, and an assumed 2 + 8 min Lyft arrives inside 15 min almost by construction; without an equal-Lyft-budget baseline, "prediction helps" is not shown.
Second, you have 30 paired nights and still report no paired intervals; that is a few lines of code, not future work.
Third, my main question, MILP versus greedy, is honestly deferred, but Table 3 grades my question (a) as "Partly" when nothing here tests optimization at all.
The ICML proceedings footer must go. Provisional grade against the syllabus criteria: A-minus, contingent on the intervals and the equal-budget comparison appearing in the final.

## Syllabus coverage

| Requirement | Section | Adequate? | Note |
|---|---|---|---|
| Work completed to date | Abstract; Sec. 1 "Contributions to date" | Yes | Clear list with forward references. |
| Data acquisition and preprocessing | Sec. 3; Table 4; Sec. 4.1-4.6 | Yes | Strong; the OBSERVED / DERIVED / ASSUMED / DESIGNED labelling is the best part. One wrong sentence on map totals (p. 3). |
| Methods implemented or investigated | Sec. 4-6; eq. (1)-(2); Tables 6, 9 | Yes | MILP, cost, time windows and rules all stated. Symbols used before definition (pi_r, Psi, b_r^max). |
| Preliminary results | Sec. 8; Tables 11, 13; Figs. 13-15 | Partly | Numbers correct, but no paired uncertainty and no baseline isolating the effect of prediction. Graduate depth expected here. |
| Problems or obstacles | Sec. 2, 5.2, 9 | Yes | Missing extracts, misread dashboard numbers, postponement-price flaw. |
| Unsuccessful approaches and lessons | Sec. 9 | Yes | Five items each with a stated lesson. Node-arc argument slightly imprecise (p. 11). |
| Changes to the original plan | Sec. 2; Tables 1-3 | Yes | Clear and candid; scope choice stated as a choice. |
| Concrete plan for the final | Sec. 11; Fig. 16; Timeline | Mostly | Ordered and sensible. Missing: statistical design of the benchmark, held-out nights for threshold search, compute estimate for five-van runs. |
| Explicit assumptions and limitations | Sec. 10; Table 12 | Thin | Sec. 10 is four sentences. Lyft cost, Lyft always available and accepting, burst-only demand and load-independent Lyft delay are not listed. |
| Clear about what was and was not accomplished | Throughout; Fig. 16 "all planned, not yet run" | Yes | Exemplary, apart from Table 3 row (a). |

## Proposal feedback

| Point | Answered? | Note |
|---|---|---|
| (a) Can optimization reduce waits and Lyft overflow? | Not yet, labelled "Partly" | Table 3 says "Partly", but the study varies a transfer rule with the optimizer fixed; nothing tests optimization against anything. Relabel "Reframed; not yet tested" and point to Sec. 11 item 5. |
| (b) When does rolling-horizon MILP beat greedy; dependence on fleet, demand, horizon? | Open, honestly | Sec. 11 item 5 names fleet (5 vs 6), demand pattern and re-plan interval, and correctly notes there is no look-ahead horizon. Good. Still needs a paired statistical design and a wider fleet range. |
| (c) Does the Dial-a-Ride aspect make optimization valuable? | Overstated | "April suggests yes: pooling is common at 6 pm" (Table 3). No pooling statistic appears in the report; 1.386 is party size, not shared trips. The ride-time tail is also explained in your own simulator by no-show waits. Say "plausible, untested". |
| (d) Lexicographic vs weighted; Lyft-first risk | Yes | Weighted sum, Lyft removed from the van objective, service and Lyft reported as two objectives (Sec. 5.1, 8.3). Honest that M keeps one near-lexicographic layer on van service. Well done. |
| (e) Make the DARP clear | Yes | Sec. 5 "The problem class": dynamic, door-to-door, paired pickup and drop-off, capacity, ride-time limits. |
| (f) Clarify time windows | Yes, one gap | Soft wait priced by phi, ride guardrail G_r, published targets as reporting thresholds (p. 8). The "20 / 25 / 25 minutes" are not explained. |
| (g) Careful with "exact" | Yes | Abstract and p. 8 use my wording; "optimal over its candidates, subject to solver status". Good. |

## Page-by-page findings

### Page 1
- **[major]** Footer, p. 1: "Proceedings of the 43rd International Conference on Machine Learning, Seoul, South Korea. PMLR 306, 2026. Copyright 2026 by the author(s)." - This is a course report, not an ICML paper; the footer states a false venue. - Remove it (compile the ICML style without `accepted`, or override `\printAffiliationsAndNotice`), and put "EN.553.402/602 midterm report, Fall 2026" instead.
- **[minor]** Sec. 1, "The question": "the 90th-percentile wait for completed rides is about 17 to 21 minutes" - A range for one percentile is unexplained (by hour? by digitization uncertainty?). - Say what the range spans, e.g. "17 to 21 minutes across the 6, 7 and 8 pm hours".
- **[nit]** Sec. 1, "The service": "shared 14-seat vans" is stated as fact, while Table 6 labels 14 seats DESIGNED. - Add "(modelled as 14 seats)" or the label.

### Page 2
- **[nit]** Fig. 1: the "booking" label collides with the arrow to Lyft service, and "Travel table t_0" uses a symbol never defined. - Move the label; drop t_0 or define it.
- Otherwise no issues: Sec. 2 and Tables 1-2 are clear and the scope change is stated as a choice.

### Page 3
- **[minor]** Sec. 3, Preprocessing: "The city maps sum to 24,056 origins and 24,057 destinations, matching completed rides to within one" - Completed rides are 24,095 (Table 4); the maps fall 39 short. Origins and destinations match each other within one. - Write "origins and destinations agree to within one; both are 39 below the 24,095 completed rides" and say where the 39 went.
- **[minor]** Sec. 3, "The ride-time tail comes from routing" - Causal claim from two aggregates. Your own Table 10 attributes all 36 guardrail excesses to no-show waits, another non-routing source of long rides. - "is consistent with detours for shared riders".
- **[minor]** Sec. 3: "The service is supply-limited: completions do not rise with requests" - No number or figure supports it. - Give the daily correlation or slope, or drop it.
- **[minor]** Sec. 4.1 and Fig. 2: workload chain. Unrounded: 5,089/30 = 169.63; 50,297/24,095 = 2.0874; product 354.1; /27.6 = 12.83, not 12.85. Same for 19:00 (10.09, not 10.10) and 20:00 (10.70, not 10.71). Fig. 2's own "355 / 27.6" is 12.86. The integer result 64/50/54 is unchanged. - Carry unrounded values or state that 12.85 uses rounded intermediates (170 x 2.087).
- **[nit]** Sec. 3: "agreed on 214 of 215" - Say how the one disagreement was resolved.
- **[nit]** Sec. 3: "correlation 0.88" - State n (30 days) and that the daily series is not in Table 4.

### Page 4
- **[major]** Table 3, row (a), Status "Partly" - Overclaims progress on my question; the evidence cited is a transfer-rule comparison with the optimizer held fixed. - Status "Reframed; not yet tested", note pointing to Sec. 11 item 5.
- **[minor]** Table 3, row (c): "April suggests yes: pooling is common at 6 pm" - No pooling measure (requests per van trip, share of shared rides) appears anywhere in the report. - Report the statistic or write "plausible, untested".
- **[minor]** Sec. 4.3: IPF matched "both April location totals ... to within 10^-10" - The two totals differ by one (24,056 vs 24,057), so exact simultaneous matching is impossible unless normalized. - State that rows and columns were normalized to shares (or to a common total) before fitting.
- **[minor]** Sec. 4.4: "mean 1.405, over all requests, so it need not equal 1.386" - No reason is given why non-completed requests should have larger parties. - One sentence of justification, or a sensitivity to a 1.386-mean mix.

### Page 5
- **[minor]** Sec. 4.5 with Table 11: the 50-75% give-up range is never compared with the simulator. Under Vans only, every cancellation is a give-up: 10.8/28 = 38.6% of requests, above the April-implied 0.474 x (50-75%) = 23.7-35.5%. - Report this; it may be the intended burst stress, but say so. It is the most direct check you have on the placeholder patience.
- **[nit]** Fig. 3 caption labels the 64/50/54 result DERIVED, while p. 3 calls the workload DERIVED + ASSUMED. - Use DERIVED + ASSUMED.
- **[nit]** Fig. 3: largest-remainder rounding needs a target total. - State "total rounded to 168 = round(168.3), one leftover unit".

### Page 6
- **[minor]** Eq. (1) uses pi_r before it is defined (definition is on p. 8, "Postponement price"). - Add "pi_r, the postponement price defined below" under eq. (1).
- **[minor]** Table 6 vs deck slide 13 / B4: Arrival times DESIGNED (report) vs DERIVED + ASSUMED (deck); Party sizes DERIVED + ASSUMED (report) vs "ASSUMED (mean derived)" (deck B4). - Make the labels identical in both.
- **[minor]** "(2017; reference 4)": reference 4 is the only bibliography entry cited in the text; references 1-3 and 5-12 are never cited (HiGHS, OSRM, TransLoc 2016, bilevel all appear in the text without citation). - Cite each where used, one citation style throughout.
- **[nit]** Fig. 5: labels are around 5 pt at print size and there is no scale. - Enlarge labels; add a 1 km bar.

### Page 7
- **[minor]** Eq. (2), "Route cost, in passenger-minutes" - phi returns points, not passenger-minutes, and 0.1 km_k is points per km. Psi enters eq. (2) with no value in the main text (1000 is only in App. B, which the text never references). - "in points (one point = one passenger-minute of waiting at the base slope)"; give Psi = 1000 here or cite App. B.
- **[minor]** "booking" has two meanings: a Night Ride request (Fig. 6, "share of bookings"; deck slide 2) and a Lyft order (Fig. 9 "lyft_booked", Fig. 12 "booking tau + l", Fig. 15 axis). - Use "request" for Night Ride and "Lyft order" for Lyft everywhere.
- Mathematics checked: phi(5)=5, phi(10)=17.5, phi(15)=42.5, phi(20)=92.5 (Fig. 10 labels correct); the TransLoc comparison phi(10)-phi(9)=2.5 > phi(5)-phi(3)=2 is correct; "linear whatever its shape" is correct because phi is evaluated during enumeration.

### Page 8
- **[minor]** Worked example: discussed on p. 8, Fig. 11 printed on p. 11, three pages later. - Place Fig. 11 next to Table 7.
- **[minor]** Time windows: "20 / 25 / 25 minutes on the live page read in October" - What are the three numbers? - Name them (e.g. pickup / ride / something).
- **[minor]** "b_r estimates the waiting cost of serving r later" - Not a definition; App. B then uses an undefined b_r^max. - Write b_r = q_r phi(W_r at earliest physically possible pickup) (the adopted rule of Sec. 5.2) and define b_r^max.
- **[nit]** Table 7 says "rider 1 / pair", Fig. 11 says "r1 / r2". - One naming. Arithmetic verified: A = 52.5 + 13.0 + 1.0 = 66.5; B = 67.5 + 12.5 + 1.0 = 81.0; timings in Fig. 11 reproduce the waits and rides.
- **[nit]** Sec. 5.2: show where 262.5 and 435.8 come from (5 x phi(16) and 5 x phi(19.47)); both verified.

### Page 9
- **[minor]** "Lyft arrives sooner" example: the Lyft reaches the curb at exactly the expected 18:27:00. The deck says the delay was fixed at 8 min on this designed evening; the report does not, so the reader thinks it is a coincidence. - Add "the Lyft delay is fixed at 8 min on this designed evening".
- **[minor]** Postponement price adopted on one designed evening, one run (Table 8); median wait rose 17.1 to 18.6. - Say "n = 1" in the text and add re-checking on the 30 nights to the plan.
- **[nit]** "has never declined a Lyft offer": offers and acceptance probability are not introduced in the text (only "Always (pilot)" in Table 6). - One clause.

### Page 10
- **[major]** Sec. 8.1, headline result. The predictive rules transfer at a median of 0 s waited (verified from `outcomes.csv`: R2 and R3 medians 0 s, R1(10) 629 s, R1(15) 932.5 s). With a 2-min lag and an assumed lognormal delay of median 8 min, a request transferred at time 0 reaches the curb inside 15 min almost by construction. So "reached within 15 min" largely measures "transferred early, under our Lyft-delay assumption". Your caveats name both pieces but do not draw the conclusion. - Add a baseline at matched Lyft budget: e.g. transfer on arrival the first B requests, or a random set of B, with B = 9.3 or 10.5 per night. Only the gap between R2/R3 and that baseline is the value of prediction. Rerun Fig. 13 with Lyft delay median 12 min (already in your plan) before the final.
- **[major]** Sec. 8 and Table 11: "no confidence intervals yet" (Sec. 10) - With 30 paired nights this is immediate. My paired 95% t-intervals (difference in share reached, then in Lyft orders per night): R1(10) - R0: +0.037 +/- 0.022, +5.93 +/- 0.61; R1(15) - R0: +0.018 +/- 0.017; R2(15) - R0: +0.257 +/- 0.031, +9.33 +/- 0.94; R3(2) - R2(15): +0.015 +/- 0.023 in reach, +1.13 +/- 0.66 in Lyft orders. So R2 and R3 are not distinguishable on service, but R3 uses more Lyft. That is a result worth stating. - Add paired intervals to Table 11 or Table 13 now.
- **[nit]** Fig. 10: slope labels along the axis are too small to read in print. - Enlarge.
- **[nit]** "932 s": the computed median is 932.5 s. - "about 930 s" or "15.5 min".

### Page 11
- **[minor]** Sec. 9, node-arc MILP: "every non-linear waiting penalty would need extra modelling inside it" - A convex piecewise-linear penalty is LP-representable with one epigraph variable per request and five inequalities; no integers needed. The real cost is the time-indexed wait variables and big-M precedence constraints. - Reword so the reason is model size and solve time, not convexity.
- **[minor]** Fig. 15 x-axis "Lyft bookings per night" vs text "Lyft use B (orders per night)"; the caption has to patch it. - Relabel the axis "Lyft orders per night".
- Sec. 8.3 dominance definition is correct (weak Pareto among the six tested points); the four "nondominated" rules were verified on the means, and R1u(10) is dominated only by R0, by exactly one request in 840 (verified).

### Page 12
- **[minor]** Table 9 (the rule definitions and codes R0..R3(2)) appears on p. 12, but the rules are used from p. 9 and the codes in Table 11 and Fig. 13. - Put Table 9 at the start of Sec. 6.
- **[minor]** Sec. 10 is four sentences plus Table 12. Missing: Lyft cost not modelled; Lyft always available and every offer accepted; Lyft delay independent of load and hour; burst-only demand; one set of 30 nights; the 8.9% presence draw reused for Lyft arrivals. - Add them to Table 12 or a list.
- **[nit]** Fig. 12: "board 30 s" is the only mention of dwell time. - State dwell in Table 6.
- **[nit]** "the 15-minute measure favours early transfer" appears in Sec. 8.1 and again in Sec. 10. - Keep once, cross-reference.

### Page 13
- **[minor]** Table 11 does not reconcile to 28 requests: there is no no-show row and no transfer row (R0: 16.1 van completed + 10.8 cancelled = 26.9; R1(10): 196 transfers in Fig. 14 vs 5.9 x 30 = 178 orders in Table 11, the gap being lag cancellations). - Add rows for van no-shows, Lyft no-shows and transfers, and state the identity.
- **[minor]** Sec. 11 item 4, threshold search "for the sample average over our nights" - Tuning and reporting on the same 30 nights overfits. - Tune on one set of nights, report on fresh seeds.
- **[minor]** Sec. 11 item 5, benchmark: no statistical design (number of nights, paired differences, primary metric) and the fleet range 5 vs 6 is narrow for "does the gap depend on fleet size". No compute estimate for five-van, 168-request runs (two-van runs already average 32 s, max 253 s). - Specify the design, widen the fleet range (e.g. 3-7) or vary load per van, and estimate run time before committing to mid-November.

### Page 14
- **[minor]** Sec. 12: "transfer rules that read the van plan's predicted pickup improved timely curb arrival" - Attributes the effect to reading the prediction, which Sec. 8.1 says is not isolated. - "transfer rules that moved requests early, guided by the plan's prediction, improved ... while using more Lyft".
- **[nit]** Fig. 15 caption has an unbalanced quotation mark: `“bookings on the axis are Lyft orders.` - Close it, or remove the sentence once the axis is relabelled.
- **[nit]** Fig. 14: the no-show and narrow lag segments carry no counts. - Label or list them in the caption.
- **[nit]** Fig. 15 has no error bars while the text reasons about dominance. - Add +/- 1 SD or paired-interval whiskers.

### Page 15
- **[nit]** Fig. 16 sits two pages after Sec. 11, which it illustrates. - Move it into Sec. 11.
- AI-use disclosure is adequate and specific. No other issues.

### Page 16
- **[minor]** App. B: the bound on M is correct (postponing j more requests costs at least jM minus at most the route-cost range and b terms, so at least j >= 1 if b_r >= 0). But (i) b_r^max is undefined, (ii) the "1 +" and "absolute gap below one cost unit" only guarantee the ordering if costs are integer-scaled, which the deck (B2: "exact integers") states and the report does not, (iii) the deck writes sum_r b_r, the report sum_r b_r^max, and (iv) App. B is never referenced from Sec. 5. - Define b_r^max, state the integer scaling and b_r >= 0, align with the deck, and cite App. B from p. 8.
- **[nit]** App. C is never referenced from the main text. - Cite it in Sec. 5 "The decision cycle".

## Number checks

All recomputed from `per_night_metrics.csv` (30 nights x 6 rules) or from the April totals, unless stated.

| # | Quantity (location) | Report | Recomputed | Verdict |
|---|---|---|---|---|
| 1 | Reached within 15 min, means (Table 11, 13) | 0.477 / 0.514 / 0.495 / 0.476 / 0.735 / 0.750 | same | OK |
| 2 | Reached SD (Table 11) | 0.09 / 0.08 / 0.09 / 0.10 / 0.07 / 0.08 | 0.09 / 0.08 / 0.09 / 0.10 / 0.07 / 0.08 | OK |
| 3 | Requests picked up (Sec. 8.1) | 16.1 to 20.2-20.4 | 16.10; 20.20; 20.37 | OK |
| 4 | Wait P90, picked up (Table 11) | 20.2 / 18.1 / 19.6 / 20.2 / 13.3 / 12.2 | 20.23 / 18.13 / 19.56 / 20.20 / 13.28 / 12.23 | OK |
| 5 | Wait P90 per passenger | 20.1 / 17.4 / 19.2 / 19.6 / 13.2 / 12.7 | 20.13 / 17.37 / 19.24 / 19.56 / 13.24 / 12.70 | OK |
| 6 | Lyft orders per night | 0 / 5.93 / 3.10 / 0.23 / 9.33 / 10.47 | same (standard + XL bookings) | OK |
| 7 | Van-km | 51.2 / 47.6 / 48.6 / 51.9 / 45.7 / 43.0 | 51.19 / 47.59 / 48.59 / 51.88 / 45.66 / 42.98 | OK |
| 8 | Van completed, Lyft completed, cancelled waiting, cancelled after transfer | Table 11 rows | all match to 0.1 | OK |
| 9 | Transfers (Fig. 14 n) | 196 / 104 / 8 / 294 / 330 | same | OK |
| 10 | R1(10) fates | 94 completed, 18 lag + 77 after = 95 cancelled | 94 completed, 7 no-show, 95 cancelled after transfer | OK |
| 11 | "About a third" cancelled, predictive rules | about 1/3 | R2 93/294 = 31.6%; R3 104/330 = 31.5% | OK |
| 12 | Median time waited at transfer (Sec. 8.1) | 0 s / 629 s / 932 s | 0 / 0 / 629 / 932.5 (from outcomes.csv) | OK (932.5) |
| 13 | Nights above / below R0 (Table 13) | 19/6, 15/5, 2/2, 30/0, 30/0 | same | OK |
| 14 | R1u(10) transfers, nights | 8 on 6 nights | 8 on 6 nights | OK |
| 15 | R0 minus R1u(10) reached | "about one request in 840" | exactly 1.0 request | OK |
| 16 | Dominance on means | only R1u(10) dominated, by R0 | same | OK |
| 17 | Decision moments; optimal; incomplete tie search | 13,663; all; 41 | 13,663; 13,663; 41 | OK |
| 18 | Run time | mean 32 s, max 253 s | 31.7 s, 252.9 s | OK |
| 19 | Guardrail excess | 36 events, 0 unexplained | 36, 0 | OK |
| 20 | Passengers per night; requests | 34-51; 28 | 34-51; 28 | OK |
| 21 | No-show rates (Sec. 4.6) | 4.7%; 8.9% | 2,359/50,297 = 4.69%; 2,359/26,454 = 8.92% | OK |
| 22 | Requests per completed ride | 2.087 / 2.09 | 2.0874 | OK |
| 23 | Load per vehicle-hour (Table 4) | 12.85 / 10.10 / 10.71 | 12.83 / 10.09 / 10.70 | Minor rounding; integers 64/50/54 unchanged |
| 24 | Five-van counts, largest remainder | 64 / 50 / 54 = 168 | exact 64.15 / 50.43 / 53.52; floors 167; leftover to 20:00 | OK |
| 25 | Party-size mean | 1.405 | 0.73 + 0.36 + 0.165 + 0.10 + 0.05 = 1.405 | OK |
| 26 | Pair weight factor | about 0.9 per minute | exp(-0.1) = 0.905 | OK |
| 27 | phi values, Table 7 and Fig. 10 | 27.5, 12.5, 52.5, 7.5; 5, 17.5, 42.5, 92.5 | same | OK |
| 28 | Worked example totals | 66.5; 81.0 | 66.5; 81.0 | OK |
| 29 | Sec. 5.2 prices | 262.5; 435.8 | 5 phi(16) = 262.5; 5 phi(19.47) = 435.8 | OK |
| 30 | R3 example timing | Lyft 18:27:00; gap 3 min 8 s; wait 10 min 30 s | 18:17 + 2 + 8; 18:30:08 - 18:27:00; 18:27:00 - 18:16:30 | OK |
| 31 | Map totals vs completed rides (Sec. 3) | "matching completed rides to within one" | 24,056 vs 24,095: differ by 39 | Wrong wording |
| 32 | Fig. 4 burst | 13.7 in burst, 840 total | bin heights sum about 27.8 per night; 28 x 30 = 840 | OK |
| 33 | Vans-only give-up share vs April range | not reported | 10.8/28 = 38.6% vs 23.7-35.5% implied | Missing check |

## Alignment with the presented deck

- Consistent on every simulated number checked; the report carries the deck's B6-B9 backups as Tables 2, 10, 11, 13.
- Label mismatches: Arrival times (Table 6 DESIGNED vs deck DERIVED + ASSUMED); Party size (report DERIVED + ASSUMED vs deck B4 "ASSUMED (mean derived)"); M uses sum_r b_r^max (report) vs sum_r b_r (deck B2).
- In the deck, missing from the report: costs are exact integers (B2), which App. B needs; the designed-evening Lyft delay is fixed at 8 min (slide 18); the acceptance probability and "a declined request is not offered again" (slide 15); the alternative group-size mixes (3+ share 8% / 12.3% / 9%), which the report gives only as a range.
- The deck's workload slide ("How busy should a constructed evening be?") still uses "about 5,100 rides / 30 days" while the report correctly uses 5,089. Fix the deck if it is reused.
- No contradictions in substance. No em dashes found in the report source (house style respected).

## Top 10 fixes, in priority order

1. Add an equal-Lyft-budget baseline (transfer-on-arrival or random set of B requests per night) so the value of prediction is separated from early transfer under the assumed Lyft delay (Sec. 8.1).
2. Report paired 95% intervals across the 30 nights for reach and Lyft orders (Table 11 or 13). State that R2(15) and R3(2) are indistinguishable on service, while R3 uses more Lyft.
3. Remove the ICML proceedings footer (p. 1).
4. Table 3: relabel (a) "Reframed; not yet tested" and (c) "plausible, untested"; drop the unsupported "pooling is common".
5. Define every symbol before or at first use: pi_r and b_r at eq. (1), Psi = 1000 and units at eq. (2), b_r^max and integer scaling in App. B; reference Apps. B and C from Sec. 5.
6. Compare the vans-only give-up share (38.6% of requests) with the April-implied 23.7-35.5% and say whether the burst explains it.
7. Fix the map-totals sentence (39 short of completed rides) and the rounding chain (12.83 / 10.09 / 10.70), and soften "the ride-time tail comes from routing".
8. One vocabulary: "request" for Night Ride, "Lyft order" for Lyft (Figs. 6, 9, 12, 15); same naming in Table 7 and Fig. 11.
9. Move Table 9 to the start of Sec. 6 and Fig. 11 beside Table 7; add no-show and transfer rows so Table 11 reconciles to 28.
10. Strengthen Sec. 10 and Sec. 11: list the missing assumptions (Lyft cost, availability, acceptance, load-independent delay, burst-only demand); give the benchmark a paired statistical design, a wider fleet range and a run-time estimate; tune thresholds on held-out nights.

Finding counts: 4 major, 28 minor, 19 nit.

---

## Resolution by the main session (2 Nov 2026)

Each finding was checked against the PDF and the source data before acting.

**Applied (verified):**
- Template footer replaced with a course line (no ICML venue claim).
- Table 3: point (a) now "Reframed; not yet tested"; point (c) "Plausible, untested" (unsupported pooling claim removed).
- Map totals wording corrected (origins and destinations agree within one; both 39 below completed rides). IPF now says totals were normalized to shares.
- Workload: 12.85 is reproduced from the tooltip value 5,098 (5,089 digitized gives 12.83); the text and Fig. 2 now say so. Hourly counts unchanged.
- Patience check added (38.6% given up under vans only vs 23.7–35.5% implied by April), in Sec. 4.5 and Sec. 10.
- Headline result: states that the 15-minute gain largely reflects transferring early under the Lyft-delay assumption; matched-budget baseline added to the plan.
- π_r, b_r, b_r^max, Ψ defined at first use; units stated as points; appendices referenced in the text; all references cited where used ([1]–[13], Deming & Stephan added for IPF).
- Table 11: no-show row and transfers row added; the outcome rows now sum to 28 (checked from `per_night_metrics.csv`).
- Node-arc lesson corrected (PWL convex penalty is LP-representable; the obstacle is size).
- Plan: tune-on-one-set / report-on-fresh-seeds for the threshold search; benchmark design (30 paired nights per cell, 4–7 vans, paired differences, run-time check first); re-check of the postponement price.
- Smaller items: target triple named; fixed 8-min Lyft delay in the worked example stated; n = 1 for the postponement experiment; blueprint labels aligned with deck B4; conclusion wording; trade-off figure redrawn with "Lyft orders"; rule table and worked-example figure moved next to their text; "booking" clarified in Fig. 6.

**Held for the team (not applied):**
- Paired confidence intervals now. The reviewer's computed intervals are plausible, but the team agreed (D-50) to fix the primary metric and margins before computing intervals, so they are not chosen after seeing results. The report now says this explicitly. Decision for the team.
- Matched-budget baseline run. It needs new simulation; added to the plan, not run.
