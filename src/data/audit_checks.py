"""Deep integrity checks on the RR data pack (read-only)."""
from pathlib import Path
import pandas as pd, numpy as np
RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "rr_data_pack"
pd.set_option("display.width", 250, "display.max_columns", 60, "display.max_rows", 300)
r = lambda n: pd.read_csv(RAW / n, low_memory=False)
bb, m, c, t, pe, ctp = map(r, ["ball_by_ball.csv","matches.csv","competitions.csv","teams.csv","playing_eleven.csv","competition_team_player_mapping.csv"])

print("== competitions by format/season"); print(c.groupby(["match_format","season"]).size().unstack(fill_value=0))
print("\n== T20 (non-T20I) comps"); print(c[c.match_format=="T20"].to_string(index=False))
m2 = m.merge(c, on="comp_id", how="left", validate="m:1")
print("\nmatches w/o comp:", m2.match_format.isna().sum())
m2["year"]=pd.to_datetime(m2.match_date).dt.year
print("\n== matches by format/year"); print(m2.groupby(["match_format","year"]).size().unstack(fill_value=0))
print("date range", m2.match_date.min(), m2.match_date.max())

# key integrity
print("\n== key integrity")
print("bb match_ids not in matches:", len(set(bb.match_id)-set(m.match_id)))
miss = sorted(set(m.match_id)-set(bb.match_id)); print("matches without bb:", len(miss))
print(m2[m2.match_id.isin(miss)][["match_id","comp_name","match_date","result"]].to_string(index=False))
print("pe match_ids not in matches:", len(set(pe.match_id)-set(m.match_id)), " matches w/o pe:", len(set(m.match_id)-set(pe.match_id)))
print("teams dup (comp,team):", t.duplicated(["comp_id","team_id"]).sum())
print("ctp dup (comp,team,player):", ctp.duplicated(["comp_id","team_id","player_id"]).sum())
print("pe dup (match,player):", pe.duplicated(["match_id","player_id"]).sum(), " (match,team,player):", pe.duplicated(["match_id","team_id","player_id"]).sum())
bbp = set(bb.striker_id)|set(bb.non_striker_id)|set(bb.bowler_id)
print("bb players not in ctp:", len(bbp-set(ctp.player_id)), " not in pe:", len(bbp-set(pe.player_id)))

# truncation check: last match
last = bb.match_id.iloc[-1]; print("\n== last bb match", last, "order sorted?", bb.match_id.is_monotonic_increasing)
lm = bb[bb.match_id==last]; print(lm.groupby("innings").agg(balls=("runs","size"), maxover=("overid","max")))
print(m2[m2.match_id==last][["match_date","comp_name","result"]].to_string(index=False))
print(lm.tail(3)[["innings","overid","over_ball_num","striker_name","bowler_name","runs","is_wicket"]])

# runs/extras semantics
print("\n== extras_type counts"); print(bb.extras_type.value_counts(dropna=False))
print(pd.crosstab(bb.extras_type.fillna("none"), bb.extras1_runs))
print(pd.crosstab(bb.extras_type.fillna("none"), bb.extras_2_runs))
print("runs>0 on wides:", ((bb.extras_type=="wide")&(bb.runs>0)).sum())
print("is_four but runs!=4:", (bb.is_four&(bb.runs!=4)).sum(), " is_six runs!=6:", (bb.is_six&(bb.runs!=6)).sum(), " runs==4 not four:", ((bb.runs==4)&~bb.is_four).sum(), " runs==6 not six:", ((bb.runs==6)&~bb.is_six).sum())
print("== dismissal types"); print(bb.dismissal_type.value_counts(dropna=False))
print("is_wicket True:", bb.is_wicket.sum(), " dismissed_player set:", bb.dismissed_player_id.notna().sum())
print(pd.crosstab(bb.is_wicket, bb.dismissal_type.fillna("NA")))
print("dismissed != striker/non-striker:", (bb.dismissed_player_id.notna() & (bb.dismissed_player_id!=bb.striker_id) & (bb.dismissed_player_id!=bb.non_striker_id)).sum())
print("== innings dist"); print(bb.groupby("innings").match_id.nunique())
print("== over_ball_num dist"); print(bb.over_ball_num.value_counts().sort_index())
print("== bowling_type"); print(bb.bowling_type.value_counts())
print("bowl_speed==0 share:", (bb.bowl_speed==0).mean().round(3), " stroke null share", bb.stroke.isna().mean().round(3))
print("== per-innings legal-ball counts (inn 1-2)")
legal = ~bb.extras_type.isin(["wide","Overstep"])
g = bb[legal & bb.innings.isin([1,2])].groupby(["match_id","innings"]).size()
print(g.describe()); print("innings with >120 legal:", (g>120).sum())
# name consistency
for idc, nc in [("striker_id","striker_name"),("bowler_id","bowler_name")]:
    x = bb.groupby(idc)[nc].nunique(); print(idc,"ids with >1 name:", (x>1).sum(), bb[bb[idc].isin(x[x>1].index)].groupby(idc)[nc].unique().head(10).to_dict())
    y = bb.groupby(nc)[idc].nunique(); print(nc,"names with >1 id:", (y>1).sum(), y[y>1].index.tolist()[:20])
z = ctp.groupby("player_name").player_id.nunique(); print("ctp names >1 id:", z[z>1].index.tolist())
z = ctp.groupby("player_id").player_name.nunique(); print("ctp ids >1 name:", ctp[ctp.player_id.isin(z[z>1].index)].drop_duplicates(["player_id","player_name"])[["player_id","player_name"]].to_string(index=False))
# batting_order consistency
print("\n== playing_eleven: is_played vs batting_order null"); print(pd.crosstab(pe.is_played, pe.batting_order.isna()))
print("impact counts", pe.is_impact.sum(), pe.is_impact_off.sum())
print("players per match-team:"); print(pe.groupby(["match_id","team_id"]).size().value_counts().sort_index())
# results
print("\n== no-winner matches"); print(m2[m2.win_team_id.isna()].result.value_counts())
print("man_of_the_match==0:", (m.man_of_the_match==0).sum())
print("== stage"); print(m2.stage.value_counts())
print("== delivery time 00:00:00 rows:", bb.delivery_ist_time.str.contains("00:00:00 UTC").sum())
