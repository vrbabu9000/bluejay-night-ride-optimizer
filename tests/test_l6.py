"""Checks on the L6 nights (Phase 4 M4, D-59; plan v2 checks 1, 3 and 4).

Hour counts are recomputed here by hand from spec §3.2, not with the generator's rounding helper.
Skips if the L6 nights have not been built (data/ is gitignored).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scenario import generator_v2 as g
from sim import inputs

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "data" / "scenarios" / "v2"
L6 = V2 / "L6"
pytestmark = pytest.mark.skipif(not (L6 / "base_5" / "r00").exists(), reason="L6 not built")
EXPECTED = {"base": (64, 50, 54), "high": (83, 66, 70)}


def nights(cell):
    return sorted((L6 / cell).glob("r*"))


def test_hour_counts_by_hand():
    """Spec §3.2: 5 vans x rho = 64.25, 50.50, 53.55 -> total 168; floors 64+50+53 = 167; the one leftover unit goes
    to the largest fraction (.55, hour 20) -> 64/50/54. High: x1.3 -> 83.525, 65.65, 69.615 -> 219; floors 217;
    two units to .65 and .615 -> 83/66/70."""
    assert g.largest_remainder([64.25, 50.5, 53.55]) == (64, 50, 54)
    assert g.largest_remainder([83.525, 65.65, 69.615]) == (83, 66, 70)
    for pat, exp in EXPECTED.items():
        assert g.l6_hour_counts(pat) == exp


@pytest.mark.parametrize("cell,pat", [("base_5", "base"), ("base_6", "base"), ("high_5", "high")])
def test_counts_and_order(cell, pat):
    fs = nights(cell)
    assert len(fs) == 30
    for f in fs:
        r = pd.read_csv(f / "requests.csv")
        per_hour = tuple(np.bincount(r.t_request_s // 3600, minlength=3)[:3])
        assert per_hour == EXPECTED[pat] and r.t_request_s.max() < 3 * 3600
        assert r.t_request_s.is_monotonic_increasing and r.request_id.is_unique
        n0 = EXPECTED[pat][0]
        assert (r.t_request_s.iloc[:n0] < 3600).all() and (r.t_request_s.iloc[n0:] >= 3600).all()


def test_frozen_and_loadable():
    frozen = json.loads((V2 / "FROZEN_v2_L6.json").read_text())
    assert set(frozen).isdisjoint(json.loads((V2 / "FROZEN_v2.json").read_text()))
    keys = [k for k in frozen if k.startswith("L6/")]
    assert len(keys) == 90
    sc = inputs.load("L6/base_5/r00", check_hash=False)   # L6 hashes live in FROZEN_v2_L6.json (inputs.py unchanged)
    assert sc.content_hash == frozen["L6/base_5/r00"]
    assert len(sc.requests) == 168 and len(sc.vans) == 5


def test_rebuild_is_identical():
    """Rebuilding a night in memory reproduces the frozen content hash."""
    frozen = json.loads((V2 / "FROZEN_v2_L6.json").read_text())
    for pat, fleet, r in (("base", 5, 0), ("base", 6, 7), ("high", 5, 29)):
        req, lat, av, params = g.build_l6(pat, r, n_vans=fleet)
        blob = b"".join(g.csv_bytes(x) for x in (req, lat, av))
        canon = json.dumps(params, sort_keys=True, separators=(",", ":")).encode()
        import hashlib
        assert hashlib.sha256(blob + canon).hexdigest() == frozen[f"L6/{pat}_{fleet}/r{r:02d}"]


def test_six_vans_same_requests():
    """D-37: the six-van night carries byte-identical requests and latent draws; only availability differs."""
    for a, b in zip(nights("base_5"), nights("base_6")):
        for name in ("requests.csv", "latent.csv"):
            assert (a / name).read_bytes() == (b / name).read_bytes()
        assert len(pd.read_csv(a / "availability.csv")) == 5 and len(pd.read_csv(b / "availability.csv")) == 6


def test_patterns_differ_and_replicates_differ():
    """D-49: patterns have their own streams, so base and high nights with the same replicate are different nights."""
    b0 = pd.read_csv(nights("base_5")[0] / "requests.csv")
    h0 = pd.read_csv(nights("high_5")[0] / "requests.csv")
    b1 = pd.read_csv(nights("base_5")[1] / "requests.csv")
    assert not b0.t_request_s.iloc[:64].equals(h0.t_request_s.iloc[:64])
    assert not b0.t_request_s.equals(b1.t_request_s)


def test_seed_isolation(monkeypatch):
    """Changing one component's stream changes only that component."""
    req0, lat0, _, _ = g.build_l6("base", 3)
    real = g.stream

    def shifted(level, pattern, replicate, component):
        return real(level, pattern, replicate + 1000 if component == "patience" else replicate, component)

    monkeypatch.setattr(g, "stream", shifted)
    req1, lat1, _, _ = g.build_l6("base", 3)
    assert req0.equals(req1)
    assert not lat0.patience_s.equals(lat1.patience_s)
    assert lat0.drop(columns="patience_s").equals(lat1.drop(columns="patience_s"))
