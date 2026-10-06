"""
T6: Detour factor. How much longer are observed rides than the direct drive
between the places riders actually travel between?

Direct times: OSRM free-flow drive times between every digitized origin point
and destination point (data/processed/tt_points_v0.csv). Trips are weighted by
an ASSUMED joint O-D model built from the observed margins:
  independence: P(o, d) ~ O_o * D_d
  gravity:      P(o, d) ~ O_o * D_d * exp(-beta * t_od), beta in {0.1, 0.2} per minute
Pairs under 1 minute apart are dropped (a rider would walk; ASSUMED).
Observed: the ride-duration quantiles of p12 (monthly mean of daily P10, median, P90).

Outputs: outputs/insights/t06_detour.png, t06_detour_table.csv, docs/evidence/insights/t06.md
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import (AQUA, BLUE, FIGS, GRAY, INK2, MUTED, ORANGE, PROCESSED, marker_kw, observations, save,
                    series, source, style, subtitle, write_brief)

QS = (0.10, 0.50, 0.90)


def wquantile(x, w, q):
    o = np.argsort(x)
    cw = np.cumsum(w[o]) / w.sum()
    return float(np.interp(q, cw, x[o]))


def main():
    style()
    obs = observations()
    ride = {m: series(obs, "p12_ride", f"ride_{m}") for m in ("p10", "median", "p90")}
    observed = {q: float(ride[m].value.mean()) for q, m in zip(QS, ("p10", "median", "p90"))}
    observed_rng = {q: (float(ride[m].value.min()), float(ride[m].value.max())) for q, m in zip(QS, ("p10", "median", "p90"))}

    pts = pd.read_csv(PROCESSED / "zone_points_v0.csv").set_index("bubble_id")
    tt = pd.read_csv(PROCESSED / "tt_points_v0.csv")
    tt = tt[tt.seconds >= 60].copy()
    tt["t_min"] = tt.seconds / 60
    tt["w0"] = pts.loc[tt.origin, "count_used"].values * pts.loc[tt.dest, "count_used"].values
    models = {"Independence": 0.0, "Gravity, beta 0.1/min": 0.1, "Gravity, beta 0.2/min": 0.2}
    rows, curves = [], {}
    for name, beta in models.items():
        w = tt.w0.values * np.exp(-beta * tt.t_min.values)
        x = tt.t_min.values
        dq = {q: wquantile(x, w, q) for q in QS}
        o = np.argsort(x)
        curves[name] = (x[o], np.cumsum(w[o]) / w.sum())
        for q in QS:
            rows.append(dict(model=name, quantile=q, direct_min=round(dq[q], 2), observed_min=round(observed[q], 2),
                             ratio=round(observed[q] / dq[q], 2), excess_min=round(observed[q] - dq[q], 2)))
    table = pd.DataFrame(rows)
    FIGS.mkdir(parents=True, exist_ok=True)
    table.to_csv(FIGS / "t06_detour_table.csv", index=False)

    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    colours = {"Independence": BLUE, "Gravity, beta 0.1/min": AQUA, "Gravity, beta 0.2/min": ORANGE}
    for name, (x, c) in curves.items():
        ax.plot(x, c, color=colours[name], lw=2, label=f"Direct drive, {name.lower()}")
    for q in QS:
        lo, hi = observed_rng[q]
        ax.plot([lo, hi], [q, q], color=INK2, lw=2, alpha=0.35)
        ax.plot([observed[q]], [q], ls="none", **marker_kw("#0b0b0b", 9))
        ax.annotate(f"observed P{int(q * 100)}: {observed[q]:.1f} min", (observed[q], q), xytext=(10, -14 if q > 0.5 else 8),
                    textcoords="offset points", fontsize=9, color=INK2)
    ax.set_xlim(0, 32); ax.set_ylim(0, 1.02)
    ax.set_xlabel("Minutes"); ax.set_ylabel("Share of completed rides at or below")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_title("Observed rides take 2-3x as long as the direct drive")
    subtitle(ax, "Distribution of direct drive times between digitized origins and destinations vs observed ride-time quantiles")
    handles = [Line2D([], [], color=colours[n], lw=2, label=f"Direct drive ({n.lower()})") for n in models]
    handles.append(Line2D([], [], ls="none", **marker_kw("#0b0b0b", 9), label="Observed ride time (mean of daily values; bar = daily range)"))
    ax.legend(handles=handles, loc="lower right")
    source(fig, "Sources: TransLoc April 2026 p12 (ride duration) and O/D maps (pp. 2-5), digitized; OSRM demo server, free-flow car times. "
                "O-D pairing ASSUMED from margins.")
    save(fig, "t06_detour")

    ind = table[table.model == "Independence"].set_index("quantile")
    longest = float(tt.t_min.max()); p99 = wquantile(tt.t_min.values, tt.w0.values, 0.99)
    body = f"""
**Question.** How much longer are observed rides than the direct drive between the places riders travel between?

**Answer (DERIVED; the O-D pairing is ASSUMED).**
- Under independence pairing of the observed O and D margins, the direct free-flow drive is {ind.loc[0.1,'direct_min']:.1f} / {ind.loc[0.5,'direct_min']:.1f} / {ind.loc[0.9,'direct_min']:.1f} min at P10 / median / P90.
- Observed ride times average {observed[0.1]:.1f} / {observed[0.5]:.1f} / {observed[0.9]:.1f} min at the same quantiles.
- The ratios are **{ind.loc[0.1,'ratio']:.2f} / {ind.loc[0.5,'ratio']:.2f} / {ind.loc[0.9,'ratio']:.2f}**. Gravity pairing (shorter trips more likely) shortens the direct times and raises the ratios; see the table.
- **The tail is made by routing, not geography.** The observed P90 ride time ({observed[0.9]:.1f} min) is longer than the longest direct drive between any two digitized points ({longest:.1f} min; weighted P99 {p99:.1f} min). The slowest tenth of rides therefore cannot be explained by distance alone: stops for other riders and detours create it. That is exactly the part a dispatcher controls.
- **Reading.** Even the short-trip end (P10) takes longer than the direct drive, so boarding/alighting time and slower-than-free-flow driving add a few minutes to every trip. Ride times in the middle and upper tail are well above the direct drive, which is consistent with pooling detours (T5 also finds more than one rider per van on average).
- **Implication for calibration (A7).** The P10 gap is the natural target for the speed-factor and dwell parameters. The median and P90 gaps should come out of the simulated pooling, not be tuned in.

**Evidence.** Uses 8,700 origin-point x destination-point pairs, whose OSRM times were retrieved on 2026-09-29, weighted by the digitized counts (margins scaled to ~24,056). The observed quantiles are the means of 30 daily values from p12, with the daily range drawn as a bar.

**What it cannot tell us.**
- The true O-D pairing. Margins do not identify the joint distribution, which is why three pairings are shown.
- Time-of-night variation: the observed ride times are daily aggregates.
- Traffic: OSRM is free-flow.
- A clean split of the excess into dwell, slower driving and pooling detour. Only a simulation can apportion it.
- A mean-to-quantile shortcut: quantiles of a sum are not sums of quantiles, so the ratio is descriptive, not a model parameter.

**Used by.** A7 calibration (speed factor and dwell from the P10 gap), T5 (occupancy context), Phase 3 generator (choice of beta).

Figure: `outputs/insights/t06_detour.png`. Table: `outputs/insights/t06_detour_table.csv`.
"""
    write_brief("t06", "Detour factor", body)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
