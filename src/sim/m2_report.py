"""M2 report: Lyft rules interacting with dispatcher C over the whole L4 evening (one run per rule).

    cd src && for r in R0 "R1(10)" "R1(15)" "R1u(10)" "R2(15)" "R3(2)"; do ../.venv/bin/python -m sim.run --level L4 --rule "$r"; done
    ../.venv/bin/python -m sim.m2_report

Reads outputs/sim/L4_<rule>/ and writes outputs/sim/m2_L4_report.md. An integration demonstration on one designed
evening (16 requests): it shows that the pieces work together and are accounted for once; it does not rank rules.
"""
import json

import numpy as np
import pandas as pd

from . import dispatch as D
from . import inputs, lyft
from .run import OUT, _mmss, clock, rule_tag, run_name

RULES = list(lyft.RULES)


def load(rule):
    d = OUT / run_name("L4", rule)
    return {"rule": rule, "dir": d, "out": pd.read_csv(d / "outcomes.csv"), "events": pd.read_csv(d / "events.csv"),
            "epochs": [json.loads(x) for x in open(d / "epochs.jsonl")],
            "manifest": json.loads((d / "run_manifest.json").read_text())}


def van_km(events, travel):
    dep = events[events.event == "depart"]
    return sum(travel.dm(a, b) for a, b in zip(dep.frm, dep.to)) / 10_000


def row(run, scen, travel):
    o, ev, eps = run["out"], run["events"], run["epochs"]
    n, pax = len(o), int(o.party.sum())
    picked = o[o.pickup_s.notna()]
    w = picked.wait_s / 60
    wp = np.repeat(w.to_numpy(), picked.party.to_numpy())
    reached15 = ((o.curb_arrival_s - o.t_request_s) <= 900).fillna(False)
    trans = o[o.transfer_s.notna()]
    booked = o[o.booking_s.notna()]
    lyc = o[o.outcome == "lyft_completed"]
    g = {r.rid: D.guardrail_s(travel.van(r.o, r.d), D.Config()) for r in scen.requests}
    vanc = o[o.outcome == "van_completed"]
    viol = int(sum(1 for _, x in vanc.iterrows() if x.ride_s > g[x.request_id]))
    st = pd.Series([e["solver"]["status"] for e in eps]).value_counts().to_dict()
    def cls(df):
        return f"{(df.lyft_class == 'standard').sum()} / {(df.lyft_class == 'XL').sum()}"
    return {
        "Terminal outcomes (16 requests): van completed / Lyft completed / cancelled / no-show":
            f"{(o.outcome == 'van_completed').sum()} / {(o.outcome == 'lyft_completed').sum()} / "
            f"{o.outcome.str.startswith('cancel').sum()} / {o.outcome.str.startswith('noshow').sum()}",
        "Rule decisions = offers (p_c = 0.9): accepted / declined": f"{len(trans)} / {o.declined_s.notna().sum()}",
        "Accepted transfers, standard / XL": cls(trans),
        "Bookings placed (after the 2-min lag), standard / XL": cls(booked),
        "Lyft trips completed, standard / XL": cls(lyc),
        "Cancelled after transfer: during the lag (no booking) / after booking": f"{(o.outcome.eq('cancel_after_transfer') & o.booking_s.isna()).sum()} / {(o.outcome.eq('cancel_after_transfer') & o.booking_s.notna()).sum()}",
        "Lyft no-shows, standard / XL": cls(o[o.outcome == "noshow_lyft"]),
        "Transfers decided before / at-or-after 18:15": f"{(trans.transfer_s < 900).sum()} / {(trans.transfer_s >= 900).sum()}",
        "Request-weighted wait to pickup, either mode: median / P90 / max, min (n = requests picked up)":
            f"{w.median():.1f} / {w.quantile(.9):.1f} / {w.max():.1f} (n={len(w)})",
        "Share of all 16 requests reached by a vehicle within 15 min": f"{reached15.mean():.0%} ({int(reached15.sum())}/{n})",
        "Passenger-weighted wait: median / P90, min (n = passengers picked up)":
            f"{np.median(wp):.1f} / {np.quantile(wp, .9):.1f} (n={len(wp)} of {pax})",
        "Van riders: ride P90 / max, min; guardrail violations": f"{(vanc.ride_s / 60).quantile(.9):.1f} / {(vanc.ride_s / 60).max():.1f}; {viol}",
        "Van-km driven": f"{van_km(ev, travel):.1f}",
        "Last drop-off (clock)": clock(o.drop_s.max()),
        "Epochs; solver status": f"{len(eps)}; " + ", ".join(f"{k} {v}" for k, v in st.items()),
        "Epochs with a re-solve after transfers": str(sum(1 for e in eps if e["lyft"].get("resolved_after_transfer"))),
        "Run wall time, s": f"{run['manifest']['wall_s_total']:.1f}",
    }


def timeline(run, rid, scen):
    ev = run["events"]
    r = next(x for x in scen.requests if x.rid == rid)
    L = [f"### One request's complete timeline: {rid} under {run['rule']} (party {r.q}, requested {clock(r.t)})", ""]
    for _, e in ev[ev.request == rid].iterrows():
        what = e.event
        if e.event == "state":
            what = f"{e.state_from} → {e.state_to}"
            if e.state_to == "xfer_hold":
                what += f" (transfer decided; {e.lyft_class}; leaves van planning now)"
            elif e.state_to == "lyft_booked":
                what += " (booking placed after the 2-min dispatcher lag)"
            elif e.state_to == "lyft_onboard":
                what += f" (Lyft at the curb, rider boards; wait {_mmss(e.wait_s)} counted from the original request)"
            elif e.state_to == "lyft_completed":
                what += f" (drop-off; ride {_mmss(e.ride_s)})"
            elif e.state_to == "onboard":
                what += f" (van {e.van} at the curb; wait {_mmss(e.wait_s)})"
            elif e.state_to == "van_completed":
                what += f" (van {e.van} drop-off; ride {_mmss(e.ride_s)})"
        elif e.event == "depart":
            what = f"van {e.van} departs toward this {'pickup' if e.stop == 'P' else 'drop-off'}, arrives {clock(e.arrive_s)}"
        L.append(f"- {clock(e.t_s)} — {what}")
    plans = []
    for ep in run["epochs"]:
        pr = ep["predicted_pickup_s"].get(rid)
        pend = rid in ep["pending"]
        if any(o["rid"] == rid for o in ep["open"]):
            src = (f"van ETA {clock(pr)}" if pr is not None else
                   f"pending (tentative ETA {clock(ep['pending'][rid]['tentative_eta_s'])})" if pend else "—")
            plans.append(f"{clock(ep['tau_s'])}: {src}")
    if plans:
        L += ["", "What the dispatcher's plan said about it at each epoch while it was open: " + "; ".join(plans) + "."]
    return "\n".join(L)


def transfer_epoch(run, scen):
    """The first epoch at or after 18:15 with a transfer: plan read by the rule, the trigger, the decision, the
    re-solved plan."""
    ep = next((e for e in run["epochs"] if e["tau_s"] >= 900 and e["lyft"]["transfers"]), None)
    if ep is None:
        return None
    pr = ep["lyft"]["plan_read_by_rule"]
    rid = ep["lyft"]["transfers"][0]
    read = ep["lyft"]["reads"][rid]
    spec = lyft.RULES[run["rule"]]
    L = [f"### One epoch: {run['rule']} at {clock(ep['tau_s'])} (trigger: {', '.join(ep['triggers'])})", "",
         "**1. The plan the rule read** (solved first, before any transfer):", ""]
    for v, r in pr["routes"].items():
        stops = ", ".join(f"{s} {clock(a)}" for s, a in zip(r["seq"], r["arrivals_s"])) or "(nothing new)"
        L.append(f"- {v}: {stops}")
    if pr["pending"]:
        L.append("- pending: " + "; ".join(
            f"{k} (tentative ETA {clock(i['tentative_eta_s'])}, pending price {i['pending_price_u'] / D.PT:.1f} pts, "
            f"earliest physical pickup {clock(i['earliest_pickup_s'])})" for k, i in pr["pending"].items()))
    t_r = ep["tau_s"] - read["elapsed_s"]
    pred = read["predicted_pickup_s"]
    test = {"elapsed": f"waited {_mmss(read['elapsed_s'])} ≥ {spec[1] // 60}:00",
            "unassigned": f"unassigned since {clock(read['unassigned_since_s'])}, ≥ {spec[1] // 60}:00",
            "predicted": f"predicted total wait {_mmss(pred - t_r)} > {spec[1] // 60}:00" if pred is not None else "no feasible van (infinite)",
            "van_vs_lyft": f"predicted pickup {_mmss(pred - ep['tau_s'])} from now > lag 2:00 + typical Lyft 8:00 + margin "
                           f"{spec[1] // 60}:00" if pred is not None else "no feasible van (infinite)"}[spec[0]]
    L += ["", f"**2. The rule's reading of {rid}** (requested {clock(t_r)}): predicted pickup {clock(pred)} "
          f"({read['source']}); test for {run['rule']}: {test} → fires. The predicted pickup is the dispatcher's "
          "current estimate, not a promise; for a pending request it is the tentative ETA, which is distinct from the "
          "pending price A that the MILP charged.", "",
          f"**3. Decision:** transfers {', '.join(ep['lyft']['transfers'])}"
          + (f"; declines {', '.join(ep['lyft']['declines'])}" if ep["lyft"]["declines"] else "")
          + ". Each accepted rider leaves van planning at once (state xfer_hold); its booking follows after the lag.", "",
          "**4. The re-solved van plan** (executed this second):", ""]
    for v, c in ep["chosen"].items():
        stops = ", ".join(f"{s} {clock(a)}" for s, a in zip(c["seq"], c["arrivals_s"])) or "(nothing new)"
        L.append(f"- {v}: {stops}")
    if ep["pending"]:
        L.append("- pending: " + ", ".join(ep["pending"]))
    def stops(routes):
        return {st: a for r in routes.values() for st, a in zip(r["seq"], r["arrivals_s"])}
    sb, sa = stops(pr["routes"]), stops(ep["chosen"])
    moved = [(st, sb[st], sa[st]) for st in sa if st in sb and sa[st] != sb[st]]
    if moved:
        L += ["", "**5. What changed for riders who stay with the vans** (same stops, re-solved times): " + "; ".join(
            f"{'pickup' if st.startswith('P') else 'drop-off'} of {st[2:]} {clock(b)} → {clock(a)}"
            for st, b, a in moved) + ". These are planned times at this epoch, not promises."]
    before, after = pr["predicted_pickup_s"], ep["predicted_pickup_s"]
    newly = [k for k in after if k not in before]
    if newly:
        L += ["", "Requests that were pending in the plan the rule read and now have a van: " + ", ".join(newly) + "."]
    return "\n".join(L)


def main():
    scen = inputs.load("L4")
    travel = inputs.Travel(1.0, 1.0)
    runs = {r: load(r) for r in RULES}
    rows = {r: row(runs[r], scen, travel) for r in RULES}
    keys = list(rows["R0"])
    L = ["# M2: Lyft rules with dispatcher C over the whole L4 evening", "",
         "Each column is a separate run of the same frozen L4 inputs (16 requests, 29 passengers; vans on duty from "
         "18:15; dispatcher lag 2 min; Lyft delay 8 min; consent probability 0.9) with dispatcher C (K = 3, pending "
         "price A, curb-wait convention D-54). Only the Lyft rule differs, and it acts at every epoch. These are "
         "**simulated outcomes of one designed integration evening**: they show that the pieces work together and that "
         "every rider and booking is accounted for once. They do **not** rank the rules.", "",
         "| Measure | " + " | ".join(RULES) + " |", "|---|" + "---|" * len(RULES)]
    for k in keys:
        L.append(f"| {k} | " + " | ".join(rows[r][k] for r in RULES) + " |")
    L += ["", "Denominators: request-weighted measures count requests (16 in total, or those picked up, as stated); "
          "passenger-weighted measures count passengers (29 in total). \"Reached within 15 min\" counts every request, "
          "including any not reached. Waits run from the original request to the pickup in either mode.", ""]
    # narrative pieces
    pick = None
    for r in ("R2(15)", "R3(2)", "R1(10)", "R1u(10)", "R1(15)"):
        ep = next((e for e in runs[r]["epochs"] if e["tau_s"] >= 900 and e["lyft"]["transfers"]), None)
        if ep:
            pick = (r, ep["lyft"]["transfers"][0])
            break
    L += ["## How a transfer works, end to end", ""]
    if pick:
        L += [transfer_epoch(runs[pick[0]], scen), "", timeline(runs[pick[0]], pick[1], scen), ""]
    else:
        L += ["No rule transferred anyone at or after 18:15 in this evening.", ""]
    # riders who stayed on vans
    base = runs["R0"]["out"].set_index("request_id")
    L += ["## What changed for riders who stayed on the vans (difference from the R0 run)", "",
          "Each rule's run evolves from its own decisions, so a difference is the joint effect of all its transfers on "
          "the whole evening, not the effect of one transfer.", "",
          "| Rule | Riders on vans in both runs | Waits shorter / longer / same | Largest change |", "|---|---|---|---|"]
    for r in RULES[1:]:
        o = runs[r]["out"].set_index("request_id")
        both = [k for k in o.index if o.loc[k, "outcome"] == "van_completed" and base.loc[k, "outcome"] == "van_completed"]
        d = {k: (o.loc[k, "wait_s"] - base.loc[k, "wait_s"]) / 60 for k in both}
        if not d:
            L.append(f"| {r} | 0 | — | — |")
            continue
        k = max(d, key=lambda x: abs(d[x]))
        L.append(f"| {r} | {len(both)} | {sum(v < 0 for v in d.values())} / {sum(v > 0 for v in d.values())} / "
                 f"{sum(v == 0 for v in d.values())} | {k}: {_mmss(base.loc[k, 'wait_s'])} → {_mmss(o.loc[k, 'wait_s'])} |")
    L += ["", "## Behaviour worth knowing (from the logs; thresholds unchanged)", "",
          "- **R1u(10) transfers nobody after 18:15.** It fires only for a request *continuously without an assigned van* "
          "for 10 minutes. Once the vans are on duty, C puts every waiting request into some van's plan within at most "
          "4 minutes (logged), even when that van's ETA is far away, so the condition never holds again. Its 3 transfers "
          "all happen before 18:15, when no van exists. The rule measures assignment, not waiting.",
          "- **R1(15) acts exactly at 18:15**, when R001 and R002 reach 15 minutes at the very epoch the vans come on duty: "
          "the plan the rule read had already given R001 a van; the transfer removed it and the re-solve re-planned.",
          "- **R2(15) and R3(2) are similar, not identical.** They make the same transfers until 18:17, when R3 transfers "
          "R011 (pickup predicted 13.1 min away, more than its 12-min bar) while R2 transfers it at 18:20 (predicted total "
          "wait 18.8 min). Their summary rows coincide partly by chance on this small evening.",
          "- **Elapsed-time rules can send a rider to Lyft whose van was predicted sooner.** R1(15) transfers R001 at 18:15 "
          "although its van ETA was 18:17:44 and the Lyft arrives at 18:25 (the independent check counts seven such R1 "
          "transfers). That is what a rule based only on time waited does; it is not a defect.",
          "- Two epochs are labelled `empty` under R2 and R3: at 18:00 both requests were transferred before any van "
          "existed, so the re-solve had nothing to decide.", ""]
    L += ["## Files", "",
          "- Per run: `outputs/sim/L4_<rule>/` with `narrative.md` (readable), `events.csv` (every event), "
          "`epochs.jsonl` (every epoch: observable state, candidates, chosen plan, pending prices and tentative ETAs, "
          "solver status, the plan the Lyft rule read and whether a re-solve followed), `outcomes.csv`, `run_manifest.json`.",
          "- Folder names: R1(10) → `L4_R1-10`, R1u(10) → `L4_R1u-10`, and so on."]
    path = OUT / "m2_L4_report.md"
    path.write_text("\n".join(L) + "\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
