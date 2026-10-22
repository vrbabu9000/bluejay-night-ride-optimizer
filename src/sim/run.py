"""Run one frozen scenario through the event engine and write the logs.

    .venv/bin/python -m sim.run --level L4 --rule R0          (from src/, or with PYTHONPATH=src)

Outputs in outputs/sim/<level>_<rule>/ (gitignored):
    events.csv         every event: time, class, van, request, state change, details
    epochs.jsonl       one line per epoch: observable state, candidates with cost parts, chosen plan, pending,
                       solver status/objective/bound/gap/wall time, Lyft rule reads
    outcomes.csv       one row per request
    run_manifest.json  input hashes, settings, code and solver versions, status counts
    narrative.md       short human-readable account, with one worked comparison of competing plans
"""
import argparse
import dataclasses
import itertools
import json
import platform
import subprocess
import time
from collections import Counter
from pathlib import Path

import highspy
import pandas as pd

from . import dispatch as D
from . import engine as E
from . import inputs

OUT = inputs.ROOT / "outputs" / "sim"


def clock(s):
    if s is None or s != s:
        return "-"
    s = int(s)
    h, m, sec = 18 + s // 3600, (s % 3600) // 60, s % 60
    return f"{h % 24:02d}:{m:02d}:{sec:02d}"


def pts(u):
    return u / D.PT


def policy_for(scen, rule, K=None):
    p = scen.params
    cfg = D.Config() if K is None else D.Config(K=K)
    if p["level"] == "L4":
        return E.Policy(rule=rule, lag_s=p["lyft_lag_s"], consent_p=p["consent_p"],
                        rule_active_before_s=p["vans_on_duty_from_s"], dispatcher=cfg)
    if rule != "R0":
        raise SystemExit("only L4 exercises Lyft rules in M0")
    return E.Policy(rule="R0", dispatcher=cfg)


def run(level, rule="R0", K=None, out=None):
    scen = inputs.load(level)
    m = scen.params["travel_multiplier"]
    travel = inputs.Travel(m_v=m, m_L=m)
    pol = policy_for(scen, rule, K)
    t0 = time.perf_counter()
    eng = E.Engine(scen, travel, pol).run()
    wall = time.perf_counter() - t0
    out = Path(out or OUT / f"{level.replace('/', '_')}_{rule}")
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(eng.events).to_csv(out / "events.csv", index=False)
    with open(out / "epochs.jsonl", "w") as f:
        for ep in eng.epochs:
            f.write(json.dumps(ep, default=str) + "\n")
    outc = pd.DataFrame(eng.outcomes())
    outc.to_csv(out / "outcomes.csv", index=False)
    manifest = {
        "scenario": level, "content_hash": scen.content_hash, "frozen_hash_match": True,
        "matrix_sha256": travel.matrix_sha256, "travel_multiplier": {"m_v": travel.m_v, "m_L": travel.m_L},
        "policy": {k: v for k, v in dataclasses.asdict(pol).items() if k != "dispatcher"},
        "dispatcher": {"name": "C (restricted route-selection MILP, HiGHS)", **dataclasses.asdict(pol.dispatcher),
                       "cost_units_per_point": D.PT},
        "code": _git(), "python": platform.python_version(), "highspy": _highs_version(),
        "end_s": eng.end_s, "end_clock": clock(eng.end_s), "n_epochs": len(eng.epochs),
        "solver_status": dict(Counter(ep["solver"]["status"] for ep in eng.epochs)),
        "tie_status": dict(Counter(ep["solver"]["tie_status"] for ep in eng.epochs)),
        "outcomes": dict(Counter(outc.outcome)), "wall_s_total": round(wall, 2),
        "note": "wall times are diagnostics only; simulated solver latency is zero (D-46)"}
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    (out / "narrative.md").write_text(narrative(eng, scen, travel, manifest))
    return eng, out


def _git():
    root = str(inputs.ROOT)
    try:
        head = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", root, "status", "--porcelain", "src/sim"], capture_output=True,
                               text=True).stdout.strip()
        return {"head": head, "src_sim_uncommitted": bool(dirty)}
    except OSError:
        return {}


def _highs_version():
    h = highspy.Highs()
    return f"{h.versionMajor()}.{h.versionMinor()}.{h.versionPatch()}"


# ---------- narrative ----------
def narrative(eng, scen, travel, man):
    L = [f"# {man['scenario']} under {man['policy']['rule']}: what happened", ""]
    L += [f"Frozen inputs `{man['scenario']}` (content hash `{man['content_hash'][:12]}…`, matches FROZEN_v2.json). "
          f"Dispatcher C, K = {man['dispatcher']['K']} uncommitted pickups per route. Times are clock times "
          f"(18:00 = 0 s). The run ends at {man['end_clock']} after {man['n_epochs']} epochs.", "",
          "**Solver status per epoch:** " + ", ".join(f"{k} {v}" for k, v in man["solver_status"].items())
          + "; **ties:** " + ", ".join(f"{k} {v}" for k, v in man["tie_status"].items()) + ".", "",
          "**Outcomes:** " + ", ".join(f"{k} {v}" for k, v in man["outcomes"].items()) + ".", "",
          "These are simulated outcomes of a designed validation case, not evidence about the real service.", ""]
    L += ["## Requests", "", "| Request | Party | Requested | Outcome | Van | Curb arrival | Wait | Drop-off | Ride |",
          "|---|---|---|---|---|---|---|---|---|"]
    for o in eng.outcomes():
        L.append(f"| {o['request_id']} | {o['party']} | {clock(o['t_request_s'])} | {o['outcome']} | {o['van'] or '-'} | "
                 f"{clock(o['curb_arrival_s'])} | {_mmss(o['wait_s'])} | {clock(o['drop_s'])} | {_mmss(o['ride_s'])} |")
    L += ["", "## Van movements", ""]
    for vid in eng.vans:
        L += [f"**{vid}**", ""]
        for ev in eng.events:
            if ev["van"] != vid:
                continue
            if ev["event"] == "depart":
                L.append(f"- {clock(ev['t_s'])} departs for the {'pickup' if ev['stop'] == 'P' else 'drop-off'} "
                         f"of {ev['request']}, arrives {clock(ev['arrive_s'])}")
            elif ev["event"] == "state" and ev["state_to"] in ("onboard", "van_completed", "noshow_van"):
                what = {"onboard": "boards", "van_completed": "is dropped off", "noshow_van": "no-show recorded"}
                L.append(f"- {clock(ev['t_s'])} {ev['request']} {what[ev['state_to']]}")
            elif ev["event"] in ("arrive_no_rider", "curb_arrival", "on_duty"):
                L.append(f"- {clock(ev['t_s'])} {ev['event'].replace('_', ' ')} {ev['request'] or ''}".rstrip())
        L.append("")
    L += ["## Epochs where the plan changed", "",
          "| Epoch | Trigger | Open | Chosen routes | Pending | Status | Wall s |", "|---|---|---|---|---|---|---|"]
    prev = None
    for ep in eng.epochs:
        sig = json.dumps({v: c["seq"] for v, c in ep["chosen"].items()})
        if sig != prev:
            routes = "; ".join(f"{v}: " + " ".join(c["seq"]) for v, c in ep["chosen"].items() if c["seq"]) or "-"
            L.append(f"| {clock(ep['tau_s'])} | {', '.join(ep['triggers'])} | {len(ep['open'])} | {routes} | "
                     f"{', '.join(ep['pending']) or '-'} | {ep['solver']['status']} | {ep['solver']['wall_s']['total']} |")
        prev = sig
    L += ["", worked_example(eng, travel), small_example(eng, travel)]
    return "\n".join(L) + "\n"


def _mmss(s):
    if s is None or s != s:
        return "-"
    return f"{int(s) // 60}:{int(s) % 60:02d}"


def worked_example(eng, travel, n_show=3):
    """The first epoch with >= 2 vans and >= 3 open requests: the best joint plans, found by direct enumeration of
    every pair of candidate routes with disjoint requests (independent of the MILP), compared with the MILP."""
    ep = next((e for e in eng.epochs if len(e["vans"]) >= 2 and len(e["open"]) >= 3), None)
    if ep is None:
        return "## Worked comparison\n\nNo epoch with two vans and three or more open requests.\n"
    vids = [v["van"] for v in ep["vans"]]
    q = {o["rid"]: o["q"] for o in ep["open"]}
    tn = ep["solver"]["next_tick_s"]
    t_of = {o["rid"]: o["t_s"] for o in ep["open"]}
    pend_u = {r: q[r] * D.phi_u(max(0, tn - t_of[r])) for r in q}
    M = ep["solver"]["M_u"]
    plans = []
    for combo in itertools.product(*[ep["candidates"][v] for v in vids]):
        used = [r for c in combo for r in c["S"]]
        if len(used) != len(set(used)):
            continue
        pend = [r for r in q if r not in used]
        obj = sum(c["cost_u"] for c in combo) + sum(pend_u[r] + M for r in pend)
        key = tuple(next((v for v, c in zip(vids, combo) if r in c["S"]), "~") for r in sorted(q))
        plans.append((obj, key, combo, pend))
    plans.sort(key=lambda z: (z[0], z[1]))
    best = plans[0]
    milp = ep["solver"]["objective_u"]
    L = [f"## Worked comparison: epoch {clock(ep['tau_s'])}", "",
         f"{len(ep['open'])} requests are open; {len(vids)} vans. Every pair of candidate routes that share no request "
         f"was enumerated directly ({len(plans):,} joint plans). The best enumerated objective is {pts(best[0]):.6f} "
         f"points; the MILP reported {pts(milp):.6f} ({'equal' if best[0] == milp else 'DIFFERENT'}).", "",
         "Open requests (waited so far): " + ", ".join(f"{o['rid']} (party {o['q']}, {_mmss(o['waited_s'])})"
                                                      for o in ep["open"]) + ".", "",
         "Each plan below serves as many requests as possible; then the points decide. Points: waiting = "
         "Σ party × φ(wait); riding = 0.5 × Σ party × ride minutes; driving = 0.1 × km; pending = party × "
         "φ(wait at the next tick) + M per request left pending.", ""]
    L += ["| Plan | Routes | Pending | Waiting | Riding | Driving | Pending price (excl. M) | Total (excl. M) |",
          "|---|---|---|---|---|---|---|---|"]
    for i, (obj, key, combo, pend) in enumerate(plans[:n_show]):
        w = sum(c["parts_u"]["wait"] for c in combo)
        r = sum(c["parts_u"]["ride"] for c in combo)
        k = sum(c["parts_u"]["km"] for c in combo)
        p = sum(pend_u[x] for x in pend)
        routes = "<br>".join(f"{v}: {' '.join(c['seq']) or '(nothing new)'}" for v, c in zip(vids, combo))
        L.append(f"| {i + 1}{' (chosen)' if i == 0 else ''} | {routes} | {', '.join(pend) or '-'} | {pts(w):.2f} | "
                 f"{pts(r):.2f} | {pts(k):.2f} | {pts(p):.2f} | {pts(obj - M * len(pend)):.2f} |")
    L += ["", "Ride points include riders already on board; waiting points include a committed pickup. "
          "Plans with the same number of pending requests are compared on the total. This is optimality over the "
          "candidate set at this epoch only, not over every possible route or the whole evening.", ""]
    return "\n".join(L)


def _plans(ep):
    vids = [v["van"] for v in ep["vans"]]
    q = {o["rid"]: o["q"] for o in ep["open"]}
    t_of = {o["rid"]: o["t_s"] for o in ep["open"]}
    pend_u = {r: q[r] * D.phi_u(max(0, ep["solver"]["next_tick_s"] - t_of[r])) for r in q}
    out = []
    for combo in itertools.product(*[ep["candidates"][v] for v in vids]):
        used = [r for c in combo for r in c["S"]]
        if len(used) != len(set(used)):
            continue
        pend = [r for r in q if r not in used]
        obj = sum(c["cost_u"] for c in combo) + sum(pend_u[r] + ep["solver"]["M_u"] for r in pend)
        key = tuple(next((v for v, c in zip(vids, combo) if r in c["S"]), "~") for r in sorted(q))
        out.append((obj, key, combo, pend, sum(pend_u[r] for r in pend)))
    out.sort(key=lambda z: (z[0], z[1]))
    return vids, out


def small_example(eng, travel):
    """A small epoch (2 vans, 2-3 open requests) whose two best plans assign requests differently: the
    stop-by-stop arithmetic a teammate can redo by hand."""
    for i, ep in enumerate(eng.epochs):
        if len(ep["vans"]) != 2 or not 2 <= len(ep["open"]) <= 3:
            continue
        vids, plans = _plans(ep)
        if len(plans) < 2 or plans[0][1] == plans[1][1] or len(plans[0][3]) != len(plans[1][3]):
            continue
        obs = eng.observations[i]
        break
    else:
        return "## A small worked example\n\nNo suitable epoch.\n"
    req = {x.rid: x for x in obs.open}
    cfg = eng.pol.dispatcher
    L = [f"## A small worked example: epoch {clock(ep['tau_s'])}", "",
         "Open requests: " + ", ".join(f"{x.rid} (party {x.q}, requested {clock(x.t)})" for x in obs.open) + ".",
         "Vans: " + "; ".join(f"{v.vid} free at {clock(v.free_s)} at {v.loc}"
                              + (f", carrying {', '.join(r.rid for r in v.riders)}" if v.riders else "")
                              for v in obs.vans) + ".", "",
         "Wait W = curb arrival − request time; φ(W): 1 point per passenger-minute up to 5 min, then 2.5, 5, 10, 20 "
         "per minute after 5, 10, 15, 20 min. Ride = drop-off arrival − pickup arrival (incl. the 30-s boarding "
         "dwell), 0.5 point per passenger-minute. Driving 0.1 point per km.", ""]
    for rank, (obj, key, combo, pend, pu) in enumerate(plans[:2]):
        L += [f"**Plan {rank + 1}{' (chosen)' if rank == 0 else ''}**" + (f"; pending {', '.join(pend)}" if pend else ""),
              "", "| Van | Stop | Arrives | Wait | φ × party | Ride | 0.5 × party × ride |", "|---|---|---|---|---|---|---|"]
        tot = {"wait": 0, "ride": 0, "km": 0, "psi": 0}
        for v, c in zip(vids, combo):
            van = next(x for x in obs.vans if x.vid == v)
            seq = tuple((s.split(":")[0], s.split(":")[1]) for s in c["seq"])
            ev = D.evaluate(van, seq, {k: req[k] for k in c["S"]}, travel, cfg, None)
            if van.committed and van.committed[1] == "P":
                rid, _, a = van.committed
                r0 = eng.req[rid]
                L.append(f"| {v} | already driving to pick up {rid} | {clock(a)} | {_mmss(a - r0.t)} | "
                         f"{pts(van.committed_wait_u):.2f} | | |")
            for (kind, rid), a in zip(seq, ev["arrivals"]):
                if kind == "P":
                    w = ev["waits"][rid]
                    L.append(f"| {v} | pick up {rid} | {clock(a)} | {_mmss(w)} | {pts(req[rid].q * D.phi_u(w)):.2f} | | |")
                else:
                    h = ev["rides"][rid]
                    qq = req[rid].q if rid in req else next(r.q for r in van.riders if r.rid == rid)
                    L.append(f"| {v} | drop {rid} | {clock(a)} | | | {_mmss(h)} | {pts(cfg.ride_u * qq * h):.2f} |")
            for k in tot:
                tot[k] += ev["parts_u"][k]
        L += ["", f"Waiting {pts(tot['wait']):.2f} + riding {pts(tot['ride']):.2f} + driving {pts(tot['km']):.2f}"
              + (f" + pending price {pts(pu):.2f}" if pend else "")
              + f" = **{pts(tot['wait'] + tot['ride'] + tot['km'] + tot['psi'] + pu):.2f} points**"
              + " (riding includes riders already aboard)", ""]
    d = pts(plans[1][0] - plans[0][0])
    L += [f"Plan 1 is cheaper by {d:.2f} points, so the MILP chooses it (status {ep['solver']['status']}). "
          "The table shows the arithmetic, not a causal claim about the evening.", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", default="L4")
    ap.add_argument("--rule", default="R0")
    ap.add_argument("--K", type=int, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    eng, out = run(a.level, a.rule, a.K, a.out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
