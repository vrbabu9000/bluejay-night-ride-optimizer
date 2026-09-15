"""
Tiny OSRM client: given ordered waypoints, return the REAL road route
(geometry that follows streets) plus total distance and duration.
Uses the public OSRM demo server and caches responses to disk so reruns
don't re-hit the API.
"""
import os, json, urllib.request

CACHE = os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "osrm_cache.json")
BASE = "https://router.project-osrm.org/route/v1/driving/"


def _load():
    try:
        with open(CACHE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(c):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w") as f:
        json.dump(c, f)


def route(waypoints):
    """waypoints: list of (lat, lon). Returns dict:
       {geometry: [[lat,lon],...] following roads, distance: m, duration: s}."""
    key = ";".join(f"{lat:.5f},{lon:.5f}" for lat, lon in waypoints)
    cache = _load()
    if key in cache:
        return cache[key]
    coords = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in waypoints)  # OSRM wants lon,lat
    url = f"{BASE}{coords}?overview=full&geometries=geojson"
    with urllib.request.urlopen(url, timeout=25) as r:
        d = json.load(r)
    if d.get("code") != "Ok":
        raise RuntimeError(f"OSRM: {d.get('code')} {d.get('message','')}")
    rt = d["routes"][0]
    out = {
        "geometry": [[c[1], c[0]] for c in rt["geometry"]["coordinates"]],  # -> [lat,lon]
        "distance": rt["distance"],
        "duration": rt["duration"],
    }
    cache[key] = out
    _save(cache)
    return out
