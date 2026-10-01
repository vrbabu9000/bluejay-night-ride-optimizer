#!/usr/bin/env python3
"""Build the one-page project map: project_map.svg, project_map.drawio and project_map.pdf.

Same layout model and checker as build_arch.py (see archlib.py).  The page is 1564 x 1012 px, which is the
17 x 11 in ratio, and the PDF is written at 1224 x 792 pt.

Reading order: top = past, bottom = future; left to right = data flow.  Colour = status (DONE, NEXT, PLANNED,
ABANDONED, SIDE-BRANCH), and every box also ends with its status in words.
"""
import datetime
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archlib import *  # noqa: F401,F403

OUT = "/Users/vigneshrbabu/Documents/Git/bluejay-night-ride-optimizer/docs/technical/architecture"

# ----------------------------------------------------------------------------- status palette
# Same values as the team guide.  NEXT gets a 2 px stroke; ABANDONED and SIDE-BRANCH are dashed.
PAL.update({
    "done": dict(fill="#E1F5EE", stroke="#0F6E56", font="#085041"),
    "next": dict(fill="#FFF3D6", stroke="#B7791F", font="#7A4B00"),
    "planned": dict(fill="#F1EFE8", stroke="#5F5E5A", font="#444441"),
    "abandoned": dict(fill="#FFFFFF", stroke="#9A9A9A", font="#7A7A7A"),
    "side": dict(fill="#EEEDFE", stroke="#534AB7", font="#3C3489"),
    "event": dict(fill="#FFFFFF", stroke="#5F5E5A", font="#444441"),     # dated milestone chips (not a status)
})
DASHED = {"abandoned", "side"}
STROKE_W = {"next": 2}
BASE = 11          # base font of every box; the bold 13 px title sits on a 15.2 px line, 11 px lines on 12.9 px

W, H = 1564, 1012
EDGE_END = W - 16
GUT = [30, 70, 24, 24]             # gutters between the five lanes (the 70 px one carries the YOU ARE HERE marker)
LW = [422, 244, 230, 237, 251]     # lane widths


# ----------------------------------------------------------------------------- helpers
def _greedy(words, limit, size, bold):
    lines, cur = [], ""
    for word in words:
        t = (cur + " " + word) if cur else word
        if not cur or tw(t, size, bold) <= limit:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def wrap(text, limit, size=SUB_SIZE, bold=False):
    """Word wrap to `limit` px with the fewest lines, then balance the lines so no word is left alone."""
    words = text.split()
    n = len(_greedy(words, limit, size, bold))
    lo, hi = max(tw(w, size, bold) for w in words), limit
    for _ in range(24):                                   # narrowest width that still gives n lines
        mid = (lo + hi) / 2.0
        if len(_greedy(words, mid, size, bold)) <= n:
            hi = mid
        else:
            lo = mid
    return _greedy(words, hi, size, bold)


def need_h(n_title, n_sub):
    return int(math.ceil(n_title * 13 * PITCH + n_sub * SUB_SIZE * PITCH + 20))


def spec(w, title, subs, tag):
    """Wrap a box's text for width `w`; returns (title lines, sub lines, tag, minimum height)."""
    lim = (w - 16) / SAFETY
    titles = [title] if isinstance(title, str) else list(title)
    lines = []
    for s in subs:
        lines += list(s) if isinstance(s, (list, tuple)) else wrap(s, lim)
    return titles, lines, tag, need_h(len(titles), len(lines) + 1)


def make(id, x, y, w, kind, sp, h=None, parent=None):
    """One status box from a spec(): bold title, 11 px lines, bold status tag as the last line."""
    titles, lines, tag, hmin = sp
    txt = ([Line([(t, True)], 13) for t in titles] + [Line(s, SUB_SIZE) for s in lines]
           + [Line([(tag, True)], SUB_SIZE)])
    html = "<br>".join('<font style="font-size:13px"><b>%s</b></font>' % hesc(t) for t in titles)
    html += '<br><font style="font-size:11px">%s<b>%s</b></font>' % (
        "".join(hesc(s) + "<br>" for s in lines), hesc(tag))
    return Node(id, x, y, w, h or hmin, kind, txt, html=html, tsize=BASE, dashed=kind in DASHED,
                sw=STROKE_W.get(kind, 1), parent=parent)


def chip(id, x, y, w, h, kind, runs_lines, parent=None, tsize=BASE, pad=8):
    """Small chip: each entry of runs_lines is (runs, size)."""
    lines = [Line(r, s) for r, s in runs_lines]
    html = "<br>".join('<font style="font-size:%dpx">%s</font>' % (
        s, "".join(("<b>%s</b>" if b else "%s") % hesc(t) for t, b in (r if isinstance(r, list) else [(r, False)])))
        for r, s in runs_lines)
    return Node(id, x, y, w, h, kind, lines, role="chip", html=html, tsize=tsize, pad=pad,
                dashed=kind in DASHED, sw=STROKE_W.get(kind, 1), parent=parent)


def header(id, x, y, w, h, runs_lines, align="center", size=BASE, pad=8, parent=None, color=None):
    """Text-only header (no box).  runs_lines: list of (runs, size); runs = str or [(text, bold)]."""
    lines = [Line(r, s) for r, s in runs_lines]
    html = "<br>".join("".join(("<b>%s</b>" if b else "%s") % hesc(t) for t, b in l.runs) for l in lines)
    return Node(id, x, y, w, h, "neutral", lines, role="header", html=html, tsize=size, pad=pad, align=align,
                parent=parent, font_override=color)


def width_for(text_w, pad=8):
    return int(math.ceil(text_w * SAFETY + 2 * pad))


# ----------------------------------------------------------------------------- page
def frame():
    P = Page("pm", "Project map", "project_map.svg", W,
             "Blue Jay Night Ride project map",
             "One-page project map for Team FourSight. Top to bottom: the abandoned 15 Sep proposal, the 28-30 Sep "
             "pivot, then five stages left to right: Digitize and Analyze (done), Build the world (next), Simulate "
             "and compare, Recommend and report (planned). A footer lists the documents and governance in place. "
             "Color is status and every box also states its status in words.")
    P.h = H

    # ---- title block and legend ---------------------------------------------------------------------
    P.add(header("pm-title", 16, 10, 572, 28, [([("Blue Jay Night Ride · Team FourSight · Project map", True)], 20)],
                 align="left", size=20, pad=0))
    P.add(header("pm-subtitle", 16, 38, 530, 18,
                 [("Where we started, where we are (1 Oct 2026), and where the data flows next", 13)],
                 align="left", size=13, pad=0))
    legend = [("done", "DONE"), ("next", "NEXT"), ("planned", "PLANNED"), ("abandoned", "ABANDONED"),
              ("side", "SIDE-BRANCH")]
    ws = [width_for(tw(t, SUB_SIZE, True)) for _, t in legend]
    x = EDGE_END - sum(ws) - 8 * (len(ws) - 1)
    lx = x - 100
    P.add(header("pm-legend-label", lx, 14, 92, 24, [("Color = status", SUB_SIZE)], align="left", pad=0))
    for (kind, label), w in zip(legend, ws):
        P.add(chip("pm-legend-" + kind, x, 14, w, 24, kind, [([(label, True)], SUB_SIZE)]))
        x += w + 8

    # ---- THEN band ----------------------------------------------------------------------------------------
    BY, BH = 66, 132
    then_hdr = ("THEN · Proposal, 15 Sep \u00a0·\u00a0 ABANDONED 28 Sep: the trip-level data never came; "
                "only the aggregate April report did")
    band = P.add(Node("pm-lane-then", 16, BY, 1532, BH, "abandoned", [Line([(then_hdr, True)], 13)], role="lane",
                      value=then_hdr, tsize=13, dashed=True, stroke_override="#9A9A9A", font_override="#7A7A7A"))
    bw, bgap = 330, 60
    then = [("Trip-level TransLoc extracts", "expected; never arrived"),
            ("Replay April nights", "reconstruct each night, trip by trip"),
            ("Node-arc MILP", "one offline model, rolling horizon"),
            ("Compare with actual April", "the historical baseline")]
    tb = []
    for i, (t, s) in enumerate(then):
        tb.append(P.add(make("pm-then-%d" % (i + 1), 32 + i * (bw + bgap), BY + 30, bw, "abandoned",
                             spec(bw, t, [s], "ABANDONED 28 Sep"), h=62, parent=band.id)))
    for i in range(3):
        P.link("pm-e-then-%d" % (i + 1), tb[i], tb[i + 1], [pt(tb[i], "r"), pt(tb[i + 1], "l")], dashed=True)
    notes = [(1, "-> survives as the replay viewer (simulated nights)"), (2, "-> survives as H, the offline ceiling")]
    for i, txt in notes:
        P.add(chip("pm-then-note-%d" % i, tb[i].x, BY + 30 + 62 + 8, bw, 24, "planned", [(txt, SUB_SIZE)],
                   parent=band.id))

    # ---- trajectory strip (the pivot) -----------------------------------------------------------------------
    SY, SH = BY + BH + 10, 44
    ms = [("28 Sep", "aggregate-only April report (12 charts)", "event"),
          ("29 Sep", "plan v2: an April-shaped arena, five dispatchers", "event"),
          ("29 Sep", 'Prof. Kearsley: "gradient pointing in the right direction"', "event"),
          ("30 Sep", "Phases 0-2 done, G1 passed", "done")]
    snug = [max(tw(d, 13, True), tw(t, SUB_SIZE)) * SAFETY + 16 for d, t, _ in ms]
    agap = 56
    scale = (1532 - agap * 3) / sum(snug)
    cx, chips = 16, []
    for i, ((d, t, kind), sw_) in enumerate(zip(ms, snug)):
        w = int(round(sw_ * scale))
        if i == len(ms) - 1:
            w = 16 + 1532 - cx
        chips.append(P.add(chip("pm-ms-%d" % (i + 1), cx, SY, w, SH, kind,
                                [([(d, True)], 13), (t, SUB_SIZE)])))
        cx += w + agap
    for i in range(3):
        P.link("pm-e-ms-%d" % (i + 1), chips[i], chips[i + 1], [pt(chips[i], "r"), pt(chips[i + 1], "l")])

    # ---- lanes: geometry ---------------------------------------------------------------------------------------
    PY = SY + SH + 8                                  # marker pill row
    LT = PY + 24 + 2 + 9 + 3                          # lane top (below the pill and its pointer)
    LB = 984                                          # bottom of stages 4 and 5
    DOC_H = 72                                        # documents-and-governance panel under stages 1-3
    LB13 = LB - DOC_H - 16                            # bottom of stages 1-3
    LH = LB - LT
    LX = [16]
    for i in range(4):
        LX.append(LX[-1] + LW[i] + GUT[i])
    names = ["1 · Digitize", "2 · Analyze and mine", "3 · Build the world", "4 · Simulate and compare",
             "5 · Recommend and report"]
    subt = ["Phase 1 · DONE · G1 passed", "Phase 2 · DONE", "Phase 3 · NEXT", "Phases 4-7 · PLANNED",
            "Phase 8 · PLANNED"]
    lane_kind = ["done", "done", "next", "planned", "planned"]
    lanes = []
    for i in range(5):
        L = P.add(Node("pm-lane-%d" % (i + 1), LX[i], LT, LW[i], (LB13 if i < 3 else LB) - LT, "neutral",
                       [Line([(names[i], True)], 13)], role="lane", value=names[i], tsize=13))
        lanes.append(L)
        P.add(header("pm-lane-sub-%d" % (i + 1), LX[i] + 8, LT + 22, LW[i] - 16, 15, [(subt[i], SUB_SIZE)],
                     parent=L.id, color=PAL[lane_kind[i]]["font"]))
    # ---- footer: documents and governance (DONE chips), tucked under stages 1-3 ---------------------------------
    doc_label = "Documents and governance · DONE"
    dx, dw = 16, LX[2] + LW[2] - 16
    doc = P.add(Node("pm-lane-docs", dx, LB - DOC_H, dw, DOC_H, "neutral", [Line([(doc_label, True)], 13)],
                     role="lane", value=doc_label, tsize=13))
    docs = ["Team guide v1.0 (22 Sep) -> v2.0 (29 Sep) -> v2.2 (1 Oct)", "Decision log D-01 to D-15",
            "AI-use log (every tool use disclosed)", "Derived April data kept out of git"]
    dws = [width_for(tw(t, SUB_SIZE)) for t in docs]
    dgap = 14
    x = dx + (dw - sum(dws) - dgap * (len(docs) - 1)) / 2.0
    for i, (t, w) in enumerate(zip(docs, dws)):
        P.add(chip("pm-doc-%d" % (i + 1), x, LB - DOC_H + 36, w, 26, "done", [(t, SUB_SIZE)], parent=doc.id))
        x += w + dgap
    # the marker: amber pill + pointer, centred on the gutter between stage 2 and stage 3
    xb = LX[1] + LW[1] + GUT[1] / 2.0
    pw = width_for(tw("YOU ARE HERE · 1 Oct", 13, True))
    P.add(chip("pm-here", xb - pw / 2.0, PY, pw, 24, "next", [([("YOU ARE HERE · 1 Oct", True)], 13)]))
    P.add(Node("pm-here-ptr", xb - 8, PY + 26, 16, 9, "next", [], shape="tri", role="marker", sw=2))
    return P, lanes, LT, LH, xb



# ----------------------------------------------------------------------------- lane contents and arrows
def page(d4=56):
    """d4: extra drop (px) of the Game engine, and with it the rest of stages 4 and 5, below Dispatchers."""
    P, lanes, LT, LH, xb = frame()
    L1, L2, L3, L4, L5 = lanes
    top = LT + 62                                     # first row of boxes (the top corridor is at LT + 46)
    ybus = LT + 46

    # ---- stage 1: Digitize (a ring: stems on top, two branches, ledger at the bottom) ------------------
    ax = L1.x + 24
    cw = int((L1.w - 24 - 14 - 26) / 2)
    bx = ax + cw + 26
    T1 = "DONE · Phase 1"
    s = {"pdf": spec(cw, "April PDF", ["12 charts on 11 pages, aggregate only"], T1),
         "img": spec(cw, "Page images", ["original pixels (pdfimages)"], T1),
         "bub": spec(cw, "Map bubbles", ["215 read; two blind readers agree on 214"], T1),
         "dig": spec(cw, "Chart digitizers", ["color masks, axis fits, tooltip un-blending"], T1),
         "geo": spec(cw, "Georeference", ["Web Mercator from POI pins; ±17 m campus, ±57 m city"], T1),
         "obs": spec(cw, "observations.csv", ["482 reads, each with an interval"], T1),
         "led": spec(2 * cw + 26, "Reconciliation ledger", ["totals close within 0.4% · G1 PASSED"], T1)}
    r1 = max(s["pdf"][3], s["img"][3])
    r2 = max(s["bub"][3], s["dig"][3])
    r3 = max(s["geo"][3], s["obs"][3])
    y1 = top
    y2 = y1 + r1 + 24
    y3 = y2 + r2 + 24
    y4 = y3 + r3 + 24
    pdf = P.add(make("pm-pdf", ax, y1, cw, "done", s["pdf"], h=r1, parent=L1.id))
    img = P.add(make("pm-images", bx, y1, cw, "done", s["img"], h=r1, parent=L1.id))
    bub = P.add(make("pm-bubbles", ax, y2, cw, "done", s["bub"], h=r2, parent=L1.id))
    dig = P.add(make("pm-digitizers", bx, y2, cw, "done", s["dig"], h=r2, parent=L1.id))
    geo = P.add(make("pm-georef", ax, y3, cw, "done", s["geo"], h=r3, parent=L1.id))
    obs = P.add(make("pm-obs", bx, y3, cw, "done", s["obs"], h=r3, parent=L1.id))
    led = P.add(make("pm-ledger", ax, y4, 2 * cw + 26, "done", s["led"], parent=L1.id))

    # ---- stage 2: Analyze and mine ------------------------------------------------------------------------
    x2, w2 = L2.x + 14, L2.w - 28
    T2 = "DONE · Phase 2"
    ins_s = spec(w2, "Insights T1-T10", ["supply, cancellation, congestion, party size, occupancy, "
                                         "detour, Lyft, O-D structure, shift"], T2)
    reg_s = spec(w2, "Operating regimes", ["supply-limited; ~7 pts of cancellations per min of wait;",
                                           "Apr 17 (Alumni Weekend): the system slowed"], T2)
    sc_s = spec(w2, "Data-quality scorecard", [["6 dimensions × 12 charts:", "numbers sound, definitions weak"]], T2)
    sd_s = spec(w2, ["Approach 2 · Events, zones", "and traffic"],
                ["when, where and how a night strains;", "scored on each new monthly report"],
                "SIDE-BRANCH · time-boxed")
    ins = P.add(make("pm-insights", x2, top, w2, "done", ins_s, parent=L2.id))
    reg = P.add(make("pm-regimes", x2, ins.y + ins.h + 20, w2, "done", reg_s, parent=L2.id))
    sc = P.add(make("pm-scorecard", x2, reg.y + reg.h + 20, w2, "done", sc_s, parent=L2.id))
    side = P.add(make("pm-line2", x2, sc.y + sc.h + 20, w2, "side", sd_s, parent=L2.id))

    # ---- stage 3: Build the world --------------------------------------------------------------------------
    x3, w3 = L3.x + 12, L3.w - 24
    y_e3 = reg.y + 0.4 * reg.h                        # the fences + regimes arrow is level with Regimes
    zon_s = spec(w3, "Zones + travel times", ["16 zones; OSRM, 8,800 directed pairs"], "DONE · v0")
    gen_s = spec(w3, "Scenario generator", ["gravity + IPF + sampling: synthetic nights consistent with the "
                                            "aggregates"], "NEXT · Phase 3")
    bas_s = spec(w3, "Base scenario M", ["18:00-19:00, 5 vans, 30 or 60 requests"], "NEXT · Phase 3")
    scl_s = spec(w3, "Scale ladder + grid", [["S0 -> S1 -> S2 -> M -> L;", "grid pre-registered"]], "NEXT · Phase 3")
    zon = P.add(make("pm-zones", x3, top, w3, "done", zon_s, parent=L3.id))
    gy = max(zon.y + zon.h + 20, y_e3 - gen_s[3] / 2.0)
    gen = P.add(make("pm-generator", x3, gy, w3, "next", gen_s, parent=L3.id))
    bas = P.add(make("pm-base", x3, gen.y + gen.h + 20, w3, "next", bas_s, parent=L3.id))
    scl = P.add(make("pm-scale", x3, bas.y + bas.h + 20, w3, "next", scl_s, parent=L3.id))

    # ---- stage 4: Simulate and compare --------------------------------------------------------------------------
    x4, w4 = L4.x + 12, L4.w - 24
    dis_s = spec(w4, "Dispatchers (players)", [["N floor · A greedy · B batched ·", "C joint MILP · H ceiling"]],
                 "PLANNED · Phase 5 · G3")
    eng_s = spec(w4, "Game engine (referee)", ["event-driven; validates every command; accounting identity"],
                 "PLANNED · Phase 4 · G2")
    rep_s = spec(w4, "Replay log", ["replay.json, request results, run manifest"], "PLANNED · Phase 4")
    cal_s = spec(w4, "Calibration-lite", ["ride P10 sets road physics; rest held out"], "PLANNED · Phase 6 · G4")
    exp_s = spec(w4, "Experiments", ["scenarios × players × paired seeds"], "PLANNED · Phase 7 · G5")
    dis = P.add(make("pm-dispatchers", x4, top + d4, w4, "planned", dis_s, parent=L4.id))
    eng = P.add(make("pm-engine", x4, dis.y + dis.h + 20, w4, "planned", eng_s, parent=L4.id))
    rep = P.add(make("pm-replaylog", x4, eng.y + eng.h + 20, w4, "planned", rep_s, parent=L4.id))
    # Replay log -> Experiments gap: wide enough that Replay viewer and Value ladder (level with them) stay 20 px apart
    rv_h, vl_h = spec(L5.w - 24, "Replay viewer", ["preview, play, fast-forward; players side by side"], "x")[3], \
        spec(L5.w - 24, "Value ladder", ["the gaps: pooling, waiting, coordination, information"], "x")[3]
    gap_rx = max(20, (rv_h + vl_h - rep.h - exp_s[3]) / 2.0 + 20)
    exp = P.add(make("pm-experiments", x4, rep.y + rep.h + gap_rx, w4, "planned", exp_s, parent=L4.id))
    cal = P.add(make("pm-calibration", x4, exp.y + exp.h + 28, w4, "planned", cal_s, parent=L4.id))

    # ---- stage 5: Recommend and report (rows level with the stage-4 boxes that feed them) ----------------------
    x5, w5 = L5.x + 12, L5.w - 24
    mid_s = spec(w5, "Mid-semester update", ["after Phase 4 · date TBD"], "PLANNED")
    rv_s = spec(w5, "Replay viewer", ["preview, play, fast-forward; players side by side"], "PLANNED · Phase 8")
    vl_s = spec(w5, "Value ladder", ["the gaps: pooling, waiting, coordination, information"], "PLANNED · Phase 8")
    fin_s = spec(w5, "Final report + deck", ["conditional recommendation, limits stated"], "PLANNED · Phase 8 · G6")
    vh_s = spec(w5, "Value to Hopkins + TransLoc", ["benchmark, headroom, fleet curves, cancellation diagnosis, "
                                                    "value of the next extract"], "PLANNED · Phase 8")
    mid = P.add(make("pm-midsem", x5, eng.cy - mid_s[3] / 2.0, w5, "planned", mid_s, parent=L5.id))
    rv = P.add(make("pm-viewer", x5, rep.cy - rv_s[3] / 2.0, w5, "planned", rv_s, parent=L5.id))
    vl = P.add(make("pm-ladder", x5, exp.cy - vl_s[3] / 2.0, w5, "planned", vl_s, parent=L5.id))
    fin = P.add(make("pm-final", x5, vl.y + vl.h + 20, w5, "planned", fin_s, parent=L5.id))
    vh = P.add(make("pm-value", x5, fin.y + fin.h + 20, w5, "planned", vh_s, parent=L5.id))

    # ---- arrows: stage 1 ------------------------------------------------------------------------------------------
    P.link("pm-e-pdf-images", pdf, img, [pt(pdf, "r"), pt(img, "l")])
    P.link("pm-e-images-digitizers", img, dig, [pt(img, "b"), pt(dig, "t")])
    x1_ = img.x + 0.12 * img.w
    ym = img.y + img.h + 10
    P.link("pm-e-images-bubbles", img, bub, [(x1_, img.y + img.h), (x1_, ym), (bub.cx, ym), pt(bub, "t")])
    P.link("pm-e-bubbles-georef", bub, geo, [pt(bub, "b"), pt(geo, "t")])
    P.link("pm-e-digitizers-obs", dig, obs, [pt(dig, "b"), pt(obs, "t")])
    P.link("pm-e-georef-ledger", geo, led, [pt(geo, "b"), pt(led, "t", (geo.cx - led.x) / led.w)])
    P.link("pm-e-obs-ledger", obs, led, [pt(obs, "b"), pt(led, "t", (obs.cx - led.x) / led.w)])
    # observations.csv -> Insights: up the gutter between stages 1 and 2
    g12a, g12b = L1.x + L1.w + 8, L1.x + L1.w + 20
    yi = ins.y + 0.3 * ins.h
    P.link("pm-e-obs-insights", obs, ins, [pt(obs, "r"), (g12a, obs.cy), (g12a, yi), (ins.x, yi)])
    # Georeference -> Zones: out of the left margin of stage 1, along the top corridor under the lane headers,
    # then down the gutter between stages 2 and 3 into Zones
    g23 = L2.x + L2.w + GUT[1] / 2.0
    xl = L1.x + 12
    P.link("pm-e-georef-zones", geo, zon, [pt(geo, "l"), (xl, geo.cy), (xl, ybus), (g23, ybus), (g23, zon.cy),
                                           pt(zon, "l")])

    # ---- arrows: stage 2 ------------------------------------------------------------------------------------------
    P.link("pm-e-insights-regimes", ins, reg, [pt(ins, "b"), pt(reg, "t")])
    yb = ins.y + 0.85 * ins.h
    P.link("pm-e-insights-scorecard", ins, sc, [pt(ins, "l", 0.85), (g12b, yb), (g12b, sc.cy), pt(sc, "l")])
    g23b = L2.x + L2.w + 12
    yr = reg.y + 0.82 * reg.h
    P.link("pm-e-regimes-line2", reg, side, [pt(reg, "r", 0.82), (g23b, yr), (g23b, side.cy), pt(side, "r")],
           dashed=True)
    P.link("pm-e-regimes-generator", reg, gen, [(reg.x + reg.w, y_e3), (gen.x, y_e3)], label="fences + regimes",
           lab_off=(0, -11))

    # ---- arrows: stage 3 -> 4 ----------------------------------------------------------------------------------------
    P.link("pm-e-zones-generator", zon, gen, [pt(zon, "b"), pt(gen, "t")])
    P.link("pm-e-generator-base", gen, bas, [pt(gen, "b"), pt(bas, "t")])
    P.link("pm-e-base-scale", bas, scl, [pt(bas, "b"), pt(scl, "t")])
    g34 = L3.x + L3.w + GUT[2] / 2.0
    P.link("pm-e-scale-engine", scl, eng, [pt(scl, "r"), (g34, scl.cy), (g34, eng.cy), pt(eng, "l")])
    P.link("pm-e-dispatchers-engine", dis, eng, [pt(dis, "b"), pt(eng, "t")])
    P.link("pm-e-engine-replaylog", eng, rep, [pt(eng, "b"), pt(rep, "t")])
    P.link("pm-e-replaylog-experiments", rep, exp, [pt(rep, "b"), pt(exp, "t")])
    lw = tw("frozen parameters", SUB_SIZE) + 6
    P.link("pm-e-calibration-experiments", cal, exp, [pt(cal, "t"), pt(exp, "b")], label="frozen parameters",
           lab_off=(8 + lw / 2.0, 0))

    # ---- arrows: stage 4 -> 5 ----------------------------------------------------------------------------------------
    P.link("pm-e-replaylog-viewer", rep, rv, [pt(rep, "r", 0.5), pt(rv, "l", 0.5)])
    P.link("pm-e-experiments-ladder", exp, vl, [pt(exp, "r", 0.5), pt(vl, "l", 0.5)])
    P.link("pm-e-ladder-final", vl, fin, [pt(vl, "b"), pt(fin, "t")])
    g45 = L4.x + L4.w + GUT[3] / 2.0 + 3
    yv = vl.y + 0.85 * vl.h
    P.link("pm-e-ladder-value", vl, vh, [pt(vl, "l", 0.85), (g45, yv), (g45, vh.cy), pt(vh, "l")])
    return P


# ----------------------------------------------------------------------------- outputs
def write_pdf(svg, path):
    """Vector PDF at 17 x 11 in (1224 x 792 pt) from the SVG text.  cairosvg treats 96 px as 1 in, so 1632 x 1056."""
    import cairosvg
    plain = svg.replace(' style="max-width:100%;height:auto"', "")      # cairosvg draws nothing with this style
    cairosvg.svg2pdf(bytestring=plain.encode("utf-8"), write_to=path, output_width=1632, output_height=1056)


def main():
    if sys.platform == "darwin" and "DYLD_FALLBACK_LIBRARY_PATH" not in os.environ and os.path.isdir("/opt/homebrew/lib"):
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/lib"      # cairocffi needs Homebrew's libcairo
        os.execv(sys.executable, [sys.executable] + sys.argv)
    d4 = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].lstrip("-").isdigit() else 56
    P = page(d4)
    print("checking", P.id, P.name, "(%d x %d)" % (P.w, P.h))
    msgs = check_page(P)
    print("check_page: %d problem(s)" % len(msgs) if msgs else "check_page: clean (no overlaps, no edges through boxes, text fits)")
    os.makedirs(OUT, exist_ok=True)
    stamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    svg = svg_page(P)
    with open(os.path.join(OUT, P.svgfile), "w", encoding="utf-8") as fh:
        fh.write(svg)
    write_drawio([P], os.path.join(OUT, "project_map.drawio"), stamp)
    write_pdf(svg, os.path.join(OUT, "project_map.pdf"))
    kinds = {}
    for n in P.nodes:
        kinds[n.role] = kinds.get(n.role, 0) + 1
    print("written to", OUT)
    print("  %s: %s | edges=%d" % (P.id, ", ".join("%s=%d" % kv for kv in sorted(kinds.items())), len(P.edges)))
    return 1 if msgs else 0


if __name__ == "__main__":
    sys.exit(main())
