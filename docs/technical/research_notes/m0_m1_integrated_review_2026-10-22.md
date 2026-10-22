# M0–M1 integrated review (22 Oct 2026)

**Reviewer:** independent integrated reviewer (Claude Code subagent). I only read code, data and docs. The one file I wrote is this note. Scratch runs went to `/private/tmp/claude-501/m0_m1_review/`, and nothing under `outputs/` or `data/` was overwritten.

**Scope:** `src/sim/*`, `tests/test_sim_engine.py`, `tests/test_sim_independent.py`, `tests/independent_check.py`. Docs checked: decision log D-46–D-53 (with the D-52 amendments and the D-53 update), `scenario_spec.md` v0.5 §17, `model_design.md` v0.3, `preregistration_v2.md`, and `scenario_methodology.md` v1.1 §7–§9.

## Verdict: **ready with fixes**

I found no blocker. All of these reproduce:
- the answer keys;
- the L4 transfer mechanics;
- every MILP choice compared against full enumeration;
- the frozen hashes;
- every quantitative status claim in methodology §7.

The fixes are of three kinds:
- **Solver status handling.** An empty model is labelled "failed", and HiGHS configuration errors are masked.
- **Wording.** A few status claims overstate what the tests covered or what was approved.
- **Repository hygiene.** The uncommitted work mixes two milestones, a Phase 4 plan folder is missing, and LaTeX build files are not ignored.

None of these changes an M0–M1 result.

## Findings

| ID | Severity | Finding | Evidence | Suggested fix |
|---|---|---|---|---|
| F1 | should-fix | **Status mapping in `_milp`.** (a) An empty model (no vans, no open requests) gets HiGHS `kModelEmpty`, and the code logs it as `failed`. (b) The return value of `h.run()` is never checked. If HiGHS refuses to run (`kError`, model status `kNotset`), the epoch is logged `failed` and committed-only work runs; it does not raise. (c) An `infeasible` status cannot happen by construction, yet it also runs committed-only work instead of raising. (d) `feasible_unproven` runs the incumbent. D-52 lists the four statuses but does not say this, and the M bound does not hold for an unproven incumbent. | (a) `L4 R2(15)` and `L4 R3(2)`: epoch τ = 0 is the re-solve after both t = 0 requests transfer, with `n_columns 0, mip_nodes -1, status failed` (scratch `out/L4_R2(15)/epochs.jsonl` line 1). Status counts: `{'failed': 1, 'optimal': 41}`. (b) Reproduced: one `highspy.Highs().run()` with default threads, then a model with `threads=1`, returns `HighsStatus.kError` / `kNotset`. `D.solve` then reports `failed` (`dispatch.py:382–395`). | Treat "no columns and no rows" as trivially optimal, or skip the solve. Raise on a `run()` error, on `kNotset` and on `infeasible`. Record in D-52 that `feasible_unproven` executes the incumbent and is not covered by the M proof. Add tests for each path. |
| F2 | should-fix | **Methodology §7 overstates the best-order check.** The text says "each candidate's cost equals a brute-force minimum (1,130 subsets, 113,879 orders)". In fact the test brute-forces every subset with \|S\| ≤ 2 plus **80 sampled** \|S\| = 3 subsets, over the 40 van states of **L4 R0 only**. The other candidates are re-costed independently, not minimised. | `pytest -s -k best_order`: "40 van states; 1130 subsets brute-forced (80 with \|S\|=3) … 113879 complete orders" (`test_sim_independent.py:136–139`). | Reword: "every subset of ≤ 2 new requests and a random sample of 3-subsets, on the 40 van states of L4 R0; every candidate's cost re-evaluated independently". |
| F3 | should-fix | **"370 epochs" (methodology §7, model_design §3.5) does not add up.** The math review's own table lists L4 44 + L1 93 + L2 95 + L3 96 + L5/r00 86 = 414 epochs. Its L4 run also used the old fixed drop order (44 epochs; the current default gives 46). | `m1_math_review_2026-10-21.md:157–159` against its summary on line 3. | Cite the current independent tests (46 L4 epochs, 151,710 combinations) for the current default. Describe the math review as having run on the pre-amendment candidate rule, with the correct count. |
| F4 | should-fix | **A proposal is presented as approved.** `docs/README.md` lists `scenario_spec.md` as "**Approved (v0.5, 22 Oct)**". But §17 holds D-46 conventions (Proposed, not approved) and D-52 settings (provisional). The spec header itself limits approval to D-27–D-32. | `git diff docs/README.md`; decision log rows D-46 and D-52 (status columns). | "Approved through v0.2 (D-27–D-32); v0.3–v0.5 additions incl. §17 proposed/provisional". |
| F5 | should-fix | **Stale or contradictory text.** (a) The spec §17 heading still says "(not implemented)". (b) The D-52 main row still says existing riders keep the committed-only drop order and the time limit is 300 s, both superseded by the amendments, with no inline marker (D-47 has one). (c) D-51 (update) is dated 2026-10-21, while the methodology, prereg and model_design say 22 Oct. (d) The prereg says "revised to match spec v0.4". (e) Code docstrings cite spec v0.4 and model_design v0.2 (`engine.py:1`, `__init__.py:3`). (f) Spec §4 says "γ 0.1 min/km", but D-52 says 0.1 points per km. (g) The D-52 alternatives column says the previous plan "always remains a candidate"; model_design correctly says "whenever it is still feasible". | `scenario_spec.md:333`; `decision_log.md:297`; `model_design.md:111`. | One documentation pass. Add `[superseded by amendment …]` markers in D-52. |
| F6 | should-fix | **Missing Phase 4 plan.** `docs/plans/README.md` and `docs/plans/phase3/log.md` point to `docs/plans/phase4/` ("Recorded in `docs/plans/phase4/log.md`"), but that folder does not exist. | `ls docs/plans/` shows master, osrm, phase1–3 only. | Create `docs/plans/phase4/plan.md` + `log.md` (versioned-plan rule), or remove the references. |
| F7 | should-fix | **Git hygiene.** (a) The uncommitted tree mixes the **21 Oct design consolidation** (D-44 wording through D-51, spec v0.4, model_design v0.2, methodology v1.0, design-review notes, archives, phase3 plan v4) with the **22 Oct M0–M1** work. HEAD still has spec v0.3 and model_design v0.1. (b) Under `methodology_pdf/_build/` only `methodology.log` is ignored: the `.aux/.lof/.lot/.toc`, `pass*.out` and a duplicate `methodology.pdf` would be committed. (c) `.venv-py310-backup/` is only partly ignored (`lib/`); 26 files show up as untracked. (d) The canonical run's `run_manifest.json` records `src_sim_uncommitted: true`, so the code that produced it cannot be identified. | `git status --short -uall`; `git show HEAD:docs/technical/scenario_spec.md \| head -1`; `.gitignore:221,229`. | Commit in two logical commits if practical (consolidation, then M0–M1). Add `docs/technical/methodology_pdf/_build/` and `.venv-py310-backup/` to `.gitignore`. Leave the `.pptx` out. Re-run `sim.run --level L4 --rule R0` after the commit so the manifest names a commit. |
| F8 | should-fix | **The §17.8 "plan audit after every epoch" is not implemented as a logged audit.** Feasibility and cost of the chosen routes are `assert`s (`dispatch.py:341`), as is capacity (`engine.py:200`). The transfer invariant and the commitment checks exist only in the tests or as departure-time errors. `assert` is also disabled under `python -O`. | `engine.py:288–324` (no audit record); spec §17.8. | Add an explicit audit (raise, not assert) and log its result in each epoch record, or mark the §17.8 item as deferred. |
| F9 | note | **Shifts.** Vans never go off duty: `_on_off_duty` only logs (`engine.py:157–161`), and off-duty is not an epoch trigger, although §17.4 lists it. A van that is free after `avail_end_s` stays dispatchable. This has no effect in L1–L5, because no request arrives after `avail_end_s` (checked in the availability and request files), and the closing rule keeps vans on anyway. | `engine.py:157`. | Implement before L7 (the shift-end rule is already open, §17.6). |
| F10 | note | **The 0-s-leg exception also reverses the "arrival beats the deadline" tie** for that arrival. Patience (class 60) is processed before the departure (class 90) that starts a 0-s leg. 0-s legs occur in L3 (1), L4 R0 (3) and L5/r00 (2); I did not find one coinciding with a deadline (inference from no cancellations in L4/L5 at those seconds; not exhaustively checked). | `engine.py:135–141`. | One sentence in §17.9. |
| F11 | note | **Consent boundary.** The code declines when `consent_u ≥ p_c`, while spec §17.5 says "`consent_u` > p_c declines". The two differ only when the values are exactly equal. | `engine.py:302`. | Align the wording. |
| F12 | note | **Candidate cache.** The cache key `(VanState, obs.open, Config)` is complete for `best_routes` and `evaluate`. Those depend only on van location, free time, riders (pickup times, destinations, party sizes), the committed wait, the open requests and the config, not on τ. The cache is scoped to one `Travel` object, and each test creates a fresh one. **No stale-reuse path was found**, provided `Travel` is not mutated. But the cache is unbounded and lives on the referee-owned `Travel` (`travel.__dict__`), so dispatcher state sits inside an engine object. | `dispatch.py:289–304`. | Move it to a dispatcher-owned LRU. Freeze `Travel` (`m_v`, `m_L`). |
| F13 | note | **Epoch log.** After a transfer, the epoch record holds only the re-solve. The plan the rule read is visible only through `lyft.reads` (the predicted pickup). | `engine.py:315–324`. | Log the first solve's status and objective as well (needed for the M2 audit). |
| F14 | note | **Test quality.** Gaps against the M0–M1 scope: there are no tests for `feasible_unproven`, the time-limit raise, tie-enumeration truncation, `kModelEmpty` (F1), `cancel_after_transfer`, `noshow_lyft`, off-duty, or rule-run solver statuses. Best-order brute force runs on L4 R0 states only, and synthetic adversarial instances would strengthen the dominance proof. Weak tests (not wrong): `test_capacity_and_guardrail_respected` checks only the guardrail (capacity is covered in the independent replay); `test_l4_answer_key_totals_are_across_rules` tests the key file, not the code; `test_observation_has_no_hidden_traits` checks field names only (the perturbation test covers the substance). No test checks the implementation against itself: the independent checker imports nothing from `sim`. | see §5 below | Add the listed cases. Rename the capacity test. |
| F15 | note | **Methodology wording.** (a) "The plan changes at most epochs while the queue lasts": the plan changes in 19 of the 36 epochs with open requests, and that count includes stops simply consumed. (b) Run times differ slightly between documents (D-52 amendment 26 s / 7.5 s; methodology 27 s / 7.8 s; my run 27.4 s / 8.1 s). These are diagnostics only. (c) In the narrative, `small_example` says "the MILP chooses it" without checking `ep["chosen"]`. It was correct in this run (`run.py:273`). | scratch runs | "about half of the epochs"; give a range of run times; assert that the narrative's plan 1 equals the chosen plan. |

## Details

### 1. Contract conformance (spec §17.1–§17.9)
These items conform:

| Item | Evidence |
|---|---|
| Integer clock and travel rounding: `round(t0 × m)` once per leg | `inputs.py:63–67` |
| Class order 10–90, with ties by key then sequence | `engine.py:28, 94, 121` |
| Triggers: request, cancellation or no-show of a request in van planning, on-duty, tick; Lyft-side events never trigger | `engine.py:146–253` |
| One epoch per second | `engine.py:130` |
| Commitment at departure, raising if the planned pickup is not `pending_van` | `engine.py:360–379` |
| Zero simulated latency | test at 18:15; departures in the same second |
| Transfer to `xfer_hold` at the decision; booking at +ℓ in class 70; a deadline inside the lag gives `cancel_after_transfer` and no booking (patience class 60 runs before booking class 70) | `engine.py:220–227` |
| Patience covers `pending_van`, `committed`, `xfer_hold` and `lyft_booked`; a curb arrival ends the clock | `engine.py:163–175` |
| Presence test at the curb with one draw for both modes; no-show at +180 s with no dwell | `engine.py:193–196, 235–237` |
| Cancelled pickup frees the van at arrival | `engine.py:188–191` |
| Closing rule: the run ends only when all requests are terminal and vans are idle | `engine.py:107` |
| Inputs not read: `p_noshow`, `lyft_noshow_u` and `eta_noise` are never loaded (`Hidden` excludes them); p comes from `Policy.p_absent` | `inputs.py:33–39`, `engine.py:38` |

Deviations: F8 (plan audit), F9 (off-duty), F10 (0-s-leg tie), F11 (consent boundary). The policy values for L4 (lag, consent, the 900-s gate) are read from `scenario.json` params in `run.policy_for`. That is consistent with the L4 design, but it puts a policy setting in an input file (note).

### 2. Information boundary
The dispatcher (`D.solve`) receives only:
- an `Observation` of frozen dataclasses (int and str values only, as checked in a test);
- the `Travel` oracle, which holds matrices only;
- a `Config`.

`dispatch.py` imports no engine or inputs module. Rule evaluation (`lyft.fires`) gets only public quantities. Consent and presence are applied by the engine. I found no path to the hidden traits other than Python introspection.

One quantity is observable but sensitive: during an absent rider's curb wait, `free_s = arrival + 180` reveals the no-show 180 s early. This is documented, and still open in methodology §9(2). The perturbation test (patience +1 h, consent and delay changed) leaves observations, plans and events identical. Cache: see F12.

### 3. D-52 conformance
These match D-52:
- K = 3;
- free drop order by default; the fixed order is a setting only and is never switched automatically;
- the M formula, which the independent test recomputes and matches exactly on every L4 R0 epoch;
- Ψ = 1000; guardrail max(1500 s, 2·direct + 300 s);
- the HiGHS options: threads 1, seed 0, presolve on, rel gap 0, abs gap 0.5, node limit 100,000; HiGHS 1.15.1 is installed;
- the time-limit safety stop raises (amendment 2);
- the exact integer objective;
- `tie_enumeration_incomplete`;
- numeric van-ID order in the tie rule.

Undocumented behaviour: F1 (status mapping), `max_tie_solves = 50` (`tie_enumeration_truncated`), and the candidate cache (F12). No heuristic fallback exists anywhere: `failed` runs committed work only.

### 4. Status claims (methodology v1.1 §7): reproduced
Runs were written to scratch with `run.run(..., out=…)`.

| Claim | Reproduced |
|---|---|
| L1–L3 keys to the second | yes (tests pass) |
| L4 R0: 46 epochs, all optimal | yes: 46 optimal; 45 unique, 1 tie |
| L1, L2, L3 epochs all optimal | yes: 93 / 95 / 96 |
| 22 transfers (4 XL), 4 declines across rule runs (R1(10) 3+1, R1u(10) 3+1, R2(15) 8+1, R3(2) 8+1, R1(15) none) | yes: each active rule has 1 XL and 1 decline |
| Waits 1.2–44.4 min; max ride 24.9 min; end 19:10 | yes: 1.23 / 44.37 / 24.85; end 19:10:00 |
| 151,710 combinations | yes (`pytest -s`) |
| 1,130 subsets / 113,879 orders | numbers yes; wording overstated (F2) |
| 370 epochs (math review) | does not reconcile (F3) |
| No ride over the guardrail | yes for L1–L4 and every rule run, and for L5/r00 (max ride − G = −2 s with m = 1.2) |
| L5/r00: 86 epochs, all optimal, ~25 s | yes: 86 optimal, 24.5 s |
| At 18:15, 3 pending with the cap as the reason | yes: `per_van` = "chosen route already has K=3 new pickups (cap)" for R002, R005, R006 |
| D-53 update: the best plan serving R002 is 116.5 points worse | yes: 116.543 |
| "optimal" qualified | yes: the methodology, model_design §3.3 and the narrative all say "over the candidate set … not over every possible route or the whole evening" |

Not reproduced (not attempted): "+173 points at the earliest physical pickup" and "with K = 4, R002 is the only pending request", because a K = 4 run is slow.

Rule runs are not covered by the §7 optimality claim. R2(15) and R3(2) each contain one spurious `failed` epoch (F1).

### 5. Tests
Command: `.venv/bin/python -m pytest -q` gave **101 passed in 250.70 s**.

The tests are meaningful: they would catch wrong dwell or travel (answer keys), wrong M or pending prices, a wrong tie rule or a missed optimum, class-order errors, double service, capacity breaches, and commitment moves.

- The independent checker (`tests/independent_check.py`) imports nothing from `sim`, so no test checks the implementation against itself.
- It does share the documented conventions with the implementation, for example the "allowed" ride limit taken from the committed-only route. A misreading of the rules that both sides share would not be caught; this is an inference about the method, not a defect found.

**Reproducibility:** I also checked across processes. Two runs with `PYTHONHASHSEED=1` and `=2` gave byte-identical `events.csv` and identical epoch records (wall times excluded), and the `outcomes.csv` matches the committed artifact `outputs/sim/L4_R0/`. Coverage gaps: F14.

### 6. Frozen inputs
- All 34 content hashes equal `FROZEN_v2.json`, including L1–L4 and L5/r00.
- No file under `data/` has an mtime after 2026-10-21. The dates are 09-29 to 10-02 (matrix and processed data) and 10-20/10-21 (v2 generation).
- `handcheck.csv` is not in the content hash, but its mtime is 21 Oct 13:35, unchanged.

### 7. Documentation consistency
The documents agree on these points:
- **Held-fixed dispatcher:** C is provisional (D-51 update), conditional on M5, and T is never a runtime fallback. This appears in spec §4/§19, model_design §5, the prereg and methodology §8.
- **Candidate rule:** free drop order, consistent everywhere except the stale D-52 main row (F5b).
- **D-53:** open everywhere, and the objective is unchanged.
- **No financial modelling:** D-45 is applied in the spec, the prereg, research_review and model_design.
- **No winning-rule claim:** no document claims a Lyft rule won.

Two status issues: F4 (the "Approved" label), and the D-50 margins, which the prereg uses as its decision rules while D-50 calls them proposals. That is acceptable in a draft, but it should be flagged.

### 8. Git hygiene: file classification
- **M0–M1 code and tests (new):**
  - `src/sim/{__init__,inputs,engine,dispatch,lyft,run}.py`;
  - `tests/test_sim_engine.py`, `tests/test_sim_independent.py`, `tests/independent_check.py`.
- **M0–M1 docs (22 Oct):**
  - `docs/technical/decision_log.md`: the D-51 update, D-52 and its amendments, D-53 and its update. The same file also carries the 21 Oct rows.
  - `scenario_spec.md` v0.5, `model_design.md` v0.3, `preregistration_v2.md`.
  - `scenario_methodology.md` v1.1, a new file that also contains v1.0 content.
  - `archive/{model_design_v0.2, scenario_spec_v0.4, scenario_methodology_v1.0}_2026-10-21.md`.
  - `research_notes/m1_math_review_2026-10-21.md`; this note.
  - `docs/technical/methodology_pdf/` (source, PDF, figures, README, SOURCES, CONFLICTS).
  - `docs/README.md`, `docs/ai_use_log.md` (22 Oct row), `docs/plans/README.md`, `docs/plans/phase3/log.md` (22 Oct row).
- **21 Oct consolidation, also uncommitted:**
  - decision log D-45–D-51 and annotations;
  - `archive/{model_design_v0.1, scenario_spec_v0.3, preregistration_v2_draft_2026-10-20}`;
  - `research_notes/design_review_{architecture,evidence,math}_2026-10-21.md`;
  - `docs/plans/phase3/plan.md` (v4) and `versions/v3_2026-10-12.md`;
  - `research_review.md` annotations;
  - the 21 Oct rows in `ai_use_log.md` and `phase3/log.md`.
- **Unrelated:**
  - `docs/presentations/BlueJayNightRide_Proposal.pptx`: a 2-byte change, mtime 16 Oct;
  - `.venv-py310-backup/`.
- **Generated or restricted, and correctly ignored:** `outputs/`, `data/`, `docs/evidence/`.
- **Generated, not ignored (F7b):** `docs/technical/methodology_pdf/_build/*` except the `.log`.

**One-line takeaway for the team:** the referee and dispatcher C reproduce every hand-checked answer, and every MILP choice equals brute-force enumeration over the candidate set. Before committing, fix the "failed" status labels, tighten three verification claims, and clean up the commit.
