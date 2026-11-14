"""Uncapped Indian track: Syed Mushtaq Ali Trophy (SMAT) ball-by-ball data from Cricsheet.

PUBLIC SOURCE (not in the RR data pack): https://cricsheet.org/downloads/sma_male_json.zip
(Open Data Commons Attribution License). Stored in data/external/ and never committed.

Method = the main pipeline, unchanged where possible:
- Same delivery flags and pre-ball match state; SMAT gets its own rolling par (tier "SMAT").
- Win probability: the data-pack logistic models (fitted on all pack years) applied to SMAT states.
  The tier dummies are 0 (same as IPL); the scoring environment enters through SMAT's own par.
- Same pressure definition (50% leverage percentile + 50% rule-based index), percentiles within SMAT.
- Expected runs/wickets: context-only LightGBM fitted on SMAT itself, leave-one-season-out, recentred
  by season. Cricsheet has no bowling type or batting hand, so those features are absent.
- Strength adjustment: ONE opponent-adjusted ridge fitted on data-pack + SMAT balls together.
  Players who appear in both (matched by name, ambiguous names rejected) link the two scales, so
  a SMAT rating is on the same scale as an IPL rating.
- Same score components and weights. Thresholds are lower because a SMAT season is ~7 league games.
"""
from __future__ import annotations

import glob
import json
import logging
import re

import lightgbm as lgb
import numpy as np

# Windows: LightGBM must run once before pyarrow is loaded, or later fits crash (access violation).
lgb.LGBMRegressor(n_estimators=1, verbose=-1).fit(np.random.default_rng(0).random((50, 2)), np.arange(50.0))

import pandas as pd  # noqa: E402

from src.config import FEATURES_DIR, PROCESSED_DIR, REPORTS_DIR, ROOT
from src.data.build_deliveries import add_match_state
from src.features import pressure as PR
from src.models import expected as E
from src.models import ratings as R
from src.models import win_probability as WP
from src.scouting import player_tables as PT
from src.scouting import reliability as RL

log = logging.getLogger(__name__)
SRC = ROOT / "data" / "external" / "cricsheet_sma"
OUT = FEATURES_DIR / "smat"
MO = REPORTS_DIR / "model_outputs"
FROM_DATE = "2021-01-01"          # SMAT 2020/21 onward (latest season available: 2024/25)
RECENT_FROM = "2023-10-01"        # must have played SMAT 2023/24 or 2024/25
ELIG = {"batting": {"high_balls": 50, "innings": 5}, "bowling": {"high_balls": 60, "spells": 5}}
ID_OFFSET = 10_000_000
BOWLER_WICKETS = {"bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"}
NON_DISMISSAL = {"retired hurt", "retired not out"}


# ---------------------------------------------------------------- parse
def parse() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    rows, matches, people = [], [], {}
    for f in sorted(glob.glob(str(SRC / "*.json"))):
        j = json.load(open(f, encoding="utf-8"))
        info = j["info"]
        date = info["dates"][0]
        if date < FROM_DATE or info.get("gender") != "male":
            continue
        mid = int(re.sub(r"\D", "", f.split("\\")[-1].split("/")[-1]))
        teams = info["teams"]
        reg = info["registry"]["people"]
        people.update({v: k for k, v in reg.items()})
        inns = [i for i in j["innings"] if not i.get("super_over")]
        if len(inns) == 0:
            continue
        oc = info.get("outcome", {})
        tgt = inns[1].get("target", {}) if len(inns) > 1 else {}
        matches.append({"match_id": mid, "match_date": pd.Timestamp(date), "tier": "SMAT", "team1": teams[0], "team2": teams[1],
                        "inn1_max_balls": 6 * int(info.get("overs", 20)), "inn2_max_balls": int(6 * tgt["overs"]) if "overs" in tgt else 6 * int(info.get("overs", 20)),
                        "revised_target": tgt.get("runs") if tgt.get("overs", 20) != 20 else np.nan,
                        "winner": oc.get("winner"), "season": info.get("season"), "event": info.get("event", {}).get("name")})
        for k, inn in enumerate(inns[:2], start=1):
            bat_team = inn["team"]
            bowl_team = teams[1] if bat_team == teams[0] else teams[0]
            order, ib = {}, 0
            for ov in inn.get("overs", []):
                for b_no, dl in enumerate(ov["deliveries"], start=1):
                    ib += 1
                    for p in (dl["batter"], dl["non_striker"]):
                        order.setdefault(p, len(order) + 1)
                    ex = dl.get("extras", {})
                    et = "Wide" if "wides" in ex else "No Ball" if "noballs" in ex else "Byes" if "byes" in ex else "Leg Byes" if "legbyes" in ex else None
                    w = (dl.get("wickets") or [None])[0]
                    rows.append({
                        "match_id": mid, "innings": k, "overid": ov["over"] + 1, "over_ball_num": b_no, "innings_ball_num": ib,
                        "batting_team": bat_team, "bowling_team": bowl_team,
                        "striker_key": reg.get(dl["batter"]), "striker_name": dl["batter"],
                        "non_striker_key": reg.get(dl["non_striker"]), "bowler_key": reg.get(dl["bowler"]), "bowler_name": dl["bowler"],
                        "batting_order": order[dl["batter"]], "runs": dl["runs"]["batter"],
                        "is_four": dl["runs"]["batter"] == 4 and not dl["runs"].get("non_boundary"),
                        "is_six": dl["runs"]["batter"] == 6, "is_wicket": w is not None and w["kind"] not in NON_DISMISSAL,
                        "dismissal_type": w["kind"] if w else None, "dismissed_key": reg.get(w["player_out"]) if w else None,
                        "extras_type": et, "wides": ex.get("wides", 0), "noballs": ex.get("noballs", 0),
                        "extras_total": dl["runs"]["extras"]})
    return pd.DataFrame(rows), pd.DataFrame(matches), people


def flags(d: pd.DataFrame) -> pd.DataFrame:
    d["is_wide"] = d["extras_type"].eq("Wide")
    d["is_noball"] = d["extras_type"].eq("No Ball")
    d["is_legal"] = ~(d["is_wide"] | d["is_noball"])
    d["is_batter_ball"] = ~d["is_wide"]
    d["total_runs"] = d["runs"] + d["extras_total"]
    d["bowler_runs"] = d["runs"] + d["wides"] + d["noballs"]
    d["bowler_wicket"] = d["is_wicket"] & d["dismissal_type"].isin(BOWLER_WICKETS)
    d["striker_out"] = d["is_wicket"] & d["dismissed_key"].eq(d["striker_key"])
    d["non_striker_out"] = d["is_wicket"] & d["dismissed_key"].eq(d["non_striker_key"])
    d["is_dot"] = d["is_legal"] & d["total_runs"].eq(0)
    d["is_boundary"] = d["is_four"] | d["is_six"]
    d["phase"] = pd.cut(d["overid"], bins=[0, 6, 15, 20], labels=["powerplay", "middle", "death"]).astype(str)
    return d


# ---------------------------------------------------------------- identity link to the data pack
def _key(name: str) -> str:
    """'Mahendra Singh Dhoni' -> 'm dhoni'; 'MS Dhoni' -> 'm dhoni' (first initial + surname)."""
    parts = re.sub(r"[^A-Za-z ]", " ", str(name)).split()
    if len(parts) < 2:
        return str(name).lower()
    return f"{parts[0][0].lower()} {parts[-1].lower()}"


def link_to_pack(smat_names: pd.Series) -> pd.Series:
    """Map SMAT player keys to data-pack player IDs for Indian players, only where the
    (first initial, surname) key is unique on BOTH sides. Returns key -> pack player_id."""
    pm = pd.read_parquet(PROCESSED_DIR / "player_map.parquet")
    ind_teams = pm[pm.comp_name.str.startswith("IPL")]
    pack = ind_teams.drop_duplicates("player_id")[["player_id", "player_name"]]
    # exclude obvious overseas players: anyone who played a T20I for a team other than India
    t20 = pm[~pm.comp_name.str.startswith("IPL") & ~pm.team_name.str.contains(" A$| A ", regex=True)]
    foreign = set(t20[t20.team_name.ne("India")].player_id)
    pack = pack[~pack.player_id.isin(foreign)].assign(k=lambda x: x.player_name.map(_key))
    pk = pack.groupby("k").player_id.agg(list)
    pk = pk[pk.str.len() == 1].str[0]
    sm = pd.DataFrame({"key": smat_names.index, "name": smat_names.to_numpy()})
    sm["k"] = sm["name"].map(_key)
    sm = sm[~sm.k.duplicated(keep=False) & sm.k.isin(pk.index)]
    return pd.Series(sm.k.map(pk).to_numpy(), index=sm.key.to_numpy())


# ---------------------------------------------------------------- build the SMAT delivery table
def wp_models(pack: pd.DataFrame, years) -> dict:
    t = WP.training_rows(pack)
    m = {inn: WP.WPModel(inn, "logit").fit(t[t["innings"] == inn]) for inn in (1, 2)}
    return {(y, inn): m[inn] for y in years for inn in (1, 2)}


def build() -> pd.DataFrame:
    raw, mt, people = parse()
    d = flags(raw)
    # integer ids: linked players reuse the pack ID; others get an offset id
    keys = pd.Series(pd.unique(pd.concat([d.striker_key, d.non_striker_key, d.bowler_key]).dropna()))
    names = pd.Series({k: people.get(k, k) for k in keys})
    link = link_to_pack(names)
    ids = {k: int(link[k]) if k in link.index else ID_OFFSET + i for i, k in enumerate(keys)}
    for c in ("striker", "non_striker", "bowler"):
        d[f"{c}_id"] = d[f"{c}_key"].map(ids).astype("Int64")
    d["dismissed_player_id"] = d["dismissed_key"].map(ids)
    teams = {t: 900_000 + i for i, t in enumerate(sorted(set(mt.team1) | set(mt.team2)))}
    d["batting_team_id"] = d["batting_team"].map(teams)
    d["bowling_team_id"] = d["bowling_team"].map(teams)
    mt["win_team_id"] = mt["winner"].map(teams)
    d = add_match_state(d, mt)
    mm = mt.set_index("match_id")
    d["match_date"] = d["match_id"].map(mm["match_date"])
    d["season"] = d["match_id"].map(mm["season"]).astype(str)
    d["year"] = d["season"].str[:4].astype("int32")  # season start year (LOSO grouping; 2020/21 -> 2020)
    d["tier"], d["is_ipl"], d["match_format"], d["comp_name"] = "SMAT", False, "Domestic T20", "Syed Mushtaq Ali Trophy"
    for c in ("bowling_type", "pace_or_spin", "batting_type"):
        d[c] = "Unknown"
    d = d[d.striker_id.notna() & d.bowler_id.notna()].reset_index(drop=True)
    for c in ("striker_id", "non_striker_id", "bowler_id"):
        d[c] = d[c].astype("int64")
    # win probability, WPA, leverage (pack models)
    pack = pd.read_parquet(PROCESSED_DIR / "deliveries.parquet")
    models = wp_models(pack, sorted(d["year"].unique()))
    wp = pd.Series(np.nan, index=d.index)
    for (yr, inn), m in models.items():
        mk = (d["year"] == yr) & (d["innings"] == inn)
        if mk.any():
            wp[mk] = m.predict(d[mk])
    d["wp_before"] = wp
    d["wp_after"] = WP.wp_after(d, wp, models)
    d["wpa_bat"] = d["wp_after"] - d["wp_before"]
    d["leverage"] = WP.leverage_index(d, wp, models)
    # pressure (same definition, percentiles within SMAT)
    p = PR.pressure_table(d)
    d["pressure_score"], d["pressure_band"] = p["pressure_score"], p["pressure_band"]
    d["high"] = d["pressure_band"].eq("high").astype(float)
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_parquet(OUT / "smat_state.parquet", index=False)
    # context expectations, fitted on SMAT, leave-one-season-out, recentred by season
    d = pd.concat([d, E.recentre(d, E.crossfit(d)).filter(like="x_")], axis=1)
    d = R.ball_values(d)
    d["player_link"] = d["striker_id"].lt(ID_OFFSET)
    OUT.mkdir(parents=True, exist_ok=True)
    d.drop(columns=["striker_key", "non_striker_key", "bowler_key", "dismissed_key"]).to_parquet(OUT / "smat_deliveries.parquet", index=False)
    names.rename("name").rename_axis("cricsheet_id").reset_index().assign(
        player_id=lambda x: x.cricsheet_id.map(ids), linked_to_pack=lambda x: x.cricsheet_id.isin(link.index)).to_csv(OUT / "smat_people.csv", index=False)
    log.info("SMAT: %d deliveries, %d matches, %d players (%d linked to pack)", len(d), d.match_id.nunique(), len(keys), len(link))
    return d


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build()
