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


def test_m5b_refuses_until_preregistration_frozen(monkeypatch, tmp_path):
    for text in (None, "**Status: DRAFT (not frozen).**"):
        f = tmp_path / "prereg.md"
        if text is None:
            f.unlink(missing_ok=True)
        else:
            f.write_text(text)
        monkeypatch.setattr(m5, "PREREG", f)
        with pytest.raises(SystemExit):
            m5.cmd_run("m5b_A", 1)


def test_run_order_follows_d61():
    a = m5.STAGES["m5b_A"]["runs"]
    assert [c.name for c, n in a[:4]] == ["base5_C_R0_t120", "base5_G_R0_t120"] * 2
    assert [n for c, n in a[:4]] == ["r00", "r00", "r01", "r01"]
    names = [c.name for c, _ in a]
    assert names.count("base5_G_R0_t120") == 30                 # cell 1's G reused by cell 4, not re-run
    firsts = [names.index(x) for x in ("base5_C_R0_t120", "base6_C_R0_t120", "base5_C_R1-10_t120",
                                         "base5_C_R0_t60", "base5_C_R0_t300")]
    assert firsts == sorted(firsts) and len(a) == 30 * 8          # 8 distinct run cells: cell 4 has two C runs and no G
    b = m5.STAGES["m5b_B"]
    assert [n for _, n in b["runs"][::2]] == m5.NIGHTS30 and b["max_workers"] == 2


def test_paired_bootstrap_and_verdict_on_synthetic_values():
    mean, lo, hi, n = m5.paired_bootstrap([-1.0] * 30)
    assert (mean, lo, hi, n) == (-1.0, -1.0, -1.0, 30)
    assert m5.paired_bootstrap([1, 2, 3]) == m5.paired_bootstrap([1, 2, 3])          # fixed seed
    assert m5.verdict(-3.5, -0.4) == "C better"
    assert m5.verdict(-1.0, -0.1) == "C better (and within ±2 pp)"
    assert m5.verdict(-1.5, 1.9) == "practically equivalent"
    assert m5.verdict(0.3, 2.5) == "G better"
    assert m5.verdict(-2.5, 1.0) == "inconclusive at this scale"


def test_usable_prefix_stops_at_first_gap_or_late_run(tmp_path):
    c, g = m5.Cell("a", "base", 5, "C"), m5.Cell("b", "base", 5, "G")

    def put(cell, n, status="ok", t="2026-11-18T10:00:00-0500"):
        d = tmp_path / cell.name / n / "rep1"
        d.mkdir(parents=True)
        (d / "manifest.json").write_text(json.dumps({"status": status, "finished_at": t}))
    for n in ("r00", "r01", "r03"):
        put(c, n); put(g, n)
    put(c, "r02"); put(g, "r02", t="2026-11-19T13:00:00-0500")          # G of r02 finished after the cutoff
    cut = "2026-11-19T12:00:00-05:00"
    assert m5.usable_prefix((c, g), cut, tmp_path) == ["r00", "r01"]
    assert m5.usable_prefix((c, g), "2026-11-20T00:00:00-05:00", tmp_path) == ["r00", "r01", "r02", "r03"]


def test_compare_pipeline_g_against_itself(tmp_path, monkeypatch, capsys):
    """End-to-end check of cmd_compare before any real M5b run: G compared with itself must give exactly 0."""
    monkeypatch.setattr(m5, "M5", tmp_path)
    pre = tmp_path / "prereg.md"
    pre.write_text("**Status: FROZEN test**")
    monkeypatch.setattr(m5, "PREREG", pre)
    cell = m5.Cell("base5_G_R0_t120", "base", 5, "G")
    monkeypatch.setitem(m5.STAGES, "t", {"runs": [], "reps": 1, "folder": "m5b"})
    assert m5.run_one(("t", cell, "r00", 1, m5.code_fingerprint()))["status"] == "ok"
    monkeypatch.setattr(m5, "COMPARISONS", [("1 self", cell, cell)])
    monkeypatch.setitem(m5.M5B_CUTOFFS, "test", "2100-01-01T00:00:00-05:00")
    m5.cmd_compare("test")
    capsys.readouterr()                                          # values are not shown
    import pandas as pd
    per = pd.read_csv(tmp_path / "m5b" / "comparison_test_per_night.csv")
    assert len(per) == 1 and per.C_not_reached_20_pp.equals(per.G_not_reached_20_pp)
    assert "| 1 self | 1 | +0.00 |" in (tmp_path / "m5b" / "comparison_test.md").read_text()
