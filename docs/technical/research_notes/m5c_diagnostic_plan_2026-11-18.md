# Diagnostic: where does the fixed drop order cost, and where does exact reordering cost time? (plan, 18 Nov 2026)

**Status:** exploratory, not preregistered. Written before the script was run. No decision rests on it alone; any dispatcher it suggests (for example a switch by riders aboard) would need its own frozen test on fresh nights.
**Asked by:** the user, 18 Nov ("lets do the diagnostics"), after M5c (`m5c_results_2026-11-17.md`).
**Question:**
- Is the 1–2 pp that exact reordering buys concentrated in vans carrying many riders, the same states where it costs the most time?
- If yes, a switch that fixes the order only when a van is full saves time but keeps the loss, and is unpromising.
- If the gain comes mostly from lightly loaded vans, the switch is promising.

## Data
- **States:** every saved re-plan (epoch) of C's M5b runs, `outputs/sim/m5/m5b/{high5,base5}_C_R0_t120/r00–r29`.
  - High load is the focus; base is for contrast.
  - r26 high is included: its states are valid, and the failed check concerns attribution after a no-show, not the plan.
- **What is rebuilt:** each epoch's observation, from:
  - the logged van states;
  - the night's request list (origin, destination, party size, request time).
- **What is not used:** the hidden traits (patience, presence).
- **Rebuild check:** every rebuilt observation must reproduce C's logged costs exactly:
  - the committed-only route of every van;
  - the chosen route of every van;
  - C's objective, from a full solve, on a sample of light epochs.

  An epoch that fails the check is reported and excluded.

## Measures (counterfactual, one epoch at a time; not rider outcomes)
1. **Binding, per van-epoch:** C's chosen route drops the van's existing riders in a different order from the committed-only route.
2. **Same-request cost gap, per van-epoch:** for the request set C chose for that van, the best fixed-order route's cost minus C's route cost, in objective points (≥ 0 by construction). If no fixed-order route for that set meets the guardrail, the van-epoch is counted as infeasible.
3. **Plan-level gap, per epoch:**
   - a full C-F solve on the same state, priced with C's own pending prices;
   - the result is the extra requests left pending, plus the cost gap in points (≥ 0 by construction);
   - also C-F's solve time against C's logged solve time.
- **Grouping:**
  - per van-epoch, by the number of rider parties aboard or committed to that van (0–1, 2, 3, 4, 5, 6, 7+);
  - per epoch, by the largest such count in the fleet.
- **The key table:** for each group, its share of van-epochs, of C's compute time, and of the total gap.

## What it cannot show
- **Rider outcomes.** The gaps are in the dispatcher's own objective at one moment, along C's trajectory. C-F's real runs follow different trajectories, and M5c measured their rider outcomes.
- **Long-run effects.** A small myopic gap can compound, and a large one can wash out.
