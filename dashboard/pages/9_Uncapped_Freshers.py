import plotly.express as px
import streamlit as st

import common as C

C.setup("Uncapped Indian Freshers", "Domestic T20 (Syed Mushtaq Ali Trophy) pressure reliability · uncapped, not on an IPL 2026 squad, aged 30 or under")

tv = C.csv("reports/model_outputs/uncapped_transfer_validation.csv").set_index("side")
C.kpis([("SMAT matches", "272"), ("SMAT balls", "62,850"), ("Players linked to data pack", "152"),
        ("Batting: domestic→IPL (Spearman)", f"{tv.loc['batting', 'spearman_smat_vs_pack_usual']:.2f}"),
        ("Bowling: domestic→IPL (Spearman)", f"{tv.loc['bowling', 'spearman_smat_vs_pack_usual']:.2f}")])
C.note("Public data: Cricsheet SMAT ball-by-ball (Open Data Commons Attribution), 2020/21–2024/25. Same pressure definition, components and weights as the main lists; "
       "one opponent-adjusted model spans the data pack and SMAT. Domestic batting form predicts IPL batting; domestic bowling form did not, so the bowlers are a watchlist.")

side = st.radio("Discipline", ["batting", "bowling"], horizontal=True)
picks = C.csv(f"reports/top_5_uncapped_{'batters' if side == 'batting' else 'bowlers'}.csv")
st.markdown("### Top 5 uncapped fresher " + ("batters" if side == "batting" else "bowlers (watchlist, low confidence)"))
fig = px.bar(picks.iloc[::-1], x="reliability_score", y="player", orientation="h", text=picks.iloc[::-1]["reliability_score"].round(0),
             color_discrete_sequence=[C.PURPLE if side == "batting" else C.PINK],
             hover_data={"domestic_team": True, "age_at_auction": True, "p_top5_bootstrap": ":.0%"})
fig.update_traces(textposition="outside", marker_line_width=0)
fig.update_layout(xaxis_title="Reliability score (percentile among all eligible SMAT players)", yaxis_title="", xaxis_range=[0, 105])
st.plotly_chart(C.style(fig, 340), use_container_width=True)
st.dataframe(picks.drop(columns=["status"]), hide_index=True, use_container_width=True,
             column_config={"p_top5_bootstrap": st.column_config.NumberColumn("P(top 5)", format="%.2f")})

st.markdown("### Everyone rated in SMAT")
allp = C.csv(f"reports/model_outputs/uncapped_scores_{side}.csv")
allp = allp[allp.eligible].assign(status=lambda x: x.exclusion_reason.fillna("").where(~x.in_pool, "In fresher pool"))
allp.loc[allp.status.eq("") & ~allp.data_pool, "status"] = "Capped, on an IPL 2026 squad, or not recent"
cols = ["full_name", "cricsheet_name", "smat_team", "age_at_auction", "score", "pool_rank", "status", "pressure_innings", "value_per100_high"]
st.dataframe(allp.sort_values("score", ascending=False)[cols].round(2), hide_index=True, use_container_width=True)
C.note("Scores are percentiles within SMAT and are not directly comparable with the main lists. Every pool player was checked on Wikipedia and the IPL 2026 personnel page "
       "(14 Nov 2026). Cricsheet's 2024/25 season has only 8 matches, so most evidence is 2020/21–2023/24.")
