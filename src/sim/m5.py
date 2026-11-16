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


def _c(pattern, fleet, alg, rule="R0", tick=120):
    return Cell(f"{pattern}{fleet}_{alg}_{rule_tag(rule)}_t{tick}", pattern, fleet, alg, rule, tick)


NIGHTS30 = [f"r{i:02d}" for i in range(30)]
# M5b comparisons (preregistration §2): (label, C-side run cell, G-side run cell). Cell 4 reuses cell 1's G.
COMPARISONS = [
    ("1 base, 5 vans, R0 (primary)", _c("base", 5, "C"), _c("base", 5, "G")),
    ("2 base, 6 vans, R0", _c("base", 6, "C"), _c("base", 6, "G")),
    ("5 base, 5 vans, R1(10)", _c("base", 5, "C", "R1(10)"), _c("base", 5, "G", "R1(10)")),
    ("4a base, 5 vans, R0, C re-plan 60 s", _c("base", 5, "C", tick=60), _c("base", 5, "G")),
    ("4b base, 5 vans, R0, C re-plan 300 s", _c("base", 5, "C", tick=300), _c("base", 5, "G")),
    ("3 high load, 5 vans, R0", _c("high", 5, "C"), _c("high", 5, "G")),
]


def _ordered(comps):
    """Run order (D-61): comparison by comparison; within one, night by night with both arms together; a run
    already listed (cell 1's G, reused by cell 4) is not repeated."""
    seen, out = set(), []
    for _, c, g in comps:
        for n in NIGHTS30:
            for cell in (c, g):
                if (cell, n) not in seen:
                    seen.add((cell, n))
                    out.append((cell, n))
    return out


STAGES = {
    "m5a": {"runs": [(Cell("base5_C_R0_t120", "base", 5, "C"), n) for n in ("r00", "r01", "r02")], "reps": 2},
    # Compute-only probe of the high-load cell before M5b is scheduled (after M5a; same blind rule: no outcome read)
    "probe_high": {"runs": [(Cell("high5_C_R0_t120", "high", 5, "C"), n) for n in ("r00", "r01", "r02")], "reps": 1},
    # M5b (D-60, D-61): group A = cells 1, 2, 5, 4; group B = cell 3 (at most 2 workers: up to 5 GB per night)
    "m5b_A": {"runs": _ordered(COMPARISONS[:5]), "reps": 1, "folder": "m5b"},
    "m5b_B": {"runs": _ordered(COMPARISONS[5:]), "reps": 1, "folder": "m5b", "max_workers": 2},
}
M5B_CUTOFFS = {"preview": "2026-11-19T12:00:00-05:00", "final": "2026-11-28T12:00:00-05:00"}


def folder(stage):
    return STAGES.get(stage, {}).get("folder", stage)


def prereg_frozen():
    return PREREG.exists() and "**Status: FROZEN" in PREREG.read_text()


def prereg_sha():
    return hashlib.sha256(PREREG.read_bytes()).hexdigest()


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
    return M5 / folder(stage) / cell.name / night / f"rep{rep}"


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
           "events_sha256": hashlib.sha256((tmp / "events.csv").read_bytes()).hexdigest(),
           "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    if folder(stage) == "m5b":
        man["prereg_sha256"] = prereg_sha()
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
    if folder(stage) == "m5b" and man.get("prereg_sha256") != prereg_sha():
        raise SystemExit(f"{cell.name} {night}: run was made under a different preregistration file; refusing to mix")
    return True                                         # complete, whatever its check status (reported, not re-run)


def cmd_run(stage, workers):
    if folder(stage) == "m5b" and not prereg_frozen():
        raise SystemExit(f"{stage}: the M5b criteria must be frozen in {PREREG.name} (a '**Status: FROZEN <date>**' "
                         "line) before the first run (D-60)")
    st, fp = STAGES[stage], code_fingerprint()
    workers = min(workers, st.get("max_workers", workers))
    (M5 / folder(stage)).mkdir(parents=True, exist_ok=True)
    todo = [(stage, c, n, k, fp) for k in range(1, st["reps"] + 1) for c, n in st["runs"] if not done(stage, c, n, k, fp)]
    print(f"code fingerprint {fp[:12]}; {len(todo)} runs to do; {workers} workers", flush=True)
    log = open(M5 / folder(stage) / "run_log.jsonl", "a")
    failed = False
    with Pool(workers, maxtasksperchild=1) as pool:             # fresh process per night: clean peak-memory figure
        it, pending = iter(todo), []
        for _ in range(workers):                                # launched strictly in the listed order (D-61)
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
            if res["status"] != "ok":
                failed = True                                   # pause: no new launches; in-flight runs finish
            if not failed:
                a = next(it, None)
                if a:
                    pending.append(pool.apply_async(run_one, (a,)))
    print("PAUSED after a failure: find the cause before resuming" if failed else f"{stage} complete", flush=True)


# ---------- M5a: compute report (no outcomes) ----------
def _epochs(d):
    with gzip.open(d / "epochs.jsonl.gz", "rt") as f:
        return [json.loads(x) for x in f]


def _q(a, p):
    return float(np.quantile(a, p)) if len(a) else float("nan")


def cmd_compute():
    st = STAGES["m5a"]
    cell = st["runs"][0][0]
    cfg = D.Config()
    nights, rows, ep_rows = [], [], []
    for n in [n for _, n in st["runs"]]:
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
    cell = STAGES["m5a"]["runs"][0][0]
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


# ---------- M5b: preregistered analysis (preregistration §3-§4) ----------
BOOT_N, BOOT_SEED, MARGIN_PP = 10_000, 20261110, 2.0
SECONDARY = [("wait_pax_p90_min", "P90 passenger wait, min"), ("ride_p90_min", "P90 van ride time, min"),
             ("van_km_per_ride", "Van-km per van-completed ride"), ("cancellations", "Cancellations per night")]


def night_measures(d):
    """Per-night measures of one finished run (batch.metrics definitions, over all requests in the slice)."""
    from .batch import metrics
    out, ev = pd.read_csv(d / "outcomes.csv"), pd.read_csv(d / "events.csv")
    m = inputs.Travel(1.2, 1.2)
    met = metrics(out, ev, _epochs(d), m)
    vc = out[out.outcome == "van_completed"]
    return {"not_reached_20_pp": 100 * (1 - met["reached_20_share"]), "wait_pax_p90_min": met["wait_pax_p90_min"],
            "ride_p90_min": _q((vc.ride_s / 60).to_numpy(), .9),
            "van_km_per_ride": met["van_km"] / met["van_completed"] if met["van_completed"] else float("nan"),
            "cancellations": met["cancel_pending_van"] + met["cancel_after_transfer"],
            "lyft_per_100": 100 * (met["bookings_standard"] + met["bookings_xl"]) / met["n_requests"]}


def usable_prefix(cells, cutoff, root=None):
    """Longest unbroken run r00..rk where every run of the comparison finished by the cutoff with status ok."""
    cut = pd.Timestamp(cutoff)
    nights = []
    for n in NIGHTS30:
        ok = True
        for cell in cells:
            f = (root or M5 / "m5b") / cell.name / n / "rep1" / "manifest.json"
            if not f.exists():
                ok = False; break
            man = json.loads(f.read_text())
            if man["status"] != "ok" or pd.Timestamp(man["finished_at"]) > cut:
                ok = False; break
        if not ok:
            break
        nights.append(n)
    return nights


def paired_bootstrap(d, n=BOOT_N, seed=BOOT_SEED):
    """Mean of paired per-night differences and its 95% percentile bootstrap interval (resampling nights)."""
    d = np.asarray(d, dtype=float)
    d = d[~np.isnan(d)]
    if len(d) == 0:
        return float("nan"), float("nan"), float("nan"), 0
    rng = np.random.default_rng(seed)
    means = d[rng.integers(0, len(d), size=(n, len(d)))].mean(axis=1)
    return float(d.mean()), float(np.quantile(means, .025)), float(np.quantile(means, .975)), len(d)


def verdict(lo, hi, margin=MARGIN_PP):
    """Preregistration §4 (D-50 margin). "C better" and "equivalent" can both hold (interval below 0 and inside
    ±2 pp); the reading then says both. "G better" (interval wholly above 0) is reported as found."""
    better = hi < 0
    equiv = lo >= -margin and hi <= margin
    if better and equiv:
        return "C better (and within ±2 pp)"
    if better:
        return "C better"
    if equiv:
        return "practically equivalent"
    if lo > 0:
        return "G better"
    return "inconclusive at this scale"


def cmd_compare(which):
    cutoff = M5B_CUTOFFS[which]
    root = M5 / "m5b"
    L = [f"# M5b comparison: C vs G, first-hour L6 slice ({which} analysis)", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')}. Cutoff {cutoff}. Preregistration "
         f"`{PREREG.name}` (sha256 {prereg_sha()[:12]}). Paired per-night differences C − G; 95% percentile bootstrap, "
         f"{BOOT_N:,} resamples of nights, seed {BOOT_SEED}. Nights used per cell: the unbroken run r00…rk with both "
         "arms finished by the cutoff and passing checks (D-61).", "",
         "| Cell | Nights | Not reached within 20 min, C − G (pp) | 95% CI | Reading |", "|---|---|---|---|---|"]
    sec, per = [], []
    for label, c, g in COMPARISONS:
        nights = usable_prefix((c, g), cutoff, root)
        mc = [night_measures(root / c.name / n / "rep1") for n in nights]
        mg = [night_measures(root / g.name / n / "rep1") for n in nights]
        for n, a, b in zip(nights, mc, mg):
            per.append({"cell": label, "night": n, **{f"C_{k}": v for k, v in a.items()}, **{f"G_{k}": v for k, v in b.items()}})
        d = [a["not_reached_20_pp"] - b["not_reached_20_pp"] for a, b in zip(mc, mg)]
        mean, lo, hi, k = paired_bootstrap(d)
        if k >= 5:
            reading = verdict(lo, hi) if label.startswith("1 ") else "descriptive (secondary cell)"
            ci = f"[{lo:+.2f}, {hi:+.2f}]"
        else:
            reading, ci = "fewer than 5 nights: point estimate only", "—"
        L.append(f"| {label} | {len(nights)} | {mean:+.2f} | {ci} | {reading} |")
        for key, name in SECONDARY + ([("lyft_per_100", "Lyft bookings per 100 requests")] if "R1(10)" in label else []):
            mm, l2, h2, k2 = paired_bootstrap([a[key] - b[key] for a, b in zip(mc, mg)])
            sec.append(f"| {label} | {name} | {k2} | {mm:+.2f} | " + (f"[{l2:+.2f}, {h2:+.2f}]" if k2 >= 5 else "—") + " |")
    L += ["", "Primary decision applies to cell 1 only: C better if the upper bound < 0; practically equivalent if the "
          "interval lies within ±2 pp; G better if the lower bound > 0; otherwise inconclusive at this scale.", "",
          "## Secondary measures (exploratory; mean per-night C − G, 95% bootstrap CI)", "",
          "| Cell | Measure | Nights | C − G | 95% CI |", "|---|---|---|---|---|"] + sec
    pd.DataFrame(per).to_csv(root / f"comparison_{which}_per_night.csv", index=False)
    (root / f"comparison_{which}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=list(STAGES) + ["m5b"])
    ap.add_argument("cmd", choices=["run", "compute", "kcheck", "compare"])
    ap.add_argument("--analysis", choices=list(M5B_CUTOFFS), default="preview")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--sample", type=int, default=8)
    a = ap.parse_args()
    if a.cmd == "run":
        cmd_run(a.stage, a.workers)
    elif a.cmd == "compute":
        cmd_compute()
    elif a.cmd == "compare":
        cmd_compare(a.analysis)
    else:
        cmd_kcheck(a.workers, a.sample)


if __name__ == "__main__":
    main()
