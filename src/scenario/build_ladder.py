"""
Phase 3, step 3.5: the scale ladder S0 -> L, and the frozen hashes.

    S0    1 van,  2 requests  hand-written (every leg time listed in scenario.json for the G2 hand-check)
    S1    1 van,  6 requests  small enough for brute force in Phase 5
    S2    3 vans, 15 requests first multi-van pooling
    M     5 vans, 30 requests the base scenario ("as served", rho 6) - FROZEN
    M60   5 vans, 60 requests "as requested" stress (rho 12)
    L170  27 vans, 170 requests real density, "as served"
    L300  27 vans, 300 requests real density, between served and requested

All sampled levels use replicate 0 of their own cell. FROZEN.json records each
content hash; a later rebuild must reproduce it exactly (tests/test_scenario.py).

Run: .venv/bin/python src/scenario/build_ladder.py
"""
import json

import pandas as pd

try:            # imported as the package scenario.*
    from .demand import load_world, ROOT
    from .generator import REQ_COLS, build_fleet, build_scenario, default_params, write_scenario
except ImportError:   # run as a script from src/scenario
    from demand import load_world, ROOT
    from generator import REQ_COLS, build_fleet, build_scenario, default_params, write_scenario

OUT = ROOT / "data" / "scenarios" / "ladder"
LEVELS = {"S1": {"n_vans": 1, "n_requests": 6}, "S2": {"n_vans": 3, "n_requests": 15},
          "M": {}, "M60": {"n_requests": 60},
          "L170": {"n_vans": 27, "n_requests": 170}, "L300": {"n_vans": 27, "n_requests": 300}}


def build_s0():
    """One van at the depot; two compatible requests (same corridor, Charles Village -> University Pkwy)."""
    loc, sec = load_world()
    p = default_params()
    p.update({"cell": "S0", "n_vans": 1, "n_requests": 2, "start_rule": "depot", "count_rule": "hand",
              "arrivals": "hand", "patience": {"dist": "hand", "median_s": None}})

    def top(zone, end, k):
        return loc[(loc.zone_id == zone) & (loc.endpoint == end)].sort_values(["weight", "loc_id"], ascending=[False, True]).loc_id.iloc[k]

    o1, o2, d1, d2 = top("Z02", "O", 0), top("Z02", "O", 1), top("Z05", "D", 0), top("Z05", "D", 1)
    li = loc.set_index("loc_id")
    req = pd.DataFrame({"request_id": ["R001", "R002"], "t_request_s": [60, 120], "o_loc": [o1, o2], "d_loc": [d1, d2],
                        "party": [1, 2], "patience_s": [3600, 3600]})
    for e in "od":
        ids = req[f"{e}_loc"]
        req[f"{e}_zone"], req[f"{e}_lat"], req[f"{e}_lon"] = li.zone_id.loc[ids].values, li.lat.loc[ids].values, li.lon.loc[ids].values
    req["direct_s"] = [sec.at[o1, d1], sec.at[o2, d2]]
    fleet = build_fleet(p)
    depot = fleet.start_loc.iloc[0]
    legs = [(depot, o1), (o1, o2), (o2, d1), (d1, d2), (o2, d2), (o1, d1), (d1, o2), (d2, d1)]
    extra = {"hand_check": {
        "purpose": "G2 hand-check: one van, two compatible requests; every leg needed for a by-hand schedule",
        "leg_seconds": {f"{a}->{b}": float(sec.at[a, b]) for a, b in legs},
        "dwell_s": {"pickup": p["pickup_dwell_s"], "dropoff": p["dropoff_dwell_s"]}}}
    return write_scenario(req[REQ_COLS], fleet, p, 0, OUT / "S0", extra)


def main():
    frozen = {"S0": build_s0()["content_hash"]}
    for name, over in LEVELS.items():
        p = default_params()
        p.update({"cell": name, **over})
        sc = build_scenario(p, 0, OUT / name)
        frozen[name] = sc["content_hash"]
        print(f"{name:5s} vans {sc['summary']['vans']:2d} requests {sc['summary']['requests']:3d} "
              f"passengers {sc['summary']['passengers']:3d} rho {sc['summary']['rho_requests_per_van_hour']:5.2f}  {sc['content_hash'][:16]}")
    # Flat {level: content_hash}, as in the scenario contract; frozen 2026-10-01 (decision log D-20)
    (ROOT / "data" / "scenarios" / "FROZEN.json").write_text(json.dumps(frozen, indent=2) + "\n")
    print("S0 hand-written;", frozen["S0"][:16])


if __name__ == "__main__":
    main()
