"""Pressure detection engine.

Two independent definitions, both computed from information available BEFORE the delivery:

1. LEVERAGE (primary, data-driven): Leverage Index from the WP model = expected absolute
   win-probability swing of the next ball, mean 1. Pressure = how much the match can change.
2. RULE-BASED PRESSURE INDEX (RPI, transparent cross-check): weighted z-scores of
   - required-rate gap vs era par rate (chases only)         -> scoreboard pressure
   - wickets lost relative to balls used                      -> resource pressure
   - wickets in the previous 12 deliveries                    -> collapse pressure
   - dot balls in the previous 12 legal deliveries            -> squeeze / build-up pressure
   - death-overs indicator                                    -> phase pressure
   - closeness of the contest: 1 - |2*WP - 1|                 -> match-in-balance pressure

FINAL DEFINITION (composite, see research/METHODOLOGY.md):
   pressure_score = 0.5 * leverage percentile WITHIN innings + 0.5 * RPI percentile
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
RPI_WEIGHTS = {"z_rrr_gap": 0.25, "z_wkt_pressure": 0.20, "z_recent_wkts": 0.15,
               "z_recent_dots": 0.10, "z_death": 0.10, "z_closeness": 0.20}


def load() -> pd.DataFrame:
    d = pd.read_parquet(PROCESSED_DIR / "deliveries.parquet")
    w = pd.read_parquet(FEATURES_DIR / "wp_leverage.parquet")
    return d.merge(w, on=["match_id", "innings", "innings_ball_num"], how="left", validate="1:1")


def rule_based_components(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby(["match_id", "innings"], sort=False)
    c = pd.DataFrame(index=d.index)
    par_rate = d["par"] / 20
    rrr = d["rrr"].clip(upper=36)
    c["rrr_gap"] = np.where(d["innings"].eq(2), (rrr - par_rate).fillna(0).clip(-10, 30), 0.0)
    used = (d["max_balls"] - d["balls_left"]).clip(lower=1)
    # wickets lost per 20 balls used, damped early in the innings
    c["wkt_pressure"] = (10 - d["wkts_left"]) / (used / 20 + 1)
    c["recent_wkts"] = g["is_wicket"].transform(lambda s: s.astype(int).shift(1).rolling(12, min_periods=1).sum()).fillna(0)
    dots = d["is_dot"].astype(int).where(d["is_legal"])
    c["recent_dots"] = dots.groupby([d["match_id"], d["innings"]]).transform(
        lambda s: s.shift(1).rolling(12, min_periods=1).mean()).fillna(0)
    c["death"] = d["phase"].eq("death").astype(float)
    c["closeness"] = 1 - (2 * d["wp_before"] - 1).abs()
    return c


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
    out["lev_pct_inn"] = d.groupby("innings")["leverage"].rank(pct=True)
    out["pressure_score"] = (0.5 * out["lev_pct_inn"] + 0.5 * out["rpi_pct"]).rank(pct=True)
    band = lambda pct: np.select([pct >= HIGH_Q, pct < LOW_Q], ["high", "low"], "medium")
    out["pressure_band"] = band(out["pressure_score"])       # FINAL
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
