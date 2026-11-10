# Reply to Prof. Kearsley's proposal comment (draft, 2 Nov 2026)

To post under the original comment. The comment itself is in [feedback_proposal_kearsley.md](feedback_proposal_kearsley.md).

---

Dear Professor Kearsley,

Apologies for not replying to your comments on our proposal sooner; we only saw them after the midterm. They were very helpful, and several shaped what we presented:

- **Objective.** It is now a weighted sum in passenger-minutes, not a priority list. Waiting carries a convex piecewise-linear penalty (steeper after 5, 10, 15 and 20 minutes), a riding minute counts half a waiting minute, and distance is only a tie-breaker. Lyft use is no longer minimized inside the van objective, which avoids the trade you warned about.
- **Wording.** We describe the dispatcher as an exact MILP over a restricted candidate set, solved repeatedly within a rolling-horizon heuristic, and we state the time windows explicitly (penalized, soft waits; a ride-time guardrail).
- **Direction.** Trip-level records never arrived, so we build synthetic evenings consistent with the April aggregates. We narrowed the question to one controllable decision: with the van dispatcher held fixed, when should a waiting request move to Lyft? In a 30-night, two-van pilot, rules that use the plan's predicted pickup got a vehicle to more riders within 15 minutes but ordered more Lyft rides, so the answer is a trade-off, not one winner.

Your question of when the rolling-horizon MILP beats greedy assignment (fleet size, demand intensity, re-planning interval) is still open; we plan to test it directly as we scale to five vans.

We would value sitting down with you in the coming weeks for your comments and direction, so we can align before the final stretch.

Best regards,
Vignesh Rajesh Babu, for Team FourSight
