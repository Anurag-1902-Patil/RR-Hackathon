"""Rajasthan Royals squad intelligence: verified squad database, player pressure audit (same
framework as all candidates, no preferential treatment), and team phase performance vs league.

Squad status sources (accessed 2026-11-14, see research/RESEARCH_SOURCE_REGISTER.md):
  S1 rajasthanroyals.com retention list (15 Nov 2025)
  S2 rajasthanroyals.com trade announcement (15 Nov 2025)
  S3 rajasthanroyals.com IPL 2026 auction purse/slots/squad (15 Dec 2025)
  S4 Wikipedia "2026 Rajasthan Royals season" (replacements; secondary source)
  S5 SportsTak (2 Nov 2026): IPL 2027 retention deadline extended to 17 Nov 2026
  D  RR data pack competition_team_player_mapping / playing_eleven (IPL 2026)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import FEATURES_DIR, PROCESSED_DIR, REPORTS_DIR, RESEARCH_DIR, RR_TEAM_ID

RETAINED_2026 = ["Dhruv Jurel", "Jofra Archer", "Kwena Maphaka", "Lhuan Pretorius", "Nandre Burger", "Riyan Parag",
                 "Sandeep Sharma", "Shimron Hetmyer", "Shubham Dubey", "Tushar Deshpande", "Vaibhav Sooryavanshi",
                 "Yashasvi Jaiswal", "Yudhvir Singh"]
TRADED_IN_2026 = {"Ravindra Jadeja": "Trade from CSK (Samson trade)", "Sam Curran": "Trade from CSK (Samson trade)",
                  "Donovan Ferreira": "Trade from DC (Nitish Rana trade)"}
REPLACEMENTS_2026 = {"Dasun Shanaka": "Replacement for Sam Curran (S4)", "Emanjot Singh Chahal": "Replacement for Ravi Singh (S4)"}
OVERSEAS = {"Jofra Archer", "Kwena Maphaka", "Lhuan Pretorius", "Nandre Burger", "Shimron Hetmyer", "Sam Curran",
            "Donovan Ferreira", "Adam Milne", "Dasun Shanaka"}  # S3 (7 overseas pre-auction, 1 slot) + auction/replacement
STATUS_2027 = "Pending: IPL 2027 retention list not yet published (deadline 17 Nov 2026, S5)"


def squad_database() -> pd.DataFrame:
    pm = pd.read_parquet(PROCESSED_DIR / "player_map.parquet")
    xi = pd.read_parquet(PROCESSED_DIR / "playing_xi.parquet")
    m = pd.read_parquet(PROCESSED_DIR / "matches.parquet")[["match_id", "comp_name", "year"]]
    sq = pm[(pm.team_id == RR_TEAM_ID) & (pm.comp_name == "IPL 2026")][["player_id", "player_name"]].drop_duplicates()
    apps = (xi[(xi.team_id == RR_TEAM_ID) & xi.is_played].merge(m, on="match_id")
              .query("comp_name.str.startswith('IPL')", engine="python")
              .groupby(["player_id", "year"]).size().unstack(fill_value=0).add_prefix("rr_apps_"))
    wk = xi[(xi.team_id == RR_TEAM_ID) & xi.is_played & xi.is_wk.eq(True)].merge(m, on="match_id").query("year == 2026").groupby("player_id").size()
    sq = sq.merge(apps, left_on="player_id", right_index=True, how="left").fillna(0)
    sq["kept_wicket_2026"] = sq["player_id"].map(wk).fillna(0).astype(int)

    def acq(n):
        if n in RETAINED_2026: return "Retained for IPL 2026 (S1)"
        if n in TRADED_IN_2026: return TRADED_IN_2026[n] + " (S2/S3)"
        if n in REPLACEMENTS_2026: return REPLACEMENTS_2026[n]
        return "IPL 2026 auction purchase (S3/S4; inferred: in IPL 2026 RR mapping, not retained/traded)"
    sq["acquisition_2026"] = sq["player_name"].map(acq)
    sq["indian_or_overseas"] = np.where(sq["player_name"].isin(OVERSEAS), "Overseas", "Indian")
    sq["overseas_source"] = "S3 slot count + D national side"
    sq["status_2026"] = "In IPL 2026 RR squad (D, S3/S4)"
    sq["status_2027"] = STATUS_2027
    return sq.sort_values("rr_apps_2026", ascending=False).reset_index(drop=True)


def player_audit(sq: pd.DataFrame) -> pd.DataFrame:
    """Same metrics and percentiles as the candidate pool; eligibility flags kept honest."""
    T = FEATURES_DIR / "player_tables"
    bat, bowl = pd.read_parquet(T / "batting.parquet"), pd.read_parquet(T / "bowling.parquet")
    rb = pd.read_csv(REPORTS_DIR / "model_outputs" / "reliability_batting.csv").set_index("player_id")
    rw = pd.read_csv(REPORTS_DIR / "model_outputs" / "reliability_bowling.csv").set_index("player_id")
    elig_b, elig_w = bat[bat.eligible], bowl[bowl.eligible]
    pctl = lambda s, col, v: (s[col] < v).mean() * 100 if pd.notna(v) else np.nan
    rows = []
    for _, p in sq.iterrows():
        i = p.player_id
        r = {"player_id": i, "player": p.player_name}
        if i in bat.index:
            b = bat.loc[i]
            r.update({"bat_role": b.role, "bat_balls": b.balls, "bat_balls_high": b.balls_high, "bat_runs": b.runs,
                      "bat_sr": round(b.sr, 1), "bat_sr_high": round(b.sr_high, 1) if pd.notna(b.sr_high) else np.nan,
                      "bat_value100_high": round(b.value_per100_high, 2) if pd.notna(b.value_per100_high) else np.nan,
                      "bat_usual100": round(b.usual_per100, 2), "bat_pressure_perf100": round(b.pressure_perf_per100, 2),
                      "bat_usual_pctile_vs_eligible": round(pctl(elig_b, "usual_per100", b.usual_per100), 0),
                      "bat_pressure_pctile_vs_eligible": round(pctl(elig_b, "pressure_perf_per100", b.pressure_perf_per100), 0),
                      "bat_eligible": bool(b.eligible), "bat_reliability_rank": rb["rank"].get(i, np.nan),
                      "bat_reliability_score": round(rb["score"].get(i, np.nan), 0)})
        if i in bowl.index:
            w = bowl.loc[i]
            r.update({"bowl_role": w.role, "bowl_type": w.bowling_type, "bowl_balls": w.legal_balls, "bowl_balls_high": w.legal_balls_high,
                      "bowl_wkts": w.wickets, "bowl_econ": round(w.economy, 2),
                      "bowl_econ_high": round(w.economy_high, 2) if pd.notna(w.economy_high) else np.nan,
                      "bowl_value100_high": round(w.value_per100_high, 2) if pd.notna(w.value_per100_high) else np.nan,
                      "bowl_usual100": round(w.usual_per100, 2), "bowl_pressure_perf100": round(w.pressure_perf_per100, 2),
                      "bowl_usual_pctile_vs_eligible": round(pctl(elig_w, "usual_per100", w.usual_per100), 0),
                      "bowl_pressure_pctile_vs_eligible": round(pctl(elig_w, "pressure_perf_per100", w.pressure_perf_per100), 0),
                      "bowl_eligible": bool(w.eligible), "bowl_reliability_rank": rw["rank"].get(i, np.nan),
                      "bowl_reliability_score": round(rw["score"].get(i, np.nan), 0)})
        rows.append(r)
    return pd.DataFrame(rows)


def team_phase(d: pd.DataFrame) -> pd.DataFrame:
    """RR vs IPL league per season x phase, batting and bowling (regulation IPL innings)."""
    ipl = d[d.is_ipl]
    rows = []
    for side, team_col in (("batting", "batting_team_id"), ("bowling", "bowling_team_id")):
        g = ipl.groupby(["year", "phase", team_col]).agg(
            balls=("is_legal", "sum"), runs=("total_runs", "sum"), wkts=("is_wicket", "sum"),
            dots=("is_dot", "sum"), bnd=("is_boundary", "sum"), value=("v_bat", "sum"), n=("v_bat", "count"),
            high_balls=("high", "sum"))
        g["run_rate"] = 6 * g["runs"] / g["balls"]
        g["wkts_per_over"] = 6 * g["wkts"] / g["balls"]
        g["dot_pct"] = 100 * g["dots"] / g["balls"]
        g["boundary_pct"] = 100 * g["bnd"] / g["balls"]
        g["value_per100"] = 100 * g["value"] / g["n"]  # batting-side context value (bowling side: lower = better)
        g = g.reset_index().rename(columns={team_col: "team_id"})
        for (yr, ph), grp in g.groupby(["year", "phase"]):
            rr = grp[grp.team_id == RR_TEAM_ID]
            if rr.empty:
                continue
            rr = rr.iloc[0]
            for met in ("run_rate", "wkts_per_over", "dot_pct", "boundary_pct", "value_per100"):
                lg = grp[met].mean()
                better_high = (side == "batting") == (met in ("run_rate", "boundary_pct", "value_per100"))
                rank = grp[met].rank(ascending=not better_high, method="min")[grp.team_id == RR_TEAM_ID].iat[0]
                rows.append({"side": side, "year": yr, "phase": ph, "metric": met, "rr": round(rr[met], 3),
                             "league_mean": round(lg, 3), "rr_minus_league": round(rr[met] - lg, 3), "rr_rank_of_10": int(rank)})
    return pd.DataFrame(rows)


def pressure_team(d: pd.DataFrame) -> pd.DataFrame:
    """RR context value per 100 balls in HIGH vs non-HIGH, batting and bowling, IPL by season, with league rank."""
    ipl = d[d.is_ipl]
    rows = []
    for side, col, val, sign in (("batting", "batting_team_id", "v_bat", 1), ("bowling", "bowling_team_id", "v_bowl", 1)):
        for hi in (1.0, 0.0):
            g = ipl[ipl.high.eq(hi)].groupby(["year", col])[val].mean().mul(100).reset_index()
            for yr, grp in g.groupby("year"):
                r = grp[grp[col] == RR_TEAM_ID]
                if r.empty:
                    continue
                rows.append({"side": side, "year": yr, "situation": "HIGH pressure" if hi else "not HIGH",
                             "rr_value_per100": round(r[val].iat[0], 2),
                             "rr_rank_of_10": int(grp[val].rank(ascending=False, method="min")[grp[col] == RR_TEAM_ID].iat[0])})
    return pd.DataFrame(rows)


def close_matches(d: pd.DataFrame) -> pd.DataFrame:
    m = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
    ipl = m[m.is_ipl & m.win_team_id.notna() & ((m.home_team_id == RR_TEAM_ID) | (m.away_team_id == RR_TEAM_ID))]
    import re
    def margin(res):
        mt = re.search(r"Won by (\d+) (run|wicket)", str(res), re.I)
        return (int(mt.group(1)), mt.group(2).lower()) if mt else (None, None)
    ipl = ipl.assign(**dict(zip(["n", "kind"], zip(*ipl.result.map(margin)))))
    ipl["close"] = ((ipl.kind == "run") & (ipl.n <= 10)) | ((ipl.kind == "wicket") & (ipl.n <= 3)) | ipl.result.str.contains("Tied|Super", case=False)
    ipl["rr_won"] = ipl.win_team_id == RR_TEAM_ID
    return ipl.groupby("year").agg(matches=("match_id", "size"), wins=("rr_won", "sum"), close_matches=("close", "sum"),
                                   close_wins=("rr_won", lambda s: (s & ipl.loc[s.index, "close"]).sum())).reset_index()


def run() -> dict[str, pd.DataFrame]:
    from src.models import ratings as R
    d = R.ball_values(R.load())
    sq = squad_database()
    aud = player_audit(sq)
    ph = team_phase(d)
    pt = pressure_team(d)
    cm = close_matches(d)
    sq.to_csv(RESEARCH_DIR / "rr_squad_database.csv", index=False)
    aud.to_csv(RESEARCH_DIR / "rr_player_performance_database.csv", index=False)
    ph.to_csv(RESEARCH_DIR / "rr_phase_performance.csv", index=False)
    pd.concat([ph.assign(table="phase"), pt.assign(table="pressure"), cm.assign(table="close_matches")]).to_csv(
        REPORTS_DIR / "rr_team_performance_dashboard_data.csv", index=False)
    return {"squad": sq, "audit": aud, "phase": ph, "pressure": pt, "close": cm}


if __name__ == "__main__":
    pd.set_option("display.width", 260, "display.max_columns", 40, "display.max_rows", 200)
    r = run()
    print(r["squad"][["player_name", "indian_or_overseas", "acquisition_2026", "rr_apps_2025", "rr_apps_2026", "kept_wicket_2026"]].to_string(index=False))
    a = r["audit"]
    print(a[["player", "bat_role", "bat_balls", "bat_balls_high", "bat_sr", "bat_sr_high", "bat_usual_pctile_vs_eligible",
             "bat_pressure_pctile_vs_eligible", "bat_eligible", "bat_reliability_rank"]].dropna(subset=["bat_balls"]).sort_values("bat_balls", ascending=False).to_string(index=False))
    print(a[["player", "bowl_role", "bowl_type", "bowl_balls", "bowl_balls_high", "bowl_econ", "bowl_econ_high", "bowl_usual_pctile_vs_eligible",
             "bowl_pressure_pctile_vs_eligible", "bowl_eligible", "bowl_reliability_rank"]].dropna(subset=["bowl_balls"]).query("bowl_balls >= 60").sort_values("bowl_balls", ascending=False).to_string(index=False))
    p = r["phase"]
    print(p[p.year >= 2025].pivot_table(index=["side", "phase", "metric"], columns="year", values=["rr", "league_mean", "rr_rank_of_10"]).round(2).to_string())
    print(r["pressure"].to_string(index=False)); print(r["close"].to_string(index=False))


def role_depth(d: pd.DataFrame, year: int = 2026, min_balls: int = 24) -> pd.DataFrame:
    """Who RR actually used in each phase in `year`, with phase output vs league phase average."""
    ipl = d[d.is_ipl & d.year.eq(year)]
    rows = []
    lg_bat = ipl[ipl.is_batter_ball].groupby("phase").agg(sr=("runs", "mean"))["sr"] * 100
    lg_bowl = ipl.groupby("phase").apply(lambda g: 6 * g.bowler_runs.sum() / g.is_legal.sum())
    rr_bat = ipl[ipl.batting_team_id.eq(RR_TEAM_ID) & ipl.is_batter_ball]
    for (ph, pid), g in rr_bat.groupby(["phase", "striker_id"]):
        if len(g) >= min_balls:
            rows.append({"side": "batting", "phase": ph, "player_id": pid, "player": g.striker_name.iat[0], "balls": len(g),
                         "share_of_rr_phase_balls_pct": round(100 * len(g) / (rr_bat.phase == ph).sum(), 1),
                         "metric": "strike_rate", "value": round(100 * g.runs.mean(), 1), "league_phase_avg": round(lg_bat[ph], 1),
                         "context_value_per100": round(100 * g.v_bat.mean(), 1), "outs": int(g.striker_out.sum())})
    rr_bowl = ipl[ipl.bowling_team_id.eq(RR_TEAM_ID)]
    for (ph, pid), g in rr_bowl.groupby(["phase", "bowler_id"]):
        if g.is_legal.sum() >= min_balls:
            rows.append({"side": "bowling", "phase": ph, "player_id": pid, "player": g.bowler_name.iat[0], "balls": int(g.is_legal.sum()),
                         "share_of_rr_phase_balls_pct": round(100 * g.is_legal.sum() / rr_bowl[rr_bowl.phase == ph].is_legal.sum(), 1),
                         "metric": "economy", "value": round(6 * g.bowler_runs.sum() / g.is_legal.sum(), 2),
                         "league_phase_avg": round(lg_bowl[ph], 2), "context_value_per100": round(100 * g.v_bowl.mean(), 1),
                         "outs": int(g.bowler_wicket.sum())})
    return pd.DataFrame(rows).sort_values(["side", "phase", "balls"], ascending=[True, True, False])


ROLE_MAP = {  # requirement -> (side, phase, RR player-role filter, audit percentile column)
    "Powerplay / opening batting": ("batting", "powerplay", ["Opener", "No.3"], "bat_pressure_pctile_vs_eligible"),
    "Middle-overs batting": ("batting", "middle", ["No.3", "Middle order (4-5)"], "bat_pressure_pctile_vs_eligible"),
    "Death-overs / finishing batting": ("batting", "death", ["Middle order (4-5)", "Finisher (6-7)"], "bat_pressure_pctile_vs_eligible"),
    "Powerplay bowling": ("bowling", "powerplay", ["Powerplay specialist", "Multi-phase"], "bowl_pressure_pctile_vs_eligible"),
    "Middle-overs bowling": ("bowling", "middle", ["Middle-overs", "Multi-phase"], "bowl_pressure_pctile_vs_eligible"),
    "Death-overs bowling": ("bowling", "death", ["Death specialist", "Multi-phase"], "bowl_pressure_pctile_vs_eligible"),
}
PHASE_METRICS = {"batting": ["run_rate", "boundary_pct", "value_per100", "wkts_per_over"],
                 "bowling": ["run_rate", "dot_pct", "value_per100", "wkts_per_over"]}
W_SEVERITY, W_COVERAGE = 0.6, 0.4


def priority_matrix(ph: pd.DataFrame, aud: pd.DataFrame, depth: pd.DataFrame) -> pd.DataFrame:
    """Transparent recruitment priority per requirement:
       severity = (mean RR rank of 10 on the phase metrics, 2025-26, minus 1) / 9      [0 best .. 1 worst]
       coverage_gap = 1 - (best pressure percentile among RR players who (a) were used in that
                      phase in 2026 (>= 24 balls) and (b) meet candidate eligibility) / 100
                      (= 1 if no eligible RR player covers the role)
       priority = 100 * (0.6 * severity + 0.4 * coverage_gap); High >= 60, Medium 40-60, Low < 40."""
    rows = []
    for req, (side, phase, roles, pcol) in ROLE_MAP.items():
        sub = ph[(ph.side == side) & (ph.phase == phase) & ph.year.isin([2025, 2026]) & ph.metric.isin(PHASE_METRICS[side])]
        sev = (sub.rr_rank_of_10.mean() - 1) / 9
        used = depth[(depth.side == side) & (depth.phase == phase)].player_id
        elig_col = "bat_eligible" if side == "batting" else "bowl_eligible"
        cov = aud[aud.player_id.isin(used) & aud[elig_col].eq(True)]
        best = cov[pcol].max() if len(cov) else np.nan
        best_name = cov.loc[cov[pcol].idxmax(), "player"] if len(cov) else "none eligible"
        gap = 1 - best / 100 if pd.notna(best) else 1.0
        pr = 100 * (W_SEVERITY * sev + W_COVERAGE * gap)
        detail = "; ".join(f"{r.metric} {int(r.year)}: #{r.rr_rank_of_10}" for r in sub.sort_values(["metric", "year"]).itertuples())
        rows.append({"requirement": req, "phase_ranks_2025_26": detail, "mean_rr_rank_of_10": round(sub.rr_rank_of_10.mean(), 2),
                     "severity": round(sev, 2), "rr_players_used_in_phase_2026": ", ".join(depth[(depth.side == side) & (depth.phase == phase)].player.head(5)),
                     "best_eligible_rr_cover": best_name, "best_cover_pressure_pctile": best, "coverage_gap": round(gap, 2),
                     "priority_score": round(pr, 0), "priority": "High" if pr >= 60 else "Medium" if pr >= 40 else "Low"})
    return pd.DataFrame(rows).sort_values("priority_score", ascending=False)


def run_extended() -> dict[str, pd.DataFrame]:
    from src.models import ratings as R
    res = run()
    d = R.ball_values(R.load())
    dep = role_depth(d)
    dep.to_csv(RESEARCH_DIR / "rr_role_depth_chart.csv", index=False)
    pm = priority_matrix(res["phase"], res["audit"], dep)
    pm.to_csv(RESEARCH_DIR / "rr_recruitment_priority_matrix.csv", index=False)
    res.update({"depth": dep, "priority": pm})
    return res
