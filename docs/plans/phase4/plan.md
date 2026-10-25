# Phase 4, Simulator and dispatcher: plan (v1, 22 Oct 2026)

**Status:** in progress. M0–M1 done and verified on 22 Oct; the D-53 decision experiment and the curb-wait convention (D-54) done on 22 Oct; pending price A approved provisionally; M2 done and verified on 22 Oct. M3 waits on the L5 policy settings (methodology §8).

**Authority.** This plan only sequences the work. What to build is in `docs/technical/scenario_spec.md` v0.7 §17 (build contract) and `docs/technical/model_design.md` v0.5; decisions are in `docs/technical/decision_log.md`; the milestone list and its reasons are in `docs/technical/scenario_methodology.md` v1.3 §8.

**Previous versions:** none. Why it changes: `log.md`.

## Scope fixed by the team (22 Oct 2026)
- Dispatcher C (restricted route-selection MILP, HiGHS) is provisionally the dispatcher held fixed (D-51), conditional on the M5 benchmark. T is a contingency or later robustness variant, never a runtime fallback.
- No financial modelling (D-45). Lyft tracking keeps operational outcomes and resource counts.
- Frozen inputs are read, never changed; routing data is not rebuilt.

## Milestones
| Milestone | Content | Status |
|---|---|---|
| M0 | Event engine reproduces L1–L3 answer keys and the L4 pre-18:15 Lyft mechanics | **Done 22 Oct** (methodology §7) |
| M1 | C on L4 under R0, with event and epoch logs and a readable narrative | **Done 22 Oct** |
| M1.5 | D-53 decision experiment (original / A / B pending price) and curb-wait convention D-54 | **Done 22 Oct**; A recommended, awaiting approval |
| M2 | Lyft rules all evening with C on L4 | **Done 22 Oct** (D-55) |
| M3 | L5, 30 seeds: pairing, metrics, bootstrap CIs, pilot variance | Not started; needs the L5 policy settings and metric set |
| M4 | L6 builder, 64 / 50 / 54 (new scenario generation; needs go-ahead) | Not started |
| M5 | First hour, 5 vans, 64 requests: benchmark of C | Not started; confirms or overturns D-51 |
| M6 | Full 168-request, five-van demonstration | Not started |
| M7 | Experiment grid | Not started; no Lyft-rule comparison before then |

Not in Phase 4 scope until decided: heuristic T, hindsight H, calibration, the L7 taper and shift ends.
