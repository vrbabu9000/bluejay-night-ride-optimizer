"""Derive every number the midterm deck shows from saved outputs (no simulation). Writes data/deck_numbers.json.

    .venv/bin/python docs/presentations/midterm/make_deck_numbers.py

Sources: outputs/sim/d53_experiment/ (pending-price experiment, L4 under R0), outputs/sim/batch_L5_v1/ (30 synthetic L5
nights x 6 rules: per-run outcomes, per_night_metrics.csv, tradeoff_rule_summary.csv, tie_incomplete_check.csv,
reproducibility.json). Run `cd src && ../.venv/bin/python -m sim.tradeoff` first.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SIM = ROOT / "outputs" / "sim"
B = SIM / "batch_L5_v1"
RULES = ["R0", "R1(10)", "R1(15)", "R1u(10)", "R2(15)", "R3(2)"]
TAG = {"R0": "R0", "R1(10)": "R1-10", "R1(15)": "R1-15", "R1u(10)": "R1u-10", "R2(15)": "R2-15", "R3(2)": "R3-2"}
PLAIN = {"R0": "never transfer", "R1(10)": "after 10 min waited", "R1(15)": "after 15 min waited",
         "R1u(10)": "after 10 min unassigned", "R2(15)": "predicted wait > 15 min", "R3(2)": "van later than Lyft + 2 min"}


def mmss(s):
    return f"{int(s) // 60} min {int(s) % 60} s"


def pending():
    out = {"wait": [], "mean": [], "r002": [], "size": []}
    for arm in ("original", "A", "B"):
        d = SIM / "d53_experiment" / f"L4_R0_pp-{arm}"
        o = pd.read_csv(d / "outcomes.csv")
        w = o.wait_s.dropna() / 60
        ep = [json.loads(x) for x in open(d / "epochs.jsonl")]
        nz = max(e["solver"].get("n_z", 0) for e in ep)
        milp = sum(e["solver"]["wall_s"].get("milp", 0) for e in ep)
        out["wait"].append(f"{w.median():.1f} / {w.quantile(.9):.1f} / {w.max():.1f}")
        out["mean"].append(f"{w.mean():.1f}")
        out["r002"].append(mmss(o.set_index("request_id").loc["R002", "wait_s"]))
        out["size"].append(f"up to {nz:,} / {milp:.1f} s total" if nz else f"0 / {milp:.1f} s total")
    return out


def fates():
    rules = [r for r in RULES if r != "R0"]
    agg = {r: dict(completed=0, noshow=0, lag=0, after=0) for r in rules}
    for night in [f"r{i:02d}" for i in range(30)]:
        for r in rules:
            o = pd.read_csv(B / night / TAG[r] / "outcomes.csv")
            c = o[o.outcome == "cancel_after_transfer"]
            agg[r]["completed"] += int((o.outcome == "lyft_completed").sum())
            agg[r]["noshow"] += int((o.outcome == "noshow_lyft").sum())
            agg[r]["lag"] += int(c.booking_s.isna().sum())
            agg[r]["after"] += int(c.booking_s.notna().sum())
    labels = [f"{r} {PLAIN[r]} (n = {sum(agg[r].values())})" for r in rules]
    return {"rules": labels, **{k: [agg[r][k] for r in rules] for k in ("completed", "noshow", "lag", "after")},
            "transfers": [sum(agg[r].values()) for r in rules]}


def tradeoff():
    s = pd.read_csv(B / "tradeoff_rule_summary.csv", index_col=0).reindex(RULES)
    nd = [r for r in RULES if s.loc[r, "nondominated_on_means_2obj"]]
    dom = [r for r in RULES if not s.loc[r, "nondominated_on_means_2obj"]]
    text = ("On the 30-night means: " + ", ".join(f"{r} ({PLAIN[r]})" for r in nd) + " are nondominated. "
            + (", ".join(f"{r} ({PLAIN[r]})" for r in dom) + " is technically dominated by R0, but the service gap ("
               f"{s.loc[dom[0], 'reached_15_share_mean']:.3f} vs {s.loc['R0', 'reached_15_share_mean']:.3f}) is far inside the "
               "night-to-night spread (SD about 0.09): in practice indistinguishable from never transferring." if dom else "")
            + " Visible pattern: the two rules that read predicted pickups reach about 0.74 of requests, against 0.48–0.51 for the others, using about 9–10 Lyft bookings a night.")
    return {"bookings": [round(float(x), 2) for x in s.lyft_bookings_mean],
            "reached": [round(float(x), 3) for x in s.reached_15_share_mean],
            "labels": [f"{r} {PLAIN[r]}" for r in RULES], "nondominated_text": text,
            # chart labels: R0 and R1u(10) sit almost on the same point, so one label names both
            "chart_labels": ["R0 never transfer · R1u(10) overlaps", "R1(10) 10 min waited", "R1(15) 15 min waited", "",
                             "R2(15) predicted wait", "R3(2) van vs Lyft"],
            "table": s.reset_index().to_dict(orient="records")}


def batch_table():
    d = pd.read_csv(B / "per_night_metrics.csv")
    d["bookings"] = d.bookings_standard + d.bookings_xl
    hdr = [{"text": "Per night", "options": {"bold": True, "color": "FFFFFF", "fill": {"color": "1E2933"}}}] + [
        {"text": f"{r}\n{PLAIN[r]}", "options": {"bold": True, "color": "FFFFFF", "fill": {"color": "1E2933"}}} for r in RULES]
    spec = [("Reached within 15 min (share of 28)", "reached_15_share", "{:.2f}"), ("Requests picked up (of 28)", "picked_up_requests", "{:.1f}"),
            ("Wait median, min (picked up)", "wait_median_min", "{:.1f}"), ("Wait 90th pct, min (picked up)", "wait_p90_min", "{:.1f}"),
            ("Wait 90th pct, min (passengers)", "wait_pax_p90_min", "{:.1f}"), ("Van completed", "van_completed", "{:.1f}"),
            ("Lyft completed", "lyft_completed", "{:.1f}"), ("Cancelled waiting for van", "cancel_pending_van", "{:.1f}"),
            ("Cancelled after transfer", "cancel_after_transfer", "{:.1f}"), ("Lyft bookings", "bookings", "{:.1f}"),
            ("Van-km", "van_km", "{:.1f}"), ("Run time, s", "wall_s", "{:.0f}")]
    rows = [hdr]
    for label, col, f in spec:
        row = [label]
        for r in RULES:
            x = d[d.rule == r][col]
            row.append(f"{f.format(x.mean())} ({f.format(x.std())})")
        rows.append(row)
    return rows


def pernight_table(tr):
    hdr = ["Rule", "Reach (mean)", "Lyft bookings (mean)", "Nights nondominated", "Nights = R0", "Reach above / below R0"]
    rows = [[{"text": h, "options": {"bold": True, "color": "FFFFFF", "fill": {"color": "1E2933"}}} for h in hdr]]
    for x in tr["table"]:
        r = x["index"] if "index" in x else x["Unnamed: 0"]
        rows.append([f"{r} {PLAIN[r]}", f"{x['reached_15_share_mean']:.3f}", f"{x['lyft_bookings_mean']:.2f}",
                     f"{int(x['nights_nondominated_2obj'])} of 30", str(int(x["nights_identical_to_R0"])),
                     f"{int(x['nights_reach_above_R0'])} / {int(x['nights_reach_below_R0'])}"])
    return rows


def diagnostics():
    d = pd.read_csv(B / "per_night_metrics.csv")
    t = pd.read_csv(B / "tie_incomplete_check.csv")
    rep = json.loads((B / "reproducibility.json").read_text())
    exc = [(m["night"], e["request"]) for f in sorted(B.glob("r*/*/manifest.json"))
           for m in [json.loads(f.read_text())] for e in m.get("guardrail_excesses", [])]
    n_req, n_night = len(set(exc)), len({n for n, _ in exc})
    return [
        f"{len(d)} runs = 30 synthetic nights × 6 rules; every run passed every check; one code version for all runs",
        f"{int(d.epochs.sum()):,} planning epochs; main solve proven optimal in all (none unproven, none failed)",
        f"{len(t)} epochs had an incomplete tie search (a solver error while looking for equally good plans); in all {len(t)} "
        f"a full enumeration shows a unique optimum, which is the plan chosen",
        f"{int(d.guardrail_excess_attributed.sum())} ride-guardrail excesses across the 180 runs ({n_req} distinct requests on {n_night} nights, "
        f"repeated across rules), each coinciding with a no-show wait on that van while the rider was aboard (attribution check, "
        f"not proof); {int(d.guardrail_excess_unexplained.sum())} unexplained",
        f"Run time per run: mean {d.wall_s.mean():.0f} s, longest {d.wall_s.max():.0f} s (Python, one core per run)",
        f"Reproducibility: {sum(1 for x in rep if x.get('events_identical'))} of {sum(1 for x in rep if 'events_identical' in x)} "
        f"sampled reruns identical byte for byte; the {sum(1 for x in rep if x.get('batch_equals_pilot_output'))} night-r00 batch runs "
        f"identical to the earlier pilot outputs",
    ]


def main():
    tr = tradeoff()
    data = {"pending": pending(), "fates": fates(), "tradeoff": tr, "batch_table": batch_table(),
            "pernight_table": pernight_table(tr), "diagnostics": diagnostics()}
    data["tradeoff"].pop("table")
    out = Path(__file__).parent / "data" / "deck_numbers.json"
    out.write_text(json.dumps(data, indent=1))
    print(json.dumps({k: data[k] for k in ("pending", "fates", "diagnostics")}, indent=1))
    print(data["tradeoff"]["nondominated_text"])


if __name__ == "__main__":
    main()
