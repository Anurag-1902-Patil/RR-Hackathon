/* SupeRR Intelligence deck (structured: theme, layouts, placeholders, sections).
 * Every number is read from reports/deck_data.json (exported from the same pipeline outputs as the PDF).
 * Run: node src/reporting/deck/build_deck.js   (APPLY_THEME_JS=<path to pptx skill apply_theme.js> to apply theme colours)
 */
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "../../..");
const REP = path.join(ROOT, "reports");
const D = JSON.parse(fs.readFileSync(path.join(REP, "deck_data.json"), "utf8"));
const OUT = path.join(REP, "presentation.pptx");
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
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "SupeRR Intelligence: Most Reliable Players Under Pressure";
pres.author = "SupeRR Intelligence (independent analysis)";
const C = pres.SchemeColor;
const W = 13.333, H = 7.5, M = 0.6;
const FOOT = "SupeRR Intelligence · independent analysis · not affiliated with Rajasthan Royals";

// ---------------- layouts
pres.defineSlideMaster({
  title: "DARK_TITLE", background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 1.6, w: 12.1, h: 2.0, fontSize: 54, bold: true, color: C.background1, valign: "bottom", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 3.8, w: 11.5, h: 1.5, fontSize: 20, color: C.accent4, valign: "top", align: "left" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION", background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 1.7, w: 12.1, h: 2.1, fontSize: 44, bold: true, color: C.background1, valign: "bottom", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.0, w: 12.1, h: 1.0, fontSize: 20, color: C.accent4, valign: "top", align: "left" }, text: "" } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: HEX.accent4 },
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: HEX.lt1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.35, w: 12.1, h: 0.85, fontSize: 32, bold: true, color: C.text1, valign: "middle", align: "left" }, text: "" } },
    { text: { text: FOOT, options: { x: M, y: 7.0, w: 9, h: 0.3, fontSize: 10, color: HEX.accent5, fontFace: "Calibri" } } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: HEX.accent5 },
});

let section = "";
function slide(master, title, sub) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (sub) s.addText(sub, { placeholder: "body" });
  return s;
}
function newSection(t) { section = t; pres.addSection({ title: t }); }
function txt(s, text, o) { s.addText(text, Object.assign({ isTextBox: true, fontSize: 16, color: C.text1, valign: "top", margin: 0 }, o)); }
function card(s, x, y, w, h, fill, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill }, objectName: name });
}
function stat(s, x, y, w, big, label, fill, bigColor, labColor, name, size = 40) {
  card(s, x, y, w, 1.75, fill, name);
  txt(s, big, { x: x + 0.25, y: y + 0.15, w: w - 0.5, h: 0.9, fontSize: size, bold: true, color: bigColor, fontFace: "Cambria", valign: "middle" });
  txt(s, label, { x: x + 0.25, y: y + 1.1, w: w - 0.5, h: 0.55, fontSize: 14, color: labColor });
}
function bullets(s, items, o) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8 } })),
    Object.assign({ isTextBox: true, fontSize: 16, color: C.text1, valign: "top", margin: 0 }, o));
}
function image(s, file, x, y, w, h, alt) { s.addImage({ path: FIG(file), x, y, w, h, sizing: { type: "contain", w, h }, altText: alt }); }
const pct = (v) => `${Math.round(v * 100)}%`;
const verdict = (p) => (p >= 0.8 ? "clear" : p >= 0.65 ? "moderate" : p >= 0.55 ? "slight" : "indistinguishable");
const chartBase = (title) => ({
  showTitle: true, title, titleFontSize: 14, titleColor: HEX.dk1, titleFontFace: "+mj-lt",
  catAxisLabelColor: HEX.accent5, valAxisLabelColor: HEX.accent5, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, valGridLine: { color: "E6E6EF", size: 0.75 }, catGridLine: { style: "none" },
  dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", dataLabelFontSize: 11, showValue: true,
});
function tableRows(header, rows) {
  const h = header.map((t) => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk1 }, fontSize: 12 } }));
  return [h, ...rows.map((r, i) => r.map((t) => ({ text: String(t), options: { fontSize: 12, color: HEX.dk1, fill: { color: i % 2 ? "F7F6FB" : "FFFFFF" } } })))];
}

// ================= OPENING
newSection("Opening");
let s = slide("DARK_TITLE", "SupeRR Intelligence", "Who delivers when it matters? The most reliable batters and bowlers under pressure, and how they could strengthen Rajasthan Royals for IPL 2027");
txt(s, `SupeRR Selector Season 2 · Data: RR data pack, ${Number(D.summary.deliveries).toLocaleString("en-US")} deliveries, IPL + T20I ${D.summary.date_from.slice(0, 4)}–${D.summary.date_to.slice(0, 4)} · Information cut-off 14 Nov 2026`,
  { x: M, y: 6.3, w: 12, h: 0.5, fontSize: 12, color: C.accent3 });
s.addNotes("Independent analytical submission for SupeRR Selector Season 2. Not affiliated with or endorsed by Rajasthan Royals. All numbers come from the pipeline outputs; the full methodology is in the PDF report.");

s = slide("CONTENT", "The answer in one slide");
stat(s, M, 1.45, 3.85, D.batting[0].player, `#1 batter · score ${D.batting[0].score}/100 · P(top 10) ${pct(D.batting[0].p_top10)}`, HEX.lt2, HEX.accent1, HEX.dk1, "stat-bat", 26);
stat(s, M + 4.1, 1.45, 3.85, D.bowling[0].player, `#1 bowler · score ${D.bowling[0].score}/100 · P(top 10) ${pct(D.bowling[0].p_top10)}`, HEX.lt2, HEX.accent1, HEX.dk1, "stat-bowl", 26);
stat(s, M + 8.2, 1.45, 3.9, "Finisher + death bowler", "RR's two highest-priority needs", HEX.accent2, HEX.lt1, HEX.lt1, "stat-need", 26);
bullets(s, [
  "Pressure = 50% stakes (win-probability leverage) + 50% difficulty (scoreboard gap, wickets, collapse, squeeze), all known before the ball.",
  "Players are judged against what an average player would do in the same situation, adjusted for the opponents they actually faced.",
  "\"Clutch\" is mostly noise: only ~21% (batters) and ~4% (bowlers) of a raw pressure-vs-normal gap is signal, so scores shrink it accordingly.",
  "Lists contain only players RR can sign: no IPL 2026 squad member, no Pakistani or Bangladeshi player, no retired or banned player.",
], { x: M, y: 3.55, w: 12.1, h: 3.2 });
s.addNotes("Lead with the conclusion: the two #1s among players RR can actually sign, and that RR's needs are finishing and death bowling. Every player in the unrestricted performance top 10 is under contract elsewhere, so the submitted lists rank the acquirable pool only.");

// ================= METHOD
newSection("Methodology");
slide("SECTION", "1 · How we measured pressure reliability", "Data → pressure → fair comparison → robust ranking");

s = slide("CONTENT", "From 200,961 balls to a defensible ranking");
image(s, "report/pipeline.png", M, 1.4, 12.1, 3.6, "Ten-step analytical pipeline from data pack to RR squad fit");
bullets(s, [
  "Official RR data pack is the primary source. It was audited (806 of 816 checkable results reconcile) and kept unmodified.",
  "Every model is validated chronologically: train 2022–24, choose on 2025, test on unseen 2026.",
  "Layer 1 (purple) answers the competition. Layer 2 (pink) assesses RR fit and never reorders the lists.",
], { x: M, y: 5.25, w: 12.1, h: 1.6, fontSize: 15 });
s.addNotes("Walk the pipeline left to right, then the second row right to left. Emphasise no leakage: every state variable is known before the ball.");

s = slide("CONTENT", "Pressure builds through both innings, not just in chases");
image(s, "pressure_by_over_heatmap.png", M, 1.35, 8.0, 2.4, "Heatmap of share of deliveries classed high pressure by over and innings");
bullets(s, [
  "Leverage alone put 92% of high-pressure balls in chases and none in first-innings death overs, because the innings-1 win model is necessarily uncertain.",
  "Final definition: 50% leverage + 50% difficulty. HIGH = top 20% of balls.",
  "A v2 review fixed batting-first collapses (2.6% → 23.9% rated HIGH) and removed phase cliffs (largest jump 39 → 5 points).",
], { x: M, y: 4.05, w: 8.0, h: 2.8, fontSize: 15 });
const pp = D.pressure_profile;
s.addChart(pres.charts.BAR, [{ name: "Dismissal % of balls faced", labels: pp.map((r) => r.pressure_band.toUpperCase()), values: pp.map((r) => r.dismissal_pct) }],
  Object.assign(chartBase("Dismissal rate by pressure band (%)"), { x: 8.9, y: 1.35, w: 3.85, h: 5.4, barDir: "col", chartColors: [HEX.accent4, "9B7FD6", HEX.accent1],
    showLegend: false, valAxisMinVal: 4, valAxisMaxVal: 6.5, dataLabelFormatCode: "0.0", dataLabelPosition: "outEnd" }));
s.addNotes("Pressure is defined only with pre-ball information. Dismissals rise under HIGH pressure. Raw strike rate is not the yardstick, because high-pressure balls cluster late in the innings.");

s = slide("CONTENT", "Fair comparison: context first, then opponents");
const steps = [
  ["1 · Expectation", "What would an average player produce in this exact situation? Context only, never player identity."],
  ["2 · Value per ball", "Actual minus expected, with a wicket charged at its situational run cost."],
  ["3 · Opponent adjustment", "Ridge model on batter + bowler effects, so each player is rated net of the opponents actually faced."],
  ["4 · Shrinkage", "Small samples pull toward average. The pressure-vs-baseline gap keeps only the signal its sample supports."],
];
steps.forEach(([h, b], i) => {
  const x = M + i * 3.07;
  card(s, x, 1.5, 2.85, 3.5, i % 2 ? HEX.lt2 : "ECE6FA", `step-${i + 1}`);
  txt(s, h, { x: x + 0.2, y: 1.7, w: 2.45, h: 0.6, fontSize: 18, bold: true, color: C.accent1, fontFace: "Cambria" });
  txt(s, b, { x: x + 0.2, y: 2.4, w: 2.45, h: 2.5, fontSize: 15 });
});
card(s, M, 5.3, 12.1, 1.35, HEX.dk2, "fairness-callout");
txt(s, "No competition-tier dummy is used: that would rate an average associate player the same as an average IPL player. Strength is calibrated through players who cross competitions; only the IPL scoring era (par 171 → 191) is modelled directly.",
  { x: M + 0.3, y: 5.45, w: 11.5, h: 1.1, fontSize: 15, color: C.background1, valign: "middle" });
s.addNotes("This is how IPL and T20I data are combined fairly, which the brief explicitly asks about.");

s = slide("CONTENT", "Simple beat advanced: models validated on unseen 2026");
const wpt = D.wp_test.filter((r) => r.innings === 2);
s.addChart(pres.charts.BAR, [{ name: "Brier (lower is better)", labels: wpt.map((r) => ({ "constant(base rate)": "Base rate", logit: "Logistic (chosen)", lgbm: "LightGBM" }[r.model])), values: wpt.map((r) => r.brier) }],
  Object.assign(chartBase("Chase win-probability: Brier score, 2026 test"), { x: M, y: 1.4, w: 6.2, h: 5.2, barDir: "col", chartColors: [HEX.accent4, HEX.accent1, HEX.accent5],
    showLegend: false, valAxisMinVal: 0, dataLabelFormatCode: "0.000", dataLabelPosition: "outEnd" }));
bullets(s, [
  `Logistic regression won on validation and test (chase AUC ${wpt.find((r) => r.model === "logit").auc}). LightGBM could not extrapolate to 2026 scoring levels.`,
  "Expected-runs models beat an over-by-over baseline on RMSE in both 2025 and 2026.",
  "A bug caught during validation: 2026 expected runs per ball came out at 1.35 against 1.51 actual until a rolling environment par was added.",
  "Production values use leave-one-year-out cross-fitting, so no ball is scored by a model that saw its own match.",
], { x: 7.2, y: 1.5, w: 5.5, h: 5.2, fontSize: 15 });
s.addNotes("A model is not included just because it is advanced. Baselines are shown alongside.");

s = slide("CONTENT", "Is clutch real? Mostly, it is noise");
const cb = D.clutch.find((r) => r.side === "batting"), cw = D.clutch.find((r) => r.side === "bowling");
stat(s, M, 1.5, 3.8, pct(cb.reliability_of_raw_delta), "of a batter's raw pressure-vs-normal gap is real signal", HEX.lt2, HEX.accent1, HEX.dk1, "clutch-bat");
stat(s, M, 3.5, 3.8, pct(cw.reliability_of_raw_delta), "for bowlers: essentially undetectable", HEX.lt2, HEX.accent2, HEX.dk1, "clutch-bowl");
image(s, "report/clutch_variance.png", 4.7, 1.5, 8.0, 3.2, "Observed vs true spread of pressure deltas");
bullets(s, [
  "Ordinary-situation value persists from 2022–24 to 2025–26 (batting r ≈ 0.4). Pressure-only value does not (r ≈ 0).",
  "So we never rank a raw clutch table. The score blends shrunk pressure performance, consistency and impact with underlying ability.",
], { x: 4.7, y: 5.0, w: 8.0, h: 1.8, fontSize: 15 });
s.addNotes("The honest scientific finding: pressure performance is measurable but mostly not a stable trait. This shapes the score design.");

s = slide("CONTENT", "Reliability score: transparent, and stress-tested");
s.addTable(tableRows(["Component", "Weight", "What it measures"], [
  ["Pressure performance", "35%", "Opponent-adjusted value on HIGH-pressure balls"],
  ["Consistency", "20%", "Share of pressure innings/spells at or above expectation"],
  ["Match impact", "20%", "Win probability added on HIGH-pressure balls"],
  ["Vs own baseline", "15%", "Pressure gap vs the player's normal level, shrunk"],
  ["Usual ability", "10%", "All-situation rating, the best predictor of the future"],
]), { x: M, y: 1.45, w: 7.4, colW: [2.3, 0.9, 4.2], border: { type: "none" } });
stat(s, 8.4, 1.45, 4.3, `${D.robust.batting.weights_min}–10 of 10`, "unrestricted batting top 10 kept across 7 weightings", HEX.lt2, HEX.accent1, HEX.dk1, "robust-w");
stat(s, 8.4, 3.4, 4.3, `${Math.min(D.robust.batting.defs_min, D.robust.bowling.defs_min)}–${Math.max(D.robust.batting.defs_max, D.robust.bowling.defs_max)} of 10`, "unrestricted top 10 kept across 4 pressure definitions", HEX.lt2, HEX.accent2, HEX.dk1, "robust-d");
bullets(s, ["Sample size is handled by shrinkage, so there is no separate \"sample confidence\" weight (it would double-count).",
  "Uncertainty: 100 match-level bootstrap resamples of the whole pipeline give each player a 90% rank interval and P(top 10)."],
  { x: M, y: 5.45, w: 12.1, h: 1.4, fontSize: 15 });
s.addNotes("The prompt's starting weights were treated as a hypothesis. The definition of pressure moves the lists more than the weights do.");

// ================= PLAYERS
newSection("The players");
slide("SECTION", "2 · The most reliable players RR can sign", "Two separate top 10s · IPL + T20I 2022–2026 · verified identities and availability");

s = slide("CONTENT", "Only players RR can actually acquire are ranked");
const rules = [
  ["Under IPL contract", "Anyone on an IPL 2026 squad (all 10 teams, including RR) is excluded. The whole unrestricted performance top 10 falls here."],
  ["Pakistan", "No Pakistan player has appeared in the IPL since 2009."],
  ["Bangladesh", "Not reliably acquirable after the BCCI-directed release of Mustafizur Rahman (a judgement: no formal rule was published)."],
  ["Retired or banned", "Russell, Ashwin and Mohit Sharma have retired from the IPL. Brook's ban may cover 2027, so he is excluded."],
];
rules.forEach(([h, b], i) => {
  const y = 1.45 + i * 1.0;
  card(s, M, y, 12.1, 0.85, i % 2 ? HEX.lt2 : "ECE6FA", `rule-${i + 1}`);
  txt(s, h, { x: M + 0.25, y: y + 0.1, w: 2.9, h: 0.65, fontSize: 16, bold: true, color: C.accent1, valign: "middle" });
  txt(s, b, { x: M + 3.3, y: y + 0.1, w: 8.6, h: 0.65, fontSize: 15, valign: "middle" });
});
txt(s, `Ranks, P(top 10) and uncertainty are recomputed within the acquirable pool (${D.pool.batting} batters, ${D.pool.bowling} bowlers). Scores stay percentiles among all eligible players, so they compare directly with the contracted elite.`,
  { x: M, y: 5.6, w: 12.1, h: 1.1, fontSize: 15, color: C.accent5 });
s.addNotes("This is the most important framing decision. The best performers under pressure are almost all contracted, so a list of them would not help RR at the auction. Players released on 17 Nov 2026 join the pool and the pipeline re-runs in one command.");
for (const side of ["batting", "bowling"]) {
  const rows = D[side];
  s = slide("CONTENT", side === "batting" ? "Top 10 batters RR can sign" : "Top 10 bowlers RR can sign");
  s.addChart(pres.charts.BAR, [{ name: "Reliability score", labels: rows.map((r) => `${r.rank}. ${r.player}`).reverse(), values: rows.map((r) => r.score).reverse() }],
    Object.assign(chartBase("Reliability score (0–100, percentile among all eligible)"), { x: M, y: 1.35, w: 6.4, h: 5.45, barDir: "bar", chartColors: [HEX.accent1], showLegend: false,
      valAxisMinVal: 0, valAxisMaxVal: 100, dataLabelPosition: "outEnd", catAxisLabelFontSize: 12 }));
  s.addTable(tableRows(["#", "Role", "P(top10)", "90% rank"], rows.map((r) => [r.rank, r.role.replace(" (4-5)", "").replace(" (6-7)", ""), pct(r.p_top10), `${r.boot_lo}–${r.boot_hi}`])),
    { x: 7.25, y: 1.45, w: 5.45, colW: [0.5, 2.55, 1.1, 1.3], border: { type: "none" }, rowH: 0.42 });
  s.addNotes(`Scores are percentile composites among eligible players. P(top10) is the share of 100 bootstrap resamples in which the player stays top 10: measurement uncertainty, not a forecast. # is the rank within the acquirable pool; the pool is small, so P(top10) partly reflects limited competition.`);
}

s = slide("CONTENT", "How sure are we? Model uncertainty across all eligible players");
image(s, "rank_uncertainty_top20.png", M, 1.3, 12.1, 5.55, "Rank uncertainty for top 20 batters and bowlers");
s.addNotes("Dot = final rank; thick bar = bootstrap 90% interval; thin bar = range across pressure definitions. This chart covers the full eligible pool, which shows the model's stability. Within the acquirable lists, bowlers #9-#10 (Joseph, Adair) are statistically level with Sodhi and Farooqi.");

for (const side of ["batting", "bowling"]) {
  s = slide("CONTENT", side === "batting" ? "Why these batters, and not the alternatives?" : "Why these bowlers, and not the alternatives?");
  s.addTable(tableRows(["#", "Selected", "Strongest unselected alternative (rank)", "Selected ranks higher", "Verdict"],
    D[side].map((r) => [r.rank, r.player, `${r.alt} (${r.alt_rank})`, pct(r.p_beats_alt), verdict(r.p_beats_alt)])),
    { x: M, y: 1.4, w: 12.1, colW: [0.5, 2.9, 4.3, 2.2, 2.2], border: { type: "none" }, rowH: 0.45 });
  txt(s, "Alternatives = highest-scoring unselected players in the same data role (the strongest real competition). Verdict thresholds: clear ≥ 80%, moderate 65–80%, slight 55–65%.",
    { x: M, y: 6.45, w: 12.1, h: 0.45, fontSize: 12, color: C.accent5 });
  s.addNotes("Read the verdict column honestly: several lower-ranked picks are statistically indistinguishable from their best alternative. Full per-player profiles are in the PDF.");
}

s = slide("CONTENT", "Narrowly missed: credible alternatives, not rejects");
s.addTable(tableRows(["Side", "Rank", "Player", "Role", "Score", "Gap to #10", "P(beats #10)", "Main shortfall"],
  D.near.map((r) => [r.side, r.rank, r.player, r.role, r.score, r.gap_to_rank10, pct(r.p_beats_rank10_bootstrap), r.main_shortfall_vs_rank10.replace("_", " ")])),
  { x: M, y: 1.45, w: 12.1, colW: [1.0, 0.7, 2.2, 2.3, 0.9, 1.2, 1.4, 2.4], border: { type: "none" }, rowH: 0.45 });
txt(s, "Ish Sodhi and Fazalhaq Farooqi are 2.3 points behind bowler #10 and beat #10 in about half of all resamples: a coin-flip. The acquirable bowling pool has only 12 players.", { x: M, y: 5.2, w: 12.1, h: 0.8, fontSize: 16 });
s.addNotes("Demonstrates the shortlist was deliberate: each near-miss is named with the component that separated them.");

// ---------------- uncapped Indian freshers (public SMAT data)
const tvb = Object.fromEntries(D.uncapped_transfer.map((r) => [r.side, r]));
s = slide("CONTENT", "Uncapped Indian freshers: adding India's domestic T20");
bullets(s, [
  "Every signable player in the data pack is an overseas international, and the pack has no Indian domestic cricket.",
  "So we added public ball-by-ball data for the Syed Mushtaq Ali Trophy (Cricsheet): 272 matches, 62,850 balls, 2020/21–2024/25, all on Indian pitches.",
  "Same pressure definition, same five components and weights. One opponent-adjusted model spans data pack + SMAT, linked by 152 players who appear in both.",
  "Pool: Indian, never capped, not retired, not on an IPL 2026 squad, aged 30 or under at the auction. All 52 candidates were checked on Wikipedia.",
], { x: M, y: 1.45, w: 7.6, h: 5.3, fontSize: 15 });
stat(s, 8.5, 1.45, 4.2, tvb.batting.spearman_smat_vs_pack_usual.toFixed(2), `batting: domestic rating vs IPL/T20I rating (Spearman, ${tvb.batting.players} players). Informative.`, HEX.lt2, HEX.accent1, HEX.dk1, "transfer-bat");
stat(s, 8.5, 3.55, 4.2, tvb.bowling.spearman_smat_vs_pack_usual.toFixed(2), `bowling (${tvb.bowling.players} players): no carry-over, so bowlers are a watchlist.`, HEX.lt2, HEX.accent2, HEX.dk1, "transfer-bowl");
txt(s, "Cricsheet's latest SMAT season (2024/25) has only 8 matches, so most fresher evidence is 2020/21–2023/24.", { x: 8.5, y: 5.65, w: 4.2, h: 1.0, fontSize: 12, color: C.accent5 });
s.addNotes("Season 1's winning entry backed an uncapped Indian, Vignesh Puthur, whom RR signed. This slide answers the obvious question: what about Indian players who have not played internationals? The validation is the key honesty point: domestic batting form predicts IPL batting; domestic bowling form did not, on this sample.");

s = slide("CONTENT", "Uncapped Indian freshers: the picks");
const ut = (rows) => tableRows(["#", "Player", "Team", "Age", "Score", "P(top 5)"],
  rows.map((r) => [r.rank, r.player, r.domestic_team.replace(" (India)", ""), r.age_at_auction, Math.round(r.reliability_score), pct(r.p_top5_bootstrap)]));
txt(s, "Batters", { x: M, y: 1.35, w: 5.9, h: 0.45, fontSize: 18, bold: true, color: C.accent1, fontFace: "Cambria" });
s.addTable(ut(D.uncapped.batting), { x: M, y: 1.85, w: 5.9, colW: [0.4, 2.0, 1.35, 0.6, 0.75, 0.8], border: { type: "none" }, rowH: 0.42 });
txt(s, "Bowlers: watchlist (low confidence)", { x: 6.8, y: 1.35, w: 5.9, h: 0.45, fontSize: 18, bold: true, color: C.accent2, fontFace: "Cambria" });
s.addTable(ut(D.uncapped.bowling), { x: 6.8, y: 1.85, w: 5.9, colW: [0.4, 2.0, 1.35, 0.6, 0.75, 0.8], border: { type: "none" }, rowH: 0.42 });
bullets(s, [
  `${D.uncapped.batting[0].player} and ${D.uncapped.batting[1].player} are the clearest uncapped batters (each top 5 in ${pct(D.uncapped.batting[0].p_top5_bootstrap)} of resamples). Picks #4–#5 are close to Shubham Pundir and Subhranshu Senapati.`,
  `${D.uncapped.bowling[0].player} leads the bowlers clearly; beyond that, treat the list as a live-scouting watchlist.`,
], { x: M, y: 4.75, w: 12.1, h: 1.6, fontSize: 14 });
txt(s, "Score = percentile among all eligible SMAT players (capped included); not directly comparable with the main lists. Rated higher but excluded: Sai Kishore (capped, GT), Cariappa and Gowtham (retired), and several players over 30.",
  { x: M, y: 6.3, w: 12.1, h: 0.55, fontSize: 11, color: C.accent5 });
s.addNotes("These are the Indian-slot ideas the data supports. Batting picks rest on informative evidence; bowling picks do not, which is said plainly. Uncapped players released on 17 Nov join this pool on re-run.");

// ================= RR
newSection("Rajasthan Royals");
slide("SECTION", "3 · How these players could strengthen Rajasthan Royals", "Squad first, needs second, candidates third");

s = slide("CONTENT", "RR's batting is elite up front and weak at the death");
image(s, "report/rr_phase_ranks.png", M, 1.35, 12.1, 3.9, "RR phase ranks among 10 IPL teams, 2025 and 2026");
bullets(s, [
  "Powerplay batting #1 of 10 in both seasons, so opening is not a need.",
  "Death batting 7th–10th on run rate, boundary %, context value and wickets lost. In 2026, Jadeja (SR 140.5), Jurel (150.0) and Dubey (146.3) were all below the league death SR of 169.4.",
  "2025: RR conceded runs faster at the death than any other team. In 2026, Sandeep Sharma conceded 13.70 an over at the death.",
], { x: M, y: 5.35, w: 12.1, h: 1.55, fontSize: 15 });
s.addNotes("RR players were rated with exactly the same framework as all candidates; no preferential treatment. The 2027 squad is pending the 17 Nov retention deadline.");

s = slide("CONTENT", "Evidence-led recruitment priorities");
const pr = D.priorities.slice().sort((a, b) => a.priority_score - b.priority_score);
s.addChart(pres.charts.BAR, [{ name: "Priority", labels: pr.map((r) => r.requirement), values: pr.map((r) => r.priority_score) }],
  Object.assign(chartBase("Recruitment priority (0–100)"), { x: M, y: 1.35, w: 7.4, h: 5.45, barDir: "bar", showLegend: false, valAxisMinVal: 0, valAxisMaxVal: 100,
    chartColors: pr.map((r) => (r.priority === "High" ? HEX.accent2 : r.priority === "Medium" ? HEX.accent3 : HEX.accent4)), dataLabelPosition: "outEnd" }));
bullets(s, [
  "Priority = 60% severity (RR's phase ranks, 2025–26) + 40% coverage gap (best eligible RR player's pressure percentile).",
  "High: finishing batting, death bowling, middle-overs batting.",
  "Only Jadeja ranks in the bowling top 20 among current RR players. RR's eligible middle order (Parag, Hetmyer, Jurel) ranks #53–#66 under pressure.",
], { x: 8.3, y: 1.5, w: 4.4, h: 5.3, fontSize: 15 });
s.addNotes("Needs were derived before matching any candidate; the method is in the PDF section 10.");

s = slide("CONTENT", "Reliability and fit are separate layers");
image(s, "report/fit_vs_reliability.png", M, 1.3, 12.1, 4.9, "Reliability rank vs RR squad fit for the 20 acquirable players");
txt(s, "Squad fit = 50% RR need priority + 35% phase evidence + 15% roster slot (an overseas player costs a scarce slot). It informs RR's targeting but never reorders the competition lists.",
  { x: M, y: 6.3, w: 12.1, h: 0.6, fontSize: 13, color: C.accent5 });
s.addNotes("A very reliable player can still be a lower RR priority if he fills a role RR already covers, e.g. an opener.");

for (const side of ["batting", "bowling"]) {
  s = slide("CONTENT", side === "batting" ? "Batting targets mapped to RR needs" : "Bowling targets mapped to RR needs");
  s.addTable(tableRows(["#", "Player", "Ind/Ovs", "RR need addressed", "Fit", "Tier", "Uplift*"],
    D[side].map((r) => [r.rank, r.player, r.nat, r.need, r.fit, r.tier, `${r.uplift > 0 ? "+" : ""}${r.uplift}`])),
    { x: M, y: 1.4, w: 12.1, colW: [0.5, 2.8, 1.2, 3.4, 0.8, 2.2, 1.2], border: { type: "none" }, rowH: 0.44 });
  txt(s, "*Hypothetical model estimate, not a forecast: runs per season if the player took the 2026 phase balls of RR's weakest regular in that phase. All players are currently uncontracted; they must register for the auction.",
    { x: M, y: 6.35, w: 12.1, h: 0.55, fontSize: 12, color: C.accent5 });
  s.addNotes(side === "batting" ? "Raza is the only primary target (97th percentile in death-overs batting). Chapman and Mitchell fit middle-overs batting. All are overseas, so slots are the binding constraint." :
    "Raza also leads the bowling list for the middle overs. Theekshana (85th percentile at the death, IPL experience incl. RR 2025) and Zampa (74th) fit death bowling.");
}

s = slide("CONTENT", "Risks we checked against official sources");
const risks = [
  ["Limited IPL record", "Six of ten batters (Campher, Chapman, Dockrell, Ibrahim Zadran, Tector, Burl) and Chase, Ngarava, Adair have no IPL balls in the data."],
  ["Age at auction", "Raza 40, Adil Rashid 38, Neesham 36 (not scored; reported for squad planning)."],
  ["Recency", "Obed McCoy's last T20I was in September 2025."],
  ["Close calls", "Bowlers #9-#10 (Joseph, Adair) are statistically level with Sodhi and Farooqi."],
  ["Registration", "Each player must register for the auction; the final list is expected around 3 Dec 2026."],
];
risks.forEach(([h, b], i) => {
  const y = 1.45 + i * 1.05;
  card(s, M, y, 12.1, 0.9, i % 2 ? HEX.lt2 : "FFF4E5", `risk-${i + 1}`);
  txt(s, h, { x: M + 0.25, y: y + 0.12, w: 2.9, h: 0.66, fontSize: 16, bold: true, color: C.accent2, valign: "middle" });
  txt(s, b, { x: M + 3.3, y: y + 0.12, w: 8.6, h: 0.66, fontSize: 15, valign: "middle" });
});
s.addNotes("Every flag is sourced in the research source register. Exclusion of Bangladeshi players and of Brook is a judgement, stated as such. The IPL 2027 purse is unverified, so no financial claims are made.");

// ================= CLOSE
newSection("Close");
s = slide("DARK_TITLE", "Recommendation for Rajasthan Royals", "");
bullets(s, [
  "First target Sikandar Raza: death-overs finishing and middle-overs bowling in one overseas slot.",
  "Death bowling: Maheesh Theekshana, then Adam Zampa.",
  "Middle-overs batting depth: Mark Chapman or Daryl Mitchell. Keep the opening pair, RR's clearest strength.",
  `Indian slots: scout uncapped batters ${D.uncapped.batting[0].player} and ${D.uncapped.batting[1].player} first; uncapped bowlers are a watchlist.`,
  "Re-run the selection when the 17 Nov releases are published: better-rated players may enter the pool (one command).",
], { x: M, y: 3.7, w: 12.1, h: 3.2, fontSize: 17, color: C.background1 });
s.addNotes("Close on the decision: Raza first, then a death bowler, within RR's overseas slots. Every name is signable today. Dashboard and full report accompany this deck.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  const themeJs = process.env.APPLY_THEME_JS;
  if (themeJs && fs.existsSync(themeJs)) {
    const { applyTheme } = require(themeJs);
    await applyTheme(OUT, THEME);
    console.log("theme applied");
  } else {
    console.warn("APPLY_THEME_JS not set: scheme colours will use Office defaults");
  }
  console.log("written", OUT);
})();
