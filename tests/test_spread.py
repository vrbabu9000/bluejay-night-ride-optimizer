"""Checks on the dispersed-geography variant (D-34; src/scenario/spread.py, build_dispersed_v2.py).

Skips if the variant has not been built (data/ is gitignored).
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
DV = ROOT / "data" / "scenarios" / "v2_dispersed"
REF = ROOT / "data" / "scenarios" / "v2"
pytestmark = pytest.mark.skipif(not (DV / "FROZEN_v2_dispersed.json").exists(), reason="dispersed variant not built")


@pytest.fixture(scope="module")
def sites():
    return pd.read_csv(P / "locations_dispersed_v1.csv")


@pytest.fixture(scope="module")
def sec():
    m = pd.read_csv(P / "tt_locations_dispersed_v1.csv")
    return dict(zip(zip(m.origin, m.dest), m.seconds))


def test_coarse_set_is_all_city_view_points(sites):
    """Every city-view bubble (and only those) is spread, into exactly 6 satellites."""
    view = pd.read_csv(P / "zone_points_v0.csv").set_index("bubble_id").view
    city = set(view[view == "city"].index)
    sat = sites[sites.is_satellite]
    assert set(sat.parent_loc) == city and len(city) == 19
    assert (sat.groupby("parent_loc").size() == 6).all()


def test_cluster_mass_and_labels_preserved(sites):
    """Satellite weights sum to the parent's April weight; zone and endpoint are inherited."""
    ref = sites[~sites.is_satellite].set_index("loc_id")
    sat = sites[sites.is_satellite]
    w = sat.groupby("parent_loc").weight.sum()
    assert np.allclose(w.to_numpy(), ref.weight.reindex(w.index).to_numpy(), rtol=0, atol=1e-9)
    assert (sat.zone_id.to_numpy() == ref.zone_id.reindex(sat.parent_loc).to_numpy()).all()
    assert (sat.endpoint.to_numpy() == ref.endpoint.reindex(sat.parent_loc).to_numpy()).all()


def test_satellites_are_valid_road_points(sites):
    """Snapped to a road within 75 m, within 400 m (+ snap) of the bubble, >= 100 m from sibling satellites."""
    sat = sites[sites.is_satellite]
    assert (sat.snap_m <= 75).all()
    assert (sat.offset_m <= 400 + 75).all()
    k = 111_320.0
    for _, grp in sat.groupby("parent_loc"):
        xy = np.c_[grp.lon * k * math.cos(math.radians(39.32)), grp.lat * k]
        d = np.hypot(*(xy[:, None, :] - xy[None, :, :]).transpose(2, 0, 1))
        assert d[np.triu_indices(len(grp), 1)].min() >= 99.0


def test_routing_complete_and_reference_consistent(sites, sec):
    """All ordered pairs present and finite; original-point pairs equal the canonical v2 matrix exactly."""
    ids = sites.loc_id.tolist()
    assert len(sec) == len(ids) ** 2 and all(np.isfinite(v) for v in sec.values())
    v2 = pd.read_csv(P / "tt_locations_v2.csv")
    assert all(sec[(a, b)] == s for a, b, s in zip(v2.origin, v2.dest, v2.seconds))


def test_dispersed_l5_aligned_with_reference(sec):
    """Times, party sizes, rider traits, availability and cluster-level O-D equal the reference night;
    each endpoint is its cluster or one of that cluster's satellites; the 60-s minimum trip holds."""
    sites = pd.read_csv(P / "locations_dispersed_v1.csv").set_index("loc_id")
    nights = sorted((DV / "L5").glob("r*"))
    assert len(nights) == 30
    for f in nights:
        d, r = pd.read_csv(f / "requests.csv"), pd.read_csv(REF / "L5" / f.name / "requests.csv")
        for c in ("request_id", "t_request_s", "party", "o_zone", "d_zone"):
            assert (d[c].to_numpy() == r[c].to_numpy()).all()
        assert (d.o_cluster.to_numpy() == r.o_loc.to_numpy()).all() and (d.d_cluster.to_numpy() == r.d_loc.to_numpy()).all()
        assert (sites.parent_loc.reindex(d.o_loc).to_numpy() == d.o_cluster.to_numpy()).all()
        assert (sites.parent_loc.reindex(d.d_loc).to_numpy() == d.d_cluster.to_numpy()).all()
        assert (d.direct_s >= 60).all()
        assert all(round(sec[(a, b)]) == s for a, b, s in zip(d.o_loc, d.d_loc, d.direct_s))
        for name in ("latent.csv", "availability.csv"):
            assert (f / name).read_bytes() == (REF / "L5" / f.name / name).read_bytes()


def test_rebuild_reproducible_and_reference_untouched(tmp_path, monkeypatch):
    """Rebuilding the variant reproduces its frozen hashes; the reference FROZEN_v2 is what the variant recorded."""
    import sys
    sys.path.insert(0, str(ROOT / "src" / "scenario"))
    import build_dispersed_v2 as b
    monkeypatch.setattr(b, "OUT", tmp_path)
    b.main()
    assert json.loads((tmp_path / "FROZEN_v2_dispersed.json").read_text()) == json.loads((DV / "FROZEN_v2_dispersed.json").read_text())
    import hashlib
    rec = json.loads((DV / "MANIFEST.json").read_text())["reference_frozen_sha256"]
    assert hashlib.sha256((REF / "FROZEN_v2.json").read_bytes()).hexdigest() == rec
