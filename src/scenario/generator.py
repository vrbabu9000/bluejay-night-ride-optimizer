"""
Phase 3, steps 3.4-3.5: sample one synthetic night and write it as a scenario.

    build_scenario(params, replicate, out_dir) -> scenario dict
        out_dir/requests.csv, fleet.csv, scenario.json   (contract: docs/technical/scenario_contract.md)

Each random component has its own stream, SeedSequence(master_seed,
spawn_key=(replicate, k)), so changing one ingredient (say patience) never
reshuffles another (say the O-D draws), and every dispatcher later plays the
identical night. The same params and replicate give byte-identical files.
"""
import copy
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

try:            # imported as the package scenario.*
    from .demand import fit_od, load_world, PROCESSED, ROOT
except ImportError:   # run as a script from src/scenario
    from demand import fit_od, load_world, PROCESSED, ROOT

COMPONENTS = {"count": 0, "times": 1, "od": 2, "party": 3, "patience": 4, "fleet": 5}
REQ_COLS = ["request_id", "t_request_s", "o_loc", "d_loc", "o_zone", "d_zone",
            "o_lat", "o_lon", "d_lat", "d_lon", "party", "patience_s", "direct_s"]
FLEET_COLS = ["van_id", "start_loc", "lat", "lon", "capacity", "shift_start_s", "shift_end_s"]

LABELS = {   # evidence label and decision for each parameter
    "window_s": "DERIVED (D-05)", "n_vans": "DERIVED (D-06)", "n_requests": "DERIVED (D-06); ladder/grid levels are design choices",
    "capacity": "ASSUMED (D-22)", "start_rule": "ASSUMED (D-07, D-17)", "count_rule": "Design choice (D-20)",
    "arrivals": "ASSUMED (D-20)", "burst_share": "ASSUMED (D-20)", "burst_window_s": "ASSUMED (D-20)",
    "beta_per_min": "ASSUMED grid (D-18)", "direction": "ASSUMED (D-19)", "min_trip_s": "Design choice (D-18)",
    "party_probs": "mean DERIVED, shape ASSUMED (D-08)", "patience": "ASSUMED placeholder, calibrated in Phase 6 (D-21)",
    "tt_multiplier": "ASSUMED placeholder, calibrated in Phase 6 (D-12)", "pickup_dwell_s": "ASSUMED placeholder (Phase 6)",
    "dropoff_dwell_s": "ASSUMED placeholder (Phase 6)", "wait_limit_s": "PROVISIONAL (D-04)", "ride_limit_s": "PROVISIONAL (D-04)",
    "spatial_population": "The maps count completed rides (D-01); using them for all requests assumes cancelled requests come from the same places (ASSUMED)",
}


def default_params():
    """Base cell = scenario M: 18:00-19:00, 5 vans, 30 requests."""
    return {"cell": "base", "master_seed": 20261001, "window_s": 3600, "n_vans": 5, "capacity": 4,
            "start_rule": "hotspot", "n_requests": 30, "count_rule": "fixed", "arrivals": "poisson",
            "burst_share": 0.4, "burst_window_s": 600, "beta_per_min": 0.1, "direction": "month_average",
            "min_trip_s": 60, "party_probs": {"1": 0.72, "2": 0.19, "3": 0.06, "4": 0.03},
            "patience": {"dist": "exponential", "median_s": 720}, "tt_multiplier": 1.0,
            "pickup_dwell_s": 30, "dropoff_dwell_s": 30, "wait_limit_s": 1200, "ride_limit_s": 1500}


def stream(params, replicate, component):
    ss = np.random.SeedSequence(params["master_seed"], spawn_key=(replicate, COMPONENTS[component]))
    return np.random.default_rng(ss)


def sample_requests(p, replicate):
    loc, _ = load_world()
    li = loc.set_index("loc_id")
    W = p["window_s"]

    rng = stream(p, replicate, "count")
    n = int(p["n_requests"]) if p["count_rule"] == "fixed" else int(rng.poisson(p["n_requests"]))
    if p["count_rule"] not in ("fixed", "poisson"):
        raise ValueError(p["count_rule"])

    rng = stream(p, replicate, "times")
    if p["arrivals"] == "poisson":          # a Poisson process given n = uniform order statistics
        t = rng.uniform(0, W, n)
    elif p["arrivals"] == "burst":
        k = int(round(p["burst_share"] * n))
        t = np.concatenate([rng.uniform(0, p["burst_window_s"], k), rng.uniform(0, W, n - k)])
    else:
        raise ValueError(p["arrivals"])
    t = np.minimum(np.floor(np.sort(t)), W - 1).astype(int)

    table, _ = fit_od(p["beta_per_min"], p["direction"], p["min_trip_s"])
    cdf = np.cumsum(table.prob.to_numpy())
    idx = np.minimum(np.searchsorted(cdf, stream(p, replicate, "od").random(n) * cdf[-1], side="right"), len(table) - 1)
    o, d = table.o_loc.to_numpy()[idx], table.d_loc.to_numpy()[idx]

    sizes = sorted(p["party_probs"], key=int)
    pr = np.array([p["party_probs"][s] for s in sizes], float)
    party = stream(p, replicate, "party").choice([int(s) for s in sizes], size=n, p=pr / pr.sum())

    pat = p["patience"]
    if pat["dist"] != "exponential":
        raise ValueError(pat["dist"])
    patience = np.maximum(1, np.round(stream(p, replicate, "patience").exponential(pat["median_s"] / math.log(2), n))).astype(int)

    req = pd.DataFrame({"t_request_s": t, "o_loc": o, "d_loc": d, "party": party, "patience_s": patience})
    req["request_id"] = [f"R{i + 1:03d}" for i in range(n)]
    req["o_zone"], req["d_zone"] = li.zone_id.loc[o].to_numpy(), li.zone_id.loc[d].to_numpy()
    req["o_lat"], req["o_lon"] = li.lat.loc[o].to_numpy(), li.lon.loc[o].to_numpy()
    req["d_lat"], req["d_lon"] = li.lat.loc[d].to_numpy(), li.lon.loc[d].to_numpy()
    req["direct_s"] = table.seconds.to_numpy()[idx]
    return req[REQ_COLS]


def build_fleet(p):
    loc, _ = load_world()
    meta = json.loads((PROCESSED / "locations_v1_meta.json").read_text())
    if p["start_rule"] == "hotspot":
        ranked = loc[loc.endpoint == "O"].sort_values(["weight", "loc_id"], ascending=[False, True]).loc_id.tolist()
        starts = [ranked[i % len(ranked)] for i in range(p["n_vans"])]
    elif p["start_rule"] == "depot":
        starts = [meta["depot_loc"]] * p["n_vans"]
    else:
        raise ValueError(p["start_rule"])
    li = loc.set_index("loc_id")
    return pd.DataFrame({"van_id": [f"V{i + 1:02d}" for i in range(p["n_vans"])], "start_loc": starts,
                         "lat": li.lat.loc[starts].to_numpy(), "lon": li.lon.loc[starts].to_numpy(),
                         "capacity": p["capacity"], "shift_start_s": 0, "shift_end_s": p["window_s"]})[FLEET_COLS]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _csv_bytes(df):
    df = df.copy()
    for c in df.columns:
        if c.endswith(("lat", "lon")):
            df[c] = df[c].round(6)
    return df.to_csv(index=False, lineterminator="\n").encode()


def code_version():
    try:
        rev = subprocess.run(["git", "describe", "--always", "--dirty"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        return rev or "unknown"
    except OSError:
        return "unknown"


def write_scenario(requests, fleet, params, replicate, out_dir, extra=None):
    """Write the three files; the content hash covers both CSVs and the canonical params + replicate."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rb, fb = _csv_bytes(requests), _csv_bytes(fleet)
    (out / "requests.csv").write_bytes(rb)
    (out / "fleet.csv").write_bytes(fb)
    canon = json.dumps({"params": params, "replicate": replicate}, sort_keys=True, separators=(",", ":")).encode()
    sc = {"params": params, "replicate": replicate,
          "seeds": {"master_seed": params["master_seed"],
                    "spawn_keys": {c: [replicate, k] for c, k in COMPONENTS.items()}},
          "inputs": {"locations_v1.csv": _sha(PROCESSED / "locations_v1.csv"),
                     "tt_locations_v1.csv": _sha(PROCESSED / "tt_locations_v1.csv")},
          "content_hash": hashlib.sha256(rb + fb + canon).hexdigest(),
          "code_version": code_version(),
          "summary": {"requests": len(requests), "passengers": int(requests.party.sum()) if len(requests) else 0,
                      "vans": len(fleet), "rho_requests_per_van_hour": round(len(requests) / len(fleet) / (params["window_s"] / 3600), 2)},
          "labels": LABELS}
    if extra:
        sc.update(extra)
    (out / "scenario.json").write_text(json.dumps(sc, indent=2) + "\n")
    return sc


def build_scenario(params, replicate, out_dir):
    p = default_params()
    p.update(copy.deepcopy(params))
    return write_scenario(sample_requests(p, replicate), build_fleet(p), p, replicate, out_dir)


if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "scenarios" / "scratch"
    sc = build_scenario(default_params(), 0, out)
    print(out, sc["content_hash"][:16], sc["summary"])
