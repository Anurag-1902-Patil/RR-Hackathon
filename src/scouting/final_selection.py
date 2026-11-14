"""FINAL SELECTION RULE (user decision, 2026-11-14): the submitted top-10 lists contain ONLY players RR can
actually acquire at the IPL 2027 auction.

A player is RR-acquirable when ALL of these hold:
  1. eligible under the reliability framework (sample thresholds, active in 2025-26, not retired from the IPL);
  2. NOT on any IPL 2026 squad (data-pack IPL 2026 mappings for all 10 franchises), so not under contract with
     another franchise and not already an RR player;
  3. no verified eligibility bar: Pakistan players (none in the IPL since 2009, S13), banned or unclear-ban players
     (Brook, S14), retirements (Ashwin S15, Mohit Sharma S16);
  4. no availability that RR cannot rely on: Bangladeshi players are excluded (BCCI directed KKR to release
     Mustafizur Rahman in Jan 2026, S12; no rule published, so RR cannot count on signing one).

Reliability scores are unchanged (percentile among ALL eligible players). Rank, P(top 10), bootstrap rank
interval and the range across pressure definitions are recomputed WITHIN the acquirable pool, from the saved
bootstrap rank matrices and per-definition ranks (order within a subset is preserved, so this is exact).
The unrestricted performance ranking is kept as overall_* columns and in reports/performance_top10_*.csv.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import FEATURES_DIR, PROCESSED_DIR, REPORTS_DIR

MO = REPORTS_DIR / "model_outputs"
EXCLUDE_NATION = {"Pakistan": "No Pakistan player in the IPL since 2009 (S13)",
                  "Bangladesh": "Availability not reliable after BCCI-directed release of Mustafizur Rahman, Jan 2026 (S12)"}
EXCLUDE_PLAYER = {"Harry Brook": "Two-season IPL/auction ban from 2025; 2027 coverage unclear (S14)",
                  "Ravichandran Ashwin": "Retired from the IPL, 27 Aug 2025 (S15)",
                  "Mohit Sharma": "Retired from all cricket, 3 Dec 2025 (S16)"}
DEF_COLS = ["rank_blend_30lev_70rpi", "rank_blend_70lev_30rpi", "rank_high_top15pct", "rank_high_top30pct"]


def acquirability(s: pd.DataFrame) -> pd.Series:
    pm = pd.read_parquet(PROCESSED_DIR / "player_map.parquet")
    ipl26 = pm[pm.comp_name == "IPL 2026"].drop_duplicates("player_id").set_index("player_id").team_name
    team = s.player_id.map(ipl26)
    reason = pd.Series(np.nan, index=s.index, dtype=object)
    reason[team.notna()] = "Under IPL contract: " + team[team.notna()] + " (IPL 2026 squad)"
    reason = reason.fillna(s.national_side.map(EXCLUDE_NATION)).fillna(s.player.map(EXCLUDE_PLAYER))
    return reason


def run() -> dict[str, pd.DataFrame]:
    out = {}
    for side in ("batting", "bowling"):
        path = MO / f"reliability_{side}.csv"
        s = pd.read_csv(path)
        if "overall_rank" in s:  # idempotent: rebuild from the unrestricted ranking
            s["rank"] = s["overall_rank"]
            for c in ("p_top10", "p_top20", "boot_mean_rank", "boot_rank_p05", "boot_rank_p95", "rank_min_across_defs", "rank_max_across_defs"):
                s[c] = s[f"overall_{c}"]
        else:
            for c in ("rank", "p_top10", "p_top20", "boot_mean_rank", "boot_rank_p05", "boot_rank_p95", "rank_min_across_defs", "rank_max_across_defs"):
                s[f"overall_{c}"] = s[c]
        s = s.sort_values("overall_rank").reset_index(drop=True)
        s.loc[s["overall_rank"] <= 10].to_csv(REPORTS_DIR / f"performance_top10_{side}.csv", index=False)
        s["not_acquirable_reason"] = acquirability(s)
        s["rr_acquirable"] = s["not_acquirable_reason"].isna()
        pool = s[s.rr_acquirable].copy()
        # ranks within the pool
        pool["rank"] = pool["score"].rank(ascending=False, method="min").astype(int)
        m = pd.read_parquet(FEATURES_DIR / f"bootstrap_ranks_{side}.parquet").reindex(pool.player_id)
        mr = m.rank(axis=0, method="min")  # re-rank within pool per replicate
        pool["boot_mean_rank"] = mr.mean(axis=1).to_numpy()
        pool["boot_rank_p05"] = mr.quantile(0.05, axis=1).to_numpy()
        pool["boot_rank_p95"] = mr.quantile(0.95, axis=1).to_numpy()
        pool["p_top10"] = (mr <= 10).mean(axis=1).to_numpy()
        pool["p_top20"] = (mr <= 20).mean(axis=1).to_numpy()
        dr = pool[DEF_COLS].rank(method="min")
        allr = pd.concat([pool["rank"], dr], axis=1)
        pool["rank_min_across_defs"] = allr.min(axis=1).astype(int)
        pool["rank_max_across_defs"] = allr.max(axis=1).astype(int)
        s = s.set_index("player_id")
        for c in ("rank", "boot_mean_rank", "boot_rank_p05", "boot_rank_p95", "p_top10", "p_top20", "rank_min_across_defs", "rank_max_across_defs"):
            s[c] = np.nan
            s.loc[pool.player_id, c] = pool.set_index("player_id")[c]
        s = s.reset_index().sort_values(["rank", "overall_rank"], na_position="last")
        s.to_csv(path, index=False)
        out[side] = s
    return out


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    r = run()
    for side, s in r.items():
        print(side, s[s["rank"] <= 10][["rank", "overall_rank", "player", "national_side", "score", "p_top10", "boot_rank_p05", "boot_rank_p95",
                                         "rank_min_across_defs", "rank_max_across_defs"]].round(2).to_string(index=False))
        print("acquirable:", int(s.rr_acquirable.sum()), "of", len(s))
