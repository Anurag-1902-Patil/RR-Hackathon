"""Build the cleaned delivery-level analytical table with pre-ball match state.

Output: data/processed/deliveries.parquet (one row per delivery, regulation innings 1-2),
        data/processed/super_overs.parquet, data/processed/matches.parquet,
        data/processed/playing_xi.parquet

All state columns (score_before, wkts_before, legal_balls_before, runs_needed, rrr, ...)
use only information available BEFORE the delivery is bowled (no target leakage).
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.config import (BOWLER_WICKET_TYPES, FULL_MEMBERS, NO_BALL_TYPES, NON_DISMISSAL_TYPES,
                        PROCESSED_DIR, RAW_DIR, WIDE)

log = logging.getLogger(__name__)


def load_raw() -> dict[str, pd.DataFrame]:
    """Read all raw CSVs (never modified)."""
    names = ["ball_by_ball", "matches", "competitions", "teams", "playing_eleven",
             "competition_team_player_mapping"]
    return {n: pd.read_csv(RAW_DIR / f"{n}.csv", low_memory=False) for n in names}


def build_matches(m: pd.DataFrame, comps: pd.DataFrame) -> pd.DataFrame:
    """Match table enriched with competition, tier and season."""
    out = m.merge(comps, on="comp_id", how="left", validate="m:1")
    out["match_date"] = pd.to_datetime(out["match_date"])
    out["year"] = out["match_date"].dt.year
    out["is_ipl"] = out["comp_name"].str.startswith("IPL")
    both_full = out["home_team"].isin(FULL_MEMBERS) & out["away_team"].isin(FULL_MEMBERS)
    out["tier"] = np.select(
        [out["is_ipl"], (out["match_format"] == "T20I") & both_full, out["match_format"] == "T20I"],
        ["IPL", "T20I_full", "T20I_assoc"], default="A_team")
    # revised overs columns are stored in balls (see audit §5.6)
    out = out.rename(columns={"first_inn_revised_overs": "inn1_max_balls",
                              "second_inn_revised_overs": "inn2_max_balls"})
    out["dls"] = out["result"].str.contains(r"D/?L", case=False, regex=True)
    return out


def dedupe_playing_xi(pe: pd.DataFrame, bb: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate (match, team, player) rows, preferring batting order seen in ball-by-ball."""
    bo = bb.groupby(["match_id", "striker_id"])["batting_order"].first().rename("bo_bb")
    pe = pe.merge(bo, left_on=["match_id", "player_id"], right_index=True, how="left")
    pe["_pref"] = (pe["batting_order"] == pe["bo_bb"]).astype(int)
    pe = (pe.sort_values(["match_id", "team_id", "player_id", "_pref"], ascending=[True, True, True, False])
            .drop_duplicates(["match_id", "team_id", "player_id"]).drop(columns=["_pref", "bo_bb"]))
    return pe.reset_index(drop=True)


def add_delivery_flags(bb: pd.DataFrame) -> pd.DataFrame:
    """Legal-ball, runs-attribution and wicket-attribution flags."""
    d = bb.copy()
    et = d["extras_type"].fillna("")
    d["is_wide"] = et.eq(WIDE)
    d["is_noball"] = et.isin(NO_BALL_TYPES)
    d["is_legal"] = ~(d["is_wide"] | d["is_noball"])
    d["is_batter_ball"] = ~d["is_wide"]  # balls faced: everything except wides
    d["total_runs"] = d["runs"] + d["extras1_runs"] + d["extras_2_runs"]
    # bowler concedes bat runs + all wide runs + no-ball penalty; byes/leg-byes are not charged
    d["bowler_runs"] = d["runs"] + np.where(d["is_wide"] | d["is_noball"], d["extras1_runs"], 0)
    d["dismissal_type"] = d["dismissal_type"].replace({"Obstracting the field": "Obstructing the field"})
    d["is_wicket"] = d["is_wicket"].astype(bool)
    d["bowler_wicket"] = d["is_wicket"] & d["dismissal_type"].isin(BOWLER_WICKET_TYPES)
    real_out = d["is_wicket"] & ~d["dismissal_type"].isin(NON_DISMISSAL_TYPES)
    d["striker_out"] = real_out & d["dismissed_player_id"].eq(d["striker_id"])
    d["non_striker_out"] = real_out & d["dismissed_player_id"].eq(d["non_striker_id"])
    d["is_dot"] = d["is_legal"] & d["total_runs"].eq(0)
    d["is_boundary"] = d["is_four"] | d["is_six"]
    d["phase"] = pd.cut(d["overid"], bins=[0, 6, 15, 20], labels=["powerplay", "middle", "death"]).astype(str)
    return d


def add_match_state(d: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """Pre-delivery match state per innings (only past information is used)."""
    d = d.sort_values(["match_id", "innings", "innings_ball_num"], kind="stable").reset_index(drop=True)
    g = d.groupby(["match_id", "innings"], sort=False)
    d["score_before"] = g["total_runs"].cumsum() - d["total_runs"]
    d["wkts_before"] = g["is_wicket"].cumsum() - d["is_wicket"].astype(int)
    d["legal_before"] = g["is_legal"].cumsum() - d["is_legal"].astype(int)

    mm = matches.set_index("match_id")
    max_balls = np.where(d["innings"].eq(1), d["match_id"].map(mm["inn1_max_balls"]),
                         d["match_id"].map(mm["inn2_max_balls"]))
    d["max_balls"] = pd.Series(max_balls).fillna(120).astype(int)
    d["balls_left"] = (d["max_balls"] - d["legal_before"]).clip(lower=0)
    d["wkts_left"] = 10 - d["wkts_before"]
    d["crr"] = np.where(d["legal_before"] > 0, d["score_before"] * 6 / d["legal_before"].replace(0, np.nan), np.nan)

    inn1_total = d[d["innings"].eq(1)].groupby("match_id")["total_runs"].sum()
    target = d["match_id"].map(mm["revised_target"]).fillna(d["match_id"].map(inn1_total) + 1)
    is_chase = d["innings"].eq(2)
    d["target"] = np.where(is_chase, target, np.nan)
    d["runs_needed"] = np.where(is_chase, d["target"] - d["score_before"], np.nan)
    d["rrr"] = np.where(is_chase & (d["balls_left"] > 0), d["runs_needed"] * 6 / d["balls_left"].replace(0, np.nan), np.nan)

    # outcome labels (used only as model targets, never as features)
    d["batting_team_won"] = d["batting_team_id"].eq(d["match_id"].map(mm["win_team_id"]))
    d["decided"] = d["match_id"].map(mm["win_team_id"]).notna()
    return d


def build(write: bool = True) -> dict[str, pd.DataFrame]:
    raw = load_raw()
    matches = build_matches(raw["matches"], raw["competitions"])
    bb = add_delivery_flags(raw["ball_by_ball"])
    supers = bb[bb["innings"] > 2].copy()
    reg = bb[bb["innings"] <= 2].copy()
    reg = add_match_state(reg, matches)
    meta = matches[["match_id", "comp_id", "comp_name", "match_format", "year", "match_date", "tier",
                    "is_ipl", "venue_id", "venue_country", "stage", "knock_out", "dls"]]
    reg = reg.merge(meta, on="match_id", how="left", validate="m:1")
    assert len(reg) + len(supers) == len(raw["ball_by_ball"]), "row count changed during build"
    xi = dedupe_playing_xi(raw["playing_eleven"], raw["ball_by_ball"])
    out = {"deliveries": reg, "super_overs": supers, "matches": matches, "playing_xi": xi,
           "player_map": raw["competition_team_player_mapping"]}
    if write:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        for k, v in out.items():
            v.to_parquet(PROCESSED_DIR / f"{k}.parquet", index=False)
            log.info("wrote %s: %s rows", k, len(v))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    res = build()
    d = res["deliveries"]
    print(d.groupby("tier").agg(deliveries=("match_id", "size"), matches=("match_id", "nunique")))
