"""Paired bootstrap intervals over the saved L5 batch (D-50 rehearsal; no new simulation).

    cd src && ../.venv/bin/python -m sim.intervals

Reads outputs/sim/batch_L5_v1/<rNN>/<rule-tag>/outcomes.csv and per_night_metrics.csv and writes
outputs/sim/batch_L5_v1/intervals/ {per_night_measures.csv, pair_intervals.csv, dominance.csv, intervals.md}.
The saved runs are not modified.

Decision criteria (D-50 approval, 10 Nov 2026):
    primary    share of ALL requests not reached by a vehicle (curb arrival) within 20 min   delta = 2 pp
    secondary  passenger P90 wait among riders picked up                                     delta = 1 min
    resource   Lyft bookings per 100 requests (standard + XL)                                delta_B = 2 (1 also shown)
    sensitivity: the primary share at 15 min (same delta).
Dominance (D-50 amendment 1): A dominates B if A is non-inferior on all three measures (primary share, P90 wait,
bookings per 100 requests) and better on at least one. delta_B = 2 (D-50 amendment 2); 1 is a sensitivity reading.
For D = A - B on a measure where larger is worse: A better if the upper bound < 0; A non-inferior if the upper bound
< +delta; a CI containing 0 means "cannot tell". Paired percentile bootstrap, 10,000 resamples of nights, one common
set of resampled nights for every pair and measure. H1-H3 use 98.3% intervals (Bonferroni over three); L5 tests no
hypothesis, so the 98.3% rows here only exercise the machinery. Two vans, placeholder patience: a rehearsal.
"""
import itertools
import json

import numpy as np
import pandas as pd

from .batch import BATCH, NIGHTS, RULES, run_dir

OUTDIR = BATCH / "intervals"
B = 10_000
SEED = 20261110
DELTA = {"not_reached_20_pp": 2.0, "not_reached_15_pp": 2.0, "wait_pax_p90_min": 1.0, "lyft_bookings": None,
         "lyft_bookings_per100": None}
ROLE = {"not_reached_20_pp": "primary", "not_reached_15_pp": "sensitivity", "wait_pax_p90_min": "secondary",
        "lyft_bookings": "resource (per night, descriptive)", "lyft_bookings_per100": "resource (dominance)"}
DELTA_B = (1.0, 2.0)


def per_night():
    saved = pd.read_csv(BATCH / "per_night_metrics.csv").set_index(["night", "rule"])
    rows = []
    for night in NIGHTS:
        for rule in RULES:
            out = pd.read_csv(run_dir(night, rule) / "outcomes.csv")
            lag = out.curb_arrival_s - out.t_request_s
            r15, r20 = int((lag <= 900).sum()), int((lag <= 1200).sum())
            m = saved.loc[(night, rule)]
            if r15 != m.reached_15_n or len(out) != m.n_requests:
                raise SystemExit(f"{night} {rule}: recount {r15}/{len(out)} != saved {m.reached_15_n}/{m.n_requests}")
            rows.append({"night": night, "rule": rule, "n_requests": len(out), "reached_15_n": r15, "reached_20_n": r20,
                         "not_reached_15_pp": 100 * (1 - r15 / len(out)), "not_reached_20_pp": 100 * (1 - r20 / len(out)),
                         "wait_pax_p90_min": m.wait_pax_p90_min, "lyft_bookings": m.bookings_standard + m.bookings_xl,
                         "lyft_bookings_per100": 100 * (m.bookings_standard + m.bookings_xl) / len(out)})
    return pd.DataFrame(rows)


def verdict(lo, hi, delta, a, b):
    if hi < 0:
        return f"{a} better"
    if lo > 0:
        return f"{b} better"
    if delta is None:
        return "cannot tell"
    if hi < delta and lo > -delta:
        return "within margin both ways"
    if hi < delta:
        return f"{a} non-inferior"
    if lo > -delta:
        return f"{b} non-inferior"
    return "cannot tell"


def intervals(d):
    idx = np.random.default_rng(SEED).integers(0, len(NIGHTS), size=(B, len(NIGHTS)))
    rows = []
    for meas in DELTA:
        w = d.pivot(index="night", columns="rule", values=meas).reindex(index=NIGHTS, columns=RULES)
        for a, b in itertools.combinations(RULES, 2):
            diff = (w[a] - w[b]).to_numpy()
            boot = np.nanmean(diff[idx], axis=1)
            for level in (95.0, 98.3):
                lo, hi = np.nanpercentile(boot, [(100 - level) / 2, 100 - (100 - level) / 2])
                rows.append({"measure": meas, "role": ROLE[meas], "level": level, "A": a, "B": b,
                             "nights": int(np.isfinite(diff).sum()), "mean_A_minus_B": float(np.nanmean(diff)),
                             "lo": float(lo), "hi": float(hi), "half_width": float((hi - lo) / 2),
                             "delta": DELTA[meas], "verdict": verdict(lo, hi, DELTA[meas], a, b)})
    return pd.DataFrame(rows)


def dominance(iv, primary, delta_b):
    """D-50 amendment 1: A dominates B if A is non-inferior on all three measures (upper bound of A - B < +delta)
    and better on at least one (upper bound < 0). Bookings are per 100 requests with margin delta_b."""
    t = iv[iv.level == 95.0].set_index(["measure", "A", "B"])
    delta = {primary: DELTA[primary], "wait_pax_p90_min": DELTA["wait_pax_p90_min"], "lyft_bookings_per100": delta_b}

    def hi(meas, a, b):  # upper bound of (a - b), from whichever orientation was computed
        return t.loc[(meas, a, b)].hi if (meas, a, b) in t.index else -t.loc[(meas, b, a)].lo

    rows = []
    for a, b in itertools.permutations(RULES, 2):
        u = {m: hi(m, a, b) for m in delta}
        ni = all(u[m] < delta[m] for m in delta)
        better = [m for m in delta if u[m] < 0]
        rows.append({"A": a, "B": b, "primary": primary, "delta_bookings_per100": delta_b,
                     "A_noninf_all_three": ni, "A_better_on": ";".join(better), "A_dominates_B": bool(ni and better)})
    return pd.DataFrame(rows)


def fmt(r, unit):
    return f"{r.mean_A_minus_B:+.1f} [{r.lo:+.1f}, {r.hi:+.1f}]{unit}"


def report(d, iv, dom):
    g = d.groupby("rule")
    lines = ["# L5 paired intervals: D-50 rehearsal", "",
             "**What this is.** The decision criteria approved on 10 Nov 2026 (D-50), applied to the 180 saved L5 runs "
             "(30 nights × 6 rules; 2 vans, 28 requests, placeholder patience, provisional presence). "
             "It checks that the interval machinery works and shows how noisy L5 is. "
             "**It is not evidence about the service, and it ranks no rule for the study.** No new simulation; "
             "the 15-min recount matches the saved metrics on all 180 runs.", "",
             "Differences are A − B, averaged over the same 30 nights; larger is worse for every measure. "
             "Brackets are 95% paired percentile bootstrap intervals (10,000 resamples of nights, seed "
             f"{SEED}). Margins: 2 pp on the shares, 1 min on P90 wait; none on bookings.", "",
             "## Rule means (per night)", "",
             "| Rule | Not reached in 20 min (primary, %) | Not reached in 15 min (sensitivity, %) | Passenger P90 wait (min) | Lyft bookings |",
             "|---|---|---|---|---|"]
    for r in RULES:
        lines.append(f"| {r} | {g.not_reached_20_pp.mean()[r]:.1f} | {g.not_reached_15_pp.mean()[r]:.1f} | "
                     f"{g.wait_pax_p90_min.mean()[r]:.1f} | {g.lyft_bookings.mean()[r]:.1f} |")
    t = iv[iv.level == 95.0]
    lines += ["", "## Each rule against R0 (never transfer)", "",
              "Read: a negative difference means the rule does better than R0 on that measure.", "",
              "| Rule (A) vs R0 | Primary: not reached in 20 min, pp | Verdict | P90 wait, min | Verdict | Lyft bookings | Verdict |",
              "|---|---|---|---|---|---|---|"]
    for r in RULES[1:]:
        cells = []
        for meas, unit in (("not_reached_20_pp", ""), ("wait_pax_p90_min", ""), ("lyft_bookings", "")):
            x = t[(t.measure == meas) & (t.A == "R0") & (t.B == r)].iloc[0]
            flip = x.copy()
            flip.mean_A_minus_B, flip.lo, flip.hi = -x.mean_A_minus_B, -x.hi, -x.lo
            v = verdict(flip.lo, flip.hi, DELTA[meas], r, "R0")
            cells += [fmt(flip, unit), v]
        lines.append(f"| {r} | " + " | ".join(cells) + " |")
    lines += ["", "## Interval widths against the power target", "",
              "Target: half-width ≤ 0.7 δ (1.4 pp, 0.7 min). Across all 15 rule pairs at 30 nights:", "",
              "| Measure | Smallest | Median | Largest | Pairs meeting the target |", "|---|---|---|---|---|"]
    for meas in ("not_reached_20_pp", "not_reached_15_pp", "wait_pax_p90_min"):
        h = t[t.measure == meas].half_width
        lines.append(f"| {meas} | {h.min():.2f} | {h.median():.2f} | {h.max():.2f} | "
                     f"{int((h <= 0.7 * DELTA[meas]).sum())} of {len(h)} |")
    lines += ["", "On L5 one request is 3.6 pp of a night, so the shares move in coarse steps. The L6 pilot "
              "(168 requests a night) sets the real night count (D-50).", "",
              "## Dominance (D-50 amendment 1, 95% intervals)", "",
              "A dominates B if A is non-inferior on all three measures (primary share, passenger P90 wait, Lyft "
              "bookings per 100 requests) and better on at least one. The adopted bookings margin is 2 per 100 requests "
              "(D-50 amendment 2, chosen before any L6 run); 1 is shown as a sensitivity reading.", "",
              "| Primary | Bookings margin (per 100 requests) | Dominance pairs | No worse on all three, better on none (A vs B) |",
              "|---|---|---|---|"]
    for dd in dom:
        pairs = dd[dd.A_dominates_B]
        txt = ", ".join(f"{a} over {b}" for a, b in zip(pairs.A, pairs.B)) or "none"
        k = dd.A_noninf_all_three & ~dd.A_dominates_B
        ni = set(zip(dd.A[k], dd.B[k]))
        tie = ", ".join(f"{a} vs {b}" for a, b in sorted(ni)) or "none"
        lines.append(f"| {dd.primary.iloc[0]} | {dd.delta_bookings_per100.iloc[0]:g} | {txt} | {tie} |")
    lines += ["", "Every other pair is a trade-off (or cannot be told apart) and stays on the frontier. "
              "Full table: `dominance.csv`.", "",
              "## The 98.3% rows", "",
              "`pair_intervals.csv` also carries 98.3% intervals, the level H1–H3 will use. L5 tests no hypothesis "
              "(H1 is about the burst pattern on L6), so these rows only show the machinery works. "
              "For the H1 pair shape on L5, R2(15) and R3(2) against R1(15) on P90 wait:", ""]
    t98 = iv[(iv.level == 98.3) & (iv.measure == "wait_pax_p90_min")]
    for a in ("R2(15)", "R3(2)"):
        x = t98[((t98.A == "R1(15)") & (t98.B == a))].iloc[0]
        lines.append(f"- {a} − R1(15): {-x.mean_A_minus_B:+.1f} min [{-x.hi:+.1f}, {-x.lo:+.1f}]")
    lines += ["", "## Limits", "",
              "Two vans, 28 requests a night, placeholder patience (median 12 min) and provisional presence. Nights "
              "where a rule picked nobody up have no P90 wait and drop out of that pair (column `nights`). "
              "Percentile bootstrap with 30 nights can under-cover slightly. Nothing here carries over to L6 or to "
              "the real service."]
    (OUTDIR / "intervals.md").write_text("\n".join(lines) + "\n")


def main():
    OUTDIR.mkdir(exist_ok=True)
    d = per_night()
    iv = intervals(d)
    dom = [dominance(iv, p, db) for p in ("not_reached_20_pp", "not_reached_15_pp") for db in DELTA_B]
    d.to_csv(OUTDIR / "per_night_measures.csv", index=False)
    iv.to_csv(OUTDIR / "pair_intervals.csv", index=False)
    pd.concat(dom).to_csv(OUTDIR / "dominance.csv", index=False)
    report(d, iv, dom)
    (OUTDIR / "run_info.json").write_text(json.dumps({"bootstrap_resamples": B, "seed": SEED, "nights": NIGHTS,
                                                      "rules": RULES, "criteria": "D-50 approval and amendment 1, 2026-11-10"}, indent=1))
    print((OUTDIR / "intervals.md").read_text())


if __name__ == "__main__":
    main()
