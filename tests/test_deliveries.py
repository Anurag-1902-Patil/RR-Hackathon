"""Integrity tests for the cleaned delivery table (requires the private data pack locally)."""
from __future__ import annotations

import re

import pandas as pd
import pytest

from src.config import RAW_DIR
from src.data.build_deliveries import build

pytestmark = pytest.mark.skipif(not (RAW_DIR / "ball_by_ball.csv").exists(), reason="data pack not present")


@pytest.fixture(scope="session")
def built() -> dict[str, pd.DataFrame]:
    return build(write=False)


def test_no_rows_lost(built):
    raw = pd.read_csv(RAW_DIR / "ball_by_ball.csv", usecols=["match_id"])
    assert len(built["deliveries"]) + len(built["super_overs"]) == len(raw)


def test_first_ball_state_is_zero(built):
    d = built["deliveries"]
    first = d.groupby(["match_id", "innings"]).head(1)
    assert (first[["score_before", "wkts_before", "legal_before"]] == 0).all().all()


def test_state_monotonic(built):
    d = built["deliveries"]
    g = d.groupby(["match_id", "innings"])
    assert (g["score_before"].diff().fillna(0) >= 0).all()
    assert (g["legal_before"].diff().fillna(0) >= 0).all()


def test_legal_balls_never_exceed_innings_limit(built):
    d = built["deliveries"]
    legal = d[d.is_legal].groupby(["match_id", "innings"]).size()
    assert legal.max() <= 120


def test_wide_and_noball_are_not_legal(built):
    d = built["deliveries"]
    assert not d.loc[d.extras_type.isin(["wide", "Overstep", "other"]), "is_legal"].any()


def test_bowler_runs_exclude_byes(built):
    d = built["deliveries"]
    byes = d[d.extras_type.isin(["byes", "legbyes"])]
    assert (byes.bowler_runs == byes.runs).all()
    assert (d.bowler_runs <= d.total_runs).all()


def test_run_outs_not_credited_to_bowler(built):
    d = built["deliveries"]
    assert not d.loc[d.dismissal_type.eq("RunOut"), "bowler_wicket"].any()
    assert not d.loc[d.dismissal_type.eq("Retire Out"), "striker_out"].any()


def test_chase_target_at_first_ball(built):
    d = built["deliveries"]
    first2 = d[d.innings == 2].groupby("match_id").head(1)
    assert (first2.runs_needed == first2.target).all()


def test_results_reconcile_for_non_dls(built):
    """Margins computed from ball data must match the official result for non-D/L matches."""
    d, m = built["deliveries"], built["matches"].set_index("match_id")
    inn = d.groupby(["match_id", "innings"]).agg(team=("batting_team_id", "first"),
                                                 score=("total_runs", "sum"), w=("is_wicket", "sum"))
    ok = bad = 0
    for mid in d.match_id.unique():
        if m.at[mid, "dls"] or (mid, 2) not in inn.index:
            continue
        mt = re.search(r"Won by (\d+) (run|wicket)", m.at[mid, "result"], re.I)
        if not mt:
            continue
        n, kind = int(mt.group(1)), mt.group(2).lower()
        i1, i2 = inn.loc[(mid, 1)], inn.loc[(mid, 2)]
        good = (i1.score - i2.score == n) if kind == "run" else (10 - i2.w == n)
        ok, bad = ok + good, bad + (not good)
    assert bad <= 1, f"{bad} non-DLS mismatches (1 known: match 20190)"
    assert ok > 790


def test_playing_xi_unique(built):
    assert not built["playing_xi"].duplicated(["match_id", "team_id", "player_id"]).any()


def test_tiers_complete(built):
    assert built["deliveries"].tier.isna().sum() == 0
    assert set(built["deliveries"].tier.unique()) == {"IPL", "T20I_full", "T20I_assoc", "A_team"}
