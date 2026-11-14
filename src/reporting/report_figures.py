"""Report figures (static PNG, 200 dpi) generated only from pipeline outputs."""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

from src.config import FIGURES_DIR, MODELS_DIR, REPORTS_DIR, RESEARCH_DIR

NAVY, PURPLE, LILAC, PINK, GOLD, MUTED, GRID = "#1B1F3B", "#4B2A99", "#C9B8EE", "#C2185B", "#C9A227", "#6B6F8A", "#E6E6EF"
MO = REPORTS_DIR / "model_outputs"
P = FIGURES_DIR / "report"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": NAVY,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.titleweight": "bold", "axes.titlesize": 12,
                     "axes.titlecolor": NAVY, "axes.spines.top": False, "axes.spines.right": False})
COMP = [("pressure_perf", "Pressure\nperformance"), ("consistency", "Consistency"), ("impact", "Match\nimpact"),
        ("delta", "Vs own\nbaseline"), ("usual", "Usual\nability")]


def save(fig, name, note=None):
    if note:
        fig.text(0.01, -0.04, note, fontsize=7, color=MUTED, ha="left", va="top")
    fig.savefig(P / f"{name}.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def pipeline():
    steps = [("RR data pack", "200,961 deliveries\nIPL + T20I 2022–26"), ("Clean & state", "legal balls, pre-ball\nscore/wkts/target"),
             ("Win probability", "logistic, per innings\nWPA + Leverage"), ("Pressure", "50% stakes +\n50% difficulty"),
             ("Expectations", "context xRuns / xWkt\n(no player identity)"), ("Opponent-adjusted\nratings", "ridge (Gaussian prior)\nbatter + bowler"),
             ("Reliability score", "5 components,\npercentile composite"), ("Uncertainty", "bootstrap ×100,\nweights & definitions"),
             ("Verification", "identity, availability\n(official sources)"), ("RR squad fit", "separate layer 2\nneeds · fit · uplift")]
    fig, ax = plt.subplots(figsize=(13, 3.6)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 2.4)
    for i, (t, s) in enumerate(steps):
        col_idx = i if i < 5 else 9 - i          # snake layout: row 2 runs right-to-left
        x, y = col_idx * 2 + 0.1, 1.3 if i < 5 else 0.05
        col = PURPLE if i < 8 else PINK
        ax.add_patch(FancyBboxPatch((x, y), 1.7, 1.0, boxstyle="round,pad=0.02,rounding_size=0.08", fc=col, ec="none"))
        ax.text(x + 0.85, y + 0.68, t, ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        ax.text(x + 0.85, y + 0.27, s, ha="center", va="center", color="#EDE7FF", fontsize=7.6)
        if i < 4:
            ax.annotate("", xy=(x + 1.95, y + 0.5), xytext=(x + 1.72, y + 0.5), arrowprops=dict(arrowstyle="->", color=MUTED))
        elif i == 4:
            ax.annotate("", xy=(x + 0.85, 1.08), xytext=(x + 0.85, 1.28), arrowprops=dict(arrowstyle="->", color=MUTED))
        elif i < 9:
            ax.annotate("", xy=(x - 0.25, y + 0.5), xytext=(x - 0.02, y + 0.5), arrowprops=dict(arrowstyle="->", color=MUTED))
    save(fig, "pipeline")


def wp_validation():
    ev = pd.read_csv(MO / "wp_evaluation.csv")
    t = ev[ev.split == "test"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    for ax, inn in zip(axes, (1, 2)):
        r = t[t.innings == inn]
        cols = [LILAC if m.startswith("constant") else (PURPLE if m == "logit" else MUTED) for m in r.model]
        ax.bar(r.model.str.replace("constant(base rate)", "Base rate").str.replace("logit", "Logistic\n(selected)").str.replace("lgbm", "LightGBM"),
               r.brier, color=cols, width=0.55)
        for i, v in enumerate(r.brier):
            ax.text(i, v + 0.004, f"{v:.3f}", ha="center", fontsize=9, color=NAVY)
        ax.set_title(f"Innings {inn}: Brier on held-out 2026 (lower = better)", loc="left", fontsize=10.5)
        ax.set_ylim(0, 0.29); ax.grid(axis="y", color=GRID)
    save(fig, "wp_validation", "Chronological split: train 2022–24, validate 2025 (model chosen here), test 2026. Source: reports/model_outputs/wp_evaluation.csv")


def clutch():
    cv = pd.read_csv(MO / "clutch_variance.csv")
    fig, ax = plt.subplots(figsize=(8, 3.2))
    y = np.arange(len(cv))
    ax.barh(y + 0.18, cv.sd_raw_delta * 100, 0.34, color=LILAC, label="Observed spread of raw pressure deltas")
    ax.barh(y - 0.18, cv.tau_true_sd * 100, 0.34, color=PURPLE, label="Estimated true spread (noise removed)")
    for i, r in cv.iterrows():
        ax.text(r.tau_true_sd * 100 + 0.4, i - 0.18, f"{r.reliability_of_raw_delta:.0%} of raw delta is signal", va="center", fontsize=9, color=NAVY)
    ax.set_yticks(y, cv.side.str.capitalize()); ax.set_xlabel("SD of pressure delta (runs per 100 balls)")
    ax.set_title("How much 'clutch' is real? Empirical-Bayes variance decomposition", loc="left")
    ax.legend(frameon=False, fontsize=8.5, loc="lower right"); ax.grid(axis="x", color=GRID)
    save(fig, "clutch_variance", "Players with ≥60 HIGH and ≥150 other balls. Source: reports/model_outputs/clutch_variance.csv")


def component_heatmap(side):
    s = pd.read_csv(MO / f"reliability_{side}.csv").query("rank <= 10")
    M = s[[f"pct_{k}" for k, _ in COMP]].to_numpy() * 100
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.imshow(M, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("p", ["#F4F0FB", PURPLE]), vmin=40, vmax=100, aspect="auto")
    for (i, j), v in np.ndenumerate(M):
        ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=9, color="white" if v > 78 else NAVY)
    ax.set_xticks(range(len(COMP)), [c for _, c in COMP], fontsize=8.5)
    ax.set_yticks(range(len(s)), [f"{int(r)}. {p}  ({sc:.0f})" for r, p, sc in zip(s["rank"], s.player, s.score)])
    ax.set_title(f"Top 10 {side}: component percentiles (score in brackets)", loc="left")
    ax.spines[:].set_visible(False); ax.tick_params(length=0)
    save(fig, f"components_{side}", "Percentile among eligible players (100 = best). Weights: 35/20/20/15/10. Source: reliability_" + side + ".csv")


def rr_phase():
    ph = pd.read_csv(RESEARCH_DIR / "rr_phase_performance.csv")
    ph = ph[ph.year.isin([2025, 2026]) & ph.metric.isin(["run_rate", "boundary_pct", "dot_pct", "wkts_per_over", "value_per100"])]
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8), gridspec_kw={"wspace": 0.05})
    for ax, side in zip(axes, ("batting", "bowling")):
        v = ph[ph.side == side].pivot_table(index="metric", columns=["phase", "year"], values="rr_rank_of_10")
        v = v.reindex(columns=[(p, y) for p in ("powerplay", "middle", "death") for y in (2025, 2026)])
        ax.imshow(v.to_numpy(), cmap=matplotlib.colors.LinearSegmentedColormap.from_list("r", [PURPLE, "#F4F0FB", PINK]), vmin=1, vmax=10, aspect="auto")
        for (i, j), x in np.ndenumerate(v.to_numpy()):
            ax.text(j, i, f"#{x:.0f}", ha="center", va="center", fontsize=9, color="white" if x <= 2 or x >= 9 else NAVY)
        lab = {"powerplay": "Powerplay", "middle": "Middle", "death": "Death"}
        ax.set_xticks(range(6), [f"{lab[p]}\n{y}" for p, y in v.columns], fontsize=8)
        nice = v.index.str.replace("_pct", " %").str.replace("_per100", " per 100").str.replace("_", " ")
        ax.set_yticks(range(len(v)), nice if side == "batting" else [""] * len(v))
        ax.set_title(f"RR {side}: rank of 10 IPL teams", loc="left"); ax.spines[:].set_visible(False); ax.tick_params(length=0)
    save(fig, "rr_phase_ranks", "1 = best in league (purple), 10 = worst (pink). Bowling ranks: lower run rate/boundary %, higher dots/wickets = better. Source: research/rr_phase_performance.csv")


def rr_players():
    a = pd.read_csv(RESEARCH_DIR / "rr_player_performance_database.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, side, col in ((axes[0], "bat", PURPLE), (axes[1], "bowl", PINK)):
        v = a.dropna(subset=[f"{side}_pressure_pctile_vs_eligible"]).query(f"{side}_balls >= 300")
        ax.scatter(v[f"{side}_usual_pctile_vs_eligible"], v[f"{side}_pressure_pctile_vs_eligible"], s=v[f"{side}_balls"] / 8, color=col, alpha=.75)
        for _, r in v.iterrows():
            ax.annotate(r.player, (r[f"{side}_usual_pctile_vs_eligible"], r[f"{side}_pressure_pctile_vs_eligible"]), fontsize=8,
                        xytext=(4, 4), textcoords="offset points", color=NAVY)
        ax.axhline(50, ls=":", color=MUTED); ax.axvline(50, ls=":", color=MUTED); ax.set_xlim(-3, 103); ax.set_ylim(-3, 103)
        ax.set_xlabel("Usual-ability percentile vs candidate pool"); ax.set_ylabel("Pressure-performance percentile")
        ax.set_title(f"RR {'batters' if side == 'bat' else 'bowlers'} (≥300 balls), same framework as all candidates", loc="left", fontsize=10.5)
    save(fig, "rr_players_pressure", "Bubble size = balls. Source: research/rr_player_performance_database.csv")


def priority():
    pm = pd.read_csv(RESEARCH_DIR / "rr_recruitment_priority_matrix.csv").sort_values("priority_score")
    fig, ax = plt.subplots(figsize=(9, 3.4))
    cmap = {"High": PINK, "Medium": GOLD, "Low": LILAC}
    ax.barh(pm.requirement, pm.priority_score, color=pm.priority.map(cmap), height=0.6)
    for i, (v, p) in enumerate(zip(pm.priority_score, pm.priority)):
        ax.text(v + 1, i, f"{v:.0f} · {p}", va="center", fontsize=9, color=NAVY)
    ax.set_xlim(0, 100); ax.set_xlabel("Priority = 100 × (0.6 × phase-rank severity + 0.4 × coverage gap)")
    ax.set_title("RR recruitment priorities (evidence-led)", loc="left"); ax.grid(axis="x", color=GRID)
    save(fig, "rr_priorities", "Severity: mean RR rank on 4 phase metrics, 2025–26. Coverage: best eligible RR player's pressure percentile. Source: rr_recruitment_priority_matrix.csv")


def fit_vs_rel():
    rec = pd.read_csv(REPORTS_DIR / "rr_recruitment_recommendations.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharex=True)
    for ax, side, col in ((axes[0], "batting", PURPLE), (axes[1], "bowling", PINK)):
        v = rec[rec.side == side]
        mk = np.where(v.indian_or_overseas == "Indian", "o", "D")
        for m in ("o", "D"):
            w = v[mk == m]
            ax.scatter(w.squad_fit_score, w.reliability_rank, color=col, marker=m, s=60, label="Indian" if m == "o" else "Overseas")
        for _, r in v.iterrows():
            ax.annotate(r.player, (r.squad_fit_score, r.reliability_rank), fontsize=8, xytext=(5, -3), textcoords="offset points")
        ax.invert_yaxis(); ax.axvline(78, ls=":", color=MUTED); ax.set_xlabel("RR squad-fit score (layer 2)"); ax.set_ylabel("Reliability rank (layer 1)")
        ax.set_title(f"{side.capitalize()}: reliability vs RR fit", loc="left"); ax.legend(frameon=False, fontsize=8); ax.set_xlim(55, 97)
    save(fig, "fit_vs_reliability", "Dotted line = 'Primary target' threshold (squad fit ≥ 78). Layers are kept separate: fit never reorders the ranking.")


def player_comparison_minis():
    alt = pd.read_csv(REPORTS_DIR / "player_comparisons.csv")
    (P / "players").mkdir(exist_ok=True)
    for side in ("batting", "bowling"):
        s = pd.read_csv(MO / f"reliability_{side}.csv").set_index("player_id")
        for pid in s.index[s["rank"] <= 10]:
            a = alt[(alt.side == side) & (alt.selected_id == pid)]
            names = [s.at[pid, "player"]] + a.alternative.tolist()
            vals = [[s.at[pid, f"pct_{k}"] * 100 for k, _ in COMP]] + [[r[f"pct_{k}_alt"] * 100 for k, _ in COMP] for _, r in a.iterrows()]
            fig, ax = plt.subplots(figsize=(6.6, 2.6))
            x = np.arange(len(COMP)); w = 0.26
            for i, (n, v) in enumerate(zip(names, vals)):
                ax.bar(x + (i - 1) * w, v, w * 0.92, color=[PINK, PURPLE, LILAC][i], label=n)
            ax.set_xticks(x, [c.replace("\n", " ") for _, c in COMP], fontsize=7.5); ax.set_ylim(0, 105); ax.set_ylabel("Percentile", fontsize=8)
            ax.legend(frameon=False, fontsize=7.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.2)); ax.grid(axis="y", color=GRID)
            save(fig, f"players/{side}_{int(s.at[pid, 'rank']):02d}")


def run():
    (P).mkdir(parents=True, exist_ok=True)
    pipeline(); wp_validation(); clutch(); component_heatmap("batting"); component_heatmap("bowling")
    rr_phase(); rr_players(); priority(); fit_vs_rel(); player_comparison_minis()
    print(sorted(p.name for p in P.glob("*.png")))


if __name__ == "__main__":
    run()
