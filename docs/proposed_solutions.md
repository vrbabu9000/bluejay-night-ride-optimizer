# Proposed Solutions

Candidate dispatch/routing strategies for Blue Jay Night Ride, evaluated against the shared replay framework described in [README.md](../README.md). Each strategy receives the same request stream, fleet state, and travel-time assumptions.

## 1. Rolling-horizon MILP (primary)

Dynamic Dial-a-Ride formulation described in the README. Node-arc MILP re-solved on each new request/state observation, with already-started actions fixed. Objective: overflow penalty + wait penalty + excess ride-time penalty + travel cost.

## 2. Baselines

- Nearest-feasible vehicle assignment
- Greedy pickup-and-drop-off insertion
- Reconstructed historical dispatch (if supported by data)

## 3. Predictive overflow / proactive Lyft assignment

Reactive overflow (triggered only after a rider has already waited past a threshold) wastes the wait time it's meant to avoid. Instead, predict overflow risk at request time and auto-assign a Lyft before the wait happens.

**Idea:** train a classifier that estimates, at the moment a request is placed, the probability the shuttle system will fail to pick the rider up within 20 minutes:

```
P(wait > 20 min | request features, current system state)
```

If `P` exceeds a tuned threshold, auto-assign a Lyft (or other TNC) immediately instead of queuing the rider for shuttle dispatch.

**Candidate features:**
- Current queue length / number of pending unassigned requests
- Number of available vehicles and their remaining capacity
- Distance / estimated travel time from nearest available vehicle to pickup
- Time of night (demand curve is not flat across a shift)
- Pickup/dropoff zone (some zones historically underserved)
- Day of week

**Why this over the MILP's built-in overflow variable alone:**
- The MILP's overflow decision is reactive — it only routes a request to overflow once the optimizer determines it can't be served in time, which may be late in the rider's wait.
- A predictive layer intervenes at request time, cutting wait time for the subset of riders who were going to overflow anyway, without waiting for the optimizer to converge on that conclusion.
- Ties naturally into the existing overflow penalty term in the objective — predicted overflows can be excluded from the MILP's assignment pool up front, shrinking the problem size for the on-time solve.

**Evaluation:**
- Precision/recall of the classifier against realized (or replay-simulated) wait times
- Net effect on mean/high-percentile wait time vs. reactive-only overflow
- Cost tradeoff: Lyft cost per proactively-diverted rider vs. shuttle capacity freed up
- False-positive cost: riders diverted to Lyft who would have made the 20-minute shuttle window anyway

**Open questions:**
- Data availability for historical wait-time outcomes to train/validate the classifier (pending JHU data audit)
- Whether threshold should be static or itself optimized against overflow-cost tradeoffs
- Cold-start behavior before enough historical data exists to train the model
