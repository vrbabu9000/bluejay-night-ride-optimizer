"""Layout model + emitters for the simulator architecture diagrams.

One model (pages -> nodes/edges with absolute coordinates) feeds two writers:
  * write_drawio(): one uncompressed .drawio (mxfile with 4 plain mxGraphModel pages)
  * svg_page():     one standalone hand-readable SVG per page
and one checker (check_page()) that tests the geometry (overlaps, edges through boxes,
text fit) before anything is written.
"""
import math
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xesc

from PIL import ImageFont

# ----------------------------------------------------------------------------- palette
PAL = {
    "engine": dict(fill="#E1F5EE", stroke="#0F6E56", font="#085041"),
    "player": dict(fill="#EEEDFE", stroke="#534AB7", font="#3C3489"),
    "neutral": dict(fill="#F1EFE8", stroke="#5F5E5A", font="#444441"),
}
EDGE_COLOR = "#5F5E5A"
TEXT_GRAY = "#444441"
LANE_STROKE = "#B4B2A9"
ARROW_L, ARROW_W = 7.5, 3.5          # arrow head length / half width (px)
RADIUS = 8                            # corner radius for every rounded rectangle (px)
SAFETY = 1.15                         # text must fit with 15% slack (other fonts run wider)
FONT_STACK = "Helvetica, Arial, sans-serif"
SUB_SIZE = 11
PITCH = 1.17                          # line height / font size; draw.io lines take the larger of the
                                      # node's base font (its "strut") and the line's own size
MIN_GAP = 20                          # minimum clear gap between neighbouring boxes (px)

# ----------------------------------------------------------------------------- text metrics
_FONT = "/System/Library/Fonts/Helvetica.ttc"
_fc = {}


def tw(text, size, bold=False):
    """Width in px of `text` in Helvetica (regular/bold) at `size` px."""
    key = (size, bold)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(_FONT, int(round(size * 10)), index=1 if bold else 0)
    return _fc[key].getlength(text) / 10.0


def hesc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def num(v):
    v = round(float(v), 4)
    return str(int(v)) if v == int(v) else ("%.4f" % v).rstrip("0").rstrip(".")


class Line:
    """One text line made of (text, bold) runs at a given font size."""

    def __init__(self, runs, size):
        self.runs = [(runs, False)] if isinstance(runs, str) else list(runs)
        self.size = size

    @property
    def plain(self):
        return "".join(t for t, _ in self.runs)

    @property
    def width(self):
        return sum(tw(t, self.size, b) for t, b in self.runs)


def pitch_of(node, line):
    """Line pitch inside `node` (draw.io lines are at least as tall as the node's base font)."""
    return max(line.size, node.tsize) * PITCH


# ----------------------------------------------------------------------------- model
class Node:
    def __init__(self, id, x, y, w, h, kind="neutral", lines=None, *, shape="round", dashed=False,
                 nofill=False, align="center", valign="middle", parent=None, role="node", html=None, value=None,
                 tsize=13, pad=8, font_override=None, stroke_override=None, sw=1):
        self.id, self.x, self.y, self.w, self.h = id, x, y, w, h
        self.kind, self.lines = kind, lines or []
        self.shape, self.dashed, self.nofill, self.align, self.valign = shape, dashed, nofill, align, valign
        self.parent, self.role, self.html, self.value = parent, role, html, value
        self.tsize, self.pad = tsize, pad
        self.font_override, self.stroke_override = font_override, stroke_override
        self.sw = sw                      # stroke width in px (default 1; 2 for the NEXT status)

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    @property
    def rect(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    @property
    def font(self):
        return self.font_override or PAL[self.kind]["font"]

    @property
    def stroke(self):
        return self.stroke_override or PAL[self.kind]["stroke"]


def std(id, x, y, w, h, kind, title, subs=(), tsize=13, **kw):
    """Standard node: bold title + smaller (11 px) subtitle lines."""
    subs = [subs] if isinstance(subs, str) else list(subs)
    lines = [Line([(title, True)], tsize)] + [Line(s, SUB_SIZE) for s in subs]
    html = "<b>%s</b>" % hesc(title)
    if subs:
        html += '<br><font style="font-size:%dpx">%s</font>' % (SUB_SIZE, "<br>".join(hesc(s) for s in subs))
    return Node(id, x, y, w, h, kind, lines, html=html, tsize=tsize, **kw)


class Edge:
    def __init__(self, id, src, dst, pts, label=None, lab_f=0.5, lab_off=(0, 0), lab_bg=False,
                 dashed=False, arrow=True):
        self.id, self.src, self.dst, self.pts = id, src, dst, [tuple(p) for p in pts]
        self.label, self.lab_f, self.lab_off, self.lab_bg = label, lab_f, lab_off, lab_bg
        self.dashed, self.arrow = dashed, arrow

    # geometry helpers ------------------------------------------------------
    def segments(self):
        return list(zip(self.pts[:-1], self.pts[1:]))

    def length(self):
        return sum(math.dist(a, b) for a, b in self.segments())

    def point_at(self, f):
        target, acc = f * self.length(), 0.0
        for a, b in self.segments():
            L = math.dist(a, b)
            if acc + L >= target - 1e-9 and L > 0:
                t = (target - acc) / L
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            acc += L
        return self.pts[-1]

    def label_center(self):
        px, py = self.point_at(self.lab_f)
        return (px + self.lab_off[0], py + self.lab_off[1])

    def label_box(self, size=SUB_SIZE):
        cx, cy = self.label_center()
        w = tw(self.label, size) + 6
        h = size * 1.25 + 3
        return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


class Page:
    def __init__(self, id, name, svgfile, w, title, desc):
        self.id, self.name, self.svgfile, self.w, self.h = id, name, svgfile, w, 0
        self.title, self.desc = title, desc
        self.nodes, self.edges, self.by_id = [], [], {}

    def add(self, n):
        assert n.id not in self.by_id, "duplicate node id " + n.id
        self.nodes.append(n)
        self.by_id[n.id] = n
        return n

    def link(self, id, src, dst, pts, **kw):
        e = Edge(id, src.id if isinstance(src, Node) else src, dst.id if isinstance(dst, Node) else dst, pts, **kw)
        self.edges.append(e)
        return e


def pt(n, side, frac=0.5):
    """Point on node boundary: side in l/r/t/b, frac along that side (0..1)."""
    if side == "l":
        return (n.x, n.y + n.h * frac)
    if side == "r":
        return (n.x + n.w, n.y + n.h * frac)
    if side == "t":
        return (n.x + n.w * frac, n.y)
    if side == "b":
        return (n.x + n.w * frac, n.y + n.h)
    raise ValueError(side)


# ----------------------------------------------------------------------------- checks
def _seg_hits_rect(a, b, r, eps):
    x0, y0, x1, y1 = r[0] + eps, r[1] + eps, r[2] - eps, r[3] - eps
    if x0 >= x1 or y0 >= y1:
        return False
    (ax, ay), (bx, by) = a, b
    if abs(ay - by) < 1e-9:
        if y0 < ay < y1:
            lo, hi = sorted((ax, bx))
            return max(lo, x0) < min(hi, x1)
        return False
    if abs(ax - bx) < 1e-9:
        if x0 < ax < x1:
            lo, hi = sorted((ay, by))
            return max(lo, y0) < min(hi, y1)
        return False
    raise ValueError("non-orthogonal segment %s -> %s" % (a, b))


def _rect_overlap(r1, r2, eps=0.0):
    return r1[0] + eps < r2[2] and r2[0] + eps < r1[2] and r1[1] + eps < r2[3] and r2[1] + eps < r1[3]


def _on_boundary(p, n, tol=0.01):
    x, y = p
    inside_x = n.x - tol <= x <= n.x + n.w + tol
    inside_y = n.y - tol <= y <= n.y + n.h + tol
    return inside_x and inside_y and (
        abs(x - n.x) < tol or abs(x - n.x - n.w) < tol or abs(y - n.y) < tol or abs(y - n.y - n.h) < tol)


def check_page(P, verbose=True):
    msgs = []
    obstacles = [n for n in P.nodes if n.role != "lane"]
    lanes = [n for n in P.nodes if n.role == "lane"]

    # 1. bounds
    for n in P.nodes:
        if n.x < 0 or n.y < 0 or n.x + n.w > P.w or n.y + n.h > P.h:
            msgs.append("BOUNDS %s outside canvas" % n.id)

    # 2. node overlaps (lane containers excluded; children must sit inside their lane)
    for i, a in enumerate(obstacles):
        for b in obstacles[i + 1:]:
            if _rect_overlap(a.rect, b.rect, eps=0.01):
                msgs.append("OVERLAP %s x %s" % (a.id, b.id))
    for n in obstacles:
        if n.parent:
            L = P.by_id[n.parent]
            if not (L.x <= n.x and L.y <= n.y and n.x + n.w <= L.x + L.w and n.y + n.h <= L.y + L.h):
                msgs.append("NOT-IN-LANE %s" % n.id)
    for i, a in enumerate(lanes):
        for b in lanes[i + 1:]:
            if _rect_overlap(a.rect, b.rect, eps=0.01):
                msgs.append("LANE OVERLAP %s x %s" % (a.id, b.id))

    # 3. text fit
    for n in obstacles:
        if not n.lines or n.role in ("separator",):
            continue
        widest = max(l.width for l in n.lines)
        if n.shape == "rhombus":
            block_h = sum(pitch_of(n, l) for l in n.lines)
            # a centered w x h block fits a rhombus if w/W + h/H <= 1
            need = widest * SAFETY / n.w + block_h / n.h
            if need > 0.92:
                msgs.append("RHOMBUS TEXT %s uses %.2f of inscribed area" % (n.id, need))
            continue
        inner = n.w - 2 * n.pad
        if widest * SAFETY > inner:
            msgs.append("TEXT-WIDTH %s: %.0f px (x%.2f = %.0f) > inner %.0f  [%s]" % (
                n.id, widest, SAFETY, widest * SAFETY, inner, max(n.lines, key=lambda l: l.width).plain))
        block = sum(pitch_of(n, l) for l in n.lines)
        if n.role == "header":
            need = block
        elif n.role == "chip":                      # small one- or two-line chips and pills
            need = block + 8
        else:
            need = (14 + block + 12) if n.valign == "top" else (block + 20)
        if need > n.h + 0.01:
            msgs.append("TEXT-HEIGHT %s: needs %.0f (block %.0f + padding) > h %.0f" % (n.id, need, block, n.h))

    # 3b. breathing room between neighbouring boxes (skip headers, separators and lanes)
    solid = [n for n in obstacles if n.role in ("node", "note")]
    for i, a in enumerate(solid):
        for b in solid[i + 1:]:
            xo = min(a.x + a.w, b.x + b.w) - max(a.x, b.x)
            yo = min(a.y + a.h, b.y + b.h) - max(a.y, b.y)
            if xo > 10:      # stacked: vertical gap
                gap = max(a.y, b.y) - min(a.y + a.h, b.y + b.h)
                if 0 <= gap < MIN_GAP:
                    msgs.append("TIGHT-VERTICAL %s / %s gap %.0f" % (a.id, b.id, gap))
            if yo > 10:      # side by side: horizontal gap
                gap = max(a.x, b.x) - min(a.x + a.w, b.x + b.w)
                if 0 <= gap < MIN_GAP:
                    msgs.append("TIGHT-HORIZONTAL %s / %s gap %.0f" % (a.id, b.id, gap))

    # 4. edges
    for e in P.edges:
        if e.src not in P.by_id or e.dst not in P.by_id:
            msgs.append("EDGE %s missing terminal" % e.id)
            continue
        s, d = P.by_id[e.src], P.by_id[e.dst]
        if not _on_boundary(e.pts[0], s):
            msgs.append("EDGE %s start not on %s boundary: %s" % (e.id, s.id, e.pts[0]))
        if not _on_boundary(e.pts[-1], d):
            msgs.append("EDGE %s end not on %s boundary: %s" % (e.id, d.id, e.pts[-1]))
        for a, b in e.segments():
            try:
                for n in obstacles:
                    if _seg_hits_rect(a, b, n.rect, 0.75):
                        msgs.append("EDGE-THROUGH-BOX %s passes through %s" % (e.id, n.id))
            except ValueError as ex:
                msgs.append("EDGE %s: %s" % (e.id, ex))
        if len(e.pts) >= 2 and math.dist(e.pts[-2], e.pts[-1]) < ARROW_L + 6 and e.arrow:
            msgs.append("EDGE %s last segment too short for the arrow head" % e.id)

    # 5. edge-edge crossings (segments of different edges must not cross; shared end/start allowed)
    segs = [(e.id, a, b) for e in P.edges for a, b in e.segments()]
    for i, (ida, a1, a2) in enumerate(segs):
        for idb, b1, b2 in segs[i + 1:]:
            if ida == idb:
                continue
            if _segs_cross(a1, a2, b1, b2):
                msgs.append("EDGE-CROSS %s x %s" % (ida, idb))

    # 6. labels
    boxes = []
    for e in P.edges:
        if not e.label:
            continue
        lb = e.label_box()
        boxes.append((e.id, lb))
        for n in obstacles:
            if _rect_overlap(lb, n.rect, eps=0.0):
                msgs.append("LABEL %s (%s) overlaps node %s" % (e.id, e.label, n.id))
        for e2 in P.edges:
            if e2.id == e.id and e.lab_bg:
                continue
            for a, b in e2.segments():
                if _seg_hits_rect(a, b, lb, 0.0):
                    msgs.append("LABEL %s (%s) touches edge %s" % (e.id, e.label, e2.id))
        if lb[0] < 0 or lb[2] > P.w or lb[1] < 0 or lb[3] > P.h:
            msgs.append("LABEL %s outside canvas" % e.id)
    for i, (ida, ra) in enumerate(boxes):
        for idb, rb in boxes[i + 1:]:
            if _rect_overlap(ra, rb):
                msgs.append("LABEL-LABEL %s x %s" % (ida, idb))
    if verbose:
        for m in msgs:
            print("  [%s] %s" % (P.id, m))
    return msgs


def _segs_cross(a1, a2, b1, b2):
    """True if two axis-aligned segments cross or overlap in more than a shared end point."""
    def bbox(p, q):
        return (min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]))
    A, B = bbox(a1, a2), bbox(b1, b2)
    lo_x, hi_x = max(A[0], B[0]), min(A[2], B[2])
    lo_y, hi_y = max(A[1], B[1]), min(A[3], B[3])
    if lo_x > hi_x + 1e-9 or lo_y > hi_y + 1e-9:
        return False
    # intersection region is a point, a segment or (for degenerate input) a rectangle
    if (hi_x - lo_x) < 1e-9 and (hi_y - lo_y) < 1e-9:
        pt_ = (lo_x, lo_y)
        ends = [a1, a2, b1, b2]
        # touching at a shared end point of both is fine (edges fan out of / into one port)
        return not (any(math.dist(pt_, p) < 1e-6 for p in (a1, a2)) and any(math.dist(pt_, p) < 1e-6 for p in (b1, b2)))
    return True   # collinear overlap or proper crossing


# ----------------------------------------------------------------------------- SVG writer
def _f(v):
    return num(v)


def _svg_text(x, y, size, fill, runs, anchor):
    """One <text> element; multiple runs become tspans (bold / regular)."""
    if len(runs) == 1:
        t, b = runs[0]
        weight = ' font-weight="bold"' if b else ""
        return '<text x="%s" y="%s" font-size="%s"%s fill="%s" text-anchor="%s">%s</text>' % (
            _f(x), _f(y), size, weight, fill, anchor, xesc(t))
    inner = "".join('<tspan%s>%s</tspan>' % (' font-weight="bold"' if b else "", xesc(t)) for t, b in runs)
    return '<text x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s">%s</text>' % (
        _f(x), _f(y), size, fill, anchor, inner)


def _block(n, top=None, height=None):
    """Baselines for a node's text block, vertically centered (or top-aligned inside [top, top+height])."""
    total = sum(pitch_of(n, l) for l in n.lines)
    y0 = (n.y + (n.h - total) / 2.0) if top is None else top
    ys, acc = [], 0.0
    for l in n.lines:
        p = pitch_of(n, l)
        ys.append(y0 + acc + p / 2.0 + 0.34 * l.size)
        acc += p
    return ys


def svg_node(n, P):
    out = []
    st = n.stroke
    if n.role == "lane":
        ldash = ' stroke-dasharray="6 4"' if n.dashed else ""
        out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%d" ry="%d" fill="#FFFFFF" stroke="%s" stroke-width="1"%s/>'
                   % (_f(n.x), _f(n.y), _f(n.w), _f(n.h), RADIUS, RADIUS, n.stroke_override or LANE_STROKE, ldash))
        out.append(_svg_text(n.cx, n.y + 6 + 0.86 * n.tsize, n.tsize, n.font_override or TEXT_GRAY, [(n.value, True)], "middle"))
        return out
    if n.role == "separator":
        y = n.y + n.h / 2.0
        out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1" stroke-dasharray="6 4"/>'
                   % (_f(n.x), _f(y), _f(n.x + n.w), _f(y), st))
        return out
    if n.role == "header":
        ys = _block(n)
        for l, y in zip(n.lines, ys):
            if n.align == "left":
                out.append(_svg_text(n.x + n.pad, y, l.size, n.font, l.runs, "start"))
            else:
                out.append(_svg_text(n.cx, y, l.size, n.font, l.runs, "middle"))
        return out
    fill = "none" if n.nofill else PAL[n.kind]["fill"]
    dash = ' stroke-dasharray="6 4"' if n.dashed else ""
    if n.shape == "rhombus":
        pts = "%s,%s %s,%s %s,%s %s,%s" % (_f(n.cx), _f(n.y), _f(n.x + n.w), _f(n.cy), _f(n.cx), _f(n.y + n.h), _f(n.x), _f(n.cy))
        out.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"%s/>' % (pts, fill, st, _f(n.sw), dash))
    elif n.shape == "tri":                      # small downward-pointing marker
        pts = "%s,%s %s,%s %s,%s" % (_f(n.x), _f(n.y), _f(n.x + n.w), _f(n.y), _f(n.cx), _f(n.y + n.h))
        out.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"%s/>' % (pts, fill, st, _f(n.sw), dash))
    else:
        out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%d" ry="%d" fill="%s" stroke="%s" stroke-width="%s"%s/>'
                   % (_f(n.x), _f(n.y), _f(n.w), _f(n.h), RADIUS, RADIUS, fill, st, _f(n.sw), dash))
    ys = _block(n, top=(n.y + 14) if n.valign == "top" else None)
    for l, y in zip(n.lines, ys):
        if not l.plain:
            continue
        if n.align == "left":
            out.append(_svg_text(n.x + 14, y, l.size, n.font, l.runs, "start"))
        else:
            out.append(_svg_text(n.cx, y, l.size, n.font, l.runs, "middle"))
    return out


def svg_edge(e, P):
    out = []
    pts = list(e.pts)
    tip = pts[-1]
    if e.arrow:
        a, b = pts[-2], pts[-1]
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        base = (tip[0] - ux * ARROW_L, tip[1] - uy * ARROW_L)
        pts[-1] = base
    dash = ' stroke-dasharray="2 3"' if e.dashed else ""
    out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1"%s/>'
               % (" ".join("%s,%s" % (_f(x), _f(y)) for x, y in pts), EDGE_COLOR, dash))
    if e.arrow:
        px, py = -uy, ux
        p1 = (base[0] + px * ARROW_W, base[1] + py * ARROW_W)
        p2 = (base[0] - px * ARROW_W, base[1] - py * ARROW_W)
        out.append('<polygon points="%s,%s %s,%s %s,%s" fill="%s" stroke="%s" stroke-width="0.5" stroke-linejoin="round"/>'
                   % (_f(tip[0]), _f(tip[1]), _f(p1[0]), _f(p1[1]), _f(p2[0]), _f(p2[1]), EDGE_COLOR, EDGE_COLOR))
    return out


def svg_label(e):
    cx, cy = e.label_center()
    out = []
    if e.lab_bg:
        x0, y0, x1, y1 = e.label_box()
        out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#FFFFFF"/>' % (_f(x0), _f(y0), _f(x1 - x0), _f(y1 - y0)))
    out.append(_svg_text(cx, cy + 0.34 * SUB_SIZE, SUB_SIZE, TEXT_GRAY, [(e.label, False)], "middle"))
    return out


def svg_page(P):
    o = []
    o.append('<?xml version="1.0" encoding="UTF-8"?>')
    o.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
             'style="max-width:100%%;height:auto" font-family="%s" role="img" aria-labelledby="title desc">'
             % (P.w, P.h, P.w, P.h, FONT_STACK))
    o.append('  <title id="title">%s</title>' % xesc(P.title))
    o.append('  <desc id="desc">%s</desc>' % xesc(P.desc))
    o.append('  <rect x="0" y="0" width="%d" height="%d" fill="#FFFFFF"/>' % (P.w, P.h))
    lanes = [n for n in P.nodes if n.role == "lane"]
    others = [n for n in P.nodes if n.role != "lane"]
    if lanes:
        o.append("  <!-- swimlanes -->")
        for n in lanes:
            o.append('  <g id="%s">' % n.id)
            o += ["    " + s for s in svg_node(n, P)]
            o.append("  </g>")
    o.append("  <!-- nodes -->")
    for n in others:
        o.append('  <g id="%s">' % n.id)
        o += ["    " + s for s in svg_node(n, P)]
        o.append("  </g>")
    if P.edges:
        o.append("  <!-- arrows -->")
    for e in P.edges:
        o.append('  <g id="%s">' % e.id)
        o += ["    " + s for s in svg_edge(e, P)]
        if e.label:
            o += ["    " + s for s in svg_label(e)]
        o.append("  </g>")
    o.append("</svg>")
    return "\n".join(o) + "\n"


# ----------------------------------------------------------------------------- draw.io writer
def _arc(n):
    return num(round(RADIUS / min(n.w, n.h) * 100, 2))


def node_style(n):
    p = PAL[n.kind]
    if n.role == "lane":
        lane_dash = "dashed=1;dashPattern=6 4;" if n.dashed else ""
        return ("rounded=1;arcSize=%s;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;"
                "fillColor=#FFFFFF;strokeColor=%s;fontColor=%s;fontStyle=1;fontSize=%d;verticalAlign=top;"
                "align=center;spacingTop=6;strokeWidth=1;%s" % (_arc(n), n.stroke_override or LANE_STROKE,
                                                                n.font_override or TEXT_GRAY, n.tsize, lane_dash))
    if n.role == "separator":
        return "shape=line;strokeWidth=1;dashed=1;dashPattern=6 4;strokeColor=%s;fillColor=none;html=1;" % n.stroke
    if n.role == "header":
        return ("text;html=1;strokeColor=none;fillColor=none;align=%s;verticalAlign=middle;whiteSpace=wrap;"
                "rounded=0;fontSize=%d;fontStyle=1;fontColor=%s;" % (n.align, n.tsize, n.font))
    fill = "none" if n.nofill else p["fill"]
    base = ("whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;fontColor=%s;strokeWidth=%s;fontSize=%d;"
            "align=%s;verticalAlign=%s;" % (fill, n.stroke, n.font, num(n.sw), n.tsize, n.align, n.valign))
    if n.valign == "top":
        base += "spacingTop=14;"
    if n.align == "left":
        base += "spacingLeft=14;spacingRight=8;"
    else:
        base += "spacingLeft=8;spacingRight=8;"
    if n.dashed:
        base += "dashed=1;dashPattern=6 4;"
    if n.shape == "rhombus":
        return "rhombus;" + base
    if n.shape == "tri":
        return "triangle;direction=south;" + base
    return "rounded=1;arcSize=%s;" % _arc(n) + base


def edge_style(e, src, dst):
    ex = (e.pts[0][0] - src.x) / src.w
    ey = (e.pts[0][1] - src.y) / src.h
    nx = (e.pts[-1][0] - dst.x) / dst.w
    ny = (e.pts[-1][1] - dst.y) / dst.h
    s = ("edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
         "strokeColor=%s;strokeWidth=1;" % EDGE_COLOR)
    if e.arrow:
        s += "endArrow=block;endFill=1;endSize=6;"
    else:
        s += "endArrow=none;endFill=0;"
    s += "fontSize=%d;fontColor=%s;" % (SUB_SIZE, TEXT_GRAY)
    s += "exitX=%s;exitY=%s;exitDx=0;exitDy=0;entryX=%s;entryY=%s;entryDx=0;entryDy=0;" % (
        num(ex), num(ey), num(nx), num(ny))
    if e.dashed:
        s += "dashed=1;dashPattern=2 3;"
    if e.label and e.lab_bg:
        s += "labelBackgroundColor=#FFFFFF;"
    return s


def dio_diagram(P):
    layer = P.id + "-layer"
    root_id = P.id + "-root"
    d = ET.Element("diagram", {"id": P.id, "name": P.name})
    m = ET.SubElement(d, "mxGraphModel", {
        "dx": "0", "dy": "0", "grid": "1", "gridSize": "10", "guides": "1", "tooltips": "1", "connect": "1",
        "arrows": "1", "fold": "1", "page": "1", "pageScale": "1", "pageWidth": str(P.w), "pageHeight": str(P.h),
        "math": "0", "shadow": "0", "background": "#FFFFFF"})
    r = ET.SubElement(m, "root")
    ET.SubElement(r, "mxCell", {"id": root_id})
    ET.SubElement(r, "mxCell", {"id": layer, "parent": root_id})
    # lanes first (lowest z-order), then everything else, then edges
    ordered = [n for n in P.nodes if n.role == "lane"] + [n for n in P.nodes if n.role != "lane"]
    for n in ordered:
        parent = P.by_id[n.parent] if n.parent else None
        gx = n.x - (parent.x if parent else 0)
        gy = n.y - (parent.y if parent else 0)
        value = n.html if n.html is not None else (n.value or "")
        c = ET.SubElement(r, "mxCell", {"id": n.id, "value": value, "style": node_style(n), "vertex": "1",
                                        "parent": parent.id if parent else layer})
        ET.SubElement(c, "mxGeometry", {"x": num(gx), "y": num(gy), "width": num(n.w), "height": num(n.h), "as": "geometry"})
    for e in P.edges:
        src, dst = P.by_id[e.src], P.by_id[e.dst]
        c = ET.SubElement(r, "mxCell", {"id": e.id, "value": e.label or "", "style": edge_style(e, src, dst),
                                        "edge": "1", "parent": layer, "source": e.src, "target": e.dst})
        g = ET.SubElement(c, "mxGeometry", {"relative": "1", "as": "geometry"})
        if e.label and abs(e.lab_f - 0.5) > 1e-6:
            g.set("x", num(2 * e.lab_f - 1))
        inner = e.pts[1:-1]
        if inner:
            arr = ET.SubElement(g, "Array", {"as": "points"})
            for x, y in inner:
                ET.SubElement(arr, "mxPoint", {"x": num(x), "y": num(y)})
        if e.label and (e.lab_off[0] or e.lab_off[1]):
            ET.SubElement(g, "mxPoint", {"x": num(e.lab_off[0]), "y": num(e.lab_off[1]), "as": "offset"})
    return d


def write_drawio(pages, path, stamp):
    root = ET.Element("mxfile", {"host": "app.diagrams.net", "modified": stamp,
                                 "agent": "Claude Code (generated; edit freely in draw.io)",
                                 "version": "24.7.0", "type": "device"})
    for P in pages:
        root.append(dio_diagram(P))
    ET.indent(root, space="  ")
    xml = ET.tostring(root, encoding="unicode")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(xml + "\n")
