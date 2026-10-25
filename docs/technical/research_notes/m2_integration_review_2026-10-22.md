# Independent review: M2, Lyft rules with dispatcher C over the whole L4 evening (22 Oct 2026)

**In plain words.** I re-derived every M2 run from its own event log and epoch records, without trusting the engine's summaries, and **found no discrepancy**. On L4, under each of the six rules, no rider is ever in a van plan and in a Lyft state at the same time. Every request ends in exactly one outcome. Offers, accepted transfers, bookings and completions reconcile, separately for standard Lyft and XL. Every transfer follows the timing rules: the booking comes 2 min after the decision, the Lyft arrives after its delay, and the wait counts from the original request. At every epoch the rule fires on exactly the requests my own reading of the logged plan says it should. Every epoch was proven optimal, apart from two `empty` epochs with nothing to decide. Two separate runs are identical. Controlled cases, built by changing hidden rider traits in memory only, exercise the paths that L4 itself never reaches: a cancellation inside the lag, a cancellation after booking, Lyft no-shows (standard and XL), a van no-show while a rule is active, and both same-second ties. They all behave as the specification says. **What this does not show:** anything about which rule is better. It is one designed evening of 16 requests, and the counts below demonstrate mechanics only.

**Scope and method.** I read `src/sim/engine.py`, `dispatch.py` (interfaces), `lyft.py`, `run.py`, `m2_report.py` (uncommitted working copy), `scenario_spec.md` v0.6 §5, §6, §17 and decision rows D-43, D-45, D-46, D-52 (and its amendments), D-53 (approval) and D-54. I wrote one test file, `tests/test_m2_independent.py`. It trusts the implementation only to load the frozen scenario, build the policy (`run.policy_for`, evening window, pending price A, curb-wait D-54) and produce the logs. In one consistency check it also calls `dispatch.solve`. The test reads requests, latent traits, vans and the travel matrix from the frozen files itself. It restates the rule thresholds, state machine, same-second order, Lyft timing and counting identities from the specification, and does not import them from `sim.lyft` or `sim.engine`. A replay walks the event log and the epoch plans in execution order and keeps its own request states, van plans, headings and loads. All runs are in memory, in parallel worker processes; nothing is written to `data/` or `outputs/`. Scratch scripts are in `/private/tmp/claude-501/m2_review/`. I edited no other file.

**Command and result.** `.venv/bin/python -m pytest -q tests/test_m2_independent.py` → **101 passed in ≈ 40 s** (`-s` prints the findings table).

**Sensitivity (mutation check, scratch).** I injected faults into a copy of the R2(15) log, and each was caught: a transferred request put back into the executed plan (exclusion check), a booking 1 s late (timing), a transfer removed from the decision list (rule recomputation), an executed plan that differs from the departures (execution replay), and a declined rider read again by the rule (eligibility).

---

## Results per item

| # | Check (all rules, L4 evening, plus the controlled runs) | Verdict |
|---|---|---|
| 1 | No request is in a van plan, heading or seat while in `xfer_hold` / `lyft_booked` / `lyft_onboard`. Checked after every event and every epoch, and on both the plan the rule read and the executed plan. Only legal state transitions occur (§17.2) | **Pass** |
| 2 | Exactly one terminal state per request, which is also its last state. Offers (recomputed independently from the rule) = accepted + declined. Accepted = bookings + cancellations during the lag. Bookings = completions + Lyft no-shows + cancellations after booking + failures (0). These hold for standard and XL separately, and the per-request table agrees. A party of 5 is always one XL booking | **Pass** |
| 3 | Booking = decision + 120 s. Lyft curb arrival = booking + latent delay. Pickup = arrival. Drop-off = pickup + 30 s + t₀(o,d)·m_L. Wait = pickup − original request time. Every cancellation happens exactly at the deadline, and never after a vehicle reached the curb | **Pass** |
| 4 | At every epoch, the eligible set (pending, not committed, not declined before) equals the set the rule read. The logged reads (elapsed time, unassigned-since, predicted pickup) match my recomputation. The rule fires on exactly the recomputed set, and the consent split follows `consent_u` < 0.9. One epoch per second. Every transfer or decline row belongs to its epoch's own first-pass decision, so there are no same-second cascades. After a transfer, `chosen` excludes the transferred rider, and re-solving the logged post-transfer observation reproduces it. Without a transfer, `chosen` is the plan the rule read. Departures follow `chosen` stop by stop | **Pass** |
| 5 | Declined riders are never offered again or read again | **Pass** |
| 6 | Capacity (replayed load and planned load), precedence and commitment: every committed pickup is served by the committing van or ends in cancellation or no-show. Executed van rides stay within the guardrail. Departure legs match the matrix. Plan audit `pass` in every epoch | **Pass** |
| 7 | Solver: every epoch is `optimal`, except one `empty` epoch each under R2(15) and R3(2) (18:00, both riders transferred before any van existed; nothing to decide). Ties: one `tie` epoch in each Lyft rule run, resolved canonically | **All solves proven optimal** |
| 8 | Two runs of R1(10) in separate processes (different hash seeds): events, epoch records (excluding wall-clock fields) and outcomes are identical | **Pass** |
| 9 | Content hashes of L1–L4 and L5/r00 equal `FROZEN_v2.json`, both through `sim.inputs.content_hash` and through the same recipe restated | **Pass** |
| — | Extra: the files in `outputs/sim/L4_<rule>/` (read only), which `m2_report` reads, match the current code's in-memory runs for all six rules | **Pass** |

## Controlled cases (hidden traits changed in memory)

| Case | Setup | Result |
|---|---|---|
| (a) Cancel during the lag | R2(15); R015 deadline 18:21:00, decision 18:20 | `xfer_hold → cancel_after_transfer`; no booking, no Lyft event |
| (a′) Deadline = booking second | R011 deadline 18:22:00 = booking time | Patience (class 60) runs before booking (class 70): cancel, no booking |
| (b) Cancel after booking | R016 deadline 18:25, booked 18:22, Lyft due 18:30 | Booking counted; cancel at the deadline; Lyft arrives to no rider; no pickup or wait |
| (c) Lyft no-show | R012 (standard) and R002 (XL) absent | Booking counted; no-show 180 s after the Lyft arrival; no completion, no wait reported |
| (c′) Deadline = Lyft arrival | R001 deadline 18:10:00 = Lyft arrival | The arrival wins the tie: the rider boards and completes |
| Counts | the case above | 13 offers (12 accepted, 1 declined); 10 bookings (9 standard, 1 XL); 2 cancellations in the lag; 1 cancellation after booking; 2 Lyft no-shows (1 standard, 1 XL); 7 completions. **All five counts differ**, and `m2_report.row` reports them as different numbers. The van side (every van event and every executed plan) is identical to the unmodified run, because Lyft-side events never trigger an epoch |
| (d) Van no-show while a rule is active | R003 absent at V1's curb at 18:20:22, under R2(15) and R1(10) | During the timer (epoch 18:22), V1 shows `P_curb_wait` and the plan keeps the hypothetical drop-off D:R003, within the guardrail counted from expiry. The rule read other riders in that epoch. At expiry (18:23:22) an epoch with trigger `noshow` removes R003 from every plan. R003 is never boarded, dropped or offered, and V1 does not leave during the timer |
| (e) Transfer of an assigned, uncommitted request | Occurs on L4 itself: R1(15) at 18:15 transfers R001, the **first stop of idle V1** in the plan the rule read | The executed plan has no R001, and V1 never departs toward it. The same holds for every L4 transfer whose read came from a plan ETA (16 across the rules) |

## Findings (not failures; thresholds unchanged)

| Rule | Transfers before / at-or-after 18:15 | Declines | Outcomes (van / Lyft completed) |
|---|---|---|---|
| R0 | 0 / 0 | 0 | 16 / 0 |
| R1(10) | 3 / 4 | 1 (R003) | 9 / 7 |
| R1(15) | 0 / 5 | 1 | 11 / 5 |
| R1u(10) | 3 / **0** | 1 | 13 / 3 |
| R2(15) | 8 / 4 | 1 | 4 / 12 |
| R3(2) | 8 / 4 | 1 | 4 / 12 |

1. **R1u(10) transfers nobody after 18:15.** Once the vans are on duty, the longest continuous unassigned spell of any eligible request is 240 s (R016 at 18:24), well below 600 s. C puts every waiting request into some van's plan within 4 minutes, even when that van's pickup is far off, so the rule measures assignment, not waiting. This confirms the `m2_report` statement. Before 18:15 no van exists, so R1u(10) and R1(10) coincide (R001, R002, R004; R003 declines).
2. **Assignment-clock convention.** The engine updates "unassigned since" from both the plan the rule read and the re-solved plan. Updating it from executed plans only would change **no** R1u decision on L4. The convention is not separately stated in §17; worth one sentence there.
3. **No second-pass candidates.** In no epoch of any rule would a second rule pass on the re-solved plan have fired. The no-cascade rule therefore holds structurally (one pass, verified), but L4 never tests whether it matters.
4. **R1 ignores ETAs, by design.** Several R1 transfers send a rider to Lyft whose predicted van pickup was *earlier* than the Lyft pickup (decision + 2 + 8 min): R1(15) at 18:15 sends R001 (van ETA 18:17:44, Lyft 18:25:00) and R002 (18:19:28 vs 18:25:00), and there are two more later under R1(15) and three under R1(10). R2 and R3 never did this. A plan ETA is not a promise, but this is the rider-facing cost of an elapsed-time rule and belongs in the M5 discussion. It is not a defect.
5. **R2(15) and R3(2)** transfer every request before 18:15 at its request time, because with no van the predicted pickup is infinite. They differ only in R011's timing (R3 at 18:17, R2 at 18:20), as the report says.
6. **Specification nit (consent boundary).** §3.3 says `consent_u` < p_c accepts; §17.5 says `consent_u` > p_c declines. The two disagree only at equality, a measure-zero case. The engine follows §3.3, and L4's draws (0 and 0.95) are far from 0.9. Align the wording.
7. **`m2_report` count coverage.** The report's table gives offers, accepted, bookings and completions by class, but not cancellations after transfer, split into during the lag and after booking, nor Lyft no-shows by class, which D-45 lists. On base L4 all of these are 0, so the current report is correct. Add these rows before runs that have cancellations or no-shows (L5 onward).

**Takeaway a teammate could present.** "Across all six rules on L4, every rider and every Lyft booking is accounted for exactly once; the rule, the lag and the re-solve behave as specified, including the cancellation and no-show paths that L4 alone does not reach."
