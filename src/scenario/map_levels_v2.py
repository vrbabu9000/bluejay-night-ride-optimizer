"""
Interactive map of the v2 validation levels L1-L5: where each request is picked up and dropped off,
with the real road route from the local OSRM server (not straight lines).

Also checks that every route's drive time equals the travel-time matrix the scenarios were built from
(tt_locations_v2.csv): the map and the scenarios use the same roads.

Needs the local OSRM server (docs/technical/osrm_local.md); routes are cached, so reruns need no server.
Output: outputs/scenario/levels_v2_map.html
Run: OSRM_URL=http://localhost:5050 .venv/bin/python src/scenario/map_levels_v2.py
"""
import json
from pathlib import Path

import pandas as pd

import travel_times as tt

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "data" / "scenarios" / "v2"
OUT = ROOT / "outputs" / "scenario" / "levels_v2_map.html"


def main():
    tt.set_server("http://localhost:5050")
    loc = pd.read_csv(ROOT / "data" / "processed" / "locations_v1.csv").set_index("loc_id")
    snap = pd.read_csv(ROOT / "data" / "processed" / "locations_snap_v2.csv").set_index("loc_id")
    mat = pd.read_csv(ROOT / "data" / "processed" / "tt_locations_v2.csv")
    mat = dict(zip(zip(mat.origin, mat.dest), mat.seconds))
    zones = pd.read_csv(ROOT / "data" / "processed" / "zones_v1.csv").set_index("zone_id").zone_name
    depot = json.loads((V2 / "L1" / "scenario.json").read_text())  # noqa: F841 (provenance kept in each file)

    def pt(lid):
        return [round(float(snap.loc[lid, "snapped_lat"]), 6), round(float(snap.loc[lid, "snapped_lon"]), 6)]

    worst = 0.0
    def route(a, b):
        nonlocal worst
        r = tt.route([(loc.loc[a, "lat"], loc.loc[a, "lon"]), (loc.loc[b, "lat"], loc.loc[b, "lon"])])
        worst = max(worst, abs(r["duration_s"] - mat[(a, b)]))
        return [[round(c[1], 5), round(c[0], 5)] for c in r["coords"]]

    scen = {}
    folders = [("L1", V2 / "L1"), ("L2", V2 / "L2"), ("L3", V2 / "L3"), ("L4", V2 / "L4")] + \
              [(f"L5 night {f.name[1:]}", f) for f in sorted((V2 / "L5").glob("r*"))]
    for name, f in folders:
        req = pd.read_csv(f / "requests.csv")
        hc = pd.read_csv(f / "handcheck.csv") if (f / "handcheck.csv").exists() else None
        items = []
        for r in req.itertuples():
            it = {"id": r.request_id, "t": int(r.t_request_s), "party": int(r.party),
                  "o": pt(r.o_loc), "d": pt(r.d_loc), "oz": zones.get(r.o_zone, r.o_zone), "dz": zones.get(r.d_zone, r.d_zone),
                  "direct": int(r.direct_s), "route": route(r.o_loc, r.d_loc)}
            if hc is not None and "level" in hc.columns:
                h = hc[hc.request_id == r.request_id].iloc[0]
                it.update(outcome=h.outcome, van=h.van, wait=None if pd.isna(h.wait_s) else int(h.wait_s),
                          pickup=None if pd.isna(h.pickup_s) else int(h.pickup_s),
                          dropoff=None if pd.isna(h.dropoff_s) else int(h.dropoff_s),
                          dead=route(h.van_from, r.o_loc) if h.van_from != r.o_loc else [])
            if hc is not None and "rule" in hc.columns:
                it["rules"] = {row.rule: (row.decision if row.decision != "transfer" else
                                          f"transfer at {int(row.decision_s)} s, total wait {int(row.wait_s)} s")
                               for row in hc[hc.request_id == r.request_id].itertuples()}
            items.append(it)
        av = pd.read_csv(f / "availability.csv")
        scen[name] = {"requests": items, "vans": len(av), "van_from_s": int(av.avail_start_s.min()),
                      "depot": pt(av.start_loc.iloc[0])}
    print(f"routes: {sum(len(s['requests']) for s in scen.values())}; worst |route - matrix| = {worst:.2f} s; "
          f"network calls {tt.HTTP_CALLS}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(TEMPLATE.replace("__DATA__", json.dumps(scen, separators=(",", ":"))))
    print(OUT)


TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Validation levels map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root{--bg:#fbfbf9;--ink:#1b1b1b;--muted:#6b6a65;--line:#e2e1da;--pick:#1b8a5a;--drop:#c2410c;--van:#e8590c;--sel:#2a78d6}
body{margin:0;font:14px/1.4 -apple-system,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);display:flex;height:100vh}
#side{width:390px;overflow:auto;border-right:1px solid var(--line);padding:14px 16px;box-sizing:border-box}
#map{flex:1}h1{font-size:18px;margin:0 0 4px}.sub{color:var(--muted);font-size:12.5px;margin-bottom:10px}
.btns button{margin:0 4px 6px 0;padding:5px 10px;border:1px solid var(--line);background:#fff;border-radius:6px;cursor:pointer}
.btns button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.explain{background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:8px 0;font-size:13px}
table{border-collapse:collapse;width:100%;font-size:12.5px}td,th{padding:4px 4px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
tr.req{cursor:pointer}tr.req:hover,tr.req.sel{background:#eef4fc}
.key span{display:inline-block;width:10px;height:10px;border-radius:50%;margin:0 4px 0 10px;vertical-align:middle}
.tag{font-size:11px;padding:1px 5px;border-radius:4px;background:#f1f0eb}
@media (max-width:760px){body{flex-direction:column}#side{width:100%;height:46vh}#map{height:54vh}}
</style></head><body>
<div id="side"><h1>Validation levels L1–L5</h1>
<div class="sub">Synthetic requests drawn from April 2026 map totals (Homewood + Peabody). Lines are the real road route from the local OSRM server. Times are after 18:00.</div>
<div class="btns" id="lv"></div><div id="night"></div>
<div class="key"><span style="background:var(--pick)"></span>pickup<span style="background:var(--drop)"></span>drop-off<span style="background:var(--van);border-radius:2px"></span>van depot</div>
<div class="explain" id="explain"></div><table id="tbl"></table></div>
<div id="map"></div>
<script>
const D=__DATA__;
const EXPL={L1:"<b>L1: nothing goes wrong.</b> 16 requests, 2 vans. Each request arrives only when both vans are free, so you can check by hand which van goes and when it arrives. Dashed lines show the van driving empty to the pickup.",
L2:"<b>L2: the same 16 requests</b>, but R005 and R011 don't show up. The van waits 3 minutes at the curb, then leaves.",
L3:"<b>L3: the same 16 requests</b>, but 3 riders give up while the van is on its way.",
L4:"<b>L4: Lyft bookkeeping.</b> 16 requests in 20 minutes, and the vans only come on duty at 18:15, so early riders have no van. Click a request to see what each Lyft rule does with it.",
L5:"<b>L5: one of 30 random nights</b> from the same recipe: 2 vans, 28 requests in an hour, with a burst at 18:20–18:30. Use the slider to flip through nights; the recipe stays the same, the riders change."};
const map=L.map('map');L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors'}).addTo(map);
let layer=L.layerGroup().addTo(map),cur=null,lines={};
const hm=s=>{const h=18+Math.floor(s/3600),m=Math.floor(s%3600/60),x=s%60;return`${String(h%24).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(x).padStart(2,'0')}`};
const mins=s=>(s/60).toFixed(1)+' min';
function color(t,T){const a=Math.min(1,t/Math.max(T,1));return `hsl(${210},${70}%,${70-40*a}%)`}
function show(name){cur=name;layer.clearLayers();lines={};const S=D[name];const T=Math.max(...S.requests.map(r=>r.t));
 const base=name.startsWith('L5')?'L5':name;document.getElementById('explain').innerHTML=EXPL[base]+(S.van_from_s>0?`<br><span class="tag">vans on duty from ${hm(S.van_from_s)}</span>`:'');
 L.marker(S.depot,{icon:L.divIcon({html:'<div style="width:14px;height:14px;background:var(--van);border:2px solid #fff"></div>',className:''})}).bindTooltip('van depot ('+S.vans+' vans start here)').addTo(layer);
 const b=[];S.requests.forEach(r=>{const c=color(r.t,T);
  if(r.dead&&r.dead.length)L.polyline(r.dead,{color:'#888',weight:2,dashArray:'4 5',opacity:.7}).addTo(layer);
  const pl=L.polyline(r.route,{color:c,weight:3,opacity:.85}).addTo(layer);lines[r.id]=pl;
  const tip=`<b>${r.id}</b> requested ${hm(r.t)} · party ${r.party}<br>${r.oz} → ${r.dz}<br>direct drive ${mins(r.direct)}`+
   (r.outcome?`<br>outcome: <b>${r.outcome}</b>${r.van?' ('+r.van+')':''}${r.wait!=null?'<br>wait '+mins(r.wait):''}`:'');
  L.circleMarker(r.o,{radius:4+r.party*1.5,color:'#fff',weight:1.5,fillColor:'var(--pick)',fillOpacity:1}).bindTooltip(tip).addTo(layer);
  L.circleMarker(r.d,{radius:4,color:'#fff',weight:1.5,fillColor:'var(--drop)',fillOpacity:1}).bindTooltip(tip).addTo(layer);
  b.push(r.o,r.d)});map.fitBounds(b,{padding:[30,30]});table(S)}
function table(S){let h='<tr><th>Req</th><th>Time</th><th>Party</th><th>From → to</th><th>Drive</th><th>'+(S.requests[0].rules?'Lyft rules':'Outcome')+'</th></tr>';
 S.requests.forEach(r=>{const out=r.rules?Object.entries(r.rules).filter(([k])=>k!='R0').map(([k,v])=>`<div><b>${k}</b>: ${v}</div>`).join(''):(r.outcome?r.outcome.replace(/_/g,' ')+(r.wait!=null?`<br><span class="tag">wait ${mins(r.wait)}</span>`:''):'');
  h+=`<tr class="req" data-id="${r.id}"><td>${r.id}</td><td>${hm(r.t)}</td><td>${r.party}</td><td>${r.oz} → ${r.dz}</td><td>${mins(r.direct)}</td><td>${out}</td></tr>`});
 const t=document.getElementById('tbl');t.innerHTML=h;t.querySelectorAll('tr.req').forEach(tr=>tr.onclick=()=>{t.querySelectorAll('tr.sel').forEach(x=>x.classList.remove('sel'));tr.classList.add('sel');
  Object.values(lines).forEach(l=>l.setStyle({opacity:.15}));const l=lines[tr.dataset.id];l.setStyle({opacity:1,color:'var(--sel)',weight:5});map.fitBounds(l.getBounds(),{padding:[60,60]})})}
const lv=document.getElementById('lv');['L1','L2','L3','L4','L5'].forEach(n=>{const bt=document.createElement('button');bt.textContent=n;bt.onclick=()=>{lv.querySelectorAll('button').forEach(x=>x.classList.remove('on'));bt.classList.add('on');
 const nd=document.getElementById('night');if(n==='L5'){nd.innerHTML='Night <input id="nr" type="range" min="0" max="29" value="0"> <b id="nv">00</b>';const s=document.getElementById('nr');s.oninput=()=>{const v=String(s.value).padStart(2,'0');document.getElementById('nv').textContent=v;show('L5 night '+v)};show('L5 night 00')}else{nd.innerHTML='';show(n)}};lv.appendChild(bt)});
lv.firstChild.click();
</script></body></html>"""

if __name__ == "__main__":
    main()
