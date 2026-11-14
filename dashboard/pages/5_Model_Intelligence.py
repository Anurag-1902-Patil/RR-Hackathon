import json

import plotly.express as px
import streamlit as st

import common as C

C.setup("Model Intelligence", "Methodology, validation, uncertainty and limitations")

st.markdown("""
**Pipeline:** clean ball-by-ball → pre-ball match state → win probability → leverage & pressure → context expectations →
per-ball value → opponent-adjusted ridge ratings (Gaussian prior) → player tables → reliability score → bootstrap & sensitivity.
""")

st.markdown("#### Win-probability model (chronological: train 2022–24, validate 2025, test 2026)")
ev = C.csv("reports/model_outputs/wp_evaluation.csv")
fig = px.bar(ev, x="model", y="brier", color="split", barmode="group", facet_col="innings", color_discrete_sequence=[C.LILAC, C.PURPLE],
             text=ev.brier.round(3))
fig.update_layout(yaxis_title="Brier score (lower is better)")
st.plotly_chart(C.style(fig, 360), use_container_width=True)
card = json.loads((C.ROOT / "models" / "wp_model_card.json").read_text())
C.note(f"Selected: {card['selected_model']} ({card['selection_rule']}). LightGBM was rejected: trees could not extrapolate to 2026 scoring levels.")
cal = C.csv("reports/model_outputs/wp_calibration_test.csv")
fig = px.line(cal, x="pred", y="obs", color="model", facet_col="innings", markers=True, color_discrete_sequence=[C.PURPLE, C.PINK])
fig.add_shape(type="line", x0=0, y0=0, x1=1, y1=1, line=dict(dash="dot", color=C.MUTED), row="all", col="all")
fig.update_layout(title="Calibration on held-out 2026", xaxis_title="Predicted WP", yaxis_title="Observed win rate")
st.plotly_chart(C.style(fig, 360), use_container_width=True)

st.markdown("#### Expected-runs / wicket models")
st.dataframe(C.csv("reports/model_outputs/expected_models_evaluation.csv").round(4), hide_index=True, use_container_width=True)

st.markdown("#### Is pressure performance a repeatable trait?")
cv = C.csv("reports/model_outputs/clutch_variance.csv")
st.dataframe(cv.round(3), hide_index=True, use_container_width=True)
C.note("tau = true between-player SD of the pressure delta (runs/ball) after removing sampling noise. "
       "Batting: ~21% of a raw delta is signal; bowling: ~4%. Pressure-delta terms never improved out-of-time prediction.")

st.markdown("#### Score robustness")
c1, c2 = st.columns(2)
c1.dataframe(C.csv("reports/model_outputs/reliability_weight_sensitivity.csv").round(3), hide_index=True, use_container_width=True)
side = c2.radio("Component correlations", ["batting", "bowling"], horizontal=True)
corr = C.csv(f"reports/model_outputs/reliability_component_corr_{side}.csv", index_col=0)
c2.plotly_chart(C.style(px.imshow(corr, text_auto=".2f", color_continuous_scale=["white", C.PURPLE], zmin=-0.2, zmax=1), 360),
                use_container_width=True)
st.image(str(C.FIG / "rank_uncertainty_top20.png"), caption="Rank uncertainty: bootstrap 90% intervals and range across pressure definitions")

st.markdown("#### Limitations")
st.markdown("""
- Pressure is unobserved; the definition is a modelling choice (stress-tested above).
- Data covers IPL + bilateral T20I + A-team T20 from 2022. It has no domestic leagues or World Cups by name, and no fielder attribution (so no fielding metrics).
- Openers face few HIGH-pressure balls, so some elite openers fall below eligibility.
- Bootstrap intervals describe measurement uncertainty in 2022–26 performance, not probabilities of future performance.
- The submitted lists rank only players RR can sign today (not on an IPL 2026 squad, not Pakistani or Bangladeshi, not retired or banned). Releases on 17 Nov 2026 will add players; the pipeline re-runs to include them.
""")
