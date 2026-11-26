"""Checks on the M8 sensitivity runner (plan: docs/technical/research_notes/m8_plan_2026-11.md).

1. Grid: 26 runs per night (R0 only in the patience settings), 780 in all, no R1u(10); five vans; night by night.
2. Transform: patience and Lyft delay are scaled per rider; everything else (requests, presence, consent draws) unchanged.
3. Acceptance: consent_p reaches the policy and the saved configuration, and is restored afterwards.
4. Real short runs: R0 is unchanged by the Lyft-delay and acceptance settings (why it is reused from M7); a transfer
   rule under each kind of setting passes every check and is labelled with its setting and the plan hash.
5. Analysis: a self-comparison gives zero shift; the night rule carries M7's explained failures.
"""
import dataclasses
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sim import m5, m6, m7, m8

ROOT = Path(__file__).resolve().parents[1]
HAVE_L6 = (ROOT / "data" / "scenarios" / "v2" / "FROZEN_v2_L6.json").exists()


def test_grid():
    assert m8.TRANSFER == ["R1(10)", "R1(15)", "R2(15)", "R3(2)"]
    r = m8.runs()
    assert len(r) == 780 and len(r) == 30 * (2 * 5 + 4 * 4)
    assert not any(x[1] == "R1u(10)" for x in r)
    assert {x[1] for x in r if x[0].startswith("lyft") or x[0].startswith("consent")} == set(m8.TRANSFER)
    assert [x[2] for x in r[:26]] == ["r00"] * 26
    assert m8.NIGHTS == m7.MAIN30 and m8.FLEET == 5


@pytest.mark.skipif(not HAVE_L6, reason="L6 not built")
def test_transform_scales_only_its_draw():
    scen, _ = m6.full_night(m7.cell("R0", 5), "r00")
    for s, (px, lx) in {"patience_short": (2 / 3, 1), "patience_long": (1.5, 1), "lyft_fast": (1, 2 / 3),
                        "lyft_slow": (1, 1.5)}.items():
        t = m8.transform(scen, s)
        assert t.requests == scen.requests and t.vans == scen.vans
        for rid, h in scen.hidden.items():
            g = t.hidden[rid]
            assert g.noshow_u == h.noshow_u and g.consent_u == h.consent_u
            assert g.patience_s == max(1, round(h.patience_s * px)) and g.lyft_delay_s == max(1, round(h.lyft_delay_s * lx))
    assert m8.transform(scen, "consent_60") is scen
    med = np.median([h.patience_s for h in m8.transform(scen, "patience_short").hidden.values()]) / 60
    assert 8 < med < 16                                                  # the Weibull median 18 min x 2/3 = 12


def test_consent_reaches_policy_and_is_restored():
    c = m7.cell("R3(2)", 5)
    m8._install_policy("consent_60")
    try:
        assert m5.policy(c).consent_p == 0.6 and m6.config(c)["consent_p"] == 0.6
    finally:
        m8._install_policy("patience_short")
    assert m5.policy(c).consent_p == 1.0 and m6.config(c)["consent_p"] == 1.0


def _cut(c, night):
    scen, key = m6.full_night(c, night)
    reqs = scen.requests[:40]
    return dataclasses.replace(scen, requests=reqs, hidden={r.rid: scen.hidden[r.rid] for r in reqs}), key


@pytest.mark.skipif(not HAVE_L6, reason="L6 not built")
def test_r0_unchanged_by_lyft_and_consent(tmp_path):
    fp = m5.code_fingerprint()
    ev = {}
    for s in ("patience_short", "lyft_slow", "consent_60"):
        root = tmp_path / s
        if s == "patience_short":                                     # the untransformed R0 (base)
            m6.run_one((m7.cell("R0", 5), "r00", fp), scen_fn=_cut, root=root)
            ev[s] = (m6.run_dir(m7.cell("R0", 5), "r00", root=root) / "events.csv").read_text()
        else:
            m8.run_one((s, "R0", "r00", fp), root=root, scen_fn=_cut)
            ev[s] = (m8.run_dir(s, "R0", "r00", root) / "events.csv").read_text()
    assert ev["lyft_slow"] == ev["patience_short"] == ev["consent_60"]


@pytest.mark.skipif(not HAVE_L6, reason="L6 not built")
@pytest.mark.parametrize("setting", ["patience_short", "lyft_slow", "consent_60"])
def test_short_real_run(setting, tmp_path):
    fp = m5.code_fingerprint()
    res = m8.run_one((setting, "R3(2)", "r00", fp), root=tmp_path, scen_fn=_cut)
    assert res["status"] == "ok", res
    man = json.loads((m8.run_dir(setting, "R3(2)", "r00", tmp_path) / "manifest.json").read_text())
    assert man["stage"] == f"m8_{setting}" and man["m8_transform"] == m8.SETTINGS[setting]
    assert man["m8_plan_sha256"] == m8.plan_sha() and all(man["checks"].values())
    assert man["config"]["consent_p"] == m8.SETTINGS[setting].get("consent_p", 1.0)
    assert m5.policy(m7.cell("R3(2)", 5)).consent_p == 1.0


def _synthetic(nights, rng):
    rows = []
    for n in nights:
        b = 24 + rng.normal(0, 3)
        for s in ["base", *m8.SETTINGS]:
            for i, r in enumerate(["R0", *m8.TRANSFER]):
                rows.append({"setting": s, "rule": r, "night": n, "from_m7": m8.from_m7(s, r), "status": "ok",
                             "finished_at": "2026-11-26T00:00:00-0500", "not_reached_20_pp": b - 2 * i,
                             "lyft_per_100": 3.0 * i})
    return pd.DataFrame(rows)


def test_self_comparison_and_night_rule():
    nights = m8.NIGHTS
    d = _synthetic(nights, np.random.default_rng(1))
    t = m8.effects(d, nights)
    assert np.allclose(t["shift"], 0) and t.holds_a.all()
    d.loc[(d.night == "r02") & (d.rule == "R0") & d.from_m7, "status"] = "checks_failed"      # explained in M7
    d.loc[(d.night == "r05") & (d.setting == "lyft_slow") & (d.rule == "R3(2)"), "status"] = "checks_failed"
    prefix, used, strict = m8.used_nights(d)
    assert prefix == nights and "r02" in used and "r05" not in used and "r02" not in strict
    _, used2, _ = m8.used_nights(d, explained=[("lyft_slow", "r05", "R3(2)")])
    assert "r05" in used2
    late = d.copy()
    late.loc[late.night == "r03", "finished_at"] = "2026-11-29T00:00:00-0500"
    assert m8.used_nights(late)[0] == nights[:3]


def test_guards(monkeypatch, tmp_path):
    draft = tmp_path / "plan.md"
    draft.write_text("**Status: DRAFT**")
    monkeypatch.setattr(m8, "PLAN", draft)
    with pytest.raises(SystemExit, match="frozen"):
        m8.cmd_run(1, root=tmp_path)
    draft.write_text("**Status: FROZEN 2026-11-25**")
    monkeypatch.setattr(m8, "CODE_FINGERPRINT", "000000000000")
    with pytest.raises(SystemExit, match="fingerprint"):
        m8.cmd_run(1, root=tmp_path)
