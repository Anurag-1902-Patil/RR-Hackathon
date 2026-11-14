from pathlib import Path
import pandas as pd
RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "rr_data_pack"
pd.set_option("display.width", 250, "display.max_columns", 40)
bb = pd.read_csv(RAW/"ball_by_ball.csv", low_memory=False); m = pd.read_csv(RAW/"matches.csv")
bb["total"]=bb.runs+bb.extras1_runs+bb.extras_2_runs
for mid in [55561, 20190]:
    x=bb[bb.match_id==mid]; print(mid, m[m.match_id==mid][["match_date","home_team","away_team","result","first_inn_revised_overs","second_inn_revised_overs","revised_target"]].to_string(index=False))
    print(x.groupby("innings").agg(score=("total","sum"),w=("is_wicket","sum"),balls=("runs","size"),last_over=("overid","max")))
    print(x[x.is_wicket][["innings","overid","dismissal_type","striker_name"]].to_string(index=False))
# legal balls if 'other' is treated as no-ball
legal = ~bb.extras_type.isin(["wide","Overstep","other"])
ov = bb[legal].groupby(["match_id","innings","overid"]).size(); print("over legal-ball counts w/ other=noball:"); print(ov.value_counts().sort_index())
g = bb[legal & bb.innings.isin([1,2])].groupby(["match_id","innings"]).size(); print("innings >120 legal:", (g>120).sum())
print("Retire Out rows:"); print(bb[bb.dismissal_type=="Retire Out"][["match_id","striker_name","overid"]])
print("is_wicket rows without dismissed id:", (bb.is_wicket & bb.dismissed_player_id.isna()).sum(), "; dismissed id w/o wicket:", (~bb.is_wicket & bb.dismissed_player_id.notna()).sum())
print(bb[~bb.is_wicket & bb.dismissed_player_id.notna()][["match_id","innings","overid","striker_name","extras_type","dismissed_player_id"]].head(12))
print("bowl_speed>0 share by year:"); bb["yr"]=bb.delivery_ist_time.str[:4]; print(bb.assign(s=bb.bowl_speed>0).groupby("yr").s.mean().round(2))
print("super-over matches:", bb[bb.innings>2].match_id.unique())
