"""Resumable paired-night batch: L5 r00-r29 x six Lyft rules (D-57). Pipeline verification and variability only.

    cd src && ../.venv/bin/python -m sim.batch run          # resumable; pauses new launches on the first failure
    ../.venv/bin/python -m sim.batch summary                 # per-night metrics table + summary.md
    ../.venv/bin/python -m sim.batch reproduce               # re-run a documented sample in memory, compare bytes

Layout: outputs/sim/batch_L5_v1/<rNN>/<rule-tag>/ {events.csv, epochs.jsonl, outcomes.csv, metrics.json, manifest.json}.
A run is complete only when manifest.json says status "ok"; a failed run leaves FAILED/ with its traceback, the
partial logs and the observation it failed on. Every manifest carries the code fingerprint (sha256 of the simulator
modules) and the configuration; a resume refuses to mix runs with a different fingerprint or configuration.
"""
import argparse
import dataclasses
import hashlib
import json
import math
import shutil
import sys
import time
import traceback
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from . import dispatch as D
from . import engine as E
from . import inputs, lyft
from .l5_pilot import checks, guardrail_excesses
from .run import OUT, policy_for, rule_tag

BATCH = OUT / "batch_L5_v1"
NIGHTS = [f"r{i:02d}" for i in range(30)]
RULES = list(lyft.RULES)
CORE = ("inputs.py", "engine.py", "dispatch.py", "lyft.py", "run.py")
SIM = Path(__file__).resolve().parent


def code_fingerprint():
    h = hashlib.sha256()
    for f in CORE:
        h.update(f.encode() + (SIM / f).read_bytes())
    return h.hexdigest()


def config(rule):
    """Everything that defines a run except the night; identical across arms apart from the rule (D-56/D-57)."""
    scen = inputs.load("L5/r00")
    pol = policy_for(scen, rule)
    d = dataclasses.asdict(pol)
    d["dispatcher"] = dataclasses.asdict(pol.dispatcher)
    d["rule_active_before_s"] = str(d["rule_active_before_s"])
    return d


def run_dir(night, rule):
    return BATCH / night / rule_tag(rule)


def _obs_json(obs):
    return json.loads(json.dumps(dataclasses.asdict(obs), default=str)) if obs else None


def metrics(out, events, epochs, travel):
    """Per-night descriptive measures. "Reached" = a vehicle's curb arrival within 15 or 20 min of the request (not
    boarding), over all requests; 20 min is the D-50 primary, 15 min the sensitivity. Waits are request -> pickup
    among picked-up requests; NaN when none."""
    n, pax = len(out), int(out.party.sum())
    picked = out[out.pickup_s.notna()]
    w = (picked.wait_s / 60).to_numpy()
    wp = np.repeat(w, picked.party.to_numpy())
    reached = ((out.curb_arrival_s - out.t_request_s) <= 900).fillna(False)
    reached_20 = ((out.curb_arrival_s - out.t_request_s) <= 1200).fillna(False)
    dep = events[events.event == "depart"]
    st = pd.Series([e["solver"]["status"] for e in epochs]).value_counts().to_dict()
    ts = pd.Series([e["solver"]["tie_status"] for e in epochs]).value_counts().to_dict()

    def q(a, p):
        return float(np.quantile(a, p)) if len(a) else math.nan

    def cls(df, c):
        return int((df.lyft_class == c).sum())
    lyft_booked = out[out.booking_s.notna()]
    return {
        "n_requests": n, "n_passengers": pax,
        "reached_15_share": float(reached.mean()), "reached_15_n": int(reached.sum()),
        "reached_20_share": float(reached_20.mean()), "reached_20_n": int(reached_20.sum()),
        "picked_up_requests": int(len(picked)), "picked_up_passengers": int(len(wp)),
        "wait_median_min": q(w, .5), "wait_p90_min": q(w, .9), "wait_max_min": float(w.max()) if len(w) else math.nan,
        "wait_pax_median_min": q(wp, .5), "wait_pax_p90_min": q(wp, .9),
        "van_completed": int((out.outcome == "van_completed").sum()),
        "lyft_completed": int((out.outcome == "lyft_completed").sum()),
        "cancel_pending_van": int((out.outcome == "cancel_pending_van").sum()),
        "cancel_after_transfer": int((out.outcome == "cancel_after_transfer").sum()),
        "noshow_van": int((out.outcome == "noshow_van").sum()), "noshow_lyft": int((out.outcome == "noshow_lyft").sum()),
        "offers": int(out.transfer_s.notna().sum() + out.declined_s.notna().sum()),
        "transfers_standard": cls(out[out.transfer_s.notna()], "standard"),
        "transfers_xl": cls(out[out.transfer_s.notna()], "XL"),
        "bookings_standard": cls(lyft_booked, "standard"), "bookings_xl": cls(lyft_booked, "XL"),
        "van_km": sum(travel.dm(a, b) for a, b in zip(dep.frm, dep.to)) / 10_000,
        "epochs": len(epochs),
        "main_optimal": int(st.get("optimal", 0)), "main_empty": int(st.get("empty", 0)),
        "main_feasible_unproven": int(st.get("feasible_unproven", 0)), "main_failed": int(st.get("failed", 0)),
        "tie_unique": int(ts.get("unique", 0)), "tie_tie": int(ts.get("tie", 0)),
        "tie_incomplete": int(ts.get("tie_enumeration_incomplete", 0)),
        "tie_truncated": int(ts.get("tie_enumeration_truncated", 0)), "tie_not_checked": int(ts.get("not_checked", 0)),
    }


def run_one(args):
    night, rule, fp = args
    level = f"L5/{night}"
    final = run_dir(night, rule)
    tmp = final.with_name(final.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    scen = inputs.load(level)                      # refuses to run if the content hash differs from FROZEN_v2.json
    m = scen.params["travel_multiplier"]
    travel = inputs.Travel(m, m)
    eng = E.Engine(scen, travel, policy_for(scen, rule))
    t0 = time.perf_counter()
    try:
        eng.run()
    except Exception:
        fail = final.with_name(final.name + ".FAILED")
        shutil.rmtree(fail, ignore_errors=True)
        tmp.rename(fail)
        (fail / "traceback.txt").write_text(traceback.format_exc())
        pd.DataFrame(eng.events).to_csv(fail / "events_partial.csv", index=False)
        with open(fail / "epochs_partial.jsonl", "w") as f:
            for ep in eng.epochs:
                f.write(json.dumps(ep, default=str) + "\n")
        try:
            (fail / "observation_at_failure.json").write_text(json.dumps(_obs_json(eng.observation()), indent=1))
        except Exception:
            pass
        return {"night": night, "rule": rule, "status": "failed", "error": traceback.format_exc().splitlines()[-1]}
    wall = time.perf_counter() - t0
    ev = pd.DataFrame(eng.events)
    ev.to_csv(tmp / "events.csv", index=False)
    with open(tmp / "epochs.jsonl", "w") as f:
        for ep in eng.epochs:
            f.write(json.dumps(ep, default=str) + "\n")
    out = pd.DataFrame(eng.outcomes())
    out.to_csv(tmp / "outcomes.csv", index=False)
    man = {"night": night, "rule": rule, "level": level, "content_hash": scen.content_hash,
           "matrix_sha256": travel.matrix_sha256, "code_fingerprint": fp, "config": config(rule),
           "end_s": eng.end_s, "wall_s": round(wall, 2), "python": sys.version.split()[0]}
    run = {"rule": rule, "out": pd.read_csv(tmp / "outcomes.csv"), "events": pd.read_csv(tmp / "events.csv"),
           "epochs": eng.epochs, "manifest": man}
    ck = checks(run, scen, travel, eng.pol.p_absent, level)
    met = metrics(run["out"], run["events"], eng.epochs, travel)
    met["wall_s"] = man["wall_s"]
    exc = guardrail_excesses(run, scen, travel)
    met["guardrail_excess_attributed"] = sum(e["attributed"] for e in exc)
    met["guardrail_excess_unexplained"] = sum(not e["attributed"] for e in exc)
    man["guardrail_excesses"] = exc
    (tmp / "metrics.json").write_text(json.dumps(met, indent=1))
    man["checks"] = {k: bool(v) for k, v in ck.items()}
    man["status"] = "ok" if all(ck.values()) else "checks_failed"
    (tmp / "manifest.json").write_text(json.dumps(man, indent=1, default=str))
    shutil.rmtree(final, ignore_errors=True)
    tmp.rename(final)
    return {"night": night, "rule": rule, "status": man["status"], "wall_s": man["wall_s"],
            "failed_checks": [k for k, v in ck.items() if not v]}


def done(night, rule, fp):
    f = run_dir(night, rule) / "manifest.json"
    if not f.exists():
        return False
    man = json.loads(f.read_text())
    if man["code_fingerprint"] != fp or man["config"] != json.loads(json.dumps(config(rule), default=str)):
        raise SystemExit(f"{night} {rule}: existing run has a different code fingerprint or configuration; "
                         "refusing to mix versions (move the batch folder aside to start a new one)")
    return man["status"] == "ok"


def cmd_run(workers):
    fp = code_fingerprint()
    BATCH.mkdir(parents=True, exist_ok=True)
    todo = [(n, r, fp) for n in NIGHTS for r in RULES if not done(n, r, fp)]
    todo.sort(key=lambda x: (x[1] != "R0", x[0]))           # slowest arm first
    print(f"code fingerprint {fp[:12]}; {len(todo)} runs to do", flush=True)
    log = open(BATCH / "batch_log.jsonl", "a")
    failed = False
    with Pool(workers) as pool:
        pending, it = [], iter(todo)
        for _ in range(workers):
            a = next(it, None)
            if a:
                pending.append(pool.apply_async(run_one, (a,)))
        while pending:
            res = pending.pop(0).get()
            res["t"] = time.strftime("%H:%M:%S")
            log.write(json.dumps(res) + "\n"); log.flush()
            print(res, flush=True)
            if res["status"] != "ok":
                failed = True                              # pause: no new launches; in-flight runs finish
            if not failed:
                a = next(it, None)
                if a:
                    pending.append(pool.apply_async(run_one, (a,)))
    print("PAUSED after a failure" if failed else "batch complete", flush=True)


def cmd_summary():
    rows, pairing = [], []
    for n in NIGHTS:
        hashes, cfgs = set(), set()
        for r in RULES:
            d = run_dir(n, r)
            man = json.loads((d / "manifest.json").read_text())
            met = json.loads((d / "metrics.json").read_text())
            rows.append({"night": n, "rule": r, "status": man["status"], **met})
            hashes.add(man["content_hash"])
            c = dict(man["config"]); c.pop("rule")
            cfgs.add(json.dumps(c, sort_keys=True))
            fp = man["code_fingerprint"]
        pairing.append({"night": n, "same_inputs": len(hashes) == 1, "same_config_except_rule": len(cfgs) == 1})
    df = pd.DataFrame(rows)
    df.to_csv(BATCH / "per_night_metrics.csv", index=False)
    pr = pd.DataFrame(pairing)
    fps = {json.loads((run_dir(n, r) / "manifest.json").read_text())["code_fingerprint"] for n in NIGHTS for r in RULES}

    def ms(s, f="{:.1f}"):
        s = s.dropna()
        return f"{f.format(s.mean())} ({f.format(s.std())}; {f.format(s.min())}–{f.format(s.max())})" + (
            f" [n={len(s)}]" if len(s) < 30 else "")
    L = ["# L5 30-night batch: summary (D-57)", "",
         "30 frozen L5 nights (r00–r29; 28 requests each) × 6 rules = 180 runs; settings of D-56/D-57, identical across "
         "arms except the rule. **Cells are averages of nightly measures: mean (SD across nights; min–max)**; counts are "
         "per night. Pipeline verification and variability under provisional assumptions: no intervals, no "
         "non-inferiority, no ranking (D-50 unresolved).", "",
         "| Measure (per night) | " + " | ".join(RULES) + " |", "|---|" + "---|" * len(RULES)]
    spec = [("Reached by a vehicle (curb arrival) within 15 min, share of all 28 requests", "reached_15_share", "{:.2f}"),
            ("Requests picked up (of 28)", "picked_up_requests", "{:.1f}"),
            ("Wait median, min (requests picked up)", "wait_median_min", "{:.1f}"),
            ("Wait P90, min (requests picked up)", "wait_p90_min", "{:.1f}"),
            ("Wait max, min (requests picked up)", "wait_max_min", "{:.1f}"),
            ("Wait median, min (passengers picked up)", "wait_pax_median_min", "{:.1f}"),
            ("Wait P90, min (passengers picked up)", "wait_pax_p90_min", "{:.1f}"),
            ("Van completed", "van_completed", "{:.1f}"), ("Lyft completed", "lyft_completed", "{:.1f}"),
            ("Cancelled while waiting for a van", "cancel_pending_van", "{:.1f}"),
            ("Cancelled after transfer", "cancel_after_transfer", "{:.1f}"),
            ("No-show, van / Lyft", None, None),
            ("Lyft bookings, standard", "bookings_standard", "{:.1f}"), ("Lyft bookings, XL", "bookings_xl", "{:.2f}"),
            ("Van-km", "van_km", "{:.1f}"), ("Run wall time, s", "wall_s", "{:.1f}")]
    for label, col, f in spec:
        if col is None:
            cells = [f"{df[df.rule == r].noshow_van.mean():.1f} / {df[df.rule == r].noshow_lyft.mean():.1f}" for r in RULES]
        else:
            cells = [ms(df[df.rule == r][col], f) for r in RULES]
        L.append(f"| {label} | " + " | ".join(cells) + " |")
    L += [f"| Van rides over the guardrail: attributed to no-show waits / unexplained (totals) | " + " | ".join(
        f"{int(df[df.rule == r].guardrail_excess_attributed.sum())} / {int(df[df.rule == r].guardrail_excess_unexplained.sum())}"
        for r in RULES) + " |"]
    tot = df.groupby("rule")[["epochs", "main_optimal", "main_empty", "main_feasible_unproven", "main_failed",
                              "tie_incomplete", "tie_truncated", "tie_tie"]].sum().reindex(RULES)
    L += ["", "**Solver diagnostics (totals over 30 nights):**", "",
          "| Rule | Epochs | Main solve optimal / empty / feasible-unproven / failed | Tie search: ties found / incomplete / truncated |",
          "|---|---|---|---|"]
    for r, x in tot.iterrows():
        L.append(f"| {r} | {x.epochs} | {x.main_optimal} / {x.main_empty} / {x.main_feasible_unproven} / {x.main_failed} | "
                 f"{x.tie_tie} / {x.tie_incomplete} / {x.tie_truncated} |")
    L += ["", f"Runs complete with all checks passing: {(df.status == 'ok').sum()} of {len(df)}. Paired arms with identical "
          f"inputs: {pr.same_inputs.sum()} of 30 nights; identical configuration except the rule: "
          f"{pr.same_config_except_rule.sum()} of 30. Code fingerprints in the batch: {len(fps)} "
          f"({', '.join(x[:12] for x in fps)}).",
          "", "An optimal main solve does not establish complete tie-breaking: an incomplete tie search means the canonical "
          "choice among equal-cost plans is not guaranteed for that epoch, and does not prove the optimum is unique.", "",
          "Empty-metric handling: a wait cell excludes nights with no picked-up requests and shows [n=…] when fewer than 30 "
          "nights contribute. Per-night values: `per_night_metrics.csv`."]
    (BATCH / "summary.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


def cmd_reproduce(sample):
    """Re-run a documented sample in memory and compare events.csv byte for byte."""
    res = []
    for night, rule in sample:
        scen = inputs.load(f"L5/{night}")
        m = scen.params["travel_multiplier"]
        eng = E.Engine(scen, inputs.Travel(m, m), policy_for(scen, rule)).run()
        same = pd.DataFrame(eng.events).to_csv(index=False) == (run_dir(night, rule) / "events.csv").read_text()
        res.append({"night": night, "rule": rule, "events_identical": same})
        print(res[-1], flush=True)
    pilot = {"R0": OUT / "L5_r00_R0", "R2(15)": OUT / "L5_r00_R2-15"}
    for rule, d in pilot.items():
        if (d / "events.csv").exists():
            same = (d / "events.csv").read_text() == (run_dir("r00", rule) / "events.csv").read_text()
            res.append({"night": "r00", "rule": rule, "batch_equals_pilot_output": same})
            print(res[-1], flush=True)
    (BATCH / "reproducibility.json").write_text(json.dumps(res, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "summary", "reproduce"])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--sample", nargs="*", default=["r00:R0", "r00:R2(15)", "r07:R1(10)", "r13:R3(2)", "r21:R1u(10)",
                                                     "r29:R1(15)"])
    a = ap.parse_args()
    if a.cmd == "run":
        cmd_run(a.workers)
    elif a.cmd == "summary":
        cmd_summary()
    else:
        cmd_reproduce([tuple(x.split(":", 1)) for x in a.sample])


if __name__ == "__main__":
    main()
