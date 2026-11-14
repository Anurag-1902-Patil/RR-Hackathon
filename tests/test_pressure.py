"""Tests for the pressure engine outputs (requires the local data pack)."""
from __future__ import annotations

import pandas as pd
import pytest

from src.config import FEATURES_DIR, PROCESSED_DIR

pytestmark = pytest.mark.skipif(not (FEATURES_DIR / "pressure.parquet").exists(), reason="run src.features.pressure first")


@pytest.fixture(scope="module")
def dp() -> pd.DataFrame:
    d = pd.read_parquet(PROCESSED_DIR / "deliveries.parquet")
    p = pd.read_parquet(FEATURES_DIR / "pressure.parquet").drop(columns=["leverage"])
    w = pd.read_parquet(FEATURES_DIR / "wp_leverage.parquet")[["match_id", "innings", "innings_ball_num", "wp_before"]]
    k = ["match_id", "innings", "innings_ball_num"]
    return d.merge(p, on=k, validate="1:1").merge(w, on=k, validate="1:1")


def test_band_shares(dp):
    share = dp.pressure_band.value_counts(normalize=True)
    assert abs(share["high"] - 0.20) < 0.01 and abs(share["low"] - 0.50) < 0.01


def test_both_innings_represented_in_high_pressure(dp):
    hi = dp[dp.pressure_band == "high"]
    assert 0.3 < hi.innings.eq(2).mean() < 0.7


def test_no_future_information_in_components(dp):
    """Rolling components at the first ball of an innings must be zero (only prior balls used)."""
    first = dp.groupby(["match_id", "innings"]).head(1)
    assert (first.recent_wkts == 0).all() and (first.recent_dots == 0).all()


def _high_share_by_over(dp, col="pressure_band"):
    return dp.groupby(["innings", "overid"])[col].apply(lambda s: (s == "high").mean() * 100).unstack()


def test_v2_no_phase_cliffs(dp):
    """v2 acceptance: no adjacent-over change in HIGH share above 15 percentage points."""
    assert _high_share_by_over(dp).diff(axis=1).abs().max().max() <= 15


def test_v2_batting_first_middle_order_pressure_recognised(dp):
    """v2 acceptance: innings-1 overs 7-15 with 4+ wickets down are at least 15% HIGH."""
    m = dp[(dp.innings == 1) & dp.overid.between(7, 15) & (dp.wkts_left <= 6)]
    assert (m.pressure_band == "high").mean() >= 0.15


def test_dead_games_rarely_high(dp):
    hi = dp.pressure_band == "high"
    dead = (dp.wp_before < 0.05) | (dp.wp_before > 0.95)
    assert (hi & dead).sum() / hi.sum() < 0.02


def test_blend_variants_present(dp):
    for col in ("pressure_band_l30", "pressure_band_l70", "pressure_band_lev", "pressure_band_rpi"):
        assert abs((dp[col] == "high").mean() - 0.20) < 0.01


def test_inn1_shortfall_uses_no_own_year(dp):
    """Shortfall is finite for every innings-1 ball (leave-one-year-out table always has data)."""
    assert dp.loc[dp.innings == 1, "shortfall_inn1"].notna().all()


def test_dismissal_rate_higher_under_pressure(dp):
    b = dp[dp.is_batter_ball]
    rate = b.groupby("pressure_band").striker_out.mean()
    assert rate["high"] > rate["low"]
