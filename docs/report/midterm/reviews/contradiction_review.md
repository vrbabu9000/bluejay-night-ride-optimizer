# Internal contradiction review: BlueJayNightRide_Midterm (17 pages)

Reviewed: `BlueJayNightRide_Midterm.tex` and the rendered PDF (all 17 pages, including every figure). Ground truth consulted: `outputs/sim/batch_L5_v1/tradeoff_rule_summary.csv`, `docs/presentations/midterm/v0.4/derived/numbers.json`, `docs/technical/decision_log.md`, `docs/technical/scenario_spec.md`, and the epoch log `outputs/sim/L4_R3-2/epochs.jsonl` for the worked transfer.

## Verdict

The report is internally consistent on everything that matters most: every headline result (0.48 vs 0.73 / 0.75 reach, 9.3 / 10.5 Lyft orders, five nondominated rules, 19 / 6 nights, 95 of 196 lost transfers) agrees across abstract, body, tables, figures and appendix, and with the batch CSV. No finding changes a result. There are three direct contradictions, all small and all labelling or arithmetic (an evidence label, a residual count). The rest are wording inconsistencies or places where one passage claims a little more, or describes the plan a little differently, than another. All are fixable with one-line edits.

## Findings

**1. Direct contradiction: evidence label of 1.386 passengers per completed request.**
- A: p. 4, Table 4 caption: "All are OBSERVED except the last block"; the row "Van passengers per completed request 1.386" sits in the observed block.
- B: p. 4, Sec. 4.4: "April identifies an average, 1.386 van passengers per completed van request DERIVED".
- Why: the same number carries two different evidence labels, in a report whose method rests on the labels.
- Data: decision log (line 188) and scenario_spec §3 both call 1.386 a derived mean. B is right.
- Fix: move the 1.386 row below the rule into the DERIVED block of Table 4 (or add it to the caption's exceptions).

**2. Inconsistency: the party-size mean is labelled DERIVED in the blueprint but called "our choice" in the text.**
- A: p. 6, Table 6, Party sizes: "ASSUMED (mean DERIVED)", Value "Mean 1.405".
- B: p. 4, Sec. 4.4: "We chose shares ... (mean 1.405) ASSUMED ... the small difference is our choice, not evidence."
- Why: Table 6 reads as if 1.405 were derived; the derived mean is 1.386 and 1.405 is assumed.
- Data: scenario_spec says the distribution is "assumed ... chosen near April's derived 1.386". B is right.
- Fix: Table 6 status "ASSUMED (chosen near the DERIVED 1.386)".

**3. Direct contradiction (arithmetic): "both fall 39 short".**
- A: p. 3, Sec. 3, Preprocessing: "24,056 origins and 24,057 destinations ... both fall 39 short of the 24,095 completed rides."
- B: same sentence's own numbers: 24,095 minus 24,057 is 38.
- Why: origins are 39 short, destinations 38.
- Fix: "fall 39 and 38 short of the 24,095 completed rides".

**4. Inconsistency: which group "Unassigned for ten minutes" (R1u(10)) belongs to.**
- A: p. 11, Sec. 6: "Two groups matter: the waiting-time rules look only at time already waited; the predictive rules read the van plan's predicted pickup."
- B: p. 8, Table 7: R1u(10) uses "time outside every van plan" (it reads the plan's assignment). p. 11, Sec. 8.1: "The waiting-time rules barely moved it (0.50 to 0.51)", which excludes R1u's 0.48; p. 12: "629 s and 932 s for the two waiting-time rules".
- Why: R1u is in neither group, yet Sec. 6 implies there are only two, and Sec. 8.1's range silently drops it. A reader who counts R1u as a waiting-time rule finds 0.48, not 0.50 to 0.51.
- Fix: in Sec. 6 add "R1u(10) reads only whether the request is in any van plan, so it sits between the two groups"; in Sec. 8.1 write "The waiting-time rules barely moved it (0.50 to 0.51), and R1u(10) not at all (0.48)."

**5. Tension: the "Lyft arrives sooner" worked example says the request "is evaluated at 18:17:00", but decision moments fire at each new request.**
- A: p. 11, Sec. 6: "a request made at 18:16:30 is evaluated at 18:17:00".
- B: p. 6, Sec. 5: "A decision moment is triggered every 2 minutes and at each new request"; p. 17, App. C puts new requests before the decision moment in the same second; p. 12: predictive rules' "median time waited at transfer: 0 s".
- Why: read together, the rule should first see the request at 18:16:30, not 18:17:00. The example reads as if 18:17:00 were the first evaluation.
- Data: `outputs/sim/L4_R3-2/epochs.jsonl` has an epoch at 990 s (18:16:30) where the plan predicted pickup at 18:26:44 against an expected Lyft at 18:26:30 (gap 14 s, below 2 min, so no transfer). At the 1,020 s tick (18:17:00) the prediction had slipped to 18:30:08 and the rule fired. The report's numbers are right; only the wording hides the first evaluation.
- Fix: "At 18:16:30 the van was predicted only 14 s later than a Lyft, so the rule waited; at the next decision moment, 18:17:00, the prediction had moved to 18:30:08 ..."

**6. Inconsistency: "Calibrating patience is the first step of our plan".**
- A: p. 5, Sec. 4.5: "Calibrating patience is the first step of our plan (Section 11)."
- B: p. 14, Sec. 11 item 1 and p. 15, Fig. 16 step 1: "Behavioural sensitivity. Rerun the saved nights under other patience shapes ... Does the gap between rules survive?"
- Why: step 1 is a sensitivity analysis over patience shapes, not a calibration; no step of the plan calibrates patience to April's 23.7 to 35.5% band.
- Fix: either reword Sec. 4.5 ("Testing other patience shapes is the first step of our plan") or add the calibration check to item 1 ("and check which shapes bring the vans-only give-up share inside April's band").

**7. Tension: robustness "before" tuning vs the timeline.**
- A: p. 14, Sec. 11: "The next steps are ordered so that we test robustness before fine-tuning a winner"; item 5: threshold search "Only then".
- B: p. 15, Timeline: "Late November: paired intervals, threshold search, robustness checks."
- Why: the timeline lists robustness checks alongside, or after, the threshold search. It also omits item 4, the matched-budget baseline, which Sec. 8.1 calls the comparison needed to show prediction adds value.
- Fix: "Late November: matched-budget baseline, paired intervals, then threshold search" and, if "robustness checks" means something other than item 1, name it (for example "re-running the tuned rule under the sensitivity cases").

**8. Tension: "one large constant remains" vs Ψ = 1000.**
- A: p. 4, Table 3, row 4: "One large constant remains (the postponement constant M)"; p. 9, Sec. 5.1: "This is the one near-lexicographic element left in the model".
- B: p. 7, Sec. 5.1: "Ψ = 1000 points per passenger-minute a very large penalty for guardrail excess"; App. B repeats Ψ.
- Why: the report itself calls Ψ "very large". A reader checking the lexicographic claim will see two big constants.
- Fix: one clause in Table 3 and Sec. 5.1: "Ψ is also large, but it only prices excess already locked into committed work, since no candidate may create or worsen an excess; it never trades against waiting in a choice between candidates."

**9. Tension (claim strengthened): cause of April's ride-time tail.**
- A: p. 3, Sec. 3: the 90th-percentile ride "is consistent with detours for shared riders"; p. 4, Table 3: "consistent with shared-ride detours, so routing choices plausibly matter".
- B: p. 8, Sec. 5.1, Weighted not lexicographic: a strict waiting priority "can buy a tiny wait saving with an unbounded on-board detour, the long-ride tail behind April's 24-minute ride percentile."
- Why: B reads as if detours caused by wait-first priority are known to be behind April's tail; A says only "consistent with".
- Fix: "the kind of long-ride tail that April's 24-minute percentile may reflect".

**10. Tension: how much brute-force enumeration was done.**
- A: p. 11, Sec. 7: "On one designed evening a separate brute-force program enumerated 292,181 plan combinations".
- B: p. 17, App. B: "(checked by full enumeration on designed evenings)"; p. 11, Table 10: "in all 41, full enumeration shows a unique optimum" (pilot moments, not designed evenings).
- Why: one evening vs several evenings vs pilot moments; the reader cannot tell the scope of the enumeration check.
- Fix: make App. B say "on one designed evening (Section 7), and on the 41 pilot moments with an incomplete tie search (Table 10)", or state in Sec. 7 that there were several if so.

**11. Tension: what the matched-budget baseline matches.**
- A: p. 12, Sec. 8.1: "a baseline that moves the same number of requests"; p. 14, item 4: "moves the same number of requests per night".
- B: p. 15, Fig. 16 step 4: "matched-Lyft baseline".
- Why: transfers and Lyft orders differ by lag cancellations (Table 11: R2(15) 9.8 transfers vs 9.3 orders), so "same requests moved" and "same Lyft use" are different baselines.
- Fix: pick one in all three places (matching transfers is the cleaner test of prediction; then the figure box should read "matched-transfer baseline").

**12. Tension: study area and what the dashboards cover.**
- A: p. 1, Sec. 1: "Our study area is the Homewood service including the Peabody area; East Baltimore is excluded"; p. 3, Sec. 3: dashboards "for the Homewood Night Ride".
- B: p. 6, Fig. 5 caption: "a few reach Mount Vernon (Peabody) and the Inner Harbor"; p. 3, Table 2 and p. 4, Table 4: the 27.6 vehicles are the "All services" average, "not a Homewood-only count".
- Why: the stated area (Homewood plus Peabody) does not mention the Inner Harbor trips that appear in the scenario, and "dashboards for the Homewood Night Ride" sits awkwardly next to an all-services vehicle panel.
- Fix: "Our study area is the Homewood service as mapped in April (reaching Mount Vernon/Peabody and the Inner Harbor); East Baltimore is excluded", and in Sec. 3 "the dashboards are for the Homewood Night Ride, except the vehicles-on-duty panel, which covers all services".

**13. Tension (mild strengthening): conclusion vs the early-transfer caveat.**
- A: p. 15, Sec. 12: "transfer rules that moved requests early, guided by the van plan's predicted pickup, improved timely curb arrival while using more Lyft."
- B: p. 12, Sec. 8.1: "this comparison does not isolate the benefit of prediction ... the gain on this measure largely reflects transferring early".
- Why: "guided by the van plan's predicted pickup" can be read as crediting the prediction, which B says is not yet shown.
- Fix: "transfer rules that moved requests early (here, the two rules that read the van plan) improved timely curb arrival while using more Lyft; whether the prediction itself adds value is not yet tested."

**14. Inconsistency (rounding): 35.5% upper bound.**
- A: p. 5, Sec. 4.5 and p. 14, Sec. 10: "0.474 x (50 to 75%) = 23.7 to 35.5%".
- B: Table 4 inputs: 23,843 / 50,297 = 0.47404; x 0.75 = 35.55%, which rounds to 35.6% (0.474 x 0.75 is also exactly 35.55).
- Why: the stated arithmetic gives 35.55, which conventional rounding reports as 35.6.
- Fix: write 35.6% in both places (the 38.6% comparison is unaffected).

**15. Inconsistency (minor): "Three things changed" vs a five-row table.**
- A: p. 2, Sec. 2: "Three things changed (Table 1)."
- B: p. 2, Table 1 has five rows (adds "Published targets as hard limits" and "Claims about real nights").
- Fix: "Three things changed, with two consequences (Table 1)" or "Table 1 lists five changes".

**16. Tension (minor): Table 6 caption vs unmarked pilot settings.**
- A: p. 6, Table 6 caption: "'Pilot' marks settings used for the results in this report."
- B: same table: patience, presence, Lyft delay and travel times are unmarked but were used in the pilot (Sec. 7 lists them as pilot settings).
- Fix: "'Pilot' marks values that differ in the pilot or are fixed only for it; all other rows apply to the pilot as well."

## Pairs checked that are consistent

- Abstract reach (about three quarters vs about half) and 9 to 10.5 Lyft orders match Sec. 8.1, Table 11, Fig. 13, Table 13 and the batch CSV (0.735 / 0.750 vs 0.477; 9.33 / 10.47).
- Pending price status: "provisionally adopted" (Sec. 5.2) and "adopted" (Sec. 5.1, Table 9, plan item 6) match decision log D-53 "A approved (provisional)".
- K = 3 and "four new pickups took minutes" agree in Sec. 5.1, Sec. 9 and Table 3.
- Re-planning every 2 minutes agrees in Sec. 5, 5.2, 9, Table 3 (60 / 120 / 300 s) and the spec (120 s).
- No-show wait of 3 minutes agrees in Sec. 1, Fig. 9 (180 s) and its caption.
- 8.9% = 2,359 / 26,454 agrees in Sec. 4.6, Fig. 7, Table 6 and Sec. 7.
- Cost weights (0.5 riding, 0.1 per km) and slopes 1 / 2.5 / 5 / 10 / 20 match Fig. 11 knots (5, 17.5, 42.5, 92.5), Table 8's phi values and the TransLoc check (2.5 > 2).
- Fig. 10 stop times reproduce Table 8 waits and rides; totals 66.5 and 81.0 are correct.
- Sec. 5.2's 262.5 and 435.8 points reproduce from phi with a party of five (waits 16 min and 19 min 28 s).
- Table 11 outcome rows sum to 28 for every rule (R1u 27.9 by rounding); requests picked up equal van plus Lyft completed within rounding.
- Fig. 14 counts reconcile with Table 11 per-night means and Sec. 8.2 (196 / 104 / 8 / 294 / 330 transfers; 95 of 196 lost, 18 + 77; about a third for R2 and R3).
- R1u "8 transfers on 6 of 30 nights" matches Table 13 (24 nights identical to vans only) and Table 11 (0.3 transfers, 0.2 orders).
- "Within about one request in 840" matches 0.477 minus 0.476.
- "Five of six nondominated", "19 above / 6 below" and "30 / 0" for the predictive rules match Fig. 15, Table 13 and the CSV.
- 38.6% = 10.8 / 28 agrees in Sec. 4.5 and Sec. 10.
- Workload chain 5,098 / 30 x 2.087 / 27.6 = 12.85 matches Fig. 2; 5 x (12.85, 10.10, 10.71) = 64.25 / 50.50 / 53.55 rounds to 64 / 50 / 54 = 168 as in Fig. 3.
- Burst mean 13.7 agrees in Sec. 4.2 and Fig. 4 (about 6.5 + 7.2 per bin).
- Run time 32 s mean, 253 s longest agrees in Table 10 and plan item 6 (numbers.json 31.7 / 252.9).
- 253 tests agrees in Sec. 7 and the AI-use disclosure; seven feedback points and four corrected numbers agree with Tables 3 and 2 and Sec. 9.
- Lyft delay median 8 min, 90th percentile about 15 min agrees in Fig. 6, Table 6, the R3 rule and plan item 1.
- Patience Weibull shape 1.5, median 18 min agrees in Sec. 4.5, Table 6 and Fig. 6.
- Guardrail rule (no candidate may create or worsen excess; committed excess charged Psi) is consistent with Table 10's 36 excess events, all on committed work during no-show waits.
- Fig. 2's grey boxes labelled DERIVED vs caption "use only observed totals": consistent with the DERIVED definition (computed from observed numbers).
- Sec. 2 "because the real dispatcher's internals are not known" vs "a scope choice": the first motivates the second; not contradictory.
- App. B "node limit never reached" agrees with Table 10 "proven optimal in all 13,663 moments".
- "Wait ten minutes almost never reaches the curb within 15 minutes" is consistent with the lognormal delay in Fig. 6 (P(delay at most 3 min) is about 2%).
- "Verified, not validated" is used the same way in the abstract, contributions, Sec. 7, Table 10, Sec. 10 and the conclusion.

## Resolution (main session, 3 Nov 2026)

- **Applied:** 1 (1.386 is DERIVED everywhere), 2 (party sizes ASSUMED, mean 1.405 shown beside the derived 1.386), 3 (39 and 38 short), 4 (three rule groups; R1u's 0.48 stated), 5 (R3 example now shows the 18:16:30 evaluation, 14 s gap, then the 18:17:00 transfer; confirmed in the epoch log), 6, 7, 8 (Table 3 names Psi separately from M), 9, 10 (Appendix B: "a designed evening"), 11 (roadmap now "matched-budget"), 12 (study-area sentence notes April's map places reach the Inner Harbor), 13 (conclusion reworded), 14 (35.6%: 23,843/50,297 x 0.75 = 0.3555), 15, 16.
- **Held:** 12, the vehicle-count half (Table 2 already states the count is "All services", not Homewood-only).
