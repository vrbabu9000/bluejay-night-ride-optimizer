"""M7 runner and analysis: the Lyft-rule grid on full base evenings (plan: research_notes/m7_plan_2026-11.md).

    cd src && ../.venv/bin/python -m sim.m7 run pilot --workers 8   # power pilot: R0, R3(2), base_5 r30-r39
    ../.venv/bin/python -m sim.m7 power                              # night count from the pilot (plan §3a)
    ../.venv/bin/python -m sim.m7 run main --workers 8               # 6 rules x 5/6 vans x the main nights
    ../.venv/bin/python -m sim.m7 compare                            # pair intervals, dominance, H3 (plan §4-§5)
    ../.venv/bin/python -m sim.m7 status

Every run is one full L6 evening (168 requests) with C exactly as in M5b/M6; only the Lyft rule and the fleet vary.
Runs reuse sim.m6.run_one (same full-night checks); the manifest is re-labelled stage "m7" and records the M7 plan
SHA-256. No fingerprinted file is changed. Layout: outputs/sim/m7/<stage>/<cell>/<night>/rep1/.
"""
import argparse
import hashlib
import itertools
import json
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from . import inputs, lyft, m5, m6
from .batch import metrics
from .run import OUT

M7 = OUT / "m7"
PLAN = inputs.ROOT / "docs" / "technical" / "research_notes" / "m7_plan_2026-11.md"
PREREG = inputs.ROOT / "docs" / "technical" / "preregistration_v2.md"
CODE_FINGERPRINT = m6.CODE_FINGERPRINT
RULES = list(lyft.RULES)                                    # R0, R1(10), R1(15), R1u(10), R2(15), R3(2)
TRANSFER_RULES = RULES[1:]
FLEETS = (5, 6)
PILOT_NIGHTS = [f"r{i:02d}" for i in range(30, 40)]
MAIN30 = [f"r{i:02d}" for i in range(30)]
MAIN60 = MAIN30 + [f"r{i:02d}" for i in range(40, 70)]
CUTOFF = "2026-11-30T12:00:00-05:00"
MAX_WORKERS = 8
B, SEED = 10_000, 20261110
DELTA = {"not_reached_20_pp": 2.0, "not_reached_15_pp": 2.0, "wait_pax_p90_min": 1.0, "lyft_per_100": 2.0}
ROLE = {"not_reached_20_pp": "primary", "not_reached_15_pp": "sensitivity", "wait_pax_p90_min": "secondary",
        "lyft_per_100": "resource"}
DOMINANCE_MEASURES = ("not_reached_20_pp", "wait_pax_p90_min", "lyft_per_100")
TRACED = ("r00", 5, ("R0", "R2(15)"))                       # plan §6, fixed before any run


def cell(rule, fleet):
    return m5._c("base", fleet, "C", rule=rule)


def plan_frozen():
    return PLAN.exists() and "**Status: FROZEN" in PLAN.read_text()


def plan_sha():
    return hashlib.sha256(PLAN.read_bytes()).hexdigest()


def main_nights(root=None):
    """30 or 60 nights, from the power decision written by `power` (plan §3a)."""
    f = (root or M7) / "power.json"
    if not f.exists():
        raise SystemExit("m7: run the pilot and `power` first; the night count is not set")
    return MAIN60 if json.loads(f.read_text())["nights"] == 60 else MAIN30


def runs(stage, root=None):
    if stage == "pilot":
        return [(cell(r, 5), n) for n in PILOT_NIGHTS for r in ("R0", "R3(2)")]
    return [(cell(r, f), n) for n in main_nights(root) for f in FLEETS for r in RULES]   # night by night


def stage_root(stage, root=None):
    return (root or M7) / stage


def run_dir(stage, c, night, root=None):
    return m6.run_dir(c, night, root=stage_root(stage, root))


def run_one(args, root=None, scen_fn=m6.full_night):
    stage, c, night, fp = args
    res = m6.run_one((c, night, fp), scen_fn=scen_fn, root=stage_root(stage, root))
    f = run_dir(stage, c, night, root) / "manifest.json"
    if f.exists():
        man = json.loads(f.read_text())
        man.update({"stage": f"m7_{stage}", "m7_plan_sha256": plan_sha() if PLAN.exists() else None,
                    "prereg_v2_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest()})
        man.pop("plan_sha256", None)                        # that key is the M6 plan's; not M7's
        f.write_text(json.dumps(man, indent=1, default=str))
    res["stage"] = stage
    return res


def done(stage, c, night, fp, root=None):
    f = run_dir(stage, c, night, root) / "manifest.json"
    if not f.exists():
        return False
    man = json.loads(f.read_text())
    if man["code_fingerprint"] != fp or man["config"] != json.loads(json.dumps(m6.config(c), default=str)):
        raise SystemExit(f"m7 {stage} {c.name} {night}: existing run has a different fingerprint or configuration")
    if man.get("m7_plan_sha256") != plan_sha():
        raise SystemExit(f"m7 {stage} {c.name} {night}: run made under a different M7 plan file; refusing to mix")
    return True


def cmd_run(stage, workers, root=None):
    if not plan_frozen():
        raise SystemExit(f"m7: the plan must be frozen in {PLAN.name} (a '**Status: FROZEN <date>**' line) first")
    fp = m5.code_fingerprint()
    if not fp.startswith(CODE_FINGERPRINT):
        raise SystemExit(f"m7: code fingerprint {fp[:12]} is not {CODE_FINGERPRINT}; refusing to run")
    for n in sorted({n for _, n in runs(stage, root)}):     # every night must exist and match its frozen hash
        for f in ((5,) if stage == "pilot" else FLEETS):
            m6.full_night(cell("R0", f), n)
    workers = min(workers, MAX_WORKERS)
    todo = [(stage, c, n, fp) for c, n in runs(stage, root) if not done(stage, c, n, fp, root)]
    stage_root(stage, root).mkdir(parents=True, exist_ok=True)
    print(f"m7 {stage}: code fingerprint {fp[:12]}; {len(todo)} runs to do; {workers} workers", flush=True)
    log = open(stage_root(stage, root) / "run_log.jsonl", "a")
    failed = False
    with Pool(workers, maxtasksperchild=1) as pool:
        it, pending = iter(todo), []
        for _ in range(workers):
            a = next(it, None)
            if a:
                pending.append(pool.apply_async(run_one, (a, root)))
        while pending:
            while not any(p.ready() for p in pending):
                time.sleep(1)
            res = pending.pop(next(i for i, p in enumerate(pending) if p.ready())).get()
            res["t"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            log.write(json.dumps(res) + "\n"); log.flush()
            print(res, flush=True)
            failed |= res["status"] == "failed"             # a crash pauses; a failed check is reported (plan §3c)
            if not failed:
                a = next(it, None)
                if a:
                    pending.append(pool.apply_async(run_one, (a, root)))
    print("PAUSED after a crash: find the cause before resuming" if failed else f"m7 {stage} complete", flush=True)


# ---------- measures ----------
def measures(d):
    out, ev = pd.read_csv(d / "outcomes.csv"), pd.read_csv(d / "events.csv")
    met = metrics(out, ev, m5._epochs(d), inputs.Travel(1.2, 1.2))
    n = met["n_requests"]
    bookings = met["bookings_standard"] + met["bookings_xl"]
    return {"not_reached_20_pp": 100 * (1 - met["reached_20_share"]),
            "not_reached_15_pp": 100 * (1 - met["reached_15_share"]),
            "wait_pax_p90_min": met["wait_pax_p90_min"], "lyft_per_100": 100 * bookings / n,
            "lyft_bookings": bookings, "van_km": met["van_km"],
            "cancellations": met["cancel_pending_van"] + met["cancel_after_transfer"],
            "transfers": met["transfers_standard"] + met["transfers_xl"], "n_requests": n}


def _man(d):
    return json.loads((d / "manifest.json").read_text())


def per_night(stage, nights, rules, fleets, root=None):
    rows = []
    for n in nights:
        for f in fleets:
            for r in rules:
                d = run_dir(stage, cell(r, f), n, root)
                if not (d / "manifest.json").exists():
                    continue
                man = _man(d)
                rows.append({"night": n, "fleet": f, "rule": r, "status": man["status"],
                             "finished_at": man["finished_at"], "wall_min": man["wall_s"] / 60,
                             "failed_checks": "; ".join(k for k, v in man["checks"].items() if not v),
                             **measures(d)})
    return pd.DataFrame(rows)


# ---------- power (plan §3a) ----------
def power(root=None):
    d = per_night("pilot", PILOT_NIGHTS, ("R0", "R3(2)"), (5,), root)
    if d.empty:
        raise SystemExit("m7 power: the pilot is not complete")
    w ={m: d.pivot(index="night", columns="rule", values=m) for m in DELTA}
    if len(w["not_reached_20_pp"].dropna()) < len(PILOT_NIGHTS):
        raise SystemExit("m7 power: the pilot is not complete")
    out = {"pilot_nights": PILOT_NIGHTS, "measures": {}}
    for m, t in w.items():
        diff = (t["R3(2)"] - t["R0"]).to_numpy()
        sd = float(np.std(diff, ddof=1))
        out["measures"][m] = {"mean_R3_minus_R0": float(diff.mean()), "sd": sd,
                              "hw30": 1.96 * sd / np.sqrt(30), "hw60": 1.96 * sd / np.sqrt(60),
                              "target": 0.7 * DELTA[m]}
    p = out["measures"]["not_reached_20_pp"]
    out["nights"] = 30 if p["hw30"] <= p["target"] else 60
    out["underpowered_at_60"] = bool(out["nights"] == 60 and p["hw60"] > p["target"])
    out["pilot_failed_checks"] = d[d.status != "ok"][["night", "rule", "failed_checks"]].to_dict("records")
    return out


def cmd_power(root=None):
    out = power(root)
    (root or M7).mkdir(parents=True, exist_ok=True)
    f = (root or M7) / "power.json"
    if f.exists() and json.loads(f.read_text())["nights"] != out["nights"]:
        raise SystemExit("m7 power: an existing power decision differs; refusing to overwrite")
    f.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


# ---------- comparison (plan §4-§5) ----------
def used_nights(d, nights, cutoff=CUTOFF, explained=()):
    """Plan §3b: the longest unbroken prefix with all 12 runs finished by the cutoff; then less nights with a failed
    check not listed in `explained` (a set of (night, fleet, rule) recorded in the run record under §3c)."""
    cut, prefix = pd.Timestamp(cutoff), []
    for n in nights:
        x = d[d.night == n]
        if len(x) < len(RULES) * len(FLEETS) or not all(pd.Timestamp(t) <= cut for t in x.finished_at):
            break
        prefix.append(n)
    bad = d[(d.status != "ok") & d.night.isin(prefix)]
    unexplained = {r.night for r in bad.itertuples() if (r.night, r.fleet, r.rule) not in set(explained)}
    strict = [n for n in prefix if n not in set(bad.night)]
    return prefix, [n for n in prefix if n not in unexplained], strict


def verdict(lo, hi, delta, a, b):
    if hi < 0:
        return f"{a} better"
    if lo > 0:
        return f"{b} better"
    if hi < delta and lo > -delta:
        return "within margin both ways"
    if hi < delta:
        return f"{a} non-inferior"
    if lo > -delta:
        return f"{b} non-inferior"
    return "cannot tell"


def boot_index(k):
    return np.random.default_rng(SEED).integers(0, k, size=(B, k))


def ci(x, idx, level=95.0):
    x = np.asarray(x, dtype=float)
    boot = x[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [(100 - level) / 2, 100 - (100 - level) / 2])
    return float(x.mean()), float(lo), float(hi)


def pair_intervals(d, nights, fleet):
    idx = boot_index(len(nights))
    rows = []
    for m in DELTA:
        w = d[d.fleet == fleet].pivot(index="night", columns="rule", values=m).reindex(index=nights, columns=RULES)
        for a, b in itertools.combinations(RULES, 2):
            mean, lo, hi = ci((w[a] - w[b]).to_numpy(), idx)
            rows.append({"fleet": fleet, "measure": m, "role": ROLE[m], "A": a, "B": b, "nights": len(nights),
                         "mean": mean, "lo": lo, "hi": hi, "delta": DELTA[m],
                         "verdict": verdict(lo, hi, DELTA[m], a, b)})
    return pd.DataFrame(rows)


def dominance(iv, fleet, delta_b=2.0):
    t = iv[iv.fleet == fleet].set_index(["measure", "A", "B"])
    delta = {"not_reached_20_pp": 2.0, "wait_pax_p90_min": 1.0, "lyft_per_100": delta_b}

    def hi(m, a, b):
        return t.loc[(m, a, b)].hi if (m, a, b) in t.index else -t.loc[(m, b, a)].lo

    rows = []
    for a, b in itertools.permutations(RULES, 2):
        u = {m: hi(m, a, b) for m in delta}
        ni = all(u[m] < delta[m] for m in delta)
        better = [m for m in delta if u[m] < 0]
        rows.append({"fleet": fleet, "delta_b": delta_b, "A": a, "B": b, "A_noninferior_all": ni,
                     "A_better_on": ";".join(better), "A_dominates_B": bool(ni and better)})
    return pd.DataFrame(rows)


def h3(d, nights, measure="not_reached_20_pp", level=98.3):
    """Plan §5: per night, mean over the five transfer rules of |A - R0| at 5 vans minus |A - R0| at 6 vans."""
    w = {f: d[d.fleet == f].pivot(index="night", columns="rule", values=measure).reindex(index=nights) for f in FLEETS}
    per_rule = {a: (w[5][a] - w[5]["R0"]).abs() - (w[6][a] - w[6]["R0"]).abs() for a in TRANSFER_RULES}
    contrast = pd.concat(per_rule, axis=1).mean(axis=1).to_numpy()
    idx = boot_index(len(nights))
    mean, lo, hi = ci(contrast, idx, level)
    reading = "supported" if lo > 0 else "contradicted" if hi < 0 else "not settled"
    rules = {a: ci(v.to_numpy(), idx) for a, v in per_rule.items()}
    return {"measure": measure, "level": level, "nights": len(nights), "mean": mean, "lo": lo, "hi": hi,
            "reading": reading, "per_rule_95": rules}


def _f(x, nd=2):
    return f"{x:+.{nd}f}"


def cmd_compare(root=None, explained=(), cutoff=CUTOFF):
    root = root or M7
    nights_all = main_nights(root)
    d = per_night("main", nights_all, RULES, FLEETS, root)
    prefix, nights, strict = used_nights(d, nights_all, cutoff, explained)
    if len(nights) < 5:
        raise SystemExit(f"m7 compare: only {len(nights)} usable nights")
    du = d[d.night.isin(nights)]
    iv = pd.concat([pair_intervals(du, nights, f) for f in FLEETS])
    dom = pd.concat([dominance(iv, f, db) for f in FLEETS for db in (2.0, 1.0)])
    H = h3(du, nights)
    Hs = {m: h3(du, nights, m, 95.0) for m in ("wait_pax_p90_min", "lyft_per_100")}
    Hstrict = h3(d[d.night.isin(strict)], strict) if len(strict) >= 5 and strict != nights else None
    L = ["# M7: Lyft-rule grid, full base evenings (L6 base_5 / base_6, 168 requests, C)", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')}. Plan `{PLAN.name}` (sha256 {plan_sha()[:12]}), "
         f"preregistration `{PREREG.name}` (sha256 {hashlib.sha256(PREREG.read_bytes()).hexdigest()[:12]}). "
         f"Cutoff {cutoff}. Nights finished / used / with no failed check: {len(prefix)} / {len(nights)} / "
         f"{len(strict)}. Paired percentile bootstrap over nights, {B:,} resamples, seed {SEED}. "
         "Levels rest on ASSUMED placeholder behaviour; the differences are the claim.", "",
         "## H3 (confirmatory, 98.3%)", "",
         f"Contrast: mean over the five transfer rules of |A − R0| at 5 vans − |A − R0| at 6 vans, primary share (pp). "
         f"**{_f(H['mean'])} [{_f(H['lo'])}, {_f(H['hi'])}] → H3 {H['reading']}.**", ""]
    if Hstrict:
        L.append(f"Sensitivity, every failed-check night excluded ({Hstrict['nights']} nights): "
                 f"{_f(Hstrict['mean'])} [{_f(Hstrict['lo'])}, {_f(Hstrict['hi'])}] → {Hstrict['reading']}.")
        L.append("")
    L += ["| Rule | |A − R0| at 5 vans − at 6 vans, pp (95%) |", "|---|---|"]
    for a, (m_, lo, hi) in H["per_rule_95"].items():
        L.append(f"| {a} | {_f(m_)} [{_f(lo)}, {_f(hi)}] |")
    for m, h in Hs.items():
        L.append(f"| (same contrast on {m}, 95%) | {_f(h['mean'])} [{_f(h['lo'])}, {_f(h['hi'])}] |")
    for f in FLEETS:
        g = du[du.fleet == f].groupby("rule")[list(DELTA) + ["van_km", "cancellations", "wall_min"]].mean()
        L += ["", f"## {f} vans: rule means over {len(nights)} nights", "",
              "| Rule | Not reached ≤20 min, % | ≤15 min, % | P90 pax wait, min | Lyft bookings /100 | Van-km | "
              "Cancellations | C wall, min |", "|---|---|---|---|---|---|---|---|"]
        for r in RULES:
            x = g.loc[r]
            L.append(f"| {r} | {x.not_reached_20_pp:.1f} | {x.not_reached_15_pp:.1f} | {x.wait_pax_p90_min:.1f} | "
                     f"{x.lyft_per_100:.1f} | {x.van_km:.0f} | {x.cancellations:.1f} | {x.wall_min:.1f} |")
        L += ["", f"### {f} vans: pairs (A − B, 95%; exploratory)", "",
              "| A | B | Not reached ≤20, pp | P90 wait, min | Bookings /100 | ≤15 (sensitivity), pp |",
              "|---|---|---|---|---|---|"]
        t = iv[iv.fleet == f].set_index(["measure", "A", "B"])
        for a, b in itertools.combinations(RULES, 2):
            cells = []
            for m in ("not_reached_20_pp", "wait_pax_p90_min", "lyft_per_100", "not_reached_15_pp"):
                r_ = t.loc[(m, a, b)]
                cells.append(f"{_f(r_['mean'], 1)} [{_f(r_.lo, 1)}, {_f(r_.hi, 1)}] {r_.verdict}")
            L.append(f"| {a} | {b} | " + " | ".join(cells) + " |")
        for db in (2.0, 1.0):
            x = dom[(dom.fleet == f) & (dom.delta_b == db) & dom.A_dominates_B]
            nd = [r for r in RULES if r not in set(x.B)]
            L += ["", f"**Dominance, {f} vans, δ_B = {db:g}:** "
                  + ("; ".join(f"{r.A} dominates {r.B} (better on {r.A_better_on})" for r in x.itertuples())
                     or "no rule dominates another") + f". Nondominated: {', '.join(nd)}."]
    root.mkdir(parents=True, exist_ok=True)
    d.to_csv(root / "per_night.csv", index=False)
    iv.to_csv(root / "pair_intervals.csv", index=False)
    dom.to_csv(root / "dominance.csv", index=False)
    (root / "h3.json").write_text(json.dumps({"primary": H, "secondary": Hs, "strict": Hstrict}, indent=1))
    (root / "comparison_m7.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


def cmd_status(root=None):
    for stage in ("pilot", "main"):
        f = stage_root(stage, root) / "run_log.jsonl"
        if not f.exists():
            print(f"{stage}: not started"); continue
        rs = [json.loads(x) for x in f.read_text().splitlines()]
        try:
            total = len(runs(stage, root))
        except SystemExit:
            total = "?"
        w = [r["wall_s"] / 60 for r in rs if "wall_s" in r]
        bad = [(r["cell"], r["night"]) for r in rs if r["status"] != "ok"]
        print(f"{stage}: {len(rs)}/{total} finished" + (f", median {np.median(w):.1f} min, max {max(w):.1f} min"
                                                       if w else "") + (f"; not ok: {bad}" if bad else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "power", "compare", "status"])
    ap.add_argument("stage", nargs="?", choices=["pilot", "main"])
    ap.add_argument("--workers", type=int, default=MAX_WORKERS)
    ap.add_argument("--explained", default="", help="JSON list of [night, fleet, rule] explained check failures")
    a = ap.parse_args()
    if a.cmd == "run":
        cmd_run(a.stage, a.workers)
    elif a.cmd == "power":
        cmd_power()
    elif a.cmd == "compare":
        cmd_compare(explained=[tuple(x) for x in json.loads(a.explained or "[]")])
    else:
        cmd_status()


if __name__ == "__main__":
    main()
