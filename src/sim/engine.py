"""Event engine (referee) for M0-M1. Build contract: scenario_spec.md v0.5 §17.

The engine owns the clock, the same-second event order, every state and the hidden rider traits. The dispatcher
only ever receives a dispatch.Observation; hidden traits are applied here, when their event happens.

Same-second order (§17.3): 10 drop-offs, 20 curb arrivals (end the patience clock; presence test), 30 service ends
(boarding/drop dwell, no-show expiry), 40 van on/off duty, 50 new requests, 60 patience checks, 70 Lyft bookings,
80 epoch (solve -> Lyft rule -> re-solve once if any transfer), 90 departures (commitment). Ties inside a class:
request ID, then van ID. One epoch per distinct second with a trigger.

Conventions made explicit here (recorded in D-52):
- A van is re-routable only at a stop: a van driving to a stop always completes that leg (commitment = departure).
  If its pickup cancels meanwhile, it arrives, finds no rider and is free at once (no dwell).
- Every stop has a 30-s dwell after curb arrival. Pickup time = curb arrival; drop-off time = arrival at the
  destination. A no-show is recorded 180 s after curb arrival; the van then leaves without dwell.
- Epoch triggers: new request, cancellation or no-show of a request in van planning, van on/off duty, the tick.
  Lyft-side events do not trigger an epoch (they cannot change a van plan).
- A leg of 0 s (consecutive stops at the same point) is processed in the same second, after that second's
  departures.
"""
import heapq
import math
from dataclasses import dataclass, field

from . import dispatch as D
from . import lyft as L

C_DROP, C_ARRIVE, C_SERVICE, C_DUTY, C_REQUEST, C_PATIENCE, C_BOOK, C_EPOCH, C_DEPART = 10, 20, 30, 40, 50, 60, 70, 80, 90
TERMINAL = {"van_completed", "lyft_completed", "cancel_pending_van", "cancel_after_transfer", "noshow_van",
            "noshow_lyft", "lyft_failed"}


@dataclass
class Policy:
    rule: str = "R0"
    lag_s: int = 120
    consent_p: float = 1.0
    p_absent: float = 0.089          # PROVISIONAL (D-48); L1-L4 outcomes are identical for any 0 < p <= 0.99
    rule_active_before_s: float = math.inf   # M0 harness: rules act only before this time (L4: 900)
    # Planning view of an absent rider's 180-s curb wait (D-54). "possible_boarding": the pickup stays committed and
    # the planner assumes the rider may board when the timer expires (dwell, seat and drop-off obligation kept) until
    # the no-show actually expires. "noshow_certain": the M1 view (planner treats the no-show as already certain).
    # Planning only: the simulator never boards an absent rider.
    curb_wait_planning: str = "possible_boarding"
    dispatcher: D.Config = field(default_factory=D.Config)


@dataclass
class ReqState:
    state: str = "unrevealed"
    van: str = None
    committed_s: int = None
    curb_arrival_s: int = None       # first vehicle arrival at the curb (van or Lyft)
    pickup_s: int = None             # boarding = curb arrival when present
    drop_s: int = None
    cancel_s: int = None
    noshow_s: int = None
    transfer_s: int = None
    booking_s: int = None
    lyft_class: str = None
    declined_s: int = None
    unassigned_since: int = None


@dataclass
class VanRun:
    vid: str
    capacity: int
    loc: str
    on_duty: bool = False
    status: str = "off"              # off / idle / moving / service
    current: tuple = ()              # (kind, rid, arrive_s) while moving or serving
    service_end_s: int = None
    absent_wait: bool = False
    onboard: dict = field(default_factory=dict)   # rid -> pickup_s
    plan: list = field(default_factory=list)      # stops after the current one: [(kind, rid)]


class Engine:
    def __init__(self, scen, travel, policy=Policy()):
        self.scen, self.travel, self.pol = scen, travel, policy
        self.req = {r.rid: r for r in scen.requests}
        self._hidden = scen.hidden                         # private: never passed to the dispatcher
        self.rs = {r.rid: ReqState() for r in scen.requests}
        self.vans = {v.vid: VanRun(v.vid, v.capacity, v.start_loc) for v in sorted(scen.vans, key=lambda v: v.vid)}
        self.heap, self._seq = [], 0
        self.events, self.epochs = [], []
        self.observations = []                             # in memory only (for the narrative); not written
        self.now, self.cls = None, None
        for r in scen.requests:
            self._push(r.t, C_REQUEST, "request", r.rid)
            self._push(r.t + self._hidden[r.rid].patience_s, C_PATIENCE, "patience", r.rid)
        for v in scen.vans:
            self._push(v.avail_start_s, C_DUTY, "on_duty", v.vid)
            self._push(v.avail_end_s, C_DUTY, "off_duty", v.vid)

    # ---------- bookkeeping ----------
    def _push(self, t, cls, kind, key, data=None):
        heapq.heappush(self.heap, (t, cls, key, self._seq, kind, data))
        self._seq += 1

    def _log(self, event, rid=None, vid=None, **kw):
        row = {"t_s": self.now, "class": self.cls, "event": event, "request": rid, "van": vid}
        row.update(kw)
        self.events.append(row)

    def _set(self, rid, new, **kw):
        old = self.rs[rid].state
        self.rs[rid].state = new
        self._log("state", rid, kw.pop("vid", None), state_from=old, state_to=new, **kw)

    def done(self):
        return all(s.state in TERMINAL for s in self.rs.values()) and all(
            v.status in ("idle", "off") for v in self.vans.values())

    # ---------- main loop ----------
    def run(self, max_s=10 * 3600):
        tick = self.pol.dispatcher.tick_s
        next_tick = 0
        while not self.done():
            t_ev = self.heap[0][0] if self.heap else math.inf
            s = min(t_ev, next_tick)
            if s > max_s:
                raise RuntimeError("run did not finish (unresolved requests)")
            self.now, trigger = s, set()
            while self.heap and self.heap[0][0] == s and self.heap[0][1] < C_EPOCH:
                t, cls, key, _, kind, data = heapq.heappop(self.heap)
                self.cls = cls
                trig = getattr(self, "_on_" + kind)(key, data)
                if trig:
                    trigger.add(trig)
            if s == next_tick:
                trigger.add("tick")
                next_tick += tick
            if trigger and not self.done():
                self.cls = C_EPOCH
                self._epoch(sorted(trigger))
            if all(st.state in TERMINAL for st in self.rs.values()):
                for v in self.vans.values():               # nothing left to serve: plans (e.g. a possible-boarding
                    v.plan = []                            # drop-off after a final no-show) are void
            self.cls = C_DEPART
            self._departures()
            while self.heap and self.heap[0][0] == s:      # 0-s legs started by this second's departures
                while self.heap and self.heap[0][0] == s:
                    t, cls, key, _, kind, data = heapq.heappop(self.heap)
                    self.cls = cls
                    getattr(self, "_on_" + kind)(key, data)
                self.cls = C_DEPART
                self._departures()
        self.end_s = self.now
        return self

    # ---------- event handlers (return a trigger name or None) ----------
    def _on_request(self, rid, _):
        self._set(rid, "pending_van")
        self.rs[rid].unassigned_since = self.now
        return "request"

    def _on_on_duty(self, vid, _):
        v = self.vans[vid]
        v.on_duty, v.status = True, "idle"
        self._log("on_duty", vid=vid, loc=v.loc)
        return "van_on_duty"

    def _on_off_duty(self, vid, _):
        busy = not all(s.state in TERMINAL for s in self.rs.values())
        self._log("off_duty_deferred" if busy else "off_duty_time", vid=vid,
                  note="closing rule: stays on duty until all accepted work is resolved" if busy else "")
        return None

    def _on_patience(self, rid, _):
        st = self.rs[rid]
        if st.curb_arrival_s is not None or st.state in TERMINAL:
            return None                                   # a vehicle arrival ended the clock
        if st.state in ("pending_van", "committed"):
            st.cancel_s = self.now
            self._set(rid, "cancel_pending_van", vid=st.van)
            return "cancellation"
        if st.state in ("xfer_hold", "lyft_booked"):
            st.cancel_s = self.now
            self._set(rid, "cancel_after_transfer", booked=st.state == "lyft_booked")
            return None
        return None

    def _on_arrive(self, vid, data):
        kind, rid = data
        v = self.vans[vid]
        v.status = "service"
        st, r = self.rs[rid], self.req[rid]
        if kind == "D":
            st.drop_s = self.now
            del v.onboard[rid]
            self._set(rid, "van_completed", vid=vid, ride_s=self.now - st.pickup_s)
            self._end_service(vid, self.now + D.DWELL_S, "drop_dwell")
            return None
        if st.state == "cancel_pending_van":
            self._log("arrive_no_rider", rid, vid, note="request cancelled while the van was driving")
            self._end_service(vid, self.now, "cancelled_pickup")
            return None
        st.curb_arrival_s = self.now
        if self._hidden[rid].noshow_u < self.pol.p_absent:
            self._log("curb_arrival", rid, vid, present=False)
            v.absent_wait = True
            self._end_service(vid, self.now + 180, "noshow_expiry", rid)
        else:
            st.pickup_s = self.now
            v.onboard[rid] = self.now
            if sum(self.req[x].q for x in v.onboard) > v.capacity:
                raise RuntimeError(f"{vid}: capacity exceeded at {self.now}")
            self._set(rid, "onboard", vid=vid, wait_s=self.now - r.t)
            self._end_service(vid, self.now + D.DWELL_S, "board_dwell")
        return None

    def _end_service(self, vid, t, why, rid=None):
        self.vans[vid].service_end_s = t
        self._push(t, C_SERVICE, "service_end", vid, (why, rid))

    def _on_service_end(self, vid, data):
        why, rid = data
        v = self.vans[vid]
        v.status, v.current, v.absent_wait = "idle", (), False
        if why == "noshow_expiry":
            self.rs[rid].noshow_s = self.now
            self._set(rid, "noshow_van", vid=vid)
            return "noshow"
        self._log("service_end", vid=vid, note=why)
        return None

    def _on_book(self, rid, _):
        st = self.rs[rid]
        if st.state != "xfer_hold":
            return None
        st.booking_s = self.now
        self._set(rid, "lyft_booked", lyft_class=st.lyft_class)
        self._push(self.now + self._hidden[rid].lyft_delay_s, C_ARRIVE, "lyft_arrive", rid)
        return None

    def _on_lyft_arrive(self, rid, _):
        st, r = self.rs[rid], self.req[rid]
        if st.state != "lyft_booked":
            self._log("lyft_arrive_no_rider", rid, note=st.state)
            return None
        st.curb_arrival_s = self.now
        if self._hidden[rid].noshow_u < self.pol.p_absent:
            self._log("lyft_curb_arrival", rid, present=False)
            self._push(self.now + 180, C_SERVICE, "lyft_noshow", rid)
            return None
        st.pickup_s = self.now
        self._set(rid, "lyft_onboard", wait_s=self.now - r.t)
        self._push(self.now + D.DWELL_S + self.travel.lyft(r.o, r.d), C_DROP, "lyft_drop", rid)
        return None

    def _on_lyft_noshow(self, rid, _):
        self.rs[rid].noshow_s = self.now
        self._set(rid, "noshow_lyft")
        return None

    def _on_lyft_drop(self, rid, _):
        st = self.rs[rid]
        st.drop_s = self.now
        self._set(rid, "lyft_completed", ride_s=self.now - st.pickup_s)
        return None

    # ---------- the observable state ----------
    def observation(self):
        tau, vans = self.now, []
        for vid, v in self.vans.items():
            if not v.on_duty:
                continue
            riders = [self._rider(x, p) for x, p in sorted(v.onboard.items())]
            loc, free, committed, cwait = v.loc, tau, (), 0
            if v.status == "moving":
                kind, rid, arr = v.current
                r = self.req[rid]
                committed = (rid, kind, arr)
                if kind == "D":
                    riders = [x for x in riders if x.rid != rid]
                    loc, free = r.d, arr + D.DWELL_S
                elif self.rs[rid].state == "cancel_pending_van":
                    loc, free = r.o, arr
                else:
                    riders = sorted(riders + [self._rider(rid, arr)], key=lambda x: x.rid)
                    loc, free, cwait = r.o, arr + D.DWELL_S, r.q * D.phi_u(arr - r.t)
            elif v.status == "service":
                free = v.service_end_s
                committed = (v.current[1], v.current[0], v.current[2]) if v.current else ()
                if v.absent_wait and self.pol.curb_wait_planning == "possible_boarding":
                    rid = v.current[1]                     # timer running: not present yet, not yet a no-show
                    r, expiry = self.req[rid], v.service_end_s
                    riders = sorted(riders + [self._rider(rid, expiry)], key=lambda x: x.rid)
                    free, cwait = expiry + D.DWELL_S, r.q * D.phi_u(expiry - r.t)
                    committed = (rid, "P_curb_wait", v.current[2])
                elif self.pol.curb_wait_planning not in ("possible_boarding", "noshow_certain"):
                    raise ValueError(self.pol.curb_wait_planning)
            vans.append(D.VanState(vid, v.capacity, loc, free, tuple(riders), committed, cwait))
        open_ = tuple(D.OpenRequest(r.rid, r.t, r.o, r.d, r.q) for r in sorted(self.req.values(), key=lambda r: r.rid)
                      if self.rs[r.rid].state == "pending_van")
        return D.Observation(tau, tuple(vans), open_)

    def _rider(self, rid, pickup_s):
        r = self.req[rid]
        return D.Rider(rid, r.d, r.q, r.t, pickup_s, self.travel.van(r.o, r.d))

    # ---------- epoch ----------
    def _epoch(self, triggers):
        obs = self.observation()
        plan, cands = D.solve(obs, self.travel, self.pol.dispatcher)
        transfers, declines, rule_reads, plan_read = [], [], {}, None
        if self.pol.rule != "R0" and self.now < self.pol.rule_active_before_s:
            plan_read = self._plan_summary(plan)
            self._update_assignment(plan)
            for x in obs.open:
                st = self.rs[x.rid]
                if st.declined_s is not None:
                    continue
                if x.rid in plan.predicted_pickup:
                    pred, src = plan.predicted_pickup[x.rid], "plan ETA"
                else:
                    pred = plan.pending_info.get(x.rid, {}).get("tentative_eta_s")
                    src = "tentative ETA (pending)" if pred is not None else "no feasible insertion (infinite)"
                rule_reads[x.rid] = {"elapsed_s": self.now - x.t, "unassigned_since_s": st.unassigned_since,
                                     "predicted_pickup_s": pred, "source": src}
                if L.fires(self.pol.rule, self.now, x.t, st.unassigned_since, pred, self.pol.lag_s):
                    if self._hidden[x.rid].consent_u < self.pol.consent_p:
                        transfers.append(x.rid)
                    else:
                        declines.append(x.rid)
            for rid in declines:
                self.rs[rid].declined_s = self.now
                self._log("transfer_declined", rid, rule=self.pol.rule)
            for rid in transfers:
                st = self.rs[rid]
                st.transfer_s = self.now
                st.lyft_class = "standard" if self.req[rid].q <= 4 else "XL"
                self._set(rid, "xfer_hold", rule=self.pol.rule, lyft_class=st.lyft_class)
                self._push(self.now + self.pol.lag_s, C_BOOK, "book", rid)
            if transfers:
                obs = self.observation()
                plan, cands = D.solve(obs, self.travel, self.pol.dispatcher)
        self._update_assignment(plan)
        audit = self._audit(obs, plan)
        for vid, v in self.vans.items():
            if v.on_duty:
                rt = plan.routes.get(vid)
                v.plan = list(rt.seq) if rt else []
        self.observations.append(obs)
        rec = self._epoch_record(obs, plan, cands, triggers, transfers, declines, rule_reads)
        rec["audit"] = audit
        rec["lyft"]["plan_read_by_rule"] = plan_read          # the plan the rule evaluated (None for R0 / no rule)
        rec["lyft"]["resolved_after_transfer"] = bool(transfers)   # if True, "chosen" is the re-solved plan
        self.epochs.append(rec)

    def _audit(self, obs, plan):
        """Plan audit after every epoch (spec §17.8). Any violation stops the run; the record lists what was checked."""
        cfg, req, bad = self.pol.dispatcher, {x.rid: x for x in obs.open}, []
        seen = {}
        for v in obs.vans:
            rt = plan.routes.get(v.vid)
            if rt is None:
                bad.append(f"{v.vid}: no route")
                continue
            load = sum(r.q for r in v.riders)
            onboard = {r.rid for r in v.riders}
            picked = set()
            for kind, rid in rt.seq:
                if kind == "P":
                    if rid not in req:
                        bad.append(f"{v.vid}: pickup of {rid}, which is not open")
                        continue
                    if rid in seen:
                        bad.append(f"{rid} planned on {seen[rid]} and {v.vid}")
                    seen[rid] = v.vid
                    picked.add(rid); onboard.add(rid); load += req[rid].q
                    if load > v.capacity:
                        bad.append(f"{v.vid}: capacity exceeded at pickup of {rid}")
                else:
                    if rid not in onboard:
                        bad.append(f"{v.vid}: drop-off of {rid} before its pickup")
                    onboard.discard(rid)
                    load -= req[rid].q if rid in req else next(r.q for r in v.riders if r.rid == rid)
            if onboard:
                bad.append(f"{v.vid}: riders left on board at the end of the plan: {sorted(onboard)}")
            ev = D.evaluate(v, rt.seq, {k: req[k] for k in picked}, self.travel, cfg, None)
            for rid in picked:
                g = D.guardrail_s(self.travel.van(req[rid].o, req[rid].d), cfg)
                if ev["rides"][rid] > g:
                    bad.append(f"{rid}: planned ride {ev['rides'][rid]} s over the guardrail {g} s")
        for rid, st in self.rs.items():
            if st.state in ("xfer_hold", "lyft_booked", "lyft_onboard") and rid in seen:
                bad.append(f"{rid} is in a Lyft state and in a van plan")
        if bad:
            raise RuntimeError(f"plan audit failed at {self.now}: " + "; ".join(bad))
        return "pass: capacity, precedence, one van per request, guardrail for new riders, transfer invariant"

    def _plan_summary(self, plan):
        """Compact record of a plan: routes with arrival times, predicted pickups, pending requests with their
        pending price (what the MILP charged) and tentative ETA (what the Lyft rules read); neither is a promise."""
        return {"routes": {v: {"seq": [f"{k}:{x}" for k, x in r.seq], "arrivals_s": list(r.arrivals)}
                           for v, r in plan.routes.items()},
                "predicted_pickup_s": dict(plan.predicted_pickup),
                "pending": {r: {"pending_price_u": i.get("pending_price_u"), "tentative_eta_s": i.get("tentative_eta_s"),
                                "earliest_pickup_s": i.get("earliest_pickup_s"), "reason": i.get("reason")}
                            for r, i in plan.pending_info.items()},
                "status": plan.log["status"], "objective_u": plan.log["objective_u"]}

    def _update_assignment(self, plan):
        assigned = set().union(*[r.S for r in plan.routes.values()]) if plan.routes else set()
        for rid, st in self.rs.items():
            if st.state != "pending_van":
                continue
            if rid in assigned:
                st.unassigned_since = None
            elif st.unassigned_since is None:
                st.unassigned_since = self.now

    def _epoch_record(self, obs, plan, cands, triggers, transfers, declines, rule_reads):
        req = {x.rid: x for x in obs.open}
        cand_log = {}
        for v in obs.vans:
            rows = []
            for S, c, seq in cands.get(v.vid, []):
                ev = D.evaluate(v, seq, req, self.travel, self.pol.dispatcher, None)
                rows.append({"S": sorted(S), "seq": [f"{k}:{r}" for k, r in seq], "cost_u": c,
                             "parts_u": ev["parts_u"], "chosen": plan.routes[v.vid].S == S})
            cand_log[v.vid] = rows
        return {
            "tau_s": obs.tau, "triggers": triggers,
            "vans": [{"van": v.vid, "loc": v.loc, "free_s": v.free_s, "committed": list(v.committed),
                      "riders": [{"rid": r.rid, "pickup_s": r.pickup_s} for r in v.riders]} for v in obs.vans],
            "open": [{"rid": x.rid, "t_s": x.t, "waited_s": obs.tau - x.t, "q": x.q} for x in obs.open],
            "candidates": cand_log,
            "chosen": {v: {"S": sorted(r.S), "seq": [f"{k}:{x}" for k, x in r.seq], "arrivals_s": list(r.arrivals),
                           "cost_u": r.cost_u, "parts_u": r.parts_u} for v, r in plan.routes.items()},
            "predicted_pickup_s": plan.predicted_pickup,
            "pending": {r: plan.pending_info[r] for r in plan.pending},
            "solver": plan.log, "lyft": {"rule": self.pol.rule, "transfers": transfers, "declines": declines,
                                         "reads": rule_reads}}

    # ---------- departures (commitment) ----------
    def _departures(self):
        for vid, v in self.vans.items():
            if not v.on_duty or v.status != "idle" or not v.plan:
                continue
            kind, rid = v.plan.pop(0)
            r, st = self.req[rid], self.rs[rid]
            if kind == "P":
                if st.state != "pending_van":
                    raise RuntimeError(f"{vid} planned pickup of {rid} in state {st.state}")
                dest = r.o
                st.van, st.committed_s = vid, self.now
                self._set(rid, "committed", vid=vid)
            else:
                if rid not in v.onboard:
                    raise RuntimeError(f"{vid} planned drop-off of {rid}, not onboard")
                dest = r.d
            arr = self.now + self.travel.van(v.loc, dest)
            self._log("depart", rid, vid, stop=kind, frm=v.loc, to=dest, arrive_s=arr)
            v.status, v.current, v.loc = "moving", (kind, rid, arr), dest
            self._push(arr, C_DROP if kind == "D" else C_ARRIVE, "arrive", vid, (kind, rid))

    # ---------- results ----------
    def outcomes(self):
        rows = []
        for r in self.scen.requests:
            st = self.rs[r.rid]
            rows.append({"request_id": r.rid, "t_request_s": r.t, "party": r.q, "outcome": st.state,
                         "van": st.van, "committed_s": st.committed_s, "curb_arrival_s": st.curb_arrival_s,
                         "pickup_s": st.pickup_s,
                         "wait_s": None if st.pickup_s is None else st.pickup_s - r.t, "drop_s": st.drop_s,
                         "ride_s": None if st.drop_s is None else st.drop_s - st.pickup_s,
                         "cancel_s": st.cancel_s, "noshow_s": st.noshow_s, "transfer_s": st.transfer_s,
                         "booking_s": st.booking_s, "lyft_class": st.lyft_class, "declined_s": st.declined_s})
        return rows
