// Midterm deck builder, content draft v0.4. Self-contained: every number comes from v0.4/derived/numbers.json
// (make_numbers.py, saved outputs only) and the figures in v0.4/figures. No simulation is run here.
//   NODE_PATH=<dir with pptxgenjs 3.12> APPLY_THEME=<pptx skill>/scripts/apply_theme.js node docs/presentations/midterm/v0.4/build_deck.js
// Main slides 1-28, backup divider 29, backups B1-B9 = slides 30-38. Footer numbers are slide positions.
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const HERE = __dirname;
const FIG = (f) => path.join(HERE, "figures", f);
const OUT = path.join(HERE, "BlueJay_Midterm_v0.4.pptx");
const N = JSON.parse(fs.readFileSync(path.join(HERE, "derived", "numbers.json"), "utf8"));
const A = N.april, Bt = N.batch, T = N.transfer, P = N.pending, PL = N.pilot;
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
  paleBlue: "E8F1FB", paleOrange: "FFF4EC", paleGreen: "E9F7F1", paleViolet: "EFEDFB", green: "0F7A57", red: "B23A3A" };
// Visual system 1: EVIDENCE (soft filled pill, dark text)
const EVID = { OBSERVED: ["E3E8EE", "1E2933"], DERIVED: ["DCEBFA", "1B4F8A"], ASSUMED: ["FDE3D3", "8E3A0E"],
  DESIGNED: ["E8E4FA", "3F2F9E"], SIMULATED: ["DDF3EA", "0F6B4B"], ILLUSTRATIVE: ["EDEDED", "4A4A4A"],
  "DERIVED + ASSUMED": ["E6E3F0", "3A3F7A"], "ORIGINAL PROPOSAL": ["FFF1C9", "6B4E00"] };
// Visual system 2: EXECUTION STATUS (white band, coloured border, square corners; dashed = not run)
const STATUS = { TESTED: ["TESTED IN SIMULATION", HEX.green, "solid"], PLANNED: ["PLANNED — NOT YET RUN", "8A6400", "dash"],
  PROPOSED: ["PROPOSED — NOT IMPLEMENTED", HEX.red, "dash"] };
// component colours, used on every slide that shows them
const COMP = { sim: ["EEF1F4", "5B6670"], opt: ["E8F1FB", "2A78D6"], rule: ["FFF4EC", "EB6834"], hidden: ["EFEDFB", "6250D6"] };
const BK = { B1: 30, B2: 31, B3: 32, B4: 33, B5: 34, B6: 35, B7: 36, B8: 37, B9: 38 };
const DOC = "docs/technical/";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "When should Night Ride move a waiting request to Lyft? (content draft v0.4)";
pres.author = "Team FourSight";
pres.company = "Johns Hopkins University";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

pres.defineSlideMaster({ title: "TITLE_DARK", background: { color: "1E2933" }, objects: [
  { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 0.9, w: 11.9, h: 1.5, fontSize: 38, bold: true, color: "FFFFFF", valign: "bottom", align: "left" }, text: "" } },
  { placeholder: { options: { name: "body", type: "body", x: 0.7, y: 2.45, w: 11.9, h: 0.9, fontSize: 19, color: "C9D1D8", valign: "top", align: "left" }, text: "" } }] });
pres.defineSlideMaster({ title: "CONTENT", background: { color: "FFFFFF" }, margin: [0.5, 0.5, 0.6, 0.5], objects: [
  { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.25, w: 12.3, h: 0.8, fontSize: 28, bold: true, color: "1E2933", valign: "middle", align: "left" }, text: "" } }] });
pres.defineSlideMaster({ title: "SECTION", background: { color: "EEF1F4" }, objects: [
  { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.4, w: 11.7, h: 1.2, fontSize: 34, bold: true, color: "1E2933" }, text: "" } },
  { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.7, w: 11.7, h: 2.6, fontSize: 16, color: "3A4750" }, text: "" } }] });

// ---------- helpers ----------
let slideNo = 0;
function txt(slide, text, o) {
  slide.addText(text, Object.assign({ isTextBox: true, fontFace: "Calibri", fontSize: 16, color: HEX.ink, margin: 0.05, valign: "top" }, o));
}
function source(slide, s) { txt(slide, "Source: " + s, { x: 0.5, y: 7.0, w: 10.6, h: 0.3, fontSize: 9.5, color: HEX.faint, valign: "middle" }); }
function evid(slide, kind, x, y, w) {
  const [f, c] = EVID[kind]; w = w || 1.3;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.28, rectRadius: 0.14, fill: { color: f }, line: { color: f }, objectName: "evidence-" + kind });
  txt(slide, kind, { x, y, w, h: 0.28, fontSize: 9.5, bold: true, color: c, align: "center", valign: "middle", margin: 0 });
}
function status(slide, kind, x, y, w) {
  const [label, c, dash] = STATUS[kind]; w = w || 2.9;
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.32, fill: { color: HEX.white }, line: { color: c, width: 1.5, dashType: dash }, objectName: "status-" + kind });
  txt(slide, label, { x, y, w, h: 0.32, fontSize: 10.5, bold: true, color: c, align: "center", valign: "middle", margin: 0 });
}
function box(slide, x, y, w, h, fill, lineColor, o) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, Object.assign({ x, y, w, h, rectRadius: 0.07, fill: { color: fill || HEX.tint },
    line: { color: lineColor || fill || HEX.tint, width: lineColor ? 1.25 : 0.75 } }, o || {}));
}
function comp(slide, kind, x, y, w, h, title, body, o) {
  const [f, c] = COMP[kind];
  box(slide, x, y, w, h, f, c, kind === "hidden" ? { line: { color: c, width: 1.25, dashType: "dash" } } : {});
  const runs = [{ text: title, options: { bold: true, color: c === "5B6670" ? HEX.ink : c, breakLine: !!body } }];
  if (body) runs.push({ text: body, options: { color: HEX.ink } });
  txt(slide, runs, Object.assign({ x: x + 0.08, y: y + 0.04, w: w - 0.16, h: h - 0.08, fontSize: 12.5, valign: "middle", align: "center" }, o || {}));
}
function arrow(slide, x1, y1, x2, y2, color, dash, width) {
  const o = { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.001), h: Math.max(Math.abs(y2 - y1), 0.001),
    line: { color: color || HEX.muted, width: width || 1.5, endArrowType: "triangle", dashType: dash || "solid" } };
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
  slide.addText(runs, Object.assign({ isTextBox: true, fontFace: "Calibri", fontSize: 15, color: HEX.ink, valign: "top", margin: 0.05 }, o));
}
function link(slide, label, target, o) {
  txt(slide, [{ text: label, options: { hyperlink: { slide: target, tooltip: "Go to slide " + target }, color: HEX.blue } }], Object.assign({ fontSize: 11 }, o));
}
function dot(slide, x, y, d, fill, lineColor) {
  slide.addShape(pres.shapes.OVAL, { x: x - d / 2, y: y - d / 2, w: d, h: d, fill: { color: fill }, line: { color: lineColor || fill, width: 1.25 } });
}
function lead(slide, text, o) { txt(slide, text, Object.assign({ x: 0.5, y: 1.05, w: 12.3, h: 0.62, fontSize: 17, color: HEX.blue, bold: true }, o)); }
function content(title, section, notes) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  slideNo++;
  txt(s, String(slideNo), { x: 12.25, y: 7.02, w: 0.6, h: 0.26, fontSize: 10, color: HEX.faint, align: "right", valign: "middle", margin: 0 });
  s.addNotes(`Script: speaking_script.md#s${String(slideNo).padStart(2, "0")}. Handbook: slide_explanations.md#s${String(slideNo).padStart(2, "0")}.` + (notes ? " " + notes : ""));
  return s;
}
const chartOpts = (o) => Object.assign({ catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  legendFontFace: "+mn-lt", titleFontFace: "+mn-lt", catAxisLabelColor: HEX.muted, valAxisLabelColor: HEX.muted,
  valGridLine: { color: "E3E6E9", size: 0.5 }, catGridLine: { style: "none" } }, o);
const hdr = (t) => ({ text: t, options: { bold: true, color: HEX.white, fill: { color: HEX.ink } } });
const TB = { fontFace: "Calibri", color: HEX.ink, border: { type: "solid", pt: 0.75, color: HEX.line } };

// =====================================================================================================
// 1 OUR QUESTION
pres.addSection({ title: "Question and starting point" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Question and starting point" });
slideNo++;
s.addText("When should Night Ride move a waiting request to Lyft?", { placeholder: "title" });
s.addText("What April's aggregate data helped us build—and what our first simulations revealed.", { placeholder: "body" });
s.addShape(pres.shapes.OVAL, { x: 2.0, y: 4.25, w: 1.5, h: 1.5, fill: { color: "2E3B47" }, line: { color: "C9D1D8", width: 1.5 } });
txt(s, "Waiting request", { x: 2.0, y: 4.25, w: 1.5, h: 1.5, fontSize: 14, bold: true, color: HEX.white, align: "center", valign: "middle" });
arrow(s, 3.55, 4.75, 6.3, 4.1, "8FB8EA", "solid", 2.5);
arrow(s, 3.55, 5.25, 6.3, 5.9, "F3A57E", "solid", 2.5);
box(s, 6.4, 3.75, 3.3, 0.75, "2A3F57", "8FB8EA");
txt(s, "Shared van", { x: 6.4, y: 3.75, w: 3.3, h: 0.75, fontSize: 18, bold: true, color: HEX.white, align: "center", valign: "middle" });
box(s, 6.4, 5.55, 3.3, 0.75, "4A3328", "F3A57E");
txt(s, "Lyft", { x: 6.4, y: 5.55, w: 3.3, h: 0.75, fontSize: 18, bold: true, color: HEX.white, align: "center", valign: "middle" });
txt(s, "?", { x: 4.3, y: 4.55, w: 0.6, h: 0.7, fontSize: 30, bold: true, color: "EDA100", align: "center", valign: "middle" });
txt(s, "Team FourSight · EN.553.602 Research and Design in Mathematics · Midterm, October 2026 · content draft v0.4",
  { x: 0.7, y: 6.8, w: 11.9, h: 0.35, fontSize: 12, color: "9AA5AF" });
s.addNotes("Script: speaking_script.md#s01. Handbook: slide_explanations.md#s01.");

// 2 THE SERVICE AND ONE REQUEST
s = content("The service and one request", "Question and starting point", "Scope: Homewood Night Ride including the Peabody area (D-23, D-27).");
lead(s, "Homewood-area Night Ride pools requests in shared vans. A dispatcher can move waiting riders to Lyft. We are studying when that transfer should happen.");
txt(s, "Area: Homewood Night Ride, including the Peabody area; East Baltimore excluded.", { x: 0.5, y: 1.62, w: 12.3, h: 0.3, fontSize: 12, color: HEX.muted });
const jr = [["Request", 0.5], ["Wait", 2.95], ["Vehicle reaches curb", 5.4], ["Boarding", 7.85], ["Drop-off", 10.3]];
jr.forEach(([t, x], i) => {
  box(s, x, 2.35, 2.05, 0.75, i === 1 ? HEX.paleBlue : HEX.tint, i === 1 ? HEX.blue : null);
  txt(s, t, { x, y: 2.35, w: 2.05, h: 0.75, fontSize: 15, bold: true, align: "center", valign: "middle" });
  if (i < 4) arrow(s, x + 2.07, 2.72, x + 2.43, 2.72, HEX.ink);
});
arrow(s, 3.97, 3.12, 3.97, 3.6, HEX.orange);
box(s, 3.0, 3.62, 1.95, 0.55, HEX.paleOrange);
txt(s, "Cancellation: rider gives up", { x: 3.0, y: 3.62, w: 1.95, h: 0.55, fontSize: 11.5, align: "center", valign: "middle" });
arrow(s, 6.42, 3.12, 6.42, 3.6, HEX.orange);
box(s, 5.45, 3.62, 1.95, 0.55, HEX.paleOrange);
txt(s, "No-show: absent after a 3-min curb wait", { x: 5.45, y: 3.62, w: 1.95, h: 0.55, fontSize: 11.5, align: "center", valign: "middle" });
arrow(s, 3.97, 2.33, 3.97, 1.98, HEX.orange, "dash");
txt(s, "transfer → a separate Lyft order; the rider can still cancel or be absent", { x: 4.05, y: 1.92, w: 6.5, h: 0.32, fontSize: 11.5, color: HEX.orange, italic: true });
const defs2 = [["Booking", "one Night Ride request, possibly with several passengers"], ["Lyft order", "a separate order placed after a transfer decision"],
  ["Curb arrival", "the vehicle reaches the pickup location"], ["Pickup", "the rider boards"]];
defs2.forEach(([h, b], i) => {
  const x = 0.5 + i * 3.1;
  box(s, x, 4.65, 2.95, 1.35, HEX.white, HEX.line);
  txt(s, [{ text: h, options: { bold: true, fontSize: 17, breakLine: true } }, { text: b, options: { color: HEX.muted, fontSize: 13.5 } }], { x: x + 0.12, y: 4.72, w: 2.75, h: 1.22 });
});
txt(s, "Waiting time runs from the request to curb arrival. Each Lyft order is an extra trip Hopkins pays for (its cost is unknown to us), so moving riders to Lyft has a price.", { x: 0.5, y: 6.2, w: 12.3, h: 0.5, fontSize: 13.5, color: HEX.muted });
source(s, DOC + "decision_log.md D-23, D-27; scenario_spec.md v0.8 §5–§6; JHU Night Ride page (3-min curb wait).");

// 3 WHERE WE STARTED (original slides)
s = content("Where we started", "Question and starting point", "Original slides 10 and 11 of the September proposal deck (committed version), reproduced as images; the dashboard map is masked.");
const IW = 6.0, IH = IW * 825 / 1467;
[["proposal_slide10.png", 0.5], ["proposal_slide11.png", 6.83]].forEach(([f, x]) => {
  s.addImage({ path: FIG(f), x, y: 1.45, w: IW, h: IH });
  s.addShape(pres.shapes.RECTANGLE, { x, y: 1.45, w: IW, h: IH, fill: { type: "none" }, line: { color: "C9A227", width: 1.5 } });
  evid(s, "ORIGINAL PROPOSAL", x, 1.1, 2.0);
});
txt(s, "Original proposal, slide 10: trip-level extracts were expected, to replay actual service nights", { x: 0.5, y: 1.5 + IH, w: IW, h: 0.55, fontSize: 13 });
txt(s, "Original proposal, slide 11: compare heuristics, a rolling-horizon MILP and a hybrid on the same request stream", { x: 6.83, y: 1.5 + IH, w: IW, h: 0.55, fontSize: 13 });
box(s, 0.5, 5.6, 12.33, 1.1, HEX.paleOrange);
txt(s, [{ text: "What changed: ", options: { bold: true } }, { text: "the trip-level extracts never arrived, so real nights could not be replayed. The data we have are April's aggregate dashboards. We also narrowed the question (next slides).", options: {} }],
  { x: 0.7, y: 5.65, w: 11.9, h: 1.0, fontSize: 15, valign: "middle" });
link(s, "All proposal corrections: B9 →", BK.B9, { x: 9.8, y: 7.0, w: 2.3, h: 0.3, fontSize: 10 });
source(s, "BlueJayNightRide_Proposal.pptx (September, committed version), slides 10–11.");

// 4 ORIGINAL NUMBERS, CORRECTED
s = content("Where we started: numbers we later corrected", "Question and starting point", "Original slides 7 and 8, with correction markers. The map is masked (restricted dashboard imagery).");
[["proposal_slide07.png", 0.5], ["proposal_slide08.png", 6.83]].forEach(([f, x]) => {
  s.addImage({ path: FIG(f), x, y: 1.45, w: IW, h: IH });
  s.addShape(pres.shapes.RECTANGLE, { x, y: 1.45, w: IW, h: IH, fill: { type: "none" }, line: { color: "C9A227", width: 1.5 } });
  evid(s, "ORIGINAL PROPOSAL", x, 1.1, 2.0);
});
const mark = (n, x, y) => { dot(s, x, y, 0.36, HEX.red); txt(s, String(n), { x: x - 0.18, y: y - 0.18, w: 0.36, h: 0.36, fontSize: 13, bold: true, color: HEX.white, align: "center", valign: "middle", margin: 0 }); };
mark(1, 0.5 + IW * 0.47, 1.45 + IH * 0.28);
mark(2, 0.5 + IW * 0.22, 1.45 + IH * 0.36);
mark(3, 0.5 + IW * 0.15, 1.45 + IH * 0.43);
mark(4, 6.83 + IW * 0.72, 1.45 + IH * 0.70);
const corr4 = [["1", "“about 5,100 rides per hour” at 6 pm", "a 30-day total: about 170 completed rides in one evening's 6 pm hour"],
  ["2", "“about 28 vans in service”", "the “All services” average (27.6 at 6 pm), not a Homewood-only count"],
  ["3", "7 pm bar “4,900”", `our digitized value is ${fmt(A.completed_by_hour[1])} (also a 30-day total)`],
  ["4", "“~1 in 4 trips overflow to Lyft”", "24.5% of riders rode Lyft: a share of riders, not of trips or requests"]];
corr4.forEach(([n, a, b], i) => {
  const x = 0.5 + (i % 2) * 6.17, y = 5.2 + Math.floor(i / 2) * 0.82;
  box(s, x, y, 6.0, 0.72, HEX.paleOrange);
  mark(n, x + 0.3, y + 0.36);
  txt(s, [{ text: a + "  →  ", options: { bold: true } }, { text: b, options: {} }], { x: x + 0.6, y, w: 5.3, h: 0.72, fontSize: 12.5, valign: "middle" });
});
source(s, "Proposal slides 7–8; April dashboards (digitized aggregates); methodology v1.5 §1a. Details: B9.");
link(s, "Details: B9 →", BK.B9, { x: 10.3, y: 7.0, w: 1.8, h: 0.3, fontSize: 10 });

// 5 REFINED QUESTION
s = content("We narrowed the question to one controllable decision", "Question and starting point",
  "Scope choice, not a claim that synthetic algorithm comparisons are invalid. Dispatcher modelled on TransLoc's published 2016 design (transloc_operations.md); current Hopkins practice not verified.");
lead(s, "We now hold one specified van dispatcher fixed and change only the Lyft transfer rule.");
const st5 = [["Original ambition", HEX.tint, ["Replay real service nights", "Compare dispatch methods head to head", "Lyft use decided inside the optimizer itself"]],
  ["Evidence available", HEX.paleOrange, ["Aggregate April dashboards only", "No individual journeys", "Hopkins' current dispatcher internals not verified"]],
  ["Current controlled experiment", HEX.paleBlue, ["One specified van dispatcher, held fixed", "Change only the Lyft transfer rule", "Same constructed nights for every rule"]]];
st5.forEach(([h, f, items], i) => {
  const x = 0.5 + i * 4.2;
  box(s, x, 1.85, 3.85, 3.3, f);
  txt(s, h, { x: x + 0.15, y: 1.95, w: 3.55, h: 0.45, fontSize: 18, bold: true });
  bullets(s, items, { x: x + 0.15, y: 2.45, w: 3.6, h: 2.6, fontSize: 14.5 });
  if (i < 2) arrow(s, x + 3.87, 3.5, x + 4.18, 3.5, HEX.ink, "solid", 2);
});
txt(s, "This lets us study how the timing and information used by that rule change service and Lyft use.", { x: 0.5, y: 5.35, w: 12.3, h: 0.45, fontSize: 16, bold: true });
box(s, 0.5, 5.9, 12.3, 0.85, HEX.tint);
txt(s, "Why: it is the question we chose, the real dispatcher's internals are not known to us, and a controlled comparison needs everything else held fixed. Our van dispatcher re-plans every 2 minutes and at each new request, cancellation or no-show while waiting, or van coming on duty: modelled on TransLoc's (the vendor's dispatch software) published 2016 design, not verified current Hopkins practice.",
  { x: 0.65, y: 5.93, w: 12.0, h: 0.8, fontSize: 13, valign: "middle" });
source(s, DOC + "scenario_methodology.md v1.5 §1a; decision_log.md D-25, D-51; transloc_operations.md.");

// =====================================================================================================
// 6 WHAT THE DATA CONTAIN
pres.addSection({ title: "From aggregates to scenario inputs" });
s = content("April describes totals—not individual journeys", "From aggregates to scenario inputs", "Restricted source: digitized aggregates only, no screenshots.");
lead(s, "We know how many requests ended in each status, where pickups and drop-offs accumulated, and how activity varied by hour. We cannot reconstruct each rider's journey.");
box(s, 0.5, 1.85, 6.05, 3.65, HEX.paleGreen);
txt(s, "Observed: totals and shares", { x: 0.7, y: 1.92, w: 5.6, h: 0.4, fontSize: 17, bold: true, color: HEX.green });
bullets(s, [`Requests by final status: ${fmt(A.status.requests)} in the month`, "Completed rides by hour (30-day totals)", `Vehicles on duty by hour (${A.vehicles["18:00"]} at 6 pm, all services)`,
  "Pickup and drop-off counts at 188 map places", "Wait-time percentiles", `Riders by van and by Lyft (${fmt(A.riders)}; ${pct(A.lyft_rider_share, 1)} by Lyft)`],
  { x: 0.7, y: 2.35, w: 5.7, h: 3.1, fontSize: 14 });
box(s, 6.8, 1.85, 6.0, 3.65, HEX.paleOrange);
txt(s, "Missing: any single journey", { x: 7.0, y: 1.92, w: 5.6, h: 0.4, fontSize: 17, bold: true, color: HEX.orange });
bullets(s, ["When each request was made", "Which pickup went with which drop-off", "How long that rider waited", "Whether they boarded, gave up or were moved to Lyft"],
  { x: 7.0, y: 2.35, w: 5.6, h: 3.1, fontSize: 14 });
const leg = [["OBSERVED", "read from April's dashboards"], ["DERIVED", "computed from observed numbers"], ["ASSUMED", "our modelling choice, to be tested"], ["DESIGNED", "an experiment setting we chose"]];
leg.forEach(([k, t], i) => { evid(s, k, 0.5 + i * 3.1, 5.72, 1.2); txt(s, t, { x: 1.75 + i * 3.1, y: 5.67, w: 1.8, h: 0.45, fontSize: 11.5, valign: "middle" }); });
txt(s, "We therefore built plausible evenings from the evidence, while keeping the missing pieces visible.", { x: 0.5, y: 6.25, w: 12.3, h: 0.45, fontSize: 15, italic: true });
source(s, "April 2026 operations dashboards (restricted; digitized aggregates in data/processed); " + DOC + "scenario_methodology.md §3.");

// 7 WORKLOAD
s = content("How busy should a constructed evening be?", "From aggregates to scenario inputs", "D-35, D-36, D-49.");
lead(s, "We estimated a workload from April's completed rides, request-to-completion ratio and reported vehicle availability.");
const ch7 = [["Completed rides, 6 pm hour", "≈ 5,100 rides ÷ 30 days", "≈ 170 rides / evening", "OBSERVED", "DERIVED"],
  ["Requests per completed ride", `${fmt(A.status.requests)} requests ÷ ${fmt(A.status.completed)} completed`, `≈ ${A.r_per_c.toFixed(2)} requests / ride`, "OBSERVED", "DERIVED"],
  ["Requests in that hour", "170 rides × 2.09", "≈ 355 requests / hour", "", "DERIVED + ASSUMED"],
  ["Per vehicle on duty", `355 ÷ ${A.vehicles["18:00"]} vehicles`, `≈ ${A.rho["18:00"]} requests / vehicle-hour`, "", "DERIVED + ASSUMED"]];
ch7.forEach(([h, calc, res, , b], i) => {
  const x = 0.5 + i * 3.1;
  box(s, x, 1.85, 2.9, 2.0, HEX.tint);
  txt(s, h, { x: x + 0.12, y: 1.9, w: 2.7, h: 0.5, fontSize: 13.5, bold: true });
  txt(s, calc, { x: x + 0.12, y: 2.4, w: 2.7, h: 0.4, fontSize: 13, color: HEX.muted });
  txt(s, res, { x: x + 0.12, y: 2.82, w: 2.7, h: 0.5, fontSize: 17, bold: true, color: HEX.blue });
  evid(s, b, x + 0.12, 3.43, b.length > 8 ? 1.8 : 1.15);
  if (i < 3) arrow(s, x + 2.92, 2.85, x + 3.08, 2.85, HEX.ink);
});
box(s, 0.5, 4.05, 12.3, 0.95, HEX.paleOrange);
evid(s, "ASSUMED", 0.65, 4.15, 1.15);
txt(s, "This assumes the monthly request-to-completion ratio applies within the hour, and uses vehicle availability reported across services. It is an estimated workload, not observed arrivals.",
  { x: 1.95, y: 4.08, w: 10.75, h: 0.9, fontSize: 14, valign: "middle" });
box(s, 0.5, 5.2, 7.4, 1.5, HEX.white, HEX.line);
txt(s, [{ text: "Five vans × hourly load → ", options: { bold: true } }, { text: `${A.five_van.join(" / ")} requests in three hours = 168`, options: { bold: true, color: HEX.blue } }],
  { x: 0.65, y: 5.28, w: 7.1, h: 0.45, fontSize: 16 });
txt(s, "Five vans is our planned evening (a team design choice). Each hour uses its own rides and vehicles on duty. Illustrative range about 150–260 (unknown Homewood share of vehicles, repeat requests).", { x: 0.65, y: 5.75, w: 7.1, h: 0.85, fontSize: 12.5, color: HEX.muted });
status(s, "PLANNED", 8.2, 5.25, 3.2);
txt(s, "The five-van, 168-request evening is designed but has not been run.", { x: 8.2, y: 5.65, w: 4.6, h: 0.9, fontSize: 13.5 });
source(s, "April dashboards (rides by hour, status totals, vehicles on duty); " + DOC + "decision_log.md D-35, D-36, D-49.");

// 8 WHAT WE ACTUALLY TESTED
s = content("We started with a smaller, deliberately demanding hour", "From aggregates to scenario inputs", "L5 pilot: D-56 settings, D-57 batch.");
lead(s, "The current results come from two vans and 28 requests in one hour, repeated across 30 constructed nights.");
const tx0 = 0.9, txw = 7.4, tY = 3.1;
const tmx = (m) => tx0 + txw * m / 60;
line(s, tx0, tY, tx0 + txw, tY, HEX.ink, 1.5);
[0, 10, 20, 30, 40, 50, 60].forEach((m) => { line(s, tmx(m), tY - 0.07, tmx(m), tY + 0.07, HEX.ink); txt(s, `18:${String(m % 60).padStart(2, "0")}`.replace("18:00", m === 60 ? "19:00" : "18:00"), { x: tmx(m) - 0.4, y: tY + 0.1, w: 0.8, h: 0.28, fontSize: 10.5, color: HEX.muted, align: "center" }); });
s.addShape(pres.shapes.RECTANGLE, { x: tmx(20), y: tY - 0.95, w: tmx(30) - tmx(20), h: 0.85, fill: { color: HEX.orange, transparency: 25 }, line: { color: HEX.orange } });
txt(s, `burst: ${PL.burst_placed} of 28 placed here`, { x: tmx(20) - 0.6, y: tY - 1.45, w: tmx(30) - tmx(20) + 1.2, h: 0.45, fontSize: 12.5, bold: true, align: "center", color: "8E3A0E" });
s.addShape(pres.shapes.RECTANGLE, { x: tx0, y: tY - 0.38, w: txw, h: 0.28, fill: { color: HEX.blue, transparency: 70 }, line: { color: HEX.blue, transparency: 70 } });
txt(s, `${28 - PL.burst_placed} spread over the hour`, { x: tx0 + 0.1, y: tY - 0.72, w: 2.6, h: 0.32, fontSize: 12, color: HEX.blue });
txt(s, `Arrivals 18:00–19:00. Background requests can also fall in the burst window, so ${PL.in_burst_window_min}–${PL.in_burst_window_max} requests (mean ${PL.in_burst_window_mean}) arrive in 18:20–18:30 on a night; ${PL.passengers_min}–${PL.passengers_max} passengers per night.`,
  { x: 0.5, y: 3.6, w: 8.0, h: 0.65, fontSize: 12.5, color: HEX.muted });
const facts8 = [["2 vans", `${PL.seats} seats each`], ["28 requests", "in one hour"], ["30 nights", "distinct constructed nights"], ["× 6 rules", "transfer rules, defined on slide 17"]];
facts8.forEach(([a, b], i) => {
  const x = 8.85 + (i % 2) * 2.0, y = 1.8 + Math.floor(i / 2) * 1.25;
  box(s, x, y, 1.9, 1.1, HEX.paleBlue);
  txt(s, [{ text: a, options: { bold: true, fontSize: 20, color: HEX.blue, breakLine: true } }, { text: b, options: { fontSize: 12 } }], { x: x + 0.05, y: y + 0.05, w: 1.8, h: 1.0, align: "center", valign: "middle" });
});
status(s, "TESTED", 8.85, 4.4, 3.9);
box(s, 0.5, 4.5, 8.0, 2.25, HEX.tint);
txt(s, [{ text: "This is a controlled pilot, not a reconstruction of a typical April night.", options: { bold: true, breakLine: true } },
  { text: `Its load is 14 requests per van-hour, close to the ${A.rho["18:00"]} estimated for 6 pm (per vehicle reported across all services), but the burst deliberately concentrates demand, and two vans are a small fleet. It is designed to stress the transfer decision.`, options: {} }],
  { x: 0.65, y: 4.58, w: 7.7, h: 2.1, fontSize: 14 });
txt(s, "“Tested in simulation” means run in our model, not validated against Hopkins operations.", { x: 8.85, y: 4.8, w: 3.95, h: 0.9, fontSize: 12, color: HEX.muted, italic: true });
source(s, "data/scenarios/v2/L5 (frozen inputs); " + DOC + "scenario_spec.md §8; decision_log.md D-56, D-57.");

// 9 GEOGRAPHY
s = content("Knowing the endpoints does not identify the journeys", "From aggregates to scenario inputs", "Gravity prior + iterative proportional fitting, D-18.");
lead(s, "Two different sets of trips can produce exactly the same pickup and drop-off totals.");
function toy(x, y, cells, title) {
  txt(s, title, { x, y, w: 2.9, h: 0.35, fontSize: 14, bold: true, color: HEX.muted });
  const rows = [["", "to X", "to Y", "total"], ["from A", String(cells[0]), String(cells[1]), "2"], ["from B", String(cells[2]), String(cells[3]), "2"], ["total", "2", "2", "4"]];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 0 || i === 3 || j === 3, align: "center", color: HEX.ink,
    fill: { color: (i === 3 || j === 3) && i > 0 && j > 0 ? HEX.paleGreen : (i === 0 || j === 0 ? HEX.tint : HEX.white) } } }))),
    Object.assign({ x, y: y + 0.4, w: 2.9, colW: [0.8, 0.7, 0.7, 0.7], rowH: 0.42, fontSize: 14 }, TB));
}
toy(0.5, 1.8, [2, 0, 0, 2], "Trips, version 1");
toy(3.75, 1.8, [1, 1, 1, 1], "Trips, version 2");
txt(s, "Green cells are all the maps show. Both versions match them exactly.", { x: 0.5, y: 3.95, w: 6.3, h: 0.4, fontSize: 13, color: HEX.muted });
box(s, 0.5, 4.45, 6.3, 2.3, HEX.paleOrange);
evid(s, "ASSUMED", 0.65, 4.55, 1.15);
txt(s, "We assumed nearby journeys were more likely, then balanced the synthetic trips to preserve the observed location totals.", { x: 0.65, y: 4.9, w: 6.0, h: 0.75, fontSize: 14, bold: true });
bullets(s, ["Distance preference: each extra minute of driving multiplies a pair's weight by about 0.9 (assumed rate 0.1 per minute)",
  "Balancing: rows and columns rescaled in turn until both April location totals match"], { x: 0.65, y: 5.65, w: 6.0, h: 1.1, fontSize: 12.5 });
s.addImage({ path: FIG("map_synthetic_hour.png"), x: 7.4, y: 1.75, w: 5.0, h: 5.0 * 4.4 / 4.2, sizing: { type: "contain", w: 5.0, h: 5.0 } });
source(s, "April pickup and drop-off maps (place totals); " + DOC + "decision_log.md D-18; map: the first constructed pilot night.");

// 10 PARTY SIZES
s = content("One average can hide very different groups", "From aggregates to scenario inputs", "D-38 (shares), D-33 (XL for a party of five).");
lead(s, "April helps identify an average group size. It does not tell us the full distribution of groups.");
const G = N.groups, lab10 = ["1", "2", "3", "4", "5"];
s.addChart(pres.charts.BAR, [
  { name: "Example A (mean 1.386)", labels: lab10, values: G.h1 }, { name: "Example B (mean 1.386)", labels: lab10, values: G.h2 },
  { name: "Our assumption (mean 1.405)", labels: lab10, values: G.ours }],
  chartOpts({ x: 0.4, y: 1.75, w: 7.4, h: 5.0, barDir: "col", barGrouping: "clustered", chartColors: [HEX.faint, HEX.yellow, HEX.blue],
    showLegend: true, legendPos: "t", legendFontSize: 12, showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 9.5, dataLabelFormatCode: "0%",
    dataLabelColor: HEX.ink, valAxisLabelFormatCode: "0%", valAxisMinVal: 0, valAxisMaxVal: 0.9, catAxisLabelFontSize: 13, valAxisLabelFontSize: 11,
    showCatAxisTitle: true, catAxisTitle: "passengers in the request", catAxisTitleFontSize: 12, catAxisTitleColor: HEX.muted, catAxisTitleFontFace: "+mn-lt" }));
box(s, 8.1, 1.8, 4.7, 1.45, HEX.tint);
evid(s, "DERIVED", 8.25, 1.9, 1.15);
txt(s, "1.386", { x: 9.5, y: 1.82, w: 2.5, h: 0.5, fontSize: 26, bold: true, color: HEX.blue });
txt(s, "van passengers per completed van request (ratio of two observed totals)", { x: 8.25, y: 2.38, w: 4.45, h: 0.8, fontSize: 12.5 });
txt(s, "Requests with 3 or more passengers: Example A 8%, Example B 12.3%, ours 9%. Examples A and B are illustrations, not data.", { x: 8.1, y: 3.35, w: 4.7, h: 0.8, fontSize: 12.5 });
box(s, 8.1, 4.25, 4.7, 2.5, HEX.paleOrange);
evid(s, "ASSUMED", 8.25, 4.35, 1.15);
bullets(s, ["Our chosen group-size mix is an assumption informed by the average—not a distribution recovered from April. It covers all requests, so its mean (1.405) need not equal 1.386",
  "Groups matter: seats per van, and waiting counted per passenger (slide 16)", "A party of five transferred to Lyft rides together in one XL (team decision)"],
  { x: 8.25, y: 4.68, w: 4.45, h: 2.05, fontSize: 11.5 });
source(s, "April dashboards (passengers, completed van requests); " + DOC + "decision_log.md D-38, D-33. Bar labels rounded.");

// 11 CANCELLATIONS AND PATIENCE
s = content("One status label hides different events", "From aggregates to scenario inputs", "Patience: Weibull shape 1.5, median 18 min, placeholder (D-39); share of 'Cancelled' that is abandonment, 50-75% range (D-49).");
lead(s, "‘Cancelled’ does not tell us whether a rider gave up or a dispatcher moved the request to Lyft.");
const st = A.status;
const lay11 = [["Observation", "OBSERVED", HEX.tint, `${fmt(st.canceled)} of ${fmt(st.requests)} requests (${pct(st.canceled_share)}) ended “Canceled”. The label alone does not say why.`],
  ["Assumed status mapping", "ASSUMED", HEX.paleOrange, "We assume requests moved to Lyft also close as “Canceled” in the van system. The share that is riders giving up is kept as a range (50–75%) to test, not a fixed number."],
  ["Hidden rider patience", "ASSUMED", HEX.paleViolet, "Each simulated rider gets a private deadline the dispatcher cannot see. Placeholder: median 18 minutes, waiting-dependent (Weibull)."]];
lay11.forEach(([h, b, f, t], i) => {
  const x = 0.5 + i * 4.15;
  box(s, x, 1.85, 3.95, 3.3, f);
  txt(s, h, { x: x + 0.15, y: 1.93, w: 3.65, h: 0.45, fontSize: 17, bold: true });
  evid(s, b, x + 0.15, 2.43, 1.15);
  txt(s, t, { x: x + 0.15, y: 2.82, w: 3.65, h: 2.25, fontSize: 14 });
  if (i < 2) arrow(s, x + 3.97, 3.5, x + 4.13, 3.5, HEX.ink);
});
box(s, 0.5, 5.35, 12.3, 1.35, HEX.white, HEX.violet);
txt(s, [{ text: "The patience distribution is provisional. It lets the simulator represent abandonment; it is not a behavioural distribution measured from April. ", options: { bold: true } },
  { text: "Many different patience distributions could produce the same cancellation share, so a chosen share does not pin one down.", options: {} }],
  { x: 0.65, y: 5.4, w: 12.0, h: 1.25, fontSize: 14, valign: "middle" });
source(s, "April dashboard status totals (digitized sums also show 99 “Denied”); " + DOC + "decision_log.md D-39, D-49; methodology Appendix C.");

// 12 NO-SHOWS
s = content("The simulator needs a probability at vehicle arrival", "From aggregates to scenario inputs", "D-40, D-48; methodology Appendix C.");
lead(s, "The share of all requests marked ‘No Show’ is different from the chance of a no-show when a vehicle actually arrives.");
const fr12 = [["Divide by all requests", fmt(st.noshow), fmt(st.requests), pct(A.noshow_all, 1), "includes requests no vehicle ever reached", HEX.tint, "DERIVED"],
  ["Divide by van arrivals (completed + no-show)", fmt(st.noshow), fmt(A.van_arrivals), pct(A.noshow_arrival, 1), "a no-show can only happen when a vehicle arrives", HEX.paleBlue, "DERIVED + ASSUMED"]];
fr12.forEach(([h, num, den, r, why, fill, b], i) => {
  const x = 0.5 + i * 6.25;
  box(s, x, 1.85, 6.0, 2.6, fill);
  txt(s, h, { x: x + 0.2, y: 1.92, w: 5.6, h: 0.42, fontSize: 16, bold: true });
  txt(s, num, { x: x + 0.2, y: 2.4, w: 2.6, h: 0.5, fontSize: 24, align: "center" });
  line(s, x + 0.4, 2.95, x + 2.6, 2.95, HEX.ink, 1.5);
  txt(s, den, { x: x + 0.2, y: 3.0, w: 2.6, h: 0.5, fontSize: 24, align: "center" });
  txt(s, "= " + r, { x: x + 2.9, y: 2.55, w: 2.9, h: 0.75, fontSize: 38, bold: true, color: i ? HEX.blue : HEX.muted });
  txt(s, why, { x: x + 0.2, y: 3.62, w: 4.0, h: 0.6, fontSize: 13, color: HEX.muted });
  evid(s, b, x + 4.1, 4.02, b.length > 8 ? 1.75 : 1.15);
});
box(s, 6.75, 4.6, 6.0, 2.1, HEX.paleOrange, HEX.orange);
txt(s, [{ text: "8.9% holds only if: ", options: { bold: true, breakLine: true } },
  { text: "“No Show” was recorded after a real van arrival; “Completed” counts van trips; and Lyft hand-offs sit in “Canceled”.", options: { breakLine: true } },
  { text: "Our arrival-based probability is provisional because it depends on how the dashboard statuses were recorded.", options: { bold: true } }],
  { x: 6.9, y: 4.65, w: 5.75, h: 2.0, fontSize: 13.5 });
txt(s, "The simulator gives each rider one presence draw, used whichever vehicle arrives (van or Lyft).", { x: 0.5, y: 4.7, w: 6.0, h: 0.8, fontSize: 14 });
source(s, "April dashboard status totals; " + DOC + "decision_log.md D-40, D-48; scenario_methodology.md Appendix C.");

// 13 BLUEPRINT
s = content("The evidence becomes a scenario blueprint", "From aggregates to scenario inputs", "Every input is frozen and hash-checked before any run.");
lead(s, "A scenario combines evidence-based inputs, explicit assumptions and hidden rider behaviour.");
const groups13 = [["Demand", HEX.paleBlue, [["Arrival times", "DERIVED + ASSUMED"], ["Locations", "DERIVED + ASSUMED"], ["Trip pairing", "ASSUMED"], ["Party sizes", "DERIVED + ASSUMED"]]],
  ["Resources", HEX.tint, [["Vans and duty times", "DESIGNED"], ["Capacity (14 seats)", "DESIGNED"], ["Travel times × 1.2", "DERIVED + ASSUMED"]]],
  ["Behaviour (hidden)", HEX.paleViolet, [["Patience", "ASSUMED"], ["Presence at the curb", "DERIVED + ASSUMED"], ["Lyft delay", "ASSUMED"]]],
  ["Experiment settings", HEX.paleOrange, [["Van dispatcher (fixed)", "DESIGNED"], ["Transfer rule (varied)", "DESIGNED"], ["Ordering lag 2 min", "ASSUMED"]]]];
groups13.forEach(([h, f, items], i) => {
  const x = 0.5 + i * 3.1;
  box(s, x, 1.85, 2.95, 3.65, f);
  txt(s, h, { x: x + 0.12, y: 1.92, w: 2.7, h: 0.42, fontSize: 16, bold: true });
  items.forEach(([t, b], j) => {
    const y = 2.42 + j * 0.76;
    txt(s, t, { x: x + 0.12, y, w: 2.75, h: 0.33, fontSize: 13 });
    evid(s, b, x + 0.12, y + 0.33, b.length > 8 ? 1.8 : 1.2);
  });
});
box(s, 0.5, 5.7, 12.3, 1.0, HEX.white, HEX.line);
txt(s, [{ text: "Inputs are fixed before the run; outcomes are not. ", options: { bold: true } },
  { text: "Cancellations, no-shows and transfers happen during the run, from the hidden draws meeting the rule and the vans. They are results, not counts imposed in advance.", options: {} }],
  { x: 0.65, y: 5.72, w: 12.0, h: 0.95, fontSize: 14, valign: "middle" });
link(s, "Where each input comes from: B4 →", BK.B4, { x: 9.5, y: 7.0, w: 2.6, h: 0.3, fontSize: 10 });
source(s, DOC + "scenario_spec.md v0.8 §3–§5; decision_log.md D-18–D-56.");

// =====================================================================================================
// 14 ARCHITECTURE
pres.addSection({ title: "Model and experiment" });
s = content("Three components have different jobs", "Model and experiment", "Simulator = engine.py; van optimizer = dispatch.py (restricted route-selection MILP, HiGHS); transfer rule = lyft.py.");
const roles = [["sim", "The simulator advances time and reveals events."], ["opt", "The van optimizer chooses among feasible candidate plans."], ["rule", "The transfer rule decides whether an eligible request moves to Lyft."]];
roles.forEach(([k, t], i) => {
  const [f, c] = COMP[k];
  box(s, 0.5 + i * 4.15, 1.05, 3.95, 0.62, f, c);
  txt(s, t, { x: 0.6 + i * 4.15, y: 1.05, w: 3.75, h: 0.62, fontSize: 13.5, bold: true, valign: "middle" });
});
// left: generation
comp(s, "sim", 0.5, 2.0, 2.2, 0.75, "Scenario generator", "built once, offline");
arrow(s, 1.6, 2.77, 1.6, 3.02, HEX.muted);
comp(s, "sim", 0.5, 3.05, 2.2, 1.0, "Scenario inputs", "requests, places, parties, vans, travel times");
comp(s, "hidden", 0.5, 4.35, 2.2, 1.15, "Hidden draws", "patience, presence, Lyft delay");
arrow(s, 2.72, 3.55, 3.15, 3.9, HEX.muted);
arrow(s, 2.72, 4.9, 3.15, 4.4, HEX.violet, "dash");
// simulator core
box(s, 3.2, 2.0, 2.6, 4.7, COMP.sim[0], COMP.sim[1]);
txt(s, [{ text: "Simulator", options: { bold: true, fontSize: 16, breakLine: true } }, { text: "clock · van positions · riders aboard · request states", options: { fontSize: 12.5, breakLine: true } },
  { text: " ", options: { breakLine: true } }, { text: "Reveals a request only when it arrives; applies a hidden draw only when its event happens", options: { fontSize: 12, italic: true } }],
  { x: 3.3, y: 2.1, w: 2.4, h: 4.5, align: "center", valign: "middle" });
// dispatcher region
box(s, 6.6, 2.0, 3.95, 3.7, HEX.white, HEX.blue, { line: { color: HEX.blue, width: 1, dashType: "sysDot" } });
txt(s, "Decision step: van dispatcher + transfer rule (sees only what has happened)", { x: 6.7, y: 2.03, w: 4.0, h: 0.32, fontSize: 12, bold: true, color: HEX.blue });
comp(s, "opt", 6.75, 2.45, 3.65, 0.7, "Route generation", "candidate routes per van");
arrow(s, 8.57, 3.17, 8.57, 3.33, HEX.blue);
comp(s, "opt", 6.75, 3.35, 3.65, 0.7, "Van optimizer", "mixed-integer linear program (MILP): one route per van");
arrow(s, 8.57, 4.07, 8.57, 4.23, HEX.orange);
comp(s, "rule", 6.75, 4.25, 3.65, 0.75, "Transfer rule", "reads plan predictions; may move requests to Lyft");
arrow(s, 5.82, 2.8, 6.72, 2.8, HEX.ink);
txt(s, "observable state", { x: 5.82, y: 2.3, w: 0.8, h: 0.48, fontSize: 9.5, color: HEX.muted, align: "center" });
arrow(s, 6.72, 4.62, 5.82, 4.62, HEX.ink);
txt(s, "plan and transfers", { x: 5.82, y: 4.67, w: 0.8, h: 0.48, fontSize: 9.5, color: HEX.muted, align: "center" });
// execution and outcomes
comp(s, "sim", 6.6, 5.95, 3.95, 0.75, "Execution", "vans drive and commit to their next stop");
arrow(s, 5.82, 6.3, 6.57, 6.3, HEX.ink);
arrow(s, 10.57, 6.3, 10.92, 6.3, HEX.ink);
comp(s, "sim", 10.95, 5.6, 1.85, 1.1, "Recorded outcomes", "event log, waits, Lyft orders");
box(s, 10.75, 2.0, 2.05, 3.4, HEX.paleViolet);
txt(s, [{ text: "Hidden from the dispatcher", options: { bold: true, color: HEX.violet, breakLine: true } }, { text: "future requests; each rider's patience and presence; the real Lyft delay", options: {} }],
  { x: 10.85, y: 2.08, w: 1.85, h: 3.25, fontSize: 12.5 });
link(s, "Event order: B3 →", BK.B3, { x: 10.3, y: 7.0, w: 1.8, h: 0.3, fontSize: 10 });
source(s, "src/sim/engine.py, dispatch.py, lyft.py; " + DOC + "scenario_spec.md v0.8 §17.");

// 15 ONE DECISION CYCLE
s = content("The same decision cycle repeats as the evening unfolds", "Model and experiment", "engine.py:305-351. One rule pass per decision moment; at most one re-plan; at most one decision moment per second.");
lead(s, "The dispatcher sees requests that have arrived. It does not see future requests.", { h: 0.45 });
const loop15 = [["sim", "1  Reveal and update", "new events applied; state observed"], ["opt", "2  Generate routes", "feasible candidates per van"],
  ["opt", "3  Select routes", "MILP: one route per van"], ["rule", "4  Evaluate rule", "each request still waiting for a van"],
  ["rule", "5  Apply transfers", "accepted requests leave van planning; Lyft ordered after 2 min"], ["opt", "6  Re-plan once", "only if a transfer happened"],
  ["sim", "7  Execute", "vans depart; a van commits to its next stop"], ["sim", "8  Repeat", "at the next trigger"]];
loop15.forEach(([k, h, b], i) => {
  const row = Math.floor(i / 4), col = row === 0 ? i : 7 - i;
  const x = 0.5 + col * 3.1, y = 1.7 + row * 1.6;
  comp(s, k, x, y, 2.8, 1.15, h, b);
  if (row === 0 && i < 3) arrow(s, x + 2.82, y + 0.57, x + 3.08, y + 0.57, HEX.ink);
  if (row === 1 && i < 7) arrow(s, x - 0.02, y + 0.57, x - 0.28, y + 0.57, HEX.ink);
});
arrow(s, 0.5 + 3 * 3.1 + 1.4, 2.87, 0.5 + 3 * 3.1 + 1.4, 3.28, HEX.ink);
arrow(s, 0.5 + 1.4, 3.28, 0.5 + 1.4, 2.87, HEX.ink, "dash");
const notes15 = [["When it runs", "every 2 minutes, and at a new request, a cancellation or no-show while waiting for a van, or a van coming on duty"],
  ["Transfers", "a transfer offer is accepted with a set probability (1.0 in the pilot); a declined request is not offered again"],
  ["No cascades", "the rule runs once per decision moment; after transfers the optimizer re-plans once, and the rule is not re-run in that second"],
  ["Commitments", "a stop a van is already driving to is fixed; requests committed to a van are not eligible for transfer"]];
notes15.forEach(([h, b], i) => {
  const x = 0.5 + (i % 2) * 6.2, y = 4.95 + Math.floor(i / 2) * 0.95;
  txt(s, [{ text: h + ": ", options: { bold: true } }, { text: b, options: {} }], { x, y, w: 6.0, h: 0.9, fontSize: 12.5 });
});
source(s, "src/sim/engine.py (epoch and triggers); " + DOC + "scenario_spec.md v0.8 §17; decision_log.md D-46, D-52, D-55.");

// 16 MATHEMATICS
s = content("The optimizer compares the consequences of candidate plans", "Model and experiment", "Full formulation and M bound: B2. Weights D-29; guardrail D-47; postponement price D-53.");
lead(s, "Waiting, riding, driving and unresolved requests enter the model in different ways.", { h: 0.45 });
const obj = [["Waiting", "party size × φ(wait)", "φ is convex: 1 point per minute for the first 5 min, then 2.5, 5, 10, 20 after 5, 10, 15, 20 min"],
  ["Riding", "0.5 × party size × ride minutes", "a riding minute always counts less than a waiting minute"],
  ["Driving", "0.1 × van kilometres", "a tie-breaker"],
  ["Unresolved (postponed)", "postponement price + large constant", "the plan first serves as many requests as its candidates allow"]];
obj.forEach(([h, f, b], i) => {
  const x = 0.5 + i * 3.1;
  box(s, x, 1.65, 2.95, 1.75, i === 3 ? HEX.paleOrange : HEX.paleBlue);
  txt(s, h, { x: x + 0.1, y: 1.7, w: 2.75, h: 0.38, fontSize: 15, bold: true, color: HEX.blue });
  txt(s, f, { x: x + 0.1, y: 2.07, w: 2.75, h: 0.4, fontSize: 13.5, bold: true });
  txt(s, b, { x: x + 0.1, y: 2.47, w: 2.75, h: 0.9, fontSize: 11.5, color: HEX.muted });
  if (i < 3) txt(s, "+", { x: x + 2.92, y: 2.2, w: 0.2, h: 0.4, fontSize: 18, bold: true, align: "center", margin: 0 });
});
txt(s, "Hard constraints: seats; pickup before drop-off; one route per van; each request served once or postponed. Ride-time guardrail max(25 min, 2 × direct + 5): no plan may create or worsen an excess (an unexpected no-show wait can still push a ride over).",
  { x: 0.5, y: 3.5, w: 12.3, h: 0.62, fontSize: 12.5 });
evid(s, "ILLUSTRATIVE", 0.5, 4.2, 1.35);
txt(s, "One van; rider 1 has waited 8 min; a party of two has waited 1 min", { x: 1.95, y: 4.16, w: 6.5, h: 0.35, fontSize: 13, color: HEX.muted });
s.addTable([[{ text: "Candidate", options: { bold: true } }, { text: "Waiting", options: { bold: true } }, { text: "Riding", options: { bold: true } }, { text: "Driving", options: { bold: true } }, { text: "Points", options: { bold: true } }],
  ["Route A: rider 1 first", "52.5", "13.0", "1.0", { text: "66.5  ✓ chosen", options: { bold: true, color: HEX.green } }],
  ["Route B: party of two first", "67.5", "12.5", "1.0", { text: "81.0", options: { bold: true } }]],
  Object.assign({ x: 0.5, y: 4.55, w: 7.4, colW: [2.6, 1.1, 1.0, 1.0, 1.7], rowH: 0.4, fontSize: 13 }, TB));
txt(s, "In Route B rider 1 would wait 16 min; past 15 min each minute costs 10 points per passenger.", { x: 0.5, y: 5.8, w: 7.4, h: 0.4, fontSize: 12, color: HEX.muted });
box(s, 8.2, 4.2, 4.6, 2.5, HEX.paleBlue, HEX.blue);
txt(s, [{ text: "‘Optimal’ means best among the candidate plans generated at that decision moment—not the best possible whole evening.", options: { bold: true, breakLine: true } },
  { text: "Candidates: each van takes at most 3 new pickups, each set in its best stop order. Points are priorities, not money.", options: {} }],
  { x: 8.35, y: 4.27, w: 4.3, h: 2.35, fontSize: 13.5, valign: "middle" });
link(s, "Formulation: B2 →", BK.B2, { x: 0.5, y: 6.35, w: 2.0, h: 0.3, fontSize: 11 });
source(s, DOC + "model_design.md v0.5 §3–§4; scenario_methodology.md §6 (worked example; boarding time omitted).");

// 17 SIX RULES
s = content("We changed the transfer decision, not the van dispatcher", "Model and experiment", "Codes: R0, R1(10), R1(15), R1u(10), R2(15), R3(2) — key in B1. lyft.py:13-30.");
const rt = [["Vans only", "—", "never"], ["Wait ten minutes", "time already waited", "now − request time ≥ 10 min"], ["Wait fifteen minutes", "time already waited", "now − request time ≥ 15 min"],
  ["Unassigned for ten minutes", "time continuously outside every van plan", "≥ 10 min (timer resets when the request enters a plan)"],
  ["Predicted total wait exceeds fifteen minutes", "predicted pickup clock time − request clock time", "> 15 min"],
  ["Lyft arrives sooner", "predicted van pickup vs expected Lyft pickup", "van predicted later than now + 2 lag + 8 typical + 2 margin"]];
const kf = ["FFFFFF", HEX.tint, HEX.tint, HEX.paleGreen, HEX.paleBlue, HEX.paleBlue];
s.addTable([[hdr("Rule"), hdr("What it reads"), hdr("Moves the request to Lyft when")], ...rt.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: j === 0, fill: { color: kf[i] } } })))],
  Object.assign({ x: 0.5, y: 1.1, w: 8.6, colW: [3.0, 2.8, 2.8], rowH: 0.6, fontSize: 13 }, TB));
txt(s, "grey: waiting-time rules · green: continuously unassigned time · blue: the predictive rules (they read the van plan's prediction)", { x: 0.5, y: 5.55, w: 8.6, h: 0.3, fontSize: 12, color: HEX.muted });
box(s, 9.4, 1.1, 3.4, 2.55, HEX.paleBlue);
txt(s, [{ text: "Predicted total wait", options: { bold: true, breakLine: true } }, { text: "= predicted pickup clock time − request clock time", options: { breakLine: true } }, { text: " ", options: { breakLine: true } },
  { text: "Predicted pickup: the van plan's time, or a tentative estimate if the request is postponed; no feasible van counts as an infinitely late pickup, so the rule fires.", options: { fontSize: 12, color: HEX.muted } }],
  { x: 9.55, y: 1.18, w: 3.15, h: 2.4, fontSize: 13.5 });
box(s, 9.4, 3.85, 3.4, 2.0, HEX.tint);
txt(s, [{ text: "Eligible requests", options: { bold: true, breakLine: true } }, { text: "still waiting for a van, not committed to one, and never having declined a Lyft offer. Evaluated once per decision moment.", options: {} }],
  { x: 9.55, y: 3.92, w: 3.15, h: 1.85, fontSize: 13 });
txt(s, "The six thresholds were specified before any run (spec §6) and not changed after seeing results.", { x: 0.5, y: 5.95, w: 8.6, h: 0.35, fontSize: 13, bold: true });
link(s, "Code key: B1 →", BK.B1, { x: 0.5, y: 6.4, w: 1.8, h: 0.3, fontSize: 11 });
source(s, "src/sim/lyft.py; engine.py:305-330; " + DOC + "scenario_spec.md v0.8 §6–§7; preregistration_v2.md (draft).");

// 18 WORKED TRANSFER
s = content("What does ‘Lyft arrives sooner’ actually compare?", "Model and experiment", "Designed evening L4 under R3(2), request R011, decision epoch at 1,020 s; Lyft delay fixed at 8 min by design; acceptance 0.9.");
lead(s, "The rule compares predicted van pickup with expected Lyft pickup, including the ordering delay.", { h: 0.45 });
evid(s, "DESIGNED", 0.5, 1.6, 1.2);
txt(s, "A small hand-built evening, separate from the randomized pilot. Here the Lyft delay is fixed, so expected and realized Lyft times coincide by design.", { x: 1.8, y: 1.56, w: 11.0, h: 0.36, fontSize: 12.5, color: HEX.muted });
const tsec = (c) => { const [h, m, x] = c.split(":").map(Number); return (h - 18) * 3600 + m * 60 + x; };
const t0 = tsec("18:15:00"), t1 = tsec("18:32:00"), X0 = 0.8, XW = 11.8, YL = 4.45;
const tx = (c) => X0 + XW * (tsec(c) - t0) / (t1 - t0);
line(s, X0, YL, X0 + XW, YL, HEX.ink, 1.5);
[15, 20, 25, 30].forEach((m) => { const x = tx(`18:${m}:00`); line(s, x, YL - 0.07, x, YL + 0.07, HEX.ink); txt(s, `18:${m}`, { x: x - 0.4, y: YL + 0.1, w: 0.8, h: 0.28, fontSize: 10, color: HEX.faint, align: "center" }); });
s.addShape(pres.shapes.RECTANGLE, { x: tx(T.request), y: YL - 0.12, w: tx(T.lyft_curb) - tx(T.request), h: 0.24, fill: { color: HEX.yellow, transparency: 55 }, line: { color: HEX.yellow, width: 0 } });
s.addShape(pres.shapes.RECTANGLE, { x: tx(T.lyft_curb), y: YL - 0.06, w: tx(T.dropped) - tx(T.lyft_curb), h: 0.12, fill: { color: HEX.orange }, line: { color: HEX.orange, width: 0 } });
const evs = [[T.request, "Request", "up", HEX.ink, 1.0], [T.decision, "Decision: compare", "down", HEX.ink, 0.55], [T.booked, "Lyft ordered", "up", HEX.orange, 0.45],
  [T.lyft_curb, "Lyft at the curb (realized)", "down", HEX.orange, 0.55], [T.dropped, "Dropped off by the Lyft", "down", HEX.ink, 0.95]];
evs.forEach(([c, l, dir, col, off]) => {
  const x = tx(c);
  dot(s, x, YL, 0.2, col);
  const y = dir === "up" ? YL - off - 0.55 : YL + off;
  line(s, x, dir === "up" ? y + 0.55 : YL + 0.1, x, dir === "up" ? YL - 0.1 : y, HEX.line, 1);
  txt(s, [{ text: l, options: { bold: true, breakLine: true } }, { text: c, options: { color: HEX.muted } }], { x: x - 1.0, y, w: 2.0, h: 0.55, fontSize: 12, align: "center" });
});
const xv = tx(T.pred_van);
dot(s, xv, YL, 0.22, HEX.white, HEX.violet);
line(s, xv, YL - 0.12, xv, YL - 1.05, HEX.violet, 1, "dash");
txt(s, [{ text: "Predicted van pickup", options: { bold: true, breakLine: true, color: HEX.violet } }, { text: T.pred_van + " (a prediction only)", options: { color: HEX.violet } }], { x: xv - 1.3, y: YL - 1.62, w: 2.4, h: 0.58, fontSize: 12, align: "center" });
const xe = tx(T.expected_lyft);
line(s, xe, YL - 1.9, xv, YL - 1.9, HEX.ink, 1.25); line(s, xe, YL - 1.98, xe, YL - 1.82, HEX.ink, 1.25); line(s, xv, YL - 1.98, xv, YL - 1.82, HEX.ink, 1.25);
txt(s, `expected Lyft ${T.expected_lyft} is ${T.gap} sooner > 2 min → transfer`, { x: xe - 3.1, y: YL - 2.33, w: 4.6, h: 0.35, fontSize: 12.5, bold: true, align: "right" });
txt(s, "Wait from request to curb: " + T.wait, { x: tx(T.request) - 0.1, y: YL + 1.05, w: 4.2, h: 0.35, fontSize: 13, bold: true, color: "8A6400" });
box(s, 0.5, 6.0, 12.3, 0.8, HEX.tint);
txt(s, `Expected Lyft pickup = ${T.decision} + 2-min ordering lag + 8-min typical delay = ${T.expected_lyft}. The van pickup time is a prediction. We do not observe what that van would have done after choosing a different action.`,
  { x: 0.65, y: 6.02, w: 12.0, h: 0.76, fontSize: 13.5, valign: "middle" });
source(s, "outputs/sim/L4_R3-2 (epochs.jsonl, outcomes.csv: request R011); " + DOC + "scenario_spec.md §6.");

// 19 POSTPONEMENT PRICE
s = content("A cheap postponement price could keep a rider waiting", "Model and experiment", "Original pending price vs A (adopted, provisional) vs route-based B; D-53. Example from the math review of 21 Oct, §7.");
lead(s, "The first formulation could price postponement more cheaply than a physically possible pickup.", { h: 0.45 });
txt(s, "1  The flaw: at 18:15 on the designed evening, a party of five had waited 15 min", { x: 0.5, y: 1.6, w: 6.1, h: 0.4, fontSize: 14, bold: true });
s.addChart(pres.charts.BAR, [{ name: "Points", labels: ["Cost charged to postpone", `Cost of serving at the earliest possible pickup (${P.r002.earliest_pickup})`],
  values: [P.r002.charged_original_pts, P.r002.charged_at_earliest_pts] }],
  chartOpts({ x: 0.4, y: 2.0, w: 6.2, h: 2.6, barDir: "bar", chartColors: [HEX.orange, HEX.ink], showLegend: false, showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.0 \"points\"", dataLabelFontSize: 13, dataLabelColor: HEX.ink, valAxisHidden: true, valGridLine: { style: "none" }, catAxisLabelFontSize: 12,
    valAxisMaxVal: 560, catAxisOrientation: "maxMin", barGapWidthPct: 50 }));
txt(s, "Postponing looked cheaper than any service a van could really give, so a long-waiting party could be left waiting.", { x: 0.5, y: 4.6, w: 6.1, h: 0.6, fontSize: 12.5, color: HEX.muted });
txt(s, "2  Controlled comparison: the whole designed evening, vans only, three formulations (all three in B5)", { x: 6.9, y: 1.6, w: 5.9, h: 0.6, fontSize: 14, bold: true });
s.addTable([[{ text: "", options: {} }, { text: "First version", options: { bold: true } }, { text: "Adopted", options: { bold: true, color: HEX.green } }],
  ["Worst wait", P.original.max + " min", { text: P.A.max + " min", options: { bold: true } }], ["Mean wait", P.original.mean + " min", P.A.mean + " min"],
  ["Median wait", P.original.median + " min", P.A.median + " min"]],
  Object.assign({ x: 6.9, y: 2.25, w: 5.9, colW: [2.1, 1.9, 1.9], rowH: 0.42, fontSize: 13.5 }, TB));
txt(s, "The adopted approximation reduced the worst wait in this designed case. It did not reduce average waiting.", { x: 6.9, y: 4.0, w: 5.9, h: 0.65, fontSize: 13.5, bold: true });
box(s, 0.5, 5.35, 6.0, 1.35, HEX.paleGreen);
txt(s, [{ text: "3  Adopted (provisionally): ", options: { bold: true } }, { text: "price postponement at the earliest time any on-duty van could physically reach the request. It changes cost coefficients only, adding no variables.", options: {} }],
  { x: 0.65, y: 5.4, w: 5.75, h: 1.25, fontSize: 13, valign: "middle" });
box(s, 6.8, 5.35, 6.0, 1.35, HEX.paleViolet);
txt(s, [{ text: "4  Still optimistic: ", options: { bold: true } }, { text: "it ignores the work the nearest van is already doing. One designed evening does not show a general improvement.", options: {} }],
  { x: 6.95, y: 5.4, w: 5.75, h: 1.25, fontSize: 13, valign: "middle" });
link(s, "Three formulations: B5 →", BK.B5, { x: 0.5, y: 6.75, w: 2.4, h: 0.28, fontSize: 10 });
source(s, "outputs/sim/d53_experiment; " + DOC + "decision_log.md D-53; model_design.md v0.5 §3.5. Provisional choice.");

// 20 EXPERIMENTAL CONTROL
s = content("Replay the same night; change one rule", "Model and experiment", "Paired design: D-57 batch_L5_v1.");
lead(s, "Each rule faces the same requests and hidden rider inputs, so differences reflect the rule within this specified model.");
box(s, 0.5, 1.95, 3.4, 3.7, HEX.ink);
txt(s, [{ text: "One constructed night", options: { bold: true, fontSize: 19, breakLine: true } }, { text: " ", options: { breakLine: true } },
  { text: "same requests, places and parties", options: { breakLine: true } }, { text: "same hidden patience and presence", options: { breakLine: true } },
  { text: "same Lyft delay per rider", options: { breakLine: true } }, { text: "same vans", options: {} }],
  { x: 0.65, y: 2.05, w: 3.1, h: 3.5, fontSize: 14, color: HEX.white, align: "center", valign: "middle" });
RULES.forEach((r, i) => {
  const y = 1.95 + i * 0.63;
  arrow(s, 3.95, 3.8, 4.75, y + 0.26, HEX.muted);
  comp(s, "rule", 4.8, y, 3.9, 0.52, NAME[r], null, { fontSize: 13, align: "left" });
});
box(s, 9.1, 1.95, 3.7, 3.7, HEX.paleBlue);
txt(s, [{ text: "Thirty nights replayed six ways are thirty paired scenarios—not 180 independent nights.", options: { bold: true, breakLine: true } }, { text: " ", options: { breakLine: true } },
  { text: "Pairing removes night-to-night differences from each comparison. It does not make the nights representative of April.", options: {} }],
  { x: 9.25, y: 2.05, w: 3.4, h: 3.5, fontSize: 14, valign: "middle" });
status(s, "TESTED", 0.5, 5.9, 3.0);
txt(s, "Provisional settings: 2-min ordering lag; every Lyft offer accepted; 8.9% no-show per arrival; placeholder patience; van travel × 1.2.", { x: 3.7, y: 5.85, w: 9.1, h: 0.75, fontSize: 13.5 });
source(s, DOC + "decision_log.md D-56, D-57; outputs/sim/batch_L5_v1/summary.md.");

// =====================================================================================================
// 21 VERIFICATION
pres.addSection({ title: "Findings" });
s = content("We checked implementation before interpreting outcomes", "Findings", "Diagnostics in B8. AI use logged in docs/ai_use_log.md.");
lead(s, "Verification asks whether the code implements the specified model. Validation asks whether the model represents the real service.");
box(s, 0.5, 1.85, 7.6, 3.75, HEX.paleGreen);
txt(s, "Verification evidence", { x: 0.7, y: 1.92, w: 7.2, h: 0.4, fontSize: 17, bold: true, color: HEX.green });
const ver = [["to the second", "3 small designed evenings reproduce hand-computed event times"], ["292,181", "plan combinations on a designed evening, enumerated by a separate brute-force program over the same candidates; always the same choice"],
  ["253 tests", "pass; 168 written by separate AI review agents that did not reuse the simulator's code"], ["6 of 6", "sampled reruns byte-identical"]];
ver.forEach(([n, l], i) => {
  const y = 2.38 + i * 0.8;
  txt(s, n, { x: 0.7, y, w: 2.2, h: 0.72, fontSize: 21, bold: true, color: HEX.green, valign: "middle" });
  txt(s, l, { x: 2.9, y, w: 5.1, h: 0.72, fontSize: 13, valign: "middle" });
});
box(s, 8.4, 1.85, 4.4, 3.75, HEX.paleOrange);
txt(s, "Not validation", { x: 8.6, y: 1.92, w: 4.0, h: 0.4, fontSize: 17, bold: true, color: HEX.orange });
bullets(s, ["Do riders behave like our hidden draws?", "Do our evenings resemble real Homewood nights?", "Would the rules behave the same in real operations?"], { x: 8.6, y: 2.4, w: 4.05, h: 3.1, fontSize: 14 });
box(s, 0.5, 5.8, 12.3, 0.9, HEX.white, HEX.line);
txt(s, "AI wrote the simulator code and the checks, under our direction. Separate implementations are useful checks, but they share our assumptions and do not replace our own understanding of the model.",
  { x: 0.65, y: 5.82, w: 12.0, h: 0.86, fontSize: 13.5, valign: "middle", bold: true });
link(s, "Diagnostics: B8 →", BK.B8, { x: 0.5, y: 6.72, w: 2.0, h: 0.28, fontSize: 10 });
source(s, "Phase 4 log; tests/; outputs/sim/batch_L5_v1/reproducibility.json; docs/ai_use_log.md.");

// 22 MAIN FINDING
s = content("The predictive rules reached more requests promptly—and used more Lyft", "Findings", "Full table B6. Reached = vehicle curb arrival within 15 min of the request, over all 28 requests.");
txt(s, "30 constructed burst-demand nights; provisional rider behaviour.", { x: 0.5, y: 1.0, w: 12.3, h: 0.4, fontSize: 16, bold: true, color: HEX.orange });
const lab22 = RULES.map((r, i) => `${NAME[r]} · ${Bt.bookings[i] ? Bt.bookings[i].toFixed(1) + " Lyft orders/night" : "no Lyft"}`);
s.addChart(pres.charts.BAR, [{ name: "Reached within 15 min", labels: lab22, values: Bt.reached }],
  chartOpts({ x: 0.4, y: 1.45, w: 8.2, h: 5.3, barDir: "bar", chartColors: [HEX.faint, HEX.faint, HEX.faint, HEX.faint, HEX.blue, HEX.blue], showLegend: false, showTitle: true,
    title: "Share of all requests a vehicle reached at the curb within 15 min (mean of 30 nights)", titleFontSize: 13, titleColor: HEX.ink, showValue: true,
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0%", dataLabelFontSize: 13, dataLabelColor: HEX.ink, valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0%",
    catAxisLabelFontSize: 12, valAxisLabelFontSize: 10, catAxisOrientation: "maxMin", barGapWidthPct: 45 }));
status(s, "TESTED", 5.4, 6.45, 3.0);
txt(s, "blue: predictive rules · grey: the others", { x: 0.5, y: 6.75, w: 4.5, h: 0.25, fontSize: 10.5, color: HEX.muted });
box(s, 8.9, 1.5, 3.9, 2.2, HEX.paleBlue);
txt(s, "In this two-van pilot, the predictive rules reached about three quarters of requests within fifteen minutes, compared with about half under vans only. They also used roughly nine to ten and a half Lyft orders per night.",
  { x: 9.05, y: 1.55, w: 3.6, h: 2.1, fontSize: 13 });
box(s, 8.9, 3.85, 3.9, 1.3, HEX.tint);
txt(s, [{ text: "Metric: a vehicle reaching the curb—not boarding or a completed trip. ", options: { bold: true } }, { text: "A rider moved after 10–15 min of waiting almost never reaches the curb within 15 min, so this measure favours early transfer.", options: {} }], { x: 9.05, y: 3.88, w: 3.6, h: 1.25, fontSize: 11.5, valign: "middle" });
box(s, 8.9, 5.3, 3.9, 1.4, HEX.paleOrange);
txt(s, "This comparison does not isolate the benefit of prediction at an equal Lyft budget.", { x: 9.05, y: 5.35, w: 3.6, h: 1.3, fontSize: 13.5, valign: "middle", bold: true });
link(s, "All metrics: B6 →", BK.B6, { x: 8.9, y: 6.75, w: 2.0, h: 0.26, fontSize: 10 });
source(s, "outputs/sim/batch_L5_v1 (tradeoff.md, summary.md). Descriptive means; between-night SD 0.07–0.10.");

// 23 AFTER TRANSFER
s = content("Moving a request to Lyft does not end its wait", "Findings", "Fates are totals over 30 nights. Elapsed wait at transfer: median 629 s / 932 s (waiting-time rules) vs 0 s (prediction rules); technical review A.");
lead(s, "The rider still waits through ordering and Lyft arrival. Their original patience clock continues running.", { h: 0.45 });
const W0 = 0.6; let wx = W0;
[["Waiting for a van", 3.0, HEX.faint], ["Ordering lag 2 min", 1.3, HEX.yellow], ["Lyft travelling", 2.5, HEX.orange]].forEach(([t, w, c]) => {
  s.addShape(pres.shapes.RECTANGLE, { x: wx, y: 1.65, w, h: 0.48, fill: { color: c }, line: { color: HEX.white, width: 2 } });
  txt(s, t, { x: wx, y: 1.65, w, h: 0.48, fontSize: 12.5, bold: true, align: "center", valign: "middle", color: c === HEX.orange ? HEX.white : HEX.ink, margin: 0 });
  wx += w;
});
dot(s, wx, 1.89, 0.22, HEX.aqua); txt(s, "curb", { x: wx + 0.15, y: 1.74, w: 0.7, h: 0.3, fontSize: 12 });
line(s, W0 + 3.0, 1.5, W0 + 3.0, 2.25, HEX.ink, 1.5);
txt(s, "transfer", { x: W0 + 2.5, y: 2.25, w: 1.0, h: 0.28, fontSize: 11, align: "center" });
line(s, W0, 2.62, W0 + 6.8, 2.62, HEX.violet, 1.5, "dash");
txt(s, "the rider's hidden patience clock, running from the original request", { x: W0, y: 2.66, w: 6.8, h: 0.3, fontSize: 12, color: HEX.violet, italic: true });
const fr23 = RULES.slice(1).map((r) => [r, Bt.fates[r]]);
const lbl23 = fr23.map(([r, f]) => `${NAME[r]} (n = ${f.transfers}${f.transfers < 20 ? ": too few to compare" : ""})`);
s.addChart(pres.charts.BAR, [
  { name: "Lyft completed", labels: lbl23, values: fr23.map(([, f]) => f.completed) }, { name: "Lyft no-show", labels: lbl23, values: fr23.map(([, f]) => f.noshow) },
  { name: "Cancelled during the 2-min ordering lag", labels: lbl23, values: fr23.map(([, f]) => f.lag) },
  { name: "Cancelled after the Lyft was ordered", labels: lbl23, values: fr23.map(([, f]) => f.after) }],
  chartOpts({ x: 0.4, y: 3.0, w: 8.4, h: 3.95, barDir: "bar", barGrouping: "percentStacked", chartColors: [HEX.aqua, HEX.yellow, HEX.magenta, HEX.orange], showLegend: true,
    legendPos: "b", legendFontSize: 11, showValue: true, dataLabelPosition: "ctr", dataLabelFontSize: 10, dataLabelColor: HEX.ink, catAxisLabelFontSize: 11,
    valAxisLabelFontSize: 10, valAxisLabelFormatCode: "0%", catAxisOrientation: "maxMin", barGapWidthPct: 35, showTitle: true,
    title: "Outcome of each transferred request (n = transfers, totals over 30 nights)", titleFontSize: 12, titleColor: HEX.ink }));
const f10 = Bt.fates["R1(10)"];
box(s, 9.1, 1.55, 3.7, 1.75, HEX.paleOrange);
txt(s, [{ text: `${f10.lag + f10.after} of ${f10.transfers}`, options: { bold: true, fontSize: 28, color: HEX.orange, breakLine: true } },
  { text: "transferred under “Wait ten minutes” cancelled before the Lyft arrived; about a third under the prediction rules", options: { fontSize: 12.5 } }],
  { x: 9.25, y: 1.6, w: 3.4, h: 1.65 });
box(s, 9.1, 3.45, 3.7, 1.75, HEX.paleBlue);
txt(s, "Riders moved by the prediction rules had usually waited less when transferred. Under our placeholder patience, that is consistent with their lower share lost after transfer: a possible contributing mechanism, not an isolated cause.",
  { x: 9.25, y: 3.5, w: 3.4, h: 1.65, fontSize: 12, valign: "middle" });
box(s, 9.1, 5.35, 3.7, 1.4, HEX.paleViolet);
evid(s, "ASSUMED", 9.2, 5.42, 1.15);
txt(s, "Whether the gap between policies survives other patience shapes is untested.", { x: 9.2, y: 5.75, w: 3.5, h: 0.95, fontSize: 12.5 });
source(s, "outputs/sim/batch_L5_v1 per-run outcomes; transfers = Lyft orders + cancellations during the ordering lag.");

// 24 PARETO
s = content("Better service and lower Lyft use can point to different choices", "Findings", "Nondominance computed in src/sim/tradeoff.py; per-night counts in B7.");
lead(s, "A tested rule is dominated if another tested rule is at least as good on both selected objectives and strictly better on one.", { h: 0.62 });
box(s, 0.5, 1.8, 3.6, 3.85, HEX.tint);
txt(s, "Dominance, in one picture", { x: 0.65, y: 1.86, w: 3.3, h: 0.35, fontSize: 14, bold: true });
const dX = 0.95, dY = 4.75, dW = 2.95, dH = 2.3;
line(s, dX, dY, dX + dW, dY, HEX.muted); line(s, dX, dY, dX, dY - dH, HEX.muted);
txt(s, "Lyft use →", { x: dX + 1.5, y: dY + 0.03, w: 1.45, h: 0.28, fontSize: 10.5, color: HEX.muted, align: "right" });
txt(s, "service ↑", { x: dX - 0.35, y: dY - dH - 0.3, w: 1.2, h: 0.28, fontSize: 10.5, color: HEX.muted });
[["A", 0.9, 1.6, HEX.blue], ["B", 1.9, 0.8, HEX.white], ["C", 2.6, 2.05, HEX.blue]].forEach(([n, x, y, c]) => { dot(s, dX + x, dY - y, 0.26, c, c === HEX.white ? HEX.ink : c); txt(s, n, { x: dX + x + 0.15, y: dY - y - 0.2, w: 0.35, h: 0.3, fontSize: 13, bold: true }); });
txt(s, "A dominates B. A and C: neither dominates the other.", { x: 0.65, y: 5.15, w: 3.35, h: 0.45, fontSize: 11.5, color: HEX.muted });
const sx0 = 4.95, sy0 = 5.35, sw = 4.5, sh = 3.1, bx = (b) => sx0 + sw * b / 12, ry = (r) => sy0 - sh * (r - 0.4) / 0.4;
line(s, sx0, sy0, sx0 + sw, sy0, HEX.muted); line(s, sx0, sy0, sx0, sy0 - sh, HEX.muted);
[0, 4, 8, 12].forEach((b) => txt(s, String(b), { x: bx(b) - 0.25, y: sy0 + 0.03, w: 0.5, h: 0.25, fontSize: 10, color: HEX.faint, align: "center" }));
[0.4, 0.6, 0.8].forEach((r) => txt(s, pct(r), { x: sx0 - 0.55, y: ry(r) - 0.13, w: 0.5, h: 0.25, fontSize: 10, color: HEX.faint, align: "right" }));
txt(s, "Lyft orders per night (lower is better)", { x: sx0, y: sy0 + 0.27, w: sw, h: 0.28, fontSize: 11, color: HEX.muted, align: "center" });
txt(s, "Reached within 15 min (higher is better)", { x: sx0 - 0.6, y: 1.8, w: 4.6, h: 0.28, fontSize: 11, color: HEX.muted });
const lbl24 = { R0: ["Vans only; Unassigned for ten minutes (overlap)", 0.15, 0.32, "left", 2.6], "R1(10)": ["Wait ten minutes", 0.12, -0.3, "left", 2.0],
  "R1(15)": ["Wait fifteen minutes", -0.9, -0.3, "left", 2.0], "R1u(10)": null, "R2(15)": ["Predicted total wait exceeds fifteen minutes", -3.2, 0.12, "right", 3.05],
  "R3(2)": ["Lyft arrives sooner", -2.3, -0.2, "right", 2.1] };
RULES.forEach((r, i) => {
  const x = bx(Bt.bookings[i]), y = ry(Bt.reached[i]);
  dot(s, x, y, 0.2, Bt.nondominated[i] ? HEX.blue : HEX.white, Bt.nondominated[i] ? HEX.blue : HEX.ink);
  if (lbl24[r]) txt(s, lbl24[r][0], { x: x + lbl24[r][1], y: y + lbl24[r][2] - 0.14, w: lbl24[r][4], h: 0.3, fontSize: 10.5, align: lbl24[r][3] });
});
txt(s, "filled = not dominated among the six (means of 30 nights)", { x: sx0, y: sy0 + 0.55, w: sw, h: 0.28, fontSize: 10.5, color: HEX.muted, align: "center" });
box(s, 9.85, 1.8, 2.95, 4.95, HEX.paleBlue);
bullets(s, ["Nondominated does not mean recommended.", "Vans only stays nondominated through zero Lyft use.",
  "“Unassigned for ten minutes” is dominated on the means: service within about one request in 840 of vans only, slightly more Lyft (0.23 vs 0 a night). No noise margin applied.",
  "This is the nondominated set among six tested rules under these two objectives—not the complete frontier of possible policies.",
  "Adding objectives or decision criteria can change the assessment."], { x: 9.95, y: 1.88, w: 2.8, h: 4.8, fontSize: 11.5 });
link(s, "Night by night: B7 →", BK.B7, { x: 0.5, y: 6.4, w: 2.2, h: 0.3, fontSize: 11 });
source(s, "src/sim/tradeoff.py; outputs/sim/batch_L5_v1/tradeoff.md. Descriptive, not a ranking; decision criteria (D-50) not agreed.");

// 25 LEADER-FOLLOWER
s = content("Could we choose the transfer policy systematically?", "Findings", "Bilevel terminology: Colson, Marcotte & Savard (2007); Dempe (2002). Technical review C.");
lead(s, "One possible extension is to optimize transfer policy while anticipating how the routing dispatcher responds.", { h: 0.45 });
status(s, "PROPOSED", 0.5, 1.6, 3.4);
comp(s, "rule", 0.5, 2.15, 3.7, 1.0, "Policy designer", "chooses the rule and its threshold");
arrow(s, 4.22, 2.65, 4.9, 2.65, HEX.ink, "solid", 2);
comp(s, "opt", 4.95, 2.15, 3.7, 1.0, "Dispatcher responds", "re-plans the vans for the requests left after transfers");
arrow(s, 6.8, 3.17, 6.8, 3.6, HEX.ink, "solid", 2);
comp(s, "sim", 4.95, 3.62, 3.7, 0.95, "Service and resource outcomes", "share reached, Lyft orders, van-km");
arrow(s, 4.93, 4.1, 2.35, 4.1, HEX.ink, "dash", 2); arrow(s, 2.35, 4.1, 2.35, 3.17, HEX.ink, "dash", 2);
txt(s, "outcomes inform the policy choice", { x: 2.45, y: 4.12, w: 2.4, h: 0.3, fontSize: 11, color: HEX.muted, italic: true });
box(s, 8.95, 2.15, 3.85, 2.42, HEX.tint);
txt(s, [{ text: "Today: ", options: { bold: true } }, { text: "six fixed rules compared on the same nights. A finite search finds the best option in a finite set for the average over our sampled nights—not the true expectation, not continuous thresholds, not all policies.", options: {} }],
  { x: 9.1, y: 2.2, w: 3.6, h: 2.32, fontSize: 12.5, valign: "middle" });
txt(s, "To state this precisely as a leader–follower (bilevel) model, we would still need to define:", { x: 0.5, y: 4.8, w: 12.3, h: 0.35, fontSize: 14, bold: true });
const need = ["the leader's choices (rule family, threshold range)", "the follower: one decision moment at a time, or the whole evening", "how ties in the follower's best response are treated",
  "the expectation over constructed nights", "the loss and the weight on Lyft use", "any budget or service-floor constraints"];
need.forEach((t, i) => txt(s, `${i + 1}. ${t}`, { x: 0.5 + (i % 3) * 4.15, y: 5.22 + Math.floor(i / 3) * 0.6, w: 4.0, h: 0.55, fontSize: 12.5 }));
source(s, DOC + "scenario_methodology.md §7b; Colson, Marcotte & Savard (2007), Ann. Oper. Res. 153:235–256; Dempe (2002).");

// =====================================================================================================
// 26 LIMITS
pres.addSection({ title: "Limits and next steps" });
s = content("Which assumptions could change the answer?", "Limits and next steps", "36 ride-time excess events (16 distinct requests, 10 nights) are in B8 and the handbook.");
lead(s, "The findings are conditional on the evenings and behaviours we constructed.", { h: 0.45 });
s.addTable([[hdr("Assumption"), hdr("Status"), hdr("How it could change the interpretation")],
  ["Rider patience", "ASSUMED placeholder", "The assumption we most expect to matter (untested): it sets how many riders give up and the losses after transfer"],
  ["Lyft delay", "ASSUMED", "A slower or more variable Lyft could weaken transfers; under our placeholder patience, late transfers most"],
  ["Workload and burst", "DERIVED + ASSUMED", "The pilot is deliberately heavy; at lighter load the rules may barely differ"],
  ["Geography and pairing", "ASSUMED", "Longer or more scattered trips change van reach and predicted pickups"],
  ["Candidate restriction", "DESIGNED", "At most 3 new pickups per van per decision; a richer search could change van performance and the rules' predictions"]],
  Object.assign({ x: 0.5, y: 1.65, w: 12.3, colW: [2.6, 2.3, 7.4], rowH: 0.72, fontSize: 13.5 }, TB));
txt(s, "Also open: the 15-minute measure favours early transfer; 8.9% no-show depends on the status mapping; two vans, not five; verification, not validation.", { x: 0.5, y: 6.1, w: 12.3, h: 0.5, fontSize: 13.5, color: HEX.muted });
source(s, DOC + "scenario_methodology.md §7–§9; decision_log.md D-39, D-43, D-49, D-52.");

// 27 NEXT EXPERIMENTS
s = content("Test robustness before fine-tuning a winner", "Limits and next steps", "Proposed next steps only; not run in this package.");
lead(s, "Next, we should test whether the findings survive different rider-patience and Lyft-delay assumptions, while checking feasibility at the larger fleet size.", { h: 0.62 });
const nx = [["1  Behavioural sensitivity", "Rerun the saved nights under other patience shapes and Lyft delays", HEX.paleViolet],
  ["2  Five-van feasibility", "Run the 168-request evening; check solve times and candidate limits", HEX.paleBlue],
  ["3  Agreed evaluation criteria", "Decide how much extra Lyft use one more rider reached is worth, then compute confidence intervals across the paired nights", HEX.paleOrange],
  ["4  Threshold / policy search", "Only then sweep thresholds, or pursue the leader–follower extension", HEX.paleGreen]];
nx.forEach(([h, b, f], i) => {
  const x = 0.5 + i * 3.1;
  box(s, x, 1.95, 2.95, 3.0, f);
  txt(s, h, { x: x + 0.12, y: 2.02, w: 2.7, h: 0.75, fontSize: 15.5, bold: true });
  txt(s, b, { x: x + 0.12, y: 2.8, w: 2.7, h: 1.6, fontSize: 13.5 });
  status(s, "PLANNED", x + 0.12, 4.45, 2.7);
  if (i < 3) arrow(s, x + 2.97, 3.4, x + 3.08, 3.4, HEX.ink);
});
txt(s, "Order matters: a threshold tuned to placeholder behaviour could be tuned to our assumptions rather than to the service.", { x: 0.5, y: 5.25, w: 12.3, h: 0.8, fontSize: 15, bold: true });
source(s, DOC + "scenario_methodology.md §8–§9; decision_log.md D-50, D-51.");

// 28 THE ANSWER SO FAR
s = content("What we can defend today", "Limits and next steps", "Closing slide; questions follow.");
box(s, 0.5, 1.3, 12.3, 1.7, HEX.tint);
txt(s, "Aggregate data did not give us individual journeys. It gave us constraints for building plausible evenings.", { x: 0.8, y: 1.35, w: 11.7, h: 1.6, fontSize: 24, bold: true, valign: "middle" });
box(s, 0.5, 3.25, 12.3, 2.3, HEX.paleBlue, HEX.blue);
txt(s, "Within our specified pilot, predictive transfer rules improved timely curb arrival while using more Lyft. Choosing a policy requires testing the assumptions and deciding what trade-off is acceptable.",
  { x: 0.8, y: 3.3, w: 11.7, h: 2.2, fontSize: 22, valign: "middle", color: "1B4F8A" });
status(s, "TESTED", 0.5, 5.85, 3.0);
txt(s, "in simulation, on 30 constructed two-van nights · not a policy recommendation", { x: 3.7, y: 5.82, w: 9.1, h: 0.4, fontSize: 13.5, color: HEX.muted });
link(s, "Backups →", 29, { x: 10.6, y: 7.0, w: 1.5, h: 0.28, fontSize: 10 });
source(s, "this deck, slides 6–27.");

// =====================================================================================================
// BACKUP
pres.addSection({ title: "Backup" });
s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Backup" });
slideNo++;
s.addText("Backup slides", { placeholder: "title" });
s.addText("B1 Code key · B2 Route-selection MILP · B3 Event order · B4 Where inputs come from · B5 Three postponement prices · B6 All metrics by rule · B7 Night by night · B8 Numerical diagnostics · B9 Corrected proposal claims",
  { placeholder: "body" });
Object.entries(BK).forEach(([b, n], i) => link(s, b, n, { x: 0.8 + i * 1.3, y: 6.3, w: 1.1, h: 0.35, fontSize: 14 }));
s.addNotes("Backup divider. Each backup links back to the main slide that uses it. Type a slide number and Enter to jump.");

function backup(code, title, back, notes) {
  const sl = content(code + "  " + title, "Backup", notes || "Backup " + code + ".");
  link(sl, "← back to slide " + back, back, { x: 10.5, y: 7.0, w: 1.7, h: 0.28, fontSize: 10 });
  return sl;
}
s = backup("B1", "Code key (files and questions only)", 17);
s.addTable([[hdr("Said in the talk"), hdr("Code in files and logs")], ...RULES.map((r) => [NAME[r], r]),
  ["Small designed evenings with hand-computed answers", "L1–L4 (L4: vans from 18:15, ordering lag 2 min, Lyft delay fixed 8 min, acceptance 0.9)"],
  ["The two-van pilot", "L5: 30 constructed one-hour nights, 2 vans, 28 requests"], ["The van optimizer", "Dispatcher C: restricted route-selection MILP (HiGHS)"],
  ["The adopted postponement price", "Pending price A (earliest physical pickup)"], ["Lyft order; ordering lag", "“booking” and “booking lag” in files (D-43)"],
  ["Numbered decisions", "D-xx entries in docs/technical/decision_log.md"]],
  Object.assign({ x: 0.5, y: 1.15, w: 12.3, colW: [5.0, 7.3], rowH: 0.4, fontSize: 13 }, TB));
source(s, "src/sim/lyft.py; scenario_spec.md §6, §8; decision log.");

s = backup("B2", "The route-selection MILP at one decision moment", 16);
txt(s, [{ text: "min  Σ_v Σ_k c_vk y_vk  +  Σ_r π_r u_r", options: { breakLine: true } },
  { text: "s.t.  Σ_k y_vk = 1  for every van v        (one route per van)", options: { breakLine: true } },
  { text: "        Σ_{v,k: r ∈ S_vk} y_vk + u_r = 1  for every waiting request r   (served once, or postponed)", options: { breakLine: true } },
  { text: "        y, u ∈ {0, 1};   S_vk = requests picked up by candidate route k of van v", options: {} }], { x: 0.5, y: 1.15, w: 12.3, h: 1.7, fontSize: 18, fontFace: "Cambria" });
bullets(s, ["c_vk: route points (waiting φ with slopes 1/2.5/5/10/20 per passenger-minute after 0/5/10/15/20 min; riding 0.5 per passenger-minute; 0.1 per km; Ψ only for unavoidable existing guardrail excess); exact integers",
  "Candidates: every subset of at most 3 waiting requests per van, each in its best stop order (exact search); the van's committed work is always a candidate",
  "π_r = b_r + M; b_r from the adopted postponement price; M = 1 + Σ_v (max_k c_vk − min_k c_vk) + Σ_r b_r: every proven-optimal solution postpones the fewest requests the candidates allow",
  "Ride-time guardrail max(25, 2 × direct + 5) min: no candidate may create or worsen an excess",
  "HiGHS: relative gap 0, absolute gap 0.5 units; ties broken by a fixed canonical order; a failed solve is logged, never replaced by a heuristic"], { x: 0.5, y: 3.0, w: 12.3, h: 3.8, fontSize: 14 });
source(s, "model_design.md v0.5 §3; decision log D-47, D-52 (amendments), D-53.");

s = backup("B3", "Event order and a request's life", 14);
bullets(s, ["Same-second order: drop-offs → curb arrivals (stop the patience clock) → service ends → vans on/off duty → new requests → patience checks → Lyft orders → decision moment → departures",
  "Decision-moment triggers in the code: new request; cancellation or no-show while waiting for a van; van coming on duty; the 2-minute tick (van going off duty does not trigger one; Lyft events never do)",
  "A van commits to a stop when it departs toward it; a committed request is not eligible for transfer",
  "After a transfer: a 2-min ordering lag, then the rider's hidden Lyft delay; the rider may cancel at any point before the Lyft reaches the curb",
  "During an absent rider's 3-min curb wait, planning assumes possible boarding at expiry; the simulator never boards an absent rider",
  "Presence is one draw per rider, used whichever vehicle arrives; planning takes zero simulated time"], { x: 0.5, y: 1.2, w: 12.3, h: 5.6, fontSize: 15 });
source(s, "src/sim/engine.py; scenario_spec.md v0.8 §17; decision log D-46, D-48, D-54.");

s = backup("B4", "Where each input comes from", 13);
const prov = [["Input", "Status", "Value", "Basis"],
  ["Requests per hour", "DERIVED + ASSUMED", "64 / 50 / 54 for five vans (planned); pilot: 28 in one hour, two vans", "D-35, D-36, D-56"],
  ["Trip pairing", "ASSUMED + fitted", "Distance prior, rate 0.1 per min, balanced to both map totals", "D-18"],
  ["Party size", "ASSUMED (mean derived)", "Shares 1–5: .73/.18/.055/.025/.01; April 1.386 van passengers per completed van request", "D-38"],
  ["Patience", "ASSUMED placeholder", "Weibull, shape 1.5, median 18 min (scale ≈ 23.0 min)", "D-39"],
  ["No-show", "DERIVED, conditional", "8.9% per vehicle arrival if the status mapping holds (4.7% of all requests)", "D-40, D-48"],
  ["Lyft", "ASSUMED", "Ordering lag 2 min; delay lognormal, median 8 min, 90th percentile 15 min", "D-43"],
  ["Travel times", "DERIVED; × 1.2 ASSUMED", "Local OSRM routing on OpenStreetMap; van times × 1.2 in the pilot (placeholder)", "D-31, D-47"]];
s.addTable(prov.map((r, i) => r.map((c) => ({ text: c, options: { bold: i === 0, color: i === 0 ? HEX.white : HEX.ink, fill: { color: i === 0 ? HEX.ink : HEX.white } } }))),
  Object.assign({ x: 0.5, y: 1.15, w: 12.3, colW: [2.0, 2.3, 6.0, 2.0], rowH: 0.6, fontSize: 13 }, TB));
source(s, "decision log D-18–D-56; methodology v1.5 §4.");

s = backup("B5", "Three postponement prices compared", 19);
const pa = N.pending_table;
s.addTable([[hdr(""), hdr("First version"), hdr("Adopted (earliest physical pickup)"), hdr("Route-based")],
  ["Price of postponing a request", "as if served at the next 2-min re-plan", "as if served at the earliest time any on-duty van can reach it", "as if served after a chosen van's route"],
  ["Wait median / 90th pct / worst (min)", ...pa.wait], ["Mean wait (min)", ...pa.mean], ["Party of five from slide 19: wait", ...pa.r002],
  ["Extra variables", ...pa.size], ["Total MILP solve time on this evening (s)", ...pa.milp_s.map(String)],
  ["Direction of error", "optimistic", "optimistic (ignores the van's other work)", "either direction"]],
  Object.assign({ x: 0.5, y: 1.15, w: 12.3, colW: [3.0, 2.8, 3.5, 3.0], rowH: 0.52, fontSize: 13 }, TB));
txt(s, "Designed evening, vans only, one run per formulation. Adopted for its meaning and no added variables, provisionally; computing the earliest pickups is extra work per decision, not separately timed. None guarantees a feasible schedule for all waiting riders.",
  { x: 0.5, y: 5.6, w: 12.3, h: 0.9, fontSize: 13, color: HEX.muted });
source(s, "outputs/sim/d53_experiment; decision log D-53; review d53_pending_price_review (22 Oct).");

s = backup("B6", "All six rules over 30 constructed nights", 22);
s.addTable([[hdr("Per night"), ...RULES.map((x) => hdr(NAME[x]))], ...N.batch_table],
  Object.assign({ x: 0.5, y: 1.1, w: 12.3, colW: [3.0, 1.55, 1.55, 1.55, 1.55, 1.55, 1.55], rowH: 0.34, fontSize: 10.5 }, TB));
txt(s, "Cells: mean of nightly values (standard deviation across nights). Waits cover only requests picked up. 30 nights replayed six ways, not 180 independent nights.",
  { x: 0.5, y: 6.45, w: 12.3, h: 0.4, fontSize: 11.5, color: HEX.muted });
source(s, "outputs/sim/batch_L5_v1 (per_night_metrics.csv), via make_numbers.py.");

s = backup("B7", "Trade-off night by night", 24);
s.addTable([[hdr("Rule"), hdr("Reached (mean)"), hdr("Lyft orders (mean)"), hdr("Nights not dominated"), hdr("Nights identical to vans only"), hdr("Nights reach above / below vans only")],
  ...RULES.map((r, i) => [NAME[r], Bt.reached[i].toFixed(3), Bt.bookings[i].toFixed(2), `${Bt.nights_nondominated[i]} of 30`, String(Bt.nights_identical_r0[i]), `${Bt.above_below_r0[i][0]} / ${Bt.above_below_r0[i][1]}`])],
  Object.assign({ x: 0.5, y: 1.15, w: 12.3, colW: [3.6, 1.5, 1.7, 1.8, 1.8, 1.9], rowH: 0.5, fontSize: 13 }, TB));
txt(s, "Ties: a rule that makes no transfer on a night replays vans only exactly; identical results do not dominate each other, so both count as not dominated. Above / below counts are paired comparisons on the same constructed night, with no intervals yet.",
  { x: 0.5, y: 4.95, w: 12.3, h: 0.9, fontSize: 13, color: HEX.muted });
source(s, "outputs/sim/batch_L5_v1/tradeoff.md.");

s = backup("B8", "Numerical diagnostics (two-van pilot)", 21);
bullets(s, N.diagnostics, { x: 0.5, y: 1.2, w: 12.3, h: 5.5, fontSize: 15 });
source(s, "outputs/sim/batch_L5_v1 (summary.md, tie_incomplete_check.csv, reproducibility.json); decision log D-52 am. 5, D-57.");

s = backup("B9", "Corrected proposal claims", 4);
s.addTable([[hdr("Proposal said"), hdr("Corrected"), hdr("Why")],
  ["About 5,100 rides per hour at 6 pm", "≈ 170 completed rides in one evening's 6 pm hour", "The bar is a 30-day total (tooltip 5,098; digitized 5,089)"],
  ["About 28 vans in service", "27.6 vehicles on duty at 6 pm, “All services” average", "Not a Homewood-only count"],
  ["7 pm bar: 4,900", `${fmt(A.completed_by_hour[1])} (digitized 30-day total)`, "Proposal chart value differs from our digitized reading"],
  ["~1 in 4 trips overflow to Lyft", "24.5% of 44,374 riders rode Lyft", "A share of riders, not of trips or requests"],
  ["Trip-level extracts coming", "Constructed evenings from aggregate dashboards", "The extracts did not arrive"],
  ["Compare dispatch methods", "Hold one specified dispatcher fixed; vary the transfer rule", "Scope choice: isolate one controllable decision"],
  ["Lyft as paid overflow inside the optimizer", "A separate, explicit transfer rule; no money modelled", "A dispatcher sends the Lyft; cost per Lyft trip unknown (D-45)"],
  ["Targets as hard constraints (20/25 min)", "Reporting thresholds plus a ride-time guardrail", "Target wording changed over time (15/20/20 around April; 20/25/25 on the 21 Oct page) (D-49)"]],
  Object.assign({ x: 0.5, y: 1.15, w: 12.3, colW: [3.3, 4.0, 5.0], rowH: 0.52, fontSize: 12 }, TB));
txt(s, "The September proposal deck is unchanged; these corrections are recorded in methodology v1.5 §1a.", { x: 0.5, y: 6.1, w: 12.3, h: 0.4, fontSize: 13, color: HEX.muted });
source(s, "methodology v1.5 §1a; decision log D-25, D-35, D-36, D-45, D-47, D-49, D-51.");

pres.writeFile({ fileName: OUT }).then(async () => {
  if (process.env.APPLY_THEME) {
    const { applyTheme } = require(process.env.APPLY_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("wrote " + OUT + " (" + slideNo + " slides)");
});
