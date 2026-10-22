"""D-53 comparison of pending-price formulations on one frozen level (default L4 under R0).

    cd src && ../.venv/bin/python -m sim.compare            (expects the three runs written by sim.run)

Reads outputs/sim/L4_R0/ (original), L4_R0_pp-A/, L4_R0_pp-B/ and writes outputs/sim/d53_comparison.md:
one comparison table, the requests whose wait changed, and a worked epoch in which each formulation's chosen plan
is re-priced under all three formulations, separating route costs from pending prices.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import dispatch as D
from . import inputs
from .run import OUT, clock, enumerate_plans, pending_charge, pts, run_name, _mmss

ARMS = ("original", "A", "B")


class _Req:                     # the minimum of an Engine that run.pending_charge needs
    def __init__(self, scen):
        self.req = {r.rid: r for r in scen.requests}


def load_run(level, rule, arm):
    d = OUT / run_name(level, rule, arm)
    ep = [json.loads(x) for x in open(d / "epochs.jsonl")]
    return {"dir": d, "epochs": ep, "out": pd.read_csv(d / "outcomes.csv"),
            "manifest": json.loads((d / "run_manifest.json").read_text())}


def churn(epochs):
    """Pending time, assignment changes and ETA changes per request, from the epoch records."""
    pend_s, assign_changes, eta_moves, eta_max = {}, {}, {}, {}
    last_van, last_eta = {}, {}
    for k, ep in enumerate(epochs):
        nxt = epochs[k + 1]["tau_s"] if k + 1 < len(epochs) else ep["tau_s"]
        van_of = {r: v for v, c in ep["chosen"].items() for r in c["S"]}
        for o in ep["open"]:
            r = o["rid"]
            v = van_of.get(r, "~")
            if r in ep["pending"]:
                pend_s[r] = pend_s.get(r, 0) + (nxt - ep["tau_s"])
            if r in last_van and last_van[r] != v:
                assign_changes[r] = assign_changes.get(r, 0) + 1
            last_van[r] = v
            eta = ep["predicted_pickup_s"].get(r)
            if eta is not None and r in last_eta and abs(eta - last_eta[r]) > 60:
                eta_moves[r] = eta_moves.get(r, 0) + 1
                eta_max[r] = max(eta_max.get(r, 0), abs(eta - last_eta[r]))
            if eta is not None:
                last_eta[r] = eta
    return pend_s, assign_changes, eta_moves, eta_max


def summary(run, scen, travel):
    o = run["out"]
    ep = run["epochs"]
    picked = o[o.pickup_s.notna()]
    w = picked.wait_s / 60
    q = picked.party
    wp = np.repeat(w.to_numpy(), q.to_numpy())
    g = {r.rid: D.guardrail_s(travel.van(r.o, r.d), D.Config()) for r in scen.requests}
    viol = int(sum(1 for _, x in picked.iterrows() if x.ride_s > g[x.request_id]))
    pend_s, ac, em, emax = churn(ep)
    sv = [e["solver"] for e in ep]
    return {
        "completed (of all requests)": f"{(o.outcome == 'van_completed').sum()} of {len(o)}",
        "cancellations / no-shows": f"{o.outcome.str.startswith('cancel').sum()} / {o.outcome.str.startswith('noshow').sum()}",
        "wait median / P90 / max, min (requests picked up, n)": f"{w.median():.1f} / {w.quantile(.9):.1f} / {w.max():.1f} (n={len(w)})",
        "wait P90, passenger-weighted, min (passengers)": f"{np.quantile(wp, .9):.1f} (n={len(wp)})",
        "mean wait, min": f"{w.mean():.2f}",
        "ride P90 / max, min": f"{(picked.ride_s / 60).quantile(.9):.1f} / {(picked.ride_s / 60).max():.1f}",
        "guardrail violations": str(viol),
        "pending time, total / max per request, min": f"{sum(pend_s.values()) / 60:.1f} / {max(pend_s.values(), default=0) / 60:.1f}",
        "assignment changes (total)": str(sum(ac.values())),
        "ETA moves > 1 min (total) / largest move, min": f"{sum(em.values())} / {max(emax.values(), default=0) / 60:.1f}",
        "epochs (all proven optimal?)": f"{len(ep)} ({'yes' if all(s['status'] in ('optimal', 'empty') for s in sv) else 'NO'})",
        "candidate generation, s (total)": f"{sum(s['wall_s']['candidates'] for s in sv):.1f}",
        "MILP solve, s (total / slowest epoch)": f"{sum(s['wall_s']['milp'] for s in sv):.2f} / {max(s['wall_s']['milp'] for s in sv):.2f}",
        "tie enumeration, s (total)": f"{sum(s['wall_s']['ties'] for s in sv):.2f}",
        "run wall time, s": f"{run['manifest']['wall_s_total']:.1f}",
        "model size, max columns / z variables / rows": f"{max(s['n_columns'] for s in sv)} / {max(s.get('n_z', 0) for s in sv)} / {max(s.get('n_rows', 0) for s in sv)}",
    }


def worked_epoch(runs, scen, travel, tau):
    """Each arm's chosen plan at the same epoch (identical state across arms), re-priced under every formulation."""
    eng = _Req(scen)
    eps = {a: next(e for e in runs[a]["epochs"] if e["tau_s"] == tau) for a in ARMS}
    same_state = len({json.dumps([eps[a]["vans"], eps[a]["open"]]) for a in ARMS}) == 1
    ref = eps["original"]
    vids = [v["van"] for v in ref["vans"]]
    off, n = {}, 0
    for v in vids:
        off[v] = n
        n += len(ref["candidates"][v])
    L = [f"## Worked epoch {clock(tau)}: why the formulations choose different plans", "",
         f"State identical in all three runs: {'yes' if same_state else 'NO (plans below are from different states)'}. "
         f"{len(ref['open'])} requests open: " + ", ".join(f"{o['rid']} (party {o['q']}, waited {_mmss(o['waited_s'])})"
                                                           for o in ref["open"]) + ".", "",
         "Each row is the plan one formulation chose. **Route cost** is the same for every formulation (waiting, riding "
         "and driving points of the routes). The pending columns re-price that plan's pending requests under each "
         "formulation (points, excluding M; every plan here leaves the same number pending, so M cancels).", "",
         "| Plan chosen by | Routes | Pending | Route cost | Pending: original | Pending: A | Pending: B | Total: original | Total: A | Total: B |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for a in ARMS:
        ch = eps[a]["chosen"]
        js = []
        for v in vids:
            k = next(i for i, c in enumerate(ref["candidates"][v]) if c["S"] == ch[v]["S"])
            js.append(off[v] + k)
        route = sum(ch[v]["cost_u"] for v in vids)
        pend = eps[a]["pending"]
        pr = {k: sum(pending_charge(k, r, js, ref, eng, travel) for r in pend) for k in ARMS}
        routes = "<br>".join(f"{v}: {' '.join(ch[v]['seq']) or '-'}" for v in vids)
        L.append(f"| {a} | {routes} | {', '.join(pend) or '-'} | {pts(route):.2f} | "
                 + " | ".join(f"{pts(pr[k]):.2f}" for k in ARMS) + " | "
                 + " | ".join(f"{pts(route + pr[k]):.2f}" for k in ARMS) + " |")
    L += ["", "Reading the table: down each **Total** column, the smallest value is the plan that formulation chose "
          "(checked by full enumeration below). The route-cost column alone would favour one plan; the pending price "
          "decides which requests are cheapest to leave waiting.", ""]
    L += ["Per pending request, the price each formulation charges in the plan it chose (points):", "",
          "| Request | Party | Waited | original (next tick) | A (earliest physical pickup) | B (after the cheapest chosen route) |",
          "|---|---|---|---|---|---|"]
    allp = sorted({r for a in ARMS for r in eps[a]["pending"]})
    for r in allp:
        o = next(x for x in ref["open"] if x["rid"] == r)
        cells = []
        for a in ARMS:
            info = eps[a]["pending"].get(r)
            cells.append(f"{pts(info['pending_price_u']):.2f}" if info else "served")
        L.append(f"| {r} | {o['q']} | {_mmss(o['waited_s'])} | " + " | ".join(cells) + " |")
    checks = []
    for a in ARMS:
        _, plans = enumerate_plans(eps[a], eng, travel)
        best = plans[0]
        chosen = {v: c["S"] for v, c in eps[a]["chosen"].items()}
        ok = all(c["S"] == chosen[v] for v, c in zip(vids, best["combo"]))
        checks.append(f"{a}: {'matches' if ok else 'DIFFERS'} ({len(plans):,} plans)")
    L += ["", "Full enumeration of every compatible pair of candidate routes, priced independently of the MILP: "
          + "; ".join(checks) + ".", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", default="L4")
    ap.add_argument("--rule", default="R0")
    ap.add_argument("--epoch", type=int, default=900)
    a = ap.parse_args()
    scen = inputs.load(a.level)
    m = scen.params["travel_multiplier"]
    travel = inputs.Travel(m, m)
    runs = {arm: load_run(a.level, a.rule, arm) for arm in ARMS}
    rows = {arm: summary(runs[arm], scen, travel) for arm in ARMS}
    keys = list(rows["original"])
    L = [f"# D-53 comparison of pending-price formulations: {a.level} under {a.rule}", "",
         "Same frozen inputs, fleet, K = 3, φ, β, γ, guardrail, solver settings and curb-wait convention in every arm; "
         "only the pending price differs. Each arm runs the whole evening from its own decisions. Simulated outcomes "
         "of one designed validation night (16 requests): they show behaviour, not a ranking.", "",
         "| Measure | Original (next tick) | A (earliest physical pickup) | B (after a chosen route) |", "|---|---|---|---|"]
    for k in keys:
        L.append(f"| {k} | " + " | ".join(rows[arm][k] for arm in ARMS) + " |")
    outs = {arm: runs[arm]["out"].set_index("request_id") for arm in ARMS}
    L += ["", "## Requests whose wait changed by more than 2 minutes between any two arms (plus R002 and R005)", "",
          "| Request | Party | Requested | Wait: original | Wait: A | Wait: B | Ride: original | Ride: A | Ride: B |",
          "|---|---|---|---|---|---|---|---|---|"]
    for rid in outs["original"].index:
        ws = [outs[arm].loc[rid, "wait_s"] for arm in ARMS]
        if rid in ("R002", "R005") or max(ws) - min(ws) > 120:
            x = outs["original"].loc[rid]
            L.append(f"| {rid} | {x.party} | {clock(x.t_request_s)} | " + " | ".join(_mmss(w) for w in ws) + " | "
                     + " | ".join(_mmss(outs[arm].loc[rid, "ride_s"]) for arm in ARMS) + " |")
    L += ["", worked_epoch(runs, scen, travel, a.epoch)]
    path = OUT / "d53_comparison.md"
    path.write_text("\n".join(L) + "\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
