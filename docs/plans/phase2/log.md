# Phase 2, Insights: log (append only)

| Date | Version | Event | Why / who | Evidence / outcome |
|---|---|---|---|---|
| 2026-09-29 | v1 | Plan approved as part of master plan v2 | Team (user) | `../master/plan_v2_2026-09-29.md` |
| 2026-09-29 | v1 | Zones v0 (16 zones, count-weighted k-means) and the OSRM demo-server tables | Needed for T6 and T8 | D-12, D-13 |
| 2026-09-30 | v1 | **Phase 2 done**: T1-T10 plus T3b (Apr 17) | Main session plus agents I1, I2 | Supply-limited; 47% of requests cancelled, rising about 7 points per minute of median wait; the ride tail comes from routing (P90 23.9 min vs the longest direct drive, 13.6); Lyft carries 24.5% of riders and tracks cancellations (r 0.88); campus is a net source |
| 2026-10-02 | v1 | Note added after the operations research (`docs/technical/transloc_operations.md`) | Context for reading T1, T7 and T9 | p06 "All services" likely includes East Baltimore vans (a 5.6-van drop at midnight), so T1's rides per van-hour (6.2 at 6 pm) is a lower bound; T7's Lyft-cancellation link fits dispatcher Lyft transfers being recorded as "Canceled" (about 1/3 of cancellations) |
