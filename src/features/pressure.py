"""Pressure detection engine.

Two independent definitions, both computed from information available BEFORE the delivery:

1. LEVERAGE (primary, data-driven): Leverage Index from the WP model = expected absolute
   win-probability swing of the next ball, mean 1. Pressure = how much the match can change.
2. RULE-BASED PRESSURE INDEX (RPI, transparent cross-check): weighted z-scores of
   - scoreboard gap (z-scored WITHIN innings)                 -> scoreboard pressure
       innings 2: required rate minus era par rate
       innings 1: runs the batting side is projected to finish BELOW era par, from an
                  expected-remaining-runs table (overs left x wickets in hand, as a share of
                  par), cross-fitted by year                                    [v2, fix A]
   - wickets lost relative to balls used                      -> resource pressure
   - wickets in the previous 12 deliveries                    -> collapse pressure
   - dot balls in the previous 12 legal deliveries            -> squeeze / build-up pressure
   - innings progress ramp (share of innings bowled)^2        -> phase pressure   [v2, fix B]
   - closeness of the contest: 1 - |2*WP - 1|                 -> match-in-balance pressure

FINAL DEFINITION (composite, see research/METHODOLOGY.md):
   pressure_score = LEV_BLEND * leverage percentile WITHIN innings + (1-LEV_BLEND) * RPI pct
   with LEV_BLEND = 0.5; 0.3 and 0.7 variants are stored for ranking sensitivity [fix D].
   Leverage percentile [fix C]: innings 1 is ranked WITHIN EACH OVER, innings 2 within the
   innings. The innings-1 WP model (AUC ~0.69) imposes its own over-by-over shape on leverage
   (highest in over 1, lowest in overs 8-15), which is model structure, not match pressure;
   ranking within the over keeps only "which situation at this stage carries more at stake".
   The innings-1 stage profile then comes from the smooth rule-based terms. Chase leverage
   (WP AUC ~0.93) keeps its genuine death-over rise. (An earlier fix-C attempt, damping
   overs 1-2 toward the over-3 median, left batting-first middle overs at 1-5% HIGH.)
   Leverage alone puts ~92% of high-pressure balls in chases (the innings-1 WP model is
   necessarily uncertain, so its swings are small). Ranking leverage within each innings keeps
   "stakes" comparable for batting-first and chasing players; RPI adds situational difficulty.
Pressure bands are percentile-based on the definition in use: HIGH = top 20%, LOW = bottom 50%.
Alternative definitions (leverage-only, RPI-only) are kept for sensitivity analysis.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.config import FEATURES_DIR, PROCESSED_DIR, REPORTS_DIR

log = logging.getLogger(__name__)

HIGH_Q = 0.80  # top 20% of deliveries = high pressure
LOW_Q = 0.50   # bottom 50% = ordinary / low pressure
RPI_WEIGHTS = {"z_scoreboard": 0.25, "z_wkt_pressure": 0.20, "z_recent_wkts": 0.15,
               "z_recent_dots": 0.10, "z_progress": 0.10, "z_closeness": 0.20}
LEV_BLEND = 0.5
LEV_BLEND_VARIANTS = (0.3, 0.7)


def load() -> pd.DataFrame:
    d = pd.read_parquet(PROCESSED_DIR / "deliveries.parquet")
    w = pd.read_parquet(FEATURES_DIR / "wp_leverage.parquet")
    return d.merge(w, on=["match_id", "innings", "innings_ball_num"], how="left", validate="1:1")


def projected_shortfall(d: pd.DataFrame) -> pd.Series:
    """Innings 1: era par minus projected total (positive = batting side tracking below par).

    projected = score + par * E[remaining runs / par | overs left, wickets in hand], where the
    expectation comes from full-length first innings of OTHER years (leave-one-year-out)."""
    i1 = d[d["innings"].eq(1)]
    full = i1[i1["max_balls"].eq(120)]
    final = full.groupby("match_id")["total_runs"].sum()
    f = full.assign(ratio=(full["match_id"].map(final) - full["score_before"]) / full["par"],
                    ovl=np.ceil(full["balls_left"] / 6).astype(int))
    out = pd.Series(np.nan, index=i1.index)
    ovl_all = np.ceil(i1["balls_left"] / 6).clip(lower=0).astype(int)
    for yr in i1["year"].unique():
        other = f[f["year"] != yr]
        tab = other.groupby(["ovl", "wkts_left"])["ratio"].agg(["mean", "size"])
        fallback = other.groupby("ovl")["ratio"].mean()
        mk = i1["year"].eq(yr)
        key = pd.MultiIndex.from_arrays([ovl_all[mk], i1.loc[mk, "wkts_left"]])
        t = tab.reindex(key)
        ratio = np.where(t["size"].fillna(0).to_numpy() >= 30, t["mean"].to_numpy(),
                         ovl_all[mk].map(fallback).to_numpy())
        projected = i1.loc[mk, "score_before"].to_numpy() + i1.loc[mk, "par"].to_numpy() * ratio
        out[mk] = i1.loc[mk, "par"].to_numpy() * i1.loc[mk, "max_balls"].to_numpy() / 120 - projected
    return out


def rule_based_components(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby(["match_id", "innings"], sort=False)
    c = pd.DataFrame(index=d.index)
    par_rate = d["par"] / 20
    rrr = d["rrr"].clip(upper=36)
    gap2 = pd.Series(np.where(d["innings"].eq(2), (rrr - par_rate).fillna(0).clip(-10, 30), 0.0), index=d.index)
    gap1 = projected_shortfall(d).reindex(d.index).clip(-40, 60)
    c["shortfall_inn1"] = gap1.fillna(0)
    c["rrr_gap_inn2"] = gap2
    # scoreboard pressure: each innings' raw gap z-scored within its own innings
    is1 = d["innings"].eq(1)
    z1 = (gap1 - gap1[is1].mean()) / gap1[is1].std(ddof=0)
    z2 = (gap2 - gap2[~is1].mean()) / gap2[~is1].std(ddof=0)
    c["scoreboard"] = np.where(is1, z1, z2)
    used = (d["max_balls"] - d["balls_left"]).clip(lower=1)
    # wickets lost per 20 balls used, damped early in the innings
    c["wkt_pressure"] = (10 - d["wkts_left"]) / (used / 20 + 1)
    c["recent_wkts"] = g["is_wicket"].transform(lambda s: s.astype(int).shift(1).rolling(12, min_periods=1).sum()).fillna(0)
    dots = d["is_dot"].astype(int).where(d["is_legal"])
    c["recent_dots"] = dots.groupby([d["match_id"], d["innings"]]).transform(
        lambda s: s.shift(1).rolling(12, min_periods=1).mean()).fillna(0)
    c["progress"] = (used / d["max_balls"]).clip(upper=1) ** 2
    c["closeness"] = 1 - (2 * d["wp_before"] - 1).abs()
    return c


def leverage_percentile(d: pd.DataFrame) -> pd.Series:
    """Fix C: innings 1 ranked within each over, innings 2 within the innings (see module doc)."""
    inn1 = d["innings"].eq(1)
    pct = pd.Series(np.nan, index=d.index)
    pct[inn1] = d[inn1].groupby("overid")["leverage"].rank(pct=True)
    pct[~inn1] = d.loc[~inn1, "leverage"].rank(pct=True)
    return pct


def pressure_table(d: pd.DataFrame) -> pd.DataFrame:
    comp = rule_based_components(d)
    z = (comp - comp.mean()) / comp.std(ddof=0)
    z.columns = [f"z_{k}" for k in comp.columns]
    rpi = sum(w * z[k] for k, w in RPI_WEIGHTS.items())
    out = pd.concat([d[["match_id", "innings", "innings_ball_num"]], comp, z], axis=1)
    out["leverage"] = d["leverage"]
    out["rpi"] = rpi
    out["rpi_pct"] = rpi.rank(pct=True)
    out["lev_pct"] = d["leverage"].rank(pct=True)
    out["lev_pct_inn"] = leverage_percentile(d)
    band = lambda pct: np.select([pct >= HIGH_Q, pct < LOW_Q], ["high", "low"], "medium")
    blend = lambda b: (b * out["lev_pct_inn"] + (1 - b) * out["rpi_pct"]).rank(pct=True)
    out["pressure_score"] = blend(LEV_BLEND)
    out["pressure_band"] = band(out["pressure_score"])       # FINAL
    for b in LEV_BLEND_VARIANTS:                               # sensitivity: blend (fix D)
        out[f"pressure_band_l{int(b * 100)}"] = band(blend(b))
    out["pressure_band_lev"] = band(out["lev_pct"])            # sensitivity: leverage only
    out["pressure_band_rpi"] = band(out["rpi_pct"])            # sensitivity: rule-based only
    return out


def compare_definitions(d: pd.DataFrame, p: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Evidence that pressure bands separate situations, and agreement between definitions."""
    x = d.join(p[["pressure_band", "pressure_band_lev", "pressure_band_rpi"]])
    x = x[x["is_batter_ball"]]

    def outcome_profile(col: str) -> pd.DataFrame:
        return (x.groupby(col).agg(balls=("runs", "size"), strike_rate=("runs", lambda s: 100 * s.mean()),
                                  dismissal_pct=("striker_out", lambda s: 100 * s.mean()),
                                  dot_pct=("is_dot", lambda s: 100 * s.mean()),
                                  boundary_pct=("is_boundary", lambda s: 100 * s.mean()))
                 .reindex(["low", "medium", "high"]).round(2))

    hi = {k: p[c].eq("high") for k, c in [("final", "pressure_band"), ("leverage", "pressure_band_lev"), ("rpi", "pressure_band_rpi")]}
    jac = lambda a, b: (a & b).sum() / (a | b).sum()
    summary = pd.DataFrame({
        "definition": list(hi),
        "share_high_in_innings2": [d.loc[h, "innings"].eq(2).mean() for h in hi.values()],
        "share_high_in_death": [d.loc[h, "phase"].eq("death").mean() for h in hi.values()],
        "jaccard_vs_final": [jac(h, hi["final"]) for h in hi.values()],
    }).round(3)
    summary["spearman_rpi_vs_leverage"] = round(p["rpi"].corr(p["leverage"], method="spearman"), 3)
    phase_mix = (pd.crosstab([d["innings"], d["phase"]], p["pressure_band"], normalize="index") * 100).round(1)
    return {"profile_final": outcome_profile("pressure_band"), "profile_leverage": outcome_profile("pressure_band_lev"),
            "profile_rpi": outcome_profile("pressure_band_rpi"), "summary": summary, "phase_mix_final": phase_mix}


def run() -> pd.DataFrame:
    d = load()
    p = pressure_table(d)
    p.to_parquet(FEATURES_DIR / "pressure.parquet", index=False)
    res = compare_definitions(d, p)
    outdir = REPORTS_DIR / "model_outputs"
    outdir.mkdir(parents=True, exist_ok=True)
    for k, v in res.items():
        v.to_csv(outdir / f"pressure_{k}.csv")
        log.info("\n== %s\n%s", k, v.to_string())
    return p


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run()
