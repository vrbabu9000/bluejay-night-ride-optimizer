# Data Findings — HW Night Ride Data, April 2026

Source: `docs/data/HW Night Ride Data April 2026.pdf` (12-page dashboard export supplied by JHU Transportation, restricted/gitignored — see [README.md](../README.md) privacy boundaries). This document contains only aggregate, de-identified figures read off the dashboard charts; no raw records, PII, or exact addresses are reproduced here.

This is a manual eye-read pass. For script-verified figures (pixel-measured, cross-checked against the dashboard's own tooltips), see [evidence_insights_summary.md](evidence_insights_summary.md).

## 1. Service window

- Vehicles in service only during a limited overnight window: near-zero average active vehicles from ~2am–5pm.
- Fleet ramps up starting ~5–6pm, peaks at **6pm with 27.6 avg active vehicles**, holds mid-20s through 8–9pm, tapers to ~16–17 by 10–11pm, drops further after midnight (~9–11 avg 12am–1am, ~4 at 2am).
- Effective operating hours: roughly **6pm–2am**, with the bulk of capacity concentrated in the first few hours of the shift rather than late night.

## 2. Demand volume and timing

- **Total April 2026 Homewood BJS ridership: 44,374** (van + Lyft combined).
- Rides-by-hour is front-loaded, not back-loaded: **6pm is the single busiest hour (~5,098 completed rides across the month)**, declining steadily each hour after — 7pm ~4.7k, 8pm ~3.8k, 9pm ~2.9k, 10pm ~2.6k, 11pm ~2.4k, then a small 12am/1am tail (~1.6–1.7k each), near-zero 2am–5am.
- Daily total passengers on vans fluctuate roughly 750–1,390/day with no obvious strong weekly pattern by day-count alone, but see day-of-week split below.
- Day-of-week average (van / Lyft overflow, in thousands): Sun 1.2/0.4, Mon 1.1/0.4, Tue 1.2/0.3, Wed 1.0/0.4, Thu 1.0/0.3, **Fri 1.0/0.5, Sat 1.2/0.4**. Friday shows the highest relative Lyft share versus van volume — weekend nights lean hardest on overflow.

## 3. Spatial demand pattern

- Ride origins are dense in a corridor running from the Homewood campus south through Charles Village/Bolton Hill toward downtown Baltimore, with the single densest origin clusters immediately on/around campus (top values ~3,878 and ~2,381 in the broad view).
- Destinations are **more tightly concentrated on campus** than origins are: the top destination cluster (~5,406) is larger than the top origin cluster, and destination density falls off faster moving away from Homewood. Net pattern: trips disperse from campus toward the surrounding neighborhood, then concentrate back onto campus — consistent with an evening dispersal / return-to-campus travel pattern.
- Zoomed "campus proximate" views confirm this: origin hot spots spread across Charles Village, Wyman Park/Remington, and the immediate campus core (top ~1,783 / 1,415 / 1,318), while destination hot spots cluster more sharply on 2–3 points directly on campus (top ~1,955 / 1,514 / 1,269 / 1,195 / 1,106).

## 4. Ride outcomes — cancellations convert to Lyft

- Daily rides-by-status (Completed, Canceled, No Show, Denied) shows **Canceled rides tracking roughly in parallel with Completed rides all month**, frequently in the 500–1,000+/day range each — not a small tail case.
- Dashboard explicitly annotates: *"many cancelled become Lyfts."* This is the direct empirical basis for the overflow dynamic — a meaningful share of riders who cancel a van request are picked up by Lyft instead, i.e., cancellation is often a proxy for "the shuttle wasn't going to arrive in time," not abandoned demand.
- No Show stays low and flat (~50–100/day). Denied is consistently near zero — capacity denial is rare; the system copes with excess demand via cancellation-to-Lyft rather than outright denial.
- **April 17 is a clear outlier day**: Canceled spikes to ~1,300 (vs. typical 700–900) while Completed dips to ~550 (vs. typical 750–950), and daily passenger count for that date also dips (~780). This same date shows the worst wait-time and ride-duration percentiles in the month (see below) — worth flagging for a root-cause look (event, weather, vehicle outage) once the raw data is available.

## 5. Wait time

- Measured request-to-pickup wait time, daily percentiles across April:
  - **P10 ≈ 3–4.5 min**
  - **Median ≈ 9.5–13 min**
  - **P90 ≈ 17–21 min**, consistently near/at the 20-minute mark all month.
- Worst day: **April 17, P90 = 21m17s, median = 12m56s** — matching the cancellation-spike anomaly above.
- Direct relevance to the proposed predictive-overflow idea in [proposed_solutions.md](proposed_solutions.md): roughly **10% of rides already sit at or above ~20 minutes of wait in a typical night**, meaning a 20-minute threshold is not a rare-tail event — it's a recurring top-decile outcome, giving a meaningful and frequent enough signal to train a proactive-overflow classifier against.

## 6. Ride duration (time on vehicle)

- **P10 ≈ 4 min, median ≈ 10–12 min, P90 ≈ 21–29 min** across April.
- Same April 17 anomaly reappears: **P90 = 29m24s, median = 12m28s**, the month's longest rides alongside its longest waits and highest cancellations — one bad night is visible across every metric on the dashboard, not just one chart.

## 7. Implications for modeling

- **Service hours**: any simulator/MILP time horizon should model the real 6pm–2am operating window, with heaviest demand at shift start (6pm) rather than assuming demand builds toward midnight.
- **Overflow ground truth**: cancel-to-Lyft is the closest available proxy for "the rider effectively overflowed." If Lyft/cancellation timestamps are in the underlying raw data, they're a usable label for training the predictive-overflow classifier proposed separately.
- **20-minute threshold is well-calibrated**: P90 wait hovering right at 20 minutes all month validates using 20 minutes as the overflow-risk threshold rather than an arbitrary pick.
- **April 17 anomaly**: exclude or flag as a special case in historical replay baselining, since it skews every metric on the dashboard for that single day.
- **Fleet sizing vs. demand curve mismatch**: average active vehicles peaks at 6pm (27.6) exactly when hourly ride volume also peaks (~5,098) — good alignment on paper, but wait times still climb toward P90≈20min even at peak supply, suggesting either dispatch inefficiency (routing/pooling) or genuine capacity shortfall worth separating out once request-level data is available.

## 8. What this document does not contain

Per repo data-governance rules, this summary omits: individual ride records, timestamps below daily/hourly aggregation, exact pickup/dropoff coordinates, rider or driver identifiers, and the underlying PDF's raw map tile data. All figures above are aggregate counts/percentiles read directly off the supplied dashboard charts.
