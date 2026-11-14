"""Export compact AGGREGATE tables for the dashboard (no ball-level data leaves the pipeline)."""
from __future__ import annotations

import pandas as pd

from src.config import FEATURES_DIR, REPORTS_DIR
from src.models import ratings as R

OUT = REPORTS_DIR / "dashboard_data"


def run() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = R.ball_values(R.load())
    rel = {s: pd.read_csv(REPORTS_DIR / "model_outputs" / f"reliability_{s}.csv") for s in ("batting", "bowling")}
    rr_ids = set(pd.read_csv(REPORTS_DIR.parent / "research" / "rr_squad_database.csv")["player_id"])
    keep = {s: set(r["player_id"]) | rr_ids for s, r in rel.items()}
    # phase profiles
    for s in ("batting", "bowling"):
        p = pd.read_parquet(FEATURES_DIR / f"phase_profiles_{s}.parquet")
        p[p.index.isin(keep[s])].round(3).to_csv(OUT / f"phase_profiles_{s}.csv")
    # pressure share by over
    h = d.groupby(["innings", "overid"])["high"].mean().mul(100).round(1).rename("pct_high").reset_index()
    h.to_csv(OUT / "pressure_by_over.csv", index=False)
    # league-wide outcomes by pressure band and phase
    b = d[d.is_batter_ball].groupby(["phase", "pressure_band"]).agg(balls=("runs", "size"), sr=("runs", lambda x: 100 * x.mean()),
                                                                     dismissal_pct=("striker_out", lambda x: 100 * x.mean()),
                                                                     dot_pct=("is_dot", lambda x: 100 * x.mean())).round(2)
    b.reset_index().to_csv(OUT / "outcomes_by_phase_band.csv", index=False)
    # per-player season trends (eligible + RR players)
    bat = d[d.is_batter_ball & d.striker_id.isin(keep["batting"])].groupby(["striker_id", "year"]).agg(
        player=("striker_name", "last"), balls=("runs", "size"), runs=("runs", "sum"), outs=("striker_out", "sum"),
        high_balls=("high", "sum"), value_per100=("v_bat", lambda x: 100 * x.mean())).reset_index().rename(columns={"striker_id": "player_id"})
    bat["sr"] = 100 * bat.runs / bat.balls
    bowl = d[d.bowler_id.isin(keep["bowling"])].groupby(["bowler_id", "year"]).agg(
        player=("bowler_name", "last"), legal_balls=("is_legal", "sum"), runs_conceded=("bowler_runs", "sum"),
        wickets=("bowler_wicket", "sum"), high_balls=("high", "sum"), value_per100=("v_bowl", lambda x: 100 * x.mean())).reset_index().rename(
        columns={"bowler_id": "player_id"})
    bowl["economy"] = 6 * bowl.runs_conceded / bowl.legal_balls
    bat.round(2).to_csv(OUT / "season_trends_batting.csv", index=False)
    bowl.round(2).to_csv(OUT / "season_trends_bowling.csv", index=False)
    # dataset summary
    m = pd.read_parquet(FEATURES_DIR.parent / "processed" / "matches.parquet")
    summary = {"deliveries": len(d), "matches_with_ball_data": d.match_id.nunique(), "ipl_matches": int(d[d.is_ipl].match_id.nunique()),
               "t20i_matches": int(d[d.match_format.eq("T20I")].match_id.nunique()), "batters": d.striker_id.nunique(), "bowlers": d.bowler_id.nunique(),
               "high_pressure_deliveries": int(d.high.sum()), "eligible_batters": len(rel["batting"]), "eligible_bowlers": len(rel["bowling"]),
               "date_from": str(m.match_date.min().date()), "date_to": str(m.match_date.max().date())}
    pd.Series(summary).to_csv(OUT / "dataset_summary.csv", header=["value"])
    print(summary)


if __name__ == "__main__":
    run()
