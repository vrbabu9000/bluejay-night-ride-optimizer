# Review findings and resolution record (v0.4, 23 Oct 2026)

Three specialist agents reviewed v0.4. None edited deliverables, ran simulations or spawned agents.

| Review | Role | Findings |
|---|---|---|
| [technical_review.md](technical_review.md) | Disputed claims A–C (before drafting); final technical wording (after draft 1) | A–C adopted; 4 must-fix, 5 should-fix, 2 minor |
| [review_first_time_listener.md](review_first_time_listener.md) | Rendered deck and spoken narrative | 6 high, 12 medium, 7 low |
| [review_presenter_professor.md](review_presenter_professor.md) | Defensibility, answers, timing, links | 4 high, 9 medium, 5 low, 6 missing Q&A |

All findings were applied in one consolidated pass. Only the affected checks were then repeated: rebuild, render of changed slides, link check and retiming.

## Disputed interpretations (Section 3 of the brief)

**A. Patience: corrected.**
- **Removed:** "would vanish" under constant hazard, and "losses after transfer exist under any patience model".
- **Now states:**
  - a transfer does not end waiting;
  - riders moved by the prediction rules had usually waited less, which under the placeholder is consistent with their lower *share* lost after transfer: a possible contributing mechanism, not an isolated cause;
  - whether the policy gap survives other patience shapes is untested.
- **Evidence:** a conditional calculation on the transferred riders (Weibull 44–47% vs 29–30%, matching the observed shares; exponential 33–34% for all). That is a conditional probability calculation, not a whole-policy experiment.

**B. Pivot: corrected.**
- **Now states:** "We now hold one specified van dispatcher fixed and change only the Lyft transfer rule," as a scope choice: the chosen question, unknown dispatcher internals, and the need for a controlled comparison.
- **Removed:** the claim that synthetic nights make algorithm comparisons mostly compare assumptions. It was uncited, and the objection applies equally to rule comparisons.
- **Cadence:** described as modelled on TransLoc's published 2016 design, not verified current Hopkins practice.
- **Methodology:** v1.5 §1a carries the same correction.

**C. Leader–follower: corrected.**
- **Framing:** a proposed, unimplemented extension: "One possible extension is to optimize transfer policy while anticipating how the routing dispatcher responds."
- **Bilevel is a choice:** optimizing a threshold is not necessarily bilevel; it becomes bilevel only if the dispatcher is modelled as optimizing its own routing objective.
- **Finite search:** solves a finite problem for the sample average, not the true expectation, continuous thresholds or all policies.
- **Six definitions** still needed are listed on the slide and in the handbook.

## Main changes after review
| Area | Change | Source |
|---|---|---|
| Lyft use as a cost | Slide 2 and narration: each Lyft order is an extra trip Hopkins pays for (cost unknown, D-45) | Listener 1 |
| "Dispatcher" | Slide 14 region renamed "Decision step: van dispatcher + transfer rule"; "van dispatcher" kept for route generation plus the optimizer | Listener 2 |
| Slide 3 | Missing data blocked replaying real nights; the dispatch comparison was a scope choice (slide 5) | Technical 1; Presenter 4 |
| Slide 5 | Cadence states the actual triggers; TransLoc explained | Technical 5; Listener 5 |
| Slide 6 | DESIGNED added to the label legend | Listener 6 |
| Slide 7 | "50,297 requests ÷ 24,095 completed"; five vans identified as a team design choice | Listener 7 |
| Slide 8 | Rules "defined on slide 17"; burst wording clarified; "per vehicle across all services" | Listener 9; Presenter 11 |
| Slide 10 | Why our mean (1.405) differs from 1.386; pointer to slide 16 | Listener 10 |
| Slide 13 | Locations relabelled DERIVED + ASSUMED; the ×1.2 and Lyft timing spoken | Presenter 10; Listener 12 |
| Slide 14 | "MILP" expanded; generator sentence trimmed | Listener 13 |
| Slide 16 | "Postponed / postponing has a price" used consistently with slide 19 | Listener 14 |
| Slide 17 | "No feasible van counts as an infinitely late pickup, so the rule fires"; thresholds "specified before any run (spec §6)"; R3 margin spoken; predictive vs waiting-time groups named | Technical 2, 6, 7; Listener 16 |
| Slide 19 | Bars relabelled as costs; "removes the flaw without adding variables"; who paid (9.8 → 35.6 min) and the 90th percentile in Q&A | Listener 18; Presenter 8, 9, 18 |
| Slide 20→21 | "Before trusting any result, we checked the implementation." | Listener 25 |
| Slide 22 | Caveat that the 15-min measure favours early transfer, on the slide and spoken; colour key for predictive rules | Presenter 1; Listener 16 |
| Slide 23 | "Lower *share* lost after transfer"; transfers include cancellations before ordering | Presenter 7; Listener 21 |
| Slide 24 | Dominance on 30-night means, with no noise margin; "Unassigned" is about 1 request in 840 from vans only; consistent hollow marker | Presenter 2, 3; Listener 22 |
| Slide 25 | Why bilevel; finite search over a sample average; definitions list spoken as optional | Presenter 5, 6; Listener 23 |
| Slide 26 | Patience "the assumption we most expect to matter (untested)"; Lyft delay statement conditioned on placeholder patience; metric caveat added | Technical 3 |
| Slide 27 | "How much extra Lyft use one more rider reached is worth … confidence intervals across the paired nights" | Listener 24 |
| Handbook | 12 new or corrected answers: metric, 0-s transfers, resemblance to April, noise, cost axis, follower ties, why bilevel, who paid, 30 nights, hand keys, per-night losses, R1u timing | Presenter (missing Q&A, 14, 15); Technical 8–11 |
| Timing | Optional sentences marked (about 180 words); one consistent estimate: about 26 min default, plan for about 27, about 28 with all optional sentences | Presenter 13; timing verdict |
| README | Review files now exist; the broken reference is resolved | Presenter 12 |

## Not adopted, with reasons
| Suggestion | Reason |
|---|---|
| Move slide 8 (pilot) after slide 13, and slide 19 (postponement) after slide 16 | The brief fixes the slide order. Slide 8's narration now says the rules are "defined shortly", and slide 19 keeps its link to slide 16's postponement price |
| Cut slide 4 to one spoken line | The brief requires readable correction annotations. The third correction is now optional in speech; all four stay on the slide |
| Drop the Booking definition | The brief requires it; the card now sits beside "Lyft order" to separate the two |
| Grey out the generator and inputs on slide 14; cut φ breakpoints on slide 16 | The brief asks for the full architecture and for explaining convex waiting |
| Remove the drop-off marker on slide 18 | It is part of the verified case. Its label "Dropped off by the Lyft" and the correction note (17 s after the predicted van pickup) keep it unambiguous |
| Add a second chart series for Lyft orders on slide 22 | Lyft orders are in every bar label and in the headline sentence; a second axis would violate the one-axis rule |
| Use "Canceled" everywhere | Slide 11's lead sentence uses the brief's wording ("Cancelled"); quoted dashboard labels keep "Canceled" |
| Reported broken link to `reviews/technical_review.md` | Not a defect: the file exists at that path and the link checker passes |

## Remaining material issues
1. **Timing is estimated, not rehearsed.** About 27 min planned, under 30 in every estimate, but with little margin if all optional sentences are kept. A timed full run is needed.
2. **The headline result is conditional.** It comes from a two-van, burst-loaded pilot with placeholder patience, a single 15-min measure that favours early transfer, and no intervals or noise margin (D-50 open).
3. **Human verification of the hand keys is unconfirmed.** The team should state which answer keys a member re-derived by hand.
4. **The methodology PDF still reflects v1.4** on the three corrected points. Its rebuild was deferred.
5. **The LibreOffice preview** may wrap text differently from PowerPoint. Check slides 7, 14, 16 and 22–25 in PowerPoint.
6. **Spec vs code:** spec §17 lists van off-duty as a decision trigger, but the code does not trigger on it. Recorded, not changed: this task makes no model changes.
