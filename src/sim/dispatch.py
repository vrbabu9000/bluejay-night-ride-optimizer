"""Dispatcher C: restricted route-selection MILP (decision log D-51, settings D-52).

At each epoch the dispatcher receives an Observation (public state only; no hidden rider traits) and returns a Plan.

1. Candidates, per van. Every subset S of the open requests with |S| <= K (K = max new pickups per route), in the
   best order of all the van's stops for that S: new pickups and drop-offs and the drop-offs of riders already
   aboard (optional restriction: existing riders keep the committed-only drop order, `fix_existing_drop_order`). The best order is found exactly by a label-setting search
   (dominance below), so for a given S nothing is lost by keeping one route. The empty subset (committed work only)
   is always a candidate, so the MILP is always feasible.
2. Route cost c_vk (D-29, model_design §3.5), in integer cost units U (1 point = PT units, exact arithmetic):
       sum_r q_r*phi(W_r) over pickups in the route (incl. a committed pickup)
     + beta * sum_r q_r*H_r over riders dropped in the route (incl. riders already onboard)
     + gamma * km
     + Psi * sum_r q_r*(H_r - G_r)+                    (only unavoidable violations; see the guardrail rule)
   W = curb arrival - request time; H = drop-off arrival - pickup arrival (includes the 30-s boarding dwell).
3. MILP (set partitioning):  min sum c_vk y_vk + sum pi_r u_r
       sum_k y_vk = 1 for every van;  sum_{v,k: r in S_k} y_vk + u_r = 1 for every open request.
   pi_r = q_r*phi(W_r^next) + M with W_r^next = next tick - t_r and
       M = 1 + sum_v (max_k c_vk - min_k c_vk) + sum_r q_r*phi(W_r^next).
   With this M every optimal solution leaves the fewest requests pending that the candidate set allows
   (proof in D-52); among those it minimises cost. This is optimality over the candidate set only.
   Status per epoch: optimal (gap closed over the candidate set); feasible_unproven (node budget reached; the best
   incumbent found is executed and labelled, pending reasons are then not established); failed (no incumbent: the
   vans execute committed work only, logged, no heuristic is called); empty (nothing to decide). A HiGHS error,
   an infeasible model or the wall-clock safety stop ends the run with an error.
4. Ties. Equal-objective optima are enumerated with no-good cuts and the canonical one is chosen: for the requests
   in ID order, the assigned van ID is compared lexicographically (pending sorts last). Within one (van, S) the
   lexicographically smallest stop order among equal-cost orders is kept.

Guardrail (D-47, proposal): G_r = max(25 min, 2*van_direct + 5 min). A candidate may not create or increase a
violation: new riders need H <= G; riders already onboard or committed need H <= max(G, H in the committed-only route).

Label dominance (exactness of step 1; riders already aboard have fixed pickup times, so only riders picked in the
route need the slack criterion). Cost is decomposed so the remaining cost depends only on the remaining stops
and the clock: a pickup at time a adds q*phi(a - t) - beta*q*a, a drop at time D adds beta*q*D (+ Psi term). Because
phi' >= 1 > beta, every future term is non-decreasing in time. Two partial routes with the same picked set, dropped
set and last stop: A dominates B if time_A <= time_B, cost_A <= cost_B and, for every rider picked in the route and
still onboard, pickup_A >= pickup_B (at least as much guardrail slack); ties in all of these keep the smaller order.
The argument needs one more fact, which holds in this model: vans never wait on purpose and there are no time
windows, so any completion of B applied to A is B's schedule shifted earlier (independent math review, 21-22 Oct).
"""
from dataclasses import dataclass, field
from itertools import combinations
import time as _time

import highspy
import numpy as np

DWELL_S = 30
PT = 1_200_000                                   # cost units per point: makes every term an exact integer
PHI_BREAKS_S = (0, 300, 600, 900, 1200)
PHI_SLOPES_120 = (2, 5, 10, 20, 40)              # 120 x slope per second (= 1, 2.5, 5, 10, 20 per minute)


@dataclass(frozen=True)
class Config:
    K: int = 3                     # max new (uncommitted) pickups per candidate route (D-52)
    fix_existing_drop_order: bool = False   # True: existing riders keep the committed-only drop order (faster,
                                            # smaller candidate set; an explicit setting, never switched automatically)
    beta: float = 0.5              # points per passenger-minute riding
    gamma: float = 0.1             # points per km
    psi: int = 1000                # points per passenger-minute over the guardrail (unavoidable violations only)
    tick_s: int = 120
    g_abs_s: int = 1500            # 25 min
    g_alpha: int = 2
    g_delta_s: int = 300           # 5 min
    mip_rel_gap: float = 0.0
    mip_abs_gap: float = 0.5       # objective is integer-valued in U, so a gap below 1 proves optimality
    mip_max_nodes: int = 100_000   # deterministic budget
    time_limit_s: float = 3600.0   # safety cap only; hitting it stops the run with an error, so wall time can never
                                   # change a plan (D-46); the node limit is the deterministic budget
    max_tie_solves: int = 50
    threads: int = 1
    random_seed: int = 0

    def __post_init__(self):
        # exact integer arithmetic needs beta*PT/60 and gamma*PT/10000 (per decimetre) to be integers
        if not (float(self.beta * PT / 60).is_integer() and float(self.gamma * PT / 10_000).is_integer()):
            raise ValueError("beta and gamma must give integer cost units (exact arithmetic)")

    @property
    def ride_u(self):              # U per passenger-second of riding
        return int(self.beta * PT / 60)

    @property
    def km_u(self):                # U per decimetre
        return int(self.gamma * PT / 10_000)

    @property
    def psi_u(self):               # U per passenger-second over the guardrail
        return int(self.psi * PT / 60)


def phi_u(wait_s):
    """phi(W) for one passenger, in U. phi(5 min) = 5 points, phi(10) = 17.5, phi(15) = 42.5, phi(20) = 92.5."""
    w, out = max(0, int(wait_s)), 0
    edges = PHI_BREAKS_S + (10 ** 12,)
    for lo, hi, s in zip(edges[:-1], edges[1:], PHI_SLOPES_120):
        if w > lo:
            out += s * (min(w, hi) - lo)
    return out * (PT // 120)


# ---------- observation and plan ----------
@dataclass(frozen=True)
class Rider:
    """A rider the van already carries, or will carry after its committed pickup (planning assumes boarding)."""
    rid: str
    d: str
    q: int
    t: int            # request time
    pickup_s: int     # actual (onboard) or planned (committed) curb arrival
    direct_van_s: int


@dataclass(frozen=True)
class VanState:
    vid: str
    capacity: int
    loc: str          # where the van is free for new stops
    free_s: int       # when it is free (after its committed stop's service)
    riders: tuple     # Rider, sorted by rid
    committed: tuple  # (rid, kind, arrive_s) of the stop the van is driving to or serving, or ()
    committed_wait_u: int = 0   # phi of a committed pickup (constant for this van; included in its route costs)


@dataclass(frozen=True)
class OpenRequest:
    rid: str
    t: int
    o: str
    d: str
    q: int


@dataclass(frozen=True)
class Observation:
    tau: int
    vans: tuple       # VanState, on-duty vans, sorted by vid
    open: tuple       # OpenRequest, sorted by rid: revealed, not committed, not onboard, not cancelled, not transferred


@dataclass
class Route:
    vid: str
    S: frozenset
    seq: tuple                    # ((kind, rid), ...) kind 'P' or 'D'
    cost_u: int
    arrivals: tuple = ()          # curb arrival time per stop
    parts_u: dict = field(default_factory=dict)


@dataclass
class Plan:
    tau: int
    routes: dict                  # vid -> Route
    pending: list                 # rids
    pending_info: dict            # rid -> {"reason":..., "per_van":..., "tentative_eta_s":...}
    predicted_pickup: dict        # rid -> s
    log: dict


# ---------- route evaluation (also used by tests and the narrative) ----------
def guardrail_s(direct_van_s, cfg):
    return max(cfg.g_abs_s, cfg.g_alpha * direct_van_s + cfg.g_delta_s)


def evaluate(van, seq, req, travel, cfg, allowed=None):
    """Schedule and cost of a stop order for one van. Returns a dict; 'feasible' covers precedence, capacity and the
    guardrail rule (allowed: rid -> max ride for riders already onboard/committed; None = no guardrail for them)."""
    t, loc = van.free_s, van.loc
    load = sum(r.q for r in van.riders)
    pick, onboard = {}, {r.rid: r for r in van.riders}
    for r in van.riders:
        pick[r.rid] = r.pickup_s
    wait_u = van.committed_wait_u
    ride_u = km_u = psi_u = 0
    arrivals, rides, waits, ok = [], {}, {}, load <= van.capacity
    for kind, rid in seq:
        if kind == "P":
            x = req[rid]
            km_u += cfg.km_u * travel.dm(loc, x.o)
            a = t + travel.van(loc, x.o)
            loc, load = x.o, load + x.q
            ok &= rid not in pick and load <= van.capacity
            pick[rid] = a
            waits[rid] = a - x.t
            wait_u += x.q * phi_u(a - x.t)
            onboard[rid] = Rider(rid, x.d, x.q, x.t, a, travel.van(x.o, x.d))
        else:
            r = onboard.pop(rid, None)
            if r is None:
                return {"feasible": False}
            km_u += cfg.km_u * travel.dm(loc, r.d)
            a = t + travel.van(loc, r.d)
            loc, load = r.d, load - r.q
            h = a - pick[rid]
            rides[rid] = h
            g = guardrail_s(r.direct_van_s, cfg)
            lim = g if rid in req else (allowed[rid] if allowed is not None else None)
            if lim is not None and h > lim:
                ok = False
            ride_u += cfg.ride_u * r.q * h
            psi_u += cfg.psi_u * r.q * max(0, h - g)
        arrivals.append(a)
        t = a + DWELL_S
    ok &= not onboard
    return {"feasible": bool(ok), "arrivals": tuple(arrivals), "waits": waits, "rides": rides,
            "parts_u": {"wait": wait_u, "ride": ride_u, "km": km_u, "psi": psi_u},
            "cost_u": wait_u + ride_u + km_u + psi_u}


# ---------- exact best order per subset (label-setting search) ----------
def best_routes(van, open_reqs, travel, cfg, K, allowed, base_order=None):
    """Best stop order for every subset S of open_reqs with |S| <= K. Returns {frozenset S: (cost_u, seq)}.
    allowed: rid -> max ride for the van's existing riders (None = unconstrained, for the committed-only route).
    base_order: if given, the van's existing riders are dropped in this order (new stops are interleaved freely)."""
    req = {x.rid: x for x in open_reqs}
    gr = {x.rid: guardrail_s(travel.van(x.o, x.d), cfg) for x in open_reqs}
    ride_u, km_u, psi_u = cfg.ride_u, cfg.km_u, cfg.psi_u
    base = {r.rid: r for r in van.riders}
    # constant part: committed pickup wait, and -beta*q*p for riders already onboard/committed
    c0 = van.committed_wait_u - sum(ride_u * r.q * r.pickup_s for r in van.riders)
    load0 = sum(r.q for r in van.riders)
    start = (frozenset(), frozenset(), None)
    layer = {start: [(van.free_s, c0, (), ())]}          # key -> [(time, cost, pvec, seq)]
    best = {}
    while layer:                                       # one layer per stop; ends when no label can be extended
        nxt = {}
        for (picked, dropped, last), labels in layer.items():
            loc = van.loc if last is None else (req[last[1]].o if last[0] == "P"
                                                else (req[last[1]].d if last[1] in req else base[last[1]].d))
            onboard_new = sorted(r for r in picked if r not in dropped)
            onboard_old = [r for r in base if r not in dropped]
            for (t, c, pvec, seq) in labels:
                if not onboard_new and not onboard_old:
                    S = picked
                    cur = best.get(S)
                    if cur is None or (c, seq) < cur:
                        best[S] = (c, seq)
                load = load0 - sum(base[r].q for r in base if r in dropped) + sum(req[r].q for r in onboard_new)
                pmap = dict(zip(onboard_new, pvec))
                moves = []
                if len(picked) < K:
                    for rid, x in req.items():
                        if rid in picked or load + x.q > van.capacity:
                            continue
                        a = t + travel.van(loc, x.o)
                        nc = c + km_u * travel.dm(loc, x.o) + x.q * phi_u(a - x.t) - ride_u * x.q * a
                        npick = picked | {rid}
                        nonb = sorted(r for r in npick if r not in dropped)
                        nmap = dict(pmap); nmap[rid] = a
                        moves.append(((npick, dropped, ("P", rid)), (a + DWELL_S, nc, tuple(nmap[r] for r in nonb),
                                                                      seq + (("P", rid),))))
                drop_old = onboard_old
                if base_order is not None and onboard_old:
                    drop_old = [base_order[len(base) - len(onboard_old)]]
                for rid in onboard_new + drop_old:
                    if rid in req:
                        x = req[rid]; dest, q, p, lim, g = x.d, x.q, pmap[rid], gr[rid], gr[rid]
                    else:
                        r = base[rid]; dest, q, p = r.d, r.q, r.pickup_s
                        g = guardrail_s(r.direct_van_s, cfg)
                        lim = None if allowed is None else allowed[rid]
                    a = t + travel.van(loc, dest)
                    h = a - p
                    if lim is not None and h > lim:
                        continue
                    nc = c + km_u * travel.dm(loc, dest) + ride_u * q * a + psi_u * q * max(0, h - g)
                    ndrop = dropped | {rid}
                    nonb = [r for r in onboard_new if r != rid]
                    moves.append(((picked, ndrop, ("D", rid)), (a + DWELL_S, nc, tuple(pmap[r] for r in nonb),
                                                                 seq + (("D", rid),))))
                for key, lab in moves:
                    _insert(nxt.setdefault(key, []), lab)
        layer = nxt
    return best


def _insert(labels, lab):
    t, c, p, s = lab
    for (t2, c2, p2, s2) in labels:
        if t2 <= t and c2 <= c and all(a >= b for a, b in zip(p2, p)) and (c2 < c or s2 < s):
            return                                   # dominated
    labels[:] = [L for L in labels
                 if not (t <= L[0] and c <= L[1] and all(a >= b for a, b in zip(p, L[2])) and (c < L[1] or s < L[3]))]
    labels.append(lab)


# ---------- the epoch solve ----------
def candidates(obs, travel, cfg):
    """All candidate routes per van, plus the 'allowed' ride limits used for each van's existing riders."""
    out, allowed_by_van = {}, {}
    cache = travel.__dict__.setdefault("_candidate_cache", {})
    for van in obs.vans:
        key = (van, obs.open, cfg)
        if key in cache:                                  # same van state and same open requests: same candidates
            out[van.vid], allowed_by_van[van.vid] = cache[key]
            continue
        exempt = best_routes(van, (), travel, cfg, 0, None)[frozenset()]
        ev = evaluate(van, exempt[1], {}, travel, cfg, None)
        allowed = {r.rid: max(guardrail_s(r.direct_van_s, cfg), ev["rides"][r.rid]) for r in van.riders}
        allowed_by_van[van.vid] = allowed
        base_order = [rid for kind, rid in exempt[1]] if cfg.fix_existing_drop_order else None
        routes = best_routes(van, obs.open, travel, cfg, cfg.K, allowed, base_order)
        routes[frozenset()] = exempt                      # committed-only route: exempt from the guardrail rule
        out[van.vid] = sorted(((S, c, seq) for S, (c, seq) in routes.items()),
                              key=lambda z: (len(z[0]), sorted(z[0]), z[1]))
        cache[key] = (out[van.vid], allowed)
    return out, allowed_by_van


def next_tick(tau, tick_s):
    return (tau // tick_s + 1) * tick_s


def solve(obs, travel, cfg=Config()):
    """One epoch: candidates -> MILP -> canonical optimum -> plan with predicted pickups and pending information."""
    t0 = _time.perf_counter()
    req = {x.rid: x for x in obs.open}
    cands, allowed = candidates(obs, travel, cfg)
    t_cand = _time.perf_counter() - t0
    rids = [x.rid for x in obs.open]
    vids = [v.vid for v in obs.vans]
    tn = next_tick(obs.tau, cfg.tick_s)
    phi_next = {r: req[r].q * phi_u(max(0, tn - req[r].t)) for r in rids}
    M = 1 + sum(max(c for _, c, _ in cands[v]) - min(c for _, c, _ in cands[v]) for v in vids) + sum(phi_next.values())
    pi = {r: phi_next[r] + M for r in rids}
    cols = [(v, S, c, seq) for v in vids for (S, c, seq) in cands[v]]
    res = _milp(cols, vids, rids, pi, cfg)
    if res["status"] == "infeasible":                 # impossible: the committed-only routes are always feasible
        raise RuntimeError(f"epoch {obs.tau}: MILP reported infeasible; the model is wrong, not the instance")
    status, chosen, bound = res["status"], res["chosen"], res["bound"]
    obj = None if chosen is None else _exact_obj(chosen, cols, rids, pi)
    ties = []
    if status == "optimal":
        chosen, ties, tie_status = _canonical(cols, vids, rids, pi, cfg, chosen, obj)
    else:
        tie_status = "not_checked"
    t_total = _time.perf_counter() - t0
    if chosen is None:                                    # failed solve: committed work only, logged (no fallback)
        chosen = [next(i for i, col in enumerate(cols) if col[0] == v and not col[1]) for v in vids]
    routes = {}
    for i in chosen:
        v, S, c, seq = cols[i]
        van = next(x for x in obs.vans if x.vid == v)
        ev = evaluate(van, seq, req, travel, cfg, allowed[v])
        if not (ev["feasible"] and ev["cost_u"] == c):
            raise RuntimeError(f"chosen route of {v} for {sorted(S)} fails re-evaluation: {ev.get('cost_u')} vs {c}")
        routes[v] = Route(v, S, seq, c, ev["arrivals"], ev["parts_u"])
    served = set().union(*[r.S for r in routes.values()]) if routes else set()
    pending = [r for r in rids if r not in served]
    pred = {}
    for v, rt in routes.items():
        for (kind, rid), a in zip(rt.seq, rt.arrivals):
            if kind == "P":
                pred[rid] = a
    pinfo = {r: _pending_info(r, obs, cands, routes, req, travel, cfg, allowed, status == "optimal") for r in pending}
    log = {"status": status, "objective_u": obj, "bound_u": bound, "gap_u": res["gap"], "M_u": M,
           "n_candidates": {v: len(cands[v]) for v in vids}, "n_columns": len(cols),
           "mip_nodes": res["nodes"], "tie_status": tie_status, "tied_optima": ties,
           "wall_s": {"candidates": round(t_cand, 4), "total": round(t_total, 4)},
           "next_tick_s": tn}
    return Plan(obs.tau, routes, pending, pinfo, pred, log), cands


def _milp(cols, vids, rids, pi, cfg, extra_rows=()):
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    for k, v in (("mip_rel_gap", cfg.mip_rel_gap), ("mip_abs_gap", cfg.mip_abs_gap), ("threads", cfg.threads),
                 ("random_seed", cfg.random_seed), ("mip_max_nodes", cfg.mip_max_nodes),
                 ("time_limit", cfg.time_limit_s), ("presolve", "on")):
        h.setOptionValue(k, v)
    inf = highspy.kHighsInf
    n_y, n_u = len(cols), len(rids)
    costs = [float(c) for (_, _, c, _) in cols] + [float(pi[r]) for r in rids]
    for j, c in enumerate(costs):
        h.addVar(0.0, 1.0)
        h.changeColCost(j, c)
    h.changeColsIntegrality(n_y + n_u, np.arange(n_y + n_u, dtype=np.int32),
                            np.full(n_y + n_u, highspy.HighsVarType.kInteger))
    for v in vids:                                     # one route per van
        idx = [j for j, col in enumerate(cols) if col[0] == v]
        h.addRow(1.0, 1.0, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx)))
    for i, r in enumerate(rids):                       # each open request: one route, or pending
        idx = [j for j, col in enumerate(cols) if r in col[1]] + [n_y + i]
        h.addRow(1.0, 1.0, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx)))
    for lo, hi, idx, vals in extra_rows:
        h.addRow(lo, hi, len(idx), np.array(idx, dtype=np.int32), np.array(vals, dtype=float))
    if not cols and not rids:                          # nothing to decide (no van on duty, nothing open)
        return {"status": "empty", "chosen": [], "obj": 0, "bound": 0.0, "gap": 0.0, "nodes": 0}
    if h.run() == highspy.HighsStatus.kError:
        raise RuntimeError("HiGHS returned an error; the run stops rather than guessing a plan")
    ms = h.getModelStatus()
    if ms == highspy.HighsModelStatus.kTimeLimit:
        raise RuntimeError("HiGHS stopped on the wall-clock safety limit; refusing a machine-dependent plan (D-46)")
    info = h.getInfo()
    has_sol = info.primal_solution_status == 2
    if ms == highspy.HighsModelStatus.kOptimal:
        status = "optimal"
    elif ms == highspy.HighsModelStatus.kInfeasible:
        status = "infeasible"
    elif has_sol:
        status = "feasible_unproven"
    else:
        status = "failed"
    chosen = obj = bound = gap = None
    if has_sol and status != "infeasible":
        x = h.getSolution().col_value
        chosen = [j for j in range(n_y) if x[j] > 0.5]
        obj = int(round(info.objective_function_value))
        bound = info.mip_dual_bound
        gap = info.mip_gap
    return {"status": status, "chosen": chosen, "obj": obj, "bound": bound, "gap": gap, "nodes": info.mip_node_count}


def _exact_obj(chosen, cols, rids, pi):
    """Objective as an exact integer: chosen route costs plus pending prices (not the solver's float)."""
    served = set().union(*[cols[j][1] for j in chosen]) if chosen else set()
    return sum(cols[j][2] for j in chosen) + sum(pi[r] for r in rids if r not in served)


def _vkey(vid):
    """Van ID order for tie-breaking: numeric part first, so V2 < V10; pending ('~') sorts last."""
    if vid == "~":
        return (2, 0, "")
    digits = "".join(ch for ch in vid if ch.isdigit())
    return (0, int(digits), vid) if digits else (1, 0, vid)


def _assign_key(chosen, cols, rids):
    who = {}
    for j in chosen:
        for r in cols[j][1]:
            who[r] = cols[j][0]
    return tuple(_vkey(who.get(r, "~")) for r in rids)


def _canonical(cols, vids, rids, pi, cfg, chosen, obj):
    """Enumerate optima with equal objective (no-good cuts) and return the canonical one."""
    found, cuts = [chosen], []
    status = "unique"
    for _ in range(cfg.max_tie_solves):
        last = found[-1]
        cuts.append((-np.inf, len(last) - 1.0, last, [1.0] * len(last)))
        obj_row = (-np.inf, obj + 0.5, list(range(len(cols) + len(rids))),
                   [float(c) for (_, _, c, _) in cols] + [float(pi[r]) for r in rids])
        res = _milp(cols, vids, rids, pi, cfg, extra_rows=cuts + [obj_row])
        if res["status"] == "feasible_unproven":
            status = "tie_enumeration_incomplete"
            break
        if res["status"] != "optimal" or _exact_obj(res["chosen"], cols, rids, pi) != obj:
            break
        found.append(res["chosen"])
        status = "tie"
    else:
        status = "tie_enumeration_truncated"
    keys = [(_assign_key(c, cols, rids), c) for c in found]
    keys.sort()
    readable = [[k[2] if k[0] < 2 else "~" for k in key] for key, _ in keys]
    return keys[0][1], readable if len(keys) > 1 else [], status


def _pending_info(r, obs, cands, routes, req, travel, cfg, allowed, proven=True):
    """Facts about why r is pending, and its tentative ETA (cheapest feasible insertion, outside the MILP).
    "the chosen subset plus this request is not a feasible candidate" is established only for a proven optimum
    (otherwise swapping to S + r would leave fewer requests pending, contradicting the M bound). The tentative
    ETA is optimistic: it ignores the cap and other pending requests."""
    per_van = {}
    for v in [x.vid for x in obs.vans]:
        in_any = any(r in S for S, _, _ in cands[v])
        S = routes[v].S
        if not in_any:
            per_van[v] = "no feasible candidate contains it (single insertion infeasible)"
        elif len(S) >= cfg.K:
            per_van[v] = f"chosen route already has K={cfg.K} new pickups (cap)"
        elif proven:
            per_van[v] = "the chosen subset plus this request is not a feasible candidate"
        else:
            per_van[v] = "not established (solve not proven optimal)"
    reason = ("no_feasible_candidate" if all(s.startswith("no feasible") for s in per_van.values())
              else "not_selected")
    best = None
    x = req[r]
    for v, rt in routes.items():
        van = next(z for z in obs.vans if z.vid == v)
        seq = list(rt.seq)
        sub = {k: req[k] for k in rt.S | {r}}
        for i in range(len(seq) + 1):
            for j in range(i, len(seq) + 1):
                s2 = seq[:i] + [("P", r)] + seq[i:j] + [("D", r)] + seq[j:]
                ev = evaluate(van, tuple(s2), sub, travel, cfg, allowed[v])
                if ev["feasible"]:
                    d = ev["cost_u"] - rt.cost_u
                    eta = ev["arrivals"][i]
                    if best is None or (d, v, i, j) < best[0]:
                        best = ((d, v, i, j), eta, v)
    return {"reason": reason, "per_van": per_van,
            "tentative_eta_s": None if best is None else best[1], "tentative_van": None if best is None else best[2]}
