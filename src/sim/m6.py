"""M6 runner: one full normal (base) evening, timed (plan: docs/technical/research_notes/m6_plan_2026-11.md).

    cd src && ../.venv/bin/python -m sim.m6 run --workers 3     # refused until the M6 plan is FROZEN
    ../.venv/bin/python -m sim.m6 report                         # outputs/sim/m6/report.md (compute + demonstration)
    ../.venv/bin/python -m sim.m6 status                         # wall time and check status only

M6 runs the full L6 base_5 nights r00-r04 (168 requests each) with C and G exactly as in M5b (R0, same settings and
code fingerprint). It is a compute measurement and a demonstration, not a test: no interval, no margin.

This module is separate from m5.py on purpose. It imports m5's settings and helpers but changes none of them, so
the M5 configurations, manifests and the code fingerprint stay as they are (m5.py is re-imported by the M5d queue
workers while they run). The one difference from the M5 run checks is the backlog check, which in l5_pilot assumes
a first-hour slice; M6 replaces it with a full-night version here.

Layout: outputs/sim/m6/<cell>/<night>/rep1/ {events.csv, outcomes.csv, epochs.jsonl.gz, manifest.json}.
"""
import argparse
import dataclasses
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

from . import engine as E
from . import inputs
from . import m5
from .l5_pilot import checks
from .run import OUT

M6 = OUT / "m6"
PLAN = inputs.ROOT / "docs" / "technical" / "research_notes" / "m6_plan_2026-11.md"
CODE_FINGERPRINT = "1f318cef8ad4"          # the M5d code (switch off = M5b byte for byte); the runner refuses others
FULL_N = {"base": 168}
NIGHTS = [f"r{i:02d}" for i in range(5)]
DEMO_NIGHT = "r00"                          # fixed in the plan before any M6 run
CELLS = [m5._c("base", 5, "C"), m5._c("base", 5, "G")]
RUNS = [(c, n) for c in CELLS for n in NIGHTS]       # C r00..r04, then G r00..r04
MAX_WORKERS = 3
OLD_BACKLOG = "backlog resolved after arrivals end (last request ≤ 3600 s)"
NEW_BACKLOG = "backlog resolved after arrivals end (all requests of the full night)"
HOURS = [(0, 3600, "18:00"), (3600, 7200, "19:00"), (7200, 10800, "20:00"), (10800, 10 ** 9, "after 21:00")]


def plan_frozen():
    return PLAN.exists() and "**Status: FROZEN" in PLAN.read_text()


def plan_sha():
    return hashlib.sha256(PLAN.read_bytes()).hexdigest()


def config(cell):
    """M5's configuration for the cell, with the slice changed to the full night."""
    d = m5.config(cell)
    d["slice"] = "full night"
    return d


def full_night(cell, night):
    """The frozen night, checked against FROZEN_v2_L6.json, with every request."""
    key = m5.level_key(cell, night)
    scen = inputs.load(key, check_hash=False)
    if json.loads(m5.FROZEN_L6.read_text()).get(key) != scen.content_hash:
        raise RuntimeError(f"{key}: content hash {scen.content_hash[:12]} does not match FROZEN_v2_L6.json")
    if len(scen.requests) != FULL_N[cell.pattern]:
        raise RuntimeError(f"{key}: {len(scen.requests)} requests, expected {FULL_N[cell.pattern]}")
    return scen, key


def full_night_checks(run, scen, travel, p_absent, key):
    """The M5 run checks, with the first-hour backlog check replaced by its full-night version."""
    ck = checks(run, scen, travel, p_absent, key, frozen=json.loads(m5.FROZEN_L6.read_text()))
    ck.pop(OLD_BACKLOG)
    o = run["out"]
    ck[NEW_BACKLOG] = bool(len(o) == len(scen.requests) and
                           run["manifest"]["end_s"] >= o[["drop_s", "cancel_s", "noshow_s"]].max().max())
    return ck


def run_dir(cell, night, rep=1, root=None):
    return (root or M6) / cell.name / night / f"rep{rep}"


def run_one(args, scen_fn=full_night, root=None):
    cell, night, fp = args
    final = run_dir(cell, night, root=root)
    tmp = final.with_name(final.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    scen, key = scen_fn(cell, night)
    m = scen.params["travel_multiplier"]
    travel = inputs.Travel(m, m)
    eng = E.Engine(scen, travel, m5.policy(cell))
    t0 = time.perf_counter()
    try:
        eng.run()
    except Exception:
        fail = final.with_name(final.name + ".FAILED")
        shutil.rmtree(fail, ignore_errors=True)
        tmp.rename(fail)
        (fail / "traceback.txt").write_text(traceback.format_exc())
        pd.DataFrame(eng.events).to_csv(fail / "events_partial.csv", index=False)
        m5._write_epochs(fail / "epochs_partial.jsonl.gz", eng.epochs)
        return {"cell": cell.name, "night": night, "status": "failed", "error": traceback.format_exc().splitlines()[-1]}
    wall = time.perf_counter() - t0
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_mb = peak / 2**20 if sys.platform == "darwin" else peak / 2**10
    pd.DataFrame(eng.events).to_csv(tmp / "events.csv", index=False)
    pd.DataFrame(eng.outcomes()).to_csv(tmp / "outcomes.csv", index=False)
    m5._write_epochs(tmp / "epochs.jsonl.gz", eng.epochs)
    man = {"stage": "m6", "cell": cell.name, "night": night, "rep": 1, "level": key, "requests": len(scen.requests),
           "content_hash": scen.content_hash, "matrix_sha256": travel.matrix_sha256, "code_fingerprint": fp,
           "config": config(cell), "end_s": eng.end_s, "wall_s": round(wall, 2), "peak_rss_mb": round(peak_mb, 1),
           "python": sys.version.split()[0], "highspy": getattr(highspy, "__version__", None),
           "events_sha256": hashlib.sha256((tmp / "events.csv").read_bytes()).hexdigest(),
           "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    if PLAN.exists():
        man["plan_sha256"] = plan_sha()
    run = {"out": pd.read_csv(tmp / "outcomes.csv"), "events": pd.read_csv(tmp / "events.csv"), "epochs": eng.epochs,
           "manifest": man}
    ck = full_night_checks(run, scen, travel, eng.pol.p_absent, key)
    man["checks"] = {k: bool(v) for k, v in ck.items()}
    man["status"] = "ok" if all(ck.values()) else "checks_failed"
    (tmp / "manifest.json").write_text(json.dumps(man, indent=1, default=str))
    shutil.rmtree(final, ignore_errors=True)
    tmp.rename(final)
    return {"cell": cell.name, "night": night, "status": man["status"], "wall_s": man["wall_s"],
            "failed_checks": [k for k, v in ck.items() if not v]}


def done(cell, night, fp, root=None):
    f = run_dir(cell, night, root=root) / "manifest.json"
    if not f.exists():
        return False
    man = json.loads(f.read_text())
    if man["code_fingerprint"] != fp or man["config"] != json.loads(json.dumps(config(cell), default=str)):
        raise SystemExit(f"m6 {cell.name} {night}: existing run has a different code fingerprint or configuration")
    if man.get("plan_sha256") != plan_sha():
        raise SystemExit(f"m6 {cell.name} {night}: run was made under a different M6 plan file; refusing to mix")
    return True


def cmd_run(workers):
    if not plan_frozen():
        raise SystemExit(f"m6: the plan must be frozen in {PLAN.name} (a '**Status: FROZEN <date>**' line) first")
    fp = m5.code_fingerprint()
    if not fp.startswith(CODE_FINGERPRINT):
        raise SystemExit(f"m6: code fingerprint {fp[:12]} is not the M5d code {CODE_FINGERPRINT}; refusing to run")
    workers = min(workers, MAX_WORKERS)
    M6.mkdir(parents=True, exist_ok=True)
    todo = [(c, n, fp) for c, n in RUNS if not done(c, n, fp)]
    print(f"code fingerprint {fp[:12]}; {len(todo)} runs to do; {workers} workers", flush=True)
    log = open(M6 / "run_log.jsonl", "a")
    failed = False
    with Pool(workers, maxtasksperchild=1) as pool:
        it, pending = iter(todo), []
        for _ in range(workers):
            a = next(it, None)
            if a:
                pending.append(pool.apply_async(run_one, (a,)))
        while pending:
            while not any(p.ready() for p in pending):
                time.sleep(1)
            res = pending.pop(next(i for i, p in enumerate(pending) if p.ready())).get()
            res["t"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            log.write(json.dumps(res) + "\n"); log.flush()
            print(res, flush=True)
            failed |= res["status"] == "failed"                # a crash pauses; a failed check is reported
            if not failed:
                a = next(it, None)
                if a:
                    pending.append(pool.apply_async(run_one, (a,)))
    print("PAUSED after a crash: find the cause before resuming" if failed else "m6 complete", flush=True)


# ---------- report ----------
def compute_row(d):
    man = json.loads((d / "manifest.json").read_text())
    eps = m5._epochs(d)
    t = np.array([e["solver"]["wall_s"]["total"] for e in eps])
    tau = np.array([e["tau_s"] for e in eps])
    st = pd.Series([e["solver"]["status"] for e in eps]).value_counts().to_dict()
    row = {"night": man["night"], "status": man["status"], "wall_min": man["wall_s"] / 60,
           "peak_gb": man["peak_rss_mb"] / 1024, "replans": len(eps), "slowest_replan_s": float(t.max()) if len(t) else 0,
           "solver_status": ", ".join(f"{k} {v}" for k, v in sorted(st.items())),
           "failed_checks": "; ".join(k for k, v in man["checks"].items() if not v) or "none"}
    for lo, hi, lab in HOURS:
        row[f"replan_min_{lab}"] = float(t[(tau >= lo) & (tau < hi)].sum()) / 60
    return row


def _fmt(x, nd=1):
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def cmd_report(root=None):
    root = root or M6
    lines = ["# M6 report: full normal evenings (L6 base_5, 168 requests, R0)", "",
             f"Plan: `{PLAN.name}`" + (f", sha256 `{plan_sha()[:12]}…`" if PLAN.exists() else "") +
             ". M6 is a compute measurement and a demonstration, not a test: no interval, no margin.", ""]
    comp = {}
    for cell in CELLS:
        rows = [compute_row(run_dir(cell, n, root=root)) for n in NIGHTS
                if (run_dir(cell, n, root=root) / "manifest.json").exists()]
        comp[cell.algorithm] = rows
        lines += [f"## Compute: {cell.name} ({len(rows)} of {len(NIGHTS)} nights finished)", ""]
        if not rows:
            lines += ["No finished runs.", ""]
            continue
        df = pd.DataFrame(rows)
        lines += ["| Night | Status | Wall, min | Peak, GB | Re-plans | Slowest re-plan, s | Re-plan min by hour "
                  "(18 / 19 / 20 / after) | Solver status | Failed checks |", "|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            hrs = " / ".join(_fmt(r[f"replan_min_{h[2]}"]) for h in HOURS)
            lines.append(f"| {r['night']} | {r['status']} | {_fmt(r['wall_min'])} | {_fmt(r['peak_gb'], 2)} | "
                         f"{r['replans']} | {_fmt(r['slowest_replan_s'])} | {hrs} | {r['solver_status']} | "
                         f"{r['failed_checks']} |")
        lines += ["", f"Median wall time per evening: **{_fmt(df.wall_min.median())} min**; "
                      f"maximum {_fmt(df.wall_min.max())} min; peak memory up to {_fmt(df.peak_gb.max(), 2)} GB.", ""]

    lines += ["## Outcomes (descriptive: 5 nights, no interval, not a test)", "",
              "| Night | Arm | Not reached within 20 min, % | P90 passenger wait, min | P90 van ride, min | "
              "Van-km per ride | Cancellations |", "|---|---|---|---|---|---|---|"]
    for n in NIGHTS:
        for cell in CELLS:
            d = run_dir(cell, n, root=root)
            if not (d / "manifest.json").exists():
                continue
            mm = m5.night_measures(d)
            lines.append(f"| {n}{' (demonstration)' if n == DEMO_NIGHT else ''} | {cell.algorithm} | "
                         f"{_fmt(mm['not_reached_20_pp'])} | {_fmt(mm['wait_pax_p90_min'])} | "
                         f"{_fmt(mm['ride_p90_min'])} | {_fmt(mm['van_km_per_ride'], 2)} | {mm['cancellations']} |")
    lines += ["", "Levels rest on ASSUMED patience, presence and Lyft delay. M5b's first-hour test is the evidence "
                  "for C vs G; these rows only describe five full evenings.", ""]
    root.mkdir(parents=True, exist_ok=True)
    (root / "report.md").write_text("\n".join(lines))
    print("\n".join(lines))


def cmd_status(root=None):
    for cell in CELLS:
        mans = [json.loads((run_dir(cell, n, root=root) / "manifest.json").read_text()) for n in NIGHTS
                if (run_dir(cell, n, root=root) / "manifest.json").exists()]
        w = [x["wall_s"] / 60 for x in mans]
        bad = [x["night"] for x in mans if x["status"] != "ok"]
        print(f"{cell.name:22s} {len(mans)}/{len(NIGHTS)} finished" +
              (f", median {np.median(w):.1f} min, max {max(w):.1f} min" if w else "") +
              (f"; checks failed: {', '.join(bad)}" if bad else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "report", "status"])
    ap.add_argument("--workers", type=int, default=MAX_WORKERS)
    a = ap.parse_args()
    {"run": lambda: cmd_run(a.workers), "report": cmd_report, "status": cmd_status}[a.cmd]()


if __name__ == "__main__":
    main()
