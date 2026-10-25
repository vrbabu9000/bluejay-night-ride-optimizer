# Design review: evidence and scenario methodology (21 Oct 2026)

**Reviewer scope.** Are the derivations, assumptions, source dates and decision provenance in `scenario_spec.md` v0.3 and `decision_log.md` (D-01 to D-44) correct and honestly labelled? Read-only review; no repo file other than this note was changed. No simulator exists, so nothing here concerns simulator behaviour.

**Method.** Recomputed every number in item 1 from `obs_p06_vehicles.csv`, `obs_p07_status.csv`, `obs_p09_rides_by_hour.csv` (pandas). Checked service-target wording against Wayback snapshots (CDX listing plus 16 distinct snapshot fetches, 6 s apart; one script, no rate-limit problems). The live JHU page could not be fetched (HTTP 403 to both urllib and WebFetch).

**Classes.** R = resolved (checked, correct as written); T = transparent base assumption (fine, needs only the label noted); S = deferred sensitivity; B = genuine implementation blocker (must change before Phase 4 or L6 generation).

## Summary

| # | Finding | Class | Where |
|---|---|---|---|
| E-01 | Volume arithmetic reproduces exactly (168 constant, 162 taper) | R | spec §3.2, D-35, D-36 |
| E-02 | Stale scenario counts after D-36/D-37 (6-van count is ambiguous: 168, ~195 or 202) | **B (L6 only)** | spec §0, §3.1, §3.2, §9.1, §11 |
| E-03 | 29-day vs 30-day vehicle denominator is an unlisted -3% effect on N | S | spec §3.2 |
| E-04 | "145–205" range does not span the project's own 18–27.6 vehicle range (about 250) | S, wording | spec §3.2, trail §2 |
| E-05 | "Fewer vans than Hopkins runs, ~20+ vans" stated as fact | wording | spec §3.1 |
| E-06 | Request-hour reading (P-12) is still a proposal but is the base | T, label | D-35, spec §3.2 |
| E-07 | No-show denominators are correct in the new text; frozen artifacts and generator still carry the wrong 0.047 and a "DERIVED" label | **B (small)** | `generator_v2.py`, 64 `scenario.json`, spec §12 |
| E-08 | Calibration pins p_van mechanically at about 8.9%; "jointly with patience" is a misdescription; what is and is not identifiable | T / wording | D-40, trail §8, spec §3.3, §12 |
| E-09 | 50–75% patience share is labelled a sensitivity range almost everywhere; one stale "two thirds", one tension with T02 | wording | research_review AS-09, spec §12, T02 |
| E-10 | The 23–46% Lyft hand-off range is traceable only to `transloc_operations.md`; it is an assumption-conditioned range | T, label | D-39, trail §7, research_review AS-10 |
| E-11 | Party sizes 1.386 and 1.405 are kept distinct in the docs; frozen label and a few phrases blur them | T / wording | spec §3.3, trail §6, `generator_v2.py` LABELS |
| E-12 | Geography: completed-ride margins under-weight exactly the long trips Lyft rules target; β_geo and the ride-time band interact | T / S | spec §3.3, D-18, D-34 |
| E-13 | Service targets: 15/20/20 for April 2026 is supported as published page wording; "Apr 2024" is a capture bound; 20/25/25 on 21 Oct is unverified | R with corrections | D-04, D-29, evidence note, research_review §4.3 |
| E-14 | Financial content remains (D-44, trail §10, D-33/D-43 fee and price language) | remove | decision log, t07.md |
| E-15 | Proposed validation described in present tense; label "hand check" for generator-computed answer keys | wording | spec §8, §12, trail |

Blockers: E-02 (before generating L6) and E-07 (before any simulator reads `scenario.json`). Everything else is wording, labels or sensitivity-list additions.

---

## 1. Request volume (E-01 to E-06)

### E-01 Recomputation: R

From the three CSVs (readings, not tooltip values):

| Quantity | Documented | Recomputed |
|---|---|---|
| Completed C / Canceled / No Show | 24,095 / 23,842 / 2,359 | 24,095.1 / 23,842.3 / 2,359.2 |
| R = C + Canceled + No Show (Denied = 0) | 50,297 | 50,296.6 |
| R / C | 2.087 | 2.0874 (2.0915 if the raw Denied offset of 99 is kept) |
| ρ at 18 / 19 / 20 h | 12.85 / 10.10 / 10.71 | 12.850 / 10.097 / 10.711 |
| 5 constant vans, unrounded | 64.2 / 50.5 / 53.6 | 64.25 / 50.48 / 53.56 (sum 168.29) |
| Largest-remainder | 64 / 50 / 54 = 168 | floors 64/50/53 = 167, leftover 1 goes to .56 → 64/50/54 = 168. Correct |
| April taper (v = 5, 4.948, 4.459) | 64 / 50 / 48 = 162 | 64.25 / 49.96 / 47.77 → floors 160, leftover 2 to .96 and .77 → 64/50/48 = 162. Correct |
| Night average load | about 11 per van-hour; 13 at 6 pm | 10.96 (eight hours with both series); 12.85 |
| Night totals at 5 vans, taper | about 304 | 303 |
| Night totals at 6 vans, taper | about 365 | 364 |
| Completed per van-hour | 5.1; 6.2 at 6 pm | 24,016/30 ÷ 157.0 vehicle-hours = 5.10; 6.16 |
| Tooltip anchor (5,098 instead of 5,089 read) | not stated | ρ18 = 12.87, N18 = 64.4, still 64 |

Units: C_h is a 30-day sum, divided by 30 to get completed rides per night; V_h is a per-hour mean number of vehicles; ρ_h is requests per vehicle per hour; N_h = ρ_h × v_h is requests per scenario hour. All consistent. One small point: R/C uses p07's 24,095 while C_h comes from p09 (sum 24,016, 0.33% lower); the effect is 0.3% and is below the reading noise.

### E-02 Stale counts after D-36 and D-37: B (before generating L6)

The decision log is internally correct (D-36: constant 5 vans, 168; D-37: the sixth van is tested on the same 168 requests). The spec body was not fully updated:

- §0 "How the base scenario is built" step 1 still says vans taper "through the night"; step 2 lists "~64, ~162 for 18:00–21:00 and ~304" (the taper count) as the base, and "At 6 vans: ~77, ~195 and ~365", which is demand scaled with the fleet (the reading D-37 set aside).
- §3.1 describes only the taper; §9.1 has "fleet level 5, 6 vans" without saying the request set is the same.
- A **constant** six-van scaled count, the case a reader of D-36 would expect, is 77.1 / 60.6 / 64.3 = **202** (77/61/64). It appears nowhere. The documented "~195" is the six-van *taper* count (77/60/57).
- D-36 also has vans staying on duty after 21:00 "until the remaining work is resolved", whereas April's fleet falls from 24.6 (20:00) to 19.4 (21:00) and the spec's §3.1 shift-end rule says "no new pickups after the van's end". The L6 post-21:00 tail therefore runs with a full fleet, which makes tail waits optimistic relative to April. This is a decided simplification, but it is not listed among the limitations.

Consequence: a generator written from the spec text could produce 162, 168, 195 or 202 requests for L6. Resolution: edit §0 steps 1–2, §3.1 and §9.1 to say "L6 base: 5 vans constant, 168 requests (D-36); the 6-van cell uses the same 168 (D-37); scaled-with-fleet counts (taper 162/195, constant 168/202) are a separate later experiment"; add the post-21:00 full-fleet tail to the limitations.

### E-03 29-day vs 30-day vehicle average: S

p06 averages vehicles over 29 days; p09 sums rides over 30 days. The formula divides rides by 30 and uses the 29-day vehicle mean unchanged. If both quantities should cover the same days (29), ρ falls 3.4% (12.42 / 9.76 / 10.35) and the constant-5 count falls to about 163 (62 / 49 / 52). If the missing day is a zero day inside the 29-day mean, the vehicle level is under-stated and the count moves the other way. Neither is in the spec, the trail, or the sensitivity list; only the p06 brief and T10 mention it. Add it to the "Limitations" row of trail §2 and to the sensitivity range.

### E-04 The "145–205" illustrative range: S, wording

It is correctly labelled "not a confidence interval". But its construction (vehicles 22–25 instead of 27.6; up to 10% rebookings) does not match the project's own uncertainty: research_review §4.4 and AS-14 give Homewood availability as "about 18–27.6 vans". At 18 vans the 162-request taper count becomes about 248 (constant: about 257). The 22–25 values are the very "22" that research_review downgraded to a hypothesis. Resolution: restate as "if the Homewood share of the 'All services' vehicle count is anywhere between 18/27.6 and 1, N rises to about 250; rebookings can lower it by roughly 10%; no probability is attached".

### E-05 "Fewer vans than Hopkins runs": wording

Spec §3.1 says the scaled system is chosen "rather than simulating ~20+ vans". The only support is the "All services" vehicle chart (27.6 at 18:00), which AS-14 and research_review §4.4 classify as mixed-service and "partly contradicted". Rephrase: "April's dashboard shows up to 27.6 vehicles at 6 pm across all services; the Homewood-only number is unknown." Same for "Hopkins runs" in D-30's basis.

### E-06 Request-hour reading: T, label

D-35 and spec §3.2 treat p09 as the request-hour shape. In the decision log this is still **P-12, "Still proposals"**, and the p09 brief says the chart "does not say whether the hour is the request, pickup or completion time". It is a defensible assumption (a 2 am bar of at most 29 rides while requests are honoured to 2 am favours request hour), but the D-35 row and the trail §2 "Assumptions" row should list it as ASSUMED with the AS-25 evidence. Also add "R/C is the same in every hour" (already in trail §2, not in the spec). If hours are completion hours, the 18:00 bar loses the first minutes of service and the hourly shape shifts earlier than assumed.

---

## 2. No-show (E-07, E-08)

### E-07 Wrong denominator survives in code and frozen artifacts: B (small)

Correctly conditioned: D-40 ("conditional on reaching the arrival event"), trail §8 ("4.7% of all recorded requests"; "~8.9% per arrival under stated assumptions", 2,359 / 26,454 = 0.0892, daily range 6.2–11.0%, recomputed and correct; 4.7% daily range 2.8–6.4% also correct), spec §3.3 table.

Not corrected:
- `src/scenario/generator_v2.py` line 52 `P_NOSHOW = 0.047` and `LABELS["noshow"] = "DERIVED rate 4.7% (April p07)"`. All 64 frozen `scenario.json` files (34 in `v2/`, 30 in `v2_dispersed/`) carry that label; the L1 and L5 files also carry `"p_noshow": 0.047` in `params`. The label is wrong twice: the number is not applicable "at arrival", and it is a share of all requests, not a derived per-arrival rate.
- The files are hash-frozen (`FROZEN_v2.json`), so they should not be edited.
- spec §12 bands say "no-show ≈ 4.7%" without "of all recorded requests". research_review §7 ("no-shows (~4.7%)") and AS-12 ("Supported (rate)") also omit the denominator. `transloc_operations.md` AS-12 reads "4.7% of requests no-show, independent of wait", which is at least denominated.
- `tests/test_scenario_v2.py:67` and the L2 text in `build_levels_v2.py` use `noshow_u < 0.047` for designated no-shows. This is harmless (the designated draws are 0.0), but it reads as the threshold.

Consequence: a Phase 4 reader that takes `p_noshow` from `scenario.json` would silently apply 4.7% per arrival. Resolution: (i) add `data/scenarios/v2/ERRATA.md` (not hashed) stating that `p_noshow` and the "DERIVED" label in `scenario.json` are superseded by D-40/D-41 and that thresholds come from the policy/calibration file; (ii) the simulator must ignore `params.p_noshow`; (iii) in the next generator version rename to `P_NOSHOW_REQUEST_SHARE_APRIL` with label "OBSERVED share of recorded requests; not a per-arrival probability", and write `p_noshow_*` only in a calibration output; (iv) add "of all recorded requests" to spec §12, research_review §7 and AS-12.

### E-08 What calibration can and cannot say about no-show: T / wording

1. **Within the model, the band pins p_van almost mechanically.** Under the §5 dashboard mapping (Completed = van-completed; patience ends at vehicle arrival; no cancellation after arrival), the van arrivals in the simulator are exactly van-completed plus van no-shows. If the simulator matches both April bands (completed ≈ 47.9% and no-show ≈ 4.7% of requests), then p_van = 4.7 / (47.9 + 4.7) ≈ 8.9%, whatever the patience scale is. So the docs' phrase "p_van is calibrated … jointly with patience" (D-40, trail §8) is a misdescription of the structure: patience moves the completed share, and p_van follows from the ratio of the two bands. "Not adopting ~8.9%" is really a decision about whether the §5 mapping is trusted; the calibration will return about 8.9% unless the mapping is changed. State this explicitly: the 8.9% is the model-implied value if the mapping holds, and the identified set should record the mapping as an assumption.
2. **What is not identified.** (a) p_lyft_standard and p_lyft_XL: no Lyft no-show data exist (D-41 equal thresholds are an assumption). (b) Whether the dashboard "No Show" includes Lyft no-shows (§5 defines the dashboard view only for Completed and Canceled; it omits No Show). Define which simulated no-shows (van only, or van plus Lyft) are compared to the 4.7% band. (c) Any link between waiting and no-show (D-42 q): the daily data cannot separate it. (d) Late boarding within the 3 min. (e) Whether "Completed" counts Lyft rides (p07 brief: unknown): if it does, the per-arrival rate changes.
3. **Patience is not identified jointly with these.** The three April shares sum to 100%, so they give two independent equations. Unknowns that move them: patience scale and shape, ρ, fleet level, travel multiplier, the status-quo Lyft rule threshold, the hand-off share inside "Canceled", rebooking and duplicates. Spec §12 correctly asks for an identified set; §12 knob list ("ρ, patience scale, travel multiplier, status-quo rule threshold") omits p_van, the share of rider cancellations, and the hand-off recording assumption. Add them.

---

## 3. Patience and the Lyft hand-off share (E-09, E-10)

### E-09 The 50–75% range: wording

Labelled a provisional sensitivity range, not a data interval, in spec §3.3 and §12, D-39, the P-08 row (annotated as superseded) and trail §7. Good. Issues:
- research_review AS-09 (line 196) still says "calibrated so rider cancellations are about two thirds of 'Canceled'" with no supersession note. Add "(superseded 21 Oct, D-39: provisional 50–75% range)".
- The trail says the range "brackets those uncertainties". It does not: it assumes hand-offs are recorded inside "Canceled". p07 brief and research_review §7 state that how a transfer is recorded, and whether "Completed" includes Lyft, is unknown. If transfers are recorded as Completed (or not at all), the rider share of "Canceled" could exceed 75%. The spec's §5 variant "Canceled = rider cancellations + transfers (variant without transfers)" covers this in principle; the sensitivity row for the rider share should name it.
- The endpoints are not a derivation: 100 − 46 = 54 and 100 − 23 = 77, not 50 and 75. Describe 50–75% as a judgement-rounded range.
- T02 says "47% is a level to compare against, not a calibration target … would overstate abandonment if rebookings are common", and the simulator has no rebooking. Spec §12 nevertheless lists "Canceled ≈ 47% pooled" as a calibration band. Reconcile: the 47% band should be compared only on the dashboard-view mapping, with the rider-cancel component calibrated to the 50–75% range of it and the rest (transfers) coming from the Lyft rule; state that duplicates inflate April's 47% and the simulator cannot reproduce them.
- Informal plausibility check (not evidence, survivor-biased): a Weibull(1.5, median 18 min) against lognormal waits through April's median/P90 (10.5/18.0 min) gives about 29% of requests cancelling (36.7% with the Apr 17 waits), inside the implied target of 23.7–35.6% (50–75% of 47.4%). The D-21 exponential reproduces its quoted 46.6% (my 46.5%). So the placeholder is not obviously inconsistent, but this is a consistency check on a placeholder, not a calibration.

### E-10 The 23–46% hand-off share: T, label

The number is not derived anywhere in the decision log or spec. The only source is `transloc_operations.md` (line 55: "roughly a third … about 260 of 795 a day; plausible range 23–46%, depending on Lyft party size", INFERRED). I reconstructed it:

- 10,821 Lyft riders (T07, p10) over 30 days = 361 a day; 23,842 Canceled = 795 a day.
- Divide Lyft riders by an assumed passengers-per-Lyft-booking: 1.0 → 45.4% (the "46"); 1.386 (the van mean) → 32.7% (the "third", 260/795); 2.0 → 22.7% (the "23").

Hence the range is "if the average Lyft party is 1 to 2" under the assumption that **every Lyft trip is the product of a "Canceled" request**. Lyft party sizes are not observed (T07: p10 is a different system, populations matched by date only; "neither number is a conversion rate"). The upper party size of 2.0 has no support, and there is no data-based lower or upper bound. The same "46%" also appears as an unrelated number: the maximum daily Lyft rider share (46.3% on Apr 17) in the calibration bands. A reader can confuse "Lyft share of riders 10–46%" with "hand-off share of Canceled 23–46%".

Resolution: add a one-line trace to D-39 and trail §7 ("Lyft riders/day ÷ assumed riders per Lyft booking ÷ Canceled/day; party 1.0–2.0; assumes all Lyft trips arise from Canceled"), and call it an "assumption-conditioned range", not an estimate.

---

## 4. Party sizes (E-11): T / wording

Kept distinct: spec §3.3 ("assumed … 1.405 … April's derived 1.386 … different quantities"), D-38, correction 1 in the decision log. Recomputed: .73 + 2(.18) + 3(.055) + 4(.025) + 5(.01) = 1.405; 1% of 168 requests = 1.68 parties of five per night, correctly stated as "≈1.7".

Remaining blur:
- Every frozen `scenario.json` label reads "mean DERIVED (April 1.39); shape ASSUMED". The generated mean is the assumed 1.405, 1.4% above the derived mean. T04's reading intervals: 1.382–1.390 (independent errors), 1.363–1.410 (all aligned). 1.405 is outside the first and inside the second. Describe as "assumed, within worst-case reading error".
- 1.386 is passengers per **completed** booking and assumes p07 Completed counts van rides only (T04 caveat; if Completed includes Lyft rides, the van ratio is higher). The base applies it to all requests, including cancelled ones whose party size is unobserved. The spec does not state this extension.
- The 1% share of parties of five is entirely assumed; T04 says even the existence of groups of four is not identified by a mean. Trail §6 says "About 1% of bookings are parties of five" without an ASSUMED tag; the spec has it. AS-16 ("Party size: Supported … max 5") overstates what the data say about shape and maximum.
- The D-08 row still lists the older shape (.72/.19/.06/.03, mean 1.40) next to the new one in D-38. Not an error; a pointer would help.

---

## 5. Geography (E-12): T / S

- **Margins.** D-01 holds: city maps sum to 24,056 (O) and 24,057 (D) against p09 24,016 and p07 24,095, inside reading error (re-checked from the CSVs). The margins describe completed rides.
- **Completed-ride margins as request margins** (trail §5 Assumptions) is stated, but its direction of bias is not: if long or Peabody/downtown trips cancel or move to Lyft more often than short ones, completed-ride margins under-weight exactly the trips on which the Lyft rules are most useful. The far-trip pattern (destination probability doubled) partly covers this. Say so in spec §3.3 and list a "request geography ≠ completed geography" sensitivity.
- **Gravity × IPF, β_geo = 0.1.** Labelled ASSUMED and provisional (D-18, trail §5). Reproducing the margins to 1e-10 holds for every β, so it is a consistency check by construction. D-18's basis "T6 brackets β" overstates T6: T6 shows three pairings and says the O-D pairing is not identified. However, β_geo is not irrelevant to calibration: T6 shows gravity shortens direct times and raises the detour ratios, so the spec §12 ride-time band (P90 ≈ 24 min) is jointly affected by β_geo, the travel multiplier and pooling. Add β_geo to the nuisance parameters whose set is reported in the identified set, or state that it is held at 0.1 for all calibration.
- **Dispersed variant.** Trail §4 and correction 5 correctly say the six tests establish consistency (weights, road snapping, routing completeness, alignment), not realism; the 400 m radius, six satellites, equal weights and the hull region are assumptions. Fine. One more point: D-27 says "as April was operated", but what is documented is only that the April maps contain Peabody and downtown bubbles (research_review §4.2: the 2023 page mentions Peabody, the 2023–2026 pages do not). The 188 points reach Inner Harbor and Penn Station, beyond the 2023 description (20th St / Guilford–South St / Pratt St / Howard St). Label the boundary INFERRED from map bubbles, not a documented service area.
- D-09's margin scaling (O ×1.020, D ×0.986) is an ASSUMED rule affecting margins by up to 2%; it is not repeated in the spec's geography section.

---

## 6. Service targets with dates (E-13)

Verified against Wayback (`jhfre.jhu.edu/ts/transportation/shuttle-services/`, text of the "What to Expect" sentence; format pickup / ride / busy-time arrival):

| Capture (UTC) | Reads |
|---|---|
| 26 Aug 2023, 24 Oct 2023, 19 Jan 2024, 3 Mar 2024 | 10 / 20 / 15 |
| 20 Apr 2024, 29 May 2024, 14 Jan 2025, 24 Apr 2025, 1 May 2025, 6 Oct 2025, 9 Jan 2026, 29 Jan 2026, 17 Feb 2026 | 15 / 20 / 20 |
| **30 Apr 2026 04:41 and 09:44** (both captures) | 15 / 20 / 20 |
| 22 Jul 2026 (last capture in the archive) | 15 / 20 / 20 |
| 21 Oct 2026 (live page) | **not verifiable by me**: live page returns 403 to urllib and WebFetch; no Wayback capture exists after 22 Jul 2026 |

Also confirmed in the 22 Jul 2026 capture: the van "will wait up to three minutes", the Lyft driver "will wait no more than three minutes upon arrival" (D-40 source correct), and the block is not labelled Homewood (existing caveat).

Assessment:
- "Captures from Apr 2024 to Jul 2026 read 15/20/20, covering April 2026": supported. I read 12 of the roughly 100 archived captures in that span (200-status rows in the CDX list); all were identical in this sentence.
- "April 2026's policy was 15/20/20": supported only as *the published page wording in April 2026* (two captures on 30 Apr 2026, the Feb 2026 capture before, the Jul 2026 capture after). The archive cannot show the operating target or the software setting, and the sentence sits in the general Blue Jay Shuttle block, not under Homewood. Keep the three-layer language of research_review §4.3. Say "published wording", not "policy".
- Change date: the docs say "from Apr 2024" and D-04 says "changed from 10/20/15 in Apr 2024". The evidence is that the last 10/20/15 capture is 3 Mar 2024 and the first 15/20/20 capture is 20 Apr 2024, with no capture between them. The change happened in that window (March or April 2024); "from Apr 2024" is the first capture date. Likewise "Aug 2023–Mar 2024" is the capture span; the 10/20/15 wording may begin earlier (earlier captures were not examined).
- The 20/25/25 reading on 21 Oct 2026 exists only in the decision-log evidence note. No source file, extract or hash is in the repo or the source index (`transloc_sources/INDEX.md` stops at 2 Oct retrievals). Treat it as an unverified team observation. Save a dated text extract or screenshot of the live page in `docs/evidence/context/transloc_sources/` and cite it. The same "block not labelled Homewood" caveat applies to the 20/25/25 reading.
- D-04's row (12 Oct) still says "20/25 are East Baltimore figures", which now sits uneasily next to the 21 Oct note that the page states 20/25/25 for the shuttle block. Add a cross-reference.
- Using 15/20/20 as reporting thresholds (D-29) with a 20/25 sensitivity is reasonable: T.

---

## 7. Financial and cost statements (E-14): remove

The team dropped financial modelling. Remaining content:
- **D-44** (Lyft cost ledger): categories "rider-cancellation fees; no-show fees; driver-cancel (no charge by assumption); pending estimated commitments; estimated expenditure"; "labelled price scenarios"; "illustrations"; alternative "dollars into the MILP objective (deferred)". Section heading "no-shows, Lyft service, cost reporting".
- **Trail §10** "Lyft cost reporting": "dollars appear only under labelled price scenarios"; "What would ground the dollars: Hopkins Lyft invoices … quotes".
- **D-33 and spec §6**: "no surcharge", "XL … cost are unknown"; trail §6 "no cost difference"; trail §9 "fees"; D-43 "Lyft driver help (no-show fee …)" and the Lyft Concierge note.
- **t07.md** "Used by": "the cost story (A9 item 4 … dollars only as an ASSUMED-price illustration)".
- **`model_design.md`** lines 219 and 261 (outside my list, found by grep): "Dollar costs appear only as labelled illustrations".
- `phase3/log.md` (D-44 row).
- Not found in scope: any explicit claim that Hopkins would save money (T07 itself bars "Hopkins will save x%"). Spec §9.3 item 6 ("Cost: Lyft trips and Lyft km per minute of P90-wait reduction") and §0/§3.4 "cost" are trip and kilometre counts; they are resource use, not money.

Recommended resolution: mark D-44 "Withdrawn 21 Oct: financial modelling dropped"; replace with a **trip-count ledger** (offers, bookings, completed trips, rider cancellations, no-shows, standard vs XL) and no price, fee or expenditure fields; delete trail §10 or retitle "Lyft resource use (trip counts and km)"; rename the spec's "Cost" to "Resource use"; strike the dollar sentence in t07 and model_design; drop the "no surcharge/cost difference" phrasing in favour of "XL availability and pickup delay unknown". A grep of the Team Technical Guide and the proposal deck for "cost", "$" and "save" is advisable (out of scope here).

---

## 8. Assumptions described as measured; scenarios as runs; validation as done (E-15)

Mostly honest. Items to fix:
1. **Frozen label "DERIVED rate 4.7%"** (E-07) calls an observed share, applied in the wrong place, DERIVED.
2. **Spec §8 L1 row** says "Checked by hand: every pickup and drop-off time computed in a spreadsheet and by the exact solver", and §12 lists "L1 hand schedule exact to the second". No spreadsheet check or exact solver exists. What exists: answer keys written by `generator_v2.py` (the same code that makes the inputs) and re-computed from the matrix by `tests/test_scenario_v2.py`. This is a consistency check of the key, not a hand or independent check, and the simulator is not built. Reword: "answer key generated and re-computed by tests; independent hand/spreadsheet check and exact-solver agreement still to do".
3. **Label of requests**: "SYNTHETIC from the April-calibrated demand model". Only the spatial margins and hourly shape are April-derived; volume is derived from an assumed vehicle denominator; times within an hour and the burst, far-trip and high-load patterns are design choices. "April-shaped" is more accurate than "April-calibrated"; nothing is calibrated until L7 exists.
4. **"Matched to April hour by hour"** (spec §3.2): a derived workload under the stated assumptions (D-36 says this correctly); the spec heading and §0 "the same load as April" read as matched demand. Prefer "April-derived workload per vehicle".
5. **Decision-log trail "Status: verified"** (dispersed variant, L4 key) is properly limited to internal consistency (correction 5). Good; keep.
6. **Not found**: any claim of simulator results, any outcome presented as a generated input. Scenario text consistently says outcomes are produced by the simulator (spec §1, §5). The statement "L1–L5 are generated" is true (64 scenario files exist, hashes in `FROZEN_v2.json`).
7. **Spec header** says the specification is "approved by the team" while D-35 is provisional and D-39 to D-44 are "not implemented". The body labels these correctly; the header could add "(parameters marked provisional remain so)".

---

## Recommended edit list (for the owner of each document)

1. Spec §0, §3.1, §9.1: one L6 rule (E-02). Add post-21:00 full-fleet tail to the limitations.
2. Spec §3.2: add 29/30-day effect; restate the range (E-03, E-04); list P-12 and constant R/C as ASSUMED (E-06).
3. Spec §3.1 and D-30: soften "Hopkins runs ~20+ vans" (E-05).
4. Spec §12 and research_review §7 / AS-12: "of all recorded requests"; define which simulated no-shows are compared; add p_van, rider share and hand-off recording to the knobs list (E-07, E-08).
5. `data/scenarios/v2/ERRATA.md` (new, unhashed) and simulator rule "ignore `params.p_noshow`" (E-07).
6. D-40 / trail §8: replace "calibrated jointly with patience" by the mechanical-implication statement (E-08).
7. D-39 / trail §7 / AS-09 / AS-10: trace the 23–46% range; say the 50–75% range does not cover transfers recorded as Completed; reconcile with T02 (E-09, E-10).
8. Trail §6 and frozen labels: party-size wording (E-11).
9. Spec §3.3 and D-27 / D-18: direction of bias from completed-ride geography; β_geo in the nuisance set; boundary INFERRED (E-12).
10. D-04, D-29, evidence note, research_review §4.3: "published wording", capture-bounded change date, store the 21 Oct page extract (E-13).
11. D-44, trail §10, t07, model_design, spec §9.3 wording: remove financial content (E-14).
12. Spec §8, §12 wording on validation status (E-15).

## What I could not verify
- The live JHU page on 21 Oct 2026 (20/25/25): HTTP 403; no archive capture.
- Archive captures not sampled (I fetched 16 distinct snapshots of the roughly 100 listed); captures before 26 Aug 2023.
- Whether the "Homewood" label applies to the "What to Expect" block (unchanged from the existing caveat).
- p10 and Lyft party sizes (no data); recorded status of Lyft transfers (not stated in the dashboard).
