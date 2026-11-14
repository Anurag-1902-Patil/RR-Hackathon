"""Opponent-adjusted player ratings with a pressure term (ridge / Gaussian-prior regression).

Per-ball value (runs, context-adjusted; positive = good for the player being rated):
    batting  v = (bat runs - xR) - C * (striker out - xOut)
    bowling  v = (xRconc - bowler runs) + C * (bowler wicket - xWkt)
where C = context dismissal cost: expected remaining runs with w wickets in hand minus with w-1,
for the same overs left, scaled to the scoring environment (resources table, full first innings).

Model (batting; bowling is the mirror image):
    v_ball = mu + a_batter + d_batter * HIGH + b_bowler + e_bowler * HIGH + noise
a = usual (all-situation) ability, d = pressure delta vs own baseline, a + d = performance under
pressure. Opponent effects (b, e) adjust for the quality of bowlers actually faced, which also
calibrates competition strength through players who cross competitions. Ridge penalties are
zero-mean Gaussian priors: small samples shrink to average, pressure deltas shrink to zero.
Penalties are tuned OUT OF TIME (fit 2022-24, score 2025-26).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.linear_model import Ridge

from src.config import FEATURES_DIR, PROCESSED_DIR, REPORTS_DIR, TEST_YEARS, TRAIN_YEARS, VALID_YEARS
from src.models.expected import env_par

log = logging.getLogger(__name__)
KEY = ["match_id", "innings", "innings_ball_num"]


def load(band_col: str = "pressure_band") -> pd.DataFrame:
    d = pd.read_parquet(PROCESSED_DIR / "deliveries.parquet")
    x = pd.read_parquet(FEATURES_DIR / "expected.parquet")
    w = pd.read_parquet(FEATURES_DIR / "wp_leverage.parquet")
    p = pd.read_parquet(FEATURES_DIR / "pressure.parquet")[KEY + ["pressure_score", "pressure_band", "pressure_band_l30",
                                                                    "pressure_band_l70", "pressure_band_lev", "pressure_band_rpi"]]
    d = d.merge(x, on=KEY, validate="1:1").merge(w, on=KEY, validate="1:1").merge(p, on=KEY, validate="1:1")
    d["high"] = d[band_col].eq("high").astype(float)
    return d


def wicket_cost(d: pd.DataFrame) -> pd.Series:
    """Context run cost of losing a wicket (resources table from full-length first innings)."""
    i1 = d[d["innings"].eq(1) & d["max_balls"].eq(120)]
    final = i1.groupby("match_id")["total_runs"].sum()
    ep = env_par(d)
    f = pd.DataFrame({"ovl": np.ceil(i1["balls_left"] / 6).astype(int), "w": i1["wkts_left"],
                      "ratio": (i1["match_id"].map(final) - i1["score_before"]) / ep[i1.index]})
    tab = f.groupby(["ovl", "w"])["ratio"].agg(["mean", "size"])
    tab = tab[tab["size"] >= 30]["mean"].unstack()
    # enforce monotone in wickets (more wickets in hand never worse) and fill gaps
    tab[0] = 0.0
    tab = tab.reindex(columns=range(0, 11)).interpolate(axis=1, limit_direction="both").cummax(axis=1)
    tab = tab.reindex(range(0, 21)).interpolate(limit_direction="both")
    ovl = np.ceil(d["balls_left"] / 6).clip(0, 20).astype(int).to_numpy()
    w = d["wkts_left"].clip(1, 10).to_numpy()
    arr = tab.to_numpy()
    cost = (arr[ovl, w] - arr[ovl, w - 1]) * ep.to_numpy()
    return pd.Series(np.clip(cost, 0, 40), index=d.index)


def ball_values(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["wkt_cost"] = wicket_cost(d)
    bat = d["is_batter_ball"]
    d["v_bat"] = np.where(bat, (d["runs"] - d["x_bat_runs"]) - d["wkt_cost"] * (d["striker_out"].astype(float) - d["x_bat_out"]), np.nan)
    d["v_bowl"] = (d["x_bowl_runs"] - d["bowler_runs"]) + d["wkt_cost"] * (d["bowler_wicket"].astype(float) - d["x_bowl_wkt"])
    return d


@dataclass
class Design:
    X: sp.csr_matrix
    cols: pd.DataFrame  # role, player_id, term


def design(rows: pd.DataFrame, subject: str, opponent: str, delta_scale: float, opp_delta: bool = True,
           with_delta: bool = True) -> Design:
    """Sparse one-hot design: subject main + subject x HIGH (+ opponent main/x HIGH)."""
    blocks, meta, n = [], [], len(rows)
    high = rows["high"].to_numpy()
    for role, col in (("subject", subject), ("opponent", opponent)):
        ids, codes = np.unique(rows[col].to_numpy(), return_inverse=True)
        main = sp.csr_matrix((np.ones(n), (np.arange(n), codes)), shape=(n, len(ids)))
        blocks.append(main); meta.append(pd.DataFrame({"role": role, "player_id": ids, "term": "main"}))
        if with_delta and (role == "subject" or opp_delta):
            dl = sp.csr_matrix((high * delta_scale, (np.arange(n), codes)), shape=(n, len(ids)))
            blocks.append(dl); meta.append(pd.DataFrame({"role": role, "player_id": ids, "term": "delta"}))
    return Design(sp.hstack(blocks).tocsr(), pd.concat(meta, ignore_index=True))


def fit(rows: pd.DataFrame, target: str, subject: str, opponent: str, alpha: float, delta_scale: float,
        with_delta: bool = True) -> pd.DataFrame:
    dz = design(rows, subject, opponent, delta_scale, with_delta=with_delta)
    m = Ridge(alpha=alpha, fit_intercept=True, solver="sparse_cg", max_iter=2000, tol=1e-6)
    m.fit(dz.X, rows[target].to_numpy())
    coef = dz.cols.assign(coef=m.coef_)
    coef.loc[coef["term"].eq("delta"), "coef"] *= delta_scale  # back to runs-per-ball units
    return coef


def predict(coef: pd.DataFrame, rows: pd.DataFrame, subject: str, opponent: str, use_delta: bool = True) -> np.ndarray:
    pred = np.zeros(len(rows))
    for role, col in (("subject", subject), ("opponent", opponent)):
        c = coef[coef["role"].eq(role)].pivot(index="player_id", columns="term", values="coef")
        pred += rows[col].map(c["main"]).fillna(0).to_numpy()
        if use_delta and "delta" in c:
            pred += rows[col].map(c["delta"]).fillna(0).to_numpy() * rows["high"].to_numpy()
    return pred


SIDES = {"batting": ("v_bat", "striker_id", "bowler_id", "is_batter_ball"),
         "bowling": ("v_bowl", "bowler_id", "striker_id", None)}


def tune(d: pd.DataFrame, side: str, alphas=(300, 600, 1000, 1500, 2000, 3000), scales=(0.0, 0.1, 0.25, 0.5, 1.0)) -> pd.DataFrame:
    """Out-of-time tuning: fit on train years, score MSE on later years (all balls and HIGH balls).
    scale = 0 means no pressure delta at all (the 'pressure is not a trait' null model)."""
    target, subj, opp, flt = SIDES[side]
    r = d[d[flt]] if flt else d
    tr = r[r["year"].isin(TRAIN_YEARS)]
    te = r[r["year"].isin(VALID_YEARS + TEST_YEARS)]
    y = te[target].to_numpy()
    hi = te["high"].to_numpy() == 1
    rows = [{"alpha": None, "delta_scale": None, "mse_all": np.mean(y ** 2), "mse_high": np.mean(y[hi] ** 2), "model": "null (0)"}]
    for a in alphas:
        for s in scales:
            coef = fit(tr, target, subj, opp, a, max(s, 1e-9))
            p = predict(coef, te, subj, opp, use_delta=s > 0)
            rows.append({"alpha": a, "delta_scale": s, "mse_all": np.mean((y - p) ** 2), "mse_high": np.mean((y[hi] - p[hi]) ** 2),
                         "model": "ridge"})
    out = pd.DataFrame(rows)
    out["skill_all_pct"] = 100 * (1 - out["mse_all"] / out.loc[0, "mse_all"])
    out["skill_high_pct"] = 100 * (1 - out["mse_high"] / out.loc[0, "mse_high"])
    return out


HIGH_SKILL_TOLERANCE = 0.97
CHOSEN: dict[str, tuple[float, float]] = {}


def choose(t: pd.DataFrame) -> tuple[float, float]:
    """alpha = best out-of-time skill on all balls. Delta scale = LARGEST scale > 0 whose out-of-time
    skill on HIGH balls is within HIGH_SKILL_TOLERANCE of the best at that alpha, i.e. keep as much
    measured pressure signal as the out-of-time evidence tolerates."""
    r = t[t["model"].eq("ridge")]
    alpha = r.loc[r["skill_all_pct"].idxmax(), "alpha"]
    ra = r[r["alpha"].eq(alpha)]
    best = ra["skill_high_pct"].max()
    ok = ra[(ra["delta_scale"] > 0) & (ra["skill_high_pct"] >= HIGH_SKILL_TOLERANCE * best)]
    scale = ok["delta_scale"].max() if len(ok) else ra[ra["delta_scale"] > 0]["delta_scale"].min()
    return float(alpha), float(scale)


def fit_side(d: pd.DataFrame, side: str, alpha: float, scale: float) -> pd.DataFrame:
    """Final fit on all years; returns usual ability, pressure delta and pressure level (runs/ball)."""
    target, subj, opp, flt = SIDES[side]
    r = d[d[flt]] if flt else d
    coef = fit(r, target, subj, opp, alpha, scale)
    out = coef[coef["role"].eq("subject")].pivot(index="player_id", columns="term", values="coef")
    out = out.rename(columns={"main": "usual", "delta": "pressure_delta"})
    out["pressure_level"] = out["usual"] + out["pressure_delta"]
    return out


PRESSURE_ALPHA: dict[str, float] = {}


def tune_pressure_only(d: pd.DataFrame, side: str, alphas=(300, 600, 1000, 2000, 3000, 5000, 10000)) -> pd.DataFrame:
    """HIGH-balls-only ridge (subject + opponent, shrink to league mean), tuned out of time on HIGH balls."""
    target, subj, opp, flt = SIDES[side]
    r = d[(d[flt] if flt else True) & d["high"].eq(1)]
    tr, te = r[r["year"].isin(TRAIN_YEARS)], r[r["year"].isin(VALID_YEARS + TEST_YEARS)]
    y = te[target].to_numpy()
    rows = [{"alpha": None, "mse_high": np.mean(y ** 2)}]
    for a in alphas:
        coef = fit(tr, target, subj, opp, a, 1.0, with_delta=False)
        rows.append({"alpha": a, "mse_high": np.mean((y - predict(coef, te, subj, opp, use_delta=False)) ** 2)})
    out = pd.DataFrame(rows)
    out["skill_high_pct"] = 100 * (1 - out["mse_high"] / out.loc[0, "mse_high"])
    return out


def fit_pressure_only(d: pd.DataFrame, side: str, alpha: float) -> pd.Series:
    target, subj, opp, flt = SIDES[side]
    r = d[(d[flt] if flt else True) & d["high"].eq(1)]
    coef = fit(r, target, subj, opp, alpha, 1.0, with_delta=False)
    return coef[coef["role"].eq("subject")].set_index("player_id")["coef"].rename("pressure_perf")


def clutch_variance(d: pd.DataFrame, side: str, min_high: int = 60, min_low: int = 150) -> dict[str, float]:
    """Empirical-Bayes (method of moments) estimate of the true between-player SD of the pressure
    delta: var(raw delta) - mean(sampling variance). tau ~ 0 => no detectable clutch variation."""
    target, subj, _, flt = SIDES[side]
    r = d[d[flt]] if flt else d
    g = r.groupby([subj, "high"])[target].agg(["mean", "var", "size"]).unstack("high")
    g = g[(g[("size", 1.0)] >= min_high) & (g[("size", 0.0)] >= min_low)]
    raw = g[("mean", 1.0)] - g[("mean", 0.0)]
    samp = g[("var", 1.0)] / g[("size", 1.0)] + g[("var", 0.0)] / g[("size", 0.0)]
    tau2 = raw.var() - samp.mean()
    return {"side": side, "players": int(len(raw)), "sd_raw_delta": float(raw.std()), "mean_sampling_sd": float(np.sqrt(samp.mean())),
            "tau_true_sd": float(np.sqrt(max(tau2, 0.0))), "tau2": float(tau2),
            "reliability_of_raw_delta": float(max(tau2, 0.0) / raw.var())}


def run(band_col: str = "pressure_band", tune_first: bool = True, d: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    if d is None:
        d = ball_values(load(band_col))
    if band_col == "pressure_band" and tune_first:
        d[KEY + ["wkt_cost", "v_bat", "v_bowl", "high"]].to_parquet(FEATURES_DIR / "ball_values.parquet", index=False)
    res = {}
    for side in SIDES:
        if tune_first:
            t = tune(d, side)
            t.to_csv(REPORTS_DIR / "model_outputs" / f"ratings_tuning_{side}.csv", index=False)
            CHOSEN[side] = choose(t)
        alpha, scale = CHOSEN[side]
        log.info("%s: alpha=%s delta_scale=%s", side, alpha, scale)
        out = fit_side(d, side, alpha, scale)
        if tune_first:
            tp = tune_pressure_only(d, side)
            tp.to_csv(REPORTS_DIR / "model_outputs" / f"ratings_tuning_pressure_only_{side}.csv", index=False)
            PRESSURE_ALPHA[side] = float(tp.loc[tp["skill_high_pct"].idxmax(), "alpha"])
            log.info("%s pressure-only alpha=%s\n%s", side, PRESSURE_ALPHA[side], tp.round(4).to_string(index=False))
        out = out.join(fit_pressure_only(d, side, PRESSURE_ALPHA[side]))
        res[side] = out
    if tune_first:
        cv = pd.DataFrame([clutch_variance(d, s) for s in SIDES])
        cv.to_csv(REPORTS_DIR / "model_outputs" / "clutch_variance.csv", index=False)
        log.info("clutch variance:\n%s", cv.round(4).to_string(index=False))
    return res


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run()
