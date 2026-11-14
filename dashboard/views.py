"""Reusable page bodies."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import common as C


def leaderboard(side: str) -> None:
    s = C.reliability(side)
    hc = C.high_col(side)
    pool = st.radio("Players shown", ["RR can sign (submitted lists)", "All eligible (context: includes contracted players)"], horizontal=True)
    if pool.startswith("RR"):
        s = s[s.rr_acquirable].sort_values("rank")
    else:
        s = s.drop(columns=["rank", "p_top10", "boot_rank_p05", "boot_rank_p95", "rank_min_across_defs", "rank_max_across_defs"]).rename(columns={
            "overall_rank": "rank", "overall_p_top10": "p_top10", "overall_boot_rank_p05": "boot_rank_p05", "overall_boot_rank_p95": "boot_rank_p95",
            "overall_rank_min_across_defs": "rank_min_across_defs", "overall_rank_max_across_defs": "rank_max_across_defs"}).sort_values("rank")
    s["status"] = s.not_acquirable_reason.fillna("RR can sign")
    roles = sorted(s.role.dropna().unique())
    c1, c2, c3 = st.columns([2, 2, 1])
    pick_roles = c1.multiselect("Role (from data)", roles, default=roles)
    top_n = c2.slider("Show top N", min(10, len(s)), len(s), min(25, len(s)))
    only_top10 = c3.toggle("Top 10 only", value=False)
    v = s[s.role.isin(pick_roles)].head(10 if only_top10 else top_n)

    st.markdown("#### Ranking with uncertainty")
    t = v.iloc[::-1]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t.boot_rank_p95, y=t.player, mode="markers", marker=dict(opacity=0), showlegend=False, hoverinfo="skip"))
    for _, r in t.iterrows():
        fig.add_shape(type="line", x0=r.boot_rank_p05, x1=r.boot_rank_p95, y0=r.player, y1=r.player, line=dict(color=C.LILAC, width=7))
        fig.add_shape(type="line", x0=r.rank_min_across_defs, x1=r.rank_max_across_defs, y0=r.player, y1=r.player, line=dict(color=C.PURPLE, width=2))
    fig.add_trace(go.Scatter(x=t["rank"], y=t.player, mode="markers", marker=dict(color=C.PINK, size=10), name="Final rank",
                             customdata=t[["score", "p_top10"]], hovertemplate="%{y}: rank %{x}<br>score %{customdata[0]:.1f} · P(top10) %{customdata[1]:.0%}<extra></extra>"))
    fig.add_vline(x=10.5, line_dash="dash", line_color=C.MUTED)
    fig.update_layout(xaxis_title="Rank (1 = best) · thick bar: bootstrap 90% interval · thin bar: range across pressure definitions", yaxis_title="")
    st.plotly_chart(C.style(fig, max(380, 24 * len(t))), use_container_width=True)

    st.markdown("#### Table")
    cols = ["rank", "player", "status", "latest_team", "role", "score", "p_top10", hc, "pressure_innings", "value_per100_high"]
    cols += (["sr_high", "sr_low"] if side == "batting" else ["economy_high", "economy_low", "wickets_high"])
    cols += [f"pct_{k}" for k in C.COMP]
    st.dataframe(v[cols].round(2), hide_index=True, use_container_width=True,
                 column_config={"score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f"),
                                "p_top10": st.column_config.NumberColumn("P(top 10)", format="%.2f")})
    C.note("Score = weighted percentile composite (pressure performance 35%, consistency 20%, impact 20%, vs-own-baseline 15%, usual ability 10%) "
           "among all eligible players. Rank, P(top 10) and intervals are computed within the pool shown. The RR-can-sign pool excludes IPL 2026 squad members, Pakistani and Bangladeshi players, and retired or banned players. Value per 100 = runs above context expectation (wicket-cost adjusted). Raw SR/economy are descriptive only.")

    st.markdown("#### Player detail")
    name = st.selectbox("Player", v.player.tolist())
    r = s[s.player == name].iloc[0]
    a, b = st.columns([1, 1])
    a.plotly_chart(C.radar(s, [name]), use_container_width=True)
    trends = C.csv(f"reports/dashboard_data/season_trends_{side}.csv")
    tr = trends[trends.player_id == r.player_id]
    fig = px.bar(tr, x="year", y="value_per100", color_discrete_sequence=[C.PURPLE], text=tr.value_per100.round(1),
                 hover_data=["balls" if side == "batting" else "legal_balls", "high_balls"])
    fig.update_layout(title=f"{name}: context value per 100 balls by season", yaxis_title="Value per 100 (runs above expected)", xaxis_title="")
    b.plotly_chart(C.style(fig, 430), use_container_width=True)
