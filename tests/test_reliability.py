"""Unit tests for the reliability scoring logic (synthetic data; no data pack required)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.scouting import reliability as RL


def _table(n: int = 30, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = pd.DataFrame({c: rng.normal(size=n) for c in RL.COMP_COLS.values()}, index=pd.Index(range(n), name="player_id"))
    t["consistency_post"] = rng.uniform(0.3, 0.8, n)
    t["eligible"] = True
    return t


def test_score_bounded_and_ranked():
    s = RL.score(_table(), RL.WEIGHTS)
    assert s["score"].between(0, 100).all()
    assert s["rank"].min() == 1 and s["rank"].is_monotonic_increasing


def test_dominant_player_ranks_first():
    t = _table()
    for c in RL.COMP_COLS.values():
        t.loc[7, c] = t[c].max() + 1
    assert RL.score(t, RL.WEIGHTS).index[0] == 7


def test_ineligible_excluded():
    t = _table()
    t.loc[[0, 1, 2], "eligible"] = False
    assert not set(RL.score(t, RL.WEIGHTS).index) & {0, 1, 2}


def test_weights_sum_to_one():
    for w in RL.ALT_WEIGHTS.values():
        assert abs(sum(w.values()) - 1) < 1e-9


def test_eb_rate_shrinks_small_samples_more():
    rng = np.random.default_rng(1)
    rows = []
    for pid in range(40):
        n = 20 if pid < 20 else 400
        rows.append(pd.DataFrame({"pid": pid, "v": rng.normal(0.1 * (pid % 5), 1.0, n)}))
    r = pd.concat(rows)
    raw = r.groupby("pid")["v"].mean()
    eb = RL.eb_rate(r, "pid", "v")
    mu = r["v"].mean()
    shrink_small = ((eb - mu).abs() / (raw - mu).abs())[:20].median()
    shrink_big = ((eb - mu).abs() / (raw - mu).abs())[20:].median()
    assert shrink_small < shrink_big
