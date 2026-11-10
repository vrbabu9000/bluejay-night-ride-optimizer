// Midterm deck builder, content draft v0.3. Every number comes from v0.3/data/numbers.json (make_numbers.py) or the
// v0.2 data/deck_numbers.json (backup tables); no simulation is run here.
//   NODE_PATH=<dir with pptxgenjs> APPLY_THEME=<pptx skill>/scripts/apply_theme.js node docs/presentations/midterm/v0.3/build_deck.js
// Main slides 1-22, backup divider 23, backups B1-B9 = slides 24-32. Footer numbers are slide positions.
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const HERE = __dirname;
const FIG = (f) => path.join(HERE, "figures", f);
const OUT = path.join(HERE, "BlueJay_Midterm_v0.3.pptx");
const N = JSON.parse(fs.readFileSync(path.join(HERE, "data", "numbers.json"), "utf8"));
const V2 = JSON.parse(fs.readFileSync(path.join(HERE, "..", "data", "deck_numbers.json"), "utf8"));
const A = N.april, Bt = N.batch, T = N.transfer, P = N.pending;
const RULES = N.rules, NAME = N.names;
const fmt = (x) => x.toLocaleString("en-US");
const pct = (x, d = 0) => (100 * x).toFixed(d) + "%";

const THEME = {
  name: "Night Ride Plain",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1E2933", lt1: "FFFFFF", dk2: "3A4750", lt2: "EEF1F4",
    accent1: "2A78D6", accent2: "EB6834", accent3: "1BAF7A", accent4: "EDA100", accent5: "E87BA4", accent6: "6250D6",
    hlink: "2A78D6", folHlink: "6250D6",
  },
};
const HEX = { ink: "1E2933", muted: "5B6670", faint: "8A939B", tint: "EEF1F4", line: "D5DADF", blue: "2A78D6",
  orange: "EB6834", aqua: "1BAF7A", yellow: "EDA100", magenta: "E87BA4", violet: "6250D6", white: "FFFFFF",
  paleBlue: "E8F1FB", paleOrange: "FFF4EC", paleGreen: "E9F7F1", paleViolet: "EFEDFB" };
// evidence-status badges: always text + colour, never colour alone
const BADGE = { OBSERVED: "1E2933", DERIVED: "2A78D6", ASSUMED: "EB6834", DESIGNED: "6250D6", SIMULATED: "0F7A57",
  CHOSEN: "0F766E", ILLUSTRATIVE: "5B6670", PREDICTION: "6250D6", "NOT IMPLEMENTED": "B23A3A" };
// backup slide positions (main 1-22, divider 23)
const BK = { B1: 24, B2: 25, B3: 26, B4: 27, B5: 28, B6: 29, B7: 30, B8: 31, B9: 32 };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "Testing Lyft transfer decisions for Blue Jay Night Ride (content draft v0.3)";
pres.author = "Team FourSight";
pres.company = "Johns Hopkins University";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: "1E2933" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.9, w: 11.7, h: 1.9, fontSize: 40, bold: true,
      color: "FFFFFF", valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 2.4, fontSize: 18,
      color: "C9D1D8", valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "FFFFFF" },
  margin: [0.5, 0.5, 0.6, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 12.3, h: 0.85, fontSize: 30, bold: true,
      color: "1E2933", valign: "middle" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION",
  background: { color: "EEF1F4" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.6, w: 11.7, h: 1.2, fontSize: 34, bold: true,
      color: "1E2933" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.9, w: 11.7, h: 2.6, fontSize: 16,
      color: "3A4750" }, text: "" } },
  ],
});

// ---------- helpers ----------
let slideNo = 0;
function txt(slide, text, o) {
  slide.addText(text, Object.assign({ isTextBox: true, fontFace: "Calibri", fontSize: 16, color: HEX.ink, margin: 0.05,
    valign: "top" }, o));
}
function source(slide, s) {
  txt(slide, "Source: " + s, { x: 0.5, y: 6.98, w: 10.9, h: 0.32, fontSize: 9.5, color: HEX.faint, valign: "middle" });
}
function badge(slide, kind, x, y, w) {
  w = w || 1.25;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.28, rectRadius: 0.08,
    fill: { color: BADGE[kind] }, line: { color: BADGE[kind] }, objectName: "badge-" + kind });
  txt(slide, kind, { x, y, w, h: 0.28, fontSize: 9.5, bold: true, color: HEX.white, align: "center", valign: "middle", margin: 0 });
}
function box(slide, x, y, w, h, fill, lineColor, o) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, Object.assign({ x, y, w, h, rectRadius: 0.08, fill: { color: fill || HEX.tint },
    line: { color: lineColor || fill || HEX.tint, width: lineColor ? 1.25 : 0.75 } }, o || {}));
}
function arrow(slide, x1, y1, x2, y2, color, dash) {
  const o = { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.001), h: Math.max(Math.abs(y2 - y1), 0.001),
    line: { color: color || HEX.muted, width: 1.5, endArrowType: "triangle", dashType: dash || "solid" } };
  if (x2 < x1) o.flipH = true;
  if (y2 < y1) o.flipV = true;
  slide.addShape(pres.shapes.LINE, o);
}
function line(slide, x1, y1, x2, y2, color, width, dash) {
  slide.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.001),
    h: Math.max(Math.abs(y2 - y1), 0.001), flipV: y2 < y1, line: { color: color || HEX.line, width: width || 1, dashType: dash || "solid" } });
}
function bullets(slide, items, o) {
  const runs = items.map((t, i) => [{ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 5 } }]).flat();
  slide.addText(runs, Object.assign({ isTextBox: true, fontFace: "Calibri", fontSize: 15, color: HEX.ink, valign: "top",
    margin: 0.05 }, o));
}
function link(slide, label, target, o) {
  txt(slide, [{ text: label, options: { hyperlink: { slide: target, tooltip: "Go to slide " + target }, color: HEX.blue } }],
    Object.assign({ fontSize: 11 }, o));
}
function dot(slide, x, y, d, fill, lineColor) {
  slide.addShape(pres.shapes.OVAL, { x: x - d / 2, y: y - d / 2, w: d, h: d, fill: { color: fill }, line: { color: lineColor || fill, width: 1.25 } });
}
function content(title, section, notes) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  slideNo++;
  txt(s, String(slideNo), { x: 12.25, y: 7.0, w: 0.6, h: 0.28, fontSize: 10, color: HEX.faint, align: "right", valign: "middle", margin: 0 });
  if (notes) s.addNotes(notes);
  return s;
}
const chartText = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  legendFontFace: "+mn-lt", titleFontFace: "+mn-lt", catAxisLabelColor: HEX.muted, valAxisLabelColor: HEX.muted,
  valGridLine: { color: "E3E6E9", size: 0.5 }, catGridLine: { style: "none" } };
const chartOpts = (o) => Object.assign({}, chartText, { valGridLine: { color: "E3E6E9", size: 0.5 }, catGridLine: { style: "none" } }, o);
const notesFor = (n, extra) => `Script: speaking_script.md slide ${n}. Explanations: slide_explanations.md §${n}.` + (extra ? " " + extra : "");

// =====================================================================================================
// OPENING
pres.addSection({ title: "Opening" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Opening" });
slideNo++;
s.addText("Testing Lyft transfer decisions for Blue Jay Night Ride", { placeholder: "title" });
s.addText("What aggregate data can tell us · how we built synthetic evenings · what replaying them showed\n\n"
  + "Team FourSight · EN.553.602 Research and Design in Mathematics · Midterm, October 2026\n"
  + "Content draft v0.3 · 20 min presentation + 10 min questions · speakers to be assigned", { placeholder: "body" });
s.addNotes(notesFor(1, "Codes appear only in notes and backups; plain rule names on slides."));

// ---------- 2 ----------
s = content("One booking, several possible outcomes", "Opening", notesFor(2));
box(s, 0.5, 2.85, 2.0, 1.1, HEX.ink);
txt(s, "Booking\n(1–5 passengers)", { x: 0.5, y: 2.85, w: 2.0, h: 1.1, fontSize: 16, bold: true, color: HEX.white, align: "center", valign: "middle" });
const branch = [["Stays with vans", 1.55, HEX.paleBlue, HEX.blue, ["Van reaches the curb → rider boards → dropped off", "Rider cancels while waiting", "No-show: rider absent after a 3-min curb wait"]],
  ["Transferred to Lyft", 4.05, HEX.paleOrange, HEX.orange, ["Lyft reaches the curb → rider boards → dropped off", "Rider cancels before the Lyft arrives", "Lyft no-show: rider absent when the Lyft arrives"]]];
branch.forEach(([h, y, fill, c, outs]) => {
  arrow(s, 2.5, 3.4, 3.2, y + 0.3, c);
  box(s, 3.2, y, 2.6, 0.6, fill, c);
  txt(s, h, { x: 3.2, y, w: 2.6, h: 0.6, fontSize: 16, bold: true, align: "center", valign: "middle" });
  outs.forEach((t, i) => {
    const oy = y - 0.4 + i * 0.6;
    arrow(s, 5.8, y + 0.3, 6.3, oy + 0.24, c);
    txt(s, t, { x: 6.35, y: oy, w: 6.4, h: 0.48, fontSize: 14, valign: "middle" });
  });
});
txt(s, "the dispatcher decides (a person today; a rule in our model)", { x: 0.4, y: 4.0, w: 2.3, h: 0.5, align: "center", fontSize: 11, color: HEX.muted, italic: true });
const defs = [["Booking", "one request in the app"], ["Passenger", "one person in a booking"], ["Curb arrival", "the vehicle reaches the pickup point"],
  ["Pickup", "the rider boards"], ["Cancellation", "the rider gives up before pickup"]];
defs.forEach(([h, b], i) => {
  const x = 0.5 + i * 2.48;
  box(s, x, 5.45, 2.36, 0.95, HEX.tint);
  txt(s, [{ text: h, options: { bold: true, breakLine: true } }, { text: b, options: { color: HEX.muted } }], { x: x + 0.08, y: 5.5, w: 2.2, h: 0.85, fontSize: 13 });
});
txt(s, "Our question: when should a waiting booking be moved to Lyft?", { x: 0.5, y: 6.45, w: 12.3, h: 0.45, fontSize: 18, bold: true, color: HEX.blue });
source(s, "JHU Night Ride service pages (3-min curb wait); scenario_spec.md §5–§6.");

// ---------- 3 ----------
s = content("What we originally proposed", "Opening", notesFor(3, "Corrections in backup B9; the proposal deck itself is unchanged."));
txt(s, "September proposal: relied on trip-level records", { x: 0.5, y: 1.3, w: 6.0, h: 0.4, fontSize: 18, bold: true });
const props = ["Replay real service nights", "Compare simple rules with an optimization model re-solved as requests arrive",
  "Choose Lyft overflow inside that optimizer", "Treat published service targets as hard limits"];
props.forEach((t, i) => {
  box(s, 0.5, 1.85 + i * 1.05, 6.0, 0.88, HEX.tint);
  txt(s, String(i + 1), { x: 0.6, y: 1.85 + i * 1.05, w: 0.5, h: 0.88, fontSize: 24, bold: true, color: HEX.blue, valign: "middle" });
  txt(s, t, { x: 1.15, y: 1.85 + i * 1.05, w: 5.25, h: 0.88, fontSize: 16, valign: "middle" });
});
txt(s, "Three proposal numbers we corrected", { x: 7.0, y: 1.3, w: 5.8, h: 0.4, fontSize: 18, bold: true });
const corr = [["“About 5,100 rides per hour at 6 pm”", "a 30-day total: about 170 in one evening's 6 pm hour"],
  ["“About 28 vans”", "the “All services” average (27.6), not a Homewood-only count"],
  ["“1 in 4 trips overflow to Lyft”", "24.5% of riders rode Lyft: a share of riders, not of trips"]];
corr.forEach(([a, b], i) => {
  const y = 1.85 + i * 1.4;
  box(s, 7.0, y, 5.8, 1.22, HEX.paleOrange);
  txt(s, a, { x: 7.15, y: y + 0.08, w: 5.5, h: 0.4, fontSize: 15, bold: true, strike: "sngStrike", color: HEX.muted });
  txt(s, "→ " + b, { x: 7.15, y: y + 0.5, w: 5.5, h: 0.65, fontSize: 15 });
});
link(s, "Corrected claims and dates: backup B9 →", BK.B9, { x: 7.0, y: 6.15, w: 5.8, h: 0.35 });
source(s, "BlueJayNightRide_Proposal.pptx (September); April 2026 dashboards; methodology v1.4 §1a.");

// ---------- 4 ----------
s = content("What April's dashboards actually contain", "Opening", notesFor(4, "Restricted source: show digitized aggregates only, never screenshots."));
box(s, 0.5, 1.35, 6.05, 5.45, HEX.paleGreen);
txt(s, "Totals and shares (April 2026)", { x: 0.75, y: 1.45, w: 5.6, h: 0.45, fontSize: 18, bold: true, color: "0F7A57" });
const has = [["Bookings by status", fmt(A.status.requests) + " in the month"], ["Completed rides by hour", "about 5,100 at 6 pm, summed over 30 days"],
  ["Vehicles on duty by hour", A.vehicles["18:00"] + " at 6 pm, all services"], ["Pickup and drop-off maps", "counts per place, 188 places"],
  ["Wait-time percentiles", "per month and hour"], ["Riders by van and by Lyft", fmt(A.riders) + " riders, " + pct(A.lyft_rider_share, 1) + " by Lyft"]];
has.forEach(([h, b], i) => {
  txt(s, [{ text: "✓  " + h, options: { bold: true, breakLine: true } }, { text: "     " + b, options: { color: HEX.muted } }],
    { x: 0.75, y: 2.0 + i * 0.78, w: 5.6, h: 0.75, fontSize: 15 });
});
box(s, 6.8, 1.35, 6.0, 5.45, HEX.paleOrange);
txt(s, "Never a single journey", { x: 7.05, y: 1.45, w: 5.6, h: 0.45, fontSize: 18, bold: true, color: HEX.orange });
["Who asked, and when", "From where to where", "How long that rider waited", "What happened next: boarded, gave up, moved to Lyft"]
  .forEach((t, i) => txt(s, "✗  " + t, { x: 7.05, y: 2.0 + i * 0.78, w: 5.6, h: 0.6, fontSize: 16, bold: true }));
txt(s, "So before testing any policy, we had to work out what the totals meant.", { x: 7.05, y: 5.4, w: 5.5, h: 1.0, fontSize: 16, italic: true });
source(s, "April 2026 operations dashboards (restricted; digitized aggregates in data/processed); methodology v1.4 §3.");

// =====================================================================================================
// INVESTIGATING THE DATA
pres.addSection({ title: "Investigating the data" });
s = content("First, we investigated the numbers", "Investigating the data", notesFor(5));
const qs = [["How many requests does a van face, and how many riders each?", "≈ 5,100", "completed rides at 6 pm (30-day total)", "slides 6 and 8"],
  ["Which pickups go with which drop-offs?", "188", "map places with pickup and drop-off counts only", "slide 7"],
  ["What do “Canceled” and “No Show” count?", fmt(A.status.canceled), "bookings ended “Canceled”", "slides 9–10"]];
qs.forEach(([q, n, l, w], i) => {
  const x = 0.5 + i * 4.15;
  box(s, x, 1.45, 3.95, 4.6, HEX.tint);
  txt(s, q, { x: x + 0.2, y: 1.75, w: 3.55, h: 1.2, fontSize: 20, bold: true });
  txt(s, n, { x: x + 0.2, y: 3.1, w: 3.55, h: 0.9, fontSize: 44, bold: true, color: HEX.blue });
  txt(s, l, { x: x + 0.2, y: 4.05, w: 3.55, h: 0.8, fontSize: 15, color: HEX.muted });
  txt(s, "→ " + w, { x: x + 0.2, y: 5.55, w: 3.55, h: 0.4, fontSize: 13, color: HEX.muted });
});
txt(s, "Each answer supplied one part of a synthetic evening, and exposed one assumption.", { x: 0.5, y: 6.2, w: 12.3, h: 0.4, fontSize: 17, italic: true });
txt(s, "Labels used from here on:  OBSERVED read from April dashboards · DERIVED computed from observed numbers · ASSUMED our choice · DESIGNED hand-built test evening · SIMULATED output of our model",
  { x: 0.5, y: 6.6, w: 12.3, h: 0.35, fontSize: 11.5, color: HEX.muted });
source(s, "April 2026 dashboards (digitized aggregates).");

// ---------- 6 ----------
s = content("How many requests should our scenario contain?", "Investigating the data", notesFor(6, "Codes: D-35, D-36, D-49."));
s.addChart(pres.charts.BAR, [{ name: "Completed rides, 30-day total", labels: A.hours.map((h) => h + ":00"), values: A.completed_by_hour }],
  chartOpts({ x: 0.4, y: 1.3, w: 6.6, h: 5.4, barDir: "col", chartColors: [HEX.blue], showLegend: false, showTitle: true,
    title: "Completed rides by hour, summed over 30 April days (digitized)", titleFontSize: 14, titleColor: HEX.ink,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 11, dataLabelColor: HEX.ink, dataLabelFormatCode: "#,##0",
    catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, valAxisLabelFormatCode: "#,##0", barGapWidthPct: 60 }));
badge(s, "OBSERVED", 5.6, 1.75, 1.25);
const chain = [["≈ 5,100 ÷ 30", "≈ 170", "completed rides in one evening's 6 pm hour", "DERIVED"],
  ["× " + A.r_per_c.toFixed(2), "≈ 355", "bookings in that hour (2.09 bookings per completed ride)", "DERIVED"],
  ["÷ " + A.vehicles["18:00"], "≈ " + A.rho["18:00"], "bookings per vehicle per hour at 6 pm (unrounded inputs)", "DERIVED"],
  ["× 5 vans", A.five_van.join(" / "), "bookings per hour, first three hours of a five-van evening: 168 in all (each hour uses its own rides and vehicles)", "DERIVED"]];
chain.forEach(([op, v, l, b], i) => {
  const y = 1.4 + i * 1.12;
  box(s, 7.3, y, 5.5, 0.98, i === 3 ? HEX.paleBlue : HEX.tint);
  txt(s, op, { x: 7.42, y: y + 0.08, w: 1.55, h: 0.4, fontSize: 15, color: HEX.muted });
  txt(s, v, { x: 8.95, y: y + 0.02, w: 2.4, h: 0.5, fontSize: 24, bold: true, color: HEX.blue });
  badge(s, b, 11.45, y + 0.1, 1.2);
  txt(s, l, { x: 7.42, y: y + 0.5, w: 5.3, h: 0.46, fontSize: i === 3 ? 11.5 : 12.5 });
});
txt(s, "Unknown: how many vehicles served Homewood, and how many bookings were repeats. The pilot (slide 16) uses 2 vans and 28 bookings in one hour.",
  { x: 7.3, y: 5.95, w: 5.5, h: 0.85, fontSize: 12.5, color: HEX.muted });
source(s, "April dashboards: rides by hour, status totals, vehicles on duty; decision log D-35, D-36, D-49.");

// ---------- 7 ----------
s = content("Pickup and drop-off maps do not identify trips", "Investigating the data", notesFor(7, "Gravity prior + iterative proportional fitting, D-18."));
txt(s, "Same place totals, different trips", { x: 0.5, y: 1.3, w: 6.3, h: 0.4, fontSize: 18, bold: true });
function toy(x, y, cells, title) {
  txt(s, title, { x, y, w: 2.9, h: 0.35, fontSize: 14, bold: true, color: HEX.muted });
  const rows = [[{ text: "", options: { fill: { color: HEX.white } } }, "to X", "to Y", "total"],
    ["from A", String(cells[0]), String(cells[1]), "2"], ["from B", String(cells[2]), String(cells[3]), "2"], ["total", "2", "2", "4"]];
  s.addTable(rows.map((r, i) => r.map((c, j) => (typeof c === "object" ? c : { text: c, options: {
    bold: i === 0 || j === 0 || i === 3 || j === 3, align: "center", color: HEX.ink,
    fill: { color: (i === 3 || j === 3) && i > 0 && j > 0 ? HEX.paleGreen : (i === 0 || j === 0 ? HEX.tint : HEX.white) } } }))),
    { x, y: y + 0.4, w: 2.9, colW: [0.8, 0.7, 0.7, 0.7], rowH: 0.42, fontSize: 14, fontFace: "Calibri", color: HEX.ink,
      border: { type: "solid", pt: 0.75, color: HEX.line } });
}
toy(0.5, 1.8, [2, 0, 0, 2], "Trips 1");
toy(3.75, 1.8, [1, 1, 1, 1], "Trips 2");
txt(s, "Green cells are all the maps show. Both tables match them exactly.", { x: 0.5, y: 3.95, w: 6.3, h: 0.4, fontSize: 13, color: HEX.muted });
box(s, 0.5, 4.5, 6.3, 2.25, HEX.paleOrange);
badge(s, "ASSUMED", 0.7, 4.65, 1.2);
txt(s, "Our pairing choice", { x: 2.0, y: 4.6, w: 4.5, h: 0.4, fontSize: 16, bold: true });
bullets(s, ["Nearby trips more likely: weight shrinks about 10% per extra minute of driving",
  "Then scaled until both map totals match exactly", "The shrink rate is our choice; the data cannot identify it"],
  { x: 0.7, y: 5.05, w: 5.95, h: 1.65, fontSize: 14 });
s.addImage({ path: FIG("map_synthetic_hour.png"), x: 7.4, y: 1.3, w: 5.3, h: 5.3 * 4.4 / 4.2 > 5.6 ? 5.6 : 5.3 * 4.4 / 4.2, sizing: { type: "contain", w: 5.3, h: 5.6 } });
source(s, "April pickup and drop-off maps (place totals); decision log D-18; map: the first synthetic pilot night.");

// ---------- 8 ----------
s = content("An average group size leaves many possibilities", "Investigating the data", notesFor(8, "D-38 (distribution), D-33 (XL for party of five)."));
const G = N.groups;
s.addChart(pres.charts.BAR, [
  { name: "Hypothetical H1 (mean 1.386)", labels: ["1", "2", "3", "4", "5"], values: G.h1 },
  { name: "Hypothetical H2 (mean 1.386)", labels: ["1", "2", "3", "4", "5"], values: G.h2 },
  { name: "Our assumption (mean 1.405)", labels: ["1", "2", "3", "4", "5"], values: G.ours },
], chartOpts({ x: 0.4, y: 1.3, w: 7.6, h: 5.4, barDir: "col", barGrouping: "clustered", chartColors: [HEX.faint, HEX.yellow, HEX.blue],
  showLegend: true, legendPos: "t", legendFontSize: 12, showTitle: true, title: "Share of bookings by party size", titleFontSize: 14,
  titleColor: HEX.ink, showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 9, dataLabelFormatCode: "0%", dataLabelColor: HEX.ink,
  valAxisLabelFormatCode: "0%", valAxisMinVal: 0, valAxisMaxVal: 0.9, catAxisLabelFontSize: 13, valAxisLabelFontSize: 11,
  showCatAxisTitle: true, catAxisTitle: "passengers in the booking", catAxisTitleFontSize: 12, catAxisTitleColor: HEX.muted, catAxisTitleFontFace: "+mn-lt" }));
box(s, 8.3, 1.4, 4.5, 1.45, HEX.tint);
badge(s, "DERIVED", 8.45, 1.5, 1.2);
txt(s, "1.386", { x: 9.75, y: 1.42, w: 2.9, h: 0.6, fontSize: 30, bold: true, color: HEX.blue });
txt(s, "van passengers per completed van booking (ratio of two observed totals; counts only completed van bookings)", { x: 8.45, y: 2.0, w: 4.25, h: 0.8, fontSize: 12.5 });
const g3 = [["H1", G.share_3plus[0]], ["H2", G.share_3plus[1]], ["Ours", G.share_3plus[2]]];
txt(s, "Bookings with 3 or more riders", { x: 8.3, y: 3.05, w: 4.5, h: 0.4, fontSize: 15, bold: true });
g3.forEach(([n, v], i) => txt(s, [{ text: pct(v, v === 0.123 ? 1 : 0), options: { bold: true, fontSize: 24, color: HEX.ink, breakLine: true } },
  { text: n, options: { fontSize: 12, color: HEX.muted } }], { x: 8.3 + i * 1.5, y: 3.45, w: 1.45, h: 0.95, align: "center" }));
box(s, 8.3, 4.6, 4.5, 2.15, HEX.paleOrange);
badge(s, "ASSUMED", 8.45, 4.7, 1.2);
bullets(s, ["Same mean, different seat needs", "Ours covers all bookings, so its mean (1.405) need not equal April's", "1% parties of five; they need a larger Lyft", "Bar labels rounded"],
  { x: 8.45, y: 5.05, w: 4.25, h: 1.65, fontSize: 13.5 });
source(s, "April dashboards (riders, completed van bookings); decision log D-38, D-33. H1 and H2 are illustrations, not data.");

// ---------- 9 ----------
s = content("What does “Canceled” mean?", "Investigating the data", notesFor(9, "Patience: Weibull shape 1.5, median 18 min, placeholder (D-39); share of 'Canceled' that is abandonment 50-75% (D-49)."));
const st = A.status;
s.addChart(pres.charts.BAR, [
  { name: "Completed", labels: ["April bookings"], values: [st.completed] },
  { name: "Canceled", labels: ["April bookings"], values: [st.canceled] },
  { name: "No Show", labels: ["April bookings"], values: [st.noshow] },
], chartOpts({ x: 0.4, y: 1.3, w: 12.5, h: 1.9, barDir: "bar", barGrouping: "stacked", chartColors: [HEX.aqua, HEX.orange, HEX.yellow],
  showLegend: true, legendPos: "b", legendFontSize: 12, showValue: true, dataLabelPosition: "ctr", dataLabelFormatCode: "#,##0",
  dataLabelFontSize: 13, dataLabelColor: HEX.ink, valAxisHidden: true, catAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: st.requests, valGridLine: { style: "none" }, barGapWidthPct: 20 }));
txt(s, fmt(st.canceled) + " of " + fmt(st.requests) + " bookings (" + pct(st.canceled_share, 0) + ") ended “Canceled”", { x: 0.5, y: 3.25, w: 12.3, h: 0.45, fontSize: 18, bold: true });
txt(s, "One label, two different events", { x: 0.5, y: 3.8, w: 6.0, h: 0.4, fontSize: 15, bold: true, color: HEX.muted });
box(s, 0.5, 4.25, 3.6, 1.5, HEX.paleOrange);
txt(s, [{ text: "Rider gave up", options: { bold: true, breakLine: true } }, { text: "assumed 50–75% of “Canceled” (a range to test)", options: { color: HEX.muted } }],
  { x: 0.65, y: 4.35, w: 3.3, h: 1.3, fontSize: 15 });
box(s, 4.3, 4.25, 3.6, 1.5, HEX.paleOrange);
txt(s, [{ text: "Moved to Lyft by the dispatcher", options: { bold: true, breakLine: true } }, { text: "assumed to close as “Canceled” in the van system (not confirmed)", options: { color: HEX.muted } }],
  { x: 4.45, y: 4.35, w: 3.3, h: 1.3, fontSize: 15 });
txt(s, "The data cannot separate the two.", { x: 0.5, y: 5.85, w: 7.4, h: 0.4, fontSize: 14, italic: true });
box(s, 8.3, 3.8, 4.5, 2.9, HEX.tint);
badge(s, "ASSUMED", 8.45, 3.92, 1.2);
txt(s, "Patience is a hidden deadline", { x: 8.45, y: 4.28, w: 4.2, h: 0.4, fontSize: 16, bold: true });
bullets(s, ["To let riders give up in the model, each rider gets a personal deadline the dispatcher cannot see", "Placeholder: median 18 minutes, until calibrated",
  "Results depend on it (slide 19)"], { x: 8.45, y: 4.72, w: 4.25, h: 1.9, fontSize: 13.5 });
source(s, "April dashboard status totals (the digitized sums also show 99 “Denied”); decision log D-39, D-49.");

// ---------- 10 ----------
s = content("Why the no-show denominator matters", "Investigating the data", notesFor(10, "D-40, D-48; methodology Appendix C."));
const fr = [["All bookings", fmt(st.noshow), fmt(st.requests), pct(A.noshow_all, 1), "Under our status mapping, a cancelled booking never had a vehicle at the curb", HEX.tint],
  ["Van arrivals (completed + no-show)", fmt(st.noshow), fmt(A.van_arrivals), pct(A.noshow_arrival, 1), "A no-show can only happen when a vehicle arrives", HEX.paleBlue]];
fr.forEach(([h, num, den, r, why, fill], i) => {
  const x = 0.5 + i * 6.25;
  box(s, x, 1.4, 6.0, 3.6, fill);
  txt(s, "Divide by " + h.toLowerCase(), { x: x + 0.2, y: 1.5, w: 5.6, h: 0.45, fontSize: 17, bold: true });
  txt(s, num, { x: x + 0.2, y: 2.05, w: 2.6, h: 0.5, fontSize: 24, align: "center" });
  line(s, x + 0.4, 2.62, x + 2.6, 2.62, HEX.ink, 1.5);
  txt(s, den, { x: x + 0.2, y: 2.68, w: 2.6, h: 0.5, fontSize: 24, align: "center" });
  txt(s, "= " + r, { x: x + 2.9, y: 2.25, w: 2.9, h: 0.75, fontSize: 40, bold: true, color: i ? HEX.blue : HEX.muted });
  txt(s, why, { x: x + 0.2, y: 3.6, w: 5.6, h: 0.8, fontSize: 14, color: HEX.muted });
  if (i) badge(s, "DERIVED", x + 4.55, 4.55, 1.25);
});
box(s, 0.5, 5.25, 12.3, 1.05, HEX.paleOrange);
badge(s, "ASSUMED", 0.7, 5.38, 1.2);
txt(s, "We use 8.9% per vehicle arrival, provisionally. It holds only if “No Show” was recorded after a real van arrival and “Completed” counts van trips. The same count gives two rates, depending on what you divide by.",
  { x: 2.05, y: 5.3, w: 10.6, h: 0.95, fontSize: 15 });
source(s, "April dashboard status totals; decision log D-40, D-48; methodology v1.4 Appendix C.");

// =====================================================================================================
// MODEL AND EXPERIMENT
pres.addSection({ title: "Model and experiment" });
s = content("Our synthetic evening is assembled", "Model and experiment", notesFor(11, "Designed evenings = L1-L4; randomized nights = L5."));
txt(s, "Inputs", { x: 0.5, y: 1.3, w: 3.9, h: 0.4, fontSize: 16, bold: true, color: HEX.muted });
const ins = [["Bookings: time, place, party size", "DERIVED"], ["Trip pairing", "ASSUMED"], ["Vans on duty", "DERIVED"], ["Travel times: road network × 1.2", "DERIVED"],
  ["Hidden: patience deadline", "ASSUMED"], ["Hidden: present at the curb?", "DERIVED"], ["Hidden: Lyft delay", "ASSUMED"]];
ins.forEach(([t, b], i) => {
  const y = 1.72 + i * 0.67;
  box(s, 0.5, y, 3.9, 0.58, i >= 4 ? HEX.paleViolet : HEX.tint);
  txt(s, t, { x: 0.6, y, w: 2.5, h: 0.58, fontSize: 12.5, valign: "middle" });
  badge(s, b, 3.12, y + 0.15, 1.15);
});
arrow(s, 4.5, 4.0, 5.05, 4.0, HEX.ink);
box(s, 5.1, 1.75, 3.3, 4.55, HEX.ink);
txt(s, [{ text: "Simulator", options: { bold: true, fontSize: 20, breakLine: true } },
  { text: "the referee", options: { italic: true, fontSize: 14, breakLine: true } }, { text: " ", options: { breakLine: true } },
  { text: "moves the vans, runs the clock, and reveals a hidden trait only when its moment comes", options: { fontSize: 14 } }],
  { x: 5.25, y: 1.95, w: 3.0, h: 4.2, color: HEX.white, align: "center", valign: "middle" });
arrow(s, 8.5, 4.0, 9.05, 4.0, HEX.ink);
box(s, 9.1, 1.75, 3.7, 2.05, HEX.paleBlue, HEX.blue);
txt(s, [{ text: "Dispatcher sees", options: { bold: true, breakLine: true } }, { text: "(in our model: van optimizer + transfer rule)", options: { italic: true, color: HEX.muted, breakLine: true } },
  { text: "bookings that have arrived, van positions and plans, and predictions", options: {} }], { x: 9.25, y: 1.85, w: 3.4, h: 1.85, fontSize: 14 });
box(s, 9.1, 4.0, 3.7, 2.3, HEX.paleViolet, HEX.violet);
txt(s, [{ text: "Hidden from the dispatcher", options: { bold: true, breakLine: true } },
  { text: "each rider's patience, presence and real Lyft delay; revealed only as events happen", options: {} }], { x: 9.25, y: 4.1, w: 3.4, h: 2.1, fontSize: 14 });
txt(s, "Two kinds of evening: small designed ones with hand-computed answers, and randomized one-hour nights for the pilot.",
  { x: 0.5, y: 6.55, w: 8.6, h: 0.4, fontSize: 13.5, color: HEX.muted });
link(s, "Inputs: B4 →", BK.B4, { x: 9.3, y: 6.58, w: 1.6, h: 0.35 });
link(s, "Event order: B3 →", BK.B3, { x: 10.9, y: 6.58, w: 1.9, h: 0.35 });
source(s, "scenario_spec.md v0.8 §1, §17; methodology v1.4 §2–§3.");

// ---------- 12 ----------
s = content("How the van optimizer chooses a plan", "Model and experiment",
  notesFor(12, "Van optimizer = dispatcher C: restricted route-selection MILP solved with HiGHS; up to 3 new pickups per van. Full formulation: B2."));
const loop = [["Reveal and update", HEX.tint], ["Generate feasible routes", HEX.paleBlue], ["Select compatible routes", HEX.paleBlue],
  ["Evaluate transfer rule", HEX.paleOrange], ["Apply accepted transfers", HEX.paleOrange], ["Re-plan once if needed", HEX.paleBlue],
  ["Execute", HEX.tint], ["Repeat", HEX.tint]];
loop.forEach(([t, f], i) => {
  const x = 0.5 + i * 1.56;
  box(s, x, 1.3, 1.36, 0.82, f);
  txt(s, [{ text: (i + 1) + "  ", options: { bold: true, color: HEX.blue } }, { text: t, options: {} }], { x: x + 0.04, y: 1.3, w: 1.28, h: 0.82, fontSize: 12, valign: "middle", align: "center" });
  if (i < 7) arrow(s, x + 1.37, 1.71, x + 1.55, 1.71, HEX.muted);
});
txt(s, "every 2 minutes and at each new event · blue = route optimizer · orange = transfer rule · grey = simulator", { x: 0.5, y: 2.15, w: 12.3, h: 0.32, fontSize: 11.5, color: HEX.muted });
txt(s, "Step 3: a mixed-integer linear program (MILP) picks one route per van", { x: 0.5, y: 2.6, w: 12.3, h: 0.4, fontSize: 17, bold: true });
badge(s, "ILLUSTRATIVE", 0.5, 3.1, 1.4);
txt(s, "One van; rider 1 has waited 8 min; a party of two has waited 1 min", { x: 2.0, y: 3.06, w: 6.2, h: 0.36, fontSize: 13, color: HEX.muted });
const routes = [["Route A: rider 1 first", "52.5", "13.0", "1.0", "66.5", true], ["Route B: party of two first", "67.5", "12.5", "1.0", "81.0", false]];
s.addTable([[{ text: "Candidate", options: { bold: true } }, { text: "Waiting", options: { bold: true } }, { text: "Riding", options: { bold: true } },
  { text: "Driving", options: { bold: true } }, { text: "Points", options: { bold: true } }],
  ...routes.map(([n, w, r, d, t, win]) => [n, w, r, d, { text: t + (win ? "  ✓ chosen" : ""), options: { bold: true, color: win ? "0F7A57" : HEX.ink } }]),
  ["Postpone a booking", { text: "priced at its earliest physically possible pickup, plus a large constant so the plan serves as many bookings as the candidates allow", options: { colspan: 4, color: HEX.muted } }]],
  { x: 0.5, y: 3.5, w: 7.7, colW: [2.3, 1.1, 1.0, 1.0, 2.3], rowH: 0.42, fontSize: 13, fontFace: "Calibri", color: HEX.ink,
    border: { type: "solid", pt: 0.75, color: HEX.line }, fill: { color: HEX.white } });
txt(s, "In Route B rider 1 waits 16 min; past 15 min each minute costs 10 points.", { x: 0.5, y: 5.45, w: 7.7, h: 0.35, fontSize: 12.5, color: HEX.muted });
box(s, 8.5, 2.6, 4.3, 3.2, HEX.tint);
txt(s, "Points, not money", { x: 8.65, y: 2.68, w: 4.0, h: 0.35, fontSize: 15, bold: true });
bullets(s, ["Waiting, per passenger-minute: 1 point for the first 5 min, then 2.5, 5, 10 and 20 after 5, 10, 15 and 20 min",
  "Riding: 0.5 per passenger-minute; driving: 0.1 per km",
  "Hard limits: seats; pickup before drop-off",
  "Ride-time guardrail max(25 min, 2 × direct + 5): no plan may create or worsen an excess"], { x: 8.65, y: 3.03, w: 4.05, h: 2.75, fontSize: 11.5 });
box(s, 0.5, 5.95, 12.3, 0.88, HEX.paleBlue);
txt(s, "“Optimal” = best among the routes we generated at that moment (up to 3 new pickups per van), proven by the solver. Not over every possible route, and not over the whole evening.",
  { x: 0.65, y: 5.98, w: 10.4, h: 0.82, fontSize: 13.5, valign: "middle" });
link(s, "Formulation: B2 →", BK.B2, { x: 11.1, y: 6.2, w: 1.6, h: 0.35 });
source(s, "model_design.md v0.5 §3–§4; methodology v1.4 §6 (worked example, boarding time omitted); decision log D-29, D-47, D-52.");

// ---------- 13 ----------
s = content("The six transfer decisions we tested", "Model and experiment", notesFor(13, "Codes: R0, R1(10), R1(15), R1u(10), R2(15), R3(2); key in B1."));
const rt = [["Vans only", "—", "never"], ["Wait ten minutes", "time already waited", "≥ 10 min"], ["Wait fifteen minutes", "time already waited", "≥ 15 min"],
  ["Unassigned for ten minutes", "time with no van planning to serve it", "≥ 10 min"],
  ["Predicted total wait exceeds fifteen minutes", "time waited + van's predicted pickup", "> 15 min"],
  ["Lyft arrives sooner", "predicted van pickup vs expected Lyft", "Lyft more than 2 min sooner"]];
const kindFill = ["FFFFFF", HEX.tint, HEX.tint, HEX.paleGreen, HEX.paleBlue, HEX.paleBlue];
s.addTable([[{ text: "Rule", options: { bold: true, color: HEX.white, fill: { color: HEX.ink } } },
  { text: "What it reads", options: { bold: true, color: HEX.white, fill: { color: HEX.ink } } },
  { text: "Moves the booking to Lyft when", options: { bold: true, color: HEX.white, fill: { color: HEX.ink } } }],
  ...rt.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: j === 0, fill: { color: kindFill[i] } } })))],
  { x: 0.5, y: 1.3, w: 7.4, colW: [3.0, 2.6, 1.8], rowH: 0.62, fontSize: 13.5, fontFace: "Calibri", color: HEX.ink,
    border: { type: "solid", pt: 0.75, color: HEX.line } });
txt(s, "grey: waiting-time rules · green: assignment rule · blue: prediction rules. Only bookings still waiting, with no van already driving to them.",
  { x: 0.5, y: 5.75, w: 7.4, h: 0.6, fontSize: 12, color: HEX.muted });
box(s, 8.2, 1.3, 4.6, 5.45, HEX.paleBlue);
txt(s, "“Lyft arrives sooner”, at one decision moment", { x: 8.35, y: 1.38, w: 4.3, h: 0.65, fontSize: 15, bold: true });
// mini timeline
const tl0 = 8.45, tlw = 4.1;
line(s, tl0, 3.1, tl0 + tlw, 3.1, HEX.ink, 1.25);
dot(s, tl0, 3.1, 0.18, HEX.ink);
txt(s, "now", { x: tl0 - 0.3, y: 3.22, w: 0.6, h: 0.3, fontSize: 11, align: "center" });
s.addShape(pres.shapes.RECTANGLE, { x: tl0, y: 2.55, w: 0.8, h: 0.32, fill: { color: HEX.yellow }, line: { color: HEX.yellow } });
txt(s, "2 min", { x: tl0, y: 2.55, w: 0.8, h: 0.32, fontSize: 9.5, align: "center", valign: "middle", margin: 0 });
s.addShape(pres.shapes.RECTANGLE, { x: tl0 + 0.8, y: 2.55, w: 2.0, h: 0.32, fill: { color: HEX.orange }, line: { color: HEX.orange } });
txt(s, "typical 8-min Lyft delay", { x: tl0 + 0.8, y: 2.55, w: 2.0, h: 0.32, fontSize: 9.5, align: "center", valign: "middle", color: HEX.white, margin: 0 });
dot(s, tl0 + 2.8, 3.1, 0.2, HEX.orange);
txt(s, "expected Lyft", { x: tl0 + 1.95, y: 3.22, w: 1.2, h: 0.3, fontSize: 11, align: "center" });
dot(s, tl0 + 3.95, 3.1, 0.2, HEX.white, HEX.blue);
txt(s, "predicted van", { x: tl0 + 3.0, y: 3.22, w: 1.3, h: 0.3, fontSize: 11, align: "center", color: HEX.blue });
line(s, tl0 + 2.8, 3.62, tl0 + 3.95, 3.62, HEX.ink, 1);
txt(s, "gap > 2 min → transfer", { x: tl0 + 2.0, y: 3.67, w: 2.0, h: 0.3, fontSize: 11, bold: true, align: "center" });
bullets(s, ["Expected Lyft pickup = now + 2-min ordering lag (time to place the Lyft order, assumed) + typical 8-min delay",
  "Transfer only if that is more than 2 minutes sooner than the van plan's predicted pickup",
  "Both are predictions; the real Lyft delay is hidden"], { x: 8.35, y: 4.15, w: 4.3, h: 2.55, fontSize: 12.5 });
link(s, "Code key: B1 →", BK.B1, { x: 0.5, y: 6.4, w: 2.5, h: 0.35 });
source(s, "scenario_spec.md v0.8 §6; src/sim/lyft.py. Thresholds fixed before any run.");

// ---------- 14 ----------
s = content("One request: compare van versus Lyft", "Model and experiment",
  notesFor(14, "Designed evening L4 under R3(2), request R011, decision epoch 1020 s; Lyft delay fixed at 8 min by design, consent 0.9."));
badge(s, "DESIGNED", 0.5, 1.3, 1.25);
txt(s, "A small designed evening, separate from the randomized pilot. Rule: “Lyft arrives sooner”.", { x: 1.85, y: 1.27, w: 10.9, h: 0.36, fontSize: 14, color: HEX.muted });
const tsec = (c) => { const [h, m, x] = c.split(":").map(Number); return (h - 18) * 3600 + m * 60 + x; };
const t0 = tsec("18:15:00"), t1 = tsec("18:32:00"), X0 = 0.8, XW = 11.8;
const tx = (c) => X0 + XW * (tsec(c) - t0) / (t1 - t0);
const YL = 4.1;
line(s, X0, YL, X0 + XW, YL, HEX.ink, 1.5);
for (let m = 15; m <= 32; m++) {
  const x = X0 + XW * (m * 60 - (t0 - 0)) / (t1 - t0) - XW * 0 ;
}
[15, 20, 25, 30].forEach((m) => {
  const x = tx(`18:${m}:00`);
  line(s, x, YL - 0.07, x, YL + 0.07, HEX.ink, 1);
  txt(s, `18:${m}`, { x: x - 0.4, y: YL + 0.1, w: 0.8, h: 0.28, fontSize: 10, color: HEX.faint, align: "center" });
});
// wait bar: request -> Lyft curb
s.addShape(pres.shapes.RECTANGLE, { x: tx(T.request), y: YL - 0.12, w: tx(T.lyft_curb) - tx(T.request), h: 0.24, fill: { color: HEX.yellow, transparency: 55 }, line: { color: HEX.yellow, width: 0 } });
const evs = [[T.request, "Request", T.request, "up", HEX.ink, 1.15], [T.decision, "Decision: compare", T.decision, "down", HEX.ink, 0.65],
  [T.booked, "Lyft ordered", T.booked, "up", HEX.orange, 0.55], [T.lyft_curb, "Lyft at the curb", T.lyft_curb, "down", HEX.orange, 0.65],
  [T.dropped, "Dropped off by the Lyft", T.dropped, "down", HEX.ink, 1.35]];
evs.forEach(([c, l, t, dir, col, off]) => {
  const x = tx(c);
  dot(s, x, YL, 0.2, col);
  const y = dir === "up" ? YL - off - 0.55 : YL + off;
  line(s, x, dir === "up" ? y + 0.55 : YL + 0.1, x, dir === "up" ? YL - 0.1 : y, HEX.line, 1);
  txt(s, [{ text: l, options: { bold: true, breakLine: true } }, { text: t, options: { color: HEX.muted } }], { x: x - 0.9, y, w: 1.8, h: 0.55, fontSize: 12, align: "center" });
});
// predicted van (prediction only)
const xv = tx(T.pred_van);
dot(s, xv, YL, 0.22, HEX.white, HEX.violet);
line(s, xv, YL - 0.12, xv, YL - 1.1, HEX.violet, 1, "dash");
txt(s, [{ text: "Predicted van pickup", options: { bold: true, breakLine: true, color: HEX.violet } }, { text: T.pred_van + " (a prediction only)", options: { color: HEX.violet } }],
  { x: xv - 1.2, y: YL - 1.72, w: 2.2, h: 0.6, fontSize: 12, align: "center" });
// gap bracket
line(s, tx(T.expected_lyft), YL - 1.95, xv, YL - 1.95, HEX.ink, 1.25);
line(s, tx(T.expected_lyft), YL - 2.03, tx(T.expected_lyft), YL - 1.87, HEX.ink, 1.25);
line(s, xv, YL - 2.03, xv, YL - 1.87, HEX.ink, 1.25);
txt(s, T.gap + " sooner > 2 min → transfer", { x: tx(T.expected_lyft) - 1.6, y: YL - 2.4, w: 3.6, h: 0.35, fontSize: 13, bold: true, align: "center" });
txt(s, "Wait from request to curb: " + T.wait, { x: tx(T.request) - 0.1, y: YL + 1.55, w: 5.0, h: 0.35, fontSize: 13, bold: true, color: "8A6400" });
box(s, 0.5, 5.95, 12.3, 0.9, HEX.tint);
txt(s, `At ${T.decision}: expected Lyft = ${T.decision} + 2-min ordering lag + 8-min typical delay = ${T.expected_lyft}. On this designed evening the delay is fixed, so the Lyft arrived exactly when expected. What the van would have done is never observed.`,
  { x: 0.65, y: 5.98, w: 12.0, h: 0.84, fontSize: 13.5, valign: "middle" });
source(s, "outputs/sim/L4_R3-2 (epochs.jsonl, outcomes.csv: request R011); scenario_spec.md §6.");

// ---------- 15 ----------
s = content("Testing exposed an optimistic postponement price", "Model and experiment",
  notesFor(15, "Original pending price vs A (chosen, provisional) vs B (route-based); D-53. R002 example from the math review §7. Full table: B5."));
txt(s, "A check on the optimizer before we compare rules", { x: 0.5, y: 1.25, w: 12.3, h: 0.4, fontSize: 14, color: HEX.muted, italic: true });
txt(s, "1  Underpricing: at 18:15 on the designed evening, a party of five has waited 15 min", { x: 0.5, y: 1.75, w: 6.1, h: 0.6, fontSize: 14, bold: true });
s.addChart(pres.charts.BAR, [{ name: "Points", labels: ["Price charged for postponing (points)", "Price if served at the earliest real pickup, " + P.r002.earliest_pickup + " (points)"],
  values: [P.r002.charged_original_pts, P.r002.charged_at_earliest_pts] }],
  chartOpts({ x: 0.4, y: 2.4, w: 6.1, h: 3.2, barDir: "bar", chartColors: [HEX.orange, HEX.ink], showLegend: false, showValue: true,
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelFontSize: 13, dataLabelColor: HEX.ink, valAxisHidden: true,
    valGridLine: { style: "none" }, catAxisLabelFontSize: 12.5, valAxisMaxVal: 520, catAxisOrientation: "maxMin", barGapWidthPct: 50 }));
txt(s, "Postponing looked cheaper than any service a van could really give, so the longest waiters were left waiting.",
  { x: 0.5, y: 5.6, w: 6.0, h: 0.65, fontSize: 13, color: HEX.muted });
txt(s, "2  Controlled comparison: whole designed evening, vans only (third version: B5)", { x: 6.9, y: 1.75, w: 5.9, h: 0.6, fontSize: 14, bold: true });
s.addTable([[{ text: "", options: {} }, { text: "First version", options: { bold: true } }, { text: "Chosen", options: { bold: true, color: "0F7A57" } }],
  ["Longest wait", P.original.max + " min", { text: P.A.max + " min", options: { bold: true } }],
  ["Mean wait", P.original.mean + " min", P.A.mean + " min"], ["Median wait", P.original.median + " min", P.A.median + " min"],
  ["Extra variables", "0", "0"]],
  { x: 6.9, y: 2.45, w: 5.9, colW: [2.1, 1.9, 1.9], rowH: 0.42, fontSize: 13.5, fontFace: "Calibri", color: HEX.ink,
    border: { type: "solid", pt: 0.75, color: HEX.line } });
txt(s, "Waiting was redistributed, not reduced on average.", { x: 6.9, y: 4.6, w: 5.9, h: 0.35, fontSize: 12.5, color: HEX.muted });
box(s, 6.9, 5.0, 2.85, 1.3, HEX.paleGreen);
badge(s, "CHOSEN", 7.0, 5.08, 1.0);
txt(s, "3  Price the earliest physically possible pickup", { x: 7.0, y: 5.4, w: 2.65, h: 0.85, fontSize: 12.5 });
box(s, 9.95, 5.0, 2.85, 1.3, HEX.paleViolet);
txt(s, "4  Still optimistic: ignores the nearest van's other work", { x: 10.05, y: 5.1, w: 2.65, h: 1.15, fontSize: 12.5, valign: "middle" });
link(s, "Three formulations compared: B5 →", BK.B5, { x: 0.5, y: 6.4, w: 4.0, h: 0.35 });
source(s, "outputs/sim/d53_experiment; decision log D-53; independent math review (21 Oct) §7. Provisional choice.");

// ---------- 16 ----------
s = content("Replaying the same evening fairly", "Model and experiment", notesFor(16, "L5 pilot: D-56 settings, D-57 batch (batch_L5_v1)."));
box(s, 0.5, 1.6, 3.2, 3.6, HEX.ink);
txt(s, [{ text: "One synthetic night", options: { bold: true, fontSize: 19, breakLine: true } }, { text: " ", options: { breakLine: true } },
  { text: "same bookings", options: { breakLine: true } }, { text: "same hidden patience and presence", options: { breakLine: true } },
  { text: "same Lyft delays", options: {} }], { x: 0.65, y: 1.75, w: 2.9, h: 3.3, fontSize: 14, color: HEX.white, align: "center", valign: "middle" });
RULES.forEach((r, i) => {
  const y = 1.45 + i * 0.66;
  arrow(s, 3.75, 3.4, 4.6, y + 0.27, HEX.muted);
  box(s, 4.65, y, 3.9, 0.54, HEX.tint);
  txt(s, NAME[r], { x: 4.75, y, w: 3.75, h: 0.54, fontSize: 13, valign: "middle" });
});
txt(s, "Only the rule changes, so differences come from the rule.", { x: 0.5, y: 5.45, w: 8.0, h: 0.4, fontSize: 15, bold: true });
const facts = [["30", "synthetic nights, each replayed six ways (not 180 independent nights)"], ["2 vans", "28 bookings in a one-hour night: 14 per van-hour vs April-derived 12.85, plus a 10-min burst"],
  ["5 vans", "the proposed evening: designed, not yet run"]];
facts.forEach(([n, l], i) => {
  const y = 1.45 + i * 1.3;
  box(s, 8.9, y, 3.9, 1.15, i === 2 ? HEX.paleOrange : HEX.paleBlue);
  txt(s, n, { x: 9.0, y: y + 0.05, w: 1.35, h: 1.05, fontSize: 26, bold: true, color: i === 2 ? HEX.orange : HEX.blue, valign: "middle" });
  txt(s, l, { x: 10.3, y: y + 0.05, w: 2.45, h: 1.05, fontSize: 12.5, valign: "middle" });
});
box(s, 8.9, 5.4, 3.9, 1.35, HEX.paleOrange);
badge(s, "ASSUMED", 9.0, 5.48, 1.2);
txt(s, "Provisional: 2-min ordering lag, riders accept Lyft, 8.9% no-show, placeholder patience, van travel × 1.2", { x: 9.0, y: 5.8, w: 3.7, h: 0.9, fontSize: 12 });
source(s, "decision log D-56, D-57; outputs/sim/batch_L5_v1/summary.md.");

// =====================================================================================================
// FINDINGS
pres.addSection({ title: "Findings" });
s = content("What our verification establishes", "Findings", notesFor(17, "Diagnostics in B8."));
box(s, 0.5, 1.35, 7.4, 5.4, HEX.paleGreen);
txt(s, "Verification: the code does what we specified", { x: 0.7, y: 1.45, w: 7.0, h: 0.45, fontSize: 18, bold: true, color: "0F7A57" });
const ver = [["to the second", "3 designed evenings reproduce hand-computed answers"], ["292,181", "plan combinations on the designed evening, checked by an independent brute-force program over the same candidates; always agreed"],
  ["253", "automated tests pass (168 written by separate AI review agents that did not reuse the simulator's code)"], ["6 of 6", "sampled reruns byte-identical"]];
ver.forEach(([n, l], i) => {
  const y = 2.05 + i * 1.12;
  txt(s, n, { x: 0.7, y, w: 2.6, h: 0.95, fontSize: 24, bold: true, color: "0F7A57", valign: "middle" });
  txt(s, l, { x: 3.3, y, w: 4.45, h: 0.95, fontSize: 14, valign: "middle" });
});
box(s, 8.2, 1.35, 4.6, 5.4, HEX.paleOrange);
txt(s, "Not yet validation", { x: 8.4, y: 1.45, w: 4.2, h: 0.45, fontSize: 18, bold: true, color: HEX.orange });
bullets(s, ["Do riders behave like our hidden traits?", "Does the real service match our evenings?", "Would these rules work on Homewood nights?",
  "These need data or trials we do not yet have"], { x: 8.4, y: 2.05, w: 4.25, h: 4.5, fontSize: 15 });
link(s, "Numerical diagnostics: B8 →", BK.B8, { x: 0.7, y: 6.35, w: 3.5, h: 0.35 });
source(s, "Phase 4 log; tests/; outputs/sim/batch_L5_v1/reproducibility.json.");

// ---------- 18 ----------
s = content("Earlier prediction changed service and Lyft use", "Findings", notesFor(18, "Full batch table B6. R1u(10) identical to R0 on 24 of 30 nights."));
const lab18 = RULES.map((r, i) => `${NAME[r]} · ${Bt.bookings[i] ? Bt.bookings[i].toFixed(1) + " Lyft orders/night" : "no Lyft"}`);
s.addChart(pres.charts.BAR, [{ name: "Reached within 15 min", labels: lab18, values: Bt.reached }],
  chartOpts({ x: 0.4, y: 1.25, w: 8.2, h: 5.5, barDir: "bar", chartColors: [HEX.faint, HEX.faint, HEX.faint, HEX.faint, HEX.blue, HEX.blue],
    showLegend: false, showTitle: true, title: "Share of all bookings a vehicle reached at the curb within 15 min (curb arrival, not boarding; mean of 30 one-hour pilot nights)",
    titleFontSize: 13, titleColor: HEX.ink, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0%", dataLabelFontSize: 13,
    dataLabelColor: HEX.ink, valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0%", catAxisLabelFontSize: 12,
    valAxisLabelFontSize: 10, catAxisOrientation: "maxMin", barGapWidthPct: 45 }));
badge(s, "SIMULATED", 7.2, 6.4, 1.3);
box(s, 8.9, 1.3, 3.9, 2.2, HEX.paleBlue);
txt(s, [{ text: "Prediction rules", options: { bold: true, breakLine: true, color: HEX.blue } },
  { text: "reach about 73–75%, against 48–51%, using about 9–10.5 Lyft orders a night. They act before the long wait has happened.", options: {} }],
  { x: 9.05, y: 1.4, w: 3.6, h: 2.0, fontSize: 13.5 });
box(s, 8.9, 3.6, 3.9, 2.7, HEX.paleGreen);
txt(s, [{ text: "Assigned is not picked up", options: { bold: true, breakLine: true, color: "0F7A57" } },
  { text: `“Unassigned for ten minutes” was mostly inactive: identical to vans only on ${Bt.r1u.nights_identical_r0} of 30 nights; ${Bt.r1u.transfers} transfers on ${Bt.r1u.nights_with_transfer} nights. Bookings were usually in some van's plan within minutes, even when pickup was far off; only during the burst did some stay unplanned for ten minutes.`, options: {} }],
  { x: 9.05, y: 3.68, w: 3.6, h: 2.55, fontSize: 12 });
link(s, "All metrics: B6 →", BK.B6, { x: 8.9, y: 6.35, w: 2.5, h: 0.35 });
source(s, "outputs/sim/batch_L5_v1 (tradeoff.md, summary.md). Descriptive means; shares vary by SD 0.07–0.10 between nights; paired night-by-night counts in B7.");

// ---------- 19 ----------
s = content("A transfer does not end the rider's wait", "Findings", notesFor(19, "Counts are totals over 30 nights. Patience is a placeholder."));
// wait timeline
const W0 = 0.6;
const segs = [["Waiting for a van", 3.2, HEX.faint], ["Ordering lag 2 min", 1.2, HEX.yellow], ["Lyft travelling", 2.6, HEX.orange]];
let wx = W0;
segs.forEach(([t, w, c]) => {
  s.addShape(pres.shapes.RECTANGLE, { x: wx, y: 1.5, w, h: 0.5, fill: { color: c }, line: { color: HEX.white, width: 2 } });
  txt(s, t, { x: wx, y: 1.5, w, h: 0.5, fontSize: 12.5, bold: true, align: "center", valign: "middle", color: c === HEX.orange ? HEX.white : HEX.ink, margin: 0 });
  wx += w;
});
dot(s, wx, 1.75, 0.22, HEX.aqua);
txt(s, "curb", { x: wx + 0.15, y: 1.6, w: 0.7, h: 0.3, fontSize: 12 });
line(s, W0 + 3.2, 1.35, W0 + 3.2, 2.15, HEX.ink, 1.5);
txt(s, "transfer", { x: W0 + 2.7, y: 2.15, w: 1.0, h: 0.3, fontSize: 11.5, align: "center" });
line(s, W0 + 0.0, 2.6, W0 + 7.0, 2.6, HEX.violet, 1.5, "dash");
txt(s, "the rider's hidden patience clock keeps running the whole time", { x: W0, y: 2.65, w: 7.0, h: 0.32, fontSize: 12, color: HEX.violet, italic: true });
const fr19 = RULES.slice(1).map((r) => [r, Bt.fates[r]]);
s.addChart(pres.charts.BAR, [
  { name: "Lyft completed", labels: fr19.map(([r, f]) => `${NAME[r]} (n = ${f.transfers} transfers${f.transfers < 20 ? ": too few to compare" : ""})`), values: fr19.map(([, f]) => f.completed) },
  { name: "Lyft no-show", labels: fr19.map(([r, f]) => `${NAME[r]} (n = ${f.transfers} transfers${f.transfers < 20 ? ": too few to compare" : ""})`), values: fr19.map(([, f]) => f.noshow) },
  { name: "Cancelled during the 2-min ordering lag", labels: fr19.map(([r, f]) => `${NAME[r]} (n = ${f.transfers} transfers${f.transfers < 20 ? ": too few to compare" : ""})`), values: fr19.map(([, f]) => f.lag) },
  { name: "Cancelled after the Lyft was ordered", labels: fr19.map(([r, f]) => `${NAME[r]} (n = ${f.transfers} transfers${f.transfers < 20 ? ": too few to compare" : ""})`), values: fr19.map(([, f]) => f.after) },
], chartOpts({ x: 0.4, y: 3.05, w: 8.4, h: 3.85, barDir: "bar", barGrouping: "percentStacked", chartColors: [HEX.aqua, HEX.yellow, HEX.magenta, HEX.orange],
  showLegend: true, legendPos: "b", legendFontSize: 11, showValue: true, dataLabelPosition: "ctr", dataLabelFontSize: 10, dataLabelColor: HEX.ink,
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, valAxisLabelFormatCode: "0%", catAxisOrientation: "maxMin", barGapWidthPct: 35 }));
box(s, 9.1, 1.35, 3.7, 2.5, HEX.paleOrange);
const f10 = Bt.fates["R1(10)"];
txt(s, [{ text: `${f10.lag + f10.after} of ${f10.transfers}`, options: { bold: true, fontSize: 30, color: HEX.orange, breakLine: true } },
  { text: `bookings transferred under “Wait ten minutes” cancelled before the Lyft arrived (${f10.after} after the Lyft was ordered)`, options: { fontSize: 13.5 } }],
  { x: 9.25, y: 1.45, w: 3.4, h: 2.3 });
box(s, 9.1, 4.05, 3.7, 1.35, HEX.paleBlue);
txt(s, "Prediction rules: about a third cancelled, consistent with earlier transfers leaving more patience for the Lyft (not isolated by an experiment).", { x: 9.25, y: 4.1, w: 3.4, h: 1.25, fontSize: 13, valign: "middle" });
box(s, 9.1, 5.6, 3.7, 1.2, HEX.tint);
badge(s, "ASSUMED", 9.2, 5.68, 1.2);
txt(s, "Losses after transfer exist under any patience; their size and the gap between rules depend on the placeholder (impatience rising with time waited).", { x: 9.2, y: 5.95, w: 3.5, h: 0.85, fontSize: 10.5 });
source(s, "outputs/sim/batch_L5_v1 per-run outcomes; totals over 30 nights; transfers = Lyft orders + cancellations during the ordering lag.");

// ---------- 20 ----------
s = content("Choosing between service and resource use", "Findings", notesFor(20, "Nondominance computed in src/sim/tradeoff.py; per-night counts in B7."));
// toy dominance
box(s, 0.5, 1.3, 3.7, 4.0, HEX.tint);
txt(s, "Dominance, in one picture", { x: 0.65, y: 1.38, w: 3.4, h: 0.35, fontSize: 14, bold: true });
const tX = 0.95, tY = 4.4, tW = 3.0, tH = 2.4;
line(s, tX, tY, tX + tW, tY, HEX.muted, 1);
line(s, tX, tY, tX, tY - tH, HEX.muted, 1);
txt(s, "Lyft use →", { x: tX + 1.6, y: tY + 0.03, w: 1.4, h: 0.28, fontSize: 10.5, color: HEX.muted, align: "right" });
txt(s, "service ↑", { x: tX - 0.4, y: tY - tH - 0.32, w: 1.2, h: 0.28, fontSize: 10.5, color: HEX.muted });
[["A", 0.9, 1.7, HEX.blue], ["B", 1.9, 0.9, HEX.faint], ["C", 2.6, 2.15, HEX.blue]].forEach(([n, x, y, c]) => {
  dot(s, tX + x, tY - y, 0.26, c);
  txt(s, n, { x: tX + x + 0.15, y: tY - y - 0.2, w: 0.35, h: 0.3, fontSize: 13, bold: true });
});
txt(s, "A dominates B: at least as good on both, better on one. A and C: neither dominates.", { x: 0.65, y: 4.85, w: 3.45, h: 0.45, fontSize: 10.5, color: HEX.muted });
// manual scatter of six rules
const sx0 = 5.0, sy0 = 5.6, sw = 4.6, sh = 4.0, bx = (b) => sx0 + sw * b / 12, ry = (r) => sy0 - sh * (r - 0.4) / 0.4;
line(s, sx0, sy0, sx0 + sw, sy0, HEX.muted, 1);
line(s, sx0, sy0, sx0, sy0 - sh, HEX.muted, 1);
[0, 4, 8, 12].forEach((b) => txt(s, String(b), { x: bx(b) - 0.25, y: sy0 + 0.03, w: 0.5, h: 0.25, fontSize: 10, color: HEX.faint, align: "center" }));
[0.4, 0.6, 0.8].forEach((r) => txt(s, pct(r), { x: sx0 - 0.55, y: ry(r) - 0.13, w: 0.5, h: 0.25, fontSize: 10, color: HEX.faint, align: "right" }));
txt(s, "Lyft orders per night (lower is better)", { x: sx0, y: sy0 + 0.28, w: sw, h: 0.3, fontSize: 11, color: HEX.muted, align: "center" });
txt(s, "Reached within 15 min (higher is better)", { x: sx0 - 0.6, y: 1.3, w: 4.6, h: 0.3, fontSize: 11, color: HEX.muted });
const lbl20 = { R0: ["Vans only and Unassigned for ten minutes (overlap)", 0.15, 0.32, "left"], "R1(10)": ["Wait ten minutes", 0.12, -0.3, "left"],
  "R1(15)": ["Wait fifteen minutes", -0.9, -0.3, "left"], "R1u(10)": null, "R2(15)": ["Predicted total wait exceeds fifteen minutes", -3.25, 0.12, "right"],
  "R3(2)": ["Lyft arrives sooner", -2.3, -0.2, "right"] };
RULES.forEach((r, i) => {
  const x = bx(Bt.bookings[i]), y = ry(Bt.reached[i]);
  dot(s, x, y, 0.2, Bt.nondominated[i] ? HEX.blue : HEX.white, Bt.nondominated[i] ? HEX.blue : HEX.ink);
  if (lbl20[r]) txt(s, lbl20[r][0], { x: x + lbl20[r][1], y: y + lbl20[r][2] - 0.14, w: r === "R2(15)" ? 3.1 : 2.4, h: 0.3, fontSize: 10.5, align: lbl20[r][3] });
});
txt(s, "filled = not dominated among the six (means of 30 nights)", { x: sx0, y: sy0 + 0.6, w: sw, h: 0.28, fontSize: 10.5, color: HEX.muted, align: "center" });
box(s, 9.95, 1.3, 2.85, 5.45, HEX.paleBlue);
bullets(s, ["Two objectives: service up, Lyft orders down", "Five of six not dominated. “Unassigned for ten minutes” is dominated by vans only: about the same service, slightly more Lyft (0.23 vs 0 a night)",
  "Not dominated ≠ recommended: choosing needs a value on Lyft use", "Six tested rules, not a frontier of every rule", "Separate from the routing points of slide 12"],
  { x: 10.05, y: 1.4, w: 2.7, h: 5.3, fontSize: 11.5 });
link(s, "Night by night: B7 →", BK.B7, { x: 0.5, y: 6.4, w: 2.5, h: 0.35 });
source(s, "src/sim/tradeoff.py; outputs/sim/batch_L5_v1/tradeoff.md. Descriptive, not a ranking.");

// =====================================================================================================
// LIMITS AND DIRECTION
pres.addSection({ title: "Limits and direction" });
s = content("Could we optimize the transfer policy itself?", "Limits and direction",
  notesFor(21, "Bilevel / Stackelberg: Colson, Marcotte & Savard (2007) Ann. Oper. Res. 153:235-256; Dempe (2002); von Stackelberg (1934). Methodology §7b."));
badge(s, "NOT IMPLEMENTED", 0.5, 1.3, 1.9);
txt(s, "A possible extension, not a result", { x: 2.55, y: 1.27, w: 6.0, h: 0.35, fontSize: 14, color: HEX.muted });
box(s, 0.5, 1.85, 3.6, 1.6, HEX.paleOrange, HEX.orange);
txt(s, [{ text: "Leader: policy designer", options: { bold: true, breakLine: true } }, { text: "chooses the rule and its threshold", options: { color: HEX.muted } }],
  { x: 0.65, y: 1.95, w: 3.3, h: 1.4, fontSize: 15, valign: "middle" });
box(s, 0.5, 4.25, 3.6, 1.6, HEX.paleBlue, HEX.blue);
txt(s, [{ text: "Follower: route optimizer", options: { bold: true, breakLine: true } }, { text: "re-plans the vans for whoever remains", options: { color: HEX.muted } }],
  { x: 0.65, y: 4.35, w: 3.3, h: 1.4, fontSize: 15, valign: "middle" });
arrow(s, 1.7, 3.5, 1.7, 4.2, HEX.ink);
txt(s, "threshold", { x: 0.55, y: 3.65, w: 1.1, h: 0.3, fontSize: 11, color: HEX.muted, align: "right" });
arrow(s, 2.9, 4.2, 2.9, 3.5, HEX.ink, "dash");
txt(s, "anticipated response", { x: 2.95, y: 3.65, w: 1.6, h: 0.3, fontSize: 11, color: HEX.muted });
box(s, 4.5, 1.85, 8.3, 1.5, HEX.tint);
txt(s, [{ text: "choose θ to minimise  service loss(θ) + λ · Lyft use(θ)", options: { breakLine: true } },
  { text: "subject to: the vans' routes are the follower's optimal response, given θ", options: {} }], { x: 4.7, y: 1.95, w: 8.0, h: 1.3, fontSize: 18, fontFace: "Cambria", valign: "middle" });
txt(s, "We have", { x: 4.5, y: 3.6, w: 4.0, h: 0.4, fontSize: 16, bold: true, color: "0F7A57" });
bullets(s, ["A simulator that evaluates any fixed rule", "Six fixed rules compared on identical nights", "Within each decision moment: routes chosen, then the rule, then at most one re-plan"],
  { x: 4.5, y: 4.0, w: 4.0, h: 2.6, fontSize: 14 });
txt(s, "Still missing", { x: 8.75, y: 3.6, w: 4.0, h: 0.4, fontSize: 16, bold: true, color: "B23A3A" });
bullets(s, ["An optimization over the threshold θ", "The follower's response written as constraints over the whole evening",
  "A treatment of uncertainty across nights", "An agreed value λ for Lyft use", "(today the follower optimizes one decision moment at a time, over restricted candidates)"], { x: 8.75, y: 4.0, w: 4.05, h: 2.6, fontSize: 14 });
source(s, "methodology v1.4 §7b; Colson, Marcotte & Savard (2007); Dempe (2002); von Stackelberg (1934).");

// ---------- 22 ----------
s = content("What we learned and what must be tested next", "Limits and direction", notesFor(22, "Guardrail excesses: 36 events, 16 distinct requests, 10 nights; attribution only."));
txt(s, "So far: deciding earlier, on a prediction, reached about 3 in 4 bookings within 15 min instead of about 1 in 2, at about 10 Lyft orders a night, in our two-van pilot. Whether that is worth it needs a value on Lyft use.",
  { x: 0.5, y: 1.2, w: 12.3, h: 0.7, fontSize: 15, bold: true, color: HEX.blue });
const cols = [["Learned", HEX.paleBlue, HEX.blue, ["Being assigned is not being picked up", "A transfer is not a completed trip", "Rules acting on predictions changed both service and Lyft use"]],
  ["Limits", HEX.paleOrange, HEX.orange, ["Aggregate data only", "Placeholder patience", "Two-van pilot, not the five-van evening", "Verification, not validation",
    `${Bt.guardrail.events} ride-time excesses across the 180 runs (${Bt.guardrail.distinct_requests} distinct bookings on ${Bt.guardrail.nights} nights), each coinciding with a no-show wait on that van (attribution, not proof)`]],
  ["Next", HEX.paleGreen, "0F7A57", ["Agree how to judge the rules, then paired comparisons on the saved nights", "Sweep the thresholds", "Run the five-van evening and check solve times",
    "Test patience and Lyft-delay assumptions"]]];
cols.forEach(([h, f, c, items], i) => {
  const x = 0.5 + i * 4.15;
  box(s, x, 2.0, 3.95, 4.75, f);
  txt(s, h, { x: x + 0.2, y: 2.08, w: 3.55, h: 0.5, fontSize: 22, bold: true, color: c });
  bullets(s, items, { x: x + 0.2, y: 2.62, w: 3.6, h: 4.05, fontSize: i === 0 ? 17 : 13.5 });
});
source(s, "methodology v1.4 §7–§9; decision log D-57; outputs/sim/batch_L5_v1.");
link(s, "Backups →", 23, { x: 10.6, y: 6.98, w: 1.5, h: 0.3, fontSize: 10 });

// =====================================================================================================
// BACKUP
pres.addSection({ title: "Backup" });
s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Backup" });
slideNo++;
s.addText("Backup slides", { placeholder: "title" });
s.addText("B1 Code key · B2 Route-selection MILP · B3 Event order · B4 Where inputs come from · B5 Three postponement prices · "
  + "B6 All metrics by rule · B7 Night by night · B8 Numerical diagnostics · B9 Corrected proposal claims", { placeholder: "body" });
Object.entries(BK).forEach(([b, n], i) => link(s, b, n, { x: 0.8 + i * 1.3, y: 6.3, w: 1.1, h: 0.35, fontSize: 14 }));
s.addNotes("Backup divider. Each backup links back to the main slide that uses it.");

function backup(code, title, back, notes) {
  const sl = content(code + "  " + title, "Backup", notes || "Backup " + code + ".");
  link(sl, "← back to slide " + back, back, { x: 10.6, y: 6.98, w: 1.6, h: 0.3, fontSize: 10 });
  return sl;
}
const hdr = (t) => ({ text: t, options: { bold: true, color: HEX.white, fill: { color: HEX.ink } } });
const TB = { fontFace: "Calibri", color: HEX.ink, border: { type: "solid", pt: 0.75, color: HEX.line } };

s = backup("B1", "Code key (for files and questions only)", 13);
s.addTable([[hdr("Said in the talk"), hdr("Code in files and logs")],
  ...RULES.map((r) => [NAME[r], r]),
  ["Small designed evenings with hand-computed answers", "L1–L4 (L4: vans from 18:15, Lyft lag 2 min, delay fixed 8 min, acceptance 0.9)"],
  ["The thirty-night pilot", "L5: 30 synthetic one-hour nights, 2 vans, 28 bookings"],
  ["The van optimizer", "Dispatcher C: restricted route-selection MILP (HiGHS)"],
  ["The postponement price we chose", "Pending price A (earliest physical pickup)"],
  ["Numbered decisions", "D-xx entries in docs/technical/decision_log.md"]],
  Object.assign({ x: 0.5, y: 1.3, w: 12.3, colW: [5.0, 7.3], rowH: 0.42, fontSize: 13.5 }, TB));
source(s, "src/sim/lyft.py; scenario_spec.md §6, §8; decision log.");

s = backup("B2", "The route-selection MILP at one decision moment", 12);
txt(s, [{ text: "min  Σ_v Σ_k c_vk y_vk  +  Σ_r π_r u_r", options: { breakLine: true } },
  { text: "s.t.  Σ_k y_vk = 1  for every van v        (one route per van)", options: { breakLine: true } },
  { text: "        Σ_{v,k: r ∈ S_vk} y_vk + u_r = 1  for every waiting booking r   (served once, or postponed)", options: { breakLine: true } },
  { text: "        y, u ∈ {0, 1};   S_vk = bookings picked up by candidate route k of van v", options: {} }], { x: 0.5, y: 1.35, w: 12.3, h: 1.7, fontSize: 18, fontFace: "Cambria" });
bullets(s, ["c_vk: route points (waiting φ with slopes 1/2.5/5/10/20 per passenger-minute after 0/5/10/15/20 min; riding 0.5 per passenger-minute; 0.1 per km); exact integers",
  "Candidates: every subset of at most 3 waiting bookings per van, each in its best stop order (exact search); the van's committed work is always a candidate",
  "π_r = b_r + M, b_r from the chosen postponement price; M = 1 + Σ_v (max_k c_vk − min_k c_vk) + Σ_r b_r guarantees every proven-optimal solution postpones the fewest bookings",
  "Ride-time guardrail max(25, 2 × direct + 5) min: no candidate may create or worsen an excess",
  "HiGHS: relative gap 0, absolute gap 0.5 units; a failed solve is logged, never replaced by a heuristic"], { x: 0.5, y: 3.2, w: 12.3, h: 3.6, fontSize: 14 });
source(s, "model_design.md v0.5 §3; decision log D-47, D-52 (amendments), D-53.");

s = backup("B3", "Event order and a booking's life", 11);
bullets(s, ["Same-second order: drop-offs → curb arrivals (stop the patience clock) → service ends → vans on/off duty → new bookings → patience checks → Lyft bookings → planning → departures",
  "A van commits to a stop when it departs toward it; a booking with a van driving to it is not eligible for transfer",
  "After a transfer: a 2-min booking lag, then the Lyft's hidden delay; the rider may cancel at any point before the Lyft reaches the curb",
  "During an absent rider's 3-min curb wait, planning assumes possible boarding at expiry; the simulator never boards an absent rider",
  "Presence is one draw per rider, used whichever vehicle arrives",
  "Planning takes zero simulated time; computer time is logged only"], { x: 0.5, y: 1.4, w: 12.3, h: 5.3, fontSize: 15 });
source(s, "scenario_spec.md v0.8 §17; decision log D-46, D-48, D-54.");

s = backup("B4", "Where each input comes from", 11);
const prov = [["Input", "Status", "Value", "Basis"],
  ["Bookings per hour", "DERIVED", "64 / 50 / 54 for five vans; pilot: 28 in one hour, two vans", "D-35, D-36, D-56"],
  ["Trip pairing", "ASSUMED + fitted", "Distance prior, decay 0.1 per min, fitted to both map totals", "D-18"],
  ["Group size", "ASSUMED (mean observed)", "Shares 1–5: .73/.18/.055/.025/.01; April: 1.386 van passengers per completed van booking", "D-38"],
  ["Patience", "ASSUMED placeholder", "Weibull, shape 1.5, median 18 min (scale ≈ 23.0 min)", "D-39"],
  ["No-show", "DERIVED, conditional", "8.9% per vehicle arrival if the status mapping holds (4.7% of all bookings)", "D-40, D-48"],
  ["Lyft", "ASSUMED", "Ordering lag 2 min; delay lognormal, median 8 min, 90th percentile 15 min", "D-43"],
  ["Travel times", "DERIVED; × 1.2 ASSUMED", "Local OSRM routing on the OpenStreetMap network; van times × 1.2 in the pilot (placeholder)", "D-31, D-47"]];
s.addTable(prov.map((r, i) => r.map((c) => ({ text: c, options: { bold: i === 0, color: i === 0 ? HEX.white : HEX.ink, fill: { color: i === 0 ? HEX.ink : HEX.white } } }))),
  Object.assign({ x: 0.5, y: 1.3, w: 12.3, colW: [2.0, 2.3, 6.0, 2.0], rowH: 0.6, fontSize: 13 }, TB));
source(s, "decision log D-18–D-56; methodology v1.4 §4.");

s = backup("B5", "Three postponement prices compared", 15);
const pa = V2.pending;
s.addTable([[hdr(""), hdr("First version"), hdr("Chosen (earliest physical pickup)"), hdr("Route-based")],
  ["Price of postponing a booking", "as if served at the next 2-min re-plan", "as if served at the earliest time any on-duty van can reach it", "as if served after a chosen van's route"],
  ["Wait median / 90th pct / longest (min)", ...pa.wait], ["Mean wait (min)", ...pa.mean], ["Party of five from slide 15: wait", ...pa.r002],
  ["Extra variables / solve time", ...pa.size],
  ["Direction of error", "optimistic", "optimistic (ignores the van's other work)", "either direction"]],
  Object.assign({ x: 0.5, y: 1.3, w: 12.3, colW: [3.0, 2.8, 3.5, 3.0], rowH: 0.55, fontSize: 13 }, TB));
txt(s, "Designed evening, vans only. Chosen for its meaning and zero added size, provisionally; neither alternative guarantees a feasible schedule for all waiting riders.",
  { x: 0.5, y: 5.6, w: 12.3, h: 0.7, fontSize: 13, color: HEX.muted });
source(s, "outputs/sim/d53_experiment/d53_comparison.md; decision log D-53; review d53_pending_price_review (22 Oct).");

s = backup("B6", "All six rules over 30 synthetic nights", 18);
const relabel = { "Requests picked up (of 28)": "Bookings picked up (of 28)", "Wait 90th pct, min (picked up)": "Wait 90th pct, min (per booking picked up)",
  "Wait 90th pct, min (passengers)": "Wait 90th pct, min (per passenger picked up)", "Wait median, min (picked up)": "Wait median, min (per booking picked up)",
  "Lyft bookings": "Lyft orders" };
const bt = V2.batch_table.map((r, i) => (i === 0 ? [hdr("Per night"), ...RULES.map((x) => hdr(NAME[x]))] : [relabel[r[0]] || r[0], ...r.slice(1)]));
s.addTable(bt, Object.assign({ x: 0.5, y: 1.25, w: 12.3, colW: [3.0, 1.55, 1.55, 1.55, 1.55, 1.55, 1.55], rowH: 0.34, fontSize: 10.5 }, TB));
txt(s, "Cells: mean of nightly values (standard deviation across nights). Waits cover only bookings picked up. 30 nights replayed six ways, not 180 independent nights.",
  { x: 0.5, y: 6.5, w: 12.3, h: 0.4, fontSize: 11.5, color: HEX.muted });
source(s, "outputs/sim/batch_L5_v1/summary.md.");

s = backup("B7", "Trade-off night by night", 20);
s.addTable([[hdr("Rule"), hdr("Reached (mean)"), hdr("Lyft orders (mean)"), hdr("Nights not dominated"), hdr("Nights identical to vans only"), hdr("Nights reach above / below vans only")],
  ...RULES.map((r, i) => [NAME[r], Bt.reached[i].toFixed(3), Bt.bookings[i].toFixed(2), `${Bt.nights_nondominated[i]} of 30`, String(Bt.nights_identical_r0[i]),
    `${Bt.above_below_r0[i][0]} / ${Bt.above_below_r0[i][1]}`])],
  Object.assign({ x: 0.5, y: 1.3, w: 12.3, colW: [3.6, 1.5, 1.7, 1.8, 1.8, 1.9], rowH: 0.5, fontSize: 13 }, TB));
txt(s, "A rule that makes no transfer on a night replays vans only exactly and ties it. Above / below counts are paired comparisons on the same synthetic night, with no intervals yet.",
  { x: 0.5, y: 5.1, w: 12.3, h: 0.8, fontSize: 13, color: HEX.muted });
source(s, "outputs/sim/batch_L5_v1/tradeoff.md.");

s = backup("B8", "Numerical diagnostics (thirty-night pilot)", 17);
bullets(s, V2.diagnostics.map((d) => d.replace("the 2 night-r00 batch runs", "the 2 batch runs of the first night").replace("requests", "bookings").replace("planning epochs", "decision moments (epochs)")), { x: 0.5, y: 1.35, w: 12.3, h: 5.3, fontSize: 15 });
source(s, "outputs/sim/batch_L5_v1 (summary.md, tie_incomplete_check.csv, reproducibility.json); decision log D-52 am. 5, D-57.");

s = backup("B9", "Corrected proposal claims", 3);
s.addTable([[hdr("Proposal said"), hdr("Corrected"), hdr("Why")],
  ["About 5,100 rides per hour at 6 pm", "≈ 170 completed rides in one evening's 6 pm hour", "The bar is a 30-day total (tooltip 5,098; digitized 5,089)"],
  ["About 28 vans", "27.6 vehicles on duty, “All services” average", "Not a Homewood-only count"],
  ["1 in 4 trips overflow to Lyft", "24.5% of 44,374 riders rode Lyft", "A share of riders, not of trips or requests"],
  ["Trip-level records coming", "Synthetic evenings built from aggregate dashboards", "The records did not arrive"],
  ["Compare dispatch algorithms", "Compare transfer rules, van optimizer held fixed", "On synthetic nights an algorithm comparison would mostly compare our assumptions"],
  ["Lyft as paid overflow inside the optimizer", "A separate, explicit transfer rule; no money modelled", "A dispatcher sends the Lyft; the cost per Lyft trip is unknown"],
  ["Targets as hard constraints", "Reporting thresholds plus a ride-time guardrail", "Hard targets would be stricter than the observed service; target wording changed over time"]],
  Object.assign({ x: 0.5, y: 1.3, w: 12.3, colW: [3.3, 4.0, 5.0], rowH: 0.56, fontSize: 12.5 }, TB));
txt(s, "The September proposal deck is unchanged; these corrections are recorded in methodology v1.4 §1a.", { x: 0.5, y: 5.95, w: 12.3, h: 0.4, fontSize: 13, color: HEX.muted });
source(s, "methodology v1.4 §1a; decision log D-25, D-35, D-36, D-45, D-47, D-49, D-51.");

pres.writeFile({ fileName: OUT }).then(async () => {
  if (process.env.APPLY_THEME) {
    const { applyTheme } = require(process.env.APPLY_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("wrote " + OUT + " (" + slideNo + " slides)");
});
