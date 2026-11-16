"""
M4 check 2 and 5 (plan v2): do the 30 L6 nights per pattern follow the recipe, and does one night look sane on a map?

Compares pooled draws with the recipe they were drawn from (not with April; calibration is later):
party-size shares vs spec §3.3; origin- and destination-zone shares vs the O-D table's marginals; latent draws vs
their stated distributions. Writes outputs/scenario/l6_check.md and outputs/scenario/l6_map_base_r00.png, and prints
a digest of the frozen L6 hashes for the tracked build note.

Run: .venv/bin/python src/scenario/check_l6.py
"""
import hashlib
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from . import generator_v2 as g
except ImportError:
    import generator_v2 as g

OUT = g.ROOT / "outputs" / "scenario"
L6 = g.OUT / "L6"


def pooled(cell):
    req = pd.concat([pd.read_csv(f / "requests.csv") for f in sorted((L6 / cell).glob("r*"))])
    lat = pd.concat([pd.read_csv(f / "latent.csv") for f in sorted((L6 / cell).glob("r*"))])
    return req, lat


def zone_margins():
    t = g.od_table("base")
    loc = g.world()[0]
    o = t.assign(z=loc.zone_id.reindex(t.o_loc).to_numpy()).groupby("z").prob.sum()
    d = t.assign(z=loc.zone_id.reindex(t.d_loc).to_numpy()).groupby("z").prob.sum()
    return o / o.sum(), d / d.sum()


def rows_for(cell):
    req, lat = pooled(cell)
    n = len(req)
    rows = []
    sh = req.party.value_counts(normalize=True).reindex(sorted(g.PARTY_P), fill_value=0)
    for k, p in g.PARTY_P.items():
        se = math.sqrt(p * (1 - p) / n)
        rows.append((cell, f"party = {k} share", p, sh[k], (sh[k] - p) / se))
    o_exp, d_exp = zone_margins()
    for side, exp, col in (("origin", o_exp, "o_zone"), ("destination", d_exp, "d_zone")):
        got = req[col].value_counts(normalize=True).reindex(exp.index, fill_value=0)
        z = (got - exp) / np.sqrt(exp * (1 - exp) / n)
        worst = z.abs().idxmax()
        rows.append((cell, f"{side} zone share, largest |z| ({worst})", exp[worst], got[worst], z[worst]))
        chi2 = float((((got - exp) ** 2) / exp).sum() * n)
        rows.append((cell, f"{side} zones chi-square (df {len(exp) - 1})", len(exp) - 1, chi2, float("nan")))
    rows.append((cell, "patience median (s)", 1080, float(lat.patience_s.median()), float("nan")))
    rows.append((cell, "Lyft delay median (s)", 480, float(lat.lyft_delay_s.median()), float("nan")))
    rows.append((cell, "Lyft delay P90 (s)", 900, float(lat.lyft_delay_s.quantile(0.9)), float("nan")))
    for c in ("noshow_u", "consent_u"):
        rows.append((cell, f"{c} mean", 0.5, float(lat[c].mean()), (lat[c].mean() - 0.5) / math.sqrt(1 / 12 / n)))
    rows.append((cell, "direct van time median (s, matrix)", float("nan"), float(req.direct_s.median()), float("nan")))
    return rows


def draw_map():
    loc = g.world()[0]
    req = pd.read_csv(L6 / "base_5" / "r00" / "requests.csv")
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.scatter(loc.lon, loc.lat, s=4, c="#cccccc", label="188 demand points")
    colors = ("#1f5fa8", "#d9822b", "#3a8f4f")
    for h, c in enumerate(colors):
        r = req[req.t_request_s // 3600 == h]
        ax.scatter(loc.lon.reindex(r.o_loc), loc.lat.reindex(r.o_loc), s=14, c=c,
                   label=f"pickups {18 + h}:00–{19 + h}:00 ({len(r)})")
    d = loc.loc[g.DEPOT]
    ax.scatter([d.lon], [d.lat], marker="s", s=60, c="black", label="depot (5 vans)")
    ax.set_title("L6 base night r00: where the 168 requests start")
    ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect(1 / math.cos(math.radians(39.3)))
    ax.legend(loc="lower left", fontsize=8, frameon=False)
    fig.tight_layout()
    path = OUT / "l6_map_base_r00.png"
    fig.savefig(path, dpi=150)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [r for cell in ("base_5", "high_5") for r in rows_for(cell)]
    df = pd.DataFrame(rows, columns=["cell", "check", "recipe", "observed", "z"])
    frozen = json.loads((g.OUT / "FROZEN_v2_L6.json").read_text())
    l6 = {k: v for k, v in sorted(frozen.items()) if k.startswith("L6/")}
    digest = hashlib.sha256(json.dumps(l6, sort_keys=True).encode()).hexdigest()
    md = ["# L6 build check (M4, D-59)", "", f"Frozen L6 entries: {len(l6)}; digest of the sorted L6 hash map: "
          f"`{digest}`", "", "Pooled over 30 nights per pattern (base_6 has the same draws as base_5).", "",
          "| cell | check | recipe | observed | z |", "|---|---|---|---|---|"]
    fmt = lambda x: "" if isinstance(x, float) and math.isnan(x) else f"{x:.4g}"
    md += [f"| {r.cell} | {r.check} | {fmt(r.recipe)} | {fmt(r.observed)} | {fmt(r.z)} |" for r in df.itertuples()]
    (OUT / "l6_check.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print("map:", draw_map())


if __name__ == "__main__":
    main()
