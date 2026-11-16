# Midterm presentation package (draft v0.2, 22 Oct 2026)

| File | What it is |
|---|---|
| `BlueJay_Midterm_draft.pptx` | Editable deck: a title, 12 core slides, 9 backup slides (divider + B1–B8), speaker notes with sources on every slide |
| `BlueJay_Midterm_draft_preview.pdf` | The same deck rendered by LibreOffice, for quick viewing (fonts may differ slightly from PowerPoint) |
| `speaking_script.md` | Team script: presenter roles P1–P3, timings (18½ min) and transitions |
| `slide_explanations.md` | Slide-by-slide teaching document: purpose, prerequisites, evidence, derivations, assumptions, interpretation, limitations |
| `review_first_time_reader.md` | A simulated first-time reader's review (a useful check, not proof of audience comprehension) |
| `review_factual_accuracy.md` | Independent fact check against the sources |
| `figures/` | Methodology figures (rendered from `docs/technical/methodology_pdf/figures/`) and the map of one synthetic night |
| `data/` | Copies of the saved-output tables the deck uses, plus `deck_numbers.json` |
| `build_deck.js`, `make_deck_numbers.py`, `make_map.py` | Scripts that rebuild everything from saved outputs (no simulation) |

**Rebuild** (from the repository root):
1. `cd src && ../.venv/bin/python -m sim.tradeoff && cd ..` (descriptive trade-off from the saved L5 batch)
2. `.venv/bin/python docs/presentations/midterm/make_map.py`
3. `.venv/bin/python docs/presentations/midterm/make_deck_numbers.py`
4. `NODE_PATH=<folder containing pptxgenjs> node docs/presentations/midterm/build_deck.js` (pptxgenjs 3.12.0; set `APPLY_THEME=<pptx skill>/scripts/apply_theme.js` to write the theme colours)

**Sources.** Decision log (D-xx), `scenario_spec.md` v0.8, `model_design.md` v0.5, `scenario_methodology.md` v1.4, and saved outputs under `outputs/sim/` (`batch_L5_v1/`, `d53_experiment/`, `m2_L4_report.md`). Each slide's notes name its sources.

**Status.** Draft for team review. Timing (18½ min + about 10 min of questions) awaits the course's confirmation; presenter roles P1–P3 await assignment. The original proposal deck (`../BlueJayNightRide_Proposal.pptx`) is unchanged.

**Revision v0.1 → v0.2 (one pass, from the two reviews).**
- From the first-time-reader review: the six rules are introduced on slide 2 with the reason for the pivot; corrected proposal numbers moved to slide 1; waits written as durations; the pending price is introduced on slide 6; slide 7 says "addressed", not "fixed"; declined offers explained; verification distinguished from validation; the R1u(10) near-tie described as a practical tie; footer numbers follow the script; the trade-off takeaway is stated.
- From the fact check: the 16th minute (not the 15th) costs 10 points; patience scale ≈ 23.0 min; 95 of 196 transferred *requests* cancelled before the Lyft arrived (77 after booking); 6 reruns plus 2 pilot comparisons; 36 guardrail-excess *events* = 16 distinct requests on 10 nights; "up to" 9,828 variables; spec v0.8; the 1% of parties of five is assumed and the XL rule came from a team correction; the spread-out geography is built but not yet tested.
- Not changed: figure labels inherited from the methodology figures (for example `xfer_hold` on the transfer timeline); the trade-off chart's x-axis shows decimals.
