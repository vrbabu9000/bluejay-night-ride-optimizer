"""Diagnose a failed guardrail-attribution check (M7 plan §3c; the pattern found in M6 C r02, 24 Nov 2026).

    cd src && ../.venv/bin/python -m sim.m7_explain <run_dir> [<run_dir> ...]

For each van ride over the guardrail that the run check could not attribute, take the last van no-show on that van
during the ride. At that moment, enumerate every order of drop-offs for the riders then aboard, starting from the
no-show stop, with the travel matrix and a 30-s drop dwell. The failure is the known pattern ("explained") if all of:
  1. unavoidable: every drop order leaves some rider over the guardrail (minimum total passenger-seconds over > 0);
  2. shared: at least two riders were aboard;
  3. bounded: the flagged rider's excess is no larger than the minimum total excess over all drop orders, plus the
     13-s matrix tolerance (so the dispatcher did not add excess beyond what the no-show made unavoidable).
Anything else is "not explained" and its night is excluded under §3c. Reads saved files only.
"""
import itertools
import json
import sys
from pathlib import Path

import pandas as pd

from . import dispatch as D
from . import inputs, m6
from .l5_pilot import MATRIX_TOL_S, guardrail_excesses


def explain(d):
    d = Path(d)
    man = json.loads((d / "manifest.json").read_text())
    scen = inputs.load(man["level"], check_hash=False)
    assert scen.content_hash == man["content_hash"]
    m = scen.params["travel_multiplier"]
    tr = inputs.Travel(m, m)
    run = {"out": pd.read_csv(d / "outcomes.csv"), "events": pd.read_csv(d / "events.csv")}
    o, ev = run["out"].set_index("request_id"), run["events"]
    R = {r.rid: r for r in scen.requests}
    g = {rid: D.guardrail_s(tr.van(r.o, r.d), D.Config()) for rid, r in R.items()}
    res = []
    for e in guardrail_excesses(run, scen, tr):
        if e["attributed"]:
            continue
        x = o.loc[e["request"]]
        ns = ev[(ev.event == "state") & (ev.state_to == "noshow_van") & (ev.van == x.van) & (ev.t_s > x.pickup_s)
                & (ev.t_s <= x.drop_s)]
        if ns.empty:
            res.append({**e, "explained": False, "why": "no van no-show during the ride"}); continue
        t0 = int(ns.t_s.max())
        stop = ev[(ev.van == x.van) & (ev.event == "curb_arrival") & (ev.request == ns.iloc[-1].request)]
        loc = R[ns.iloc[-1].request].o if stop.empty else R[stop.iloc[-1].request].o
        aboard = [rid for rid, y in o.iterrows() if y.van == x.van and y.outcome == "van_completed"
                  and y.pickup_s <= t0 < y.drop_s]
        best = None
        for order in itertools.permutations(aboard):
            t, l, tot = t0, loc, 0
            for rid in order:
                t += tr.van(l, R[rid].d)
                tot += R[rid].q * max(0, t - o.loc[rid, "pickup_s"] - g[rid])
                t += D.DWELL_S
                l = R[rid].d
            best = tot if best is None else min(best, tot)
        ok = best > 0 and len(aboard) >= 2 and e["excess_s"] <= best + MATRIX_TOL_S
        res.append({**e, "noshow_t_s": t0, "aboard": aboard, "min_total_pax_s_over": int(best),
                    "explained": bool(ok),
                    "why": "unavoidable excess shared among riders aboard after a van no-show" if ok else
                    ("avoidable" if best == 0 else "single rider aboard" if len(aboard) < 2
                     else "excess larger than the unavoidable minimum")})
    return res


if __name__ == "__main__":
    for p in sys.argv[1:]:
        for r in explain(p):
            print(p, json.dumps(r, default=str))
