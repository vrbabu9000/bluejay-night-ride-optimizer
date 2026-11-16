"""Checks on dispatcher G (greedy insertion, never reassign; D-60, M5b).

1. On L1-L3 (one open request at a time, hand-checked to the second for C) G and C must give identical outcomes:
   with one request and idle vans, cheapest insertion and the MILP solve the same problem.
2. Never reassign, never reorder: once G assigns a request to a van, it stays on that van until pickup (unless a
   logged repair release), and the relative order of kept stops never changes between epochs.
3. Determinism: two runs give identical event logs.
4. The engine's plan audit runs on every G epoch (capacity, precedence, guardrail); a full L5 night passing is the check.
5. An unknown algorithm name is refused.
Skips if the v2 levels have not been built (data/ is gitignored).
"""
import dataclasses
from pathlib import Path

import pandas as pd
import pytest

from sim import engine as E
from sim import inputs
from sim.run import policy_for

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (ROOT / "data" / "scenarios" / "v2" / "FROZEN_v2.json").exists(),
                                reason="v2 levels not built")


def run(level, rule="R0", alg="G"):
    scen = inputs.load(level)
    m = scen.params.get("travel_multiplier", 1.0)
    pol = dataclasses.replace(policy_for(scen, rule), algorithm=alg)
    return E.Engine(scen, inputs.Travel(m, m), pol).run()


@pytest.mark.parametrize("level", ["L1", "L2", "L3"])
def test_matches_c_when_one_request_is_open(level):
    g, c = pd.DataFrame(run(level, alg="G").outcomes()), pd.DataFrame(run(level, alg="C").outcomes())
    assert g.equals(c)


def _chosen(eng):
    """Per epoch: {vid: [(kind, rid), ...]} as executed."""
    out = []
    for ep in eng.epochs:
        out.append({v: [tuple(s.split(":")) for s in r["seq"]] for v, r in ep["chosen"].items()})
    return out


@pytest.mark.parametrize("level,rule", [("L4", "R0"), ("L5/r00", "R0"), ("L5/r09", "R0"), ("L5/r00", "R1(10)")])
def test_never_reassigns_or_reorders(level, rule):
    eng = run(level, rule)
    released = {r for ep in eng.epochs for r in ep["solver"]["released_for_repair"]}
    owner, prev = {}, None
    for ep, routes in zip(eng.epochs, _chosen(eng)):
        for v, seq in routes.items():
            for kind, rid in seq:
                if kind == "P":
                    if rid in owner and rid not in released:
                        assert owner[rid] == v, f"{rid} moved from {owner[rid]} to {v} at {ep['tau_s']}"
                    owner[rid] = v
            if prev is not None and v in prev:
                common = set(seq) & set(prev[v])
                assert [s for s in prev[v] if s in common] == [s for s in seq if s in common], \
                    f"{v} reordered kept stops at {ep['tau_s']}"
        prev = routes
    assert all(ep["solver"]["algorithm"] == "G" for ep in eng.epochs)
    assert not any(ep["solver"]["missing_drop_repaired"] for ep in eng.epochs)


def test_deterministic():
    a, b = run("L5/r03"), run("L5/r03")
    assert pd.DataFrame(a.events).equals(pd.DataFrame(b.events))


def test_unknown_algorithm_refused():
    scen = inputs.load("L1")
    with pytest.raises(ValueError):
        E.Engine(scen, inputs.Travel(1.0, 1.0), dataclasses.replace(policy_for(scen, "R0"), algorithm="X"))


def test_repair_releases_and_reinserts():
    """Force the repair path: a kept sequence that breaks the guardrail of a request not yet picked up. With a tight
    guardrail (max(60 s, 1 x direct)), interleaving two trips makes the first rider's planned ride exceed it, so G must
    release the request with the larger excess, keep the plan legal, and re-insert the released request as new."""
    from sim import dispatch as D
    from sim.greedy import Greedy
    scen = inputs.load("L1")
    tr = inputs.Travel(1.0, 1.0)
    cfg = D.Config(g_abs_s=60, g_alpha=1, g_delta_s=0)
    a = scen.requests[0]
    b = next(r for r in scen.requests[1:] if len({a.o, a.d, r.o, r.d}) == 4)
    van = D.VanState("V1", 14, a.o, 0, (), ())
    obs = D.Observation(0, (van,), (D.OpenRequest(a.rid, 0, a.o, a.d, 1), D.OpenRequest(b.rid, 0, b.o, b.d, 1)))
    g = Greedy(tr, cfg)
    g.route = {"V1": [("P", a.rid), ("P", b.rid), ("D", a.rid), ("D", b.rid)]}
    g.owner = {a.rid: "V1", b.rid: "V1"}
    req = {x.rid: x for x in obs.open}
    assert not D.evaluate(van, g.route["V1"], req, tr, cfg, None)["feasible"]
    plan, _ = g.solve(obs)
    assert plan.log["released_for_repair"]
    seq = plan.routes["V1"].seq
    picked = {rid: req[rid] for k, rid in seq if k == "P"}
    assert D.evaluate(van, seq, picked, tr, cfg, None)["feasible"]
    for rid in plan.log["released_for_repair"]:
        assert rid in {x["rid"] for x in plan.log["inserted"]} or rid in plan.pending


def test_same_epoch_resolve_restarts_from_pre_plan_state():
    """After a Lyft transfer the engine re-solves at the same tau; G's final plan must equal the plan of a fresh G
    restored to its state before the discarded first plan (independent review finding 1)."""
    import copy
    from sim.greedy import Greedy
    calls = []                    # all 30 nights; with the restore disabled, 22 of 177 re-solves differ (mutation check)
    for r in range(30):
        scen = inputs.load(f"L5/r{r:02d}")
        pol = dataclasses.replace(policy_for(scen, "R1(10)"), algorithm="G")
        eng = E.Engine(scen, inputs.Travel(1.2, 1.2), pol)
        g = eng._solve.__self__

        def spy(obs, g=g, real=g.solve):
            before = (copy.deepcopy(g.route), copy.deepcopy(g.owner))
            plan, c = real(obs)
            calls.append((obs, before, plan))
            return plan, c

        eng._solve = spy
        eng.run()
        calls.append((None, None, None))      # night separator
    n = 0
    for (o1, b1, p1), (o2, b2, p2) in zip(calls, calls[1:]):
        if o1 is None or o2 is None or o1.tau != o2.tau:
            continue
        n += 1
        ref = Greedy(eng.travel, pol.dispatcher)
        ref.route, ref.owner = copy.deepcopy(b1[0]), copy.deepcopy(b1[1])
        rp, _ = ref.solve(o2)
        assert {v: r.seq for v, r in rp.routes.items()} == {v: r.seq for v, r in p2.routes.items()}
        assert p2.log["replaced_same_epoch"]
    assert n > 100                # 171 with the fix (the trajectory itself changes, so not 177)


def test_g_refuses_prediction_based_rules():
    scen = inputs.load("L5/r00")
    for rule in ("R2(15)", "R3(2)"):
        with pytest.raises(ValueError):
            E.Engine(scen, inputs.Travel(1.2, 1.2), dataclasses.replace(policy_for(scen, rule), algorithm="G"))
