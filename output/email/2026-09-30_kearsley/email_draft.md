# Reply to Prof. Kearsley (final, confirmed 1 Oct 2026)

**Subject:** reply in his thread ("Re: ..."). If you start a new one: *One step up the gradient*

**Attachments (two):**
1. `FourSight_three_approaches.png`: also paste it inline where marked below
2. `FourSight_project_map.pdf`

---

Professor Kearsley,

A gradient is local information, so we took a step and looked again. It still points the same way.

We gave your undefined "quality" six questions per chart. The numbers are sound: independent charts agree within 0.4%. The definitions are not: "Canceled" is never defined. And as your first note predicted, the aggregates pull apart into regimes. Completions follow the fleet, not the requests, and each extra minute of median wait comes with about seven more points of cancellations.

[image inline]

Height is defensibility, from dark (non-defensible) to green (defensible). We dropped the trip-level plan when that data never came, took one step on the aggregate data, and now stand at a fork:

1. **Simulation and dispatch (our project, the van).** Synthetic nights consistent with the aggregates, and five dispatchers, from nearest-van to clairvoyant, on identical nights. The gaps between them are priced as the value of pooling, waiting, coordination and information.
2. **Events, zones and traffic (a side branch).** April 17 was the opening night of the 150th All-Alumni Weekend, with two JFX lanes closed. It carried a median night's riders but the month's longest waits and fewest van rides. The system slowed; demand did not. When, where and how a night strains may be predictable, and each new monthly report would test that out of sample.
3. **What's in plain sight that we can't see.** A climb only sees the slope underfoot. Where would you point the lantern?

The second attachment maps where we started, what we abandoned, and where the data flows next.

Best regards,
[Your name], for Team FourSight

P.S. The paths in the picture are true gradient flows of the landscape drawn. We checked.

---

## Where each claim comes from (for the team; do not send)

| Claim | Source |
|---|---|
| Charts agree within 0.4% | `docs/evidence/reconciliation_ledger.md` (T10, G1) |
| "Canceled" undefined | `docs/evidence/data_quality.md`, dimension 3; G1 caveat |
| Completions follow the fleet, not the requests | T1: rides per van-hour 4.8-6.2 by hour; daily completions vs requests slope -0.02, r -0.04 |
| About 7 points of cancellations per extra minute of median wait | T3: slope 7.2 points, r 0.74 (0.72 within weekday). Associational, hence "comes with", not "causes" |
| April 17 | T3b (`outputs/insights/t03b_apr17_profile.csv`): total riders 1,456, the month's median; median and P90 wait and ride the month's highest; 543 completed van rides, the fewest. Event and JFX closure verified in `docs/evidence/context/april_2026_calendar.md` (JHU post and Hub; Baltimore DOT notice) |
| "test that out of sample" | Only if Hopkins keeps sending monthly reports (not yet confirmed) |
| "Paths are true gradient flows" | `docs/technical/figures/build_gradient_figure.py`, asserted in code. The fork is a flat point, so each approach leaves it with one short first step, then follows the gradient flow |
