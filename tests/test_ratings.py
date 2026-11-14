"""Tests for ball values and opponent-adjusted ratings (requires local data pack + features)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.config import FEATURES_DIR, REPORTS_DIR
from src.models import ratings as R

pytestmark = pytest.mark.skipif(not (FEATURES_DIR / "expected.parquet").exists(), reason="run src.models.expected first")


@pytest.fixture(scope="module")
def d() -> pd.DataFrame:
    return R.ball_values(R.load())


def test_wicket_cost_positive_and_larger_early(d):
    assert (d.wkt_cost >= 0).all()
    early = d[(d.overid <= 4) & (d.wkts_left >= 8)].wkt_cost.mean()
    late = d[(d.overid >= 19)].wkt_cost.mean()
    assert early > late


def test_values_centred_per_season(d):
    """Season recentring makes mean per-ball value ~0 within each season-environment."""
    env = d.year.astype(str) + np.where(d.is_ipl, "I", "N")
    assert d.groupby(env).v_bowl.mean().abs().max() < 0.2


def test_choose_rule_prefers_largest_tolerated_scale():
    t = pd.DataFrame({"model": ["null (0)"] + ["ridge"] * 3, "alpha": [None, 10, 10, 10], "delta_scale": [None, 0.0, 0.25, 1.0],
                      "skill_all_pct": [0, 0.05, 0.05, 0.04], "skill_high_pct": [0, 0.10, 0.098, 0.05]})
    assert R.choose(t) == (10.0, 0.25)


def test_tuning_outputs_exist():
    for s in ("batting", "bowling"):
        assert (REPORTS_DIR / "model_outputs" / f"ratings_tuning_{s}.csv").exists()
    cv = pd.read_csv(REPORTS_DIR / "model_outputs" / "clutch_variance.csv")
    assert set(cv.side) == {"batting", "bowling"} and (cv.reliability_of_raw_delta.between(0, 1)).all()
