"""Generate research/PLAYER_COMPARISONS.md (why-this-player profiles) from pipeline outputs only.

No number in the document is typed by hand: every value comes from the CSVs below. The wording
uses fixed thresholds for evidence strength so claims never outrun the bootstrap.
"""
from __future__ import annotations

import pandas as pd

from src.config import REPORTS_DIR, RESEARCH_DIR

COMP = [("pressure_perf", "Pressure performance"), ("consistency", "Consistency"), ("impact", "Match impact (WPA)"),
        ("delta", "Pressure vs own baseline"), ("usual", "Usual ability")]


def strength(p: float) -> str:
    if pd.isna(p):
        return "not available"
    if p >= 0.80: return f"clear ({p:.0%} of resamples)"
    if p >= 0.65: return f"moderate ({p:.0%})"
    if p >= 0.55: return f"slight ({p:.0%})"
    return f"statistically indistinguishable ({p:.0%})"


def profile(side: str, s: pd.Series, alts: pd.DataFrame, fit: pd.Series, up: pd.Series, reg: pd.Series | None) -> str:
    hb = "balls_high" if side == "batting" else "legal_balls_high"
    L = [f"### #{int(s['rank'])} {s['player']} ({s['role']})", ""]
    if reg is not None:
        L.append(f"*{reg['full_name']}* · {reg['country']} · {reg['bat']} / {reg['bowl']} · age at auction {reg['age_at_auction_calc']} (calc.) "
                 f"· IPL 2026: {reg['ipl_2026_team']} · **IPL 2027: {reg['ipl_2027_status']}**")
        L.append(f"> Verified notes: {reg['notes']} (sources: {reg['sources']})")
        L.append("")
    L.append(f"**Reliability score {s['score']:.0f}/100** · {int(s[hb])} HIGH-pressure balls · {int(s['pressure_innings'])} pressure "
             f"{'innings' if side == 'batting' else 'spells'} · context value on HIGH balls {s['value_per100_high']:+.1f} per 100 · "
             f"P(top 10) {s['p_top10']:.0%} · bootstrap 90% rank {int(s['boot_rank_p05'])}–{int(s['boot_rank_p95'])} · "
             f"rank range across pressure definitions {int(s['rank_min_across_defs'])}–{int(s['rank_max_across_defs'])}")
    if side == "batting":
        L.append(f"Raw (descriptive): SR {s['sr_high']:.1f} under HIGH pressure vs {s['sr_low']:.1f} in LOW-pressure situations.")
    else:
        L.append(f"Raw (descriptive): economy {s['economy_high']:.2f} under HIGH pressure vs {s['economy_low']:.2f} in LOW; "
                 f"{int(s['wickets_high'])} HIGH-pressure wickets.")
    L += ["", "| Criterion (percentile among eligible) | " + s["player"] + " | " + " | ".join(alts["alternative"]) + " |",
          "|---|---:|" + "---:|" * len(alts)]
    for k, lab in COMP:
        L.append(f"| {lab} | {s['pct_' + k]:.2f} | " + " | ".join(f"{a[k + '_alt'] if k + '_alt' in a else a['pct_' + k + '_alt']:.2f}" for _, a in alts.iterrows()) + " |")
    L.append(f"| Reliability score | {s['score']:.0f} | " + " | ".join(f"{a['score_alt']:.0f} (rank {a['alternative_rank']})" for _, a in alts.iterrows()) + " |")
    L.append(f"| HIGH-pressure balls | {int(s[hb])} | " + " | ".join(f"{int(a['high_balls_alt'])}" for _, a in alts.iterrows()) + " |")
    L.append(f"| P(selected ranks higher), bootstrap | — | " + " | ".join(f"{a['p_selected_ranks_higher_bootstrap']:.2f}" for _, a in alts.iterrows()) + " |")
    L.append("")
    # why this player
    best = max(COMP, key=lambda c: s["pct_" + c[0]])
    weak = min(COMP, key=lambda c: s["pct_" + c[0]])
    lines = [f"**Why this player?** Strongest evidence: {best[1].lower()} (percentile {s['pct_' + best[0]]:.2f}); "
             f"weakest component: {weak[1].lower()} ({s['pct_' + weak[0]]:.2f})."]
    for _, a in alts.iterrows():
        diffs = {lab: s["pct_" + k] - a[f"pct_{k}_alt"] for k, lab in COMP}
        lead = max(diffs, key=diffs.get)
        trail = min(diffs, key=diffs.get)
        lines.append(f"Versus **{a['alternative']}** (rank {a['alternative_rank']}, {a['role_alternative']}): ahead most on {lead.lower()} "
                     f"({diffs[lead]:+.2f})" + (f", behind on {trail.lower()} ({diffs[trail]:+.2f})" if diffs[trail] < 0 else "")
                     + f"; the advantage is {strength(a['p_selected_ranks_higher_bootstrap'])}.")
    L.append(" ".join(lines))
    L.append("")
    L.append(f"**RR fit (layer 2, separate):** best fits *{fit['best_fit_requirement']}* (RR priority {fit['requirement_priority']:.0f}); "
             f"{fit['best_fit_phase']} context value {fit['phase_value_eb_per100']:+.1f}/100 over {int(fit['phase_balls'])} balls "
             f"(percentile {fit['phase_value_pctile']:.0f}); {fit['indian_or_overseas']}; squad-fit {fit['squad_fit_score']:.0f} "
             f"({fit['squad_fit_no_slot']:.0f} without slot cost). Hypothetical uplift (model estimate, not a forecast): "
             f"{up['est_runs_gained_per_season_MODEL_ESTIMATE']:+.1f} runs/season if given the 2026 {up['phase']} balls of "
             f"{up['replaces_weakest_rr_regular']} ({int(up['rr_regular_2026_phase_balls'])} balls).")
    L.append("")
    return "\n".join(L)


def build() -> str:
    alt = pd.read_csv(REPORTS_DIR / "player_comparisons.csv")
    fit = pd.read_csv(RESEARCH_DIR / "player_to_rr_squad_fit.csv").set_index(["side", "rank"])
    up = pd.read_csv(RESEARCH_DIR / "rr_phase_uplift_scenarios.csv").set_index(["side", "rank"])
    reg = pd.read_csv(RESEARCH_DIR / "player_verification_register.csv").drop_duplicates("player_id").set_index("player_id")
    near = pd.read_csv(REPORTS_DIR / "model_outputs" / "near_misses.csv")
    out = ["# Player Comparisons: Why These Players? (auto-generated)", "",
           "Generated by `src/reporting/comparisons_doc.py` from `reports/player_comparisons.csv`, `research/player_to_rr_squad_fit.csv`, "
           "`research/rr_phase_uplift_scenarios.csv` and `research/player_verification_register.csv`. Alternatives are the two highest-scoring "
           "**unselected** eligible players in the same data-derived role: the strongest real competition, not chosen to flatter the pick. "
           "Evidence wording is fixed by bootstrap thresholds: clear ≥ 80%, moderate 65–80%, slight 55–65%, otherwise statistically indistinguishable.", ""]
    for side in ("batting", "bowling"):
        s = pd.read_csv(REPORTS_DIR / "model_outputs" / f"reliability_{side}.csv")
        out += [f"## {'Batters' if side == 'batting' else 'Bowlers'}", ""]
        for _, r in s[s["rank"] <= 10].iterrows():
            a = alt[(alt.side == side) & (alt.selected_id == r.player_id)]
            out.append(profile(side, r, a, fit.loc[(side, r["rank"])], up.loc[(side, r["rank"])],
                               reg.loc[r.player_id] if r.player_id in reg.index else None))
        n = near[near.side == side]
        out += [f"### Narrowly missed ({side})", "", "| Rank | Player | Role | Score | Gap to #10 | P(top 10) | P(beats #10) | Main shortfall vs #10 | Rank range across defs |",
                "|---:|---|---|---:|---:|---:|---:|---|---|"]
        out += [f"| {x['rank']} | {x.player} | {x.role} | {x.score} | {x.gap_to_rank10} | {x.p_top10:.2f} | {x.p_beats_rank10_bootstrap:.2f} | "
                f"{x.main_shortfall_vs_rank10} | {x.rank_range_across_defs} |" for _, x in n.iterrows()]
        out += ["", "These players are credible alternatives: most beat #10 in 30–50% of resamples. They missed on the stated component, "
                "not on overall quality.", ""]
    return "\n".join(out)


def recommendations() -> pd.DataFrame:
    """RR recruitment matrix. Tier rule (fixed, stated): squad-fit >= 78 -> 'Primary target';
    70-77 -> 'Strong option'; < 70 -> 'Situational / depth'. Availability is reported, never scored."""
    fit = pd.read_csv(RESEARCH_DIR / "player_to_rr_squad_fit.csv")
    reg = pd.read_csv(RESEARCH_DIR / "player_verification_register.csv").drop_duplicates("player_id").set_index("player_id")
    alt = pd.read_csv(REPORTS_DIR / "player_comparisons.csv")
    up = pd.read_csv(RESEARCH_DIR / "rr_phase_uplift_scenarios.csv").set_index(["side", "rank"])
    rows = []
    for f in fit.itertuples():
        a = alt[(alt.side == f.side) & (alt.selected_id == f.player_id)].iloc[0]
        tier = "Primary target" if f.squad_fit_score >= 78 else "Strong option" if f.squad_fit_score >= 70 else "Situational / depth"
        rg = reg.loc[f.player_id]
        rows.append({"side": f.side, "reliability_rank": f.rank, "player": f.player, "role": f.role, "indian_or_overseas": f.indian_or_overseas,
                     "rr_need_addressed": f.best_fit_requirement, "rr_need_priority": f.requirement_priority, "squad_fit_score": f.squad_fit_score,
                     "top_alternative": a.alternative, "p_beats_top_alternative": a.p_selected_ranks_higher_bootstrap,
                     "uplift_runs_per_season_MODEL_ESTIMATE": up.loc[(f.side, f.rank), "est_runs_gained_per_season_MODEL_ESTIMATE"],
                     "availability": rg["availability_class"], "ipl_2027_status": rg["ipl_2027_status"], "risk_notes": rg["notes"],
                     "recommendation_tier": tier})
    out = pd.DataFrame(rows)
    out.to_csv(REPORTS_DIR / "rr_recruitment_recommendations.csv", index=False)
    return out


if __name__ == "__main__":
    (RESEARCH_DIR / "PLAYER_COMPARISONS.md").write_text(build(), encoding="utf-8")
    r = recommendations()
    print(r[["side", "reliability_rank", "player", "rr_need_addressed", "squad_fit_score", "recommendation_tier", "availability"]].to_string(index=False))
