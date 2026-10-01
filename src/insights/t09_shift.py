"""
T9: Shift mismatch, vans in service vs completed rides by hour.

For the nine clock hours 6 pm to 2 am:
  van-hour share  = hour's average vans in service (p06, 'All services', 29 days) / sum over the nine hours
                    (one van in service for one clock hour = one van-hour)
  ride share      = hour's completed rides (p09, Homewood Night Ride, 30-day total) / sum over the nine hours
Each series is divided by its own total, so the 29 vs 30 day counts cancel in the shares. The gap
(ride share - van-hour share) is positive exactly when that hour's completed rides per van-hour are above
the night's average, so it is a productivity index. Completions are censored by supply (T1): hourly
cancellations are not reported, so the hourly demand share cannot be computed from these charts.

Outputs: outputs/insights/t09_shift.png, t09_shift_table.csv, docs/evidence/insights/t09.md
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import BLUE, FIGS, INK2, ORANGE, observations, save, series, source, style, subtitle, write_brief

HOURS = ["18:00", "19:00", "20:00", "21:00", "22:00", "23:00", "00:00", "01:00", "02:00"]
HOUR_NAMES = {"18:00": "6 pm", "19:00": "7 pm", "20:00": "8 pm", "21:00": "9 pm", "22:00": "10 pm",
              "23:00": "11 pm", "00:00": "12 am", "01:00": "1 am", "02:00": "2 am"}
RIDE_DAYS = 30        # p09 is a 30-day sum; rides per day = sum / 30 (as in T1)
FLAG = 1.0            # percentage points: hours whose two shares differ by more than this are called out


def joined(names):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def share_bounds(v, lo, hi):
    """Share of the total for each element, plus worst-case bounds: the element at one end of its reading
    interval and every other element at the opposite end."""
    v, lo, hi = (np.asarray(a, dtype=float) for a in (v, lo, hi))
    return v / v.sum(), lo / (lo + (hi.sum() - hi)), hi / (hi + (lo.sum() - lo))


def main():
    style()
    obs = observations()
    veh = series(obs, "p06_vehicles", "avg_active_vehicles")
    rid = series(obs, "p09_rides_by_hour", "completed_rides")
    v, r = veh.loc[HOURS], rid.loc[HOURS]
    assert abs(rid.value.sum() - r.value.sum()) < 1e-6          # nothing completes outside 6 pm to 2 am in p09

    t = pd.DataFrame({"hour": HOURS, "hour_name": [HOUR_NAMES[h] for h in HOURS],
                      "vans": v.value.to_numpy(), "rides_30d": r.value.to_numpy()})
    for name, (val, lo, hi) in {"van": (v.value, v.lower, v.upper), "ride": (r.value, r.lower, r.upper)}.items():
        s, s_lo, s_hi = share_bounds(val, lo, hi)
        t[f"{name}_share"], t[f"{name}_share_lo"], t[f"{name}_share_hi"] = 100 * s, 100 * s_lo, 100 * s_hi
    t["gap_pp"] = t.ride_share - t.van_share
    t["gap_pp_lo"] = t.ride_share_lo - t.van_share_hi
    t["gap_pp_hi"] = t.ride_share_hi - t.van_share_lo
    t["rides_per_day"] = t.rides_30d / RIDE_DAYS
    t["rides_per_van_hour"] = t.rides_per_day / t.vans
    t["rpvh_lo"] = r.lower.to_numpy() / RIDE_DAYS / v.upper.to_numpy()
    t["rpvh_hi"] = r.upper.to_numpy() / RIDE_DAYS / v.lower.to_numpy()
    FIGS.mkdir(parents=True, exist_ok=True)
    t.drop(columns=["gap_pp_lo", "gap_pp_hi"]).rename(columns={
        "vans": "vans_in_service", "van_share": "van_hours_share_pct", "van_share_lo": "van_hours_share_lo_pct",
        "van_share_hi": "van_hours_share_hi_pct", "ride_share": "ride_share_pct", "ride_share_lo": "ride_share_lo_pct",
        "ride_share_hi": "ride_share_hi_pct"}).round(3).to_csv(FIGS / "t09_shift_table.csv", index=False)

    # ---- summary numbers ---------------------------------------------------------------------
    vh_night = t.vans.sum()                                      # van-hours per night, 6 pm to 2 am
    vh_thru1 = t.vans.iloc[:-1].sum()                            # 6 pm to 1 am
    vh_err = float(np.sqrt((((v.upper - v.lower) / 2) ** 2).sum()))
    rides_night = t.rides_30d.sum() / RIDE_DAYS
    rpvh_night, rpvh_thru1 = rides_night / vh_night, rides_night / vh_thru1
    first, last = t.iloc[0], t.iloc[-1]
    off = t[t.gap_pp.abs() > FLAG]
    mid = t[(t.gap_pp.abs() <= FLAG)]
    mid_in = mid[mid.hour != first.hour]                         # 7 pm to 1 am when 6 pm and 2 am are the flagged hours
    above = t[t.gap_pp > 0].hour_name.tolist()
    rides_hi_2am = float(r.upper.iloc[-1])                       # 'no bar visible': under about 1.5 px
    max_noise = float(np.ceil(10 * max((t.ride_share_hi - t.ride_share_lo).max(), (t.van_share_hi - t.van_share_lo).max()) / 2) / 10)
    p7 = t.iloc[1]                                               # 7 pm: the ride bar is partly hidden by the chart's tooltip
    wait_ride = float(series(obs, "p11_wait", "wait_median").value.mean() + series(obs, "p12_ride", "ride_median").value.mean())
    assert list(off.hour) == ["18:00", "02:00"], "title and brief are written for gaps at 6 pm and 2 am; review them"

    # ---- figure ------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(t))
    w, gap = 0.24, 0.03                                           # thin columns with a small surface gap between the pair
    ax.bar(x - (w + gap) / 2, t.ride_share, width=w, color=BLUE, zorder=3, label="Share of the night's completed rides (p09)")
    ax.bar(x + (w + gap) / 2, t.van_share, width=w, color=ORANGE, zorder=3, label="Share of the night's van-hours (p06)")
    half = (w + gap) / 2
    for i in (0, len(t) - 1):                                     # direct labels on the 6 pm and 2 am pairs only
        rs, vs = t.ride_share.iloc[i], t.van_share.iloc[i]
        # (x of bar centre, value, label, is the bar on the left of the pair)
        for xc, val, text, left in ((i - half, rs, f"{rs:.1f}%" if rs >= 0.5 else "~0%", True), (i + half, vs, f"{vs:.1f}%", False)):
            if val >= max(rs, vs):
                xa, ha = xc, "center"                             # the taller bar: label centred on its cap
            elif left:
                xa, ha = xc + w / 2, "right"                      # shorter bar on the left: label runs left, away from the taller bar
            else:
                xa, ha = xc - w / 2, "left"                       # shorter bar on the right: label runs right, away from the taller bar
            ax.annotate(text, (xa, val), xytext=(0, 4), textcoords="offset points", ha=ha, va="bottom", fontsize=9, color=INK2)
    ax.set_xticks(x, t.hour_name); ax.set_xlim(-0.6, len(t) - 0.4)
    ax.set_ylim(0, 25); ax.set_yticks(np.arange(0, 26, 5))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v_, _: f"{v_:.0f}%"))
    ax.grid(axis="x", visible=False)
    ax.set_xlabel("Clock hour (start of the hour), April 2026"); ax.set_ylabel("% of the night's total")
    ax.set_title(f"Completed rides follow van-hours all night, except at {joined(off.hour_name.tolist())}")
    subtitle(ax, f"{first.hour_name}: {first.ride_share:.1f}% of rides on {first.van_share:.1f}% of van-hours "
                 f"({first.rides_per_van_hour:.1f} rides per van-hour). "
                 f"{last.hour_name}: {last.van_share:.1f}% of van-hours, ~0 completed rides.")
    ax.legend(loc="upper right")
    source(fig, "Sources: TransLoc April 2026 p06 (vehicles in service by hour, 'All services', 29 days) and p09 (completed rides by hour, "
                "Homewood Night Ride, 30 days), digitized. Each share is of its own 6 pm to 2 am total.")
    save(fig, "t09_shift")

    # ---- brief -------------------------------------------------------------------------------
    rows = "\n".join(
        f"| {q.hour_name} | {q.vans:.1f} | {q.van_share:.1f}% | {q.rides_30d:,.0f} | {q.ride_share:.1f}% | {q.gap_pp:+.1f} | "
        + (f"{q.rides_per_van_hour:.2f} |" if q.rides_30d > 0 else f"0 (at most {q.rpvh_hi:.2f}) |")
        for q in t.itertuples())
    lo_rpvh, hi_rpvh = mid_in.rides_per_van_hour.min(), mid_in.rides_per_van_hour.max()
    body = f"""
**Question.** Does the van schedule follow the hourly pattern of completed rides? Where do vans run without completing rides, and where do they complete more rides than their share of supply?

**Answer (DERIVED from OBSERVED charts): the two shapes nearly coincide, and the mismatch sits in two hours: 6 pm (rides ahead of vans) and 2 am (vans, no rides).**

| Hour | Vans in service | Share of van-hours | Completed rides (30 days) | Share of completed rides | Gap (points) | Rides per van-hour |
|---|---|---|---|---|---|---|
{rows}

- **Night totals.** {vh_night:.1f} van-hours per night (the nine hourly averages summed; {vh_thru1:.1f} through 1 am; about ±{vh_err:.1f} from reading the bars) against {rides_night:.1f} completed rides per night. That is {rpvh_night:.2f} completed rides per van-hour over the whole night ({rpvh_thru1:.2f} through 1 am, the T1 convention of dividing 30-day rides by 30).
- **{mid_in.hour_name.iloc[0]} to {mid_in.hour_name.iloc[-1]}: proportional.** Every hour's share of completed rides is within {mid_in.gap_pp.abs().max():.1f} points of its share of van-hours, and rides per van-hour stay between {lo_rpvh:.1f} and {hi_rpvh:.1f}. This is T1's flat productivity restated as shares.
- **6 pm: rides ahead of vans.** {first.ride_share:.1f}% of the night's completed rides on {first.van_share:.1f}% of its van-hours ({first.gap_pp:+.1f} points; worst-case reading interval {first.gap_pp_lo:+.1f} to {first.gap_pp_hi:+.1f}), and {first.rides_per_van_hour:.1f} completed rides per van-hour against {rpvh_night:.1f} for the night. A positive gap means exactly that an hour's rides per van-hour are above the night's average, so where the completed-ride share exceeds the van-hour share the vans are busier than their night average, and at 6 pm they are busiest by far. The other hours above the night's average ({joined([h for h in above if h != first.hour_name])}) do so by at most {t[t.hour != first.hour].gap_pp.clip(lower=0).max():.1f} points of share.
- **Completions are censored by supply (T1), so the 6 pm demand share is probably higher than {first.ride_share:.1f}%.** T1 finds the service very likely supply-limited at the peak, so completed rides understate demand there. The 6 pm demand share exceeds {first.ride_share:.1f}% if the fraction of requests lost is larger at 6 pm than later in the night, which is what a cap that binds hardest at the peak implies. How much cannot be measured: cancellations are reported only by day (p07), so an hourly demand share cannot be computed. This is a direction, not a number.
- **2 am: vans in service, about no completed rides.** {last.vans:.1f} vans are in service in that clock hour on average, which is {last.vans:.1f} van-hours a night, **{last.van_share:.1f}% of the night's van-hours**, while p09 shows no ride bar for the hour (no more than about {rides_hi_2am:.0f} completed rides in 30 days, so at most {last.rpvh_hi:.2f} per van-hour and {last.ride_share_hi:.1f}% of the night's rides). The data cannot say what these vans are doing: finishing a last trip, returning to a depot, drivers logging out, or another service's vans (p06 is "All services"). For scale, that supply is about a sixth of the 6 pm fleet ({first.vans:.1f} vans).
- **Reading the two flagged hours together.** The schedule and the completions differ visibly only at the start and the end of service. Each fits a simple operational story (a busy first hour; an end-of-shift tail) that these charts cannot confirm. Nothing in between looks mistimed against completions, but completions cannot show whether the shape of supply is right, because they are themselves capped by it.

**Caveats.**
- **p06 is "All services" and 29 days; p09 is Homewood Night Ride and 30 days.** If other services' vans share the count, van-hours are overstated for Homewood and the mix may change by hour; the 2 am vans may not be Homewood vans. The day counts cancel in the shares (each series is divided by its own total) but not in rides per van-hour: dividing by 29 instead of 30 raises each rate by 3.4%.
- **The hour in p09 may be the request, pickup or completion hour** (the chart does not say). If it is not the completion hour, the last rides of the night finish after the clock hour in which they are counted, so vans at 2 am may be finishing trips that p09 counts at 1 am or earlier. A typical request-to-drop-off time is about {wait_ride:.0f} minutes (median wait plus median ride, p11 and p12), enough to move some rides across an hour boundary.
- **6 pm is the start-of-service hour**, the least stationary hour of the night (T5): vans and riders may still be arriving during the hour, so its rate is the least reliable as an hourly average.
- **Reading precision.** Worst-case reading noise on any share is at most {max_noise:.1f} points (every bar at the far end of its reading interval). Two bars are less certain: the 7 pm ride bar is partly hidden by the chart's tooltip (interval doubled, ±58 rides) and the 8 pm van bar is recovered from under it (±0.29 vans). The 7 pm gap ({p7.gap_pp:+.1f}) is the third largest, but its worst-case interval ({p7.gap_pp_lo:+.1f} to {p7.gap_pp_hi:+.1f}) is wide for that reason; treat it as small. The 6 pm and 2 am gaps stay far outside the noise ({first.gap_pp_lo:+.1f} to {first.gap_pp_hi:+.1f} and {last.gap_pp_lo:+.1f} to {last.gap_pp_hi:+.1f}).
- **The van bars are averages over days** (p06), which blend different nightly schedules; the shares describe the average night, not any one night's shift plan.

**What it cannot tell us.**
- Whether the peak is under-supplied and by how much: hourly cancellations are not reported, so hourly demand is unobserved.
- Which vans are on the road at 2 am, shift start and end times, or how many distinct vans work a night (p06 counts vans in service per hour, not shifts).
- Whether another shift pattern would serve more riders. That is a simulation question (fleet and shift sensitivity runs), not a result of these charts.

**Used by.** The fleet and shift sensitivity experiments (A9 item 3, fleet and shift curves) and the scenario grid (fleet schedule scenarios: test the coverage, never use these counts silently as Homewood vans; the 6 pm base scenario sits at about {first.rides_per_van_hour:.1f} completed rides per van-hour).

Figure: `outputs/insights/t09_shift.png`. Table: `outputs/insights/t09_shift_table.csv`.
"""
    write_brief("t09", "Shift mismatch, vans in service vs completed rides by hour", body)

    print(t[["hour_name", "vans", "van_share", "rides_30d", "ride_share", "gap_pp", "gap_pp_lo", "gap_pp_hi",
             "rides_per_van_hour", "rpvh_lo", "rpvh_hi"]].round(2).to_string(index=False))
    print(f"van-hours per night {vh_night:.2f} (through 1 am {vh_thru1:.2f}, reading noise {vh_err:.2f}); rides per night {rides_night:.1f}; "
          f"per van-hour {rpvh_night:.3f} (through 1 am {rpvh_thru1:.3f}); 2 am: {last.vans:.3f} van-hours, {last.van_share:.2f}% of night, "
          f"rides upper bound {rides_hi_2am:.1f} -> {last.rpvh_hi:.3f} per van-hour, {last.ride_share_hi:.3f}% of rides")
    print(f"max |gap| outside 6 pm/2 am {mid_in.gap_pp.abs().max():.2f}; hours above night average: {above}; max share noise {max_noise:.3f}; median wait + ride {wait_ride:.1f} min")


if __name__ == "__main__":
    main()
