#!/usr/bin/env python3
"""Build sim_architecture.drawio + p1..p4 SVGs from one layout model (see archlib.py)."""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archlib import *  # noqa: F401,F403

OUT = "/Users/vigneshrbabu/Documents/Git/bluejay-night-ride-optimizer/docs/technical/architecture"


def header(id, x, y, w, h, texts, size=12):
    texts = [texts] if isinstance(texts, str) else list(texts)
    return Node(id, x, y, w, h, "neutral", [Line([(t, True)], size) for t in texts], role="header",
                html="<br>".join(hesc(t) for t in texts), tsize=size)


# =============================================================================== page 1
def page1():
    P = Page("p1", "Overview (game framing)", "p1_overview.svg", 1000,
             "Simulator overview (game framing)",
             "The level builder turns April hotspots into a scenario and the experiment runner plays scenarios, "
             "players and seeds. The game engine (referee) and a dispatcher (player) trade observations and "
             "commands. The engine writes a replay log that feeds the replay viewer and the scoreboard.")
    W, H, T = 290, 64, 14
    LX, RX = 70, 640
    Y = [40, 170, 300, 430]
    b = P.add(std("p1-builder", LX, Y[0], W, H, "neutral", "Level builder", "April hotspots to a scenario", T))
    r = P.add(std("p1-runner", RX, Y[0], W, H, "neutral", "Experiment runner", "Scenarios × players × seeds", T))
    e = P.add(std("p1-engine", LX, Y[1], W, H, "engine", "Game engine (referee)", "Clock, rules, rider behavior", T))
    d = P.add(std("p1-dispatcher", RX, Y[1], W, H, "player", "Dispatcher (player)", "Reads state, sends commands", T))
    l = P.add(std("p1-log", LX, Y[2], W, H, "neutral", "Replay log", "Every event, time-stamped", T))
    v = P.add(std("p1-viewer", LX, Y[3], W, H, "neutral", "Replay viewer", "Preview, play, fast-forward", T))
    s = P.add(std("p1-scoreboard", RX, Y[3], W, H, "neutral", "Scoreboard", "Served, waits, Lyft overflow", T))
    P.h = Y[3] + H + 40

    P.link("p1-e-runner-builder", r, b, [pt(r, "l"), pt(b, "r")])
    P.link("p1-e-runner-dispatcher", r, d, [pt(r, "b"), pt(d, "t")])
    P.link("p1-e-builder-engine", b, e, [pt(b, "b"), pt(e, "t")])
    P.link("p1-e-engine-dispatcher", e, d, [pt(e, "r", 20 / 64), pt(d, "l", 20 / 64)],
           label="state / observation", lab_off=(0, -11))
    P.link("p1-e-dispatcher-engine", d, e, [pt(d, "l", 44 / 64), pt(e, "r", 44 / 64)],
           label="commands", lab_off=(0, 11))
    P.link("p1-e-engine-log", e, l, [pt(e, "b"), pt(l, "t")])
    P.link("p1-e-log-viewer", l, v, [pt(l, "b"), pt(v, "t")])
    P.link("p1-e-log-scoreboard", l, s, [pt(l, "r"), (s.cx, l.cy), pt(s, "t")])
    return P


# =============================================================================== page 2
def page2():
    P = Page("p2", "Players (dispatchers)", "p2_players.svg", 1000,
             "Players (dispatchers)",
             "A two-by-two grid of dispatchers: when they decide (on each request or every W seconds) against how "
             "they decide (greedy one at a time or a joint MILP over all pending requests). A immediate greedy, "
             "B batched greedy, C batched MILP; the immediate-MILP cell is not planned. Below a dashed line sit "
             "the benchmarks N (floor) and H (ceiling). A side note names the gap between each pair.")
    GX = [210, 494]
    GW, RH, T = 260, 76, 14
    RY = [76, 176, 318]
    P.add(header("p2-h-col1", GX[0], 38, GW, 26, "Decides on each request"))
    P.add(header("p2-h-col2", GX[1], 38, GW, 26, "Decides every W seconds"))
    P.add(header("p2-h-row1", 20, RY[0], 180, RH, "Greedy, one at a time"))
    P.add(header("p2-h-row2", 20, RY[1], 180, RH, "Joint MILP, all pending"))
    P.add(header("p2-h-row3", 20, RY[2], 180, RH, "Benchmarks"))
    P.add(std("p2-A", GX[0], RY[0], GW, RH, "player", "A: immediate greedy", "Inserts each request", T))
    P.add(std("p2-B", GX[1], RY[0], GW, RH, "player", "B: batched greedy", "A, but waits W seconds", T))
    P.add(std("p2-notplanned", GX[0], RY[1], GW, RH, "neutral", "Not planned", "Little to coordinate", T,
              dashed=True, nofill=True))
    P.add(std("p2-C", GX[1], RY[1], GW, RH, "player", "C: batched MILP", "B, but decides jointly", T))
    P.add(Node("p2-separator", 30, 280, GX[1] + GW - 30, 10, "neutral", [], role="separator"))
    P.add(std("p2-N", GX[0], RY[2], GW, RH, "player", "N: floor", "Nearest van, no pooling", T))
    P.add(std("p2-H", GX[1], RY[2], GW, RH, "player", "H: ceiling", "Decides once, sees all", T))

    gaps = [("A − N", "pooling"), ("B − A", "waiting"), ("C − B", "coordination"), ("H − C", "headroom")]
    lines = [Line([("Gaps between players", True)], 13), Line("", 13)]
    lines += [Line([(a, True), (" = " + b, False)], 12) for a, b in gaps]
    html = ("<b>Gaps between players</b><br><br><font style=\"font-size:12px\">"
            + "<br>".join("<b>%s</b> = %s" % (hesc(a), hesc(b)) for a, b in gaps) + "</font>")
    P.add(Node("p2-gaps", 790, 76, 184, 126, "neutral", lines, role="note", align="left", valign="top",
               html=html, tsize=13, pad=11))
    P.h = RY[2] + RH + 40
    return P


# =============================================================================== page 3
def page3():
    P = Page("p3", "Engine loop (one turn)", "p3_engine_loop.svg", 1000,
             "Engine loop (one turn)",
             "Flowchart of one engine turn: pop the next event, update the world, and if a trigger fired build an "
             "observation, call Dispatcher.decide(), have the referee validate the commands and either commit them "
             "or log the reason; then append to the replay log and loop. A patience expiry cancels the request and "
             "applies the Lyft overflow rule. When the queue is empty the accounting identity is checked.")
    MX, MW = 155, 290
    pop = P.add(std("p3-pop", MX, 30, MW, 76, "engine", "Pop next event from the queue",
                    ["Tie order: drop-offs, pickups, new requests,", "patience checks, dispatch ticks"]))
    upd = P.add(std("p3-update", MX, 146, MW, 56, "engine", "Update world state",
                    "Van positions, loads, request states"))
    trg = P.add(Node("p3-trigger", 190, 242, 220, 92, "engine", [Line([("Trigger fired?", True)], 13)],
                     shape="rhombus", html="<b>Trigger fired?</b>"))
    obs = P.add(std("p3-observe", MX, 374, MW, 68, "engine", "Build observation",
                    ["Current state + revealed requests only", "(no future information)"]))
    dec = P.add(std("p3-decide", MX, 478, MW, 56, "player", "Dispatcher.decide()", "Observation in, commands out"))
    val = P.add(std("p3-validate", MX, 570, MW, 88, "engine", "Referee validates commands",
                    ["Capacity, pickup before drop-off, same van,", "wait/ride limits, frozen commitments,", "shift end"]))
    com = P.add(std("p3-commit", MX, 698, MW, 60, "engine", "Commit + schedule arrivals",
                    "Van arrival events go into the queue"))
    rej = P.add(std("p3-reject", 565, val.cy - 28, 220, 56, "engine", "Log reason", "Rejected, state unchanged"))
    app = P.add(std("p3-append", 70, 798, 860, 52, "neutral", "Append to replay log", "Every event, time-stamped"))
    can = P.add(std("p3-cancel", 545, upd.cy - 34, 160, 68, "engine", "Cancel request", "Patience clock ran out"))
    ovf = P.add(std("p3-overflow", 745, upd.cy - 34, 170, 68, "engine", "Overflow (Lyft) rule",
                    ["Counts as Lyft overflow", "or abandoned"]))
    end = P.add(std("p3-end", 690, pop.cy - 34, 270, 68, "engine", "Accounting check",
                    ["generated = completed + abandoned +", "overflow + unserved at close"]))
    note = P.add(std("p3-triggers", 490, trg.cy - 42, 230, 84, "neutral", "Triggers",
                     ["New request (on-request players)", "Tick every W (batched players)",
                      "Urgent request (any player)"], role="note", align="left", pad=11))
    P.h = app.y + app.h + 30

    P.link("p3-e-pop-update", pop, upd, [pt(pop, "b"), pt(upd, "t")])
    P.link("p3-e-update-trigger", upd, trg, [pt(upd, "b"), pt(trg, "t")])
    P.link("p3-e-trigger-observe", trg, obs, [pt(trg, "b"), pt(obs, "t")], label="yes", lab_off=(20, 0))
    P.link("p3-e-observe-decide", obs, dec, [pt(obs, "b"), pt(dec, "t")])
    P.link("p3-e-decide-validate", dec, val, [pt(dec, "b"), pt(val, "t")])
    P.link("p3-e-validate-commit", val, com, [pt(val, "b"), pt(com, "t")], label="accepted", lab_off=(38, 0))
    P.link("p3-e-validate-reject", val, rej, [pt(val, "r"), pt(rej, "l")], label="rejected", lab_off=(0, -11))
    P.link("p3-e-commit-append", com, app, [pt(com, "b"), (com.cx, app.y)])
    P.link("p3-e-reject-append", rej, app, [pt(rej, "b"), (rej.cx, app.y)])
    e_no = P.link("p3-e-trigger-append", trg, app, [pt(trg, "l"), (118, trg.cy), (118, app.y)],
                  label="no", lab_off=(0, -11))
    e_no.lab_f = 36 / e_no.length()
    e_loop = P.link("p3-e-append-pop", app, pop, [pt(app, "l", 0.5), (48, app.cy), (48, pop.cy), pt(pop, "l")],
                    label="next event", lab_bg=True)
    e_loop.lab_f = (22 + (app.cy - 450)) / e_loop.length()
    P.link("p3-e-update-cancel", upd, can, [pt(upd, "r"), pt(can, "l")], label="patience expiry", lab_off=(0, -11))
    P.link("p3-e-cancel-overflow", can, ovf, [pt(can, "r"), pt(ovf, "l")])
    P.link("p3-e-overflow-append", ovf, app, [pt(ovf, "b"), (ovf.cx, app.y)])
    P.link("p3-e-pop-end", pop, end, [pt(pop, "r"), pt(end, "l")], label="queue empty after the last arrival",
           lab_off=(0, -11))
    P.link("p3-e-trigger-note", trg, note, [pt(trg, "r"), pt(note, "l")], dashed=True, arrow=False)
    return P


# =============================================================================== page 4
def page4():
    P = Page("p4", "Data flow and files", "p4_data_flow.svg", 1000,
             "Data flow and files",
             "Four swimlanes, left to right: Evidence, World, Simulation, Communication. The April PDF is digitized "
             "into observations and map clusters, which feed the insight figures and, via zones and OSRM travel "
             "times, the scenario generator. Scenario files feed the runner, whose outputs feed the replay viewer "
             "and the experiment figures.")
    LW, LY, LH = 234, 10, 733
    lane_x = {"Evidence": 8, "World": 258, "Simulation": 508, "Communication": 758}
    lanes = {}
    for name, x in lane_x.items():
        lanes[name] = P.add(Node("p4-lane-" + name.lower(), x, LY, LW, LH, "neutral", [Line([(name, True)], 13)],
                                 role="lane", value=name, tsize=13))
    cy = {1: 84, 2: 162, 3: 240, 4: 333, 5: 427, 6: 521, 7: 615, 8: 693}

    def box(id, lane, row, h, kind, title, subs):
        L = lanes[lane]
        return P.add(std(id, L.x + 12, cy[row] - h / 2, 210, h, kind, title, subs, parent=L.id))

    e1 = box("p4-april-pdf", "Evidence", 1, 52, "neutral", "April PDF", "12 charts on 11 pages")
    e2 = box("p4-page-images", "Evidence", 2, 52, "neutral", "Page images", "data/raw/april/pNN.png")
    e3 = box("p4-digitizers", "Evidence", 3, 52, "neutral", "Digitizers", "src/evidence")
    e4 = box("p4-digitized", "Evidence", 4, 82, "neutral", "Digitized data",
             ["data/processed/observations.csv", "data/processed/map_clusters.csv", "+ briefs in docs/evidence"])
    e5 = box("p4-insights", "Evidence", 5, 52, "neutral", "Insights T1–T10", "src/insights")
    e6 = box("p4-insight-figs", "Evidence", 6, 52, "neutral", "Insight figures", "outputs/insights")
    w1 = box("p4-zones", "World", 4, 68, "neutral", "Zones + OSRM travel times", ["src/scenario", "Travel-time matrix, cached routes"])
    w2 = box("p4-generator", "World", 5, 68, "neutral", "Scenario generator", ["src/scenario", "Gravity + IPF, then sampling"])
    w3 = box("p4-scenario-files", "World", 6, 52, "neutral", "Scenario files", "requests_*.csv, fleet_*.csv")
    s1 = box("p4-dispatchers", "Simulation", 5, 68, "player", "Dispatchers", ["src/sim/dispatchers", "N, A, B, C, H"])
    s2 = box("p4-runner", "Simulation", 6, 68, "engine", "Runner + engine", ["src/sim", "Scenarios × players × seeds"])
    s3 = box("p4-outputs", "Simulation", 7, 68, "neutral", "Run outputs", ["replay.json, request_results,", "run_manifest.json"])
    c1 = box("p4-viewer", "Communication", 7, 52, "neutral", "Replay viewer", "src/viewer")
    c2 = box("p4-exp-figs", "Communication", 8, 52, "neutral", "Experiment figures", "Value ladder, heat map")
    P.h = LY + LH + 10

    P.link("p4-e-pdf-images", e1, e2, [pt(e1, "b"), pt(e2, "t")])
    P.link("p4-e-images-digitizers", e2, e3, [pt(e2, "b"), pt(e3, "t")])
    P.link("p4-e-digitizers-data", e3, e4, [pt(e3, "b"), pt(e4, "t")])
    P.link("p4-e-data-insights", e4, e5, [pt(e4, "b"), pt(e5, "t")])
    P.link("p4-e-insights-figs", e5, e6, [pt(e5, "b"), pt(e6, "t")])
    P.link("p4-e-data-zones", e4, w1, [pt(e4, "r"), pt(w1, "l")])
    P.link("p4-e-zones-generator", w1, w2, [pt(w1, "b"), pt(w2, "t")])
    P.link("p4-e-generator-files", w2, w3, [pt(w2, "b"), pt(w3, "t")])
    P.link("p4-e-files-runner", w3, s2, [pt(w3, "r"), pt(s2, "l")])
    P.link("p4-e-dispatchers-runner", s1, s2, [pt(s1, "b"), pt(s2, "t")])
    P.link("p4-e-runner-outputs", s2, s3, [pt(s2, "b"), pt(s3, "t")])
    P.link("p4-e-outputs-viewer", s3, c1, [pt(s3, "r"), pt(c1, "l")])
    P.link("p4-e-outputs-figs", s3, c2, [pt(s3, "b"), (s3.cx, c2.cy), pt(c2, "l")])
    return P


def main():
    pages = [page1(), page2(), page3(), page4()]
    problems = 0
    for P in pages:
        print("checking", P.id, P.name, "(%d x %d)" % (P.w, P.h))
        problems += len(check_page(P))
    if problems:
        print("\n%d geometry problem(s) found" % problems)
    os.makedirs(OUT, exist_ok=True)
    stamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    write_drawio(pages, os.path.join(OUT, "sim_architecture.drawio"), stamp)
    for P in pages:
        with open(os.path.join(OUT, P.svgfile), "w", encoding="utf-8") as fh:
            fh.write(svg_page(P))
    print("\nwritten to", OUT)
    for P in pages:
        kinds = {}
        for n in P.nodes:
            kinds[n.role] = kinds.get(n.role, 0) + 1
        print("  %s: %s | edges=%d" % (P.id, ", ".join("%s=%d" % kv for kv in sorted(kinds.items())), len(P.edges)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
