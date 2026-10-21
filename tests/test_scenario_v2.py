"""Checks on the v2 validation levels (scenario_spec v0.2 §8, §12).

The hand-check arithmetic is recomputed here from the travel matrix directly, not with the generator's helpers.
Skips if the levels have not been built (data/ is gitignored).
"""
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "data" / "scenarios" / "v2"
pytestmark = pytest.mark.skipif(not (V2 / "FROZEN_v2.json").exists(), reason="v2 levels not built")

REQ_COLS = ["request_id", "t_request_s", "o_loc", "d_loc", "o_zone", "d_zone", "party", "direct_s"]
LAT_COLS = ["request_id", "patience_s", "noshow_u", "consent_u", "lyft_delay_s", "lyft_noshow_u", "eta_noise"]
AV_COLS = ["van_id", "start_loc", "capacity", "avail_start_s", "avail_end_s"]


@pytest.fixture(scope="module")
def sec():
    tt = pd.read_csv(ROOT / "data" / "processed" / "tt_locations_v2.csv")
    return {(a, b): int(round(s)) for a, b, s in zip(tt.origin, tt.dest, tt.seconds)}


def folders():
    return [V2 / lv for lv in ("L1", "L2", "L3", "L4")] + sorted((V2 / "L5").glob("r*"))


def test_schema_and_counts():
    """Every scenario has the three input files with the spec §10 columns; L5 has 30 nights of 28 requests."""
    for f in folders():
        assert list(pd.read_csv(f / "requests.csv").columns) == REQ_COLS
        assert list(pd.read_csv(f / "latent.csv").columns) == LAT_COLS
        assert list(pd.read_csv(f / "availability.csv").columns) == AV_COLS
        r = pd.read_csv(f / "requests.csv")
        assert r.t_request_s.is_monotonic_increasing and r.request_id.is_unique
    assert len(sorted((V2 / "L5").glob("r*"))) == 30
    assert all(len(pd.read_csv(f / "requests.csv")) == 28 for f in (V2 / "L5").glob("r*"))


def test_rebuild_is_byte_identical(tmp_path, monkeypatch):
    """Same seeds give the same scenarios: rebuilding into a temp folder reproduces every frozen content hash."""
    import sys
    sys.path.insert(0, str(ROOT / "src" / "scenario"))
    import build_levels_v2 as b
    import generator_v2 as g
    monkeypatch.setattr(g, "OUT", tmp_path)
    b.main()
    assert json.loads((tmp_path / "FROZEN_v2.json").read_text()) == json.loads((V2 / "FROZEN_v2.json").read_text())


@pytest.mark.parametrize("lv", ["L1", "L2", "L3"])
def test_l1_l3_handcheck_arithmetic(lv, sec):
    """Both vans are idle at every request; pickup, drop-off and event times follow the stated rules."""
    hc = pd.read_csv(V2 / lv / "handcheck.csv")
    lat = pd.read_csv(V2 / lv / "latent.csv").set_index("request_id")
    free = {"V1": 0, "V2": 0}
    for r in hc.itertuples():
        assert r.t_request_s >= max(free.values()), "a van was still busy when the request arrived"
        assert r.pickup_arrival_s == r.t_request_s + sec[(r.van_from, r.o_loc)]
        if r.outcome == "van_completed":
            assert r.dropoff_s == r.pickup_s + 30 + sec[(r.o_loc, r.d_loc)]
            assert r.van_free_s == r.dropoff_s + 30
        elif r.outcome == "noshow_van":
            assert r.event_s == r.pickup_arrival_s + 180 and lat.loc[r.request_id, "noshow_u"] < 0.047
        elif r.outcome == "cancel_pending_van":
            pat = lat.loc[r.request_id, "patience_s"]
            assert r.event_s == r.t_request_s + pat and r.event_s < r.pickup_arrival_s
            assert r.van_free_s == r.pickup_arrival_s
        free[r.van] = r.van_free_s
    counts = hc.outcome.value_counts().to_dict()
    expected = {"L1": {"van_completed": 16}, "L2": {"van_completed": 14, "noshow_van": 2},
                "L3": {"van_completed": 13, "cancel_pending_van": 3}}[lv]
    assert counts == expected


def test_l1_to_l3_share_requests():
    """L1-L3 use the identical request list; only the latent draws differ."""
    a, b, c = (pd.read_csv(V2 / lv / "requests.csv") for lv in ("L1", "L2", "L3"))
    assert a.equals(b) and a.equals(c)


def test_l4_lyft_bookkeeping(sec):
    """Transfers decided before 18:15: wait = decision + lag + Lyft delay - request (clock not reset);
    a party of 5 is transferred whole to an XL vehicle (decision D-33); a decliner is never transferred."""
    hc = pd.read_csv(V2 / "L4" / "handcheck.csv")
    req = pd.read_csv(V2 / "L4" / "requests.csv").set_index("request_id")
    lat = pd.read_csv(V2 / "L4" / "latent.csv").set_index("request_id")
    tr = hc[hc.decision == "transfer"]
    assert len(tr) > 0 and (tr.decision_s < 900).all()
    assert (tr.wait_s == tr.decision_s + 120 + 480 - tr.t_request_s).all()
    assert (tr.lyft_dropoff_s == tr.lyft_pickup_s + 30 + [sec[(req.loc[i, "o_loc"], req.loc[i, "d_loc"])] for i in tr.request_id]).all()
    party = req.loc[tr.request_id, "party"].to_numpy()
    assert ((party <= 4) == (tr.lyft_class == "standard").to_numpy()).all()
    assert ((party == 5) == (tr.lyft_class == "XL").to_numpy()).all()
    assert (tr.lyft_class == "XL").any(), "L4 must exercise one XL transfer"
    assert (lat.loc[tr.request_id, "consent_u"] < 0.9).all()
    assert (hc[hc.rule == "R0"].decision == "no transfers under R0").all()


def test_l5_design():
    """Burst block holds at least 40% of requests; latent draws are within their stated ranges."""
    for f in (V2 / "L5").glob("r*"):
        r, lat = pd.read_csv(f / "requests.csv"), pd.read_csv(f / "latent.csv")
        assert ((r.t_request_s >= 1200) & (r.t_request_s < 1800)).sum() >= 11
        assert r.party.between(1, 5).all() and (lat.patience_s > 0).all() and (lat.lyft_delay_s > 0).all()
        assert lat[["noshow_u", "consent_u", "lyft_noshow_u"]].stack().between(0, 1).all()
