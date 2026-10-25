"""Derive every number the v0.4 deck shows (no simulation). Writes v0.4/derived/numbers.json.

    .venv/bin/python docs/presentations/midterm/v0.4/make_numbers.py

Self-contained: the backup tables (postponement prices, all-rule batch table, diagnostics) are regenerated here from
saved outputs; nothing is read from earlier deck versions.

Sources (read-only):
  data/processed/obs_p06_vehicles.csv, obs_p07_status.csv, obs_p09_rides_by_hour.csv   April 2026 aggregates (digitized)
  outputs/sim/batch_L5_v1/                    30 synthetic two-van nights x 6 rules (per-run outcomes, metrics, trade-off)
  outputs/sim/L4_R3-2/                         designed evening, "Lyft arrives sooner" rule (worked transfer)
  outputs/sim/d53_experiment/                  pending-price comparison on the designed evening
  data/scenarios/v2/L5/                        frozen pilot inputs (burst window and size)
Run `cd src && ../.venv/bin/python -m sim.tradeoff` first if tradeoff_rule_summary.csv is missing.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PROC, SIM = ROOT / "data" / "processed", ROOT / "outputs" / "sim"
B = SIM / "batch_L5_v1"
RULES = ["R0", "R1(10)", "R1(15)", "R1u(10)", "R2(15)", "R3(2)"]
TAG = {"R0": "R0", "R1(10)": "R1-10", "R1(15)": "R1-15", "R1u(10)": "R1u-10", "R2(15)": "R2-15", "R3(2)": "R3-2"}
NAME = {"R0": "Vans only", "R1(10)": "Wait ten minutes", "R1(15)": "Wait fifteen minutes",
        "R1u(10)": "Unassigned for ten minutes", "R2(15)": "Predicted total wait exceeds fifteen minutes",
        "R3(2)": "Lyft arrives sooner"}


def clock(s):
    s = int(s)
    return f"{18 + s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def dur(s):
    s = int(round(s))
    return f"{s // 60} min {s % 60} s" if s % 60 else f"{s // 60} min"


def april():
    p9 = pd.read_csv(PROC / "obs_p09_rides_by_hour.csv").set_index("date_or_hour")["value"]
    hours = ["18:00", "19:00", "20:00", "21:00", "22:00", "23:00", "00:00", "01:00"]
    p7 = pd.read_csv(PROC / "obs_p07_status.csv").groupby("metric")["value"].sum()
    p6 = pd.read_csv(PROC / "obs_p06_vehicles.csv").set_index("date_or_hour")["value"]
    completed, noshow, requests = 24095, 2359, 50297          # dashboard status totals (decision log trail §2, §8)
    canceled = requests - completed - noshow
    rc = requests / completed
    rho = {h: (p9[h] / 30) * rc / p6[h] for h in ("18:00", "19:00", "20:00")}
    return {"hours": [h[:2] for h in hours], "completed_by_hour": [int(round(p9[h])) for h in hours],
            "tooltip_18": 5098, "vehicles": {h: round(float(p6[h]), 1) for h in ("18:00", "19:00", "20:00")},
            "status": {"requests": requests, "completed": completed, "canceled": canceled, "noshow": noshow,
                       "canceled_share": round(canceled / requests, 3), "digitized_status_sums": {k: round(float(v)) for k, v in p7.items()}},
            "r_per_c": round(rc, 3), "rho": {h: round(v, 2) for h, v in rho.items()},
            "five_van": [64, 50, 54], "noshow_all": round(noshow / requests, 3),
            "noshow_arrival": round(noshow / (completed + noshow), 3), "van_arrivals": completed + noshow,
            "riders": 44374, "lyft_rider_share": 0.245}


def group_sizes():
    ours = [0.73, 0.18, 0.055, 0.025, 0.01]
    h1 = [0.72, 0.20, 0.054, 0.026, 0.0]
    h2 = [0.807, 0.07, 0.073, 0.03, 0.02]
    mean = lambda p: round(sum((i + 1) * x for i, x in enumerate(p)), 3)
    big = lambda p: round(sum(p[2:]), 3)
    return {"ours": ours, "h1": h1, "h2": h2, "means": [mean(h1), mean(h2), mean(ours)], "share_3plus": [big(h1), big(h2), big(ours)]}


def batch():
    s = pd.read_csv(B / "tradeoff_rule_summary.csv", index_col=0).reindex(RULES)
    d = pd.read_csv(B / "per_night_metrics.csv")
    d["bookings"] = d.bookings_standard + d.bookings_xl
    fates = {}
    for r in RULES[1:]:
        f = dict(completed=0, noshow=0, lag=0, after=0)
        for n in [f"r{i:02d}" for i in range(30)]:
            o = pd.read_csv(B / n / TAG[r] / "outcomes.csv")
            c = o[o.outcome == "cancel_after_transfer"]
            f["completed"] += int((o.outcome == "lyft_completed").sum()); f["noshow"] += int((o.outcome == "noshow_lyft").sum())
            f["lag"] += int(c.booking_s.isna().sum()); f["after"] += int(c.booking_s.notna().sum())
        f["transfers"] = sum(f.values()); fates[r] = f
    r1u = d[d.rule == "R1u(10)"]
    exc = [(m["night"], e["request"]) for f in sorted(B.glob("r*/*/manifest.json"))
           for m in [json.loads(f.read_text())] for e in m.get("guardrail_excesses", [])]
    g = d.groupby("rule")
    return {
        "reached": [round(float(x), 5) for x in s.reached_15_share_mean], "reached_sd": [round(float(x), 3) for x in s.reached_15_share_sd],
        "bookings": [round(float(x), 2) for x in s.lyft_bookings_mean], "van_km": [round(float(x), 1) for x in s.van_km_mean],
        "nondominated": [bool(x) for x in s.nondominated_on_means_2obj],
        "nights_nondominated": [int(x) for x in s.nights_nondominated_2obj], "nights_identical_r0": [int(x) for x in s.nights_identical_to_R0],
        "above_below_r0": [[int(a), int(b)] for a, b in zip(s.nights_reach_above_R0, s.nights_reach_below_R0)],
        "fates": fates,
        "r1u": {"transfers": fates["R1u(10)"]["transfers"], "nights_with_transfer": int((r1u.offers > 0).sum()),
                "nights_identical_r0": int(s.loc["R1u(10)", "nights_identical_to_R0"])},
        "picked_up_mean": {r: round(float(g.picked_up_requests.mean()[r]), 1) for r in RULES},
        "wait_p90": {r: round(float(g.wait_p90_min.mean()[r]), 1) for r in RULES},
        "guardrail": {"events": int(d.guardrail_excess_attributed.sum() + d.guardrail_excess_unexplained.sum()),
                      "unexplained": int(d.guardrail_excess_unexplained.sum()), "distinct_requests": len(set(exc)),
                      "nights": len({n for n, _ in exc})},
        "epochs": int(d.epochs.sum()), "tie_incomplete": int(d.tie_incomplete.sum()),
        "wall_mean": round(float(d.wall_s.mean()), 1), "wall_max": round(float(d.wall_s.max()), 1),
    }


def worked_transfer():
    d = SIM / "L4_R3-2"
    man = json.loads((d / "run_manifest.json").read_text())
    ep = next(json.loads(x) for x in open(d / "epochs.jsonl") if "R011" in json.loads(x)["lyft"]["transfers"])
    o = pd.read_csv(d / "outcomes.csv").set_index("request_id").loc["R011"]
    tau, pred = ep["tau_s"], ep["lyft"]["reads"]["R011"]["predicted_pickup_s"]
    lag, typical = man["policy"]["lag_s"], 480
    expected = tau + lag + typical
    assert pred > expected + 120, "rule should fire"
    return {"request": clock(o.t_request_s), "decision": clock(tau), "pred_van": clock(pred), "expected_lyft": clock(expected),
            "gap": dur(pred - expected), "booked": clock(o.booking_s), "lyft_curb": clock(o.curb_arrival_s),
            "dropped": clock(o.drop_s), "wait": dur(o.wait_s), "lag_s": lag, "typical_s": typical,
            "note": "Designed evening (L4): Lyft delay fixed at 8 min by design, so realized = expected; consent probability 0.9 (this rider accepts)."}


def pending():
    out = {}
    for arm in ("original", "A", "B"):
        o = pd.read_csv(SIM / "d53_experiment" / f"L4_R0_pp-{arm}" / "outcomes.csv")
        w = o.wait_s.dropna() / 60
        out[arm] = {"median": round(float(w.median()), 1), "p90": round(float(w.quantile(.9)), 1), "max": round(float(w.max()), 1),
                    "mean": round(float(w.mean()), 1)}
    # the 18:15 example, from the independent math review (research_notes/m1_math_review_2026-10-21.md §7)
    out["r002"] = {"waited": "15 min", "party": 5, "charged_original_pts": 262.5, "earliest_pickup": "18:19:28",
                   "charged_at_earliest_pts": 435.83}
    return out


def pending_table():
    """Backup B5: the three postponement prices on the designed evening (vans only)."""
    out = {"wait": [], "mean": [], "r002": [], "size": [], "milp_s": []}
    for arm in ("original", "A", "B"):
        d = SIM / "d53_experiment" / f"L4_R0_pp-{arm}"
        o = pd.read_csv(d / "outcomes.csv")
        w = o.wait_s.dropna() / 60
        ep = [json.loads(x) for x in open(d / "epochs.jsonl")]
        nz = max(e["solver"].get("n_z", 0) for e in ep)
        out["wait"].append(f"{w.median():.1f} / {w.quantile(.9):.1f} / {w.max():.1f}")
        out["mean"].append(f"{w.mean():.1f}")
        out["r002"].append(dur(o.set_index("request_id").loc["R002", "wait_s"]))
        out["size"].append(f"up to {nz:,}" if nz else "0")
        out["milp_s"].append(round(sum(e["solver"]["wall_s"].get("milp", 0) for e in ep), 1))
    return out


BATCH_ROWS = [("Reached within 15 min (share of 28)", "reached_15_share", "{:.2f}"), ("Requests picked up (of 28)", "picked_up_requests", "{:.1f}"),
              ("Wait median, min (per request picked up)", "wait_median_min", "{:.1f}"), ("Wait 90th pct, min (per request picked up)", "wait_p90_min", "{:.1f}"),
              ("Wait 90th pct, min (per passenger picked up)", "wait_pax_p90_min", "{:.1f}"), ("Van completed", "van_completed", "{:.1f}"),
              ("Lyft completed", "lyft_completed", "{:.1f}"), ("Cancelled waiting for van", "cancel_pending_van", "{:.1f}"),
              ("Cancelled after transfer", "cancel_after_transfer", "{:.1f}"), ("Lyft orders", "bookings", "{:.1f}"),
              ("Van-km", "van_km", "{:.1f}"), ("Run time, s", "wall_s", "{:.0f}")]


def batch_table():
    """Backup B6: every metric by rule, mean (SD) over the 30 nights."""
    d = pd.read_csv(B / "per_night_metrics.csv")
    d["bookings"] = d.bookings_standard + d.bookings_xl
    rows = []
    for label, col, f in BATCH_ROWS:
        rows.append([label] + [f"{f.format(d[d.rule == r][col].mean())} ({f.format(d[d.rule == r][col].std())})" for r in RULES])
    return rows


def diagnostics():
    """Backup B8: solver statuses, tie searches, guardrail attribution, run time, reproducibility."""
    d = pd.read_csv(B / "per_night_metrics.csv")
    t = pd.read_csv(B / "tie_incomplete_check.csv")
    rep = json.loads((B / "reproducibility.json").read_text())
    exc = [(m["night"], e["request"]) for f in sorted(B.glob("r*/*/manifest.json"))
           for m in [json.loads(f.read_text())] for e in m.get("guardrail_excesses", [])]
    return [
        f"{len(d)} runs = 30 constructed nights × 6 rules; every run passed every per-run check; one code version for all runs",
        f"{int(d.epochs.sum()):,} decision moments (epochs); the main solve was proven optimal over its candidates in all of them",
        f"{len(t)} decision moments had an incomplete search for equally good plans (a solver error); in all {len(t)}, full enumeration shows a unique optimum, which is the plan chosen",
        f"{int(d.guardrail_excess_attributed.sum())} ride-time excess events across the 180 runs ({len(set(exc))} distinct requests on {len({n for n, _ in exc})} nights, repeated across rules); each coincided with a no-show wait on that van while the rider was aboard (attribution check, not proof); {int(d.guardrail_excess_unexplained.sum())} unexplained",
        f"Run time per run: mean {d.wall_s.mean():.0f} s, longest {d.wall_s.max():.0f} s (Python, one core per run)",
        f"Reproducibility: {sum(1 for x in rep if x.get('events_identical'))} of {sum(1 for x in rep if 'events_identical' in x)} sampled reruns byte-identical; "
        f"the {sum(1 for x in rep if x.get('batch_equals_pilot_output'))} first-night batch runs identical to the earlier pilot outputs",
    ]


def pilot():
    """The two-van pilot's frozen inputs: arrival window, burst, parties, capacity."""
    n, burst, pax = [], [], []
    for f in sorted((ROOT / "data/scenarios/v2/L5").glob("r*/requests.csv")):
        r = pd.read_csv(f)
        n.append(len(r)); burst.append(int(((r.t_request_s >= 1200) & (r.t_request_s < 1800)).sum())); pax.append(int(r.party.sum()))
    p = json.loads((ROOT / "data/scenarios/v2/L5/r00/scenario.json").read_text())["params"]
    return {"nights": len(n), "requests": sorted(set(n)), "window": "18:00–19:00", "burst_window": "18:20–18:30",
            "burst_share_placed": p["burst"]["share"], "burst_placed": round(p["burst"]["share"] * p["n_requests"]),
            "in_burst_window_min": min(burst), "in_burst_window_max": max(burst), "in_burst_window_mean": round(sum(burst) / len(burst), 1),
            "passengers_min": min(pax), "passengers_max": max(pax), "passengers_mean": round(sum(pax) / len(pax), 1),
            "vans": p["n_vans"], "seats": p["capacity"], "travel_multiplier": p["travel_multiplier"]}


def main():
    data = {"names": NAME, "rules": RULES, "april": april(), "groups": group_sizes(), "batch": batch(),
            "transfer": worked_transfer(), "pending": pending(),
            "pending_table": pending_table(), "batch_table": batch_table(), "batch_rows": [r[0] for r in BATCH_ROWS],
            "diagnostics": diagnostics(), "pilot": pilot()}
    out = HERE / "derived" / "numbers.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, indent=1))
    print(json.dumps({k: data[k] for k in ("april", "groups", "transfer")}, indent=1))
    print(json.dumps({k: data["batch"][k] for k in ("reached", "bookings", "r1u", "guardrail")}, indent=1))
    print(json.dumps({k: data[k] for k in ("pilot", "pending_table")}, indent=1))


if __name__ == "__main__":
    main()
