"""Reliability score (0-100), weight sensitivity, pressure-definition sensitivity and bootstrap
rank stability for batters and bowlers.

Score = weighted mean of component PERCENTILES among eligible players (interpretable as
"rates above X% of eligible players"). Components:
  pressure_perf  opponent-adjusted value on HIGH balls (ridge, shrunk to league mean)
  consistency    share of pressure innings/spells with value >= 0 (Beta-Binomial shrunk)
  impact         WPA per HIGH ball, empirical-Bayes shrunk (method of moments)
  delta          pressure vs own baseline, empirical-Bayes shrunk
  usual          all-situation opponent-adjusted ability (predictive anchor)
Sample size enters only through shrinkage (no separate "sample confidence" component, which
would double-count it).
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.config import FEATURES_DIR, REPORTS_DIR, SEED
from src.models import ratings as R
from src.scouting import player_tables as PT

log = logging.getLogger(__name__)

WEIGHTS = {"pressure_perf": 0.35, "consistency": 0.20, "impact": 0.20, "delta": 0.15, "usual": 0.10}
ALT_WEIGHTS = {
    "final": WEIGHTS,
    "equal": dict.fromkeys(WEIGHTS, 0.2),
    "prompt_hypothesis_mapped": {"pressure_perf": 0.30, "impact": 0.25, "consistency": 0.20, "delta": 0.15, "usual": 0.10},
    "pressure_only": {"pressure_perf": 1.0},
    "no_impact": {"pressure_perf": 0.45, "consistency": 0.25, "delta": 0.20, "usual": 0.10},
    "predictive_tilt": {"pressure_perf": 0.30, "consistency": 0.15, "impact": 0.15, "delta": 0.10, "usual": 0.30},
    "baseline_delta_heavy": {"pressure_perf": 0.25, "consistency": 0.20, "impact": 0.15, "delta": 0.35, "usual": 0.05},
}
COMP_COLS = {"pressure_perf": "pressure_perf_per100", "consistency": "consistency_post", "impact": "impact_eb",
             "delta": "delta_eb", "usual": "usual_per100"}


def eb_rate(r: pd.DataFrame, pid: str, val: str) -> pd.Series:
    """Empirical-Bayes shrunk per-ball mean of `val` (method-of-moments tau^2), per player."""
    g = r.groupby(pid)[val].agg(["mean", "var", "size"])
    g = g[g["size"] >= 2]
    mu = np.average(g["mean"], weights=g["size"])
    s2 = g["var"] / g["size"]
    big = g["size"] >= 60
    tau2 = max(g.loc[big, "mean"].var() - s2[big].mean(), 1e-12)
    return mu + (g["mean"] - mu) * tau2 / (tau2 + s2)


def add_impact(tabs: dict[str, pd.DataFrame], d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    h = d[d["high"].eq(1) & d["wpa_bat"].notna()]
    hb = h[h["is_batter_ball"]]
    tabs["batting"]["impact_eb"] = 100 * eb_rate(hb, "striker_id", "wpa_bat")
    hw = h.assign(wpa_bowl=-h["wpa_bat"])
    tabs["bowling"]["impact_eb"] = 100 * eb_rate(hw, "bowler_id", "wpa_bowl")
    return tabs


def score(t: pd.DataFrame, weights: dict[str, float], universe: pd.Index | None = None) -> pd.DataFrame:
    e = t.loc[universe] if universe is not None else t[t["eligible"]]
    pct = pd.DataFrame({k: e[COMP_COLS[k]].rank(pct=True) for k in weights})
    s = sum(w * pct[k] for k, w in weights.items()) / sum(weights.values())
    out = pct.add_prefix("pct_")
    out["score"] = 100 * s
    out["rank"] = out["score"].rank(ascending=False, method="min").astype(int)
    return out.sort_values("rank")


def component_tables(d: pd.DataFrame, tune: bool) -> dict[str, pd.DataFrame]:
    ratings = R.run(d=d, tune_first=tune)
    return add_impact(PT.build(d, ratings), d)


def weight_sensitivity(tabs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for side, t in tabs.items():
        base = score(t, WEIGHTS)
        top = set(base.index[base["rank"] <= 10])
        for name, w in ALT_WEIGHTS.items():
            s = score(t, w)
            alt_top = set(s.index[s["rank"] <= 10])
            rows.append({"side": side, "variant": name, "top10_overlap": len(top & alt_top),
                         "spearman_vs_final": s["score"].corr(base["score"], method="spearman")})
    return pd.DataFrame(rows)


def comp_correlations(tabs) -> dict[str, pd.DataFrame]:
    return {side: t[t["eligible"]][[COMP_COLS[k] for k in WEIGHTS]].corr(method="spearman").round(2) for side, t in tabs.items()}


def with_high(d: pd.DataFrame, high: pd.Series) -> pd.DataFrame:
    d = d.copy()
    d["high"] = high.astype(float)
    d["pressure_band"] = np.where(high, "high", np.where(d["pressure_score"] < 0.5, "low", "medium"))
    return d


def definition_sensitivity(d: pd.DataFrame, base_tabs: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict]:
    """Re-run the whole player pipeline under alternative pressure definitions (same model settings),
    scoring the SAME eligible universe as the final definition."""
    variants = {
        "blend_30lev_70rpi": d["pressure_band_l30"].eq("high"),
        "blend_70lev_30rpi": d["pressure_band_l70"].eq("high"),
        "high_top15pct": d["pressure_score"] >= 0.85,
        "high_top30pct": d["pressure_score"] >= 0.70,
    }
    rows, ranks = [], {}
    base = {s: score(t, WEIGHTS) for s, t in base_tabs.items()}
    for name, hi in variants.items():
        tabs = component_tables(with_high(d, hi), tune=False)
        for side, t in tabs.items():
            uni = base[side].index
            s = score(t, WEIGHTS, universe=uni)
            ranks.setdefault(side, {})[name] = s["rank"]
            top, alt = set(base[side].index[base[side]["rank"] <= 10]), set(s.index[s["rank"] <= 10])
            rows.append({"side": side, "variant": name, "top10_overlap": len(top & alt),
                         "spearman_vs_final": s["score"].reindex(uni).corr(base[side]["score"], method="spearman")})
    return pd.DataFrame(rows), ranks


def bootstrap(d: pd.DataFrame, base_tabs: dict[str, pd.DataFrame], n_boot: int = 100) -> dict[str, pd.DataFrame]:
    """Match-level bootstrap of the full player pipeline; ranks within the fixed eligible universe."""
    rng = np.random.default_rng(SEED)
    matches = d["match_id"].unique()
    by_match = {m: idx for m, idx in d.groupby("match_id").indices.items()}
    uni = {s: t.index[t["eligible"]] for s, t in base_tabs.items()}
    store = {s: [] for s in base_tabs}
    for b in range(n_boot):
        pick = rng.choice(matches, size=len(matches), replace=True)
        idx = np.concatenate([by_match[m] for m in pick])
        db = d.iloc[idx].copy()
        # make duplicated matches distinct so per-innings groupings stay correct
        rep = np.concatenate([np.full(len(by_match[m]), k) for k, m in enumerate(pick)])
        db["match_id"] = db["match_id"].astype(np.int64) * 1000 + rep % 1000 + (rep // 1000) * 10**7
        db.index = np.arange(len(db))
        tabs = component_tables(db, tune=False)
        for side, t in tabs.items():
            t = t.reindex(uni[side])
            for c in COMP_COLS.values():
                t[c] = t[c].fillna(t[c].median())
            s = score(t.assign(eligible=True), WEIGHTS)
            store[side].append(s["rank"].rename(b))
        if (b + 1) % 10 == 0:
            log.info("bootstrap %d/%d", b + 1, n_boot)
    out = {}
    for side, cols in store.items():
        m = pd.concat(cols, axis=1)
        m.columns = m.columns.astype(str)
        m.to_parquet(FEATURES_DIR / f"bootstrap_ranks_{side}.parquet")  # player x replicate rank matrix
        out[side] = pd.DataFrame({"boot_mean_rank": m.mean(axis=1), "boot_rank_p05": m.quantile(0.05, axis=1),
                                  "boot_rank_p95": m.quantile(0.95, axis=1), "p_top10": (m <= 10).mean(axis=1),
                                  "p_top20": (m <= 20).mean(axis=1)})
    return out


RECENT_YEARS = (2025, 2026)  # auction relevance: must appear in the data in 2025 or 2026
# Verified formal IPL retirements (user decision 2026-11-14: exclude from IPL 2027 lists).
# player_id -> source ID in research/RESEARCH_SOURCE_REGISTER.md
RETIRED_FROM_IPL: dict[int, str] = {1318: "Andre Russell: retired from IPL 30 Nov 2025 (S7)"}


def recent_flag(d: pd.DataFrame) -> dict[str, pd.Series]:
    r = d[d["year"].isin(RECENT_YEARS)]
    return {"batting": pd.Series(True, index=r.loc[r["is_batter_ball"], "striker_id"].unique()),
            "bowling": pd.Series(True, index=r["bowler_id"].unique())}


def run(n_boot: int = 100) -> dict[str, pd.DataFrame]:
    out_dir = REPORTS_DIR / "model_outputs"
    d = PT.load_all()
    tabs = component_tables(d, tune=True)
    rec = recent_flag(d)
    excluded = []
    for side, t in tabs.items():
        t["active_recent"] = t.index.isin(rec[side].index)
        t["retired_from_ipl"] = t.index.isin(list(RETIRED_FROM_IPL))
        excluded.append(t[t["eligible"] & ~t["active_recent"]][["player", "last_match"]].assign(side=side, reason="no data 2025-26"))
        excluded.append(t[t["eligible"] & t["retired_from_ipl"]][["player", "last_match"]].assign(
            side=side, reason=lambda x: x.index.map(RETIRED_FROM_IPL)))
        t["eligible_statistical"] = t["eligible"]
        t["eligible"] = t["eligible"] & t["active_recent"] & ~t["retired_from_ipl"]
    pd.concat(excluded).to_csv(out_dir / "excluded_inactive.csv")
    for side, c in comp_correlations(tabs).items():
        c.to_csv(out_dir / f"reliability_component_corr_{side}.csv")
    weight_sensitivity(tabs).to_csv(out_dir / "reliability_weight_sensitivity.csv", index=False)
    defs, def_ranks = definition_sensitivity(d, tabs)
    defs.to_csv(out_dir / "reliability_definition_sensitivity.csv", index=False)
    log.info("definition sensitivity:\n%s", defs.round(3).to_string(index=False))
    boot = bootstrap(d, tabs, n_boot=n_boot)
    final = {}
    for side, t in tabs.items():
        s = score(t, WEIGHTS)
        s = s.join(pd.DataFrame(def_ranks[side]).add_prefix("rank_"))
        s = s.join(boot[side])
        rank_cols = ["rank"] + [c for c in s if c.startswith("rank_")]
        s["rank_min_across_defs"] = s[rank_cols].min(axis=1)
        s["rank_max_across_defs"] = s[rank_cols].max(axis=1)
        s = t.join(s, how="inner").sort_values("rank")
        s.to_csv(out_dir / f"reliability_{side}.csv")
        final[side] = s
    return final


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    res = run()
    pd.set_option("display.width", 250, "display.max_columns", 30)
    for side, s in res.items():
        print(f"\n== {side}")
        print(s[["player", "latest_team", "role", "score", "rank", "rank_min_across_defs", "rank_max_across_defs",
                 "boot_rank_p05", "boot_rank_p95", "p_top10"]].head(20).round(2).to_string())
    print(pd.read_csv(REPORTS_DIR / "model_outputs" / "excluded_inactive.csv").to_string(index=False))
