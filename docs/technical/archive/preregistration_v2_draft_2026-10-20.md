# Pre-registration v2 (DRAFT, 20 Oct 2026)

**Status:** a draft written from `scenario_spec.md` v0.2. It is **frozen when the first L6 comparison run starts.**
- Changes before then are allowed, and are logged at the bottom.
- Changes after then are dated amendments, with the original text kept.
- v1 (`preregistration.md`) is paused and unchanged.

## 1. Question
**Primary.** Which dispatcher-initiated Lyft transfer rule gives the best rider outcomes for its resource cost, holding the van dispatcher fixed (TransLoc-like T)? Under which demand pattern and fleet level? Why?

The study is about **policy**, not algorithm.

## 2. Arms (one rule at a time; everything else fixed)
- **The six rules:** R0 never; R1(10); R1(15); R1u(10); R2(15); R3(2).
- **Fixed for every rule:** dispatcher T with Δ = 120 s, the commit rule and the objective (D-29); lag 2 min; consent 1.0; unlimited dispatcher capacity; Lyft delay lognormal with a median of 8 min.
- **Conditions:**
  - pattern: base / burst / far-trip / high;
  - fleet: 5 / 6 vans.
- **Nights:** 30 paired nights per condition. The same nights are used for every rule.

## 3. Metrics
**Primary.** Two rider-outcome measures are each paired against R0 and reported against Lyft trips per night (the resource cost), as a frontier:
- passenger-weighted **P90 wait**, from request to actual pickup in either mode;
- the **share of requests not picked up within 15 min**, where abandonment after 15 min counts as a miss.

**Secondary:**
- median and P95 wait;
- the share over 10 and over 20 min;
- cancellation rate; completed-service rate;
- ride time P90; detour P90; share of rides over 20 min; guardrail violations;
- van-km and empty km; Lyft km;
- ETA churn; backlog after the window closes;
- subgroups: parties of 5 (transferred by Lyft XL; D-33) and Peabody zone; XL trips counted separately from standard Lyft trips.

**Explanation metrics.** As in spec §9.3: transfer timing, who was transferred, the wait split, spill-over, cancellations avoided, cost per minute of P90 reduction, and 2–3 traced nights.

## 4. Decision rules
- **Paired differences** with 95% bootstrap confidence intervals (10,000 resamples of nights).
- **Rule A is "better" than rule B on a condition** if A's primary outcomes are not worse (CI includes 0 or favours A) **and** A uses fewer Lyft trips, **or** A improves an outcome at equal Lyft use. Otherwise both lie on the frontier, and the trade-off is reported.
- **Minimum meaningful difference:** 1 min of P90 wait, or 2 percentage points on the share over 15 min.
- **Power check** on L5/L6 pilot variance: if CI half-widths exceed those minimums at 30 nights, use 60 nights for every cell.
- **Confirmatory hypotheses, stated in advance:**
  - **H1.** Rules that act on predictions (R2, R3) beat R1(15) on P90 wait in the burst pattern, at a higher Lyft use.
  - **H2.** Under far-trip, the benefit of any transfer rule over R0 is larger than under base.
  - **H3.** With 6 vans, the differences between rules shrink relative to 5 vans.
  - **H4.** The ranking of rules is the same under dispatcher T and T− (robustness).

  Everything else is exploratory.

## 5. Fixed before any comparison
Calibration (L7 base) fixes the following, keeping the identified set:
- the load ratio ρ;
- the patience scale;
- the travel multiplier;
- the status-quo threshold.

The main comparison is re-run at the extremes of the identified set.

## Change log (pre-freeze)
- 2026-10-20: draft created from scenario_spec v0.2.
