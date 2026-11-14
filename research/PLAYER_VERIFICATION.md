# Player Verification: Provisional Top 10s (2026-11-14)

Register: `research/player_verification_register.csv` (code: `src/research/verified_players.py`). Sources: `RESEARCH_SOURCE_REGISTER.md` (W-*, S7–S10).

## Identity check
For all 20 players, the data-pack player ID matches the verified person on **country, IPL teams and batting hand / bowling type**. No name collisions affect the shortlist; the Rashid Khan in the list is ID 4722 (Afghanistan / GT), not the Nepal player.

Data and external sources agree on these points:
- Pathirana: 1 IPL match in 2026 (injury).
- Russell: last data point July 2025 (retired from internationals 17 Jul 2025).
- Patidar: no IPL 2023 data (Achilles injury).
- Raza: no IPL games after 2024 (no contract).

## Material findings

| Player | Finding | Evidence | Effect |
|---|---|---|---|
| **Andre Russell** (bat #5) | **Retired from the IPL on 30 Nov 2025.** Now KKR "power coach". Still plays other T20 leagues | S7 (Gleaner/CMC), Wikipedia verbatim, many outlets | **Cannot be recruited for IPL 2027.** The data-only recency rule missed this because he played in 2025 |
| **Matheesha Pathirana** (bowl #7) | Ruled out of IPL 2026 after 1 match (hamstring); calf injury at the Feb 2026 T20 World Cup; surgery reported in June 2026 | S8 (official IPL); surgery report not opened | Fitness risk flag. The 2027 fitness status is **unverified**. Performance rating unchanged |
| **Kuldeep Yadav** (bowl #9) | Traded DC → LSG on 23 Jun 2026 (₹13.5 cr) | S9 (official IPL), S10 (LSG) | Contracted to LSG for 2027 unless released |
| **Sikandar Raza** (bowl #10) | No IPL contract since 2024 (PBKS 2023–24) | Wikipedia + data | **Potential auction entrant** if registered. Registration not verifiable until the auction list (~3 Dec). Age 40 at auction |
| **Lockie Ferguson** (bowl #4) | Only 4 (2025) and 3 (2026) IPL appearances in the data | Data | Rating leans on T20Is. IPL usage risk flag |
| Suryakumar Yadav (bat #10) | Removed as India T20I captain and dropped from T20I squads in 2026; Wikipedia describes a poor IPL 2026 | Wikipedia | Form-decline flag. Already reflected in data through 2026 |
| Heinrich Klaasen, Sunil Narine | Retired from international cricket (2025, 2023). Still active in the IPL | Wikipedia | Plays IPL and leagues only. Narine is 38 at auction |

## Ages at auction (calculated from verified DOB to 16 Dec 2026)
- Batting: Iyer 32, Klaasen 35, Patidar 33, Tilak 24, Russell 38, Kishan 28, Dhir 26, David 30, Miller 37, Suryakumar 36.
- Bowling: Varun 35, Narine 38, Bumrah 33, Ferguson 35, Rashid 28, Axar 32, Pathirana 23, Bhuvneshwar 36, Kuldeep 32, Raza 40.

Age is reported for context only and is **not** used in the reliability score.

## Auction feasibility
- 18 of the 20 were under IPL contracts in 2026. Their availability depends on retentions due **17 Nov 2026**, plus any trades before the window closes. Most players at this level are usually retained, but that is **not** assumed for any individual.
- Russell is unavailable (retired from the IPL).
- Raza is the only shortlisted player currently without an IPL contract.
- **The competition asks for the most reliable players under pressure.** The top-10 lists therefore remain a data ranking, and auction feasibility is reported alongside it, not used to filter. **The exception is players who have formally retired from the IPL**: see the decision below.

## Decision needed (user)
How to handle **Andre Russell** (rank #5 on the data):
- **Option A (recommended): exclude players who have officially retired from the IPL** from the submitted lists. Russell drops out, ranks 6–10 move up, and **Glenn Phillips (#11, score 80)** enters at #10. The submission is framed around IPL 2027, where Russell cannot play. His pressure record is still discussed in the report.
- Option B: keep him as a pure data ranking, with a "retired from IPL" flag.
