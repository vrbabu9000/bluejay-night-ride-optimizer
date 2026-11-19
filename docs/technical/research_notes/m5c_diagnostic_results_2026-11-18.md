# Diagnostic results: where the fixed drop order costs, and where exact reordering costs time (18 Nov 2026)

**Status:** exploratory, not preregistered. The plan (`m5c_diagnostic_plan_2026-11-18.md`) was written before the run. No decision rests on this alone.
**Command:**
- `python -m sim.diag_cf run --pattern both --workers 6`, then `python -m sim.diag_cf summary`;
- outputs go to `outputs/sim/m5/diag_cf/` (`summary.md` and per-night CSVs, git-ignored).
- Code: `src/sim/diag_cf.py`. It is not in the fingerprint, and it reads saved runs only, never hidden rider traits.

**Data:** every saved re-plan of C's M5b runs:
- **high_5:** 30 nights, 4,578 epochs, 22,890 van-epochs;
- **base_5:** 30 nights, 3,630 epochs, 18,150 van-epochs.

**Rebuild check: exact.**
- **Logged costs:** 0 epochs failed to reproduce C's logged costs (committed-only and chosen routes).
- **Full re-solves:** all 3,955 full C re-solves on lighter epochs matched C's logged objective to the unit.
- **Totals:** the rebuilt totals also match the runs. C's median per high night is 60.6 min (run record: 1.0 h). C-F solved on C's states takes a median 15.3 min per night (M5c's real C-F runs: 15.2).

## Findings
1. **The fixed order costs waiting, not riding.**
   - In every load group, about 105% of the gap is extra wait penalty, and about −5% is ride time (C-F rides are slightly shorter).
   - **Why:** with the order fixed, a new pickup often cannot go before a drop-off without pushing an aboard rider over the ride guardrail. So the new rider waits until the drops are done.
   - **How this fits M5c:** it matches C-F's rider result, more requests not reached within 20 min.
2. **The value of exact reordering sits in moderately loaded vans. Its compute cost sits in the full ones.** High load, distinct decisions:

   | Parties aboard the van | Share of van re-plans | Fixed order binds | Share of the objective lost by fixing the order |
   |---|---|---|---|
   | 0–1 | 38% | never | 0% |
   | 2–4 | 54% | 16–38% | 76% |
   | 5 | 6% | 39% | 15% |
   | 6+ | 2% | 46–47% | 9% |

   By epoch, the re-plans where some van carries 6 or more parties are 11% of re-plans. They take 65% of C's time (38 of 58 h) and account for 15% of the objective gap.
3. **A switch by van fullness gives a smooth trade-off, but no setting passes the 15-min gate at high load while keeping most of the value.**
   - **How the estimate works:** if any van is at or over the threshold, the re-plan is costed at C-F's time; otherwise at C's.
   - **What the estimate ignores:** that the trajectory would change.

   | Fix the order in vans with ≥ | High: est. median min per night (max) | High: value kept | Base: est. median (max) | Base: value kept |
   |---|---|---|---|---|
   | never (C) | 60.6 (≈1,400) | 100% | 8.0 (33) | 100% |
   | 7 parties | 47 (599) | 98% | 8.0 (33) | 100% |
   | 6 parties | 38 (97) | 91% | 6.5 (33) | 99% |
   | 5 parties | 24 (56) | 76% | 4.9 (21) | 90% |
   | 4 parties | 16 (44) | 45% | 2.2 (11) | 60% |
   | always (C-F) | 15.3 | 0% | 1.5 | 0% |

   - **Base load:** a switch at 6 parties is nearly free (99% kept).
   - **High load:** a switch at 6 keeps 91% of the value and removes the extreme nights (the worst night drops from about 23 h to about 1.6 h), but it is still about 2.5 times the gate.

## What this means
- **The "switch when full" hybrid** is a reasonable safety valve against runaway nights. It is not a way to make high-load evenings cheap without losing riders.
- **The cost of exactness lives in the tail.** About a tenth of re-plans take two-thirds of the time. That points to a **time budget per re-plan** (the anytime idea: start from the C-F plan, improve until the budget runs out), not a fixed rule. A budget spends effort where it pays and caps the tail.
- **These are one-moment objective gaps along C's trajectory, not rider outcomes.** A switch or a time budget would need its own frozen test on fresh nights (r30 and on) before any claim about riders.
