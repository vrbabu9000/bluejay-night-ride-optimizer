# Independent review: the M1 dispatcher C and its engine interface (21 Oct 2026)

**In plain words.** The code for dispatcher C does what it says. The cost units are exact. The route search really does find the best stop order for each set of riders (a brute-force check over about 21,800 cases found no differences). The large pending price M does make the solver serve as many requests as the candidates allow. On all 370 epochs of L1–L4 and L5/r00, the solver's answer and its tie-breaking matched a full enumeration. **No blocker was found in the code.** The main finding is a property of the **documented objective** itself. A pending request is priced at its wait at the next tick, which is lower than the cost of any pickup a van could physically make. A served request, in contrast, is charged its real, later pickup. So when the cap K binds, the solver tends to leave pending the requests whose service is most expensive per minute: the oldest requests and the largest parties. At 18:15 in L4, serving R002 (party of 5, waited 15 min) at the earliest moment any van could reach it scores 116.5 points worse than leaving it pending. With K = 4, R002 is the **only** request left pending. This is a design question for the team, not a bug. Two smaller items should be fixed. The cap K counts every uncommitted request, whereas D-47(3) says it counts only requests that are new relative to the van's previous plan. The decision row D-52, which the code cites for the M proof and the settings, does not exist in `decision_log.md`.

**Scope and method.** I read `src/sim/dispatch.py`, `src/sim/engine.py`, `src/sim/inputs.py` (and `lyft.py`, `run.py` for context), `model_design.md` v0.2 §3–§5, `scenario_spec.md` v0.4 §17, and decision-log rows D-29, D-46, D-47, D-51 (and the D-51 update). I ran `python -m sim.run --level L4 --rule R0` as instructed. That run writes to the gitignored folder `outputs/sim/L4_R0/`. I also ran scratch experiments under `/private/tmp/claude-501/m1_math_review/`. I edited no other file. Statements marked *(inference)* are reasoned, not tested.

---

## Summary table

| # | Item | Verdict | Severity | Evidence (short) |
|---|---|---|---|---|
| 7 | Pending price π_r = q·φ(W^next) + M under a binding cap K | **Correct implementation of an objective with a systematic bias** | **should-fix (team decision before experiments are frozen)** | 18:15 L4: serving R002 at its earliest physical pickup costs +116.5 pts; with K = 4, R002 is the only request left pending (Exp 3, Exp 4) |
| 7a | Cap K counts all uncommitted requests, not "new relative to the previous plan" (D-47(3)) | **Deviates from the documented correction** | **should-fix** | `best_routes`: `len(picked) < K` over every open request; D-47(3) is a correction marked "must be implemented before L6" |
| 8a | Code cites D-52 for the M proof and M1 settings; no D-52 row exists | Missing record | **should-fix (documentation)** | `grep D-52 decision_log.md` returns only forward references inside D-46/D-47 |
| 4a | `time_limit = 300 s` (wall clock) can change a plan | Contradicts D-46(5) if it is ever hit | should-fix (low) | `_milp` uses the incumbent or the committed-only fallback when the time limit stops the solve; never hit in these runs (max epoch 2.0 s; one static K = 5 test took 104 s) |
| 1 | Units, scaling, multiplier | **Correct** | note | All factors check exactly (§1); multiplier applied once per leg, same expression as `generator_v2.T()` |
| 2 | Label dominance in `best_routes` | **Correct** (exact under the stated fixed-old-drop-order restriction) | note | Proof in §2; 0 mismatches over 21,834 subsets, including 531 equal-cost cases and a tight-guardrail stress (Exp 1) |
| 3 | M bound | **Correct with caveat** | note | Proof in §3; held on 370/370 epochs (Exp 2). Caveat: it minimises pending **requests**, not passengers |
| 4 | Solver statuses, gap, fallback, ties, determinism | **Correct with caveat** | note | Brute-force optimum, objective and canonical choice matched on 370/370 epochs (Exp 2). Caveats in §4: objective taken from a float, tie loop labels, reasons assume optimality |
| 5 | Guardrail rule vs D-47(2) | **Correct with caveat** | note | Matches the rule per rider; violations can still arise *between* epochs (no-show wait, triangle-inequality gaps up to 12.7 s); these are exempt by design and must be attributed in reports |
| 6 | Observation of moving / serving / curb-waiting vans | **Correct with caveat** | note (revisit before M2) | No hidden trait leaks before its event. But during an absent-rider curb wait, the planner already plans as if the no-show has happened (L2: R005, R011) |
| 8 | Other wording and claims | Minor | note | Docstring wording on "new" pickups and on why dominance holds; tentative ETA is optimistic; van-ID string ordering ("V10" < "V2") |

---

## 1. Units and scaling — correct

- **Integer units.** U = points × PT, with PT = 1,200,000.
  - Riding: `ride_u` = 0.5 × PT / 60 = 10,000 U per passenger-second = 0.5 points per passenger-minute ✓.
  - Distance: `km_u` = 0.1 × PT / 10,000 = 12 U per decimetre = 120,000 U per km = 0.1 points per km ✓.
  - Guardrail excess: `psi_u` = 1000 × PT / 60 = 2×10⁷ U per passenger-second = 1000 points per passenger-minute ✓.
  - The `__post_init__` assertion guards integrality of these factors.
- **φ.** The slopes ×120 per second are (2, 5, 10, 20, 40), multiplied by PT/120 = 10,000. That gives slope_min × seconds × 20,000 = slope_min × (seconds / 60) × PT ✓. The breaks are at 0/300/600/900/1200 s ✓. φ(5) = 5, φ(10) = 17.5, φ(15) = 42.5 and φ(20) = 92.5 points, which matches D-29 and §4.1.
- **Definitions.** W = curb arrival − t_r. H = drop-off arrival − pickup arrival, so H includes the 30-s boarding dwell. Both match §3.4 and the engine's `ride_s`. The β·q·H term includes the sunk ride time of riders already on board. That part is a constant per van, so it does not affect the argmin.
- **Travel.** `Travel.van` = `int(round(t0 × m_v))` per leg, the identical expression to `generator_v2.T()`. The guardrail uses `travel.van(o, d)`, i.e. t₀ × m_v, as D-47(1) requires. Lyft uses m_L once. Distances are not scaled, which is correct. Decimetres: `round(m × 10)` is exact (the matrix has at most one decimal; max residual 0.0).
- **Rounding caveat (wording).** "Half-to-even" applies only to exact binary ties. With m = 1.2, products such as 192.2 × 1.2 are binary approximations. The rule is therefore "Python `round` on the float product". That is still identical to the generator, so the answer keys reproduce.

## 2. Label dominance — correct

**Decomposition.** The final cost is Σ_pickups q·φ(a−t) + β Σ_drops q·(D−p) + γ·km + Ψ Σ q·(H−G)⁺. Writing β q (D − p) = β q D − β q p gives the stated additive form: a pickup adds q·φ(a−t) − β·q·a, and a drop adds β·q·D plus the Ψ term. For existing riders, the term −β q p is a constant in `c0` ✓.

**Why dominance is exact.** The docstring's argument is right but incomplete. The fact that makes it work is that **there is no waiting**: legs are fixed, the dwell is a constant 30 s, and there are no time windows. So any completion of label B, applied to label A with t_A = t_B − δ, produces exactly B's schedule shifted earlier by δ. Then:
- For riders picked up in the completion, H is unchanged. Their φ term is evaluated δ earlier, which is ≤ because φ is non-decreasing. The −β q a and +β q D terms cancel in the shift.
- For riders on board at the label, D is earlier by δ. Their β q D and Ψ terms are ≤.
- For new riders on board, H_A = D − δ − p_A ≤ D − p_B, because p_A ≥ p_B. That is the guardrail-slack criterion. Existing riders have the same p, so their H is smaller ✓.
- Capacity, the K count and the forced next old drop are functions of the key (picked, dropped, last) ✓.

Completions of A therefore cost no more than completions of B and are feasible whenever B's are. φ′ ≥ 1 > β is sufficient for this but not needed: φ′ ≥ 0 suffices once a rider's pickup and drop are paired.

**Tie rule.** `_insert` discards B only if (c_A < c_B or s_A < s_B), and labels in the same layer have the same length. Suppose an optimal completion of B gave the lexicographically smallest optimal route s_B + X. Then s_A + X costs no more than s_B + X and is lexicographically smaller, a contradiction. So the canonical route survives. The relation is transitive (checked case by case), so chained pruning is safe.

**Counterexample search.** I found none. Exp 1 compared `best_routes` with full permutation enumeration (`evaluate` on every precedence-valid order with the old drops in the committed-only order). It also compared the committed-only route against all orders of the old drops.

**Restriction to keep stated.** Existing riders are dropped in the order of the committed-only route. The result is "best order given that restriction". A single insertion that is feasible only with a different old-drop order gets no candidate. That is slightly weaker than §3.3's "every open request gets a single-insertion candidate on every van that can feasibly take it" *(inference: rare, because appending after all old drops is always feasible when the seats allow)*.

## 3. The M bound — correct, with a caveat on what it counts

**Claim.** Let b_r = q_r·φ(W_r^next) ≥ 0, R = Σ_v (max_k c_vk − min_k c_vk), B = Σ_r b_r and M = 1 + R + B. Then every optimal solution has the minimum number of pending requests over the candidate set.

**Proof.** Suppose an optimal x* has p* pending requests and a feasible x′ has p′ < p*. Then

obj(x*) − obj(x′) = Σ_v [c_v(x*) − c_v(x′)] + Σ_{P*} b_r − Σ_{P′} b_r + (p* − p′)·M ≥ −R + 0 − B + M = 1 > 0.

This contradicts the optimality of x*. ∎

The proof needs only b_r ≥ 0, B ≥ Σ_{P′} b_r, and exact costs (all costs are integers in U). Exp 2 confirmed the property on 370/370 epochs. It does **not** hold for `feasible_unproven` solutions.

**Caveat: it counts requests, not passengers.** The first-stage criterion treats a party of 5 and a single rider as equal. The cap K is also per request. When seats or the cap make two singles compete with one party of 5, the singles win regardless of φ. This sits uneasily with §3.4 ("costs and metrics are passenger-weighted"). If the team wants passengers first, π_r = q_r·(φ(W^next) + M) with the **same** M stays valid: one fewer pending passenger is worth at least M. It would change the D-47(3) statement to "maximises passengers served". This is a team choice, not an error.

## 4. Solver handling — correct with caveats

- **Statuses.** kOptimal → `optimal`, kInfeasible → `infeasible` (impossible by construction, because the committed-only columns plus u are always feasible), a primal solution without proof → `feasible_unproven`, nothing → `failed`. `failed` and `infeasible` fall back to the committed-only routes (all open requests pending) and are logged. No heuristic T fallback is used, as D-51 requires ✓. *Suggestion:* raise on `infeasible`, since it can only mean a bug.
- **Gap.** Every column cost and π_r is an integer in U, so every feasible objective is an integer. mip_abs_gap = 0.5 with mip_rel_gap = 0 therefore certifies optimality ✓, up to HiGHS floating-point tolerances. Objectives reach 3.5×10¹⁰ U (L4) *(inference: tolerances of about 1e-9 relative could blur differences of the order of 10–100 U, i.e. 10⁻⁴ points; not observed)*.
- **Objective from a float.** `obj = int(round(info.objective_function_value))`. The tie loop compares this number and also uses it in the objective row (≤ obj + 0.5). It matched the exact integer sum on 370/370 epochs, but it is safer to compute obj exactly as Σ of the chosen columns' integer costs plus Σ π of the pending requests.
- **Tie enumeration.** One y-column per van, and u is determined by y, so the no-good cut Σ_{j∈last} y_j ≤ |V| − 1 excludes exactly one solution. Cuts accumulate. The objective row keeps only equal-objective solutions. One column per (v, S) means an assignment determines the solution, so `_assign_key` is a total order on optima ✓. Exp 2 found the same tied optima and the same canonical choice as brute force (L1–L3: 2 ties each; L4 and L5/r00: 1 each).
  - Minor: if a tie re-solve returns `feasible_unproven`, the loop stops and labels the result `unique`/`tie` instead of "incomplete".
  - Van IDs compare as strings ("V10" < "V2") once there are 10 or more vans.
- **Determinism.** With threads = 1 and seed 0, HiGHS is deterministic for a given version and build. More importantly, when enumeration completes, the canonical rule makes the chosen plan **independent of the solver path**, which is a robust design ✓. The node limit is deterministic. The 300-s `time_limit` is not, so if it ever binds, the plan depends on the machine. That contradicts D-46(5) ("wall time … never changes a plan"). *Fix:* treat a time-limit stop as a run error, not as a usable incumbent.
- **Pending reasons.** The string "the chosen subset plus this request is not a feasible candidate" is correct **for an optimal solution**: if S ∪ {r} were a candidate, swapping to it would cut pending by one, which contradicts the M bound. For `feasible_unproven` solutions it is not established. "Infeasible" also means "infeasible under the fixed old-drop order".

## 5. Guardrail vs D-47(2) — correct with caveat

- **As implemented.** New riders need H ≤ G (`lim = g if rid in req`). Onboard and committed riders need H ≤ max(G, H in the committed-only route) (`allowed`). The committed-only route is exempt and computed without limits, and its cost includes Ψ, so its order minimises violations first. Ψ is charged on (H − G)⁺ in every route, and no candidate can exceed the unavoidable level. This matches the D-47(2) text read **per rider** ✓.
- **Gap 1: within an epoch, not across epochs.** Violations can appear between epochs without any candidate "creating" them:
  - (i) **Absent rider.** The engine waits 180 s at the curb, but planning assumes a 30-s board dwell. Any onboard rider with less than 150 s of slack goes over G.
  - (ii) **Dropped stops.** The matrix violates t(a,c) ≤ t(a,b) + 30 + t(b,c) in 4 triples, by up to 12.7 s. So removing a planned stop (reassignment, cancellation, transfer) can make later arrivals later.

  Both are exempt by design. The plan audit and the reports should attribute them so they are not read as dispatcher failures.
- **Gap 2.** "Unavoidable" means unavoidable **within the restricted candidate set** (fixed old-drop order). State this in the report wording.

## 6. Observation — correct with caveat

- **Moving to a pickup.** The committed rider is added as if boarding at the planned arrival, with committed_wait = q·φ(arr − t). The presence draw is not used ✓.
- **Moving to a drop.** That rider is removed, and the van is free at arr + 30 at d ✓.
- **Cancelled while driving.** The van is free at arr at o (a public event) ✓.
- **Serving.** Board or drop dwell: free at service end, with the onboard set current ✓.
- **Hidden traits.** Patience, consent and Lyft delay never enter the Observation. Lyft rule R3 uses the fixed 480 s, not the hidden delay ✓.
- **Caveat: curb wait for an absent rider.** The van shows free = arrival + 180 s and the rider is not in `riders`. Observed in L2: R005 (V2, epoch 2640) and R011 (V1, epochs 5880 and 6000). In this engine, "absent at arrival" ⇔ "no-show", so the planner treats the no-show as certain up to 180 s before it happens. A real dispatcher sees only "not here yet, timer running". It is also inconsistent with the "plan as if the committed rider boards" convention used for moving vans, and with §3.2 (C_v includes "the van at the curb in its 3-min wait").
  - Effect: during the wait, departures cannot happen, so the van's own moves are unaffected. But predicted and tentative ETAs of other requests, and other vans' assignments, do use the inference. These ETAs matter once Lyft rules read them after 18:15 (M2).
  - L4 R0 has no absences, so it is unaffected.
  - Suggest one stated convention, e.g. "free at arrival + 180 s, rider assumed to board at the end of the wait", or record the current one as a modelling choice in D-52.

## 7. Pending price at 18:15 (L4 R0) — inherent to the documented objective under a binding cap

**Mechanism.**
- A served request is charged q·φ at its real pickup a_r. A pending one is charged q·φ at tn = the next tick, regardless of where the vans are.
- For any request whose earliest physical pickup L_r = min_v (free_v + T(loc_v, o_r)) is later than tn, π_r − M is below the cost of **every** possible service, by at least q·[φ(L_r − t) − φ(tn − t)].
- That gap grows with q and with φ′, i.e. with the party size and with age.
- When K binds, M fixes how many requests are pending, and this gap decides *which*. The bias points toward pending the oldest and largest parties. That is the opposite of §3.5's stated intent ("old requests are prioritised") *(inference for the general case; quantified below for this epoch)*.

**Quantified at 18:15:00** (tn = 18:16:00; 9 open requests, 2 vans, K = 3, so at least 3 must be pending):

| | Chosen plan | Best plan serving R002 |
|---|---|---|
| Pending | R002, R005, R006 | R004, R005, R006 |
| V2 route | R004, R007, R009 | R002, R007, R009 |
| Objective excl. M (points) | 897.32 | 1013.86 (**+116.54**) |

- **R002's earliest possible pickup** is 18:19:28. That is its pickup in the alternative plan, i.e. wait 19.47 min and φ = 435.83 points. Its pending price is φ(16 min) × 5 = 262.50, so serving it at the **physical optimum** is charged +173.33 over pending.
- **R004's optimism** is only 49.33 (served at 18:18:48: 127.67 vs 78.33).
- **Net.** The difference in optimism (124.0) exceeds the true cost difference of the routes, so R002 is pended.
- **Realised outcome.** R002 was picked up at 18:22:18 (wait 22:18, φ = 692.5 points). It stayed pending at every epoch through 18:18:30 (Exp 3).
- **Not just the cap level.** Re-solving the same 18:15 state with K = 4 leaves **only R002** pending (8 of 9 served). K = 5 serves all 9, but that one epoch took 104 s to solve (Exp 4).

**Two alternatives** (not implemented). Both keep the M bound valid, because the proof needs only b ≥ 0 and B = Σ_r of an upper bound on each b_r.

- **A. Lower-bound pending price.**
  - Definition: b_r = q·φ(max(tn, L_r) − t_r), with L_r = min_v (free_v + T(loc_v, o_r)), computed from the Observation, independent of the solution. M = 1 + R + Σ b_r.
  - What it changes: it removes the "teleport" optimism. Pending is never charged less than the best physically possible service. It stays a lower bound, so the bias shrinks but keeps its sign.
  - Static re-solve on the R0 trajectory: R002 is served at 18:15, 18:15:50, 18:16:00 and 18:16:30. It is pending again at 18:17:00–18:18:30, now by margins of 7–9 points. At 18:15 it pends R004, R005, R006.
- **B. Deferred-append pending price.**
  - Definition: price pending r at the wait it would have if appended after the chosen route of the best van: b_rvk = q·φ(max(tn, e_vk + T(ℓ_vk, o_r)) − t_r), where e_vk and ℓ_vk are the end time and place of column k.
  - Linearisation: z_rvk ∈ [0,1], z_rvk ≤ y_vk, Σ_{v,k} z_rvk = u_r, cost Σ b_rvk z_rvk. For fixed integer y the LP picks the minimum, so z can stay continuous. M = 1 + R + Σ_r max_{v,k} b_rvk.
  - Size: it adds |R| × |columns| variables (≈ 2,300 at 18:15).
  - What it changes: pending is priced at an **achievable** deferred service, which removes the optimistic bias. The tendency becomes closer to "oldest first": at 18:15 it pends R007, R008, R009 (waited 5:20, 5:20, 1:10), and R002 is served at every epoch from 18:15.
  - Risks: it can be pessimistic, because r might be inserted earlier at the next epoch. Several pending requests may claim the same van end. M grows.
  - A cheaper, solution-independent variant appends after each van's committed-only route. It is less accurate.

The "price at the tentative ETA" option in the brief is circular as written, because the tentative ETA depends on the chosen routes. B is its linearisable form. The static re-solves above reuse the documented run's states. They show the direction of the effect, not a counterfactual evening.

**On D-47(3).** At 18:15 every request is new, so the cap deviation (7a) does not change this epoch. From 18:15:50 on, the van's previously planned, still uncommitted requests use up its K slots. That is what D-47(3) was written to prevent. Fixing 7a reduces how often K binds, but not the bias whenever it does bind.

## 8. Other points

- **a. D-52 is missing.** `dispatch.py` cites "proof in D-52" and "settings D-52", and `engine.py` and `__init__.py` cite D-52 for conventions. No such row exists in `decision_log.md` as read. The M proof (§3 above) and the M1 values (K = 3, Ψ = 1000, the gap, node and time limits, the planning convention for a curb wait) need that row. Note that D-47(2) and (4) are proposals, not approvals.
- **b. Docstring wording.** "K = max new (uncommitted) pickups" redefines "new" relative to D-47(3) (7a). "Because φ′ ≥ 1 > β, every future term is non-decreasing" should also name the no-waiting uniform-shift property, which is what makes dominance exact (§2).
- **c. Tentative ETA.** Each pending request is inserted alone into the chosen routes, ignoring K and ignoring other pending requests. The reported ETA is that of the cheapest-Δcost insertion, not the earliest. It is an optimistic estimate, and Lyft rules R2 and R3 will read it in M2. Label it as such in the logs.
- **d. W^next.** The next *tick* is the latest possible next epoch. Since no pickup can happen at the epoch instant, "next tick" is itself optimistic (see §7).

---

## Experiments (all read-only; scripts in `/private/tmp/claude-501/m1_math_review/`)

| Exp | Command | Result |
|---|---|---|
| 0 | `cd src && ../.venv/bin/python -m sim.run --level L4 --rule R0` | 44 epochs, all `optimal`; ties: 43 unique, 1 tie (18:15, symmetric vans); 16 `van_completed`; about 8–11 s wall |
| 1 | `exp1_dominance.py <seed> <m_v>` for seeds 1–4 (m_v 1.0, and 1.2 for seed 4), plus `exp1b_dominance_smallpool.py <seed> 1.0 3` for seeds 5 and 6 (3-location pool to force ties). Random vans on v2 locations: 0–3 onboard riders, 1–4 open requests, K = 3; base guardrail and a tight one (G = max(7 min, T + 1 min)) | **0 mismatches over 21,834 subsets** (committed-only route also checked against all orders). Among the 18,099 subsets of seeds 2–6 (where counters were on): some orders infeasible in 12,611, equal-cost orders in 531, all with the same canonical choice |
| 2 | `exp2_bruteforce_epochs.py <epochs.jsonl>`: enumerate every disjoint pair of logged candidates (2 vans), exact integer objective | L4: 44/44 epochs match (objective, canonical choice, M, every optimum at minimum pending); max objective 3.55×10¹⁰ U, max M 7.98×10⁹ U. Same for L1 (93), L2 (95), L3 (96) and L5/r00 (86), run to scratch with `sim.run.run(level, 'R0', out=…)`; L5/r00 took 26 s |
| 3 | `exp3_pending_price.py` and `exp3b_decompose.py`: capture each Observation by wrapping `dispatch.solve`, then re-solve each epoch statically under the documented price and alternatives A and B | Numbers in §7 |
| 4 | `exp4_cap.py`: re-solve the 18:15 state with K = 3, 4, 5 | K = 3: pending R002, R005, R006. K = 4: pending **R002 only**. K = 5: none pending (104 s for the epoch) |
| aux | Triangle-inequality scan of `tt_locations_v2.csv` with a 30-s dwell; L2 epochs during absent curb waits | 4 violating triples, worst 12.7 s; L2 curb-wait observations as in §6 |

**What this review does not show.** It does not show whether either alternative pending price improves evening-level outcomes; that needs paired full runs after a team decision. It does not test vans ≥ 3, where brute force is impractical, or m = 1.2 runs. It does not cover the Lyft rules after 18:15 (M2).
