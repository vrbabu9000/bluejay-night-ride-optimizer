"""
Directed road travel times from the public OSRM demo server (car profile,
free-flow; no traffic), cached to disk so reruns never re-query.

    zone matrix:   zones_v0 centroids x centroids      -> data/processed/tt_zones_v0.csv
    point matrix:  origin points x destination points  -> data/processed/tt_points_v0.csv

The demo server is for light use, so requests are chunked (<= 100 coordinates
each) and throttled. Values are OSRM seconds and metres; any congestion or
night-time speed factor is applied later as a named scenario parameter.
Run: .venv/bin/python src/scenario/travel_times.py
"""
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
CACHE = ROOT / "data" / "raw" / "osrm_cache"
BASE = "https://router.project-osrm.org/table/v1/driving/"
UA = {"User-Agent": "bluejay-course-project/0.1"}
CHUNK = 50


def table(src, dst):
    """src, dst: lists of (lat, lon). Returns (durations, distances) as nested lists."""
    coords = src + dst
    key = "_".join(f"{a:.5f},{b:.5f}" for a, b in coords)
    path = CACHE / f"table_{abs(hash(key)) % 10**12}_{len(src)}x{len(dst)}.json"
    if not path.exists():
        url = (BASE + ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coords)
               + f"?sources={';'.join(map(str, range(len(src))))}"
               + f"&destinations={';'.join(map(str, range(len(src), len(coords))))}"
               + "&annotations=duration,distance")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            d = json.load(r)
        if d.get("code") != "Ok":
            raise RuntimeError(d)
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"key": key, "durations": d["durations"], "distances": d["distances"]}))
        time.sleep(1.1)
    d = json.loads(path.read_text())
    return d["durations"], d["distances"]


def matrix(src_df, dst_df, src_id, dst_id):
    rows = []
    for i in range(0, len(src_df), CHUNK):
        s = src_df.iloc[i:i + CHUNK]
        for j in range(0, len(dst_df), CHUNK):
            t = dst_df.iloc[j:j + CHUNK]
            dur, dist = table(list(zip(s.lat, s.lon)), list(zip(t.lat, t.lon)))
            for a, sa in enumerate(s[src_id]):
                for b, tb in enumerate(t[dst_id]):
                    rows.append({"origin": sa, "dest": tb, "seconds": dur[a][b], "meters": dist[a][b]})
    return pd.DataFrame(rows)


def main():
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
