"""Score SMAT players with the main reliability method and select the uncapped Indian picks.

Pool rule (stated, applied after scoring): Indian, uncapped in T20Is (no India T20I in the data pack,
confirmed against Wikipedia for every pick), not on any IPL 2026 squad, played SMAT 2023/24 or later.
Score = same five components and weights, percentiles among ALL eligible SMAT players (capped players
included), so the uncapped picks are measured against India's full domestic field.
Strength: one ridge fitted on data-pack + SMAT balls (see src/domestic/smat.py).
Validation: does SMAT ability predict IPL ability? Spearman between a SMAT-only rating and the pack
rating for players with enough balls in both.
"""
from __future__ import annotations

import lightgbm as lgb  # noqa: F401  (import order: see smat.py)
import numpy as np

from src.domestic import smat as S  # runs the LightGBM warm-up before pyarrow loads

import pandas as pd  # noqa: E402

from src.config import FEATURES_DIR, PROCESSED_DIR, REPORTS_DIR  # noqa: E402
from src.models import ratings as R  # noqa: E402
from src.scouting import player_tables as PT  # noqa: E402
from src.scouting import reliability as RL  # noqa: E402
from src.domestic import verified_uncapped as V  # noqa: E402

MO = REPORTS_DIR / "model_outputs"
ELIG = {"batting": ("balls_high", 40, 4), "bowling": ("legal_balls_high", 48, 4)}
N_PICKS = 5
N_BOOT = 60


def alphas() -> dict:
    out = {}
    for side in ("batting", "bowling"):
        a, sc = R.choose(pd.read_csv(MO / f"ratings_tuning_{side}.csv"))
        tp = pd.read_csv(MO / f"ratings_tuning_pressure_only_{side}.csv")
        out[side] = (a, sc, float(tp.loc[tp["skill_high_pct"].idxmax(), "alpha"]))
    return out


def pack_rows() -> pd.DataFrame:
    bv = pd.read_parquet(FEATURES_DIR / "ball_values.parquet")
    d = pd.read_parquet(PROCESSED_DIR / "deliveries.parquet", columns=R.KEY + ["striker_id", "bowler_id", "is_batter_ball", "year"])
    return d.merge(bv, on=R.KEY, validate="1:1")


COLS = ["striker_id", "bowler_id", "is_batter_ball", "v_bat", "v_bowl", "high"]


def combined_ratings(sm: pd.DataFrame, pk: pd.DataFrame, A: dict) -> dict[str, pd.DataFrame]:
    both = pd.concat([pk[COLS], sm[COLS]], ignore_index=True)
    res = {}
    for side in ("batting", "bowling"):
        a, sc, pa = A[side]
        res[side] = R.fit_side(both, side, a, sc).join(R.fit_pressure_only(both, side, pa))
    return res


def tables(sm: pd.DataFrame, ratings: dict) -> dict[str, pd.DataFrame]:
    t = RL.add_impact(PT.build(sm, ratings), sm)
    for side, (hc, nb, ni) in ELIG.items():
        x = t[side]
        x["eligible"] = (x[hc].fillna(0) >= nb) & (x["pressure_innings"].fillna(0) >= ni)
    return t


def score_side(x: pd.DataFrame) -> pd.DataFrame:
    x = x.copy()
    x["eligible"] = x["eligible"] & x[list(RL.COMP_COLS.values())].notna().all(axis=1)
    return RL.score(x, RL.WEIGHTS)


def identity(sm: pd.DataFrame, t: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    pm = pd.read_parquet(PROCESSED_DIR / "player_map.parquet")
    ipl26 = pm[pm.comp_name.eq("IPL 2026")]
    ipl26_id = ipl26.drop_duplicates("player_id").set_index("player_id").team_name
    ipl26_key = ipl26.assign(k=ipl26.player_name.map(S._key)).groupby("k").team_name.first()
    pack_tabs = {s: pd.read_parquet(FEATURES_DIR / "player_tables" / f"{s}.parquet") for s in ("batting", "bowling")}
    capped = set()
    for v in pack_tabs.values():
        capped |= set(v.index[v.national_side.eq("India")])
    ppl = pd.read_csv(FEATURES_DIR / "smat" / "smat_people.csv").drop_duplicates("player_id").set_index("player_id")
    for side, (pid, team) in {"batting": ("striker_id", "batting_team"), "bowling": ("bowler_id", "bowling_team")}.items():
        x = t[side]
        g = sm.sort_values("match_date").groupby(pid)
        x["smat_team"] = g[team].last()
        x["last_smat_match"] = g["match_date"].max().dt.date
        x["smat_seasons"] = g["season"].agg(lambda s: ", ".join(sorted(set(s))))
        x["cricsheet_name"] = ppl["name"].reindex(x.index)
        x["linked_to_pack"] = x.index < S.ID_OFFSET
        x["india_t20i_cap_in_pack"] = x.index.isin(capped)
        x["ipl_2026_team"] = pd.Series(x.index.map(ipl26_id), index=x.index)
        by_name = x["cricsheet_name"].map(S._key).map(ipl26_key)
        x["ipl_2026_name_match"] = by_name.where(~x["linked_to_pack"])  # possible squad member, verify
        ipl_balls = {s: pack_tabs[s]["pct_balls_IPL"] * pack_tabs[s]["balls" if s == "batting" else "legal_balls"] / 100 for s in pack_tabs}
        x["ipl_balls_2022_26"] = x.index.map(ipl_balls[side]).fillna(0) if hasattr(x.index, "map") else 0
        x["recent"] = x["last_smat_match"].astype(str) >= S.RECENT_FROM
    return t


def pool_mask(x: pd.DataFrame) -> pd.Series:
    return (x["eligible"] & x["recent"] & ~x["india_t20i_cap_in_pack"] & x["ipl_2026_team"].isna()
            & x["ipl_2026_name_match"].isna())


def validate_transfer(sm: pd.DataFrame, A: dict) -> pd.DataFrame:
    """SMAT-only ridge rating vs data-pack rating (usual ability), players with enough balls in both."""
    rows = []
    for side, (n_s, n_p) in {"batting": (150, 150), "bowling": (150, 150)}.items():
        a, sc, _ = A[side]
        smr = R.fit_side(sm[COLS], side, a, sc)["usual"]
        pk = pd.read_parquet(FEATURES_DIR / "player_tables" / f"{side}.parquet")
        vol = "balls" if side == "batting" else "legal_balls"
        cnt = sm[sm.is_batter_ball].groupby("striker_id").size() if side == "batting" else sm[sm.is_legal].groupby("bowler_id").size()
        ids = [i for i in smr.index if i < S.ID_OFFSET and cnt.get(i, 0) >= n_s and pk[vol].get(i, 0) >= n_p]
        r = pd.DataFrame({"smat": smr.reindex(ids), "pack": pk["usual_per100"].reindex(ids)})
        rows.append({"side": side, "players": len(ids), "spearman_smat_vs_pack_usual": round(r.smat.corr(r.pack, method="spearman"), 3)})
    return pd.DataFrame(rows)


def bootstrap(sm: pd.DataFrame, pk: pd.DataFrame, A: dict, base: dict, n: int = N_BOOT) -> dict[str, pd.DataFrame]:
    """Match-level bootstrap of SMAT matches (pack balls fixed): re-fit ridge, tables and scores;
    rank within the uncapped pool. Returns per-player P(top N_PICKS) and 90% rank interval."""
    rng = np.random.default_rng(2027)
    mids = sm["match_id"].unique()
    pools = {s: base[s].index[base[s]["in_pool"]] for s in base}
    ranks = {s: [] for s in base}
    for b in range(n):
        pick = rng.choice(mids, len(mids), replace=True)
        cnt = pd.Series(pick).value_counts()
        parts = []
        for k, (mid, c) in enumerate(cnt.items()):
            g = sm[sm.match_id == mid] if c else None
            for j in range(c):
                parts.append(g.assign(match_id=mid * 100 + j))
        sb = pd.concat(parts, ignore_index=True)
        rt = combined_ratings(sb, pk, A)
        tb = tables(sb, rt)
        for s in base:
            sc = score_side(tb[s])
            p = sc.reindex(pools[s]).dropna(subset=["score"])["score"].rank(ascending=False, method="min")
            ranks[s].append(p.reindex(pools[s]))
    out = {}
    for s in base:
        m = pd.concat(ranks[s], axis=1)
        m.columns = range(m.shape[1])
        out[s] = pd.DataFrame({"p_top5": (m <= N_PICKS).mean(axis=1), "boot_rank_p05": m.quantile(0.05, axis=1),
                               "boot_rank_p95": m.quantile(0.95, axis=1), "boot_present": m.notna().mean(axis=1)})
        m.to_parquet(FEATURES_DIR / "smat" / f"bootstrap_uncapped_{s}.parquet")
    return out


def run(n_boot: int = N_BOOT) -> dict[str, pd.DataFrame]:
    sm = pd.read_parquet(FEATURES_DIR / "smat" / "smat_deliveries.parquet")
    pk = pack_rows()
    A = alphas()
    t = identity(sm, tables(sm, combined_ratings(sm, pk, A)))
    res = {}
    for side, x in t.items():
        sc = score_side(x)
        y = x.join(sc, how="left")
        y["data_pool"] = pool_mask(y) & y["score"].notna()
        st = y["cricsheet_name"].map(lambda n: V.status(n))
        y["fresher_ok"] = st.str[0].fillna(False).astype(bool)
        y["exclusion_reason"] = st.str[1]
        y["age_at_auction"] = st.str[2]
        y["full_name"] = st.str[3]
        y["in_pool"] = y["data_pool"] & y["fresher_ok"]
        y["pool_rank"] = y.loc[y["in_pool"], "score"].rank(ascending=False, method="min")
        res[side] = y
    if n_boot:
        bs = bootstrap(sm, pk, A, res, n_boot)
        for s in res:
            res[s] = res[s].join(bs[s])
    for side, y in res.items():
        y.sort_values(["in_pool", "pool_rank", "score"], ascending=[False, True, False]).to_csv(MO / f"uncapped_scores_{side}.csv")
    validate_transfer(sm, A).to_csv(MO / "uncapped_transfer_validation.csv", index=False)
    return res


if __name__ == "__main__":
    import sys
    r = run(int(sys.argv[1]) if len(sys.argv) > 1 else N_BOOT)
    pd.set_option("display.width", 250, "display.max_columns", 20)
    for s, y in r.items():
        print(s, "eligible", int(y.eligible.sum()), "pool", int(y.in_pool.sum()))
        print(y[y.in_pool].sort_values("pool_rank").head(12)[["full_name", "smat_team", "age_at_auction", "score", "pool_rank", "ipl_balls_2022_26", "last_smat_match"]
              + [c for c in ("p_top5", "boot_rank_p05", "boot_rank_p95") if c in y]].to_string())
    print(pd.read_csv(MO / "uncapped_transfer_validation.csv").to_string(index=False))
