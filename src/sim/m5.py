"""M5 runner: first-hour L6 slice, dispatcher C and greedy G (plan v2, D-60).

    cd src && ../.venv/bin/python -m sim.m5 m5a run          # M5a: C, R0, base_5 r00-r02, two repeats each (resumable)
    ../.venv/bin/python -m sim.m5 m5a compute                 # compute.md: compute measures and the gate (no outcomes)
    ../.venv/bin/python -m sim.m5 m5a kcheck                  # K = 4 coverage on a fixed sample of epochs

M5b (C vs G) refuses to run until docs/technical/research_notes/m5_preregistration_2026-11.md exists: its criteria
are frozen before the first M5b run.

Layout: outputs/sim/m5/<stage>/<cell>/<night>/rep<k>/ {events.csv, outcomes.csv, epochs.jsonl.gz, manifest.json}.
A run is complete only when manifest.json exists; a crash leaves <rep>.FAILED/ with its traceback and partial logs.
Each night runs in a fresh worker process, so the recorded peak memory belongs to that night alone.

Blind rule (M5a): the M5a commands read solver logs, wall times, memory, audits and event logs only. They never
tabulate rider outcomes. outcomes.csv is written for the audit trail and is read only by the pass/fail run checks.

The first-hour slice: the requests with t_request_s < 3600 of a frozen L6 night (64 base, 83 high), which are exactly
its first rows (M4 check 1). Vans keep their frozen availability; the closing rule keeps them on duty until all
accepted work is resolved (D-36, D-46). Run settings: those of the L5 batch (D-56/D-57): lag 120 s, consent 1.0,
presence p = 0.089 (provisional), curb-wait "possible_boarding", pending price A, K = 3, travel multiplier 1.2.
"""
import argparse
import dataclasses
import gzip
import hashlib
import json
import resource
import shutil
import sys
import time
import traceback
from multiprocessing import Pool
from pathlib import Path

import highspy
import numpy as np
import pandas as pd

from . import dispatch as D
from . import engine as E
from . import inputs
from .l5_pilot import checks
from .run import OUT, rule_tag

M5 = OUT / "m5"
SIM = Path(__file__).resolve().parent
FINGERPRINTED = ("inputs.py", "engine.py", "dispatch.py", "lyft.py", "greedy.py", "l5_pilot.py")
FROZEN_L6 = inputs.SCEN / "FROZEN_v2_L6.json"
PREREG = inputs.ROOT / "docs" / "technical" / "research_notes" / "m5_preregistration_2026-11.md"
FIRST_HOUR_S = 3600
SLICE_N = {"base": 64, "high": 83}


@dataclasses.dataclass(frozen=True)
class Cell:
    name: str
    pattern: str        # base | high
    fleet: int          # 5 | 6
    algorithm: str      # C | G
    rule: str = "R0"
    tick_s: int = 120


STAGES = {
    "m5a": {"cells": [Cell("base5_C_R0_t120", "base", 5, "C")], "nights": ["r00", "r01", "r02"], "reps": 2},
    # Compute-only probe of the high-load cell before M5b is scheduled (after M5a; same blind rule: no outcome read)
    "probe_high": {"cells": [Cell("high5_C_R0_t120", "high", 5, "C")], "nights": ["r00", "r01", "r02"], "reps": 1},
}


def code_fingerprint():
    h = hashlib.sha256()
    for f in FINGERPRINTED:
        h.update(f.encode() + (SIM / f).read_bytes())
    return h.hexdigest()


def policy(cell):
    return E.Policy(rule=cell.rule, lag_s=120, consent_p=1.0, p_absent=0.089, curb_wait_planning="possible_boarding",
                    dispatcher=D.Config(tick_s=cell.tick_s), algorithm=cell.algorithm)


def config(cell):
    pol = policy(cell)
    d = dataclasses.asdict(pol)
    d["dispatcher"] = dataclasses.asdict(pol.dispatcher)
    d["rule_active_before_s"] = str(d["rule_active_before_s"])
    d["cell"] = dataclasses.asdict(cell)
    d["slice"] = f"t_request_s < {FIRST_HOUR_S}"
    return d


def level_key(cell, night):
    return f"L6/{cell.pattern}_{cell.fleet}/{night}"


def first_hour(cell, night):
    """The frozen night, checked against FROZEN_v2_L6.json, cut to its first hour."""
    key = level_key(cell, night)
    scen = inputs.load(key, check_hash=False)
    if json.loads(FROZEN_L6.read_text()).get(key) != scen.content_hash:
        raise RuntimeError(f"{key}: content hash {scen.content_hash[:12]} does not match FROZEN_v2_L6.json")
    reqs = [r for r in scen.requests if r.t < FIRST_HOUR_S]
    n = SLICE_N[cell.pattern]
    if len(reqs) != n or reqs != scen.requests[:n]:
        raise RuntimeError(f"{key}: first-hour slice is not the first {n} rows")
    return dataclasses.replace(scen, requests=reqs, hidden={r.rid: scen.hidden[r.rid] for r in reqs}), key


def run_dir(stage, cell, night, rep):
    return M5 / stage / cell.name / night / f"rep{rep}"


def _write_epochs(path, epochs):
    with gzip.open(path, "wt") as f:
        for ep in epochs:
            f.write(json.dumps(ep, default=str) + "\n")


def run_one(args):
    stage, cell, night, rep, fp = args
    final = run_dir(stage, cell, night, rep)
    tmp = final.with_name(final.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    scen, key = first_hour(cell, night)
    m = scen.params["travel_multiplier"]
    travel = inputs.Travel(m, m)
    eng = E.Engine(scen, travel, policy(cell))
    t0 = time.perf_counter()
    try:
        eng.run()
    except Exception:
        fail = final.with_name(final.name + ".FAILED")
        shutil.rmtree(fail, ignore_errors=True)
        tmp.rename(fail)
        (fail / "traceback.txt").write_text(traceback.format_exc())
        pd.DataFrame(eng.events).to_csv(fail / "events_partial.csv", index=False)
        _write_epochs(fail / "epochs_partial.jsonl.gz", eng.epochs)
        return {"cell": cell.name, "night": night, "rep": rep, "status": "failed",
                "error": traceback.format_exc().splitlines()[-1]}
    wall = time.perf_counter() - t0
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss          # bytes on macOS, KiB on Linux
    peak_mb = peak / 2**20 if sys.platform == "darwin" else peak / 2**10
    pd.DataFrame(eng.events).to_csv(tmp / "events.csv", index=False)
    pd.DataFrame(eng.outcomes()).to_csv(tmp / "outcomes.csv", index=False)
    _write_epochs(tmp / "epochs.jsonl.gz", eng.epochs)
    man = {"stage": stage, "cell": cell.name, "night": night, "rep": rep, "level": key, "slice_requests": len(scen.requests),
           "content_hash": scen.content_hash, "matrix_sha256": travel.matrix_sha256, "code_fingerprint": fp,
           "config": config(cell), "end_s": eng.end_s, "wall_s": round(wall, 2), "peak_rss_mb": round(peak_mb, 1),
           "python": sys.version.split()[0], "highspy": highspy.__version__ if hasattr(highspy, "__version__") else None,
           "events_sha256": hashlib.sha256((tmp / "events.csv").read_bytes()).hexdigest()}
    run = {"out": pd.read_csv(tmp / "outcomes.csv"), "events": pd.read_csv(tmp / "events.csv"), "epochs": eng.epochs,
           "manifest": man}
    ck = checks(run, scen, travel, eng.pol.p_absent, key, frozen=json.loads(FROZEN_L6.read_text()))
    man["checks"] = {k: bool(v) for k, v in ck.items()}
    man["status"] = "ok" if all(ck.values()) else "checks_failed"
    (tmp / "manifest.json").write_text(json.dumps(man, indent=1, default=str))
    shutil.rmtree(final, ignore_errors=True)
    tmp.rename(final)
    return {"cell": cell.name, "night": night, "rep": rep, "status": man["status"], "wall_s": man["wall_s"],
            "failed_checks": [k for k, v in ck.items() if not v]}


def done(stage, cell, night, rep, fp):
    f = run_dir(stage, cell, night, rep) / "manifest.json"
    if not f.exists():
        return False
    man = json.loads(f.read_text())
    if man["code_fingerprint"] != fp or man["config"] != json.loads(json.dumps(config(cell), default=str)):
        raise SystemExit(f"{stage} {cell.name} {night} rep{rep}: existing run has a different code fingerprint or "
                         "configuration; refusing to mix versions (move the folder aside to start again)")
    return True                                         # complete, whatever its check status (reported, not re-run)


def cmd_run(stage, workers):
    if stage != "m5a" and not PREREG.exists():
        raise SystemExit(f"{stage}: the M5b criteria must be frozen in {PREREG.name} before the first run (D-60)")
    st, fp = STAGES[stage], code_fingerprint()
    (M5 / stage).mkdir(parents=True, exist_ok=True)
    todo = [(stage, c, n, k, fp) for k in range(1, st["reps"] + 1) for c in st["cells"] for n in st["nights"]
            if not done(stage, c, n, k, fp)]
    print(f"code fingerprint {fp[:12]}; {len(todo)} runs to do", flush=True)
    log = open(M5 / stage / "run_log.jsonl", "a")
    with Pool(workers, maxtasksperchild=1) as pool:             # fresh process per night: clean peak-memory figure
        for res in pool.imap_unordered(run_one, todo):
            res["t"] = time.strftime("%H:%M:%S")
            log.write(json.dumps(res) + "\n"); log.flush()
            print(res, flush=True)


# ---------- M5a: compute report (no outcomes) ----------
def _epochs(d):
    with gzip.open(d / "epochs.jsonl.gz", "rt") as f:
        return [json.loads(x) for x in f]


def _q(a, p):
    return float(np.quantile(a, p)) if len(a) else float("nan")


def cmd_compute():
    st = STAGES["m5a"]
    cell = st["cells"][0]
    cfg = D.Config()
    nights, rows, ep_rows = [], [], []
    for n in st["nights"]:
        reps = {}
        for k in range(1, st["reps"] + 1):
            d = run_dir("m5a", cell, n, k)
            if not (d / "manifest.json").exists():
                raise SystemExit(f"{n} rep{k} is missing or failed: see {d.parent}")
            reps[k] = (json.loads((d / "manifest.json").read_text()), d)
        man, d = reps[1]
        eps = _epochs(d)
        for e in eps:
            s = e["solver"]
            nc = s.get("n_candidates", {})
            ep_rows.append({"night": n, "tau_s": e["tau_s"], "status": s["status"], "n_open": len(e["open"]),
                            "riders": sum(len(v["riders"]) for v in e["vans"]),
                            "cand_per_van_mean": float(np.mean(list(nc.values()))) if nc else 0.0,
                            "cand_per_van_max": max(nc.values()) if nc else 0, "n_columns": s.get("n_columns", 0),
                            "n_rows": s.get("n_rows") or 0, "nodes": s.get("mip_nodes", 0) or 0,
                            "gap_u": s.get("gap_u"), "solve_s": s["wall_s"]["total"],
                            "cand_s": s["wall_s"].get("candidates", 0), "milp_s": s["wall_s"].get("milp", 0),
                            "ties_s": s["wall_s"].get("ties", 0), "tie_status": s.get("tie_status"),
                            "max_new_pickups": max((len(c["S"]) for c in e["chosen"].values()), default=0)})
        same = len({m["events_sha256"] for m, _ in reps.values()}) == 1
        rows.append({"night": n, "epochs": len(eps), "wall_s": [m["wall_s"] for m, _ in reps.values()],
                     "peak_mb": [m["peak_rss_mb"] for m, _ in reps.values()],
                     "checks_ok": all(m["status"] == "ok" for m, _ in reps.values()),
                     "failed_checks": sorted({c for m, _ in reps.values() for c, v in m["checks"].items() if not v}),
                     "audit_ok": all(m["checks"][next(c for c in m["checks"] if c.startswith("plan audit"))]
                                     for m, _ in reps.values()),
                     "events_identical": same, "events_bytes": (d / "events.csv").stat().st_size,
                     "epochs_gz_bytes": (d / "epochs.jsonl.gz").stat().st_size, "fp": man["code_fingerprint"]})
    E_ = pd.DataFrame(ep_rows)
    E_.to_csv(M5 / "m5a" / "compute_epochs.csv", index=False)
    solved = E_[E_.status != "empty"]
    at_limit = solved[(solved.status == "feasible_unproven") | (solved.nodes >= cfg.mip_max_nodes)]
    nz_gap = solved[solved.gap_u.fillna(0).astype(float) > 0]
    walls = [w for r in rows for w in r["wall_s"]]
    med_night = float(np.median([np.median(r["wall_s"]) for r in rows]))
    share_limit = len(at_limit) / max(len(solved), 1)
    gate = {"plan audit passed every epoch, every run": all(r["audit_ok"] for r in rows),
            "repeat runs give identical event logs": all(r["events_identical"] for r in rows),
            "share of epochs at the node limit <= 5%": share_limit <= 0.05}
    stop = not all(gate.values())
    nights_rule = med_night > 15 * 60
    L = ["# M5a: compute benchmark of C (first-hour L6 slice, 5 vans, R0)", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M')}. Plan v2 M5a; D-60. **Compute only: no rider outcome is read or "
         "tabulated here** (blind rule).", "",
         f"Runs: C under R0 on L6/base_5 r00–r02, first hour ({SLICE_N['base']} requests), 5 vans, K = 3, node budget "
         f"{cfg.mip_max_nodes:,}, threads 1; each night run twice, each run in a fresh process. Code fingerprint "
         f"{rows[0]['fp'][:12]}. Machine: this Mac ({sys.platform}), runs in parallel worker processes.", "",
         "## Gate (thresholds approved with D-60)", "", "| Check | Result |", "|---|---|"]
    for k, v in gate.items():
        L.append(f"| {k} | {'pass' if v else '**FAIL: STOP**'} |")
    L.append(f"| median night wall time ≤ 15 min (else the M5b night count is reset from compute alone) | "
             f"{'pass' if not nights_rule else '**over: reset the night count**'} ({med_night / 60:.1f} min) |")
    verdict = ("**STOP and report**" if stop else
               "**Reset the M5b night count from compute alone before M5b**" if nights_rule else
               "**Pass: M5b runs with 30 nights**")
    L += ["", f"Verdict: {verdict}.", "", "## Per night", "",
          "| Night | Epochs | Wall time, s (rep 1 / rep 2) | Peak memory, MB | Event logs identical | Run checks |",
          "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['night']} | {r['epochs']} | {' / '.join(f'{w:,.0f}' for w in r['wall_s'])} | "
                 f"{' / '.join(f'{m:,.0f}' for m in r['peak_mb'])} | {'yes' if r['events_identical'] else '**no**'} | "
                 f"{'all pass' if r['checks_ok'] else 'failed: ' + '; '.join(r['failed_checks'])} |")

    def dist(col, f="{:,.2f}"):
        a = solved[col].to_numpy(dtype=float)
        return " | ".join(f.format(x) for x in (np.median(a), _q(a, .9), _q(a, .99), a.max()))
    L += ["", f"## Per epoch (rep 1 of each night; {len(E_)} epochs, {len(solved)} with something to decide)", "",
          "| Measure | Median | P90 | P99 | Max |", "|---|---|---|---|---|",
          f"| Open requests | {dist('n_open', '{:,.0f}')} |",
          f"| Riders aboard (all vans) | {dist('riders', '{:,.0f}')} |",
          f"| Candidates per van (mean over vans) | {dist('cand_per_van_mean', '{:,.0f}')} |",
          f"| Candidates, largest van | {dist('cand_per_van_max', '{:,.0f}')} |",
          f"| MILP columns | {dist('n_columns', '{:,.0f}')} |", f"| MILP rows | {dist('n_rows', '{:,.0f}')} |",
          f"| B&B nodes | {dist('nodes', '{:,.0f}')} |",
          f"| Solve time per epoch, s (candidates + MILP + tie search) | {dist('solve_s')} |",
          f"| of which candidate generation, s | {dist('cand_s')} |", f"| of which first MILP, s | {dist('milp_s')} |",
          f"| of which tie enumeration, s | {dist('ties_s')} |", "",
          f"- Epochs at the node limit or feasible-unproven: {len(at_limit)} of {len(solved)} ({share_limit:.1%}).",
          f"- Epochs with a non-zero final gap: {len(nz_gap)}.",
          "- Main-solve status: " + ", ".join(f"{k} {v}" for k, v in E_.status.value_counts().items()) + ".",
          "- Tie search: " + ", ".join(f"{k} {v}" for k, v in E_.tie_status.value_counts().items()) + ".",
          f"- Epochs where some van's chosen plan uses the full K = 3 new pickups: "
          f"{int((solved.max_new_pickups >= 3).sum())} of {len(solved)} (where the cap can bind; see the K = 4 check).",
          f"- Night wall time over all {len(walls)} runs: median {np.median(walls):,.0f} s, max {max(walls):,.0f} s. "
          f"Logs per night: events.csv ~{np.mean([r['events_bytes'] for r in rows]) / 1e3:,.0f} kB, "
          f"epochs.jsonl.gz ~{np.mean([r['epochs_gz_bytes'] for r in rows]) / 1e6:,.1f} MB.", "",
          "Per-epoch values: `compute_epochs.csv`."]
    kc = M5 / "m5a" / "kcheck.json"
    if kc.exists():
        L += ["", "## K = 4 coverage (sample of epochs)", ""] + _kcheck_lines(json.loads(kc.read_text()))
    (M5 / "m5a" / "compute.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


# ---------- M5a: K = 4 coverage on a fixed sample ----------
def kcheck_sample(eps, n=8):
    """Fixed, outcome-blind sample: epochs whose chosen plan uses the full K = 3 on some van (the only epochs where a
    4-pickup route could be chosen), evenly spaced by position; if there are fewer, all of them."""
    idx = [i for i, e in enumerate(eps) if e["solver"]["status"] != "empty"
           and max((len(c["S"]) for c in e["chosen"].values()), default=0) >= 3]
    if len(idx) <= n:
        return idx
    return [idx[round(j * (len(idx) - 1) / (n - 1))] for j in range(n)]


def _k_solve(args):
    obs, K, m = args
    travel = inputs.Travel(m, m)
    t0 = time.perf_counter()
    plan, _ = D.solve(obs, travel, D.Config(K=K))
    pend = len(plan.pending)
    return {"K": K, "status": plan.log["status"], "pending": pend,
            "objective_less_M_u": plan.log["objective_u"] - pend * plan.log["M_u"] if plan.log["objective_u"] is not None else None,
            "routes": {v: [f"{k}:{x}" for k, x in r.seq] for v, r in plan.routes.items()},
            "max_new_pickups": max((len(r.S) for r in plan.routes.values()), default=0),
            "wall_s": round(time.perf_counter() - t0, 2)}


def cmd_kcheck(workers, n):
    """Re-run night r00 (rep 1 settings) to recover its observations, then solve the sampled epochs with K = 3 and
    K = 4 from the same observation. Reports whether K = 4 would plan differently (more requests served, or a cheaper
    plan); it reads no rider outcome."""
    cell = STAGES["m5a"]["cells"][0]
    scen, key = first_hour(cell, "r00")
    m = scen.params["travel_multiplier"]
    eng = E.Engine(scen, inputs.Travel(m, m), policy(cell)).run()
    saved = (run_dir("m5a", cell, "r00", 1) / "events.csv").read_text()
    assert pd.DataFrame(eng.events).to_csv(index=False) == saved, "re-run differs from the saved r00 run"
    sample = kcheck_sample(eng.epochs, n)
    jobs = [(eng.observations[i], K, m) for i in sample for K in (3, 4)]
    with Pool(workers, maxtasksperchild=1) as pool:
        res = pool.map(_k_solve, jobs)
    out = []
    for j, i in enumerate(sample):
        k3, k4 = res[2 * j], res[2 * j + 1]
        out.append({"epoch_index": i, "tau_s": eng.epochs[i]["tau_s"], "n_open": len(eng.observations[i].open),
                    "k3": k3, "k4": k4, "same_plan": k3["routes"] == k4["routes"]})
        print(out[-1]["tau_s"], out[-1]["n_open"], k3["wall_s"], k4["wall_s"], out[-1]["same_plan"], flush=True)
    (M5 / "m5a" / "kcheck.json").write_text(json.dumps({"night": "r00", "sample": out}, indent=1))


def _kcheck_lines(kc):
    s = kc["sample"]
    L = [f"Night {kc['night']}, {len(s)} epochs where a van's chosen plan used the full K = 3 (fixed rule, evenly spaced). "
         "Each epoch is solved from the same observation with K = 3 and K = 4. Planning measures only.", "",
         "| Epoch time | Open | Same plan | Pending K3 / K4 | Cost less pending (K4 − K3), points | Uses 4 new pickups | Solve s K3 / K4 |",
         "|---|---|---|---|---|---|---|"]
    for x in s:
        a, b = x["k3"], x["k4"]
        dc = (b["objective_less_M_u"] - a["objective_less_M_u"]) / D.PT if None not in (a["objective_less_M_u"], b["objective_less_M_u"]) else float("nan")
        L.append(f"| {x['tau_s']} s | {x['n_open']} | {'yes' if x['same_plan'] else 'no'} | {a['pending']} / {b['pending']} | "
                 f"{dc:+.1f} | {'yes' if b['max_new_pickups'] >= 4 else 'no'} | {a['wall_s']:,.1f} / {b['wall_s']:,.1f} |")
    diff = sum(not x["same_plan"] for x in s)
    L += ["", f"K = 4 plans differently in {diff} of {len(s)} sampled epochs."]
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=list(STAGES))
    ap.add_argument("cmd", choices=["run", "compute", "kcheck"])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--sample", type=int, default=8)
    a = ap.parse_args()
    if a.cmd == "run":
        cmd_run(a.stage, a.workers)
    elif a.cmd == "compute":
        cmd_compute()
    else:
        cmd_kcheck(a.workers, a.sample)


if __name__ == "__main__":
    main()
