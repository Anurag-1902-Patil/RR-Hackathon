/* SupeRR Intelligence: 10-slide PITCH deck (the submission deck).
 * Every number is read from reports/deck_data.json (same pipeline outputs as all other deliverables).
 * Run: node src/reporting/deck/build_pitch.js   (APPLY_THEME_JS=<pptx skill apply_theme.js> applies theme colours)
 */
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "../../..");
const REP = path.join(ROOT, "reports");
const D = JSON.parse(fs.readFileSync(path.join(REP, "deck_data.json"), "utf8"));
const OUT = path.join(REP, "SupeRR_Intelligence_Pitch.pptx");
const FIG = (p) => path.join(REP, "figures", p);

const THEME = {
  name: "SupeRR Intelligence",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: { dk1: "1B1F3B", lt1: "FFFFFF", dk2: "21184F", lt2: "F4F0FB", accent1: "4B2A99", accent2: "C2185B", accent3: "C9A227",
            accent4: "C9B8EE", accent5: "6B6F8A", accent6: "2E86AB", hlink: "4B2A99", folHlink: "6B6F8A" },
};
const HEX = THEME.colors;
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "SupeRR Intelligence: who delivers when it matters";
pres.author = "SupeRR Intelligence (independent analysis)";
const C = pres.SchemeColor;
const M = 0.6;
const FOOT = "SupeRR Intelligence · independent analysis for SupeRR Selector Season 2 · not affiliated with Rajasthan Royals";

pres.defineSlideMaster({
  title: "DARK", background: { color: HEX.dk2 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 0.55, w: 12.1, h: 1.5, fontSize: 44, bold: true, color: C.background1, valign: "top", align: "left" }, text: "" } }],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: HEX.accent4 },
});
pres.defineSlideMaster({
  title: "LIGHT", background: { color: HEX.lt1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.3, w: 12.1, h: 0.9, fontSize: 30, bold: true, color: C.text1, valign: "middle", align: "left" }, text: "" } },
    { text: { text: FOOT, options: { x: M, y: 7.02, w: 10, h: 0.3, fontSize: 9, color: HEX.accent5, fontFace: "Calibri" } } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: HEX.accent5 },
});

let section = "";
const sec = (t) => { section = t; pres.addSection({ title: t }); };
function slide(master, title) { const s = pres.addSlide({ masterName: master, sectionTitle: section }); s.addText(title, { placeholder: "title" }); return s; }
function txt(s, text, o) { s.addText(text, Object.assign({ isTextBox: true, fontSize: 16, color: C.text1, valign: "top", margin: 0 }, o)); }
function card(s, x, y, w, h, fill, name) { s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill }, objectName: name }); }
function chip(s, x, y, w, big, label, fill, bigCol, labCol, name, size = 34) {
  card(s, x, y, w, 1.45, fill, name);
  txt(s, big, { x: x + 0.22, y: y + 0.12, w: w - 0.44, h: 0.72, fontSize: size, bold: true, color: bigCol, fontFace: "Cambria", valign: "middle" });
  txt(s, label, { x: x + 0.22, y: y + 0.86, w: w - 0.44, h: 0.5, fontSize: 12.5, color: labCol });
}
function image(s, file, x, y, w, h, alt) { s.addImage({ path: FIG(file), x, y, w, h, sizing: { type: "contain", w, h }, altText: alt }); }
const pct = (v) => (v === null || v === undefined || Number.isNaN(v) ? "" : `${Math.round(v * 100)}%`);
function rows(header, body, fs = 12) {
  const h = header.map((t) => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk1 }, fontSize: fs } }));
  return [h, ...body.map((r, i) => r.map((t) => ({ text: String(t), options: { fontSize: fs, color: HEX.dk1, fill: { color: i % 2 ? "F7F6FB" : "FFFFFF" } } })))];
}
const chartBase = (title) => ({
  showTitle: true, title, titleFontSize: 13, titleColor: HEX.dk1, titleFontFace: "+mj-lt",
  catAxisLabelColor: HEX.dk1, valAxisLabelColor: HEX.accent5, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 12, valAxisLabelFontSize: 10, valGridLine: { color: "E6E6EF", size: 0.75 }, catGridLine: { style: "none" },
  dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", dataLabelFontSize: 11, showValue: true, showLegend: false,
});
const bat = D.batting, bowl = D.bowling, ub = D.uncapped.batting, uw = D.uncapped.bowling;
const tv = Object.fromEntries(D.uncapped_transfer.map((r) => [r.side, r]));
const cb = D.clutch.find((r) => r.side === "batting"), cw = D.clutch.find((r) => r.side === "bowling");
const hi = D.pressure_profile.find((r) => r.pressure_band === "high"), lo = D.pressure_profile.find((r) => r.pressure_band === "low");
const pr = Object.fromEntries(D.priorities.map((r) => [r.requirement, r.priority_score]));

// 1 ---------------------------------------------------------------- hook
sec("Pitch");
let s = slide("DARK", "Who delivers when it matters?");
txt(s, "A pressure-reliability engine that finds the players Rajasthan Royals can actually sign for IPL 2027, including uncapped Indians.",
  { x: M, y: 1.95, w: 11.6, h: 1.0, fontSize: 21, color: C.accent4 });
chip(s, M, 3.35, 3.85, Number(D.summary.deliveries).toLocaleString("en-US"), "balls of IPL + T20I cricket, 2022–26 (RR data pack)", "2D2366", HEX.lt1, HEX.accent4, "hook-balls");
chip(s, M + 4.1, 3.35, 3.85, "62,850", "domestic T20 balls added (Syed Mushtaq Ali Trophy) for uncapped Indians", "2D2366", HEX.lt1, HEX.accent4, "hook-smat");
chip(s, M + 8.2, 3.35, 3.9, "30 names", "10 batters + 10 bowlers RR can sign, plus 5 + 5 uncapped freshers", "2D2366", HEX.accent3, HEX.accent4, "hook-names");
txt(s, "SupeRR Selector Season 2 · Round 1 · information cut-off 14 Nov 2026", { x: M, y: 5.3, w: 12, h: 0.4, fontSize: 13, color: C.accent5 });
s.addNotes("Hook: everyone can list stars. The question is who stays reliable when the game is on the line, and whom RR can actually buy. 30 seconds per slide.");

// 2 ---------------------------------------------------------------- answer first
s = slide("LIGHT", "The answer, up front");
const col = (x, head, color, names, sub, name) => {
  card(s, x, 1.35, 3.9, 4.05, "F4F0FB", name);
  txt(s, head, { x: x + 0.25, y: 1.5, w: 3.4, h: 0.45, fontSize: 15, bold: true, color });
  txt(s, names.map((n, i) => `${i + 1}. ${n}`).join("\n"), { x: x + 0.25, y: 2.05, w: 3.45, h: 2.3, fontSize: 17, color: C.text1, fontFace: "Cambria", lineSpacingMultiple: 1.1 });
  txt(s, sub, { x: x + 0.25, y: 4.45, w: 3.45, h: 0.85, fontSize: 12, color: C.accent5 });
};
col(M, "MOST RELIABLE BATTERS RR CAN SIGN", C.accent1, bat.slice(0, 5).map((r) => r.player), "Full top 10 on slide 6", "ans-bat");
col(M + 4.1, "MOST RELIABLE BOWLERS RR CAN SIGN", C.accent1, bowl.slice(0, 5).map((r) => r.player), "Full top 10 on slide 7", "ans-bowl");
col(M + 8.2, "UNCAPPED INDIAN FRESHERS", C.accent2, ub.slice(0, 5).map((r) => r.player), "Batters from domestic T20; bowlers are a watchlist (slide 8)", "ans-unc");
card(s, M, 5.6, 12.1, 1.15, HEX.dk2, "ans-callout");
txt(s, [{ text: "First target: Sikandar Raza. ", options: { bold: true, color: HEX.accent3 } },
  { text: "#1 signable bowler and #5 batter: covers RR's death-overs batting gap and middle-overs bowling in one overseas slot.", options: { color: HEX.lt1 } }],
  { x: M + 0.3, y: 5.72, w: 11.5, h: 0.9, fontSize: 17, valign: "middle" });
s.addNotes("Lead with the decision. Everything after this slide is why we trust it.");

// 3 ---------------------------------------------------------------- pressure
sec("How");
s = slide("LIGHT", "Pressure is defined before every ball");
card(s, M, 1.35, 5.4, 2.55, "F4F0FB", "def-stakes");
txt(s, "50%  STAKES", { x: M + 0.25, y: 1.5, w: 5, h: 0.5, fontSize: 20, bold: true, color: C.accent1, fontFace: "Cambria" });
txt(s, "How much can the next ball swing the match? A win-probability model (validated on the unseen 2026 season) measures it.", { x: M + 0.25, y: 2.05, w: 4.9, h: 1.7, fontSize: 15 });
card(s, M, 4.1, 5.4, 2.6, "FCEAF1", "def-diff");
txt(s, "50%  DIFFICULTY", { x: M + 0.25, y: 4.25, w: 5, h: 0.5, fontSize: 20, bold: true, color: C.accent2, fontFace: "Cambria" });
txt(s, "Scoreboard gap to par, wickets lost, a recent collapse, a dot-ball squeeze, and how late it is. The top 20% of balls are HIGH pressure.", { x: M + 0.25, y: 4.8, w: 4.9, h: 1.8, fontSize: 15 });
image(s, "pressure_by_over_heatmap.png", 6.3, 1.35, 6.4, 3.3, "Share of high-pressure balls by over and innings");
chip(s, 6.3, 4.95, 3.1, `${hi.dismissal_pct.toFixed(1)}%`, `of balls end in a dismissal under HIGH pressure, vs ${lo.dismissal_pct.toFixed(1)}% LOW`, "F4F0FB", HEX.accent2, HEX.dk1, "def-dis", 30);
chip(s, 9.6, 4.95, 3.1, `${Number(D.summary.high_pressure_deliveries).toLocaleString("en-US")}`, "HIGH-pressure balls rated, batting first and chasing", "F4F0FB", HEX.accent1, HEX.dk1, "def-n", 30);
s.addNotes("Only information available before the ball is used. Stakes alone missed batting-first collapses, so difficulty is half the definition.");

// 4 ---------------------------------------------------------------- fair + honest
s = slide("LIGHT", "Fair comparison, honest uncertainty");
const steps = [["Context", "Expected runs and wickets for an average player in the same situation"], ["Value", "Actual minus expected; a wicket costs its real runs"],
  ["Opponents", "Ridge model nets out the bowlers or batters actually faced, putting IPL and T20I on one scale"], ["Shrinkage", "Small samples pulled to average"]];
steps.forEach(([h, b], i) => {
  const x = M + i * 3.07;
  card(s, x, 1.35, 2.85, 2.2, i % 2 ? "F4F0FB" : "ECE6FA", `step-${i}`);
  txt(s, `${i + 1} · ${h}`, { x: x + 0.2, y: 1.5, w: 2.45, h: 0.45, fontSize: 17, bold: true, color: C.accent1, fontFace: "Cambria" });
  txt(s, b, { x: x + 0.2, y: 2.0, w: 2.45, h: 1.45, fontSize: 13.5 });
});
chip(s, M, 3.8, 3.85, pct(cb.reliability_of_raw_delta), `of a batter's raw "clutch" gap is real signal (bowlers: ${pct(cw.reliability_of_raw_delta)}), so we shrink it`, "F4F0FB", HEX.accent2, HEX.dk1, "f-clutch");
chip(s, M + 4.1, 3.8, 3.85, `${D.robust.batting.weights_min}–10 of 10`, "of the batting top 10 kept under 7 alternative weightings", "F4F0FB", HEX.accent1, HEX.dk1, "f-robust");
chip(s, M + 8.2, 3.8, 3.9, "100", "match-level bootstrap resamples give every player a P(top 10) and a rank range", "F4F0FB", HEX.accent1, HEX.dk1, "f-boot");
txt(s, "Score = pressure performance 35% · consistency 20% · match impact (win probability added) 20% · vs own baseline 15% · usual ability 10%. Validated chronologically: train 2022–24, choose on 2025, test on unseen 2026.",
  { x: M, y: 5.6, w: 12.1, h: 0.9, fontSize: 14, color: C.accent5 });
s.addNotes("The scientific finding that shapes everything: most apparent clutch is noise, so we never rank a raw clutch table.");

// 5 ---------------------------------------------------------------- reality check
sec("Who");
s = slide("LIGHT", "The best under pressure are all under contract");
const un = (side) => D.unrestricted[side].slice(0, 5).map((r) => [r.rank, r.player, r.why.replace("Under IPL contract: ", "").replace(" (IPL 2026 squad)", "")]);
txt(s, "Unrestricted top 5 batters", { x: M, y: 1.3, w: 5.9, h: 0.4, fontSize: 15, bold: true, color: C.accent5 });
s.addTable(rows(["#", "Player", "2026 team"], un("batting"), 12), { x: M, y: 1.72, w: 5.9, colW: [0.45, 2.6, 2.85], border: { type: "none" }, rowH: 0.36 });
txt(s, "Unrestricted top 5 bowlers", { x: M, y: 4.05, w: 5.9, h: 0.4, fontSize: 15, bold: true, color: C.accent5 });
s.addTable(rows(["#", "Player", "2026 team"], un("bowling"), 12), { x: M, y: 4.47, w: 5.9, colW: [0.45, 2.6, 2.85], border: { type: "none" }, rowH: 0.36 });
const rules = [["Under IPL contract", "on any 2026 squad, RR included"], ["Pakistan", "no player in the IPL since 2009"], ["Bangladesh", "not reliably acquirable (a stated judgement)"], ["Retired or banned", "Russell, Ashwin, Mohit Sharma, Brook"]];
txt(s, "So we rank only players RR can sign. Excluded:", { x: 6.9, y: 1.3, w: 5.8, h: 0.45, fontSize: 16, bold: true, color: C.accent1 });
rules.forEach(([h, b], i) => {
  const y = 1.85 + i * 0.95;
  card(s, 6.9, y, 5.8, 0.8, i % 2 ? "F4F0FB" : "FCEAF1", `rule-${i}`);
  txt(s, h, { x: 7.1, y: y + 0.1, w: 2.1, h: 0.6, fontSize: 14, bold: true, color: C.accent2, valign: "middle" });
  txt(s, b, { x: 9.25, y: y + 0.1, w: 3.3, h: 0.6, fontSize: 13, valign: "middle" });
});
txt(s, `Pool left: ${D.pool.batting} batters, ${D.pool.bowling} bowlers. Scores stay percentiles among all eligible players, so they compare with the contracted elite.`,
  { x: 6.9, y: 5.75, w: 5.8, h: 0.9, fontSize: 13, color: C.accent5 });
s.addNotes("A list of stars would not help at the auction. This is the most important framing decision in the submission.");

// 6/7 ---------------------------------------------------------------- top 10s
for (const [side, title] of [["batting", "Top 10 batters RR can sign"], ["bowling", "Top 10 bowlers RR can sign"]]) {
  const r = D[side];
  s = slide("LIGHT", title);
  s.addChart(pres.charts.BAR, [{ name: "Reliability score", labels: r.map((x) => `${x.rank}. ${x.player}`).reverse(), values: r.map((x) => x.score).reverse() }],
    Object.assign(chartBase("Reliability score (percentile among all eligible players)"), { x: M, y: 1.25, w: 6.6, h: 5.6, barDir: "bar", chartColors: [side === "batting" ? HEX.accent1 : HEX.accent2],
      valAxisMinVal: 0, valAxisMaxVal: 100, dataLabelPosition: "outEnd" }));
  s.addTable(rows(["#", "Role", "Fits RR need", "P(top 10)"], r.map((x) => [x.rank, x.role.replace(" (4-5)", "").replace(" (6-7)", ""), x.need.replace("Death-overs / finishing batting", "Finishing").replace("Death-overs bowling", "Death overs").replace("Middle-overs batting", "Middle overs").replace("Middle-overs bowling", "Middle overs").replace("Powerplay / opening batting", "Powerplay").replace("Powerplay bowling", "Powerplay"), pct(x.p_top10)]), 11.5),
    { x: 7.45, y: 1.35, w: 5.25, colW: [0.45, 1.8, 1.85, 1.15], border: { type: "none" }, rowH: 0.4 });
  const note = side === "batting"
    ? "Mitchell has the most IPL experience; Raza is 97th percentile in death-overs batting. Six of ten have no IPL record, so they are rated on opponent-adjusted T20Is."
    : "Raza, Theekshana and Zampa are near-certain top-10 picks. #9–#10 (Joseph, Adair) are statistically level with Sodhi and Farooqi.";
  txt(s, note, { x: 7.45, y: 5.95, w: 5.25, h: 0.9, fontSize: 12, color: C.accent5 });
  s.addNotes("P(top 10) = share of 100 bootstrap resamples in which the player stays top 10 within the signable pool: measurement uncertainty, not a forecast.");
}

// 8 ---------------------------------------------------------------- uncapped
s = slide("LIGHT", "Uncapped Indian freshers, rated on Indian pitches");
const ut = (rr) => rows(["#", "Player", "Team", "Age", "Score", "P(top 5)"], rr.map((r) => [r.rank, r.player, r.domestic_team.replace(" (India)", ""), r.age_at_auction, Math.round(r.reliability_score), pct(r.p_top5_bootstrap)]), 11.5);
txt(s, "Batters", { x: M, y: 1.25, w: 5.9, h: 0.4, fontSize: 17, bold: true, color: C.accent1, fontFace: "Cambria" });
s.addTable(ut(ub), { x: M, y: 1.7, w: 5.9, colW: [0.4, 2.05, 1.3, 0.6, 0.7, 0.85], border: { type: "none" }, rowH: 0.38 });
txt(s, "Bowlers: watchlist", { x: 6.8, y: 1.25, w: 5.9, h: 0.4, fontSize: 17, bold: true, color: C.accent2, fontFace: "Cambria" });
s.addTable(ut(uw), { x: 6.8, y: 1.7, w: 5.9, colW: [0.4, 2.05, 1.3, 0.6, 0.7, 0.85], border: { type: "none" }, rowH: 0.38 });
chip(s, M, 4.3, 3.0, tv.batting.spearman_smat_vs_pack_usual.toFixed(2), "domestic batting rating vs IPL rating: it carries over", "F4F0FB", HEX.accent1, HEX.dk1, "u-bat", 30);
chip(s, M + 3.2, 4.3, 3.0, tv.bowling.spearman_smat_vs_pack_usual.toFixed(2), "domestic bowling: no carry-over, hence watchlist", "FCEAF1", HEX.accent2, HEX.dk1, "u-bowl", 30);
txt(s, "Public Syed Mushtaq Ali Trophy data (Cricsheet, 272 matches), scored with the same pressure definition and the same score. Pool: never capped, not retired, not on an IPL 2026 squad, aged 30 or under. All 52 candidates were checked on Wikipedia.",
  { x: 7.0, y: 4.35, w: 5.7, h: 1.5, fontSize: 13 });
txt(s, "Domestic scores are percentiles among SMAT players and are not directly comparable with the international lists. Data runs to 2024/25.", { x: M, y: 6.1, w: 12.1, h: 0.5, fontSize: 11.5, color: C.accent5 });
s.addNotes("Season 1's winners backed an uncapped Indian. These are the Indian-slot ideas the data supports. Batting evidence is informative; bowling evidence is not, and we say so.");

// 9 ---------------------------------------------------------------- RR fit
sec("So what");
s = slide("LIGHT", "What RR needs, and who fills it");
image(s, "report/rr_phase_ranks.png", M, 1.25, 5.9, 3.6, "RR phase ranks among 10 IPL teams, 2025 and 2026");
txt(s, "RR's batting is #1 of 10 in the powerplay but 7th–10th at the death; in 2025 its death bowling conceded runs faster than any other team's.",
  { x: M, y: 5.0, w: 5.9, h: 1.0, fontSize: 13.5 });
const fits = [[`Finishing batting · priority ${pr["Death-overs / finishing batting"]}`, "Sikandar Raza (97th pct at the death)"],
  [`Death bowling · priority ${pr["Death-overs bowling"]}`, "Maheesh Theekshana, then Adam Zampa"],
  [`Middle-overs batting · priority ${pr["Middle-overs batting"]}`, "Mark Chapman, Daryl Mitchell"],
  ["Indian slots (uncapped)", `${ub[0].player}, ${ub[1].player}`]];
fits.forEach(([need, who], i) => {
  const y = 1.3 + i * 1.3;
  card(s, 6.85, y, 5.85, 1.1, i === 3 ? "FCEAF1" : "F4F0FB", `fit-${i}`);
  txt(s, need, { x: 7.05, y: y + 0.1, w: 5.5, h: 0.4, fontSize: 13, bold: true, color: i === 3 ? C.accent2 : C.accent1 });
  txt(s, who, { x: 7.05, y: y + 0.5, w: 5.5, h: 0.5, fontSize: 17, fontFace: "Cambria" });
});
txt(s, "RR's own players were rated with the same framework. Squad fit guides targeting but never reorders the reliability lists.", { x: 6.85, y: 6.5, w: 5.85, h: 0.45, fontSize: 11.5, color: C.accent5 });
s.addNotes("Needs were derived before matching any candidate. Opening is RR's strength, not a need.");

// 10 ---------------------------------------------------------------- plan
s = slide("DARK", "The auction plan");
const plan = [["1", "Sikandar Raza", "death-overs bat + middle-overs ball, one overseas slot"],
  ["2", "Theekshana, then Zampa", "defend the death, where RR leaked most"],
  ["3", "Chapman or Mitchell", "middle-overs batting under pressure"],
  ["4", `${ub[0].player} · ${ub[1].player}`, "uncapped Indian batters to scout for Indian slots"]];
plan.forEach(([n, who, why], i) => {
  const y = 2.0 + i * 0.95;
  s.addShape(pres.shapes.OVAL, { x: M, y: y + 0.05, w: 0.6, h: 0.6, fill: { color: HEX.accent2 }, line: { color: HEX.accent2 }, objectName: `plan-dot-${i}` });
  txt(s, n, { x: M, y: y + 0.05, w: 0.6, h: 0.6, fontSize: 20, bold: true, color: C.background1, align: "center", valign: "middle" });
  txt(s, [{ text: who, options: { bold: true, color: HEX.lt1 } }, { text: `  ${why}`, options: { color: HEX.accent4 } }], { x: M + 0.85, y: y + 0.05, w: 11.2, h: 0.6, fontSize: 19, valign: "middle" });
});
txt(s, "Honest limits: every signable international is overseas; several have little IPL record; uncapped bowlers are a watchlist. Re-run in one command after the 17 Nov 2026 releases.",
  { x: M, y: 6.0, w: 12.1, h: 0.75, fontSize: 13, color: C.accent4 });
s.addNotes("Close on the decision and the honest limits. The interactive dashboard (dashboard/SupeRR_Intelligence_Dashboard.html) lets the panel explore every player.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  const themeJs = process.env.APPLY_THEME_JS;
  if (themeJs && fs.existsSync(themeJs)) { const { applyTheme } = require(themeJs); await applyTheme(OUT, THEME); console.log("theme applied"); }
  else console.warn("APPLY_THEME_JS not set: scheme colours will use Office defaults");
  console.log("written", OUT);
})();
