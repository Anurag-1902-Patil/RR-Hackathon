"""Headless smoke tests: every dashboard page must render without exceptions."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard"
PAGES = sorted((DASH / "pages").glob("*.py"))

pytestmark = pytest.mark.skipif(not (ROOT / "reports" / "dashboard_data" / "dataset_summary.csv").exists(),
                                reason="run pipeline + src.reporting.dashboard_data first")


@pytest.mark.parametrize("page", PAGES, ids=[p.stem for p in PAGES])
def test_page_renders(page):
    from streamlit.testing.v1 import AppTest
    sys.path.insert(0, str(DASH))
    at = AppTest.from_file(str(page), default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]


def test_scouting_report_every_player():
    """Scouting page renders for all 20 selected players (both disciplines)."""
    from streamlit.testing.v1 import AppTest
    sys.path.insert(0, str(DASH))
    at = AppTest.from_file(str(DASH / "pages" / "6_Scouting_Reports.py"), default_timeout=120).run()
    for side_idx in (0, 1):
        at.radio[0].set_value(["batting", "bowling"][side_idx]).run()
        for name in at.selectbox[0].options:
            at.selectbox[0].set_value(name).run()
            assert not at.exception, (name, [e.value for e in at.exception])


def test_navigation_entrypoint():
    from streamlit.testing.v1 import AppTest
    sys.path.insert(0, str(DASH))
    at = AppTest.from_file(str(DASH / "app.py"), default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
