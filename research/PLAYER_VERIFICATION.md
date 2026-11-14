# Player Verification: Final RR-Acquirable Top 10s (2026-11-14)

Register: `research/player_verification_register.csv` (code: `src/research/verified_players.py`, `FACTS_BY_NAME`). Sources: `RESEARCH_SOURCE_REGISTER.md` (W-* final-selection pages, S1, S7, S12–S16).

## Final selection (user decision, 2026-11-14)
The submitted lists contain **only players RR can sign** at the IPL 2027 auction: not on any IPL 2026 squad, not Pakistani or Bangladeshi, and not retired or banned
(`src/scouting/final_selection.py`, enforced by `tests/test_reliability.py::test_final_top10_only_rr_acquirable`). The provisional verification of the unrestricted top 10s is kept below for the record.

## Identity and availability check (final 20; 19 unique players, as Raza is on both lists)
- For each player, the Wikipedia page was read on 2026-11-14 (W-* codes in the register). Full name, DOB, country, batting hand and bowling type match the data pack.
- **No page lists an IPL team for 2026 or 2027, and none states a retirement from the IPL or from T20 cricket.**
- Player IDs are resolved from the data by name. An unknown name stops the build. This replaced 14 hand-typed IDs that were found to be wrong during this check.
- Maheesh Theekshana was released by RR before IPL 2026 (S1), so is not under contract.
- Sikandar Raza has had no IPL contract since 2024 (PBKS 2023–24).
- Every player must still **register** for the auction. The list is expected around 3 Dec 2026 and cannot be verified yet.

## Ages at auction (calculated from verified DOB to 16 Dec 2026; not scored)
- Batting: Daryl Mitchell 35, Curtis Campher 27, Kusal Mendis 31, Mark Chapman 32, Sikandar Raza 40, Jimmy Neesham 36, George Dockrell 34, Ibrahim Zadran 25, Harry Tector 27, Ryan Burl 32.
- Bowling: Sikandar Raza 40, Maheesh Theekshana 26, Adam Zampa 34, Joshua Little 27, Adil Rashid 38, Roston Chase 34, Obed McCoy 29, Richard Ngarava 28, Alzarri Joseph 30, Mark Adair 30.

## Risk flags (reported, never scored)
- **Limited IPL evidence:** Curtis Campher, Mark Chapman, George Dockrell, Ibrahim Zadran, Harry Tector, Ryan Burl (batting) and Roston Chase, Richard Ngarava, Mark Adair (bowling) have no IPL balls in the data. Their ratings rest on opponent-adjusted T20Is.
- **Recency:** Obed McCoy's last T20I in the data is September 2025.
- **Exclusion judgements:** Bangladeshi players (S12) and Harry Brook (S14) are excluded as unreliable to acquire. No formal rule was published for either case.

---

# Archive: Verification of the Provisional (Unrestricted) Top 10s (2026-11-14)

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

## Decision (user, 2026-11-14): verified IPL retirements are excluded
**Andre Russell has been removed** (`RETIRED_FROM_IPL` in `src/scouting/reliability.py`, with a regression test), and the full pipeline was re-run. **Glenn Phillips** enters the batting list at #10.

Phillips' verification:
- Glenn Dominic Phillips, born 6 Dec 1996 (age 30 at auction), New Zealand all-rounder, RHB, off-break.
- IPL: RR 2021, SRH, GT 2025–. Missed IPL 2025 through injury; retained by GT for 2026 (S11).
- No 2026 injury is reported.
- Data ID 4853 matches (New Zealand; GT/SRH).
- Flag: only 5 IPL games each in 2023 and 2026, so his rating leans on T20Is.

Russell's pressure record is still discussed in the report as context.
