# Presenter / professor review (v0.4 draft 1, 23 Oct 2026)

Reviewer: presenter-and-professor agent; read-only. All 39 handbook anchors resolved. Backup numbers and back-links matched. The slide 22–24 numbers matched `numbers.json`. This is a condensed record.

**Findings** (H = high, M = medium, L = low).

| # | Location | Sev. | Finding |
|---|---|---|---|
| 1 | 22 | H | The 15-min metric mechanically penalises the waiting-time rules (P(reach ≤ 15) ≈ 2% for "Wait ten") |
| 2 | 24 | H | "Unassigned is dominated" rests on a difference of about 1 request in 840, with no noise margin |
| 3 | 24 | M | The spoken dominance claim does not say "means" |
| 4 | 3 | H | The box says comparing dispatch methods could not be done (contradicts review B) |
| 5 | 25 | M | The finite-search claim omits that it is a sample average |
| 6 | 25 | M | It never says why the problem is bilevel rather than simulation optimisation |
| 7 | s23 | M | "Lower loss" is ambiguous: the per-night losses are similar; the *share* is lower |
| 8 | s19 | M | "Adopted the simplest" is wrong: the first version is simpler |
| 9 | s19 | M | "Reduced the worst wait" hides another rider going from 9.8 to 35.6 min |
| 10 | 13 | M | "Locations: OBSERVED" overclaims |
| 11 | 8 | L | 12.85 is per vehicle across all services |
| 12 | README | M | It references review files that do not exist yet |
| 13 | script/README | L | Three different timing figures |
| 14 | s21 | M | Who produced the hand keys? |
| 15 | handbook §20 | M | The "30 nights enough?" answer is procedural |
| 16 | handbook §22 | L | Point to the metric caveat |
| 17 | 11 | L | "Cancelled" vs "Canceled" |
| 18 | 19 | L | The 90th percentile rose slightly (31.0 → 31.2) |

**Missing Q&A** (added to the handbook).
- Is the metric rigged for early transfer?
- Isn't a 0-s elapsed transfer just sending the burst to Lyft?
- Why Lyft orders, not cost?
- Do the pilot nights resemble April?
- Is the Pareto set robust to noise?
- Is the follower optimistic or pessimistic?

**Timing verdict.**
- The arithmetic is internally consistent: about 26.8 min as an estimate, not a rehearsal.
- That estimate is optimistic: number reading adds about 1 min, and 4 s pauses are short for slides 14–16 and 22–24. Realistic delivery is 28–29 min.
- Recommended: mark about 150 optional words, then time one full run.
