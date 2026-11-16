"""New figures for the midterm report (the reused f1-f9 come from the methodology PDF).

Every number is read from saved files; nothing is simulated here:
  docs/presentations/midterm/v0.4/derived/numbers.json   (the deck's numbers)
  data/scenarios/v2/L5/r*/requests.csv                    (the 30 pilot nights)

Run:  .venv/bin/python docs/report/midterm/make_report_figures.py
Writes PDF figures into docs/report/midterm/figures/.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "docs/technical/methodology_pdf"))
import make_figures as mf  # noqa: E402  (shared style, palette, box and arrow helpers)
from make_figures import (C_EVID, C_INPUT, C_OUT, C_POL, C_SIM, C_WARN, GRID, INK, MUTED,  # noqa: E402
                          arrow, box, plt)

OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)
NUM = json.load(open(REPO / "docs/presentations/midterm/v0.4/derived/numbers.json"))
L5 = REPO / "data/scenarios/v2/L5"
COLW = 3.25   # inches, one ICML column
TEXTW = 6.75  # inches, ICML \textwidth
PREDICTIVE = {"R2(15)", "R3(2)"}


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def label(code):
    return f"{NUM['names'][code]} [{code}]"


# ------------------------------------------------------------ R1 workload chain
def fig_workload():
    a = NUM["april"]
    fig, ax = plt.subplots(figsize=(TEXTW, 1.9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1.9)
    ax.axis("off")
    steps = [
        ("Completed rides,\n6 pm hour", f"{a['tooltip_18']:,} in 30 days\n≈ 170 per evening", "DERIVED"),
        ("Requests per\ncompleted ride", f"{a['status']['requests']:,} ÷ {a['status']['completed']:,}\n≈ {a['r_per_c']:.2f}", "DERIVED"),
        ("Requests in\nthat hour", "170 × 2.09\n≈ 355 per evening", "DERIVED + ASSUMED"),
        ("Per vehicle\non duty", f"355 ÷ {a['vehicles']['18:00']}\n≈ {a['rho']['18:00']} per\nvehicle-hour", "DERIVED + ASSUMED"),
    ]
    xs = [1.2, 3.75, 6.25, 8.8]
    for x, (title, body, tag) in zip(xs, steps):
        box(ax, x, 1.05, 2.2, 1.45, "", C_INPUT if "ASSUMED" in tag else C_EVID)
        ax.text(x, 1.5, title, ha="center", va="center", fontsize=8.2, color=INK, weight="bold")
        ax.text(x, 0.82, body, ha="center", va="center", fontsize=8.0, color=INK)
        ax.text(x, 0.12, tag, ha="center", va="center", fontsize=7.6, color=MUTED, weight="bold")
    for x0, x1 in zip(xs[:-1], xs[1:]):
        arrow(ax, (x0 + 1.12, 1.05), (x1 - 1.12, 1.05))
    save(fig, "r1_workload")


# ------------------------------------------------------------ R2 pilot arrivals
def fig_arrivals():
    nights = sorted(p for p in L5.iterdir() if (p / "requests.csv").exists())
    counts = [0] * 12
    for n in nights:
        for row in csv.DictReader(open(n / "requests.csv")):
            counts[min(int(row["t_request_s"]) // 300, 11)] += 1
    mean = [c / len(nights) for c in counts]
    fig, ax = plt.subplots(figsize=(COLW, 2.1))
    ax.axvspan(20, 30, color=C_SIM[0], zorder=0, lw=0)
    ax.bar([5 * i + 2.5 for i in range(12)], mean, width=4.4, color=C_POL[1], zorder=2)
    ax.text(25, max(mean) * 1.04, "burst window\n18:20–18:30", ha="center", va="bottom",
            fontsize=7.8, color=MUTED)
    ax.set_xticks(range(0, 61, 10))
    ax.set_xticklabels([f"18:{m:02d}" if m < 60 else "19:00" for m in range(0, 61, 10)], fontsize=7.8)
    ax.set_xlim(0, 60)
    ax.set_ylim(0, max(mean) * 1.35)
    ax.set_ylabel("requests per 5 min\n(mean of 30 nights)", fontsize=8.5)
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    save(fig, "r2_arrivals")
    return len(nights), sum(counts)


# ------------------------------------------------------------ R3 reach by rule
def fig_reach():
    b = NUM["batch"]
    rules = NUM["rules"]
    fig, ax = plt.subplots(figsize=(COLW, 2.35))
    ys = list(range(len(rules)))[::-1]
    for y, code, r, sd, lyft in zip(ys, rules, b["reached"], b["reached_sd"], b["bookings"]):
        # deck colours: blue predictive, green unassigned-time, grey waiting-time rules
        c = C_INPUT[1] if code in PREDICTIVE else (C_POL[1] if code == "R1u(10)" else C_EVID[1])
        ax.barh(y, r, height=0.62, color=c, zorder=2)
        ax.errorbar(r, y, xerr=sd, color=INK, lw=0.8, capsize=2, zorder=3)
        ax.text(0.02, y, f"{r:.2f}", va="center", ha="left", fontsize=7.8, color="white", weight="bold",
                zorder=4)
        ax.text(1.0, y, f"{lyft:.1f}", va="center", ha="right", fontsize=7.8, color=INK)
    ax.text(1.0, len(rules) - 0.35, "Lyft orders\nper night", ha="right", va="bottom", fontsize=7.2,
            color=MUTED)
    ax.set_yticks(ys)
    ax.set_yticklabels(rules, fontsize=8)
    ax.set_xlim(0, 1.0)
    ax.set_xticks([0, 0.25, 0.5, 0.75])
    ax.set_xlabel("share of the 28 requests reached by a vehicle\nwithin 15 min (mean ± SD over 30 nights)",
                  fontsize=8)
    ax.xaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    save(fig, "r3_reach")


# ------------------------------------------------------------ R4 transfer fates
def fig_fates():
    f = NUM["batch"]["fates"]
    rules = ["R1(10)", "R1(15)", "R1u(10)", "R2(15)", "R3(2)"]
    parts = [("completed", "Lyft trip completed", C_POL[1]),
             ("noshow", "Lyft no-show", C_EVID[1]),
             ("lag", "cancelled during the 2-min ordering lag", "#e8a09a"),
             ("after", "cancelled after the Lyft was ordered", C_WARN[1])]
    fig, ax = plt.subplots(figsize=(TEXTW * 0.72, 2.2))
    ys = list(range(len(rules)))[::-1]
    for y, code in zip(ys, rules):
        left = 0.0
        n = f[code]["transfers"]
        for key, name, col in parts:
            w = f[code][key] / n
            ax.barh(y, w, left=left, height=0.62, color=col, edgecolor="white", lw=1.0,
                    label=name if code == rules[0] else None)
            if w > 0.08:
                ax.text(left + w / 2, y, f"{f[code][key]}", ha="center", va="center", fontsize=7.6,
                        color="white", weight="bold")
            left += w
        ax.text(1.01, y, f"n = {n}", va="center", fontsize=7.8, color=INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([label(c) for c in rules], fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("share of transferred requests (totals over 30 nights; n = transfers)", fontsize=8.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.42, -0.32), ncol=2, frameon=False, fontsize=7.8)
    save(fig, "r4_fates")


# ------------------------------------------------------------ R5 architecture
def fig_architecture():
    fig, ax = plt.subplots(figsize=(TEXTW, 3.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.6)
    ax.axis("off")

    def card(x, y, w, h, title, body, colours, fs=7.8):
        box(ax, x, y, w, h, "", colours)
        ax.text(x, y + h / 2 - 0.22, title, ha="center", va="center", fontsize=fs + 0.4, color=INK, weight="bold")
        ax.text(x, y - 0.12, body, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.25)

    card(1.2, 3.85, 2.2, 0.85, "Scenario generator", "\nbuilt once, offline", C_INPUT)
    card(1.2, 2.45, 2.2, 1.25, "Scenario inputs", "\nrequests, places,\nparties, vans,\ntravel times", C_INPUT)
    card(1.2, 0.85, 2.2, 1.35, "Hidden draws", "\npatience, presence,\nLyft delay; never\nshown to dispatcher", C_WARN)
    arrow(ax, (1.2, 3.42), (1.2, 3.08))
    card(4.05, 1.75, 2.35, 2.0, "Simulator (referee)", "\nclock, van positions,\nriders aboard,\nrequest states;\nreveals each event\nonly when it happens", C_SIM)
    arrow(ax, (2.3, 2.45), (2.87, 2.05))
    arrow(ax, (2.3, 0.85), (2.87, 1.25))
    card(4.05, 4.1, 2.35, 0.8, "Recorded outcomes", "\nwaits, Lyft, van-km", C_OUT)
    arrow(ax, (4.05, 2.75), (4.05, 3.7))
    region = mf.FancyBboxPatch((6.0, 0.15), 3.95, 4.3, boxstyle="round,pad=0.02,rounding_size=0.08",
                               fc="none", ec=C_POL[1], lw=1.0, ls=(0, (4, 3)))
    ax.add_patch(region)
    ax.text(7.97, 4.22, "Decision step: sees only the past", ha="center", fontsize=8.0, color=C_POL[1], weight="bold")
    card(7.97, 3.35, 3.5, 0.85, "Route generation", "\ncandidate routes per van", C_POL)
    card(7.97, 2.15, 3.5, 0.85, "Van optimizer (MILP)", "\none route per van", C_POL)
    card(7.97, 0.85, 3.5, 1.05, "Transfer rule", "\nreads plan predictions;\nmay move requests to Lyft", C_POL)
    arrow(ax, (7.97, 2.92), (7.97, 2.58))
    arrow(ax, (7.97, 1.72), (7.97, 1.38))
    arrow(ax, (5.23, 2.3), (6.22, 3.2))
    ax.text(5.55, 3.05, "observable\nstate", ha="center", fontsize=7.6, color=MUTED)
    arrow(ax, (6.22, 0.75), (5.23, 1.0))
    ax.text(5.6, 0.45, "plan and\ntransfers", ha="center", fontsize=7.6, color=MUTED)
    save(fig, "r5_architecture")


# ------------------------------------------------------------ R6 roadmap
def fig_roadmap():
    fig, ax = plt.subplots(figsize=(TEXTW, 2.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2.5)
    ax.axis("off")
    steps = [("1  Behavioural\nsensitivity", "rerun saved nights\nunder other patience\nshapes, Lyft delays"),
             ("2  Five-van\nfeasibility", "run the 168-request\nevening; check solve\ntimes, candidate limits"),
             ("3  Agreed evaluation\ncriteria", "price one more rider\nreached per Lyft order;\npaired intervals"),
             ("4  Baseline, then\nthreshold search", "matched-budget\nbaseline; tune on some\nnights, report on fresh")]
    xs = [1.2, 3.75, 6.25, 8.8]
    for x, (t, b) in zip(xs, steps):
        box(ax, x, 1.62, 2.2, 1.5, "", C_POL)
        ax.text(x, 2.05, t, ha="center", va="center", fontsize=8.2, color=INK, weight="bold")
        ax.text(x, 1.3, b, ha="center", va="center", fontsize=7.8, color=INK)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        arrow(ax, (x0 + 1.12, 1.62), (x1 - 1.12, 1.62))
    box(ax, 5.0, 0.38, 9.8, 0.6, "", C_SIM)
    ax.text(5.0, 0.38, "In parallel, from step 2: dispatcher benchmark, rolling-horizon MILP vs greedy insertion,\n"
            "across fleet size, demand pattern and re-planning interval", ha="center", va="center",
            fontsize=7.8, color=INK)
    save(fig, "r6_roadmap")


# ------------------------------------------------------------ R7 trade-off (report wording: Lyft orders)
def fig_tradeoff():
    rows = list(csv.DictReader(open(REPO / "outputs/sim/batch_L5_v1/tradeoff_rule_summary.csv")))
    fig, ax = plt.subplots(figsize=(COLW, 2.5))
    offsets = {"R0": (-0.3, 0.02), "R1(10)": (0.4, 0.0), "R1(15)": (0.4, 0.0),
               "R1u(10)": (0.5, -0.03), "R2(15)": (-0.4, 0.0), "R3(2)": (0.4, -0.02)}
    for r in rows:
        name = r[""]
        x, y = float(r["lyft_bookings_mean"]), float(r["reached_15_share_mean"])
        nd = r["nondominated_on_means_2obj"] == "True"
        ax.plot(x, y, "o", ms=6, mec=C_POL[1], mfc=C_POL[1] if nd else "white", mew=1.3, zorder=3)
        dx, dy = offsets.get(name, (0.4, 0.0))
        ax.text(x + dx, y + dy, name, fontsize=7.6, va="center", ha="left" if dx > 0 else "right", color=INK)
    ax.set_xlim(-1.6, 12.5)
    ax.set_ylim(0.40, 0.80)
    ax.set_xlabel("Lyft orders per night (mean of 30 nights)", fontsize=8)
    ax.set_ylabel("share of all requests reached\nwithin 15 min (mean)", fontsize=8)
    ax.tick_params(labelsize=7.8)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.plot([], [], "o", ms=6, mec=C_POL[1], mfc=C_POL[1], label="not dominated by another tested rule")
    ax.plot([], [], "o", ms=6, mec=C_POL[1], mfc="white", mew=1.3, label="dominated (by R0)")
    ax.legend(loc="upper left", frameon=False, fontsize=7.2)
    save(fig, "r7_tradeoff")


if __name__ == "__main__":
    fig_workload()
    n, total = fig_arrivals()
    fig_reach()
    fig_fates()
    fig_architecture()
    fig_roadmap()
    fig_tradeoff()
    print(f"arrivals: {n} nights, {total} requests; figures written to {OUT}")
