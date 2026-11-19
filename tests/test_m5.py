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


def test_cf_cell_and_m5c_guard(monkeypatch, tmp_path):
    """C-F (M5c, D-63) differs from C only in the drop-order flag; M5b configs are unchanged; M5c waits for its freeze."""
    cf, c = m5._c("high", 5, "C", fixed_drop=True), m5._c("high", 5, "C")
    assert cf.name == "high5_CF_R0_t120" and c.name == "high5_C_R0_t120"
    assert m5.policy(cf).dispatcher.fix_existing_drop_order and not m5.policy(c).dispatcher.fix_existing_drop_order
    assert "fixed_drop" not in m5.config(c)["cell"] and m5.config(cf)["cell"]["fixed_drop"] is True
    assert [x.name for x, _ in m5.STAGES["m5c"]["runs"][::30]] == ["high5_CF_R0_t120", "base5_CF_R0_t120"]
    f = tmp_path / "m5c.md"
    f.write_text("**Status: DRAFT (not frozen).**")
    monkeypatch.setattr(m5, "PREREG_C", f)
    with pytest.raises(SystemExit):
        m5.cmd_run("m5c", 1)


def test_m5c_noninferiority_reading():
    assert m5.noninferiority(-1.0, 1.5) == "C-F non-inferior"
    assert m5.noninferiority(-3.0, -0.5) == "C-F non-inferior (and better than C)"
    assert m5.noninferiority(2.5, 5.0) == "C-F worse by more than the margin"
    assert m5.noninferiority(0.5, 3.0) == "inconclusive at this scale"


def test_m5c_compare_pipeline_g_against_itself(tmp_path, monkeypatch, capsys):
    """End-to-end check of the M5c analysis before any C-F run: one arm compared with itself gives exactly 0."""
    monkeypatch.setattr(m5, "M5", tmp_path)
    for name in ("PREREG", "PREREG_C"):
        f = tmp_path / f"{name}.md"
        f.write_text("**Status: FROZEN test**")
        monkeypatch.setattr(m5, name, f)
    cell = m5.Cell("base5_G_R0_t120", "base", 5, "G")
    monkeypatch.setitem(m5.STAGES, "t", {"runs": [], "reps": 1, "folder": "m5b"})
    assert m5.run_one(("t", cell, "r00", 1, m5.code_fingerprint()))["status"] == "ok"
    monkeypatch.setattr(m5, "M5C_PAIRS", [("self", cell, cell, cell)])
    m5.cmd_compare_m5c(root_c=tmp_path / "m5b", root_b=tmp_path / "m5b")
    capsys.readouterr()                                          # values are not shown
    text = (tmp_path / "m5b" / "comparison_m5c.md").read_text()
    assert "| self | 1 | +0.00 |" in text and "| self | 1 |" in text.split("## Compute")[1]


def test_cs6_switch_and_m5d_guard(monkeypatch, tmp_path):
    """C-S6 (M5d, D-64): a van keeps its drop order only at >= 6 parties aboard/committed; C and C-F unchanged;
    M5a-M5c configurations stay byte-equal; M5d waits for its freeze; the fresh nights are r30-r59."""
    from sim import dispatch as D

    def van(k):
        riders = tuple(D.Rider(f"R{i:03d}", "X", 1, 0, 0, 60) for i in range(k))
        return D.VanState("V1", 12, "X", 0, riders, ())
    s6 = D.Config(fix_drop_order_min_parties=6)
    assert [D.fixes_drop_order(van(k), s6) for k in (0, 5, 6, 9)] == [False, False, True, True]
    assert not any(D.fixes_drop_order(van(k), D.Config()) for k in (0, 6, 9))
    assert all(D.fixes_drop_order(van(k), D.Config(fix_existing_drop_order=True)) for k in (0, 6))
    cs6, c = m5._c("high", 5, "C", drop_switch=6), m5._c("high", 5, "C")
    assert cs6.name == "high5_CS6_R0_t120" and m5.policy(cs6).dispatcher.fix_drop_order_min_parties == 6
    assert "drop_switch" not in m5.config(c)["cell"] and "fix_drop_order_min_parties" not in m5.config(c)["dispatcher"]
    assert m5.config(cs6)["cell"]["drop_switch"] == 6 and not m5.policy(cs6).dispatcher.fix_existing_drop_order
    assert m5.NIGHTS_FRESH[0] == "r30" and len(m5.NIGHTS_FRESH) == 30 and not set(m5.NIGHTS_FRESH) & set(m5.NIGHTS30)
    assert {n for _, n in m5.STAGES["m5d_C"]["runs"] + m5.STAGES["m5d_rest"]["runs"]} == set(m5.NIGHTS_FRESH)
    f = tmp_path / "m5d.md"
    f.write_text("**Status: DRAFT (not frozen).**")
    monkeypatch.setattr(m5, "PREREG_D", f)
    for stage in ("m5d_C", "m5d_rest"):
        with pytest.raises(SystemExit):
            m5.cmd_run(stage, 1)


def test_fresh_night_first_hour_slice():
    for pattern, n in (("base", 64), ("high", 83)):
        scen, key = m5.first_hour(m5.Cell("t", pattern, 5, "G"), "r30")
        assert key == f"L6/{pattern}_5/r30" and len(scen.requests) == n


def test_guardrail_check_d62_fix():
    """The M5b r26 case (D-62): a no-show at the drop's own timestamp counts, and one equal-cost re-sequencing dwell
    per no-show is allowed. An excess without a no-show, or beyond the allowance, is still unexplained."""
    import pandas as pd
    from types import SimpleNamespace
    from sim.l5_pilot import guardrail_excesses
    scen = SimpleNamespace(requests=[SimpleNamespace(rid=r, o="A", d="B") for r in ("R1", "R2", "R3", "R4")])
    travel = SimpleNamespace(van=lambda a, b: 600)              # guardrail = max(1500, 2*600 + 300) = 1500 s
    out = pd.DataFrame({"request_id": ["R1", "R2", "R3", "R4"], "outcome": ["van_completed"] * 4,
                        "van": ["V5"] * 3 + ["V1"], "pickup_s": [2000, 2000, 2000, 2000],
                        "drop_s": [4254, 4500, 4600, 4500],
                        "ride_s": [1500 + 24, 1500 + 177, 1500 + 194, 1500 + 10]})
    ev = pd.DataFrame({"event": ["state"], "state_to": ["noshow_van"], "van": ["V5"], "t_s": [4254]})
    got = {e["request"]: e["attributed"] for e in guardrail_excesses({"out": out, "events": ev}, scen, travel)}
    assert got == {"R1": True, "R2": True, "R3": False, "R4": False}


def test_m5d_compare_pipeline_and_night_rule(tmp_path, monkeypatch, capsys):
    """M5d analysis before any M5d run: one arm compared with itself gives exactly 0; the prefix rule stops at the
    first night not finished by the cutoff; a night with a failed check is finished but not used."""
    monkeypatch.setattr(m5, "M5", tmp_path)
    f = tmp_path / "PREREG_D.md"
    f.write_text("**Status: FROZEN test**")
    monkeypatch.setattr(m5, "PREREG_D", f)
    cell = m5.Cell("base5_G_R0_t120", "base", 5, "G")
    monkeypatch.setitem(m5.STAGES, "t", {"runs": [], "reps": 1, "folder": "m5d"})
    for n in ("r30", "r31", "r33"):
        assert m5.run_one(("t", cell, n, 1, m5.code_fingerprint()))["status"] == "ok"
    man = tmp_path / "m5d" / cell.name / "r31" / "rep1" / "manifest.json"
    j = json.loads(man.read_text()); j["status"] = "checks_failed"; man.write_text(json.dumps(j))
    prefix, used = m5.m5d_nights((cell, cell, cell), "2100-01-01T00:00:00-05:00", tmp_path / "m5d")
    assert prefix == ["r30", "r31"] and used == ["r30"]
    assert m5.m5d_nights((cell,), "2000-01-01T00:00:00-05:00", tmp_path / "m5d") == ([], [])
    monkeypatch.setattr(m5, "M5D_PAIRS", [("self", cell, cell, cell)])
    m5.cmd_compare_m5d("2100-01-01T00:00:00-05:00", tmp_path / "m5d")
    capsys.readouterr()
    text = (tmp_path / "m5d" / "comparison_m5d.md").read_text()
    assert "| self | 2 / 1 | +0.00 |" in text
