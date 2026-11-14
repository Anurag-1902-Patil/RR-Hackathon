"""Auction-realistic shortlists: the most reliable players under pressure who are NOT contracted to any
IPL 2026 squad (data-pack IPL 2026 mappings for all 10 franchises) and not excluded by a verified
eligibility issue. Ranked by the same reliability score; RR fit added from phase evidence.

Contracted players can only reach RR if released at the 17 Nov 2026 retention deadline or traded; that
is not knowable today, so they are listed separately as a release watchlist.
Sources: research/RESEARCH_SOURCE_REGISTER.md (S12-S16).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import FEATURES_DIR, PROCESSED_DIR, REPORTS_DIR, RESEARCH_DIR

MO = REPORTS_DIR / "model_outputs"
EXCLUDE_NATION = {"Pakistan": "No Pakistan player has featured in the IPL since 2009 (Wisden, 20 Feb 2026; S13)"}
EXCLUDE_PLAYER = {
    "Harry Brook": "Banned from IPL/IPL auction for two seasons after 2025 withdrawal; whether 2027 is covered is unclear (Tribune/ANI, 13 Mar 2025; S14)",
    "Ravichandran Ashwin": "Retired from the IPL, 27 Aug 2025 (Gulf News/IANS; S15)",
    "Mohit Sharma": "Retired from all cricket, 3 Dec 2025 (Tribune/ANI; S16)",
}
FLAG_NATION = {"Bangladesh": "Availability risk: BCCI directed KKR to release Mustafizur Rahman in Jan 2026 (Akashvani; S12); no wider rule published"}
REQ = {("batting", "powerplay"): "Powerplay / opening batting", ("batting", "middle"): "Middle-overs batting",
       ("batting", "death"): "Death-overs / finishing batting", ("bowling", "powerplay"): "Powerplay bowling",
       ("bowling", "middle"): "Middle-overs bowling", ("bowling", "death"): "Death-overs bowling"}


def best_fit(side: str, pid: int, prof: pd.DataFrame, pool_ids, pri: dict) -> tuple[str, float, int]:
    best = None
    for ph in ("powerplay", "middle", "death"):
        n = prof.at[pid, f"balls_{ph}"] if pid in prof.index else np.nan
        if pd.isna(n) or n < 120:
            continue
        ref = prof.loc[prof.index.isin(pool_ids) & (prof[f"balls_{ph}"] >= 120), f"value_eb_{ph}"]
        pct = 100 * (ref < prof.at[pid, f"value_eb_{ph}"]).mean()
        cand = (pri[REQ[(side, ph)]] * pct, REQ[(side, ph)], pct, int(n))
        best = cand if best is None or cand[0] > best[0] else best
    return (best[1], round(best[2]), best[3]) if best else ("insufficient phase sample", np.nan, 0)


def run() -> dict[str, pd.DataFrame]:
    pm = pd.read_parquet(PROCESSED_DIR / "player_map.parquet")
    ipl26 = pm[pm.comp_name == "IPL 2026"].drop_duplicates("player_id").set_index("player_id").team_name
    pri = pd.read_csv(RESEARCH_DIR / "rr_recruitment_priority_matrix.csv").set_index("requirement").priority_score.to_dict()
    out = {}
    for side in ("batting", "bowling"):
        s = pd.read_csv(MO / f"reliability_{side}.csv")
        s["ipl_2026_team"] = s.player_id.map(ipl26)
        s["exclusion"] = s.national_side.map(EXCLUDE_NATION).fillna(s.player.map(EXCLUDE_PLAYER))
        s["risk_flag"] = s.national_side.map(FLAG_NATION)
        pool = s[s.ipl_2026_team.isna() & s.exclusion.isna()].copy()
        prof = pd.read_parquet(FEATURES_DIR / f"phase_profiles_{side}.parquet")
        fits = [best_fit(side, p, prof, set(s.player_id), pri) for p in pool.player_id]
        pool["rr_need_best_fit"] = [f[0] for f in fits]
        pool["phase_value_pctile_vs_eligible"] = [f[1] for f in fits]
        pool["phase_balls"] = [f[2] for f in fits]
        pool["indian_or_overseas"] = np.where(pool.national_side.isin(["India", "India A"]), "Indian", "Overseas")
        pool["auction_pool_rank"] = range(1, len(pool) + 1)
        hb = "balls_high" if side == "batting" else "legal_balls_high"
        cols = ["auction_pool_rank", "rank", "player", "player_id", "national_side", "indian_or_overseas", "role", "score", "p_top10",
                hb, "pressure_innings", "value_per100_high", "rr_need_best_fit", "phase_value_pctile_vs_eligible", "phase_balls",
                "pct_balls_IPL", "last_match", "risk_flag"]
        pool = pool[cols].rename(columns={"rank": "overall_reliability_rank"})
        out[side] = pool
        excl = s[s.ipl_2026_team.isna() & s.exclusion.notna()][["rank", "player", "national_side", "exclusion"]]
        watch = s[s.ipl_2026_team.notna() & (s["rank"] <= 15)][["rank", "player", "ipl_2026_team"]]
        out[f"{side}_excluded"], out[f"{side}_watchlist"] = excl, watch
        fname = "auction_pool_batsmen.csv" if side == "batting" else "auction_pool_bowlers.csv"
        pool.round(3).to_csv(REPORTS_DIR / fname, index=False)
        excl.to_csv(MO / f"auction_pool_excluded_{side}.csv", index=False)
        watch.to_csv(MO / f"release_watchlist_{side}.csv", index=False)
    return out


if __name__ == "__main__":
    pd.set_option("display.width", 260, "display.max_columns", 30, "display.max_colwidth", 60)
    r = run()
    for side in ("batting", "bowling"):
        p = r[side]
        print(f"\n== {side}: auction pool top 12")
        print(p[["auction_pool_rank", "overall_reliability_rank", "player", "national_side", "role", "score", "p_top10",
                 "rr_need_best_fit", "phase_value_pctile_vs_eligible", "pct_balls_IPL", "risk_flag"]].head(12).round(2).to_string(index=False))
        print("excluded:", r[f"{side}_excluded"].player.tolist())
