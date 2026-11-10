# Math and evidence review: midterm package v0.3

Reviewer: independent mathematical and evidence reviewer, 23 Oct 2026.
Scope: all 32 pages of `BlueJay_Midterm_v0.3_preview.pdf` (main deck 1–22, divider 23, backups B1–B9 on 24–32), plus `speaking_script.md`, `slide_explanations.md`, `content_storyboard.md`, `build_deck.js`, `make_numbers.py` and `data/numbers.json`.
Checked against: methodology v1.4, decision log (D-05, D-18, D-33, D-35–D-40, D-43, D-48–D-57 and the D-52/D-53 amendments), model_design v0.5, `outputs/sim/batch_L5_v1/` (summary, tradeoff, per-night CSV, all 180 `outcomes.csv`, tie check, reproducibility), `outputs/sim/L4_R3-2/` (epochs, events, outcomes), `outputs/sim/d53_experiment/d53_comparison.md`, and `data/processed/obs_p06/p07/p08/p09/p10`. I recomputed every result directly from the saved outputs. I edited no project file and ran no simulation.

## Verdict

**The package is numerically sound. I found no high-severity error.** Every headline number traces to a saved output or an observed CSV, and I reproduced each one independently:

- the volume chain;
- the no-show rates;
- the group-size means;
- the φ example;
- the 262.5 vs 435.8 example;
- the R011 timeline;
- the batch means;
- the fate counts;
- the dominance results;
- the diagnostics.

The main framing is careful and correct on most points:

- 30 nights replayed six ways;
- verification vs validation;
- curb arrival vs boarding;
- "optimal" restricted to the generated candidates and one decision moment;
- the leader–follower model shown as an unimplemented extension, with no collapse claim;
- guardrail excesses described only by attribution.

The remaining problems are wording that states an assumption as fact, or overstates a formal property. There are seven medium-severity findings:

- the dispatcher's Lyft transfers asserted to be recorded as "Canceled";
- "serving everyone comes first";
- ride time listed as a "hard limit";
- the dominance of "Unassigned for ten minutes" called "noise" or "a tie";
- "36 rides" over the time limit;
- thresholds described as "operating targets";
- a 74% bar label that double-rounds the true 73.45%.

There are also a dozen low-severity polish items.

## Findings

| # | Slide or file:section | Severity | Finding | Evidence (source and the value I found) | Correction (exact replacement wording) |
|---|---|---|---|---|---|
| 1 | Slide 9 (event box "Moved to Lyft by the dispatcher"); script §Slide 9; explanations §9 line 218 | medium | The deck states as fact that bookings the dispatcher moved to Lyft "close as 'Canceled' in the van system". It is one leg of the **assumed** status mapping, and the slide gives it no badge (the neighbouring "Rider gave up" box is marked assumed). The same mapping underlies the 8.9% figure. | Methodology App. C: "The mapping assumed: … Lyft hand-offs are recorded as 'Canceled'". D-49(4): the 50–75% range "ignores transfers recorded as Completed". | Slide: "Moved to Lyft by the dispatcher: assumed to close as 'Canceled' in the van system (not confirmed)". Script: "But the label probably also includes bookings the dispatcher moved to Lyft; we assume those close as 'Canceled' in the van system." |
| 2 | Slide 12 (table row "Postpone a booking"); script §Slide 12 | medium | The slide says a large constant makes "serving everyone come first". In fact M only guarantees that every proven-optimal plan postpones the **fewest** bookings that the candidate set allows. With K = 3 and the cap binding, some bookings are still postponed. The D-53 example on slide 15 is exactly such a case. | model_design §3: "every optimal solution leaves the fewest *requests* pending that the candidate set allows". B2 states it correctly. d53_comparison: 3 requests pending at 18:15 in every arm. | Slide: "…plus a large constant, so the plan serves as many bookings as the candidates allow before anything else". Script: "…but a large constant makes serving as many bookings as possible come first." |
| 3 | Slide 12 ("Points, not money": "Hard limits: seats, pickup before drop-off, ride time at most max(25 min, 2 × direct + 5 min)") | medium | The slide calls ride time a hard limit. In the code it is a planning guardrail: no candidate may create or worsen an excess, and existing excesses carry a penalty Ψ. Excesses can still occur between epochs; the batch has 36 of them (slide 22, B8). Calling it a hard limit contradicts the deck's own slide 22. | B2: "no candidate may create or worsen an excess". model_design c_vk includes Ψ·Σ q_r(H_r − G_r)⁺. summary.md guardrail row: 11/2/9/11/1/2 = 36. | "Hard limits: seats, pickup before drop-off. Ride-time guardrail max(25 min, 2 × direct + 5 min): no plan may create or worsen an excess (a no-show wait can still push a ride over; slide 22)." |
| 4 | Slide 20 bullet "dominated by a thousandth: noise"; script §Slide 20 ("by a thousandth, which is noise"); explanations §20 ("far inside the night-to-night SD of about 0.09: a tie in practice") | medium | There are two errors. (a) The dominance does not rest on the 0.001 in service. R1u(10) also uses 0.23 Lyft bookings per night against 0, so vans only would still dominate it with service exactly tied. (b) Comparing a paired difference with the between-night SD is the wrong yardstick, because the arms are paired. The two arms are identical on 24 nights, and the paired service difference is −0.0012, with 2 nights above and 2 below. "Noise" also implies a statistical judgement, which D-50 has not authorized. | tradeoff_rule_summary.csv: R1u S = 0.47619, B = 0.2333; R0 S = 0.47738, B = 0. Paired diff vs R0 = −0.00119; above/below 2/2; identical nights 24. | Slide: "'Unassigned for ten minutes' is dominated by vans only: about the same service (0.476 vs 0.477) with slightly more Lyft use (0.23 vs 0 a night)". Script: "…is dominated by vans only: it reaches about the same share and books a few Lyfts that vans only does not." Explanations: replace the SD sentence with "Identical to vans only on 24 nights; on the other 6 it reached more on 2 and fewer on 2 while booking 7 Lyfts in all. No statistical margin is applied (D-50)." |
| 5 | Slide 22 Limits bullet "36 rides over the time limit, each matching a no-show wait on that van"; script §Slide 22 ("we saw 36 such cases") | medium | The 36 are run-level excess events across 180 runs. They come from only 16 distinct bookings on 10 nights, because the same booking repeats under rules that made the same decisions. "36 rides" overstates the count roughly twofold. The script's Preparation note has the right figures, but the slide and the spoken text do not. | numbers.json guardrail: events 36, distinct_requests 16, nights 10. Methodology §7: "36 excess events … from 16 distinct requests on 10 nights". | Slide: "36 ride-time excesses across the 180 runs (16 distinct bookings on 10 nights), each coinciding with a no-show wait on that van (attribution, not proof)". Script: "…we saw 36 such excess events across the runs, from 16 distinct bookings, each matching a no-show wait on that van." |
| 6 | Script §Slide 13, Likely questions ("They are the operating targets of 10–15 min"); explanations §13 line 346 ("from the 10–15-min operating targets") | medium | The text calls the thresholds "operating targets". D-49 says the published target wording is "not proof of operating policy", and it changed over time: 10/20/15 until 2024, 15/20/20 around April 2026, 20/25/25 on the live page. "Operating targets" is the very proposal claim that B9 corrects. | D-49(1); B9 row "Targets as hard constraints … target wording changed over time". | "They echo the published pickup-target wording (10 min in older captures, 15 min around April 2026; wording, not verified operating policy) plus a 2-min margin. They were fixed before any run and not tuned to results." (same in explanations §13) |
| 7 | Slide 18 bar label "74%" and text "reach about 74–75%" (build_deck.js chart data) vs B6 "0.73 (0.07)" | medium | The label double-rounds. The true mean is 0.73452, which numbers.json first rounds to 0.735 and the chart then rounds to 74%. Correct rounding gives 73%, which is what B6, summary.md and the methodology show. A main-result slide should not disagree with its own backup. | tradeoff_rule_summary.csv reached_15_share_mean R2(15) = 0.7345238; summary.md 0.73. | Chart label "73%"; text "Prediction rules reach about 73–75%, against 48–51%". Fix the source by rounding from the unrounded mean (do not round to 3 dp before formatting). |
| 8 | Slide 6, badge on the "≈ 170" tile (OBSERVED) | low–medium | 5,089 ÷ 30 is a per-evening average **derived** from the observed 30-day total. It also assumes the hour's total spreads evenly over 30 days, while the vehicle chart covers 29 (D-49(3)). The OBSERVED badge blurs the distinction the deck teaches. | obs_p09 18:00 = 5,089.09 (30-day sum); D-05 labels 170/h DERIVED. | Badge "DERIVED"; keep "≈ 5,100 ÷ 30 ≈ 170". |
| 9 | Slide 4 ("5,098 at 6 pm, summed over 30 days") vs slides 5–6 ("5,089") | low | Two different values appear for the same quantity in the main deck: slide 4 uses the tooltip value and slides 5–6 the digitized value. B9 explains both, but the main deck does not. | numbers.json: tooltip_18 5,098; completed_by_hour[0] 5,089. ρ = 12.85 is computed from 5,089.09 / 30 × 2.0874 / 27.556. | Slide 4: "about 5,090 at 6 pm, summed over 30 days (tooltip 5,098)", or use 5,089 throughout. |
| 10 | Slide 6, chain "≈ 170 × 2.09 ≈ 355 ÷ 27.6 = 12.85" | low | The chain is fine, but recomputing from the displayed rounded inputs gives 12.83–12.87, not exactly 12.85. The "=" sign invites someone to redo the arithmetic and get a different answer. | 5,089/30 × 2.0874 / 27.556 = 12.850 (unrounded inputs); 170 × 2.09 / 27.6 = 12.87. | "≈ 12.85 (from unrounded inputs)", or show 27.56 instead of 27.6. |
| 11 | Slide 17 tile "identical — repeated runs give byte-identical results"; script ("repeated runs are identical") | low | This generalizes from a sample. The evidence is 6 of 6 sampled reruns, plus the 2 r00 runs matching the pilot. | reproducibility.json: 6 entries `events_identical: true`, 2 `batch_equals_pilot_output: true`. | "6 of 6 sampled reruns byte-identical". Script: "and the reruns we sampled were byte-identical." |
| 12 | Slide 17 tile "292,181 … always agreed with the optimizer" | low | The figure is correct: 151,710 combinations under the original price plus 140,471 under A, on the L4 designed evening. But the tile does not say the check covers only the designed evening, and only the same generated candidates. Without that, it can be read as a check of global optimality. | research_notes/d53_pending_price_review §: 151,710 / 140,471; methodology §5 verification table. | "plan combinations on the designed evening, checked by an independent brute-force program over the same candidates; always agreed with the optimizer" |
| 13 | Slide 18 Prediction box "using about 9–10 Lyft bookings a night"; script ("with nine to ten") | low | The upper end is 10.47, so the range is understated. | tradeoff_rule_summary: 9.33, 10.47. | "using about 9–10.5 Lyft bookings a night" |
| 14 | Script §Slide 18 ("The number above each bar is Lyft bookings per night") | low | This does not match the slide. The number at each bar is the service share; Lyft bookings per night sit in the category labels. | PDF p.18. | "The number at the end of each bar is the share reached; the Lyft bookings per night are in each label." |
| 15 | Script §Slide 18 ("A van was usually assigned quickly even when pickup was far off") | low | This explanation needs a qualifier. The only quantified support is L4, where every request was assigned within about 4 min. In L5 the rule did fire 8 times during the burst, so assignment is not always quick. | Methodology §7 mechanism 2: L4 "assigned every waiting request within about 4 minutes"; L5 fired 8 times on 6 nights (I confirmed: requests 18:21–18:28, transfers 18:35–18:38). | "Bookings were usually in some van's plan within minutes, even when the pickup itself was far off; only during the burst did some stay unplanned for ten minutes." |
| 16 | Script §Slide 19, Likely questions ("Lyft no-shows … 7 to 15 per rule") | low | The range is wrong. Wait fifteen minutes has 4 and Unassigned for ten minutes has 0. | Fates: 7 / 4 / 0 / 14 / 15. | "Yes, as a separate segment (0 to 15 per rule over 30 nights)." |
| 17 | Script §Slide 19 ("Transferring earlier leaves more time for the Lyft to arrive"); slide 19 blue box ("Earlier transfers leave more time for the Lyft.") | low | This is a causal interpretation that no experiment isolated; the rules differ in more than timing. | No ablation in batch_L5_v1. | "Consistent with earlier transfers leaving more of the rider's patience for the Lyft (not isolated by an experiment)." |
| 18 | Slide 15 bar chart | low | The bars have no unit, and the second label ("Earliest real pickup (18:19:28)") reads as a time rather than a price. | d53_comparison: R002 pending price 262.50 points; φ(19:28) × 5 = 435.83 points. | Axis or title "points"; labels "Price charged for postponing (points)" and "Price if served at the earliest real pickup, 18:19:28 (points)". |
| 19 | Script §Slide 15 ("Postponing them cost 262 points … worth 436 points") | low | 262.5 is rounded down while 435.8 is rounded up. The slide shows 262.5 and 435.8. | d53_comparison 262.50; numbers.json 435.83. | "…cost 262.5 points … worth about 436 points." |
| 20 | Script §Slide 14 ("…the rider was dropped at 18:30:25, a wait of ten and a half minutes from the original request") | low | The sentence attaches the wait to the drop-off time. The wait of 10 min 30 s runs from request to curb (18:16:30 → 18:27:00). The slide gets this right. | outcomes.csv R011: curb 1620 s, wait_s 630, drop 1825 s. | "…the Lyft reached the curb at 18:27, ten and a half minutes after the request, and the rider was dropped at 18:30:25." |
| 21 | Slide 8 tile "1.386 van passengers per completed van booking" (OBSERVED) | low | The figure is the ratio of two observed totals (33,394 passengers ÷ 24,095 completed). The word "van" in both places relies on the assumed mapping Completed = van-completed. | obs_p08 sum 33,394.2; obs_p07 completed 24,095.1; ratio 1.386. | Badge "DERIVED (ratio of two observed totals)", or keep OBSERVED and say "passengers per completed booking". |
| 22 | Slide 10 left card ("Most cancelled bookings never had a vehicle at the curb") | low | This is an inference under the assumed mapping, not an observation. | Methodology App. C (mapping assumed). | "Under our status mapping, a cancelled booking never had a vehicle at the curb." |
| 23 | B4 row "Travel times — OBSERVED road network" | low | OSRM times are modelled from the OpenStreetMap network, and the pilot multiplies van times by 1.2. That makes the times derived, not observed. | B4 itself: "Local OSRM routing; van times × 1.2". | Status "DERIVED (OSRM on OpenStreetMap; van × 1.2 assumed)". |
| 24 | Slide 21 constraint "the vans' routes are optimal for the follower, given θ" | low | The formulation is sound, and the "Still missing" list covers its gaps. One clause would prevent the reading that the follower solves a single whole-evening problem. | Explanations §21: "Ours optimizes one epoch at a time over restricted candidates." | "subject to: the vans' routes are the follower's optimal response, given θ (today: one decision moment at a time, over restricted candidates)" |
| 25 | Source document (not the deck): methodology v1.4 §"Pushback" item 1 | low (source, outside the deck) | The deck cites this section. Item 1 still says "No Lyft-rule comparison has been run", which is stale after M2 and the L5 batch (§7, D-55, D-57). | scenario_methodology.md line 33. | For the methodology owner: "Designed validation cases (L1–L4) and a 30-night descriptive pilot (L5) have been simulated; no rule has been ranked." (A guide edit requires the versioning rule.) |

## Claims verified as correct

**Volume (slides 3, 5, 6, B4, B9)**
- [x] 5,089 is the digitized 6 pm value (obs_p09 5,089.09).
- [x] The 6 pm tooltip reads 5,098.
- [x] 5,089 / 30 = 169.6 ≈ 170.
- [x] R/C = 50,297 / 24,095 = 2.0874.
- [x] The vehicle averages are 27.56, 27.27 and 24.58.
- [x] ρ = 12.850, 10.098 and 10.706.
- [x] Five vans give 64.25, 50.49 and 53.53, which round by largest remainder to 64 / 50 / 54 = 168.
- [x] The hourly bars 3,957 … 1,558 match obs_p09.
- [x] The pilot's 28 bookings in one hour on 2 vans is 14 per van-hour.

**Status counts and no-shows (slides 9, 10)**
- [x] 24,095 + 23,843 + 2,359 = 50,297.
- [x] 23,843 / 50,297 = 47.4%.
- [x] The footnote's 99 "Denied" and the digitized 23,842 are as stated.
- [x] 2,359 / 50,297 = 4.69% ≈ 4.7%.
- [x] 24,095 + 2,359 = 26,454, and 2,359 / 26,454 = 8.92% ≈ 8.9%.
- [x] 8.9% is presented as a provisional, conditional derivation (slide 10 box, B4, explanations §10), not as a verified probability.
- [x] "4.7% per arrival would undercount by about half": 4.7 / 8.9 = 0.53.

**Riders and group sizes (slides 3, 4, 8, B4)**
- [x] Riders: 24.5% of 44,374 rode Lyft. The digitized daily sums give 10,821 / 44,248 = 24.46%.
- [x] The correction "a share of riders, not trips" is right.
- [x] Group-size means: ours 1.405, H1 1.386, H2 1.386.
- [x] Shares of bookings with 3 or more riders: 8.0%, 12.3% and 9.0%.
- [x] 1.386 = 33,394 / 24,095.
- [x] H1 and H2 are labelled as illustrations.

**Trip pairing, patience and Lyft delay (slides 7, 9, B4)**
- [x] A decay of e^(−0.1) = 0.905 matches "about 10% per extra minute" (D-18, β = 0.1 per min).
- [x] Patience is Weibull with shape 1.5 and median 18 min, so the scale is 18 / (ln 2)^(2/3) = 22.98 ≈ 23.0 (D-39).
- [x] The 50–75% share of "Canceled" is labelled as an assumed range (D-39, D-49).
- [x] Lyft lag is 2 min, and the delay is lognormal with median 8 min and 90th percentile 15 min (D-43; manifest lag_s 120).

**Routing objective and MILP (slide 12, B2)**
- [x] φ slopes are 1 / 2.5 / 5 / 10 / 20, with breaks at 5 / 10 / 15 / 20 min.
- [x] The example values check: φ(12) = 27.5, φ(8) = 12.5, φ(16) = 52.5, φ(6) = 7.5.
- [x] Route A: 52.5 + 13.0 + 1.0 = 66.5.
- [x] Route B: 67.5 + 12.5 + 1.0 = 81.0.
- [x] In Route B rider 1 waits 16 min, past the 15-min break where the slope is 10 points per minute.
- [x] β = 0.5 and γ = 0.1 per km (manifest).
- [x] The guardrail is max(25, 2 × direct + 5): g_abs 1500 s, α 2, δ 300 s.
- [x] B2 is a correct set-partitioning MILP.
- [x] The M bound is valid: one extra postponement costs ≥ M − Σ b_r − Σ_v (max − min) = 1 > 0.5 (the absolute gap), given b_r ≥ 0.
- [x] HiGHS runs with relative gap 0 and absolute gap 0.5.
- [x] MILP is spelled out on slide 12 and in the script.
- [x] "Optimal" is correctly qualified: over the generated candidates, up to 3 new pickups per van, at one moment, not over the evening (slide 12, script, explanations).

**Transfer rules (slide 13, B1)**
- [x] The six rule definitions match.
- [x] R3(2) compares now + 2 + 8 against the predicted van pickup, with a margin above 2 min.
- [x] The L4 settings are vans from 18:15, Lyft delay fixed at 8 min, and acceptance 0.9.
- [x] L5 uses consent 1.0, which the slides label "riders accept Lyft" and assumed (D-56, D-57).

**Worked transfer R011 (slide 14)**
- [x] Request at 990 s = 18:16:30.
- [x] Transfer decision at 1020 s = 18:17:00.
- [x] Predicted van pickup 1808 s = 18:30:08 (epochs.jsonl lyft.reads).
- [x] Expected Lyft 1020 + 120 + 480 = 1620 s = 18:27:00; the gap is 188 s = 3 min 8 s, which exceeds 2 min.
- [x] Booking at 1140 s = 18:19:00.
- [x] Curb arrival at 1620 s = 18:27:00.
- [x] Drop-off at 1825 s = 18:30:25.
- [x] The wait is 630 s = 10 min 30 s.
- [x] At 18:16:30 the gap was 14 s, below the 2-min margin, so no transfer then. This is consistent with the slide.
- [x] "What the van would have done is never observed" is correct.

**Postponement price (slide 15, B5)**
- [x] The original price is 262.50 = 5 × φ(16), the next tick at 18:16.
- [x] The price at the earliest physical pickup is 5 × φ(19.467) = 435.83, a difference of 173.3 (D-53 update: "+173 points").
- [x] Whole designed evening, first version vs chosen: median 17.1 vs 18.6, P90 31.0 vs 31.2, max 44.4 vs 35.6, mean 18.79 vs 18.80. B gives 21.1 / 34.3 / 38.6 with mean 21.82.
- [x] The party of five waits 22:18, 19:28 and 20:39 in the three versions.
- [x] B adds up to 9,828 z variables, and its MILP takes 4.79 s.
- [x] A adds 0 variables.
- [x] "Redistributed, not reduced on average" holds.

**Batch results (slides 16, 18, B6, B7)**
- [x] 180 runs = 30 × 6, described as "30 synthetic nights replayed six ways, not 180 independent nights" on slide 16, B6 and the script.
- [x] Service means: 0.477 / 0.514 / 0.495 / 0.476 / 0.735 / 0.750. SDs range from 0.074 to 0.096, matching "about 0.07–0.10".
- [x] Lyft bookings per night: 0 / 5.93 / 3.10 / 0.23 / 9.33 / 10.47 (standard + XL).
- [x] Van-km: 51.2 / 47.6 / 48.6 / 51.9 / 45.7 / 43.0.
- [x] Every B6 cell matches summary.md.
- [x] The run-time means (43 / 40 / 49 / 50 / 5 / 4 s) average to 31.7 s, and the longest run is 252.9 s.
- [x] "Reached" is defined as curb arrival, not boarding, over all 28 bookings (slide 18, B6, explanations).

**Fates of transferred bookings (slide 19)**
I recomputed the fate counts from all 180 outcomes.csv files:

| Rule | Lyft completed | Lyft no-show | Cancelled in lag | Cancelled after booking | Total |
|---|---|---|---|---|---|
| Wait ten minutes | 94 | 7 | 18 | 77 | 196 |
| Wait fifteen minutes | 55 | 4 | 11 | 34 | 104 |
| Unassigned for ten minutes | 4 | 0 | 1 | 3 | 8 |
| Predicted total wait exceeds fifteen minutes | 187 | 14 | 14 | 79 | 294 |
| Lyft arrives sooner | 211 | 15 | 16 | 88 | 330 |

- [x] Every row reconciles.
- [x] Under "Wait ten minutes", 95 of 196 = 48% cancelled before the Lyft arrived ("almost half").
- [x] The prediction rules lost 31.6% and 31.5% ("about a third").
- [x] The booking lag is 120 s for all 872 bookings.
- [x] Transfers minus cancellations in the lag equal bookings × 30: for example, 196 − 18 = 178 = 5.93 × 30.
- [x] The deck keeps cancellations before and after transfer separate (slide 19 legend, B6 rows "Cancelled waiting for van" and "Cancelled after transfer").

**"Unassigned for ten minutes" (slide 18)**
- [x] 8 transfers on 6 nights.
- [x] Identical to vans only on 24 nights.
- [x] The requests fell between 18:21 and 18:28, inside the burst, with transfers at 18:35–18:38.
- [x] It is described as "mostly inactive", not universally inactive.

**Pareto statements (slide 20, B7)**
- [x] The dominance definition (≥ on both objectives, strict on one) is correct, and the A/B/C cartoon is correct.
- [x] The tie treatment is right: identical points are both nondominated.
- [x] "Five of six not dominated" on the means is correct, and the same five stay nondominated with van-km as a third objective.
- [x] Nights nondominated: 30 / 11 / 14 / 26 / 24 / 12.
- [x] Nights identical to vans only: 30 / 0 / 1 / 24 / 0 / 0.
- [x] Nights reaching above / below vans only: 0/0, 19/6, 15/5, 2/2, 30/0, 30/0.
- [x] The deck makes no global-frontier claim ("six tested rules, not a frontier").
- [x] "Nondominated ≠ recommended" is stated.
- [x] The routing weights are kept separate from the policy trade-off.

**Leader–follower (slide 21)**
- [x] It is badged NOT IMPLEMENTED.
- [x] The bilevel statement is sound.
- [x] The "still missing" list is accurate.
- [x] Riders and Lyft are correctly not treated as players.
- [x] No single-level reduction is claimed.
- [x] Explanations §21 states "aligned objectives do not by themselves collapse the hierarchy". Nothing anywhere claims a collapse.

**Verification and diagnostics (slide 17, B8)**
- [x] "3 designed evenings to the second" refers to the L1–L3 answer keys.
- [x] 253 tests, of which 168 = 38 + 29 + 101 were written by independent reviewers.
- [x] 292,181 = 151,710 + 140,471.
- [x] 13,663 epochs, all with an optimal main solve.
- [x] 41 epochs had an incomplete tie search; each has a unique optimum by enumeration and the chosen plan is canonical (tie_incomplete_check.csv: 41 rows, all True).
- [x] 36 guardrail events, 0 unexplained, from 16 distinct bookings on 10 nights.
- [x] One code fingerprint covers all runs.
- [x] Verification and validation are kept distinct (slide 17, slide 22).

**Other framing**
- [x] Slides 16 and 22 and the script describe the two-van pilot and the five-van evening as "designed, not yet run".
- [x] The proposal corrections (slide 3, B9) are consistent with methodology §1a and D-49, apart from finding 6 in the script and explanations.
- [x] The guardrail excesses are described only as attribution evidence (B8, slide 22, script, explanations), apart from the count wording in finding 5.
