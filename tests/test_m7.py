"""Checks on the M7 runner and analysis (plan: docs/technical/research_notes/m7_plan_2026-11.md).

1. Grid: 6 rules x 5/6 vans; pilot R0/R3(2) on r30-r39; main nights skip the pilot; settings are M6's except the rule.
2. Analysis on a self-comparison: identical rules give zero differences, "within margin both ways", no dominance.
3. H3 on synthetic nights: 6-van effects half the 5-van ones -> supported; equal -> not settled at zero.
4. Night rule: a missing run ends the prefix; an unexplained failed check drops its night; an explained one keeps it.
5. A short real run (6 vans, R3(2)) passes every check and is labelled stage m7 with the plan hash.
6. The runner refuses an unfrozen plan and another fingerprint; power refuses an incomplete pilot.
"""
import dataclasses
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sim import m5, m6, m7

ROOT = Path(__file__).resolve().parents[1]
HAVE_L6 = (ROOT / "data" / "scenarios" / "v2" / "FROZEN_v2_L6.json").exists()


def test_grid_and_config():
    assert m7.RULES == ["R0", "R1(10)", "R1(15)", "R1u(10)", "R2(15)", "R3(2)"]
    assert not set(m7.PILOT_NIGHTS) & set(m7.MAIN60) and len(m7.MAIN60) == 60 and m7.MAIN30 == m7.MAIN60[:30]
    pilot = m7.runs("pilot")
    assert len(pilot) == 20 and {c.rule for c, _ in pilot} == {"R0", "R3(2)"} and {c.fleet for c, _ in pilot} == {5}
    base = m6.config(m6.CELLS[0])
    for r in m7.RULES:
        for f in m7.FLEETS:
            c = m7.cell(r, f)
            x = m6.config(c)
            assert x["rule"] == r and x["cell"]["fleet"] == f
            for k in ("lag_s", "consent_p", "p_absent", "curb_wait_planning", "dispatcher", "algorithm", "slice"):
                assert x[k] == base[k], k


def _synthetic(nights, effect5, effect6, noise=0.5):
    rng = np.random.default_rng(1)
    rows = []
    for n in nights:
        base = 25 + rng.normal(0, 3)
        for f, eff in ((5, effect5), (6, effect6)):
            for i, r in enumerate(m7.RULES):
                e = 0 if r == "R0" else eff * (i / 5)
                rows.append({"night": n, "fleet": f, "rule": r, "status": "ok", "finished_at": "2026-11-25T00:00:00-0500",
                             "not_reached_20_pp": base - (2 if f == 6 else 0) + e + rng.normal(0, noise),
                             "not_reached_15_pp": base + 5 + e, "wait_pax_p90_min": 12 + e / 4,
                             "lyft_per_100": 0 if r == "R0" else 3 * i, "van_km": 400, "cancellations": 30,
                             "wall_min": 8})
    return pd.DataFrame(rows)


def test_self_comparison_is_null():
    nights = m7.MAIN30
    d = _synthetic(nights, 0, 0, noise=0)
    d = d[d.rule == "R0"]
    d = pd.concat([d.assign(rule=r) for r in m7.RULES])
    iv = pd.concat([m7.pair_intervals(d, nights, f) for f in m7.FLEETS])
    assert np.allclose(iv[["mean", "lo", "hi"]].to_numpy(), 0)
    assert set(iv.verdict) == {"within margin both ways"}
    dom = m7.dominance(iv, 5)
    assert not dom.A_dominates_B.any()
    h = m7.h3(d, nights)
    assert h["mean"] == 0 and h["reading"] == "not settled"


def test_h3_reads_known_answers():
    nights = m7.MAIN30
    assert m7.h3(_synthetic(nights, -10, -5), nights)["reading"] == "supported"
    assert m7.h3(_synthetic(nights, -5, -10), nights)["reading"] == "contradicted"
    h = m7.h3(_synthetic(nights, -6, -6, noise=0), nights)
    assert abs(h["mean"]) < 1e-9 and h["reading"] == "not settled"


def test_used_nights_rule():
    nights = m7.MAIN30[:8]
    d = _synthetic(nights, -5, -3)
    d = d[~((d.night == "r06") & (d.rule == "R0") & (d.fleet == 6))]          # r06 incomplete: prefix ends at r05
    d.loc[(d.night == "r02") & (d.rule == "R1(10)") & (d.fleet == 5), "status"] = "checks_failed"
    d.loc[(d.night == "r04") & (d.rule == "R0") & (d.fleet == 6), "status"] = "checks_failed"
    prefix, used, strict = m7.used_nights(d, nights, explained=[("r04", 6, "R0")])
    assert prefix == nights[:6] and used == ["r00", "r01", "r03", "r04", "r05"]
    assert strict == ["r00", "r01", "r03", "r05"]
    late = d.copy()
    late.loc[late.night == "r01", "finished_at"] = "2026-12-01T00:00:00-0500"
    assert m7.used_nights(late, nights)[0] == ["r00"]


@pytest.mark.skipif(not HAVE_L6, reason="L6 not built")
def test_short_real_run_six_vans(tmp_path):
    def cut(c, night):
        scen, key = m6.full_night(c, night)
        reqs = scen.requests[:12]
        return dataclasses.replace(scen, requests=reqs, hidden={r.rid: scen.hidden[r.rid] for r in reqs}), key

    fp = m5.code_fingerprint()
    c = m7.cell("R3(2)", 6)
    res = m7.run_one(("main", c, "r00", fp), root=tmp_path, scen_fn=cut)
    assert res["status"] == "ok", res
    man = json.loads((m7.run_dir("main", c, "r00", tmp_path) / "manifest.json").read_text())
    assert man["stage"] == "m7_main" and man["m7_plan_sha256"] == m7.plan_sha() and "plan_sha256" not in man
    assert man["level"] == "L6/base_6/r00" and all(man["checks"].values())
    mm = m7.measures(m7.run_dir("main", c, "r00", tmp_path))
    assert mm["n_requests"] == 12 and 0 <= mm["not_reached_20_pp"] <= 100


def test_guards(monkeypatch, tmp_path):
    draft = tmp_path / "plan.md"
    draft.write_text("**Status: DRAFT (not frozen).**")
    monkeypatch.setattr(m7, "PLAN", draft)
    with pytest.raises(SystemExit, match="frozen"):
        m7.cmd_run("pilot", 1, root=tmp_path)
    draft.write_text("**Status: FROZEN 2026-11-24**")
    monkeypatch.setattr(m7, "CODE_FINGERPRINT", "000000000000")
    with pytest.raises(SystemExit, match="fingerprint"):
        m7.cmd_run("pilot", 1, root=tmp_path)
    with pytest.raises(SystemExit):
        m7.power(root=tmp_path)
    with pytest.raises(SystemExit, match="night count"):
        m7.main_nights(root=tmp_path)


M6_R02 = ROOT / "outputs" / "sim" / "m6" / "base5_C_R0_t120" / "r02" / "rep1"


@pytest.mark.skipif(not (M6_R02 / "manifest.json").exists(), reason="M6 outputs not present")
def test_explain_reproduces_m6_r02_diagnosis():
    from sim import m7_explain
    (r,) = m7_explain.explain(M6_R02)
    assert r["request"] == "R046" and r["excess_s"] == 196 and r["min_total_pax_s_over"] == 196
    assert r["explained"] and len(r["aboard"]) == 3
