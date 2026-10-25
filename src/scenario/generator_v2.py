"""
Phase 3C: scenario generator v2 (scenario_spec.md v0.2), validation levels L1-L5.

A scenario holds INPUTS only (requests, latent per-request draws, vehicle
availability); no policy-dependent outcome is pre-assigned. For L1-L4 a
hand-check sheet gives the expected outcome under the simple, unambiguous
situations those levels are designed for, so the Phase 4 simulator can be
checked to the second.

Every random component has its own stream,
    SeedSequence(MASTER_SEED, spawn_key=(level_id, pattern_id, replicate, component_id)),
so changing one ingredient never reshuffles another, and every Lyft rule later
replays identical riders (common random numbers).

Run: .venv/bin/python src/scenario/build_levels_v2.py
"""
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import pandas as pd

try:            # imported as the package scenario.*
    from .demand import fit_od, load_world, PROCESSED, ROOT
except ImportError:   # run as a script from src/scenario
    from demand import fit_od, load_world, PROCESSED, ROOT

MASTER_SEED = 20261020
OUT = ROOT / "data" / "scenarios" / "v2"
LEVEL_ID = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5, "L6": 6, "L7": 7}
PATTERN_ID = {"base": 0, "burst": 1, "far": 2, "high": 3}
COMPONENTS = {"count": 0, "times": 1, "od": 2, "party": 3, "availability": 4, "patience": 5, "noshow": 6,
              "consent": 7, "lyft_delay": 8, "lyft_noshow": 9, "eta_noise": 10, "solver": 11,
              "spread": 12}             # spread: which satellite a request uses in the dispersed variant (D-34)
DEPOT = "p04_b040"                      # D-17
CAPACITY = 14                           # D-30
DWELL_S = 30                            # per stop (ASSUMED, P-05)
NOSHOW_WAIT_S = 180                     # the van waits 3 min at the curb (JHU)
NEVER_S = 10 * 3600                     # "never cancels" patience for designed levels
PARTY_P = {1: .73, 2: .18, 3: .055, 4: .025, 5: .01}     # spec §3.3 (mean 1.405)
PARTY_P_1TO4 = {1: .73, 2: .18, 3: .055, 4: .025}        # L1-L4 draws (renormalised; L4 adds one party of 5 by design)
# Lyft vehicle class (decision D-33, user-supplied operational knowledge, 21 Oct 2026): parties of 1-4 ride a standard
# Lyft; a party of 5 stays together in a larger vehicle (e.g. Lyft XL). XL availability, delay and cost are unknown:
# the base uses the same latent Lyft delay for both classes (ASSUMED) and reports XL trips separately.
LYFT_STANDARD_MAX_PARTY = 4
PHI_BREAKS_MIN = (0, 5, 10, 15, 20)
PHI_SLOPES = (1.0, 2.5, 5.0, 10.0, 20.0)                  # per passenger-minute (D-29)
BETA_RIDE, GAMMA_KM = 0.5, 0.1                            # D-29
P_NOSHOW = 0.047

LABELS = {
    "requests": "SYNTHETIC from the April-calibrated demand model (gravity x IPF, v2 matrix; D-18, D-31)",
    "party": "mean DERIVED (April 1.39); shape ASSUMED (spec 3.3)",
    "availability": "Fleet 5-6 vans x 14 seats is a team decision (D-30); 2 vans at L1-L5 by design (D-32)",
    "patience": "ASSUMED placeholder; Weibull shape 1.5, median 18 min; calibrated in Phase 6 (P-08)",
    "lyft_delay": "ASSUMED: lognormal, median 8 min, P90 15 min (AS-08)",
    "noshow": "DERIVED rate 4.7% (April p07)",
    "travel_multiplier": "ASSUMED placeholder; calibrated (AS-21)",
}


# ---------- seeds, world, small helpers ----------
def stream(level, pattern, replicate, component):
    ss = np.random.SeedSequence(MASTER_SEED, spawn_key=(LEVEL_ID[level], PATTERN_ID[pattern], replicate, COMPONENTS[component]))
    return np.random.default_rng(ss)


_MAT = {}


def world():
    """Locations, and v2 seconds and metres as dicts keyed (from, to)."""
    if not _MAT:
        loc, _ = load_world("v2")
        tt = pd.read_csv(PROCESSED / "tt_locations_v2.csv")
        _MAT["loc"] = loc.set_index("loc_id")
        _MAT["sec"] = dict(zip(zip(tt.origin, tt.dest), tt.seconds))
        _MAT["m"] = dict(zip(zip(tt.origin, tt.dest), tt.meters))
    return _MAT["loc"], _MAT["sec"], _MAT["m"]


def T(a, b, mult=1.0):
    """Van travel time in whole seconds (matrix seconds x multiplier, rounded)."""
    return int(round(world()[1][(a, b)] * mult))


def phi(wait_s):
    """Convex PWL wait penalty per passenger, in penalty-minutes (D-29)."""
    w, out = wait_s / 60.0, 0.0
    edges = list(PHI_BREAKS_MIN) + [math.inf]
    for lo, hi, s in zip(edges[:-1], edges[1:], PHI_SLOPES):
        if w > lo:
            out += s * (min(w, hi) - lo)
    return out


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def csv_bytes(df):
    return df.to_csv(index=False, lineterminator="\n").encode()


def manifest():
    """Fingerprints of every routing/data artifact the scenarios depend on (D-31)."""
    prov = json.loads((ROOT / "data" / "osrm" / "PROVENANCE.json").read_text())
    m = {"created_for": "scenario generator v2 (scenario_spec v0.2)",
         "osm_extract": {"url": prov["source_url"], "md5": prov["md5"], "osm_timestamp": "2026-10-01T20:22:06Z"},
         "osrm_image": {"tag": prov["image_tag"], "index_digest": prov["image_digest"].split("@")[1],
                        "arm64_manifest_digest": "sha256:733da1be48587358a417750655cc4748bbae9af60e3ace610db68d4febe038d8",
                        "profile": prov["profile"], "algorithm": prov["algorithm"]},
         "built_on": {"platform": "linux/arm64 (Docker on Apple Silicon)", "machine": platform.machine()},
         "files": {f: sha256(PROCESSED / f) for f in
                   ("locations_v1.csv", "tt_locations_v2.csv", "locations_snap_v2.csv", "zones_v1.csv")}}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "MANIFEST.json"
    path.write_text(json.dumps(m, indent=2) + "\n")
    return sha256(path)


def od_table(pattern="base"):
    """Base O-D table (Homewood + Peabody, D-27). 'far' doubles pairs with an end in the Peabody/downtown zones."""
    t, _ = fit_od(0.1, "month_average", 60.0, "v2")
    if pattern == "far":
        loc = world()[0]
        south = {"Z03", "Z04", "Z07", "Z09", "Z11"}
        touch = loc.zone_id.reindex(t.o_loc).isin(south).to_numpy() | loc.zone_id.reindex(t.d_loc).isin(south).to_numpy()
        t["prob"] = np.where(touch, 2 * t.prob, t.prob)
        t["prob"] /= t.prob.sum()
    return t


def draw_od(rng, n, pattern="base", max_direct_s=None):
    t = od_table(pattern)
    if max_direct_s is not None:
        t = t[t.seconds <= max_direct_s].copy()
        t["prob"] /= t.prob.sum()
    cdf = np.cumsum(t.prob.to_numpy())
    idx = np.minimum(np.searchsorted(cdf, rng.random(n) * cdf[-1], side="right"), len(t) - 1)
    return t.o_loc.to_numpy()[idx], t.d_loc.to_numpy()[idx]


def draw_party(rng, n, probs):
    k = sorted(probs)
    p = np.array([probs[i] for i in k]); p /= p.sum()
    return rng.choice(k, size=n, p=p)


def request_frame(t, o, d, party, mult):
    loc = world()[0]
    df = pd.DataFrame({"request_id": [f"R{i + 1:03d}" for i in range(len(t))], "t_request_s": np.asarray(t, int),
                       "o_loc": o, "d_loc": d})
    df["o_zone"] = loc.zone_id.reindex(df.o_loc).to_numpy()
    df["d_zone"] = loc.zone_id.reindex(df.d_loc).to_numpy()
    df["party"] = np.asarray(party, int)
    df["direct_s"] = [T(a, b, 1.0) for a, b in zip(o, d)]     # unscaled matrix time (spec 10)
    return df


def write_scenario(folder, requests, latent, availability, params, extra=None, manifest_path=None):
    """Write the input files; the content hash covers the three CSVs and the canonical params."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    blobs = [csv_bytes(requests), csv_bytes(latent), csv_bytes(availability)]
    for name, b in zip(("requests.csv", "latent.csv", "availability.csv"), blobs):
        (folder / name).write_bytes(b)
    canon = json.dumps(params, sort_keys=True, separators=(",", ":")).encode()
    sc = {"params": params, "labels": LABELS, "manifest_sha256": sha256(manifest_path or OUT / "MANIFEST.json"),
          "generator": "src/scenario/generator_v2.py", "seeds": {"master_seed": MASTER_SEED,
          "spawn_key": "(level_id, pattern_id, replicate, component_id)", "level_id": LEVEL_ID[params["level"]],
          "pattern_id": PATTERN_ID[params["pattern"]], "replicate": params["replicate"], "components": COMPONENTS},
          "content_hash": hashlib.sha256(b"".join(blobs) + canon).hexdigest()}
    if extra:
        sc.update(extra)
    (folder / "scenario.json").write_text(json.dumps(sc, indent=2) + "\n")
    return sc


# ---------- L1-L3: one open request at a time, both vans idle; hand-checkable ----------
def _best_van(vans, o, d, q, t, mult):
    """Cost-minimal idle van for an isolated request (D-29 cost), tie -> lower van id."""
    loc, sec, met = world()
    rows = []
    for vid, (pos, _) in sorted(vans.items()):
        dead = T(pos, o, mult)
        ride = DWELL_S + T(o, d, mult)
        km = (met[(pos, o)] + met[(o, d)]) / 1000
        cost = q * phi(dead) + BETA_RIDE * q * ride / 60 + GAMMA_KM * km
        rows.append((round(cost, 6), vid, dead, ride, km))
    rows.sort()
    return rows


def build_l1_to_l3(mult=1.0):
    """16 requests shared by L1-L3. Request times are chosen so that, in every level, both vans are idle
    when each request arrives; the cost-minimal van then goes directly (its next stop is the pickup, so it
    is committed and never reassigned). L2 adds two no-shows, L3 adds designed cancellations."""
    n = 16
    rng_od, rng_p, rng_t = (stream("L1", "base", 0, c) for c in ("od", "party", "times"))
    o, d = draw_od(rng_od, n, max_direct_s=480)          # trips <= 8 min keep the hand check short
    party = draw_party(rng_p, n, PARTY_P_1TO4)
    gaps = (rng_t.integers(3, 13, n) * 10).tolist()        # 30-120 s idle gap before each request
    noshow_idx = {4, 10}                                   # L2: R005 and R011 do not show
    levels = ("L1", "L2", "L3")
    vans = {lv: {"V1": (DEPOT, 0), "V2": (DEPOT, 0)} for lv in levels}   # (position, idle-from time)
    patience = {i: NEVER_S for i in range(n)}
    cancels_needed, rows, t = 3, {lv: [] for lv in levels}, 0
    for i in range(n):
        t = max(max(v[1] for v in vans[lv].values()) for lv in levels) + gaps[i]
        for lv in levels:
            ranked = _best_van(vans[lv], o[i], d[i], int(party[i]), t, mult)
            cost, vid, dead, ride, km = ranked[0]
            pos = vans[lv][vid][0]
            arrive = t + dead
            row = {"level": lv, "request_id": f"R{i + 1:03d}", "t_request_s": t, "party": int(party[i]),
                   "o_loc": o[i], "d_loc": d[i], "van": vid, "van_from": pos,
                   "deadhead_s": dead, "pickup_arrival_s": arrive,
                   "cost_V1": next(r[0] for r in ranked if r[1] == "V1"),
                   "cost_V2": next(r[0] for r in ranked if r[1] == "V2")}
            if lv == "L2" and i in noshow_idx:
                row.update(outcome="noshow_van", wait_s=None, pickup_s=None, dropoff_s=None,
                           event_s=arrive + NOSHOW_WAIT_S, van_free_s=arrive + NOSHOW_WAIT_S, van_free_at=o[i])
            elif lv == "L3" and i >= 2 and cancels_needed > 0 and dead >= 150 and patience[i] == NEVER_S:
                patience[i] = dead // 2                     # cancels while the van is still driving
                cancels_needed -= 1
                row.update(outcome="cancel_pending_van", wait_s=None, pickup_s=None, dropoff_s=None,
                           event_s=t + patience[i], van_free_s=arrive, van_free_at=o[i])
            else:
                drop = arrive + DWELL_S + T(o[i], d[i], mult)
                row.update(outcome="van_completed", wait_s=dead, pickup_s=arrive, dropoff_s=drop,
                           ride_s=drop - arrive, event_s=drop, van_free_s=drop + DWELL_S, van_free_at=d[i])
            vans[lv][vid] = (row["van_free_at"], row["van_free_s"])
            rows[lv].append(row)
    req = request_frame([r["t_request_s"] for r in rows["L1"]], o, d, party, mult)
    return req, rows, patience, noshow_idx


def _latent_designed(req, patience=None, noshow_idx=(), consent=None, lyft_delay=480):
    n = len(req)
    return pd.DataFrame({"request_id": req.request_id,
                         "patience_s": [int((patience or {}).get(i, NEVER_S)) for i in range(n)],
                         "noshow_u": [0.0 if i in noshow_idx else 0.99 for i in range(n)],
                         "consent_u": [(consent or {}).get(i, 0.0) for i in range(n)],
                         "lyft_delay_s": [lyft_delay] * n, "lyft_noshow_u": [0.99] * n, "eta_noise": [1.0] * n})


def _availability(n_vans, start_s, end_s):
    return pd.DataFrame({"van_id": [f"V{i + 1}" for i in range(n_vans)], "start_loc": DEPOT, "capacity": CAPACITY,
                         "avail_start_s": start_s, "avail_end_s": end_s})


# ---------- L4: Lyft bookkeeping; vans come on duty at 18:15, so early transfers are hand-traceable ----------
L4_VANS_FROM_S, L4_LAG_S, L4_LYFT_DELAY_S, L4_CONSENT_P = 900, 120, 480, 0.9
L4_RULES = {"R0": None, "R1(10)": ("elapsed", 600), "R1(15)": ("elapsed", 900), "R1u(10)": ("unassigned", 600),
            "R2(15)": ("predicted", 900), "R3(2)": ("van_vs_lyft", 120)}


def build_l4(mult=1.0):
    n = 16
    rng_t, rng_od, rng_p = (stream("L4", "base", 0, c) for c in ("times", "od", "party"))
    t = np.sort((rng_t.integers(0, 121, n) * 10))          # 16 requests in 0-1200 s, 10-s grid
    o, d = draw_od(rng_od, n, max_direct_s=480)
    party = draw_party(rng_p, n, PARTY_P_1TO4)
    early = [i for i in range(n) if t[i] < L4_VANS_FROM_S]
    party[early[1]] = 5                                     # one party of 5: Lyft-eligible via XL (D-33), kept together
    decliner = early[2]                                     # one rider declines the Lyft offer
    req = request_frame(t, o, d, party, mult)
    latent = _latent_designed(req, consent={decliner: 0.95}, lyft_delay=L4_LYFT_DELAY_S)
    # decision epochs before the vans arrive: 120-s ticks and request arrivals (events)
    epochs = sorted(set(range(0, L4_VANS_FROM_S, 120)) | {int(x) for x in t if x < L4_VANS_FROM_S})
    rows = []
    for rule, spec in L4_RULES.items():
        for i in range(n):
            base = {"rule": rule, "request_id": f"R{i + 1:03d}", "t_request_s": int(t[i]), "party": int(party[i])}
            if spec is None:
                rows.append({**base, "decision": "no transfers under R0", "decision_s": None})
                continue
            kind, theta = spec
            if kind in ("elapsed", "unassigned"):
                fire = next((e for e in epochs if e >= t[i] + theta), None)   # None: falls at/after 18:15
            else:   # predicted-wait and van-vs-Lyft: no van can be assigned before 900 s, predicted pickup = infinity
                fire = int(t[i]) if t[i] < L4_VANS_FROM_S else None
            if fire is None:
                rows.append({**base, "decision": "after vans arrive: depends on the dispatcher (not hand-checked)",
                             "decision_s": None})
            elif i == decliner:
                rows.append({**base, "decision": "offered, declined (consent_u 0.95 > p_c 0.9): stays with the vans; "
                                                 "not offered again", "decision_s": fire})
            else:
                pick = fire + L4_LAG_S + L4_LYFT_DELAY_S
                drop = pick + DWELL_S + T(o[i], d[i], mult)
                rows.append({**base, "decision": "transfer", "decision_s": fire, "lyft_request_s": fire + L4_LAG_S,
                             "lyft_class": "standard" if party[i] <= LYFT_STANDARD_MAX_PARTY else "XL",
                             "lyft_pickup_s": pick, "wait_s": pick - int(t[i]), "lyft_dropoff_s": drop,
                             "outcome": "lyft_completed"})
    return req, latent, pd.DataFrame(rows), {"decliner": f"R{decliner + 1:03d}",
                                             "party5": f"R{early[1] + 1:03d}", "epochs_s": epochs}


# ---------- L5: pipeline dress rehearsal, random latent draws, 30 paired nights ----------
L5_N, L5_WINDOW_S, L5_BURST = 28, 3600, (1200, 1800, 0.4)


def build_l5(replicate, mult=1.2):
    lv, pat = "L5", "base"
    rng = {c: stream(lv, pat, replicate, c) for c in COMPONENTS}
    k = int(round(L5_BURST[2] * L5_N))
    t = np.concatenate([rng["times"].uniform(L5_BURST[0], L5_BURST[1], k), rng["times"].uniform(0, L5_WINDOW_S, L5_N - k)])
    t = np.minimum(np.floor(np.sort(t)), L5_WINDOW_S - 1).astype(int)
    o, d = draw_od(rng["od"], L5_N)
    party = draw_party(rng["party"], L5_N, PARTY_P)
    req = request_frame(t, o, d, party, mult)
    shape, median = 1.5, 18 * 60
    scale = median / (math.log(2) ** (1 / shape))
    sigma = math.log(900 / 480) / 1.2816                    # lognormal: median 480 s, P90 900 s
    latent = pd.DataFrame({
        "request_id": req.request_id,
        "patience_s": np.maximum(1, np.round(scale * rng["patience"].weibull(shape, L5_N))).astype(int),
        "noshow_u": rng["noshow"].random(L5_N).round(6),
        "consent_u": rng["consent"].random(L5_N).round(6),
        "lyft_delay_s": np.round(480 * np.exp(sigma * rng["lyft_delay"].standard_normal(L5_N))).astype(int),
        "lyft_noshow_u": rng["lyft_noshow"].random(L5_N).round(6),
        "eta_noise": np.exp(0.15 * rng["eta_noise"].standard_normal(L5_N)).round(6)})
    return req, latent, _availability(2, 0, L5_WINDOW_S)


# ---------- Dispersed geography variant (D-34): same requests, coarse endpoints spread over road satellites ----------
def disperse_requests(req, level, pattern, replicate, sites, sec, min_trip_s=60, max_redraws=50):
    """Replace endpoints that are coarse city clusters by one of their satellites, drawn uniformly (equal weights)
    from the named "spread" stream. Request times, cluster-level O-D, party and rider traits are untouched.
    If a drawn satellite pair drives under min_trip_s, both endpoints are redrawn (counted in the return value)."""
    rng = stream(level, pattern, replicate, "spread")
    sats = sites[sites.is_satellite].groupby("parent_loc").loc_id.apply(list).to_dict()
    out, redraws = req.copy(), 0
    o_new, d_new = [], []
    for o, d in zip(req.o_loc, req.d_loc):
        for attempt in range(max_redraws + 1):
            oo = sats[o][rng.integers(len(sats[o]))] if o in sats else o
            dd = sats[d][rng.integers(len(sats[d]))] if d in sats else d
            if sec[(oo, dd)] >= min_trip_s or (oo == o and dd == d):
                break
            redraws += 1
        else:
            raise RuntimeError(f"no satellite pair >= {min_trip_s} s for {o}->{d}")
        o_new.append(oo); d_new.append(dd)
    out.insert(out.columns.get_loc("o_loc") + 1, "o_cluster", req.o_loc.to_numpy())
    out.insert(out.columns.get_loc("d_loc") + 2, "d_cluster", req.d_loc.to_numpy())
    out["o_loc"], out["d_loc"] = o_new, d_new
    out["direct_s"] = [int(round(sec[(a, b)])) for a, b in zip(o_new, d_new)]
    return out, redraws
