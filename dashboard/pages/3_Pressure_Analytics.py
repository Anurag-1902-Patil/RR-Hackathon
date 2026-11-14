import plotly.express as px
import streamlit as st

import common as C

C.setup("Pressure Analytics", "How pressure is defined, where it occurs, and what it does to outcomes")

st.markdown("""**Definition (v2).** Pressure = 50% *stakes* + 50% *difficulty*:
- **Stakes:** Leverage Index, the expected win-probability swing of the next ball. It is ranked within each over in innings 1 and within the innings in chases.
- **Difficulty:** a rule-based index built from the scoreboard gap vs era par (chases: required rate; batting first: projected shortfall), wickets lost, recent collapse, dot-ball squeeze, innings progress and closeness of the contest.

HIGH = top 20% of balls; LOW = bottom 50%. Everything uses only information known *before* the ball.""")

h = C.csv("reports/dashboard_data/pressure_by_over.csv")
pv = h.pivot(index="innings", columns="overid", values="pct_high")
fig = px.imshow(pv, text_auto=".0f", color_continuous_scale=["#F4F0FB", C.PURPLE], aspect="auto",
                labels=dict(x="Over", y="Innings", color="% HIGH"), y=["Setting (1)", "Chasing (2)"])
fig.update_layout(title="Share of deliveries classed HIGH pressure, by over (%)")
st.plotly_chart(C.style(fig, 300), use_container_width=True)

o = C.csv("reports/dashboard_data/outcomes_by_phase_band.csv")
o["pressure_band"] = o.pressure_band.str.capitalize()
c1, c2 = st.columns(2)
for col, met, lab in ((c1, "dismissal_pct", "Dismissal rate (% of balls faced)"), (c2, "sr", "Strike rate")):
    fig = px.bar(o, x="phase", y=met, color="pressure_band", barmode="group", category_orders={"phase": ["powerplay", "middle", "death"],
                 "pressure_band": ["Low", "Medium", "High"]}, color_discrete_map={"Low": C.LILAC, "Medium": "#9B7FD6", "High": C.PURPLE})
    fig.update_layout(title=f"{lab} by phase and pressure band", yaxis_title=lab, xaxis_title="")
    col.plotly_chart(C.style(fig, 380), use_container_width=True)
C.note("Within each phase, compare bands. Raw strike rate is not the ranking metric: HIGH-pressure balls cluster late in the innings, "
       "so players are judged against context-expected outcomes.")

st.markdown("#### Robustness of the definition")
sens = C.csv("reports/model_outputs/pressure_sensitivity.csv").sort_values("jaccard_vs_final")
fig = px.bar(sens, x="jaccard_vs_final", y="variant", orientation="h", color_discrete_sequence=[C.PURPLE], text=sens.jaccard_vs_final.round(2))
fig.update_layout(xaxis_title="Overlap of HIGH set with final definition (Jaccard)", yaxis_title="", xaxis_range=[0, 1])
st.plotly_chart(C.style(fig, 340), use_container_width=True)
ds = C.csv("reports/model_outputs/reliability_definition_sensitivity.csv")
st.dataframe(ds.round(3), hide_index=True, use_container_width=True)
C.note("Top-10 overlap when the whole pipeline is re-run under alternative pressure definitions (same eligible pool).")
