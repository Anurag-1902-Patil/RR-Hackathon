"""SupeRR Intelligence dashboard entry point. Run: streamlit run dashboard/app.py"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

P = Path(__file__).parent / "pages"
st.set_page_config(page_title="SupeRR Intelligence", layout="wide", page_icon="🏏")
nav = st.navigation({
    "Overview": [st.Page(P / "0_Executive_Overview.py", title="Executive Overview", default=True)],
    "Rankings": [st.Page(P / "1_Batting_Leaderboard.py", title="Batting Leaderboard"),
                 st.Page(P / "2_Bowling_Leaderboard.py", title="Bowling Leaderboard")],
    "Analysis": [st.Page(P / "3_Pressure_Analytics.py", title="Pressure Analytics"),
                 st.Page(P / "4_Player_Comparison.py", title="Player Comparison"),
                 st.Page(P / "5_Model_Intelligence.py", title="Model Intelligence")],
    "Scouting": [st.Page(P / "6_Scouting_Reports.py", title="Scouting Reports"),
                 st.Page(P / "7_RR_Squad_Intelligence.py", title="RR Squad Intelligence")],
    "Evidence": [st.Page(P / "8_Research_and_Sources.py", title="Research & Sources")],
})
nav.run()
