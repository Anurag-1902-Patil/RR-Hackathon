import streamlit as st

import common as C

C.setup("Research & Sources", "Data provenance, external sources and verification")

st.markdown("#### Data provenance")
st.markdown("""
- **Primary:** official RR SupeRR Selector data pack (ball-by-ball, matches, competitions, teams, playing XIs, mappings), audited in `research/DATA_AUDIT.md`.
- **Calculated:** every metric is reproducibly derived by the pipeline in `src/` (see README).
- **External:** only for identity, availability and squad status, with each fact tied to a source below.
""")
st.markdown("#### Verified player register (top 20)")
st.dataframe(C.register(), hide_index=True, use_container_width=True)
st.markdown("#### Source register")
st.markdown((C.RES / "RESEARCH_SOURCE_REGISTER.md").read_text(encoding="utf-8"))
