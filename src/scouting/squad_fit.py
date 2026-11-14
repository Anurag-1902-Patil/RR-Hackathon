"""Layer 2: RR squad fit, alternatives, head-to-head evidence and hypothetical phase uplift.

Kept SEPARATE from the reliability score (layer 1); it never reorders the competition top 10.

Squad-fit score (0-100), per shortlisted player:
  50%  requirement priority  - RR priority score (research/rr_recruitment_priority_matrix.csv) of the
                               requirement the player best fits (best of priority x phase evidence)
  35%  phase evidence        - player's empirical-Bayes context value in that phase, percentile among
                               eligible players with >= 120 balls in that phase
  15%  slot cost             - Indian 1.0, overseas 0.5. ASSUMPTION: an overseas signing must displace an
                               overseas regular in a max-4-overseas XI; reported with and without it.
Uplift (MODEL ESTIMATE, hypothetical): (candidate phase value/ball - weakest RR 2026 regular's phase
value/ball) x that regular's 2026 IPL balls in the phase. Not a forecast; ignores role interactions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import FEATURES_DIR, REPORTS_DIR, RESEARCH_DIR, RR_TEAM_ID
from src.models import ratings as R
from src.scouting import reliability as RL

W = {"priority": 0.50, "phase": 0.35, "slot": 0.15}
SLOT = {"Indian": 1.0, "Overseas": 0.5}
PHASE_MIN_BALLS = 120
REQ = {("batting", "powerplay"): "Powerplay / opening batting", ("batting", "middle"): "Middle-overs batting",
       ("batting", "death"): "Death-overs / finishing batting", ("bowling", "powerplay"): "Powerplay bowling",
       ("bowling", "middle"): "Middle-overs bowling", ("bowling", "death"): "Death-overs bowling"}
SIDE = {"batting": ("striker_id", "v_bat", "is_batter_ball"), "bowling": ("bowler_id", "v_bowl", None)}


def phase_profiles(d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out = {}
    for side, (pid, val, flt) in SIDE.items():
        r = d[d[flt]] if flt else d
        prof = []
        for ph in ("powerplay", "middle", "death"):
            rp = r[r["phase"].eq(ph)]
            n = rp.groupby(pid).size().rename(f"balls_{ph}")
            eb = RL.eb_rate(rp, pid, val).mul(100).rename(f"value_eb_{ph}")
            prof += [n, eb]
        p = pd.concat(prof, axis=1)
        tot = p[[f"balls_{ph}" for ph in ("powerplay", "middle", "death")]].sum(axis=1)
        for ph in ("powerplay", "middle", "death"):
            p[f"share_{ph}"] = 100 * p[f"balls_{ph}"].fillna(0) / tot
        out[side] = p
    return out


def nationality(t: pd.DataFrame) -> pd.Series:
    """Verified register country first (shortlisted players); else the data's T20I side; else 'Unverified'.
    (A missing T20I side must NOT be read as Indian: e.g. Sunil Narine, retired from internationals 2023.)"""
    reg = pd.read_csv(RESEARCH_DIR / "player_verification_register.csv").drop_duplicates("player_id").set_index("player_id")["country"]
    from_data = t["national_side"].map(lambda s: "Indian" if s in ("India", "India A") else ("Overseas" if isinstance(s, str) else "Unverified"))
    verified = t.index.to_series().map(reg).map(lambda c: np.nan if pd.isna(c) else ("Indian" if c == "India" else "Overseas"))
    return verified.fillna(from_data)


def squad_fit(rel: dict[str, pd.DataFrame], prof: dict[str, pd.DataFrame], pm: pd.DataFrame) -> pd.DataFrame:
    pri = pm.set_index("requirement")["priority_score"]
    rows = []
    for side, s in rel.items():
        p = prof[side]
        elig = s.index
        for pid in s.index[s["rank"] <= 10]:
            best = None
            for ph in ("powerplay", "middle", "death"):
                if p.at[pid, f"balls_{ph}"] < PHASE_MIN_BALLS or pd.isna(p.at[pid, f"balls_{ph}"]):
                    continue
                pool = p.loc[p.index.isin(elig) & (p[f"balls_{ph}"] >= PHASE_MIN_BALLS), f"value_eb_{ph}"]
                pct = 100 * (pool < p.at[pid, f"value_eb_{ph}"]).mean()
                req = REQ[(side, ph)]
                cand = (pri[req] * pct, ph, req, pct)
                best = cand if best is None or cand[0] > best[0] else best
            nat = "Indian" if s.at[pid, "nat"] == "Indian" else "Overseas"
            _, ph, req, pct = best
            fit = W["priority"] * pri[req] + W["phase"] * pct + W["slot"] * 100 * SLOT[nat]
            fit_no_slot = (W["priority"] * pri[req] + W["phase"] * pct) / (W["priority"] + W["phase"])
            rows.append({"side": side, "rank": int(s.at[pid, "rank"]), "player_id": pid, "player": s.at[pid, "player"],
                         "role": s.at[pid, "role"], "indian_or_overseas": nat, "best_fit_requirement": req, "best_fit_phase": ph,
                         "requirement_priority": pri[req], "phase_balls": int(p.at[pid, f"balls_{ph}"]),
                         "phase_value_eb_per100": round(p.at[pid, f"value_eb_{ph}"], 2), "phase_value_pctile": round(pct, 0),
                         "squad_fit_score": round(fit, 0), "squad_fit_no_slot": round(fit_no_slot, 0)})
    return pd.DataFrame(rows)


def alternatives(rel: dict[str, pd.DataFrame], boot: dict[str, pd.DataFrame], n_alt: int = 2) -> pd.DataFrame:
    """Two highest-scoring UNSELECTED eligible players in the same data role (strongest real competition);
    if fewer exist, fill with the next highest-scoring unselected players of the same side."""
    rows = []
    for side, s in rel.items():
        sel = s[s["rank"] <= 10]
        rest = s[s["rank"] > 10].sort_values("rank")
        m = boot[side]
        for pid, r in sel.iterrows():
            same = rest[rest["role"].eq(r["role"])]
            alts = pd.concat([same, rest.drop(same.index)]).head(n_alt)
            for aid, a in alts.iterrows():
                p_better = float((m.loc[pid] < m.loc[aid]).mean()) if pid in m.index and aid in m.index else np.nan
                rows.append({"side": side, "selected_rank": int(r["rank"]), "selected": r["player"], "selected_id": pid,
                             "alternative": a["player"], "alternative_id": aid, "alternative_rank": int(a["rank"]),
                             "same_role": a["role"] == r["role"], "role_selected": r["role"], "role_alternative": a["role"],
                             "p_selected_ranks_higher_bootstrap": round(p_better, 2),
                             **{f"{k}_{who}": x[k] for who, x in (("sel", r), ("alt", a)) for k in
                                ("score", "pct_pressure_perf", "pct_consistency", "pct_impact", "pct_delta", "pct_usual",
                                 "pressure_innings", "consistency_raw", "wpa_high_total", "p_top10")},
                             "high_balls_sel": r["balls_high" if side == "batting" else "legal_balls_high"],
                             "high_balls_alt": a["balls_high" if side == "batting" else "legal_balls_high"],
                             "value100_high_sel": r["value_per100_high"], "value100_high_alt": a["value_per100_high"],
                             "nat_sel": r["nat"], "nat_alt": a["nat"]})
    return pd.DataFrame(rows)


def near_misses(rel: dict[str, pd.DataFrame], boot: dict[str, pd.DataFrame], k: int = 5) -> pd.DataFrame:
    rows = []
    for side, s in rel.items():
        tenth = s.index[s["rank"] == 10][0]
        m = boot[side]
        for pid, r in s[(s["rank"] > 10) & (s["rank"] <= 10 + k)].iterrows():
            comp = {c: r[f"pct_{c}"] - s.at[tenth, f"pct_{c}"] for c in ("pressure_perf", "consistency", "impact", "delta", "usual")}
            worst = min(comp, key=comp.get)
            rows.append({"side": side, "rank": int(r["rank"]), "player": r["player"], "role": r["role"], "score": round(r["score"], 1),
                         "gap_to_rank10": round(s.at[tenth, "score"] - r["score"], 1), "p_top10": r["p_top10"],
                         "p_beats_rank10_bootstrap": round(float((m.loc[pid] < m.loc[tenth]).mean()), 2),
                         "main_shortfall_vs_rank10": f"{worst} percentile {comp[worst]:+.2f}",
                         "rank_range_across_defs": f"{int(r['rank_min_across_defs'])}-{int(r['rank_max_across_defs'])}"})
    return pd.DataFrame(rows)


def uplift(fit: pd.DataFrame, prof: dict[str, pd.DataFrame], d: pd.DataFrame) -> pd.DataFrame:
    dep = pd.read_csv(RESEARCH_DIR / "rr_role_depth_chart.csv")
    rows = []
    for r in fit.itertuples():
        side, ph = r.side, r.best_fit_phase
        regs = dep[(dep.side == side) & (dep.phase == ph)].sort_values("balls", ascending=False).head(3)
        p = prof[side]
        regs = regs.assign(eb=regs.player_id.map(p[f"value_eb_{ph}"]))
        weak = regs.loc[regs.eb.idxmin()]
        gain = (p.at[r.player_id, f"value_eb_{ph}"] - weak.eb) / 100 * weak.balls
        rows.append({"side": side, "rank": r.rank, "player": r.player, "phase": ph, "replaces_weakest_rr_regular": weak.player,
                     "rr_regular_phase_value_eb_per100": round(weak.eb, 1), "candidate_phase_value_eb_per100": round(p.at[r.player_id, f"value_eb_{ph}"], 1),
                     "rr_regular_2026_phase_balls": int(weak.balls), "est_runs_gained_per_season_MODEL_ESTIMATE": round(gain, 1)})
    return pd.DataFrame(rows)


def run() -> dict[str, pd.DataFrame]:
    d = R.ball_values(R.load())
    rel = {}
    for side in ("batting", "bowling"):
        s = pd.read_csv(REPORTS_DIR / "model_outputs" / f"reliability_{side}.csv").set_index("player_id")
        s["nat"] = nationality(s)
        rel[side] = s
    boot = {s: pd.read_parquet(FEATURES_DIR / f"bootstrap_ranks_{s}.parquet") for s in rel}
    prof = phase_profiles(d)
    pm = pd.read_csv(RESEARCH_DIR / "rr_recruitment_priority_matrix.csv")
    fit = squad_fit(rel, prof, pm)
    alt = alternatives(rel, boot)
    nm = near_misses(rel, boot)
    up = uplift(fit, prof, d)
    fit.merge(up[["side", "rank", "replaces_weakest_rr_regular", "est_runs_gained_per_season_MODEL_ESTIMATE"]], on=["side", "rank"]).to_csv(
        REPORTS_DIR / "squad_fit_analysis.csv", index=False)
    fit.to_csv(RESEARCH_DIR / "player_to_rr_squad_fit.csv", index=False)
    alt.to_csv(REPORTS_DIR / "player_comparisons.csv", index=False)
    nm.to_csv(REPORTS_DIR / "model_outputs" / "near_misses.csv", index=False)
    up.to_csv(RESEARCH_DIR / "rr_phase_uplift_scenarios.csv", index=False)
    for side, p in prof.items():
        p.to_parquet(FEATURES_DIR / f"phase_profiles_{side}.parquet")
    return {"fit": fit, "alt": alt, "near": nm, "uplift": up}


if __name__ == "__main__":
    pd.set_option("display.width", 260, "display.max_columns", 30, "display.max_colwidth", 40)
    r = run()
    print(r["fit"].to_string(index=False))
    print(r["alt"][["side", "selected_rank", "selected", "alternative", "alternative_rank", "same_role", "score_sel", "score_alt",
                    "p_selected_ranks_higher_bootstrap"]].to_string(index=False))
    print(r["near"].to_string(index=False))
    print(r["uplift"].to_string(index=False))
