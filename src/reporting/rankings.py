"""Export provisional top-10 CSVs and the rank-uncertainty figure from the reliability outputs."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import FIGURES_DIR, REPORTS_DIR

INK, MUTED, GRID, PURPLE, PINK = "#1B1F3B", "#6B6F8A", "#E6E6EF", "#4B2A99", "#C2185B"

COMMON = ["rank", "overall_rank", "player", "player_id", "latest_team", "national_side", "ipl_teams", "role", "score",
          "pct_pressure_perf", "pct_consistency", "pct_impact", "pct_delta", "pct_usual",
          "pressure_innings", "consistency_raw", "wpa_high_total", "pressure_perf_per100", "usual_per100",
          "delta_raw", "delta_eb", "rank_min_across_defs", "rank_max_across_defs",
          "boot_rank_p05", "boot_rank_p95", "p_top10", "pct_balls_IPL", "pct_balls_T20I_full",
          "pct_balls_T20I_assoc", "pct_balls_A_team", "last_match"]
BAT = ["batting_hand", "median_position", "balls", "balls_high", "runs_high", "sr_high", "sr_low", "avg_high",
       "value_per100_high", "value_per100_low", "runs_above_exp_high", "dot_pct_high", "boundary_pct_high"]
BOWL = ["bowling_type", "pace_or_spin", "legal_balls", "legal_balls_high", "wickets_high", "economy_high", "economy_low",
        "bowl_sr_high", "value_per100_high", "value_per100_low", "runs_saved_high", "wickets_above_exp_high",
        "dot_pct_high", "boundary_conc_pct_high"]


def export() -> dict[str, pd.DataFrame]:
    out = {}
    for side, extra, fname in (("batting", BAT, "top_10_batsmen.csv"), ("bowling", BOWL, "top_10_bowlers.csv")):
        s = pd.read_csv(REPORTS_DIR / "model_outputs" / f"reliability_{side}.csv")
        s["score"] = s["score"].round(0).astype(int)
        cols = [c for c in COMMON + extra if c in s]
        top = s[s["rank"] <= 10][cols].round(3)
        top.insert(1, "status", "FINAL - RR-acquirable (not under IPL contract; eligibility verified 2026-11-14)")
        top.to_csv(REPORTS_DIR / fname, index=False)
        s[s["rank"].notna()][cols].round(3).to_csv(REPORTS_DIR / "model_outputs" / f"shortlist_top25_{side}.csv", index=False)
        out[side] = s
    return out


def fig_rank_uncertainty(tabs: dict[str, pd.DataFrame], n: int = 20) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 7.2))
    for ax, (side, s) in zip(axes, tabs.items()):
        t = s[s["rank"].notna()].sort_values("rank").head(n).iloc[::-1]
        y = np.arange(len(t))
        ax.hlines(y, t["boot_rank_p05"], t["boot_rank_p95"], color="#C9B8EE", lw=5, zorder=1, label="Bootstrap 90% rank interval")
        ax.hlines(y, t["rank_min_across_defs"], t["rank_max_across_defs"], color=PURPLE, lw=1.6, zorder=2,
                  label="Range across pressure definitions")
        ax.scatter(t["rank"], y, color=PINK, s=36, zorder=3, label="Final rank")
        ax.axvline(10.5, color=MUTED, lw=1, ls="--")
        ax.set_yticks(y, [f"{p}  (P top10 {q:.0%})" for p, q in zip(t["player"], t["p_top10"])], fontsize=8.5)
        ax.set_xlim(0, max(16, t["boot_rank_p95"].max() + 1))
        ax.set_xlabel("Rank (1 = best)"); ax.grid(axis="x", color=GRID); ax.spines[["top", "right"]].set_visible(False)
        ax.set_title(f"{side.capitalize()}: RR-acquirable pool, rank within pool", loc="left", fontweight="bold", color=INK)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, 0.035))
    fig.text(0.01, 0.01, "RR-acquirable pool = eligible players not under IPL contract and with no verified eligibility bar. Bootstrap = 100 match-level resamples of the full pipeline, re-ranked within the pool. Intervals describe measurement uncertainty "
             "in 2022-26 performance, not future performance probabilities. Dashed line = top-10 cut-off.", fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(FIGURES_DIR / "rank_uncertainty_top20.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    t = export()
    fig_rank_uncertainty(t)
    for side, s in t.items():
        print(side, s[s["rank"] <= 10][["rank", "player", "score", "p_top10"]].to_string(index=False))
