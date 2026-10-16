"""Independent tests for the Phase 3 scenario world-builder.

Written from docs/technical/scenario_contract.md only (not from the
implementation). Expected values are derived here from the input CSVs.
"""
import copy
import hashlib
import json
import math
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
LOC_CSV = PROC / "locations_v1.csv"
TT_CSV = PROC / "tt_locations_v1.csv"
ZP_CSV = PROC / "zone_points_v0.csv"
SCEN = ROOT / "data" / "scenarios"

REQ_COLS = {
    "request_id", "t_request_s", "o_loc", "d_loc", "o_zone", "d_zone",
    "o_lat", "o_lon", "d_lat", "d_lon", "party", "patience_s", "direct_s",
}
FLEET_COLS = {
    "van_id", "start_loc", "lat", "lon", "capacity", "shift_start_s", "shift_end_s",
}
BETAS = [0.0, 0.1, 0.2]
DIRECTIONS = ["month_average", "campus_outbound_6pm"]


# --------------------------------------------------------------------------
# helpers / fixtures
# --------------------------------------------------------------------------
def _gen():
    return pytest.importorskip("scenario.generator")


def _demand():
    return pytest.importorskip("scenario.demand")


def build(params, rep, out_dir):
    return _gen().build_scenario(params, rep, out_dir)


def base_params():
    return copy.deepcopy(_gen().default_params())


def read_req(d):
    return pd.read_csv(Path(d) / "requests.csv")


def read_fleet(d):
    return pd.read_csv(Path(d) / "fleet.csv")


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def locs():
    if not LOC_CSV.exists():
        pytest.skip("locations_v1.csv not built yet")
    return pd.read_csv(LOC_CSV)


@pytest.fixture(scope="module")
def tt():
    if not TT_CSV.exists():
        pytest.skip("tt_locations_v1.csv not built yet")
    return pd.read_csv(TT_CSV)


@pytest.fixture(scope="module")
def sec(tt, locs):
    """Seconds as a dict-of-pairs lookup and as a pivot DataFrame."""
    return tt.pivot(index="origin", columns="dest", values="seconds")


def targets(locs, direction):
    """Point-margin targets as probabilities (each side sums to 1).

    month_average: April weights. campus_outbound_6pm: Z08 origin weights x1.5,
    then the origin total renormalised (uniform rescale to the April total, which
    in probability terms is w'/sum(w')). Destination targets unchanged.
    """
    O = locs[locs.endpoint == "O"].set_index("loc_id")
    D = locs[locs.endpoint == "D"].set_index("loc_id")
    wo = O.weight.astype(float).copy()
    if direction == "campus_outbound_6pm":
        wo[O.zone_id == "Z08"] *= 1.5
    return wo / wo.sum(), D.weight.astype(float) / D.weight.sum()


@lru_cache(maxsize=None)
def fit(beta, direction, min_trip_s=60.0):
    return _demand().fit_od(beta, direction, min_trip_s)


def table_matrix(table, o_ids, d_ids):
    """Dense prob matrix (o x d) from the long table; duplicates summed."""
    m = table.pivot_table(index="o_loc", columns="d_loc", values="prob",
                          aggfunc="sum", fill_value=0.0)
    return m.reindex(index=o_ids, columns=d_ids, fill_value=0.0)


def lp_feasible(allowed, t_o, t_d):
    """Is there a nonnegative flow on `allowed` pairs with exactly these margins?"""
    from scipy.optimize import linprog
    from scipy.sparse import lil_matrix

    ii, jj = np.nonzero(allowed)
    nv = len(ii)
    nO, nD = allowed.shape
    A = lil_matrix((nO + nD, nv))
    for k, (i, j) in enumerate(zip(ii, jj)):
        A[i, k] = 1.0
        A[nO + j, k] = 1.0
    b = np.concatenate([t_o, t_d])
    res = linprog(np.zeros(nv), A_eq=A.tocsr(), b_eq=b, bounds=(0, None), method="highs")
    return res.status == 0


# --------------------------------------------------------------------------
# 0. inputs sanity (locations derive from zone_points_v0)
# --------------------------------------------------------------------------
def test_locations_match_zone_points(locs):
    """Contract s1: locations_v1 = one row per bubble, loc_id = bubble_id,
    weight = count_used, zone_id/endpoint carried over."""
    zp = pd.read_csv(ZP_CSV)
    assert locs.loc_id.is_unique
    assert set(locs.loc_id) == set(zp.bubble_id)
    m = locs.merge(zp, left_on="loc_id", right_on="bubble_id", suffixes=("", "_zp"))
    assert np.allclose(m.weight, m.count_used)
    assert (m.zone_id == m.zone_id_zp).all()
    assert (m.endpoint == m.endpoint_zp).all()
    assert set(locs.endpoint) == {"O", "D"}


# --------------------------------------------------------------------------
# 1. matrix
# --------------------------------------------------------------------------
def test_matrix_complete_directed(locs, tt):
    """Contract s1: tt_locations_v1 is the complete directed matrix over all
    locations; every ordered pair exactly once, diagonal 0, finite, >= 0."""
    ids = list(locs.loc_id)
    n = len(ids)
    assert list(tt.columns[:4]) == ["origin", "dest", "seconds", "meters"] or \
        {"origin", "dest", "seconds", "meters"} <= set(tt.columns)
    assert len(tt) == n * n
    assert not tt.duplicated(["origin", "dest"]).any()
    pairs = set(zip(tt.origin, tt.dest))
    assert pairs == {(a, b) for a in ids for b in ids}
    diag = tt[tt.origin == tt.dest]
    assert len(diag) == n
    assert (diag.seconds == 0).all()
    for col in ("seconds", "meters"):
        v = tt[col].to_numpy(dtype=float)
        assert np.isfinite(v).all()
        assert (v >= 0).all()


# --------------------------------------------------------------------------
# 2. population fit
# --------------------------------------------------------------------------
@pytest.mark.parametrize("direction", DIRECTIONS)
@pytest.mark.parametrize("beta", BETAS)
def test_fit_od_contract(beta, direction, locs, sec):
    """Contract s2: prob>=0 and sums to 1; o_loc in O, d_loc in D; structural
    zeros for seconds < min_trip_s; diag fields; point and zone margins within 1%
    on attainable targets (unattainable ones must be flagged in diag)."""
    min_trip = 60.0
    table, diag = fit(beta, direction, min_trip)
    assert {"o_loc", "d_loc", "prob"} <= set(table.columns)
    p = table.prob.to_numpy(dtype=float)
    assert np.isfinite(p).all() and (p >= 0).all()
    assert abs(p.sum() - 1.0) < 1e-9

    O_ids = list(locs[locs.endpoint == "O"].loc_id)
    D_ids = list(locs[locs.endpoint == "D"].loc_id)
    assert set(table.o_loc) <= set(O_ids)
    assert set(table.d_loc) <= set(D_ids)

    # structural zeros
    s = sec.reindex(index=O_ids, columns=D_ids).to_numpy()
    allowed = s >= min_trip
    P = table_matrix(table, O_ids, D_ids).to_numpy()
    assert P[~allowed].sum() == 0.0

    # diag contents
    for key in ("converged", "iterations", "max_rel_resid_o", "max_rel_resid_d",
                "zone_rel_resid_o", "zone_rel_resid_d"):
        assert key in diag, f"diag missing {key}"
    assert isinstance(diag["zone_rel_resid_o"], dict)
    assert isinstance(diag["zone_rel_resid_d"], dict)

    # independently computed targets
    t_o, t_d = targets(locs, direction)
    t_o = t_o.reindex(O_ids).to_numpy()
    t_d = t_d.reindex(D_ids).to_numpy()
    dead_o = ~allowed.any(axis=1)
    dead_d = ~allowed.any(axis=0)
    has_dead = dead_o.any() or dead_d.any()

    alive_o, alive_d = ~dead_o, ~dead_d
    if has_dead:
        # Unattainable: dead points can carry no mass. Compare the rest after
        # renormalising both sides over alive points (implementation-agnostic).
        flagged = (not diag["converged"]) or max(diag["max_rel_resid_o"],
                                                  diag["max_rel_resid_d"]) > 0.01 \
            or any(str(x) in str(diag) for x in
                   [O_ids[i] for i in np.nonzero(dead_o)[0]] +
                   [D_ids[j] for j in np.nonzero(dead_d)[0]])
        assert flagged, "points with only structural-zero partners must be reported in diag"
    sub = allowed[np.ix_(alive_o, alive_d)]
    to = t_o[alive_o] / t_o[alive_o].sum()
    td = t_d[alive_d] / t_d[alive_d].sum()
    feasible = lp_feasible(sub, to, td)
    if not feasible:
        # exact margins impossible on the support: must be flagged, no 1% claim
        assert (not diag["converged"]) or max(diag["max_rel_resid_o"],
                                              diag["max_rel_resid_d"]) > 0.0
        pytest.skip("margins not exactly attainable on the support; flag-only check done")

    fo = P.sum(axis=1)[alive_o]
    fd = P.sum(axis=0)[alive_d]
    fo, fd = fo / fo.sum(), fd / fd.sum()
    rel_o = np.abs(fo - to) / to
    rel_d = np.abs(fd - td) / td
    assert rel_o.max() < 0.01, f"origin point margin off by {rel_o.max():.4f}"
    assert rel_d.max() < 0.01, f"destination point margin off by {rel_d.max():.4f}"
    if not has_dead:
        assert diag["converged"] is True or diag["converged"]
        # diag's reported residuals agree with an independent computation
        assert abs(diag["max_rel_resid_o"] - rel_o.max()) < 1e-4
        assert abs(diag["max_rel_resid_d"] - rel_d.max()) < 1e-4

    # zone-level margins
    zone = locs.set_index("loc_id").zone_id
    zo_t = pd.Series(to, index=np.array(O_ids)[alive_o]).groupby(zone).sum()
    zo_f = pd.Series(fo, index=np.array(O_ids)[alive_o]).groupby(zone).sum()
    zd_t = pd.Series(td, index=np.array(D_ids)[alive_d]).groupby(zone).sum()
    zd_f = pd.Series(fd, index=np.array(D_ids)[alive_d]).groupby(zone).sum()
    assert ((zo_f - zo_t).abs() / zo_t).max() < 0.01
    assert ((zd_f - zd_t).abs() / zd_t).max() < 0.01


def test_fit_od_custom_min_trip(locs, sec):
    """Contract s2: the structural-zero threshold is the min_trip_s argument."""
    table, _ = fit(0.1, "month_average", 300.0)
    O_ids = list(locs[locs.endpoint == "O"].loc_id)
    D_ids = list(locs[locs.endpoint == "D"].loc_id)
    s = sec.reindex(index=O_ids, columns=D_ids).to_numpy()
    P = table_matrix(table, O_ids, D_ids).to_numpy()
    assert P[s < 300.0].sum() == 0.0
    assert abs(table.prob.sum() - 1) < 1e-9


def test_fit_od_campus_shifts_origin_mass_to_z08(locs):
    """Contract s2: campus_outbound_6pm raises Z08 origin share (x1.5 pre-renorm)
    and leaves destination zone shares ~unchanged."""
    zone = locs.set_index("loc_id").zone_id
    ta, _ = fit(0.1, "month_average")
    tc, _ = fit(0.1, "campus_outbound_6pm")
    za = ta.groupby("o_loc").prob.sum().groupby(zone).sum()
    zc = tc.groupby("o_loc").prob.sum().groupby(zone).sum()
    assert zc["Z08"] > za["Z08"] * 1.2
    da = ta.groupby("d_loc").prob.sum().groupby(zone).sum()
    dc = tc.groupby("d_loc").prob.sum().groupby(zone).sum()
    assert ((da - dc).abs().max()) < 0.01 * da.max() + 1e-3


# --------------------------------------------------------------------------
# 3. gravity effect
# --------------------------------------------------------------------------
def test_gravity_mean_direct_seconds_decreases_with_beta(locs, sec):
    """Contract s2: seed w_o*w_d*exp(-beta*sec/60) => mean direct seconds under
    prob strictly decreases in beta (month_average)."""
    O_ids = list(locs[locs.endpoint == "O"].loc_id)
    D_ids = list(locs[locs.endpoint == "D"].loc_id)
    s = sec.reindex(index=O_ids, columns=D_ids).to_numpy()
    means = []
    for b in BETAS:
        table, _ = fit(b, "month_average")
        P = table_matrix(table, O_ids, D_ids).to_numpy()
        means.append(float((P * s).sum() / P.sum()))
    assert means[0] > means[1] > means[2], means


# --------------------------------------------------------------------------
# 4-5. reproducibility and stream independence
# --------------------------------------------------------------------------
def test_reproducible_byte_identical(tmp_path):
    """Contract s3 (Random streams): same params + replicate => byte-identical
    requests/fleet and equal content_hash; another replicate differs."""
    p = base_params()
    a, b, c = tmp_path / "A", tmp_path / "B", tmp_path / "C"
    ja = build(p, 0, a)
    jb = build(p, 0, b)
    jc = build(p, 1, c)
    for f in ("requests.csv", "fleet.csv"):
        assert (a / f).read_bytes() == (b / f).read_bytes()
    assert ja["content_hash"] == jb["content_hash"]
    assert (a / "requests.csv").read_bytes() != (c / "requests.csv").read_bytes()
    assert ja["content_hash"] != jc["content_hash"]
    assert (a / "scenario.json").exists()


def test_scenario_json_contents(tmp_path):
    """Contract s3: scenario.json holds params (as given), replicate, seeds,
    inputs (sha256 of locations_v1 and tt_locations_v1), content_hash,
    code_version, labels; build_scenario returns the parsed file."""
    if not (LOC_CSV.exists() and TT_CSV.exists()):
        pytest.skip("inputs not built")
    p = base_params()
    ret = build(p, 3, tmp_path / "x")
    on_disk = json.loads((tmp_path / "x" / "scenario.json").read_text())
    assert ret == on_disk
    for k in ("params", "replicate", "seeds", "inputs", "content_hash",
              "code_version", "labels"):
        assert k in on_disk, k
    assert on_disk["params"] == json.loads(json.dumps(p))
    assert on_disk["replicate"] == 3
    assert on_disk["seeds"]["master_seed"] == p["master_seed"]
    ih = json.dumps(on_disk["inputs"])
    assert sha256_file(LOC_CSV) in ih and sha256_file(TT_CSV) in ih
    ch = on_disk["content_hash"]
    assert isinstance(ch, str) and len(ch) == 64 and int(ch, 16) >= 0
    # "an evidence label for each parameter": identifiers (cell, master_seed)
    # are not modelling assumptions, so they are exempt (contract ambiguity).
    assert (set(p) - {"cell", "master_seed"}) <= set(on_disk["labels"])


def test_stream_independence_patience(tmp_path):
    """Contract s3 (Random streams): changing patience leaves t_request_s,
    o_loc, d_loc, party unchanged; patience_s changes."""
    p1 = base_params()
    p2 = base_params()
    p2["patience"]["median_s"] = 1440
    build(p1, 2, tmp_path / "a")
    build(p2, 2, tmp_path / "b")
    a, b = read_req(tmp_path / "a"), read_req(tmp_path / "b")
    for c in ("t_request_s", "o_loc", "d_loc", "party"):
        assert a[c].equals(b[c]), c
    assert not np.allclose(a.patience_s, b.patience_s)


@pytest.mark.parametrize("change", [
    {"capacity": 6},
    {"n_vans": 3},
    {"n_vans": 9},
    {"start_rule": "depot"},
])
def test_stream_independence_fleet_params(change, tmp_path):
    """Contract s3 (Random streams): changing capacity / n_vans / start_rule
    leaves requests.csv byte-identical (while the content_hash must change)."""
    p1 = base_params()
    p2 = base_params()
    p2.update(change)
    j1 = build(p1, 4, tmp_path / "a")
    j2 = build(p2, 4, tmp_path / "b")
    assert (tmp_path / "a" / "requests.csv").read_bytes() == \
        (tmp_path / "b" / "requests.csv").read_bytes()
    assert j1["content_hash"] != j2["content_hash"]


# --------------------------------------------------------------------------
# 6. request file validity
# --------------------------------------------------------------------------
@pytest.mark.parametrize("n", [6, 30, 170])
def test_requests_valid(n, tmp_path, locs, sec):
    """Contract s3 requests.csv: exact columns, n rows under count_rule=fixed,
    sorted, time/party/patience ranges, zones, direct_s from the matrix."""
    p = base_params()
    p["n_requests"] = n
    p["count_rule"] = "fixed"
    build(p, 0, tmp_path)
    r = read_req(tmp_path)
    assert set(r.columns) == REQ_COLS
    assert len(r) == n
    assert list(r.request_id) == [f"R{i:03d}" for i in range(1, n + 1)] or \
        sorted(r.request_id) == sorted(f"R{i:03d}" for i in range(1, n + 1))
    # sorted by t_request_s then request_id
    keyed = list(zip(r.t_request_s, r.request_id))
    assert keyed == sorted(keyed)
    assert (r.t_request_s >= 0).all() and (r.t_request_s < p["window_s"]).all()
    assert r.party.between(1, 4).all()
    assert (r.party == r.party.round()).all()
    assert (r.patience_s > 0).all()
    L = locs.set_index("loc_id")
    assert set(r.o_loc) <= set(L.index[L.endpoint == "O"])
    assert set(r.d_loc) <= set(L.index[L.endpoint == "D"])
    assert (r.o_zone.to_numpy() == L.loc[r.o_loc, "zone_id"].to_numpy()).all()
    assert (r.d_zone.to_numpy() == L.loc[r.d_loc, "zone_id"].to_numpy()).all()
    assert np.allclose(r.o_lat, L.loc[r.o_loc, "lat"].to_numpy(), atol=1e-6)
    assert np.allclose(r.o_lon, L.loc[r.o_loc, "lon"].to_numpy(), atol=1e-6)
    assert np.allclose(r.d_lat, L.loc[r.d_loc, "lat"].to_numpy(), atol=1e-6)
    assert np.allclose(r.d_lon, L.loc[r.d_loc, "lon"].to_numpy(), atol=1e-6)
    expect = np.array([sec.loc[o, d] for o, d in zip(r.o_loc, r.d_loc)])
    assert np.allclose(r.direct_s, expect, rtol=1e-6, atol=1e-3)
    assert (r.direct_s >= p["min_trip_s"]).all()


def test_poisson_count_rule(tmp_path):
    """Contract s3 params: count_rule='poisson' => count ~ Poisson(n_requests):
    counts vary across replicates and average near n (3-sigma band)."""
    p = base_params()
    p["count_rule"] = "poisson"
    counts = []
    for rep in range(40):
        build(p, rep, tmp_path / f"r{rep}")
        counts.append(len(read_req(tmp_path / f"r{rep}")))
    assert len(set(counts)) > 5
    se = math.sqrt(p["n_requests"] / len(counts))
    assert abs(np.mean(counts) - p["n_requests"]) < 3.5 * se


def test_window_s_respected(tmp_path):
    """Contract s3: t_request_s in [0, window_s) for a non-default window; fleet
    shift_end_s tracks it."""
    p = base_params()
    p["window_s"] = 1800
    p["n_requests"] = 60
    build(p, 0, tmp_path)
    r = read_req(tmp_path)
    assert (r.t_request_s >= 0).all() and (r.t_request_s < 1800).all()
    assert (read_fleet(tmp_path).shift_end_s == 1800).all()


# --------------------------------------------------------------------------
# 7. burst
# --------------------------------------------------------------------------
def test_burst_arrivals(tmp_path):
    """Contract s3 params: under 'burst', round(burst_share*n) requests are
    uniform in [0, burst_window_s), the rest on the whole window => at least
    round(0.4*60)=24 requests in [0, 600)."""
    p = base_params()
    p["arrivals"] = "burst"
    p["n_requests"] = 60
    for rep in range(5):
        build(p, rep, tmp_path / f"r{rep}")
        r = read_req(tmp_path / f"r{rep}")
        assert len(r) == 60
        assert (r.t_request_s < p["burst_window_s"]).sum() >= round(0.4 * 60)


# --------------------------------------------------------------------------
# 8. fleet
# --------------------------------------------------------------------------
def test_fleet_hotspot(tmp_path, locs):
    """Contract s3 fleet rules: hotspot vans go to O locations ranked by weight,
    cycling when n_vans > #O locations."""
    O = locs[locs.endpoint == "O"].sort_values("weight", ascending=False)
    for n_vans in (5, len(O) + 7):
        p = base_params()
        p["n_vans"] = n_vans
        p["start_rule"] = "hotspot"
        d = tmp_path / f"v{n_vans}"
        build(p, 0, d)
        f = read_fleet(d)
        assert set(f.columns) == FLEET_COLS
        assert len(f) == n_vans
        assert list(f.van_id) == [f"V{i:02d}" for i in range(1, n_vans + 1)]
        assert (f.capacity == p["capacity"]).all()
        assert (f.shift_start_s == 0).all()
        assert (f.shift_end_s == p["window_s"]).all()
        L = locs.set_index("loc_id")
        assert (L.loc[f.start_loc, "endpoint"] == "O").all()
        assert np.allclose(f.lat, L.loc[f.start_loc, "lat"].to_numpy(), atol=1e-6)
        assert np.allclose(f.lon, L.loc[f.start_loc, "lon"].to_numpy(), atol=1e-6)
        ranked_w = O.weight.to_numpy()
        got_w = L.loc[f.start_loc, "weight"].to_numpy()
        exp_w = np.array([ranked_w[i % len(O)] for i in range(n_vans)])
        assert np.allclose(got_w, exp_w)
        if n_vans == 5:  # top-5 weights are distinct in the April data
            assert list(f.start_loc) == list(O.loc_id.head(5))
        else:
            assert f.start_loc.iloc[len(O)] == f.start_loc.iloc[0]


def test_fleet_depot(tmp_path, locs):
    """Contract s3 fleet rules: depot => all vans at one location, the highest
    weight O location in Z08."""
    p = base_params()
    p["start_rule"] = "depot"
    p["n_vans"] = 7
    p["capacity"] = 6
    build(p, 0, tmp_path)
    f = read_fleet(tmp_path)
    assert len(f) == 7
    assert (f.capacity == 6).all()
    assert f.start_loc.nunique() == 1
    Z = locs[(locs.endpoint == "O") & (locs.zone_id == "Z08")]
    expected = Z.sort_values("weight", ascending=False).loc_id.iloc[0]
    assert f.start_loc.iloc[0] == expected
    meta = LOC_CSV.with_name("locations_v1_meta.json")
    if meta.exists():  # contract: depot "named in locations_v1 metadata"
        assert json.loads(meta.read_text()).get("depot_loc") == expected
    assert (locs.set_index("loc_id").loc[f.start_loc, "zone_id"] == "Z08").all()
    assert (f.shift_end_s == p["window_s"]).all()
    assert (f.shift_start_s == 0).all()


# --------------------------------------------------------------------------
# 9. pooled sampling: generator validation against the fitted table
# --------------------------------------------------------------------------
@pytest.mark.slow
def test_pooled_sampling_matches_fit(tmp_path, locs):
    """Generator validation: pooling replicates of the base cell reproduces the
    fitted table's zone-level origin/destination shares (0.015 abs), the party
    mean implied by party_probs (0.05) and the patience median (10%).
    Uses 200 replicates (6,000 requests); if one build takes > 0.27 s (projected
    > 55 s) it falls back to 100 replicates and a 0.02 zone tolerance."""
    p = base_params()
    reps, tol = 200, 0.015
    frames = []
    t0 = time.time()
    build(p, 0, tmp_path / "r0")
    per = time.time() - t0
    if per * 200 > 55:
        reps, tol = 100, 0.02
    frames.append(read_req(tmp_path / "r0"))
    for rep in range(1, reps):
        build(p, rep, tmp_path / f"r{rep}")
        frames.append(read_req(tmp_path / f"r{rep}"))
    R = pd.concat(frames, ignore_index=True)
    assert len(R) == reps * p["n_requests"]

    table, _ = fit(p["beta_per_min"], p["direction"], float(p["min_trip_s"]))
    zone = locs.set_index("loc_id").zone_id
    exp_o = table.assign(z=table.o_loc.map(zone)).groupby("z").prob.sum()
    exp_d = table.assign(z=table.d_loc.map(zone)).groupby("z").prob.sum()
    emp_o = R.o_zone.value_counts(normalize=True)
    emp_d = R.d_zone.value_counts(normalize=True)
    zones = sorted(set(exp_o.index) | set(exp_d.index) | set(emp_o.index) | set(emp_d.index))
    for z in zones:
        assert abs(emp_o.get(z, 0.0) - exp_o.get(z, 0.0)) < tol, f"origin share {z}"
        assert abs(emp_d.get(z, 0.0) - exp_d.get(z, 0.0)) < tol, f"dest share {z}"

    pp = {int(k): v for k, v in p["party_probs"].items()}
    tot = sum(pp.values())
    implied = sum(k * v for k, v in pp.items()) / tot
    assert abs(R.party.mean() - implied) < 0.05
    assert abs(R.patience_s.median() / p["patience"]["median_s"] - 1) < 0.10


# --------------------------------------------------------------------------
# 10-11. ladder and grid
# --------------------------------------------------------------------------
LADDER = {"S0": (1, 2), "S1": (1, 6), "S2": (3, 15), "M": (5, 30),
          "M60": (5, 60), "L170": (27, 170), "L300": (27, 300)}


def _need(path):
    if not path.exists():
        pytest.skip(f"{path.relative_to(ROOT)} not built yet")


def test_ladder_sizes():
    """Contract s4: ladder S0..L300 exist with the stated vans and requests."""
    _need(SCEN / "ladder")
    for name, (nv, nr) in LADDER.items():
        d = SCEN / "ladder" / name
        assert d.is_dir(), name
        for f in ("requests.csv", "fleet.csv", "scenario.json"):
            assert (d / f).exists(), f"{name}/{f}"
        assert len(read_fleet(d)) == nv, name
        assert len(read_req(d)) == nr, name


def test_frozen_hashes_cover_ladder_and_match_files():
    """Contract s4: FROZEN.json maps each ladder id to its content_hash, which
    equals the hash in that folder's scenario.json."""
    _need(SCEN / "ladder")
    _need(SCEN / "FROZEN.json")
    frozen = json.loads((SCEN / "FROZEN.json").read_text())
    assert set(LADDER) <= set(frozen)
    for name in LADDER:
        sj = json.loads((SCEN / "ladder" / name / "scenario.json").read_text())
        assert frozen[name] == sj["content_hash"], name


@pytest.mark.slow
def test_frozen_hashes_rebuild(tmp_path):
    """Contract s4 + s3: rebuilding each generated ladder scenario (M required;
    S1, S2, M60, L170, L300 too) from its saved params + replicate reproduces the
    frozen content_hash. S0 is hand-written and is not rebuilt."""
    _need(SCEN / "ladder")
    _need(SCEN / "FROZEN.json")
    frozen = json.loads((SCEN / "FROZEN.json").read_text())
    for name in ("M", "S1", "S2", "M60", "L170", "L300"):
        sj = json.loads((SCEN / "ladder" / name / "scenario.json").read_text())
        out = build(sj["params"], sj["replicate"], tmp_path / name)
        assert out["content_hash"] == frozen[name], name
        for f in ("requests.csv", "fleet.csv"):
            assert (tmp_path / name / f).read_bytes() == \
                (SCEN / "ladder" / name / f).read_bytes(), f"{name}/{f}"


def test_grid_manifest():
    """Contract s4: manifest.csv (cell, replicate, content_hash) has 30
    replicates per cell, unique (cell, replicate), and hashes that match each
    folder's scenario.json."""
    _need(SCEN / "grid" / "manifest.csv")
    m = pd.read_csv(SCEN / "grid" / "manifest.csv")
    assert {"cell", "replicate", "content_hash"} <= set(m.columns)
    assert not m.duplicated(["cell", "replicate"]).any()
    for cell, g in m.groupby("cell"):
        assert len(g) == 30, cell
        assert sorted(g.replicate) == list(range(30)), cell
    for row in m.itertuples():
        d = SCEN / "grid" / row.cell / f"r{int(row.replicate):02d}"
        sj = json.loads((d / "scenario.json").read_text())
        assert sj["content_hash"] == row.content_hash, (row.cell, row.replicate)
        assert sj["replicate"] == row.replicate


@pytest.mark.slow
def test_grid_sample_rebuild(tmp_path):
    """Contract s4 + s3: replicate 0 of every grid cell rebuilds to the
    manifest hash."""
    _need(SCEN / "grid" / "manifest.csv")
    m = pd.read_csv(SCEN / "grid" / "manifest.csv")
    for row in m[m.replicate == 0].itertuples():
        d = SCEN / "grid" / row.cell / "r00"
        sj = json.loads((d / "scenario.json").read_text())
        out = build(sj["params"], sj["replicate"], tmp_path / row.cell)
        assert out["content_hash"] == row.content_hash, row.cell
