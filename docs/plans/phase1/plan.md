# Phase 1, Evidence: plan (v1, as executed)

**Status:** done; **G1 passed 30 Sep 2026.** The source is master plan v2, A2 and Parts B and C (`../master/plan_v2_2026-09-29.md`). This file records the plan as it was executed.

## Goal
Digitize every chart in the April 2026 TransLoc dashboard PDF (12 charts on 11 pages), each with an interval, an overlay check, a recreated chart and a one-page brief. Then reconcile the charts against each other (gate G1).

## Method
- **Bar and line charts (pp. 6–12):** take the original pixels with `pdfimages`; calibrate the axes from gridlines and ticks; mask by the Highcharts colours; give each value an interval of ±(1 px + marker radius); reproduce the tooltip anchors; draw an overlay; do an independent second read.
- **Maps (pp. 2–5):** georeference with a scale plus offset from labelled points of interest; for each bubble record the centre, the count read and the colour bucket (the colour gives the digit count, a built-in check); flag bubbles cut off at the edges; reconcile campus vs city bubbles without double counting. Two readers (A, plus a blind B).
- **Brief per chart:** title, filter, definition, units, anchors, error, quirks, what it can and cannot tell us, and which tasks use it.

## Work split
- **Main session:** `digitize.py` and the p11 worked example; georeferencing the maps and reader A; reviewing every brief.
- **Agents:**
  - E1: p6 + p9;
  - E2: p7 + p8;
  - E3: p12;
  - E4: p10;
  - E5: blind second read of every map bubble.

## Gate G1 (reconciliation)
- Tooltip anchors reproduced within tolerance.
- Overlays inspected.
- The second read agrees.
- The colour/digit rule holds for every bubble.
- Every ledger residual is explained.

## Outputs
- `data/processed/obs_*.csv`, `observations.csv`, `map_*.csv`, `map_clusters.geojson`.
- `docs/evidence/` (briefs, `reconciliation_ledger.md`, `data_quality.md`).
- `outputs/evidence/`.
