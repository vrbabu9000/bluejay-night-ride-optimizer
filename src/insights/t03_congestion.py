"""
T3: Do cancellations rise when service degrades? Congestion and "patience" curves
across April's 30 days.

  (a) daily cancellation share (p07) vs daily median wait (p11)
  (b) daily P90 wait (p11) vs daily requests (p07: completed + cancelled + no-show + denied)
These are 30-point associations, not causal curves: busy days raise both waits and
cancellations, and day of week confounds both. They are SHAPES the simulator should
reproduce (G4), not parameters to copy.

Outputs: outputs/insights/t03_congestion.png, t03_daily_table.csv, docs/evidence/insights/t03.md
"""
import datetime as dt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from common import (BLUE, FIGS, GRAY, INK2, MUTED, ORANGE, observations, save, series, source, style, subtitle,
                    write_brief)


def main():
    style()
    obs = observations()
    d = pd.DataFrame({m: series(obs, "p07_status", m).value for m in ("completed", "canceled", "no_show", "denied")})
    d["requests"] = d.sum(axis=1)
    d["cancel_share"] = d.canceled / d.requests
    for m in ("p10", "median", "p90"):
        d[f"wait_{m}"] = series(obs, "p11_wait", f"wait_{m}").value
        d[f"ride_{m}"] = series(obs, "p12_ride", f"ride_{m}").value
    d["weekday"] = [dt.date.fromisoformat(i).strftime("%a") for i in d.index]
    FIGS.mkdir(parents=True, exist_ok=True)
    d.round(4).to_csv(FIGS / "t03_daily_table.csv")

    def fit(x, y):
        r = stats.pearsonr(x, y); rho = stats.spearmanr(x, y)
        b, a = np.polyfit(x, y, 1)
        return r[0], r[1], rho[0], b, a

    # within-weekday association: remove each weekday's mean from both variables first
    def within(col):
        return d[col] - d.groupby("weekday")[col].transform("mean")
    rw_a = stats.pearsonr(within("wait_median"), within("cancel_share"))[0]
    rw_b = stats.pearsonr(within("requests"), within("wait_p90"))[0]
    ex = d.drop("2026-04-17")
    r_a_ex = stats.pearsonr(ex.wait_median, ex.cancel_share)[0]
    r_b_ex = stats.pearsonr(ex.requests, ex.wait_p90)[0]
    ra = fit(d.wait_median, d.cancel_share)
    rb = fit(d.requests, d.wait_p90)
    rc = fit(d.requests, d.ride_p90)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, x, y, res, xl, yl, title, fmt in (
        (axes[0], d.wait_median, d.cancel_share, ra, "Median wait that day (min)", "Cancelled share of requests",
         "(a) Longer waits, more cancellations", lambda v, _: f"{v:.0%}"),
        (axes[1], d.requests, d.wait_p90, rb, "Requests that day", "P90 wait that day (min)",
         "(b) Tail waits rise only weakly with requests", lambda v, _: f"{v:.0f}")):
        other = d.index != "2026-04-17"
        ax.scatter(x[other], y[other], s=46, color=BLUE, edgecolors="#fcfcfb", linewidths=1.5, zorder=3)
        ax.scatter(x[~other], y[~other], s=60, color=ORANGE, edgecolors="#fcfcfb", linewidths=1.5, zorder=4)
        ax.annotate("Fri Apr 17 (fewest completions)", (x[~other].iloc[0], y[~other].iloc[0]), xytext=(-8, 6),
                    textcoords="offset points", ha="right", fontsize=9, color=INK2)
        xs = np.linspace(x.min(), x.max(), 50)
        ax.plot(xs, res[3] * xs + res[4], color=GRAY, lw=1.5, zorder=2)
        ax.set_xlabel(xl); ax.set_ylabel(yl); ax.set_title(title)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt))
        if ax is axes[1]:
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        subtitle(ax, f"30 days; Pearson r = {res[0]:.2f}, Spearman rho = {res[2]:.2f}")
    fig.subplots_adjust(wspace=0.28)
    source(fig, "Sources: TransLoc April 2026 p07 (rides by status), p11 (wait), p12 (ride), digitized. Associations only; not causal.")
    save(fig, "t03_congestion")

    body = f"""
**Question.** Do cancellations rise when service degrades? What do the day-to-day congestion and "patience" relationships look like?

**Answer (DERIVED, associational, 30 days).**
- **(a) Cancellations vs median wait.** Across days, the cancelled share rises with the median wait: Pearson r = {ra[0]:.2f} (p = {ra[1]:.3f}), Spearman rho = {ra[2]:.2f}. The fitted slope is **{ra[3] * 100:.1f} percentage points of requests per extra minute of median wait**.
- **(b) Tail waits vs requests.** The P90 wait rises with daily requests: r = {rb[0]:.2f} (p = {rb[1]:.3f}), rho = {rb[2]:.2f}, slope {rb[3] * 1000:.2f} min per 1,000 extra requests. The P90 ride time moves similarly (r = {rc[0]:.2f}).
- **Robustness.** (a) survives both checks: within-weekday r = {rw_a:.2f} (each weekday's mean removed from both variables), and r = {r_a_ex:.2f} without Apr 17. (b) is weaker: within-weekday r = {rw_b:.2f} and r = {r_b_ex:.2f} without Apr 17. Much of (b) is a weekday pattern: Fridays and Saturdays are busier and have longer tails.
- **Apr 17 (Friday) is a supply-side outlier, not a demand peak.** It had {d.loc['2026-04-17','requests']:,.0f} requests, below the month's maximum of {d.requests.max():,.0f} on {d.requests.idxmax()}, yet the **fewest completed rides ({d.loc['2026-04-17','completed']:.0f})**, the most cancellations ({d.loc['2026-04-17','canceled']:,.0f}, {d.loc['2026-04-17','cancel_share']:.0%} of requests), the longest waits (median {d.loc['2026-04-17','wait_median']:.1f} min, P90 {d.loc['2026-04-17','wait_p90']:.1f} min) and the most Lyft riders (674, p10). Fewer rides served on a normal-demand night points to a service disruption (fewer vans or slower operations), not a demand surge. That makes it the natural "reduced-fleet" stress case for the scenario grid, and a candidate question for Hopkins/TransLoc.

**How to use this.**
- These are **shapes the simulator must reproduce** under the baseline policy (G4). A fitted rider-patience model should produce a cancel-vs-wait slope of this order.
- They are **not** causal patience curves. Busy days push waits and cancellations up together, and a cancelled rider's wait is never observed (selection).
- Rebookings inflate the cancelled count (T2), so the level of the curve is uncertain even where its slope is informative.

**What it cannot tell us.**
- Individual patience. A rider-level distribution is not identified from daily aggregates.
- Hour-of-night effects: all the values are daily.
- Causal direction, and the day-of-week effects that confound both variables (only 4-5 of each weekday).

Figure: `outputs/insights/t03_congestion.png`. Table: `outputs/insights/t03_daily_table.csv`.
"""
    write_brief("t03", "Congestion and cancellation curves", body)
    print(d[["requests", "completed", "canceled", "cancel_share", "wait_median", "wait_p90"]].round(3).to_string())
    print("a:", [round(v, 4) for v in ra], "b:", [round(v, 4) for v in rb], "c:", [round(v, 4) for v in rc], "within-weekday:", round(rw_a, 3), round(rw_b, 3), "ex-Apr17:", round(r_a_ex, 3), round(r_b_ex, 3))


if __name__ == "__main__":
    main()
