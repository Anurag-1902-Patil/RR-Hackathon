"""Pressure-definition review figures (static PNGs for report and review)."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import FEATURES_DIR, FIGURES_DIR, PROCESSED_DIR
from src.features.pressure import rule_based_components

INK, MUTED, GRID, SURFACE = "#1B1F3B", "#6B6F8A", "#E6E6EF", "#FFFFFF"
SEQ = ["#D9CCF2", "#9B7FD6", "#4B2A99"]  # low -> high (one purple hue, light -> dark)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlecolor": INK})


def load() -> pd.DataFrame:
    d = pd.read_parquet(PROCESSED_DIR / "deliveries.parquet")
    w = pd.read_parquet(FEATURES_DIR / "wp_leverage.parquet")
    p = pd.read_parquet(FEATURES_DIR / "pressure.parquet").drop(columns=["leverage"])
    k = ["match_id", "innings", "innings_ball_num"]
    return d.merge(w, on=k, validate="1:1").merge(p, on=k, validate="1:1")


def _note(fig, text: str) -> None:
    fig.text(0.01, 0.01, text, fontsize=7.5, color=MUTED, ha="left", va="bottom")


def fig_over_heatmap(x: pd.DataFrame, col: str = "pressure_band", name: str = "pressure_by_over_heatmap") -> None:
    h = (x.groupby(["innings", "overid"])[col].apply(lambda s: (s == "high").mean() * 100).unstack())
    fig, ax = plt.subplots(figsize=(11, 2.9))
    im = ax.imshow(h.values, aspect="auto", cmap=matplotlib.colors.LinearSegmentedColormap.from_list("p", ["#F4F0FB", "#4B2A99"]), vmin=0, vmax=50)
    for (i, j), v in np.ndenumerate(h.values):
        ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8, color=SURFACE if v > 28 else INK)
    ax.set_xticks(range(20), range(1, 21)); ax.set_yticks([0, 1], ["Innings 1\n(setting)", "Innings 2\n(chasing)"])
    ax.set_xlabel("Over")
    ax.set_title("Share of deliveries classed HIGH pressure, by over (%)", loc="left")
    for xv in (5.5, 14.5):
        ax.axvline(xv, color=SURFACE, lw=2)
    cb = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=7)
    _note(fig, "Source: RR data pack (IPL + T20I, 2022–2026), 200,961 deliveries. HIGH = top 20% of composite pressure score.")
    fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(FIGURES_DIR / f"{name}.png", dpi=200); plt.close(fig)


def fig_outcomes(x: pd.DataFrame) -> None:
    b = x[x["is_batter_ball"]]
    defs = [("pressure_band", "Composite (final)"), ("pressure_band_lev", "Leverage only"), ("pressure_band_rpi", "Rule-based only")]
    metrics = [("striker_out", "Dismissal rate (% of balls faced)", 100), ("runs", "Strike rate (runs per 100 balls)", 100)]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    width = 0.26
    for ax, (m, label, mult) in zip(axes, metrics):
        for bi, band in enumerate(["low", "medium", "high"]):
            vals = [b.loc[b[c] == band, m].mean() * mult for c, _ in defs]
            pos = np.arange(3) + (bi - 1) * width
            ax.bar(pos, vals, width - 0.03, color=SEQ[bi], label=band.capitalize(), zorder=2)
            for p_, v in zip(pos, vals):
                ax.text(p_, v, f"{v:.1f}" if m == "striker_out" else f"{v:.0f}", ha="center", va="bottom", fontsize=7.5, color=INK)
        ax.set_xticks(range(3), [n for _, n in defs]); ax.set_title(label, loc="left", fontsize=10.5)
        ax.grid(axis="y", color=GRID, zorder=0); ax.spines[["top", "right"]].set_visible(False)
        lo = min(p.get_height() for p in ax.patches); ax.set_ylim(lo * 0.85, None)
    axes[0].legend(title="Pressure band", frameon=False, fontsize=8, title_fontsize=8, loc="upper left")
    fig.suptitle("How batting outcomes change across pressure bands, under three definitions", x=0.01, ha="left", fontweight="bold", color=INK)
    _note(fig, "Balls faced (wides excluded). Low = bottom 50%, Medium = 50–80th pct, High = top 20%. Y-axes truncated to show differences.")
    fig.tight_layout(rect=(0, 0.05, 1, 0.95)); fig.savefig(FIGURES_DIR / "pressure_outcomes_by_definition.png", dpi=200); plt.close(fig)


def sensitivity_table(x: pd.DataFrame) -> pd.DataFrame:
    comp = rule_based_components(x)
    z = (comp - comp.mean()) / comp.std(ddof=0)
    base_w = {"rrr_gap": .25, "wkt_pressure": .20, "recent_wkts": .15, "recent_dots": .10, "death": .10, "closeness": .20}

    def high(wts: dict, lev_w: float = 0.5) -> pd.Series:
        r = sum(v * z[k] for k, v in wts.items())
        return (lev_w * x["lev_pct_inn"] + (1 - lev_w) * r.rank(pct=True)).rank(pct=True) >= 0.8

    base = x["pressure_band"].eq("high")
    alts = {
        "RPI: equal weights": (dict.fromkeys(comp.columns, 1 / 6), 0.5),
        "RPI: drop dot-squeeze": ({"rrr_gap": .3, "wkt_pressure": .22, "recent_wkts": .17, "death": .11, "closeness": .2}, 0.5),
        "RPI: drop closeness": ({"rrr_gap": .3, "wkt_pressure": .25, "recent_wkts": .2, "recent_dots": .1, "death": .15}, 0.5),
        "Blend 30% leverage / 70% RPI": (base_w, 0.3),
        "Blend 70% leverage / 30% RPI": (base_w, 0.7),
        "Leverage only (within-innings pct)": (base_w, 1.0),
        "RPI only": (base_w, 0.0),
    }
    rows = []
    for k, (wts, lw) in alts.items():
        h = high(wts, lw)
        rows.append({"variant": k, "jaccard_vs_final": (h & base).sum() / (h | base).sum()})
    return pd.DataFrame(rows)


def fig_sensitivity(t: pd.DataFrame) -> None:
    t = t.sort_values("jaccard_vs_final")
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.barh(t["variant"], t["jaccard_vs_final"], color="#4B2A99", height=0.55, zorder=2)
    for i, v in enumerate(t["jaccard_vs_final"]):
        ax.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=8, color=INK)
    ax.set_xlim(0, 1); ax.grid(axis="x", color=GRID, zorder=0); ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlabel("Overlap of HIGH-pressure ball sets with final definition (Jaccard, 1 = identical)")
    ax.set_title("Which choices move the pressure definition?", loc="left")
    _note(fig, "Rule-based weights barely matter (0.78–0.86); the leverage/rule-based blend is the decisive choice.")
    fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(FIGURES_DIR / "pressure_sensitivity.png", dpi=200); plt.close(fig)


def run() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    x = load()
    fig_over_heatmap(x)
    fig_outcomes(x)
    t = sensitivity_table(x)
    t.round(3).to_csv(FIGURES_DIR.parent / "model_outputs" / "pressure_sensitivity.csv", index=False)
    fig_sensitivity(t)
    print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    run()
