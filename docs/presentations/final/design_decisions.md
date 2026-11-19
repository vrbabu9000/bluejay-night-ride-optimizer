# Design decisions to explain in the final presentation (1 Dec 2026)

**Purpose.** These are the choices that make the results defensible. Each entry says:
- what we chose and what we gave up;
- the evidence behind it;
- one way to show it on a slide (one visual, short takeaway, detail in the speaker notes).

Source rows are in `docs/technical/decision_log.md`. This list is kept current as decisions land.
Started 17 Nov 2026 at the user's request: "these are very valuable design decisions which i want to explain in my final presentation".

## 1. Synthetic nights built from the April aggregates
- **Chose:** generate nights consistent with April 2026's aggregate TransLoc dashboard. We had no trip-level replay.
- **Gave up:** replaying real nights. No trip-level data exists for us.
- **Why:** this is Prof. Kearsley's own framing: gather sufficient statistics, separate operating regimes, then build synthetic data consistent with the aggregates.
- **Evidence:** the G1 reconciliation, and frozen nights with content hashes.
- **Slide idea:** April dashboard → recipe → a night of requests on the map.

## 2. Hold the van dispatcher fixed, compare Lyft rules (D-25, D-51)
- **Chose:** one van dispatcher, held fixed while Lyft-transfer rules vary.
- **Gave up:** a broad "which dispatch algorithm is best" study.
- **Why:** the research question is about Lyft rules. Varying two things at once confounds them.
- **Slide idea:** two dials, one locked.

## 3. C: choose among precomputed routes, solved exactly every re-plan (D-51, D-52)
- **Chose:** a route-selection MILP. Up to K = 3 new requests per van, the best stop order per route, and HiGHS picks one route per van.
- **Gave up:** the node-arc MILP in the proposal, which is too slow to re-solve every two minutes.
- **Evidence:** every re-plan was proven optimal over its candidate set; 0 node-limit epochs in M5a.
- **Slide idea:** candidate routes fanning out from each van, one chosen.

## 4. Free drop-off reordering: plan quality vs compute (D-52 amendment)
- **Chose:** reorder all of a van's stops, including drop-offs of riders already aboard.
- **Gave up:** speed. The fixed-order rule was faster, but it lost up to 286 objective points in one re-plan and was binding in 45 of 132 checked cases (L4).
- **Consequence found later:** time grows explosively with riders aboard. The median re-plan took 0.2 s with 3 aboard and 385 s with 7, and one high-load first hour took 23.3 h.
- **Follow-on (M5c, 17 Nov):** a variant C-F keeps the aboard riders' drop order fixed. We tested it against C under criteria frozen before the runs, and it failed both ways:
  - **speed:** median high-load night 15.2 min, just over the 15-min gate (C took about 1 h);
  - **riders:** about 2 pp more requests unreached within 20 min at high load (+2.08 pp [+0.50, +3.78]).
  So C was kept as tested, and high-load full evenings are reported as a compute limitation. The result also measures what exact reordering buys: about 1–2 pp of riders. C-F still beats greedy by about 9.5 pp, so most of C's gain comes from re-planning all open work together.
- **Diagnostic (18 Nov, exploratory):** the value of exact reordering sits in moderately loaded vans (2–4 parties, about 76%), while its compute cost sits in the full ones (6+ parties: 11% of re-plans, 65% of time). Fixing the order costs new riders waiting, not ride time. So a "switch when full" rule is a safety valve, not a cure; a time budget per re-plan is the natural next design.
- **Why it matters for the talk:** we had a hypothesis we liked, tested it with a pass mark set in advance, and it lost. We report it, and the rule stopped us from moving the threshold after a 15.2-vs-15 miss.
- **Slide idea:** run time against riders aboard (steep curve), then C vs C-F: faster, but not fast enough, and it costs riders.

## 5. A simple greedy baseline G, to answer "when does the MILP beat greedy?" (D-60)
- **Chose:** insertion that never reassigns, sharing everything else with C (engine, cost, guardrail).
- **Why:** this is the instructor's main open question. A tie would also have been a presentable finding.
- **Slide idea:** same night, two dispatchers.

## 6. Measure compute blind, before looking at any outcome (M5a)
- **Chose:** C's compute benchmark reported compute only, with no rider outcome read.
- **Why:** any change made after the benchmark (K, cadence, budget) then can't be influenced by which dispatcher looks better.

## 7. Freeze the criteria before running, and commit them to git (D-60, D-61)
- **Chose:** a preregistration fixing the measure, margin, bootstrap, seed and stopping rule. It was frozen and committed (`e84f73b`) before the first M5b run.
- **Why:** the result can't have been tuned after the fact. Git timestamps prove the order.
- **Slide idea:** a timeline of freeze → runs → analysis.

## 8. A fixed-order stopping rule instead of fewer nights or a changed C (D-61)
- **Chose:** run cells in a fixed order with fixed cutoffs. Each analysis uses the unbroken run of finished nights.
- **Gave up:** (b) 10 nights for high load, which gives a wider interval; (c) changing C for every cell, which would have meant re-running M5a.
- **Why:** it keeps C and the night count intact and cannot be steered by results.

## 9. Pause on any failure; keep the rule even when the failure is the check's fault (D-62)
- **Chose:** when r26 failed a guardrail check, the batch paused. Diagnosis showed a check defect, not a simulator one. We kept the frozen rule (cell 3 uses 26 nights) and reported all 30 nights only as a labelled deviation.
- **Gave up:** fixing the check and re-running 300 runs after the freeze.
- **Why:** the frozen record stands, and the conclusion is the same either way (−12.5 vs −11.9 pp).

## 10. One primary measure, paired nights, a margin set in advance (D-50, D-37)
- **Chose:**
  - the share of requests not reached within 20 min;
  - paired per-night differences (the same requests and hidden draws for both dispatchers; the 6-van case reuses the 5-van requests);
  - a 95% bootstrap;
  - ±2 pp for "practically equivalent".
- **Why:** pairing removes night-to-night noise. The margin turns "no difference" into a testable claim.
- **Slide idea:** a P90-free gauge, the share reached within 20 min.

## 11. Re-planning on events makes the re-plan timer almost irrelevant (M5b, cell 4)
- **Finding:** C at 60 s, 120 s and 300 s gives the same result, because C also re-plans on every request, cancellation and no-show. The timer only adds re-plans with nothing new to react to.
- **Why it matters:** it stops the misreading that "slow re-planning is fine".

## 12. Claim the difference, not the levels
- **Chose:** headline the paired C − G difference, not "22% unreached".
- **Why:** patience, presence and the Lyft delay are ASSUMED placeholders. Levels move with them. The paired difference is the quantity the study was designed to compare, though its sensitivity to these placeholders has not been tested. G is not TransLoc, which also reassigns.
