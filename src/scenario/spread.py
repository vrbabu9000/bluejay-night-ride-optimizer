"""
Dispersed geography, variant "dispersed_v1" (decision D-34): spread the coarse city-view map clusters over
nearby road locations, keeping the point-based reference (locations_v1 + tt_locations_v2) untouched.

Which points: every city-view bubble (19: 9 origin, 10 destination). Criterion = map resolution: the city view
is 4x coarser than the campus view (14.8 vs 3.7 m/px; position uncertainty 101 m vs ~28 m), so each city bubble
stands for a whole neighbourhood. The 169 campus-view points are kept as they are.

How (per coarse cluster, reproducible from one named seed stream "spread_sites"):
  1. draw candidate points uniformly over a disk of radius R = 400 m around the bubble (ASSUMED bound);
  2. snap each to the road network with the pinned local OSRM (/nearest); keep it only if the snap is <= 75 m,
     the snapped point is inside the approximate modelled region (convex hull of the 188 April points + 100 m;
     an approximation, NOT a verified service boundary), outside the campus-map frame (that area is already
     represented by campus-view bubbles), and >= 100 m from the cluster's other satellites;
  3. stop at K = 6 satellites; each carries weight / K, so the cluster's probability mass is preserved exactly.
Satellites are synthetic representations of positional uncertainty, not recovered April addresses.

Outputs (separate from the reference): data/processed/locations_dispersed_v1.csv,
tt_locations_dispersed_v1.csv (all ordered pairs over the 188 reference points + satellites),
dispersed_v1_provenance.json.
Run: .venv/bin/python src/scenario/spread.py     (needs the local OSRM server; answers are cached)
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.path import Path as MPath
from scipy.spatial import ConvexHull

try:
    from . import travel_times as tt
    from .zones import campus_frame
except ImportError:
    import travel_times as tt
    from zones import campus_frame

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
VARIANT = "dispersed_v1"
MASTER_SEED = 20261020                  # same master seed as generator_v2
SITE_SPAWN_KEY = (0, 0, 0, 13)          # (world, -, -, "spread_sites"); generator_v2 uses level ids >= 1
RADIUS_M, K, MIN_SEP_M, MAX_SNAP_M, HULL_BUFFER_M, MAX_TRIES = 400.0, 6, 100.0, 75.0, 100.0, 400
LAT0 = 39.32
M_PER_DEG_LAT = 111_320.0
M_PER_DEG_LON = 111_320.0 * math.cos(math.radians(LAT0))


def xy(lat, lon):
    return np.c_[(np.asarray(lon) + 76.62) * M_PER_DEG_LON, (np.asarray(lat) - LAT0) * M_PER_DEG_LAT]


def region_test(loc):
    """Inside the convex hull of the 188 April points, or within HULL_BUFFER_M of its boundary."""
    p = xy(loc.lat, loc.lon)
    hull = p[ConvexHull(p).vertices]
    poly = MPath(hull)
    edges = list(zip(hull, np.roll(hull, -1, axis=0)))

    def inside(lat, lon):
        q = xy([lat], [lon])[0]
        if poly.contains_point(q):
            return True
        for a, b in edges:
            ab, aq = b - a, q - a
            t = np.clip(aq @ ab / (ab @ ab), 0, 1)
            if np.hypot(*(q - (a + t * ab))) <= HULL_BUFFER_M:
                return True
        return False
    return inside


def build_sites():
    loc = pd.read_csv(PROCESSED / "locations_v1.csv")
    view = pd.read_csv(PROCESSED / "zone_points_v0.csv").set_index("bubble_id").view
    loc["view"] = loc.loc_id.map(view)
    coarse = loc[loc.view == "city"].sort_values("loc_id")
    south, north, west, east = campus_frame()
    in_region = region_test(loc)
    rng = np.random.default_rng(np.random.SeedSequence(MASTER_SEED, spawn_key=SITE_SPAWN_KEY))
    rows, rejects = [], {"snap": 0, "region": 0, "frame": 0, "separation": 0}
    for c in coarse.itertuples():
        kept, tries = [], 0
        while len(kept) < K:
            tries += 1
            if tries > MAX_TRIES:
                raise RuntimeError(f"{c.loc_id}: only {len(kept)} valid satellites after {MAX_TRIES} candidates")
            r, th = RADIUS_M * math.sqrt(rng.random()), 2 * math.pi * rng.random()   # uniform over the disk
            lat = c.lat + r * math.sin(th) / M_PER_DEG_LAT
            lon = c.lon + r * math.cos(th) / M_PER_DEG_LON
            n = tt.nearest(round(lat, 6), round(lon, 6))
            slat, slon = n["snapped_lat"], n["snapped_lon"]
            if n["snap_m"] > MAX_SNAP_M:
                rejects["snap"] += 1; continue
            if not in_region(slat, slon):
                rejects["region"] += 1; continue
            if south <= slat <= north and west <= slon <= east:
                rejects["frame"] += 1; continue
            q = xy([slat], [slon])[0]
            if any(np.hypot(*(q - xy([k["lat"]], [k["lon"]])[0])) < MIN_SEP_M for k in kept):
                rejects["separation"] += 1; continue
            kept.append({"loc_id": f"{c.loc_id}_s{len(kept) + 1}", "parent_loc": c.loc_id, "lat": round(slat, 6),
                         "lon": round(slon, 6), "zone_id": c.zone_id, "endpoint": c.endpoint,
                         "weight": c.weight / K, "offset_m": round(float(np.hypot(*(q - xy([c.lat], [c.lon])[0]))), 1),
                         "snap_m": round(n["snap_m"], 2), "road_name": n["road_name"] or ""})
        rows += kept
    sat = pd.DataFrame(rows)
    ref = loc.drop(columns="view").assign(parent_loc=loc.loc_id, offset_m=0.0, snap_m=np.nan, road_name="", is_satellite=False)
    sat["is_satellite"] = True
    return pd.concat([ref, sat], ignore_index=True), coarse.loc_id.tolist(), rejects


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    tt.set_server("http://localhost:5050")
    allpts, coarse, rejects = build_sites()
    cols = ["loc_id", "parent_loc", "is_satellite", "lat", "lon", "zone_id", "endpoint", "weight", "offset_m", "snap_m", "road_name"]
    allpts[cols].to_csv(PROCESSED / f"locations_{VARIANT}.csv", index=False, lineterminator="\n")
    m = tt.matrix(allpts, allpts, "loc_id", "loc_id")
    m.loc[m.origin == m.dest, ["seconds", "meters"]] = 0.0
    prov = json.loads((ROOT / "data" / "osrm" / "PROVENANCE.json").read_text())
    m["source"] = f"OSRM local v6.0.0, Geofabrik maryland-latest md5 {prov['md5'][:8]}, car, free-flow"
    m = m.sort_values(["origin", "dest"]).reset_index(drop=True)
    m.to_csv(PROCESSED / f"tt_locations_{VARIANT}.csv", index=False, lineterminator="\n")
    meta = {"variant": VARIANT, "decision": "D-34 (dispersed geography variant; reference geography unchanged)",
            "coarse_clusters": coarse, "criterion": "all city-view bubbles (map resolution 4x coarser than campus view)",
            "method": {"radius_m": RADIUS_M, "satellites_per_cluster": K, "min_separation_m": MIN_SEP_M,
                       "max_snap_m": MAX_SNAP_M, "region": f"convex hull of the 188 April points + {HULL_BUFFER_M:.0f} m (approximate, not a verified boundary)",
                       "frame_exclusion": "campus-map frame excluded (campus-view bubbles already represent it)",
                       "sampling": "uniform over the disk, snapped to the nearest road (pinned local OSRM)"},
            "status": {"radius_m": "ASSUMED (city-view clusters aggregate ~0.9 km grid cells at 60 px; library default, SECONDARY)",
                       "satellites_per_cluster": "design choice (bounded)"},
            "seed": {"master_seed": MASTER_SEED, "spawn_key": list(SITE_SPAWN_KEY), "stream": "spread_sites"},
            "rejected_candidates": rejects, "n_points": int(len(allpts)), "n_satellites": int(allpts.is_satellite.sum()),
            "osrm": {"image_tag": prov["image_tag"], "index_digest": prov["image_digest"].split("@")[1], "pbf_md5": prov["md5"],
                     "cache_folder": tt.CACHE_DIR.name},
            "inputs_sha256": {f: sha(PROCESSED / f) for f in ("locations_v1.csv", "zone_points_v0.csv", "tt_locations_v2.csv")},
            "outputs_sha256": {f: sha(PROCESSED / f) for f in (f"locations_{VARIANT}.csv", f"tt_locations_{VARIANT}.csv")}}
    (PROCESSED / f"{VARIANT}_provenance.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"{meta['n_satellites']} satellites for {len(coarse)} clusters; rejects {rejects}; matrix {len(m)} pairs; "
          f"network calls {tt.HTTP_CALLS}")


if __name__ == "__main__":
    main()
