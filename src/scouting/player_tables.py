"""Per-player batting and bowling tables: volume, raw stats by pressure band, context-adjusted
value, opponent-adjusted ratings, empirical-Bayes pressure delta, consistency, impact and role.

All numbers are CALCULATED from the RR data pack (see research/METHODOLOGY.md).
Units: "value" is runs per ball relative to context expectation (positive = good for the player);
tables report it per 100 balls.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.config import FEATURES_DIR, PROCESSED_DIR, REPORTS_DIR
from src.models import ratings as R

log = logging.getLogger(__name__)

ELIG = {"batting": {"high_balls": 120, "high_innings": 10}, "bowling": {"high_balls": 150, "high_matches": 10}}
SPELL_MIN_HIGH = 6  # an innings/spell counts as a "pressure innings/spell" with >= 6 HIGH balls


def load_all() -> pd.DataFrame:
    d = R.ball_values(R.load())
    return d


def identity(d: pd.DataFrame, pid: str, name: str) -> pd.DataFrame:
    """Name, latest team, national side (from T20I appearances), IPL sides, last match."""
    team_col = "batting_team_id" if pid == "striker_id" else "bowling_team_id"
    pm = pd.read_parquet(PROCESSED_DIR / "player_map.parquet")
    tname = pm.drop_duplicates("team_id").set_index("team_id")["team_name"]
    x = d[[pid, name, team_col, "match_date", "match_format", "is_ipl"]].copy()
    x["team"] = x[team_col].map(tname)
    g = x.sort_values("match_date").groupby(pid)
    out = pd.DataFrame({
        "player": g[name].last(),
        "latest_team": g["team"].last(),
        "last_match": g["match_date"].max().dt.date,
        "national_side": x[x["match_format"].eq("T20I")].groupby(pid)["team"].agg(lambda s: s.value_counts().index[0]),
        "ipl_teams": x[x["is_ipl"]].groupby(pid)["team"].agg(lambda s: " / ".join(dict.fromkeys(s))),
    })
    return out


def tier_mix(r: pd.DataFrame, pid: str, ball_mask: pd.Series) -> pd.DataFrame:
    t = pd.crosstab(r.loc[ball_mask, pid], r.loc[ball_mask, "tier"], normalize="index")
    return (t * 100).round(1).add_prefix("pct_balls_")


def eb_delta(r: pd.DataFrame, pid: str, val: str, tau2: float) -> pd.DataFrame:
    """Raw pressure delta (HIGH mean - non-HIGH mean, runs/ball) and its empirical-Bayes shrinkage."""
    g = r.groupby([pid, "high"])[val].agg(["mean", "var", "size"]).unstack("high")
    raw = g[("mean", 1.0)] - g[("mean", 0.0)]
    s2 = g[("var", 1.0)] / g[("size", 1.0)] + g[("var", 0.0)] / g[("size", 0.0)]
    k = max(tau2, 0.0) / (max(tau2, 0.0) + s2)
    return pd.DataFrame({"delta_raw": raw, "delta_eb": raw * k, "delta_shrink": k, "delta_se": np.sqrt(s2)})


def consistency(r: pd.DataFrame, pid: str, val: str) -> pd.DataFrame:
    """Share of pressure innings/spells (>= SPELL_MIN_HIGH HIGH balls) with value >= 0,
    Beta-Binomial shrunk toward the population rate (prior strength 10 innings)."""
    h = r[r["high"].eq(1)].groupby([pid, "match_id", "innings"])[val].agg(["sum", "size"])
    h = h[h["size"] >= SPELL_MIN_HIGH]
    g = h.groupby(level=0).agg(pressure_innings=("sum", "size"), good=("sum", lambda s: (s >= 0).sum()),
                               innings_value_sd=("sum", "std"))
    p0 = g["good"].sum() / g["pressure_innings"].sum()
    a, b = 10 * p0, 10 * (1 - p0)
    g["consistency_raw"] = g["good"] / g["pressure_innings"]
    g["consistency_post"] = (g["good"] + a) / (g["pressure_innings"] + a + b)
    return g


def impact(r: pd.DataFrame, pid: str, sign: float) -> pd.DataFrame:
    """Win Probability Added on HIGH balls (batting +WPA, bowling -WPA), total and per ball."""
    h = r[r["high"].eq(1) & r["wpa_bat"].notna()]
    g = h.groupby(pid)["wpa_bat"].agg(["sum", "size"])
    return pd.DataFrame({"wpa_high_total": sign * g["sum"], "wpa_high_per100": sign * 100 * g["sum"] / g["size"]})


def batting_role(r: pd.DataFrame) -> pd.DataFrame:
    pos = r.groupby(["striker_id", "match_id"])["batting_order"].first().groupby(level=0).median()
    band = pd.cut(pos, [0, 2.5, 3.5, 5.5, 7.5, 12], labels=["Opener", "No.3", "Middle order (4-5)", "Finisher (6-7)", "Lower order (8+)"])
    ph = pd.crosstab(r["striker_id"], r["phase"], normalize="index").mul(100).round(1).add_prefix("pct_balls_")
    return pd.DataFrame({"median_position": pos, "role": band.astype(str)}).join(ph)


def bowling_role(r: pd.DataFrame) -> pd.DataFrame:
    ph = pd.crosstab(r["bowler_id"], r["phase"], normalize="index").mul(100).round(1)
    role = np.select([ph["death"] >= 40, ph["powerplay"] >= 45, ph["middle"] >= 55],
                     ["Death specialist", "Powerplay specialist", "Middle-overs"], "Multi-phase")
    typ = r.groupby("bowler_id").agg(bowling_type=("bowling_type", lambda s: s.mode().iat[0]),
                                     pace_or_spin=("pace_or_spin", lambda s: s.mode().iat[0]))
    return typ.join(ph.add_prefix("pct_balls_")).assign(role=pd.Series(role, index=ph.index))


def band_stats_batting(r: pd.DataFrame, suffix: str) -> pd.DataFrame:
    g = r.groupby("striker_id")
    out = pd.DataFrame({
        f"balls{suffix}": g.size(), f"runs{suffix}": g["runs"].sum(), f"outs{suffix}": g["striker_out"].sum(),
        f"value_per100{suffix}": 100 * g["v_bat"].mean(),
        f"dot_pct{suffix}": 100 * g["is_dot"].mean(), f"boundary_pct{suffix}": 100 * g["is_boundary"].mean(),
    })
    out[f"sr{suffix}"] = 100 * out[f"runs{suffix}"] / out[f"balls{suffix}"]
    out[f"avg{suffix}"] = out[f"runs{suffix}"] / out[f"outs{suffix}"].replace(0, np.nan)
    out[f"xruns{suffix}"] = g["x_bat_runs"].sum()
    out[f"runs_above_exp{suffix}"] = out[f"runs{suffix}"] - out[f"xruns{suffix}"]
    return out


def band_stats_bowling(r: pd.DataFrame, suffix: str) -> pd.DataFrame:
    g = r.groupby("bowler_id")
    out = pd.DataFrame({
        f"legal_balls{suffix}": g["is_legal"].sum(), f"runs_conceded{suffix}": g["bowler_runs"].sum(),
        f"wickets{suffix}": g["bowler_wicket"].sum(), f"value_per100{suffix}": 100 * g["v_bowl"].mean(),
        f"dot_pct{suffix}": 100 * g["is_dot"].sum() / g["is_legal"].sum(),
        f"boundary_conc_pct{suffix}": 100 * g["is_boundary"].sum() / g["is_legal"].sum(),
        f"xruns_conceded{suffix}": g["x_bowl_runs"].sum(), f"xwickets{suffix}": g["x_bowl_wkt"].sum(),
    })
    out[f"economy{suffix}"] = 6 * out[f"runs_conceded{suffix}"] / out[f"legal_balls{suffix}"]
    out[f"bowl_sr{suffix}"] = out[f"legal_balls{suffix}"] / out[f"wickets{suffix}"].replace(0, np.nan)
    out[f"runs_saved{suffix}"] = out[f"xruns_conceded{suffix}"] - out[f"runs_conceded{suffix}"]
    out[f"wickets_above_exp{suffix}"] = out[f"wickets{suffix}"] - out[f"xwickets{suffix}"]
    return out


def build(d: pd.DataFrame, ratings: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    cv = pd.read_csv(REPORTS_DIR / "model_outputs" / "clutch_variance.csv").set_index("side")["tau2"]
    # ---------------- batting
    rb = d[d["is_batter_ball"]]
    bat = identity(rb, "striker_id", "striker_name")
    bat = bat.join(rb.groupby("striker_id").agg(batting_hand=("batting_type", lambda s: s.mode().iat[0]),
                                                matches=("match_id", "nunique")))
    bat = bat.join(band_stats_batting(rb, "")).join(band_stats_batting(rb[rb["high"].eq(1)], "_high"))
    bat = bat.join(band_stats_batting(rb[rb["pressure_band"].eq("low")], "_low"))
    bat = bat.join(tier_mix(rb, "striker_id", rb["is_batter_ball"]))
    bat = bat.join(ratings["batting"].mul(100).add_suffix("_per100"))
    bat = bat.join(eb_delta(rb, "striker_id", "v_bat", cv["batting"]).assign(
        delta_raw=lambda x: 100 * x.delta_raw, delta_eb=lambda x: 100 * x.delta_eb, delta_se=lambda x: 100 * x.delta_se))
    bat = bat.join(consistency(rb, "striker_id", "v_bat")).join(impact(rb, "striker_id", 1.0)).join(batting_role(rb))
    bat["eligible"] = (bat["balls_high"].fillna(0) >= ELIG["batting"]["high_balls"]) & (bat["pressure_innings"].fillna(0) >= ELIG["batting"]["high_innings"])
    # ---------------- bowling
    rw = d
    bowl = identity(rw, "bowler_id", "bowler_name")
    bowl = bowl.join(rw.groupby("bowler_id").agg(matches=("match_id", "nunique")))
    bowl = bowl.join(band_stats_bowling(rw, "")).join(band_stats_bowling(rw[rw["high"].eq(1)], "_high"))
    bowl = bowl.join(band_stats_bowling(rw[rw["pressure_band"].eq("low")], "_low"))
    bowl = bowl.join(tier_mix(rw, "bowler_id", pd.Series(True, index=rw.index)))
    bowl = bowl.join(ratings["bowling"].mul(100).add_suffix("_per100"))
    bowl = bowl.join(eb_delta(rw, "bowler_id", "v_bowl", cv["bowling"]).assign(
        delta_raw=lambda x: 100 * x.delta_raw, delta_eb=lambda x: 100 * x.delta_eb, delta_se=lambda x: 100 * x.delta_se))
    bowl = bowl.join(consistency(rw, "bowler_id", "v_bowl")).join(impact(rw, "bowler_id", -1.0)).join(bowling_role(rw))
    bowl["eligible"] = (bowl["legal_balls_high"].fillna(0) >= ELIG["bowling"]["high_balls"]) & (bowl["pressure_innings"].fillna(0) >= ELIG["bowling"]["high_matches"])
    bat.index.name = bowl.index.name = "player_id"
    return {"batting": bat, "bowling": bowl}


def run() -> dict[str, pd.DataFrame]:
    d = load_all()
    ratings = R.run(d=d)
    tabs = build(d, ratings)
    out = FEATURES_DIR / "player_tables"
    out.mkdir(exist_ok=True)
    for k, v in tabs.items():
        v.to_parquet(out / f"{k}.parquet")
        log.info("%s: %d players, %d eligible", k, len(v), v["eligible"].sum())
    return tabs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    t = run()
    pd.set_option("display.width", 250, "display.max_columns", 30)
    for k, v in t.items():
        e = v[v.eligible]
        cols = ["player", "latest_team", "role", "balls_high" if k == "batting" else "legal_balls_high",
                "usual_per100", "pressure_perf_per100", "delta_eb", "consistency_post", "wpa_high_per100"]
        print(f"\n== {k}: top 15 by pressure_perf (eligible)\n", e.sort_values("pressure_perf_per100", ascending=False)[cols].head(15).round(2).to_string())
