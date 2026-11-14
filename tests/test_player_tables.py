"""Consistency tests for per-player tables against the delivery table."""
from __future__ import annotations

import pandas as pd
import pytest

from src.config import FEATURES_DIR, PROCESSED_DIR

T = FEATURES_DIR / "player_tables"
pytestmark = pytest.mark.skipif(not (T / "batting.parquet").exists(), reason="run src.scouting.player_tables first")


@pytest.fixture(scope="module")
def tabs():
    return {k: pd.read_parquet(T / f"{k}.parquet") for k in ("batting", "bowling")}


@pytest.fixture(scope="module")
def d():
    return pd.read_parquet(PROCESSED_DIR / "deliveries.parquet")


def test_batting_runs_reconcile(tabs, d):
    assert tabs["batting"]["runs"].sum() == d.loc[d.is_batter_ball, "runs"].sum()


def test_bowling_wickets_reconcile(tabs, d):
    assert tabs["bowling"]["wickets"].sum() == d["bowler_wicket"].sum()


def test_high_balls_subset(tabs):
    b = tabs["batting"].dropna(subset=["balls_high"])
    assert (b["balls_high"] <= b["balls"]).all()


def test_eligibility_floor(tabs):
    b, w = tabs["batting"], tabs["bowling"]
    assert (b.loc[b.eligible, "balls_high"] >= 120).all()
    assert (w.loc[w.eligible, "legal_balls_high"] >= 150).all()
    assert 50 <= b.eligible.sum() <= 150 and 50 <= w.eligible.sum() <= 150


def test_consistency_bounded(tabs):
    for t in tabs.values():
        c = t["consistency_post"].dropna()
        assert c.between(0, 1).all()


def test_unique_player_ids(tabs):
    for t in tabs.values():
        assert t.index.is_unique
