"""M8: sensitivity of the five-van Lyft-rule results to patience, Lyft delay and acceptance
(plan: docs/technical/research_notes/m8_plan_2026-11.md).

    cd src && ../.venv/bin/python -m sim.m8 run --workers 8
    ../.venv/bin/python -m sim.m8 status
    ../.venv/bin/python -m sim.m8 compare [--explained JSON]

Each run is one full L6 base_5 evening with C exactly as in M7. Only one assumption moves per setting:
  - patience and Lyft delay: every rider's frozen draw is scaled (common random numbers); the frozen files are not changed;
  - acceptance: the policy's consent_p (a rider accepts if their frozen consent_u < p_c).
Runs reuse sim.m6.run_one (same checks, evaluated on the scaled scenario). The base and the R0 runs for the Lyft and
acceptance settings are the M7 five-van runs. No fingerprinted file is changed. Layout:
outputs/sim/m8/<setting>/<cell>/<night>/rep1/.
"""
import argparse
import dataclasses
import hashlib
import json
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from . import inputs, m5, m6, m7
from .run import OUT

M8 = OUT / "m8"
PLAN = inputs.ROOT / "docs" / "technical" / "research_notes" / "m8_plan_2026-11.md"
CODE_FINGERPRINT = m6.CODE_FINGERPRINT
SETTINGS = {
    "patience_short": {"patience_x": 2 / 3},
    "patience_long": {"patience_x": 3 / 2},
    "lyft_fast": {"lyft_delay_x": 2 / 3},
    "lyft_slow": {"lyft_delay_x": 3 / 2},
    "consent_80": {"consent_p": 0.8},
    "consent_60": {"consent_p": 0.6},
}
TRANSFER = ["R1(10)", "R1(15)", "R2(15)", "R3(2)"]            # R1u(10) never fires (M7 §3): not run
NIGHTS = m7.MAIN30
FLEET = 5
CUTOFF = "2026-11-28T12:00:00-05:00"
MIN_NIGHTS = 10
MAX_WORKERS = 8
M7_EXPLAINED = {("r00", "R1(10)"), ("r02", "R0"), ("r02", "R1(15)"), ("r02", "R1u(10)"), ("r04", "R2(15)")}  # M7 run record


def rules(setting):
    return (["R0"] if setting.startswith("patience") else []) + TRANSFER


def runs():
    return [(s, r, n) for n in NIGHTS for s in SETTINGS for r in rules(s)]           # night by night


def plan_frozen():
    return PLAN.exists() and "**Status: FROZEN" in PLAN.read_text()


def plan_sha():
    return hashlib.sha256(PLAN.read_bytes()).hexdigest()


def transform(scen, setting):
    """The frozen night with this setting's per-rider scaling (patience, Lyft delay). Acceptance is a policy setting."""
    s = SETTINGS[setting]
    px, lx = s.get("patience_x", 1.0), s.get("lyft_delay_x", 1.0)
    if px == 1.0 and lx == 1.0:
        return scen
    hidden = {rid: dataclasses.replace(h, patience_s=max(1, int(round(h.patience_s * px))),
                                       lyft_delay_s=max(1, int(round(h.lyft_delay_s * lx))))
              for rid, h in scen.hidden.items()}
    return dataclasses.replace(scen, hidden=hidden)


def hidden_sha(scen):
    rows = [(rid, h.patience_s, h.noshow_u, h.consent_u, h.lyft_delay_s) for rid, h in sorted(scen.hidden.items())]
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def _install_policy(setting):
    """Within this worker only: m5.policy (read by m6.run_one and m5.config) gets this setting's consent_p."""
    p_c = SETTINGS[setting].get("consent_p")
    base = getattr(m5.policy, "_m8_base", m5.policy)
    if p_c is None:
        m5.policy = base
        return
    def policy(cell):
        return dataclasses.replace(base(cell), consent_p=p_c)
    policy._m8_base = base
    m5.policy = policy


def run_dir(setting, rule, night, root=None):
    return m6.run_dir(m7.cell(rule, FLEET), night, root=(root or M8) / setting)


def run_one(args, root=None, scen_fn=m6.full_night):
    setting, rule, night, fp = args
    _install_policy(setting)
    try:
        def load(c, n):
            scen, key = scen_fn(c, n)
            return transform(scen, setting), key
        res = m6.run_one((m7.cell(rule, FLEET), night, fp), scen_fn=load, root=(root or M8) / setting)
        f = run_dir(setting, rule, night, root) / "manifest.json"
        if f.exists():
            man = json.loads(f.read_text())
            scen, _ = load(m7.cell(rule, FLEET), night)
            man.update({"stage": f"m8_{setting}", "m8_setting": setting, "m8_transform": SETTINGS[setting],
                        "hidden_sha256_after_transform": hidden_sha(scen),
                        "m8_plan_sha256": plan_sha() if PLAN.exists() else None})
            man.pop("plan_sha256", None)
            f.write_text(json.dumps(man, indent=1, default=str))
    finally:
        _install_policy("patience_short")                     # restore (no consent_p) for anything after
    res.update({"setting": setting, "rule": rule})
    return res


def done(setting, rule, night, fp, root=None):
    f = run_dir(setting, rule, night, root) / "manifest.json"
    if not f.exists():
        return False
    man = json.loads(f.read_text())
    if man["code_fingerprint"] != fp or man.get("m8_plan_sha256") != plan_sha():
        raise SystemExit(f"m8 {setting} {rule} {night}: existing run has another fingerprint or plan; refusing to mix")
    return True


def cmd_run(workers, root=None):
    if not plan_frozen():
        raise SystemExit(f"m8: the plan must be frozen in {PLAN.name} first")
    fp = m5.code_fingerprint()
    if not fp.startswith(CODE_FINGERPRINT):
        raise SystemExit(f"m8: code fingerprint {fp[:12]} is not {CODE_FINGERPRINT}; refusing to run")
    for n in NIGHTS:
        m6.full_night(m7.cell("R0", FLEET), n)
    workers = min(workers, MAX_WORKERS)
    todo = [(s, r, n, fp) for s, r, n in runs() if not done(s, r, n, fp, root)]
    (root or M8).mkdir(parents=True, exist_ok=True)
    print(f"m8: code fingerprint {fp[:12]}; {len(todo)} runs to do; {workers} workers", flush=True)
    log = open((root or M8) / "run_log.jsonl", "a")
    failed = False
    with Pool(workers, maxtasksperchild=1) as pool:
        it, pending = iter(todo), []
        for _ in range(workers):
            a = next(it, None)
            if a:
                pending.append(pool.apply_async(run_one, (a, root)))
        while pending:
            while not any(p.ready() for p in pending):
                time.sleep(2)
            for p in [p for p in pending if p.ready()]:
                pending.remove(p)
                res = p.get()
                res["t"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
                print(res, flush=True)
                log.write(json.dumps(res, default=str) + "\n"); log.flush()
                failed |= res["status"] == "failed"
                if not failed:
                    a = next(it, None)
                    if a:
                        pending.append(pool.apply_async(run_one, (a, root)))
    print("PAUSED after a crash: find the cause before resuming" if failed else "m8 complete", flush=True)


# ---------- analysis (plan §4) ----------
def _row(d, setting, rule, night, from_m7=False):
    man = json.loads((d / "manifest.json").read_text())
    o = pd.read_csv(d / "outcomes.csv")
    t = o[o.transfer_s.notna()]
    return {"setting": setting, "rule": rule, "night": night, "from_m7": from_m7, "status": man["status"], "finished_at": man["finished_at"],
            "wall_min": man["wall_s"] / 60, "failed_checks": "; ".join(k for k, v in man["checks"].items() if not v),
            "cancel_after_transfer_pct": 100 * (t.outcome == "cancel_after_transfer").mean() if len(t) else np.nan,
            **m7.measures(d)}


def from_m7(setting, rule):
    """The base, and R0 under the Lyft and acceptance settings, are the M7 five-van runs (plan §3)."""
    return setting == "base" or (rule == "R0" and not setting.startswith("patience"))


def source(setting, rule, night, root=None, m7_root=None):
    if from_m7(setting, rule):
        return m7.run_dir("main", m7.cell(rule, FLEET), night, m7_root)
    return run_dir(setting, rule, night, root)


def per_night(root=None, m7_root=None):
    rows = []
    for s in ["base", *SETTINGS]:
        for r in ["R0", *TRANSFER]:
            for n in NIGHTS:
                d = source(s, r, n, root, m7_root)
                if (d / "manifest.json").exists():
                    rows.append(_row(d, s, r, n, from_m7(s, r)))
    return pd.DataFrame(rows)


def used_nights(d, cutoff=CUTOFF, explained=()):
    """Longest prefix of nights complete in every setting before the cutoff; then the M7 §3c night rule."""
    need = {(s, r) for s in ["base", *SETTINGS] for r in ["R0", *TRANSFER]}
    cut = pd.Timestamp(cutoff)
    prefix = []
    for n in NIGHTS:
        x = d[d.night == n]
        have = {(a.setting, a.rule) for a in x.itertuples() if pd.Timestamp(a.finished_at) <= cut}
        if not need <= have:
            break
        prefix.append(n)
    bad = d[(d.status != "ok") & d.night.isin(prefix)]
    ok = set(explained)
    unexplained = {a.night for a in bad.itertuples()
                   if (a.setting, a.night, a.rule) not in ok and not (a.from_m7 and (a.night, a.rule) in M7_EXPLAINED)}
    return prefix, [n for n in prefix if n not in unexplained], [n for n in prefix if n not in set(bad.night)]


def effects(d, nights, measure="not_reached_20_pp"):
    """Per setting and transfer rule: E = A - R0 (95%), shift E_s - E_base (95%), gain per booking (95%)."""
    idx = m7.boot_index(len(nights))
    w = {s: g.pivot(index="night", columns="rule", values=measure).reindex(index=nights) for s, g in d.groupby("setting")}
    bk = {s: g.pivot(index="night", columns="rule", values="lyft_per_100").reindex(index=nights)
          for s, g in d.groupby("setting")}
    rows = []
    for s in ["base", *SETTINGS]:
        for a in TRANSFER:
            e = (w[s][a] - w[s]["R0"]).to_numpy()
            sh = e - (w["base"][a] - w["base"]["R0"]).to_numpy()
            gain, b = -e, bk[s][a].to_numpy()
            ratio = gain[idx].mean(axis=1) / b[idx].mean(axis=1)
            m, lo, hi = m7.ci(e, idx)
            rows.append({"setting": s, "rule": a, "measure": measure, "effect": m, "effect_lo": lo, "effect_hi": hi,
                         "shift": sh.mean(), "shift_lo": m7.ci(sh, idx)[1], "shift_hi": m7.ci(sh, idx)[2],
                         "bookings_per_100": b.mean(), "gain_per_booking": gain.mean() / b.mean() if b.mean() else np.nan,
                         "gpb_lo": np.percentile(ratio, 2.5), "gpb_hi": np.percentile(ratio, 97.5),
                         "holds_a": bool(hi < 0)})
    t = pd.DataFrame(rows)
    gpb = t.pivot(index="setting", columns="rule", values="gain_per_booking")
    t["holds_b"] = t.setting.map(lambda s: bool(gpb.loc[s, "R2(15)"] > gpb.loc[s, "R1(10)"]
                                              and gpb.loc[s, "R3(2)"] > gpb.loc[s, "R1(10)"]))
    return t


def cmd_compare(root=None, explained=(), cutoff=CUTOFF):
    d = per_night(root)
    prefix, nights, strict = used_nights(d, cutoff, explained)
    out = root or M8
    out.mkdir(parents=True, exist_ok=True)
    d.to_csv(out / "per_night.csv", index=False)
    means = d[d.night.isin(nights)].groupby(["setting", "rule"])[
        ["not_reached_20_pp", "not_reached_15_pp", "wait_pax_p90_min", "lyft_per_100", "cancellations",
         "cancel_after_transfer_pct", "wall_min"]].mean()
    L = [f"# M8: sensitivity of the five-van Lyft-rule results", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')}. Plan `{PLAN.name}` (sha256 {plan_sha()[:12]}). "
         f"Cutoff {cutoff}. Nights complete / used / strict: {len(prefix)} / {len(nights)} / {len(strict)}. "
         "Paired percentile bootstrap over nights, 10,000 resamples, seed 20261110. Sensitivity analysis: no test.", ""]
    if len(nights) < MIN_NIGHTS:
        L += [f"**Fewer than {MIN_NIGHTS} nights: means only (plan §3).**", "", means.round(2).to_markdown()]
        (out / "comparison_m8.md").write_text("\n".join(L) + "\n")
        print("\n".join(L))
        return
    t = effects(d, nights)
    t.to_csv(out / "effects.csv", index=False)
    ts = effects(d, strict) if strict != nights else None
    if ts is not None:
        ts.to_csv(out / "effects_strict.csv", index=False)
    f = lambda m, lo, hi: f"{m:+.1f} [{lo:+.1f}, {hi:+.1f}]"
    L += ["## Effect of each rule against R0 (not reached within 20 min, pp, 95%)", "",
          "| Setting | " + " | ".join(TRANSFER) + " | (a) holds for all | (b) holds |", "|---" * (len(TRANSFER) + 3) + "|"]
    for s in ["base", *SETTINGS]:
        x = t[t.setting == s].set_index("rule")
        L.append(f"| {s} | " + " | ".join(f(x.loc[a, 'effect'], x.loc[a, 'effect_lo'], x.loc[a, 'effect_hi'])
                                          for a in TRANSFER) + f" | {'yes' if x.holds_a.all() else 'no'} | "
                 f"{'yes' if x.holds_b.iloc[0] else 'no'} |")
    L += ["", "## Shift of the effect from base (pp, 95%)", "", "| Setting | " + " | ".join(TRANSFER) + " |",
          "|---" * (len(TRANSFER) + 1) + "|"]
    for s in SETTINGS:
        x = t[t.setting == s].set_index("rule")
        L.append(f"| {s} | " + " | ".join(f(x.loc[a, 'shift'], x.loc[a, 'shift_lo'], x.loc[a, 'shift_hi']) for a in TRANSFER) + " |")
    L += ["", "## Gain per booking (pp of riders reached per booking per 100 requests, 95%) and bookings per 100", "",
          "| Setting | " + " | ".join(TRANSFER) + " |", "|---" * (len(TRANSFER) + 1) + "|"]
    for s in ["base", *SETTINGS]:
        x = t[t.setting == s].set_index("rule")
        L.append(f"| {s} | " + " | ".join(f"{x.loc[a, 'gain_per_booking']:.2f} [{x.loc[a, 'gpb_lo']:.2f}, "
                                          f"{x.loc[a, 'gpb_hi']:.2f}] ({x.loc[a, 'bookings_per_100']:.1f})"
                                          for a in TRANSFER) + " |")
    if ts is not None:
        L += ["", f"Strict ({len(strict)} nights, every failed-check night out): (a) holds in "
              f"{sum(ts.groupby('setting').holds_a.all())} of 7 settings; (b) in {int(ts.groupby('setting').holds_b.first().sum())} of 7."]
    L += ["", "## Means over the used nights", "", means.round(2).to_markdown()]
    (out / "comparison_m8.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


def cmd_status(root=None):
    fp = m5.code_fingerprint()
    n = sum(done(s, r, ni, fp, root) for s, r, ni in runs())
    print(f"m8: {n} / {len(runs())} runs done")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "status", "compare"])
    ap.add_argument("--workers", type=int, default=MAX_WORKERS)
    ap.add_argument("--explained", default="", help="JSON list of [setting, night, rule] explained check failures")
    a = ap.parse_args()
    if a.cmd == "run":
        cmd_run(a.workers)
    elif a.cmd == "status":
        cmd_status()
    else:
        cmd_compare(explained=[tuple(x) for x in json.loads(a.explained or "[]")])
