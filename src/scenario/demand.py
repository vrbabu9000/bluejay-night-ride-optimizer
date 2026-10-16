"""
Phase 3, step 3.3: the population demand model (gravity x IPF).

For every origin bubble o and destination bubble d:

    seed[o,d] = w_o * w_d * exp(-beta * t_od / 60)     (t_od = OSRM free-flow seconds)
    seed[o,d] = 0  if t_od < min_trip_s                 (structural zero, D-18)

IPF rescales rows and columns until the table's margins match the April
bubble weights (completed rides, D-01), so zone margins match too. The fit is
done at bubble level rather than zone level: it reproduces both margins and
keeps distance deterrence inside a zone (D-18). Targets that cannot be met
are reported in `diag`, never silently redistributed.

direction (D-19):
  month_average        targets = April bubble weights
  campus_outbound_6pm  origin weights in Z08 x 1.5, origin total renormalised;
                       destination targets unchanged (ASSUMED tilt)

Many tables fit the same margins; beta picks one of them (D-18 grid 0 / 0.1 / 0.2).
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
CAMPUS_ZONE, CAMPUS_TILT = "Z08", 1.5
TOL = 0.01            # config spatial.balance_tolerance
DIRECTIONS = ("month_average", "campus_outbound_6pm")


@lru_cache(maxsize=1)
def load_world():
    loc = pd.read_csv(PROCESSED / "locations_v1.csv")
    tt = pd.read_csv(PROCESSED / "tt_locations_v1.csv")
    sec = tt.pivot(index="origin", columns="dest", values="seconds").loc[loc.loc_id, loc.loc_id]
    return loc, sec


def targets(direction):
    loc, _ = load_world()
    o, d = loc[loc.endpoint == "O"], loc[loc.endpoint == "D"]
    wo = o.weight.to_numpy(float).copy()
    if direction == "campus_outbound_6pm":
        total = wo.sum()
        wo[(o.zone_id == CAMPUS_ZONE).to_numpy()] *= CAMPUS_TILT
        wo *= total / wo.sum()
    elif direction != "month_average":
        raise ValueError(f"unknown direction {direction!r}")
    return o, d, wo, d.weight.to_numpy(float)


@lru_cache(maxsize=16)
def _fit(beta_per_min, direction, min_trip_s):
    loc, sec = load_world()
    o, d, wo, wd = targets(direction)
    t = sec.loc[o.loc_id, d.loc_id].to_numpy()
    support = t >= min_trip_s
    T = np.where(support, np.outer(wo, wd) * np.exp(-beta_per_min * t / 60.0), 0.0)
    T *= wo.sum() / T.sum()

    unattainable_o = o.loc_id[~support.any(axis=1)].tolist()
    unattainable_d = d.loc_id[~support.any(axis=0)].tolist()
    converged, it = False, 0
    for it in range(1, 5001):
        r = T.sum(axis=1); T *= np.divide(wo, r, out=np.ones_like(r), where=r > 0)[:, None]
        c = T.sum(axis=0); T *= np.divide(wd, c, out=np.ones_like(c), where=c > 0)[None, :]
        ro = np.abs(T.sum(axis=1) / wo - 1)
        if ro.max() < 1e-9:
            converged = True
            break

    def rel(fit, target):
        return np.abs(fit / target - 1)

    fo, fd = T.sum(axis=1), T.sum(axis=0)
    zo = pd.Series(fo).groupby(o.zone_id.to_numpy()).sum() / pd.Series(wo).groupby(o.zone_id.to_numpy()).sum() - 1
    zd = pd.Series(fd).groupby(d.zone_id.to_numpy()).sum() / pd.Series(wd).groupby(d.zone_id.to_numpy()).sum() - 1
    oi, di = np.nonzero(T > 0)
    table = pd.DataFrame({"o_loc": o.loc_id.to_numpy()[oi], "d_loc": d.loc_id.to_numpy()[di],
                          "prob": T[oi, di] / T.sum(), "seconds": t[oi, di]})
    diag = {"beta_per_min": beta_per_min, "direction": direction, "min_trip_s": min_trip_s,
            "converged": bool(converged), "iterations": it, "tolerance": TOL,
            "max_rel_resid_o": float(rel(fo, wo).max()), "max_rel_resid_d": float(rel(fd, wd).max()),
            "zone_rel_resid_o": {k: float(abs(v)) for k, v in zo.items()},
            "zone_rel_resid_d": {k: float(abs(v)) for k, v in zd.items()},
            "unattainable_o": unattainable_o, "unattainable_d": unattainable_d,
            "structural_zero_pairs": int((~support).sum()), "pairs": int(support.size),
            "mean_direct_s": float((table.prob * table.seconds).sum())}
    diag["within_tolerance"] = bool(max(diag["max_rel_resid_o"], diag["max_rel_resid_d"]) < TOL)
    return table, diag


def fit_od(beta_per_min: float, direction: str, min_trip_s: float = 60.0):
    """Return (table, diag): table columns o_loc, d_loc, prob (sums to 1), seconds."""
    table, diag = _fit(float(beta_per_min), direction, float(min_trip_s))
    return table.copy(), dict(diag)


if __name__ == "__main__":
    for direction in DIRECTIONS:
        for beta in (0.0, 0.1, 0.2):
            _, g = fit_od(beta, direction)
            print(f"{direction:20s} beta {beta:.1f}: converged {g['converged']} in {g['iterations']:4d} it; "
                  f"max point resid O {g['max_rel_resid_o']:.1e} D {g['max_rel_resid_d']:.1e}; "
                  f"zero pairs {g['structural_zero_pairs']}/{g['pairs']}; mean direct {g['mean_direct_s'] / 60:.2f} min; "
                  f"unattainable {len(g['unattainable_o']) + len(g['unattainable_d'])}")
