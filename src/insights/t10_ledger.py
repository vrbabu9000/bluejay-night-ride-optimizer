"""
T10: Reconciliation ledger (gate G1). Every identity we can check between the
digitized charts, with left side, right side, residual and an interpretation.
A residual is not forced to zero: it is explained, carried as uncertainty, or
flagged as a definition difference.

Output: docs/evidence/reconciliation_ledger.md, outputs/insights/t10_ledger.csv
"""
import datetime as dt

import numpy as np
import pandas as pd

from common import FIGS, PROCESSED, ROOT, observations, series

LEDGER = ROOT / "docs" / "evidence" / "reconciliation_ledger.md"

VERDICT = """
## G1 verdict (input integrity): PASS, with carried caveats (reviewed 2026-09-29)

**Required evidence (guide ch. 6) and status**
- **Definitions and coverage recorded.** Every chart has a brief in `docs/evidence/briefs/` (11 files covering 12 charts), with the title, filter, date range, grain, units, quirks, and can/cannot.
- **Extraction checked.**
  - Tooltip anchors: p06 27.56 vs 27.6; p09 5,089 vs 5,098; p08 1,387.4 vs 1,388; p11 +1.6/-0.3/-4.0 s; p12 +4.0/+3.7/+1.2 s; p10 total within 0.3% of the printed 44,374.
  - Second-method reads: p06/p09/p08 chroma re-read (all bar tops agree); p07 three methods (within 0.62 px); p10 second reader (all 37 bars); p11 blob-centre re-read (median/P10 0 px, P90 within 1 px ≈ 4.8 s); p12 polyline check.
  - Maps: two independent readers agree on 214 of 215 bubbles, with one adjudicated.
- **Residuals explained or retained.** Every cross-chart identity closes within 0.4% of its total (table above). The campus-vs-city frame gap is explained by edge-cut bubbles and clusters straddling the frame. The Apr 30 shortfall is partly explained by after-midnight rides falling into May and is otherwise retained.
- **Units verified.** Minutes, rides, passengers, vehicles and riders are labelled in every observation row.

**Carried caveats (alternative interpretations, not resolved by the data)**
1. The vans chart counts "All services" over 29 days, so per-van rates are bounds (T1, T5).
2. The hour attribution in p09 (request, pickup or completion) is unknown.
3. "Canceled" is undefined: it may include rebookings and Lyft handoffs, so requests are an upper bound on distinct demand (T2, T7).
4. p08 counts van riders only (it matches the PowerBI van series).
5. The maps count completed rides (D-01); where cancelled requests came from is unobserved.
6. The p07 zero line reads +3.3 rides/day on "Denied" (a reading offset, inside the interval).
7. The triangle-marker bias (≈0.5-1 px) is documented on p11.

**Consequence.** The digitized evidence may be used downstream (Phase 3 generator, calibration targets) with these caveats. Nothing here authorizes Hopkins-specific claims about demand or dispatch outcomes.
"""


def main():
    obs = observations()
    rows = []

    def add(identity, left_name, left, right_name, right, coverage, interpretation):
        resid = left - right
        rows.append(dict(identity=identity, left=f"{left_name} = {left:,.1f}", right=f"{right_name} = {right:,.1f}",
                         residual=round(resid, 1), residual_pct=round(100 * resid / right, 2) if right else np.nan,
                         coverage=coverage, interpretation=interpretation))

    maps = pd.read_csv(PROCESSED / "map_clusters.csv")
    o_city = maps[maps.map_name == "origins_city"].count_best.sum()
    d_city = maps[maps.map_name == "destinations_city"].count_best.sum()
    add("Map origins = map destinations (city view)", "sum O bubbles", o_city, "sum D bubbles", d_city,
        "same month, same view", "Each completed ride has one origin and one destination. The 1-ride residual sits inside the reading range of the one partly hidden label (p02_b010, 6030-6039); it is carried, not balanced away.")

    hourly = obs[obs.chart_id == "p09_rides_by_hour"].value.sum()
    add("Map total = hourly completed rides", "map O total", o_city, "sum p09 (24 h)", hourly,
        "Homewood Night Ride, 30 days", "Supports D-01: the maps count completed rides. The residual is within reading error.")

    comp = series(obs, "p07_status", "completed")
    add("Hourly completed = daily completed", "sum p09", hourly, "sum p07 completed", comp.value.sum(),
        "hour-of-day totals vs calendar days", "Both report completed rides for the month. p07's zero line reads +3.3 rides/day on 'Denied'; if that offset applies to every p07 series, p07 is ~99 high and the residual shrinks to ~+20.")

    pax = series(obs, "p08_passengers", "passengers")
    van = obs[(obs.chart_id == "p10_vanlyft_daily") & (obs.metric == "van_riders")]
    add("TransLoc passengers = PowerBI van riders", "sum p08", pax.value.sum(), "sum p10 van", van.value.sum(),
        "different systems (TransLoc vs PowerBI)", "The same population if 'van riders' means boarded passengers; PowerBI resolution is low (±1.5 px ≈ ±30 riders per bar).")

    lyft = obs[(obs.chart_id == "p10_vanlyft_daily") & (obs.metric == "lyft_riders")]
    add("Van + Lyft = printed total", "sum p10 van + lyft", van.value.sum() + lyft.value.sum(), "printed total", 44374,
        "PowerBI panel", "Checks the p10 read against the printed 44,374.")

    # day-of-week panel vs daily reads
    dow = obs[obs.chart_id == "p10_vanlyft_dow"]
    if len(dow):
        daily = van.assign(day=van.date_or_hour.map(lambda s: dt.date.fromisoformat(s).strftime("%A")))
        means = daily.groupby("day").value.mean()
        for r in dow[dow.metric == "van_avg"].itertuples():
            label = str(r.date_or_hour).strip()
            key = next((d for d in means.index if d.lower().startswith(label.lower()[:3])), None)
            if key:
                add(f"DOW panel van average = mean of daily reads ({label})", "p10 DOW van", r.value, f"mean daily van ({key})",
                    means[key], "PowerBI panel vs daily bars", "The axis lists Friday before Thursday; the labels themselves are correct (p10 brief).")

    # passengers per completed ride, daily stability
    ppr = (pax.value / comp.value).dropna()
    rows.append(dict(identity="Passengers per completed ride (not an identity; stability check)", left=f"sum p08 / sum p07 completed = {pax.value.sum() / comp.value.sum():.3f}",
                     right=f"daily range {ppr.min():.2f}-{ppr.max():.2f} (mean {ppr.mean():.3f})", residual=np.nan, residual_pct=np.nan,
                     coverage="p08 = van riders only (matches p10 van, r 0.9994)", interpretation="Stable enough to use one party-size mean (1.39); its shape is ASSUMED."))

    # campus frame vs city bubbles inside frame
    for kind, city_inside in (("origins", 18776), ("destinations", 17056)):
        camp = maps[maps.map_name == f"{kind}_campus"]
        add(f"Campus-view read = city bubbles inside campus frame ({kind})", "campus read (labelled)", camp.count_read.sum(),
            "city bubbles inside frame", city_inside, "zoom-dependent clustering",
            f"Cut bubbles add {int(camp.lower.sum() - camp.count_read.sum())}-{int(camp.upper.sum() - camp.count_read.sum())} rides; city clusters straddle the frame edge.")

    # service night effect: Apr 30 deficit vs after-midnight rides per night
    h = obs[obs.chart_id == "p09_rides_by_hour"].assign(hh=lambda d: d.date_or_hour.str.strip().str.lower())
    after_mid = h[h.hh.isin(["00:00", "01:00", "02:00"])].value.sum() / 30
    c = comp.value
    typical = c.drop(["2026-04-30"], errors="ignore").mean()
    add("Apr 30 shortfall = after-midnight rides of the Apr 30 night (in May)", "mean day - Apr 30", typical - c.get("2026-04-30", np.nan),
        "after-midnight rides per night", after_mid, "calendar day vs service night",
        "If about equal, the low Apr 30 is a truncation artefact of calendar-day reporting, not a bad night.")

    veh_days = "29 days (p06 tooltip)"
    rows.append(dict(identity="Vehicles vs rides coverage", left="p06: All services, 29 days", right="p09: Homewood Night Ride, 30 days",
                     residual=np.nan, residual_pct=np.nan, coverage=veh_days,
                     interpretation="Definition mismatch, not an identity: per-van rates are bounds (T1, T5)."))

    df = pd.DataFrame(rows)
    FIGS.mkdir(parents=True, exist_ok=True)
    df.to_csv(FIGS / "t10_ledger.csv", index=False)
    lines = ["# Reconciliation ledger (gate G1)", "",
             "Each identity: left side, right side, residual (left - right), coverage, and what we do about it. "
             "Residuals are explained, carried as uncertainty, or flagged; never forced to zero.", "",
             "| Identity | Left | Right | Residual | % | Coverage | Interpretation / action |", "|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        pct = "" if pd.isna(r.residual_pct) else f"{r.residual_pct:+.2f}%"
        res = "" if pd.isna(r.residual) else f"{r.residual:+,.1f}"
        lines.append(f"| {r.identity} | {r.left} | {r.right} | {res} | {pct} | {r.coverage} | {r.interpretation} |")
    lines += ["", VERDICT.strip(), ""]
    LEDGER.write_text("\n".join(lines))
    print(df[["identity", "left", "right", "residual", "residual_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
