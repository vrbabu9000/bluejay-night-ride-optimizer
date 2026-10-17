"""
Road products from the local OSRM server (v2): directed travel times, the real route
shapes of scenario M, and where every location lands on the road network.

    data/processed/tt_locations_v2.csv     all ordered pairs of locations_v1.csv, columns as tt_locations_v1.csv
    data/processed/routes_M_v2.geojson     street geometry of the 30 trips in data/scenarios/ladder/M/requests.csv
    data/processed/locations_snap_v2.csv   per location: distance to the road, snapped point, road name

The server is the pinned local one (http://localhost:5050; map data, image and dates in
data/osrm/PROVENANCE.json). OSRM answers are cached in data/raw/osrm_cache/local_v6.0.0_ff90439c/ (image tag + map md5), so a
rerun makes no network calls and writes identical files; the number of real HTTP requests is printed
at the end. If the server is down this stops with an error: it never falls back to the demo server,
and the v1 files (demo server, 1 Oct) are not touched.

A van stops where a location lands on the road network (locations_snap_v2.csv), not at the digitized
coordinate. The plan's limit is 75 m; one location is over it (p04_b037, 94.9 m to Poole St), a
documented exception: docs/plans/osrm/log.md, step A2. The coordinate is not moved.
Run: cd src/scenario && ../../.venv/bin/python travel_times_v2.py
"""
import json
from email.utils import parsedate_to_datetime
from pathlib import Path

import numpy as np
import pandas as pd

try:            # imported as the package scenario.*
    from . import travel_times as t
except ImportError:   # run as a script from src/scenario
    import travel_times as t

ROOT = t.ROOT
PROCESSED = t.PROCESSED
LOCAL_URL = f"http://localhost:{t.LOCAL_PORT}"
LOCATIONS = PROCESSED / "locations_v1.csv"
REQUESTS_M = ROOT / "data" / "scenarios" / "ladder" / "M" / "requests.csv"
OUT_TT = PROCESSED / "tt_locations_v2.csv"
OUT_ROUTES = PROCESSED / "routes_M_v2.geojson"
OUT_SNAP = PROCESSED / "locations_snap_v2.csv"
SNAP_LIMIT_M = 75.0


def source_label(prov):
    """The `source` column: the pinned build, named from PROVENANCE.json."""
    version = prov["image_tag"].rsplit(":", 1)[-1]                          # v6.0.0
    extract = Path(prov["source_url"]).name.removesuffix(".osm.pbf")        # maryland-latest
    modified = parsedate_to_datetime(prov["http_last_modified"]).date().isoformat()
    profile = prov["profile"].removesuffix(".lua")                          # car
    return f"OSRM local {version}, Geofabrik {extract} (Last-Modified {modified}), {profile}, free-flow"


def build_matrix(loc, source):
    n = len(loc)
    tt = t.matrix(loc, loc, "loc_id", "loc_id")
    fetched = tt.attrs.get("retrieved_utc")
    if not fetched:
        raise RuntimeError("the cached table answer has no retrieval time; delete its file and rerun")
    diag = tt.origin == tt.dest
    not_zero = int(((tt.seconds[diag] != 0) | (tt.meters[diag] != 0)).sum())     # OSRM's own diagonal, before we set it
    tt.loc[diag, ["seconds", "meters"]] = 0.0
    tt["source"] = source
    tt["retrieval_date"] = fetched[:10]            # when the server was asked (kept in the cache), not today's date
    tt = tt.sort_values(["origin", "dest"]).reset_index(drop=True)
    vals = tt[["seconds", "meters"]].to_numpy(dtype=float)
    if len(tt) != n * n or tt[["origin", "dest"]].duplicated().any() or not np.isfinite(vals).all() or (vals < 0).any():
        raise ValueError("matrix is not complete, finite and non-negative; nothing written")
    return tt, not_zero


def build_routes(req):
    """One LineString per request, pickup -> drop-off, following the streets."""
    feats = []
    for r in req.itertuples(index=False):
        rt = t.route([(r.o_lat, r.o_lon), (r.d_lat, r.d_lon)])
        feats.append({"type": "Feature",
                      "properties": {"request_id": r.request_id, "duration_s": rt["duration_s"], "distance_m": rt["distance_m"]},
                      "geometry": {"type": "LineString", "coordinates": rt["coords"]}})
    return feats


def build_snap(loc):
    rows = []
    for r in loc.itertuples(index=False):
        s = t.nearest(r.lat, r.lon)
        rows.append({"loc_id": r.loc_id, "snap_m": round(s["snap_m"], 2), "snapped_lat": s["snapped_lat"],
                     "snapped_lon": s["snapped_lon"], "road_name": s["road_name"]})
    return pd.DataFrame(rows)


def write_geojson(feats, path, source):
    body = ",\n".join(json.dumps(f, separators=(",", ":")) for f in feats)       # one trip per line: readable diffs
    path.write_text('{"type":"FeatureCollection","source":' + json.dumps(source) + ',"features":[\n' + body + "\n]}\n")


def main():
    previous = t.SERVER
    t.set_server(LOCAL_URL)         # this script is the local server's; restored below for any caller in the same process
    calls0 = t.HTTP_CALLS
    try:
        prov = json.loads(t.PROVENANCE.read_text())
        source = source_label(prov)
        loc = pd.read_csv(LOCATIONS)
        if not loc.loc_id.is_unique:
            raise ValueError(f"{LOCATIONS.name}: loc_id is not unique")
        req = pd.read_csv(REQUESTS_M)
        print(f"server {t.SERVER}; cache {t.CACHE_DIR.relative_to(ROOT)}/; chunk {t.CHUNK}")
        print(f"source: {source}")

        tt, diag_not_zero = build_matrix(loc, source)     # all three are built before any is written
        feats = build_routes(req)
        snap = build_snap(loc)

        tt.to_csv(OUT_TT, index=False)
        write_geojson(feats, OUT_ROUTES, source)
        snap.to_csv(OUT_SNAP, index=False)
    finally:
        t.set_server(previous)

    off = tt.seconds[tt.origin != tt.dest]
    print(f"{OUT_TT.name}: {len(tt):,} rows ({loc.shape[0]} x {loc.shape[0]}); retrieval_date {tt.retrieval_date.iloc[0]}; "
          f"off-diagonal median {off.median() / 60:.1f} min, max {off.max() / 60:.1f} min; "
          f"diagonal values OSRM did not already return as 0: {diag_not_zero}")
    print(f"{OUT_ROUTES.name}: {len(feats)} routes; {sum(f['properties']['distance_m'] for f in feats) / 1000:.1f} km, "
          f"{sum(f['properties']['duration_s'] for f in feats) / 60:.1f} min in total")
    far = snap[snap.snap_m > SNAP_LIMIT_M]
    worst = snap.loc[snap.snap_m.idxmax()]
    print(f"{OUT_SNAP.name}: {len(snap)} rows; median snap {snap.snap_m.median():.1f} m; max {worst.snap_m:.1f} m "
          f"({worst.loc_id}, {worst.road_name or 'unnamed road'}); over {SNAP_LIMIT_M:.0f} m: {len(far)}"
          + (f" ({', '.join(far.loc_id)})" if len(far) else ""))
    print(f"HTTP requests (real network calls; cache hits not counted): {t.HTTP_CALLS - calls0}")


if __name__ == "__main__":
    main()
