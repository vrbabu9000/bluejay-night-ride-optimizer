"""
Reconcile the two independent reads of the O/D map bubbles into final counts.

Reader A (main session) and reader B (blind subagent) read every bubble
separately. Where they agree, the count is final. Disagreements are adjudicated
from the pixels and recorded; totals are never balanced by choice (the guide's
"do not force equality" rule).

Output: data/processed/map_counts_final.csv, docs/evidence/map_count_reconciliation.md
Run: .venv/bin/python src/evidence/map_reconcile.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "data" / "processed"

# Adjudications (bubble_id -> final count, reason). Only disagreements belong here.
ADJUDICATED = {
    "p02_b010": (6036, "Readers disagreed on the last digit (A 6037, B 6036); both saw a 6/7-shaped glyph under a halo. "
                       "B's template match favours 6 (0.81 vs 7 lowest). Final 6036 by the pixels. The O = D identity "
                       "would imply 6037, but totals are not balanced by choice; the O-D residual of 1 ride is carried "
                       "as reading uncertainty (bounds 6030-6039)."),
}


def main():
    a = pd.read_csv(P / "map_counts_readerA.csv")
    b = pd.read_csv(P / "map_counts_readerB.csv")
    m = a.merge(b, on="bubble_id", suffixes=("_A", "_B"))
    rows = []
    for r in m.itertuples():
        same = (r.count_read_A == r.count_read_B) or (pd.isna(r.count_read_A) and pd.isna(r.count_read_B))
        if r.bubble_id in ADJUDICATED:
            count, why = ADJUDICATED[r.bubble_id]
            agreement, conf, note = "adjudicated", "medium", why
        elif same:
            count = r.count_read_A
            agreement = "agree"
            conf = r.confidence_B if isinstance(r.confidence_B, str) else r.confidence_A
            note = r.notes_B if isinstance(r.notes_B, str) and r.notes_B else r.notes_A
        else:
            raise SystemExit(f"unadjudicated disagreement: {r.bubble_id} A={r.count_read_A} B={r.count_read_B}")
        lower = r.lower_B if pd.notna(r.lower_B) else r.lower_A
        upper = r.upper_B if pd.notna(r.upper_B) else r.upper_A
        if pd.notna(count):
            lower, upper = (lower, upper) if r.bubble_id in ADJUDICATED else (count, count)
        rows.append(dict(bubble_id=r.bubble_id, count_read=count, lower=lower, upper=upper, confidence=conf,
                         status=r.status_B, agreement=agreement, reader_A=r.count_read_A, reader_B=r.count_read_B,
                         notes=note))
    df = pd.DataFrame(rows)
    df.to_csv(P / "map_counts_final.csv", index=False)

    bub = pd.read_csv(P / "map_bubbles.csv")[["bubble_id", "map_name"]]
    df2 = df.merge(bub, on="bubble_id", how="left")
    df2.loc[df2.bubble_id.str.startswith("p04_extra"), "map_name"] = "origins_campus"
    live = df2[df2.status != "not_a_bubble"]
    summary = live.groupby("map_name").agg(bubbles=("bubble_id", "size"), read_sum=("count_read", "sum"),
                                          lower_sum=("lower", "sum"), upper_sum=("upper", "sum"),
                                          unread=("count_read", lambda s: int(s.isna().sum())))
    n_agree = int((df.agreement == "agree").sum())
    lines = ["# Map count reconciliation (two independent readers)", "",
             f"- Bubbles and extra rows: {len(df)}; readers agree exactly on **{n_agree}**; adjudicated: {len(df) - n_agree}.",
             "- Reader A: main session, contact sheets plus 4-10x zooms. Reader B: blind subagent (never saw A), own crops, template matching and an LDA check.",
             "- Status labels follow reader B (finer: ok / partial / hidden / not_a_bubble / extra); the counts are identical wherever both read one.", "",
             "| Map | Bubbles | Sum of reads | Hard bounds (with unread bubbles) | Unread (cut or hidden) |", "|---|---|---|---|---|"]
    for name, r in summary.iterrows():
        lines.append(f"| {name} | {r.bubbles} | {r.read_sum:,.0f} | {r.lower_sum:,.0f} - {r.upper_sum:,.0f} | {r.unread} |")
    lines += ["", "**Adjudicated**", ""]
    for k, (v, why) in ADJUDICATED.items():
        lines.append(f"- `{k}` -> {v}. {why}")
    lines += ["", "**Consequence.** City origins = 24,056 and city destinations = 24,057 (reads). They are equal within the one partly hidden label's reading range, and both match the completed-ride totals (p09 24,016; p07 24,095), so the maps count completed rides. The 1-ride residual is not forced away.", ""]
    (ROOT / "docs" / "evidence" / "map_count_reconciliation.md").write_text("\n".join(lines))
    print(summary)
    print("agree", n_agree, "of", len(df))


if __name__ == "__main__":
    main()
