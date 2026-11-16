# D-50 decision brief: how we will judge the transfer rules

Prepared 10 Nov 2026 for team approval. **Outcome (10 Nov): approved, with one change.** The primary measure uses **20 min**, with 15 min as the sensitivity check. Recommendations 2–6 were approved as written; see D-50 (approval) in the decision log. Once approved, it goes into the decision log as D-50 (approval) and into `preregistration_v2.md`.

## Why this decision comes first

Every result so far is descriptive. Before we can say "rule X is better" or "rule X is no worse", we need fixed rules for what counts as a real difference. These rules have to be set **before** we look at intervals. Otherwise we would be choosing the yardstick after seeing who wins. D-50 drafted these rules on 21 Oct, before the 30-night batch ran. This brief asks the team to approve them, fix two gaps, and add one missing piece.

## What D-50 already proposes (21 Oct, unchanged)

| Item | Proposal |
|---|---|
| Primary measure | Share of **all** requests not reached by a vehicle (van or Lyft) within 15 min. Riders who cancel count as not reached. |
| Secondary measure | Passenger P90 wait among riders who were picked up. Always read next to the primary measure, because it leaves out the riders who cancelled. |
| Resource measure | Lyft bookings per night (and van-km), reported next to the rider measure as a trade-off. No money. |
| Comparison | Paired differences across the same nights, 95% bootstrap intervals (10,000 resamples of nights). |
| Margins δ | 2 percentage points on the primary share; 1 min on P90 wait. |
| "No worse" | Upper 95% bound of (A − B) below +δ. "Better": upper bound below 0. A CI containing 0 means "can't tell", not "no worse". |
| Power target | Half-width at most 0.7 δ, otherwise 60 nights per cell. Pilot seeds outside the main 30. |

## What the saved L5 batch says about noise (variance only, no rule ranking)

From `outputs/sim/batch_L5_v1/per_night_metrics.csv`: the spread of the night-by-night **difference** between two rules, turned into the expected 95% half-width (≈ 1.96 · SD / √n). I deliberately did not compute or look at any interval for a rule effect.

| Pair (vs R0) | Primary share: half-width at 30 / 60 nights (pp) | P90 wait: half-width at 30 / 60 nights (min) |
|---|---|---|
| R1u(10) | 0.9 / 0.6 | 0.8 / 0.6 |
| R1(15) | 1.6 / 1.1 | 1.4 / 1.0 |
| R1(10) | 2.1 / 1.5 | 1.9 / 1.4 |
| R2(15) | 2.9 / 2.1 | 2.1 / 1.5 |
| R3(2) | 3.6 / 2.6 | 2.4 / 1.7 |

The target is 0.7 δ = **1.4 pp** and **0.7 min**. On L5, most pairs miss the target even at 60 nights.

**Why this does not settle the night count for the real experiment.** L5 has 2 vans and 28 requests, so one request is 3.6 pp of the night. That means the 2-pp margin is smaller than a single rider on L5. L6 has 168 requests (one request ≈ 0.6 pp), so a share is less noisy. If the noise were mostly the luck of individual riders, half-widths would shrink by about √6 ≈ 2.4×, and the worst pair would land near 1.5 pp at 30 nights. That is a rough guess and an ASSUMPTION. Only a small L6 pilot can answer it.

## Recommendations

1. **Primary measure: approve as drafted, at 15 min.** It counts every request, so a rule cannot look good by losing its longest waiters to cancellation. Known bias: it rewards early transfers (methodology §7a, mechanism 5). That is why it is always shown next to Lyft bookings and never on its own. Report 20 min (the live JHU target) as a sensitivity check, not a second primary.
2. **Margins: approve 2 pp and 1 min unchanged.** They were set before any results. Changing them now, after seeing the batch, is exactly what pre-registration exists to prevent. On L6, 2 pp is about 3 riders a night, and 1 min of P90 is noticeable to riders.
3. **Power rule: make the pilot L6, with a cap.** Run 10 L6 nights on seeds outside the main 30, for R0 and the noisiest rule (R3(2)). If the 30-night half-width would exceed 0.7 δ, use 60 nights. If 60 is still not enough, **stop at 60** and label the pair "underpowered at δ". Do not keep adding nights. The L5 batch stays as the rehearsal it was.
4. **Multiplicity (missing from the draft): keep the confirmatory set small.** Only H1–H3 are confirmatory, tested with **98.3% intervals** (Bonferroni over three). Everything else (all 15 rule pairs × conditions) is reported with 95% intervals and labelled exploratory.
5. **No single score (closes the "L and λ" item).** We will not combine service and Lyft use into one number with a weight. We report the frontier and the dominance rule only. The team does not have to pick a price for a Lyft ride, which D-45 already ruled out.
6. **First use: the L5 intervals as a rehearsal.** Once this is approved, compute the paired intervals on the saved L5 batch (no new simulation) to check that the pipeline works. Label them "pipeline rehearsal, 2 vans, placeholder behaviour". They are not evidence about the service.

## What this decision does not do

It does not rank any rule. It does not approve L6, M5 or calibration. It does not change the dispatcher or the objective.
