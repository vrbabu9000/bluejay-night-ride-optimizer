#!/usr/bin/env python3
"""
Validate the local OSRM server against the OSRM demo-server travel-time matrix.

    .venv/bin/python infra/osrm/validate_local.py [--url http://localhost:5050]

What it does (about one second of server time):
  1. reads data/processed/locations_v1.csv (the 188 digitized bubbles) and
     data/processed/tt_locations_v1.csv (the demo-server matrix, 188 x 188 ordered pairs);
  2. sends ONE table request for all 188 points to the local server
     (annotations=duration,distance) and reads the snapping distance of every point;
  3. compares local and demo on every ordered pair; the ratio statistics leave out the diagonal
     (0 s against 0 s) and the few pairs whose demo time is 0 (a ratio is undefined there);
  4. writes data/osrm/validation_pairs.csv and data/osrm/validation_report.md;
  5. prints the acceptance checklist; exit code 0 = every check passed, 1 = a check failed,
     2 = the server could not be used.

Acceptance (docs/plans/osrm/plan.md, step A2): table code Ok; 188 x 188 with no nulls;
Pearson r (seconds) >= 0.95; median relative difference <= 10%; max snapping distance <= 75 m.
A failed check is reported with its numbers. This script never changes an OSRM setting, the map
data or an input file, and it never falls back to another server.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LOCATIONS = ROOT / "data" / "processed" / "locations_v1.csv"
DEMO_TABLE = ROOT / "data" / "processed" / "tt_locations_v1.csv"
OSRM_DIR = ROOT / "data" / "osrm"
PROVENANCE = OSRM_DIR / "PROVENANCE.json"
BUILD_LOG = OSRM_DIR / "build.log"
PAIRS_OUT = OSRM_DIR / "validation_pairs.csv"
REPORT_OUT = OSRM_DIR / "validation_report.md"

DEFAULT_URL = "http://localhost:5050"
N_LOCATIONS = 188

# Acceptance thresholds (plan A2).
MIN_PEARSON_S = 0.95
MAX_MEDIAN_REL = 0.10
MAX_SNAP_M = 75.0

SAME_ROUTE_TOL_M = 0.15    # distances within one 0.1 m rounding step (plus float noise) count as the same route length
STEP_S = 2.0               # the v6.0.0 car profile's per-node penalty for a traffic signal or stop sign
STEP_TOL_S = 0.12          # a time difference this close to a multiple of STEP_S counts as "in steps of 2 s"
N_WORST = 10
N_SNAP_LIST = 5


class ServerError(Exception):
    """The local server could not be used; nothing is compared and nothing is written."""


# ---------------------------------------------------------------------------------------------
# inputs and the one table request
# ---------------------------------------------------------------------------------------------
def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    loc = pd.read_csv(LOCATIONS)
    demo = pd.read_csv(DEMO_TABLE)
    if len(loc) != N_LOCATIONS or not loc.loc_id.is_unique:
        raise SystemExit(f"{LOCATIONS.name}: expected {N_LOCATIONS} unique loc_id rows, got {len(loc)}")
    if len(demo) != N_LOCATIONS ** 2 or demo[["origin", "dest"]].duplicated().any():
        raise SystemExit(f"{DEMO_TABLE.name}: expected {N_LOCATIONS ** 2} unique ordered pairs, got {len(demo)}")
    if set(demo.origin) != set(loc.loc_id) or set(demo.dest) != set(loc.loc_id):
        raise SystemExit(f"{DEMO_TABLE.name}: origin/dest ids differ from {LOCATIONS.name}")
    for col in ("lat", "lon"):      # the query prints 6 decimals: it must not round the input
        if not (loc[col].round(6) == loc[col]).all():
            raise SystemExit(f"{LOCATIONS.name}: {col} has more than 6 decimals")
    return loc, demo


def query_table(base_url: str, loc: pd.DataFrame, timeout: float = 120.0) -> dict:
    coords = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in zip(loc.lat, loc.lon))
    url = f"{base_url.rstrip('/')}/table/v1/driving/{coords}?annotations=duration,distance"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as err:          # OSRM sends a JSON error body with a 4xx status
        try:
            body = json.load(err)
        except ValueError:
            raise ServerError(f"{base_url} answered HTTP {err.code} without a JSON body") from err
    except (urllib.error.URLError, OSError) as err:
        raise ServerError(f"OSRM server {base_url} not reachable ({err}). Start it with: "
                          "docker compose -f infra/osrm/docker-compose.yml up -d") from err
    if body.get("code") != "Ok":
        raise ServerError(f"table request answered code={body.get('code')!r}: {body.get('message', '')}")
    return body


def tidy_pairs(loc: pd.DataFrame, demo: pd.DataFrame, body: dict) -> pd.DataFrame:
    """Long table: origin, dest, demo_s, local_s, demo_m, local_m (demo row order kept)."""
    n = len(loc)
    dur = np.array(body["durations"], dtype=float)      # a null (None) becomes NaN
    dist = np.array(body["distances"], dtype=float)
    if dur.shape != (n, n) or dist.shape != (n, n):
        raise ServerError(f"table is {dur.shape} (durations) and {dist.shape} (distances), expected {(n, n)}")
    ids = loc.loc_id.to_numpy()
    oi, di = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    local = pd.DataFrame({"origin": ids[oi.ravel()], "dest": ids[di.ravel()],
                          "local_s": dur.ravel(), "local_m": dist.ravel()})
    pairs = (demo.rename(columns={"seconds": "demo_s", "meters": "demo_m"})
                 [["origin", "dest", "demo_s", "demo_m"]]
                 .merge(local, on=["origin", "dest"], how="left", validate="one_to_one", indicator=True))
    if not (pairs["_merge"] == "both").all():       # how="left" keeps the demo row order
        raise ServerError("local and demo pairs do not line up")
    return pairs[["origin", "dest", "demo_s", "local_s", "demo_m", "local_m"]]


# ---------------------------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------------------------
def pearson(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.corrcoef(a, b)[0, 1])


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation of the average ranks (ties handled), so scipy is not needed."""
    return pearson(pd.Series(a).rank().to_numpy(), pd.Series(b).rank().to_numpy())


def agreement(demo: np.ndarray, local: np.ndarray) -> dict:
    """Local against demo over aligned pairs. Relative difference = |local - demo| / demo."""
    ok = np.isfinite(demo) & np.isfinite(local)
    d, lo = demo[ok], local[ok]
    diff = lo - d
    ad = np.abs(diff)
    pos = d > 0
    rel = ad[pos] / d[pos]
    return {
        "n": int(ok.sum()), "n_ratio": int(pos.sum()),
        "abs_median": float(np.median(ad)), "abs_p95": float(np.percentile(ad, 95)), "abs_max": float(ad.max()),
        "rel_median": float(np.median(rel)), "rel_p95": float(np.percentile(rel, 95)), "rel_max": float(rel.max()),
        "rel_signed_median": float(np.median(diff[pos] / d[pos])),
        "within_10": float((rel <= 0.10).mean()),
        "pearson": pearson(d, lo), "spearman": spearman(d, lo),
    }


def analyse(loc: pd.DataFrame, pairs: pd.DataFrame, body: dict) -> dict:
    n = len(loc)
    off = pairs[pairs.origin != pairs.dest].reset_index(drop=True)
    finite = np.isfinite(pairs.demo_s) & np.isfinite(pairs.local_s)
    res: dict = {
        "n_pairs": len(pairs), "n_diag": n, "n_off": len(off),
        "nulls": {c: int(pairs[c].isna().sum()) for c in ("demo_s", "local_s", "demo_m", "local_m")},
        "sec": agreement(off.demo_s.to_numpy(), off.local_s.to_numpy()),
        "met": agreement(off.demo_m.to_numpy(), off.local_m.to_numpy()),
        "pearson_all_s": pearson(pairs.demo_s[finite].to_numpy(), pairs.local_s[finite].to_numpy()),
        "n_zero_demo": int((off.demo_s == 0).sum()),
        "n_zero_both": int(((off.demo_s == 0) & (off.local_s == 0)).sum()),
        "diag_zero_local": bool((pairs.loc[pairs.origin == pairs.dest, ["local_s", "local_m"]] == 0).all().all()),
    }

    # How the differences are built: identical route length (same road path in practice) or not.
    dm = (off.local_m - off.demo_m).abs()
    ds = off.local_s - off.demo_s
    same = dm <= SAME_ROUTE_TOL_M
    pos = off.demo_s > 0
    d_same = ds[same]
    d_nz = d_same[d_same.abs() > 0.05]                    # same route, different time
    k = d_nz / STEP_S
    res["route"] = {
        "same_share": float(same.mean()),
        "same_seconds_share": float((ds.abs() < 0.05).mean()),
        "same_med_diff_s": float(d_same.median()),
        "same_med_rel": float((ds[same & pos] / off.demo_s[same & pos]).median()),
        "same_slower": float((d_same > 0.05).mean()), "same_equal": float((d_same.abs() <= 0.05).mean()),
        "same_faster": float((d_same < -0.05).mean()),
        "same_step_share": float((((k - k.round()).abs() * STEP_S) <= STEP_TOL_S).mean()) if len(d_nz) else float("nan"),
        "diff_share": float((~same).mean()),
        "diff_med_abs_s": float(ds[~same].abs().median()) if (~same).any() else float("nan"),
    }

    # The ten largest relative differences in seconds (ties broken by absolute difference).
    w = off[pos].copy()
    w["abs_s"] = (w.local_s - w.demo_s).abs()
    w["rel"] = w.abs_s / w.demo_s
    res["worst"] = w.sort_values(["rel", "abs_s", "origin", "dest"], ascending=[False, False, True, True]).head(N_WORST)
    ws = res["worst"][(res["worst"].local_m - res["worst"].demo_m).abs() <= SAME_ROUTE_TOL_M]   # time-only differences
    res["worst_same"] = {"n": len(ws), "max_abs_s": float(ws.abs_s.max()) if len(ws) else 0.0,
                         "max_demo_s": float(ws.demo_s.max()) if len(ws) else 0.0}

    # Snapping: the "distance" field of each source and destination waypoint (metres from the
    # input coordinate to the road). Sources and destinations are the same 188 points.
    src = np.array([s["distance"] for s in body["sources"]], dtype=float)
    dst = np.array([s["distance"] for s in body["destinations"]], dtype=float)
    snap = loc[["loc_id", "zone_id", "endpoint", "weight"]].copy()
    snap["snap_m"] = np.maximum(src, dst)
    snap["road"] = [s.get("name") or "(unnamed)" for s in body["sources"]]
    snap = snap.sort_values(["snap_m", "loc_id"], ascending=[False, True]).reset_index(drop=True)
    far = set(snap.loc[snap.snap_m > MAX_SNAP_M, "loc_id"])
    touch = off.origin.isin(far) | off.dest.isin(far)
    pos_rel = off[pos].assign(rel=lambda t: (t.local_s - t.demo_s).abs() / t.demo_s)
    touch_pos = pos_rel.origin.isin(far) | pos_rel.dest.isin(far)
    res["snap"] = {
        "table": snap, "max": float(snap.snap_m.iloc[0]), "max_id": snap.loc_id.iloc[0],
        "median": float(snap.snap_m.median()), "p95": float(snap.snap_m.quantile(0.95)),
        "src_dst_equal": bool(np.allclose(src, dst)),
        "n_over": {t: int((snap.snap_m > t).sum()) for t in (25, 50, MAX_SNAP_M)},
        "n_far": len(far), "far_weight_share": float(snap.loc[snap.snap_m > MAX_SNAP_M, "weight"].sum() / snap.weight.sum()),
        "n_far_pairs": int(touch.sum()),
        "far_rel_median": float(pos_rel.rel[touch_pos].median()) if touch_pos.any() else float("nan"),
        "other_rel_median": float(pos_rel.rel[~touch_pos].median()),
    }

    # Acceptance checks: (name, threshold, value, passed).
    r, med, sn = res["sec"]["pearson"], res["sec"]["rel_median"], res["snap"]
    nulls = res["nulls"]["local_s"] + res["nulls"]["local_m"]
    res["checks"] = [
        ("Table response code", "Ok", str(body["code"]), body["code"] == "Ok"),
        ("188 x 188, no nulls (local)", "188 x 188, 0 nulls", f"{n} x {n}, {nulls} nulls", nulls == 0),
        ("Pearson r, seconds", f">= {MIN_PEARSON_S}", f"{r:.4f}", r >= MIN_PEARSON_S),
        ("Median relative difference, seconds", f"<= {MAX_MEDIAN_REL:.0%}", f"{med:.2%}", med <= MAX_MEDIAN_REL),
        ("Max snapping distance", f"<= {MAX_SNAP_M:.0f} m", f"{sn['max']:.1f} m ({sn['max_id']})", sn["max"] <= MAX_SNAP_M),
    ]
    return res


# ---------------------------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------------------------
def pct(x: float, d: int = 2) -> str:
    return f"{100 * x:.{d}f}%"


def signed_pct(x: float, d: int = 2) -> str:
    return f"{100 * x:+.{d}f}%"


def provenance_facts() -> dict:
    facts = {"prov": {}, "osm_timestamp": "not found in build.log"}
    if PROVENANCE.exists():
        facts["prov"] = json.loads(PROVENANCE.read_text())
    if BUILD_LOG.exists():
        # build.log is appended on every build, so the last timestamp is the data now being served
        stamps = re.findall(r"\btimestamp: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", BUILD_LOG.read_text(errors="replace"))
        if stamps:
            facts["osm_timestamp"] = stamps[-1]
    return facts


def interpretation(res: dict, facts: dict, demo_date: str) -> list[str]:
    """Three lines: how close, why they differ, what this does not show (plus the snapping verdict)."""
    s, rt, sn = res["sec"], res["route"], res["snap"]
    side = "slower" if s["rel_signed_median"] > 0 else "faster"
    line1 = (f"Agreement is very close: Pearson r {s['pearson']:.4f}, median relative difference {pct(s['rel_median'])} "
             f"(P95 {pct(s['rel_p95'])}, worst pair {pct(s['rel_max'], 1)}), with the local server {pct(abs(s['rel_signed_median']))} "
             f"{side} at the median.")
    line2 = (f"Most of the difference is a small time shift on identical routes ({pct(rt['same_share'], 0)} of pairs; local a median "
             f"{rt['same_med_diff_s']:+.1f} s, in steps of {STEP_S:.0f} s, the v6.0.0 profile's signal/stop-sign penalty); the "
             f"{pct(rt['diff_share'], 0)} of pairs with a different route length are consistent with different OSM data dates (local: "
             f"Geofabrik extract, OSM timestamp {facts['osm_timestamp']}; demo: public server, matrix retrieved {demo_date}, map date "
             f"not published). This test cannot separate OSM data dates from OSRM-version or profile effects.")
    if sn["n_far"]:
        snap_txt = (f"The snapping check fails for {sn['n_far']} of {len(sn['table'])} locations (max {sn['max']:.1f} m at {sn['max_id']}, "
                    f"{pct(sn['far_weight_share'], 3)} of the April weight): that is the bubble's coordinate against the OSM roads, "
                    f"not a router setting, so it is reported for the team to decide, not tuned.")
    else:
        snap_txt = f"Snapping is within the {MAX_SNAP_M:.0f} m limit (max {sn['max']:.1f} m at {sn['max_id']})."
    line3 = ("This is agreement between two routers on free-flowing roads, not with real night traffic or van times "
             f"(Phase 6 calibrates that). {snap_txt}")
    return [line1, line2, line3]


def md_table(header: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out


def build_report(res: dict, facts: dict, demo: pd.DataFrame, base_url: str) -> str:
    prov, s, m, rt, sn = facts["prov"], res["sec"], res["met"], res["route"], res["snap"]
    demo_date = ", ".join(sorted(demo.retrieval_date.astype(str).unique()))
    demo_src = ", ".join(sorted(demo.source.astype(str).unique()))
    digest = str(prov.get("image_digest", "?")).split("@")[-1][:19]      # e.g. sha256:729461bcc9ae
    failed = [c for c in res["checks"] if not c[3]]
    run = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    L: list[str] = []
    L += ["# Local OSRM validation: local server against the demo-server matrix", ""]
    L += [f"Run {run} by `infra/osrm/validate_local.py` against `{base_url}`. Evidence label: DERIVED (comparison statistics "
          "computed from two routing-engine tables; neither is a measured van time).", ""]
    verdict = "PASS" if not failed else "FAIL"
    L += [f"**Result: {verdict}** ({len(res['checks']) - len(failed)} of {len(res['checks'])} acceptance checks pass)"
          + ("" if not failed else "; the failed check is reported with its numbers and no OSRM setting or data was changed (plan A2)") + ".", ""]

    L += ["## Acceptance checklist", ""]
    L += md_table(["Check", "Threshold", "Value", "Result"],
                  [[n, t, v, "PASS" if ok else "**FAIL**"] for n, t, v, ok in res["checks"]])

    L += ["", "## What was compared", ""]
    L += md_table(["", "Local", "Demo"], [
        ["Server", f"osrm-routed from image `{prov.get('image_tag', '?')}` (digest `{digest}`), algorithm "
                   f"{prov.get('algorithm', '?')}, profile {prov.get('profile', '?')}, started by `infra/osrm/docker-compose.yml`",
         "OSRM public demo server (router.project-osrm.org)"],
        ["Map data", f"Geofabrik maryland-latest, md5 `{str(prov.get('md5', '?'))[:8]}...`, HTTP Last-Modified "
                     f"{prov.get('http_last_modified', '?')}, downloaded {prov.get('downloaded_utc', '?')}; "
                     f"OSM data timestamp {facts['osm_timestamp']} (PBF header)", "not published by the server"],
        ["Travel times", "one table request, 188 points, `annotations=duration,distance`",
         f"`data/processed/tt_locations_v1.csv`: {demo_src}; retrieval_date {demo_date}"],
    ])
    L += ["", f"Note on dates: the matrix's own `retrieval_date` column is the date used here. Decision D-12 and `team_config.v2.json` "
          f"say 2026-09-29, which is the retrieval date of the v0 tables (`tt_zones_v0`, `tt_points_v0`); the 188 x 188 matrix "
          f"was fetched on {demo_date}.", ""]

    L += ["## Agreement", "",
          f"Ordered pairs: {res['n_pairs']:,} (diagonal {res['n_diag']}, off-diagonal {res['n_off']:,}). Nulls: local seconds "
          f"{res['nulls']['local_s']}, local meters {res['nulls']['local_m']}, demo seconds {res['nulls']['demo_s']}, demo meters "
          f"{res['nulls']['demo_m']}. The statistics below use the {res['n_off']:,} off-diagonal pairs; relative difference = "
          f"|local - demo| / demo, over the {s['n_ratio']:,} pairs with a demo time above 0 ({res['n_zero_demo']} pairs have demo time 0; "
          f"local is also 0 for {res['n_zero_both']} of them)"
          + ("" if m["n_ratio"] == s["n_ratio"] else f" and the {m['n_ratio']:,} pairs with a demo distance above 0 for meters") + ".", ""]
    L += md_table(["Statistic", "Seconds", "Meters"], [
        ["Median absolute difference", f"{s['abs_median']:.1f} s", f"{m['abs_median']:.1f} m"],
        ["P95 absolute difference", f"{s['abs_p95']:.1f} s", f"{m['abs_p95']:.1f} m"],
        ["Max absolute difference", f"{s['abs_max']:.1f} s", f"{m['abs_max']:.1f} m"],
        ["Median relative difference", pct(s["rel_median"]), pct(m["rel_median"])],
        ["P95 relative difference", pct(s["rel_p95"]), pct(m["rel_p95"])],
        ["Max relative difference", pct(s["rel_max"]), pct(m["rel_max"])],
        ["Median signed difference (local - demo) / demo", signed_pct(s["rel_signed_median"]), signed_pct(m["rel_signed_median"])],
        ["Pairs within 10% of demo", pct(s["within_10"]), pct(m["within_10"])],
        ["Pearson r", f"{s['pearson']:.4f}", f"{m['pearson']:.4f}"],
        ["Spearman rho", f"{s['spearman']:.4f}", f"{m['spearman']:.4f}"],
    ])
    L += ["", f"Including the {res['n_diag']} diagonal zeros, Pearson r (seconds) is {res['pearson_all_s']:.4f}. The local diagonal is "
              f"{'0' if res['diag_zero_local'] else 'NOT 0'} in both annotations.", ""]
    L += [f"Where the differences come from: {pct(rt['same_share'], 1)} of pairs have the same route length (distances within "
          f"{SAME_ROUTE_TOL_M} m). On those pairs the local time is slower for {pct(rt['same_slower'], 1)}, equal for "
          f"{pct(rt['same_equal'], 1)} and faster for {pct(rt['same_faster'], 1)}, a median {rt['same_med_diff_s']:+.1f} s "
          f"({signed_pct(rt['same_med_rel'])}); of those whose time differs, {pct(rt['same_step_share'], 0)} differ by a multiple of "
          f"{STEP_S:.0f} s (within {STEP_TOL_S} s), the size of the per-node penalty the v6.0.0 car profile gives a traffic signal or a "
          f"stop sign (give-way: 1 s; `lib/obstacles.lua` in the image). The other {pct(rt['diff_share'], 1)} of pairs have a different "
          f"route length (median time difference {rt['diff_med_abs_s']:.1f} s).", ""]

    L += ["## Snapping", "",
          f"Max {sn['max']:.1f} m at {sn['max_id']}; median {sn['median']:.1f} m, P95 {sn['p95']:.1f} m. Locations above 25 m: "
          f"{sn['n_over'][25]}, above 50 m: {sn['n_over'][50]}, above {MAX_SNAP_M:.0f} m: {sn['n_over'][MAX_SNAP_M]}. "
          f"(Sources and destinations are the same points; their snapping distances {'agree' if sn['src_dst_equal'] else 'DIFFER'}.)", ""]
    top = sn["table"].head(N_SNAP_LIST)
    L += md_table(["loc_id", "Snap (m)", "Road", "Zone", "Endpoint", "April weight"],
                  [[r.loc_id, f"{r.snap_m:.1f}", r.road, r.zone_id, r.endpoint, f"{r.weight:.1f}"] for r in top.itertuples()])
    if sn["n_far"]:
        L += ["", f"Effect on the comparison: the {sn['n_far_pairs']} pairs that touch a location above {MAX_SNAP_M:.0f} m have a median "
              f"relative difference of {pct(sn['far_rel_median'])} (all other pairs: {pct(sn['other_rel_median'])}); those locations carry "
              f"{pct(sn['far_weight_share'], 4)} of the total April weight ({sn['table'].weight.sum():,.0f})."]

    L += ["", f"## The {N_WORST} pairs with the largest relative difference (seconds)", ""]
    L += md_table(["#", "Origin", "Dest", "Demo (s)", "Local (s)", "Abs diff (s)", "Relative", "Demo (m)", "Local (m)"],
                  [[str(i), r.origin, r.dest, f"{r.demo_s:.1f}", f"{r.local_s:.1f}", f"{r.abs_s:.1f}", pct(r.rel, 1),
                    f"{r.demo_m:.1f}", f"{r.local_m:.1f}"] for i, r in enumerate(res["worst"].itertuples(), 1)])
    ws = res["worst_same"]
    L += ["", f"{ws['n']} of these {N_WORST} pairs have the same route length (a time-only difference of at most {ws['max_abs_s']:.1f} s, "
              f"on trips of at most {ws['max_demo_s']:.1f} s); the other {N_WORST - ws['n']} took a different route length "
              f"(the distance columns differ)."]

    L += ["", "## Interpretation", ""]
    L += [f"{i}. {t}" for i, t in enumerate(interpretation(res, facts, demo_date), 1)]
    L += ["", f"Files: `data/osrm/validation_pairs.csv` (origin, dest, demo_s, local_s, demo_m, local_m; all {res['n_pairs']:,} pairs). "
              "Reproduce: `.venv/bin/python infra/osrm/validate_local.py` with the server running.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--url", default=DEFAULT_URL, help=f"local OSRM base URL (default {DEFAULT_URL})")
    args = ap.parse_args()

    loc, demo = load_inputs()
    try:
        body = query_table(args.url, loc)
        pairs = tidy_pairs(loc, demo, body)
    except ServerError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2

    res = analyse(loc, pairs, body)
    pairs.to_csv(PAIRS_OUT, index=False)
    REPORT_OUT.write_text(build_report(res, provenance_facts(), demo, args.url) + "\n")

    print(f"{res['n_pairs']:,} ordered pairs; wrote {PAIRS_OUT.relative_to(ROOT)} and {REPORT_OUT.relative_to(ROOT)}")
    for name, thr, val, ok in res["checks"]:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {val} (threshold {thr})")
    print(f"Worst {N_WORST} relative differences (seconds):")
    for i, r in enumerate(res["worst"].itertuples(), 1):
        print(f"  {i:2d}. {r.origin} -> {r.dest}: demo {r.demo_s:.1f} s, local {r.local_s:.1f} s, "
              f"|diff| {r.abs_s:.1f} s ({pct(r.rel, 1)})")
    return 0 if all(c[3] for c in res["checks"]) else 1


if __name__ == "__main__":
    sys.exit(main())
