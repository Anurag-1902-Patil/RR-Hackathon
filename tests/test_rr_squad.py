"""Tests for RR squad intelligence outputs."""
from __future__ import annotations

import pandas as pd
import pytest

from src.config import RESEARCH_DIR

pytestmark = pytest.mark.skipif(not (RESEARCH_DIR / "rr_squad_database.csv").exists(), reason="run rr_squad first")


def test_squad_matches_data_and_official_counts():
    sq = pd.read_csv(RESEARCH_DIR / "rr_squad_database.csv")
    assert len(sq) == 27 and sq.player_id.is_unique
    retained = sq.acquisition_2026.str.startswith("Retained")
    assert retained.sum() == 13  # official retention list (S1)
    assert (sq.indian_or_overseas == "Overseas").sum() <= 9  # 8 + one injury replacement
    assert sq.status_2027.str.startswith("Pending").all()  # never present 2027 as confirmed


def test_priority_matrix_bounded_and_documented():
    pm = pd.read_csv(RESEARCH_DIR / "rr_recruitment_priority_matrix.csv")
    assert pm.priority_score.between(0, 100).all()
    assert set(pm.priority) <= {"High", "Medium", "Low"}
    assert pm.phase_ranks_2025_26.str.contains("#").all()


def test_depth_chart_shares_valid():
    dc = pd.read_csv(RESEARCH_DIR / "rr_role_depth_chart.csv")
    assert dc.share_of_rr_phase_balls_pct.between(0, 100).all()
    assert dc.groupby(["side", "phase"]).share_of_rr_phase_balls_pct.sum().le(100.01).all()
