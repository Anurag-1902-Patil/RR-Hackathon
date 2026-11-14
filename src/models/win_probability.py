"""T20 win-probability (WP) models, Win Probability Added (WPA) and Leverage Index (LI).

Design
------
* Two models: innings 1 (setting) and innings 2 (chasing). WP is always from the
  BATTING team's perspective at the moment BEFORE the delivery.
* Baseline: logistic regression on engineered state features.
  Candidate: LightGBM with monotonic constraints (more runs needed -> lower WP, etc.).
* Evaluation: chronological split (train 2022-24, valid 2025, test 2026), matches kept whole.
* Production values: leave-one-year-out cross-fitting, so no delivery's WP comes from a
  model that saw that match.
* WPA: WP_after - WP_before for the batting side (bowler receives the negative).
* Leverage Index (Tango-style): expected absolute WP swing of the next delivery given the
  state, divided by its average over all deliveries. LI = 1 is an average-pressure ball.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import MODELS_DIR, PROCESSED_DIR, REPORTS_DIR, SEED, TEST_YEARS, TRAIN_YEARS, VALID_YEARS

log = logging.getLogger(__name__)
TIERS = ["IPL", "T20I_full", "T20I_assoc", "A_team"]

# ---------------------------------------------------------------- features

def features(df: pd.DataFrame, innings: int) -> pd.DataFrame:
    """State features available before the delivery. Works on real or hypothetical states."""
    X = pd.DataFrame(index=df.index)
    balls_left = df["balls_left"].clip(lower=0).astype(float)
    X["balls_left"] = balls_left
    X["wkts_left"] = df["wkts_left"].astype(float)
    for t in TIERS[1:]:
        X[f"tier_{t}"] = (df["tier"] == t).astype(float)
    par = df["par"].astype(float)
    frac_left = balls_left / df["max_balls"].astype(float)
    X["frac_left"] = frac_left
    X["wkts_x_frac"] = X["wkts_left"] * frac_left
    if innings == 1:
        legal = (df["max_balls"] - balls_left).astype(float)
        X["score_vs_par"] = df["score_before"].astype(float) - par * (1 - frac_left)
        crr = np.where(legal > 0, df["score_before"] * 6 / legal.replace(0, np.nan), par / 20)
        # projection with wicket-dependent acceleration damped toward par rate
        X["proj_vs_par"] = df["score_before"] + crr * balls_left / 6 * (0.6 + 0.04 * X["wkts_left"]) - par * df["max_balls"] / 120
        X["proj_x_frac"] = X["proj_vs_par"] * (1 - frac_left)
    else:
        rn = df["runs_needed"].astype(float)
        par_rate = par / 20  # par runs per over
        rrr = np.where(balls_left > 0, rn * 6 / balls_left.replace(0, np.nan), 36.0)
        X["rrr_vs_par"] = (rrr - par_rate).clip(-15, 30)
        X["rrr_vs_par_sq"] = X["rrr_vs_par"] ** 2 * np.sign(X["rrr_vs_par"])
        X["need_frac"] = (rn / df["target"].astype(float)).clip(-0.5, 1.5)
        X["need_per_wkt"] = (rn / X["wkts_left"].clip(lower=1)).clip(-20, 250)
        X["rrr_x_wkts"] = X["rrr_vs_par"] * X["wkts_left"]
        X["target_vs_par"] = df["target"].astype(float) - par
    return X


def monotone(innings: int, cols: list[str]) -> list[int]:
    rules = ({"wkts_left": 1, "score_vs_par": 1, "proj_vs_par": 1} if innings == 1
             else {"wkts_left": 1, "rrr_vs_par": -1, "rrr_vs_par_sq": -1, "need_per_wkt": -1, "need_frac": -1})
    return [rules.get(c, 0) for c in cols]


@dataclass
class WPModel:
    innings: int
    kind: str  # "lgbm" | "logit"
    model: object = None
    cols: list[str] | None = None

    def fit(self, df: pd.DataFrame, n_estimators: int = 400) -> "WPModel":
        X, y = features(df, self.innings), df["batting_team_won"].astype(int)
        self.cols = list(X.columns)
        if self.kind == "lgbm":
            self.model = lgb.LGBMClassifier(
                n_estimators=n_estimators, learning_rate=0.03, num_leaves=31, min_child_samples=200,
                subsample=0.8, subsample_freq=1, colsample_bytree=0.9, reg_lambda=1.0,
                monotone_constraints=monotone(self.innings, self.cols), random_state=SEED, verbose=-1)
        else:
            self.model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
        self.model.fit(X, y)
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(features(df, self.innings)[self.cols])[:, 1]


# ---------------------------------------------------------------- data

def training_rows(d: pd.DataFrame) -> pd.DataFrame:
    """Decided, non-super-over matches with both innings present."""
    both = d.groupby("match_id")["innings"].nunique().eq(2)
    tied = d[d["match_id"].isin(pd.read_parquet(PROCESSED_DIR / "super_overs.parquet")["match_id"])]["match_id"].unique()
    keep = d["decided"] & d["match_id"].map(both) & ~d["match_id"].isin(tied)
    return d[keep]


def metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    bins = np.clip((p * 10).astype(int), 0, 9)
    ece = sum(abs(p[bins == b].mean() - y[bins == b].mean()) * (bins == b).mean() for b in range(10) if (bins == b).any())
    return {"brier": brier_score_loss(y, p), "log_loss": log_loss(y, p), "auc": roc_auc_score(y, p),
            "ece": float(ece), "n_balls": int(len(y))}


def evaluate(d: pd.DataFrame) -> pd.DataFrame:
    """Chronological evaluation of both model kinds for both innings."""
    t = training_rows(d)
    rows, calib = [], []
    for inn in (1, 2):
        ti = t[t["innings"] == inn]
        tr, va, te = (ti[ti["year"].isin(Y)] for Y in (TRAIN_YEARS, VALID_YEARS, TEST_YEARS))
        # always-0.5 / rate baseline
        for split, part in (("valid", va), ("test", te)):
            y = part["batting_team_won"].astype(int).to_numpy()
            rows.append({"innings": inn, "model": "constant(base rate)", "split": split,
                         **metrics(y, np.full(len(y), tr["batting_team_won"].mean()))})
        for kind in ("logit", "lgbm"):
            m = WPModel(inn, kind).fit(tr)
            for split, part in (("valid", va), ("test", te)):
                y, p = part["batting_team_won"].astype(int).to_numpy(), m.predict(part)
                rows.append({"innings": inn, "model": kind, "split": split, **metrics(y, p)})
                if split == "test":
                    cb = pd.DataFrame({"p": p, "y": y}).assign(bin=lambda x: (x.p * 10).astype(int).clip(0, 9))
                    calib.append(cb.groupby("bin").agg(pred=("p", "mean"), obs=("y", "mean"), n=("y", "size"))
                                 .reset_index().assign(innings=inn, model=kind))
    res = pd.DataFrame(rows)
    REPORTS_DIR.joinpath("model_outputs").mkdir(parents=True, exist_ok=True)
    res.to_csv(REPORTS_DIR / "model_outputs" / "wp_evaluation.csv", index=False)
    pd.concat(calib).to_csv(REPORTS_DIR / "model_outputs" / "wp_calibration_test.csv", index=False)
    return res


# ---------------------------------------------------------------- cross-fitted WP for every delivery

def crossfit_wp(d: pd.DataFrame, kind: str = "lgbm") -> tuple[pd.Series, dict]:
    """Leave-one-year-out WP for every delivery, plus per-year models for hypothetical states."""
    t = training_rows(d)
    wp = pd.Series(np.nan, index=d.index)
    models: dict[tuple[int, int], WPModel] = {}
    for yr in sorted(d["year"].unique()):
        for inn in (1, 2):
            m = WPModel(inn, kind).fit(t[(t["innings"] == inn) & (t["year"] != yr)])
            models[(yr, inn)] = m
            mask = (d["year"] == yr) & (d["innings"] == inn)
            wp.loc[mask] = m.predict(d.loc[mask])
    return wp, models


def _state_wp(states: pd.DataFrame, models: dict) -> np.ndarray:
    """WP (batting side of `states.innings`) for hypothetical post-delivery states, with terminal logic."""
    out = np.full(len(states), np.nan)
    s = states.reset_index(drop=True)
    inn2 = s["innings"] == 2
    won2 = inn2 & (s["runs_needed"] <= 0)
    over2 = inn2 & ~won2 & ((s["balls_left"] <= 0) | (s["wkts_left"] <= 0))
    out[won2] = 1.0
    out[over2 & (s["runs_needed"] == 1)] = 0.5  # tie
    out[over2 & (s["runs_needed"] > 1)] = 0.0
    # innings-1 terminal states are scored by the innings-1 model itself (balls_left/wkts_left = 0),
    # so the innings-1 -> innings-2 model seam is never credited to a player.
    s["balls_left"] = s["balls_left"].clip(lower=0)
    s["wkts_left"] = s["wkts_left"].clip(lower=0)
    live = s.index[np.isnan(out)]
    for (yr, inn), m in models.items():
        mk = live[(s.loc[live, "year"] == yr) & (s.loc[live, "innings"] == inn)]
        if len(mk):
            out[mk] = m.predict(s.loc[mk])
    return out


OUTCOMES = {"dot": (0, 0, 1), "one": (1, 0, 1), "two": (2, 0, 1), "three": (3, 0, 1),
            "four": (4, 0, 1), "six": (6, 0, 1), "wicket": (0, 1, 1), "wide": (1, 0, 0)}


def outcome_probs(d: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """Empirical next-ball outcome probabilities by tier x over, smoothed with a centred
    `window`-over moving average (count-weighted) so leverage has no step at phase boundaries."""
    o = np.select(
        [d["is_wicket"], d["is_wide"] | d["is_noball"], d["total_runs"] >= 6, d["total_runs"].between(4, 5),
         d["total_runs"] == 3, d["total_runs"] == 2, d["total_runs"] == 1],
        ["wicket", "wide", "six", "four", "three", "two", "one"], default="dot")
    counts = (pd.crosstab([d["tier"], d["overid"]], o)
                .reindex(columns=list(OUTCOMES), fill_value=0).astype(float))
    smooth = counts.groupby(level="tier", group_keys=False).apply(
        lambda c: c.rolling(window, center=True, min_periods=1).sum())
    return smooth.div(smooth.sum(axis=1), axis=0)


def leverage_index(d: pd.DataFrame, wp_before: pd.Series, models: dict) -> pd.Series:
    """Expected |delta WP| of the next delivery given the state, normalised to mean 1."""
    probs = outcome_probs(d)
    base = d[["innings", "year", "tier", "score_before", "wkts_left", "balls_left", "max_balls",
              "target", "runs_needed", "par"]].copy()
    exp_swing = np.zeros(len(d))
    key = pd.MultiIndex.from_arrays([d["tier"], d["overid"]])
    for name, (r, w, legal) in OUTCOMES.items():
        st = base.copy()
        st["score_before"] = st["score_before"] + r
        st["wkts_left"] = st["wkts_left"] - w
        st["balls_left"] = st["balls_left"] - legal
        st["runs_needed"] = st["runs_needed"] - r
        wp_next = _state_wp(st, models)
        p = probs.reindex(key)[name].to_numpy()
        exp_swing += p * np.abs(wp_next - wp_before.to_numpy())
    exp_swing = pd.Series(exp_swing, index=d.index)
    return exp_swing / exp_swing.mean()


def wp_after(d: pd.DataFrame, wp: pd.Series, models: dict) -> pd.Series:
    """WP of the batting side after each delivery.

    Last ball of innings 1: innings-1 model at the terminal state (NOT the chase model), so the
    model-switch seam at the innings break is attributed to no player."""
    d = d.assign(wp=wp)
    nxt = d.groupby(["match_id", "innings"])["wp"].shift(-1)
    last = nxt.isna()
    after = nxt.copy()
    m1 = last & (d["innings"] == 1)
    st = d.loc[m1, ["innings", "year", "tier", "max_balls", "par", "target", "runs_needed"]].copy()
    st["score_before"] = d.loc[m1, "score_before"] + d.loc[m1, "total_runs"]
    st["wkts_left"] = d.loc[m1, "wkts_left"] - d.loc[m1, "is_wicket"].astype(int)
    st["balls_left"] = d.loc[m1, "balls_left"] - d.loc[m1, "is_legal"].astype(int)
    after[m1] = _state_wp(st, models)
    # last ball of innings 2 -> terminal result (tie = 0.5); undecided matches stay NaN
    m2 = last & (d["innings"] == 2)
    res = np.where(d.loc[m2, "decided"], d.loc[m2, "batting_team_won"].astype(float), np.nan)
    sup = d.loc[m2, "match_id"].isin(pd.read_parquet(PROCESSED_DIR / "super_overs.parquet")["match_id"])
    res[sup.to_numpy()] = 0.5
    after[m2] = res
    return after


def run() -> pd.DataFrame:
    d = pd.read_parquet(PROCESSED_DIR / "deliveries.parquet")
    ev = evaluate(d)
    log.info("\n%s", ev.round(4).to_string(index=False))
    # model choice is made on the VALIDATION year only (mean Brier over both innings)
    cand = ev[(ev["split"] == "valid") & ev["model"].isin(["logit", "lgbm"])]
    kind = cand.groupby("model")["brier"].mean().idxmin()
    log.info("selected WP model (by validation Brier): %s", kind)
    wp, models = crossfit_wp(d, kind)
    d["wp_before"] = wp
    d["wp_after"] = wp_after(d, wp, models)
    d["wpa_bat"] = d["wp_after"] - d["wp_before"]
    d["leverage"] = leverage_index(d, wp, models)
    out = d[["match_id", "innings", "innings_ball_num", "wp_before", "wp_after", "wpa_bat", "leverage"]]
    from src.config import FEATURES_DIR
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(FEATURES_DIR / "wp_leverage.parquet", index=False)
    MODELS_DIR.mkdir(exist_ok=True)
    test = ev[ev["split"] == "test"].set_index(["innings", "model"])[["brier", "log_loss", "auc", "ece"]]
    (MODELS_DIR / "wp_model_card.json").write_text(json.dumps({
        "selected_model": kind, "selection_rule": "lowest mean validation Brier across innings",
        "candidates": ["constant(base rate)", "logit", "lgbm (monotone)"],
        "production_values": "leave-one-year-out cross-fitting",
        "train_years": TRAIN_YEARS, "valid_years": VALID_YEARS, "test_years": TEST_YEARS, "seed": SEED,
        "features_inn1": models[(int(d['year'].min()), 1)].cols,
        "features_inn2": models[(int(d['year'].min()), 2)].cols,
        "test_metrics": {f"inn{i}_{m}": v for (i, m), v in test.round(4).to_dict("index").items()},
    }, indent=2))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    o = run()
    print(o.describe().round(3).to_string())
