"""L5 engineering pilot (D-56): checks and descriptive measures for L5/r00 under R0 and R2(15).

    cd src && for r in R0 "R2(15)"; do ../.venv/bin/python -m sim.run --level L5/r00 --rule "$r"; done
    ../.venv/bin/python -m sim.l5_pilot

Writes outputs/sim/l5_pilot_report.md. Descriptive only: no statistical margins, no ranking of rules.
"""
import json

import pandas as pd

from . import dispatch as D
from . import engine as E
from . import inputs
from .m2_report import row
from .run import OUT, policy_for, run_name

RULES = ("R0", "R2(15)")
LEVEL = "L5/r00"


def load(rule):
    d = OUT / run_name(LEVEL, rule)
    return {"rule": rule, "out": pd.read_csv(d / "outcomes.csv"), "events": pd.read_csv(d / "events.csv"),
            "epochs": [json.loads(x) for x in open(d / "epochs.jsonl")],
            "manifest": json.loads((d / "run_manifest.json").read_text())}


def checks(run, scen, travel, p_absent):
    o, ev, eps = run["out"], run["events"], run["epochs"]
    h = scen.hidden
    res = {}
    res["inputs match FROZEN_v2.json"] = run["manifest"]["content_hash"] == inputs.frozen_hashes()[LEVEL]
    res["one terminal outcome per request"] = len(o) == len(scen.requests) and o.outcome.isin(E.TERMINAL).all()
    res["backlog resolved after arrivals end (last request ≤ 3600 s)"] = bool(o.t_request_s.max() < 3600 and
                                                                             run["manifest"]["end_s"] >= o[["drop_s", "cancel_s", "noshow_s"]].max().max())
    # patience: every cancellation happens exactly at request + patience, before any vehicle reached the curb
    c = o[o.outcome.str.startswith("cancel")]
    res["cancellations at request + patience, before any curb arrival"] = all(
        x.cancel_s == x.t_request_s + h[x.request_id].patience_s and (pd.isna(x.curb_arrival_s) or x.curb_arrival_s > x.cancel_s)
        for _, x in c.iterrows())
    # presence: a rider reached by a vehicle is a no-show iff its shared draw is below p
    reached = o[o.curb_arrival_s.notna()]
    res["no-show iff presence draw < p at the first curb arrival"] = all(
        (x.outcome.startswith("noshow")) == (h[x.request_id].noshow_u < p_absent) for _, x in reached.iterrows())
    res["no-show recorded 180 s after curb arrival"] = all(
        x.noshow_s == x.curb_arrival_s + 180 for _, x in o[o.outcome.str.startswith("noshow")].iterrows())
    # Lyft reconciliation, per class
    ok = True
    for cls in ("standard", "XL"):
        t = o[o.lyft_class == cls]
        booked = t[t.booking_s.notna()]
        lag_cancel = t[(t.outcome == "cancel_after_transfer") & t.booking_s.isna()]
        ok &= len(t) == len(booked) + len(lag_cancel)
        ok &= len(booked) == ((booked.outcome == "lyft_completed") | (booked.outcome == "noshow_lyft")
                              | (booked.outcome == "cancel_after_transfer")).sum()
        ok &= (t.booking_s.dropna() == t.transfer_s[t.booking_s.notna()] + 120).all()
    ok &= (o[o.party == 5].lyft_class.dropna() == "XL").all() and (o[o.party <= 4].lyft_class.dropna() == "standard").all()
    res["transfers = bookings + lag cancellations; bookings = completions + Lyft no-shows + later cancellations (per class)"] = bool(ok)
    # no request in a van plan while in a Lyft state, and no transferred rider ever boards a van
    lyft_rids = set(o.request_id[o.transfer_s.notna()])
    van_board = set(ev.request[(ev.event == "state") & (ev.state_to == "onboard")])
    res["no transferred rider boards a van"] = not (lyft_rids & van_board)
    res["plan audit passed every epoch (capacity, precedence, one van per request, guardrail, transfer invariant)"] = all(
        e["audit"].startswith("pass") for e in eps)
    committed = ev[(ev.event == "state") & (ev.state_to == "committed")]
    res["every committed pickup served by its van or ended by cancellation/no-show"] = all(
        (o.set_index("request_id").loc[r.request, "van"] == r.van) for _, r in committed.iterrows())
    g = {r.rid: D.guardrail_s(travel.van(r.o, r.d), D.Config()) for r in scen.requests}
    vc = o[o.outcome == "van_completed"]
    res["no van ride over the guardrail"] = all(x.ride_s <= g[x.request_id] for _, x in vc.iterrows())
    res["every epoch proven optimal over its candidate set"] = all(e["solver"]["status"] in ("optimal", "empty") for e in eps)
    return res


def reproduce(rule, scen, travel):
    """Re-run in memory and compare with the saved events.csv byte for byte (written the same way as sim.run)."""
    a = E.Engine(scen, travel, policy_for(scen, rule)).run()
    saved = (OUT / run_name(LEVEL, rule) / "events.csv").read_text()
    return pd.DataFrame(a.events).to_csv(index=False) == saved


def main():
    scen = inputs.load(LEVEL)
    m = scen.params["travel_multiplier"]
    travel = inputs.Travel(m, m)
    runs = {r: load(r) for r in RULES}
    pol = policy_for(scen, "R0")
    L = ["# L5 engineering pilot: L5/r00 under R0 and R2(15)", "",
         f"Settings (D-56; identical in both arms except the rule): dispatcher C, K = 3, pending price A, curb-wait D-54, "
         f"lag {pol.lag_s} s, consent {pol.consent_p}, presence p = {pol.p_absent} (provisional), travel multiplier {m}; "
         "frozen patience, presence draws and Lyft delays unchanged; the frozen `p_noshow` is not read. "
         "Descriptive measures from one 28-request night; they do not rank the rules.", "",
         "## Checks", "", "| Check | " + " | ".join(RULES) + " |", "|---|" + "---|" * len(RULES)]
    cs = {r: checks(runs[r], scen, travel, pol.p_absent) for r in RULES}
    for r in RULES:
        cs[r]["re-run reproduces events.csv"] = reproduce(r, scen, inputs.Travel(m, m))
    for k in cs["R0"]:
        L.append(f"| {k} | " + " | ".join("pass" if cs[r][k] else "**FAIL**" for r in RULES) + " |")
    same_hidden = runs["R0"]["manifest"]["content_hash"] == runs["R2(15)"]["manifest"]["content_hash"]
    L += ["", f"Both arms read identical inputs and hidden draws (same content hash, which covers `latent.csv`): "
              f"{'yes' if same_hidden else 'NO'}.", "",
          "## Descriptive measures", "", "| Measure | " + " | ".join(RULES) + " |", "|---|" + "---|" * len(RULES)]
    rows = {r: row(runs[r], scen, travel) for r in RULES}
    n, pax = len(runs["R0"]["out"]), int(runs["R0"]["out"].party.sum())
    for k in rows["R0"]:
        if "18:15" in k:                                    # L4-specific (vans on duty from 18:15); not meaningful here
            continue
        label = (k.replace("(16 requests)", f"({n} requests)").replace("all 16 requests", f"all {n} requests")
                 .replace("p_c = 0.9", f"p_c = {pol.consent_p}"))
        L.append(f"| {label} | " + " | ".join(rows[r][k] for r in RULES) + " |")
    L.append(f"\nDenominators: {n} requests and {pax} passengers in total; wait measures count those picked up (n shown).")
    for r in RULES:
        ties = pd.Series([e["solver"]["tie_status"] for e in runs[r]["epochs"]]).value_counts().to_dict()
        L.append("")
        L.append(f"{r}: tie handling per epoch: " + ", ".join(f"{k} {v}" for k, v in ties.items()) + ".")
    path = OUT / "l5_pilot_report.md"
    path.write_text("\n".join(L) + "\n")
    print(f"wrote {path}")
    return all(all(v for v in c.values()) for c in cs.values())


if __name__ == "__main__":
    ok = main()
    print("all checks pass" if ok else "SOME CHECKS FAIL")
