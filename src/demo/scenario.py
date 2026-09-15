"""
Illustrative (DUMMY) scenario: ONE van, 5 ride requests around Homewood.
Points are chosen so that serving riders one-at-a-time in arrival order
(NAIVE) ping-pongs across campus, while a pooled/reordered route
(OPTIMIZED) traces a clean loop. Both are routed on real roads (OSRM),
so the distance difference is the visible proof optimization happened.
"""
import math

# van start / depot
CAMPUS          = (39.3290, -76.6200)

# request endpoints (lat, lon), spread W / E / N / S so naive crisscrosses
HAMPDEN         = (39.3268, -76.6360)  # far west
WYMAN           = (39.3255, -76.6295)  # west
REMINGTON       = (39.3200, -76.6300)  # southwest
WAVERLY         = (39.3290, -76.6070)  # far east
ABELL           = (39.3235, -76.6115)  # east
BARCLAY         = (39.3190, -76.6120)  # southeast
ST33            = (39.3315, -76.6155)  # north
OLD_GOUCHER     = (39.3150, -76.6165)  # south
CHARLES_VILLAGE = (39.3235, -76.6150)  # central

# arrival order R1..R5 deliberately alternates sides
REQUESTS = {
    "R1": {"spawn": 0,  "pickup": HAMPDEN,         "dropoff": WAVERLY},
    "R2": {"spawn": 3,  "pickup": ABELL,           "dropoff": REMINGTON},
    "R3": {"spawn": 6,  "pickup": WYMAN,           "dropoff": BARCLAY},
    "R4": {"spawn": 9,  "pickup": ST33,            "dropoff": OLD_GOUCHER},
    "R5": {"spawn": 12, "pickup": CHARLES_VILLAGE, "dropoff": HAMPDEN},
}

CAPACITY = 3  # optimized van may pool up to 3 riders


def _hav(a, b):
    R = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = math.radians(b[0] - a[0]); dl = math.radians(b[1] - a[1])
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def naive_stops():
    """One rider at a time, in arrival order: P1,D1,P2,D2,..."""
    stops = [("start", CAMPUS)]
    for rid, r in REQUESTS.items():
        stops.append((rid + "p", r["pickup"]))
        stops.append((rid + "d", r["dropoff"]))
    return stops


def optimized_stops():
    """Pooled nearest-neighbor with pickup-before-dropoff + capacity."""
    pos = CAMPUS
    onboard, remaining = [], list(REQUESTS.keys())
    stops = [("start", CAMPUS)]
    while remaining or onboard:
        cands = []
        if len(onboard) < CAPACITY:
            for rid in remaining:
                cands.append((_hav(pos, REQUESTS[rid]["pickup"]), rid + "p", rid, "p", REQUESTS[rid]["pickup"]))
        for rid in onboard:
            cands.append((_hav(pos, REQUESTS[rid]["dropoff"]), rid + "d", rid, "d", REQUESTS[rid]["dropoff"]))
        cands.sort(key=lambda c: c[0])
        _, label, rid, kind, pt = cands[0]
        stops.append((label, pt))
        pos = pt
        if kind == "p":
            onboard.append(rid); remaining.remove(rid)
        else:
            onboard.remove(rid)
    return stops


def bounds():
    pts = [CAMPUS] + [r["pickup"] for r in REQUESTS.values()] + [r["dropoff"] for r in REQUESTS.values()]
    lats = [p[0] for p in pts]; lons = [p[1] for p in pts]
    pad_la = (max(lats) - min(lats)) * 0.10
    pad_lo = (max(lons) - min(lons)) * 0.10
    return (min(lats) - pad_la, min(lons) - pad_lo), (max(lats) + pad_la, max(lons) + pad_lo)
