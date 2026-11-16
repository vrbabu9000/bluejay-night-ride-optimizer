// Midterm deck builder (draft v0.2). Every number comes from the decision log, the methodology, or the saved outputs
// listed in SOURCES.md; no simulation is run here.
//   NODE_PATH=<dir with pptxgenjs> node docs/presentations/midterm/build_deck.js
// then: node <pptx skill>/scripts/apply_theme.js (done below if APPLY_THEME is set to the script path).
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const HERE = __dirname;
const FIG = (f) => path.join(HERE, "figures", f);
const OUT = path.join(HERE, "BlueJay_Midterm_draft.pptx");
const DATA = JSON.parse(fs.readFileSync(path.join(HERE, "data", "deck_numbers.json"), "utf8"));

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
  orange: "EB6834", aqua: "1BAF7A", yellow: "EDA100", magenta: "E87BA4", violet: "6250D6", white: "FFFFFF" };
// evidence-status badges (always text + colour, never colour alone)
const BADGE = { OBSERVED: "1E2933", DERIVED: "2A78D6", ASSUMED: "EB6834", DESIGNED: "6250D6", SIMULATED: "1BAF7A", CHOSEN: "0F766E" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "Blue Jay Night Ride: midterm (draft)";
pres.author = "Team FourSight";
pres.company = "Johns Hopkins University";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: "1E2933" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 1.9, fontSize: 38, bold: true,
      color: "FFFFFF", valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 2.2, fontSize: 18,
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
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.8, w: 11.7, h: 1.2, fontSize: 34, bold: true,
      color: "1E2933" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.0, w: 11.7, h: 1.2, fontSize: 18,
      color: "3A4750" }, text: "" } },
  ],
});

// ---------- helpers ----------
function txt(slide, text, o) {
  slide.addText(text, Object.assign({ isTextBox: true, fontFace: "Calibri", fontSize: 16, color: HEX.ink, margin: 0.05,
    valign: "top" }, o));
}
function source(slide, s) {
  txt(slide, "Source: " + s, { x: 0.5, y: 6.95, w: 11.6, h: 0.35, fontSize: 10, color: HEX.faint, valign: "middle" });
}
function badge(slide, kind, x, y, w) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: w || 1.15, h: 0.3, rectRadius: 0.08,
    fill: { color: BADGE[kind] }, line: { color: BADGE[kind] }, objectName: "badge-" + kind });
  txt(slide, kind, { x, y, w: w || 1.15, h: 0.3, fontSize: 10, bold: true, color: HEX.white, align: "center",
    valign: "middle", margin: 0 });
}
function card(slide, x, y, w, h, fill) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill || HEX.tint },
    line: { color: fill || HEX.tint } });
}
function bullets(slide, items, o) {
  const runs = items.map((t, i) => {
    const opts = { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 };
    if (Array.isArray(t)) return t.map((r, j) => ({ text: r.text, options: Object.assign({}, r.options || {},
      j === 0 ? { bullet: true } : {}, j === t.length - 1 ? { breakLine: i < items.length - 1, paraSpaceAfter: 6 } : {}) }));
    return [{ text: t, options: opts }];
  }).flat();
  slide.addText(runs, Object.assign({ isTextBox: true, fontFace: "Calibri", fontSize: 16, color: HEX.ink, valign: "top",
    margin: 0.05 }, o));
}
function img(slide, f, x, y, w, ar) {
  slide.addImage({ path: FIG(f), x, y, w, h: w / ar });
}
let coreNum = 0;
function content(title, section) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  const m = title.match(/^(B\d+)\s/);           // footer numbers follow the script: core 1-12, backups B1-B8
  txt(s, m ? m[1] : String(++coreNum), { x: 12.2, y: 7.0, w: 0.7, h: 0.3, fontSize: 10, color: HEX.faint, align: "right",
    valign: "middle", margin: 0 });
  return s;
}
const AR = { f1: 1.345, f2: 2.087, f3: 3.241, f4: 2.359, f5: 1.963, f6: 1.541, f7: 0.961, f8: 3.005, map: 0.97 };

// =====================================================================================================
pres.addSection({ title: "Core" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Core" });
s.addText("What aggregate data can and cannot tell us: synthetic evenings for testing Lyft-transfer rules on Blue Jay Night Ride",
  { placeholder: "title" });
s.addText("Team FourSight · EN.553.602 Research and Design in Mathematics: Data Mining · Midterm, October 2026 · DRAFT\n"
  + "Presenters: P1 (slides 1–4) · P2 (5–8) · P3 (9–12), roles to be confirmed", { placeholder: "body" });
s.addNotes("Title. P1 opens. One sentence: we set out to optimize the Night Ride shuttle; what we learned first is what the "
  + "data can and cannot tell us, and how to build experiments that stay honest about that. Timing assumed 18.5 min + ~10 min "
  + "questions, awaiting confirmation.");

// ---------- 1. service problem and original proposal ----------
s = content("Blue Jay Night Ride, and what we proposed in September", "Core");
card(s, 0.5, 1.35, 6.1, 5.3);
txt(s, "The service", { x: 0.75, y: 1.5, w: 5.6, h: 0.4, fontSize: 20, bold: true });
const steps = [["1  Request", "a rider books a trip in the app (6 pm–2 am, Homewood area)"],
  ["2  Shared van", "a dispatcher assigns a van; other riders may share it"],
  ["3  Curb to curb", "picked up at the curb, dropped at the destination"],
  ["or  Lyft", "Hopkins can send a Lyft instead; about 1 in 4 April riders (24.5%) rode Lyft"]];
steps.forEach(([h, b], i) => {
  txt(s, h, { x: 0.75, y: 2.05 + i * 1.08, w: 1.75, h: 0.9, fontSize: 18, bold: true, color: HEX.blue });
  txt(s, b, { x: 2.5, y: 2.05 + i * 1.08, w: 3.9, h: 0.9, fontSize: 16 });
});
txt(s, "What we proposed", { x: 7.0, y: 1.5, w: 5.8, h: 0.4, fontSize: 20, bold: true });
bullets(s, [
  "Replay real service nights from trip-level records",
  "Compare dispatch methods: simple greedy rules vs an optimization model (a mixed-integer linear program, MILP) re-solved as requests arrive",
  "Treat Lyft as paid overflow chosen inside the optimizer",
  "Use the published service targets as hard constraints",
], { x: 7.0, y: 2.0, w: 5.8, h: 2.2, fontSize: 15 });
card(s, 7.0, 4.25, 5.8, 2.45, "FFF4EC");
txt(s, "Proposal numbers we later corrected", { x: 7.2, y: 4.35, w: 5.4, h: 0.35, fontSize: 15, bold: true });
bullets(s, ["\"5,100 rides per hour at 6 pm\" was a 30-day total: about 170 completed rides in one evening's 6 pm hour",
  "\"28 vans\" counted all services, not only Homewood",
  "\"1 in 4 overflow to Lyft\": a share of riders (people), not of requests or trips"],
  { x: 7.2, y: 4.75, w: 5.4, h: 1.9, fontSize: 13 });
source(s, "Proposal deck (Sep 2026); April 2026 JHU/TransLoc dashboard: 44,374 riders, van + Lyft, 24.5% by Lyft "
  + "(transloc_operations.md).");
s.addNotes("P1, 1 min. Introduce the service exactly as in the proposal: request in the app, shared van, curb to curb, about "
  + "6 pm to 2 am. Lyft: in April about one rider in four (24.5% of 44,374 riders, van and Lyft together) rode Lyft. That is "
  + "a share of riders, not of trips or requests. The proposal promised to replay real nights and compare a greedy method, a "
  + "rolling-horizon MILP and a hybrid, with Lyft as paid overflow inside the MILP and the targets as hard limits. Say plainly: "
  + "most of that changed, and the change is part of the result. Sources: proposal deck slides 5–15; transloc_operations.md "
  + "(April data row).");

// ---------- 2. how the question changed ----------
s = content("How the research question changed", "Core");
const rows = [
  ["", "September proposal", "Now"],
  ["Data", "Trip-level records were expected", "Only aggregate dashboards: totals, shares, percentiles"],
  ["Question", "Which dispatch algorithm is best?", "Which Lyft-transfer rule, with the van dispatcher held fixed?"],
  ["Lyft", "Paid overflow inside the optimizer", "A separate, explicit transfer rule; no money modelled (cost unknown)"],
  ["Targets", "Hard constraints", "Wait targets are reported, not imposed; plans may not create a ride longer than max(25 min, 2 × the direct drive + 5 min)"],
  ["Claims", "About real nights", "About synthetic evenings consistent with April's totals"],
];
s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: {
  bold: i === 0 || j === 0, color: i === 0 ? HEX.white : HEX.ink, fill: { color: i === 0 ? HEX.ink : (j === 2 ? "E8F1FB" : HEX.white) },
  fontSize: 14, valign: "middle" } }))), { x: 0.5, y: 1.35, w: 8.2, colW: [1.3, 3.0, 3.9], rowH: 0.6,
  color: HEX.ink, color: HEX.ink, border: { type: "solid", pt: 0.75, color: HEX.line }, fontFace: "Calibri" });
txt(s, "Why switch: on synthetic nights, a ranking of dispatch algorithms would mostly reflect our guesses about demand detail. "
  + "Replaying the same night with one lever changed (the transfer rule, the decision Hopkins' dispatchers actually make) "
  + "isolates that lever's effect under stated assumptions.", { x: 0.5, y: 5.15, w: 8.2, h: 1.1, fontSize: 13.5, color: HEX.muted });
card(s, 9.0, 1.35, 3.8, 1.95, "E8F1FB");
txt(s, "Research question", { x: 9.2, y: 1.42, w: 3.4, h: 0.35, fontSize: 16, bold: true, color: HEX.blue });
txt(s, "With the van dispatcher held fixed, which rule for transferring waiting riders to Lyft gives the best rider service "
  + "for the Lyft use it requires, and why?", { x: 9.2, y: 1.78, w: 3.45, h: 1.5, fontSize: 13.5 });
txt(s, "The six transfer rules we compare", { x: 9.0, y: 3.45, w: 3.8, h: 0.35, fontSize: 15, bold: true });
s.addTable([["R0", "never transfer"], ["R1(10)", "after 10 min of waiting"], ["R1(15)", "after 15 min of waiting"],
  ["R1u(10)", "after 10 min with no van assigned"], ["R2(15)", "if the predicted total wait > 15 min"],
  ["R3(2)", "if the van is predicted later than a Lyft (+2 min)"]].map((r) => [{ text: r[0], options: { bold: true } }, r[1]]),
  { x: 9.0, y: 3.85, w: 3.8, colW: [0.85, 2.95], rowH: 0.42, fontSize: 12.5, fontFace: "Calibri", color: HEX.ink,
    border: { type: "solid", pt: 0.5, color: HEX.line }, valign: "middle" });
source(s, "Proposal deck; decision log D-23–D-27, D-45, D-49; research_review.md.");
s.addNotes("P1, 1.5 min. Walk the table row by row. Data: trip records never arrived, so everything rests on monthly "
  + "aggregates. Question: comparing dispatch algorithms needs real nights to be meaningful; with synthetic nights the "
  + "defensible question is a policy question: hold one reasonable dispatcher fixed and vary the Lyft rule. Lyft: we "
  + "separated it into its own rule (the JHU page says a dispatcher sends the Lyft) and we do not model money, because "
  + "Hopkins' cost per Lyft trip is unknown (a rider's app showing no charge does not reveal it). Targets: we report against "
  + "them; the hard limit is a ride guardrail. Corrections: the proposal's 5,100 rides at 6 pm is the 30-day total for that "
  + "clock hour; 28 vans counted all services. Sources: decision log D-23 (Homewood scope), D-25 (dispatcher direction), "
  + "D-45 (no money), D-49 (targets dated); proposal slides 6–7.");

// ---------- 3. building an evening from aggregate data ----------
s = content("Building an evening from aggregate data", "Core");
const heads = ["OBSERVED", "DERIVED", "UNKNOWN", "CHOSEN"];
const hx = [0.5, 2.55, 4.6, 6.65];
heads.forEach((h, i) => { if (h === "UNKNOWN") {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: hx[i], y: 1.3, w: 1.95, h: 0.3, rectRadius: 0.08, fill: { color: "FFFFFF" },
    line: { color: HEX.ink, width: 1 } });
  txt(s, "UNKNOWN", { x: hx[i], y: 1.3, w: 1.95, h: 0.3, fontSize: 10, bold: true, align: "center", valign: "middle", margin: 0 });
} else badge(s, h, hx[i], 1.3, 1.95); });
const chain = [
  ["How many requests", "About 5,100 completed rides in the 6 pm hour over 30 days (tooltip: 5,098); 27.6 vehicles on duty (all services)",
    "÷30 → 170 per evening; ×2.087 requests per completion → 355; ÷27.6 → 12.85 requests per vehicle-hour",
    "Homewood's share of the vehicles; rebookings", "Load per van: 5 vans × 12.85 → 64 requests at 6 pm (64 / 50 / 54 over 3 h)"],
  ["Where trips go", "Pickup and drop-off totals per place, separately", "A trip table matching both totals",
    "Who travels where", "Gravity prior (longer drives less likely, 0.1 per minute) + iterative fitting to both totals"],
];
chain.forEach((r, i) => {
  const y = 1.75 + i * 1.75;
  txt(s, r[0], { x: 0.5, y, w: 8.1, h: 0.35, fontSize: 16, bold: true });
  [r[1], r[2], r[3], r[4]].forEach((c, j) => {
    card(s, hx[j], y + 0.38, 1.95, 1.22, j === 2 ? "FFFFFF" : HEX.tint);
    if (j === 2) s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: hx[j], y: y + 0.38, w: 1.95, h: 1.22, rectRadius: 0.08,
      fill: { color: "FFFFFF" }, line: { color: HEX.line, width: 1, dashType: "dash" } });
    txt(s, c, { x: hx[j] + 0.08, y: y + 0.42, w: 1.8, h: 1.15, fontSize: 12 });
  });
});
txt(s, "Uncertain: the count is an illustrative range, ~150–260, not a confidence interval; a spread-out geography variant is built but not yet used in experiments",
  { x: 0.5, y: 5.3, w: 8.1, h: 0.6, fontSize: 14, italic: true, color: HEX.muted });
img(s, "map_L5_r00.png", 8.95, 1.25, 3.9, 4.2 / 4.4);
txt(s, "Lines pair each pickup with its drop-off, not road routes. Synthetic requests from the April-calibrated demand model.", { x: 8.95, y: 5.4, w: 3.9, h: 0.7, fontSize: 11, color: HEX.muted });
source(s, "April dashboard aggregates via decision log D-35/D-36, D-18, D-49; methodology §4; figure: frozen L5 night r00.");
s.addNotes("P1, 2.5 min. This is the heart of the story: what we observed, what we derived, what stayed unknown, what we "
  + "chose. Volume worked example: the dashboard gives about 5,100 completed rides in the 6 pm clock hour summed over 30 days (its tooltip reads 5,098; our digitized value is 5,089), so "
  + "about 170 per evening. Each completed ride corresponds to 2.087 recorded requests on average (50,297 requests / 24,095 "
  + "completed), so about 355 requests in an evening's 6 pm hour, shared by 27.6 vehicles on duty: 12.85 requests per "
  + "vehicle-hour. For five vans that is 64 requests at 6 pm, 50 at 7 pm and 54 at 8 pm (168 in three hours, rounded hour by "
  + "hour). Unknown: what fraction of the 27.6 vehicles served Homewood, and how many requests were rebookings; so 168 is a "
  + "derived workload with an illustrative range of about 150–260, not an estimate of April demand. Geography: the maps give "
  + "how many pickups and how many drop-offs each place had, but never which pickup went with which drop-off. We start from a "
  + "gravity prior, an assumption that nearby trips are more common (weight falls by e^-0.1 per minute of drive), and then "
  + "rescale so both sets of totals are matched exactly (iterative proportional fitting). The data cannot tell us the decay "
  + "rate: any rate reproduces the totals. The map shows one synthetic night. Sources: decision log D-18, D-35, D-36, D-49; "
  + "methodology §4 and Appendix B.");

// ---------- 4. assumptions that complete the evening ----------
s = content("Assumptions that complete the evening", "Core");
img(s, "f4_assumed.png", 0.5, 1.3, 6.6, AR.f4);
img(s, "f3_noshow.png", 0.5, 4.3, 6.6, AR.f3);
const asm = [
  ["DERIVED", "Group size: 1.386 van passengers per completed van booking. That fixes a mean, not the distribution; ours is assumed (mean 1.405). A party of 5 needs a larger Lyft (XL)."],
  ["ASSUMED", "\"Canceled\" (≈47% of requests) mixes riders who gave up with requests handed to Lyft. Riders give up at a hidden personal deadline (placeholder: median 18 min); their share of \"Canceled\" is a provisional 50–75% sensitivity range."],
  ["DERIVED", "No-shows: 4.7% of all requests, or about 8.9% of van arrivals only if the status labels mean what we assume. We use 8.9% per arrival, provisionally."],
  ["ASSUMED", "Lyft: booked 2 min after the decision; arrives after a random delay (median 8, 90th percentile 15 min)."],
];
asm.forEach((a, i) => {
  badge(s, a[0], 7.45, 1.35 + i * 1.33, 1.15);
  txt(s, a[1], { x: 7.45, y: 1.7 + i * 1.33, w: 5.4, h: 0.98, fontSize: 13.5 });
});
source(s, "Decision log D-38, D-39, D-40, D-43, D-48; trail §6–§9; methodology §4 and Appendix C.");
s.addNotes("P1, 1.5 min. These are the inputs April cannot pin down. Group size: the dashboard gives van passengers and "
  + "completed van bookings; their ratio, 1.386, is a mean over completed van trips only. Many distributions share that mean; "
  + "ours is an assumption with mean 1.405. In it, 1% of bookings are parties of five; a team correction established that a transferred party of five rides together in a larger Lyft (XL). Canceled: almost half of April "
  + "requests ended 'Canceled', but that label includes requests the dispatcher moved to Lyft, so it is not a measure of "
  + "rider impatience. We model a hidden personal deadline per rider and keep the abandonment share as a 50–75% range. "
  + "No-shows: 4.7% of all requests; but many requests never had a van arrive, so per van arrival it is about 8.9%, and only "
  + "if 'No Show' is recorded after a real arrival and 'Completed' excludes Lyft. That conditional is important. Lyft: a 2-minute "
  + "dispatcher lag and a random arrival delay. Every orange badge is an assumption that later results depend on. Sources: "
  + "decision log D-38–D-43, D-48; trail sections 6–9.");

// ---------- 5. how the algorithm operates ----------
s = content("How our algorithm operates, every time something happens", "Core");
const loop = ["Reveal new requests; update vans and riders", "Generate feasible candidate routes per van",
  "MILP selects one route per van", "Lyft rule reads the predicted pickups", "Apply accepted transfers",
  "Re-plan once if anyone was transferred", "Execute: vans drive to their next stop"];
loop.forEach((t, i) => {
  const y = 1.35 + i * 0.73;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 5.2, h: 0.58, rectRadius: 0.08,
    fill: { color: i === 2 ? "E8F1FB" : (i >= 3 && i <= 5 ? "FFF4EC" : HEX.tint) }, line: { color: HEX.line } });
  txt(s, `${i + 1}  ${t}`, { x: 0.65, y, w: 5.0, h: 0.58, fontSize: 15, valign: "middle" });
  if (i < loop.length - 1) s.addShape(pres.shapes.LINE, { x: 3.1, y: y + 0.58, w: 0, h: 0.15, line: { color: HEX.faint, width: 1.5,
    endArrowType: "triangle" } });
});
txt(s, "repeat at every request, cancellation, no-show and every 2 minutes", { x: 0.5, y: 6.5, w: 5.2, h: 0.35,
  fontSize: 13, italic: true, color: HEX.muted });
card(s, 6.1, 1.35, 3.25, 2.6, "E8F1FB");
txt(s, "The dispatcher sees", { x: 6.3, y: 1.45, w: 2.9, h: 0.35, fontSize: 16, bold: true, color: HEX.blue });
bullets(s, ["requests that have arrived", "where each van is, who is aboard", "travel times"], { x: 6.3, y: 1.85, w: 2.95, h: 2.0, fontSize: 14 });
card(s, 9.6, 1.35, 3.25, 2.6, "FFF4EC");
txt(s, "Hidden until it happens", { x: 9.8, y: 1.45, w: 2.9, h: 0.35, fontSize: 16, bold: true, color: HEX.orange });
bullets(s, ["each rider's patience deadline", "whether the rider will be at the curb", "each Lyft's actual delay"],
  { x: 9.8, y: 1.85, w: 2.95, h: 2.0, fontSize: 14 });
txt(s, "One actual transfer on a small designed evening (rule R2(15): transfer if predicted total wait > 15 min)", { x: 6.1, y: 4.1,
  w: 6.75, h: 0.6, fontSize: 14, bold: true });
img(s, "f8_transfer.png", 6.1, 4.7, 6.3, AR.f8);
txt(s, "Rider R011: asked 18:16:30 · at 18:20 a van was predicted at 18:35:20 (total wait 18 min 50 s > 15) → transferred · booked 18:22 · Lyft at the curb 18:30 (wait 13 min 30 s) · dropped 18:33:25",
  { x: 6.1, y: 6.8, w: 6.75, h: 0.3, fontSize: 11, color: HEX.muted });
source(s, "scenario_spec.md v0.8 §17; decision log D-46, D-55; outputs/sim/m2_L4_report.md.");
s.addNotes("P2, 2 min. The loop runs at every event and every two minutes of simulated time. Steps 1–3 are the van "
  + "dispatcher: list feasible routes for each van, then a MILP picks one route per van so that every waiting request is "
  + "either in a route or left waiting. Steps 4–6 are the separate Lyft rule: it reads the dispatcher's predicted pickup "
  + "times, transfers riders that meet its condition, and the dispatcher re-plans once. Important distinction: the "
  + "predicted pickups are the dispatcher's estimates; the simulator's actual events (arrivals, boardings, cancellations) "
  + "come from travel times and the hidden rider traits on the right, which the dispatcher never sees. Worked timeline: on "
  + "the designed L4 evening under the predicted-wait rule, R011 asked at 18:16:30; at 18:20 the plan predicted a van at "
  + "18:35:20, a total wait of 18 min 50 s, above 15, so it was transferred; booked at 18:22, Lyft at the curb 18:30, dropped "
  + "at 18:33:25. Its wait is counted from the original request: 13.5 min. Sources: spec §17.3–17.5, D-55, m2_L4_report.");

// ---------- 6. how the mathematics chooses a plan ----------
s = content("How the mathematics chooses a plan", "Core");
txt(s, "Each candidate route gets penalty points (not money); the MILP picks the cheapest compatible set", { x: 0.5, y: 1.3,
  w: 12.3, h: 0.4, fontSize: 16, color: HEX.muted });
txt(s, [{ text: "route points  =  ", options: { bold: true } },
  { text: "Σ party × φ(wait)", options: { color: HEX.blue, bold: true } }, { text: "  +  0.5 × Σ party × ride minutes  +  0.1 × km", options: {} }],
  { x: 0.5, y: 1.75, w: 12.3, h: 0.45, fontSize: 20 });
txt(s, "A request in no chosen route is left waiting at a price (slide 7); a large constant makes the model first serve as many requests as it can.",
  { x: 0.5, y: 2.15, w: 12.3, h: 0.35, fontSize: 13, color: HEX.muted });
img(s, "f5_phi.png", 0.5, 2.55, 5.8, AR.f5);
txt(s, "φ: each extra minute of waiting costs more the longer the rider has already waited (1, 2.5, 5, 10, 20 points per minute after 0, 5, 10, 15, 20 minutes)",
  { x: 0.5, y: 5.55, w: 6.0, h: 0.9, fontSize: 13, color: HEX.muted });
img(s, "f6_example.png", 6.9, 2.55, 4.2, AR.f6);
txt(s, "One van; r1 (1 rider, waited 8 min) and r2 (2 riders, waited 1 min)", { x: 11.15, y: 2.6, w: 1.75, h: 1.6, fontSize: 11.5, color: HEX.muted });
txt(s, "Route A (long waiter first): 66.5 points\nRoute B: 81.0 points → A is chosen",
  { x: 6.9, y: 5.35, w: 5.9, h: 0.7, fontSize: 15, bold: true });
txt(s, "\"Optimal\" means optimal over the candidate routes generated at that moment (up to 3 new pickups per van), proven by the solver. Not optimal over all possible routes, and not over the whole evening.",
  { x: 6.9, y: 6.05, w: 5.9, h: 0.85, fontSize: 12.5, color: HEX.muted });
source(s, "model_design.md v0.5 §3–§4; methodology §6 (worked example); decision log D-29, D-52.");
s.addNotes("P2, 1.5 min. The objective in words: waiting points, riding points, driving points. Waiting uses a convex penalty "
  + "phi: the fifth minute of waiting costs 1 point, the sixteenth costs 10, the twenty-first costs 20. This is how the model "
  + "protects riders who have already waited long. Riding costs half a point per passenger-minute; driving 0.1 point per km "
  + "as a tie-breaker. A ride-time guardrail forbids plans that create a ride longer than max(25 min, 2 × direct + 5). "
  + "Worked example (two requests, one van): serving the 8-minute waiter first costs 66.5 points, serving the party of two "
  + "first costs 81.0, because the first rider's wait would cross 15 minutes where each minute costs 10 points. Points are "
  + "priorities, not dollars. Qualify 'optimal': the solver proves optimality over the routes we generated at that epoch, "
  + "with at most three new pickups per van; it is not a whole-evening optimum. Backup B1 has the full MILP and the bound "
  + "that makes it serve as many requests as possible first. Sources: model_design §3.5, §4; D-29, D-52.");

// ---------- 7. pending price ----------
s = content("A weakness we found, tested and addressed", "Core");
txt(s, "Problem: the price for leaving a request waiting (the \"pending price\") assumed a van could reach it at the next 2-minute re-plan, sooner than any van physically could. So the cheapest requests to postpone were often those that had waited longest.",
  { x: 0.5, y: 1.3, w: 12.3, h: 0.8, fontSize: 16 });
const pp = DATA.pending;
s.addTable([
  [{ text: "Same small designed evening (16 requests), whole evening", options: { bold: true, color: HEX.white, fill: { color: HEX.ink } } },
   { text: "Original price", options: { bold: true, color: HEX.white, fill: { color: HEX.ink } } },
   { text: "A: earliest physical pickup", options: { bold: true, color: HEX.white, fill: { color: HEX.ink } } },
   { text: "B: after a chosen route", options: { bold: true, color: HEX.white, fill: { color: HEX.ink } } }],
  ["Wait median / 90th pct / max (min)", pp.wait[0], pp.wait[1], pp.wait[2]],
  ["Mean wait (min)", pp.mean[0], pp.mean[1], pp.mean[2]],
  ["Total wait of the party of five that had already waited 15 min by 18:15", pp.r002[0], pp.r002[1], pp.r002[2]],
  ["Extra MILP variables / total solve time", pp.size[0], pp.size[1], pp.size[2]],
], { x: 0.5, y: 2.25, w: 8.6, colW: [3.2, 1.7, 1.9, 1.8], rowH: 0.55, fontSize: 14, fontFace: "Calibri",
  color: HEX.ink, border: { type: "solid", pt: 0.75, color: HEX.line }, valign: "middle" });
card(s, 9.4, 2.25, 3.4, 3.4, "E8F1FB");
txt(s, "Decision: A (approved, provisional)", { x: 9.6, y: 2.35, w: 3.0, h: 0.7, fontSize: 16, bold: true, color: HEX.blue });
bullets(s, ["a direct physical pickup estimate", "no new variables", "keeps \"serve as many as possible first\""],
  { x: 9.6, y: 3.05, w: 3.05, h: 1.6, fontSize: 14 });
txt(s, "Reason: clear meaning at no added cost, not that one rider was served sooner.", { x: 9.6, y: 4.65, w: 3.0, h: 0.9, fontSize: 13, italic: true,
  color: HEX.muted });
txt(s, "Still an approximation: A ignores work the nearest van is already doing, so postponing can still look too cheap. The experiment checked behaviour over a whole evening: A cut the longest waits but redistributed waiting (the median rose and the most recent request waited longer); it did not improve every outcome.",
  { x: 0.5, y: 5.2, w: 8.6, h: 1.0, fontSize: 14, color: HEX.muted });
source(s, "Decision log D-53 (update 2, approval); outputs/sim/d53_experiment/d53_comparison.md; review note d53_pending_price_review.");
s.addNotes("P2, 1.5 min. When a request cannot be served this epoch it gets a 'pending price'. The original price assumed "
  + "pickup at the next 2-minute tick, which is physically impossible when vans are far away, so postponing looked cheap, "
  + "and most of all for riders who would be picked up late, often the longest waiters. At 18:15 on the designed evening a "
  + "party of five that had waited 15 minutes was left waiting. We ran a controlled experiment: three formulations, each run "
  + "through the whole evening on identical inputs. A prices waiting at the earliest physical pickup by any van; B prices it "
  + "after a chosen van's route. A added nothing to the model; B added up to about 9,800 variables here and about 135,000 in a "
  + "synthetic five-van epoch, and its estimate can be wrong in both directions. We approved A provisionally for its meaning "
  + "and cost, not because R002 was served sooner. A is still optimistic, and the change shifted waiting toward younger "
  + "riders. Sources: D-53 update 2 and approval; d53_comparison.md.");

// ---------- 8. verification ----------
s = content("How we know the code does what we specify", "Core");
const tiles = [["to the second", "hand-computed answer keys reproduced on three designed evenings (L1–L3)"],
  ["22 + 4", "Lyft transfers and declined offers (there, riders accept with probability 0.9) matched on a fourth designed evening, summed over the five rules that transfer"],
  ["292,181", "plan combinations enumerated by an independent brute-force program (the designed evening under the original and the approved pending price); the MILP's choice matched at every epoch"],
  ["253", "automated tests (207 on the simulator); 168 written by independent reviewers who did not reuse the simulator's logic"]];
tiles.forEach(([n, l], i) => {
  const x = 0.5 + (i % 2) * 6.2, y = 1.4 + Math.floor(i / 2) * 2.4;
  card(s, x, y, 6.0, 2.15);
  txt(s, n, { x: x + 0.25, y: y + 0.15, w: 5.5, h: 0.9, fontSize: 40, bold: true, color: HEX.blue });
  txt(s, l, { x: x + 0.25, y: y + 1.05, w: 5.5, h: 1.0, fontSize: 15 });
});
txt(s, "Plus on every run: one outcome per request, counts reconcile, seats and pickup-before-drop-off hold, inputs unchanged, sampled reruns identical. This checks the code against our rules, not our rules against the real service.",
  { x: 0.5, y: 6.25, w: 12.3, h: 0.6, fontSize: 14, color: HEX.muted });
source(s, "Phase 4 log; decision log D-52, D-55, D-57; tests/ (test_sim_*, test_m2_independent, test_pending_price_independent).");
s.addNotes("P2, 1 min. Before trusting any result we checked the machinery. Three small designed evenings have answer keys "
  + "computed by hand; the simulator reproduces every pickup, drop-off, no-show and cancellation time to the second. On the "
  + "fourth designed evening, the Lyft bookkeeping before the vans come on duty matched: 22 transfers and 4 declined offers, "
  + "summed over five separate rule runs (not one night). For the MILP, an independent brute-force program enumerated every "
  + "compatible combination of candidate routes (151,710 under the original pending price and 140,471 under the approved one, on the designed evening) and agreed with the solver every time. 253 "
  + "automated tests, two thirds of them written by independent reviewers. A simulation that is only plausible is not enough; these "
  + "checks let us say the numbers on the next slides are what the model does. Sources: Phase 4 log; tests directory.");

// ---------- 9. thirty-night pilot findings ----------
s = content("Thirty synthetic nights: what the rules actually did", "Core");
txt(s, "Pilot: 30 synthetic one-hour nights, each replayed under all six rules (same riders, same hidden traits). Two vans for 28 requests: a heavy load by design (14 per van-hour, a 10-minute burst). Provisional settings; the five-van evening is not yet run.",
  { x: 0.5, y: 1.25, w: 12.3, h: 0.65, fontSize: 14, color: HEX.muted });
const F = DATA.fates;
s.addChart(pres.charts.BAR, [
  { name: "Lyft completed", labels: F.rules, values: F.completed },
  { name: "Lyft no-show", labels: F.rules, values: F.noshow },
  { name: "Cancelled before booking (in the 2-min lag)", labels: F.rules, values: F.lag },
  { name: "Cancelled after booking", labels: F.rules, values: F.after },
], { x: 0.5, y: 1.95, w: 6.9, h: 4.85, barDir: "bar", barGrouping: "percentStacked", chartColors: ["1BAF7A", "EDA100", "E87BA4", "EB6834"],
  showTitle: true, title: "Outcome of each transferred request, share by rule (n = transfers over 30 nights)", titleFontSize: 14, titleFontFace: "+mn-lt",
  titleColor: HEX.ink, showLegend: true, legendPos: "b", legendFontSize: 11, legendFontFace: "+mn-lt",
  showValue: true, dataLabelPosition: "ctr", dataLabelFontSize: 10, dataLabelColor: HEX.ink, dataLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: HEX.muted, valAxisLabelColor: HEX.muted,
  valAxisLabelFontSize: 10, valAxisLabelFontFace: "+mn-lt", valGridLine: { color: "E3E6E9", size: 0.5 }, catGridLine: { style: "none" },
  catAxisOrientation: "maxMin", valAxisLabelFormatCode: "0%" });
const mech = [
  ["A transfer is not a rescue", "Patience keeps running: 95 of 196 requests transferred under R1(10) cancelled before their Lyft arrived (77 after booking); about a third under R2(15) and R3(2)."],
  ["Assigned is not picked up", "\"Transfer after 10 min with no van assigned\" (R1u(10)) fired only when a request stayed unassigned that long: 8 transfers on 6 of 30 nights, all for requests made during the burst."],
  ["Rides over the limit", "Plans never exceed the ride limit, but rides did 36 times across the 180 runs (16 distinct requests on 10 nights); each coincided with a no-show wait on that van while the rider was aboard: consistent with, not proof of, that cause."],
  ["Mind the denominator", "Wait percentiles cover only riders picked up (16 of 28 under never-transfer); \"reached within 15 min\" counts every request."],
];
mech.forEach(([h, b], i) => {
  txt(s, h, { x: 7.75, y: 1.95 + i * 1.22, w: 5.1, h: 0.35, fontSize: 15, bold: true });
  txt(s, b, { x: 7.75, y: 2.28 + i * 1.22, w: 5.1, h: 0.88, fontSize: 11.5 });
});
source(s, "outputs/sim/batch_L5_v1 (summary.md, per-run outcomes); decision log D-56, D-57. Counts are totals over 30 nights.");
s.addNotes("P3, 2 min. Define L5 carefully: 30 synthetic nights, not real nights and not 180 independent nights; each night is "
  + "replayed under all six rules with the same riders and the same hidden traits, so differences come from the rule. Two vans, "
  + "28 requests in an hour with a burst; this is a two-van pilot, not the proposed five-van evening. Settings are provisional: "
  + "placeholder patience, 8.9% presence. Mechanism 1: a transfer does not stop the patience clock; with a 2-minute lag and an "
  + "8-minute typical Lyft delay, many late transfers end in cancellation after the booking was placed. Under 'transfer after 10 "
  + "minutes waited', 95 of 196 transferred requests (almost half) cancelled before the Lyft arrived, 77 of them after the booking was placed. Mechanism 2: the unassigned-time rule measures assignment, not "
  + "waiting; on the designed L4 evening it never fired after vans came on duty, while in L5 it fired 8 times on 6 nights, all "
  + "for requests made during the burst, when two vans could not absorb the queue. Mechanism 3: the 36 guardrail excesses (16 distinct requests on 10 nights, repeated across rules that made the same decisions) each coincide with a no-show "
  + "wait on the same van; this is an attribution consistent with timing, not a proof of cause. Mechanism 4: wait percentiles "
  + "only describe riders who were picked up, so a rule that loses riders to cancellation can look better than it is. "
  + "Sources: batch summary.md; D-56, D-57.");

// ---------- 10. trade-off ----------
s = content("Service versus Lyft use: a trade-off among tested rules", "Core");
txt(s, "Service = share of all requests a vehicle reached at the curb within 15 min. Rule P dominates Q if P has at least Q's service with no more Lyft bookings, and is strictly better in one.",
  { x: 0.5, y: 1.2, w: 12.3, h: 0.6, fontSize: 14 });
const T = DATA.tradeoff;
s.addChart(pres.charts.SCATTER, [
  { name: "Lyft bookings per night", values: T.bookings },
  { name: "Six tested rules (means of 30 nights)", values: T.reached, labels: T.chart_labels },
], { x: 0.5, y: 1.75, w: 7.6, h: 5.1, chartColors: ["1E2933"], lineSize: 0, lineDataSymbol: "circle", lineDataSymbolSize: 9,
  showTitle: false, showLegend: false, dataLabelFormatScatter: "custom", showLabel: true, dataLabelPosition: "r",
  dataLabelFontSize: 11, dataLabelFontFace: "+mn-lt", dataLabelColor: HEX.ink,
  showValAxisTitle: true, valAxisTitle: "share of all requests reached within 15 min", valAxisTitleFontSize: 12,
  valAxisTitleColor: HEX.muted, valAxisTitleFontFace: "+mn-lt", showCatAxisTitle: true, catAxisTitle: "Lyft bookings per night (mean)",
  catAxisTitleFontSize: 12, catAxisTitleColor: HEX.muted, catAxisTitleFontFace: "+mn-lt", valAxisMinVal: 0.4, valAxisMaxVal: 0.8,
  valAxisLabelFormatCode: "0.00", catAxisLabelFormatCode: "0", catAxisMinVal: 0, catAxisMaxVal: 12, valAxisLabelColor: HEX.muted, catAxisLabelColor: HEX.muted,
  valAxisLabelFontSize: 11, catAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", catAxisLabelFontFace: "+mn-lt",
  valGridLine: { color: "E3E6E9", size: 0.5 }, catGridLine: { style: "none" } });
card(s, 8.4, 1.85, 4.4, 3.35, "E8F1FB");
txt(s, "Nondominated among the six tested", { x: 8.6, y: 1.92, w: 4.0, h: 0.35, fontSize: 14, bold: true, color: HEX.blue });
txt(s, T.nondominated_text, { x: 8.6, y: 2.27, w: 4.05, h: 2.9, fontSize: 11.5 });
bullets(s, ["Not a frontier of all possible policies", "Not a recommendation: picking a point needs a value judgement",
  "Weights inside the routing objective are a different trade-off", "Decision criteria (margins, intervals) are not yet agreed"],
  { x: 8.4, y: 5.3, w: 4.4, h: 1.6, fontSize: 12 });
source(s, "outputs/sim/batch_L5_v1/tradeoff.md (src/sim/tradeoff.py; descriptive, saved outputs only).");
s.addNotes("P3, 1.5 min. Two objectives stated explicitly: service, the share of all requests a vehicle reaches within 15 "
  + "minutes (curb arrival, larger is better), and Lyft use, bookings per night (smaller is better). Introduce dominance with "
  + "the sentence on the slide. Each point is a rule's average over the 30 paired nights. Never-transfer uses no Lyft and "
  + "reaches about 48%; the elapsed-time rules buy little extra reach per booking; the two rules that read predicted pickups "
  + "reach about three quarters of requests with about 9–10 bookings. The unassigned-time rule is dominated on these means, very narrowly. Per night "
  + "the picture varies: see backup B6. Four cautions on the slide: only six policies were tested; nondominated is not "
  + "'best'; this trade-off between transfer rules is different from the fixed exchange rate inside the routing objective; and "
  + "the statistical decision criteria (margins, intervals) are a proposal not yet approved. Sources: tradeoff.md, computed from "
  + "the saved batch with src/sim/tradeoff.py.");

// ---------- 11. leader-follower ----------
s = content("A leader–follower reading: possible, but not what we solved", "Core");
card(s, 0.5, 1.35, 3.6, 1.6, "E8F1FB");
txt(s, "Leader: policy designer", { x: 0.7, y: 1.45, w: 3.2, h: 0.4, fontSize: 16, bold: true, color: HEX.blue });
txt(s, "chooses the transfer rule and its threshold θ", { x: 0.7, y: 1.9, w: 3.2, h: 0.9, fontSize: 14 });
card(s, 0.5, 3.4, 3.6, 1.6, "FFF4EC");
txt(s, "Follower: routing optimizer", { x: 0.7, y: 3.5, w: 3.2, h: 0.4, fontSize: 16, bold: true, color: HEX.orange });
txt(s, "re-plans the vans around the riders left after transfers", { x: 0.7, y: 3.95, w: 3.2, h: 0.9, fontSize: 14 });
s.addShape(pres.shapes.LINE, { x: 2.3, y: 2.95, w: 0, h: 0.45, line: { color: HEX.faint, width: 1.5, endArrowType: "triangle" } });
txt(s, "Formal version (an extension):", { x: 4.5, y: 1.35, w: 8.3, h: 0.4, fontSize: 16, bold: true });
txt(s, "choose θ to minimise  E[ service loss(θ, y) + λ × Lyft bookings(θ) ]\nsubject to  y ∈ argmin over feasible routes of routing cost(y; riders not transferred under θ)",
  { x: 4.5, y: 1.8, w: 8.3, h: 1.1, fontSize: 16, fontFace: "Cambria", color: HEX.ink });
txt(s, "What we implemented", { x: 4.5, y: 3.05, w: 4.0, h: 0.4, fontSize: 15, bold: true });
bullets(s, ["a sequential policy simulation: plan → rule reads plan → transfers → re-plan once", "six fixed rules compared by replaying nights"],
  { x: 4.5, y: 3.45, w: 4.0, h: 1.8, fontSize: 13.5 });
txt(s, "Missing for a solved bilevel model", { x: 8.8, y: 3.05, w: 4.0, h: 0.4, fontSize: 15, bold: true });
bullets(s, ["an upper-level optimisation over θ", "the follower's response stated as constraints over the whole evening (ours is per epoch, restricted)",
  "a treatment of the expectation over nights"], { x: 8.8, y: 3.45, w: 4.0, h: 2.2, fontSize: 13.5 });
txt(s, "Riders follow assumed patience rules and Lyft is a delay distribution: they are not modelled as optimizing players.",
  { x: 0.5, y: 5.75, w: 12.3, h: 0.6, fontSize: 13.5, color: HEX.muted });
source(s, "Bilevel and leader–follower terminology: Colson, Marcotte & Savard (2007); Dempe (2002); von Stackelberg (1934). Implementation: spec §17.4, D-55.");
s.addNotes("P3, 1 min. Leader–follower (Stackelberg) models have a leader who decides first anticipating how a follower will "
  + "respond optimally. A natural reading of our problem: the leader is a policy designer choosing the transfer rule and its "
  + "threshold; the follower is the routing optimizer that re-plans the vans for the riders who remain. Written formally, that "
  + "is a bilevel program: the upper level chooses theta to minimise expected service loss plus lambda times Lyft use, subject "
  + "to the routes being optimal for the lower-level routing problem. We have not solved that. What we run is a sequential "
  + "policy simulation: the dispatcher plans, the rule reads the plan, accepted transfers leave, the dispatcher re-plans once; "
  + "and we compare six fixed rules by replaying nights. Missing: an optimisation over theta, the follower's optimality "
  + "imposed as constraints over the evening (our dispatcher optimizes one epoch at a time over a restricted candidate set), "
  + "and the expectation over nights. Any reduction of such a model to a single level would need specific assumptions and "
  + "justification; we make no such claim. This is a possible extension, not something impossible and not something done. "
  + "References: Colson, Marcotte & Savard (2007), Annals of Operations Research 153; Dempe (2002), Foundations of Bilevel "
  + "Programming; von Stackelberg (1934).");

// ---------- 12. limitations and next ----------
s = content("Limitations, next experiments and what we contribute", "Core");
txt(s, "Limitations", { x: 0.5, y: 1.3, w: 4.0, h: 0.4, fontSize: 18, bold: true });
bullets(s, ["Aggregate data only; no comparison with real nights yet", "Patience is a placeholder; no-show probability provisional",
  "Results so far: two-van pilot; five-van evening not yet run", "Up to 3 new pickups planned per van; some runs take minutes",
  "One night pattern; designed evenings are small"], { x: 0.5, y: 1.75, w: 4.0, h: 4.8, fontSize: 14 });
txt(s, "Next", { x: 4.75, y: 1.3, w: 4.0, h: 0.4, fontSize: 18, bold: true });
bullets(s, ["Agree the decision criteria, then compute paired intervals on the saved 30 nights (to size the main experiment, not to conclude)", "Sweep rule thresholds to trace trade-off curves",
  "Build the five-van evening and check the MILP is fast enough there", "Test sensitivity to patience and Lyft delay"], { x: 4.75, y: 1.75, w: 4.0, h: 4.8, fontSize: 14 });
card(s, 9.0, 1.3, 3.8, 3.2, "E8F1FB");
txt(s, "Intended contribution", { x: 9.2, y: 1.4, w: 3.4, h: 0.4, fontSize: 18, bold: true, color: HEX.blue });
txt(s, "A transparent, code-verified way to turn aggregate dashboards into paired synthetic experiments that say clearly what is observed, what is assumed and what the simulation produced. Not yet validated against real service nights.",
  { x: 9.2, y: 1.9, w: 3.4, h: 2.5, fontSize: 15 });
source(s, "Phase 4 plan and log; decision log D-50, D-56, D-57; methodology §7–§9.");
s.addNotes("P3, 1.5 min. Be direct about limits: aggregate data only; patience is a placeholder and the 8.9% no-show "
  + "probability depends on how statuses were recorded; all results so far are from the two-van pilot; the five-van evening "
  + "is designed but not run. Next steps in order: agree the decision criteria and compute paired intervals on the saved 30 "
  + "nights; sweep thresholds to turn six points into curves; build and benchmark the five-van evening; test sensitivity. "
  + "Contribution: not a claim that one rule wins, but a method that keeps observed, assumed and simulated facts separate and "
  + "is verified to the second. Invite questions.");

// =====================================================================================================
pres.addSection({ title: "Backup" });
s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Backup" });
s.addText("Backup slides", { placeholder: "title" });
s.addText("B1 MILP and bound · B2 event order and lifecycle · B3 code key · B4 parameter provenance · B5 all-rule batch table · "
  + "B6 per-night trade-off · B7 pending-price formulas · B8 numerical diagnostics", { placeholder: "body" });

s = content("B1  The route-selection MILP at one epoch", "Backup");
txt(s, [
  { text: "min  Σ_v Σ_k c_vk y_vk  +  Σ_r π_r u_r", options: { breakLine: true } },
  { text: "s.t.  Σ_k y_vk = 1  for every van v        (one route per van)", options: { breakLine: true } },
  { text: "        Σ_{v,k: r ∈ S_k} y_vk + u_r = 1  for every open request r   (served once, or pending)", options: { breakLine: true } },
  { text: "        y, u ∈ {0, 1}", options: {} }], { x: 0.5, y: 1.35, w: 12.3, h: 1.7, fontSize: 18, fontFace: "Cambria" });
bullets(s, [
  "c_vk: route points (waiting φ, riding 0.5/passenger-min, 0.1/km; Ψ only for unavoidable guardrail excesses); exact integers",
  "Candidates: every subset of ≤ 3 open requests per van, best order of all its stops (exact search); the van's committed-work route is always a candidate",
  "π_r = b_r + M with b_r from pending price A; M = 1 + Σ_v (max_k c_vk − min_k c_vk) + Σ_r b_r guarantees that every proven-optimal solution leaves the fewest requests pending (per request, not per passenger)",
  "HiGHS: relative gap 0, absolute gap 0.5 units, node limit 100,000; ties broken canonically; a failed solve is logged, never replaced by a heuristic",
], { x: 0.5, y: 3.2, w: 12.3, h: 3.6, fontSize: 14 });
source(s, "model_design.md v0.5 §3; decision log D-47, D-52 (amendments), D-53 approval.");
s.addNotes("Backup for questions on the formulation, the M bound and solver handling.");

s = content("B2  Event order and a request's life", "Backup");
img(s, "f7_lifecycle.png", 0.5, 1.3, 5.4, AR.f7);
bullets(s, ["Same-second order: drop-offs → curb arrivals (stop the patience clock) → service ends → vans on/off duty → new requests → patience checks → Lyft bookings → planning epoch → departures",
  "A van commits to a stop when it departs toward it",
  "During an absent rider's 3-min curb wait, planning assumes possible boarding at expiry; the simulator never boards an absent rider (D-54)",
  "Planning takes zero simulated time; wall-clock time is logged only"], { x: 6.2, y: 1.4, w: 6.6, h: 5.3, fontSize: 14 });
source(s, "scenario_spec.md v0.8 §17; decision log D-46, D-54.");
s.addNotes("Backup: event order and lifecycle.");

s = content("B3  Code key", "Backup");
s.addTable([
  [{ text: "Code", options: { bold: true, color: HEX.white, fill: { color: HEX.ink } } }, { text: "Plain meaning", options: { bold: true, color: HEX.white, fill: { color: HEX.ink } } }],
  ["R0", "Never transfer to Lyft (reference)"], ["R1(10), R1(15)", "Transfer after 10 or 15 minutes of waiting"],
  ["R1u(10)", "Transfer after 10 minutes with no van assigned in the plan"], ["R2(15)", "Transfer if the predicted total wait exceeds 15 minutes"],
  ["R3(2)", "Transfer if the van is predicted later than a Lyft could arrive, plus 2 minutes"],
  ["L1–L4", "Small designed evenings with hand-computed answer keys (L4: Lyft bookkeeping, vans from 18:15)"],
  ["L5", "Pilot: 30 synthetic one-hour nights, 2 vans, 28 requests each"],
  ["C", "Our van dispatcher: a restricted route-selection MILP solved with HiGHS"],
  ["A", "Pending price: a waiting request is charged its earliest physically possible pickup"],
  ["D-xx", "Numbered entry in the decision log"], ["MILP", "Mixed-integer linear program"],
  ["XL", "Larger Lyft vehicle, used for a party of 5"]],
  { x: 0.5, y: 1.3, w: 12.3, colW: [2.3, 10.0], rowH: 0.4, fontSize: 14, fontFace: "Calibri", color: HEX.ink, border: { type: "solid", pt: 0.75, color: HEX.line } });
source(s, "lyft.py; scenario_spec.md §6, §8; decision log.");
s.addNotes("Backup: code key.");

s = content("B4  Where each input comes from", "Backup");
const prov = [["Input", "Status", "Value", "Basis"],
  ["Requests per hour", "DERIVED", "64 / 50 / 54 for five vans (pilot: 28 in one hour, two vans)", "D-35, D-36; L5 design"],
  ["Trip pairing", "ASSUMED + fitted", "Gravity prior, decay 0.1/min, fitted to both April margins", "D-18"],
  ["Group size", "ASSUMED (mean derived)", "P(1..5) = .73/.18/.055/.025/.01; April 1.386 van passengers per completed van booking", "D-38"],
  ["Patience", "ASSUMED placeholder", "Weibull, shape 1.5, median 18 min", "D-39"],
  ["No-show", "DERIVED, conditional", "8.9% per arrival if status mapping holds (4.7% of all requests)", "D-48"],
  ["Lyft", "ASSUMED", "Lag 2 min; delay lognormal, median 8, 90th pct 15 min", "D-43"],
  ["Travel times", "OBSERVED (routing)", "Local OSRM road network; van × 1.2 in the pilot", "D-31, D-47"]];
s.addTable(prov.map((r, i) => r.map((c) => ({ text: c, options: { bold: i === 0, color: i === 0 ? HEX.white : HEX.ink,
  fill: { color: i === 0 ? HEX.ink : HEX.white } } }))), { x: 0.5, y: 1.3, w: 12.3, colW: [2.0, 2.2, 6.0, 2.1], rowH: 0.55,
  fontSize: 13, fontFace: "Calibri", color: HEX.ink, border: { type: "solid", pt: 0.75, color: HEX.line } });
source(s, "decision log D-18–D-48; methodology §4.");
s.addNotes("Backup: parameter provenance.");

s = content("B5  All six rules over 30 synthetic nights", "Backup");
s.addTable(DATA.batch_table, { x: 0.5, y: 1.25, w: 12.3, colW: [3.3, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5], rowH: 0.36, fontSize: 11,
  fontFace: "Calibri", color: HEX.ink, border: { type: "solid", pt: 0.75, color: HEX.line } });
txt(s, "Cells: mean of nightly values (standard deviation across nights). Waits cover only requests picked up.", { x: 0.5,
  y: 6.55, w: 12.3, h: 0.35, fontSize: 12, color: HEX.muted });
source(s, "outputs/sim/batch_L5_v1/summary.md.");
s.addNotes("Backup: the full batch table.");

s = content("B6  Trade-off night by night", "Backup");
s.addTable(DATA.pernight_table, { x: 0.5, y: 1.3, w: 12.3, colW: [3.4, 1.8, 1.8, 2.0, 1.6, 1.7], rowH: 0.5, fontSize: 13,
  fontFace: "Calibri", color: HEX.ink, border: { type: "solid", pt: 0.75, color: HEX.line } });
txt(s, "A rule that makes no transfer on a night replays never-transfer exactly and ties it. Nights with reach above / below never-transfer are paired comparisons of the same synthetic night.",
  { x: 0.5, y: 5.2, w: 12.3, h: 0.8, fontSize: 13, color: HEX.muted });
source(s, "outputs/sim/batch_L5_v1/tradeoff.md.");
s.addNotes("Backup: per-night nondominance and paired comparisons with never-transfer.");

s = content("B7  The three pending prices", "Backup");
bullets(s, ["Original: b_r = q_r · φ(next tick − t_r)",
  "A (approved, provisional): b_r = q_r · φ(max(next tick, L_r) − t_r), L_r = earliest any on-duty van can reach the pickup",
  "B (experimental): price after a chosen van's route, linearised with continuous variables z_rj ≤ y_j, Σ_j z_rj = u_r",
  "A is a lower bound on any future service (up to a 13-s matrix exception, vans not yet on duty, the next-tick floor); B can err in both directions and adds |requests| × |routes| variables",
  "Neither is a guaranteed feasible joint schedule for all waiting riders"], { x: 0.5, y: 1.35, w: 12.3, h: 5.3, fontSize: 15 });
source(s, "model_design.md v0.5 §3.5; decision log D-53; research_notes/d53_pending_price_review_2026-10-22.md.");
s.addNotes("Backup: pending-price formulas.");

s = content("B8  Numerical diagnostics (L5 pilot)", "Backup");
bullets(s, DATA.diagnostics, { x: 0.5, y: 1.35, w: 12.3, h: 5.3, fontSize: 15 });
source(s, "outputs/sim/batch_L5_v1 (summary.md, tie_incomplete_check.csv, reproducibility.json); decision log D-52 am. 5, D-57.");
s.addNotes("Backup: solver statuses, tie searches, runtime, guardrail attribution, reproducibility.");

pres.writeFile({ fileName: OUT }).then(async () => {
  if (process.env.APPLY_THEME) {
    const { applyTheme } = require(process.env.APPLY_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("wrote " + OUT);
});
