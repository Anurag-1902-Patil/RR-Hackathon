"""Verified external facts for the provisional top-10 batters and bowlers (accessed 2026-11-14).

Every field is OBSERVED from the cited source; `age_at_auction` is CALCULATED from DOB to the
reported auction date (16 Dec 2026). Source IDs refer to research/RESEARCH_SOURCE_REGISTER.md.
Flags summarise availability / risk; they never change the data-driven reliability score.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from src.config import REPORTS_DIR, RESEARCH_DIR

AUCTION_DATE = date(2026, 12, 16)

# player_id: (full name, DOB, country, bat, bowl, IPL 2026 team, IPL 2027 status, flags, sources)
FACTS = {
    3647: ("Shreyas Santosh Iyer", "1994-12-06", "India", "RHB", "Right-arm leg break", "Punjab Kings (captain)",
           "Pending retention (17 Nov)", "India T20I captain from Jun 2026; spleen injury on 2025 Australia tour, returned Jan 2026", "W-SI"),
    4260: ("Heinrich Klaasen", "1991-07-30", "South Africa", "RHB", "Right-arm off spin", "Sunrisers Hyderabad",
           "Pending retention (17 Nov)", "Retired from international cricket (2 Jun 2025); IPL/leagues only", "W-HK"),
    5039: ("Rajat Manohar Patidar", "1993-06-01", "India", "RHB", "Right-arm off break", "Royal Challengers Bengaluru (captain)",
           "Pending retention (17 Nov)", "Missed IPL 2023 (Achilles); page reports RCB titles 2025 and 2026 (single source)", "W-RP"),
    7897: ("Namboori Thakur Tilak Varma", "2002-11-08", "India", "LHB", "Right-arm off break", "Mumbai Indians",
           "Pending retention (17 Nov)", "Returned from surgery before Feb 2026 T20 WC call-up", "W-TV"),
    1318: ("Andre Dwayne Russell", "1988-04-29", "West Indies", "RHB", "Right-arm fast", "None: KKR power coach",
           "RETIRED FROM IPL (30 Nov 2025): not available", "Also retired from international cricket (17 Jul 2025); still plays other T20 leagues", "W-AR; S7"),
    4117: ("Ishan Pranav Kumar Pandey Kishan", "1998-07-18", "India", "LHB", "Leg break / off break", "Sunrisers Hyderabad (interim captain early 2026)",
           "Pending retention (17 Nov)", "Wicket-keeper batter", "W-IK"),
    37052: ("Naman Dhir", "1999-12-31", "India", "RHB", "Right-arm off break", "Mumbai Indians",
            "Pending retention (17 Nov)", "India debut 2026; 14 games / 318 runs IPL 2026 (page)", "W-ND"),
    6396: ("Timothy Hays David", "1996-03-16", "Australia", "RHB", "Right-arm off break", "Royal Challengers Bengaluru",
           "Pending retention (17 Nov)", "Overseas", "W-TD"),
    1077: ("David Andrew Miller", "1989-06-10", "South Africa", "LHB", "Right-arm off break", "Delhi Capitals",
           "Pending retention (17 Nov)", "Overseas; age 37 at auction", "W-DM"),
    1699: ("Suryakumar Ashok Yadav", "1990-09-14", "India", "RHB", "Right-arm off break", "Mumbai Indians",
           "Pending retention (17 Nov)", "Removed as India T20I captain and dropped from T20I squads in 2026; page calls IPL 2026 'terrible'", "W-SKY"),
    4853: ("Glenn Dominic Phillips", "1996-12-06", "New Zealand", "RHB", "Right-arm off break", "Gujarat Titans",
           "Pending retention (17 Nov)", "Overseas; missed IPL 2025 (injury) but retained by GT for 2026 (S11); only 5 IPL games each in 2023 and 2026 in data, so rating leans on T20Is", "W-GP; S11; D"),
    6256: ("Varun Chakaravarthy Vinod", "1991-08-29", "India", "RHB", "Right-arm leg break googly", "Kolkata Knight Riders",
           "Pending retention (17 Nov)", "Missed early IPL 2026 games (fitness reports, news only)", "W-VC"),
    781: ("Sunil Philip Narine", "1988-05-26", "West Indies", "LHB", "Right-arm off break", "Kolkata Knight Riders",
          "Pending retention (17 Nov)", "Retired from internationals (Nov 2023); age 38 at auction; first overseas bowler to 200 IPL wickets (3 May 2026)", "W-SN"),
    2933: ("Jasprit Jasbir Singh Bumrah", "1993-12-06", "India", "RHB", "Right-arm fast", "Mumbai Indians",
           "Pending retention (17 Nov)", "Workload management references (Mar and Oct 2026); missed IPL 2023 (back)", "W-JB"),
    4692: ("Lachlan Hammond Ferguson", "1991-06-13", "New Zealand", "RHB", "Right-arm fast", "Punjab Kings",
           "Pending retention (17 Nov)", "Overseas; only 4 (2025) and 3 (2026) IPL matches in data, so rating leans on T20Is", "W-LF; D"),
    4722: ("Rashid Khan Arman", "1998-09-20", "Afghanistan", "RHB", "Leg break googly", "Gujarat Titans",
           "Pending retention (17 Nov)", "Overseas", "W-RK"),
    2876: ("Akshar Rajeshbhai Patel (Axar)", "1994-01-20", "India", "LHB", "Slow left-arm orthodox", "Delhi Capitals (captain)",
           "Pending retention (17 Nov)", "All-rounder", "W-AP"),
    8661: ("Matheesha Pathirana", "2002-12-18", "Sri Lanka", "RHB", "Right-arm fast", "Kolkata Knight Riders",
           "Pending retention (17 Nov)", "INJURY: ruled out of IPL 2026 (hamstring, 24 May 2026) after 1 match; earlier calf injury at Feb 2026 T20 WC; surgery reported Jun 2026 (news, not opened)", "W-MP; S8"),
    360: ("Bhuvneshwar Kumar Singh", "1990-02-05", "India", "RHB", "Right-arm medium", "Royal Challengers Bengaluru",
          "Pending retention (17 Nov)", "Recalled to India T20I squad Oct 2026; age 36 at auction", "W-BK"),
    3644: ("Kuldeep Yadav", "1994-12-14", "India", "LHB", "Left-arm wrist spin", "Delhi Capitals",
           "TRADED DC -> LSG (IPL press release 23 Jun 2026, Rs 13.5 cr)", "Under contract with LSG for 2027 unless released", "W-KY; S9; S10"),
    2984: ("Sikandar Raza Butt", "1986-04-24", "Zimbabwe", "RHB", "Right-arm off break", "None (last IPL: Punjab Kings 2024)",
           "No IPL contract: potential auction entrant if registered (registration not verified)", "Zimbabwe T20I captain; age 40 at auction", "W-SR; D"),
}
COLS = ["full_name", "dob", "country", "bat", "bowl", "ipl_2026_team", "ipl_2027_status", "notes", "sources"]


def register() -> pd.DataFrame:
    rows = []
    for side, f in (("batting", "reliability_batting"), ("bowling", "reliability_bowling")):
        s = pd.read_csv(REPORTS_DIR / "model_outputs" / f"{f}.csv").set_index("player_id")
        for pid in s.index[s["rank"] <= 10]:
            fact = dict(zip(COLS, FACTS[pid]))
            dob = date.fromisoformat(fact["dob"])
            age = AUCTION_DATE.year - dob.year - ((AUCTION_DATE.month, AUCTION_DATE.day) < (dob.month, dob.day))
            status = fact["ipl_2027_status"]
            avail = ("UNAVAILABLE" if status.startswith("RETIRED") else
                     "AUCTION POOL CANDIDATE (unverified)" if status.startswith("No IPL contract") else
                     "CONTRACTED ELSEWHERE" if status.startswith("TRADED") else "DEPENDS ON RETENTIONS")
            rows.append({"side": side, "rank": int(s.at[pid, "rank"]), "player_id": pid, "data_name": s.at[pid, "player"],
                         **fact, "age_at_auction_calc": age, "overseas_for_ipl": fact["country"] != "India",
                         "availability_class": avail, "identity_check": "Data-pack ID matches country, IPL teams and handedness/bowling type",
                         "verified_on": "2026-11-14"})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    r = register()
    r.to_csv(RESEARCH_DIR / "player_verification_register.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 20, "display.max_colwidth", 50)
    print(r[["side", "rank", "data_name", "country", "age_at_auction_calc", "ipl_2026_team", "availability_class"]].to_string(index=False))
