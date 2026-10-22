"""Independent reference computations for the src/sim checks (tests/test_sim_independent.py).

Nothing here calls the dispatcher's own route logic (best_routes, _insert, _milp, _canonical, evaluate, phi_u,
guardrail_s). Every quantity is recomputed from the documented rules (model_design v0.2 §3-§5, scenario_spec §17,
decision log D-52), straight from the frozen CSV files:

    travel per leg = round(t0 x m) (Python round), 30-s dwell after every curb arrival,
    pickup = curb arrival, ride H = drop arrival - pickup arrival, wait W = pickup arrival - request time,
    cost (points) = sum q*phi(W) [route pickups + a committed pickup the van is driving to]
                  + 0.5 * sum q*H/60 [riders dropped in the route, incl. riders already aboard]
                  + 0.1 * km [matrix metres / 1000, summed over legs]
                  + 1000 * sum q*(H - G)+/60 [only where the guardrail rule allows a violation],
    phi piecewise linear in minutes, slopes 1, 2.5, 5, 10, 20, breaks 5, 10, 15, 20;
    guardrail G = max(25 min, 2 * van direct time + 5 min); capacity from availability.csv.

Exact arithmetic: costs are kept as integers in REF units, REF = 600,000 per point (the least common multiple of the
denominators: 1/120 point per passenger-second of phi or riding, 1/100,000 point per decimetre). The implementation
uses 1,200,000 units per point; comparisons go through fractions.Fraction, so no tolerance is needed.
"""
import csv
import itertools
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCEN = ROOT / "data" / "scenarios" / "v2"
MATRIX = ROOT / "data" / "processed" / "tt_locations_v2.csv"

REF = 600_000                     # reference cost units per point
IMPL_UNITS_PER_POINT = 1_200_000  # stated in the task / dispatch docstring; used only to convert
DWELL = 30
CAPACITY_DEFAULT = 14
G_ABS, G_ALPHA, G_DELTA = 25 * 60, 2, 5 * 60
TICK = 120
LYFT_STATES = {"xfer_hold", "lyft_booked", "lyft_onboard", "lyft_completed", "noshow_lyft", "cancel_after_transfer",
               "lyft_failed"}
TERMINAL = {"van_completed", "noshow_van", "cancel_pending_van", "lyft_completed", "noshow_lyft",
            "cancel_after_transfer", "lyft_failed"}                      # scenario_spec §17.2
ALLOWED_TRANSITIONS = {                                                  # scenario_spec §17.2 (+ lyft_onboard step)
    "unrevealed": {"pending_van"},
    "pending_van": {"committed", "cancel_pending_van", "xfer_hold"},
    "committed": {"onboard", "noshow_van", "cancel_pending_van"},
    "onboard": {"van_completed"},
    "xfer_hold": {"lyft_booked", "cancel_after_transfer"},
    "lyft_booked": {"lyft_onboard", "noshow_lyft", "cancel_after_transfer", "lyft_failed"},
    "lyft_onboard": {"lyft_completed"},
}


def to_points(units, per_point):
    return Fraction(units, per_point)


# ---------- raw inputs, read with the csv module ----------
_MATRIX = None


def matrix():
    """{(o, d): (seconds as float, decimetres as int)} from the raw matrix file."""
    global _MATRIX
    if _MATRIX is None:
        out = {}
        with open(MATRIX, newline="") as f:
            for row in csv.DictReader(f):
                out[(row["origin"], row["dest"])] = (float(row["seconds"]), int(round(float(row["meters"]) * 10)))
        _MATRIX = out
    return _MATRIX


def read_csv(level, name):
    with open(SCEN / level / name, newline="") as f:
        return list(csv.DictReader(f))


class Ref:
    """Reference rules for one scenario (multiplier m, requests, capacities)."""

    def __init__(self, level, m):
        self.m = m
        self.mx = matrix()
        self.req = {r["request_id"]: dict(t=int(r["t_request_s"]), o=r["o_loc"], d=r["d_loc"], q=int(r["party"]))
                    for r in read_csv(level, "requests.csv")}
        self.cap = {v["van_id"]: int(v["capacity"]) for v in read_csv(level, "availability.csv")}

    def vt(self, a, b):
        return int(round(self.mx[(a, b)][0] * self.m))

    def t0(self, a, b):
        return self.mx[(a, b)][0]

    def dm(self, a, b):
        return self.mx[(a, b)][1]

    def G(self, rid):
        r = self.req[rid]
        return max(G_ABS, G_ALPHA * self.vt(r["o"], r["d"]) + G_DELTA)


def phi_ref(wait_s):
    """phi for one passenger in REF units (exact). Slopes per minute 1, 2.5, 5, 10, 20 -> per second x REF/60."""
    w = max(0, wait_s)
    out = 0
    for lo, hi, slope_per_min_x2 in ((0, 300, 2), (300, 600, 5), (600, 900, 10), (900, 1200, 20), (1200, None, 40)):
        if w > lo:
            seg = (w if hi is None else min(w, hi)) - lo
            out += slope_per_min_x2 * seg * (REF // 120)      # (slope/2)/60 point per second = slope_x2*REF/120
    return out


def phi_minutes(wait_min):
    """phi in points as an exact Fraction, written directly from the minute breakpoints (for cross-checking)."""
    w = max(Fraction(0), Fraction(wait_min))
    pts = Fraction(0)
    for lo, hi, s in ((0, 5, Fraction(1)), (5, 10, Fraction(5, 2)), (10, 15, Fraction(5)), (15, 20, Fraction(10)),
                      (20, None, Fraction(20))):
        top = w if hi is None else min(w, Fraction(hi))
        pts += s * max(Fraction(0), top - lo)
    return pts


RIDE_REF = REF // 120          # 0.5 point per passenger-minute = 1/120 point per passenger-second
KM_REF = 6                     # 0.1 point per km = 1/100,000 point per decimetre -> 6 REF units
PSI_REF = 1000 * REF // 60     # 1000 points per passenger-minute over the guardrail


# ---------- a van's starting state, read from the Observation ----------
class VanCtx:
    """Starting state of one van. Riders: rid -> pickup time (actual, or planned for a committed pickup)."""

    def __init__(self, ref, obs_tau, van):
        self.vid = van.vid
        self.loc = van.loc
        self.free = van.free_s
        self.cap = ref.cap[van.vid]
        assert van.capacity == self.cap
        self.riders = {r.rid: r.pickup_s for r in van.riders}
        for r in van.riders:                                  # the observation must agree with the raw files
            x = ref.req[r.rid]
            assert (r.d, r.q, r.t) == (x["d"], x["q"], x["t"]), r
            assert r.direct_van_s == ref.vt(x["o"], x["d"]), r
        # a committed pickup the van is still driving to: its wait is part of every route of this van
        self.committed_wait = 0
        c = van.committed
        if c and c[1] == "P" and c[2] > obs_tau and c[0] in self.riders:
            assert self.riders[c[0]] == c[2]
            x = ref.req[c[0]]
            self.committed_wait = x["q"] * phi_ref(c[2] - x["t"])


def evaluate(ref, ctx, seq, new, limits):
    """My route evaluator. seq: ((kind, rid), ...). new: set of new request ids (H <= G required).
    limits: rid -> max ride for existing riders, or None (committed-only route: exempt).
    Returns (feasible, cost_ref, arrivals, rides)."""
    t, loc = ctx.free, ctx.loc
    load = sum(ref.req[r]["q"] for r in ctx.riders)
    pick = dict(ctx.riders)
    cost = ctx.committed_wait
    onboard = set(ctx.riders)
    arrivals, rides, ok = [], {}, load <= ctx.cap
    picked_new = set()
    for kind, rid in seq:
        x = ref.req[rid]
        if kind == "P":
            if rid not in new or rid in picked_new:
                return False, None, None, None
            dest = x["o"]
        else:
            if rid not in onboard:
                return False, None, None, None
            dest = x["d"]
        cost += KM_REF * ref.dm(loc, dest)
        a = t + ref.vt(loc, dest)
        if kind == "P":
            picked_new.add(rid)
            onboard.add(rid)
            pick[rid] = a
            load += x["q"]
            ok &= load <= ctx.cap
            cost += x["q"] * phi_ref(a - x["t"])
        else:
            onboard.discard(rid)
            load -= x["q"]
            h = a - pick[rid]
            rides[rid] = h
            g = ref.G(rid)
            lim = g if rid in new else (None if limits is None else limits[rid])
            if lim is not None and h > lim:
                ok = False
            cost += RIDE_REF * x["q"] * h + PSI_REF * x["q"] * max(0, h - g)
        arrivals.append(a)
        loc, t = dest, a + DWELL
    ok &= not onboard and picked_new == set(new)
    return bool(ok), cost, tuple(arrivals), rides


def committed_only_best(ref, ctx):
    """Brute force over every drop order of the van's existing riders (no guardrail: the route is exempt).
    Returns (cost, seq, rides) with the lexicographically smallest seq among the cheapest."""
    best = None
    n = 0
    for perm in itertools.permutations(sorted(ctx.riders)):
        seq = tuple(("D", r) for r in perm)
        ok, c, _, rides = evaluate(ref, ctx, seq, set(), None)
        n += 1
        assert ok
        if best is None or (c, seq) < best[:2]:
            best = (c, seq, rides)
    return best, n


def limits_for(ref, ctx, co_rides):
    """Guardrail rule for existing riders: H <= max(G, H in the committed-only route)."""
    return {r: max(ref.G(r), co_rides[r]) for r in ctx.riders}


def brute_force_subset(ref, ctx, S, base_order, limits):
    """Every precedence-feasible order of S's pickups/drops together with the existing riders' drops.
    base_order=None (default dispatcher setting): the existing riders' drops are ordered freely as well.
    base_order=[...] (fix_existing_drop_order=True): they keep that order, new stops are interleaved freely.
    Enumerated exhaustively by DFS; the only pruning is infeasibility (capacity overflow, a guardrail breach), which
    no extension can repair. Returns (min (cost, seq) or None, number of complete orders seen)."""
    S = sorted(S)
    q = {r: ref.req[r]["q"] for r in S}
    best = [None]
    count = [0]
    G = {r: ref.G(r) for r in S}

    old = sorted(ctx.riders)
    n_old = len(old)

    def dfs(t, loc, load, cost, pick, dropped, bi, seq):
        done_new = len(dropped) == len(S)
        if done_new and len(old_done) == n_old and len(pick) == len(S):
            count[0] += 1
            key = (cost, tuple(seq))
            if best[0] is None or key < best[0]:
                best[0] = key
            return
        for r in S:                                            # a new pickup
            if r in pick or load + q[r] > ctx.cap:
                continue
            x = ref.req[r]
            a = t + ref.vt(loc, x["o"])
            pick[r] = a
            seq.append(("P", r))
            dfs(a + DWELL, x["o"], load + q[r], cost + KM_REF * ref.dm(loc, x["o"]) + q[r] * phi_ref(a - x["t"]),
                pick, dropped, bi, seq)
            seq.pop()
            del pick[r]
        for r in S:                                            # a new drop
            if r not in pick or r in dropped:
                continue
            x = ref.req[r]
            a = t + ref.vt(loc, x["d"])
            h = a - pick[r]
            if h > G[r]:
                continue
            dropped.add(r)
            seq.append(("D", r))
            dfs(a + DWELL, x["d"], load - q[r], cost + KM_REF * ref.dm(loc, x["d"]) + RIDE_REF * q[r] * h,
                pick, dropped, bi, seq)
            seq.pop()
            dropped.discard(r)
        if base_order is None:                                 # any existing rider not yet dropped
            nxt = [r for r in old if r not in old_done]
        else:                                                  # only the next one in base_order
            nxt = [base_order[bi]] if bi < len(base_order) else []
        for r in nxt:
            x = ref.req[r]
            a = t + ref.vt(loc, x["d"])
            h = a - ctx.riders[r]
            if limits is not None and h > limits[r]:
                continue
            g = ref.G(r)
            seq.append(("D", r))
            old_done.add(r)
            dfs(a + DWELL, x["d"], load - x["q"],
                cost + KM_REF * ref.dm(loc, x["d"]) + RIDE_REF * x["q"] * h + PSI_REF * x["q"] * max(0, h - g),
                pick, dropped, bi + 1, seq)
            old_done.discard(r)
            seq.pop()

    if base_order is not None:
        assert sorted(base_order) == old
    old_done = set()
    load0 = sum(ref.req[r]["q"] for r in ctx.riders)
    if load0 <= ctx.cap:
        dfs(ctx.free, ctx.loc, load0, ctx.committed_wait, {}, set(), 0, [])
    return best[0], count[0]


# ---------- route selection over a given candidate set ----------
def next_tick(tau):
    return (tau // TICK + 1) * TICK


def enumerate_combinations(cands_by_van, open_rids):
    """All selections of one candidate per van with no request in two routes.
    cands_by_van: [(vid, [(S frozenset, cost), ...]), ...]. Yields tuples of chosen indices."""
    vids = [v for v, _ in cands_by_van]

    def rec(i, used, chosen):
        if i == len(vids):
            yield tuple(chosen)
            return
        for k, (S, _) in enumerate(cands_by_van[i][1]):
            if used.isdisjoint(S):
                chosen.append(k)
                yield from rec(i + 1, used | S, chosen)
                chosen.pop()

    yield from rec(0, frozenset(), [])


def canonical_key(assign, open_rids):
    """Requests in ID order; assigned van ID compared lexicographically; pending sorts last."""
    return tuple((0, assign[r]) if r in assign else (1, "") for r in sorted(open_rids))


# ---------- event-log replay ----------
def state_events(events):
    return [e for e in events if e["event"] == "state"]


def per_request_states(events):
    out = {}
    for e in state_events(events):
        out.setdefault(e["request"], []).append(e)
    return out


def first(events, pred):
    for e in events:
        if pred(e):
            return e
    return None
