# Phase 3, Build the world: plan (v3, 12 Oct 2026)

**Status:** in progress.
- 3A research: done, and reviewed critically on 12 Oct.
- 3B scenario definition: **approved 20 Oct** (spec v0.2; decisions D-27–D-32).
- 3C data generation: **L1–L5 generated 20 Oct** (`data/scenarios/v2/`); L6–L7 after calibration.
- 3D local OSRM: complete.
- The v1 generator, ladder and grid are **paused, not deleted**.

**Previous versions:** `versions/v1_2026-10-01.md`, `versions/v2_2026-10-02.md`. Why it changed: `log.md`.

## Why v3
The team accepted the direction set out below (decisions D-23–D-26), and asked for a critical review before the scenarios are finalised.
- the scope is Homewood only and door-to-door;
- the baseline is TransLoc-like;
- the primary question is Lyft transfer rules.

The review (12 Oct) found:
- the vendor evidence is historical (2016);
- the Peabody boundary and the targets need a decision or context;
- the Homewood fleet is uncertain;
- several assumptions can reverse conclusions.

So 3B now has a full draft specification, mathematical design and computing plan.

## Steps
| Step | What | Output | Gate | Status |
|---|---|---|---|---|
| **3A** Research + critical review | Operations of TransLoc/Hopkins; review of the framing; audit of the assumptions; missing angles | `transloc_operations.md` v1.1, `research_review.md`, `research_notes/` | Team review | **Done** |
| **3B** Scenario definition | Inputs / policies / outcomes; Lyft rules; ladder L1–L7; compact experiment matrix; schemas; seeds; validation; calibration limits | `scenario_spec.md` v0.1, `model_design.md` v0.1, `compute_feasibility.md` v0.1 | **Team agrees in writing, and decisions D-A…D-G are settled** | **Approved 20 Oct** (v0.2) |
| **3C** Scenario generation | Generator v2 (latent draws, availability profile, v2 matrix + MANIFEST); then L1–L5 files; L6–L7 after calibration | `data/scenarios/v2/` | Validation criteria in `scenario_spec.md` §12 | **L1–L5 done 20 Oct**; L6–L7 after calibration |
| **3D** Local OSRM | Pinned routing, v2 matrix, routes, snaps | `../osrm/` | Its acceptance checks | **Complete**; cross-machine policy proposed (P-02) |

## Sequence after approval (each step needs its own go-ahead)
1. **Approve the specification:** D-A…D-G, plus the parameter proposals P-01–P-12.
2. **Re-write the pre-registration** from the approved specification: rules, thresholds, metrics, hypotheses, seeds.
3. **Generate the scenarios** (3C): the generator v2, L1–L5 files and the hand-check sheets for L1–L4.
4. **Phase 4 (separately authorised):** set up a lock file and HiGHS, then build the simulator, dispatchers T/G/C/H and the Lyft module; pass L1–L4 validation.
5. **Run the bounded benchmark** (B0–B5; B6 separately).
6. **Calibrate:** L7 base; keep the identified set.
7. **Generate L6–L7 and run the policy experiments:** primary matrix, robustness blocks, frontiers.

## What carries over from v1 (reused)
- Locations, zones and depot rule.
- Gravity × IPF demand (`demand.py`).
- Sampler machinery: per-component seeds, content hashes, byte-identical rebuilds.
- The 32 tests.
- The v2 travel matrix and snaps.

## Paused (kept; superseded in draft by scenario_spec v0.1)
- `scenario_contract.md` and `preregistration.md` (banners added);
- the v1 ladder, `FROZEN.json` and the 330-scenario grid.
- Decisions D-04, D-06, D-12, D-20, D-21 and D-22 are under revision (decision log, 12 Oct section).
