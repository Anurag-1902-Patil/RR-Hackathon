"""Single-file interactive dashboard: dashboard/SupeRR_Intelligence_Dashboard.html

Self-contained (no server, no CDN, opens offline). Data is embedded as JSON from the pipeline outputs;
charts are inline SVG drawn in vanilla JS. Design: overview first -> filter -> details on demand;
position/length encodings; colour never the only cue (text labels everywhere); table view for every chart;
keyboard-operable; light + dark themes.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.config import REPORTS_DIR, RESEARCH_DIR, ROOT

MO = REPORTS_DIR / "model_outputs"
OUT = ROOT / "dashboard" / "SupeRR_Intelligence_Dashboard.html"
COMP = ["pressure_perf", "consistency", "impact", "delta", "usual"]


def r(x, n=1):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)


def main_players(side: str) -> list[dict]:
    s = pd.read_csv(MO / f"reliability_{side}.csv")
    fit = pd.read_csv(RESEARCH_DIR / "player_to_rr_squad_fit.csv")
    fit = fit[fit.side == side].set_index("player_id")
    bat = side == "batting"
    out = []
    for x in s.itertuples():
        f = fit.loc[x.player_id] if x.player_id in fit.index else None
        out.append({
            "id": int(x.player_id), "name": x.player, "country": x.national_side if isinstance(x.national_side, str) else "",
            "team": x.latest_team if isinstance(x.latest_team, str) else "", "role": x.role, "score": r(x.score),
            "rank": None if pd.isna(x.rank) else int(x.rank), "orank": int(x.overall_rank), "signable": bool(x.rr_acquirable),
            "why": x.not_acquirable_reason if isinstance(x.not_acquirable_reason, str) else "",
            "p": r(x.p_top10, 2), "lo": r(x.boot_rank_p05, 0), "hi": r(x.boot_rank_p95, 0),
            "op": r(x.overall_p_top10, 2), "olo": r(x.overall_boot_rank_p05, 0), "ohi": r(x.overall_boot_rank_p95, 0),
            "pct": [r(getattr(x, f"pct_{c}"), 2) for c in COMP],
            "hb": int(getattr(x, "balls_high" if bat else "legal_balls_high")), "inn": int(x.pressure_innings),
            "vh": r(x.value_per100_high), "ipl": r(x.pct_balls_IPL, 0),
            "a_hi": r(x.sr_high if bat else x.economy_high, 1 if bat else 2), "a_lo": r(x.sr_low if bat else x.economy_low, 1 if bat else 2),
            "wk": None if bat else int(x.wickets_high),
            "need": f.best_fit_requirement if f is not None else None, "fit": r(f.squad_fit_score, 0) if f is not None else None,
        })
    return out


def uncapped_players(side: str) -> list[dict]:
    y = pd.read_csv(MO / f"uncapped_scores_{side}.csv")
    y = y[y.eligible & y.score.notna()]
    bat = side == "batting"
    disp = {}
    from src.domestic.verified_uncapped import DISPLAY
    out = []
    for x in y.itertuples():
        if x.in_pool:
            status = "In fresher pool"
        elif isinstance(x.exclusion_reason, str) and x.exclusion_reason:
            status = x.exclusion_reason[0].upper() + x.exclusion_reason[1:]
        elif x.india_t20i_cap_in_pack:
            status = "Capped for India (T20I)"
        elif isinstance(x.ipl_2026_team, str):
            status = f"On IPL 2026 squad: {x.ipl_2026_team}"
        elif not x.recent:
            status = "No SMAT since 2023/24"
        else:
            status = "Not in pool"
        name = DISPLAY.get(x.cricsheet_name) or (x.full_name if isinstance(x.full_name, str) else x.cricsheet_name)
        out.append({"id": int(x.player_id), "name": name, "team": x.smat_team, "role": x.role, "score": r(x.score),
                    "rank": None if pd.isna(x.pool_rank) else int(x.pool_rank), "pool": bool(x.in_pool), "status": status,
                    "age": None if pd.isna(x.age_at_auction) else int(x.age_at_auction),
                    "p": r(getattr(x, "p_top5", np.nan), 2), "lo": r(getattr(x, "boot_rank_p05", np.nan), 0), "hi": r(getattr(x, "boot_rank_p95", np.nan), 0),
                    "pct": [r(getattr(x, f"pct_{c}"), 2) for c in COMP],
                    "hb": int(getattr(x, "balls_high" if bat else "legal_balls_high")), "inn": int(x.pressure_innings), "vh": r(x.value_per100_high),
                    "a_hi": r(x.sr_high if bat else x.economy_high, 1 if bat else 2), "a_lo": r(x.sr_low if bat else x.economy_low, 1 if bat else 2),
                    "seasons": x.smat_seasons})
    return out


def data() -> dict:
    D = json.loads((REPORTS_DIR / "deck_data.json").read_text(encoding="utf-8"))
    po = pd.read_csv(REPORTS_DIR / "dashboard_data" / "pressure_by_over.csv")
    ph = pd.read_csv(RESEARCH_DIR / "rr_phase_performance.csv")
    ph = ph[ph.year.isin([2025, 2026])]
    return {
        "summary": D["summary"], "pool": D["pool"], "clutch": D["clutch"], "robust": D["robust"], "wp": D["wp_test"],
        "profile": D["pressure_profile"], "priorities": D["priorities"], "transfer": D["uncapped_transfer"],
        "bat": main_players("batting"), "bowl": main_players("bowling"),
        "ubat": uncapped_players("batting"), "ubowl": uncapped_players("bowling"),
        "byover": po.to_dict("records"), "phase": ph[["side", "year", "phase", "metric", "rr_rank_of_10"]].to_dict("records"),
    }


def build() -> None:
    html = TEMPLATE.replace("__DATA__", json.dumps(data(), separators=(",", ":"), default=str))
    OUT.write_text(html, encoding="utf-8")
    print("written", OUT, f"{OUT.stat().st_size / 1024:.0f} KB")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SupeRR Intelligence</title>
<style>
:root{--bg:#F7F6FB;--panel:#FFFFFF;--ink:#1B1F3B;--muted:#5E6280;--line:#E4E2EE;--soft:#F1EEF9;
--pri:#4B2A99;--pri-soft:#E4DCF6;--acc:#C2185B;--acc-soft:#FBE3EC;--gold:#9A7A12;--na:#A3A6B8;--hero1:#21184F;--hero2:#4B2A99}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#12132A;--panel:#1B1D3A;--ink:#ECEBF6;--muted:#A9ABC6;--line:#2E3058;--soft:#24264A;
--pri:#A58BEB;--pri-soft:#3A2F6B;--acc:#F06292;--acc-soft:#4A2238;--gold:#E3C35A;--na:#6E7194;--hero1:#0E0C26;--hero2:#33206F}}
:root[data-theme="dark"]{--bg:#12132A;--panel:#1B1D3A;--ink:#ECEBF6;--muted:#A9ABC6;--line:#2E3058;--soft:#24264A;
--pri:#A58BEB;--pri-soft:#3A2F6B;--acc:#F06292;--acc-soft:#4A2238;--gold:#E3C35A;--na:#6E7194;--hero1:#0E0C26;--hero2:#33206F}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "Segoe UI",Calibri,system-ui,sans-serif}
h1,h2,h3{font-family:Cambria,Georgia,serif;margin:0}
.hero{background:linear-gradient(120deg,var(--hero1),var(--hero2));color:#fff;padding:22px 28px 18px}
.hero h1{font-size:30px}.hero p{margin:4px 0 0;color:#D9D0F5;max-width:900px}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-top:16px}
.kpi{background:rgba(255,255,255,.1);border-radius:12px;padding:10px 14px}.kpi b{display:block;font:700 24px Cambria,Georgia,serif}
.kpi span{font-size:12.5px;color:#D9D0F5}
nav{display:flex;gap:4px;flex-wrap:wrap;padding:10px 24px;background:var(--panel);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
nav button{border:0;background:transparent;color:var(--muted);padding:8px 14px;border-radius:999px;font:600 14px inherit;cursor:pointer}
nav button[aria-selected="true"]{background:var(--pri);color:#fff}nav button:focus-visible,button:focus-visible,select:focus-visible,input:focus-visible{outline:3px solid var(--acc);outline-offset:2px}
main{padding:20px 24px 40px;max-width:1320px;margin:0 auto}section[hidden]{display:none}
.grid{display:grid;gap:16px}.g3{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}.g2{grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.card h3{font-size:17px;margin-bottom:8px}.eyebrow{font:700 12px inherit;letter-spacing:.06em;text-transform:uppercase;color:var(--pri)}
.eyebrow.acc{color:var(--acc)}.muted{color:var(--muted)}.small{font-size:12.5px}
ol.names{margin:6px 0 0;padding-left:22px;font:17px/1.7 Cambria,Georgia,serif}
.callout{background:var(--hero1);color:#fff;border-radius:14px;padding:14px 18px;margin-top:16px}.callout b{color:#F2D06B}
.plan{display:grid;gap:10px;margin-top:6px}.step{display:flex;gap:12px;align-items:center}
.dot{flex:0 0 30px;height:30px;border-radius:50%;background:var(--acc);color:#fff;display:grid;place-items:center;font-weight:700}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}
.seg button{border:0;background:var(--panel);color:var(--ink);padding:7px 14px;cursor:pointer;font:600 13px inherit}
.seg button[aria-pressed="true"]{background:var(--pri);color:#fff}
select,input[type=search]{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:7px 10px;font:inherit}
.lb{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:16px}@media(max-width:900px){.lb{grid-template-columns:1fr}}
.rows{display:flex;flex-direction:column;gap:2px;max-height:640px;overflow:auto;padding-right:4px}
.row{display:grid;grid-template-columns:34px minmax(120px,190px) 1fr 52px;gap:8px;align-items:center;border:0;background:transparent;color:var(--ink);
text-align:left;padding:5px 6px;border-radius:8px;cursor:pointer;font:inherit}
.row:hover,.row[aria-current="true"]{background:var(--soft)}.row .rk{font-weight:700;color:var(--muted);text-align:right}
.row .nm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.row .tag{font-size:11px;color:var(--muted);display:block;line-height:1.1}
.bar{height:14px;background:var(--soft);border-radius:4px;position:relative}.bar i{position:absolute;left:0;top:0;bottom:0;border-radius:0 4px 4px 0;background:var(--pri)}
.bar i.na{background:repeating-linear-gradient(135deg,var(--na) 0 4px,transparent 4px 7px);border:1px solid var(--na)}
.bar i.acc{background:var(--acc)}.sc{font-variant-numeric:tabular-nums;text-align:right;font-weight:600}
.detail h2{font-size:22px}.chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.chip{background:var(--soft);border-radius:999px;padding:3px 10px;font-size:12.5px}
.chip.ok{background:var(--pri-soft)}.chip.no{background:var(--acc-soft)}
.mini{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0}.mini div{background:var(--soft);border-radius:10px;padding:8px 10px}
.mini b{display:block;font:700 19px Cambria,Georgia,serif}.mini span{font-size:12px;color:var(--muted)}
.comp{display:grid;grid-template-columns:150px 1fr 44px;gap:8px;align-items:center;margin:5px 0;font-size:13.5px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left}
th{color:var(--muted);font-weight:600;cursor:pointer;white-space:nowrap}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
details summary{cursor:pointer;color:var(--pri);font-weight:600;margin:10px 0}
svg text{fill:var(--ink);font-family:"Segoe UI",Calibri,sans-serif}svg .ax{fill:var(--muted);font-size:11px}svg .grid{stroke:var(--line)}
.tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--panel);padding:6px 9px;border-radius:8px;font-size:12.5px;opacity:0;transition:opacity .1s;z-index:20;max-width:260px}
.heat td{text-align:center;font-weight:700;font-variant-numeric:tabular-nums}.theme{background:rgba(255,255,255,.14);color:#fff;border:0;border-radius:999px;padding:6px 12px;cursor:pointer;font:600 13px inherit}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:var(--muted);margin:6px 0}.legend i{display:inline-block;width:14px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
footer{color:var(--muted);font-size:12px;text-align:center;padding:20px}
</style>
</head>
<body>
<header class="hero"><div class="top"><div><h1>SupeRR Intelligence</h1>
<p>Who delivers when it matters? The most reliable players under pressure that Rajasthan Royals can actually sign for IPL 2027, plus uncapped Indian freshers.</p></div>
<button class="theme" id="themeBtn" aria-label="Toggle dark mode">Dark mode</button></div>
<div class="kpis" id="kpis"></div></header>
<nav role="tablist" aria-label="Dashboard sections" id="tabs"></nav>
<main>
<section id="t-overview" role="tabpanel"></section>
<section id="t-bat" role="tabpanel" hidden></section>
<section id="t-bowl" role="tabpanel" hidden></section>
<section id="t-unc" role="tabpanel" hidden></section>
<section id="t-pressure" role="tabpanel" hidden></section>
<section id="t-rr" role="tabpanel" hidden></section>
<section id="t-method" role="tabpanel" hidden></section>
</main>
<footer>Independent analysis for SupeRR Selector Season 2 · not affiliated with Rajasthan Royals · data: RR data pack (IPL + T20I 2022–26) and Cricsheet Syed Mushtaq Ali Trophy (Open Data Commons Attribution) · information cut-off 14 Nov 2026</footer>
<div class="tip" id="tip" role="status" aria-live="polite"></div>
<script>
const D = __DATA__;
const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pct = (v) => (v == null ? "–" : Math.round(v * 100) + "%");
const fmt = (v, d = 0) => (v == null ? "–" : Number(v).toFixed(d));
const COMP = ["Pressure performance", "Consistency", "Match impact", "Vs own baseline", "Usual ability"];
const W = [35, 20, 20, 15, 10];

// theme
const root = document.documentElement;
try { const t = localStorage.getItem("srr-theme"); if (t) root.dataset.theme = t; } catch (e) {}
function syncThemeLabel() { const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches; $("#themeBtn").textContent = dark ? "Light mode" : "Dark mode"; return dark; }
$("#themeBtn").onclick = () => { const dark = syncThemeLabel(); root.dataset.theme = dark ? "light" : "dark"; try { localStorage.setItem("srr-theme", root.dataset.theme); } catch (e) {} syncThemeLabel(); };
syncThemeLabel();

// tooltip
const tip = $("#tip");
function showTip(e, html) { tip.innerHTML = html; tip.style.opacity = 1; tip.style.left = Math.min(e.clientX + 14, innerWidth - 280) + "px"; tip.style.top = e.clientY + 14 + "px"; }
function hideTip() { tip.style.opacity = 0; }

// KPIs
const S = D.summary;
$("#kpis").innerHTML = [[Number(S.deliveries).toLocaleString("en-US"), "balls analysed (IPL + T20I, 2022–26)"],
  [Number(S.high_pressure_deliveries).toLocaleString("en-US"), "HIGH-pressure balls (top 20%)"],
  [`${D.pool.batting} + ${D.pool.bowling}`, "batters + bowlers RR can sign (rated)"],
  ["272", "domestic T20 matches added for uncapped Indians"],
  [pct(D.clutch.find((c) => c.side === "batting").reliability_of_raw_delta), "of raw batting 'clutch' is real signal"]]
  .map(([b, s]) => `<div class="kpi"><b>${b}</b><span>${s}</span></div>`).join("");

// tabs
const TABS = [["overview", "Overview"], ["bat", "Batters"], ["bowl", "Bowlers"], ["unc", "Uncapped Indians"], ["pressure", "Pressure"], ["rr", "RR needs"], ["method", "Method & trust"]];
$("#tabs").innerHTML = TABS.map(([k, l], i) => `<button role="tab" id="tab-${k}" aria-controls="t-${k}" aria-selected="${i === 0}" tabindex="${i === 0 ? 0 : -1}">${l}</button>`).join("");
const tabBtns = [...document.querySelectorAll("nav button")];
function openTab(k) {
  tabBtns.forEach((b) => { const on = b.id === "tab-" + k; b.setAttribute("aria-selected", on); b.tabIndex = on ? 0 : -1; });
  TABS.forEach(([x]) => ($("#t-" + x).hidden = x !== k));
  try { localStorage.setItem("srr-tab", k); } catch (e) {}
}
tabBtns.forEach((b, i) => {
  b.onclick = () => openTab(b.id.slice(4));
  b.onkeydown = (e) => { if (e.key === "ArrowRight" || e.key === "ArrowLeft") { const j = (i + (e.key === "ArrowRight" ? 1 : -1) + tabBtns.length) % tabBtns.length; tabBtns[j].focus(); openTab(tabBtns[j].id.slice(4)); } };
});

// ---------------- overview
(function overview() {
  const top = (arr, n) => arr.filter((p) => p.rank != null).sort((a, b) => a.rank - b.rank).slice(0, n);
  const ub = top(D.ubat.filter((p) => p.pool), 5), uw = top(D.ubowl.filter((p) => p.pool), 5);
  const col = (eye, cls, arr, note, tab) => `<div class="card"><div class="eyebrow ${cls}">${eye}</div>
    <ol class="names">${arr.map((p) => `<li>${esc(p.name)}</li>`).join("")}</ol><p class="small muted">${note}</p>
    <button class="seg" style="border:1px solid var(--line);padding:6px 12px;border-radius:999px;background:var(--panel);color:var(--pri);cursor:pointer;font-weight:600" onclick="openTab('${tab}')">Explore →</button></div>`;
  const tb = D.transfer.find((t) => t.side === "batting"), tw = D.transfer.find((t) => t.side === "bowling");
  $("#t-overview").innerHTML = `<div class="grid g3">
    ${col("Most reliable batters RR can sign", "", top(D.bat, 5), "Top 5 of 10. All are overseas internationals not on any IPL 2026 squad.", "bat")}
    ${col("Most reliable bowlers RR can sign", "", top(D.bowl, 5), "Top 5 of 10. Raza tops this list and is #5 among batters.", "bowl")}
    ${col("Uncapped Indian freshers (batters)", "acc", ub, `Rated on domestic T20 (SMAT). Domestic batting carries over to the IPL (Spearman ${tb.spearman_smat_vs_pack_usual.toFixed(2)}); bowling does not (${tw.spearman_smat_vs_pack_usual.toFixed(2)}), so uncapped bowlers are a watchlist: ${uw.map((p) => esc(p.name)).join(", ")}.`, "unc")}
  </div>
  <div class="callout"><b>First target: Sikandar Raza.</b> #1 signable bowler and #5 batter, 97th percentile in death-overs batting: covers RR's biggest gap (finishing) and middle-overs bowling in one overseas slot.</div>
  <div class="grid g2" style="margin-top:16px">
    <div class="card"><h3>The auction plan</h3><div class="plan">
      ${[["Sikandar Raza", "death-overs bat + middle-overs ball"], ["Maheesh Theekshana, then Adam Zampa", "defend the death, where RR leaked most"], ["Mark Chapman or Daryl Mitchell", "middle-overs batting under pressure"], [`${ub[0].name} · ${ub[1].name}`, "uncapped Indian batters to scout for Indian slots"]]
        .map(([w, y], i) => `<div class="step"><div class="dot" aria-hidden="true">${i + 1}</div><div><b>${esc(w)}</b><br><span class="muted small">${y}</span></div></div>`).join("")}
    </div></div>
    <div class="card"><h3>Why the list is not the usual stars</h3>
      <p class="small">The unrestricted top 10 under pressure (e.g. ${D.bat.filter((p) => p.orank <= 3).sort((a, b) => a.orank - b.orank).map((p) => esc(p.name)).join(", ")}) is entirely under IPL contract.
      We rank only players RR can sign: not on any 2026 squad, not Pakistani or Bangladeshi, not retired or banned. Switch any leaderboard to <i>All eligible</i> to see the contracted elite and why each is excluded.</p>
      <p class="small muted"><b>Honest limits:</b> every signable international is overseas; several have little IPL record; uncapped evidence runs to 2024/25. Re-run in one command after the 17 Nov 2026 releases.</p></div>
  </div>`;
})();

// ---------------- leaderboard component
function leaderboard(el, cfg) {
  const st = { pool: cfg.poolDefault, role: "All", q: "", sel: null, table: false };
  el.innerHTML = `<div class="controls">
     ${cfg.poolOpts ? `<div class="seg" role="group" aria-label="Players shown">${cfg.poolOpts.map(([k, l]) => `<button data-pool="${k}" aria-pressed="${k === st.pool}">${l}</button>`).join("")}</div>` : ""}
     <label class="small">Role <select class="role"><option>All</option>${[...new Set(cfg.data.map((p) => p.role))].sort().map((r) => `<option>${esc(r)}</option>`).join("")}</select></label>
     <input type="search" class="q" placeholder="Search player" aria-label="Search player">
     <span class="small muted count"></span></div>
     <div class="legend">${cfg.legend}</div>
     <div class="lb"><div class="card"><div class="rows" role="list"></div>
       <details><summary>Table view</summary><div class="tbl" style="overflow:auto"></div></details></div>
     <div class="card detail" aria-live="polite"></div></div>
     <p class="small muted">${cfg.note}</p>`;
  const rowsEl = $(".rows", el), det = $(".detail", el);
  el.querySelectorAll("[data-pool]").forEach((b) => (b.onclick = () => { st.pool = b.dataset.pool; el.querySelectorAll("[data-pool]").forEach((x) => x.setAttribute("aria-pressed", x === b)); draw(); }));
  $(".role", el).onchange = (e) => { st.role = e.target.value; draw(); };
  $(".q", el).oninput = (e) => { st.q = e.target.value.toLowerCase(); draw(); };
  function list() {
    let a = cfg.data.filter((p) => cfg.inPool(p, st.pool));
    if (st.role !== "All") a = a.filter((p) => p.role === st.role);
    a = a.map((p) => ({ ...p, _r: cfg.rankOf(p, st.pool) })).sort((x, y) => (x._r ?? 999) - (y._r ?? 999) || y.score - x.score);
    return a;
  }
  function draw() {
    const a = list().filter((p) => !st.q || p.name.toLowerCase().includes(st.q));
    $(".count", el).textContent = `${a.length} players`;
    rowsEl.innerHTML = a.map((p) => `<button class="row" role="listitem" data-id="${p.id}" aria-current="${st.sel === p.id}" aria-label="${esc(p.name)}, rank ${p._r ?? "not ranked"}, score ${fmt(p.score)}">
      <span class="rk">${p._r ?? "–"}</span><span class="nm">${esc(p.name)}<span class="tag">${esc(cfg.tag(p))}</span></span>
      <span class="bar"><i class="${cfg.barCls(p)}" style="width:${p.score}%"></i></span><span class="sc">${fmt(p.score)}</span></button>`).join("");
    rowsEl.querySelectorAll(".row").forEach((b) => {
      b.onclick = () => { st.sel = +b.dataset.id; draw(); };
      b.onmousemove = (e) => { const p = cfg.data.find((x) => x.id === +b.dataset.id); showTip(e, `<b>${esc(p.name)}</b><br>Score ${fmt(p.score)} · ${esc(cfg.tag(p))}`); };
      b.onmouseleave = hideTip;
    });
    $(".tbl", el).innerHTML = `<table><thead><tr><th class="n">#</th><th>Player</th><th>Role</th><th class="n">Score</th><th class="n">${cfg.pLabel}</th><th class="n">HIGH balls</th><th>Status</th></tr></thead><tbody>
      ${a.map((p) => `<tr><td class="n">${p._r ?? "–"}</td><td>${esc(p.name)}</td><td>${esc(p.role)}</td><td class="n">${fmt(p.score)}</td><td class="n">${pct(cfg.pOf(p, st.pool))}</td><td class="n">${p.hb}</td><td>${esc(cfg.status(p))}</td></tr>`).join("")}</tbody></table>`;
    const sel = cfg.data.find((p) => p.id === st.sel) || a[0];
    if (sel) detail(sel);
  }
  function detail(p) {
    const r = cfg.rankOf(p, st.pool), iv = cfg.interval(p, st.pool);
    det.innerHTML = `<div class="eyebrow ${cfg.eyeCls || ""}">${esc(cfg.eyebrow(p))}</div><h2>${esc(p.name)}</h2>
      <div class="chips">${cfg.chips(p).map(([t, c]) => `<span class="chip ${c || ""}">${esc(t)}</span>`).join("")}</div>
      <div class="mini"><div><b>${fmt(p.score)}</b><span>reliability score (0–100)</span></div>
        <div><b>${r ?? "–"}</b><span>rank ${cfg.rankLabel(st.pool)}${iv ? ` · 90% range ${iv}` : ""}</span></div>
        <div><b>${pct(cfg.pOf(p, st.pool))}</b><span>${cfg.pLabel} in bootstrap resamples</span></div></div>
      <h3 style="font-size:15px;margin-top:6px">Score components (percentile among eligible)</h3>
      ${p.pct.map((v, i) => `<div class="comp"><span>${COMP[i]} <span class="muted small">${W[i]}%</span></span><span class="bar"><i class="${cfg.eyeCls === "acc" ? "acc" : ""}" style="width:${(v ?? 0) * 100}%"></i></span><span class="sc">${v == null ? "–" : Math.round(v * 100)}</span></div>`).join("")}
      <div class="mini" style="margin-top:12px"><div><b>${p.hb}</b><span>HIGH-pressure balls</span></div><div><b>${p.inn}</b><span>pressure ${cfg.unit}</span></div>
        <div><b>${p.vh == null ? "–" : (p.vh > 0 ? "+" : "") + fmt(p.vh, 1)}</b><span>runs vs expected per 100 HIGH balls</span></div></div>
      <p class="small"><b>${cfg.rawLabel}:</b> ${fmt(p.a_hi, cfg.rawDp)} under HIGH pressure vs ${fmt(p.a_lo, cfg.rawDp)} in LOW-pressure balls${p.wk != null ? ` · ${p.wk} HIGH-pressure wickets` : ""}. Raw numbers are descriptive; the score uses context- and opponent-adjusted values.</p>
      ${cfg.extra(p)}`;
  }
  draw();
}

const mainCfg = (side) => ({
  data: D[side], poolDefault: "sign", poolOpts: [["sign", "RR can sign"], ["all", "All eligible (context)"]],
  inPool: (p, pool) => pool === "all" || p.signable, rankOf: (p, pool) => (pool === "all" ? p.orank : p.rank),
  pOf: (p, pool) => (pool === "all" ? p.op : p.p), interval: (p, pool) => (pool === "all" ? (p.olo != null ? `${p.olo}–${p.ohi}` : "") : (p.lo != null ? `${p.lo}–${p.hi}` : "")),
  rankLabel: (pool) => (pool === "all" ? "among all eligible" : "among players RR can sign"), pLabel: "P(top 10)",
  tag: (p) => `${p.country || p.team} · ${p.role}${p.signable ? "" : " · contracted/excluded"}`,
  barCls: (p) => (p.signable ? (side === "bowl" ? "acc" : "") : "na"),
  status: (p) => (p.signable ? "RR can sign" : p.why), eyebrow: (p) => (p.signable ? "RR can sign" : "Not signable"), eyeCls: side === "bowl" ? "acc" : "",
  chips: (p) => [[p.country || "–"], [p.role], [p.signable ? "RR can sign" : p.why, p.signable ? "ok" : "no"], [`${p.ipl}% of balls in the IPL`]],
  unit: side === "bat" ? "innings" : "spells", rawLabel: side === "bat" ? "Strike rate" : "Economy", rawDp: side === "bat" ? 1 : 2,
  extra: (p) => (p.need ? `<div class="card" style="background:var(--soft);border:0;margin-top:8px"><b>RR fit:</b> best fits <i>${esc(p.need)}</i> · squad-fit ${fmt(p.fit)}/100 (separate layer; never reorders the ranking)</div>` : ""),
  legend: `<span><i style="background:var(--${side === "bowl" ? "acc" : "pri"})"></i>RR can sign</span><span><i style="background:repeating-linear-gradient(135deg,var(--na) 0 4px,transparent 4px 7px);border:1px solid var(--na)"></i>Contracted or excluded (hatched, labelled)</span>`,
  note: "Score = percentile composite among all eligible players (pressure performance 35%, consistency 20%, match impact 20%, vs own baseline 15%, usual ability 10%). P(top 10) = share of 100 match-level bootstrap resamples in which the player stays top 10: measurement uncertainty, not a forecast.",
});
leaderboard($("#t-bat"), mainCfg("bat"));
leaderboard($("#t-bowl"), mainCfg("bowl"));

// ---------------- uncapped
(function () {
  const el = $("#t-unc");
  const tb = D.transfer.find((t) => t.side === "batting"), tw = D.transfer.find((t) => t.side === "bowling");
  el.innerHTML = `<div class="grid g3" style="margin-bottom:16px">
    <div class="card"><div class="eyebrow acc">Why</div><p class="small">Every signable international is overseas and the RR data pack has no Indian domestic cricket. We added public Syed Mushtaq Ali Trophy ball-by-ball data (Cricsheet, 272 matches, 2020/21–2024/25), played on Indian pitches, scored with the same pressure definition and score.</p></div>
    <div class="card"><div class="eyebrow">Does domestic form carry over?</div><p class="small">Rating in SMAT vs rating in IPL/T20I for players with both: batting Spearman <b>${tb.spearman_smat_vs_pack_usual.toFixed(2)}</b> (${tb.players} players), bowling <b>${tw.spearman_smat_vs_pack_usual.toFixed(2)}</b> (${tw.players}). Batting picks are informative; bowling picks are a watchlist.</p></div>
    <div class="card"><div class="eyebrow">Fresher pool</div><p class="small">Indian, never capped, not retired, not on an IPL 2026 squad, played SMAT 2023/24 or later, aged 30 or under at the auction. All 52 candidates checked on Wikipedia (14 Nov 2026).</p></div></div>
    <div class="controls"><div class="seg" role="group" aria-label="Discipline"><button data-d="ubat" aria-pressed="true">Batters</button><button data-d="ubowl" aria-pressed="false">Bowlers (watchlist)</button></div></div>
    <div id="uncLB"></div>`;
  const cfg = (k) => ({
    data: D[k], poolDefault: "pool", poolOpts: [["pool", "Fresher pool"], ["all", "All rated in SMAT"]],
    inPool: (p, pool) => pool === "all" || p.pool, rankOf: (p, pool) => (pool === "all" ? null : p.rank), pOf: (p, pool) => (pool === "all" ? null : p.p),
    interval: (p, pool) => (pool === "all" || p.lo == null ? "" : `${p.lo}–${p.hi}`), rankLabel: () => "in the fresher pool", pLabel: "P(top 5)",
    tag: (p) => `${p.team}${p.age ? " · age " + p.age : ""} · ${p.pool ? "fresher" : p.status}`, barCls: (p) => (p.pool ? "acc" : "na"),
    status: (p) => p.status, eyebrow: (p) => (p.pool ? "Uncapped fresher" : p.status), eyeCls: "acc",
    chips: (p) => [[p.team], [p.role], [p.age ? `Age ${p.age} at auction` : "Age not verified"], [p.status, p.pool ? "ok" : "no"]],
    unit: k === "ubat" ? "innings" : "spells", rawLabel: k === "ubat" ? "Strike rate" : "Economy", rawDp: k === "ubat" ? 1 : 2,
    extra: (p) => `<p class="small muted">SMAT seasons: ${esc(p.seasons)}. Score = percentile among all eligible SMAT players (capped included); not comparable with the international lists.</p>`,
    legend: `<span><i style="background:var(--acc)"></i>In fresher pool</span><span><i style="background:repeating-linear-gradient(135deg,var(--na) 0 4px,transparent 4px 7px);border:1px solid var(--na)"></i>Capped, retired, contracted or over 30 (hatched, labelled)</span>`,
    note: "Thresholds are lower than the main lists (a SMAT season is about 7 league games); empirical-Bayes shrinkage handles small samples. P(top 5) from 60 match-level bootstrap resamples.",
  });
  const host = $("#uncLB", el);
  leaderboard(host, cfg("ubat"));
  el.querySelectorAll("[data-d]").forEach((b) => (b.onclick = () => { el.querySelectorAll("[data-d]").forEach((x) => x.setAttribute("aria-pressed", x === b)); leaderboard(host, cfg(b.dataset.d)); }));
})();

// ---------------- pressure tab
(function () {
  const el = $("#t-pressure");
  const w = 760, h = 300, m = { l: 44, r: 90, t: 16, b: 36 };
  const x = (o) => m.l + ((o - 1) / 19) * (w - m.l - m.r), y = (v) => h - m.b - (v / 60) * (h - m.t - m.b);
  const ser = [1, 2].map((inn) => D.byover.filter((d) => d.innings === inn).sort((a, b) => a.overid - b.overid));
  const col = ["var(--pri)", "var(--acc)"], lab = ["Batting first", "Chasing"];
  let svg = `<svg viewBox="0 0 ${w} ${h}" width="100%" role="img" aria-labelledby="pt pd"><title id="pt">Share of balls rated HIGH pressure by over</title><desc id="pd">Two lines, batting first and chasing, rising toward the death overs.</desc>`;
  [0, 20, 40, 60].forEach((v) => (svg += `<line class="grid" x1="${m.l}" x2="${w - m.r}" y1="${y(v)}" y2="${y(v)}"/><text class="ax" x="${m.l - 8}" y="${y(v) + 4}" text-anchor="end">${v}%</text>`));
  [1, 6, 10, 15, 20].forEach((o) => (svg += `<text class="ax" x="${x(o)}" y="${h - 12}" text-anchor="middle">${o}</text>`));
  svg += `<text class="ax" x="${(w - m.r + m.l) / 2}" y="${h - 1}" text-anchor="middle">Over</text>`;
  ser.forEach((s, i) => {
    svg += `<polyline fill="none" stroke="${col[i]}" stroke-width="2.5" points="${s.map((d) => `${x(d.overid)},${y(d.pct_high)}`).join(" ")}"/>`;
    s.forEach((d) => (svg += `<circle cx="${x(d.overid)}" cy="${y(d.pct_high)}" r="${i ? 4 : 3.5}" fill="${col[i]}" ${i ? 'stroke="var(--panel)" stroke-width="1.5"' : ""} data-t="${lab[i]}, over ${d.overid}: ${d.pct_high}% HIGH"><title>${lab[i]}, over ${d.overid}: ${d.pct_high}%</title></circle>`));
    const last = s[s.length - 1];
    svg += `<text x="${x(20) + 8}" y="${y(last.pct_high) + 4 + (i ? 10 : -6)}" style="font-size:12px;font-weight:600;fill:${col[i]}">${lab[i]}</text>`;
  });
  svg += "</svg>";
  const pf = D.profile, bw = 230, bh = 200;
  const bars = (key, title, unit) => { const mx = Math.max(...pf.map((p) => p[key])) * 1.15;
    return `<div><div class="small" style="font-weight:600">${title}</div><svg viewBox="0 0 ${bw} ${bh}" width="100%" role="img" aria-label="${title}">${pf.map((p, i) => { const bx = 20 + i * 70, hh = (p[key] / mx) * (bh - 50);
      return `<rect x="${bx}" y="${bh - 28 - hh}" width="44" height="${hh}" rx="4" fill="${p.pressure_band === "high" ? "var(--acc)" : "var(--pri)"}" opacity="${p.pressure_band === "medium" ? 0.6 : 1}"><title>${p.pressure_band}: ${p[key]}${unit}</title></rect>
      <text x="${bx + 22}" y="${bh - 34 - hh}" text-anchor="middle" style="font-size:12px;font-weight:600">${p[key].toFixed(1)}${unit}</text><text class="ax" x="${bx + 22}" y="${bh - 10}" text-anchor="middle">${p.pressure_band.toUpperCase()}</text>`; }).join("")}</svg></div>`; };
  el.innerHTML = `<div class="grid g2"><div class="card"><h3>Pressure builds through both innings</h3>${svg}
    <details><summary>Table view</summary><table><thead><tr><th class="n">Over</th><th class="n">Batting first % HIGH</th><th class="n">Chasing % HIGH</th></tr></thead><tbody>${ser[0].map((d, i) => `<tr><td class="n">${d.overid}</td><td class="n">${d.pct_high}</td><td class="n">${ser[1][i] ? ser[1][i].pct_high : "–"}</td></tr>`).join("")}</tbody></table></details></div>
    <div class="card"><h3>How pressure is defined (before every ball)</h3>
      <p><b style="color:var(--pri)">50% stakes:</b> how much the next ball can swing the match, from a win-probability model validated on the unseen 2026 season.</p>
      <p><b style="color:var(--acc)">50% difficulty:</b> scoreboard gap to an era-adjusted par, wickets lost, a recent collapse, a dot-ball squeeze, and how late it is.</p>
      <p class="small muted">HIGH = top 20% of balls. Stakes alone put 92% of HIGH balls in chases; adding difficulty lets batting-first collapses count.</p>
      <div class="grid" style="grid-template-columns:1fr 1fr">${bars("dismissal_pct", "Dismissals per 100 balls", "")}${bars("dot_pct", "Dot balls per 100 balls", "")}</div>
      <p class="small muted">Under HIGH pressure, batters are dismissed more often (${pf.find((p) => p.pressure_band === "high").dismissal_pct.toFixed(2)} vs ${pf.find((p) => p.pressure_band === "low").dismissal_pct.toFixed(2)} per 100 balls). Raw strike rate is not the yardstick because HIGH balls cluster late.</p></div></div>`;
  el.querySelectorAll("circle[data-t]").forEach((c) => { c.onmousemove = (e) => showTip(e, c.dataset.t); c.onmouseleave = hideTip; });
})();

// ---------------- RR needs tab
(function () {
  const el = $("#t-rr");
  const pr = [...D.priorities].sort((a, b) => b.priority_score - a.priority_score);
  const rows = pr.map((p) => `<div class="comp" style="grid-template-columns:220px 1fr 44px"><span>${esc(p.requirement)} <span class="chip ${p.priority === "High" ? "no" : ""}" style="font-size:11px">${p.priority}</span></span><span class="bar"><i class="${p.priority === "High" ? "acc" : ""}" style="width:${p.priority_score}%"></i></span><span class="sc">${p.priority_score.toFixed(0)}</span></div>`).join("");
  const metrics = [...new Set(D.phase.map((d) => d.metric))];
  const heat = (side) => { const ph = ["powerplay", "middle", "death"], yrs = [2025, 2026];
    const cell = (m, p, y) => { const d = D.phase.find((x) => x.side === side && x.metric === m && x.phase === p && x.year === y); if (!d) return "<td>–</td>";
      const k = d.rr_rank_of_10, a = (11 - k) / 10; return `<td style="background:color-mix(in srgb, var(--pri) ${Math.round(a * 85)}%, var(--acc-soft));color:${k <= 4 ? "#fff" : "var(--ink)"}" title="${m}, ${p} ${y}: rank ${k} of 10">#${k}</td>`; };
    const ms = [...new Set(D.phase.filter((d) => d.side === side).map((d) => d.metric))];
    return `<table class="heat"><thead><tr><th>${side === "batting" ? "Batting" : "Bowling"} metric</th>${ph.map((p) => yrs.map((y) => `<th class="n">${p} ${y}</th>`).join("")).join("")}</tr></thead><tbody>
      ${ms.map((m) => `<tr><th style="text-align:left;font-weight:500">${m.replace(/_/g, " ")}</th>${ph.map((p) => yrs.map((y) => cell(m, p, y)).join("")).join("")}</tr>`).join("")}</tbody></table>`; };
  el.innerHTML = `<div class="grid g2"><div class="card"><h3>Recruitment priority (0–100)</h3>${rows}
      <p class="small muted">Priority = 60% severity (RR's phase ranks, 2025–26) + 40% coverage gap (best current RR player's pressure percentile). Derived before matching any candidate.</p></div>
    <div class="card"><h3>Who fills each need</h3>
      ${[["Finishing batting", "Sikandar Raza", "97th percentile in death-overs batting"], ["Death bowling", "Maheesh Theekshana, then Adam Zampa", "85th and 74th percentile at the death"], ["Middle-overs batting", "Mark Chapman, Daryl Mitchell", "92nd and 66th percentile in the middle overs"], ["Indian slots", D.ubat.filter((p) => p.pool && p.rank <= 2).sort((a, b) => a.rank - b.rank).map((p) => p.name).join(", "), "uncapped batters, domestic T20 evidence"]]
        .map(([n, w, why]) => `<p><span class="eyebrow">${n}</span><br><b style="font-family:Cambria,Georgia,serif;font-size:17px">${esc(w)}</b><br><span class="small muted">${why}</span></p>`).join("")}</div></div>
    <div class="card" style="margin-top:16px;overflow:auto"><h3>RR rank among 10 IPL teams by phase (1 = best)</h3><p class="small muted">Darker = better rank; every cell shows its rank number, so colour is never the only cue.</p>${heat("batting")}<div style="height:12px"></div>${heat("bowling")}</div>`;
})();

// ---------------- method tab
(function () {
  const el = $("#t-method");
  const cb = D.clutch.find((c) => c.side === "batting"), cw = D.clutch.find((c) => c.side === "bowling");
  const wp = D.wp.filter((r) => r.innings === 2), lg = wp.find((r) => r.model === "logit"), lb = wp.find((r) => r.model === "lgbm");
  el.innerHTML = `<div class="grid g3">
    ${[["1 · Context", "For every ball, a model estimates what an average player would produce in exactly that situation (never the player's identity)."],
       ["2 · Value", "Actual minus expected, with a wicket charged at its real run cost in that situation."],
       ["3 · Opponents", "A ridge model rates batters and bowlers together, so each player is judged net of the opponents actually faced. This puts IPL and T20I on one scale."],
       ["4 · Shrinkage", "Small samples are pulled toward average; the pressure-vs-baseline gap keeps only the signal its sample supports."],
       ["5 · Score", "Pressure performance 35%, consistency 20%, match impact 20%, vs own baseline 15%, usual ability 10%, as percentiles among eligible players."],
       ["6 · Uncertainty", "100 match-level bootstrap resamples of the whole pipeline give every player a rank range and P(top 10)."]]
      .map(([h, b]) => `<div class="card"><h3>${h}</h3><p class="small">${b}</p></div>`).join("")}</div>
    <div class="grid g3" style="margin-top:16px">
      <div class="card"><div class="eyebrow">Is clutch real?</div><p><b style="font-size:26px;font-family:Cambria,Georgia,serif">${pct(cb.reliability_of_raw_delta)}</b> of a batter's raw pressure-vs-normal gap is real signal; bowlers ${pct(cw.reliability_of_raw_delta)}. So we never rank a raw clutch table.</p></div>
      <div class="card"><div class="eyebrow">Simple beat advanced</div><p>On the unseen 2026 season, logistic regression won (chase Brier <b>${lg.brier.toFixed(3)}</b>) over LightGBM (${lb.brier.toFixed(3)}), which could not extrapolate to record scoring.</p></div>
      <div class="card"><div class="eyebrow">Robust</div><p>Under 7 alternative weightings, ${D.robust.batting.weights_min}–10 of the unrestricted batting top 10 stay; across 4 pressure definitions, ${Math.min(D.robust.batting.defs_min, D.robust.bowling.defs_min)}–${Math.max(D.robust.batting.defs_max, D.robust.bowling.defs_max)} of 10.</p></div></div>
    <div class="card" style="margin-top:16px"><h3>Limitations and sources</h3><ul class="small">
      <li>Pressure is unobserved; the definition is a modelling choice, stress-tested with alternatives.</li>
      <li>Several signable internationals have little or no IPL record; they are rated on opponent-adjusted T20Is.</li>
      <li>Uncapped evidence: Cricsheet SMAT data runs to 2024/25 (8 matches that season); domestic bowling form did not predict IPL bowling.</li>
      <li>Exclusions of Bangladeshi players and of Harry Brook are stated judgements. Squads change on 17 Nov 2026; the pipeline re-runs in one command.</li>
      <li>Sources: RR data pack (primary); Cricsheet SMAT (ODC-By); official IPL and franchise pages and Wikipedia for identity, availability and retirement (full register in the repository).</li></ul></div>`;
})();

let start = "overview";
try { start = localStorage.getItem("srr-tab") || "overview"; } catch (e) {}
if (TABS.some(([k]) => k === start)) openTab(start);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    build()
