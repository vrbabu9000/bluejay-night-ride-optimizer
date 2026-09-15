"""
Blue Jay Night Ride — single-van route demo (NAIVE vs OPTIMIZED), real roads.
ILLUSTRATIVE dummy scenario. Both routes follow actual streets via OSRM.

Outputs (open in Chrome/Safari; Brave needs Shields down):
  outputs/demo_naive.html, outputs/demo_optimized.html, outputs/demo.html (side by side)
"""
import os, io, sys, base64, bisect
from datetime import datetime, timedelta
import folium
from folium.plugins import TimestampedGeoJson
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import scenario as SC
import osrm

OUTDIR = os.path.join(os.path.dirname(__file__), "..", "..", "outputs")
BASE = datetime(2026, 4, 17, 21, 0, 0)
STEP = 0.5  # min grid (PT30S)
PICKUP = "#2FA36B"; DROPOFF = "#E8624A"; VAN = "#12305E"
ROUTE_COLOR = {"NAIVE": "#E8624A", "OPTIMIZED": "#2FA36B"}
TITLE = {"NAIVE": "Naive — one rider at a time", "OPTIMIZED": "Optimized — pooled & reordered"}


def van_icon(hexcolor):
    s = 2; W, H = 40 * s, 24 * s
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    col = tuple(int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    d.rounded_rectangle([2 * s, 4 * s, 38 * s, 18 * s], radius=4 * s, fill=col, outline=(255, 255, 255), width=1 * s)
    d.rectangle([6 * s, 6 * s, 13 * s, 12 * s], fill=(235, 244, 255))
    d.rectangle([15 * s, 6 * s, 22 * s, 12 * s], fill=(215, 230, 252))
    d.rectangle([24 * s, 6 * s, 31 * s, 12 * s], fill=(215, 230, 252))
    d.ellipse([7 * s, 15 * s, 14 * s, 22 * s], fill=(20, 20, 20))
    d.ellipse([26 * s, 15 * s, 33 * s, 22 * s], fill=(20, 20, 20))
    img = img.resize((40, 24), Image.LANCZOS)
    buf = io.BytesIO(); img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _cum(geom):
    out = [0.0]
    for a, b in zip(geom, geom[1:]):
        out.append(out[-1] + SC._hav(a, b))
    return out


def _iso(minute):
    return (BASE + timedelta(minutes=minute)).isoformat()


def sample(geom, cumd, v, t_end):
    tv = [d / v for d in cumd]
    times, coords, g = [], [], 0.0
    while g <= t_end + 1e-9:
        if g <= tv[0]:
            p = geom[0]
        elif g >= tv[-1]:
            p = geom[-1]
        else:
            i = bisect.bisect_right(tv, g) - 1
            t0, t1 = tv[i], tv[i + 1]; p0, p1 = geom[i], geom[i + 1]
            f = 0 if t1 == t0 else (g - t0) / (t1 - t0)
            p = (p0[0] + f * (p1[0] - p0[0]), p0[1] + f * (p1[1] - p0[1]))
        times.append(_iso(g)); coords.append([p[1], p[0]]); g = round(g + STEP, 3)
    return times, coords


def caption(side, km, pct=None):
    extra = f' &nbsp;<span style="color:#1E6B45">(&minus;{pct:.0f}% distance)</span>' if pct is not None else ""
    return f"""
    <div style="position:absolute; top:10px; left:10px; z-index:9999; pointer-events:none;
        background:rgba(255,255,255,.94); border:1px solid #D5DCEA; border-radius:9px;
        padding:8px 12px; font-family:Arial,sans-serif; box-shadow:0 2px 8px rgba(0,0,0,.12);">
      <div style="font-size:15px; font-weight:700; color:#1B2540;">{TITLE[side]}</div>
      <div style="font-size:12px; color:#5B6472; margin-top:3px;">
        total drive <b style="color:#1B2540">{km:.1f} km</b>{extra} &nbsp;·&nbsp; 1 van · 5 requests
      </div>
    </div>"""


def build_side(side, stops, v, t_end, pct=None):
    waypoints = [pt for _, pt in stops]
    rt = osrm.route(waypoints)                     # real road geometry
    geom = rt["geometry"]; km = rt["distance"] / 1000.0
    cumd = _cum(geom)
    times, coords = sample(geom, cumd, v, t_end)

    sw, ne = SC.bounds()
    m = folium.Map(tiles="OpenStreetMap", control_scale=True)
    m.fit_bounds([[sw[0], sw[1]], [ne[0], ne[1]]])
    # full route drawn faintly so the tangle-vs-loop shape is visible up front
    folium.PolyLine(geom, color=ROUTE_COLOR[side], weight=4, opacity=0.35).add_to(m)

    feats = []
    for rid, r in SC.REQUESTS.items():
        t = _iso(r["spawn"]); (px, py), (dx, dy) = r["pickup"], r["dropoff"]
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [py, px]},
            "properties": {"times": [t], "icon": "circle", "popup": f"{rid} pickup ({r['spawn']}m)",
                "iconstyle": {"radius": 7, "color": "#fff", "weight": 2, "fillColor": PICKUP, "fillOpacity": 1}}})
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [dy, dx]},
            "properties": {"times": [t], "icon": "circle", "popup": f"{rid} drop-off",
                "iconstyle": {"radius": 7, "color": DROPOFF, "weight": 2, "fillColor": DROPOFF, "fillOpacity": 0.3}}})
    feats.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords},
        "properties": {"times": times, "style": {"color": ROUTE_COLOR[side], "weight": 5, "opacity": 0.95},
            "icon": "marker", "iconstyle": {"iconUrl": van_icon(VAN), "iconSize": [40, 24], "iconAnchor": [20, 12]}}})

    TimestampedGeoJson({"type": "FeatureCollection", "features": feats},
        period="PT30S", duration=None, transition_time=300, auto_play=True, loop=True,
        loop_button=True, max_speed=6, min_speed=0.2, date_options="HH:mm",
        time_slider_drag_update=True, add_last_point=False).add_to(m)
    m.get_root().html.add_child(folium.Element(caption(side, km, pct)))
    m.save(os.path.join(OUTDIR, f"demo_{side.lower()}.html"))
    return km


def wrapper():
    html = """<!doctype html><html><head><meta charset="utf-8">
<title>Blue Jay Night Ride — route optimization demo</title>
<style>
 html,body{margin:0;height:100%;font-family:Arial,Helvetica,sans-serif;background:#0E1A33;}
 .bar{color:#fff;padding:10px 16px;font-size:15px;font-weight:700;}
 .bar span{color:#F5A623;font-weight:600;font-size:12px;margin-left:10px;}
 .maps{display:flex;gap:6px;padding:0 6px;}
 .col{flex:1;background:#fff;border-radius:8px;overflow:hidden;}
 iframe{width:100%;height:83vh;border:0;display:block;}
 .legend{color:#C7D0E4;font-size:12px;padding:8px 16px;}
</style></head><body>
 <div class="bar">Blue Jay Night Ride — one van, five requests, real streets
   <span>Illustrative · same requests both sides · press &#9654; play</span></div>
 <div class="maps">
   <div class="col"><iframe src="demo_naive.html"></iframe></div>
   <div class="col"><iframe src="demo_optimized.html"></iframe></div>
 </div>
 <div class="legend"><b style="color:#2FA36B">&#9679;</b> pickup &nbsp; <b style="color:#E8624A">&#9675;</b> drop-off &nbsp; &#128656; van follows real roads (OSRM) &nbsp;·&nbsp; left ping-pongs one rider at a time; right pools &amp; reorders into a shorter loop.</div>
</body></html>"""
    with open(os.path.join(OUTDIR, "demo.html"), "w") as f:
        f.write(html)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    naive, opt = SC.naive_stops(), SC.optimized_stops()
    dn = osrm.route([p for _, p in naive])["distance"]
    do = osrm.route([p for _, p in opt])["distance"]
    v = dn / 30.0                      # speed so the naive route spans ~30 min
    t_end = round(dn / v) + 2          # = 32
    pct = (dn - do) / dn * 100.0
    km_n = build_side("NAIVE", naive, v, t_end)
    km_o = build_side("OPTIMIZED", opt, v, t_end, pct=pct)
    wrapper()
    print(f"naive {km_n:.1f} km  |  optimized {km_o:.1f} km  ({pct:.0f}% shorter)")
    print("WROTE", os.path.abspath(os.path.join(OUTDIR, "demo.html")))


if __name__ == "__main__":
    main()
