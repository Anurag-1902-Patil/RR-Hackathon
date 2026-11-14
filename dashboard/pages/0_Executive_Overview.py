"""SupeRR Intelligence: Executive Overview (landing page). Run: streamlit run dashboard/app.py"""
from __future__ import annotations

import plotly.express as px
import streamlit as st

import common as C

C.setup("SupeRR Intelligence", "Pressure-Based Player Reliability & Scouting Engine · independent analysis for SupeRR Selector Season 2")

s = C.summary()
C.kpis([("Deliveries analysed", f"{int(s['deliveries']):,}"), ("Matches", f"{int(s['matches_with_ball_data']):,}"),
        ("HIGH-pressure balls", f"{int(s['high_pressure_deliveries']):,}"), ("Eligible batters", s["eligible_batters"]),
        ("Eligible bowlers", s["eligible_bowlers"])])
C.note(f"RR data pack: IPL 2022–2026 ({s['ipl_matches']} matches) + T20I/A-team ({s['t20i_matches']} T20I) · {s['date_from']} to {s['date_to']}. "
       "HIGH pressure = top 20% of a composite of match leverage and situational difficulty.")

st.markdown("### Final top 10s: players RR can sign at the IPL 2027 auction")
c1, c2 = st.columns(2)
for col, side, title in ((c1, "batting", "Most reliable batters RR can sign"), (c2, "bowling", "Most reliable bowlers RR can sign")):
    r = C.reliability(side).query("rank <= 10")
    fig = px.bar(r.iloc[::-1], x="score", y="player", orientation="h", text=r.iloc[::-1]["score"].round(0),
                 color_discrete_sequence=[C.PURPLE], hover_data={"p_top10": ":.0%", "role": True, "score": ":.1f"})
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(title=title, xaxis_title="Reliability score (0–100, percentile composite)", yaxis_title="", xaxis_range=[0, 105])
    col.plotly_chart(C.style(fig, 430), use_container_width=True)

st.markdown("### What Rajasthan Royals need (evidence-led)")
pm = C.csv("research/rr_recruitment_priority_matrix.csv")
fig = px.bar(pm.sort_values("priority_score"), x="priority_score", y="requirement", orientation="h", color="priority",
             color_discrete_map={"High": C.PINK, "Medium": C.GOLD, "Low": C.LILAC}, text="priority_score")
fig.update_layout(xaxis_title="Recruitment priority (0–100)", yaxis_title="", xaxis_range=[0, 100])
st.plotly_chart(C.style(fig, 320), use_container_width=True)

st.markdown("### Key findings")
st.markdown("""
- **Pressure changes outcomes.** Under HIGH pressure, batters are dismissed on more balls than in ordinary situations (see *Pressure Analytics*).
- **"Clutch" is mostly not repeatable.** Ordinary-situation performance persists across 2022–24 → 2025–26. Pressure-only performance and pressure deltas do not. Scores therefore borrow strength from all-situation ability.
- **Only players RR can sign are ranked.** The whole unrestricted performance top 10 is under contract at IPL teams. Also excluded: Pakistani and Bangladeshi players, and retired or banned players (Russell, Ashwin, Mohit Sharma, Brook). Switch the leaderboards to *All eligible* for context.
- **Sikandar Raza is the standout target:** #1 acquirable bowler, #5 batter, and 97th percentile in death-overs batting. Death bowling: Theekshana, then Zampa.
- **Uncapped Indian freshers (public SMAT data):** batters Rahul Buddhi, Narayan Jagadeesan, Rajat Dey, Atharva Taide, Harsh Tyagi; bowling watchlist led by Atit Sheth. See *Uncapped Indian Freshers*.
- **Honest limits:** every acquirable player is overseas, several have little or no IPL record, and bowlers #9–#10 are statistically level with Sodhi and Farooqi.
- **RR's clearest gaps:** death-overs / finishing batting and death bowling. Opening batting is RR's strength (#1 in the IPL in 2025 and 2026).
""")
C.note("Independent analytical submission, not affiliated with or endorsed by Rajasthan Royals. Players released on 17 Nov 2026 join the pool; the pipeline re-runs in one command.")
