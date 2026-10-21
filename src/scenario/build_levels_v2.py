"""
Build the validation levels L1-L5 (scenario_spec v0.2 §8) and the L1-L4 hand-check sheets.

    data/scenarios/v2/MANIFEST.json                 fingerprints of every routing/data input
    data/scenarios/v2/L1..L4/                       requests, latent, availability, scenario.json,
                                                    handcheck.csv + HANDCHECK.md
    data/scenarios/v2/L5/r00..r29/                  30 paired nights (random latent draws)
    data/scenarios/v2/FROZEN_v2.json                content hash of every scenario

Run: .venv/bin/python src/scenario/build_levels_v2.py
"""
import json

import pandas as pd

try:
    from . import generator_v2 as g
except ImportError:
    import generator_v2 as g

HANDCHECK_RULES = """## How to check it by hand
All times are seconds after 18:00. Travel times come from `tt_locations_v2.csv` (multiplier 1.0 at L1–L4), rounded to whole seconds. Dwell is 30 s at every pickup and drop-off.

**The design.** Each request arrives only when **both vans are idle**, so the dispatcher faces a single open request.
- It sends the van with the lower cost, ties going to V1. Cost = party × φ(deadhead wait) + 0.5 × party × ride minutes + 0.1 × km.
  - φ is the convex wait penalty: slopes per minute of 1, 2.5, 5, 10 and 20, changing at 5, 10, 15 and 20 minutes (D-29).
- The van departs at the request time. Its next stop is the pickup, which is committed, so no re-plan or 2-minute tick can move the ride.

**Per row:**
- `pickup_arrival_s` = `t_request_s` + T(`van_from`, `o_loc`). Wait = pickup arrival − request time.
- Completed: `dropoff_s` = pickup + 30 + T(`o_loc`, `d_loc`). The van is free at the drop-off point 30 s later.
- No-show (L2): the van waits 180 s at the curb, then the request ends as `noshow_van`. The van is free at the pickup point.
- Cancel (L3): the rider cancels at request + `patience_s` while the van is still driving. The van does not divert mid-street (P-05): it finishes the drive to the pickup point and is free there on arrival.

The Phase 4 simulator must reproduce every `outcome`, `van`, `pickup_s`, `dropoff_s` and `event_s` here **to the second**.
"""


def handcheck_md(level, rows, extra):
    first = rows[0]
    lines = [f"# Hand-check sheet: {level}", "", extra, "", HANDCHECK_RULES, "## Worked example (first request)",
             f"- {first['request_id']}, requested at {first['t_request_s']} s, party {first['party']}, "
             f"{first['o_loc']} → {first['d_loc']}.",
             f"- Both vans are at the depot `{g.DEPOT}`. Cost V1 = {first['cost_V1']}, V2 = {first['cost_V2']}: "
             f"**{first['van']}** goes (equal costs go to V1).",
             f"- Deadhead T(depot, origin) = {first['deadhead_s']} s, so the pickup is at {first['pickup_arrival_s']} s "
             f"and the wait is {first['deadhead_s']} s.",
             (f"- Ride = 30 + T(origin, destination) = {first.get('ride_s')} s, so the drop-off is at {first.get('dropoff_s')} s."
              if first["outcome"] == "van_completed" else f"- Outcome: {first['outcome']}."),
             "", "## Summary",
             f"- Requests: {len(rows)}; outcomes: "
             + ", ".join(f"{k} {v}" for k, v in pd.Series([r['outcome'] for r in rows]).value_counts().items()),
             f"- Last event at {max(r['event_s'] for r in rows)} s "
             f"({max(r['event_s'] for r in rows) / 60:.0f} min after 18:00)."]
    return "\n".join(lines) + "\n"


def main():
    g.OUT.mkdir(parents=True, exist_ok=True)
    g.manifest()
    frozen = {}

    # L1-L3: shared requests
    req, rows, patience, noshow_idx = g.build_l1_to_l3()
    end = max(r["van_free_s"] for lv in rows for r in rows[lv]) + 3600
    for lv, extra, lat in (
        ("L1", "**L1:** 16 requests, 2 vans, nothing goes wrong. It tests the engine, the dispatcher and the accounting.",
         g._latent_designed(req)),
        ("L2", "**L2:** the same 16 requests; **R005 and R011 do not show** (`noshow_u` = 0 < 0.047).",
         g._latent_designed(req, noshow_idx=noshow_idx)),
        ("L3", "**L3:** the same 16 requests; the designed riders (`patience_s` below 10 h) **cancel while the van is on its way**.",
         g._latent_designed(req, patience=patience))):
        params = {"level": lv, "pattern": "base", "replicate": 0, "n_requests": len(req), "n_vans": 2,
                  "capacity": g.CAPACITY, "travel_multiplier": 1.0, "dwell_s": g.DWELL_S,
                  "noshow_wait_s": g.NOSHOW_WAIT_S, "max_direct_s": 480, "lyft": "none at this level",
                  "design": "requests arrive only when both vans are idle (hand-checkable)"}
        sc = g.write_scenario(g.OUT / lv, req, lat, g._availability(2, 0, end), params)
        hc = pd.DataFrame(rows[lv])
        hc.to_csv(g.OUT / lv / "handcheck.csv", index=False, lineterminator="\n")
        (g.OUT / lv / "HANDCHECK.md").write_text(handcheck_md(lv, rows[lv], extra))
        frozen[lv] = sc["content_hash"]

    # L4: Lyft bookkeeping
    req4, lat4, hc4, info = g.build_l4()
    params = {"level": "L4", "pattern": "base", "replicate": 0, "n_requests": len(req4), "n_vans": 2,
              "capacity": g.CAPACITY, "travel_multiplier": 1.0, "dwell_s": g.DWELL_S, "vans_on_duty_from_s": g.L4_VANS_FROM_S,
              "lyft_lag_s": g.L4_LAG_S, "lyft_delay_s": g.L4_LYFT_DELAY_S, "consent_p": g.L4_CONSENT_P,
              "rules": list(g.L4_RULES), "max_direct_s": 480}
    sc = g.write_scenario(g.OUT / "L4", req4, lat4, g._availability(2, g.L4_VANS_FROM_S, 4 * 3600), params)
    hc4.to_csv(g.OUT / "L4" / "handcheck.csv", index=False, lineterminator="\n")
    tr = hc4[hc4.decision == "transfer"]
    md = [
        "# Hand-check sheet: L4 (Lyft bookkeeping)", "",
        f"16 requests between 18:00 and 18:20. **The 2 vans come on duty only at {g.L4_VANS_FROM_S} s (18:15)**, so "
        "until then every request is pending with no van. That makes each rule's early decisions traceable by hand.",
        "",
        f"- **Fixed:** dispatcher lag {g.L4_LAG_S} s; Lyft delay {g.L4_LYFT_DELAY_S} s; consent probability {g.L4_CONSENT_P}; "
        "no cancellations; no no-shows.",
        f"- **Designed riders:** {info['party5']} is a **party of 5**: it is Lyft-eligible through a larger vehicle "
        "(Lyft XL), and the party stays together (decision D-33, a user-supplied operational correction of 21 Oct 2026; "
        "it replaces the 2018 rule that 5+ riders always got a van, which referred to standard 4-seat Lyft cars). "
        "XL pickup delay is assumed equal to the standard Lyft delay here. "
        f"{info['decliner']} **declines** the Lyft offer (`consent_u` 0.95 > 0.9) and is not asked again.",
        "- **Decision epochs before 18:15:** every 120-s tick plus every request arrival: "
        f"{info['epochs_s']}. Each rule is evaluated after every re-plan.",
        "- **When each rule fires:**",
        "  - **R1(θ) and R1u(10):** at the first epoch ≥ request + θ. Before 18:15 nobody has a van, so 'elapsed' and "
        "'elapsed unassigned' coincide.",
        "  - **R2(15) and R3(2):** with no van available, the predicted van pickup is infinite (the dispatcher is "
        "assumed not to plan for vans that are not yet on duty), so they fire at the request itself.",
        "- **For each transfer:** Lyft requested = decision + 120. Lyft pickup = decision + 120 + 480. "
        "**Wait = Lyft pickup − original request time; the clock is not reset.** Drop-off = pickup + 30 + T(o, d). "
        "A transfer is not a completion: the outcome becomes `lyft_completed` only at the Lyft drop-off.",
        "- **Not hand-checked:** decisions that fall at or after 18:15 depend on the van dispatcher. "
        "The simulator must still satisfy the same identities for them.",
        "", "## Transfers that can be checked by hand",
        f"{len(tr)} transfer decisions across the five active rules:",
        tr.groupby('rule').size().to_string(), "",
        "## Identities that must hold in every rule",
        "1. Requests = the sum of terminal states.",
        "2. Each transferred rider's wait = Lyft pickup − request time.",
        "3. A transferred party of 5 rides one XL vehicle (`lyft_class` = XL) and is never split.",
        "4. A rider who declined is never transferred later.",
    ]
    (g.OUT / "L4" / "HANDCHECK.md").write_text("\n".join(md) + "\n")
    frozen["L4"] = sc["content_hash"]

    # L5: 30 paired nights
    for r in range(30):
        req5, lat5, av5 = g.build_l5(r)
        params = {"level": "L5", "pattern": "base", "replicate": r, "n_requests": len(req5), "n_vans": 2,
                  "capacity": g.CAPACITY, "travel_multiplier": 1.2, "dwell_s": g.DWELL_S, "window_s": g.L5_WINDOW_S,
                  "burst": {"from_s": g.L5_BURST[0], "to_s": g.L5_BURST[1], "share": g.L5_BURST[2]},
                  "patience": {"dist": "weibull", "shape": 1.5, "median_s": 1080},
                  "lyft_delay": {"dist": "lognormal", "median_s": 480, "p90_s": 900}, "p_noshow": g.P_NOSHOW}
        sc = g.write_scenario(g.OUT / "L5" / f"r{r:02d}", req5, lat5, av5, params)
        frozen[f"L5/r{r:02d}"] = sc["content_hash"]

    (g.OUT / "FROZEN_v2.json").write_text(json.dumps(frozen, indent=2) + "\n")
    print(f"built {len(frozen)} scenarios; L1 last event {max(r['event_s'] for r in rows['L1'])} s")


if __name__ == "__main__":
    main()
