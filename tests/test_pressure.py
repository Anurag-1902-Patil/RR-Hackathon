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
    return d.merge(p, on=["match_id", "innings", "innings_ball_num"], validate="1:1")


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


def test_dismissal_rate_higher_under_pressure(dp):
    b = dp[dp.is_batter_ball]
    rate = b.groupby("pressure_band").striker_out.mean()
    assert rate["high"] > rate["low"]
