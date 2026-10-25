"""Independent check of the three pending-price formulations of dispatcher C (decision D-53).

What the implementation is trusted for: the candidate columns (S, cost, stop order) returned by dispatch.solve /
dispatch.candidates, and the travel oracle sim.inputs.Travel. Everything else is recomputed here from the written
definitions, by full enumeration of every compatible combination of columns (one column per van, disjoint request
sets). Nothing here calls dispatch.pending_prices, column_end, _milp, _exact_obj, _pend_cost, _canonical or phi_u.

Definitions (tn = the next 120-s tick after tau; U = 1,200,000 per point; phi in minutes, slopes 1, 2.5, 5, 10, 20,
breaks 5, 10, 15, 20):
    original  b_r  = q_r * phi(max(0, tn - t_r))
    A         b_r  = q_r * phi(max(tn, L_r) - t_r),  L_r = min_v free_v + T(loc_v, o_r)
    B         b_rj = q_r * phi(max(tn, e_j + T(l_j, o_r)) - t_r), (e_j, l_j) = van v_j free after route j
              (30-s dwell per stop, no waiting); a pending r is charged min_j over the CHOSEN columns.
    M = 1 + sum_v (max_k c_vk - min_k c_vk) + sum_r bmax_r     (bmax_r = b_r, or max_j b_rj for B)
    objective = sum chosen c + sum_pending (M + price)
    tie rule: requests in ID order, assigned van compared by numeric van ID, pending last.

Also re-checks the preserved whole-evening L4 runs (outputs/sim/d53_experiment/L4_R0_pp-{original,A,B} and
outputs/sim/L4_R0_M1_reference) epoch by epoch, and checks that a fresh in-memory L4 R0 run under the default
config (A) reproduces the preserved pp-A events.csv byte for byte.

Run: .venv/bin/python -m pytest -q tests/test_pending_price_independent.py      (-s prints the per-case findings)
"""
import csv
import itertools
import json
from fractions import Fraction
from pathlib import Path

import pytest

from sim import dispatch as D
from sim import inputs

ROOT = Path(__file__).resolve().parents[1]
PT = 1_200_000
DWELL = 30
TICK = 120
KINDS = ("original", "A", "B")

# real location IDs (data/processed/tt_locations_v2.csv); H is the L4 depot
H = "p04_b040"
NEAR = ["p05_b044", "p05_b036", "p04_b031", "p05_b043", "p04_b039", "p04_b051", "p05_b057"]
FAR = ["p03_b023", "p02_b020", "p03_b021", "p02_b021", "p02_b019", "p03_b020", "p03_b019", "p05_b041"]


@pytest.fixture(scope="module")
def travel():
    return inputs.Travel(1.0, 1.0)


# ---------------------------------------------------------------- reference definitions
def phi_ref(wait_s):
    """q = 1 penalty in U, from the slopes per minute (exact)."""
    w = Fraction(max(0, wait_s), 60)
    pts, lo = Fraction(0), Fraction(0)
    for hi, slope in zip((5, 10, 15, 20, None), (1, Fraction(5, 2), 5, 10, 20)):
        if w > lo:
            pts += slope * ((w if hi is None else min(w, hi)) - lo)
        if hi is None:
            break
        lo = Fraction(hi)
    u = pts * PT
    assert u.denominator == 1
    return int(u)


def next_tick_ref(tau):
    return (tau // TICK + 1) * TICK                     # smallest multiple of 120 s strictly after tau


def route_end(travel, free_s, loc, seq, where):
    """(e, l): when and where the van is free after the stop sequence; where(kind, rid) -> location."""
    t = free_s
    for kind, rid in seq:
        nxt = where(kind, rid)
        t += travel.van(loc, nxt) + DWELL
        loc = nxt
    return t, loc


def van_key(vid):
    digits = "".join(ch for ch in vid if ch.isdigit())
    return (0, int(digits), vid)


PENDING_KEY = (1, 0, "")


def enumerate_epoch(kind, tau, vans, open_reqs, cols_by_van, travel):
    """Full enumeration over the given columns.

    vans: list of (vid, free_s, loc, rider_dest {rid: d}) in solver order;
    open_reqs: list of (rid, t, o, d, q) sorted by rid;
    cols_by_van: {vid: [(S frozenset, cost_u, seq tuple of (kind, rid))]} in column order.
    Returns a dict with M, prices, the minimum objective, the canonical assignment and the counts."""
    rids = [x[0] for x in open_reqs]
    req = {x[0]: x for x in open_reqs}
    bit = {r: 1 << i for i, r in enumerate(rids)}
    tn = next_tick_ref(tau)
    cols, j = {}, 0                                      # global column index: cumulative over vans in listed order
    for vid, free_s, loc, rdest in vans:
        def where(k, rid, rdest=rdest):
            if k == "P":
                return req[rid][2]
            return req[rid][3] if rid in req else rdest[rid]
        lst = []
        for S, c, seq in cols_by_van[vid]:
            m = 0
            for r in S:
                m |= bit[r]
            e, l = (free_s, loc) if not seq else route_end(travel, free_s, loc, seq, where)
            lst.append((j, m, c, e, l, S))
            j += 1
        cols[vid] = lst
    ncols = j
    # pending prices
    if not vans or kind == "original":
        b = {r: q * phi_ref(max(0, tn - t)) for r, t, o, d, q in open_reqs}
        bmax, bj, L = dict(b), None, None
    elif kind == "A":
        L = {r: min(f + travel.van(lc, o) for _, f, lc, _ in vans) for r, t, o, d, q in open_reqs}
        b = {r: q * phi_ref(max(tn, L[r]) - t) for r, t, o, d, q in open_reqs}
        bmax, bj = dict(b), None
    elif kind == "B":
        bj = {r: {} for r in rids}
        for vid in cols:
            for (jj, m, c, e, l, S) in cols[vid]:
                for r, t, o, d, q in open_reqs:
                    bj[r][jj] = (q * phi_ref(max(tn, e + travel.van(l, o)) - t), max(tn, e + travel.van(l, o)))
        bmax = {r: max(v[0] for v in bj[r].values()) for r in rids}
        b, L = None, None
    else:
        raise ValueError(kind)
    R = sum(max(x[2] for x in cols[v[0]]) - min(x[2] for x in cols[v[0]]) for v in vans)
    M = 1 + R + sum(bmax.values())
    full = (1 << len(rids)) - 1
    best, best_key, min_pending, n_comb = None, None, None, 0
    lists = [cols[v[0]] for v in vans]
    for combo in itertools.product(*lists):
        m = 0
        ok = True
        for x in combo:
            if m & x[1]:
                ok = False
                break
            m |= x[1]
        if not ok:
            continue
        n_comb += 1
        pend = full & ~m
        npend = bin(pend).count("1")
        obj = sum(x[2] for x in combo)
        prices = {}
        for r in rids:
            if pend & bit[r]:
                if kind == "B" and vans:
                    p = min(bj[r][x[0]][0] for x in combo)
                else:
                    p = b[r]
                prices[r] = p
                obj += M + p
        who = {}
        for x in combo:
            for r in x[5]:
                who[r] = combo.index(x)
        key = tuple(van_key(vans[who[r]][0]) if r in who else PENDING_KEY for r in rids)
        if min_pending is None or npend < min_pending:
            min_pending = npend
        if best is None or (obj, key) < (best[0], best_key):
            best, best_key = (obj, combo, prices, npend), key
    out = {"tn": tn, "M": M, "R": R, "sum_bmax": sum(bmax.values()), "b": b, "bmax": bmax, "L": L, "bj": bj,
           "ncols": ncols, "n_comb": n_comb, "min_pending": min_pending}
    if best is None:                                     # no van: everything pending, one "combination"
        prices = {r: b[r] for r in rids}
        out.update(obj=sum(M + p for p in prices.values()), assign={r: None for r in rids}, prices=prices,
                   npend=len(rids), chosen_cols=[], route_cost=0, min_pending=len(rids))
        return out
    obj, combo, prices, npend = best
    assign = {r: None for r in rids}
    for vi, x in enumerate(combo):
        for r in x[5]:
            assign[r] = vans[vi][0]
    out.update(obj=obj, assign=assign, prices=prices, npend=npend, chosen_cols=[x[0] for x in combo],
               route_cost=sum(x[2] for x in combo),
               priced_after={r: vans[min(range(len(combo)), key=lambda i: (bj[r][combo[i][0]][0], i))][0]
                             for r in prices} if kind == "B" and vans else None,
               priced_pickup={r: min(bj[r][x[0]] for x in combo)[1] for r in prices} if kind == "B" and vans
               else None)
    return out


# ---------------------------------------------------------------- synthetic epochs
def mkvan(vid, loc, free_s, riders=(), committed=(), cwait=0, cap=14):
    return D.VanState(vid, cap, loc, free_s, tuple(sorted(riders, key=lambda r: r.rid)), committed, cwait)


def check(obs, travel, kind, K):
    """Solve with the implementation, enumerate independently, assert agreement. Returns (plan, ref)."""
    cfg = D.Config(K=K, pending_price=kind)
    plan, cands = D.solve(obs, travel, cfg)
    assert plan.log["status"] == "optimal"
    vans = [(v.vid, v.free_s, v.loc, {r.rid: r.d for r in v.riders}) for v in obs.vans]
    open_reqs = [(x.rid, x.t, x.o, x.d, x.q) for x in obs.open]
    assert [x[0] for x in open_reqs] == sorted(x[0] for x in open_reqs)
    ref = enumerate_epoch(kind, obs.tau, vans, open_reqs, cands, travel)
    # same M, same minimum objective, same canonical choice, fewest pending
    assert plan.log["M_u"] == ref["M"], (kind, plan.log["M_u"], ref["M"])
    assert plan.log["objective_u"] == ref["obj"], (kind, plan.log["objective_u"], ref["obj"])
    impl_assign = {x.rid: None for x in obs.open}
    for v, rt in plan.routes.items():
        for r in rt.S:
            impl_assign[r] = v
    assert impl_assign == ref["assign"], (kind, impl_assign, ref["assign"])
    assert len(plan.pending) == ref["npend"] == ref["min_pending"]
    # the price the implementation reports as charged equals ours
    for r in plan.pending:
        assert plan.pending_info[r]["pending_price_u"] == ref["prices"][r], (kind, r)
        if kind == "A":
            assert plan.pending_info[r]["earliest_pickup_s"] == ref["L"][r]
        if kind == "B":
            assert plan.pending_info[r]["priced_pickup_s"] == ref["priced_pickup"][r]
    if kind == "B":                                     # column ends recomputed from the stop sequences
        cols = [(v, S, c, seq) for v in [x.vid for x in obs.vans] for (S, c, seq) in cands[v]]
        assert len(cols) == ref["ncols"]
        assert plan.log["n_z"] == len(obs.open) * ref["ncols"]
    return plan, ref


def case_a_old_vs_young():
    """One van, K = 1: one old request far away (waited 15 min) against two young ones near the van."""
    tau = 1800
    van = mkvan("V1", H, tau)
    rq = (D.OpenRequest("R1", tau - 900, FAR[4], NEAR[0], 1),
          D.OpenRequest("R2", tau - 60, NEAR[1], FAR[7], 1),
          D.OpenRequest("R3", tau - 60, NEAR[2], NEAR[5], 1))
    return D.Observation(tau, (van,), rq), 1


def case_b_party_size():
    """One van, K = 1: two requests of the same age (8 min), party of 1 near, party of 5 a little further."""
    tau = 1800
    van = mkvan("V1", H, tau)
    rq = (D.OpenRequest("R1", tau - 480, NEAR[1], FAR[6], 1),
          D.OpenRequest("R2", tau - 480, FAR[7], NEAR[3], 5))
    return D.Observation(tau, (van,), rq), 1


def case_c_binding_cap():
    """Two vans, K = 2, six requests of mixed age, size and place: at least two must be pending."""
    tau = 2400
    vans = (mkvan("V1", H, tau), mkvan("V2", NEAR[4], tau + 45))
    rq = (D.OpenRequest("R1", tau - 1080, FAR[0], NEAR[2], 2),
          D.OpenRequest("R2", tau - 600, NEAR[3], FAR[5], 1),
          D.OpenRequest("R3", tau - 300, FAR[3], H, 5),
          D.OpenRequest("R4", tau - 200, NEAR[5], NEAR[6], 1),
          D.OpenRequest("R5", tau - 100, NEAR[0], FAR[1], 3),
          D.OpenRequest("R6", tau - 30, FAR[6], NEAR[1], 1))
    return D.Observation(tau, vans, rq), 2


def case_d_shared_van():
    """One van, K = 1, four requests: three must be pending and all compete for the one van's next position."""
    tau = 1800
    van = mkvan("V1", H, tau)
    rq = (D.OpenRequest("R1", tau - 420, NEAR[1], FAR[2], 1),
          D.OpenRequest("R2", tau - 360, NEAR[2], NEAR[6], 2),
          D.OpenRequest("R3", tau - 300, NEAR[3], FAR[4], 1),
          D.OpenRequest("R4", tau - 240, NEAR[5], NEAR[0], 1))
    return D.Observation(tau, (van,), rq), 1


def case_e_all_assignable():
    """Two vans, K = 3, three requests: all can be served, so every formulation must return the same plan."""
    tau = 1800
    vans = (mkvan("V1", H, tau), mkvan("V2", NEAR[4], tau))
    rq = (D.OpenRequest("R1", tau - 700, FAR[1], NEAR[2], 2),
          D.OpenRequest("R2", tau - 200, NEAR[3], FAR[5], 1),
          D.OpenRequest("R3", tau - 50, NEAR[0], NEAR[6], 4))
    return D.Observation(tau, vans, rq), 3


def case_f_committed_work(travel):
    """Two vans with work in progress (a rider aboard, a committed pickup): exercises route ends that end at a
    drop-off of a rider who is not an open request. K = 2, five open requests."""
    tau = 3000
    t_on, t_c = 2500, 2700
    p_on = 2650
    arr = tau + travel.van(H, NEAR[2])                  # V1 is driving to its committed pickup at NEAR[2]
    r_on = D.Rider("Q1", FAR[2], 2, t_on, p_on, travel.van(NEAR[6], FAR[2]))
    r_c = D.Rider("Q2", NEAR[5], 1, t_c, arr, travel.van(NEAR[2], NEAR[5]))
    v1 = mkvan("V1", NEAR[2], arr + DWELL, riders=(r_on, r_c), committed=("Q2", "P", arr),
               cwait=1 * phi_ref(arr - t_c))
    r_on2 = D.Rider("Q3", FAR[6], 1, 2600, 2900, travel.van(H, FAR[6]))
    v2 = mkvan("V2", H, tau, riders=(r_on2,))
    rq = (D.OpenRequest("R1", tau - 900, FAR[3], NEAR[0], 1),
          D.OpenRequest("R2", tau - 500, NEAR[3], FAR[0], 3),
          D.OpenRequest("R3", tau - 300, NEAR[1], NEAR[4], 1),
          D.OpenRequest("R4", tau - 120, FAR[5], H, 2),
          D.OpenRequest("R5", tau - 20, NEAR[6], FAR[1], 1))
    return D.Observation(tau, (v1, v2), rq), 2


CASES = {"a_old_vs_young": case_a_old_vs_young, "b_party_size": case_b_party_size,
         "c_binding_cap": case_c_binding_cap, "d_shared_van": case_d_shared_van,
         "e_all_assignable": case_e_all_assignable}


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("name", list(CASES))
def test_small_case_matches_enumeration(name, kind, travel):
    obs, K = CASES[name]()
    plan, ref = check(obs, travel, kind, K)
    print(f"\n[{name}/{kind}] pending={sorted(plan.pending)} obj-M*n={ref['obj'] - ref['M'] * ref['npend']} "
          f"prices={ref['prices']}")


@pytest.mark.parametrize("kind", KINDS)
def test_committed_work_case_matches_enumeration(kind, travel):
    obs, K = case_f_committed_work(travel)
    check(obs, travel, kind, K)


def test_all_assignable_gives_same_plan(travel):
    obs, K = case_e_all_assignable()
    plans = {k: check(obs, travel, k, K)[0] for k in KINDS}
    assert all(not p.pending for p in plans.values())
    ref = {v: (rt.S, rt.seq) for v, rt in plans["original"].routes.items()}
    for k in KINDS:
        assert {v: (rt.S, rt.seq) for v, rt in plans[k].routes.items()} == ref
        # with nothing pending the objective is the route cost alone; only M differs between formulations
        assert plans[k].log["objective_u"] == sum(rt.cost_u for rt in plans[k].routes.values())


def test_phi_reference_points():
    assert [phi_ref(m * 60) / PT for m in (5, 10, 15, 20)] == [5, 17.5, 42.5, 92.5]
    assert phi_ref(-10) == 0 and phi_ref(1) == PT // 60


# ---------------------------------------------------------------- demonstrations (task 3)
def test_A_optimism_competing_work(travel):
    """A prices a pending rider as if the closest van were free now; that van is busy with the route it is given."""
    tau = 1800
    van = mkvan("V1", H, tau)
    rq = (D.OpenRequest("R1", tau - 600, NEAR[0], FAR[0], 1),      # near the van, long trip out
          D.OpenRequest("R2", tau - 590, NEAR[1], NEAR[2], 1))     # also near the van
    obs = D.Observation(tau, (van,), rq)
    plan, ref = check(obs, travel, "A", 1)
    (pend,) = plan.pending
    served = next(iter(plan.routes["V1"].S))
    rt = plan.routes["V1"]
    x = {r.rid: r for r in rq}[pend]
    end_t = rt.arrivals[-1] + DWELL
    after = end_t + travel.van({r.rid: r for r in rq}[served].d, x.o)
    # A assumes the pickup at L_r (van free now); the earliest pickup consistent with the chosen route (append) is later
    assert ref["L"][pend] < after
    gap_pts = (x.q * phi_ref(after - x.t) - ref["prices"][pend]) / PT
    assert gap_pts > 0
    print(f"\n[A optimism] serves {served}, pends {pend}: A assumes pickup {ref['L'][pend]} s, "
          f"after the chosen route {after} s; under-charge {gap_pts:.2f} points")


def test_B_shared_claims_on_one_van(travel):
    """(d): under B all pending riders are priced after the same van's route end; no van can do that jointly."""
    obs, K = case_d_shared_van()
    plan, ref = check(obs, travel, "B", K)
    req = {x.rid: x for x in obs.open}
    pend = sorted(plan.pending)
    assert len(pend) == 3 and set(ref["priced_after"].values()) == {"V1"}
    pk = ref["priced_pickup"]
    # every pending rider is priced at a pickup reached directly from the same (e_j, l_j);
    # a single van serving them one after another must reach at least one of each pair later
    e_j = plan.routes["V1"].arrivals[-1] + DWELL
    for r in pend:
        assert pk[r] == max(next_tick_ref(obs.tau), e_j + travel.van(_end_loc(plan, req), req[r].o))
    best_joint = None
    for order in itertools.permutations(pend):         # pick all three in some order straight after the route
        t, loc, cost = e_j, _end_loc(plan, req), 0
        for r in order:
            t = max(next_tick_ref(obs.tau), t + travel.van(loc, req[r].o))
            cost += req[r].q * phi_ref(t - req[r].t)
            t, loc = t + DWELL, req[r].o
        best_joint = cost if best_joint is None else min(best_joint, cost)
    sum_b = sum(ref["prices"].values())
    assert sum_b < best_joint
    print(f"\n[B shared van] pending {pend} priced at pickups {[pk[r] for r in pend]} (all after V1's end "
          f"{e_j} s); sum of B prices {sum_b / PT:.2f} pts < best joint pick-up-in-a-row {best_joint / PT:.2f} pts")


def _end_loc(plan, req):
    kind, rid = plan.routes["V1"].seq[-1]
    return req[rid].o if kind == "P" else req[rid].d


def test_B_pessimism_next_epoch_inserts_earlier(travel):
    """(ii): B charges a pending rider the wait after the van's whole route; at the next epoch the van has
    committed to its first stop, the cap frees up, and the rider is inserted before the route ends."""
    tau = 1800
    van = mkvan("V1", H, tau)
    r1 = D.OpenRequest("R1", tau - 400, NEAR[1], FAR[3], 1)
    r2 = D.OpenRequest("R2", tau - 380, NEAR[2], NEAR[4], 1)
    obs = D.Observation(tau, (van,), (r1, r2))
    plan, ref = check(obs, travel, "B", 1)
    assert plan.pending == ["R2"] or plan.pending == ["R1"]
    p = plan.pending[0]
    s = "R1" if p == "R2" else "R2"
    rs, rp = (r1, r2) if s == "R1" else (r2, r1)
    priced = ref["priced_pickup"][p]
    # a later epoch (30 s on, e.g. triggered by any event): V1 is driving to its committed pickup of s; as in the
    # engine's observation, the rider counts as aboard at the planned pickup and the van is free after the dwell
    arr = plan.routes["V1"].arrivals[0]
    tau2 = tau + 30
    assert arr > tau2
    rider = D.Rider(s, rs.d, rs.q, rs.t, arr, travel.van(rs.o, rs.d))
    v2 = mkvan("V1", rs.o, arr + DWELL, riders=(rider,), committed=(s, "P", arr), cwait=rs.q * phi_ref(arr - rs.t))
    obs2 = D.Observation(tau2, (v2,), (rp,))
    plan2, _ = check(obs2, travel, "B", 1)
    assert p in plan2.predicted_pickup
    assert plan2.predicted_pickup[p] < priced
    print(f"\n[B pessimism] at {tau} s {p} priced at pickup {priced} s; at {tau2} s it is planned at "
          f"{plan2.predicted_pickup[p]} s ({(priced - plan2.predicted_pickup[p]) / 60:.1f} min earlier)")


def test_M_magnitude_below_2_53():
    """Plausible upper ranges: 5 vans, 20 open, waits up to 120 min, parties of 5, K = 3 pickups per route, a full
    van (14 riders) riding 60 min, 100 km, and (worst case) 60 min over the guardrail for all 14 riders."""
    cfg = D.Config()
    b = 5 * phi_ref(120 * 60)                           # 1.26e10 U per request
    route_no_psi = 3 * b + cfg.ride_u * 14 * 3600 + cfg.km_u * 1_000_000
    for route, headroom in ((route_no_psi, 900), (route_no_psi + cfg.psi_u * 14 * 3600, 50)):
        M = 1 + 5 * route + 20 * b                      # every route cost range bounded by the route itself
        obj = 5 * route + 20 * (M + b)                  # everything pending: the largest objective
        assert obj * headroom < 2 ** 53                 # integers stay exact in a double
        assert float(obj) == obj


# ---------------------------------------------------------------- logged whole-evening runs
# preserved D-53 evidence runs (outputs/sim/L4_R0/ is now the default-A arm and is not checked here)
RUNS = {"d53_experiment/L4_R0_pp-original": "original", "d53_experiment/L4_R0_pp-A": "A",
        "d53_experiment/L4_R0_pp-B": "B", "L4_R0_M1_reference": "original"}


def _requests():
    with open(ROOT / "data" / "scenarios" / "v2" / "L4" / "requests.csv") as f:
        return {r["request_id"]: r for r in csv.DictReader(f)}


@pytest.mark.parametrize("run", list(RUNS))
def test_logged_run_epochs(run, travel):
    """Every optimal epoch of a preserved run, by full enumeration of the logged candidates."""
    path = ROOT / "outputs" / "sim" / run / "epochs.jsonl"
    assert path.exists(), f"{path} missing: the preserved D-53 evidence is required"
    man = json.loads((path.parent / "run_manifest.json").read_text())
    assert man["travel_multiplier"] == {"m_v": 1.0, "m_L": 1.0}
    kind = RUNS[run]
    if "pending_price" in man["dispatcher"]:
        assert man["dispatcher"]["pending_price"] == kind
    rq = _requests()
    n_checked = 0
    for line in path.open():
        e = json.loads(line)
        s = e["solver"]
        if s["status"] != "optimal":
            continue
        vans = [(v["van"], v["free_s"], v["loc"], {x["rid"]: rq[x["rid"]]["d_loc"] for x in v["riders"]})
                for v in e["vans"]]
        open_reqs = [(x["rid"], x["t_s"], rq[x["rid"]]["o_loc"], rq[x["rid"]]["d_loc"], x["q"]) for x in e["open"]]
        cols = {v["van"]: [(frozenset(c["S"]), c["cost_u"],
                            tuple((z.split(":")[0], z.split(":")[1]) for z in c["seq"]))
                           for c in e["candidates"][v["van"]]] for v in e["vans"]}
        ref = enumerate_epoch(kind, e["tau_s"], vans, open_reqs, cols, travel)
        tag = (run, e["tau_s"])
        assert s["next_tick_s"] == ref["tn"], tag
        assert s["M_u"] == ref["M"], tag
        assert s["objective_u"] == ref["obj"], tag
        if s["tie_status"] in ("unique", "tie"):
            for v in e["vans"]:
                chosen = [c for c in e["candidates"][v["van"]] if c["chosen"]]
                assert len(chosen) == 1
                assert sorted(chosen[0]["S"]) == sorted(r for r, w in ref["assign"].items() if w == v["van"]), tag
        assert len(e["pending"]) == ref["npend"] == ref["min_pending"], tag
        for r, info in e["pending"].items():
            if "pending_price_u" in info or run != "L4_R0_M1_reference":     # the M1 log predates this field
                assert info["pending_price_u"] == ref["prices"][r], (tag, r)
        if kind == "B" and vans:
            assert s["n_z"] == len(open_reqs) * ref["ncols"], tag
            assert s["n_rows"] == len(vans) + 2 * len(open_reqs) + s["n_z"], tag
            # logged column ends equal ours
            j = 0
            for v in vans:
                req = {x[0]: x for x in open_reqs}
                for S, c, seq in cols[v[0]]:
                    def where(k, rid, rd=v[3]):
                        return req[rid][2] if k == "P" else (req[rid][3] if rid in req else rd[rid])
                    end = (v[1], v[2]) if not seq else route_end(travel, v[1], v[2], seq, where)
                    assert s["column_end"][str(j)] == [end[0], end[1]], (tag, j)
                    j += 1
            for r, info in e["pending"].items():
                assert info["priced_pickup_s"] == ref["priced_pickup"][r], (tag, r)
        if kind == "A" and vans:
            assert s["earliest_pickup_s"] == ref["L"], tag
        n_checked += 1
    assert n_checked >= 40
    print(f"\n[{run}] {n_checked} epochs re-checked by full enumeration")


def test_default_is_A_and_reproduces_preserved_A_run():
    """A fresh L4 R0 run under the default dispatcher config (pending_price "A", D-53 approval), run in memory
    (nothing written to outputs/), gives events byte-identical to the preserved D-53 pp-A run."""
    import io
    import pandas as pd
    from sim import engine as E
    from sim import run as RUN
    assert D.Config().pending_price == "A"
    scen = inputs.load("L4")
    m = scen.params["travel_multiplier"]
    pol = RUN.policy_for(scen, "R0")
    assert pol.dispatcher == D.Config()
    eng = E.Engine(scen, inputs.Travel(m_v=m, m_L=m), pol).run()
    buf = io.StringIO()
    pd.DataFrame(eng.events).to_csv(buf, index=False)
    ref = (ROOT / "outputs" / "sim" / "d53_experiment" / "L4_R0_pp-A" / "events.csv").read_bytes()
    assert buf.getvalue().encode() == ref
