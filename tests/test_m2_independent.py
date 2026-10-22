"""Independent verification of M2: Lyft transfer rules interacting with dispatcher C over the whole L4 evening.

What is trusted from the implementation: sim.inputs.load (to build the frozen scenario), sim.run.policy_for (the
policy under test), Engine(...).run() (to produce the logs) and, in one consistency check, dispatch.solve. Everything
else is recomputed here from the event log, the per-epoch records and the frozen files, which this module reads
itself (requests.csv, latent.csv, availability.csv, scenario.json, the travel matrix). The rule thresholds, the state
machine, the same-second order, the Lyft timing and the counting identities are restated from scenario_spec.md v0.6
§5, §6, §17 and D-43/D-45/D-46/D-52/D-54, not imported from sim.lyft or sim.engine.

Runs: the six rules on L4 (evening window, pending price A, curb-wait D-54), one repeat for reproducibility, and
controlled cases built by changing scen.hidden IN MEMORY only (frozen files are never written):
    lyft_paths:R2(15)   R015 deadline inside the lag; R011 deadline exactly at booking time (patience before booking);
                        R016 deadline after booking, before the Lyft arrives; R012 (standard) and R002 (XL) absent at
                        the Lyft curb; R001 deadline exactly at the Lyft arrival (arrival wins the tie).
    van_noshow:R2(15)   R003 absent at the van curb at 18:20:22 while R2 is active (D-54 hypothetical drop-off).
    van_noshow:R1(10)   the same under R1(10).
Case (e), a transfer of a request assigned (not committed) in the plan the rule read, occurs on L4 itself (e.g. R1(15)
at 18:15: R001 is the first stop of idle V1), so it is checked on the L4 runs.

Run: .venv/bin/python -m pytest -q tests/test_m2_independent.py        (add -s to print the findings tables)
All runs execute in parallel worker processes (about 45 s wall in total); nothing is written to disk.
"""
import csv
import dataclasses
import hashlib
import io
import json
import math
import multiprocessing as mp
import os
import time
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pytest

from sim import dispatch as D
from sim import engine as E
from sim import inputs, run as RUN

ROOT = Path(__file__).resolve().parents[1]
SCEN = ROOT / "data" / "scenarios" / "v2"
L4 = SCEN / "L4"
MATRIX = ROOT / "data" / "processed" / "tt_locations_v2.csv"

RULES = ["R0", "R1(10)", "R1(15)", "R1u(10)", "R2(15)", "R3(2)"]
# spec §6 table, restated (not imported from sim.lyft)
RULE_SPEC = {"R1(10)": ("elapsed", 600), "R1(15)": ("elapsed", 900), "R1u(10)": ("unassigned", 600),
             "R2(15)": ("predicted", 900), "R3(2)": ("van_vs_lyft", 120)}
TYPICAL_LYFT_S = 480          # spec §6 R3: "8 min"
DWELL_S, NOSHOW_WAIT_S = 30, 180
VANS_ON_S = 900               # 18:15
TERMINAL = {"van_completed", "lyft_completed", "cancel_pending_van", "cancel_after_transfer", "noshow_van",
            "noshow_lyft", "lyft_failed"}
LYFT_STATES = {"xfer_hold", "lyft_booked", "lyft_onboard"}
VAN_STATES = {"committed", "onboard"}
ALLOWED = {                   # spec §17.2
    "unrevealed": {"pending_van"},
    "pending_van": {"committed", "xfer_hold", "cancel_pending_van"},
    "committed": {"onboard", "noshow_van", "cancel_pending_van"},
    "onboard": {"van_completed"},
    "xfer_hold": {"lyft_booked", "cancel_after_transfer"},
    "lyft_booked": {"lyft_onboard", "noshow_lyft", "cancel_after_transfer", "lyft_failed"},
    "lyft_onboard": {"lyft_completed"},
}
C_EPOCH, C_DEPART = 80, 90

LYFT_PATH_MODS = {"R015": {"patience_s": 60}, "R011": {"patience_s": 330}, "R016": {"patience_s": 300},
                  "R012": {"noshow_u": 0.0}, "R002": {"noshow_u": 0.0}, "R001": {"patience_s": 600}}
VAN_NOSHOW_MODS = {"R003": {"noshow_u": 0.0}}
JOBS = [(f"L4:{r}", r, {}) for r in RULES] + [
    ("repeat:R1(10)", "R1(10)", {}),
    ("lyft_paths:R2(15)", "R2(15)", LYFT_PATH_MODS),
    ("van_noshow:R2(15)", "R2(15)", VAN_NOSHOW_MODS),
    ("van_noshow:R1(10)", "R1(10)", VAN_NOSHOW_MODS),
]
ALL_RUNS = [j[0] for j in JOBS if not j[0].startswith("repeat:")]
RULE_RUNS = [n for n in ALL_RUNS if not n.endswith(":R0")]


# ---------------------------------------------------------------- running (worker processes, in memory) ----------
def _run_job(job):
    name, rule, mods = job
    try:
        scen = inputs.load("L4")
        for rid, kw in mods.items():                       # in memory only
            scen.hidden[rid] = dataclasses.replace(scen.hidden[rid], **kw)
        pol = RUN.policy_for(scen, rule)
        t0 = time.perf_counter()
        eng = E.Engine(scen, inputs.Travel(1.0, 1.0), pol).run()
        return name, {"name": name, "rule": rule, "mods": mods, "events": eng.events, "epochs": eng.epochs,
                      "outcomes": eng.outcomes(), "observations": eng.observations, "p_absent": pol.p_absent,
                      "consent_p": pol.consent_p, "lag_s": pol.lag_s, "cfg": pol.dispatcher,
                      "rule_active_before_s": pol.rule_active_before_s, "wall_s": time.perf_counter() - t0}
    except Exception:                                      # reported by the tests that use this run
        return name, {"name": name, "error": traceback.format_exc()}


@pytest.fixture(scope="module")
def runs():
    try:
        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=max(1, min(len(JOBS), os.cpu_count() or 1)), mp_context=ctx) as ex:
            return dict(ex.map(_run_job, JOBS))
    except Exception:                                      # pool unavailable (e.g. another import mode): serial
        return dict(map(_run_job, JOBS))


def get(runs, name):
    r = runs[name]
    if "error" in r:
        pytest.fail(f"run {name} raised:\n{r['error']}")
    return r


# ---------------------------------------------------------------- independent reading of the frozen inputs -------
_MATRIX = {}


def _matrix():
    if not _MATRIX:
        with open(MATRIX, newline="") as f:
            for row in csv.DictReader(f):
                _MATRIX[(row["origin"], row["dest"])] = float(row["seconds"])
    return _MATRIX


class Ref:
    def __init__(self, mods):
        self.params = json.loads((L4 / "scenario.json").read_text())["params"]
        with open(L4 / "requests.csv", newline="") as f:
            self.req = {r["request_id"]: {"t": int(r["t_request_s"]), "o": r["o_loc"], "d": r["d_loc"],
                                          "q": int(r["party"])} for r in csv.DictReader(f)}
        with open(L4 / "latent.csv", newline="") as f:
            self.lat = {r["request_id"]: {"patience_s": int(r["patience_s"]), "noshow_u": float(r["noshow_u"]),
                                          "consent_u": float(r["consent_u"]), "lyft_delay_s": int(r["lyft_delay_s"])}
                        for r in csv.DictReader(f)}
        for rid, kw in mods.items():
            self.lat[rid].update(kw)
        with open(L4 / "availability.csv", newline="") as f:
            self.vans = {r["van_id"]: {"loc": r["start_loc"], "cap": int(r["capacity"]),
                                       "on": int(r["avail_start_s"])} for r in csv.DictReader(f)}
        self.m = float(self.params["travel_multiplier"])
        self.lag = int(self.params["lyft_lag_s"])
        self.p_c = float(self.params["consent_p"])

    def van_s(self, a, b):
        return int(round(_matrix()[(a, b)] * self.m))

    def lyft_s(self, a, b):
        return int(round(_matrix()[(a, b)] * self.m))

    def guardrail(self, rid):                               # D-47 / D-52: max(25 min, 2 x van direct + 5 min)
        r = self.req[rid]
        return max(1500, 2 * self.van_s(r["o"], r["d"]) + 300)

    def lyft_class(self, rid):
        return "standard" if self.req[rid]["q"] <= 4 else "XL"

    def deadline(self, rid):
        return self.req[rid]["t"] + self.lat[rid]["patience_s"]


def ref_for(res):
    return Ref(res["mods"])


def _stop(s):
    k, r = s.split(":")
    return k, r


# ---------------------------------------------------------------- replay of the event log with the epoch plans ----
class Replay:
    """Walks the event log and the epoch records in execution order and keeps its own copy of every request state,
    every van's remaining plan (replaced by `chosen` at each epoch, popped at each departure), heading and load.
    Violations are collected per category."""

    def __init__(self, res, ref):
        self.res, self.ref = res, ref
        self.v = defaultdict(list)
        ev, eps = res["events"], res["epochs"]
        self.states = {rid: "unrevealed" for rid in ref.req}
        self.hist = defaultdict(list)                       # rid -> state-change rows
        self.rows = defaultdict(list)                       # rid -> every row naming it
        self.plans, self.heading, self.loc = {}, {}, {v: x["loc"] for v, x in ref.vans.items()}
        self.curb_wait = {}                                 # vid -> absent rider whose 180-s timer runs (D-54)
        self.onboard = defaultdict(dict)
        self.committed_by, self.declined_at, self.offers = {}, {}, []
        self.snap = []                                      # per epoch: states before the epoch's own events
        self.max_load = defaultdict(int)
        taus = [ep["tau_s"] for ep in eps]
        if taus != sorted(set(taus)):
            self.v["epochs"].append("epoch times are not strictly increasing (more than one epoch in a second?)")
        pos, j = [], 0
        for tau in taus:
            while j < len(ev) and (ev[j]["t_s"] < tau or (ev[j]["t_s"] == tau and ev[j]["class"] < C_EPOCH)):
                j += 1
            pos.append(j)
        self.epoch_events = []
        i = k = 0
        while i < len(ev) or k < len(eps):
            if k < len(eps) and pos[k] == i:
                ep, tau = eps[k], taus[k]
                self.snap.append(dict(self.states))
                own = []
                while i < len(ev) and ev[i]["t_s"] == tau and ev[i]["class"] == C_EPOCH:
                    own.append(ev[i])
                    self._handle(ev[i])
                    i += 1
                self.epoch_events.append(own)
                self._check_plan_read(ep, self.snap[-1])
                for vid, c in ep["chosen"].items():
                    self.plans[vid] = [_stop(s) for s in c["seq"]]
                self._check_plans_after_epoch(ep)
                k += 1
                continue
            if i >= len(ev):
                self.v["epochs"].append(f"epoch at {taus[k]} placed after the last event")
                k += 1
                continue
            if ev[i]["class"] == C_EPOCH:
                self.v["epochs"].append(f"class-80 event at {ev[i]['t_s']} outside any epoch: {ev[i]}")
            self._handle(ev[i])
            i += 1
            self._check_lyft_exclusion(f"after event {ev[i - 1]['event']} at {ev[i - 1]['t_s']}")

    # -- checks
    def _van_refs(self, rid):
        out = []
        for vid, pl in self.plans.items():
            if any(r == rid for _, r in pl):
                out.append(f"plan of {vid}")
        for vid, h in self.heading.items():
            if h and h[1] == rid:
                out.append(f"heading of {vid}")
        for vid, ob in self.onboard.items():
            if rid in ob:
                out.append(f"onboard {vid}")
        return out

    def _check_lyft_exclusion(self, where):
        for rid, s in self.states.items():
            if s in LYFT_STATES:
                refs = self._van_refs(rid)
                if refs:
                    self.v["exclusion"].append(f"{rid} in {s} and in {refs} ({where})")

    def _check_plan_read(self, ep, pre):
        pr = ep["lyft"]["plan_read_by_rule"]
        if pr is None:
            return
        for vid, rt in pr["routes"].items():
            for s in rt["seq"]:
                k, rid = _stop(s)
                if k == "P" and pre[rid] != "pending_van":
                    self.v["exclusion"].append(f"plan read at {ep['tau_s']}: pickup of {rid} in state {pre[rid]}")
                if pre[rid] in LYFT_STATES or pre[rid] in TERMINAL:
                    self.v["exclusion"].append(f"plan read at {ep['tau_s']}: {rid} in state {pre[rid]}")

    def _check_plans_after_epoch(self, ep):
        tau = ep["tau_s"]
        self._check_lyft_exclusion(f"after epoch {tau}")
        for vid, pl in self.plans.items():
            picked, load = set(), sum(self.ref.req[r]["q"] for r in self.onboard[vid])
            h = self.heading.get(vid)
            if h and h[0] == "P" and self.states[h[1]] == "committed":
                load += self.ref.req[h[1]]["q"]
                picked.add(h[1])
            cw = self.curb_wait.get(vid)
            if cw is not None and self.states[cw] == "committed":   # D-54: planned as possibly boarding at expiry
                picked.add(cw)
                load += self.ref.req[cw]["q"]
            have = set(self.onboard[vid]) | picked
            if h and h[0] == "D" and h[1] in have:          # the drop the van is driving to is not in its plan
                have.discard(h[1])
                load -= self.ref.req[h[1]]["q"]
            for k, rid in pl:
                s = self.states[rid]
                if s in TERMINAL or s in LYFT_STATES:
                    self.v["exclusion"].append(f"epoch {tau}: plan of {vid} has {k}:{rid} in state {s}")
                if k == "P":
                    if s != "pending_van":
                        self.v["precedence"].append(f"epoch {tau}: {vid} plans pickup of {rid} in state {s}")
                    have.add(rid)
                    load += self.ref.req[rid]["q"]
                    if load > self.ref.vans[vid]["cap"]:
                        self.v["capacity"].append(f"epoch {tau}: planned load {load} on {vid} at P:{rid}")
                else:
                    if rid not in have:
                        self.v["precedence"].append(f"epoch {tau}: {vid} plans drop of {rid} not aboard/picked")
                    have.discard(rid)
                    load -= self.ref.req[rid]["q"]
            if have:
                self.v["precedence"].append(f"epoch {tau}: {vid} plan leaves {sorted(have)} aboard")

    # -- event handling
    def _handle(self, e):
        rid, vid, t = e["request"], e["van"], e["t_s"]
        if rid is not None:
            self.rows[rid].append(e)
        kind = e["event"]
        if kind == "state":
            frm, to = e["state_from"], e["state_to"]
            if self.states[rid] != frm:
                self.v["states"].append(f"{rid} at {t}: logged from {frm}, replay has {self.states[rid]}")
            if to not in ALLOWED.get(frm, set()):
                self.v["states"].append(f"{rid} at {t}: illegal transition {frm} -> {to}")
            self.states[rid] = to
            self.hist[rid].append(e)
            if to in LYFT_STATES and self._van_refs(rid) and to != "xfer_hold":
                self.v["exclusion"].append(f"{rid} enters {to} at {t} while in {self._van_refs(rid)}")
            if to == "xfer_hold":
                self.offers.append((t, rid, "accepted"))
            if to == "committed":
                self.committed_by[rid] = vid
            elif to == "onboard":
                if self.committed_by.get(rid) != vid:
                    self.v["commitment"].append(f"{rid} boards {vid}, committed by {self.committed_by.get(rid)}")
                if self.heading.get(vid) != ("P", rid):
                    self.v["precedence"].append(f"{rid} boards {vid} at {t}, van heading {self.heading.get(vid)}")
                self.onboard[vid][rid] = t
                self.heading[vid] = None
                load = sum(self.ref.req[x]["q"] for x in self.onboard[vid])
                self.max_load[vid] = max(self.max_load[vid], load)
                if load > self.ref.vans[vid]["cap"]:
                    self.v["capacity"].append(f"{vid} load {load} at {t}")
            elif to == "van_completed":
                if rid not in self.onboard[vid]:
                    self.v["precedence"].append(f"{rid} dropped by {vid} at {t} without boarding it")
                else:
                    del self.onboard[vid][rid]
                if self.heading.get(vid) != ("D", rid):
                    self.v["precedence"].append(f"{rid} dropped by {vid} at {t}, van heading {self.heading.get(vid)}")
                self.heading[vid] = None
            elif to == "noshow_van":
                self.curb_wait.pop(vid, None)
                if self.committed_by.get(rid) != vid:
                    self.v["commitment"].append(f"{rid} no-show on {vid}, committed by {self.committed_by.get(rid)}")
        elif kind == "depart":
            pl = self.plans.get(vid) or []
            head = pl.pop(0) if pl else None
            if head != (e["stop"], rid):
                self.v["execution"].append(f"{vid} departs at {t} for {e['stop']}:{rid}; plan head was {head}")
            if e["frm"] != self.loc[vid]:
                self.v["execution"].append(f"{vid} departs from {e['frm']} at {t}, replay location {self.loc[vid]}")
            want = t + self.ref.van_s(e["frm"], e["to"])
            if e["arrive_s"] != want:
                self.v["timing"].append(f"{vid} leg {e['frm']}->{e['to']} at {t}: arrive {e['arrive_s']} != {want}")
            if e["stop"] == "P":
                if self.states[rid] != "committed" or self.committed_by.get(rid) != vid:
                    self.v["commitment"].append(f"{vid} departs for P:{rid} at {t}; state {self.states[rid]}")
                if e["to"] != self.ref.req[rid]["o"]:
                    self.v["execution"].append(f"{vid} P:{rid} goes to {e['to']}")
            else:
                if rid not in self.onboard[vid]:
                    self.v["precedence"].append(f"{vid} departs to drop {rid} at {t}, not aboard")
                if e["to"] != self.ref.req[rid]["d"]:
                    self.v["execution"].append(f"{vid} D:{rid} goes to {e['to']}")
            self.heading[vid] = (e["stop"], rid)
            self.loc[vid] = e["to"]
        elif kind in ("curb_arrival", "arrive_no_rider"):
            if self.heading.get(vid) != ("P", rid):
                self.v["precedence"].append(f"{kind} {rid} by {vid} at {t}, heading {self.heading.get(vid)}")
            self.heading[vid] = None
            if kind == "curb_arrival":
                self.curb_wait[vid] = rid
            if kind == "curb_arrival" and e.get("present") is not False:
                self.v["states"].append(f"curb_arrival row for {rid} without present=False")
        elif kind == "transfer_declined":
            if rid in self.declined_at:
                self.v["offers"].append(f"{rid} offered again at {t} after declining at {self.declined_at[rid]}")
            if self.states[rid] != "pending_van":
                self.v["offers"].append(f"{rid} declined at {t} in state {self.states[rid]}")
            self.declined_at[rid] = t
            self.offers.append((t, rid, "declined"))


_REPLAYS = {}


def replay(res):
    key = res["name"]
    if key not in _REPLAYS:
        _REPLAYS[key] = Replay(res, ref_for(res))
    return _REPLAYS[key]


# ---------------------------------------------------------------- rule recomputation -------------------------------
def fires(rule, tau, t, unas, pred, lag):
    kind, th = RULE_SPEC[rule]
    pred = math.inf if pred is None else pred
    if kind == "elapsed":
        return tau - t >= th
    if kind == "unassigned":
        return unas is not None and tau - unas >= th
    if kind == "predicted":
        return pred - t > th
    if kind == "van_vs_lyft":
        return pred > tau + lag + TYPICAL_LYFT_S + th
    raise ValueError(kind)


def _assigned(routes):
    return {_stop(s)[1] for rt in routes.values() for s in rt["seq"] if s.startswith("P:")}


def _pred(plan_pred, plan_pending, rid):
    if rid in plan_pred:
        return plan_pred[rid]
    return (plan_pending.get(rid) or {}).get("tentative_eta_s")


def rule_check(res):
    """Recompute at every epoch which eligible requests the rule should fire on, from the logged plan the rule read
    (`plan_read_by_rule`) and observable fields only. Returns mismatches and diagnostics."""
    rp, ref, rule = replay(res), ref_for(res), res["rule"]
    out = {"mismatch": [], "offers": [], "would_fire_on_resolved": [], "exec_only_diff": [], "max_unas_after": 0,
           "reads": 0}
    unas, unas_exec = {}, {}           # engine convention (both plans of the epoch) / executed plans only
    declined = set()
    for k, ep in enumerate(res["epochs"]):
        tau, ly = ep["tau_s"], ep["lyft"]
        pre = rp.snap[k]
        for rid, s in pre.items():                      # revealed requests start unassigned at their request time
            if s != "unrevealed" and rid not in unas and s == "pending_van":
                unas[rid] = unas_exec[rid] = ref.req[rid]["t"]
        first_open = {r for r, s in pre.items() if s == "pending_van"}
        transfers, declines = set(ly["transfers"]), set(ly["declines"])
        final_open = {o["rid"] for o in ep["open"]}
        if final_open != first_open - transfers:
            out["mismatch"].append(f"{tau}: open after epoch {sorted(final_open)} != pending before minus "
                                   f"transfers {sorted(first_open - transfers)}")
        active = rule != "R0" and tau < res["rule_active_before_s"]
        pr = ly["plan_read_by_rule"]
        if not active:
            if pr is not None or transfers or declines or ly["reads"]:
                out["mismatch"].append(f"{tau}: rule inactive but plan read / decisions logged")
        else:
            if pr is None:
                out["mismatch"].append(f"{tau}: rule active but no plan read logged")
                continue
            a_read = _assigned(pr["routes"])
            for rid in first_open:
                if rid in a_read:
                    unas[rid] = None
                elif unas.get(rid) is None:
                    unas[rid] = tau
            eligible = first_open - declined
            if set(ly["reads"]) != eligible:
                out["mismatch"].append(f"{tau}: rule read {sorted(ly['reads'])}, eligible {sorted(eligible)}")
            fired = set()
            for rid in sorted(eligible):
                t = ref.req[rid]["t"]
                pred = _pred(pr["predicted_pickup_s"], pr["pending"], rid)
                rd = ly["reads"].get(rid, {})
                if rd.get("predicted_pickup_s") != pred or rd.get("elapsed_s") != tau - t or \
                        rd.get("unassigned_since_s") != unas.get(rid):
                    out["mismatch"].append(f"{tau} {rid}: logged read {rd} vs recomputed pred={pred} "
                                           f"elapsed={tau - t} unassigned_since={unas.get(rid)}")
                out["reads"] += 1
                if fires(rule, tau, t, unas.get(rid), pred, ref.lag):
                    fired.add(rid)
                if RULE_SPEC[rule][0] == "unassigned":
                    if unas.get(rid) is not None and tau >= VANS_ON_S:
                        out["max_unas_after"] = max(out["max_unas_after"], tau - unas[rid])
                    if fires(rule, tau, t, unas.get(rid), pred, ref.lag) != \
                            fires(rule, tau, t, unas_exec.get(rid), pred, ref.lag):
                        out["exec_only_diff"].append((tau, rid))
            want_t = {r for r in fired if ref.lat[r]["consent_u"] < ref.p_c}       # spec §3.3: U < p_c accepts
            want_d = fired - want_t
            if transfers != want_t or declines != want_d:
                out["mismatch"].append(f"{tau}: engine transfers {sorted(transfers)} declines {sorted(declines)}; "
                                       f"recomputed {sorted(want_t)} / {sorted(want_d)}")
            out["offers"] += [(tau, r) for r in sorted(fired)]
            declined |= declines
            if transfers:                                   # what a second pass on the re-solved plan would do
                for rid in sorted(final_open - declined):
                    pred = _pred(ep["predicted_pickup_s"], ep["pending"], rid)
                    if fires(rule, tau, ref.req[rid]["t"], unas.get(rid), pred, ref.lag):
                        out["would_fire_on_resolved"].append((tau, rid))
        a_exec = _assigned(ep["chosen"])
        for rid in final_open:
            if rid in a_exec:
                unas[rid] = unas_exec[rid] = None
            else:
                if unas.get(rid) is None:
                    unas[rid] = tau
                if unas_exec.get(rid) is None:
                    unas_exec[rid] = tau
    return out


_RULECHECK = {}


def rule_result(res):
    if res["name"] not in _RULECHECK:
        _RULECHECK[res["name"]] = rule_check(res)
    return _RULECHECK[res["name"]]


# ---------------------------------------------------------------- counts ------------------------------------------
def lyft_counts(res):
    """Operational counts (D-45), each from its own kind of event, split by class (party size from requests.csv)."""
    ref, c = ref_for(res), Counter()
    for e in res["events"]:
        rid = e["request"]
        if e["event"] == "transfer_declined":
            c["offers", ref.lyft_class(rid)] += 1
            c["declined", ref.lyft_class(rid)] += 1
        if e["event"] != "state":
            continue
        k, frm, to = ref.lyft_class(rid), e["state_from"], e["state_to"]
        if to == "xfer_hold":
            c["offers", k] += 1
            c["accepted", k] += 1
        elif to == "lyft_booked":
            c["bookings", k] += 1
        elif to == "cancel_after_transfer":
            c["cancel_in_lag" if frm == "xfer_hold" else "cancel_after_booking", k] += 1
        elif to == "lyft_completed":
            c["completed", k] += 1
        elif to == "noshow_lyft":
            c["lyft_noshow", k] += 1
        elif to == "lyft_failed":
            c["lyft_failed", k] += 1
    return c


# =================================================================== tests ==========================================
@pytest.mark.parametrize("name", ALL_RUNS)
def test_01_no_request_in_van_and_lyft_state(runs, name):
    """Replay: a request in xfer_hold / lyft_booked / lyft_onboard is never in a van plan, heading or aboard, and no
    plan (read or executed) contains a request in a Lyft or terminal state; legal state transitions only."""
    rp = replay(get(runs, name))
    assert not rp.v["exclusion"], rp.v["exclusion"][:10]
    assert not rp.v["states"], rp.v["states"][:10]
    assert not rp.v["epochs"], rp.v["epochs"][:10]
    for rid, rows in rp.rows.items():
        hist = [e["state_to"] for e in rp.hist[rid]]
        if any(s in LYFT_STATES for s in hist):
            vanish = [e for e in rows if e["van"] is not None or e["event"] in ("depart", "curb_arrival")]
            assert not vanish, f"{rid}: van-side rows for a transferred request: {vanish}"
            assert not any(s in VAN_STATES for s in hist), f"{rid}: {hist}"


@pytest.mark.parametrize("name", ALL_RUNS)
def test_02_one_terminal_outcome_and_count_identities(runs, name):
    res = get(runs, name)
    rp, ref = replay(res), ref_for(res)
    for rid in ref.req:
        term = [e["state_to"] for e in rp.hist[rid] if e["state_to"] in TERMINAL]
        assert len(term) == 1, f"{rid}: terminal states {term}"
        assert rp.hist[rid][-1]["state_to"] == term[0], f"{rid}: state change after terminal {term[0]}"
    out = {o["request_id"]: o for o in res["outcomes"]}
    assert {r: out[r]["outcome"] for r in ref.req} == {r: rp.states[r] for r in ref.req}
    c = lyft_counts(res)
    rc = rule_result(res)
    for k in ("standard", "XL"):
        assert c["offers", k] == c["accepted", k] + c["declined", k]
        assert c["accepted", k] == c["bookings", k] + c["cancel_in_lag", k], (k, c)
        assert c["bookings", k] == (c["completed", k] + c["lyft_noshow", k] + c["cancel_after_booking", k]
                                    + c["lyft_failed", k]), (k, c)
        assert c["lyft_failed", k] == 0
    # offers counted independently: the rule firings recomputed from the logged plans
    assert len(rc["offers"]) == c["offers", "standard"] + c["offers", "XL"], (rc["offers"], c)
    # the per-request table counts the same things
    acc = sum(o["transfer_s"] is not None for o in out.values())
    assert acc == c["accepted", "standard"] + c["accepted", "XL"]
    assert sum(o["booking_s"] is not None for o in out.values()) == c["bookings", "standard"] + c["bookings", "XL"]
    assert sum(o["declined_s"] is not None for o in out.values()) == c["declined", "standard"] + c["declined", "XL"]
    for k in ("standard", "XL"):
        assert sum(o["outcome"] == "lyft_completed" and o["lyft_class"] == k for o in out.values()) == c["completed", k]
        assert sum(o["booking_s"] is not None and o["lyft_class"] == k for o in out.values()) == c["bookings", k]
    # a party of 5 is always one XL booking
    for rid, o in out.items():
        if o["transfer_s"] is not None:
            assert o["lyft_class"] == ref.lyft_class(rid), rid
        books = [e for e in rp.hist[rid] if e["state_to"] == "lyft_booked"]
        assert len(books) <= 1, rid
        for e in books:
            assert e["lyft_class"] == ref.lyft_class(rid)


@pytest.mark.parametrize("name", ALL_RUNS)
def test_03_lyft_timing_identities(runs, name):
    res = get(runs, name)
    rp, ref = replay(res), ref_for(res)
    out = {o["request_id"]: o for o in res["outcomes"]}
    n = 0
    for rid in ref.req:
        h = {e["state_to"]: e for e in rp.hist[rid]}
        if "xfer_hold" not in h:
            continue
        n += 1
        r, lat, o = ref.req[rid], ref.lat[rid], out[rid]
        dec = h["xfer_hold"]["t_s"]
        assert o["transfer_s"] == dec
        book = dec + ref.lag
        dl = ref.deadline(rid)
        lyft_rows = {e["event"]: e for e in rp.rows[rid] if e["event"].startswith("lyft_")}
        if dl <= book:                                    # deadline inside the lag (patience before booking, §17.3)
            assert "lyft_booked" not in h and h["cancel_after_transfer"]["t_s"] == dl
            assert h["cancel_after_transfer"]["state_from"] == "xfer_hold"
            assert o["booking_s"] is None and not lyft_rows, (rid, lyft_rows)
            continue
        assert h["lyft_booked"]["t_s"] == book and o["booking_s"] == book, rid
        arr = book + lat["lyft_delay_s"]
        if dl < arr:                                      # cancelled after booking, before the Lyft arrives
            assert h["cancel_after_transfer"]["t_s"] == dl and h["cancel_after_transfer"]["state_from"] == "lyft_booked"
            assert lyft_rows["lyft_arrive_no_rider"]["t_s"] == arr
            assert o["curb_arrival_s"] is None and o["pickup_s"] is None
            continue
        assert o["curb_arrival_s"] == arr, rid             # arrival wins a same-second tie with the deadline
        if lat["noshow_u"] < res["p_absent"]:
            assert lyft_rows["lyft_curb_arrival"]["t_s"] == arr and lyft_rows["lyft_curb_arrival"]["present"] is False
            assert h["noshow_lyft"]["t_s"] == arr + NOSHOW_WAIT_S
            assert "lyft_completed" not in h and o["pickup_s"] is None and o["wait_s"] is None
            continue
        pick = arr
        drop = pick + DWELL_S + ref.lyft_s(r["o"], r["d"])
        assert h["lyft_onboard"]["t_s"] == pick and o["pickup_s"] == pick
        assert h["lyft_onboard"]["wait_s"] == pick - r["t"] == o["wait_s"], rid   # from the ORIGINAL request
        assert h["lyft_completed"]["t_s"] == drop == o["drop_s"], rid
        assert h["lyft_completed"]["ride_s"] == drop - pick == o["ride_s"]
    if res["rule"] != "R0":
        assert n > 0
    # every cancellation happens exactly at the deadline, and never after a vehicle reached the curb
    for rid in ref.req:
        for e in rp.hist[rid]:
            if e["state_to"] in ("cancel_pending_van", "cancel_after_transfer"):
                assert e["t_s"] == ref.deadline(rid), (rid, e)
                reached = [x for x in rp.rows[rid] if x["t_s"] <= e["t_s"] and (
                    x["event"] in ("curb_arrival", "lyft_curb_arrival")
                    or (x["event"] == "state" and x["state_to"] in ("onboard", "lyft_onboard")))]
                assert not reached, (rid, e, reached)
                assert not any(x["state_to"] in ("onboard", "lyft_onboard") for x in rp.hist[rid])


@pytest.mark.parametrize("name", RULE_RUNS)
def test_04_rule_decisions_recomputed_each_epoch(runs, name):
    rc = rule_result(get(runs, name))
    assert not rc["mismatch"], rc["mismatch"][:10]
    assert rc["reads"] > 0


@pytest.mark.parametrize("name", ALL_RUNS)
def test_04b_single_rule_pass_and_resolved_plan_executed(runs, name):
    """One epoch per second; every xfer_hold / decline is that epoch's own decision (no same-second cascade); after a
    transfer `chosen` is a different (re-solved) plan without the transferred request; without a transfer `chosen`
    equals the plan the rule read; departures follow `chosen` (replay)."""
    res = get(runs, name)
    rp = replay(res)
    for ep, own in zip(res["epochs"], rp.epoch_events):
        ly = ep["lyft"]
        xf = sorted(e["request"] for e in own if e["event"] == "state" and e["state_to"] == "xfer_hold")
        dc = sorted(e["request"] for e in own if e["event"] == "transfer_declined")
        assert xf == sorted(ly["transfers"]) and dc == sorted(ly["declines"]), ep["tau_s"]
        assert ly["resolved_after_transfer"] == bool(ly["transfers"])
        pr = ly["plan_read_by_rule"]
        chosen_stops = {_stop(s)[1] for c in ep["chosen"].values() for s in c["seq"]}
        assert not (chosen_stops & set(ly["transfers"])), (ep["tau_s"], ly["transfers"])
        if pr is not None and not ly["transfers"]:
            assert {v: c["seq"] for v, c in ep["chosen"].items()} == {v: r["seq"] for v, r in pr["routes"].items()}
            assert {v: c["arrivals_s"] for v, c in ep["chosen"].items()} == \
                   {v: r["arrivals_s"] for v, r in pr["routes"].items()}
    # xfer_hold / decline rows only ever come from an epoch (class 80)
    for e in res["events"]:
        if e["event"] == "transfer_declined" or (e["event"] == "state" and e["state_to"] == "xfer_hold"):
            assert e["class"] == C_EPOCH
    assert not rp.v["execution"], rp.v["execution"][:10]


@pytest.mark.parametrize("name", ["L4:R1(10)", "L4:R1(15)", "L4:R2(15)", "L4:R3(2)"])
def test_04c_resolve_reproduces_chosen(runs, name):
    """After a transfer, re-solving the logged post-transfer observation reproduces `chosen` (the executed plan is the
    re-solve on the reduced request set, not the plan the rule read)."""
    res = get(runs, name)
    travel = inputs.Travel(1.0, 1.0)
    n = 0
    for ep, obs in zip(res["epochs"], res["observations"]):
        if not ep["lyft"]["transfers"]:
            continue
        assert not ({x.rid for x in obs.open} & set(ep["lyft"]["transfers"]))
        plan, _ = D.solve(obs, travel, res["cfg"])
        assert {v: [f"{k}:{x}" for k, x in r.seq] for v, r in plan.routes.items()} == \
               {v: c["seq"] for v, c in ep["chosen"].items()}, ep["tau_s"]
        n += 1
    assert n > 0


def test_04d_transfer_of_assigned_request_case_e(runs):
    """Case (e) on L4: R1(15) at 18:15 transfers R001, the first stop of idle V1 in the plan the rule read (it would
    have been committed at this second's departures). The executed plan no longer contains it and V1 does not depart
    toward it."""
    res = get(runs, "L4:R1(15)")
    ep = next(e for e in res["epochs"] if e["tau_s"] == 900)
    pr = ep["lyft"]["plan_read_by_rule"]
    assert pr["routes"]["V1"]["seq"][0] == "P:R001" and "R001" in ep["lyft"]["transfers"]
    v1 = next(v for v in ep["vans"] if v["van"] == "V1")
    assert v1["committed"] == [] and v1["free_s"] == 900
    assert "P:R001" not in ep["chosen"]["V1"]["seq"] and "P:R001" not in ep["chosen"]["V2"]["seq"]
    assert not [e for e in res["events"] if e["request"] == "R001" and e["event"] == "depart"]
    # every L4 transfer of a request assigned in the plan read (source "plan ETA") obeys the same
    cases = 0
    for nm in RULE_RUNS:
        if not nm.startswith("L4:"):
            continue
        for ep in get(runs, nm)["epochs"]:
            for rid in ep["lyft"]["transfers"]:
                if ep["lyft"]["reads"][rid]["source"] == "plan ETA":
                    cases += 1
                    assert any(f"P:{rid}" in r["seq"] for r in ep["lyft"]["plan_read_by_rule"]["routes"].values())
                    assert all(f"P:{rid}" not in c["seq"] for c in ep["chosen"].values())
    assert cases > 0


@pytest.mark.parametrize("name", RULE_RUNS)
def test_05_declined_never_offered_again(runs, name):
    res = get(runs, name)
    rp = replay(res)
    assert not rp.v["offers"], rp.v["offers"]
    per = Counter(r for _, r, _ in rp.offers)
    assert all(v == 1 for v in per.values()), per
    for ep in res["epochs"]:
        for rid, t in rp.declined_at.items():
            if ep["tau_s"] > t:
                assert rid not in ep["lyft"]["reads"], (rid, ep["tau_s"])


@pytest.mark.parametrize("name", ALL_RUNS)
def test_06_capacity_precedence_commitment_guardrail_audit(runs, name):
    res = get(runs, name)
    rp, ref = replay(res), ref_for(res)
    for cat in ("capacity", "precedence", "commitment", "execution", "timing"):
        assert not rp.v[cat], (cat, rp.v[cat][:10])
    assert all(ep["audit"].startswith("pass") for ep in res["epochs"])
    # a committed pickup is served by the committing van or ends in cancellation / no-show
    for rid, vid in rp.committed_by.items():
        nxt = [e for e in rp.hist[rid] if e["state_from"] == "committed"]
        assert len(nxt) == 1 and nxt[0]["state_to"] in ("onboard", "noshow_van", "cancel_pending_van"), rid
        if nxt[0]["state_to"] != "cancel_pending_van":
            assert nxt[0]["van"] == vid, rid
    # guardrail on executed van rides; van wait/ride fields
    over = []
    for rid in ref.req:
        h = {e["state_to"]: e for e in rp.hist[rid]}
        if "van_completed" in h:
            pick, drop = h["onboard"]["t_s"], h["van_completed"]["t_s"]
            assert h["onboard"]["wait_s"] == pick - ref.req[rid]["t"]
            assert h["van_completed"]["ride_s"] == drop - pick
            if drop - pick > ref.guardrail(rid):
                over.append((rid, drop - pick, ref.guardrail(rid)))
    assert not over, f"executed van rides over the guardrail: {over}"


@pytest.mark.parametrize("name", ALL_RUNS)
def test_06b_epoch_triggers(runs, name):
    """One epoch per triggered second; Lyft-side events never trigger an epoch (§17.4)."""
    res = get(runs, name)
    ev = res["events"]
    by_t = defaultdict(list)
    for e in ev:
        by_t[e["t_s"]].append(e)
    for ep in res["epochs"]:
        tau, trig = ep["tau_s"], set(ep["triggers"])
        assert trig and trig <= {"tick", "request", "cancellation", "noshow", "van_on_duty"}, (tau, trig)
        rows = [e for e in by_t[tau] if e["class"] < C_EPOCH]
        if "tick" in trig:
            assert tau % res["cfg"].tick_s == 0
        if "request" in trig:
            assert any(e["event"] == "state" and e["state_to"] == "pending_van" for e in rows)
        if "cancellation" in trig:
            assert any(e["event"] == "state" and e["state_to"] == "cancel_pending_van" for e in rows)
        if "noshow" in trig:
            assert any(e["event"] == "state" and e["state_to"] == "noshow_van" for e in rows)
        if "van_on_duty" in trig:
            assert any(e["event"] == "on_duty" for e in rows)
    taus = {ep["tau_s"] for ep in res["epochs"]}
    for e in ev:                                          # every van-side trigger got its epoch (unless the run ended)
        if e["event"] == "state" and e["state_to"] in ("pending_van", "cancel_pending_van", "noshow_van"):
            assert e["t_s"] in taus or e["t_s"] == ev[-1]["t_s"], e


@pytest.mark.parametrize("name", ALL_RUNS)
def test_07_solver_status(runs, name):
    res = get(runs, name)
    st = Counter(ep["solver"]["status"] for ep in res["epochs"])
    assert set(st) <= {"optimal", "empty"}, st
    for ep in res["epochs"]:
        if ep["solver"]["status"] == "empty":
            assert not ep["vans"] or not ep["open"], ep["tau_s"]


def _strip_wall(x):
    if isinstance(x, dict):
        return {k: _strip_wall(v) for k, v in x.items() if k != "wall_s"}
    if isinstance(x, list):
        return [_strip_wall(v) for v in x]
    return x


def test_08_reproducible(runs):
    a, b = get(runs, "L4:R1(10)"), get(runs, "repeat:R1(10)")   # two separate processes (different hash seeds)
    assert a["events"] == b["events"]
    ja = json.dumps(_strip_wall(a["epochs"]), sort_keys=True, default=str)
    jb = json.dumps(_strip_wall(b["epochs"]), sort_keys=True, default=str)
    assert ja == jb
    assert a["outcomes"] == b["outcomes"]


@pytest.mark.parametrize("level", ["L1", "L2", "L3", "L4", "L5/r00"])
def test_09_frozen_inputs_unchanged(level):
    frozen = json.loads((SCEN / "FROZEN_v2.json").read_text())
    assert inputs.content_hash(SCEN / level) == frozen[level]
    folder = SCEN / level
    blob = b"".join((folder / n).read_bytes() for n in ("requests.csv", "latent.csv", "availability.csv"))
    params = json.loads((folder / "scenario.json").read_text())["params"]
    canon = json.dumps(params, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(blob + canon).hexdigest() == frozen[level]


# ---------------------------------------------------------------- controlled cases --------------------------------
def test_10_lyft_paths_cancel_in_lag_after_booking_noshow(runs):
    """(a) cancel during the lag: no booking; (b) cancel after booking before the Lyft arrives: booking counted, no
    pickup; (c) Lyft no-show (standard and XL): booking counted, no-show 180 s after arrival, no completion; plus the
    two same-second ties (deadline = booking time -> cancel, no booking; deadline = Lyft arrival -> boards)."""
    res, base = get(runs, "lyft_paths:R2(15)"), get(runs, "L4:R2(15)")
    rp = replay(res)
    out = {o["request_id"]: o for o in res["outcomes"]}
    h = {rid: [(e["t_s"], e["state_from"], e["state_to"]) for e in rp.hist[rid]] for rid in out}
    ev = {rid: [(e["t_s"], e["event"]) for e in rp.rows[rid] if e["event"] != "state"] for rid in out}
    assert h["R015"][-2:] == [(1200, "pending_van", "xfer_hold"), (1260, "xfer_hold", "cancel_after_transfer")]
    assert out["R015"]["booking_s"] is None and not ev["R015"]
    assert h["R011"][-1] == (1320, "xfer_hold", "cancel_after_transfer") and out["R011"]["booking_s"] is None
    assert h["R016"][-2:] == [(1320, "xfer_hold", "lyft_booked"), (1500, "lyft_booked", "cancel_after_transfer")]
    assert ev["R016"] == [(1800, "lyft_arrive_no_rider")] and out["R016"]["curb_arrival_s"] is None
    assert h["R012"][-2:] == [(1320, "xfer_hold", "lyft_booked"), (1980, "lyft_booked", "noshow_lyft")]
    assert ev["R012"] == [(1800, "lyft_curb_arrival")] and out["R012"]["curb_arrival_s"] == 1800
    assert out["R012"]["pickup_s"] is None and out["R012"]["wait_s"] is None
    assert h["R002"][-1] == (780, "lyft_booked", "noshow_lyft") and out["R002"]["lyft_class"] == "XL"
    assert h["R001"][-2:] == [(600, "lyft_booked", "lyft_onboard"), (897, "lyft_onboard", "lyft_completed")]
    c = lyft_counts(res)
    want = {("offers", "standard"): 12, ("offers", "XL"): 1, ("accepted", "standard"): 11, ("accepted", "XL"): 1,
            ("declined", "standard"): 1, ("bookings", "standard"): 9, ("bookings", "XL"): 1,
            ("cancel_in_lag", "standard"): 2, ("cancel_after_booking", "standard"): 1,
            ("lyft_noshow", "standard"): 1, ("lyft_noshow", "XL"): 1, ("completed", "standard"): 7}
    assert {k: v for k, v in c.items() if v} == want
    # Lyft-side events never touch the vans: the van side is identical to the unmodified run
    def van_side(r):
        return [e for e in r["events"] if e["van"] is not None]
    assert van_side(res) == van_side(base)
    assert [_strip_wall(e["chosen"]) for e in res["epochs"]] == [_strip_wall(e["chosen"]) for e in base["epochs"]]


def test_10b_m2_report_counts_on_controlled_case(runs):
    """sim.m2_report.row on the controlled run: offers, accepted, bookings and completions are reported as different
    numbers (they differ in this case)."""
    import pandas as pd
    from sim import m2_report
    res = get(runs, "lyft_paths:R2(15)")
    run_d = {"rule": res["rule"], "out": pd.DataFrame(res["outcomes"]), "events": pd.DataFrame(res["events"]),
             "epochs": res["epochs"], "manifest": {"wall_s_total": res["wall_s"]}}
    row = m2_report.row(run_d, inputs.load("L4"), inputs.Travel(1.0, 1.0))
    get_ = lambda prefix: next(v for k, v in row.items() if k.startswith(prefix))
    assert get_("Terminal outcomes") == "4 / 7 / 3 / 2"
    assert get_("Rule decisions = offers") == "12 / 1"
    assert get_("Accepted transfers") == "11 / 1"
    assert get_("Bookings placed") == "9 / 1"
    assert get_("Lyft trips completed") == "7 / 0"


@pytest.mark.parametrize("name", ["van_noshow:R2(15)", "van_noshow:R1(10)"])
def test_11_van_noshow_while_rule_active(runs, name):
    """(d) R003 absent at the van curb after 18:15 while the rule acts: during the 180-s timer the plan keeps the
    hypothetical drop-off (P_curb_wait, guardrail from expiry); at expiry an epoch removes it; R003 is never boarded,
    dropped or offered; the van does not leave during the timer."""
    res = get(runs, name)
    rp, ref = replay(res), ref_for(res)
    arr = [e for e in res["events"] if e["event"] == "curb_arrival" and e["request"] == "R003"]
    assert len(arr) == 1 and arr[0]["present"] is False
    a, vid = arr[0]["t_s"], arr[0]["van"]
    exp = a + NOSHOW_WAIT_S
    assert a >= VANS_ON_S
    ns = [e for e in rp.hist["R003"] if e["state_to"] == "noshow_van"]
    assert len(ns) == 1 and ns[0]["t_s"] == exp and ns[0]["van"] == vid
    inside = [ep for ep in res["epochs"] if a < ep["tau_s"] < exp]
    assert inside, "no epoch inside the curb-wait timer: the case does not exercise D-54"
    assert any(ep["lyft"]["reads"] for ep in inside), "rule had nothing to read during the timer"
    for ep in inside:
        v = next(x for x in ep["vans"] if x["van"] == vid)
        assert v["committed"] == ["R003", "P_curb_wait", a], v["committed"]
        assert any(r["rid"] == "R003" and r["pickup_s"] == exp for r in v["riders"])
        seq, arrs = ep["chosen"][vid]["seq"], ep["chosen"][vid]["arrivals_s"]
        assert "D:R003" in seq
        assert arrs[seq.index("D:R003")] - exp <= ref.guardrail("R003")
        assert "R003" not in ep["lyft"]["reads"]
    at = [ep for ep in res["epochs"] if ep["tau_s"] == exp]
    assert at and "noshow" in at[0]["triggers"]
    for ep in res["epochs"]:
        if ep["tau_s"] >= exp:
            pr = ep["lyft"]["plan_read_by_rule"] or {"routes": {}}
            for plan in (ep["chosen"], pr["routes"]):
                assert all("R003" not in s for c in plan.values() for s in c["seq"]), ep["tau_s"]
            assert all(r["rid"] != "R003" for v in ep["vans"] for r in v["riders"])
    states = [e["state_to"] for e in rp.hist["R003"]]
    assert "onboard" not in states and "van_completed" not in states and "xfer_hold" not in states
    assert not [e for e in res["events"] if e["event"] == "depart" and e["request"] == "R003" and e["stop"] == "D"]
    assert not [e for e in res["events"] if e["event"] == "depart" and e["van"] == vid and a <= e["t_s"] < exp]


# ---------------------------------------------------------------- findings (reported, not failures) ---------------
def test_12_findings_report(runs):
    """Per-rule transfers before / at-or-after 18:15, recomputed from events, and the R1u reading. Printed with -s."""
    lines = []
    for r in RULES:
        res = get(runs, f"L4:{r}")
        rp = replay(res)
        xf = [e["t_s"] for rid in rp.hist for e in rp.hist[rid] if e["state_to"] == "xfer_hold"]
        dc = [t for t, _, kind in rp.offers if kind == "declined"]
        out = Counter(o["outcome"] for o in res["outcomes"])
        st = Counter(ep["solver"]["status"] for ep in res["epochs"])
        rc = rule_result(res) if r != "R0" else {"would_fire_on_resolved": [], "exec_only_diff": [],
                                                  "max_unas_after": None}
        lines.append(f"{r:8s} transfers <18:15 {sum(t < VANS_ON_S for t in xf)}  >=18:15 {sum(t >= VANS_ON_S for t in xf)}"
                     f"  declines {len(dc)}  outcomes {dict(out)}  epochs {len(res['epochs'])} {dict(st)}"
                     f"  would-fire-on-resolved {len(rc['would_fire_on_resolved'])}"
                     f"  R1u exec-only-diff {len(rc['exec_only_diff'])}  max-unassigned>=18:15 {rc['max_unas_after']}"
                     f"  wall {res['wall_s']:.1f}s")
        # the outcomes table agrees with the events on the split
        o_xf = [o["transfer_s"] for o in res["outcomes"] if o["transfer_s"] is not None]
        assert sorted(o_xf) == sorted(xf)
    print("\n" + "\n".join(lines))
    r1u = rule_result(get(runs, "L4:R1u(10)"))
    assert r1u["max_unas_after"] < 600            # explains "no R1u transfer after 18:15" (finding, consistent)


@pytest.mark.parametrize("rule", RULES)
def test_13_outputs_on_disk_match_in_memory(runs, rule):
    """Read-only: the M2 report reads outputs/sim/L4_<rule>/; check those files match the current code's run."""
    import pandas as pd
    d = ROOT / "outputs" / "sim" / RUN.run_name("L4", rule)
    if not (d / "outcomes.csv").exists():
        pytest.skip(f"{d} not present")
    res = get(runs, f"L4:{rule}")
    mem = pd.read_csv(io.StringIO(pd.DataFrame(res["outcomes"]).to_csv(index=False)))
    pd.testing.assert_frame_equal(pd.read_csv(d / "outcomes.csv"), mem)
    mem_ev = pd.read_csv(io.StringIO(pd.DataFrame(res["events"]).to_csv(index=False)))
    pd.testing.assert_frame_equal(pd.read_csv(d / "events.csv"), mem_ev)
