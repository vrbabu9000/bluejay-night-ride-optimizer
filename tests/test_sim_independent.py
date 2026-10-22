"""Independent verification of src/sim (M0-M1): checks that do not trust the implementation's own logic.

The implementation is used only to produce answers (sim.inputs to load the frozen files, Engine(...).run(), and
sim.dispatch.solve, wrapped to capture each epoch's Observation, Plan and candidate set). Every reference value is
recomputed by tests/independent_check.py from the documented rules; it never calls dispatch.best_routes, _insert,
_milp, _canonical, evaluate, phi_u or guardrail_s.

Run: .venv/bin/python -m pytest -q tests/test_sim_independent.py        (add -s to see the coverage counts)
"""
import dataclasses
import itertools
import math
import random
from fractions import Fraction
from functools import lru_cache
from types import SimpleNamespace

import pytest

import independent_check as X
from sim import dispatch as D
from sim import engine as E
from sim import inputs, run

L4_RULES = ["R0", "R1(10)", "R1(15)", "R1u(10)", "R2(15)", "R3(2)"]


def U(ref_units):
    """REF units -> implementation units (exact: IMPL = 2 x REF)."""
    assert X.IMPL_UNITS_PER_POINT == 2 * X.REF
    return 2 * ref_units


def _execute(level, rule="R0", hidden=None, fixed=False):
    """fixed=False: the default dispatcher (riders aboard reordered freely with the new stops);
    fixed=True: the optional restriction fix_existing_drop_order=True."""
    scen = inputs.load(level)
    if hidden is not None:
        scen.hidden = hidden(scen.hidden)
    m = scen.params["travel_multiplier"]
    travel = inputs.Travel(m, m)                               # fresh oracle: no candidate cache shared across runs
    pol = run.policy_for(scen, rule)
    if fixed:
        pol = dataclasses.replace(pol, dispatcher=dataclasses.replace(pol.dispatcher, fix_existing_drop_order=True))
    solves = []
    orig = D.solve

    def capture(obs, trav, cfg=D.Config()):
        plan, cands = orig(obs, trav, cfg)
        solves.append(SimpleNamespace(obs=obs, plan=plan, cands=cands, cfg=cfg))
        return plan, cands

    D.solve = capture
    try:
        eng = E.Engine(scen, travel, pol).run()
    finally:
        D.solve = orig
    assert solves and all(x.cfg.fix_existing_drop_order is fixed for x in solves)
    return SimpleNamespace(level=level, rule=rule, scen=scen, eng=eng, solves=solves, ref=X.Ref(level, m),
                           fixed=fixed)


@lru_cache(maxsize=None)
def get_run(level, rule="R0", fixed=False):
    """Call positionally (get_run("L4", "R0") and get_run("L4", "R0", False) are distinct cache keys otherwise)."""
    return _execute(level, rule, fixed=fixed)


def test_default_is_free_drop_order():
    assert D.Config().fix_existing_drop_order is False


@pytest.fixture(scope="module")
def l4r0():
    return get_run("L4", "R0", False)


@pytest.fixture(scope="module", params=["free", "fixed"])
def l4r0_mode(request):
    return get_run("L4", "R0", request.param == "fixed")      # positional: shares the lru_cache entry


def _van_states(r):
    """Distinct (van state, open requests) pairs seen by the dispatcher, with the implementation's candidates."""
    seen = {}
    for s in r.solves:
        for van in s.obs.vans:
            key = (van, s.obs.open)
            if key not in seen:
                seen[key] = (s.obs, van, s.cands[van.vid])
    return list(seen.values())


def _ctx_and_limits(ref, obs, van):
    ctx = X.VanCtx(ref, obs.tau, van)
    (co_cost, co_seq, co_rides), n_perm = X.committed_only_best(ref, ctx)
    return ctx, co_cost, co_seq, X.limits_for(ref, ctx, co_rides), n_perm


# ======================================================================================================
# 0. the reference rules themselves
# ======================================================================================================
def test_reference_phi_and_units():
    for w_min, pts in ((5, 5), (10, Fraction(35, 2)), (15, Fraction(85, 2)), (20, Fraction(185, 2)),
                       (12, Fraction(55, 2))):
        assert X.phi_minutes(w_min) == pts
    for w in range(0, 3000, 7):                    # integer-second version == minute formula, exactly
        assert Fraction(X.phi_ref(w), X.REF) == X.phi_minutes(Fraction(w, 60))
    assert Fraction(X.RIDE_REF * 60, X.REF) == Fraction(1, 2)          # 0.5 point per passenger-minute
    assert Fraction(X.KM_REF * 10_000, X.REF) == Fraction(1, 10)       # 0.1 point per km
    assert Fraction(X.PSI_REF * 60, X.REF) == 1000


# ======================================================================================================
# 1. best stop order per (van, subset)
# ======================================================================================================
def test_best_order_per_subset(l4r0_mode):
    r = l4r0_mode
    ref = r.ref
    rng = random.Random(20261022)
    n_states = n_sub = n_sub3 = n_orders = n_absent = n_perm_total = 0
    for obs, van, cand_list in _van_states(r):
        n_states += 1
        impl = {S: (c, tuple(seq)) for S, c, seq in cand_list}
        assert len(impl) == len(cand_list), "duplicate subsets in a van's candidate list"
        ctx, co_cost, co_seq, limits, n_perm = _ctx_and_limits(ref, obs, van)
        n_perm_total += n_perm
        # the committed-only route: my brute force over all drop orders (no guardrail) vs the implementation
        assert frozenset() in impl, (obs.tau, van.vid)
        c, seq = impl[frozenset()]
        assert Fraction(c, X.IMPL_UNITS_PER_POINT) == Fraction(co_cost, X.REF), (obs.tau, van.vid, c, co_cost)
        assert seq == co_seq, (obs.tau, van.vid, seq, co_seq)
        # fixed mode: existing riders keep MY committed-only order; free mode: every stop is ordered freely
        base = [rid for _, rid in co_seq] if r.fixed else None
        rids = [x.rid for x in obs.open]
        subsets = [frozenset(S) for k in (1, 2) for S in itertools.combinations(rids, k)]
        all3 = [frozenset(S) for S in itertools.combinations(rids, 3)]
        n3 = 4 if (r.fixed or len(van.riders) <= 3) else 1     # free order with 4-5 riders aboard: ~10^6 orders each
        sample3 = rng.sample(all3, min(n3, len(all3)))
        for S in subsets + sample3:
            best, n = X.brute_force_subset(ref, ctx, S, base, limits)
            n_orders += n
            n_sub += 1
            n_sub3 += len(S) == 3
            if best is None:
                n_absent += 1
                assert S not in impl, f"tau={obs.tau} {van.vid} S={sorted(S)}: candidate exists but no feasible order"
                continue
            assert S in impl, f"tau={obs.tau} {van.vid} S={sorted(S)}: feasible (cost {best[0]}) but no candidate"
            c, seq = impl[S]
            assert Fraction(c, X.IMPL_UNITS_PER_POINT) == Fraction(best[0], X.REF), \
                f"tau={obs.tau} {van.vid} S={sorted(S)}: impl {c / 1.2e6:.6f} pts, brute-force min {best[0] / 6e5:.6f}"
            assert seq == best[1], f"tau={obs.tau} {van.vid} S={sorted(S)}: impl {seq}, lexicographic min {best[1]}"
        # every candidate (incl. all |S| = 3 ones): its own order is feasible and costs what it says
        for S, (c, seq) in impl.items():
            assert len(S) <= 3
            ok, mc, _, _ = X.evaluate(ref, ctx, seq, set(S), limits if S else None)
            assert ok and Fraction(c, X.IMPL_UNITS_PER_POINT) == Fraction(mc, X.REF), (obs.tau, van.vid, sorted(S))
    print(f"\n[best-order {'fixed' if r.fixed else 'free'}] {n_states} van states; {n_sub} subsets brute-forced ({n_sub3} with |S|=3, "
          f"{n_absent} infeasible), {n_orders} complete orders enumerated; {n_perm_total} committed-only orders")
    assert n_states >= 30 and n_sub >= 1000


# ======================================================================================================
# 2. route selection over the implementation's candidate set
# ======================================================================================================
def test_route_selection_exhaustive(l4r0_mode):
    rn = l4r0_mode
    ref = rn.ref
    n_ep = n_comb = n_ties = 0
    for s in rn.solves:
        obs, plan = s.obs, s.plan
        rids = [x.rid for x in obs.open]
        q = {x.rid: x.q for x in obs.open}
        t = {x.rid: x.t for x in obs.open}
        per_van = []
        for van in obs.vans:
            ctx, _, _, limits, _ = _ctx_and_limits(ref, obs, van)
            rows = []
            for S, c, seq in s.cands[van.vid]:
                ok, mc, _, _ = X.evaluate(ref, ctx, tuple(seq), set(S), limits if S else None)
                assert ok and U(mc) == c, (obs.tau, van.vid, sorted(S), c, U(mc))
                rows.append((frozenset(S), U(mc)))
            per_van.append((van.vid, rows))
        tn = X.next_tick(obs.tau)
        phi_next = {r: q[r] * U(X.phi_ref(tn - t[r])) for r in rids}
        M = 1 + sum(max(c for _, c in rows) - min(c for _, c in rows) for _, rows in per_van) + sum(phi_next.values())
        pi = {r: phi_next[r] + M for r in rids}
        assert plan.log["M_u"] == M, (obs.tau, plan.log["M_u"], M)
        best_obj, best_keys, min_pending, argmin_pending = None, [], None, None
        for combo in X.enumerate_combinations(per_van, rids):
            n_comb += 1
            assign = {}
            cost = 0
            for (vid, rows), k in zip(per_van, combo):
                S, c = rows[k]
                cost += c
                for r in S:
                    assign[r] = vid
            pend = [r for r in rids if r not in assign]
            obj = cost + sum(pi[r] for r in pend)
            min_pending = len(pend) if min_pending is None else min(min_pending, len(pend))
            key = X.canonical_key(assign, rids)
            if best_obj is None or obj < best_obj:
                best_obj, best_keys, argmin_pending = obj, [key], len(pend)
            elif obj == best_obj:
                best_keys.append(key)
        n_ep += 1
        n_ties += len(best_keys) > 1
        # the implementation's choice
        impl_assign = {r: vid for vid, rt in plan.routes.items() for r in rt.S}
        assert set(plan.routes) == {v.vid for v in obs.vans}
        impl_cost = 0
        for vid, rows in per_van:
            match = [c for S, c in rows if S == frozenset(plan.routes[vid].S)]
            assert len(match) == 1, (obs.tau, vid)
            impl_cost += match[0]
        impl_pend = [r for r in rids if r not in impl_assign]
        assert sorted(plan.pending) == impl_pend
        impl_obj = impl_cost + sum(pi[r] for r in impl_pend)
        assert impl_obj == best_obj, f"tau={obs.tau}: impl objective {impl_obj} U, enumerated minimum {best_obj} U"
        assert X.canonical_key(impl_assign, rids) == min(best_keys), \
            f"tau={obs.tau}: impl {X.canonical_key(impl_assign, rids)} is not the canonical optimum {min(best_keys)}"
        assert argmin_pending == min_pending, f"tau={obs.tau}: optimum leaves {argmin_pending} pending, min {min_pending}"
        assert plan.log["objective_u"] == best_obj
    print(f"\n[route-selection {'fixed' if rn.fixed else 'free'}] {n_ep} epochs, {n_comb} combinations enumerated, {n_ties} epochs with tied optima")
    assert n_ep == len(rn.eng.epochs) and n_ep > 0


# ======================================================================================================
# 3. answer keys
# ======================================================================================================
def _key(level):
    return {r["request_id"]: r for r in X.read_csv(level, "handcheck.csv")}


def _fnum(s):
    return None if s in ("", None) else int(float(s))


@pytest.mark.parametrize("level", ["L1", "L2", "L3"])
def test_answer_keys_l1_l3(level):
    r = get_run(level, "R0", False)
    ev = r.eng.events
    key = _key(level)
    states = X.per_request_states(ev)
    assert set(key) == set(r.ref.req)
    for rid, k in key.items():
        x = r.ref.req[rid]
        deps = [e for e in ev if e["event"] == "depart" and e["request"] == rid and e["stop"] == "P"]
        assert len(deps) == 1, (rid, deps)
        dep = deps[0]
        assert dep["van"] == k["van"], (rid, dep["van"], k["van"])
        assert dep["frm"] == k["van_from"] and dep["to"] == x["o"], (rid, dep)
        assert dep["arrive_s"] == _fnum(k["pickup_arrival_s"]), (rid, dep["arrive_s"], k["pickup_arrival_s"])
        assert dep["arrive_s"] - dep["t_s"] == _fnum(k["deadhead_s"]) == r.ref.vt(k["van_from"], x["o"]), rid
        final = states[rid][-1]["state_to"]
        assert final == k["outcome"], (rid, final, k["outcome"])
        vid, curb = k["van"], _fnum(k["pickup_arrival_s"])
        if final == "van_completed":
            onb = X.first(states[rid], lambda e: e["state_to"] == "onboard")
            done = states[rid][-1]
            assert onb["t_s"] == curb == _fnum(k["pickup_s"]) and onb["van"] == vid, rid
            assert onb["t_s"] - x["t"] == _fnum(k["wait_s"]), rid
            assert done["t_s"] == _fnum(k["dropoff_s"]) == _fnum(k["event_s"]) and done["van"] == vid, rid
            assert done["t_s"] - onb["t_s"] == _fnum(k["ride_s"]), rid
            # my own schedule: drop = curb + 30 + van time(o, d) (the van goes straight there in L1-L3)
            assert done["t_s"] == curb + X.DWELL + r.ref.vt(x["o"], x["d"]), rid
            free_t, free_loc = done["t_s"] + X.DWELL, x["d"]
            assert X.first(ev, lambda e: e["event"] == "service_end" and e["van"] == vid and e["t_s"] == free_t
                           and e["note"] == "drop_dwell"), rid
        elif final == "noshow_van":
            ca = X.first(ev, lambda e: e["event"] == "curb_arrival" and e["request"] == rid)
            assert ca and ca["t_s"] == curb and ca["van"] == vid and ca["present"] is False, rid
            assert states[rid][-1]["t_s"] == curb + 180 == _fnum(k["event_s"]), rid
            free_t, free_loc = curb + 180, x["o"]
            assert not any(e["state_to"] == "onboard" for e in states[rid])
        elif final == "cancel_pending_van":
            assert states[rid][-1]["t_s"] == _fnum(k["event_s"]), (rid, states[rid][-1]["t_s"], k["event_s"])
            nr = X.first(ev, lambda e: e["event"] == "arrive_no_rider" and e["request"] == rid)
            assert nr and nr["t_s"] == curb and nr["van"] == vid, (rid, nr)
            free_t, free_loc = curb, x["o"]                    # the van reaches the empty curb and is free at once
            assert X.first(ev, lambda e: e["event"] == "service_end" and e["van"] == vid and e["t_s"] == curb), rid
        else:
            raise AssertionError((rid, final))
        assert free_t == _fnum(k["van_free_s"]) and free_loc == k["van_free_at"], (rid, free_t, k["van_free_s"])
        # the key's per-van single-request cost at the request epoch, recomputed with my evaluator
        s = next(s for s in r.solves if s.obs.tau == x["t"] and any(o.rid == rid for o in s.obs.open))
        for van in s.obs.vans:
            ctx, co_cost, co_seq, limits, _ = _ctx_and_limits(r.ref, s.obs, van)
            best, _ = X.brute_force_subset(r.ref, ctx, {rid}, [b for _, b in co_seq], limits)
            marginal = Fraction(best[0] - co_cost, X.REF)
            assert abs(float(marginal) - float(k[f"cost_{van.vid}"])) < 1e-6, (rid, van.vid, float(marginal),
                                                                               k[f"cost_{van.vid}"])


@pytest.mark.parametrize("rule", L4_RULES)
def test_answer_key_l4(rule):
    r = get_run("L4", rule, False)
    ev = r.eng.events
    params = r.scen.params
    lag, delay, start = params["lyft_lag_s"], params["lyft_delay_s"], params["vans_on_duty_from_s"]
    rows = [k for k in X.read_csv("L4", "handcheck.csv") if k["rule"] == rule]
    exp_t = {k["request_id"]: k for k in rows if k["decision"] == "transfer"}
    exp_d = {k["request_id"]: k for k in rows if k["decision"].startswith("offered, declined")}
    got_t = {e["request"]: e for e in ev if e["event"] == "state" and e["state_to"] == "xfer_hold" and e["t_s"] < start}
    got_d = {e["request"]: e for e in ev if e["event"] == "transfer_declined" and e["t_s"] < start}
    assert set(got_t) == set(exp_t), (rule, sorted(got_t), sorted(exp_t))
    assert set(got_d) == set(exp_d), (rule, sorted(got_d), sorted(exp_d))
    states = X.per_request_states(ev)
    for rid, k in exp_t.items():
        x = r.ref.req[rid]
        dec = got_t[rid]["t_s"]
        assert dec == _fnum(k["decision_s"]), (rule, rid, dec, k["decision_s"])
        booked = X.first(states[rid], lambda e: e["state_to"] == "lyft_booked")["t_s"]
        pick = X.first(states[rid], lambda e: e["state_to"] == "lyft_onboard")["t_s"]
        drop = X.first(states[rid], lambda e: e["state_to"] == "lyft_completed")["t_s"]
        assert booked == dec + lag == _fnum(k["lyft_request_s"]), (rule, rid, booked)
        assert pick == booked + delay == _fnum(k["lyft_pickup_s"]), (rule, rid, pick)
        assert pick - x["t"] == _fnum(k["wait_s"]), (rule, rid)
        assert drop == pick + X.DWELL + int(round(r.ref.t0(x["o"], x["d"]) * params["travel_multiplier"])) \
            == _fnum(k["lyft_dropoff_s"]), (rule, rid, drop)
        cls = "XL" if x["q"] >= 5 else "standard"
        assert got_t[rid]["lyft_class"] == cls == k["lyft_class"], (rule, rid)
        assert states[rid][-1]["state_to"] == k["outcome"] == "lyft_completed"
    for rid, k in exp_d.items():
        assert got_d[rid]["t_s"] == _fnum(k["decision_s"]), (rule, rid, got_d[rid]["t_s"], k["decision_s"])
        assert not any(e["state_to"] == "xfer_hold" for e in states[rid]), f"{rule}: {rid} declined, transferred later"
        assert sum(e["event"] == "transfer_declined" and e["request"] == rid for e in ev) == 1
    if rule == "R0":
        assert not any(e["event"] == "transfer_declined" or e.get("state_to") in X.LYFT_STATES for e in ev)


# ======================================================================================================
# 4. accounting and invariants on every run
# ======================================================================================================
RUNS = [("L1", "R0"), ("L2", "R0"), ("L3", "R0")] + [("L4", rule) for rule in L4_RULES]


@pytest.mark.parametrize("level,rule", RUNS)
def test_accounting_and_invariants(level, rule):
    r = get_run(level, rule, False)
    ev, ref = r.eng.events, r.ref
    # (a) one terminal state per request; legal transitions; the state chain is consistent
    states = X.per_request_states(ev)
    assert set(states) == set(ref.req)
    for rid, seq in states.items():
        prev = "unrevealed"
        for e in seq:
            assert e["state_from"] == prev, (rid, e)
            assert e["state_to"] in X.ALLOWED_TRANSITIONS.get(prev, set()), (rid, prev, e["state_to"])
            prev = e["state_to"]
        assert sum(e["state_to"] in X.TERMINAL for e in seq) == 1 and prev in X.TERMINAL, (rid, prev)
    # replay in log order
    state = {rid: "unrevealed" for rid in ref.req}
    load = {v: 0 for v in ref.cap}
    committed_by, pickup_t = {}, {}
    ever_lyft = set()
    by_second = {}
    for i, e in enumerate(ev):
        by_second.setdefault(e["t_s"], []).append(i)
        rid, vid = e["request"], e["van"]
        if e["event"] == "depart" and e["stop"] == "P":
            assert rid not in ever_lyft and state[rid] == "committed", (rid, state[rid])
        if e["event"] in ("curb_arrival", "arrive_no_rider") and vid is not None:
            assert committed_by.get(rid) == vid, (rid, vid, committed_by.get(rid))
        if e["event"] != "state":
            continue
        state[rid] = e["state_to"]
        if e["state_to"] in X.LYFT_STATES:
            ever_lyft.add(rid)
            assert rid not in committed_by, f"{rid} committed to a van and then put in a Lyft state"
        if e["state_to"] == "committed":
            committed_by[rid] = vid
        if e["state_to"] == "onboard":
            assert committed_by.get(rid) == vid, (rid, vid, committed_by.get(rid))   # served by the committed van
            load[vid] += ref.req[rid]["q"]
            assert load[vid] <= ref.cap[vid], (vid, e["t_s"], load[vid])
            pickup_t[rid] = e["t_s"]
        if e["state_to"] == "noshow_van":
            assert committed_by.get(rid) == vid
        if e["state_to"] == "van_completed":
            load[vid] -= ref.req[rid]["q"]
            ride = e["t_s"] - pickup_t[rid]
            assert ride <= ref.G(rid), f"{rid}: ride {ride} s > guardrail {ref.G(rid)} s"
    assert all(v == 0 for v in load.values())
    # (b) no request in a van route and in a Lyft state at once: state right after each epoch (class 80)
    for ep in r.eng.epochs:
        tau = ep["tau_s"]
        st = {rid: "unrevealed" for rid in ref.req}
        for e in ev:                                       # stop at this second's first departure
            if e["t_s"] > tau or (e["t_s"] == tau and e["class"] == 90):
                break
            if e["event"] == "state":
                st[e["request"]] = e["state_to"]
        for vid, ch in ep["chosen"].items():
            for stop in ch["seq"]:
                rr = stop.split(":", 1)[1]
                assert st[rr] not in X.LYFT_STATES, (level, rule, tau, rr, st[rr])
        for o in ep["open"]:
            assert st[o["rid"]] == "pending_van", (tau, o["rid"], st[o["rid"]])
    # (c) time order; within a second, class order (D-52: a 0-s leg is processed after that second's departures,
    #     so a departure with arrive_s == t starts a new same-second segment)
    times = [e["t_s"] for e in ev]
    assert times == sorted(times)
    n_cascade = 0
    for t, idx in by_second.items():
        last = -1
        for i in idx:
            e = ev[i]
            if e["class"] < last:
                prev = ev[i - 1]
                assert prev["event"] == "depart" and prev["arrive_s"] == t and prev["class"] == 90, \
                    f"t={t}: class {e['class']} after {last} not explained by a 0-s leg: {prev}"
                n_cascade += 1
            last = e["class"]
    if n_cascade:
        print(f"\n[order] {level} {rule}: {n_cascade} same-second restart(s) after a 0-s departure (D-52)")


# ======================================================================================================
# 5. hidden traits are invisible to the dispatcher
# ======================================================================================================
FORBIDDEN = ("patience", "present", "presence", "absent", "noshow", "no_show", "consent", "lyft", "delay", "hidden",
             "latent", "eta_noise")


def _fields_recursive(cls, seen=None):
    seen = set() if seen is None else seen
    out = []
    for f in dataclasses.fields(cls):
        out.append((cls.__name__, f.name))
    for sub in (D.VanState, D.Rider, D.OpenRequest):
        if sub not in seen:
            seen.add(sub)
            out += _fields_recursive(sub, seen)
    return out


def _walk(obj):
    yield obj
    if dataclasses.is_dataclass(obj):
        for f in dataclasses.fields(obj):
            yield from _walk(getattr(obj, f.name))
    elif isinstance(obj, (tuple, list)):
        for v in obj:
            yield from _walk(v)


def test_observation_has_no_hidden_fields(l4r0):
    for cls, name in _fields_recursive(D.Observation):
        assert not any(tok in name.lower() for tok in FORBIDDEN), (cls, name)
    allowed = (D.Observation, D.VanState, D.Rider, D.OpenRequest, tuple, int, str)
    for s in l4r0.solves:
        for v in _walk(s.obs):
            assert isinstance(v, allowed) and not isinstance(v, (inputs.Hidden, float)), type(v)


def _plans(r):
    return [(s.obs.tau, {v: (tuple(rt.seq), rt.cost_u) for v, rt in s.plan.routes.items()}, tuple(s.plan.pending))
            for s in r.solves]


def test_hidden_traits_do_not_change_plans(l4r0):
    def perturb(hidden):   # values that never fire under R0 in L4: patience +1 h, consent/lyft delay unused,
        return {rid: dataclasses.replace(h, patience_s=h.patience_s + 3600, consent_u=1.0 - h.consent_u,
                                         lyft_delay_s=h.lyft_delay_s + 600,
                                         noshow_u=0.5 if h.noshow_u >= 0.5 else h.noshow_u)   # still present
                for rid, h in hidden.items()}
    alt = _execute("L4", "R0", hidden=perturb)
    assert alt.scen.hidden != l4r0.scen.hidden
    assert [s.obs for s in alt.solves] == [s.obs for s in l4r0.solves]
    assert _plans(alt) == _plans(l4r0)
    assert alt.eng.events == l4r0.eng.events


# ======================================================================================================
# 6. reproducibility
# ======================================================================================================
def _strip(epochs):
    out = []
    for ep in epochs:
        ep = dict(ep)
        ep["solver"] = {k: v for k, v in ep["solver"].items() if k != "wall_s"}
        out.append(ep)
    return out


def test_reproducible(l4r0):
    again = _execute("L4", "R0")
    assert again.eng.events == l4r0.eng.events
    assert _strip(again.eng.epochs) == _strip(l4r0.eng.epochs)
    assert len(again.eng.epochs) == len(l4r0.eng.epochs) > 0
