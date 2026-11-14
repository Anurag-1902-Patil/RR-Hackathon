"""Score reconciliation and extras semantics checks (read-only)."""
from pathlib import Path
import re, pandas as pd, numpy as np
RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "rr_data_pack"
pd.set_option("display.width", 250, "display.max_columns", 60, "display.max_rows", 300)
r = lambda n: pd.read_csv(RAW / n, low_memory=False)
bb, m, c, pe, ctp = map(r, ["ball_by_ball.csv","matches.csv","competitions.csv","playing_eleven.csv","competition_team_player_mapping.csv"])
m = m.merge(c, on="comp_id", validate="m:1")
print("== matches per comp (T20)"); print(m[m.match_format=="T20"].groupby("comp_name").size())

bb["total"] = bb.runs + bb.extras1_runs + bb.extras_2_runs
print("\n== sample rows per extras type")
for et in ["wide","Overstep","other","byes","legbyes","Penalty"]:
    print(et); print(bb[bb.extras_type==et][["runs","extras1_runs","extras_2_runs","is_four","over_ball_num"]].value_counts().head(6))
# Over with >6 legal balls?
legal = ~bb.extras_type.isin(["wide","Overstep"])
ov = bb[legal].groupby(["match_id","innings","overid"]).size()
print("\novers by legal-ball count:"); print(ov.value_counts().sort_index())
bad = ov[ov>6].reset_index().head(3); print(bad)
if len(bad):
    k=bad.iloc[0]; print(bb[(bb.match_id==k.match_id)&(bb.innings==k.innings)&(bb.overid==k.overid)][["over_ball_num","innings_ball_num","striker_name","bowler_name","runs","extras_type","extras1_runs","extras_2_runs","is_wicket","delivery_ist_time"]])

# score reconciliation
inn = bb[bb.innings.isin([1,2])].groupby(["match_id","innings"]).agg(team=("batting_team_id","first"), score=("total","sum"), wkts=("is_wicket","sum"), balls=("runs","size")).reset_index()
w = inn.pivot(index="match_id", columns="innings", values=["team","score","wkts"])
w.columns=[f"{a}{b}" for a,b in w.columns]; w=w.reset_index().merge(m[["match_id","result","win_team_id","comp_name","revised_target"]], on="match_id")
def check(row):
    res=str(row.result); mm=re.search(r"Won by (\d+) (run|wicket)", res, re.I)
    if not mm or pd.isna(row.get("score2")): return "n/a"
    n=int(mm.group(1)); kind=mm.group(2).lower()
    if kind=="run":
        ok = (row.team1==row.win_team_id) and (row.score1-row.score2==n)
    else:
        ok = (row.team2==row.win_team_id) and (row.score2>row.score1 or not pd.isna(row.revised_target)) and (10-row.wkts2==n)
    return "ok" if ok else "MISMATCH"
w["chk"]=w.apply(check, axis=1)
print("\n== result reconciliation"); print(w.chk.value_counts())
print(w[w.chk=="MISMATCH"][["match_id","comp_name","score1","wkts1","score2","wkts2","result","revised_target"]].to_string(index=False))
print("\n== matches with only 1 innings in bb:"); one = w[w.score2.isna()]; print(one[["match_id","comp_name","score1","wkts1","result"]].to_string(index=False))
print("\n== pe duplicates"); d=pe[pe.duplicated(["match_id","player_id"],keep=False)].sort_values(["match_id","player_id"]); print(d.head(8)); print(d.match_id.nunique(),"matches")
print("\n== pe: batting_order in bb vs pe consistency (sample)")
bo = bb.groupby(["match_id","striker_id"]).batting_order.first().reset_index().merge(pe[pe.is_played==True].drop_duplicates(["match_id","player_id"]), left_on=["match_id","striker_id"], right_on=["match_id","player_id"], how="left", suffixes=("_bb","_pe"))
print("striker rows not in pe(played):", bo.batting_order_pe.isna().sum(), " order mismatches:", (bo.batting_order_bb!=bo.batting_order_pe).sum(), "of", len(bo))
print("\n== duplicate names detail")
for nm in ['Abdul Samad','Bashir Ahmad','Basil Hameed','Haider Ali','Mohammad Ali','Muhammad Farooq','Rashid Khan']:
    print(nm, ctp[ctp.player_name==nm].groupby("player_id").team_name.unique().to_dict())
print("\n== players per format (bb)")
bbm = bb.merge(m[["match_id","match_format","comp_name"]], on="match_id")
bbm["is_ipl"]=bbm.comp_name.str.startswith("IPL")
print("batters IPL:", bbm[bbm.is_ipl].striker_id.nunique(), " batters T20I:", bbm[bbm.match_format=="T20I"].striker_id.nunique(), " both:", len(set(bbm[bbm.is_ipl].striker_id)&set(bbm[bbm.match_format=="T20I"].striker_id)))
print("bowlers IPL:", bbm[bbm.is_ipl].bowler_id.nunique(), " bowlers T20I:", bbm[bbm.match_format=="T20I"].bowler_id.nunique())
print("balls by segment:"); print(bbm.groupby(["match_format","is_ipl"]).size())
print("T20I teams:", sorted(m[m.match_format=="T20I"].home_team.unique().tolist()+m[m.match_format=="T20I"].away_team.unique().tolist()) and sorted(set(m[m.match_format=="T20I"].home_team)|set(m[m.match_format=="T20I"].away_team)))
rr = 7 if False else None
print("\n== RR team id:", m[m.home_team.str.contains("Rajasthan")].home_team_id.unique())
