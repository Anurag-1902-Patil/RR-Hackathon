# Rajasthan Royals: Squad Intelligence, Performance Audit & Recruitment Needs

**Information cut-off:** 14 November 2026. **Data:** RR data pack (IPL 2022–26 + T20I). External sources: `research/RESEARCH_SOURCE_REGISTER.md` (S1–S5).
**Files:** `research/rr_squad_database.csv`, `rr_player_performance_database.csv`, `rr_phase_performance.csv`, `rr_role_depth_chart.csv`, `rr_recruitment_priority_matrix.csv`, `reports/rr_team_performance_dashboard_data.csv`. **Code:** `src/scouting/rr_squad.py`.

> **Process followed:** the squad was understood first, then measured with the *same* pressure framework applied to every candidate, and only then were needs identified. No candidate players were considered while deriving these needs.

---

## 1. Squad status: what is verified and what is not

| Snapshot | Status | Basis |
|---|---|---|
| **RR 2026 squad (baseline)** | ✅ Verified: 27 players | Data-pack IPL 2026 RR mapping, matching official RR retention (S1), trade (S2) and auction-status (S3) pages |
| **RR 2027 pre-auction squad** | ⏳ **Pending** | No official retention list yet. BCCI deadline extended to **17 Nov 2026** (S5). Mini-auction **16 Dec 2026, Goa** (S5; ESPNcricinfo page blocked automated access, so this date is single-sourced) |

**Verified 2026 moves (official RR, 15 Nov 2025):**
- Retained: 13 players.
- Trades: Sanju Samson → CSK for **Ravindra Jadeja + Sam Curran**; Nitish Rana → DC for **Donovan Ferreira**.
- Released: Hasaranga, Theekshana, Farooqi, Kartikeya, Madhwal, Rathore, Ashok Sharma.
- Pre-auction position: ₹16.05 cr purse, one overseas slot (S3).

**2026 in-season changes** (Wikipedia, secondary, S4): Sam Curran ruled out for the season (replaced by Dasun Shanaka). Ravi Singh replaced by Emanjot Singh Chahal.

**2026 outcome:** the data shows 16 matches and 9 wins. The secondary source S4 gives 4th in the league, an Eliminator win and a Qualifier 2 loss; the data is consistent with that.

**Not used:** retention "predictions", former players' picks and trade rumours (e.g. reports linking Yashasvi Jaiswal with LSG). None of these are official.

### 1.1 IPL 2027 rules relevant to recruitment (S5; to re-verify with BCCI/IPL when published)
- Mini-auction with no cap on retentions and no Right-to-Match.
- Squad maximum 25, of which at most 8 overseas.
- Purse after retention deductions. **The IPL 2027 purse figure is not verified** (sources conflict), so no financial claims are made.

## 2. Squad usage in 2026 (data)
| Group | Players (RR IPL 2026 appearances) |
|---|---|
| Core every match | Jaiswal 16, Jurel 16 (kept wicket in all 16), Archer 16, Sooryavanshi 16 |
| Regulars | Ferreira 15, Jadeja 14, Parag 14 (captain), Burger 13, Brijesh Sharma 13 |
| Rotated | Bishnoi 9, Hetmyer 8, Yash Punja 8, Shanaka 7, Dubey 7, Deshpande 7, Sandeep Sharma 6 |
| Fringe / unused | Sushant Mishra 2, Pretorius 2, Milne 1, Ravi Singh 1; **0 apps:** Curran (injured), Kuldeep Sen, Yudhvir Singh, Maphaka, Chahal, Aman Rao, Vignesh Puthur |

Overseas players: 9 listed (8 plus Shanaka as injury replacement).

## 3. RR players under the same pressure framework (no preferential treatment)
Percentiles are against the full eligible candidate pool (82 batters, 78 bowlers; IPL + T20I, 2022–26). "Eligible" uses the same thresholds as every candidate.

**Batting**
| Player | Role (data) | Balls | HIGH balls | SR | SR HIGH | Usual pctile | Pressure pctile | Eligible / rank |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Yashasvi Jaiswal | Opener | 1872 | 120 | 156.4 | 206.7 | 62 | 94 | No (only 120 HIGH balls; too few pressure innings) |
| Shimron Hetmyer | Middle order | 1245 | 413 | 151.6 | 144.1 | 49 | 38 | Yes, #58 |
| Riyan Parag | Middle order | 1084 | 276 | 151.5 | 148.6 | 55 | 45 | Yes, #53 |
| Ravindra Jadeja | Finisher | 958 | 300 | 135.1 | 140.0 | 16 | 20 | Yes, #68 |
| Sam Curran | Finisher | 858 | 218 | 130.8 | 135.8 | 9 | 23 | Yes, #65 |
| Dhruv Jurel | Middle order | 798 | 316 | 151.3 | 135.4 | 13 | **6** | Yes, #66 |
| Dasun Shanaka | Finisher | 774 | 388 | 139.5 | 141.2 | 35 | 52 | Yes, #42 |
| Vaibhav Sooryavanshi | Opener | 676 | 111 | 223.2 | 203.6 | **100** | 68 | No (sample) |
| Donovan Ferreira | Finisher | 343 | 93 | 163.8 | 189.2 | 35 | 63 | No (sample) |

**Bowling**
| Player | Role (data) | Legal balls | HIGH | Econ | Econ HIGH | Usual pctile | Pressure pctile | Eligible / rank |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Ravi Bishnoi | Middle overs (leg-spin) | 2327 | 538 | 8.35 | 8.83 | 62 | **14** | Yes, #65 |
| Ravindra Jadeja | Middle overs (SLA) | 1396 | 214 | 7.90 | 7.15 | 76 | **73** | Yes, **#17** |
| Sam Curran | Multi-phase | 1350 | 234 | 9.64 | 10.46 | 9 | 18 | Yes, #66 |
| Jofra Archer | Powerplay | 1259 | 261 | 9.04 | 8.83 | 59 | 33 | Yes, #51 |
| Tushar Deshpande | Powerplay | 1037 | 206 | 9.96 | 9.76 | 32 | 59 | Yes, #30 |
| Sandeep Sharma | Multi-phase | 961 | 281 | 9.02 | 10.72 | 33 | **13** | Yes, #68 |
| Nandre Burger | Powerplay | 441 | 109 | 9.80 | 8.86 | 15 | 55 | No (sample) |
| Brijesh Sharma | Multi-phase | 273 | 59 | 9.89 | 8.44 | 38 | 74 | No (sample) |

**Reading.**
- No current RR batter is in the candidate top 25 for pressure reliability.
- Every eligible middle-order and finishing batter except Dasun Shanaka (#42, an injury replacement) sits in the **bottom half** (#53–#68 of 82).
- The two openers rate highly but have too few pressure balls to qualify. Openers structurally face fewer HIGH-pressure balls; this is noted as a framework limitation.
- In bowling, **Jadeja is the one RR player in the top 20**. Bishnoi and Sandeep Sharma, RR's most-used spinner and an experienced seamer, rate in the bottom fifth under pressure.

## 4. Team performance vs the IPL (rank of 10; 1 = best)
| Phase | Batting 2025 → 2026 | Bowling 2025 → 2026 |
|---|---|---|
| Powerplay | **Run rate #1 → #1** (10.88 → 11.67 vs league 9.60 → 10.08); boundary % #1 → #1 | Run rate #4 → #7; wickets/over **#10 → #3** |
| Middle (7–15) | Run rate #8 → #4; wickets/over **#9 → #9** | **Dot % #10 → #9**; run rate #9 → #8; wickets/over #10 → #2 |
| Death (16–20) | **Boundary % #9 → #10**; run rate #9 → #7 (10.22/10.34 vs 10.98/10.82) | **2025: #10 on run rate (12.40), dot %, value**; 2026 improved to run rate #5, value #7 |

**Pressure situations (team context value per 100 balls, IPL rank).**
- Batting under HIGH pressure: #2 in 2026 but **#9 in 2025**.
- Bowling under HIGH pressure: **#8 in 2026**, #4 in 2025, #9 in 2024. Defending under pressure has been mid-to-low in 3 of the last 3 seasons.

**Close matches** (≤ 10 runs / ≤ 3 wickets): **5 wins from 16 close matches** in 2023–2026 (2023: 2/5, 2024: 2/5, 2025: 1/5, 2026: 1/1). This is a small sample and indicative only.

## 5. Who RR actually used, by phase (2026)
- **Death batting:**
  - Ferreira (83 balls, SR 221.7, +29.4 value per 100) is the only above-par finisher.
  - Jadeja (74 balls, SR 140.5), Jurel (SR 150.0) and Dubey (SR 146.3) were all well below the league death average of 169.4.
  - Archer faced 32 death balls, a sign of lower-order exposure.
- **Death bowling:**
  - Archer (9.35), Burger (9.33) and Brijesh Sharma (10.58) were at or better than the league death average of 10.67.
  - Sandeep Sharma (13.70, −85.3 value per 100) and Deshpande (12.38) were well above it.
- **Middle-overs bowling:** Jadeja (8.39, 10 wickets) carried it. Bishnoi went at 10.11 against a league 9.22, and Punja at 9.54.
- **Middle-overs batting:**
  - Sooryavanshi (SR 240) and Parag (SR 166) were above par.
  - Jaiswal (SR 135.9, −49.7) and Hetmyer (SR 117.5, −54.9) were below.

## 6. Recruitment priority matrix (`rr_recruitment_priority_matrix.csv`)
`priority = 100 × (0.6 × severity + 0.4 × coverage gap)`:
- **severity** = (mean RR rank on 4 phase metrics over 2025–26, minus 1) ÷ 9.
- **coverage gap** = 1 − (best pressure percentile among *eligible* RR players actually used in that phase in 2026) ÷ 100.

| Requirement | Mean rank (2025–26) | Best eligible RR cover (pressure pctile) | Priority |
|---|---:|---|---|
| **Death-overs / finishing batting** | 8.4 | Jadeja (20) | **High: 81** |
| **Death-overs bowling** | 7.6 | Deshpande (59) | **High: 61** |
| **Middle-overs batting** | 7.1 | Shanaka (52; injury replacement, 2027 status unknown) | **High: 60** |
| Middle-overs bowling | 7.8 | Jadeja (73) | Medium: 56 |
| Powerplay bowling | 5.9 | Deshpande (59) | Medium: 49 |
| Powerplay / opening batting | 2.1 | Parag (45); openers ineligible by sample | Low: 30 |

**Not scored but assessed:**
- **Wicketkeeping:** Jurel kept in all 16 matches. Ferreira and Pretorius are listed as keepers (S3), so a backup exists, but his batting under pressure rates in the 6th percentile.
- **Overseas balance:** 3 of the 9 overseas players (Curran, Maphaka, Pretorius) made 0–2 appearances in 2026. If they are released, slots open up, but **that depends on the 17 Nov retentions**.

## 7. Evidence-led recruitment requirements
1. **A middle-order / finishing batter who is reliable under pressure.** This is the clearest, most persistent gap. RR's death batting ranked 7th–10th on run rate, boundary %, context value and wickets lost in both seasons (dot-ball % was mid-table), and every eligible RR middle-order batter (Parag, Hetmyer, Jurel) rates below the pool median under pressure. Ideally the player bats 4–7, and Indian or overseas depending on slots.
2. **A death-overs bowler who is reliable under pressure.** In 2025 RR ranked last of 10 on death-overs run rate conceded, dot %, boundary % and context value (9th on wickets), and improved to mid-table in 2026. Two of the five 2026 death options conceded more than 12 an over. Team bowling value under HIGH pressure ranked #8 in 2026.
3. **Middle-overs control.** Dot % ranked 10th and 9th. Jadeja is strong, but RR's second spin option rated poorly under pressure. This could be met by a spinner or by a batter who bowls, and is lower priority than 1–2.
4. **Not a need:** opening and powerplay batting, where RR were the league's best in both seasons.

## 8. Caveats
- The 2027 squad is unknown until the official retention list is published (deadline 17 Nov 2026). These needs **must be re-run** once it is. If key players are released (e.g. a finisher or a death bowler), priorities change. The pipeline makes this a single command.
- Team phase ranks are single-season, 10-team comparisons, so one bad season moves them a lot. This is why both 2025 and 2026 are averaged.
- Pressure percentiles use all competitions in the data (IPL + T20I), with opponent adjustment.
- Openers are structurally under-sampled in HIGH pressure, which is why Jaiswal and Sooryavanshi are ineligible. This is a property of the definition, not evidence of weakness.
- Fielding cannot be assessed because the data has no fielder attribution.
