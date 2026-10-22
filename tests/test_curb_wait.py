"""Curb-wait planning convention (D-54): while an absent rider's 180-s timer runs, the planner keeps the pickup
committed and assumes possible boarding at expiry (dwell, seat, drop-off obligation); the obligation disappears when
the no-show expires. Planning only: the simulator never boards an absent rider.

Case: L4 under R0 with R003 made absent IN MEMORY (frozen files untouched). In the M1 trace V1 reaches R003 at
1323 s (18:22:03) carrying R001 and R013, other requests are open, the 1440-s tick falls inside the timer, and the
no-show expires at 1503 s.
"""
import dataclasses

import pytest

from sim import dispatch as D
from sim import engine as E
from sim import inputs, run

ARRIVE, EXPIRY, TICK = 1323, 1503, 1440


def _run(convention):
    scen = inputs.load("L4")
    h = scen.hidden["R003"]
    scen.hidden["R003"] = inputs.Hidden(h.patience_s, 0.0, h.consent_u, h.lyft_delay_s)     # absent at the curb
    pol = run.policy_for(scen, "R0", curb_wait=convention)
    return E.Engine(scen, inputs.Travel(1.0, 1.0), pol).run()


@pytest.fixture(scope="module")
def runs():
    return {c: _run(c) for c in ("possible_boarding", "noshow_certain")}


def _at(eng, tau):
    i = next(k for k, ep in enumerate(eng.epochs) if ep["tau_s"] == tau)
    return eng.observations[i], eng.epochs[i]


def test_case_is_the_intended_one(runs):
    eng = runs["possible_boarding"]
    arr = [e for e in eng.events if e["event"] == "curb_arrival" and e["request"] == "R003"]
    assert arr and arr[0]["t_s"] == ARRIVE and arr[0]["van"] == "V1" and arr[0]["present"] is False
    obs, ep = _at(eng, TICK)
    v1 = next(v for v in obs.vans if v.vid == "V1")
    assert {"R001", "R013"} <= {r.rid for r in v1.riders}       # passengers already aboard
    assert len(obs.open) >= 1                                     # another request is waiting


def test_during_the_timer_the_pickup_stays_committed_with_possible_boarding(runs):
    obs, ep = _at(runs["possible_boarding"], TICK)
    v1 = next(v for v in obs.vans if v.vid == "V1")
    assert v1.committed == ("R003", "P_curb_wait", ARRIVE)
    r3 = next(r for r in v1.riders if r.rid == "R003")
    assert r3.pickup_s == EXPIRY                                  # boarding assumed at expiry, not earlier
    assert v1.free_s == EXPIRY + D.DWELL_S and v1.loc == runs["possible_boarding"].req["R003"].o
    load = sum(r.q for r in v1.riders)
    assert load <= v1.capacity and load == sum(runs["possible_boarding"].req[x].q for x in ("R001", "R013", "R003"))
    assert "D:R003" in ep["chosen"]["V1"]["seq"]                  # drop-off obligation planned
    assert "R003" not in {o["rid"] for o in ep["open"]}           # committed, not open
    assert runs["possible_boarding"].rs["R003"].state == "noshow_van"   # and it never actually boards
    assert not [e for e in runs["possible_boarding"].events if e["request"] == "R003" and e.get("state_to") == "onboard"]


def test_old_convention_treats_the_noshow_as_certain(runs):
    obs, ep = _at(runs["noshow_certain"], TICK)
    v1 = next(v for v in obs.vans if v.vid == "V1")
    assert "R003" not in {r.rid for r in v1.riders} and v1.free_s == EXPIRY
    assert "D:R003" not in ep["chosen"]["V1"]["seq"]


def test_after_expiry_the_obligation_is_removed(runs):
    for conv in ("possible_boarding", "noshow_certain"):
        eng = runs[conv]
        obs, ep = _at(eng, EXPIRY)
        assert "noshow" in ep["triggers"]
        v1 = next(v for v in obs.vans if v.vid == "V1")
        assert "R003" not in {r.rid for r in v1.riders} and v1.free_s == EXPIRY and v1.committed == ()
        assert all("R003" not in c["seq"][i] for c in ep["chosen"].values() for i in range(len(c["seq"])))
        assert eng.rs["R003"].noshow_s == EXPIRY


def test_predicted_etas_are_conservative_during_the_timer(runs):
    """During the timer, V1's next new pickup is planned no earlier than expiry + dwell; after expiry the same van
    can be planned to leave at once."""
    _, ep = _at(runs["possible_boarding"], TICK)
    seq, arr = ep["chosen"]["V1"]["seq"], ep["chosen"]["V1"]["arrivals_s"]
    picks = [a for s, a in zip(seq, arr) if s.startswith("P:")]
    assert all(a >= EXPIRY + D.DWELL_S for a in picks)
    _, ep2 = _at(runs["possible_boarding"], EXPIRY)
    seq2, arr2 = ep2["chosen"]["V1"]["seq"], ep2["chosen"]["V1"]["arrivals_s"]
    first = arr2[0] if arr2 else None
    assert first is None or first >= EXPIRY


def test_executed_actions_identical_before_expiry(runs):
    """Both conventions execute the same events up to expiry (the van is held at the curb either way)."""
    a = [e for e in runs["possible_boarding"].events if e["t_s"] <= EXPIRY]
    b = [e for e in runs["noshow_certain"].events if e["t_s"] <= EXPIRY]
    assert a == b


def test_audit_passes_with_the_convention(runs):
    assert all(ep["audit"].startswith("pass") for ep in runs["possible_boarding"].epochs)
