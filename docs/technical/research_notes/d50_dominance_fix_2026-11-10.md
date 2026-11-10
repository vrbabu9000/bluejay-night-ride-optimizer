# D-50 amendment draft: fixing the dominance rule

Prepared 10 Nov 2026 for team approval. **Outcome (10 Nov):** the single rule was approved. For the bookings margin the team asked to try **both 1 and 2** per 100 requests; one must be chosen before the L6 freeze. L5 result: no dominance at either margin; the margin changes only whether R1u(10) counts as no worse than R0 on all three (yes at 2, no at 1). See D-50 (amendment 1). Found during the L5 rehearsal (D-58). Written **before** re-running anything with the new wording, so the choice is not shaped by what it does to L5. The pre-registration is not frozen yet (it freezes at the first L6 comparison run), so this counts as a pre-freeze change, not an amendment after the fact.

## The rule as written (`preregistration_v2.md` §4)

> Rule A dominates rule B on a condition if A is non-inferior on both outcome measures **and** uses fewer Lyft bookings (upper bound of the booking difference below 0), **or** A is better on an outcome and non-inferior on bookings.

## Gap 1: no margin on Lyft bookings

"Non-inferior on bookings" needs a margin, and none was set. Without one, the rule cannot be applied as written.

**Proposed fix:** count bookings **per 100 requests** (so the same number means the same thing on L5's 28 requests and L6's 168), with margin **δ_B = 2 bookings per 100 requests**.

**Why 2:** it mirrors the service margin. We already said that reaching 2 more riders in 100 matters. The matching statement on the cost side is that 2 extra Lyft rides in 100 requests matters. We have no price for a Lyft ride (D-45), so a symmetric margin is the one choice that does not quietly put a value on it. On L6, that is about 3 bookings a night.

## Gap 2: the second clause lets a rule "win" while clearly worse on the other rider measure

As written, A "dominates" B if A is better on one outcome and no worse on bookings, even when A is clearly worse on the **other** outcome. That is not dominance.

**Proposed fix:** replace both clauses with one standard definition, Pareto dominance with margins:

> **Rule A dominates rule B** on a condition if A is **non-inferior on all three measures** (the primary share, passenger P90 wait, and Lyft bookings per 100 requests, each with its margin) **and better on at least one** of them (upper bound of A − B below 0).

This keeps everything the old first clause allowed (non-inferior on both outcomes plus fewer bookings), drops the loophole, and fits on one line of a slide.

## What it does not change

The measures, the 2 pp / 1 min margins, the 20-min primary, the power rule and the 98.3% level for H1–H3 all stay as approved. Van-km is still reported next to the results, not inside the dominance rule.

## After approval

1. Update `preregistration_v2.md` §4 and its change log, and add D-50 (amendment 1) to the decision log.
2. Update `src/sim/intervals.py`: bookings per 100 requests, δ_B = 2, the single-sentence rule.
3. Re-run the L5 rehearsal and report whether any pair changes status. That is information about L5, and it must not feed back into the rule.
