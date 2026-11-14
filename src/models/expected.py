"""Context expectation models: expected runs / dismissal per ball for batting and bowling.

Expectations use ONLY the match situation and delivery context, never player identity, so a
player's residual (actual - expected) measures their contribution relative to an average
player in the same situation.

Competition fairness: no T20I tier variable is used. A tier dummy would set "average for
an associate match" equal to "average for an IPL match" and inflate weak-competition players.
League strength is instead calibrated by the opponent-adjusted ridge model (src/models/ratings.py)
through players who cross competitions. Only the IPL scoring environment by season (impact-player
era, rising par) is modelled directly via `env`.

Validation: chronological (train 2022-24, valid 2025, test 2026) against a simple baseline
(mean by innings x over). Production predictions are leave-one-year-out cross-fitted.
"""
from __future__ import annotations

import json
import logging

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, mean_absolute_error, mean_squared_error

from src.config import FEATURES_DIR, MODELS_DIR, PROCESSED_DIR, REPORTS_DIR, SEED, TEST_YEARS, TRAIN_YEARS, VALID_YEARS

log = logging.getLogger(__name__)

CAT = ["bowling_type", "pace_or_spin", "batting_type", "matchup"]
ENV_WINDOW = 60


def env_par(d: pd.DataFrame) -> pd.Series:
    """Scoring environment per match: rolling mean full-length first-innings total over the
    previous ENV_WINDOW matches of the same environment (IPL vs all internationals pooled).
    Strictly prior matches only; pooled internationals so it carries no T20I tier/quality split."""
    i1 = d[d["innings"].eq(1) & d["max_balls"].eq(120)].groupby("match_id")["total_runs"].sum()
    m = d.groupby("match_id").agg(date=("match_date", "first"), ipl=("is_ipl", "first")).sort_values("date")
    m["inn1"] = m.index.map(i1)
    m["env_par"] = m.groupby("ipl")["inn1"].transform(lambda s: s.shift(1).rolling(ENV_WINDOW, min_periods=1).mean())
    return d["match_id"].map(m["env_par"].fillna(160.0))


def frame(d: pd.DataFrame) -> pd.DataFrame:
    X = pd.DataFrame(index=d.index)
    X["innings"] = d["innings"]
    X["overid"] = d["overid"]
    X["balls_left"] = d["balls_left"]
    X["wkts_left"] = d["wkts_left"]
    X["frac_left"] = d["balls_left"] / d["max_balls"]
    used = (d["max_balls"] - d["balls_left"]).clip(lower=1)
    X["crr_vs_par"] = (d["score_before"] * 6 / used - d["par"] / 20).where(d["max_balls"] > d["balls_left"], 0)
    X["rrr_vs_par"] = np.where(d["innings"].eq(2), (d["rrr"].clip(upper=36) - d["par"] / 20), np.nan)
    X["need_frac"] = np.where(d["innings"].eq(2), d["runs_needed"] / d["target"], np.nan)
    X["is_ipl"] = d["is_ipl"].astype(int)
    X["env_par"] = env_par(d)
    X["bowling_type"] = d["bowling_type"]
    X["pace_or_spin"] = d["pace_or_spin"]
    X["batting_type"] = d["batting_type"]
    arm = np.where(d["bowling_type"].str.startswith("Left"), "L", "R")
    X["matchup"] = d["batting_type"] + "_v_" + arm + "_" + d["pace_or_spin"]
    for c in CAT:
        X[c] = X[c].astype("category")
    return X


SPECS = {
    # name: (row filter, target column, objective, drop features)
    "bat_runs": ("is_batter_ball", "runs", "regression", []),
    "bat_out": ("is_batter_ball", "striker_out", "binary", []),
    "bowl_runs": (None, "bowler_runs", "regression", ["bowling_type", "pace_or_spin", "matchup"]),
    "bowl_wkt": (None, "bowler_wicket", "binary", ["bowling_type", "pace_or_spin", "matchup"]),
}


def _rows(d: pd.DataFrame, flt: str | None) -> pd.DataFrame:
    return d if flt is None else d[d[flt]]


def _model(obj: str) -> lgb.LGBMModel:
    kw = dict(n_estimators=300, learning_rate=0.03, num_leaves=31, min_child_samples=500,
              subsample=0.8, subsample_freq=1, colsample_bytree=0.9, reg_lambda=5.0, random_state=SEED, verbose=-1)
    return lgb.LGBMClassifier(**kw) if obj == "binary" else lgb.LGBMRegressor(**kw)


def _predict(m, X: pd.DataFrame, obj: str) -> np.ndarray:
    return m.predict_proba(X)[:, 1] if obj == "binary" else m.predict(X)


def _score(y, p, obj) -> dict:
    if obj == "binary":
        return {"log_loss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)), "mean_pred": float(np.mean(p)), "mean_obs": float(np.mean(y))}
    return {"mae": mean_absolute_error(y, p), "rmse": float(np.sqrt(mean_squared_error(y, p))),
            "mean_pred": float(np.mean(p)), "mean_obs": float(np.mean(y))}


def evaluate(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, (flt, tgt, obj, drop) in SPECS.items():
        r = _rows(d, flt)
        X = frame(r).drop(columns=drop)
        y = r[tgt].astype(float)
        tr, va, te = (r["year"].isin(Y) for Y in (TRAIN_YEARS, VALID_YEARS, TEST_YEARS))
        base = r[tr].groupby(["innings", "overid"])[tgt].mean()
        m = _model(obj).fit(X[tr], y[tr])
        for split, mk in (("valid", va), ("test", te)):
            b = pd.MultiIndex.from_frame(r.loc[mk, ["innings", "overid"]]).map(base.to_dict().get)
            b = pd.Series(b, index=r.index[mk]).fillna(y[tr].mean()).to_numpy()
            rows.append({"model": name, "kind": "baseline(innings x over mean)", "split": split, **_score(y[mk], b, obj)})
            rows.append({"model": name, "kind": "lightgbm(context)", "split": split, **_score(y[mk], _predict(m, X[mk], obj), obj)})
    out = pd.DataFrame(rows)
    out.to_csv(REPORTS_DIR / "model_outputs" / "expected_models_evaluation.csv", index=False)
    return out


def crossfit(d: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-year-out expectations for every delivery."""
    out = pd.DataFrame(index=d.index)
    for name, (flt, tgt, obj, drop) in SPECS.items():
        r = _rows(d, flt)
        X = frame(r).drop(columns=drop)
        pred = pd.Series(np.nan, index=r.index)
        for yr in sorted(r["year"].unique()):
            mk = r["year"].eq(yr)
            m = _model(obj).fit(X[~mk], r.loc[~mk, tgt].astype(float))
            pred[mk] = _predict(m, X[mk], obj)
        out["x_" + name] = pred
    return out


def recentre(d: pd.DataFrame, x: pd.DataFrame) -> pd.DataFrame:
    """Season-environment normalisation: scale expectations so that, within each (year, IPL/intl)
    environment, mean expected = mean observed. Players are then measured against the average
    player of that season (league-wide level only; no player-specific information)."""
    x = x.copy()
    env = d["year"].astype(str) + np.where(d["is_ipl"], "_IPL", "_INTL")
    for name, (flt, tgt, _, _) in SPECS.items():
        mk = d[flt] if flt else pd.Series(True, index=d.index)
        col = "x_" + name
        ratio = (d.loc[mk, tgt].astype(float).groupby(env[mk]).mean() / x.loc[mk, col].groupby(env[mk]).mean())
        x.loc[mk, col] = x.loc[mk, col] * env[mk].map(ratio)
        x.loc[mk, "recentre_" + name] = env[mk].map(ratio)
    return x


def run() -> pd.DataFrame:
    d = pd.read_parquet(PROCESSED_DIR / "deliveries.parquet")
    ev = evaluate(d)
    log.info("\n%s", ev.round(4).to_string(index=False))
    x = recentre(d, crossfit(d))
    adj = x.filter(like="recentre_").groupby(d["year"].astype(str) + np.where(d["is_ipl"], "_IPL", "_INTL")).first()
    adj.round(4).to_csv(REPORTS_DIR / "model_outputs" / "expected_recentre_factors.csv")
    log.info("recentre factors:\n%s", adj.round(3).to_string())
    x = x.drop(columns=adj.columns)
    res = pd.concat([d[["match_id", "innings", "innings_ball_num"]], x], axis=1)
    res.to_parquet(FEATURES_DIR / "expected.parquet", index=False)
    (MODELS_DIR / "expected_model_card.json").write_text(json.dumps({
        "models": {k: {"rows": v[0] or "all deliveries", "target": v[1], "objective": v[2], "dropped": v[3]} for k, v in SPECS.items()},
        "features": list(frame(d.head(50)).columns), "algorithm": "LightGBM", "crossfit": "leave-one-year-out",
        "no_tier_feature": True, "seed": SEED}, indent=2))
    return res


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    r = run()
    print(r.describe().round(4).to_string())
