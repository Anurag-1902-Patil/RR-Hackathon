import plotly.express as px
import streamlit as st

import common as C

C.setup("Rajasthan Royals Squad Intelligence", "Verified 2026 squad · same pressure framework · team phase performance vs IPL · recruitment needs")

st.markdown('<div class="srr-flag"><b>IPL 2027 squad: pending.</b> The official retention list is due by 17 Nov 2026. '
            'The 2026 squad below is the verified baseline (data pack + official RR announcements).</div>', unsafe_allow_html=True)
sq = C.csv("research/rr_squad_database.csv")
aud = C.csv("research/rr_player_performance_database.csv")

t1, t2, t3, t4, t5 = st.tabs(["Squad", "Players under pressure", "Team vs league", "Depth chart", "Needs & recommendations"])
with t1:
    st.dataframe(sq[["player_name", "indian_or_overseas", "acquisition_2026", "rr_apps_2025", "rr_apps_2026", "kept_wicket_2026", "status_2027"]],
                 hide_index=True, use_container_width=True)
with t2:
    c1, c2 = st.columns(2)
    b = aud.dropna(subset=["bat_pressure_pctile_vs_eligible"]).query("bat_balls >= 300")
    fig = px.scatter(b, x="bat_usual_pctile_vs_eligible", y="bat_pressure_pctile_vs_eligible", text="player", size="bat_balls",
                     color_discrete_sequence=[C.PURPLE], labels={"bat_usual_pctile_vs_eligible": "Usual ability percentile",
                                                                  "bat_pressure_pctile_vs_eligible": "Pressure performance percentile"})
    fig.add_hline(y=50, line_dash="dot", line_color=C.MUTED); fig.add_vline(x=50, line_dash="dot", line_color=C.MUTED)
    fig.update_traces(textposition="top center"); fig.update_layout(title="RR batters vs the candidate pool (≥300 balls)")
    c1.plotly_chart(C.style(fig, 430), use_container_width=True)
    w = aud.dropna(subset=["bowl_pressure_pctile_vs_eligible"]).query("bowl_balls >= 300")
    fig = px.scatter(w, x="bowl_usual_pctile_vs_eligible", y="bowl_pressure_pctile_vs_eligible", text="player", size="bowl_balls",
                     color_discrete_sequence=[C.PINK], labels={"bowl_usual_pctile_vs_eligible": "Usual ability percentile",
                                                                "bowl_pressure_pctile_vs_eligible": "Pressure performance percentile"})
    fig.add_hline(y=50, line_dash="dot", line_color=C.MUTED); fig.add_vline(x=50, line_dash="dot", line_color=C.MUTED)
    fig.update_traces(textposition="top center"); fig.update_layout(title="RR bowlers vs the candidate pool (≥300 balls)")
    c2.plotly_chart(C.style(fig, 430), use_container_width=True)
    st.dataframe(aud, hide_index=True, use_container_width=True)
    C.note("Same eligibility, metrics and percentiles as every external candidate; no preferential treatment.")
with t3:
    ph = C.csv("research/rr_phase_performance.csv")
    side = st.radio("Side", ["batting", "bowling"], horizontal=True)
    met = st.selectbox("Metric", sorted(ph.metric.unique()), index=sorted(ph.metric.unique()).index("run_rate"))
    v = ph[(ph.side == side) & (ph.metric == met)]
    fig = px.line(v, x="year", y="rr_rank_of_10", color="phase", markers=True, color_discrete_sequence=[C.PURPLE, C.PINK, C.GOLD])
    fig.update_yaxes(autorange="reversed", dtick=1, range=[10.5, 0.5]); fig.update_layout(title=f"RR {side} {met}: rank of 10 IPL teams (1 = best)")
    st.plotly_chart(C.style(fig, 380), use_container_width=True)
    st.dataframe(v.pivot_table(index="phase", columns="year", values=["rr", "league_mean"]).round(2), use_container_width=True)
    cm = C.csv("reports/rr_team_performance_dashboard_data.csv").query("table == 'close_matches'").dropna(axis=1, how="all")
    st.markdown("**Close matches** (≤10 runs / ≤3 wickets)"); st.dataframe(cm, hide_index=True)
with t4:
    dep = C.csv("research/rr_role_depth_chart.csv")
    side = st.radio("Depth chart side", ["batting", "bowling"], horizontal=True, key="dc")
    v = dep[dep.side == side]
    fig = px.bar(v, x="balls", y="player", color="context_value_per100", facet_col="phase", orientation="h",
                 color_continuous_scale=[[0, C.PINK], [0.5, "#EEEEEE"], [1, C.PURPLE]], color_continuous_midpoint=0,
                 category_orders={"phase": ["powerplay", "middle", "death"]})
    fig.update_layout(title=f"Who RR used in 2026 ({side}); colour = context value per 100 (purple good, pink poor)")
    fig.update_yaxes(matches=None, showticklabels=True)
    st.plotly_chart(C.style(fig, 520), use_container_width=True)
with t5:
    pm = C.csv("research/rr_recruitment_priority_matrix.csv")
    st.dataframe(pm[["requirement", "priority_score", "priority", "mean_rr_rank_of_10", "best_eligible_rr_cover", "best_cover_pressure_pctile",
                     "rr_players_used_in_phase_2026"]], hide_index=True, use_container_width=True)
    C.note("priority = 100 × (0.6 × severity from 2025–26 phase ranks + 0.4 × coverage gap from the best eligible RR player's pressure percentile).")
    rec = C.csv("reports/rr_recruitment_recommendations.csv")
    fig = px.scatter(rec, x="squad_fit_score", y="reliability_rank", color="side", text="player", symbol="indian_or_overseas",
                     color_discrete_sequence=[C.PURPLE, C.PINK], hover_data=["rr_need_addressed", "availability"])
    fig.update_yaxes(autorange="reversed"); fig.update_traces(textposition="middle right")
    fig.update_layout(title="Reliability (layer 1) vs RR squad fit (layer 2)", xaxis_title="Squad-fit score", yaxis_title="Reliability rank")
    st.plotly_chart(C.style(fig, 520), use_container_width=True)
    st.dataframe(rec, hide_index=True, use_container_width=True)
    up = C.csv("research/rr_phase_uplift_scenarios.csv")
    st.markdown("**Hypothetical phase uplift** (model estimate, not a forecast)")
    st.dataframe(up, hide_index=True, use_container_width=True)
