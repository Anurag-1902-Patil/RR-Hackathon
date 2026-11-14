"""Shared loaders, palette and UI helpers for the SupeRR Intelligence dashboard.

Every number shown in the dashboard is read from pipeline outputs (reports/, research/); nothing is
hard-coded. Run the pipeline first (see README) to regenerate them.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
REP, RES, MO, DD, FIG = ROOT / "reports", ROOT / "research", ROOT / "reports" / "model_outputs", ROOT / "reports" / "dashboard_data", ROOT / "reports" / "figures"

NAVY, PURPLE, LILAC, PINK, GOLD, INK, MUTED, GRID = "#1B1F3B", "#4B2A99", "#C9B8EE", "#C2185B", "#C9A227", "#1B1F3B", "#6B6F8A", "#E6E6EF"
SERIES = [PURPLE, PINK, GOLD, "#2E86AB", "#6B6F8A"]  # fixed categorical order

COMP = {"pressure_perf": "Pressure performance", "consistency": "Consistency", "impact": "Match impact (WPA)",
        "delta": "Vs own baseline", "usual": "Usual ability"}


def setup(title: str, subtitle: str = "") -> None:
    try:  # pages run standalone (tests) or under st.navigation (app.py already set the config)
        st.set_page_config(page_title=f"{title} · SupeRR Intelligence", layout="wide", page_icon="🏏")
    except Exception:
        pass
    st.markdown(f"""
    <style>
      .block-container {{padding-top: 1.6rem;}}
      .srr-hero {{background: linear-gradient(120deg, {NAVY} 0%, {PURPLE} 70%, {PINK} 130%); color: white; padding: 18px 24px;
                 border-radius: 14px; margin-bottom: 14px;}}
      .srr-hero h1 {{color: white; margin: 0; font-size: 1.7rem;}}
      .srr-hero p {{color: #E9E3FF; margin: 4px 0 0 0;}}
      .srr-kpi {{background: white; border: 1px solid {GRID}; border-radius: 12px; padding: 12px 14px;}}
      .srr-kpi .v {{font-size: clamp(1.05rem, 1.7vw, 1.6rem); font-weight: 700; color: {NAVY}; white-space: nowrap;}}
      .srr-kpi .l {{font-size: .8rem; color: {MUTED}; text-transform: uppercase; letter-spacing: .04em;}}
      .srr-note {{font-size: .8rem; color: {MUTED};}}
      .srr-flag {{background: #FFF4E5; border-left: 4px solid {GOLD}; padding: 6px 10px; border-radius: 6px; font-size: .88rem;}}
    </style>
    <div class="srr-hero"><h1>{title}</h1><p>{subtitle or 'SupeRR Intelligence · Pressure-Based Player Reliability & Scouting Engine'}</p></div>
    """, unsafe_allow_html=True)


def kpis(items: list[tuple[str, str]]) -> None:
    cols = st.columns(len(items))
    for c, (label, value) in zip(cols, items):
        c.markdown(f'<div class="srr-kpi"><div class="v">{value}</div><div class="l">{label}</div></div>', unsafe_allow_html=True)


def note(text: str) -> None:
    st.markdown(f'<div class="srr-note">{text}</div>', unsafe_allow_html=True)


def style(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(height=height, template="plotly_white", font=dict(color=INK, size=13), margin=dict(l=10, r=10, t=50, b=10),
                      legend=dict(orientation="h", y=-0.15), hoverlabel=dict(bgcolor="white"))
    fig.update_xaxes(gridcolor=GRID); fig.update_yaxes(gridcolor=GRID)
    return fig


@st.cache_data
def csv(path: str, **kw) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, **kw)


def reliability(side: str) -> pd.DataFrame:
    return csv(f"reports/model_outputs/reliability_{side}.csv")


def register() -> pd.DataFrame:
    return csv("research/player_verification_register.csv")


def summary() -> dict:
    return csv("reports/dashboard_data/dataset_summary.csv", index_col=0)["value"].to_dict()


def high_col(side: str) -> str:
    return "balls_high" if side == "batting" else "legal_balls_high"


def radar(df: pd.DataFrame, names: list[str]) -> go.Figure:
    fig = go.Figure()
    cats = list(COMP.values())
    for i, n in enumerate(names):
        r = df[df.player == n].iloc[0]
        vals = [r[f"pct_{k}"] * 100 for k in COMP]
        fig.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], name=n, line=dict(color=SERIES[i % len(SERIES)], width=2),
                                      fill="toself", opacity=0.55))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100], ticksuffix="", gridcolor=GRID)), showlegend=True)
    return style(fig, 430)
