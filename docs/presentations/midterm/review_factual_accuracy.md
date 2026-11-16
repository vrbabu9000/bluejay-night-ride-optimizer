# Midterm package: factual-accuracy review (22 Oct 2026)

**Scope.** Every quantitative and factual or methodological claim in:
- `BlueJay_Midterm_draft.pptx` (slide text and speaker notes, 22 slides);
- `speaking_script.md`;
- `slide_explanations.md`.

**Checked against.** The decision log (D-01…D-57 and the design trail), `scenario_spec.md` v0.8, `model_design.md` v0.5, `scenario_methodology.md` v1.4, `transloc_operations.md`, the Phase 4 log, the saved outputs under `outputs/sim/`, the April observation files `data/processed/obs_p06–p09`, the proposal deck, and `pytest --collect-only`.

**Recomputed independently.** These scripts are in `/private/tmp/claude-501/fact_check/` and are read-only:
- transfer fates from the 180 per-run `outcomes.csv` files;
- R1u(10) transfer times;
- guardrail excesses from the per-run `manifest.json` files;
- the trade-off means, nondominance and per-night counts, from `per_night_metrics.csv`;
- the April ratios from the `obs_p0*` files;
- the φ worked example;
- the Weibull and lognormal parameters;
- the test counts.

**Numbering.** Slides are cited by the deck's printed page number (title = 1). The script and the explanations number the core slides from 1 starting after the title, so their "Slide n" is deck page n + 1.

## Summary verdict

The package is accurate on substance. Every headline number reproduces from the saved outputs or the April files:
- 50,297 / 24,095 = 2.087;
- 2,359 / 26,454 = 8.9%;
- ρ = 12.85, which gives 64 / 50 / 54 = 168;
- 66.5 versus 81.0;
- the transfer-fate table;
- the trade-off means and the nondominated set;
- 253 tests, of which 168 are independent;
- 151,710 combinations;
- 22 transfers and 4 declines;
- 8 R1u(10) transfers on 6 nights;
- 36 guardrail excesses;
- 13,663 epochs;
- 41 incomplete tie searches;
- the R011 timeline;
- the pending-price table;
- 44,374 riders and 24.5% by Lyft.

All twelve wording safeguards (a)–(l) are respected in the slides, the notes, the script and the explanations.

**Three errors need fixing.** Each is small:
- one φ slope in the slide-7 notes;
- the Weibull scale in the explanations;
- "almost half" in the slide-10 notes.

**One mislabelled reproducibility count.** B8 says "8 of 8 sampled reruns". There were 6 reruns, plus 2 comparisons of batch runs with the earlier pilot outputs.

**About a dozen imprecisions.** The most important is that the 36 guardrail excesses are 16 distinct request-nights repeated across rules. The others are stale spec-version citations, a misleading "Tested:" label, presenter slide ranges that are offset from the page numbers, and an unqualified "up to" on B's variable count.

## Issues

| ID | Severity | File, location | Claim | What the source says | Suggested correction |
|---|---|---|---|---|---|
| F-01 | **error** | Deck p.7, speaker notes | "the fifth minute of waiting costs 1 point, **the fifteenth costs 10**, the twenty-first costs 20" | φ slopes are 1 / 2.5 / 5 / 10 / 20 *after* 0 / 5 / 10 / 15 / 20 min (D-29; methodology §6). The 15th minute (14→15) costs **5**. The 16th costs 10. | "the fifth minute costs 1 point, the sixteenth costs 10, the twenty-first costs 20" |
| F-02 | **error** | Explanations, Slide 4 ("Rider patience") | Weibull scale "18 / (ln 2)^(1/1.5) ≈ **23.1** minutes" | 18 / 0.7832 = **22.98** min. This is the same formula as `generator_v2.py` l.318. | "≈ 23.0 minutes" |
| F-03 | **error** | Deck p.10, speaker notes | "many late transfers end in cancellation after the booking was placed. Under 'transfer after 10 minutes waited' **almost half** of transfers ended that way" | R1(10): 77 of 196 (39%) cancelled after booking. 95 of 196 (48%) cancelled before the Lyft arrived, including 18 during the lag (recomputed from outcomes.csv; methodology §7a). | "…almost half (95 of 196) cancelled before their Lyft arrived, most of them (77) after the booking was placed" |
| F-04 | **error** (count mislabelled) | Deck p.22 (B8), bullet 6; `deck_numbers.json` "diagnostics" | "Reproducibility: **8 of 8 sampled reruns** identical byte for byte" | D-57 and Phase 4 log: "6/6 sampled runs reproduce". Methodology §7a: "6 sampled reruns were byte-identical…, and the two r00 batch runs were byte-identical to the earlier pilot outputs". `reproducibility.json` holds 6 `events_identical` entries and 2 `batch_equals_pilot_output` entries. | "6 of 6 sampled reruns identical byte for byte; the two r00 batch runs also match the earlier pilot outputs" |
| F-05 | imprecise | Deck p.10 (Guardrail box) and p.22 (B8); script Slide 9; explanations Slide 9; methodology §7a | "36 rides exceeded the ride guardrail" | 36 is a count of excess *events* over the 180 runs (11/2/9/11/1/2 by rule). Paired replays repeat the same event: there are only **16 distinct (night, request) pairs on 10 of 30 nights**. For example, R0 and R1u(10) are identical on 24 nights. | "36 excesses across the 180 runs (16 distinct requests on 10 nights, repeated under rules that made the same decisions)". At minimum, say "across 180 runs". |
| F-06 | imprecise | Deck p.8, table row "Extra MILP variables / solve time" | B: "9,828 / 4.8 s" | 9,828 is the *maximum* number of z variables in one epoch. 4.8 s is the *total* MILP time over the evening (d53_comparison.md; D-53 "up to 9,828"). The explanations already say "up to". | "up to 9,828 / 4.8 s (whole evening)" |
| F-07 | imprecise | Deck p.4, bottom-left line | "**Tested:** the count is a range, ~150–260, not a confidence interval; geography also has a spread-out variant" | The 150–260 range is an illustrative sensitivity range and has not been run (D-49(2)). The dispersed variant is "implemented and verified" only for internal consistency, and no experiment has used it (D-34; trail §4, correction 5). | Replace "Tested:" with "Uncertainty:", and say "a spread-out geography variant is built (not yet used in experiments)" |
| F-08 | imprecise | Script, Slide 3 | "so that choice is ours, **and we test** a spread-out geography variant" | As in F-07: no run has used the dispersed variant. | "and we have built a spread-out geography variant to test it" |
| F-09 | imprecise | Deck p.3 notes ("the hard limit is a ride guardrail"); script Slide 2 ("The one hard limit is a guardrail") | The guardrail is a hard limit | D-29 calls it an "elastic guardrail". D-47(2): no candidate may *create or increase* a violation, and unavoidable violations are penalised by Ψ. The batch executed 36 excesses between epochs. | "The one limit built into planning is a ride-time guardrail: no plan may create a ride over it" |
| F-10 | imprecise | Deck p.1 (title) | "P1 (slides 1–4) · P2 (5–8) · P3 (9–12)" | These ranges use the script's numbering. The printed page numbers put P1 on pp.2–5, P2 on 6–9 and P3 on 10–13, and the speaker notes agree. The script's "Slide n" and Q&A references ("Slide 2; backup B4") are off by one from the printed pages throughout, as are the explanations. | Use the printed page numbers in all three documents, or state the convention once at the top of the script and the explanations |
| F-11 | imprecise | Deck p.6 and p.16 (B2) sources; explanations "Sources" | "scenario_spec.md **v0.7**" | The spec is **v0.8** (22 Oct). The Phase 4 log shows the midterm package itself bumped it. | Cite v0.8 |
| F-12 | imprecise | Script, Slide 4 | "One percent of bookings are parties of five, which need a larger Lyft" | 1% is the *assumed* distribution (D-38), not an observation. XL eligibility comes from user-supplied operational knowledge, not verified Hopkins policy (D-33). | "In our assumed distribution, one percent of bookings are parties of five; if transferred, they go together in a larger Lyft (XL)" |
| F-13 | imprecise | Deck p.5, notes | "the 1% parties of five **forced** the XL rule" | The XL rule comes from the user's operational correction (D-33). The 1% is only the assumed potential XL demand (correction 2). | "parties of five, 1% in our distribution, travel by XL if transferred (D-33)" |
| F-14 | imprecise | Script, Slide 10 | "One rule dominates another if it **serves** at least as many riders…" | Service S is the share of *requests reached by a vehicle within 15 min* (curb arrival), not riders served (tradeoff.md; D-50(2)). | "…if it reaches at least as many requests within 15 minutes with no more Lyft bookings…". The same applies to deck p.11 "reaches at least as many riders" (ok-but-note there, because "reaches" is correct). |
| F-15 | ok-but-note | Deck p.11, notes | "the two rules that read predicted pickups reach about **74–75%**" | 0.735 and 0.750 (tradeoff.md). B5 rounds R2(15) to 0.73. | "about 73–75%" or "about three quarters" |
| F-16 | ok-but-note | Deck p.10, Patience box | "about a third under the **predicted-wait rules**" | Correct for R2(15) (93/294 = 32%) and R3(2) (104/330 = 32%). However, R3(2) compares the van ETA with a Lyft, so it is not a "predicted-wait" rule. | "under the two rules that read predicted pickups" (the wording in the notes and the script) |
| F-17 | ok-but-note | Deck p.10; script Slide 9 | "95 of 196 **riders** transferred" | 196 counts transferred *requests*. Parties can be larger than 1. | "95 of 196 transferred requests" |
| F-18 | ok-but-note | Deck p.22 (B8) | "Run time **per night**: mean 32 s, longest 253 s" | The mean is over the 180 *runs*: (43.5+39.6+49.0+49.8+4.7+3.7)/6 = 31.7 s, with a maximum of 252.9 s. | "Run time per run" |
| F-19 | ok-but-note | Deck p.9; script Slide 8; explanations Slide 8 | "151,710 plan combinations…; the MILP's choice matched on every epoch" | Correct. However, 151,710 is the 46-epoch L4 R0 run under the *original* pending price (and the M1 reference). Under the current default A, the check covered 45 epochs and 140,471 combinations, which also matched (d53 review §4). | Optional: "151,710 (and 140,471 under the current price A)" |
| F-20 | ok-but-note | Deck p.9; script Slide 8 | "253 automated tests" for "how we know the simulator does what we say" | 253 collected. Of these, 46 test scenario generation (test_scenario 32, test_scenario_v2 8, test_spread 6), so 207 test the simulator. The independent count of 168 is exact (101 + 38 + 29). | Optional: "253 automated tests across scenario building and simulation" |
| F-21 | ok-but-note | Explanations, Slide 7 | "Independent review…, with **29** tests" | `test_pending_price_independent.py` now collects 29 tests. D-53 update 2 recorded 28 at the time. | Fine as a current count. Note the difference if asked. |
| F-22 | ok-but-note | Deck p.19 (B5), "Lyft bookings" row | Source given as summary.md | summary.md splits standard and XL bookings (e.g. R3(2) 10.4 + 0.07). The deck row is the *total* (10.5 (1.9)), which appears in tradeoff.md and per_night_metrics.csv. | Add "tradeoff.md" to the source line, or label the row "Lyft bookings (standard + XL)" |
| F-23 | ok-but-note | Deck p.5 (ASSUMED box) | "their share of 'Canceled' is a 50–75% range" | This is a provisional *sensitivity* range for later calibration. It is not established by data and is not exhaustive (D-39, D-49(4)). The placeholder patience is not yet calibrated to it. | "…is treated as a 50–75% sensitivity range" |
| F-24 | ok-but-note | Deck p.13 and explanations Slide 12 | "paired intervals on the saved 30 nights" as the next step | The spec calls L5 a "dress rehearsal… too small for conclusions" (§8). D-57 excluded intervals and power claims, and D-50(3) puts the power pilot outside the main seeds. | Add "as a rehearsal of the analysis" so that the intervals are not read as evidence for the research question |
| F-25 | ok-but-note | Script, Slide 2 | "the 20- and 25-minute targets are from **today's** web page" | The live page was read on 21 Oct 2026 (D-49(1)). | "from the live page as read on 21 October" |
| F-26 | ok-but-note | Script, Slide 4 | "1.386 riders per booking" | 1.386 = van passengers ÷ completed van bookings (33,394 / 24,095). The same sentence names the denominator, so it is acceptable, but the shorthand drops "completed van". | "1.386 van passengers per completed van booking" |
| F-27 | ok-but-note | Deck p.4 (OBSERVED cell) | "27.6 vehicles on duty" | This is the "All services" average over 29 days (obs_p06 = 27.556; D-49(3)). The slide does not show the qualifier, although p.3 says "28 vans counted all services". | "27.6 vehicles on duty (all services)" |
| F-28 | ok-but-note | Explanations, Slide 6 | H "including the 30-s boarding dwell", then the worked example | The methodology's worked example is labelled "dwell omitted for clarity". The explanations' example omits dwell silently. | Add "(dwell omitted)" to the example |
| F-29 | ok-but-note | Explanations, Slide 1 | The proposal deck "stays unchanged" | The session's opening git status lists `docs/presentations/BlueJayNightRide_Proposal.pptx` as modified in the working tree. I did not inspect the change (no git, by instruction). Its current text still reads "5,100 rides per hour", "28 vans" and "1 in 4 trips". | The team should confirm that the modification is intended, or restore the file |
| F-30 | ok-but-note | Deck p.3 (corrections box) | Three corrected proposal numbers | Methodology §1a also corrects "1 in 4 trips overflow to Lyft" (it is a share of riders). The deck handles this on p.2 but does not list it as a correction. | Optional fourth bullet |
| F-31 | ok-but-note | Script, transition to Slide 11; explanations, Slide 11 | "Our professor asked about leader–follower models" | No repository source records the request. I could not verify it. | Keep if the team confirms it |

## Claims verified OK

**April data and derivations.** Recomputed from `obs_p06`–`obs_p09` and checked against D-35/D-36/D-49 and methodology §1a, §4 and App. B–C.
- R/C = 50,297 / 24,095 = 2.087. Requests = Completed + Canceled + No-show with Denied read as 0, which is stated in the spec. The digitized Denied total is about 99.
- 6 pm completed rides: digitized 5,089, tooltip 5,098, so about 170 per evening and 355 requests.
- V₁₈ = 27.556, which gives ρ = 12.85 / 10.10 / 10.71.
- 5 × ρ = 64.25 / 50.48 / 53.55. The total rounds to 168. Largest-remainder rounding gives 64 / 50 / 54.
- Range: 168 / 0.8 ≈ 210, 168 / 0.65 ≈ 258, 168 × 0.9 ≈ 151. That supports "~150–260, illustrative, not a CI".
- Canceled = 23,843 (47.4%).
- No-shows: 2,359 / 50,297 = 4.7%, and 2,359 / 26,454 = 8.9%, conditional on the status mapping (D-48).
- Passengers 33,394 / 24,095 = 1.386. Assumed distribution mean = 1.405.
- 44,374 riders, 24.5% by Lyft, as a share of riders.
- Parties of five ≈ 1.7 per 168-request evening.
- Lognormal σ = 0.49.
- 28 requests ÷ 2 vans = 14 per van-hour.

**Proposal and dates.**
- The proposal pptx says "5,100 rides per hour", "about 28 vans", targets 20 (25 busy) and 25, "Lyft as paid overflow", service promises as constraints, replay of real nights from trip-level extracts, and greedy / MILP / hybrid.
- Course and team name are correct.
- Target wording: the 15/20/20 captures run from 20 Apr 2024 to 22 Jul 2026; the live page read on 21 Oct 2026 says 20/25/25.

**Model.**
- φ slopes and breakpoints.
- φ(5, 10, 15, 20) = 5 / 17.5 / 42.5 / 92.5.
- φ(10) − φ(9) = 2.5 > 2.
- β = 0.5 and γ = 0.1.
- Guardrail max(25, 2·direct + 5).
- Route A = 52.5 + 13.0 + 1.0 = **66.5**; Route B = 67.5 + 12.5 + 1.0 = **81.0**.
- K = 3 and the candidate rule, including the free reordering of existing riders.
- The M bound and the "fewest pending requests for proven-optimal solutions" claim.
- The definitions of A and B, the z constraints, and A's three stated exceptions (≤ 13 s on 3 of 35,344 pairs).
- HiGHS gaps and node limit.
- Same-second order (D-46).
- D-54 curb-wait convention.
- The van and Lyft multiplier of 1.2 in L5.

**Pending-price table (p.8).** All values match D-53 update 2 and `d53_comparison.md`:
- waits 17.1/31.0/44.4, 18.6/31.2/35.6 and 21.1/34.3/38.6;
- means 18.8, 18.8 and 21.8;
- R002 waits 22:18, 19:28 and 20:39;
- 0, 0 and 9,828 extra variables (see F-06);
- 0.10, 0.10 and 4.8 s;
- about 135,100 variables, and 19.6 s versus 3.0 s, in the five-van epoch;
- R009 waits 9:48 and 35:34.

The approval is stated as provisional, with the reasons not resting on R002.

**L4, M2 and the R011 timeline.**
- R011 was requested at 18:16:30. The plan's ETA was 18:35:20, a predicted wait of 18:50, which exceeds 15. It was transferred at 18:20, booked at 18:22, the Lyft arrived at 18:30 (a wait of 13:30) and dropped the rider at 18:33:25.
- L4 has 16 requests and vans from 18:15.
- R1u(10) did not fire after 18:15 on L4, because C assigned every request within about 4 minutes.
- Hand key: 22 transfers (4 of them XL) and 4 declines over the five rules before 18:15 (handcheck.csv; Phase 4 log).
- L1–L3 are reproduced "to the second".
- 151,710 combinations over the 46 L4 R0 epochs.
- 253 tests collected; 168 of them independent.

**L5 batch.** Recomputed from the per-run files.
- Transfer fates:

  | Rule | Transfers | Lyft completed | Lyft no-show | Cancelled in lag | Cancelled after booking |
  |---|---|---|---|---|---|
  | R1(10) | 196 | 94 | 7 | 18 | 77 |
  | R1(15) | 104 | 55 | 4 | 11 | 34 |
  | R1u(10) | 8 | 4 | 0 | 1 | 3 |
  | R2(15) | 294 | 187 | 14 | 14 | 79 |
  | R3(2) | 330 | 211 | 15 | 16 | 88 |

  Every row reconciles.
- 95 of 196 cancelled before the Lyft arrived. Under R2(15) and R3(2) the share is about 32%.
- R1u(10) made 8 transfers on 6 nights (r00, r08, r10 ×2, r13 ×2, r19, r27).
  - The requests came between 18:21:09 and 18:28:00, inside the 18:20–18:30 burst.
  - The transfers came between 18:35:14 and 18:38:00.
  - The K = 3 cap is logged as the pending reason in r00.
- Guardrail: 36 excesses, all attributed, the largest 149 s per no-show.
- 13,663 epochs, all main solves optimal.
- 41 incomplete tie searches. In all of them the enumeration found a unique optimum, which is the plan chosen.
- 180 of 180 runs pass, under one code fingerprint.
- Every B5 cell matches summary.md, apart from the bookings total noted in F-22.
- Mean run time is 31.7 s and the longest is 252.9 s.
- Picked up: 16.1 of 28 under R0 and 20.2 under R2(15).

**Trade-off.**
- Means (S, B):

  | Rule | S | B |
  |---|---|---|
  | R0 | 0.477 | 0 |
  | R1(10) | 0.514 | 5.93 |
  | R1(15) | 0.495 | 3.10 |
  | R1u(10) | 0.476 | 0.23 |
  | R2(15) | 0.735 | 9.33 |
  | R3(2) | 0.750 | 10.47 |

- Nondominated on the means: R0, R1(10), R1(15), R2(15) and R3(2). R1u(10) is dominated by R0. The same holds with van-km added.
- Nights nondominated: 30 / 11 / 14 / 26 / 24 / 12.
- Nights identical to R0: 30 / 0 / 1 / 24 / 0 / 0.
- Nights above / below R0: 0/0, 19/6, 15/5, 2/2, 30/0, 30/0.

All of these were recomputed and match B6 and tradeoff.md.

**Wording safeguards (a)–(l).** All are satisfied:
- (a) R1u(10): L4 and L5 are kept separate.
- (b) Guardrail excesses are called "attribution… consistent with timing, not a proof" in the notes, the script, the explanations and the methodology.
- (c) Gravity prior with a chosen decay; "the data cannot tell us the decay rate".
- (d) 8.9% is conditional on the status mapping.
- (e) 1.386 is van passengers per completed van booking.
- (f) "30 synthetic nights… not 180 independent nights".
- (g) The two-van pilot is distinguished from the five-van evening, which is not run.
- (h) Cancellation after transfer and the denominators of the wait percentiles are explained.
- (i) No winner; D-50 is provisional; nondominated ≠ recommended; not a frontier.
- (j) Leader–follower is a possible extension, not implemented and not impossible, with no claim that the hierarchy reduces to one level.
- (k) "Optimal" means over the candidates generated at that epoch, with at most 3 new pickups.
- (l) Points are not money.

**References.** The following are correctly attributed:
- Colson, Marcotte & Savard (2007), *Annals of Operations Research* 153;
- Dempe (2002), *Foundations of Bilevel Programming*;
- von Stackelberg (1934).

**Timing.** The script's segments sum to 18 min 30 s after the 10-s title.
