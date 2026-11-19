"""Exploratory diagnostic (not preregistered): where the fixed drop order costs, along C's own M5b trajectories.

Plan: docs/technical/research_notes/m5c_diagnostic_plan_2026-11-18.md. Not in the code fingerprint; reads saved runs only.

For every saved epoch of C (M5b, high5/base5, R0, t120): rebuild the observation from the logged van states and the
night's public request list (hidden traits are never read), check it reproduces C's logged costs, then measure:
  van-epoch: binding (C reorders existing riders' drops), same-S cost gap of the fixed-order route (points)
  epoch:     full C-F solve on the same state, priced with C's pending prices (extra pending, cost gap, solve time)

    python -m sim.diag_cf run [--pattern high|base|both] [--workers 6] [--nights r00,r01]
    python -m sim.diag_cf summary
"""
import argparse
import dataclasses
import gzip
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd

from . import dispatch as D
from . import inputs, m5

OUT = m5.M5 / "diag_cf"
PT = D.PT
LIGHT_EPOCH_S = 1.0          # full C re-solve (rebuild check) only on epochs C solved in under this time


def _bucket(n):
    return "0-1" if n <= 1 else ("7+" if n >= 7 else str(n))


def rebuild(rec, req, travel, cap):
    """Observation from one epoch record. Returns (obs, problems). committed_wait_u is not logged: it is chosen
    among the values the engine can produce (0, or q*phi(pickup - t) of the committed rider) by matching the
    logged committed-only route cost; no match is a rebuild failure."""
    cfg = D.Config()
    vans, problems = [], []
    for v in rec["vans"]:
        riders = tuple(D.Rider(x["rid"], req[x["rid"]].d, req[x["rid"]].q, req[x["rid"]].t, x["pickup_s"],
                               travel.van(req[x["rid"]].o, req[x["rid"]].d)) for x in v["riders"])
        committed = tuple(v["committed"])
        options = [0]
        if committed and committed[0] in {r.rid for r in riders}:
            r = next(x for x in riders if x.rid == committed[0])
            options.append(r.q * D.phi_u(r.pickup_s - r.t))
        logged = next(c["cost_u"] for c in rec["candidates"][v["van"]] if not c["S"])
        match = None
        for cw in options:
            vs = D.VanState(v["van"], cap, v["loc"], v["free_s"], riders, committed, cw)
            if D.best_routes(vs, (), travel, cfg, 0, None)[frozenset()][0] == logged:
                match = vs
                break
        if match is None:
            problems.append(f"{v['van']}: committed-only cost not reproduced")
            match = D.VanState(v["van"], cap, v["loc"], v["free_s"], riders, committed, 0)
        vans.append(match)
    open_ = tuple(D.OpenRequest(x["rid"], req[x["rid"]].t, req[x["rid"]].o, req[x["rid"]].d, req[x["rid"]].q)
                  for x in rec["open"])
    return D.Observation(rec["tau_s"], tuple(vans), open_), problems


def _drop_order(seq, existing):
    return [s.split(":")[1] for s in seq if s.startswith("D:") and s.split(":")[1] in existing]


def night(args):
    pattern, nt = args
    cell = m5._c(pattern, 5, "C")
    scen, _ = m5.first_hour(cell, nt)
    req = {r.rid: r for r in scen.requests}              # public fields only (rid, t, o, d, q)
    mult = scen.params["travel_multiplier"]
    travel = inputs.Travel(mult, mult)
    cfg_c, cfg_f = D.Config(), D.Config(fix_existing_drop_order=True)
    path = m5.M5 / "m5b" / cell.name / nt / "rep1" / "epochs.jsonl.gz"
    van_rows, ep_rows = [], []
    with gzip.open(path, "rt") as fh:
        for k, line in enumerate(fh):
            rec = json.loads(line)
            if not rec["open"] and not any(v["riders"] for v in rec["vans"]):
                continue
            travel.__dict__.pop("_candidate_cache", None)          # bounded memory; no reuse across epochs
            obs, problems = rebuild(rec, req, travel, 14)
            allowed_all = {}
            sl = rec["solver"]
            # ---- van level
            for v in obs.vans:
                ch = rec["chosen"][v.vid]
                S = frozenset(ch["S"])
                exempt = D.best_routes(v, (), travel, cfg_c, 0, None)[frozenset()]
                ev = D.evaluate(v, exempt[1], {}, travel, cfg_c, None)
                allowed = {r.rid: max(D.guardrail_s(r.direct_van_s, cfg_c), ev["rides"][r.rid]) for r in v.riders}
                allowed_all[v.vid] = allowed
                existing = {r.rid for r in v.riders}
                ex_order = [rid for kind, rid in exempt[1] if kind == "D" and rid in existing]
                row = {"pattern": pattern, "night": nt, "epoch": k, "tau_s": rec["tau_s"], "van": v.vid,
                       "aboard": len(v.riders), "bucket": _bucket(len(v.riders)), "S_size": len(S),
                       "binds": _drop_order(ch["seq"], existing) != [r for r in ex_order],
                       "gap_pts": 0.0, "fixed_infeasible": False, "rebuild_ok": True}
                if S:
                    sub = tuple(x for x in obs.open if x.rid in S)
                    c_free = D.best_routes(v, sub, travel, cfg_c, len(S), allowed).get(S)
                    if c_free is None or c_free[0] != ch["cost_u"]:
                        row["rebuild_ok"] = False
                        problems.append(f"{v.vid}: chosen route cost not reproduced")
                    base_order = [rid for kind, rid in exempt[1]]
                    c_fix = D.best_routes(v, sub, travel, cfg_c, len(S), allowed, base_order).get(S)
                    if c_fix is None:
                        row["fixed_infeasible"] = True
                        row["gap_pts"] = None
                    else:
                        row["gap_pts"] = (c_fix[0] - ch["cost_u"]) / PT
                        if row["gap_pts"] > 0:
                            rq = {x.rid: x for x in sub}
                            pf = D.evaluate(v, c_fix[1], rq, travel, cfg_c, allowed)["parts_u"]
                            for part in ("wait", "ride", "km", "psi"):
                                row[f"gap_{part}_pts"] = (pf[part] - ch["parts_u"][part]) / PT
                    # the same decision often recurs over consecutive re-plans until the van acts on it
                    row["decision"] = f"{v.vid}|{','.join(sorted(S))}|{'>'.join(ch['seq'])}"
                van_rows.append(row)
            # ---- epoch level: full C-F solve on the same state, priced with C's pending prices
            t0 = time.perf_counter()
            plan_f, _ = D.solve(obs, travel, cfg_f)
            t_f = time.perf_counter() - t0
            b_c = sl["pending_base_u"]
            obj_f_on_c = sum(r.cost_u for r in plan_f.routes.values()) + sum(b_c[r] + sl["M_u"] for r in plan_f.pending)
            n_pend_c = len(rec["pending"])
            obj_c_check = None
            if sl["wall_s"]["total"] < LIGHT_EPOCH_S:
                plan_c, _ = D.solve(obs, travel, cfg_c)
                obj_c_check = plan_c.log["objective_u"] == sl["objective_u"]
                if not obj_c_check:
                    problems.append("full C re-solve objective differs")
            gap_u = obj_f_on_c - sl["objective_u"] - (len(plan_f.pending) - n_pend_c) * sl["M_u"]
            ep_rows.append({"pattern": pattern, "night": nt, "epoch": k, "tau_s": rec["tau_s"],
                            "max_aboard": max((len(v.riders) for v in obs.vans), default=0),
                            "bucket": _bucket(max((len(v.riders) for v in obs.vans), default=0)),
                            "n_open": len(obs.open), "c_wall_s": sl["wall_s"]["total"],
                            "c_cand_s": sl["wall_s"]["candidates"], "cf_wall_s": round(t_f, 4),
                            "c_status": sl["status"], "cf_status": plan_f.log["status"],
                            "extra_pending": len(plan_f.pending) - n_pend_c,
                            "plan_gap_pts": gap_u / PT, "c_resolve_match": obj_c_check,
                            "problems": "; ".join(problems)})
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(van_rows).to_csv(OUT / f"van_{pattern}_{nt}.csv", index=False)
    pd.DataFrame(ep_rows).to_csv(OUT / f"epoch_{pattern}_{nt}.csv", index=False)
    return pattern, nt, len(ep_rows), sum(bool(r["problems"]) for r in ep_rows)


def cmd_run(a):
    pats = ["high", "base"] if a.pattern == "both" else [a.pattern]
    nights = a.nights.split(",") if a.nights else m5.NIGHTS30
    jobs = [(p, n) for p in pats for n in nights]
    with ProcessPoolExecutor(a.workers) as ex:
        for f in as_completed([ex.submit(night, j) for j in jobs]):
            p, n, ne, bad = f.result()
            print(f"{p} {n}: {ne} epochs, {bad} with rebuild problems", flush=True)


def _md(df):
    """Markdown table without the tabulate dependency."""
    cols = [df.index.name or ""] + list(df.columns)
    rows = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for i, r in df.iterrows():
        rows.append("| " + " | ".join([str(i)] + ["" if pd.isna(x) else f"{x:g}" for x in r]) + " |")
    return "\n".join(rows)


def summary():
    van = pd.concat(pd.read_csv(f) for f in sorted(OUT.glob("van_*.csv")))
    ep = pd.concat(pd.read_csv(f) for f in sorted(OUT.glob("epoch_*.csv")))
    order = ["0-1", "2", "3", "4", "5", "6", "7+"]
    lines = []
    for p in ("high", "base"):
        v, e = van[van.pattern == p], ep[ep.pattern == p]
        if v.empty:
            continue
        lines.append(f"\n## {p}: {e.night.nunique()} nights, {len(e)} epochs, {len(v)} van-epochs")
        lines.append(f"rebuild problems: {int((e.problems.fillna('') != '').sum())} epochs; "
                     f"C re-solve checks: {int(e.c_resolve_match.eq(True).sum())} match, "
                     f"{int(e.c_resolve_match.eq(False).sum())} differ")
        g = v.groupby("bucket")
        tv = pd.DataFrame({"van-epochs": g.size(), "binds %": 100 * g.binds.mean(),
                           "gap pts total": g.gap_pts.sum(), "fixed infeasible": g.fixed_infeasible.sum()}).reindex(order)
        pos = v[v.gap_pts > 1e-9]
        first = pos.drop_duplicates(["night", "decision"])          # each distinct decision counted once
        gp = pos.groupby("bucket")
        tv["median gap pts (when > 0)"] = gp.gap_pts.median().reindex(order)
        tv["distinct decisions with gap"] = first.groupby("bucket").size().reindex(order)
        tv["gap pts, distinct decisions"] = first.groupby("bucket").gap_pts.sum().reindex(order)
        for part in ("wait", "ride", "km", "psi"):
            if f"gap_{part}_pts" in pos:
                tv[f"of which {part} %"] = 100 * gp[f"gap_{part}_pts"].sum().reindex(order) / tv["gap pts total"]
        tv["share of van-epochs %"] = 100 * tv["van-epochs"] / tv["van-epochs"].sum()
        tv["share of gap (distinct) %"] = 100 * tv["gap pts, distinct decisions"] / tv["gap pts, distinct decisions"].sum()
        tv["share of gap %"] = 100 * tv["gap pts total"] / tv["gap pts total"].sum()
        lines.append("\nVan level, by parties aboard or committed to that van\n")
        lines.append(_md(tv.round(1)))
        ge = e.groupby("bucket")
        te = pd.DataFrame({"epochs": ge.size(), "C time h": ge.c_wall_s.sum() / 3600,
                           "C-F time h": ge.cf_wall_s.sum() / 3600, "extra pending": ge.extra_pending.sum(),
                           "plan gap pts total": ge.plan_gap_pts.sum(),
                           "epochs with any gap %": 100 * ge.plan_gap_pts.apply(lambda s: (s > 1e-9).mean())}).reindex(order)
        te["share of C time %"] = 100 * te["C time h"] / te["C time h"].sum()
        te["share of plan gap %"] = 100 * te["plan gap pts total"] / te["plan gap pts total"].sum()
        lines.append("\nEpoch level, by the largest party count aboard any van\n")
        lines.append(_md(te.round(2)))
    txt = "# C-F diagnostic summary (exploratory)\n" + "\n".join(lines) + "\n"
    (OUT / "summary.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("--pattern", default="both", choices=["high", "base", "both"])
    r.add_argument("--workers", type=int, default=6)
    r.add_argument("--nights", default="")
    sp.add_parser("summary")
    a = ap.parse_args()
    cmd_run(a) if a.cmd == "run" else summary()
