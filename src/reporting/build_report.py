"""Build the final research report (HTML -> PDF via headless Edge/Chrome).

All tables and player numbers are read from pipeline outputs; narrative text frames them.
Output: reports/final_report.html, reports/final_report.pdf
"""
from __future__ import annotations

import html
import subprocess
from pathlib import Path

import pandas as pd

from src.config import REPORTS_DIR, RESEARCH_DIR, ROOT

MO, FIG = REPORTS_DIR / "model_outputs", REPORTS_DIR / "figures"
BROWSERS = [Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")]
COMP = [("pressure_perf", "Pressure perf."), ("consistency", "Consistency"), ("impact", "Impact"), ("delta", "Vs baseline"), ("usual", "Usual")]
E = lambda x: html.escape("" if x is None or (isinstance(x, float) and x != x) else str(x))


def img(path: Path, caption: str, width: str = "100%") -> str:
    return (f'<figure><img src="{path.relative_to(REPORTS_DIR).as_posix()}" style="width:{width}"/>'
            f"<figcaption>{caption}</figcaption></figure>")


def table(df: pd.DataFrame, cls: str = "") -> str:
    h = "".join(f"<th>{E(str(c))}</th>" for c in df.columns)
    rows = "".join("<tr>" + "".join(f"<td>{E(str(v))}</td>" for v in r) + "</tr>" for r in df.itertuples(index=False))
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{rows}</tbody></table>'


def verdict(p: float) -> str:
    return "clear" if p >= .8 else "moderate" if p >= .65 else "slight" if p >= .55 else "statistically indistinguishable"


def load():
    D = {s: pd.read_csv(MO / f"reliability_{s}.csv") for s in ("batting", "bowling")}
    return dict(
        ub=pd.read_csv(REPORTS_DIR / 'top_5_uncapped_batters.csv'), uw=pd.read_csv(REPORTS_DIR / 'top_5_uncapped_bowlers.csv'),
        utv=pd.read_csv(MO / 'uncapped_transfer_validation.csv'),
        uall={s_: pd.read_csv(MO / f'uncapped_scores_{s_}.csv') for s_ in ('batting', 'bowling')},
        rel=D, reg=pd.read_csv(RESEARCH_DIR / "player_verification_register.csv").drop_duplicates("player_id").set_index("player_id"),
        fit=pd.read_csv(RESEARCH_DIR / "player_to_rr_squad_fit.csv").set_index(["side", "rank"]),
        up=pd.read_csv(RESEARCH_DIR / "rr_phase_uplift_scenarios.csv").set_index(["side", "rank"]),
        alt=pd.read_csv(REPORTS_DIR / "player_comparisons.csv"), near=pd.read_csv(MO / "near_misses.csv"),
        rec=pd.read_csv(REPORTS_DIR / "rr_recruitment_recommendations.csv"), pm=pd.read_csv(RESEARCH_DIR / "rr_recruitment_priority_matrix.csv"),
        wp=pd.read_csv(MO / "wp_evaluation.csv"), cv=pd.read_csv(MO / "clutch_variance.csv"), xe=pd.read_csv(MO / "expected_models_evaluation.csv"),
        ws=pd.read_csv(MO / "reliability_weight_sensitivity.csv"), ds=pd.read_csv(MO / "reliability_definition_sensitivity.csv"),
        sq=pd.read_csv(RESEARCH_DIR / "rr_squad_database.csv"), aud=pd.read_csv(RESEARCH_DIR / "rr_player_performance_database.csv"),
        summ=pd.read_csv(REPORTS_DIR / "dashboard_data" / "dataset_summary.csv", index_col=0)["value"].to_dict(),
        excl=pd.read_csv(MO / "excluded_inactive.csv"))


def rr_bat_table(aud: pd.DataFrame) -> pd.DataFrame:
    a = aud[aud.bat_balls.fillna(0) >= 700]
    return pd.DataFrame({"RR batter": a.player, "Role": a.bat_role, "Balls": a.bat_balls.astype(int), "SR": a.bat_sr.map("{:.1f}".format),
                         "SR HIGH": a.bat_sr_high.map("{:.1f}".format), "Pressure pctile": a.bat_pressure_pctile_vs_eligible.map("{:.0f}".format),
                         "Eligible / rank": [f"Yes, #{int(r)}" if e and pd.notna(r) else ("Yes" if e else "No (sample)")
                                             for e, r in zip(a.bat_eligible, a.bat_reliability_rank)]})


def top_table(s: pd.DataFrame, side: str) -> str:
    t = s[s["rank"] <= 10].copy()
    hb = "balls_high" if side == "batting" else "legal_balls_high"
    out = pd.DataFrame({"#": t["rank"], "Player": t.player, "Role (data)": t.role, "Score": t.score.round(0).astype(int),
                        "HIGH balls": t[hb].astype(int), "Pressure inns" if side == "batting" else "Pressure spells": t.pressure_innings.astype(int),
                        "Value/100 HIGH": t.value_per100_high.map("{:+.1f}".format)})
    if side == "batting":
        out["SR HIGH / LOW"] = t.sr_high.map("{:.0f}".format) + " / " + t.sr_low.map("{:.0f}".format)
    else:
        out["Econ HIGH / LOW"] = t.economy_high.map("{:.2f}".format) + " / " + t.economy_low.map("{:.2f}".format)
    out["P(top 10)"] = t.p_top10.map("{:.0%}".format)
    out["90% rank"] = t.boot_rank_p05.astype(int).astype(str) + "–" + t.boot_rank_p95.astype(int).astype(str)
    return table(out, "dense")


def profile(side: str, r: pd.Series, D: dict) -> str:
    g = D["reg"].loc[r.player_id]
    f = D["fit"].loc[(side, r["rank"])]
    u = D["up"].loc[(side, r["rank"])]
    a = D["alt"][(D["alt"].side == side) & (D["alt"].selected_id == r.player_id)]
    hb = "balls_high" if side == "batting" else "legal_balls_high"
    raw = (f"SR {r.sr_high:.1f} under HIGH pressure vs {r.sr_low:.1f} in LOW-pressure situations" if side == "batting" else
           f"economy {r.economy_high:.2f} under HIGH pressure vs {r.economy_low:.2f} in LOW; {int(r.wickets_high)} HIGH-pressure wickets")
    comp = pd.DataFrame({"Component (percentile)": [c for _, c in COMP],
                         r.player: [f"{r['pct_' + k] * 100:.0f}" for k, _ in COMP],
                         **{x.alternative: [f"{x[f'pct_{k}_alt'] * 100:.0f}" for k, _ in COMP] for _, x in a.iterrows()}})
    comp.loc[len(comp)] = ["Score (rank)", f"{r.score:.0f} ({int(r['rank'])})"] + [f"{x.score_alt:.0f} ({x.alternative_rank})" for _, x in a.iterrows()]
    comp.loc[len(comp)] = ["HIGH-pressure balls", f"{int(r[hb])}"] + [f"{int(x.high_balls_alt)}" for _, x in a.iterrows()]
    strengths = sorted(COMP, key=lambda c: -r["pct_" + c[0]])
    why = []
    for _, x in a.iterrows():
        diffs = {lab: r["pct_" + k] - x[f"pct_{k}_alt"] for k, lab in COMP}
        lead, trail = max(diffs, key=diffs.get), min(diffs, key=diffs.get)
        why.append(f"<li>vs <b>{E(x.alternative)}</b> (rank {x.alternative_rank}, {E(x.role_alternative)}): ahead most on {lead.lower()} "
                   f"({diffs[lead] * 100:+.0f} pts){f', behind on {trail.lower()} ({diffs[trail] * 100:+.0f} pts)' if diffs[trail] < 0 else ''}. "
                   f"Ranks higher in <b>{x.p_selected_ranks_higher_bootstrap:.0%}</b> of bootstrap resamples, so the advantage is <i>{verdict(x.p_selected_ranks_higher_bootstrap)}</i>.</li>")
    ipl_share = r.get("pct_balls_IPL", float("nan"))
    flag_cls = "flag warn" if (ipl_share < 1 or g.age_at_auction_calc >= 38 or "INJURY" in str(g.notes)) else "flag"
    return f"""
<section class="profile">
  <div class="ph"><div class="rk">{int(r['rank'])}</div><div><h3>{E(g.full_name)}</h3>
  <div class="meta">{E(g.country)} · {E(g.bat)} / {E(g.bowl)} · age at auction {g.age_at_auction_calc} (calculated from verified DOB) · IPL 2026: {E(g.ipl_2026_team)} · data role: {E(r.role)}</div></div>
  <div class="score">{r.score:.0f}<span>/100</span></div></div>
  <div class="{flag_cls}"><b>IPL 2027:</b> {E(g.ipl_2027_status)} · IPL share of this player's balls in the data: <b>{ipl_share:.0f}%</b> · {E(g.notes)} <span class="src">[{E(g.sources)}]</span></div>
  <div class="kpis"><div><b>{int(r[hb])}</b>HIGH-pressure balls</div><div><b>{int(r.pressure_innings)}</b>pressure {'innings' if side == 'batting' else 'spells'}</div>
  <div><b>{r.value_per100_high:+.1f}</b>value per 100 on HIGH</div><div><b>{r.p_top10:.0%}</b>P(top 10)</div>
  <div><b>{int(r.boot_rank_p05)}–{int(r.boot_rank_p95)}</b>90% rank interval</div><div><b>{int(r.rank_min_across_defs)}–{int(r.rank_max_across_defs)}</b>rank across definitions</div></div>
  <div class="two">
    <div>{table(comp, 'mini')}<p class="small">Descriptive: {raw}. Strongest: {strengths[0][1].lower()}, {strengths[1][1].lower()}. Weakest: {strengths[-1][1].lower()}.</p></div>
    <div><img src="figures/report/players/{side}_{int(r['rank']):02d}.png" style="width:100%"/></div>
  </div>
  <h4>Why this player?</h4><ul>{''.join(why)}</ul>
  <h4>How this player could strengthen Rajasthan Royals (layer 2, separate from the ranking)</h4>
  <p>Best fits RR's <b>{E(f.best_fit_requirement)}</b> need (priority {f.requirement_priority:.0f}/100). Context value in the {E(f.best_fit_phase)} phase is
  {f.phase_value_eb_per100:+.1f} per 100 balls over {int(f.phase_balls)} balls (percentile {f.phase_value_pctile:.0f} among eligible players). {E(f.indian_or_overseas)} player;
  squad-fit <b>{f.squad_fit_score:.0f}</b> ({f.squad_fit_no_slot:.0f} without the overseas-slot cost). <i>Hypothetical model estimate, not a forecast:</i>
  {u.est_runs_gained_per_season_MODEL_ESTIMATE:+.1f} runs per season if given the 2026 {E(u.phase)} balls of {E(u.replaces_weakest_rr_regular)} ({int(u.rr_regular_2026_phase_balls)} balls).</p>
</section>"""


CSS = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm;
  @bottom-left { content: "SupeRR Intelligence · independent analysis · not affiliated with Rajasthan Royals"; font: 7.5pt 'Segoe UI', sans-serif; color: #6B6F8A; }
  @bottom-right { content: "Page " counter(page) " of " counter(pages); font: 7.5pt 'Segoe UI', sans-serif; color: #6B6F8A; } }
@page :first { margin: 0; @bottom-left { content: none } @bottom-right { content: none } }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; font-size: 9.6pt; color: #1B1F3B; line-height: 1.45; margin: 0; }
h1 { font-family: Georgia, serif; font-size: 21pt; color: #1B1F3B; margin: 0 0 6px 0; border-bottom: 3px solid #C2185B; padding-bottom: 4px; page-break-before: always; }
h2 { font-size: 13pt; color: #4B2A99; margin: 16px 0 6px 0; } h3 { margin: 0; font-size: 13pt; } h4 { color: #4B2A99; margin: 10px 0 4px 0; font-size: 10.5pt; }
p { margin: 4px 0 8px 0; } ul { margin: 2px 0 8px 18px; padding: 0; } li { margin-bottom: 3px; }
figure { margin: 8px 0 12px 0; page-break-inside: avoid; } figure img { display: block; margin: 0 auto; }
figcaption { font-size: 8pt; color: #6B6F8A; margin-top: 4px; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px 0; font-size: 8.4pt; page-break-inside: avoid; }
th { background: #1B1F3B; color: white; text-align: left; padding: 4px 6px; font-weight: 600; }
td { padding: 3px 6px; border-bottom: 1px solid #E6E6EF; } tr:nth-child(even) td { background: #F7F6FB; }
table.dense { font-size: 8pt; } table.mini { font-size: 7.8pt; }
.small { font-size: 8pt; color: #6B6F8A; }
.cover { height: 297mm; background: linear-gradient(150deg, #1B1F3B 0%, #2B1A66 55%, #4B2A99 80%, #C2185B 130%); color: white; padding: 34mm 22mm; position: relative; }
.cover .kicker { color: #C9A227; letter-spacing: .18em; font-size: 9pt; text-transform: uppercase; }
.cover h1 { color: white; border: 0; font-size: 40pt; page-break-before: avoid; margin-top: 10mm; line-height: 1.05; }
.cover .sub { font-size: 14pt; color: #E3DAFF; margin-top: 6mm; max-width: 150mm; }
.cover .box { position: absolute; bottom: 30mm; left: 22mm; right: 22mm; border-top: 1px solid rgba(255,255,255,.35); padding-top: 6mm; font-size: 9pt; color: #E3DAFF; }
.cover .gold { color: #C9A227; font-weight: 600; }
.callout { background: #F4F0FB; border-left: 4px solid #4B2A99; padding: 8px 12px; border-radius: 4px; margin: 8px 0 12px 0; page-break-inside: avoid; }
.callout.pink { border-left-color: #C2185B; background: #FCEFF4; }
.flag { background: #F4F0FB; border-left: 4px solid #4B2A99; padding: 5px 9px; border-radius: 4px; font-size: 8.4pt; margin: 6px 0; }
.flag.warn { background: #FFF4E5; border-left-color: #C9A227; } .src { color: #6B6F8A; }
.profile { page-break-inside: avoid; border: 1px solid #E6E6EF; border-radius: 8px; padding: 10px 12px; margin: 10px 0 14px 0; }
.ph { display: flex; align-items: center; gap: 12px; } .ph .rk { background: #C2185B; color: white; font-weight: 700; font-size: 16pt; width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.ph .meta { font-size: 8pt; color: #6B6F8A; } .ph .score { margin-left: auto; font-size: 22pt; font-weight: 700; color: #4B2A99; } .ph .score span { font-size: 9pt; color: #6B6F8A; }
.kpis { display: flex; gap: 6px; margin: 6px 0; } .kpis div { flex: 1; background: #F7F6FB; border-radius: 6px; padding: 4px 6px; font-size: 7.4pt; color: #6B6F8A; }
.kpis b { display: block; font-size: 11.5pt; color: #1B1F3B; }
.two { display: flex; gap: 12px; align-items: flex-start; } .two > div { flex: 1; }
.grid2 { display: flex; gap: 14px; } .grid2 > div { flex: 1; }
.toc li { margin: 2px 0; } .pb { page-break-before: always; }
"""


def build() -> str:
    D = load()
    s, bat, bowl = D["summ"], D["rel"]["batting"], D["rel"]["bowling"]
    wp = D["wp"][D["wp"].split == "test"]
    w = lambda inn, m, k: wp[(wp.innings == inn) & (wp.model == m)][k].iat[0]
    cv = D["cv"].set_index("side")
    bt, bw = bat[bat["rank"] <= 10], bowl[bowl["rank"] <= 10]
    pm = D["pm"]
    H = []
    # ---------------- cover
    H.append(f"""<div class="cover"><div class="kicker">SupeRR Selector Season 2 · IPL 2027 Auction Analytics</div>
<h1>SupeRR Intelligence</h1><div class="sub">Who delivers when it matters? A pressure-based reliability and scouting study of IPL and T20I players, 2022–2026,
with a squad-intelligence view of how the most reliable players could strengthen Rajasthan Royals.</div>
<div class="box"><span class="gold">Methodology · Top 10 batters · Top 10 bowlers · RR squad fit</span><br/>
Data: official RR data pack ({int(s['deliveries']):,} deliveries, {int(s['matches_with_ball_data'])} matches, {s['date_from']} to {s['date_to']}) plus verified public sources.<br/>
Information cut-off: 14 November 2026 (before the IPL 2027 retention deadline of 17 November 2026).<br/>
Independent analytical submission. Not affiliated with or endorsed by Rajasthan Royals. No official logos are used.</div></div>""")
    # ---------------- executive summary
    H.append(f"""<h1>Executive summary</h1>
<div class="callout"><b>The brief:</b> identify the batters and bowlers who perform most reliably in high-pressure situations <i>compared with their usual level</i>,
explain the method, and show how each player could strengthen Rajasthan Royals for the IPL 2027 auction.</div>
<h2>Our answer in five points</h2><ul>
<li><b>Pressure is defined before the ball is bowled</b> as 50% <i>stakes</i> (how much the next ball can swing the win probability) and 50% <i>difficulty</i>
(scoreboard gap to era par, wickets lost, recent collapse, dot-ball squeeze, innings progress, closeness). The top 20% of balls, {int(s['high_pressure_deliveries']):,} in total, are HIGH pressure.</li>
<li><b>Players are judged against context, not raw averages.</b> Every ball is compared with what an average player would produce in the same situation. A ridge (Gaussian-prior) model then adjusts
for the quality of the opponents each player actually faced. This also calibrates IPL, full-member and associate cricket.</li>
<li><b>"Clutch" is only partly real.</b> After removing sampling noise, about {cv.at['batting', 'reliability_of_raw_delta']:.0%} of a batter's raw pressure-vs-normal difference is signal,
and only about {cv.at['bowling', 'reliability_of_raw_delta']:.0%} for bowlers. Pressure-only form does not predict later pressure form. Our score therefore blends performance delivered under pressure
with consistency, match impact, the shrunk own-baseline delta and underlying ability.</li>
<li><b>The lists contain only players RR can actually sign.</b> All of the unrestricted performance top 10s (Section 7) were under contract at other franchises.
We therefore rank only <b>RR-acquirable</b> players: not on any IPL 2026 squad, not Pakistani (no Pakistan player in the IPL since 2009), not Bangladeshi
(availability not reliable after the BCCI-directed release of Mustafizur Rahman), and not retired or banned. That leaves {int(bat.rr_acquirable.sum())} eligible batters and
{int(bowl.rr_acquirable.sum())} eligible bowlers.</li>
<li><b>RR's clearest needs are a finisher and a death bowler who hold up under pressure.</b> RR's death-overs batting ranked 7th–10th of 10 on run rate, boundary %, context value and wickets lost in both 2025 and 2026,
and in 2025 its death bowling conceded runs faster than any other team's. Opening batting is a strength (#1 in both seasons).</li></ul>
<div class="grid2"><div><h2>Top 10 batters</h2>{table(pd.DataFrame({'#': bt['rank'], 'Player': bt.player, 'Score': bt.score.round(0).astype(int), 'P(top10)': bt.p_top10.map('{:.0%}'.format)}))}</div>
<div><h2>Top 10 bowlers</h2>{table(pd.DataFrame({'#': bw['rank'], 'Player': bw.player, 'Score': bw.score.round(0).astype(int), 'P(top10)': bw.p_top10.map('{:.0%}'.format)}))}</div></div>
<p class="small">Score = 0–100 reliability composite (percentile among eligible players). P(top10) = share of 100 match-level bootstrap resamples in which the player stays in the top 10.
This is the share of resamples in which the player stays top 10 within the acquirable pool, a measure of uncertainty in the 2022–26 evidence and not a forecast.
The pool is small, so high values partly reflect limited competition.</p>
<h2>What RR gains</h2><ul>
<li><b>Uncapped Indian freshers (new):</b> using public Syed Mushtaq Ali Trophy data, the same method picks 5 fresher batters
({', '.join(D['ub'].player)}) and a 5-player bowling watchlist ({', '.join(D['uw'].player)}). Domestic batting form carries over to the IPL moderately; domestic bowling form did not, so the bowlers are low confidence.</li>
<li><b>Sikandar Raza</b> is the standout: #1 acquirable bowler and #5 batter, 97th percentile in death-overs batting, so one overseas slot covers two RR needs.</li>
<li><b>Death bowling:</b> Maheesh Theekshana (85th percentile at the death, the most IPL experience of the pool) and Adam Zampa (74th).
<b>Middle overs:</b> Daryl Mitchell and Mark Chapman (92nd percentile) with the bat.</li>
<li><b>Honest limits:</b> the acquirable pool is clearly weaker than the contracted elite, several players have little or no IPL record, and every one is overseas.
Releases on 17 Nov 2026 will add names; the pipeline re-runs in one command.</li></ul>""")
    # ---------------- contents
    H.append("""<h1>Contents</h1><ol class="toc">
<li>Competition context and research questions</li><li>Data, provenance and preparation</li><li>Defining pressure</li><li>Measuring performance fairly</li>
<li>Models and validation</li><li>The reliability score and its robustness</li><li>Top 10 batters: rankings and scouting profiles</li>
<li>Top 10 bowlers: rankings and scouting profiles</li><li>Players who narrowly missed</li><li>Uncapped Indian freshers (domestic T20)</li><li>Rajasthan Royals: squad intelligence and needs</li>
<li>How these players could strengthen Rajasthan Royals</li><li>Risks, limitations and auction feasibility</li><li>Final recommendations</li>
<li>References and source register</li><li>Technical appendix: formulas and reproducibility</li></ol>""")
    # ---------------- 1 context
    H.append(f"""<h1>1. Competition context and research questions</h1>
<p>SupeRR Selector Season 2 asks for two ordered top-10 lists (batters and bowlers) of the players who perform best under pressure, plus a report explaining how pressure was defined,
how ratings were built, how comparisons were made fair, the evidence for the top 10, and the reliability and limitations of the method.</p>
<div class="callout"><b>Central question.</b> Which batters and bowlers consistently deliver the most reliable performances in high-pressure T20 situations, relative to what the situation demands and to their own usual level?</div>
<ul><li><b>Two separate lists:</b> batting and bowling are evaluated by independent but symmetric pipelines.</li>
<li><b>Eligibility (decision):</b> IPL and T20I players are both eligible, with competition and opposition strength adjusted. A player must have ≥120 HIGH-pressure balls faced and ≥10 pressure innings (batting),
or ≥150 HIGH legal balls and ≥10 pressure spells (bowling). The player must also appear in the data in 2025–26 and must not have formally retired from the IPL.</li>
<li><b>Acquirability (decision):</b> the submitted lists contain only players RR can sign at the IPL 2027 auction. That means no IPL 2026 squad member
(including RR's own), no Pakistani players, no Bangladeshi players, and no retired or banned players. Ranks, P(top 10) and uncertainty are recomputed within that pool.</li>
<li><b>Two layers:</b> layer 1 is the pressure-reliability ranking that answers the competition. Layer 2 is RR squad fit. It is kept separate and never reorders the lists.</li></ul>
{img(FIG / 'report' / 'pipeline.png', 'Figure 1. Analytical pipeline. Purple: measurement and ranking (layer 1). Pink: verification and RR squad fit (layer 2).')}""")
    # ---------------- 2 data
    H.append(f"""<h1>2. Data, provenance and preparation</h1>
<p><b>Primary source:</b> the official RR data pack. It contains six CSVs (ball-by-ball, matches, competitions, teams, playing XIs, competition-team-player mapping) covering IPL 2022–2026,
bilateral and multi-nation T20Is, and two A-team tournaments. The original archive is preserved unmodified (SHA-256 recorded), and all work runs on a copy.</p>
{table(pd.DataFrame({'Item': ['Deliveries (regulation innings)', 'Matches with ball-by-ball data', 'IPL matches', 'T20I matches', 'Distinct batters / bowlers', 'Date range'],
                      'Value': [f"{int(s['deliveries']):,}", s['matches_with_ball_data'], s['ipl_matches'], s['t20i_matches'], f"{s['batters']} / {s['bowlers']}", f"{s['date_from']} to {s['date_to']}"]}))}
<h2>Audit findings that shaped the method</h2><ul>
<li><b>Complete and consistent:</b> all 16 matches without ball data were abandoned. Computed score margins match the official result in 806 of 816 checkable matches; the 10 exceptions are mostly D/L games.</li>
<li><b>A hidden no-ball code:</b> extras type <code>other</code> behaves as a no-ball. Treating it as legal would create 244 seven-ball overs. Legal balls exclude wides and both no-ball codes.</li>
<li><b>Attribution:</b> bowler runs exclude byes and leg-byes. Bowler wickets exclude run-outs, retirements and obstruction. "Retire Out" is not a batter failure.</li>
<li><b>Identity:</b> joins use player IDs only, because some names belong to different people (e.g. Rashid Khan of Afghanistan vs Nepal).</li>
<li><b>Mixed competition strength:</b> associate and A-team matches sit alongside IPL. This is handled by opponent adjustment, not by tier dummies (Section 4).</li>
<li><b>Not available:</b> fielder attribution (so no fielding metrics), venue names, and 39% of bowling speeds.</li></ul>
<p>Every pre-ball state variable uses only information available before the delivery: score, wickets in hand, legal balls left (respecting D/L-reduced innings), target, runs needed, and current and required rates.</p>""")
    # ---------------- 3 pressure
    H.append(f"""<h1>3. Defining pressure</h1>
<p>Pressure cannot be observed directly, so it must be defined. We built two independent candidates, found that each had a blind spot, and combined them.</p>
<h2>Stakes: the Leverage Index</h2><p>A win-probability model gives each team's chance of winning before every ball. The Leverage Index is the expected absolute swing in that probability from the next ball,
normalised so the average ball = 1. A last-over chase needing 4 off 2 balls reaches about 30. A one-sided chase sits near 0.</p>
<h2>Difficulty: a transparent rule-based index</h2>
{table(pd.DataFrame({'Component': ['Scoreboard gap (chase: required rate vs era par; batting first: projected shortfall vs par)', 'Wickets lost relative to balls used', 'Closeness of contest (from win probability)', 'Wickets in previous 12 balls (collapse)', 'Dot-ball share of previous 12 legal balls (squeeze)', 'Innings progress (share bowled)²'],
                      'Weight': ['25%', '20%', '20%', '15%', '10%', '10%']}))}
<div class="callout pink"><b>Why combine them?</b> Leverage alone put 92% of high-pressure balls in chases and none in first-innings death overs. The first-innings model is necessarily uncertain,
so its swings are small. Difficulty alone ignores stakes. Final: <b>pressure = 50% leverage percentile + 50% difficulty percentile</b>. HIGH = top 20%, LOW = bottom 50%.</div>
<p>A review (v1 → v2) fixed three flaws. Batting-first middle-overs collapses had been ignored (2.6% → 23.9% HIGH). There was a hard cliff between overs 15 and 16 (the largest jump fell from 39 to 5 percentage points).
Leverage also stepped at phase boundaries.</p>
{img(FIG / 'pressure_by_over_heatmap.png', 'Figure 2. Share of deliveries classed HIGH pressure, by over and innings (v2). Pressure builds smoothly through both innings.')}
{img(FIG / 'pressure_outcomes_by_definition.png', 'Figure 3. Batting outcomes by pressure band under three definitions. Dismissal rates rise under HIGH pressure. Raw strike rate is not the yardstick because HIGH balls cluster late in innings.', '92%')}
{img(FIG / 'pressure_sensitivity.png', 'Figure 4. Which choices move the definition? Rule-based weights barely matter; the leverage/difficulty blend is the key judgement call, so rankings are re-run under 30/70 and 70/30.', '80%')}""")
    # ---------------- 4 measurement
    H.append("""<h1>4. Measuring performance fairly</h1>
<h2>Step 1: expectation for every ball</h2><p>LightGBM models estimate the runs and dismissal probability an <i>average</i> player would produce in each situation: over, wickets, chase state,
bowling type and batter hand, plus the scoring environment. Separate models cover runs conceded and wickets for the bowler. <b>Player identity is never a feature.</b></p>
<div class="callout"><b>Fairness across competitions.</b> We deliberately did <i>not</i> add a competition-tier variable. That would make "average for an associate match" equal to "average for an IPL match"
and inflate players who mostly face weak opposition. Competition strength is calibrated in Step 3 through players and opponents who cross competitions. Only the scoring environment is modelled directly:
a rolling par built from earlier matches only, for IPL and for internationals. IPL par rose from 171 (2022) to 191 (2026).</div>
<h2>Step 2: value per ball</h2><p><b>Batting value</b> = (runs − expected runs) − C × (dismissed − expected dismissal probability). <b>Bowling value</b> is the mirror image.
C is the cost of a wicket in that situation: the expected remaining runs with w wickets in hand minus with w − 1, for the same overs left. A wicket early in the innings costs more than one in the last over.</p>
<h2>Step 3: opponent-adjusted ratings</h2><p>A ridge regression fits the per-ball value on batter and bowler effects together. Each player is rated net of the opponents actually faced.
The ridge penalty acts as a Gaussian prior: small samples shrink towards average. Penalties were tuned <i>out of time</i>, fitting on 2022–24 and scoring 2025–26. Two ratings feed the score:
<b>pressure performance</b> (a ridge on HIGH-pressure balls only) and <b>usual ability</b> (all balls).</p>
<h2>Step 4: own-baseline comparison</h2><p>Each player's HIGH-minus-ordinary difference is shrunk by empirical Bayes. The true spread of this difference is estimated by subtracting sampling noise from the observed spread.
Each player keeps the share of his raw difference that his sample size justifies.</p>""")
    # ---------------- 5 models
    xe = D["xe"]
    H.append(f"""<h1>5. Models and validation</h1>
<p>All models use a chronological split with matches kept whole: <b>train 2022–24, validate 2025, test 2026</b>. Models are chosen on validation only. Sophisticated models had to beat simple baselines.</p>
{img(FIG / 'report' / 'wp_validation.png', 'Figure 5. Win-probability models on the held-out 2026 season. Logistic regression beat LightGBM on both validation and test, because trees could not extrapolate to 2026 scoring levels.', '90%')}
{table(pd.DataFrame({'Model (2026 test)': ['Innings 1 · logistic', 'Innings 1 · base rate', 'Innings 2 · logistic', 'Innings 2 · base rate'],
                      'Brier': [f"{w(1, 'logit', 'brier'):.3f}", f"{w(1, 'constant(base rate)', 'brier'):.3f}", f"{w(2, 'logit', 'brier'):.3f}", f"{w(2, 'constant(base rate)', 'brier'):.3f}"],
                      'Log loss': [f"{w(1, 'logit', 'log_loss'):.3f}", f"{w(1, 'constant(base rate)', 'log_loss'):.3f}", f"{w(2, 'logit', 'log_loss'):.3f}", f"{w(2, 'constant(base rate)', 'log_loss'):.3f}"],
                      'AUC': [f"{w(1, 'logit', 'auc'):.3f}", "0.500", f"{w(2, 'logit', 'auc'):.3f}", "0.500"]}))}
<p><b>Expectation models</b> beat an innings × over baseline on RMSE in both 2025 and 2026 (runs per ball, 2026: {xe[(xe.model == 'bat_runs') & (xe.split == 'test') & (xe.kind.str.startswith('lightgbm'))].rmse.iat[0]:.3f}
vs {xe[(xe.model == 'bat_runs') & (xe.split == 'test') & (xe.kind.str.startswith('baseline'))].rmse.iat[0]:.3f}). Ball-level dismissals are close to random, so the wicket models only match the baseline.
A bug caught during validation: without the environment par, 2026 expected runs per ball came out at 1.35 against 1.51 actual. That would have flattered every 2026 batter.</p>
<h2>Is pressure performance a repeatable trait?</h2>
{img(FIG / 'report' / 'clutch_variance.png', 'Figure 6. Most of the apparent spread in pressure-vs-normal performance is noise, especially for bowlers.', '66%')}
<p>Player-level persistence from 2022–24 to 2025–26 tells the same story. Ordinary-situation value carries over (batting r ≈ 0.37–0.49). Pressure-only value does not (r ≈ 0), and adding pressure terms to the rating model
never improved out-of-time prediction. <b>Implication:</b> a raw "clutch" table would mostly rank noise. Our score uses opponent-adjusted pressure performance, consistency and impact (all shrunk by sample size),
anchored by underlying ability.</p>""")
    # ---------------- 6 score
    ws = D["ws"]
    H.append(f"""<h1>6. The reliability score and its robustness</h1>
{table(pd.DataFrame({'Component': ['Pressure performance', 'Consistency', 'Match impact', 'Vs own baseline', 'Usual ability'],
                      'Weight': ['35%', '20%', '20%', '15%', '10%'],
                      'Definition': ['Opponent-adjusted value on HIGH balls (ridge, shrunk)', 'Share of pressure innings/spells with value ≥ 0 (Beta-Binomial shrunk)',
                                     'Win Probability Added per HIGH ball (empirical Bayes)', 'HIGH minus ordinary value (empirical Bayes)', 'All-ball opponent-adjusted rating (best predictor)']}))}
<p>The score is the weighted mean of component <i>percentiles</i> among eligible players (0–100), reported as whole numbers to avoid false precision. The prompt's starting weights were treated as a hypothesis.
"Sample confidence" was dropped because shrinkage already uses sample size. "Role adaptability" moved to the squad-fit layer. Pressure performance and impact correlate (ρ ≈ 0.8), so a no-impact variant is also tested.</p>
<div class="grid2"><div><h2>Weight sensitivity (top-10 kept)</h2>{table(ws.assign(spearman_vs_final=ws.spearman_vs_final.round(3)).rename(columns={'side': 'Side', 'variant': 'Variant', 'top10_overlap': 'Top-10 kept', 'spearman_vs_final': 'Spearman'}), 'dense')}</div>
<div><h2>Pressure-definition sensitivity</h2>{table(D['ds'].assign(spearman_vs_final=D['ds'].spearman_vs_final.round(3)).rename(columns={'side': 'Side', 'variant': 'Variant', 'top10_overlap': 'Top-10 kept', 'spearman_vs_final': 'Spearman'}), 'dense')}
<p class="small">Each variant re-runs the whole pipeline on the same eligible pool. The definition matters more than the weights.</p></div></div>
{img(FIG / 'rank_uncertainty_top20.png', 'Figure 7. Top 20 per side. Dot = final rank; thick bar = bootstrap 90% rank interval (100 match-level resamples of the full pipeline); thin bar = range across pressure definitions.')}""")
    # ---------------- 7/8 tops + profiles
    for n, side, title, data in ((7, "batting", "Top 10 batters", bat), (8, "bowling", "Top 10 bowlers", bowl)):
        un = data.sort_values("overall_rank").head(10)
        ctx = table(pd.DataFrame({"Overall #": un.overall_rank.astype(int), "Player": un.player, "Score": un.score.round(0).astype(int),
                                  "Why not in the RR list": un.not_acquirable_reason.fillna("Acquirable: in the list")}), "dense")
        H.append(f"""<h1>{n}. {title} RR can sign: rankings and scouting profiles</h1>{top_table(data, side)}
<p class="small"># = rank within the RR-acquirable pool. The score is unchanged: a percentile among <i>all</i> eligible players, so it compares directly with the unrestricted ranking below.</p>
<h2>Context: the unrestricted top 10 (not signable by RR today)</h2>{ctx}
<p class="small">Value/100 HIGH = runs above context expectation per 100 HIGH-pressure balls (wicket-cost adjusted, before opponent adjustment). Raw SR/economy are descriptive.
HIGH-pressure balls cluster late in innings, so a lower raw rate can still be above what the situation demanded.</p>
{img(FIG / 'report' / f'components_{side}.png', f'Figure {n}a. Component percentiles for the top 10 {side}.', '78%')}
<p>Each profile shows the verified identity and IPL 2027 status, the evidence, a comparison with the two strongest <i>unselected</i> players in the same data role, a bootstrap verdict on whether the
difference is meaningful (clear ≥ 80%, moderate 65–80%, slight 55–65%, otherwise statistically indistinguishable), and how the player fits RR.</p>""")
        H.append("".join(profile(side, r, D) for _, r in data[data["rank"] <= 10].iterrows()))
    # ---------------- 9 near misses
    nm = D["near"]
    H.append(f"""<h1>9. Players who narrowly missed</h1>
<p>The next acquirable players, with the component that separated them from #10. Bowling has only two (the acquirable bowling pool is 12 players).
Where P(beats #10) is near 50%, the choice is statistically a coin-flip and is labelled as such in the profiles.</p>
{table(nm.rename(columns={'side': 'Side', 'rank': 'Rank', 'player': 'Player', 'role': 'Role', 'score': 'Score', 'gap_to_rank10': 'Gap to #10', 'p_top10': 'P(top10)',
                         'p_beats_rank10_bootstrap': 'P(beats #10)', 'main_shortfall_vs_rank10': 'Main shortfall vs #10', 'rank_range_across_defs': 'Rank range (defs)'}), 'dense')}
<p><b>Excluded despite statistical eligibility:</b> {', '.join(D['excl'].drop_duplicates('player').apply(lambda x: f"{x.player} ({x.reason})", axis=1))}.</p>""")
    # ---------------- 10 uncapped freshers
    ub, uw, tv = D['ub'], D['uw'], D['utv']
    def utab(t, side):
        cols = {'#': t['rank'], 'Player': t.player, 'Team': t.domestic_team, 'Age': t.age_at_auction, 'Role': t.role, 'Score': t.reliability_score.round(0).astype(int),
                'P(top 5)': t.p_top5_bootstrap.map(lambda v: '' if pd.isna(v) else f"{v:.0%}"), 'HIGH balls': t.high_pressure_balls_smat}
        if side == 'batting':
            cols['SR HIGH / LOW'] = t.sr_high.round(0).astype(int).astype(str) + ' / ' + t.sr_low.round(0).astype(int).astype(str)
        else:
            cols['Econ HIGH / LOW'] = t.economy_high.round(2).astype(str) + ' / ' + t.economy_low.round(2).astype(str)
        cols['Value/100 HIGH'] = t.value_per100_high.map(lambda v: f"{v:+.1f}")
        return table(pd.DataFrame(cols), 'dense')
    ex = pd.concat([x.assign(side=k) for k, x in D['uall'].items()])
    ex = ex[ex.data_pool & ~ex.fresher_ok].drop_duplicates('cricsheet_name')
    tvb = tv.set_index('side')
    H.append(f"""<h1>10. Uncapped Indian freshers (domestic T20)</h1>
<div class="callout pink"><b>Why this section:</b> every player RR can sign from the data pack is an overseas international, and the data pack holds no Indian domestic cricket.
Season 1's winning entry backed an uncapped Indian (Vignesh Puthur), whom RR then signed. We therefore added public ball-by-ball data for India's domestic T20 competition,
the <b>Syed Mushtaq Ali Trophy</b> (SMAT, Cricsheet, open-data licence), played entirely on Indian pitches.</div>
<h2>Method (same as the main lists)</h2><ul>
<li><b>Data:</b> SMAT 2020/21 to 2024/25, 272 matches, 62,850 balls. Cricsheet's latest season (2024/25) has only 8 matches, so most evidence is 2020/21 to 2023/24.</li>
<li><b>Pressure:</b> the same definition (50% leverage + 50% rule-based difficulty), using the data-pack win-probability model with SMAT's own scoring par. HIGH = top 20% of SMAT balls.</li>
<li><b>Fair comparison:</b> context-only expected runs and wickets fitted on SMAT (leave-one-season-out); one opponent-adjusted ridge fitted on data-pack and SMAT balls together,
linked through 152 players who appear in both, so domestic ratings sit on the IPL/T20I scale.</li>
<li><b>Score:</b> the same five components and weights; percentiles among all {int(D['uall']['batting'].eligible.sum())} eligible SMAT batters and {int(D['uall']['bowling'].eligible.sum())} bowlers
(capped players included). Thresholds are lower than the main lists (batting 40 HIGH balls and 4 pressure innings; bowling 48 and 4) because a SMAT season is about 7 league games; shrinkage handles small samples.</li>
<li><b>Pool rule:</b> Indian, never capped by India, not retired, not on any IPL 2026 squad, played SMAT 2023/24 or later, and <b>aged 30 or under at the auction</b> ("fresher").
Every pool player was checked on Wikipedia and the IPL 2026 personnel page (14 Nov 2026).</li>
<li><b>Uncertainty:</b> 60 match-level bootstrap resamples of SMAT; P(top 5) is the share in which the player stays in the top 5 of the fresher pool.</li></ul>
<h2>Does domestic form predict IPL form?</h2>
<p>For players with at least 150 balls in both SMAT and the data pack, a SMAT-only rating of usual ability correlates with the IPL/T20I rating at Spearman
<b>{tvb.loc['batting', 'spearman_smat_vs_pack_usual']:.2f}</b> for batting ({int(tvb.loc['batting', 'players'])} players) and
<b>{tvb.loc['bowling', 'spearman_smat_vs_pack_usual']:.2f}</b> for bowling ({int(tvb.loc['bowling', 'players'])} players). Domestic batting evidence is informative; domestic bowling evidence,
on this sample, is not. The bowling picks are therefore a <b>watchlist</b> for live scouting, not firm recommendations.</p>
<h2>Top 5 uncapped fresher batters</h2>{utab(ub, 'batting')}
<h2>Uncapped fresher bowlers: watchlist (low confidence)</h2>{utab(uw, 'bowling')}
{img(FIG / 'report' / 'uncapped_picks.png', 'Figure 10a. Uncapped Indian freshers: reliability score (percentile among all eligible SMAT players) and bootstrap P(top 5).')}
<h2>Rated highly but excluded by the pool rule (verified)</h2>
{table(pd.DataFrame({'Player': ex.full_name.fillna(ex.cricsheet_name), 'Team': ex.smat_team, 'SMAT score': ex.score.round(0).astype(int), 'Reason': ex.exclusion_reason}).sort_values('SMAT score', ascending=False).head(14), 'dense')}
<p class="small">Scores here are percentiles within SMAT, so they are not directly comparable with the main lists' scores. Uncapped players currently on IPL squads may be released on 17 Nov 2026 and would then join this pool on re-run.</p>""")
    # ---------------- 11 RR
    H.append(f"""<h1>11. Rajasthan Royals: squad intelligence and needs</h1>
<div class="callout pink"><b>Process:</b> understand the existing squad first, measure it with the <i>same</i> framework as every candidate, derive needs from evidence, and only then match candidates to needs.</div>
<h2>Squad status</h2><p>The 2026 squad (27 players) is verified against the data pack and official RR announcements. These record 13 retentions and the trades of Samson for Jadeja and Curran and of Rana for Ferreira.
RR entered the auction with ₹16.05 cr and one overseas slot. Parag captained; Curran was ruled out for the season. RR won 9 of 16 matches and lost Qualifier 2.
<b>The IPL 2027 squad is pending:</b> retentions are due 17 Nov 2026, and the mini-auction is on 16 Dec 2026 (Goa; maximum 25 players, 8 overseas).</p>
{img(FIG / 'report' / 'rr_phase_ranks.png', 'Figure 10a. RR rank among 10 IPL teams by phase, 2025–2026. Elite powerplay batting; weak death-overs batting; 2025 death bowling last on run rate, dot %, boundary % and value.')}
{img(FIG / 'report' / 'rr_players_pressure.png', 'Figure 10b. RR players rated with the same pressure framework as all candidates. Most of the middle order and death bowlers sit below the pool median under pressure.')}
{table(rr_bat_table(D['aud']), 'dense')}
{img(FIG / 'report' / 'rr_priorities.png', 'Figure 10c. Recruitment priorities. Severity from 2025–26 phase ranks; coverage from the best eligible RR player in the role.', '85%')}
<h2>Evidence-led requirements</h2><ol>
<li><b>Finisher / middle-order batter reliable under pressure (High, {pm.set_index('requirement').at['Death-overs / finishing batting', 'priority_score']:.0f}).</b> Death batting ranked 7th–10th on run rate, boundary %, context value and wickets lost in both seasons (dot-ball % was mid-table).
In 2026 Jadeja (SR 140.5), Jurel (150.0) and Dubey (146.3) were well below the league death SR of 169.4. Only Ferreira was above par.</li>
<li><b>Death bowler reliable under pressure (High, {pm.set_index('requirement').at['Death-overs bowling', 'priority_score']:.0f}).</b> In 2025 RR ranked last of 10 on death-overs run rate conceded, dot %, boundary % and context value (9th on wickets). In 2026, Sandeep Sharma conceded 13.70 an over and Deshpande 12.38 at the death.</li>
<li><b>Middle-overs batting (High, {pm.set_index('requirement').at['Middle-overs batting', 'priority_score']:.0f})</b> and <b>middle-overs bowling control (Medium)</b>. Dot % ranked 10th and 9th; Jadeja is strong, but the second spin option is weak under pressure.</li>
<li><b>Not a need:</b> opening batting. RR ranked #1 in the league in both seasons (Sooryavanshi SR 234 in the 2026 powerplay).</li></ol>""")
    # ---------------- 11 strengthen RR
    rec = D["rec"]
    rt = rec[["side", "reliability_rank", "player", "indian_or_overseas", "rr_need_addressed", "squad_fit_score", "top_alternative", "p_beats_top_alternative",
              "uplift_runs_per_season_MODEL_ESTIMATE", "recommendation_tier"]].rename(columns={
        "side": "Side", "reliability_rank": "Rank", "player": "Player", "indian_or_overseas": "Ind/Ovs", "rr_need_addressed": "RR need", "squad_fit_score": "Fit",
        "top_alternative": "Top alternative", "p_beats_top_alternative": "P(beats alt.)", "uplift_runs_per_season_MODEL_ESTIMATE": "Uplift* (runs)", "recommendation_tier": "Tier"})
    rt["Fit"] = rt["Fit"].round(0).astype(int)
    H.append(f"""<h1>12. How these players could strengthen Rajasthan Royals</h1>
<p>Squad fit is a separate layer, scored as follows:</p>
<ul><li>50%: RR's priority for the player's best-fit need.</li>
<li>35%: the player's phase evidence.</li>
<li>15%: roster slot (Indian 1.0, overseas 0.5). An overseas signing must displace an overseas regular in a maximum-4 XI. This is an assumption, so scores are also reported without it.</li></ul>
<h2>Squad-building implications</h2><ul>
<li><b>Sikandar Raza is the one primary target</b> (squad fit 82): 97th percentile in death-overs batting, plus RR's #1 acquirable bowler for the middle overs. One overseas slot covers two needs.</li>
<li><b>Finishing batting (RR's top need):</b> after Raza, Ibrahim Zadran (58th percentile at the death) and Ryan Burl (53rd) are the realistic options. The pool is thin here.</li>
<li><b>Middle-overs batting:</b> Mark Chapman (92nd percentile, squad fit 70) and Daryl Mitchell (66th, the most IPL experience among the batters).</li>
<li><b>Death bowling:</b> Maheesh Theekshana (85th percentile, with 39% of balls bowled in the IPL, including RR in 2025) and Adam Zampa (74th).</li>
<li><b>All acquirable players are overseas.</b> RR can hold at most 8, and the XI takes 4. Realistically one to three of these can be signed, so prioritise multi-need value (Raza) and the top need (death overs).</li>
<li><b>Indian slots:</b> the data pack holds no Indian domestic cricket, so uncapped Indians are assessed separately from public SMAT data (Section 10). Rahul Buddhi and Narayan Jagadeesan are the clearest uncapped batters.</li></ul>{img(FIG / 'report' / 'fit_vs_reliability.png', 'Figure 11. Reliability rank (layer 1) vs RR squad fit (layer 2). Primary targets sit right of the dotted line.')}
{table(rt, 'dense')}
<p class="small">*Hypothetical model estimate, not a forecast: the player's phase value minus that of RR's weakest 2026 regular in the phase, times that regular's 2026 balls. It ignores role interactions and opposition.</p>
""")
    # ---------------- 12 risks
    H.append("""<h1>13. Risks, limitations and auction feasibility</h1><h2>Player-specific risks (verified)</h2><ul>
<li><b>Limited IPL evidence:</b> six of the ten batters (Campher, Chapman, Dockrell, Ibrahim Zadran, Tector, Burl) and Chase, Ngarava and Adair have no IPL balls in the data.
Their ratings rest on T20Is against full-member and associate sides, opponent-adjusted.</li>
<li><b>Age at auction</b> (not scored): Raza 40, Adil Rashid 38, Neesham 36.</li>
<li><b>Recency:</b> Obed McCoy's last T20I was in September 2025.</li>
<li><b>Close calls:</b> bowlers #9 and #10 (Alzarri Joseph, Mark Adair) are statistically indistinguishable from Ish Sodhi and Fazalhaq Farooqi.</li>
<li><b>Registration:</b> a player must register for the auction. The final list is expected around 3 Dec 2026.</li>
<li><b>Exclusion choices:</b> Bangladeshi players are excluded as unreliable to acquire. This is a judgement, since no formal rule was published (S12). Brook is excluded because his ban's coverage of 2027 is unclear (S14).</li></ul>
<h2>Method limitations</h2><ul>
<li>Pressure is unobserved; the definition is a reasoned choice, stress-tested in Section 6.</li>
<li>The data covers 2022–26, IPL plus bilateral T20I plus A-team. There are no domestic leagues, no fielding attribution and no venue names.</li>
<li>Openers face few HIGH balls, so elite openers (e.g. Jaiswal) can fall below eligibility. This is a property of the definition, not evidence of weakness.</li>
<li>Bootstrap intervals describe measurement uncertainty in past performance, not future probabilities. Uplift estimates are hypothetical.</li>
<li>The 2026 win-probability calibration is weaker than 2025, but WP is used to measure stakes, not to predict results.</li></ul>
<h2>Auction feasibility</h2><p>IPL 2027 rules as reported (SportsTak, citing a BCCI communique of 2 Nov 2026): mini-auction, no retention cap, no Right-to-Match, maximum 25 players and 8 overseas.
The IPL 2027 purse is not verified, so <b>no financial claims are made</b>. The lists are built from players not under contract today; players released on 17 Nov 2026 will join the pool, and the pipeline re-runs to include them.</p>""")
    # ---------------- 13 final
    H.append(f"""<h1>14. Final recommendations</h1>
<div class="grid2"><div><h2>Submitted top 10 batters</h2>{table(pd.DataFrame({'#': bt['rank'], 'Player': bt.player, 'Score': bt.score.round(0).astype(int)}))}</div>
<div><h2>Submitted top 10 bowlers</h2>{table(pd.DataFrame({'#': bw['rank'], 'Player': bw.player, 'Score': bw.score.round(0).astype(int)}))}</div></div>
<div class="grid2"><div><h2>Uncapped fresher batters</h2>{table(pd.DataFrame({'#': D['ub']['rank'], 'Player': D['ub'].player, 'Age': D['ub'].age_at_auction}))}</div>
<div><h2>Uncapped fresher bowlers (watchlist)</h2>{table(pd.DataFrame({'#': D['uw']['rank'], 'Player': D['uw'].player, 'Age': D['uw'].age_at_auction}))}</div></div>
<div class="callout"><b>For Rajasthan Royals.</b> First target <b>Sikandar Raza</b> (finishing bat plus middle-overs bowling in one overseas slot). For death bowling, target
<b>Maheesh Theekshana</b>, then Adam Zampa. For middle-overs batting depth, Mark Chapman or Daryl Mitchell. Keep the opening pair, RR's clearest strength.
For Indian slots, scout <b>{D['ub'].player.iloc[0]}</b> and <b>{D['ub'].player.iloc[1]}</b> first among uncapped batters; treat the uncapped bowlers as a live-scouting watchlist.
Re-run the selection when the 17 Nov releases are published, because better-rated players may enter the pool.</div>
<h2>Conclusion</h2><p>Reliable pressure performance is real but noisy. The defensible way to find it is to define pressure from the match situation, judge players against context and opponents, shrink small samples,
and report how sure we are. On that basis the lists above are the most reliable performers under pressure in the 2022–26 data <i>among players RR can actually sign</i>. Their value to RR is clearest where RR has been weakest: finishing innings and defending at the death.</p>""")
    # ---------------- references
    H.append(f"""<h1>15. References and source register</h1><div class="small">{md_table(RESEARCH_DIR / 'RESEARCH_SOURCE_REGISTER.md')}</div>
<h2>Methodological references</h2><ul class="small">
<li>Tango, T. M., Lichtman, M. G., Dolphin, A. E. (2007). <i>The Book: Playing the Percentages in Baseball</i>: Leverage Index and win-probability-added concepts adapted here.</li>
<li>Rosenbaum, D. (2004). Measuring how NBA players help their teams win: adjusted plus-minus. The ridge (regularised) variant is used here for opponent adjustment.</li>
<li>Efron, B. &amp; Morris, C. (1975). Data analysis using Stein's estimator and its generalizations. <i>JASA</i>: empirical-Bayes shrinkage.</li>
<li>Duckworth, F. C. &amp; Lewis, A. J. (1998). A fair method for resetting the target in interrupted one-day cricket matches. <i>JORS</i>: the resources concept behind the wicket-cost table.</li></ul>""")
    # ---------------- appendix
    H.append("""<h1>16. Technical appendix: formulas and reproducibility</h1><ul>
<li><b>Legal ball:</b> extras type ∉ {wide, Overstep, other}. <b>Ball faced:</b> not a wide. <b>Bowler runs:</b> bat runs + wide/no-ball extras.</li>
<li><b>Leverage:</b> LI = Σ<sub>o</sub> p(o | tier, over) · |WP(state after o) − WP(state)| ÷ mean over all balls, with outcomes o ∈ {0, 1, 2, 3, 4, 6, wicket, wide}.</li>
<li><b>Pressure score:</b> percentile(0.5 · leverage percentile + 0.5 · RPI percentile). The leverage percentile is computed within each over for innings 1 and within the innings for innings 2. HIGH = top 20%.</li>
<li><b>Value per ball:</b> batting v = (r − x̂r) − C(s) · (out − p̂out); bowling v = (x̂c − c) + C(s) · (wkt − p̂wkt). C(s) = E[remaining | overs left, w] − E[remaining | overs left, w − 1].</li>
<li><b>Ratings:</b> v = μ + a<sub>player</sub> + d<sub>player</sub>·HIGH + b<sub>opponent</sub> + e<sub>opponent</sub>·HIGH, with a ridge penalty (α = 1000) tuned out of time. Pressure-only ridge on HIGH balls (α = 2000).</li>
<li><b>Empirical Bayes delta:</b> δ̂ = δ<sub>raw</sub> · τ² ÷ (τ² + s²<sub>i</sub>), where τ² = Var(δ<sub>raw</sub>) − mean(s²).</li>
<li><b>Consistency:</b> (good + 10p₀) ÷ (n + 10). Score = Σ w<sub>k</sub> · percentile<sub>k</sub> × 100.</li>
<li><b>Reproduce:</b> see README. The pipeline is <code>src/</code> (data → models → features → scouting → reporting), with 56 automated tests, fixed seed 2027, and leave-one-year-out cross-fitting for all production predictions.</li></ul>
<p class="small">Generated by <code>src/reporting/build_report.py</code>. Every table and player figure is read from pipeline outputs in <code>reports/</code> and <code>research/</code>.</p>""")
    return f'<!doctype html><html><head><meta charset="utf-8"><title>SupeRR Intelligence: Final Report</title><style>{CSS}</style></head><body>{"".join(H)}</body></html>'


def md_table(path: Path) -> str:
    """Render the first markdown table in a file as HTML (for the source register)."""
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("|")]
    rows, out = [], []
    for l in lines:
        cells = [c.strip() for c in l.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    head, body = rows[0], [r for r in rows[1:] if len(r) == len(rows[0])]
    keep = [i for i, h in enumerate(head) if h in ("ID", "Source", "URL", "Published / updated", "Accessed", "Type")]
    h = "".join(f"<th>{E(head[i])}</th>" for i in keep)
    b = "".join("<tr>" + "".join(f"<td style='word-break:break-all'>{E(r[i])}</td>" for i in keep) + "</tr>" for r in body)
    return f"<table class='dense'><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def to_pdf(html_path: Path, pdf_path: Path) -> None:
    import tempfile
    import time
    exe = next(b for b in BROWSERS if b.exists())
    prof = Path(tempfile.gettempdir()) / "superr_pdf_profile"  # isolated profile (works even if a normal browser is open)
    pdf_path.unlink(missing_ok=True)
    subprocess.run([str(exe), "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={prof}",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()], timeout=180, capture_output=True)
    for _ in range(120):  # the browser may hand off to a child process; wait for the file to be complete
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            size = pdf_path.stat().st_size
            time.sleep(1)
            if pdf_path.stat().st_size == size:
                return
        time.sleep(1)
    raise RuntimeError("PDF was not produced")


if __name__ == "__main__":
    hp = REPORTS_DIR / "final_report.html"
    hp.write_text(build(), encoding="utf-8")
    to_pdf(hp, REPORTS_DIR / "final_report.pdf")
    from pypdf import PdfReader
    print("pages:", len(PdfReader(REPORTS_DIR / "final_report.pdf").pages))
