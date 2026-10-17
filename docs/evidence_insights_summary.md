# Evidence insights summary — April 2026 (script-computed)

Source: `docs/data/HW Night Ride Data April 2026.pdf`, pages 6-12 (the seven daily/hourly charts), digitized by `src/evidence/chart_p*.py` and analyzed by `src/insights/t01-t09*.py`. Every number below is pixel-measured off the dashboard's own charts and cross-checked against the dashboard's printed tooltips/totals (all anchor checks passed); none of it is eyeballed. Full briefs with caveats, reading intervals and robustness checks live in `docs/evidence/insights/t0N.md` (gitignored, derived data — regenerate with the scripts above against the restricted PDF).

This is a second, independent pass alongside the earlier manual eye-read in [data_findings.md](data_findings.md) — the two should roughly agree, not match exactly, since they're different methods on the same source.

Scope note: the spatial/map pages (2-5) and the three insights that depend on them (T06 detour, T08 O-D structure, full T10 reconciliation ledger) are **not** included this round — that pipeline needs live Nominatim/OSM geocoding and a bubble-count step the team does with two independent human readers for QA, which a solo pass can't match. Candidate follow-up.

## 1. The service is supply-capped, not demand-paced (T01)

Completed rides per van-hour stays in a narrow 4.8-6.2 band from 6pm to 1am even as the fleet falls from 27.6 to 9.3 vans — throughput tracks the fleet, not demand. More tellingly: **daily completions barely move with daily requests** (slope -0.02 completed rides per extra request, r = -0.04), even though daily requests swing from 1,438 to 2,148. On busy days the extra demand becomes cancellations, not rides — the signature of a hard capacity cap, not a fleet that's merely well-matched to expected demand.

**Implication:** the hourly completed-rides chart (p09) is *censored demand*, not demand itself. The base scenario's "~6 rides per van-hour at 6pm" is a floor on true demand, not an estimate of it.

## 2. Cancellation is almost as large as completion (T02)

Month-pooled: **47.4% of all 50,297 requests were cancelled** (24,095 completed, 23,842 cancelled, 2,359 no-show). Cancellations *outnumber* completions on 13 of 30 days. Daily cancelled share ranges from 31.5% (Apr 21) to 68.4% (Apr 17), and rises with daily request volume (r = +0.67) — busier nights cancel a larger share, not just a larger count.

Requests-per-completed-ride = 2.09 — this is the empirical basis for D-06's "30 requests as served ≈ 60 as requested."

**Caveat carried forward:** "cancelled" isn't defined on the dashboard — it likely blends rebookings and Lyft hand-offs, so it overstates distinct unserved riders. The true unserved-rider share is at most 52.1% (cancelled+no-show+denied / requests), possibly much lower.

## 3. Cancellation tracks wait time; Apr 17 is a supply failure, not a demand spike (T03, T03b)

Across the 30 days, cancelled share rises with median wait: **r = 0.74** (7.2 percentage points of cancellation per extra minute of median wait), robust to removing weekday effects (r = 0.72) and to dropping Apr 17 (r = 0.64).

**April 17**, flagged repeatedly throughout the whole dashboard, ranks **worst or near-worst on every single metric**: fewest completed rides (543, rank 30/30), most cancellations (1,290, rank 1/30), highest cancel share (68%), longest wait median (12.9min) and P90 (21.2min), longest ride median (12.5min) and P90 (29.4min), most Lyft riders (674, rank 1/30) — while its *request* volume (1,889) was only the 4th-highest of the month, well below the maximum (2,148 on Apr 29). More requests arrived on other days without the same breakdown. That pattern — normal demand, abnormally bad service — points to a supply-side disruption (fewer working vans, slower trips) rather than a demand surge, making Apr 17 the natural "reduced-fleet stress case" for the scenario grid rather than a "high-demand" one.

## 4. Party size: mean is solid, shape is not identifiable from these charts (T04)

Month-pooled van passengers per completed ride: **1.386** (33,394 passengers / 24,095 completed rides), stable day to day (1.21-1.63) and with no detectable relationship to volume (r = -0.01). It does vary by weekday though: weekends average 1.49 vs 1.35 Monday-Friday (ANOVA p = 0.0003).

Confirms D-08's split status: the **mean (1.386) is DERIVED and solid**, but the *distribution* over party sizes 1-4 is not identifiable from a mean alone — anywhere from 61% to 87% solo riders is consistent with this same mean. The plan's pilot shape (.72/.19/.06/.03) stays an assumption, not a measured value.

## 5. Pooling is certain at the peak, not assumed (T05)

At 6pm, **1.31 rides are in progress per van on average** (1.81 riders on board) — a lower bound, before counting empty/idle driving. Since each completed ride uses only 9.7 van-minutes against a 12.7-minute average ride duration, rides must be overlapping on the same vehicle: pooling isn't a modeling assumption here, it's an arithmetic consequence of the dashboard numbers. Later hours (7pm-1am) sit at a more marginal 1.0-1.2 rides/van — consistent with, but not conclusive proof of, continued pooling.

Side finding: wait time is **not** lognormal (a lognormal fit through the median/P90 overpredicts P10 by nearly 2x) — it has a much heavier short end than ride duration does. Don't reuse the same distribution family for both in the generator.

## 6. Lyft share moves with cancellations, but it's not proof of a hand-off (T07)

Lyft carried **24.5%** of all riders month-pooled (10,821 of 44,248), ranging 9.9% (Apr 5) to 46.3% (Apr 17) daily. Days with more cancellations have more Lyft riders: **r = 0.88** (CI 0.77-0.94), robust to dropping Apr 17 (r = 0.85) and to removing weekday effects (r = 0.84). About 22% of daily Lyft variation is still unexplained (e.g., Apr 30 is a large outlier below the trend).

**Important correction to the earlier manual read:** the dashboard's "many cancelled become Lyfts" is a slide annotation, not a measured conversion rate — nothing in these charts records an actual rider-level hand-off. The correlation is real and strong, but three different stories fit it equally well: cancelled riders switching to Lyft, Lyft being dispatched as planned extra supply exactly on the nights vans fall behind, or a busy night simply driving both numbers up together. Treat "cancel-to-Lyft" as a plausible proxy for overflow, not a confirmed mechanism — this matters for how confidently the predictive-overflow classifier's training label should be framed.

## 7. Where supply and demand misalign: 6pm and 2am (T09)

Supply (van-hours) and demand (completed-ride share) track each other closely for 7pm-1am (gaps all within ±0.9 percentage points, 4.8-5.6 rides per van-hour throughout). The two exceptions:
- **6pm**: 21.2% of the night's completed rides run on only 17.5% of van-hours (+3.6pp gap, 6.16 rides/van-hour vs 5.10 night average) — and since T01 shows completions are supply-capped, true 6pm demand share is probably *even higher* than 21.2%.
- **2am**: 2.9% of van-hours produce essentially 0% of completed rides (at most 0.22 rides/van-hour) — vans are in service but not completing trips; the dashboard can't say whether they're finishing a last trip, returning to depot, or logging out.

## Carried caveats (apply to all of the above)

- Vans (p06) are filtered to "All services," not Homewood-specific, and averaged over 29 days vs 30 for the ride charts — a consistent ~3% scale caveat on every rides-per-van-hour number.
- "Cancelled" and "completed" status definitions aren't documented on the dashboard; cancellations likely include rebookings.
- Everything here is a **daily or hourly aggregate relationship**, not a rider-level causal one — none of these correlations establish individual patience, wait tolerance, or cancel/Lyft decision mechanics. They're targets the simulator's *aggregate behavior* should reproduce, not inputs to draw per-rider.
- Apr 17 is one outlier night (n=1) — useful as a stress-test scenario, not as evidence of a recurring "event effect" (matches D-14's reasoning for not pursuing an event-aware forecasting line).

## What this document does not contain

Same governance boundary as `data_findings.md`: no individual ride records, no PII, no raw map/coordinate data. Every number above is read directly off aggregate dashboard charts, and the full computation (with pixel-reading intervals and every robustness check) is reproducible from `docs/data/HW Night Ride Data April 2026.pdf` via the scripts in `src/evidence/` and `src/insights/`.
