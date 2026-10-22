# Independent review: the three pending-price formulations of D-53 (22 Oct 2026)

**In plain words.** The code computes all three pending prices (original, A, B) exactly as defined. On six small hand-built epochs and on every optimal epoch of the four logged L4 R0 runs (185 epochs, about 665,000 column combinations), a full enumeration that I wrote separately gives the same objective, the same M, the same plan, the same tie-break and the same charged prices. **No discrepancy was found.** The M bound holds for all three formulations: every proven-optimal plan leaves the fewest requests pending that the candidate set allows. The formulations differ only in *which* requests they leave pending when the cap binds. The original price charges a pending rider as if a van could pick it up at the next tick. **A** charges the earliest pickup any van could physically make. That is a true lower bound, it costs nothing to compute, and it removes the "teleport" error, but it still ignores that the nearest van is busy with the work the plan gives it. **B** charges the pickup after the van's chosen route. In the simplest cases this models deferral correctly, but it is neither a lower nor an upper bound, and it makes the MILP much larger: about 135,000 extra variables and 6.5× the wall time in a 5-van, 20-request epoch. **My assessment: A is the simplest formulation that is defensible.** It is cheap and has a clear meaning. It shrinks the D-53 bias but does not remove it, and that must be reported. Neither A nor B is a feasible joint future schedule for the pending riders.

**Scope and method.** I read `src/sim/dispatch.py` (uncommitted working copy, `pending_prices()`, `column_end()`, `solve()`, `_milp()`), decision-log rows D-53 and D-53 (update), the M1 math review §7 and `model_design.md` v0.3 §3. I wrote one test file, `tests/test_pending_price_independent.py`. It trusts the implementation only for the candidate columns (S, cost, stop order) and the travel oracle. It recomputes φ, tn, the route ends (e_j, l_j), L_r, every price, M, the minimum objective, the minimum pending count and the canonical tie-break from the written definitions. It does not call `pending_prices`, `column_end`, `_milp`, `_exact_obj`, `_pend_cost`, `_canonical` or `phi_u`. Scratch scripts are in `/private/tmp/claude-501/d53_review/`. I edited no other file and re-ran no logged run.

**Command and result.** `.venv/bin/python -m pytest -q tests/test_pending_price_independent.py` → **28 passed in 3.4 s** (`-s` prints the per-case findings).

**Sensitivity of the test (mutation check).** In scratch, I made three deliberate faults in the implementation and re-ran the five main cases × three formulations. Each fault was caught:

| Fault introduced | Checks that failed |
|---|---|
| B route end without the final 30-s dwell | 5 |
| A priced as the original | 5 |
| M without the Σ bmax term | 15 |

---

## Summary table

| # | Item | Verdict | Evidence |
|---|---|---|---|
| 1 | Implementation vs definitions (synthetic cases a–f, all three formulations) | **Agree** | 18 enumeration checks pass: objective, M, plan, tie rule, minimum pending count, charged price, A's L_r, B's priced pickup and n_z |
| 2 | Logged runs (original, A, B, M1 reference) | **Agree** | 46 / 45 / 48 / 46 optimal epochs. The B log's `column_end` matches route ends recomputed from the stop orders. n_rows = V + 2R + n_z |
| 3 | M bound | **Holds** for all three (proof §2). Not guaranteed for `feasible_unproven`, but the gap gives a bound on the excess (§2) | Proof, plus the minimum pending count confirmed by enumeration |
| 4 | Number sizes | **Safe.** Worst plausible objective ≈ 1.2·10¹⁴ U, 78× below 2⁵³. HiGHS tolerances are a minor caveat | §2.3 |
| 5 | A | **Still optimistic.** The nearest van may be busy with its own route | Test `A_optimism` (+14.2 points); case b (+1,022.5 points) |
| 6 | B | **Shared claims** (optimistic), **ignored insertion** (pessimistic), **size** | Case d; two-epoch test; L4 and the 5-van timing |
| 7 | Recommendation | **A** as the simplest defensible formulation; report its remaining bias; B only as a stated sensitivity check | §5 |

---

## 1. Small controlled cases

All cases use real location IDs, Travel(1.0, 1.0), vans with capacity 14 and HiGHS through `dispatch.solve`. "Routes" and "pending" in the tables are point totals (1 point = 1.2·10⁶ U), excluding M. For each case the table lists the best plan for each possible pending set, with the minimum number pending. The first row is the optimum.

**(a) An old request against young ones** (1 van, K = 1). R1 has waited 15 min and is 606 s from the van. R2 and R3 have waited 1 min and are about 105 s away. Two requests must be pending.

| Pending set | original (routes + pending) | A | B |
|---|---|---|---|
| R1, R2 (serve R3) | **4.67 + 65.50** | **4.67 + 197.50** | **4.67 + 300.17** |
| R1, R3 (serve R2) | 6.79 + 65.50 | 6.79 + 197.50 | 6.79 + 467.50 |
| R2, R3 (serve R1) | 200.23 + 6.00 | 200.23 + 6.00 | 200.23 + 313.67 |

- **All three leave the old request R1 pending.**
- Under the original and A, serving R1 costs about 200 points of route (it waits 25 min at pickup). Pending it costs 62.5 points (original) or 194.5 points (A, pickup at 18:40:06).
- Under B, serving R1 pushes both young riders behind a 15-min trip (313.67), so B also pends R1 (300.17).
- Here the decision is driven by the route cost, not by price optimism.

**(b) Party size, 1 vs 5** (1 van, K = 1, both waited 8 min; the party of 5 is 489 s away, the single 105 s).

| Pending set | original | A | B |
|---|---|---|---|
| R2 (q = 5) | **21.87 + 87.50** | **21.87 + 270.00** | 21.87 + 1,292.50 |
| R1 (q = 1) | 289.92 + 17.50 | 289.92 + 17.50 | **289.92 + 209.50** |

- **The original and A leave the party of 5 pending; B leaves the single pending.**
- With one van and nothing else open, B's price is the real cost of the two-job sequence. The van serves one rider, then the other.
- B therefore makes the right comparison here. Original and A undercharge the deferral of the party of 5, by 1,205 and 1,022.5 points respectively.
- This is the D-53 mechanism in its smallest form. **A does not fix it**, because L_r assumes the van is free now.

**(c) Binding cap** (2 vans, K = 2, six requests, so at least two are pending).

- **Original and A** pend R1 and R3: the oldest (18 min, q = 2, far away) and the party of 5. The objectives excluding M are 322.37 and 887.20 points.
- **B** pends R1 and R6: the oldest and the youngest (30 s). It serves the party of 5 on V2. Its objective is 1,222.50 points, of which routes 367.00 and pending 855.50.
- Even under B the oldest request stays pending, because it is far away and serving it costs more than deferring it after V1's route.

**(d) Several pending requests competing for one van** (1 van, K = 1, four nearby requests, so three are pending).

- **Original and A** give the same result. Every L_r ≤ tn, so A equals the original except for R4. Both serve the youngest request (R4) and pend R1–R3, including the two oldest.
- **B** serves R2 (party of 2) and pends R1, R3 and R4. They are priced at pickups 18:38:50, 18:38:21 and 18:35:48, all reached directly from V1's free position at 18:35:47. See §3.2(i).

**(e) Everything can be served** (2 vans, K = 3, three requests).

- All three formulations return the identical plan, with the same routes and stop orders, and an objective equal to the route cost (316.33 points).
- Only M differs: 1,167.91, 1,368.57 and 4,366.91 points.
- This must hold: by the M bound every optimum has zero pending, so the pending price never enters the objective.

**(f) Work in progress** (one van with a rider aboard and a committed pickup; one van with a rider aboard; K = 2; five requests).

- This case tests route ends that finish at the drop-off of a rider who is not an open request.
- All three formulations pend R1 (waited 15 min, far away) and choose the same routes. The enumeration agrees.

**Per-case takeaway.** The pending price never changes *how many* requests are served. It changes *which* ones, and only when the cap binds:
- **Original and A** pend the large or old request whenever its service is expensive: cases b, c and d.
- **B** pends it only if the B-priced deferral is cheaper. It still pends old requests that are far away: cases a and c.

---

## 2. The M bound

### 2.1 Proof (all three formulations)

**Notation.**
- R = Σ_v (max_k c_vk − min_k c_vk), the spread of the route costs.
- B̄ = Σ_r bmax_r, where bmax_r is an upper bound on the pending charge of r, so M = 1 + R + B̄.
- For any feasible solution x with p(x) requests pending:

  obj(x) = Σ_v c_{v,k(v)} + Σ_{r pending} (M + β_r(x)),

  where β_r(x) is r's pending charge.

**Pending charge.**
- *Original and A:* β_r = b_r. It is a constant with 0 ≤ b_r = bmax_r, because φ ≥ 0.
- *B:* β_r = Σ_j b_rj z_rj, where z_rj ≤ y_j and Σ_j z_rj = u_r = 1. So β_r is a convex combination of b_rj over the chosen columns. It lies in [min over chosen columns, max over chosen columns] ⊆ [0, bmax_r] **for every feasible z, not only the LP-optimal one**.

**Bounds on the objective.** In all cases 0 ≤ β_r ≤ bmax_r, so

  Σ_v min_k c_vk + p(x)·M ≤ obj(x) ≤ Σ_v max_k c_vk + p(x)·M + B̄.

**Comparison.** Take x with p pending and x′ with p′ < p pending:

  obj(x) − obj(x′) ≥ (p − p′)·M − R − B̄ ≥ M − (M − 1) = 1 > 0.

So x is not optimal. **Every optimal solution minimises the number of pending requests over the candidate set.** Among those solutions it minimises route cost plus the pending charge.

**Two conditions.**
- The proof needs only 0 ≤ β_r ≤ bmax_r.
- It is optimality over the candidate set (K, guardrail), not over all possible routes.

The enumeration confirms the bound in every checked epoch: the optimum's pending count equals the minimum over all combinations.

### 2.2 What is not guaranteed for `feasible_unproven`

An incumbent that has not been proven optimal can leave more requests pending than necessary. The bound still limits the excess.
- Let x be the incumbent with p pending and gap = obj(x) − (dual bound). Let x* be an optimum with p* pending.
- Then (p − p* − 1)·M + 1 ≤ obj(x) − obj(x*) ≤ gap. So **p − p* ≤ 1 + (gap − 1)/M**:
  - gap < 1 ⇒ p = p*;
  - gap < M + 1 ⇒ at most one extra request pending.
- I suggest logging gap/M for such epochs.

What is *not* established for an unproven incumbent:
- which requests are pending, or why (the `_pending_info` reasons);
- the canonical tie-break (`tie_status` = "not_checked");
- for B, the choice of z. The code recomputes the exact charge as the minimum over the chosen columns, so the reported objective is correct for the executed y.

None of the logged runs hit this case: every epoch with vans is `optimal`.

### 2.3 Number sizes and HiGHS tolerances

**Worst plausible case** (5 vans, 20 open requests, waits up to 120 min, q = 5, K = 3, a full van of 14 riding 60 min, 100 km):

| Quantity | Value (U) |
|---|---|
| b per request | 1.26·10¹⁰ |
| M | 4.4·10¹¹ |
| Largest objective (everything pending) | 9.3·10¹² (970× below 2⁵³ ≈ 9.0·10¹⁵) |
| With 60 min over the guardrail for all 14 riders (Ψ = 1,000 points/pax-min) | M ≈ 5.5·10¹², objective ≈ 1.2·10¹⁴ (**78× below 2⁵³**) |

- Every coefficient and objective value is an exact integer in a double (`test_M_magnitude_below_2_53`).
- In the logged runs the maximum objective is 3.4·10¹⁰ (original), 2.3·10¹⁰ (A) and 2.0·10¹¹ (B). B's M is about 3.5× larger than the original's, because bmax_r is taken over every column, including the longest routes.

**Tolerances.**
- `mip_abs_gap = 0.5` U against an objective of 10¹⁰–10¹¹ is a relative gap of 10⁻¹¹ to 10⁻¹². Double rounding at that size is about 10⁻⁵ U, so the gap test itself is meaningful.
- The caveat is HiGHS's *feasibility* tolerances (primal and dual 10⁻⁷, integrality 10⁻⁶). They act on variable values, so their effect on the objective scales with the cost coefficients. For example, y = 1 − 10⁻⁶ on a 10¹⁰ U column moves the LP objective by 10⁴ U ≈ 0.01 point.
- So "optimal" is reliable to about 0.01 point, not to 0.5 U. The observed |objective − bound| was at most 1.5·10⁻⁴ U (B run).
- The code protects the plan by rounding y and recomputing the objective exactly as an integer.
- The remaining risk is in tie enumeration. The objective-cap row (coefficients up to 10¹¹) could, within tolerance, admit a solution 1 U worse. `_canonical` would then stop early ("break") before it has found every tie.
- No logged epoch shows this: my canonical choice matched in all epochs labelled `unique` or `tie`.
- **Low severity.** It would only matter for near-ties within about 0.01 point.

---

## 3. What each formulation guarantees

### 3.1 A: a lower bound, still optimistic because of competing work

**The bound.** L_r = min_v (free_v + T(loc_v, o_r)) is the earliest time any on-duty van can reach r's origin. So q_r·φ(max(tn, L_r) − t_r) is a lower bound on r's wait cost under any future plan, with three small exceptions:
- **Paths through another stop.** The travel matrix with a 30-s dwell violates the triangle inequality for 3 of 35,344 pairs, by up to 13 s, so a path through another stop can be slightly faster than going direct.
- **Vans not yet on duty.** A van that comes on duty later is not in L_r.
- **The next-tick floor.** Pending is not charged a pickup earlier than tn, even if a van could arrive earlier. This is a modelling choice, kept from the original.

**Why it is still optimistic.**
- L_r assumes the closest van goes straight to r. But that van usually receives a route of its own in the same plan.
- Test `test_A_optimism_competing_work` (1 van, K = 1, two nearby requests): A charges pending R1 at pickup 18:30:41. The van is serving R2, and the earliest pickup after that route is 18:34:50. The undercharge is **14.2 points**.
- In case (b) the undercharge is **1,022.5 points**, and it decides the plan: A pends the party of 5.
- The bias keeps the original's direction (it favours pending the expensive requests). It is smaller wherever L_r > tn and unchanged where L_r ≤ tn (case d).

### 3.2 B: deferral after the chosen route

**(i) Shared claims (optimistic).**
- Each pending rider is priced at a pickup reached directly from the end (e_j, l_j) of one chosen column. Several riders can claim the same end.
- Case (d), `test_B_shared_claims_on_one_van`: R1, R3 and R4 are all priced after V1's end at 18:35:47, at pickups 18:38:50, 18:38:21 and 18:35:48.
- No single van can make all three pickups. The best schedule that picks all three up in a row right after the route costs **125.00 points**. B charges **102.08 points**.
- The undercharge grows with the number of pending riders per van. That is exactly the regime where the cap binds hardest.

**(ii) Ignored insertion (pessimistic).**
- B assumes r waits until the van has finished its whole route, including drop-offs of riders already aboard. At the next epoch the dispatcher can insert r before that.
- `test_B_pessimism_next_epoch_inserts_earlier`: at 18:30:00, R1 is priced at pickup 18:35:52.
- 30 s later, the van has committed to its first pickup, which frees its single K slot. R1 is then planned at 18:32:15, **3.6 min earlier**.
- So B is **neither a lower nor an upper bound**. For a single pending rider alone, it is a service the van could actually perform (case b), and nothing more.

**(iii) Size.**
- B adds one continuous z per (open request, column) and one row per z, plus one row per request: n_rows = V + 2R + n_z (confirmed on every logged B epoch).

| Instance | Columns | n_z | n_rows | MILP + ties wall time (original → B) |
|---|---|---|---|---|
| L4 R0, worst epoch (2 vans, 13 open, K = 3) | 756 | 9,828 | 9,856 | total for the evening 24.8 s → 41.6 s |
| Synthetic, 5 vans, 20 open, K = 3 (seed 53; all 1,351 subsets per van feasible) | 6,755 | **135,100** | **135,145** | MILP 0.23 s → 7.26 s; ties 0.24 s → 9.40 s; epoch total **3.0 s → 19.6 s** |

- Upper bound for the second row: Σ_{k≤3} C(20, k) = 1,351 columns per van × 5 vans = 6,755 columns, so 20 × 6,755 = 135,100 z.
- Both synthetic solves were proven optimal at the root node. Candidate generation took 2.5 s in both.
- At L5 scale (many epochs, possibly more vans or a larger K) the cost of B grows as R × Σ_v |columns|. Tie enumeration rebuilds the full model for each extra solve, so it scales the same way.
- **Cheap reductions** (not implemented):
  - drop the z_rj for columns that contain r (about 14 % of z at 20 open requests);
  - share one z per (r, column end) when several columns end at the same (e_j, l_j).

**(iv) A modelling coupling.**
- Under the original and A, the pending charge is a constant, so the route chosen for the served requests is the cheapest one for them.
- Under B, the route choice also changes the price of pending riders. The solver may choose a route that ends early or near a pending cluster at some cost to the served riders.
- This is the point of B. It is also a further modelling claim, about a speculative future, that a teammate would have to defend.

### 3.3 What neither guarantees

**Neither A nor B is a feasible joint future schedule for all pending riders.**
- A ignores the work the plan gives the vans.
- B ignores that several pending riders share one van's end, and that later epochs re-plan.
- Both are prices that steer the choice of which requests to pend under a binding cap. Neither is a forecast of pickups.
- The tentative ETA (`_pending_info`) remains a separate, optimistic quantity that ignores the cap and the other pending riders.

---

## 4. Whole-evening runs (read only)

**Re-checks.**
- Every optimal epoch of `L4_R0` (46), `L4_R0_pp-A` (45), `L4_R0_pp-B` (48) and `L4_R0_M1_reference` (46) was re-checked by full enumeration of the logged candidates. That is 151,710 / 140,471 / 220,862 / 151,710 combinations.
- In every epoch the following match: next tick, M, objective, the canonical plan, the minimum pending count, the charged price, and (for A) L_r. For B they also include the logged column ends, the priced pickups, n_z and n_rows.
- The M1 reference and the new original run agree epoch by epoch: same times, objectives, chosen routes and pending sets. The new code reproduces M1 under `pending_price="original"`.

**At 18:15** the pending sets are:

| Formulation | Pending at 18:15 | Riders' waits at 18:15 |
|---|---|---|
| Original | R002, R005, R006 | |
| A | R004, R005, R006 | |
| B | R007, R008, R009 | 5:20, 5:20, 1:10 |

This is as in the math review §7.

**Single-trajectory context only, not a basis for the choice.** Mean waits are 18.8 / 18.8 / 21.8 min and maximum waits 44.4 / 35.6 / 38.6 min (original / A / B). These are one scenario and one evening: different formulations lead to different states later in the evening. They show the direction of the effect, not which formulation is better.

---

## 5. Recommendation input

**A is the simplest defensible formulation.**
- **Meaning.** "A pending request is never charged less than the cheapest service any van could physically make." That is a valid lower bound (up to a 13-s triangle exception and the next-tick floor), and it is one sentence at the board.
- **Burden.** None. It is one constant per request, the MILP is unchanged, and the M bound holds as before.
- **Cost of the fix.** It removes the "teleport" part of the D-53 bias at no cost.

**Caveats to state with A.**
- It **does not remove** the bias, because it still ignores competing work: case (b) still pends the party of 5, and case (d) is unchanged from the original.
- The direction of the remaining bias is known (old, large, far requests are pended more readily), and it should be reported alongside the results.

**B models deferral more accurately in the simplest cases** (one van, one pending rider: case b). Its drawbacks:
- It is neither a lower nor an upper bound, because of shared claims and ignored insertion.
- It couples route choice to a speculative future.
- It multiplies MILP size by roughly R (6.5× wall time at 5 vans × 20 requests).
- It is affordable at L4 and plausibly at L5, but it is harder to defend.

If the team wants to *remove* the bias rather than shrink it, B (or a variant that charges the k-th pending rider on a van for its k-th position) is the direction. It should be presented as a heuristic price, not as an achievable schedule.

**Whatever the team chooses:**
- freeze it **before** the Lyft-rule experiments;
- apply it identically to every policy;
- do not choose it from the L4 outcome numbers in §4.

**One-line takeaway for the team:** *The pending price never changes how many riders are served, only which ones wait when the cap binds; A makes the price physically honest at zero cost, B makes it look ahead at a real cost, and neither predicts the future schedule.*
