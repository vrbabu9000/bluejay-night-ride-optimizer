# Pre-registration v2 (DRAFT, revised 22 Oct 2026)

**Status:** a draft written from `scenario_spec.md` v0.2 and revised to match spec v0.4 (21 Oct; D-45, D-49–D-51; the 20 Oct draft is archived in `archive/`). It is **frozen when the first L6 comparison run starts.**
- Changes before then are allowed, and are logged at the bottom.
- Changes after then are dated amendments, with the original text kept.
- v1 (`preregistration.md`) is paused and unchanged.

## 1. Question
**Primary.** Which dispatcher-initiated Lyft transfer rule gives the best rider outcomes for the resources it uses (Lyft bookings, van-km), holding the van dispatcher fixed? Under which demand pattern and fleet level? Why? No money is modelled (D-45).

*Dispatcher (D-51 update, 21 Oct):* the held-fixed dispatcher is **provisionally C**, the restricted route-selection MILP (HiGHS) with the candidate rule of D-52, conditional on the M5 benchmark. It shares the published structure of TransLoc's dispatcher but is not a reproduction of it. **Open before freeze:** the pending-price question (D-53), which changes ETAs and pending status that the rules read.

The study is about **policy**, not algorithm.

## 2. Arms (one rule at a time; everything else fixed)
- **The six rules:** R0 never; R1(10); R1(15); R1u(10); R2(15); R3(2).
- **Fixed for every rule:** the van dispatcher C (provisional, D-51; candidate rule D-52) with Δ = 120 s, the commit rule and the objective (D-29); lag 2 min; consent 1.0; unlimited dispatcher capacity; Lyft delay lognormal with a median of 8 min.
- **Conditions:**
  - pattern: base / burst / far-trip / high;
  - fleet: 5 / 6 vans; the sixth van uses the **same** requests as five (D-37).
- **Nights:** 30 paired nights per condition. The same nights are used for every rule. Nights are **not** paired across patterns (each pattern has its own demand streams, D-49).

## 3. Metrics
**Primary (D-50).** One rider-outcome measure that counts **every** request, paired against R0 and reported against Lyft bookings per night (resource use), as a frontier:
- the **share of requests not reached by a vehicle (van or Lyft) within 15 min** of the request. A rider who cancelled, or who was never reached, counts as not reached. "Reached" means a **curb arrival**; it is named as such so the wait-to-boarding metrics are not redefined.

**Secondary (D-50; replacing "co-primary" in the 21 Oct draft, which contradicted D-50):** passenger-weighted **P90 wait** from request to actual pickup in either mode, among riders picked up. It leaves out riders who cancelled, so a rule that loses its longest waiters to cancellation can look better; it is always read beside the primary measure.

**Secondary:**
- median and P95 wait;
- the share over 10 and over 20 min;
- cancellation rate; completed-service rate; no-show rate per vehicle arrival;
- ride time P90; detour P90; share of rides over 20 min; guardrail violations;
- van-km and empty km; Lyft km; Lyft decisions, bookings, completed trips, cancellations after transfer and Lyft no-shows, standard and XL separately (no money, D-45);
- ETA churn; backlog after the window closes;
- subgroups: parties of 5 (transferred by Lyft XL; D-33) and Peabody zone.

**Explanation metrics.** As in spec §9.3: transfer timing, who was transferred, the wait split, spill-over, cancellations avoided, resource use beside the outcome change, and 2–3 traced nights.

## 4. Decision rules
- **Paired differences** with 95% bootstrap confidence intervals (10,000 resamples of nights).
- **Margins δ (minimum meaningful difference):** 2 percentage points on the primary share; 1 min of P90 wait.
- For a metric where larger is worse, with D = A − B:
  - **A is non-inferior to B** if the **upper** 95% bound of D is below +δ;
  - **A is better than B** if the upper bound is below 0.
  - *A confidence interval that contains 0 does **not** show "not worse"; it shows only that the data cannot tell (D-50, replacing the 20 Oct wording).*
- **Rule A dominates rule B on a condition** if A is non-inferior on both outcome measures **and** uses fewer Lyft bookings (upper bound of the booking difference below 0), **or** A is better on an outcome and non-inferior on bookings. Otherwise both lie on the frontier, and the trade-off is reported.
- **Power check:** run a pilot on seeds **outside** the main 30 (L5/L6 variance). If the expected CI half-width at 30 nights exceeds **0.7 δ** (≈ 80% power for a true difference of δ), use 60 nights for every cell.
- **Confirmatory hypotheses, stated in advance:**
  - **H1.** Rules that act on predictions (R2, R3) beat R1(15) on P90 wait in the burst pattern, at a higher Lyft use.
  - **H2.** Under far-trip, the benefit of any transfer rule over R0 is larger than under base. *(The two patterns use different nights, so this is an **unpaired** comparison of two paired effects; its CI is wider.)*
  - **H3.** With 6 vans, the differences between rules shrink relative to 5 vans.
  - **H4.** The ranking of rules is the same under dispatcher C and under T, if T is built (robustness; was "T and T−" before C was provisionally selected, D-51).

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
- 2026-10-22: dispatcher C provisional (D-51); P90 wait made secondary, consistent with D-50; H4 restated for C vs T; D-53 open before freeze.
- 2026-10-21: no money (D-45); primary metric counts every request; non-inferiority margins replace "CI includes 0"; power at half-width ≤ 0.7 δ with pilot seeds outside the main 30; H2 marked unpaired; sixth van on the same requests; dispatcher algorithm open (D-51) (D-49, D-50).
