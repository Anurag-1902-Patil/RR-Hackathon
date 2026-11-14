# SupeRR Intelligence
**Pressure-Based Player Reliability & Scouting Engine.** An independent analytical submission for Rajasthan Royals' *SupeRR Selector Season 2* (IPL 2027 auction analytics challenge). It is not affiliated with or endorsed by Rajasthan Royals.

> The private RR data pack is **not** in this repository. Place `data_set.zip`'s `Data Pack/*.csv` files in `data/raw/rr_data_pack/` to reproduce the results.

## Status
| Phase | State |
|---|---|
| 1. Data audit | ✅ `research/DATA_AUDIT.md` |
| 3. Data pipeline (delivery table, pre-ball match state, era par) | ✅ |
| 5a. Win probability, WPA, Leverage Index | ✅ (logistic selected; 2026 chase Brier 0.116) |
| 2/6. Pressure definition (composite stakes + difficulty) | ✅ `research/METHODOLOGY.md` |
| Expectation models, opponent-adjusted ratings, reliability score | ✅ |
| Rankings, bootstrap uncertainty, weight & definition sensitivity | ✅ `research/RANKINGS_FINAL.md` (RR-acquirable players only) |
| Player verification (identity, availability) | ✅ `research/PLAYER_VERIFICATION.md` |
| RR squad intelligence, needs, squad fit, comparisons | ✅ `research/RR_SQUAD_ANALYSIS.md`, `research/PLAYER_COMPARISONS.md` |
| Streamlit dashboard (9 pages) | ✅ `dashboard/` |
| Final report (47-page PDF) and 25-slide PPTX deck | ✅ `reports/final_report.pdf`, `reports/presentation.pptx` |
| Uncapped Indian freshers (public SMAT data) | ✅ `reports/top_5_uncapped_*.csv`, `reports/FINAL_SUBMISSION.md` |
| Documentary video, trailer, social reel and posts | ✅ `reports/video/`, `reports/social_content/` |

## Setup (Windows, Python 3.11)
```bash
py -3.11 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```
Versions are pinned. Newer pandas, pyarrow and scikit-learn wheels were blocked by Windows Application Control on the development machine.

## Run the pipeline
```bash
.venv/Scripts/python -m src.data.build_deliveries     # data/processed/*.parquet
.venv/Scripts/python -m src.models.win_probability    # data/features/wp_leverage.parquet + evaluation
.venv/Scripts/python -m src.features.pressure         # data/features/pressure.parquet + comparison tables
.venv/Scripts/python -m src.models.expected          # context expectations
.venv/Scripts/python -m src.scouting.player_tables    # per-player tables
.venv/Scripts/python -m src.scouting.reliability      # score, sensitivity, bootstrap (~9 min)
.venv/Scripts/python -m src.scouting.final_selection  # RR-acquirable pool: within-pool ranks and uncertainty
.venv/Scripts/python -m src.reporting.rankings        # final top-10 CSVs + figure
.venv/Scripts/python -m src.research.verified_players # verification register (needs facts for every selected player)
.venv/Scripts/python -m src.reporting.rankings_doc    # research/RANKINGS_FINAL.md
.venv/Scripts/python -m src.scouting.rr_squad         # RR squad intelligence (run_extended for depth/priority)
.venv/Scripts/python -m src.scouting.squad_fit        # squad fit, alternatives, uplift
.venv/Scripts/python -m src.reporting.comparisons_doc # PLAYER_COMPARISONS.md + recommendations
.venv/Scripts/python -m src.reporting.dashboard_data  # dashboard aggregates
# uncapped Indian freshers (public Cricsheet SMAT data; unzip sma_male_json.zip into data/external/cricsheet_sma/)
.venv/Scripts/python -m src.domestic.smat             # SMAT delivery table: state, WP, pressure, expectations
.venv/Scripts/python -m src.domestic.uncapped         # combined ridge, score, fresher pool, bootstrap (~10 min)
.venv/Scripts/python -m src.domestic.report           # top-5 uncapped CSVs, figure, FINAL_SUBMISSION list
.venv/Scripts/python -m pytest -q tests
```

## Report and deck
```bash
.venv/Scripts/python -m src.reporting.report_figures   # report figures
.venv/Scripts/python -m src.reporting.build_report     # reports/final_report.pdf (headless Edge/Chrome)
.venv/Scripts/python -m src.reporting.deck_data        # reports/deck_data.json (same numbers as the PDF)
cd src/reporting/deck && npm install && cd ../../..
node src/reporting/deck/build_deck.js                  # reports/presentation.pptx (set APPLY_THEME_JS to apply theme colours)
```

## Video and social content
```bash
.venv/Scripts/python -m src.reporting.video.build_video   # documentary, trailer, reel (PowerPoint slide export + Windows speech + ffmpeg)
.venv/Scripts/python -m src.reporting.video.social        # reel script, LinkedIn/Instagram drafts (not posted)
```

## Dashboard
```bash
.venv/Scripts/streamlit run dashboard/app.py
```
Ten pages (including Uncapped Indian Freshers): Executive Overview, Batting and Bowling Leaderboards, Pressure Analytics, Player Comparison, Model Intelligence, Scouting Reports, RR Squad Intelligence, and Research & Sources. The dashboard reads only aggregate outputs in `reports/` and `research/`, never the raw data pack.

## Layout
```
src/config.py                 paths, constants, chronological split
src/data/                     audit scripts + delivery-table build
src/models/win_probability.py WP models, WPA, Leverage Index
src/features/pressure.py      pressure engine (composite + sensitivity variants)
research/                     DATA_AUDIT.md, METHODOLOGY.md
reports/model_outputs/        evaluation and pressure-comparison tables (aggregates only)
models/                       model cards
tests/                        pytest suite
```
