"""Dispatcher G: greedy insertion, never reassign (model_design v0.6 §6.1; decision D-60, M5b).

G is the floor against which C (the restricted route-selection MILP, dispatch.py) is benchmarked. It receives the same
Observation as C, returns the same Plan object, and scores everything with C's own route evaluator
(dispatch.evaluate: the D-29 cost, capacity, the guardrail rule), so the one designed difference is the algorithm:

1. Keep. Each van keeps the stop sequence G gave it earlier. At each epoch the sequence is reconciled with the
   observation: stops of requests that were picked up, cancelled, transferred or found absent are removed (the engine
   already removed the stop a van departed for). Assigned requests are never moved to another van and never reordered.
2. Repair (only to keep the plan legal). Vans run late after no-shows and dwell, so a kept sequence can drift past
   the guardrail of a request not yet picked up; the engine's plan audit would (rightly) reject that plan. G then
   releases the assigned request with the largest planned excess and repeats until the kept sequence is feasible.
   A released request is treated as new in step 3. Every release is logged; it is the only exception to "never
   reassign".
3. Insert. Each unassigned open request, in arrival order (request time, then ID), goes to the van and the pair of
   positions (pickup at i, drop-off at j >= i in the van's current sequence) with the smallest increase in that van's
   route cost, subject to feasibility: capacity; the guardrail for every rider G picks up in the route; riders already
   aboard may not end above max(guardrail, their ride in the van's route before the insertion). Ties: lower van ID
   (V2 < V10), then earlier i, then earlier j. A request with no feasible insertion stays pending and is retried at
   every later epoch.

Designed differences from C, stated so they are not mistaken for bias (independent review, 10 Nov):
- Riders already aboard: an insertion may not push them above max(guardrail, their ride in the van's current G route).
  C's reference is the committed-only route. Both apply the same principle ("a plan may not create or increase a
  violation" relative to the plan the dispatcher is bound to); G is bound to its own earlier plan because it never
  reorders. Using C's reference would make every insertion on a van infeasible once G's own plan exceeded it.
- Repair checks only riders not yet picked up; an aboard rider's ride can stay above the guardrail in a kept plan,
  is charged Psi in the cost, and is not released (G cannot reorder to fix it).
- No K cap: G may hold any number of assigned pickups per van; K = 3 is part of C's restricted candidate set.

What G is not: it has no reassignment, no reordering of assigned stops, and no look-ahead. It is not TransLoc's
dispatcher and not heuristic T (which re-optimizes all open work). A pending request gets no tentative ETA
(the Lyft rules read None = infinite), so G is used with R0 and the time-based R1(θ) only (D-60).
"""
import time as _time

from . import dispatch as D


class Greedy:
    """Stateful per run: create one instance per Engine."""

    def __init__(self, travel, cfg):
        self.travel, self.cfg = travel, cfg
        self.route = {}          # vid -> [(kind, rid), ...] after the van's committed stop
        self.owner = {}          # rid -> vid, for assigned requests not yet picked up
        self._snap = None        # (tau, route, owner) before the first solve at tau (see solve)
        self._discarded = []     # logs of same-tau plans that were replaced before execution

    # ---------- step 1: reconcile ----------
    def _reconcile(self, obs, req):
        missing_drops = []
        for v in obs.vans:
            riders = {r.rid for r in v.riders}
            keep = []
            for kind, rid in self.route.get(v.vid, []):
                mine = rid in req and self.owner.get(rid) == v.vid
                if (kind == "P" and mine) or (kind == "D" and (rid in riders or mine)):
                    keep.append((kind, rid))
            have = {rid for kind, rid in keep if kind == "D"}
            for rid in sorted(riders - have):            # cannot happen by construction; logged if it does
                keep.append(("D", rid))
                missing_drops.append(rid)
            self.route[v.vid] = keep
        vids = {v.vid for v in obs.vans}
        self.owner = {r: v for r, v in self.owner.items() if r in req and v in vids and ("P", r) in self.route[v]}
        return missing_drops

    def _assigned(self, vid, req):
        return {rid: req[rid] for kind, rid in self.route[vid] if kind == "P"}

    # ---------- step 2: repair ----------
    def _repair(self, van, req):
        released = []
        while True:
            seq = self.route[van.vid]
            asg = self._assigned(van.vid, req)
            ev = D.evaluate(van, seq, asg, self.travel, self.cfg, None)
            if ev["feasible"]:
                return released, ev
            excess = {rid: ev["rides"].get(rid, 0) - D.guardrail_s(self.travel.van(x.o, x.d), self.cfg)
                      for rid, x in asg.items()}
            if not excess:
                raise RuntimeError(f"{van.vid}: kept sequence infeasible with no released-able request")
            worst = max(sorted(excess), key=lambda r: excess[r])
            self.route[van.vid] = [s for s in seq if s[1] != worst]
            del self.owner[worst]
            released.append(worst)

    # ---------- step 3: insert ----------
    def _insert(self, x, vans, req, base):
        best = None
        for v in sorted(vans, key=lambda v: D._vkey(v.vid)):
            seq = self.route[v.vid]
            ev0 = base[v.vid]
            allowed = {r.rid: max(D.guardrail_s(r.direct_van_s, self.cfg), ev0["rides"][r.rid]) for r in v.riders}
            asg = self._assigned(v.vid, req)
            asg[x.rid] = x
            n = len(seq)
            for i in range(n + 1):
                for j in range(i, n + 1):
                    new = seq[:i] + [("P", x.rid)] + seq[i:j] + [("D", x.rid)] + seq[j:]
                    ev = D.evaluate(v, new, asg, self.travel, self.cfg, allowed)
                    if not ev["feasible"]:
                        continue
                    key = (ev["cost_u"] - ev0["cost_u"], D._vkey(v.vid), i, j)
                    if best is None or key < best[0]:
                        best = (key, v.vid, new, ev)
        return best

    # ---------- the epoch ----------
    def solve(self, obs):
        t0 = _time.perf_counter()
        # Same-epoch re-solve (the engine re-solves once after Lyft transfers, engine._epoch). The first plan at this
        # tau was never executed, so G restarts from its state before that plan, exactly as C re-solves from scratch.
        # Without this, stops placed around a just-transferred request would stay (independent review, 10 Nov).
        if self._snap is not None and self._snap[0] == obs.tau:
            self.route = {v: list(s) for v, s in self._snap[1].items()}
            self.owner = dict(self._snap[2])
        else:
            self._snap = (obs.tau, {v: list(s) for v, s in self.route.items()}, dict(self.owner))
            self._discarded = []
        req = {x.rid: x for x in obs.open}
        missing = self._reconcile(obs, req)
        released, base = [], {}
        for v in obs.vans:
            rel, ev = self._repair(v, req)
            released += rel
            base[v.vid] = ev
        inserted, n_tried = [], 0
        for x in sorted((x for x in obs.open if x.rid not in self.owner), key=lambda x: (x.t, x.rid)):
            n_tried += 1
            best = self._insert(x, obs.vans, req, base)
            if best is None:
                continue
            key, vid, new, ev = best
            self.route[vid], self.owner[x.rid] = new, vid
            base[vid] = ev
            inserted.append({"rid": x.rid, "van": vid, "delta_u": key[0], "pos": [key[2], key[3]]})
        routes, pred = {}, {}
        for v in obs.vans:
            seq = tuple(self.route[v.vid])
            ev = base[v.vid]
            S = frozenset(rid for kind, rid in seq if kind == "P")
            routes[v.vid] = D.Route(v.vid, S, seq, ev["cost_u"], ev["arrivals"], ev["parts_u"])
            for (kind, rid), a in zip(seq, ev["arrivals"]):
                if kind == "P":
                    pred[rid] = a
        pending = [x.rid for x in obs.open if x.rid not in self.owner]
        pinfo = {r: {"reason": "no feasible insertion on any van", "tentative_eta_s": None} for r in pending}
        wall = round(_time.perf_counter() - t0, 4)
        status = "empty" if not obs.vans and not obs.open else "greedy"     # as C: nothing to decide
        log = {"status": status, "algorithm": "G", "objective_u": sum(r.cost_u for r in routes.values()),
               "bound_u": None, "gap_u": None, "tie_status": "not_applicable", "pending_price": None,
               "n_tried": n_tried, "inserted": inserted, "released_for_repair": released,
               "missing_drop_repaired": missing, "replaced_same_epoch": list(self._discarded),
               "wall_s": {"total": wall}}
        self._discarded.append({k: log[k] for k in ("inserted", "released_for_repair")})
        cands = {vid: [(rt.S, rt.cost_u, rt.seq)] for vid, rt in routes.items()}
        return D.Plan(obs.tau, routes, pending, pinfo, pred, log), cands
