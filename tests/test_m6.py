"""Checks on the M6 runner (full normal evening; plan: docs/technical/research_notes/m6_plan_2026-11.md).

1. M6's cells, settings and configuration are M5b's, except the slice ("full night").
2. The full night is the frozen L6 base_5 night with all 168 requests (hash checked).
3. A full-night G run passes every check, including the full-night backlog check that replaces the first-hour one.
4. C runs on a short cut of a night (seconds) and passes every check; report and status read the results.
5. The runner refuses to start until the M6 plan is frozen, and refuses any other code fingerprint.
Skips if L6 has not been built (data/ is gitignored).
"""
import dataclasses
import json
from pathlib import Path

import pytest

from sim import m5, m6

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (ROOT / "data" / "scenarios" / "v2" / "FROZEN_v2_L6.json").exists(),
                                reason="L6 not built")


def test_cells_and_config_are_m5b_except_the_slice():
    assert [c.name for c in m6.CELLS] == ["base5_C_R0_t120", "base5_G_R0_t120"]
    assert m6.CELLS[0] == m5.COMPARISONS[0][1] and m6.CELLS[1] == m5.COMPARISONS[0][2]
    assert m6.RUNS[:5] == [(m6.CELLS[0], n) for n in m6.NIGHTS] and m6.DEMO_NIGHT == "r00"
    for c in m6.CELLS:
        a, b = m5.config(c), m6.config(c)
        assert b.pop("slice") == "full night" and a.pop("slice").startswith("t_request_s <")
        assert a == b


def test_full_night_has_every_request():
    scen, key = m6.full_night(m6.CELLS[1], "r00")
    assert key == "L6/base_5/r00" and len(scen.requests) == 168
    hours = [sum(lo <= r.t < hi for r in scen.requests) for lo, hi, _ in m6.HOURS[:3]]
    assert hours == [64, 50, 54]
    first, _ = m5.first_hour(m6.CELLS[1], "r00")
    assert scen.requests[:64] == first.requests


def test_full_night_g_run_passes_every_check(tmp_path):
    fp = m5.code_fingerprint()
    res = m6.run_one((m6.CELLS[1], "r00", fp), root=tmp_path)
    assert res["status"] == "ok", res
    man = json.loads((m6.run_dir(m6.CELLS[1], "r00", root=tmp_path) / "manifest.json").read_text())
    assert man["requests"] == 168 and man["config"]["slice"] == "full night"
    assert m6.NEW_BACKLOG in man["checks"] and m6.OLD_BACKLOG not in man["checks"]
    assert all(man["checks"].values())


def test_c_on_a_short_cut_then_report_and_status(tmp_path, capsys):
    def cut(cell, night):                       # first 12 requests: C finishes in seconds
        scen, key = m6.full_night(cell, night)
        reqs = scen.requests[:12]
        return dataclasses.replace(scen, requests=reqs, hidden={r.rid: scen.hidden[r.rid] for r in reqs}), key

    fp = m5.code_fingerprint()
    for cell in m6.CELLS:
        res = m6.run_one((cell, "r00", fp), scen_fn=cut, root=tmp_path)
        assert res["status"] == "ok", res
    m6.cmd_status(root=tmp_path)
    m6.cmd_report(root=tmp_path)
    out = capsys.readouterr().out
    assert "base5_C_R0_t120        1/5 finished" in out and "r00 (demonstration) | C |" in out
    assert (tmp_path / "report.md").exists()
    row = m6.compute_row(m6.run_dir(m6.CELLS[0], "r00", root=tmp_path))
    assert row["failed_checks"] == "none" and "optimal" in row["solver_status"]


def test_runner_guards(monkeypatch, tmp_path):
    draft = tmp_path / "plan.md"
    draft.write_text("**Status: DRAFT (not frozen).**")
    monkeypatch.setattr(m6, "PLAN", draft)
    with pytest.raises(SystemExit, match="frozen"):
        m6.cmd_run(1)
    draft.write_text("**Status: FROZEN 2026-11-20**")
    monkeypatch.setattr(m6, "CODE_FINGERPRINT", "000000000000")
    with pytest.raises(SystemExit, match="fingerprint"):
        m6.cmd_run(1)
