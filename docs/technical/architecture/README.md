# Simulator architecture diagrams

Four diagrams of the Blue Jay Night Ride dispatch simulator, drawn as a game: a referee (the engine), players (the dispatchers), a replay log and a viewer. The source of truth is one editable draw.io file. The SVGs are standalone copies of the same four pages.

| File | What it is |
|---|---|
| `sim_architecture.drawio` | One draw.io file, four pages (tabs at the bottom of the window). Edit this one. |
| `p1_overview.svg` | Page 1, standalone SVG (about 1000 px wide). |
| `p2_players.svg` | Page 2, standalone SVG. |
| `p3_engine_loop.svg` | Page 3, standalone SVG. |
| `p4_data_flow.svg` | Page 4, standalone SVG. |

## What each page shows

**1. Overview (game framing).** Seven boxes in two columns. The level builder turns the April hotspots into a scenario. The experiment runner plays scenarios x players x seeds. The game engine (referee) and one dispatcher (player) talk in a loop: the engine sends a state / observation, the dispatcher sends commands back. Everything the engine does goes into the replay log, and the log feeds both the replay viewer and the scoreboard. The third cell of the right column is left empty on purpose, so the log-to-scoreboard arrow can run through it without crossing anything.

**2. Players (dispatchers).** A 2x2 grid. Columns are *when* a player decides (on each request, or every W seconds). Rows are *how* (greedy, one request at a time, or a joint MILP over all pending requests). A = immediate greedy, B = batched greedy (A, but it waits W seconds), C = batched MILP (B, but it decides jointly). The fourth cell, an immediate MILP, is dashed and marked "Not planned" because a single pending request leaves nothing to coordinate. Below the dashed line are the two benchmarks: N, the floor (nearest van, no pooling) and H, the ceiling (decides once and sees the whole hour). The side note names each gap: A - N = pooling, B - A = waiting, C - B = coordination, H - C = headroom. Each rung changes one ingredient, so each gap is the value of one thing.

**3. Engine loop (one turn).** Flowchart of what the engine does for one event. Pop the next event (ties break in a fixed order), update the world, and test whether a trigger fired (a new request for on-request players, a tick every W for batched players, or an urgent request for any player; these three sit in a note beside the diamond). If yes: build an observation (current state and revealed requests only, never the future), call `Dispatcher.decide()`, and let the referee validate the commands. Accepted commands are committed and their van-arrival events go back on the queue; rejected commands only log a reason. Every path ends in "Append to replay log" and loops to the next event. A side branch handles patience expiry: cancel, apply the Lyft overflow rule, log. When the queue is empty after the last arrival, the engine checks the accounting identity: generated = completed + abandoned + overflow + unserved at close.

**4. Data flow and files.** Four swimlanes read left to right: Evidence (April PDF to page images to digitizers to `observations.csv` and `map_clusters.csv`, then the insights and their figures), World (zones and OSRM travel times, scenario generator, `requests_*.csv` and `fleet_*.csv`), Simulation (dispatchers plug into the runner and engine, which write `replay.json`, `request_results` and `run_manifest.json`) and Communication (replay viewer, experiment figures). Only the map clusters feed the World lane, and the scenario files are the only thing handed on to the Simulation lane.

## Colours and shapes

| Meaning | Fill | Stroke | Text |
|---|---|---|---|
| Engine (referee, rules, accounting) | `#E1F5EE` | `#0F6E56` | `#085041` |
| Players (dispatchers) | `#EEEDFE` | `#534AB7` | `#3C3489` |
| Data and neutral | `#F1EFE8` | `#5F5E5A` | `#444441` |

Rounded rectangles everywhere, thin strokes, orthogonal arrows. The dashed cell on page 2 marks a combination we chose not to build, and the dashed line there is only a divider. The diamond on page 3 is the only decision, and the dotted line beside it ties the trigger note to that decision. Labels are HTML: a bold title and an 11 px subtitle, `<b>Title</b><br><font style="font-size:11px">Subtitle</font>`.

## Open and edit

- **In the browser:** go to <https://app.diagrams.net>, choose *File -> Open from -> Device*, and pick `sim_architecture.drawio`.
- **Desktop app:** install draw.io Desktop, then *File -> Open* and pick the file.

The four pages are the tabs at the bottom-left. Double-click a shape to edit its text (keep the bold title and the 11 px subtitle). Connect boxes with draw.io connectors (hover a shape and drag from one of its blue arrows) rather than free lines; the arrows then stay attached and orthogonal when you move boxes. Grid snapping is 10 px. Colours are in the shapes' styles (*Edit Style*), so copy a shape to reuse the palette. If you change a page, re-export it (below) and replace the matching SVG, since the SVGs do not update by themselves.

## Export

Use the *File -> Export as* menu in the browser or desktop app.

- **Visio (VSDX):** *File -> Export as -> VSDX...*. Each page should become a page in the `.vsdx`. Open it in Visio (or Visio for the web) and check that no label wraps differently; widen a shape if one does.
- **PNG:** *File -> Export as -> PNG...*. Pick the page, set zoom to 200% or more for slides, and leave "Include a copy of my diagram" ticked so the PNG can be re-opened for editing.
- **PDF:** *File -> Export as -> PDF...*. Choose all pages or the current page.
- **SVG:** *File -> Export as -> SVG...* works too, but draw.io writes HTML labels into `foreignObject`, which Word, PowerPoint and Inkscape may not draw. Use PNG or PDF there, or use the SVGs in this folder.

## Notes

- The SVGs use explicit colours and the generic `Helvetica, Arial, sans-serif` stack, with no external CSS or fonts. The root element has `max-width:100%` so they scale down in narrow viewers (this also stops macOS Quick Look from cropping them); the intrinsic size is 1000 px wide.
- Subtitles are 11 px on a 1000 px canvas, which is small if a whole page is squeezed onto a portrait sheet. For print, use a landscape page or export the PNG at 200% or more.
- Names and file paths in the diagrams follow the plan of record (plan v2, Part D: Files): `src/evidence`, `src/insights`, `src/scenario`, `src/sim`, `src/sim/dispatchers`, `src/viewer`. If a folder is renamed, edit page 4.

## Project map

`project_map.svg`, `project_map.drawio` and `project_map.pdf` are a fifth diagram: one page for a reader with 30 seconds, joining the project trajectory with the overall data flow. It is separate from the four simulator pages, so it has its own draw.io file and `sim_architecture.drawio` is unchanged. The page is 1564 x 1012 px (the 17 x 11 in ratio); the PDF is vector, 17 x 11 in landscape (1224 x 792 pt), with real text.

- **Top to bottom is time, left to right is data flow.** The dashed THEN band is the abandoned 15 Sep plan (trip-level data that never arrived). The strip under it is the pivot (28 to 30 Sep) and ends at the amber YOU ARE HERE marker. Below are five swimlanes, one per stage: Digitize, Analyze and mine, Build the world, Simulate and compare, Recommend and report. The panel at the bottom left lists the documents and governance in place.
- **Colour is status, and the last line of every box says it in words.** DONE `#E1F5EE`, NEXT `#FFF3D6` with a 2 px stroke, PLANNED `#F1EFE8`, ABANDONED white with a dashed `#9A9A9A` stroke, SIDE-BRANCH `#EEEDFE` with a dashed `#534AB7` stroke. These are the team guide's values.
- **Arrows.** Georeference -> Zones leaves stage 1 by its left margin and runs along the top of the lanes, because the map branch and the chart branch of stage 1 both feed the ledger and cannot both leave on the right without crossing. The up-going elbows (observations.csv -> Insights, Scale ladder -> Game engine) run in the gutters between lanes.
- **Rebuild:** `.venv/bin/python docs/technical/architecture/generator/build_project_map.py`. It runs the same geometry checker as the other pages, then writes the SVG, the draw.io file and the PDF. The PDF needs `cairosvg` (`.venv/bin/pip install cairosvg`); on macOS the script sets `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` itself, so Homebrew's cairo is found. Edit the generator (or the draw.io file), not the SVG.
- `archlib.py` gained five optional features for this page: a stroke width, dashed or coloured lanes, left-aligned headers, a `chip` role for small pills, and a triangle marker. Their defaults leave the four original pages byte-identical.
