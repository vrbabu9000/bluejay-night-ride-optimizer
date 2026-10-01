"""
T7: Lyft share of riders and its relation to cancellations, April's 30 days.

  (a) daily Lyft share of riders = lyft / (van + lyft), from p10 (PowerBI, riders per day),
      with the pooled monthly share as a reference line
  (b) daily Lyft riders (p10) vs daily cancelled ride requests (p07, TransLoc), 30 points
These are associations, not conversion rates. Units differ (p10 counts riders, i.e. passengers,
p07 counts ride requests) and the two charts come from different systems. "Many cancelled become
Lyfts" is a Hopkins slide annotation on p07, not a measured rate, and the co-movement does not
show how many cancellations became Lyft trips.

Outputs: outputs/insights/t07_lyft.png, t07_lyft_table.csv, docs/evidence/insights/t07.md
"""
import datetime as dt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy import stats

from common import (BLUE, FIGS, GRAY, INK2, MUTED, ORANGE, SURFACE, marker_kw, observations, save, series, source,
                    style, subtitle, write_brief)

EMPHASIS = "2026-04-17"       # month's Lyft and cancellation peak; the day the story is about
PRINTED_TOTAL = 44374         # p10 printed "Total HW BJS Ridership"
WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEK_FULL = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday",
             "Sat": "Saturday", "Sun": "Sunday"}


def day_name(iso):
    """'2026-04-17' -> 'Apr 17'"""
    return f"Apr {dt.date.fromisoformat(iso).day}"


def fisher_ci(r, n, z=1.96):
    zr, se = np.arctanh(r), 1 / np.sqrt(n - 3)
    return float(np.tanh(zr - z * se)), float(np.tanh(zr + z * se))


def main():
    style()
    obs = observations()

    # ---- daily table -------------------------------------------------------------------------
    van = series(obs, "p10_vanlyft_daily", "van_riders")
    lyft = series(obs, "p10_vanlyft_daily", "lyft_riders")
    d = pd.DataFrame({"van_riders": van.value, "lyft_riders": lyft.value})
    d["riders"] = d.van_riders + d.lyft_riders
    d["lyft_share"] = d.lyft_riders / d.riders
    d["lyft_share_lo"] = lyft.lower / d.riders          # Lyft read interval (+/-1.5 px) over the same total
    d["lyft_share_hi"] = lyft.upper / d.riders
    d["canceled"] = series(obs, "p07_status", "canceled").value
    d["weekday"] = [dt.date.fromisoformat(i).strftime("%a") for i in d.index]
    n = len(d)
    assert n == 30 and d.notna().all().all()

    pooled = d.lyft_riders.sum() / d.riders.sum()
    pooled_if_printed = d.lyft_riders.sum() / PRINTED_TOTAL   # the whole 126-rider gap to the printed total is Van
    s = d.lyft_share
    q1, q3 = s.quantile([0.25, 0.75])
    lo_day, hi_day = s.idxmin(), s.idxmax()
    lo_wd, hi_wd = d.loc[lo_day, "weekday"], d.loc[hi_day, "weekday"]

    # ---- relation to cancellations -----------------------------------------------------------
    fit = stats.linregress(d.canceled, d.lyft_riders)
    tcrit = stats.t.ppf(0.975, n - 2)
    slope_lo, slope_hi = fit.slope - tcrit * fit.stderr, fit.slope + tcrit * fit.stderr
    r = fit.rvalue
    r_lo, r_hi = fisher_ci(r, n)
    rho = stats.spearmanr(d.canceled, d.lyft_riders)[0]
    d["fitted_lyft"] = fit.intercept + fit.slope * d.canceled
    d["residual"] = d.lyft_riders - d.fitted_lyft
    ex = d.drop(EMPHASIS)
    fit_ex = stats.linregress(ex.canceled, ex.lyft_riders)
    rho_ex = stats.spearmanr(ex.canceled, ex.lyft_riders)[0]
    within = lambda col: d[col] - d.groupby("weekday")[col].transform("mean")
    r_within = stats.pearsonr(within("canceled"), within("lyft_riders"))[0]
    tot_lyft, tot_canc = d.lyft_riders.sum(), d.canceled.sum()
    ratio = tot_lyft / tot_canc                      # Lyft riders per cancelled request (ratio of monthly totals)
    daily_ratio = d.lyft_riders / d.canceled
    resid_hi, resid_lo = d.residual.idxmax(), d.residual.idxmin()
    r_lyft_van = stats.pearsonr(d.lyft_riders, d.van_riders)[0]

    # weekday summary (4 or 5 days each)
    g = d.groupby("weekday").agg(days=("lyft_riders", "size"), lyft=("lyft_riders", "mean"),
                                 lyft_sum=("lyft_riders", "sum"), riders_sum=("riders", "sum"),
                                 canc=("canceled", "mean")).reindex(WEEK)
    g["share"] = g.lyft_sum / g.riders_sum
    rho_wd = stats.spearmanr(g.lyft, g.canc)[0]           # do the seven weekday means rank alike?
    fri_ex = ex[ex.weekday == "Fri"]
    fri_ex_share = fri_ex.lyft_riders.sum() / fri_ex.riders.sum()
    gx_share = (ex.groupby("weekday").lyft_riders.sum() / ex.groupby("weekday").riders.sum()).reindex(WEEK)
    top_wd, low_wd = g.share.idxmax(), g.share.idxmin()
    second_ex = gx_share.drop("Fri").idxmax()            # runner-up once Apr 17 is dropped from Friday

    # units: p10 Van riders vs p08 passengers, and party size (illustration only)
    pas = series(obs, "p08_passengers", "passengers").value
    comp = series(obs, "p07_status", "completed").value
    r_van_p08 = stats.pearsonr(d.van_riders, pas)[0]
    party = pas.sum() / comp.sum()
    canc_pax = tot_canc * party
    ratio_pax = tot_lyft / canc_pax

    # ---- CSV twin ---------------------------------------------------------------------------
    out = d[["weekday", "van_riders", "lyft_riders", "riders", "lyft_share", "lyft_share_lo", "lyft_share_hi",
             "canceled", "fitted_lyft"]].copy()
    out["pooled_share"] = pooled
    out.index.name = "date"
    out = out.rename(columns={"canceled": "canceled_requests"})
    FIGS.mkdir(parents=True, exist_ok=True)
    out.round({"van_riders": 1, "lyft_riders": 1, "riders": 1, "lyft_share": 4, "lyft_share_lo": 4, "lyft_share_hi": 4,
               "canceled_requests": 1, "fitted_lyft": 1, "pooled_share": 4}).to_csv(FIGS / "t07_lyft_table.csv")

    # ---- figure -----------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1.15, 1]})

    # (a) daily Lyft share
    ax = axes[0]
    day = np.arange(1, n + 1)
    ax.axhline(pooled, color=GRAY, lw=1.5, zorder=2)
    ax.plot(day, s, color=BLUE, zorder=3)          # 30 daily points: a continuous line, ringed markers only on the extremes
    i_hi, i_lo = list(d.index).index(hi_day), list(d.index).index(lo_day)
    ax.plot([day[i_lo]], [s[lo_day]], linestyle="none", zorder=4, **marker_kw(BLUE, 8))
    ax.plot([day[i_hi]], [s[hi_day]], linestyle="none", zorder=4, **marker_kw(ORANGE, 8))
    ax.annotate(f"{day_name(hi_day)}: {s[hi_day]:.1%}", (day[i_hi], s[hi_day]), xytext=(-10, -1),
                textcoords="offset points", ha="right", va="center", fontsize=9, color=INK2)
    ax.annotate(f"{day_name(lo_day)}: {s[lo_day]:.1%}", (day[i_lo], s[lo_day]), xytext=(0, -12),
                textcoords="offset points", ha="center", va="top", fontsize=9, color=INK2)
    ax.set_xlim(0, n + 1); ax.set_ylim(0, 0.5)
    ax.set_xticks([1, 5, 10, 15, 20, 25, 30])
    ax.set_yticks(np.arange(0, 0.51, 0.1))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("April 2026 (day of month)"); ax.set_ylabel("Lyft share of riders")
    ax.set_title(f"(a) Lyft's share of riders swings from {s.min():.0%} to {s.max():.0%}")
    subtitle(ax, f"Daily share of riders; the month pools to {pooled:.1%}, about one rider in four")
    ax.legend(handles=[Line2D([], [], color=BLUE, lw=2, label="Daily Lyft share"),
                       Line2D([], [], color=GRAY, lw=1.5, label=f"Pooled month share, {pooled:.1%}")],
              loc="lower right")

    # (b) Lyft riders vs cancelled requests
    ax = axes[1]
    other = d.index != EMPHASIS
    xs = np.linspace(d.canceled.min(), d.canceled.max(), 50)
    ax.plot(xs, fit.intercept + fit.slope * xs, color=GRAY, lw=1.5, zorder=2)
    ax.scatter(d.canceled[other], d.lyft_riders[other], s=46, color=BLUE, edgecolors=SURFACE, linewidths=1.5, zorder=3)
    ax.scatter(d.canceled[~other], d.lyft_riders[~other], s=60, color=ORANGE, edgecolors=SURFACE, linewidths=1.5, zorder=4)
    e = d.loc[EMPHASIS]
    ax.annotate(day_name(EMPHASIS), (e.canceled, e.lyft_riders), xytext=(-9, 4), textcoords="offset points",
                ha="right", va="bottom", fontsize=9, color=INK2)
    m = d.loc[resid_lo]                               # the one day that breaks the pattern (discussed in the brief)
    ax.annotate(day_name(resid_lo), (m.canceled, m.lyft_riders), xytext=(9, 0), textcoords="offset points",
                ha="left", va="center", fontsize=9, color=INK2)
    ax.set_ylim(0, d.lyft_riders.max() * 1.12)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_xlabel("Cancelled ride requests that day (p07)"); ax.set_ylabel("Lyft riders that day (p10)")
    ax.set_title("(b) Lyft riders rise with cancellations")
    subtitle(ax, f"30 days; Pearson r = {r:.2f}, Spearman rho = {rho:.2f}")
    ax.legend(handles=[Line2D([], [], color="none", marker="o", markersize=7, markerfacecolor=BLUE,
                              markeredgecolor=SURFACE, markeredgewidth=1.5, label="Day"),
                       Line2D([], [], color=GRAY, lw=1.5, label=f"Linear fit, slope {fit.slope:.2f}")],
              loc="upper left")
    fig.subplots_adjust(wspace=0.28)
    source(fig, "Sources: TransLoc April 2026 p07 (rides by status, Homewood Night Ride) and p10 (PowerBI, van + Lyft riders per day), digitized. "
                "Riders and requests are different units; association only.")
    save(fig, "t07_lyft")

    # ---- brief ------------------------------------------------------------------------------
    rows = "\n".join(f"| {WEEK_FULL[w]} | {int(g.days[w])} | {g.lyft[w]:,.0f} | {g.share[w]:.1%} | {g.canc[w]:,.0f} |" for w in WEEK)
    body = f"""
**Question.** How large is Lyft's share of Homewood riders, how much does it move from day to day, and how does it relate to cancellations?

**Answer (DERIVED from OBSERVED charts, associational, 30 days): Lyft carries about one rider in four, and its daily use moves closely with cancellations; the charts do not show a hand-off.**
- **Level.** Lyft carried {tot_lyft:,.0f} of {d.riders.sum():,.0f} riders in the month, a pooled share of **{pooled:.1%}** ({pooled_if_printed:.1%} if the whole {PRINTED_TOTAL - d.riders.sum():,.0f}-rider gap to the printed total of {PRINTED_TOTAL:,} were Van). The mean of the 30 daily shares is {s.mean():.1%} (median {s.median():.1%}, SD {s.std() * 100:.1f} points, middle half {q1:.1%} to {q3:.1%}).
- **Spread.** The daily share runs from **{s.min():.1%}** on {day_name(lo_day)} (a {WEEK_FULL[lo_wd]}; read interval {d.loc[lo_day, 'lyft_share_lo']:.1%} to {d.loc[lo_day, 'lyft_share_hi']:.1%}) to **{s.max():.1%}** on {day_name(hi_day)} (a {WEEK_FULL[hi_wd]}; {d.loc[hi_day, 'lyft_share_lo']:.1%} to {d.loc[hi_day, 'lyft_share_hi']:.1%}). Lyft riders per day range from {d.lyft_riders.min():,.0f} to {d.lyft_riders.max():,.0f} (mean {d.lyft_riders.mean():,.0f}); the two extremes are also the month's lowest and highest Lyft counts. Lyft does not mirror Van demand (r = {r_lyft_van:.2f} with daily Van riders).
- **By weekday** (April 1, 2026 is a Wednesday; 4 or 5 days each, so suggestive only):

| Weekday | Days | Lyft riders per day | Lyft share (pooled) | Cancelled requests per day |
|---|---|---|---|---|
{rows}

  {WEEK_FULL[top_wd]} has the highest share ({g.share[top_wd]:.1%}) and {WEEK_FULL[low_wd]} the lowest ({g.share[low_wd]:.1%}). One day drives the Friday figure: without {day_name(EMPHASIS)} Friday falls to {fri_ex_share:.1%}, still the highest weekday but only just ahead of {WEEK_FULL[second_ex]} ({gx_share[second_ex]:.1%}). The seven weekday means of Lyft riders and of cancelled requests rank alike (Spearman rho = {rho_wd:.2f}).
- **Relation to cancellations.** Days with more cancelled requests have more Lyft riders: Pearson r = **{r:.2f}** (95% CI {r_lo:.2f} to {r_hi:.2f}), Spearman rho = **{rho:.2f}**. The fitted slope is **{fit.slope:.2f} Lyft riders per additional cancelled request** (95% CI {slope_lo:.2f} to {slope_hi:.2f}; intercept {fit.intercept:,.0f} riders, so read the line only inside the observed range of {d.canceled.min():,.0f} to {d.canceled.max():,.0f} cancellations a day).
- **Robustness.** Without {day_name(EMPHASIS)} (the highest point on both axes) r = {fit_ex.rvalue:.2f}, rho = {rho_ex:.2f} and the slope is {fit_ex.slope:.2f}, so one day does not make the association. Removing each weekday's mean from both variables leaves r = {r_within:.2f}, so it is not only a weekday pattern. About {1 - r ** 2:.0%} of the daily variation in Lyft riders is left unexplained: the largest misses are {day_name(resid_lo)} ({-d.residual[resid_lo]:,.0f} fewer Lyft riders than the line predicts: {d.loc[resid_lo, 'canceled']:,.0f} cancellations but only about {round(d.loc[resid_lo, 'lyft_riders'], -1):,.0f} Lyft riders) and {day_name(resid_hi)} ({d.residual[resid_hi]:,.0f} more). The cause of the {day_name(resid_lo)} miss is unknown.
- **Ratio of monthly totals.** {tot_lyft:,.0f} Lyft riders over {tot_canc:,.0f} cancelled requests is **{ratio:.2f} Lyft riders per cancelled request** ({1 / ratio:.1f} cancelled requests per Lyft rider). Day by day the ratio runs from {daily_ratio.min():.2f} ({day_name(daily_ratio.idxmin())}) to {daily_ratio.max():.2f} ({day_name(daily_ratio.idxmax())}). The slope ({fit.slope:.2f}) is higher than the ratio ({ratio:.2f}) only because the line has a negative intercept. Neither number is a conversion rate (see the caveats).

**Caveats.**
- **Units differ.** Lyft counts riders (passengers); cancellations count ride requests. The p10 Van series matches p08's daily van passengers (r = {r_van_p08:.4f}, month sums {d.van_riders.sum():,.0f} vs {pas.sum():,.0f}), so p10 "riders" are passengers on completed van rides, and Lyft is presumably counted the same way (that cannot be checked). A completed request carries {party:.2f} passengers on average (p08 / p07). As an illustration only, if cancelled requests had the same party size (ASSUMED, unobserved), the {tot_canc:,.0f} cancelled requests would be about {round(canc_pax, -3):,.0f} passengers, and the ratio in like units would be about {ratio_pax:.2f} Lyft riders per cancelled passenger rather than {ratio:.2f}. The level of any ratio depends on this; the correlation would not change if the party size were constant.
- **"Many cancelled become Lyfts" is a Hopkins slide annotation** on p07, not a measured rate. Nothing in these charts records a hand-off.
- **The association does not show how many cancellations became Lyft trips.** The same daily pattern would arise if cancelled riders switch to Lyft, if Lyft is dispatched as planned extra supply on nights the vans fall behind (which is also when waits grow and riders cancel), or if a busy night simply raises both. It also cannot separate rebookings from lost requests: cancellations include rebookings (T2), so a rider who cancels and rebooks adds to the cancelled count without ever needing Lyft.
- **p10 is a different system (PowerBI)**, a low-resolution raster (each Lyft read is good to ±28 riders; the thin Apr 5 and Apr 30 segments carry 17-19% relative error). Its reads sum to {d.riders.sum():,.0f} against the printed {PRINTED_TOTAL:,} ({d.riders.sum() - PRINTED_TOTAL:+,.0f}, {(d.riders.sum() - PRINTED_TOTAL) / PRINTED_TOTAL:+.2%}). The two charts are matched by date only: "HW BJS" (p10) and "Homewood Night Ride" (p07) are not shown to be the same population, and the after-midnight day cut may differ. p07 reads carry about ±7 rides a day plus a possible common offset of 3 rides a day (0.4% of the month); neither moves the ratio beyond its third decimal.
- **Thirty points, one high-leverage day.** {day_name(EMPHASIS)} is the month's peak in both Lyft riders and cancellations; the checks above show the association survives without it. Day-of-week patterns rest on 4 or 5 days each.

**What it cannot tell us.**
- How many cancelled requests ended in a Lyft trip, a rebooked van ride, or no ride at all.
- When in the night Lyft is used: p10 has one point per day.
- The direction of cause, or what Lyft costs. Lyft trips are not priced here, and the team guide bars any claim of the form "Hopkins will save x% of Lyft trips".

**Used by.** The simulator's overflow rule and its G4 plausibility check (a loose band, not a target: Lyft riders {d.lyft_riders.min():,.0f} to {d.lyft_riders.max():,.0f} a day, {s.min():.0%} to {s.max():.0%} of riders, {ratio:.2f} per cancelled request as an association; modeled overflow is reported separately and never labelled Lyft trips), the cost story (A9 item 4: the size of the Lyft flow, about {tot_lyft / 1000:.1f}k riders a month, with dollars only as an ASSUMED-price illustration), and the TransLoc/Hopkins data wish list (A9 item 5: cancel reason with a Lyft-handoff flag, which would turn this association into a measured rate).

Figure: `outputs/insights/t07_lyft.png`. Table: `outputs/insights/t07_lyft_table.csv`.
"""
    write_brief("t07", "Lyft share and its relation to cancellations", body)

    print(d[["van_riders", "lyft_riders", "riders", "lyft_share", "canceled", "weekday"]].round(3).to_string())
    print(f"pooled {pooled:.4f} (printed-total basis {pooled_if_printed:.4f}); mean {s.mean():.4f}; median {s.median():.4f}; sd {s.std():.4f}; q1/q3 {q1:.4f}/{q3:.4f}")
    print(f"min {lo_day} {s.min():.4f}; max {hi_day} {s.max():.4f}")
    print(g.round(3).to_string()); print("Fri without Apr 17:", round(fri_ex_share, 4), "| ex-Apr17 shares:", gx_share.round(4).to_dict())
    print(f"r {r:.4f} CI [{r_lo:.3f}, {r_hi:.3f}]  rho {rho:.4f}  slope {fit.slope:.4f} CI [{slope_lo:.3f}, {slope_hi:.3f}]  intercept {fit.intercept:.1f}")
    print(f"ex-Apr17: r {fit_ex.rvalue:.4f} rho {rho_ex:.4f} slope {fit_ex.slope:.4f}; within-weekday r {r_within:.4f}")
    print(f"ratio of totals {ratio:.4f} ({tot_lyft:.1f} / {tot_canc:.1f}); daily ratio {daily_ratio.min():.3f} .. {daily_ratio.max():.3f}")
    print(f"largest residuals: {resid_lo} {d.residual[resid_lo]:.1f}, {resid_hi} {d.residual[resid_hi]:.1f}")
    print(f"units: r(van, p08) {r_van_p08:.4f}, sums {d.van_riders.sum():.1f} vs {pas.sum():.1f}; party {party:.4f}; cancelled pax {canc_pax:.0f}; ratio per pax {ratio_pax:.4f}")


if __name__ == "__main__":
    main()
