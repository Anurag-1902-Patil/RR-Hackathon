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
| Batting & bowling reliability engines | 🔜 |
| Rankings, uncertainty, sensitivity | 🔜 |
| RR squad intelligence, dashboard, report, video | 🔜 |

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
.venv/Scripts/python -m pytest -q tests
```

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
