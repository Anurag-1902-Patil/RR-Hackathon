"""Central configuration: paths, constants and seeds for the SupeRR Intelligence pipeline."""
from __future__ import annotations

from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[1]
RAW_DIR: Path = ROOT / "data" / "raw" / "rr_data_pack"
PROCESSED_DIR: Path = ROOT / "data" / "processed"
FEATURES_DIR: Path = ROOT / "data" / "features"
MODELS_DIR: Path = ROOT / "models"
REPORTS_DIR: Path = ROOT / "reports"
FIGURES_DIR: Path = REPORTS_DIR / "figures"
RESEARCH_DIR: Path = ROOT / "research"

SEED: int = 2027

RR_TEAM_ID: int = 3

# ICC full members (used to tag T20I matches as full-member vs associate).
FULL_MEMBERS: frozenset[str] = frozenset({
    "Afghanistan", "Australia", "Bangladesh", "England", "India", "Ireland",
    "New Zealand", "Pakistan", "South Africa", "Sri Lanka", "West Indies", "Zimbabwe",
})

# Delivery semantics (verified in research/DATA_AUDIT.md §2.1)
WIDE = "wide"
NO_BALL_TYPES: frozenset[str] = frozenset({"Overstep", "other"})
BOWLER_WICKET_TYPES: frozenset[str] = frozenset({"Bowled", "Caught", "LBW", "Stump", "Hit Wicket"})
NON_DISMISSAL_TYPES: frozenset[str] = frozenset({"Retire Out"})  # tactical retirement

PHASES: tuple[tuple[str, int, int], ...] = (("powerplay", 1, 6), ("middle", 7, 15), ("death", 16, 20))

# Chronological split for model validation (season = calendar year of match)
TRAIN_YEARS: tuple[int, ...] = (2022, 2023, 2024)
VALID_YEARS: tuple[int, ...] = (2025,)
TEST_YEARS: tuple[int, ...] = (2026,)
