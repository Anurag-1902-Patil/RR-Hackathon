"""Verified facts for every player in the SMAT uncapped pool (Wikipedia pages read 2026-11-14;
IPL 2026 squads from 'List of 2026 Indian Premier League personnel changes', source W-IPL26).

Key = Cricsheet scorecard name. Value = (full name, DOB or None, India international, retired, IPL 2026 squad, note).
Players without a verifiable page/DOB are excluded as unverifiable (never guessed).
"""
from __future__ import annotations

from datetime import date

AUCTION_DATE = date(2026, 12, 16)
MAX_AGE = 30  # "fresher": aged 30 or under at the IPL 2027 auction (user request: new uncapped players)

FACTS = {
    # batting pool
    "M Vohra": ("Manan Vohra", "1993-07-18", None, False, None, "IPL: KXIP, RCB, RR 2021, LSG 2022-23"),
    "Rahul Buddhi": ("Rahul Ravinder Buddhi", "1997-09-20", None, False, None, "Hyderabad; no IPL team"),
    "PN Mankad": ("Prerak Nileshkumar Mankad", "1994-04-23", None, False, None, "IPL: PBKS 2022, LSG 2023"),
    "Samarth Vyas": ("Samarth Bipin Vyas", "1995-11-28", None, False, None, "IPL: SRH 2023 (released)"),
    "Chirag Gandhi": ("Chirag Jayeshkumar Gandhi", "1990-06-18", None, False, None, "Gujarat"),
    "Ritwik Roy Chowdhury": ("Ritwik Rupnath Roy Chowdhury", "1995-11-20", None, False, None, "Bengal"),
    "N Jagadeesan": ("Narayan Jagadeesan", "1995-12-24", None, False, None, "Test squad call-up 2025, no appearance stated; IPL: CSK 2020-22, KKR 2023"),
    "A Manohar": ("Abhinav Manohar Sadarangani", "1994-09-16", None, False, None, "IPL: GT 2022-24, SRH 2025"),
    "Rajat Dey": ("Rajat Arjun Dey", "1996-12-31", None, False, None, "Tripura; no IPL team"),
    "AV Wankhade": ("Akshay Wankhade", None, None, False, None, "no Wikipedia page: unverifiable"),
    "Parth Sahani": ("Parth Mukesh Sahani", "1993-03-09", None, False, None, "Madhya Pradesh"),
    "Chirag Jani": ("Chirag Sureshbhai Jani", "1989-11-09", None, False, None, "Saurashtra"),
    "Atharva Taide": ("Atharva Taide", "2000-04-26", None, False, None, "IPL: PBKS 2023-24, SRH 2025; not on a 2026 squad"),
    "RV Patel": ("Ripal Vinubhai Patel", "1995-09-28", None, False, None, "IPL: DC 2021-23"),
    "Vishnu Solanki": ("Vishnu Purshottam Solanki", "1992-10-15", None, False, None, "Baroda"),
    "Harsh Tyagi": ("Harsh Tyagi", "1999-12-23", None, False, None, "Delhi/Railways all-rounder; no IPL team"),
    "SP Jackson": ("Sheldon Jackson", None, None, False, None, "cricketer page not found (title is a different person): unverifiable"),
    "Shubham Pundir": ("Shubham Singh Pundir", "1998-10-16", None, False, None, "Jammu & Kashmir; no IPL team"),
    "Subhransu Senapati": ("Subhranshu Pradeep Senapati", "1996-12-30", None, False, None, "Odisha/MP; IPL: CSK squad 2022-23"),
    "V Shankar": ("Vijay Shankar", "1991-01-26", "ODI/T20I (2018-19)", False, None, "capped"),
    "Shivam Chaudhary": ("Shivam Chaudhary", "1997-08-04", None, False, None, "Railways; no IPL team"),
    "RK Bhui": ("Ricky Kannakumar Bhui", "1996-09-29", None, False, None, "IPL: SRH 2018-19, DC 2024"),
    "Upendra Yadav": ("Upendra Diwansingh Yadav", "1996-10-08", None, False, None, "Railways; IPL: SRH 2023"),
    "Shivam Bhambri": ("Shivam Bhambri", "1995-09-30", None, False, None, "Chandigarh"),
    "Bhanu Pania": ("Bhanu Pania", None, None, False, None, "no Wikipedia page: unverifiable"),
    # bowling pool
    "KC Cariappa": ("Konganda Charamanna Cariappa", "1994-04-13", None, True, None, "Jan 2026"),
    "LI Meriwala": ("Lukman Iqbal Meriwala", "1991-12-11", None, False, None, "Baroda"),
    "R Sai Kishore": ("Ravisrinivasan Sai Kishore", "1996-11-06", "T20I (2023)", False, "Gujarat Titans", "capped; on GT 2026 squad"),
    "K Gowtham": ("Krishnappa Gowtham", "1988-10-20", "ODI (2021)", True, None, "Dec 2025"),
    "Cheepurapalli Stephen": ("Cheepurapalli Veeraghavulu Stephen", "1993-12-03", None, False, None, "Andhra"),
    "Ravi Teja": ("Telukupalli Ravi Teja", "1994-10-19", None, False, None, "Hyderabad"),
    "Mohit Avasthi": ("Mohit Anil Avasthi", "1992-11-18", None, False, None, "Mumbai"),
    "Dharmendrasinh Jadeja": ("Dharmendrasinh Aniruddsinh Jadeja", "1990-08-04", None, False, None, "Saurashtra/Chhattisgarh"),
    "M Mohammed": ("M. Mohammed", "1991-12-03", None, False, None, "Tamil Nadu"),
    "PP Chawla": ("Piyush Chawla", "1988-12-24", "Test/ODI/T20I", True, None, "Jun 2025"),
    "S Sandeep Warrier": ("Sankarankutty Sandeep Warrier", "1991-04-04", "T20I (2021)", False, None, "capped"),
    "S Kaul": ("Siddarth Kaul", "1990-05-19", "T20I/ODI (2018)", True, None, "from Indian cricket, 2024"),
    "Tanay Thyagarajan": ("Tanay Thyagarajan", "1995-11-15", None, False, None, "Hyderabad"),
    "A Sheth": ("Atit Arpit Sheth", "1996-02-03", None, False, None, "Baroda"),
    "Harishankar Reddy": ("Maramreddy Harishankar Reddy", "1998-06-02", None, False, None, "Andhra"),
    "CV Milind": ("Chama Vrajendra Milind", "1994-09-04", None, False, None, "Hyderabad"),
    "DG Nalkande": ("Darshan Girish Nalkande", "1998-10-04", None, False, None, "Vidarbha; IPL: GT 2022-24"),
    "K D Patel": ("K D Patel", None, None, False, None, "identity ambiguous: unverifiable"),
    "Abid Mushtaq": ("Abid Mushtaq Mangnoo", "1997-01-17", None, False, None, "Jammu & Kashmir; IPL: RR 2024"),
    "Vijaykumar Vyshak": ("Vijaykumar Vyshak", None, None, False, "Punjab Kings", "on PBKS 2026 squad (data pack: 'Vyshak Kumar')"),
    "M Prasidh Krishna": ("Prasidh Krishna", None, "Test/ODI/T20I", False, "Gujarat Titans", "capped"),
    "A Nagwaswalla": ("Arzan Rohinton Nagwaswalla", "1997-10-17", None, False, None, "Gujarat; Test standby 2021, no appearance"),
    "MM Sharma": ("Mohit Sharma", "1988-09-18", "ODI/T20I", True, None, "Dec 2025, S16"),
    "K Kartikeya": ("Kumar Kartikeya Singh", "1997-12-26", None, False, None, "Madhya Pradesh; IPL: MI 2022-24, RR 2025; not on a 2026 squad"),
}


def age(dob: str | None) -> int | None:
    if not dob:
        return None
    d = date.fromisoformat(dob)
    return AUCTION_DATE.year - d.year - ((AUCTION_DATE.month, AUCTION_DATE.day) < (d.month, d.day))


def status(name: str) -> tuple[bool, str, int | None, str | None]:
    """(eligible fresher?, reason if not, age at auction, full name)."""
    if name not in FACTS:
        return False, "not verified", None, None
    full, dob, intl, retired, ipl26, note = FACTS[name]
    a = age(dob)
    if dob is None:
        return False, f"unverifiable ({note})", a, full
    if retired:
        return False, f"retired ({note})", a, full
    if intl:
        return False, f"capped for India: {intl}", a, full
    if ipl26:
        return False, f"on IPL 2026 squad: {ipl26}", a, full
    if a > MAX_AGE:
        return False, f"age {a} at auction (over {MAX_AGE})", a, full
    return True, "", a, full

# common (scorecard-style) names used in deliverables; full names stay in the CSVs
DISPLAY = {"Rahul Buddhi": "Rahul Buddhi", "N Jagadeesan": "Narayan Jagadeesan", "Rajat Dey": "Rajat Dey", "Atharva Taide": "Atharva Taide",
           "Harsh Tyagi": "Harsh Tyagi", "Shubham Pundir": "Shubham Pundir", "Subhransu Senapati": "Subhranshu Senapati",
           "Shivam Chaudhary": "Shivam Chaudhary", "RK Bhui": "Ricky Bhui", "Upendra Yadav": "Upendra Yadav",
           "A Sheth": "Atit Sheth", "Harishankar Reddy": "Harishankar Reddy", "DG Nalkande": "Darshan Nalkande",
           "Abid Mushtaq": "Abid Mushtaq", "A Nagwaswalla": "Arzan Nagwaswalla", "K Kartikeya": "Kumar Kartikeya"}
