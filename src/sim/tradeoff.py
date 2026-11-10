"""Descriptive service-versus-Lyft-use trade-off over the saved L5 batch (no new simulation).

    cd src && ../.venv/bin/python -m sim.tradeoff

Reads outputs/sim/batch_L5_v1/per_night_metrics.csv (30 synthetic nights replayed under six rules) and writes
tradeoff_rule_summary.csv, tradeoff_per_night.csv and tradeoff.md next to it.

Objectives (stated explicitly; both descriptive):
    service  S = share of ALL requests reached by a vehicle (curb arrival) within 15 min   -> larger is better
    Lyft use B = Lyft bookings per night (standard + XL)                                    -> smaller is better
A rule P dominates Q when S_P >= S_Q and B_P <= B_Q with at least one strict. "Nondominated among the six tested
rules" is not a Pareto frontier of all possible policies, not a recommendation, and carries no statistical margin
(D-50 is unresolved). Van-km is reported as a second resource, used only in the three-objective check.
"""
from pathlib import Path

import pandas as pd

from .run import OUT

BATCH = OUT / "batch_L5_v1"
RULE_ORDER = ["R0", "R1(10)", "R1(15)", "R1u(10)", "R2(15)", "R3(2)"]
LABEL = {"R0": "Never transfer", "R1(10)": "Transfer after 10 min waited", "R1(15)": "Transfer after 15 min waited",
         "R1u(10)": "Transfer after 10 min with no van assigned", "R2(15)": "Transfer if predicted total wait > 15 min",
         "R3(2)": "Transfer if the van is predicted later than a Lyft (+2 min)"}


def dominates(p, q, keys):
    """p dominates q: no worse on every objective, strictly better on one. keys: [(column, 'max'|'min')]."""
    ge = all((p[c] >= q[c]) if s == "max" else (p[c] <= q[c]) for c, s in keys)
    gt = any((p[c] > q[c]) if s == "max" else (p[c] < q[c]) for c, s in keys)
    return ge and gt


def nondominated(df, keys):
    return [i for i, p in df.iterrows() if not any(dominates(q, p, keys) for j, q in df.iterrows() if j != i)]


def main():
    d = pd.read_csv(BATCH / "per_night_metrics.csv")
    d["lyft_bookings"] = d.bookings_standard + d.bookings_xl
    two = [("reached_15_share", "max"), ("lyft_bookings", "min")]
    three = two + [("van_km", "min")]
    g = d.groupby("rule")
    s = pd.DataFrame({
        "plain_label": [LABEL[r] for r in RULE_ORDER],
        "reached_15_share_mean": g.reached_15_share.mean().reindex(RULE_ORDER),
        "reached_15_share_sd": g.reached_15_share.std().reindex(RULE_ORDER),
        "lyft_bookings_mean": g.lyft_bookings.mean().reindex(RULE_ORDER),
        "lyft_bookings_sd": g.lyft_bookings.std().reindex(RULE_ORDER),
        "van_km_mean": g.van_km.mean().reindex(RULE_ORDER),
    }, index=RULE_ORDER)
    means = s.rename(columns={"reached_15_share_mean": "reached_15_share", "lyft_bookings_mean": "lyft_bookings",
                              "van_km_mean": "van_km"})
    s["nondominated_on_means_2obj"] = [r in nondominated(means, two) for r in RULE_ORDER]
    s["nondominated_on_means_3obj"] = [r in nondominated(means, three) for r in RULE_ORDER]
    # per night: which rules are nondominated among the six on that night (ties: identical points both survive)
    pn = []
    for night, x in d.groupby("night"):
        x = x.set_index("rule")
        nd = set(nondominated(x, two))
        for r in RULE_ORDER:
            pn.append({"night": night, "rule": r, "reached_15_share": x.loc[r, "reached_15_share"],
                       "lyft_bookings": x.loc[r, "lyft_bookings"], "nondominated_2obj": r in nd,
                       "identical_to_R0_on_both": (x.loc[r, "reached_15_share"] == x.loc["R0", "reached_15_share"]
                                                    and x.loc[r, "lyft_bookings"] == x.loc["R0", "lyft_bookings"])})
    pn = pd.DataFrame(pn)
    s["nights_nondominated_2obj"] = pn.groupby("rule").nondominated_2obj.sum().reindex(RULE_ORDER)
    s["nights_identical_to_R0"] = pn.groupby("rule").identical_to_R0_on_both.sum().reindex(RULE_ORDER)
    # paired differences from R0 (descriptive; same night, same hidden draws)
    piv = d.pivot(index="night", columns="rule", values="reached_15_share")
    s["reach_diff_vs_R0_mean"] = [(piv[r] - piv["R0"]).mean() for r in RULE_ORDER]
    s["nights_reach_above_R0"] = [int(((piv[r] - piv["R0"]) > 0).sum()) for r in RULE_ORDER]
    s["nights_reach_below_R0"] = [int(((piv[r] - piv["R0"]) < 0).sum()) for r in RULE_ORDER]
    s.to_csv(BATCH / "tradeoff_rule_summary.csv")
    pn.to_csv(BATCH / "tradeoff_per_night.csv", index=False)
    L = ["# Service versus Lyft use: descriptive trade-off (L5 batch, saved outputs)", "",
         "30 synthetic L5 nights (2 vans, 28 requests each), each replayed under six rules. Objectives: service S = share "
         "of all requests reached by a vehicle within 15 min (larger is better); Lyft use B = bookings per night (smaller "
         "is better). Means are averages of nightly values. Nondominated means *among these six tested rules*: not a "
         "frontier of all policies, not a recommendation, no statistical margin (D-50 unresolved).", "",
         "| Rule | Plain meaning | S mean (SD) | B mean (SD) | Van-km | Nondominated on means (S, B) | Nights nondominated (S, B) | Nights identical to R0 | Nights S above / below R0 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r, x in s.iterrows():
        L.append(f"| {r} | {x.plain_label} | {x.reached_15_share_mean:.3f} ({x.reached_15_share_sd:.3f}) | "
                 f"{x.lyft_bookings_mean:.2f} ({x.lyft_bookings_sd:.2f}) | {x.van_km_mean:.1f} | "
                 f"{'yes' if x.nondominated_on_means_2obj else 'no'} | {int(x.nights_nondominated_2obj)} of 30 | "
                 f"{int(x.nights_identical_to_R0)} | {x.nights_reach_above_R0} / {x.nights_reach_below_R0} |")
    L += ["", "With van-km as a third objective, nondominated on means: "
          + ", ".join(r for r in RULE_ORDER if s.loc[r, "nondominated_on_means_3obj"]) + ".", "",
          "Notes: a rule that makes no transfer on a night replays R0 exactly, so it ties R0 and both count as "
          "nondominated that night. These values rest on placeholder patience and provisional presence."]
    (BATCH / "tradeoff.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
