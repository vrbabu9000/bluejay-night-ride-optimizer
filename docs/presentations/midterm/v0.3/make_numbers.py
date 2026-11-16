"""Derive every number the v0.3 deck shows (no simulation). Writes v0.3/data/numbers.json.

    .venv/bin/python docs/presentations/midterm/v0.3/make_numbers.py

Sources (read-only):
  data/processed/obs_p06_vehicles.csv, obs_p07_status.csv, obs_p09_rides_by_hour.csv   April 2026 aggregates (digitized)
  outputs/sim/batch_L5_v1/                    30 synthetic two-van nights x 6 rules (per-run outcomes, metrics, trade-off)
  outputs/sim/L4_R3-2/                         designed evening, "Lyft arrives sooner" rule (worked transfer)
  outputs/sim/d53_experiment/                  pending-price comparison on the designed evening
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


def main():
    data = {"names": NAME, "rules": RULES, "april": april(), "groups": group_sizes(), "batch": batch(),
            "transfer": worked_transfer(), "pending": pending()}
    out = HERE / "data" / "numbers.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, indent=1))
    print(json.dumps({k: data[k] for k in ("april", "groups", "transfer")}, indent=1))
    print(json.dumps({k: data["batch"][k] for k in ("reached", "bookings", "r1u", "guardrail")}, indent=1))


if __name__ == "__main__":
    main()
