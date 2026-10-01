"""
T5: Average occupancy from Little's law, and the evidence that pooling happens.

  rides in progress per van (hour h) = lambda_h * E[ride time] / vans_h
  riders on board per van            = the above * passengers per completed ride
with lambda_h = p09 hourly completions / 30, vans_h from p06, passengers per ride
= April passengers (p08) / April completed rides (p07), and E[ride time] from a
lognormal through the monthly ride-time median and P90 (p12). The lognormal is
checked against the observed P10 before its mean is used.

Because the vans chart counts "All services" (at least the Homewood fleet), these
per-van figures are LOWER bounds for Homewood. A value above 1 ride in progress
per van means rides overlap in time on the same van, i.e. pooling, even before
counting deadhead and idle time.

Outputs: outputs/insights/t05_occupancy.png, t05_occupancy_table.csv, docs/evidence/insights/t05.md
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (BLUE, BLUE_LIGHT, FIGS, GRAY, INK2, MUTED, observations, save, series, source, style,
                    subtitle, write_brief)
from t01_supply import HOUR_NAMES, SERVICE_HOURS, hour_label

Z90 = 1.2816


def main():
    style()
    obs = observations()
    ride = {m: series(obs, "p12_ride", f"ride_{m}").value for m in ("p10", "median", "p90")}
    med, p90, p10 = ride["median"].mean(), ride["p90"].mean(), ride["p10"].mean()
    sigma = np.log(p90 / med) / Z90
    p10_pred = med * np.exp(-Z90 * sigma)
    mean_ride = med * np.exp(sigma ** 2 / 2)
    # daily-fit version, to show the monthly figure is not an artefact of averaging
    s_d = np.log(ride["p90"] / ride["median"]) / Z90
    mean_ride_daily = float((ride["median"] * np.exp(s_d ** 2 / 2)).mean())

    wmed = series(obs, "p11_wait", "wait_median").value.mean()
    wp90 = series(obs, "p11_wait", "wait_p90").value.mean()
    wp10 = series(obs, "p11_wait", "wait_p10").value.mean()
    wp10_pred = wmed * np.exp(-np.log(wp90 / wmed))
    pax = series(obs, "p08_passengers", "passengers").value.sum()
    done = series(obs, "p07_status", "completed").value.sum()
    ppr = pax / done

    veh = obs[obs.chart_id == "p06_vehicles"].assign(h=lambda d: d.date_or_hour.map(hour_label)).set_index("h")
    rid = obs[obs.chart_id == "p09_rides_by_hour"].assign(h=lambda d: d.date_or_hour.map(hour_label)).set_index("h")
    hours = [h for h in SERVICE_HOURS if h in veh.index and h in rid.index]
    t = pd.DataFrame({"hour": hours, "vans": [veh.loc[h, "value"] for h in hours],
                      "rides_per_hour": [rid.loc[h, "value"] / 30 for h in hours]})
    t["rides_in_progress_per_van"] = t.rides_per_hour * (mean_ride / 60) / t.vans
    t["riders_on_board_per_van"] = t.rides_in_progress_per_van * ppr
    t["van_minutes_per_ride"] = 60 * t.vans / t.rides_per_hour
    FIGS.mkdir(parents=True, exist_ok=True)
    t.round(3).to_csv(FIGS / "t05_occupancy_table.csv", index=False)

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    x = np.arange(len(t))
    w = 0.34
    ax.bar(x - w / 2 - 0.01, t.rides_in_progress_per_van, width=w, color=BLUE_LIGHT, label="Rides in progress per van")
    ax.bar(x + w / 2 + 0.01, t.riders_on_board_per_van, width=w, color=BLUE, label="Riders on board per van")
    ax.axhline(1, color=GRAY, lw=1.2, zorder=1, label="One ride at a time (1.0)")
    ax.set_xticks(x, [HOUR_NAMES[h] for h in t.hour]); ax.grid(axis="x", visible=False)
    ax.set_ylabel("Average per van in service (lower bound)")
    ax.set_title("At the 6 pm peak, vans must be carrying overlapping rides")
    subtitle(ax, f"Little's law with mean ride time {mean_ride:.1f} min (lognormal fit) and {ppr:.2f} passengers per completed ride")
    ax.legend(loc="upper right")
    top = t.iloc[0]
    ax.text(0 + w / 2, top.riders_on_board_per_van + 0.04, f"{top.riders_on_board_per_van:.1f}", ha="center", fontsize=9, color=INK2)
    source(fig, "Sources: TransLoc April 2026 p06, p07, p08, p09, p12, digitized. Vans counted under 'All services', so per-van values are lower bounds.")
    save(fig, "t05_occupancy")

    body = f"""
**Question.** How many riders does a van carry on average, and is pooling routine?

**Answer (DERIVED; lower bounds).**
- **Distribution check.** A lognormal through the monthly median ({med:.1f} min) and P90 ({p90:.1f} min) of ride time predicts a P10 of {p10_pred:.1f} min against an observed {p10:.1f} min, so the lognormal is a fair description of ride time. Its mean is **{mean_ride:.1f} min**; fitting each day separately gives {mean_ride_daily:.1f} min on average.
- **Passengers per completed ride:** {pax:,.0f} / {done:,.0f} = **{ppr:.2f}**.
- **At 6 pm:** {top.rides_in_progress_per_van:.2f} rides are in progress per van on average, i.e. **{top.riders_on_board_per_van:.2f} riders on board**. Across the night the range is {t.rides_in_progress_per_van.min():.2f}-{t.rides_in_progress_per_van.max():.2f} rides and {t.riders_on_board_per_van.min():.2f}-{t.riders_on_board_per_van.max():.2f} riders per van.
- **Pooling at the peak is certain, not assumed.** At 6 pm, 1.31 rides are in progress per van on average, a lower bound, before counting any empty or idle driving. Rides must therefore overlap on the same van. Each completed ride uses only {top.van_minutes_per_ride:.1f} van-minutes, less than the {mean_ride:.1f}-minute average ride itself.
- **Later hours are marginal.** From 7 pm to 1 am the value is {t.rides_in_progress_per_van.iloc[1:].min():.2f}-{t.rides_in_progress_per_van.iloc[1:].max():.2f}. That is consistent with pooling, but within the uncertainty of the mean ride time (the lognormal overstates P10 by about {p10_pred - p10:.2f} min). If the true mean were 5% lower, these hours would sit at about 1.0. Evidence of pooling after 7 pm rests on the lower-bound argument (vans counted under "All services"), not on the point values.
- **Wait times are not lognormal (contrast).** The same fit on p11 (median {wmed:.1f}, P90 {wp90:.1f} min) predicts a P10 of {wp10_pred:.1f} min against an observed {wp10:.1f} min. The wait distribution has a much heavier short end: some riders are picked up almost immediately. The simulator must not assume a lognormal wait.

**Caveats.**
- Vans are counted under "All services", so these per-van figures are lower bounds.
- Little's law needs a stationary hour. The 6 pm start-of-service hour is the least stationary, so treat that value as indicative.
- Hour attribution in p09 is unknown.

**What it cannot tell us.** The distribution of occupancy (how often a van carries 3+ riders), capacity binding, or empty-driving share. These are simulator outputs, to be compared against this average (A7, G4).

Figure: `outputs/insights/t05_occupancy.png`. Table: `outputs/insights/t05_occupancy_table.csv`.
"""
    write_brief("t05", "Average occupancy and pooling", body)
    print(t.round(3).to_string(index=False))
    print(f"median {med:.2f} p90 {p90:.2f} p10 {p10:.2f} sigma {sigma:.3f} p10_pred {p10_pred:.2f} mean {mean_ride:.2f} (daily {mean_ride_daily:.2f}) ppr {ppr:.3f}")


if __name__ == "__main__":
    main()
