"""Checks on the M5 runner (plan v2 M5, D-60). Uses G so it runs in seconds; reads no rider outcome.

1. The first-hour slice is exactly the first 64 (base) / 83 (high) requests and keeps the frozen night's hash check.
2. A full run_one writes the logs and a manifest whose run checks all pass, with the algorithm recorded.
3. M5b refuses to run before the preregistration note exists.
Skips if L6 has not been built (data/ is gitignored).
"""
import dataclasses
import json
from pathlib import Path

import pytest

from sim import m5

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (ROOT / "data" / "scenarios" / "v2" / "FROZEN_v2_L6.json").exists(),
                                reason="L6 not built")


@pytest.mark.parametrize("pattern,fleet,n", [("base", 5, 64), ("base", 6, 64), ("high", 5, 83)])
def test_first_hour_slice(pattern, fleet, n):
    cell = m5.Cell("t", pattern, fleet, "G")
    scen, key = m5.first_hour(cell, "r00")
    assert key == f"L6/{pattern}_{fleet}/r00"
    assert len(scen.requests) == n and max(r.t for r in scen.requests) < 3600
    assert set(scen.hidden) == {r.rid for r in scen.requests}
    assert len(scen.vans) == fleet


def test_run_one_writes_a_checked_run(tmp_path, monkeypatch):
    monkeypatch.setattr(m5, "M5", tmp_path)
    cell = m5.Cell("base5_G_R0_t120", "base", 5, "G")
    res = m5.run_one(("test", cell, "r01", 1, m5.code_fingerprint()))
    assert res["status"] == "ok", res
    d = m5.run_dir("test", cell, "r01", 1)
    man = json.loads((d / "manifest.json").read_text())
    assert all(man["checks"].values())
    assert man["config"]["algorithm"] == "G" and man["slice_requests"] == 64
    assert {p.name for p in d.iterdir()} == {"events.csv", "outcomes.csv", "epochs.jsonl.gz", "manifest.json"}
    assert m5.done("test", cell, "r01", 1, man["code_fingerprint"])
    with pytest.raises(SystemExit):                       # a different configuration is refused, not mixed
        m5.done("test", dataclasses.replace(cell, tick_s=60), "r01", 1, man["code_fingerprint"])


def test_m5b_refuses_before_preregistration(monkeypatch, tmp_path):
    monkeypatch.setattr(m5, "PREREG", tmp_path / "missing.md")
    monkeypatch.setitem(m5.STAGES, "m5b", {"cells": [], "nights": [], "reps": 1})
    with pytest.raises(SystemExit):
        m5.cmd_run("m5b", 1)
