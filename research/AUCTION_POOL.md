# Auction-Realistic Shortlists (IPL 2027), 2026-11-14

**Why this exists:** in the competition ranking, every top-10 batter and 9 of the 10 top bowlers were on another franchise's IPL 2026 squad. Raza is the exception, and Kuldeep has since been traded to LSG. In a mini-auction those players reach RR only if released at the **17 Nov 2026** retention deadline or traded, and nobody can know that today. This document ranks the players who are **not on any IPL 2026 squad**, using the data pack's squad lists for all 10 franchises. Those are the players who can realistically be in the IPL 2027 auction pool.

Same reliability score, eligibility and pressure definition as the main ranking. Code: `src/scouting/auction_pool.py`. Files: `reports/auction_pool_batsmen.csv`, `reports/auction_pool_bowlers.csv`.

## Batters available in the auction pool (top 10)
| Pool # | Overall # | Player | Country | Role | Score | P(top10) | IPL share of balls | Best RR fit (phase pctile) | Flag |
|---:|---:|---|---|---|---:|---:|---:|---|---|
| 1 | 14 | Daryl Mitchell | New Zealand | Middle order (4-5) | 77 | 35% | 23% | Middle-overs batting (66) |  |
| 2 | 15 | Curtis Campher | Ireland | Middle order (4-5) | 76 | 17% | 0% | Middle-overs batting (42) |  |
| 3 | 18 | Kusal Mendis | Sri Lanka | Opener | 72 | 10% | 1% | Middle-overs batting (37) |  |
| 4 | 27 | Mark Chapman | New Zealand | Middle order (4-5) | 63 | 13% | 0% | Middle-overs batting (92) |  |
| 5 | 28 | Sikandar Raza | Zimbabwe | Middle order (4-5) | 62 | 9% | 14% | Death-overs / finishing batting (97) |  |
| 6 | 33 | Jimmy Neesham | New Zealand | Finisher (6-7) | 58 | 4% | 6% | Middle-overs batting (71) |  |
| 7 | 35 | Jaker Ali Anik | Bangladesh | Finisher (6-7) | 56 | 5% | 0% | Death-overs / finishing batting (76) | Bangladesh availability risk (S12) |
| 8 | 43 | George Dockrell | Ireland | Finisher (6-7) | 45 | 3% | 0% | Middle-overs batting (53) |  |
| 9 | 45 | Ibrahim Zadran | Afghanistan | No.3 | 45 | 5% | 0% | Death-overs / finishing batting (58) |  |
| 10 | 49 | Harry Tector | Ireland | Middle order (4-5) | 41 | 0% | 0% | Death-overs / finishing batting (26) |  |

## Bowlers available in the auction pool (top 10)
| Pool # | Overall # | Player | Country | Role | Score | P(top10) | IPL share of balls | Best RR fit (phase pctile) | Flag |
|---:|---:|---|---|---|---:|---:|---:|---|---|
| 1 | 10 | Sikandar Raza | Zimbabwe | Middle-overs | 85 | 50% | 8% | Middle-overs bowling (72) |  |
| 2 | 14 | Maheesh Theekshana | Sri Lanka | Multi-phase | 78 | 26% | 39% | Death-overs bowling (85) |  |
| 3 | 15 | Taskin Ahmed | Bangladesh | Powerplay specialist | 77 | 18% | 0% | Death-overs bowling (70) | Bangladesh availability risk (S12) |
| 4 | 16 | Adam Zampa | Australia | Middle-overs | 77 | 30% | 16% | Death-overs bowling (74) |  |
| 5 | 23 | Joshua Little | Ireland | Multi-phase | 64 | 11% | 29% | Powerplay bowling (69) |  |
| 6 | 29 | Adil Rashid | England | Middle-overs | 59 | 9% | 3% | Middle-overs bowling (38) |  |
| 7 | 34 | Mahedi Hasan | Bangladesh | Powerplay specialist | 54 | 6% | 0% | Powerplay bowling (94) | Bangladesh availability risk (S12) |
| 8 | 39 | Roston Chase | West Indies | Middle-overs | 48 | 4% | 0% | Middle-overs bowling (65) |  |
| 9 | 49 | Obed McCoy | West Indies | Multi-phase | 40 | 0% | 26% | Powerplay bowling (65) |  |
| 10 | 52 | Richard Ngarava | Zimbabwe | Powerplay specialist | 37 | 0% | 0% | Death-overs bowling (52) |  |

## Excluded despite being uncontracted (verified)
| Player | Reason |
|---|---|
| Fakhar Zaman | No Pakistan player has featured in the IPL since 2009 (Wisden, 20 Feb 2026; S13) |
| Salman Agha | No Pakistan player has featured in the IPL since 2009 (Wisden, 20 Feb 2026; S13) |
| Harry Brook | Banned from IPL/IPL auction for two seasons after 2025 withdrawal; whether 2027 is covered is unclear (Tribune/ANI, 13 Mar 2025; S14) |
| Mohammad Nawaz | No Pakistan player has featured in the IPL since 2009 (Wisden, 20 Feb 2026; S13) |
| Shaheen Afridi | No Pakistan player has featured in the IPL since 2009 (Wisden, 20 Feb 2026; S13) |
| Ravichandran Ashwin | Retired from the IPL, 27 Aug 2025 (Gulf News/IANS; S15) |
| Mohit Sharma | Retired from all cricket, 3 Dec 2025 (Tribune/ANI; S16) |
| Haris Rauf | No Pakistan player has featured in the IPL since 2009 (Wisden, 20 Feb 2026; S13) |
| Shadab Khan | No Pakistan player has featured in the IPL since 2009 (Wisden, 20 Feb 2026; S13) |

## Release watchlist (contracted elsewhere; available to RR only if released on 17 Nov or traded)
- **Batting:** Shreyas Iyer (Punjab Kings), Heinrich Klaasen (Sunrisers Hyderabad), Rajat Patidar (Royal Challengers Bengaluru), Namboori Tilak Varma (Mumbai Indians), Ishan Kishan (Sunrisers Hyderabad), Naman Dhir (Mumbai Indians), David Miller (Delhi Capitals), Tim David (Royal Challengers Bengaluru), Suryakumar Yadav (Mumbai Indians), Glenn Phillips (Gujarat Titans), Abhishek Sharma (Sunrisers Hyderabad), Cameron Green (Kolkata Knight Riders), Rinku Singh (Kolkata Knight Riders)
- **Bowling:** Varun Chakravarthy (Kolkata Knight Riders), Sunil Narine (Kolkata Knight Riders), Jasprit Bumrah (Mumbai Indians), Lockie Ferguson (Punjab Kings), Rashid Khan (Gujarat Titans), Axar Patel (Delhi Capitals), Matheesha Pathirana (Kolkata Knight Riders), Bhuvneshwar Kumar (Royal Challengers Bengaluru), Kuldeep Yadav (Delhi Capitals), Mohsin Khan (Lucknow Super Giants), Krunal Pandya (Royal Challengers Bengaluru), Kagiso Rabada (Gujarat Titans)

## Read this before using the lists
1. **The available pool is much thinner than the competition top 10.** Pool batters ranked 8–10 have reliability scores of 41–45 and a P(top 10) of 0–3%. Several have **no IPL experience in the data** (0% IPL balls), so their record is mostly against international and associate opposition.
2. **Every pool player is overseas.** The data pack covers only IPL and T20I matches, so **uncapped Indian domestic players, who make up most mini-auction signings, cannot be assessed**. This is a data gap, not evidence about them. RR can hold at most 8 overseas players, so in practice only one to three of these could be signed.
3. **Registration is not yet known.** The final auction list is expected around 3 Dec 2026, and a player must register to be auctioned.
4. **Re-run after 17 Nov.** Released players join the pool. Running the pipeline with the updated squad lists will add them automatically.

## Strongest realistic targets for RR's needs (data-led)
- **Finishing / death-overs batting (RR's top need):** Sikandar Raza (97th phase percentile at the death). Next is Jaker Ali (76th), who carries the Bangladesh availability risk.
- **Middle-overs batting:** Daryl Mitchell (pool #1, 23% of balls in the IPL) and Mark Chapman (92nd phase percentile, but no IPL record).
- **Death bowling:** Maheesh Theekshana (85th phase percentile, 39% IPL balls) and Adam Zampa (74th). Taskin Ahmed (70th) carries the Bangladesh risk.
- **Middle-overs bowling:** Sikandar Raza (pool #1 bowler, overall #10). Raza covers bat and ball, which matters given the overseas-slot limit.
