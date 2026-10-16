# Phase 2, Insights: plan (v1, as executed)

**Status:** done, 30 Sep 2026. The source is master plan v2, Part B (the 10 tasks) (`../master/plan_v2_2026-09-29.md`). This file records the plan as it was executed.

## Goal
Answer ten questions from the digitized April data, each with a figure, a CSV of its numbers and a brief. Every number is traceable to observation ids and carries an evidence label. Also build zones v0 and an OSRM travel-time table, which T6 and T8 need.

| Task | Question | Owner |
|---|---|---|
| T1 | Is the system supply-limited? (rides per van-hour by hour) | Main |
| T2 | How big is cancellation? | Agent I1 |
| T3 | Do cancellations rise when service degrades? (+ T3b, Apr 17) | Main |
| T4 | Party size | Agent I1 |
| T5 | Occupancy (Little's law, lognormal ride time) | Main |
| T6 | Detour factor (observed ride vs direct OSRM) | Main |
| T7 | Lyft share; Lyft vs cancellations | Agent I2 |
| T8 | O-D structure, net flows by zone | Main |
| T9 | Shift mismatch (vans vs rides by hour) | Agent I2 |
| T10 | Reconciliation ledger | Agent drafts, main signs |

## Rule
Every figure has a "cannot tell us" line; no number without a trace.

## Outputs
- `src/insights/t01…t10`;
- `outputs/insights/*`;
- `docs/evidence/insights/t01…t09.md`;
- `data/processed/zones_v0.csv`, `tt_points_v0.csv`, `tt_zones_v0.csv`.
