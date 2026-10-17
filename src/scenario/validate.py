"""
Phase 3, step 3.7: generator validation (the Phase 3 exit-gate evidence).

  1. Population: IPF margins per fit, point and zone level (tolerance 1%).
  2. Sampling: 1,000 pooled base nights vs the April zone shares (reported, not forced).
  3. Party mean vs the D-08 shape (1.40) and the April mean (1.39, T4).
  4. Reproducibility: the ladder rebuilt from scratch reproduces FROZEN.json;
     grid base r00 and ladder M carry identical requests.
  5. Plausibility: direct times of sampled trips vs T6 and the observed ride quantiles.
  6. Patience placeholder: the abandonment share it implies under April's daily
     wait distributions, next to the reported cancel share (T2/T3).

Outputs: outputs/scenario/generator_validation.csv (+ printed summary)
Run: .venv/bin/python src/scenario/validate.py
"""
import filecmp
import json
import math
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

try:            # imported as the package scenario.*
    from .demand import DIRECTIONS, fit_od, load_world, ROOT
    from .generator import build_scenario, default_params, sample_requests
except ImportError:   # run as a script from src/scenario
    from demand import DIRECTIONS, fit_od, load_world, ROOT
    from generator import build_scenario, default_params, sample_requests

OUT = ROOT / "outputs" / "scenario"
NIGHTS = 1000


def population():
    rows = []
    for direction in DIRECTIONS:
        for beta in (0.0, 0.1, 0.2):
            _, g = fit_od(beta, direction)
            rows.append({"check": "population", "case": f"{direction}, beta {beta}",
                         "value": max(g["max_rel_resid_o"], g["max_rel_resid_d"],
                                      max(g["zone_rel_resid_o"].values()), max(g["zone_rel_resid_d"].values())),
                         "target": "< 0.01", "pass": g["within_tolerance"] and g["converged"]})
    return rows


def sampling():
    loc, _ = load_world()
    p = default_params()
    req = pd.concat([sample_requests(p, r) for r in range(NIGHTS)])
    rows, shares = [], []
    for e, col in (("O", "o_zone"), ("D", "d_zone")):
        april = loc[loc.endpoint == e].groupby("zone_id").weight.sum()
        april /= april.sum()
        synth = req[col].value_counts(normalize=True).reindex(april.index, fill_value=0)
        diff = (synth - april).abs()
        # binomial sampling SE of a share over len(req) draws, for scale
        se = np.sqrt(april * (1 - april) / len(req))
        rows.append({"check": "sampling", "case": f"zone {e} shares, {NIGHTS} nights x 30",
                     "value": float(diff.max()), "target": "report (max |synthetic - April|)",
                     "pass": bool((diff <= 4 * se + 1e-12).all())})
        shares.append(pd.DataFrame({"zone_id": april.index, "endpoint": e, "april_share": april.values,
                                    "synthetic_share": synth.values}))
    party = req.party.mean()
    rows.append({"check": "party", "case": "pooled mean party", "value": float(party),
                 "target": "1.40 (D-08 shape); April 1.39 (T4)", "pass": abs(party - 1.40) < 0.02})
    q = np.percentile(req.direct_s / 60, [10, 50, 90])
    for k, (v, obs) in enumerate(zip(q, (4.17, 10.2, 23.92))):
        rows.append({"check": "plausibility", "case": f"direct trip P{[10, 50, 90][k]} (min) vs observed ride",
                     "value": round(float(v), 2), "target": f"below observed {obs} (rides include detour, dwell, pooling)",
                     "pass": bool(v < obs)})
    return rows, pd.concat(shares), req


def reproducibility():
    rows = []
    frozen = json.loads((ROOT / "data" / "scenarios" / "FROZEN.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        for level, h in frozen.items():
            sj = json.loads((ROOT / "data" / "scenarios" / "ladder" / level / "scenario.json").read_text())
            if level == "S0":       # hand-written: re-hash the stored files
                continue
            sc = build_scenario(sj["params"], sj["replicate"], Path(tmp) / level)
            rows.append({"check": "reproducibility", "case": f"ladder {level} rebuilt", "value": sc["content_hash"][:16],
                         "target": h[:16], "pass": sc["content_hash"] == h})
    same = filecmp.cmp(ROOT / "data/scenarios/ladder/M/requests.csv", ROOT / "data/scenarios/grid/base/r00/requests.csv", shallow=False)
    rows.append({"check": "reproducibility", "case": "grid base r00 requests == ladder M requests", "value": same,
                 "target": True, "pass": same})
    return rows


def patience():
    """Implied abandonment P(patience < wait) per April day; wait ~ lognormal through the daily median and P90 (T3 table)."""
    d = pd.read_csv(ROOT / "outputs" / "insights" / "t03_daily_table.csv")
    d = d[d.date_or_hour.str.startswith("2026-04")]
    med = default_params()["patience"]["median_s"] / 60
    lam = math.log(2) / med
    z = np.linspace(-4, 4, 801)
    w = norm.pdf(z); w /= w.sum()
    implied = []
    for _, r in d.iterrows():
        mu, sig = math.log(r.wait_median), (math.log(r.wait_p90) - math.log(r.wait_median)) / 1.2816
        waits = np.exp(mu + sig * z)
        implied.append(float((w * (1 - np.exp(-lam * waits))).sum()))
    d = d.assign(implied_abandon=implied)
    r = np.corrcoef(d.implied_abandon, d.cancel_share)[0, 1]
    return [{"check": "patience", "case": f"exponential, median {med:.0f} min: mean implied abandonment over April days",
             "value": round(float(d.implied_abandon.mean()), 3),
             "target": f"<= reported cancel share {d.cancel_share.mean():.3f} (which also counts rebookings, Lyft hand-offs)",
             "pass": bool(d.implied_abandon.mean() <= d.cancel_share.mean())},
            {"check": "patience", "case": "correlation of implied abandonment with daily cancel share", "value": round(float(r), 2),
             "target": "> 0 (same direction as T3)", "pass": bool(r > 0)}]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s_rows, shares, req = sampling()
    rows = population() + s_rows + reproducibility() + patience()
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "generator_validation.csv", index=False)
    shares.to_csv(OUT / "zone_shares_synthetic_vs_april.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_colwidth", 70):
        print(res.to_string(index=False))
    print("ALL PASS" if res["pass"].all() else "FAILURES: " + ", ".join(res.loc[~res["pass"], "case"]))


if __name__ == "__main__":
    main()
