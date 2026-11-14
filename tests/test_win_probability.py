"""Behavioural tests for WP / WPA / leverage outputs (requires the local data pack)."""
from __future__ import annotations

import pandas as pd
import pytest

from src.config import FEATURES_DIR, PROCESSED_DIR, REPORTS_DIR

pytestmark = pytest.mark.skipif(not (FEATURES_DIR / "wp_leverage.parquet").exists(), reason="run src.models.win_probability first")


@pytest.fixture(scope="module")
def d() -> pd.DataFrame:
    base = pd.read_parquet(PROCESSED_DIR / "deliveries.parquet")
    w = pd.read_parquet(FEATURES_DIR / "wp_leverage.parquet")
    return base.merge(w, on=["match_id", "innings", "innings_ball_num"], validate="1:1")


def test_wp_bounded(d):
    assert d.wp_before.between(0, 1).all()
    assert d.wp_after.dropna().between(0, 1).all()


def test_leverage_normalised(d):
    assert abs(d.leverage.mean() - 1) < 1e-6
    assert (d.leverage >= 0).all()


def test_wp_monotone_in_runs_needed(d):
    """Chasing WP should fall as runs needed rises, holding balls/wickets bands fixed."""
    c = d[(d.innings == 2) & d.balls_left.between(30, 36) & d.wkts_left.between(6, 8)]
    by = c.groupby(pd.cut(c.runs_needed, [0, 30, 50, 70, 200]), observed=True).wp_before.mean()
    assert by.is_monotonic_decreasing


def test_close_death_chases_have_highest_leverage(d):
    c = d[(d.innings == 2) & (d.phase == "death")]
    close = c[(c.runs_needed - c.balls_left).abs() <= 5].leverage.mean()
    lopsided = c[(c.runs_needed - c.balls_left) < -20].leverage.mean()
    assert close > 2 and lopsided < 0.5


def test_innings_break_seam_small(d):
    last1 = d[d.innings == 1].groupby("match_id").tail(1)
    assert last1.wpa_bat.abs().mean() < 2 * d.drop(last1.index).wpa_bat.abs().mean()


def test_selected_model_beats_baseline_on_test():
    ev = pd.read_csv(REPORTS_DIR / "model_outputs" / "wp_evaluation.csv")
    t = ev[ev.split == "test"].set_index(["innings", "model"]).brier
    for inn in (1, 2):
        assert t[(inn, "logit")] < t[(inn, "constant(base rate)")]
