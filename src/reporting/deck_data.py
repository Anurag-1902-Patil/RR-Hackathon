"""Export every number the PPTX deck uses into one JSON, read from the same pipeline outputs as the PDF
(guarantees identical selections and scores across deliverables)."""
from __future__ import annotations

import json

import pandas as pd

from src.config import REPORTS_DIR, RESEARCH_DIR

MO = REPORTS_DIR / "model_outputs"


def rnd(x, n=2):
    return None if pd.isna(x) else round(float(x), n)


def run() -> dict:
    out = {}
    s = pd.read_csv(REPORTS_DIR / "dashboard_data" / "dataset_summary.csv", index_col=0)["value"].to_dict()
    out["summary"] = s
    rec = pd.read_csv(REPORTS_DIR / "rr_recruitment_recommendations.csv")
    alt = pd.read_csv(REPORTS_DIR / "player_comparisons.csv")
    for side in ("batting", "bowling"):
        r = pd.read_csv(MO / f"reliability_{side}.csv")
        t = r[r["rank"] <= 10]
        hb = "balls_high" if side == "batting" else "legal_balls_high"
        rows = []
        for _, x in t.iterrows():
            a = alt[(alt.side == side) & (alt.selected_id == x.player_id)].iloc[0]
            rr = rec[(rec.side == side) & (rec.reliability_rank == x["rank"])].iloc[0]
            rows.append({"rank": int(x["rank"]), "player": x.player, "role": x.role, "score": int(round(x.score)), "p_top10": rnd(x.p_top10),
                         "high_balls": int(x[hb]), "value_high": rnd(x.value_per100_high, 1), "boot_lo": int(x.boot_rank_p05), "boot_hi": int(x.boot_rank_p95),
                         "def_lo": int(x.rank_min_across_defs), "def_hi": int(x.rank_max_across_defs),
                         "alt": a.alternative, "alt_rank": int(a.alternative_rank), "p_beats_alt": rnd(a.p_selected_ranks_higher_bootstrap),
                         "need": rr.rr_need_addressed, "fit": int(rr.squad_fit_score), "tier": rr.recommendation_tier, "nat": rr.indian_or_overseas,
                         "availability": rr.availability, "uplift": rnd(rr.uplift_runs_per_season_MODEL_ESTIMATE, 1)})
        out[side] = rows
    out["pool"] = {side: int(pd.read_csv(MO / f"reliability_{side}.csv")["rr_acquirable"].sum()) for side in ("batting", "bowling")}
    out["unrestricted"] = {}
    for side in ("batting", "bowling"):
        r = pd.read_csv(MO / f"reliability_{side}.csv").sort_values("overall_rank").head(10)
        out["unrestricted"][side] = [{"rank": int(x.overall_rank), "player": x.player, "score": int(round(x.score)),
                                      "why": str(x.not_acquirable_reason) if isinstance(x.not_acquirable_reason, str) else "signable"} for x in r.itertuples()]
    out["uncapped"] = {side: pd.read_csv(REPORTS_DIR / f"top_5_uncapped_{f}.csv").to_dict("records") for side, f in (("batting", "batters"), ("bowling", "bowlers"))}
    out["uncapped_transfer"] = pd.read_csv(MO / "uncapped_transfer_validation.csv").to_dict("records")
    nm = pd.read_csv(MO / "near_misses.csv")
    out["near"] = nm[nm["rank"] <= 13].to_dict("records")
    prof = pd.read_csv(MO / "pressure_profile_final.csv")
    out["pressure_profile"] = prof.to_dict("records")
    ev = pd.read_csv(MO / "wp_evaluation.csv")
    out["wp_test"] = ev[ev.split == "test"][["innings", "model", "brier", "auc"]].round(3).to_dict("records")
    out["clutch"] = pd.read_csv(MO / "clutch_variance.csv")[["side", "tau_true_sd", "sd_raw_delta", "reliability_of_raw_delta"]].round(3).to_dict("records")
    ws = pd.read_csv(MO / "reliability_weight_sensitivity.csv")
    ds = pd.read_csv(MO / "reliability_definition_sensitivity.csv")
    out["robust"] = {side: {"weights_min": int(ws[(ws.side == side) & (ws.variant != "final")].top10_overlap.min()),
                            "defs_min": int(ds[ds.side == side].top10_overlap.min()), "defs_max": int(ds[ds.side == side].top10_overlap.max())}
                     for side in ("batting", "bowling")}
    pm = pd.read_csv(RESEARCH_DIR / "rr_recruitment_priority_matrix.csv")
    out["priorities"] = pm[["requirement", "priority_score", "priority", "best_eligible_rr_cover", "best_cover_pressure_pctile"]].to_dict("records")
    (REPORTS_DIR / "deck_data.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    d = run()
    print([x["player"] for x in d["batting"]], [x["player"] for x in d["bowling"]])
