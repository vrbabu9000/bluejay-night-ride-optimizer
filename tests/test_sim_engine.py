"""M0-M1 tests for the event engine and dispatcher C (src/sim). Inputs are the frozen v2 scenarios (read-only).

Run: .venv/bin/python -m pytest -q tests/test_sim_engine.py
"""
import dataclasses
import itertools

import pandas as pd
import pytest

from sim import dispatch as D
from sim import engine as E
from sim import inputs, lyft, run


def _run(level, rule="R0", pending_price="A"):
    """M0-era runs: the Lyft rules use the M0 window (before the vans come on duty in L4), as the answer key does."""
    scen = inputs.load(level)
    m = scen.params["travel_multiplier"]
    pol = run.policy_for(scen, rule, pending_price=pending_price, lyft_window="m0")
    return E.Engine(scen, inputs.Travel(m, m), pol).run(), scen


@pytest.fixture(scope="module")
def l4():
    return _run("L4")


def _strip_wall(epochs):
    out = []
    for ep in epochs:
        ep = dict(ep)
        ep["solver"] = {k: v for k, v in ep["solver"].items() if k != "wall_s"}
        out.append(ep)
    return out


# ---------- inputs ----------
@pytest.mark.parametrize("name", ["L1", "L2", "L3", "L4", "L5/r00"])
def test_frozen_inputs_unchanged(name):
    assert inputs.content_hash(inputs.SCEN / name) == inputs.frozen_hashes()[name]


def test_phi_units():
    assert D.phi_u(300) == 5 * D.PT and D.phi_u(600) == int(17.5 * D.PT)
    assert D.phi_u(900) == int(42.5 * D.PT) and D.phi_u(1200) == int(92.5 * D.PT)
    assert D.phi_u(12 * 60) == int(27.5 * D.PT)          # methodology §6 worked example
    cfg = D.Config()
    assert cfg.ride_u * 60 == 0.5 * D.PT                  # beta = 0.5 point per passenger-minute
    assert cfg.km_u * 10_000 == 0.1 * D.PT                # gamma = 0.1 point per km (10,000 dm)


# ---------- M0: answer keys ----------
@pytest.mark.parametrize("level", ["L1", "L2", "L3"])
def test_l1_l3_answer_keys(level):
    eng, scen = _run(level)
    out = pd.DataFrame(eng.outcomes()).set_index("request_id")
    key = pd.read_csv(scen.folder / "handcheck.csv").set_index("request_id")
    empty_curb = {e["request"]: e["t_s"] for e in eng.events if e["event"] == "arrive_no_rider"}
    free = {}
    for e in eng.events:                                   # when each van became free after serving a request
        if e["event"] in ("service_end", "state") and e["van"]:
            free.setdefault(e["van"], []).append(e)
    for rid, k in key.iterrows():
        o = out.loc[rid]
        assert o.outcome == k.outcome and o.van == k.van, rid
        if k.outcome == "van_completed":
            assert (o.curb_arrival_s, o.pickup_s, o.wait_s, o.drop_s, o.ride_s) == \
                   (k.pickup_arrival_s, k.pickup_s, k.wait_s, k.dropoff_s, k.ride_s), rid
        elif k.outcome == "noshow_van":
            assert o.curb_arrival_s == k.pickup_arrival_s and o.noshow_s == k.event_s, rid
        else:                                              # cancelled while the van was driving to the curb
            assert o.cancel_s == k.event_s and empty_curb[rid] == k.pickup_arrival_s == k.van_free_s, rid
    assert len(out) == len(key)


@pytest.mark.parametrize("rule", [r for r in lyft.RULES if r != "R0"])
def test_l4_transfers_before_vans_arrive(rule):
    eng, scen = _run("L4", rule)
    out = pd.DataFrame(eng.outcomes()).set_index("request_id")
    key = pd.read_csv(scen.folder / "handcheck.csv")
    key = key[key.rule == rule].set_index("request_id")
    kt = key[key.decision == "transfer"]
    kd = key[key.decision.str.startswith("offered")]
    assert set(out.index[out.transfer_s.notna()]) == set(kt.index)
    assert set(out.index[out.declined_s.notna()]) == set(kd.index)
    for rid, k in kt.iterrows():
        o = out.loc[rid]
        assert (o.transfer_s, o.booking_s, o.pickup_s, o.wait_s, o.drop_s, o.lyft_class, o.outcome) == \
               (k.decision_s, k.lyft_request_s, k.lyft_pickup_s, k.wait_s, k.lyft_dropoff_s, k.lyft_class,
                "lyft_completed"), rid
    for rid, k in kd.iterrows():
        assert out.loc[rid].declined_s == k.decision_s


def test_l4_answer_key_totals_are_across_rules():
    """The 22 transfers and 4 declines are totals over the five rule cases, not counts for one night."""
    key = pd.read_csv(inputs.SCEN / "L4" / "handcheck.csv")
    per_rule = key[key.decision == "transfer"].groupby("rule").size().to_dict()
    assert per_rule == {"R1(10)": 3, "R1u(10)": 3, "R2(15)": 8, "R3(2)": 8}
    assert key.decision.str.startswith("offered").sum() == 4


# ---------- states, commitment, accounting ----------
ALLOWED = {("unrevealed", "pending_van"), ("pending_van", "committed"), ("committed", "onboard"),
           ("onboard", "van_completed"), ("committed", "noshow_van"), ("pending_van", "cancel_pending_van"),
           ("committed", "cancel_pending_van"), ("pending_van", "xfer_hold"), ("xfer_hold", "lyft_booked"),
           ("xfer_hold", "cancel_after_transfer"), ("lyft_booked", "cancel_after_transfer"),
           ("lyft_booked", "lyft_onboard"), ("lyft_onboard", "lyft_completed"), ("lyft_booked", "noshow_lyft")}


@pytest.mark.parametrize("level,rule", [("L1", "R0"), ("L2", "R0"), ("L3", "R0"), ("L4", "R0"), ("L4", "R2(15)")])
def test_state_transitions_and_accounting(level, rule):
    eng, scen = _run(level, rule)
    for e in eng.events:
        if e["event"] == "state":
            assert (e["state_from"], e["state_to"]) in ALLOWED, e
    terminal = [eng.rs[r.rid].state for r in scen.requests]
    assert all(s in E.TERMINAL for s in terminal) and len(terminal) == len(scen.requests)
    times = [(e["t_s"], e["class"]) for e in eng.events]
    assert [t for t, _ in times] == sorted(t for t, _ in times)


def test_commitment_is_final(l4):
    """Once a van departs toward a pickup, that request never appears as open again and is served by that van."""
    eng, _ = l4
    committed = {e["request"]: (e["t_s"], e["van"]) for e in eng.events
                 if e["event"] == "state" and e["state_to"] == "committed"}
    for ep in eng.epochs:
        for o in ep["open"]:
            assert o["rid"] not in committed or committed[o["rid"]][0] >= ep["tau_s"]   # commitment (class 90) follows the epoch (class 80)
    for rid, (_, vid) in committed.items():
        assert eng.rs[rid].van == vid
        boards = [e for e in eng.events if e["request"] == rid and e.get("state_to") == "onboard"]
        assert boards and boards[0]["van"] == vid


def test_zero_simulated_latency(l4):
    """The plan made at the 18:15 epoch is executed in that same second."""
    eng, _ = l4
    dep = [e for e in eng.events if e["event"] == "depart" and e["t_s"] == 900]
    assert {e["van"] for e in dep} == {"V1", "V2"}
    ep = next(x for x in eng.epochs if x["tau_s"] == 900)
    for e in dep:
        assert ep["chosen"][e["van"]]["seq"][0] == f"P:{e['request']}"


def test_capacity_and_guardrail_respected(l4):
    eng, scen = l4
    tr = inputs.Travel(1.0, 1.0)
    cfg = D.Config()
    for r in scen.requests:
        st = eng.rs[r.rid]
        assert st.drop_s - st.pickup_s <= D.guardrail_s(tr.van(r.o, r.d), cfg)


# ---------- M1: joint route selection ----------
def test_joint_route_selection_at_1815(l4):
    """At 18:15 nine requests wait and two vans come on duty. Direct enumeration of every compatible pair of
    candidate routes reproduces the MILP objective, the fewest pending requests and the canonical choice."""
    eng, _ = l4
    ep = next(x for x in eng.epochs if x["tau_s"] == 900)
    assert len(ep["open"]) == 9 and ep["solver"]["status"] == "optimal"
    vids = ["V1", "V2"]
    q = {o["rid"]: o["q"] for o in ep["open"]}
    tr = inputs.Travel(1.0, 1.0)
    sc = inputs.load("L4")
    R = {r.rid: r for r in sc.requests}
    tn = ep["solver"]["next_tick_s"]
    assert ep["solver"]["pending_price"] == "A"
    L = {r: min(v["free_s"] + tr.van(v["loc"], R[r].o) for v in ep["vans"]) for r in q}       # A, recomputed here
    pend = {r: q[r] * D.phi_u(max(tn, L[r]) - R[r].t) + ep["solver"]["M_u"] for r in q}
    assert {r: pend[r] - ep["solver"]["M_u"] for r in q} == ep["solver"]["pending_base_u"]
    best, min_pending = None, 99
    for a, b in itertools.product(ep["candidates"]["V1"], ep["candidates"]["V2"]):
        if set(a["S"]) & set(b["S"]):
            continue
        p = [r for r in q if r not in set(a["S"]) | set(b["S"])]
        obj = a["cost_u"] + b["cost_u"] + sum(pend[r] for r in p)
        keyv = tuple("V1" if r in a["S"] else "V2" if r in b["S"] else "~" for r in sorted(q))
        min_pending = min(min_pending, len(p))
        if best is None or (obj, keyv) < best[:2]:
            best = (obj, keyv, a["S"], b["S"], len(p))
    assert best[0] == ep["solver"]["objective_u"]
    assert best[4] == min_pending == 3                     # K = 3 per van, 2 vans, 9 open
    assert best[2] == ep["chosen"]["V1"]["S"] and best[3] == ep["chosen"]["V2"]["S"]
    assert ep["solver"]["tie_status"] == "tie"             # the two vans start identically at the depot


def test_every_l4_epoch_proven_optimal(l4):
    eng, _ = l4
    assert {ep["solver"]["status"] for ep in eng.epochs} == {"optimal"}


def test_failed_solve_is_logged_not_replaced(monkeypatch):
    """A failed solve keeps committed work only and says so; no heuristic is called."""
    monkeypatch.setattr(D, "_milp", lambda *a, **k: {"status": "failed", "chosen": None, "obj": None,
                                                     "bound": None, "gap": None, "nodes": 0})
    scen = inputs.load("L4")
    tr = inputs.Travel(1.0, 1.0)
    obs = D.Observation(900, (D.VanState("V1", 14, "p04_b040", 900, (), ()),),
                        tuple(D.OpenRequest(r.rid, r.t, r.o, r.d, r.q) for r in scen.requests if r.t < 900))
    plan, _ = D.solve(obs, tr)
    assert plan.log["status"] == "failed" and plan.routes["V1"].seq == () and len(plan.pending) == 9


# ---------- information and reproducibility ----------
def test_observation_has_no_hidden_traits():
    names = set()
    for cls in (D.Observation, D.VanState, D.OpenRequest, D.Rider):
        names |= {f.name for f in dataclasses.fields(cls)}
    assert not names & {"patience_s", "noshow_u", "consent_u", "lyft_delay_s", "lyft_noshow_u", "eta_noise"}


def test_reproducible(l4):
    eng1, _ = l4
    eng2, _ = _run("L4")
    assert eng1.events == eng2.events
    assert _strip_wall(eng1.epochs) == _strip_wall(eng2.epochs)


# ---------- coverage added after the integrated review (22 Oct) ----------
def _engine(level, rule="R0", **pol):
    scen = inputs.load(level)
    m = scen.params["travel_multiplier"]
    p = run.policy_for(scen, rule, lyft_window="m0")
    p = dataclasses.replace(p, **pol)
    return E.Engine(scen, inputs.Travel(m, m), p), scen


def test_no_failed_labels_and_audit_passes():
    for rule in ("R0", "R2(15)", "R3(2)"):
        eng, _ = _engine("L4", rule)
        eng.run()
        assert "failed" not in {ep["solver"]["status"] for ep in eng.epochs}
        assert all(ep["audit"].startswith("pass") for ep in eng.epochs)


def test_unproven_solve_is_executed_and_labelled(monkeypatch):
    real = D._milp

    def unproven(*a, **k):
        res = real(*a, **k)
        if res["status"] == "optimal" and not k.get("extra_rows"):
            res = dict(res, status="feasible_unproven")
        return res
    monkeypatch.setattr(D, "_milp", unproven)
    scen = inputs.load("L4")
    tr = inputs.Travel(1.0, 1.0)
    vans = (D.VanState("V1", 14, "p04_b040", 900, (), ()), D.VanState("V2", 14, "p04_b040", 900, (), ()))
    obs = D.Observation(900, vans, tuple(D.OpenRequest(r.rid, r.t, r.o, r.d, r.q) for r in scen.requests if r.t < 900))
    plan, _ = D.solve(obs, tr)
    assert plan.log["status"] == "feasible_unproven" and plan.log["tie_status"] == "not_checked"
    assert sum(len(r.S) for r in plan.routes.values()) == 6          # the incumbent is executed
    for info in plan.pending_info.values():
        assert all(v.startswith("chosen route already") or v.startswith("not established")
                   for v in info["per_van"].values())


def test_lyft_and_van_noshows_when_everyone_is_absent():
    eng, scen = _engine("L4", "R2(15)", p_absent=1.0)      # every presence draw (0.99) is below p: all absent
    eng.run()
    out = pd.DataFrame(eng.outcomes()).set_index("request_id")
    lyft = out[out.transfer_s.notna()]
    assert (lyft.outcome == "noshow_lyft").all() and len(lyft) == 8
    assert ((lyft.noshow_s - lyft.curb_arrival_s) == 180).all()
    assert ((lyft.curb_arrival_s - lyft.booking_s) == 480).all() and lyft.pickup_s.isna().all()
    van = out[out.transfer_s.isna()]
    assert (van.outcome == "noshow_van").all() and ((van.noshow_s - van.curb_arrival_s) == 180).all()


def test_cancel_during_lag_books_nothing_and_after_booking_is_counted():
    scen = inputs.load("L4")                                # in-memory change only; the frozen files are untouched
    h = scen.hidden
    # R001 is transferred at 0 s: booking at 120 s, Lyft arrival at 600 s
    h["R001"] = inputs.Hidden(60, h["R001"].noshow_u, h["R001"].consent_u, h["R001"].lyft_delay_s)    # inside the lag
    h["R004"] = inputs.Hidden(400, h["R004"].noshow_u, h["R004"].consent_u, h["R004"].lyft_delay_s)   # after booking
    eng = E.Engine(scen, inputs.Travel(1.0, 1.0), run.policy_for(scen, "R2(15)", lyft_window="m0")).run()
    o = {r["request_id"]: r for r in eng.outcomes()}
    assert o["R001"]["outcome"] == "cancel_after_transfer" and o["R001"]["booking_s"] is None
    assert o["R001"]["cancel_s"] == 60
    assert o["R004"]["outcome"] == "cancel_after_transfer" and o["R004"]["booking_s"] == o["R004"]["transfer_s"] + 120
    assert o["R004"]["cancel_s"] == 100 + 400 and o["R004"]["curb_arrival_s"] is None
    assert not [e for e in eng.events if e["request"] == "R001" and e.get("state_to") == "lyft_booked"]
