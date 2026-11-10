# Midterm presentation, content draft v0.3 (22 Oct 2026)

This is a content redesign of the midterm talk: 30 minutes, made up of a 20-minute presentation and 10 minutes of questions. It is a draft for team review and a further independent review. It is not yet designed for professor-facing use. The v0.2 package in the parent folder is preserved unchanged.

## Reading order
1. [content_storyboard.md](content_storyboard.md): the designer's brief. It gives each slide's purpose, exact on-slide content, visual instructions, time and transition.
2. [BlueJay_Midterm_v0.3.pptx](BlueJay_Midterm_v0.3.pptx) and [BlueJay_Midterm_v0.3_preview.pdf](BlueJay_Midterm_v0.3_preview.pdf).
   - 22 main slides, a backup divider (23) and backups B1–B9 (24–32).
   - The PDF is exported from the PPTX by LibreOffice, so fonts may differ slightly from PowerPoint.
   - Internal links go main → backup and back.
3. [speaking_script.md](speaking_script.md): the journey paragraph, suggested speaker splits, a Q&A jump table to the backups, then per slide:
   - context;
   - spoken text (about 2,390 words, 19.1 min at 125 wpm; budgets proportional to length);
   - preparation notes;
   - likely questions;
   - links;
   - transition.
4. [slide_explanations.md](slide_explanations.md): the derivations, evidence and limitations per slide. Its anchors (`#s01`–`#s22`) match the script's.
5. [reviews/](reviews/): the three independent reviews of the first v0.3 draft and how they were addressed (see the revision record below).

## How to rebuild
```
.venv/bin/python docs/presentations/midterm/v0.3/make_numbers.py   # every deck number → data/numbers.json (reads saved outputs only)
.venv/bin/python docs/presentations/midterm/v0.3/make_map.py       # figures/map_synthetic_hour.png
NODE_PATH=<dir with pptxgenjs 3.12> APPLY_THEME=<pptx skill>/scripts/apply_theme.js node docs/presentations/midterm/v0.3/build_deck.js
```
Notes on the build:
- `build_deck.js` also reads `../data/deck_numbers.json` (v0.2) for three backup tables (B5, B6, B8). Their numbers are unchanged; only labels are rewritten in plain language.
- No simulation, calibration or optimizer change was made for v0.3.

## Source versions
- **Methodology:** `docs/technical/scenario_methodology.md` **v1.4**, the scientific source. The methodology PDF was **not** regenerated for this package.
- **Specifications and decisions:**
  - `scenario_spec.md` v0.8;
  - `model_design.md` v0.5;
  - decision log up to D-57 (D-52 amendment 5).
- **Outputs:**
  - `outputs/sim/batch_L5_v1` (30 nights × 6 rules);
  - `outputs/sim/L4_R3-2` (worked transfer);
  - `outputs/sim/d53_experiment` (postponement prices).
- **April 2026 dashboards:** digitized aggregates in `data/processed/`. They are restricted, so no images are used.

## What changed from v0.2
| | v0.2 | v0.3 |
|---|---|---|
| Length | 12 core slides + 8 backups, assumed 18.5 min | 22 main slides + 9 backups, confirmed 20 + 10 min |
| Speakers | P1–P3 assumed | Unassigned; natural handoffs after slides 4, 10, 16, 20 |
| Opening | Service and proposal on one slide | Booking-outcome tree (2), proposal (3), what the data contain (4) |
| Data investigation | Two dense slides | Five slides, one input each: volume (6), pairing (7), group size (8), "Canceled" (9), no-show denominator (10) |
| Rule names | Codes plus short glosses (R0, R3(2) …) | Six consistent plain names; codes only in notes, B1 and footers |
| Rules | Introduced inside the pivot slide | Dedicated slide (13) before any result, with the "Lyft arrives sooner" timing explained |
| Worked transfer | "Predicted total wait" example (18:20 decision) | Verified "Lyft arrives sooner" example: 18:17 decision, van 18:30:08 vs Lyft 18:27, gap 3 min 8 s; labelled DESIGNED |
| Optimizer | Methodology figures (φ curve, route sketch) | Native loop strip in eight steps; candidate table with constraints, penalties and postponement; MILP spelled out |
| Postponement price | Dense three-formulation table | Four-step story on slide 15; the table moved to B5 |
| Findings | One combined pilot slide | Separate slides: verification (17), service (18), after-transfer fates (19), trade-off (20) |
| Pareto | Scatter plus text | Toy dominance example, tie rule, "not a recommendation", "not a frontier", routing weights separate |
| Leader–follower | Text slide | Diagram, formulation in words, have / missing lists, NOT IMPLEMENTED badge |
| Figures | Methodology PNGs with labels such as "L5, r00" | Native charts and shapes; the map regenerated without implementation labels |
| Footer numbers | Script numbering (core 1–12, B1–B8) | Actual slide positions |

## Revision record
| Version | Date | Change |
|---|---|---|
| v0.1 | 22 Oct 2026 | First midterm package (parent folder) |
| v0.2 | 22 Oct 2026 | One revision after first-time-reader and factual reviews (parent folder, preserved) |
| v0.3 draft 1 | 22 Oct 2026 | Content redesign to 22 slides per the team's structure; new storyboard, script and explanations |
| v0.3 | 23 Oct 2026 | One consolidated revision after three independent reviews (see "Review responses" below) |

## Review responses (one consolidated revision)
Three independent reviews of draft 1 are in [reviews/](reviews/). All high-severity findings were addressed:

| Review | Found | Main changes |
|---|---|---|
| First-time listener | 4 high, 16 medium, 9 low | "Booking" kept for the rider's request, the Lyft side renamed "Lyft order" everywhere; one 6 pm figure ("about 5,100") in the main talk; the 168 shown on slide 6 and said correctly; slide 12 text tightened (all 8 loop steps kept, as the brief requires); slide 22 opens with a provisional answer to slide 2's question; status labels defined on slide 5; "the dispatcher" defined on slides 2 and 11; Lyft orders vs transfers explained; travel times added to slide 11 |
| Math and evidence | 0 high, 7 medium, 18 low | 73% label fixed by rounding once from the unrounded mean; ride time called a guardrail, not a hard limit; the large constant described as "as many bookings as the candidates allow"; the dominated rule described by its Lyft use, not "noise"; "36 excess events from 16 bookings"; status-mapping and ×1.2 labelled as assumptions; thresholds no longer called operating targets; verification tiles qualified (designed evening, sampled reruns) |
| Presenter and preparation | 5 high, 11 medium, 7 low | Slide 19 patience claim corrected (the gap between rules depends on the assumed rising impatience); AI-written code and checks stated plainly with a prepared answer; 18 new Q&A entries (Pareto, leader–follower, validity, scale, sample size, no-show); Q&A jump table, speaker splits, optional sentences; slide 11 → B3/B4 and slide 22 → backups links; budgets rebalanced |

**Not adopted, with reasons.**
- Splitting slide 12 or cutting its loop to 4 steps: the brief asks for the full 8-step loop on that slide. The text was shortened instead.
- Retitling slide 18: the title is the team's; its chart title now says "curb arrival, not boarding".
- Per-category greying of the n = 8 bar on slide 19: native stacked charts colour by series; the label now says "too few to compare".

## Remaining issues (honest list)
1. **Timing is tight.** 19.1 min of spoken text at 125 wpm leaves under a minute for pauses and handoffs; the script lists optional sentences to drop. Sections run 3:00 / 4:39 / 6:28 / 3:54 / 2:00 against the brief's 3 / 5 / 6 / 4 / 2: the model section is about 30 s long, the data section about 20 s short.
2. **Slide 12 is still the densest slide** (81 s).
3. **The preview is LibreOffice**, so fonts and wrapping may differ in PowerPoint; check slides 6, 12, 15 and 19 there.
4. **Pareto Q&A numbers** (supported points, reach per Lyft order) were recomputed from B7 means and are in the explanations, but are not yet in any committed analysis output.
5. The decision criteria (D-50) are still open, so no result is ranked or given intervals.

## Source corrections found while preparing v0.3
- **Methodology v1.4, "Pushback" item 1** (stale) still says no Lyft-rule comparison has been run. The designed-evening rule runs and the 30-night pilot have since been simulated. Not edited here: a methodology edit follows the guide versioning rule. Suggested wording: "Designed validation cases (L1–L4) and a 30-night descriptive pilot (L5) have been simulated; no rule has been ranked."
- Deck-only wording alignments, no source change needed:
  - the proposal's Lyft claim is quoted as "1 in 4 **trips**";
  - B9's reasons follow methodology §1a;
  - the threshold rationale follows D-49 (target wording, not operating policy).

## Open questions for the team
1. Is the 22-slide pace (≈ 55 s per slide) comfortable, or should slide 5 (signpost) or slide 17 (verification) move to backup?
2. Who speaks which section? The handoffs are marked in the script.
3. Should the designed worked transfer (slide 14) be joined by one randomized-night example, or is one designed case enough?
4. The decision criteria (D-50) are still unagreed. Slides 20 and 22 say so; should the team propose a criterion before the midterm?
5. The professor-facing visual design is still to come. The storyboard marks what the designer may restyle.
