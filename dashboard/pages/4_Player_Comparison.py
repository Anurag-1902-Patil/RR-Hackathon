import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import common as C

C.setup("Player Comparison", "Compare any eligible players, or a selected player against their strongest alternatives")

side = st.radio("Discipline", ["batting", "bowling"], horizontal=True)
s = C.reliability(side)
tab1, tab2 = st.tabs(["Free comparison", "Selected vs alternatives"])

with tab1:
    default = s.player.head(3).tolist()
    names = st.multiselect("Players (2–5)", s.player.tolist(), default=default, max_selections=5)
    if len(names) >= 2:
        c1, c2 = st.columns(2)
        c1.plotly_chart(C.radar(s, names), use_container_width=True)
        hc = C.high_col(side)
        sub = s[s.player.isin(names)].set_index("player")
        fig = px.scatter(s, x=hc, y="pressure_perf_per100", hover_name="player", color_discrete_sequence=[C.LILAC],
                         labels={hc: "HIGH-pressure balls (sample size)", "pressure_perf_per100": "Pressure performance (per 100, opponent-adjusted)"})
        fig.add_scatter(x=sub[hc], y=sub.pressure_perf_per100, mode="markers+text", text=sub.index, textposition="top center",
                        marker=dict(color=C.PINK, size=12), name="Selected")
        fig.update_layout(title="Pressure performance vs sample size (all eligible)")
        c2.plotly_chart(C.style(fig, 430), use_container_width=True)
        cols = ["rank", "score", "p_top10", hc, "pressure_innings", "value_per100_high", "consistency_raw", "wpa_high_total",
                "pressure_perf_per100", "usual_per100", "delta_eb"]
        st.dataframe(sub[cols].T.round(2), use_container_width=True)
        C.note("delta_eb = pressure vs own baseline after empirical-Bayes shrinkage (batting retains ~21% of raw signal, bowling ~4%).")

with tab2:
    alt = C.csv("reports/player_comparisons.csv")
    a = alt[alt.side == side]
    pick = st.selectbox("Selected player", a.selected.unique().tolist())
    rows = a[a.selected == pick]
    st.dataframe(rows[["alternative", "alternative_rank", "role_alternative", "score_sel", "score_alt", "high_balls_sel", "high_balls_alt",
                       "p_selected_ranks_higher_bootstrap"]].round(2), hide_index=True, use_container_width=True)
    st.plotly_chart(C.radar(s, [pick] + rows.alternative.tolist()), use_container_width=True)
    p = rows.p_selected_ranks_higher_bootstrap
    verdict = np.select([p >= .8, p >= .65, p >= .55], ["clear", "moderate", "slight"], "statistically indistinguishable")
    for (_, r), v in zip(rows.iterrows(), verdict):
        st.markdown(f"- vs **{r.alternative}** (rank {r.alternative_rank}): {pick} ranks higher in **{r.p_selected_ranks_higher_bootstrap:.0%}** "
                    f"of match-level bootstrap resamples, so the advantage is *{v}*.")
