"""
Phase 3, steps 3.1-3.2: zones v1, the location set, and the full travel-time matrix.

Zones v1 = zones v0 unchanged once three checks pass (every point zoned; O and
D margins each on the city-map fence ~24,056; no zone empty in both O and D).
Locations are the digitized bubbles themselves (D-16): requests start at O
bubbles, end at D bubbles, and vans may be anywhere in the set, so the engine
needs every ordered pair (deadhead D->O, pooling O->O and D->D), not only O->D.
The depot is the heaviest origin bubble in the Homewood campus zone Z08 (D-17,
ASSUMED: the real depot is not known).

Outputs: data/processed/zones_v1.csv, locations_v1.csv, locations_v1_meta.json,
         tt_locations_v1.csv
Run: .venv/bin/python src/scenario/locations.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

try:            # imported as the package scenario.*
    from . import travel_times
except ImportError:   # run as a script from src/scenario
    import travel_times

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
FENCE = 24_056          # city-map completed rides (D-01, D-09)
FENCE_TOL = 0.005
DEPOT_ZONE = "Z08"
RETRIEVED_V1 = "2026-10-01"   # demo-server fetch date of the v1 matrix (its cache files predate fetch-time stamps)


def check_zones(zones, pts):
    problems = []
    if pts.zone_id.isna().any():
        problems.append(f"{int(pts.zone_id.isna().sum())} points without a zone")
    for e in "OD":
        tot = pts.loc[pts.endpoint == e, "count_used"].sum()
        if abs(tot / FENCE - 1) > FENCE_TOL:
            problems.append(f"{e} margin {tot:.0f} is off the fence {FENCE}")
    by = pts.groupby(["zone_id", "endpoint"]).count_used.sum().unstack(fill_value=0)
    empty = by[(by.get("O", 0) == 0) & (by.get("D", 0) == 0)].index.tolist()
    if empty:
        problems.append(f"zones empty in O and D: {empty}")
    if set(zones.zone_id) != set(pts.zone_id):
        problems.append("zone ids in points and zones differ")
    return problems


def main():
    if not travel_times.IS_DEMO:    # tt_locations_v1 is the demo server's matrix; local times go to v2 (travel_times_v2.py)
        raise RuntimeError(f"locations.py builds the v1 matrix from the demo server, but OSRM_URL points to "
                           f"{travel_times.SERVER}; unset it to run this script")
    zones = pd.read_csv(PROCESSED / "zones_v0.csv")
    pts = pd.read_csv(PROCESSED / "zone_points_v0.csv")
    problems = check_zones(zones, pts)
    if problems:
        raise SystemExit("zones v0 fail the v1 checks: " + "; ".join(problems))
    zones.to_csv(PROCESSED / "zones_v1.csv", index=False)

    loc = (pts.rename(columns={"bubble_id": "loc_id", "count_used": "weight"})
              [["loc_id", "lat", "lon", "zone_id", "endpoint", "weight"]]
              .sort_values("loc_id").reset_index(drop=True))
    loc.to_csv(PROCESSED / "locations_v1.csv", index=False, float_format="%.6f")

    z8 = loc[(loc.zone_id == DEPOT_ZONE) & (loc.endpoint == "O")].sort_values(["weight", "loc_id"], ascending=[False, True])
    meta = {"version": "v1", "date": "2026-10-01", "n_locations": len(loc),
            "n_origin": int((loc.endpoint == "O").sum()), "n_destination": int((loc.endpoint == "D").sum()),
            "depot_loc": z8.loc_id.iloc[0], "depot_rule": "heaviest origin bubble in Z08 (D-17, ASSUMED)",
            "margins": {e: round(float(loc.loc[loc.endpoint == e, "weight"].sum()), 1) for e in "OD"}}
    (PROCESSED / "locations_v1_meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    tt = travel_times.matrix(loc, loc, "loc_id", "loc_id")
    tt.loc[tt.origin == tt.dest, ["seconds", "meters"]] = 0.0
    tt["source"] = "OSRM demo server, car, free-flow"
    fetched = tt.attrs.get("retrieved_utc")
    tt["retrieval_date"] = fetched[:10] if fetched else RETRIEVED_V1
    tt = tt.sort_values(["origin", "dest"]).reset_index(drop=True)
    tt.to_csv(PROCESSED / "tt_locations_v1.csv", index=False)

    # Matrix checks (3.2)
    n = len(loc)
    sec = tt.pivot(index="origin", columns="dest", values="seconds").loc[loc.loc_id, loc.loc_id].to_numpy()
    assert sec.shape == (n, n) and np.isfinite(sec).all() and (sec >= 0).all(), "matrix incomplete or negative"
    via = np.min(sec[:, :, None] + sec[None, :, :], axis=1)      # best two-leg time i -> k -> j
    tri = sec - via
    asym = np.abs(sec - sec.T)
    print(f"locations {n} (O {meta['n_origin']}, D {meta['n_destination']}); depot {meta['depot_loc']}")
    print(f"pairs {len(tt)}; median {np.median(sec[sec > 0]) / 60:.1f} min; max {sec.max() / 60:.1f} min")
    print(f"triangle: pairs beaten by a two-leg route by >60 s: {(tri > 60).sum()} (max {tri.max():.0f} s)")
    print(f"asymmetry |t_ij - t_ji|: median {np.median(asym):.0f} s, P90 {np.percentile(asym, 90):.0f} s, max {asym.max():.0f} s")
    print(f"co-located pairs (< 60 s apart, off-diagonal): {int(((sec < 60) & ~np.eye(n, dtype=bool)).sum())}")


if __name__ == "__main__":
    main()
