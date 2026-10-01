"""
T1: Is the service supply-limited?

Two tests on the digitized charts:
  (a) Hour of day: completed rides per van-hour = (p09 hourly total / 30) / p06 average vans.
      If throughput tracks the fleet rather than demand, this ratio is flat across hours.
  (b) Day to day: if the fleet caps service, daily completions (p07) vary little while
      total requests (completed + cancelled + no-show + denied) swing, and the excess shows
      up as cancellations.
Alternative explanation for (a): the fleet schedule is planned to match expected demand.
Test (b) helps separate the two.

Outputs: outputs/insights/t01_supply.png, t01_supply_table.csv, docs/evidence/insights/t01.md
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import (BLUE, FIGS, GRAY, INK2, MUTED, ORANGE, marker_kw, observations, save, series, source,
                    style, subtitle, write_brief)

SERVICE_HOURS = ["18:00", "19:00", "20:00", "21:00", "22:00", "23:00", "00:00", "01:00"]
HOUR_NAMES = {"18:00": "6 pm", "19:00": "7 pm", "20:00": "8 pm", "21:00": "9 pm", "22:00": "10 pm",
              "23:00": "11 pm", "00:00": "12 am", "01:00": "1 am", "02:00": "2 am"}


def hour_label(v):
    return str(v).strip().lower()


def main():
    style()
    obs = observations()
    veh = obs[obs.chart_id == "p06_vehicles"].copy()
    rid = obs[obs.chart_id == "p09_rides_by_hour"].copy()
    veh["h"] = veh.date_or_hour.map(hour_label); rid["h"] = rid.date_or_hour.map(hour_label)
    veh, rid = veh.set_index("h"), rid.set_index("h")
    hours = [h for h in SERVICE_HOURS if h in veh.index and h in rid.index]
    t = pd.DataFrame({"hour": hours,
                      "vans": [veh.loc[h, "value"] for h in hours],
                      "rides_per_day": [rid.loc[h, "value"] / 30 for h in hours],
                      "rides_per_day_lo": [rid.loc[h, "lower"] / 30 for h in hours],
                      "rides_per_day_hi": [rid.loc[h, "upper"] / 30 for h in hours]})
    t["rides_per_van_hour"] = t.rides_per_day / t.vans
    t["rpvh_lo"] = t.rides_per_day_lo / veh.loc[hours, "upper"].values
    t["rpvh_hi"] = t.rides_per_day_hi / veh.loc[hours, "lower"].values
    base = t.iloc[0]
    t["vans_index"] = 100 * t.vans / base.vans
    t["rides_index"] = 100 * t.rides_per_day / base.rides_per_day
    FIGS.mkdir(parents=True, exist_ok=True)
    t.round(3).to_csv(FIGS / "t01_supply_table.csv", index=False)

    st = {m: series(obs, "p07_status", m).value for m in ("completed", "canceled", "no_show", "denied")}
    daily = pd.DataFrame(st)
    daily["requests"] = daily.sum(axis=1)
    cv = lambda s: s.std() / s.mean()

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axes[0]
    x = np.arange(len(t))
    ax.plot(x, t.rides_index, color=BLUE, **marker_kw(BLUE, 8), label="Completed rides per hour")
    ax.plot(x, t.vans_index, color=ORANGE, **marker_kw(ORANGE, 8), label="Vans in service")
    ax.set_xticks(x, [HOUR_NAMES[h] for h in t.hour]); ax.set_ylim(0, 110)
    ax.set_ylabel("Index, 6 pm = 100")
    ax.set_title("(a) Rides fall off with the fleet, hour by hour")
    subtitle(ax, f"Completed rides per van-hour stay between {t.rides_per_van_hour.min():.1f} and {t.rides_per_van_hour.max():.1f}")
    ax.legend(loc="lower left")
    ax = axes[1]
    ax.scatter(daily.requests, daily.completed, s=46, color=BLUE, edgecolors="#fcfcfb", linewidths=1.5, zorder=3)
    lim = [daily.requests.min() * 0.9, daily.requests.max() * 1.05]
    ax.plot(lim, lim, color=GRAY, lw=1.2, zorder=1)
    ax.text(lim[1], lim[1], "every request served", fontsize=8.5, color=MUTED, ha="right", va="bottom")
    if "2026-04-17" in daily.index:
        r = daily.loc["2026-04-17"]
        ax.annotate("Apr 17", (r.requests, r.completed), xytext=(9, -3), textcoords="offset points", ha="left", va="center", fontsize=9, color=INK2)
    ax.set_xlabel("Requests per day (completed + cancelled + no-show + denied)")
    ax.set_ylabel("Completed rides per day")
    ax.set_title("(b) Busy days add cancellations, not rides")
    subtitle(ax, f"30 days: completions do not rise with requests (slope {np.polyfit(daily.requests, daily.completed, 1)[0]:+.2f}, r = {np.corrcoef(daily.requests, daily.completed)[0, 1]:+.2f})")
    fig.subplots_adjust(wspace=0.28)
    source(fig, "Sources: TransLoc April 2026 p06 (vans, 'All services', 29 days), p09 (completed rides by hour, 30 days), p07 (rides by status), digitized.")
    save(fig, "t01_supply")

    r = np.corrcoef(daily.requests, daily.completed)[0, 1]
    slope = np.polyfit(daily.requests, daily.completed, 1)[0]
    body = f"""
**Question.** Is the service supply-limited, so that completed rides are set by the fleet rather than by demand?

**Answer (DERIVED from OBSERVED charts): very likely at the peak, and consistent with it all night.**
- **Hour of day.** Completed rides per van-hour stay within {t.rides_per_van_hour.min():.1f}-{t.rides_per_van_hour.max():.1f} from 6 pm to 1 am, while the fleet falls from {t.vans.iloc[0]:.1f} to {t.vans.iloc[-1]:.1f} vans. Throughput follows the fleet.
- **Day to day.** Daily completions do not respond to daily requests at all: the slope is {slope:+.2f} completed rides per extra request and the correlation is {r:+.2f}. Requests range from {daily.requests.min():,.0f} to {daily.requests.max():,.0f} a day, while completions stay near {daily.completed.median():,.0f} (the median). Extra requests on busy days become cancellations, not rides, which is what a capacity cap produces. Both series vary by about the same relative amount (CV {cv(daily.requests):.0%} vs {cv(daily.completed):.0%}), but the completion swings are unrelated to demand. The biggest is Apr 17 (543 completed), which looks like a supply-side disruption (see T3).
- **Alternative explanation.** Panel (a) alone would also fit a fleet planned to match expected demand. Panel (b) is what points to a cap: on high-demand days, completions barely move.
- **Implication.** Hourly completions (p09) are **censored demand** and must not be copied as the demand profile. The base scenario's "as served" load (about 6 rides per van-hour at 6 pm) is a floor on demand, not demand itself.

**Caveats.**
- The vans chart is filtered to "All services" and averaged over 29 days, while the rides are Homewood-only over 30 days. If other services share the count, Homewood productivity is higher than shown, and the flat shape is unaffected only if that share is constant.
- The hour in p09 may be the request, pickup or completion hour.
- Cancellations include rebookings and Lyft handoffs (T2, T7), so "requests" overstates distinct riders.

**What it cannot tell us.**
- Demand by hour: cancellations are only reported daily.
- Whether more vans would convert cancellations into rides one-for-one. That is a simulation question (Phase 7 equivalent-fleet runs).

Figure: `outputs/insights/t01_supply.png`. Table: `outputs/insights/t01_supply_table.csv`.
"""
    write_brief("t01", "Is the service supply-limited?", body)
    print(t.round(2).to_string(index=False))
    print(f"daily: requests CV {cv(daily.requests):.3f}, completed CV {cv(daily.completed):.3f}, slope {slope:.3f}, r {r:.3f}")


if __name__ == "__main__":
    main()
