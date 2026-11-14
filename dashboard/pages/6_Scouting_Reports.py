import plotly.express as px
import streamlit as st

import common as C

C.setup("Scouting Reports", "Individual profiles for the 20 selected players RR can sign: evidence, alternatives, RR fit and risks")

side = st.radio("Discipline", ["batting", "bowling"], horizontal=True)
s = C.reliability(side).query("rank <= 10")
reg = C.register().drop_duplicates("player_id").set_index("player_id")
fit = C.csv("research/player_to_rr_squad_fit.csv").set_index(["side", "rank"])
up = C.csv("research/rr_phase_uplift_scenarios.csv").set_index(["side", "rank"])
alt = C.csv("reports/player_comparisons.csv")
name = st.selectbox("Player", s.player.tolist())
r = s[s.player == name].iloc[0]
g = reg.loc[r.player_id]
f = fit.loc[(side, r["rank"])]
u = up.loc[(side, r["rank"])]

st.markdown(f"## #{int(r['rank'])} {g.full_name}")
st.caption(f"{g.country} · {g.bat} / {g.bowl} · age at auction {g.age_at_auction_calc} (calculated from verified DOB) · IPL 2026: {g.ipl_2026_team}")
if g.availability_class != "DEPENDS ON RETENTIONS" or "INJURY" in str(g.notes):
    st.markdown(f'<div class="srr-flag"><b>{g.ipl_2027_status}</b> · {g.notes}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="srr-flag">IPL 2027: {g.ipl_2027_status} · {g.notes}</div>', unsafe_allow_html=True)
st.write("")
hc = C.high_col(side)
C.kpis([("Reliability score", f"{r.score:.0f}"), ("P(top 10)", f"{r.p_top10:.0%}"), ("HIGH balls", int(r[hc])),
        ("Pressure innings/spells", int(r.pressure_innings)), ("Value/100 on HIGH", f"{r.value_per100_high:+.1f}"),
        ("RR squad-fit", f"{f.squad_fit_score:.0f}")])
st.write("")
c1, c2 = st.columns(2)
a = alt[(alt.side == side) & (alt.selected == r.player)]
c1.plotly_chart(C.radar(C.reliability(side), [r.player] + a.alternative.tolist()), use_container_width=True)
tr = C.csv(f"reports/dashboard_data/season_trends_{side}.csv").query("player_id == @r.player_id")
fig = px.line(tr, x="year", y="value_per100", markers=True, color_discrete_sequence=[C.PINK])
fig.update_layout(title="Context value per 100 balls by season", xaxis_title="", yaxis_title="Runs above expected per 100")
c2.plotly_chart(C.style(fig, 430), use_container_width=True)

st.markdown("### Why this player?")
for _, x in a.iterrows():
    p = x.p_selected_ranks_higher_bootstrap
    v = "clear" if p >= .8 else "moderate" if p >= .65 else "slight" if p >= .55 else "statistically indistinguishable"
    st.markdown(f"- vs **{x.alternative}** (rank {x.alternative_rank}, score {x.score_alt:.0f}): ranks higher in **{p:.0%}** of resamples, so the advantage is *{v}*.")
st.markdown(f"- Rank range across pressure definitions: **{int(r.rank_min_across_defs)}–{int(r.rank_max_across_defs)}**; "
            f"bootstrap 90% rank interval **{int(r.boot_rank_p05)}–{int(r.boot_rank_p95)}**.")

st.markdown("### How this player could strengthen RR (layer 2, separate from the ranking)")
st.markdown(f"""
- **RR need addressed:** {f.best_fit_requirement} (RR priority {f.requirement_priority:.0f}/100)
- **Phase evidence:** {f.best_fit_phase} context value {f.phase_value_eb_per100:+.1f} per 100 over {int(f.phase_balls)} balls (percentile {f.phase_value_pctile:.0f})
- **Roster:** {f.indian_or_overseas}; squad-fit {f.squad_fit_score:.0f} ({f.squad_fit_no_slot:.0f} without slot cost)
- **Hypothetical uplift (model estimate, not a forecast):** {u.est_runs_gained_per_season_MODEL_ESTIMATE:+.1f} runs per season if given the 2026 {u.phase} balls of {u.replaces_weakest_rr_regular} ({int(u.rr_regular_2026_phase_balls)} balls)
""")
C.note(f"Sources: {g.sources}. Full write-up: research/PLAYER_COMPARISONS.md. No player photographs are used, because licensed images were not obtained.")
