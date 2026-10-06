# Team Technical Guide: change log

One entry per version, newest first. Each gives the date, the trigger, the changes (page numbers are in that version's own PDF) and the files.
To release a version: bump `VERSION` and `DATE` in `docs/technical/build_team_guide.py`, add a row to Reference F and an entry here, build, then copy the builder to `docs/technical/guide_history/build_team_guide_<version>.py`.
Every build also writes `output/pdf/archive/BlueJay_Team_Technical_Guide_<version>.pdf` next to the current `output/pdf/BlueJay_Team_Technical_Guide_v2.pdf`. This log and the builder snapshots are kept by hand.

## v2.2, 1 October 2026

**Trigger:** the reworked figure and email to Prof. Kearsley (1 Oct). The guide must use the same names as what he sees.

**Changes** (pages in the v2.2 PDF, 31 pages)
- Cover and running footer: version 2.2, 1 October 2026.
- Chapter 1, p. 3: the subsection becomes "Where we started, and the three approaches from here". The table columns are now No. / Approach / Status (were Line / Direction / Status), numbered 0-3 as in the figure.
  - Approach 2 is renamed **"Events, zones and traffic"** (was "Regimes and the calendar"): when, where and how a night strains, meaning campus events from the historical calendar, zones, and traffic flow. Apr 17 stays as the motivating slow night.
  - Approach 3 reads "What's in plain sight that we can't see".
  - Statuses are unchanged.
- Reference F, p. 29: v2.2 row added.
- Layout: the longer Approach 2 row moves chapter 2 to the top of p. 4, so the document grows from 30 to 31 pages. Nothing else moved by more than one page.

**Files**
- PDF: `output/pdf/archive/BlueJay_Team_Technical_Guide_v2.2.pdf` (byte-identical to the current `output/pdf/BlueJay_Team_Technical_Guide_v2.pdf`)
- Builder snapshot: `docs/technical/guide_history/build_team_guide_v2.2.py`

## v2.1, 30 September 2026

**Trigger:** team review of v2.0 (30 Sep): show data analysis and insights as a stage; keep the data list but reframe it; keep a copy of every iteration.

**Changes** (pages in the v2.1 PDF, 30 pages)
- Cover, p. 1: version 2.1 and the new date in the subtitle, header and footer. The one-line takeaway now says we mine April "for what it can support". The scope paragraph adds "mine it for insights and operating regimes". The Part III navigation lists References E and F.
- Chapter 1, pp. 2-3: the one-sentence box is replaced by a five-stage flow (1 Digitize and 2 Analyze and mine DONE, 3 Build the world NEXT, 4 Simulate and compare and 5 Recommend PLANNED), with a paragraph that names stages 1 and 2 as the data-mining core (p. 2). New closing subsection "Where we started, and the directions from here" (p. 3): lines 0 to 3, each with a status (ABANDONED, ACTIVE, SIDE-BRANCH, OPEN). Line 2 names Apr 17 as the opening night of the 150th All-Alumni Weekend, a slow night rather than a busy one, and targets an event-aware forecast of daily load and slowdowns (D-14).
- Chapter 4, p. 6: the T3 row now profiles Apr 17 (Fri): total riders exactly at the month's median (1,456 riders, tied with two other days) but the fewest van completions (543), the most Lyft riders (674) and the longest waits and rides. Its "cannot tell us" cell adds why Apr 17 slowed: it was the opening night of the 150th All-Alumni Weekend, with a southbound JFX lane closure and a dry evening (verified, `docs/evidence/context/april_2026_calendar.md`), but one night cannot separate event, closure and an ordinary Friday. Source table: `outputs/insights/t03b_apr17_profile.csv`.
- Chapter 5, p. 7: item 5 "A data wish list" becomes "The value of the next extract". The detail moves to Reference E.
- Chapter 12, p. 20, and the Reference C phase table (row 8 Show), p. 24: "data wish list" becomes "the value of the next extract (Reference E)" and "value of the next extract".
- Reference C, p. 26: new paragraph recording Prof. Kearsley's first note (on the aggregate data).
- Reference E, p. 28 (new): "What more is possible: the value of the next extract". Six extracts ranked by cost, each with the assumption it retires and the result it sharpens.
- Reference F, p. 29 (new): revision history table. This log holds the details.
- Builder: every build also writes the archive copy; the PDF title carries the version; the docstring and Reference F describe the release routine.
- Housekeeping: `output/pdf/archive/` (v1.0, v2.0, v2.1) and `docs/technical/guide_history/` (README.md, builder snapshots) added.

**Layout fixes**
- Chapters 5 and 8 opened at a page foot in v2.0 (133 pt and 142 pt left, against a flat `CHAP_MIN` of 130). A chapter now needs its opening (title, intro and the first table or section) to fit, between 200 pt (`CHAP_MIN`) and 240 pt (`CHAP_MAX`). Run on the v2.0 content, both chapters start at the top of a page. In v2.1 every chapter opens with 261 pt or more, or at a page top. References E and F start on their own pages (28 and 29).
- The last row of the chapter 7 base-scenario table sat alone at the top of p. 11 in v2.0. `table()` now keeps the first two and the last two body rows of every table together (`NOSPLIT`), so a page break never leaves one row alone. Run on the v2.0 content, that table splits 4 rows and 4 rows.
- The heading guard now measures paragraphs at the real text width (492 pt, not 504).
- Checked on the v2.1 PDF: no heading at a page foot, no single-row table fragment, no chapter opening at a page foot, page numbers settled. The cover navigation table has one body row by design.
- Table widths: directions table first column 36 pt so "Line" does not wrap; Reference E Cost column 64 pt; Reference F Date column 64 pt. A soft line break in the Reference E title keeps "extract" off a line of its own.
- Noted, not changed: tables are 504 pt wide but the text column is 492 pt (6 pt frame padding each side), so table edges run 12 pt past the text on the right, as in v2.0.

**Files**
- PDF: `output/pdf/archive/BlueJay_Team_Technical_Guide_v2.1.pdf` (byte-identical to `output/pdf/BlueJay_Team_Technical_Guide_v2.pdf`)
- Builder snapshot: `docs/technical/guide_history/build_team_guide_v2.1.py`

## v2.0 refresh, 30 September 2026

**Trigger:** Phases 1 and 2 complete; Prof. Kearsley's comment of 29 Sep.

**Changes** (pages in the archived v2.0 PDF, 27 pages)
- Chapter 4, pp. 4-6: filled with the confirmed Phase 1-2 results from the evidence pack in `docs/evidence/`, replacing the preliminary eye-read of plan v2. It holds the 12-chart check table, the six-dimension data-quality scorecard (p. 5), the finding that the maps count completed rides (D-01), and the T1-T10 findings table.
- Gate G1 marked PASSED 2026-09-29 with seven carried caveats (gate box, p. 9).
- Reference C, p. 25: records Prof. Kearsley's comment.
- Same version number and cover date (29 September 2026): the build overwrote the first v2.0 issue in place. That first issue is not archived, so the v2.0 files below are the refreshed build.

**Files**
- PDF: `output/pdf/archive/BlueJay_Team_Technical_Guide_v2.0.pdf`
- Builder snapshot: `docs/technical/guide_history/build_team_guide_v2.0.py`

## v2.0, 29 September 2026

**Trigger:** plan v2, after the aggregate-only scope of 28 Sep (the trip-level data never came).

**Changes** (pages in the archived v2.0 PDF, 27 pages)
- Reordered into Part I Think (chapters 1-5, from p. 2), Part II Build (chapters 6-12, from p. 7) and Part III Reference (A-D, from p. 19), plus "What moved where" (p. 27), which maps every v1.0 section to its v2.0 place.
- New chapters 2-5: what is hard and what is not; truth, anchors and synthetic data; what April tells us; value to Hopkins and TransLoc.
- New build content: the April-shaped base scenario and scale ladder (chapter 7, p. 9); the game table and code shape (8, p. 11); players N and H and the ladder of gaps (9, p. 13); calibration-lite (10, p. 16); the value outputs (11, p. 17); the replay viewer (12, p. 18).
- New reference content: code locations (A, p. 19), config v2 defaults (B, p. 21), the phase and agent plans (C, p. 23), limits, risks and the cut list (D, p. 25).
- A gate box closes each Part II chapter.

**Files:** as for the v2.0 refresh above.

## v1.0, 22 September 2026

**Trigger:** plan of record after the proposal (15 Sep).

**Changes** (13 pages)
- First team guide: research design, implementation instructions, data contracts and a value-entry workbook. Covers the pipeline, policies A-C, gates G1-G6, calibration and experiments. A proposed specification with no digitized values or results.

**Files**
- PDF: `output/pdf/archive/BlueJay_Team_Technical_Guide_v1.0.pdf` (copy of `output/pdf/BlueJay_Team_Technical_Guide.pdf`)
- Builder: `docs/technical/build_team_guide_v1.py`, left in place. It rewrites `team_config.template.json`, so do not run it.
