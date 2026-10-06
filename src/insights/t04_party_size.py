"""
T4: Party size (passengers per completed ride).

Daily ratio = p08 passengers / p07 completed rides. p08 counts van riders only (it matches the
p10 van riders, r = 0.9994), so this is van passengers per completed ride. The MEAN is DERIVED
from the two charts. The DISTRIBUTION over party sizes 1..4 is not identified by a mean: the
plan's pilot shape P(1..4) = .72/.19/.06/.03 (mean 1.40, decision D-08) is ASSUMED.

Reported: month pooled ratio, mean, median, sd and extremes of the 30 daily ratios; reading
uncertainty (Monte Carlo on independent errors, and the worst case where every error lines up);
the mean by weekday; a test of whether the ratio changes with daily volume (correlation and slope
against completed rides, with robustness checks); how far the daily spread exceeds what reading
noise and independent party-size draws could produce; and what a mean does and does not pin down.

Error bars in the figure are conservative: the ratio's lower bound is (p08 lower) / (p07 upper) and
its upper bound is (p08 upper) / (p07 lower).

The script reads obs_p07_status.csv and obs_p08_passengers.csv directly, so it does not rewrite
data/processed/observations.csv.

Outputs: outputs/insights/t04_party_size.png, t04_party_size_table.csv, docs/evidence/insights/t04.md
"""
import datetime as dt
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from common import (BLUE, BLUE_LIGHT, FIGS, GRAY, INK2, MUTED, PROCESSED, marker_kw, save, series, source, style,
                    subtitle, write_brief)

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HIGHLIGHT = "2026-04-17"                     # the disrupted night (p07, T3)
RUN = ("2026-04-24", "2026-04-28")           # a run of high days, picked after looking: descriptive only
SIZES = np.arange(1, 5)
PILOT = np.array([0.72, 0.19, 0.06, 0.03])   # ASSUMED (D-08)


def day_label(iso, weekday=True):
    d = dt.date.fromisoformat(iso)
    return f"{d:%a} {d:%b} {d.day}" if weekday else f"{d:%b} {d.day}"


def day_axis(ax, iso_dates):
    """One tick per calendar day: day number, with the weekday initials in a quieter row below."""
    days = [int(i[-2:]) for i in iso_dates]
    ax.set_xticks(days, [str(k) for k in days])
    ax.tick_params(axis="x", labelsize=9.5)
    for k, i in zip(days, iso_dates):
        wd = dt.date.fromisoformat(i).strftime("%a")[:2]
        ax.text(k, -0.085, wd, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=7.5,
                color=INK2 if wd in ("Sa", "Su") else MUTED)
    ax.grid(axis="x", visible=False)
    ax.set_xlabel("April 2026 (weekends in darker type)", labelpad=17)


def main():
    style()
    obs = pd.concat([pd.read_csv(PROCESSED / f) for f in ("obs_p07_status.csv", "obs_p08_passengers.csv")],
                    ignore_index=True)
    comp, pax = series(obs, "p07_status", "completed"), series(obs, "p08_passengers", "passengers")
    assert list(comp.index) == list(pax.index), "p07 and p08 dates differ"
    off = series(obs, "p07_status", "denied").value.mean()      # the +3.3 rides/day reading of Denied

    d = pd.DataFrame({"completed": comp.value, "completed_lo": comp.lower, "completed_hi": comp.upper,
                      "passengers": pax.value, "passengers_lo": pax.lower, "passengers_hi": pax.upper})
    d["ratio"] = d.passengers / d.completed
    d["ratio_lo"] = d.passengers_lo / d.completed_hi           # conservative: numerator low, denominator high
    d["ratio_hi"] = d.passengers_hi / d.completed_lo
    d["weekday"] = [dt.date.fromisoformat(i).strftime("%a") for i in d.index]
    n = len(d)
    ratio = d.ratio

    # --- the mean and its reading uncertainty ---
    P, C = d.passengers.sum(), d.completed.sum()
    pooled = P / C
    i_min, i_max = ratio.idxmin(), ratio.idxmax()
    rng = np.random.default_rng(20260929)
    sims = [rng.uniform(d.passengers_lo, d.passengers_hi).sum() / rng.uniform(d.completed_lo, d.completed_hi).sum()
            for _ in range(5000)]
    mc_lo, mc_hi = np.percentile(sims, [2.5, 97.5])
    hw_p, hw_c = (d.passengers_hi - d.passengers_lo).sum() / 2, (d.completed_hi - d.completed_lo).sum() / 2
    worst_lo, worst_hi = (P - hw_p) / (C + hw_c), (P + hw_p) / (C - hw_c)
    alt_offset = P / (C - 30 * off)                            # if p07 Completed is +off/day too high
    hw = (d.ratio_hi - d.ratio_lo) / 2
    n_excl = int(((d.ratio_lo > pooled) | (d.ratio_hi < pooled)).sum())

    # --- weekday ---
    by = d.groupby("weekday").ratio.agg(["mean", "count"]).reindex(WEEKDAYS)
    groups = [ratio[d.weekday == w] for w in WEEKDAYS]
    anova_p = stats.f_oneway(*groups).pvalue
    we = d.weekday.isin(["Sat", "Sun"])
    wk_mean, we_mean = ratio[~we].mean(), ratio[we].mean()
    wd_txt = ", ".join(f"{w} {by.loc[w, 'mean']:.2f}" for w in WEEKDAYS)
    fri_ex = ratio[(d.weekday == "Fri") & (d.index != HIGHLIGHT)].mean()
    resid = ratio - ratio.groupby(d.weekday).transform("mean")
    within_sd = math.sqrt((resid ** 2).sum() / (n - len(WEEKDAYS)))
    in_run = (d.index >= RUN[0]) & (d.index <= RUN[1])

    # --- does the ratio change with daily volume? ---
    x, y = d.completed, ratio
    r, p_r = stats.pearsonr(x, y)
    rho = stats.spearmanr(x, y)[0]
    fit = stats.linregress(x, y)
    tcrit = stats.t.ppf(0.975, n - 2)
    ci_r = np.tanh(np.arctanh(r) + np.array([-1, 1]) * 1.96 / math.sqrt(n - 3))
    s100, s100_lo, s100_hi = (100 * v for v in (fit.slope, fit.slope - tcrit * fit.stderr, fit.slope + tcrit * fit.stderr))
    r_ex17 = stats.pearsonr(x.drop(HIGHLIGHT), y.drop(HIGHLIGHT))[0]
    r_ex_max = stats.pearsonr(x.drop(i_max), y.drop(i_max))[0]
    xw = x - x.groupby(d.weekday).transform("mean")
    r_within = stats.pearsonr(xw, resid)[0]
    fit_p = stats.linregress(x, d.passengers)                  # passengers per additional completed ride

    def r_with_extra_noise():
        """r(ratio, completed) after adding one more dose of reading noise to both counts."""
        c = x + rng.uniform(-1, 1, n) * (d.completed_hi - d.completed_lo) / 2
        p = d.passengers + rng.uniform(-1, 1, n) * (d.passengers_hi - d.passengers_lo) / 2
        return stats.pearsonr(c, p / c)[0]

    bias = np.mean([r_with_extra_noise() for _ in range(2000)]) - r   # push toward negative r from denominator noise

    # --- is the daily spread more than reading noise and independent party-size draws? ---
    m = pooled
    sd_ride = {"min": math.sqrt((m - 1) * (2 - m)),            # all mass on sizes 1 and 2
               "max": math.sqrt((m - 1) * (4 - m)),            # all mass on sizes 1 and 4
               "pilot": math.sqrt((PILOT * SIZES ** 2).sum() - (PILOT * SIZES).sum() ** 2)}
    samp = {k: math.sqrt(np.mean(v ** 2 / d.completed)) for k, v in sd_ride.items()}   # sd of a day's mean party size
    read_sd = math.sqrt(np.mean((hw / math.sqrt(3)) ** 2))
    exp_max, exp_pilot = math.hypot(samp["max"], read_sd), math.hypot(samp["pilot"], read_sd)
    sd = ratio.std()

    # --- what a mean does and does not identify ---
    solo_lo, solo_hi = 1 - (m - 1), 1 - (m - 1) / 3            # share of solo rides: others all pairs / all size 4
    lam = m - 1
    pois = np.array([math.exp(-lam) * lam ** (k - 1) / math.factorial(k - 1) for k in SIZES])
    pois = pois / pois.sum()                                   # 1 + Poisson(lam), truncated at 4 (D-08 alternative)
    pilot_mean, pois_mean = float(PILOT @ SIZES), float(pois @ SIZES)
    shape = lambda p: "/".join(f"{v:.2f}".lstrip("0") for v in p)
    if mc_lo <= pilot_mean <= mc_hi:
        fit_txt = "inside the reading interval, so it agrees with the data"
    elif worst_lo <= pilot_mean <= worst_hi:
        fit_txt = "inside the worst-case reading interval but outside the independent-error one, so a fair match, not an exact one"
    else:
        fit_txt = "outside even the worst-case reading interval, so the pilot shape does not match the data"

    # --- CSV twin: the plotted numbers ---
    FIGS.mkdir(parents=True, exist_ok=True)
    out = d[["weekday", "completed", "completed_lo", "completed_hi", "passengers", "passengers_lo", "passengers_hi",
             "ratio", "ratio_lo", "ratio_hi"]].copy()
    out["pooled_ratio"] = pooled
    out.index.name = "date"
    out.round({"completed": 1, "completed_lo": 1, "completed_hi": 1, "passengers": 1, "passengers_lo": 1,
               "passengers_hi": 1, "ratio": 4, "ratio_lo": 4, "ratio_hi": 4, "pooled_ratio": 4}).to_csv(
        FIGS / "t04_party_size_table.csv")

    # --- figure ---
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    days = np.array([int(i[-2:]) for i in d.index])
    ax.plot([0.4, 30.5], [pooled, pooled], color=GRAY, lw=1.5, zorder=1)
    ax.text(30.85, pooled, f"Month pooled\n{pooled:.2f}", ha="left", va="center", fontsize=9.5, color=INK2)
    ax.errorbar(days, ratio, yerr=np.vstack([ratio - d.ratio_lo, d.ratio_hi - ratio]), fmt="none", ecolor=BLUE_LIGHT,
                elinewidth=1.4, capsize=3, capthick=1.4, zorder=2)
    ax.plot(days, ratio, color=BLUE, **marker_kw(BLUE, 8), zorder=3)
    ax.annotate(f"{day_label(i_max)}: {ratio[i_max]:.2f}", (int(i_max[-2:]), d.ratio_hi[i_max]), xytext=(0, 6),
                textcoords="offset points", ha="center", va="bottom", fontsize=9.5, color=INK2)
    ax.annotate(f"{day_label(i_min)}: {ratio[i_min]:.2f}", (int(i_min[-2:]), d.ratio_lo[i_min]), xytext=(0, -6),
                textcoords="offset points", ha="center", va="top", fontsize=9.5, color=INK2)
    day_axis(ax, list(d.index))
    ax.set_xlim(0.4, 33.6)
    ax.set_ylim(1.0, 1.72)
    ax.set_yticks(np.arange(1.0, 1.71, 0.1))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}"))
    ax.set_ylabel("Passengers per completed ride")
    ax.set_title(f"A completed ride carries {pooled:.2f} passengers on average, from {ratio.min():.2f} to {ratio.max():.2f} by day")
    subtitle(ax, "Van passengers (p08) per completed ride (p07); bars show the reading interval; axis starts at 1.0 (one passenger per ride)")
    fig.subplots_adjust(bottom=0.2)
    source(fig, "Sources: TransLoc April 2026 p07 (rides by status) and p08 (total passengers), digitized. Bars combine "
                "both readings conservatively: p08 lower / p07 upper to p08 upper / p07 lower.")
    save(fig, "t04_party_size")

    # --- brief ---
    body = f"""
**Question.** How many passengers does a completed ride carry, does that change with daily volume, and how much of the party-size distribution do these charts pin down?

**Answer (DERIVED from the OBSERVED p07 and p08 daily readings, except the party-size shapes, which are ASSUMED).**
- **Mean (DERIVED).** Van passengers per completed ride, month pooled: {P:,.0f} / {C:,.0f} = **{pooled:.3f}**. The 30 daily ratios average {ratio.mean():.3f} (median {ratio.median():.3f}, sd {sd:.3f}) and run from {ratio.min():.3f} ({day_label(i_min)}) to {ratio.max():.3f} ({day_label(i_max)}). Reading error moves the pooled ratio little: {mc_lo:.3f}-{mc_hi:.3f} (95%, independent errors), {worst_lo:.3f}-{worst_hi:.3f} if every error lined up, and {alt_offset:.3f} if the +{off:.1f} rides/day of p07's Denied reading is a common offset (p07 brief). Day to day, the ratio differs from the pooled one by more than its reading interval on {n_excl} of 30 days, so the spread is not reading noise.
- **No sign that it changes with volume.** Ratio vs completed rides: r = {r:+.2f} (95% CI {ci_r[0]:+.2f} to {ci_r[1]:+.2f}, p = {p_r:.2f}, Spearman rho = {rho:+.2f}); slope {s100:+.3f} per 100 extra completed rides (95% CI {s100_lo:+.3f} to {s100_hi:+.3f}), so no change larger than about {max(abs(s100_lo), abs(s100_hi)):.2f} per 100 rides. It holds without Apr 17 (r = {r_ex17:+.2f}), without {day_label(i_max, False)} (r = {r_ex_max:+.2f}) and within weekday (r = {r_within:+.2f}); reading noise in the denominator biases r by only about {bias:+.3f}. Regressing passengers on completed rides gives {fit_p.slope:.2f} ± {fit_p.stderr:.2f} passengers per extra ride, the same as the mean. The lowest-volume day, Apr 17 ({d.loc[HIGHLIGHT, 'completed']:.0f} rides), has an ordinary Friday ratio ({ratio[HIGHLIGHT]:.2f} against {fri_ex:.2f} on the other Fridays). With 30 days and completions confined to {d.completed.min():.0f}-{d.completed.max():.0f} rides a day, this rules out a strong dependence, not a weak one.
- **The distribution over party sizes 1, 2, 3, 4 is NOT identified by a mean.** With sizes 1-4 (the plan's assumed support), a mean of {m:.3f} is met by anything from {solo_lo:.0%} to {solo_hi:.0%} of rides being solo (every other party a pair, or every other party of size 4). The plan's pilot shape P(1..4) = {shape(PILOT)} (mean {pilot_mean:.2f}) is **ASSUMED**, and so is the Poisson-shifted alternative named in D-08 (read here as 1 + Poisson({lam:.3f}), truncated at 4: {shape(pois)}, mean {pois_mean:.2f}). Both have a mean close to the derived one but differ in shape (pairs {PILOT[1]:.0%} vs {pois[1]:.0%}; groups of 3 or 4 {PILOT[2:].sum():.0%} vs {pois[2:].sum():.0%}), and the charts cannot tell them apart. The data check only the pilot's mean, which is {pilot_mean - pooled:+.3f} ({(pilot_mean - pooled) / pooled:+.1%}) from the derived one: {fit_txt}.
- **It follows the day of week.** Mean ratio by weekday: {wd_txt} (4-5 days each; one-way ANOVA p = {anova_p:.4f}). Weekends average {we_mean:.2f} against {wk_mean:.2f} Monday to Friday.
- **The daily spread is about {sd / exp_max:.0f} times what independent party-size draws could give.** The sd of the daily ratio is {sd:.3f}. Reading noise adds about {read_sd:.3f}, and independent draws from any shape on 1-4 with this mean add at most {samp['max']:.3f} ({samp['pilot']:.3f} for the pilot shape), so at most {exp_max:.3f} together ({exp_pilot:.3f} for the pilot). Removing the weekday means leaves sd {within_sd:.3f}, partly a run of high days at the end of April ({day_label(RUN[0], False)} to {day_label(RUN[1], False)} average {ratio[in_run].mean():.2f} against {ratio[~in_run].mean():.2f} on the other days; the window was chosen after looking, so it is descriptive only). Unless p07 and p08 are counted on different bases from day to day, the mix of party sizes shifts from night to night; it is not one fixed distribution drawn independently for every ride.

**Caveats.**
- p08 counts van riders only (it matches the p10 van riders, r = 0.9994), so this is van passengers per completed ride. It assumes p07 Completed counts van rides only. The page does not say, and the slide's remark that cancelled requests become Lyfts suggests it does. If Completed included rides served by Lyft, the van ratio would be higher.
- "Party size" assumes one completed-ride record is one booking with one pickup and one drop-off.
- Completed rides only. Riders who cancelled are absent from p08; if party size relates to cancelling (larger parties are harder to serve, or less patient), the mean over all requests differs from {pooled:.2f}.
- Weekday means rest on 4-5 days each in a single month, and the calendar-date bars split each service night at midnight (D-03).

**What it cannot tell us.**
- The distribution of party sizes: the share of solo riders, pairs and groups of 3 or 4, or even that groups of 4 occur.
- Party size by hour, trip length or zone, or for requests that were not completed.

**Used by.**
- **Generator party-size input (D-08):** the mean {pooled:.2f} is DERIVED and the shape stays ASSUMED; each scenario should say which shape it uses. The daily range ({ratio.min():.1f}-{ratio.max():.1f}) and the weekday split (about {wk_mean:.2f} Monday to Friday, {we_mean:.2f} at weekends) suggest treating the mean as a night-type input and varying it as a sensitivity.
- **T5:** riders on board = rides in progress × {pooled:.2f}.

Figure: `outputs/insights/t04_party_size.png`. Table: `outputs/insights/t04_party_size_table.csv`.
"""
    write_brief("t04", "Party size (passengers per completed ride)", body)

    print(f"pooled {pooled:.4f} (P {P:,.1f} / C {C:,.1f}); mean {ratio.mean():.4f} median {ratio.median():.4f} sd {sd:.4f}")
    print(f"min {i_min} {ratio.min():.4f}; max {i_max} {ratio.max():.4f}; interval half-width mean {hw.mean():.4f}; days excluding pooled {n_excl}")
    print(f"pooled uncertainty: MC95 {mc_lo:.4f}-{mc_hi:.4f}; worst {worst_lo:.4f}-{worst_hi:.4f}; offset-alt {alt_offset:.4f}")
    print("weekday:", by["mean"].round(3).to_dict(), f"ANOVA p {anova_p:.5f}; weekend {we_mean:.3f} weekday {wk_mean:.3f}; Fri ex Apr17 {fri_ex:.3f}")
    print(f"volume: r {r:+.4f} p {p_r:.3f} CI {ci_r.round(3)} rho {rho:+.3f}; slope/100 {s100:+.4f} CI {s100_lo:+.4f} {s100_hi:+.4f}; "
          f"ex17 {r_ex17:+.3f} exmax {r_ex_max:+.3f} within {r_within:+.3f}; pax~completed {fit_p.slope:.3f}±{fit_p.stderr:.3f} (int {fit_p.intercept:.1f}); denominator-noise bias {bias:+.4f}")
    print(f"spread: sd {sd:.4f}; reading {read_sd:.4f}; sampling min/pilot/max {samp['min']:.4f}/{samp['pilot']:.4f}/{samp['max']:.4f}; "
          f"expected max {exp_max:.4f} pilot {exp_pilot:.4f}; within-weekday sd {within_sd:.4f}; run {ratio[in_run].mean():.3f} vs {ratio[~in_run].mean():.3f}")
    print(f"solo share bounds {solo_lo:.3f}-{solo_hi:.3f}; pilot mean {pilot_mean:.3f}; shifted Poisson {pois.round(4)} mean {pois_mean:.3f}")


if __name__ == "__main__":
    main()
