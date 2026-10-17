"""
Directed road travel times from an OSRM server (car profile, free-flow; no
traffic), cached to disk so reruns never re-query.

    zone matrix:   zones_v0 centroids x centroids      -> data/processed/tt_zones_v0.csv
    point matrix:  origin points x destination points  -> data/processed/tt_points_v0.csv

Which server: the environment variable OSRM_URL, or set_server(url) in code. The
default is the public demo server (https://router.project-osrm.org); every v0 and
v1 file was built from it, so existing scripts run as before. The local server
(http://localhost:5050, pinned image and map data in data/osrm/PROVENANCE.json)
feeds the v2 files, built by travel_times_v2.py.

Caches: one per server, so results from different servers never mix. The demo
server keeps data/raw/osrm_cache/ as it was (same folder, same file names, same
keys); any other server uses data/raw/osrm_cache/<slug>/. For http://localhost:5050 the slug is
local_<image tag>_<first 8 hex of the map-data md5>, both from PROVENANCE.json, i.e.
local_v6.0.0_ff90439c: a new map extract or image gets a fresh folder, so old travel times are
never served under a new data date. A cache file is named by a stable sha1 of the request
coordinates and keeps the key it was built from.

No fallback: if the chosen server cannot be reached the call raises RuntimeError.
Nothing is ever retried against another server.

The demo server is for light use, so its requests are chunked (50 x 50 coordinates)
and throttled; a local server takes 200 x 200 and is not throttled. Values are OSRM
seconds and metres; any congestion or night-time speed factor is applied later as a
named scenario parameter.
Run (demo server, v0 tables): .venv/bin/python src/scenario/travel_times.py
"""
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
CACHE = ROOT / "data" / "raw" / "osrm_cache"        # the demo server's cache (folder and files unchanged)
PROVENANCE = ROOT / "data" / "osrm" / "PROVENANCE.json"
DEMO_URL = "https://router.project-osrm.org"
LOCAL_PORT = 5050                                   # infra/osrm/docker-compose.yml (macOS holds 5000 for AirPlay)
LOOPBACK_HOSTS = ("localhost", "127.0.0.1", "::1")
UA = {"User-Agent": "bluejay-course-project/0.1"}
CHUNK_DEMO = 50                                     # demo: <= 100 coordinates per table request
CHUNK_LOCAL = 200                                   # local: osrm-routed --max-table-size 500

# Chosen server. Set by set_server() (called once below with OSRM_URL); read at call time.
SERVER = DEMO_URL
BASE = DEMO_URL + "/table/v1/driving/"              # kept: the table endpoint of the chosen server
CACHE_DIR = CACHE
CHUNK = CHUNK_DEMO
IS_DEMO = True
IS_LOCAL = False
HTTP_CALLS = 0                                      # network calls made by this process; cache hits are not counted


def _pinned():
    """Image tag and map-data md5 (first 8 hex) of the pinned local server, from data/osrm/PROVENANCE.json:
    ('v6.0.0', 'ff90439c'). Both name the cache folder, so a rebuild with new data never reuses old answers."""
    try:
        prov = json.loads(PROVENANCE.read_text())
        image, md5 = prov["image_tag"], prov["md5"]
    except (OSError, ValueError, KeyError):
        return "unpinned", "nodata"
    name = image.rsplit("/", 1)[-1]                 # osrm-backend:v6.0.0
    return (name.split(":", 1)[1] if ":" in name else "unpinned"), md5[:8]


def _slug(url, local):
    """Cache folder name of a non-demo server. The pinned local server (documented port) is
    local_<tag>_<data md5>; a loopback server on another port gets a port suffix, so two servers never share a folder."""
    u = urllib.parse.urlparse(url)
    if local:
        port = u.port or (443 if u.scheme == "https" else 80)
        tag, data = _pinned()
        slug = f"local_{tag}_{data}" + ("" if port == LOCAL_PORT else f"_port{port}")
    else:
        slug = f"{u.netloc}{u.path}"
    return re.sub(r"[^A-Za-z0-9._-]", "_", slug)


def set_server(url):
    """Choose the OSRM server for every later call; returns the URL as stored. Also sets the
    cache folder, the chunk size and the throttle (see the module docstring)."""
    global SERVER, BASE, CACHE_DIR, CHUNK, IS_DEMO, IS_LOCAL
    url = str(url).strip().rstrip("/")
    u = urllib.parse.urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise ValueError(f"OSRM server URL must look like http://host:port, got {url!r}")
    IS_DEMO = u.hostname == urllib.parse.urlparse(DEMO_URL).hostname
    IS_LOCAL = u.hostname in LOOPBACK_HOSTS
    SERVER = url
    BASE = url + "/table/v1/driving/"
    CACHE_DIR = CACHE if IS_DEMO else CACHE / _slug(url, IS_LOCAL)
    CHUNK = CHUNK_LOCAL if IS_LOCAL else CHUNK_DEMO
    return url


set_server(os.environ.get("OSRM_URL") or DEMO_URL)


def _get_json(url):
    """One HTTP GET to the chosen server, JSON back: the only place this module touches the network."""
    global HTTP_CALLS
    HTTP_CALLS += 1
    req = urllib.request.Request(url, headers=UA)
    try:
        if IS_LOCAL:    # loopback never goes through a proxy
            resp = urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=60)
        else:
            resp = urllib.request.urlopen(req, timeout=60)
        with resp as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:     # the server answered, but refused this request (e.g. TooBig, NoSegment)
        try:
            reply = json.load(e)
        except ValueError:
            reply = {"code": f"HTTP {e.code}", "message": str(e.reason)}
        raise RuntimeError(f"OSRM server {SERVER} refused the request: {reply}") from None
    except (urllib.error.URLError, OSError) as e:   # refused connection, DNS failure, timeout
        raise RuntimeError(f"OSRM server {SERVER} not reachable; see docs/technical/osrm_local.md") from e
    if d.get("code") != "Ok":
        raise RuntimeError(f"OSRM server {SERVER} replied: {d}")
    return d


def _cache_path(kind, key, suffix=""):
    return CACHE_DIR / f"{kind}_{hashlib.sha1(key.encode()).hexdigest()[:16]}{suffix}.json"


def _cached(path, key, url, parse):
    """The cache file if there is one; otherwise one network call, kept on disk (with the key it was
    built from, the server and the UTC time) and returned."""
    if path.exists():
        return json.loads(path.read_text())
    out = {"key": key, **parse(_get_json(url)), "server": SERVER,
           "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")        # write whole, then rename: an interrupted run leaves no half file
    tmp.write_text(json.dumps(out))
    os.replace(tmp, path)
    if IS_DEMO:
        time.sleep(1.1)
    return out


def _table_entry(src, dst):
    """The cached or fetched answer to one table request (src, dst: lists of (lat, lon))."""
    coords = src + dst
    # Demo keys stay at 5 decimals so the existing cache files keep hitting; other servers key at the 6 sent.
    f = ".5f" if IS_DEMO else ".6f"
    key = "_".join(f"{a:{f}},{b:{f}}" for a, b in coords)
    shape = f"{len(src)}x{len(dst)}"
    # A stable name (Python's hash() is salted per process, so the old names never hit on a rerun).
    path = _cache_path("table", key, f"_{shape}")
    if IS_DEMO and not path.exists():
        for old in CACHE.glob(f"table_*_{shape}.json"):     # files written under the old naming
            if json.loads(old.read_text()).get("key") == key:
                old.rename(path)
                break
    url = (BASE + ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coords)
           + f"?sources={';'.join(map(str, range(len(src))))}"
           + f"&destinations={';'.join(map(str, range(len(src), len(coords))))}"
           + "&annotations=duration,distance")
    return _cached(path, key, url, lambda d: {"durations": d["durations"], "distances": d["distances"]})


def table(src, dst):
    """src, dst: lists of (lat, lon). Returns (durations, distances) as nested lists."""
    d = _table_entry(src, dst)
    return d["durations"], d["distances"]


def matrix(src_df, dst_df, src_id, dst_id):
    """All ordered pairs src x dst as a DataFrame (origin, dest, seconds, meters). The latest UTC time at
    which one of the answers was fetched is kept in result.attrs['retrieved_utc'] (None for answers cached
    before times were recorded)."""
    rows, fetched = [], []
    for i in range(0, len(src_df), CHUNK):
        s = src_df.iloc[i:i + CHUNK]
        for j in range(0, len(dst_df), CHUNK):
            t = dst_df.iloc[j:j + CHUNK]
            d = _table_entry(list(zip(s.lat, s.lon)), list(zip(t.lat, t.lon)))
            fetched.append(d.get("retrieved_utc"))
            dur, dist = d["durations"], d["distances"]
            for a, sa in enumerate(s[src_id]):
                for b, tb in enumerate(t[dst_id]):
                    rows.append({"origin": sa, "dest": tb, "seconds": dur[a][b], "meters": dist[a][b]})
    out = pd.DataFrame(rows)
    out.attrs["retrieved_utc"] = max(fetched) if fetched and all(fetched) else None
    return out


def route(lat_lon_list):
    """Road route through the (lat, lon) points in order, with the street geometry.
    Returns dict(duration_s, distance_m, coords=[[lon, lat], ...])."""
    pts = [(float(a), float(b)) for a, b in lat_lon_list]
    if len(pts) < 2:
        raise ValueError("route() needs at least two (lat, lon) points")
    query = "overview=full&geometries=geojson"
    key = ";".join(f"{a:.6f},{b:.6f}" for a, b in pts) + "|" + query
    url = (f"{SERVER}/route/v1/driving/" + ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in pts) + "?" + query)
    d = _cached(_cache_path("route", key, f"_{len(pts)}wp"), key, url,
                lambda r: {"duration_s": r["routes"][0]["duration"], "distance_m": r["routes"][0]["distance"],
                           "coords": r["routes"][0]["geometry"]["coordinates"]})
    return {"duration_s": d["duration_s"], "distance_m": d["distance_m"], "coords": d["coords"]}


def nearest(lat, lon):
    """Where a point lands on the road network (OSRM /nearest, one result): the point a vehicle actually
    uses. Returns dict(snap_m, snapped_lat, snapped_lon, road_name); snap_m is the distance moved."""
    key = f"{lat:.6f},{lon:.6f}|number=1"
    url = f"{SERVER}/nearest/v1/driving/{lon:.6f},{lat:.6f}?number=1"
    d = _cached(_cache_path("nearest", key), key, url,
                lambda r: {"snap_m": r["waypoints"][0]["distance"], "snapped_lat": r["waypoints"][0]["location"][1],
                           "snapped_lon": r["waypoints"][0]["location"][0], "road_name": r["waypoints"][0].get("name", "")})
    return {k: d[k] for k in ("snap_m", "snapped_lat", "snapped_lon", "road_name")}


def main():
    if not IS_DEMO:     # these two files are the demo server's v0 tables (retrieved 29 Sep); never overwrite them with other data
        raise RuntimeError(f"main() rebuilds the v0 tables from the demo server, but the chosen server is {SERVER}; "
                           "unset OSRM_URL to run it. Local-server tables come from travel_times_v2.py.")
    zones = pd.read_csv(PROCESSED / "zones_v0.csv")
    zm = matrix(zones, zones, "zone_id", "zone_id")
    zm["source"] = "OSRM demo server, car, free-flow"; zm["retrieval_date"] = time.strftime("%Y-%m-%d")
    zm.to_csv(PROCESSED / "tt_zones_v0.csv", index=False)
    pts = pd.read_csv(PROCESSED / "zone_points_v0.csv")
    o, d = pts[pts.endpoint == "O"], pts[pts.endpoint == "D"]
    pm = matrix(o, d, "bubble_id", "bubble_id")
    pm["source"] = "OSRM demo server, car, free-flow"; pm["retrieval_date"] = time.strftime("%Y-%m-%d")
    pm.to_csv(PROCESSED / "tt_points_v0.csv", index=False)
    print("zone pairs", len(zm), "median min", round(zm.seconds.median() / 60, 1))
    print("point pairs", len(pm), "median min", round(pm.seconds.median() / 60, 1), "missing", int(pm.seconds.isna().sum()))


if __name__ == "__main__":
    main()
