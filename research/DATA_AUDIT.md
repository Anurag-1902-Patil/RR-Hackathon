# DATA AUDIT — SupeRR Intelligence (Phase 1)

**Audit date:** 2026-11-14
**Auditor scripts (reproducible, read-only):** `src/data/profile_raw.py`, `src/data/audit_checks.py`, `src/data/audit_checks2.py`, `src/data/audit_checks3.py`
**Environment:** Python 3.11.9 venv (`.venv`), pandas 2.2.3, numpy 2.1.3

> Every number in this document is **OBSERVED** (read directly from the files) or **CALCULATED** (a reproducible aggregation done by the scripts above). Nothing in it has been estimated.

---

## 1. File inventory and provenance

The original archive `data_set.zip` (SHA-256 `82da62e94840e614ef136f0bb24168fe72b567c3eff71bf6b58488ac9b2b7f7d`) sits untouched in the project root. A copy was extracted to `data/raw/rr_data_pack/`. The macOS artefacts (`__MACOSX/`, `.DS_Store`) were dropped from that copy and **no data file was changed**.

| File | Rows (excl. header) | Cols | Size | Grain |
|---|---:|---:|---:|---|
| `ball_by_ball.csv` | 200,999 | 33 | 41.1 MB | One delivery (including wides/no-balls) |
| `matches.csv` | 883 | 22 | 124 KB | One match |
| `competitions.csv` | 141 | 4 | 7.6 KB | One competition/series |
| `teams.csv` | 353 | 3 | 6.9 KB | Competition × team |
| `playing_eleven.csv` | 28,381 | 9 | 966 KB | Match × team × squad member |
| `competition_team_player_mapping.csv` | 6,413 | 6 | 463 KB | Competition × team × player |
| `Round 1 Problem Statement _ SupeRR Selector Season 2.docx.pdf` | — | — | 254 KB | Official brief (2 pages) |

### 1.1 Official brief: key requirements (from the PDF)
- Measure how batters and bowlers perform **in high-pressure situations compared with their usual performance levels**, then rank the players who deliver **most consistently** under pressure.
- **The definition of pressure is ours to choose and justify.** It must separate pressure situations from ordinary ones and work for both batting and bowling.
- Data: "historical IPL and T20 International (T20I) data from 2022 onwards".
- Submission: two ordered top-10 lists (batters, bowlers), with no repeats inside a list, chosen through dropdowns on Unstop, plus a methodology report.
- The report must cover the pressure definition, performance measurement (including **player baselines**), fair comparisons (sample size, eligibility, match context, **how IPL and T20I data are combined**), evidence for the top 10, and reliability/limitations. It must be **reproducible**.
- "Rankings must be supported by analysis of the supplied data, not reputation alone."
- The optional journey video is suggested at **about 30–60 seconds**. It is optional and not evaluated.

> ⚠️ **Scope note:** the official brief asks for something narrower than the master instruction (no squad-fit or auction strategy). It asks for performance **relative to the player's own baseline**. Our framework will put that requirement first. The RR squad-fit work stays a separate second layer, as the master instruction says.

---

## 2. Schemas and data dictionary

### 2.1 `ball_by_ball.csv`

| Column | Type | Nulls | Distinct | Meaning / observed values |
|---|---|---:|---:|---|
| match_id | int | 0 | 867 | FK → matches.match_id |
| innings | int | 0 | 4 | 1, 2 = regulation innings; 3, 4 = super over (6 matches) |
| overid | int | 0 | 20 | Over number, **1-indexed** (1–20) |
| over_ball_num | int | 0 | 13 | Delivery sequence within the over, **counting illegal deliveries** (up to 13) |
| innings_ball_num | int | 0 | 136 | Delivery sequence within the innings (includes extras) |
| batting_team_id / bowling_team_id | int | 0 | 38 | FK → team_id |
| striker_id, striker_name | int / str | 0 | 888 / 885 | Batter on strike |
| non_striker_id, non_striker_name | int / str | 0 | 867 / 864 | Non-striker |
| bowler_id, bowler_name | int / str | 0 | 647 / 646 | Bowler |
| batting_type | str | 0 | 2 | Striker hand: RHB / LHB |
| bowling_type | str | 0 | 12 | e.g. Right-arm Fast, Slow left-arm orthodox, Left-arm Chinaman |
| batting_order | int | 0 | 13 | Striker's batting position in this match |
| runs | int | 0 | 7 | **Runs off the bat only** (0 on every wide) |
| is_four / is_six | bool | 0 | 2 | Boundary flags (all-run 4s and 6s are *not* flagged: 20 + 3 rows) |
| is_wicket | bool | 0 | 2 | 10,881 True |
| dismissal_type_id, dismissal_type | float / str | 190,118 | 8 / 9 | Caught 7,557; Bowled 1,775; LBW 709; RunOut 600; Stump 214; Hit Wicket 17; Retire Out 6; Obstructing (two spellings) 3 |
| dismissed_player_id | float | 190,107 | 814 | Player out (can be the non-striker) |
| extras_type | str | 189,167 | 6 | wide 7,714; legbyes 2,748; **Overstep** 576; byes 529; **other** 264; Penalty 1 |
| extras1_runs | int | 0 | 6 | Primary extras runs (wide/no-ball penalty, byes, leg-byes) |
| extras_2_runs | int | 0 | 3 | Secondary extras (byes/leg-byes taken off no-balls) |
| pace_or_spin | str | 0 | 2 | Pace / Spin |
| bowl_speed | float | 0 | 1,033 | km/h; **0 = not recorded (38.7% of rows)** |
| stroke | str | 6,158 | 30 | Shot played (tracking annotation) |
| delivery_style | str | 391 | 34 | e.g. Yorker, Inswing, Full Toss |
| over_or_around | str | 407 | 2 | Over / Around the wicket |
| on_or_off | str | 0 | 2 | Shot direction side |
| delivery_ist_time | str | 0 | 200,826 | Timestamp (labelled "UTC" despite the column name saying IST); 42 rows have a placeholder 00:00:00 |

**Extras semantics (verified):**
- **Total runs on a delivery** = `runs + extras1_runs + extras_2_runs`. This reconciles to the official result margin in 806 of 816 checkable matches (§5.2).
- **Illegal deliveries** = `wide`, `Overstep` (front-foot no-ball) and **`other`**. `other` is a non-overstep no-ball: once it is counted as illegal, 31,757 of 32,358 completed overs have exactly 6 legal balls, only **one** over in the whole dataset has 7, and no innings exceeds 120 legal balls. If `other` were treated as legal, 244 overs would have 7 or more legal balls.
- **Ball faced by the batter** = every delivery except wides.
- **Runs conceded by the bowler** = `runs` + wide/no-ball extras. Byes and leg-byes are excluded. Bowler wickets exclude run-outs, retirements and obstructing the field.

### 2.2 `matches.csv`

| Column | Nulls | Notes |
|---|---:|---|
| match_id (PK, unique) | 0 | 883 matches |
| comp_id | 0 | FK → competitions (all resolve) |
| match_number, match_date | 0 | 2022-01-22 → 2026-11-01 |
| stage | 0 | League 620, Others 226, Final 12, Qualifier 10, Super 4 6, Eliminator 5, Semi Final 4 |
| venue_id, venue_country | 0 | 98 venues, 17 countries. **No venue name** |
| home/away team id and name | 0 | |
| home/away captain id | 44 / 45 | |
| toss_win_team_id, toss_opted | 15 | |
| man_of_the_match | 0 | **0 means missing (119 matches)** |
| first/second_inn_revised_overs | 858 | Populated only for rain-shortened games. **Units look like balls** (e.g. 114, 84, 66), not overs |
| revised_target | 860 | D/L targets |
| knock_out | 0 | 0/1 |
| win_team_id | 41 | Null for No Result 21, Abandoned 19, Tied 1 |
| result | 0 | Free text, e.g. "X Won by 7 wickets", "(D/L method)" |

### 2.3 `competitions.csv`
`comp_id` (PK), `comp_name`, `match_format` ∈ {T20I, T20}, `season` ∈ {2022, 2022/23, 2023, 2023/24, 2024, 2024/25, 2025, 2026}.

### 2.4 `teams.csv`
`comp_id`, `team_id`, `team_name`. The (comp_id, team_id) pair is unique. There are 38 distinct teams: 10 IPL franchises, 23 full-member or associate national sides, and 5 "A" sides (Afghanistan A, Bangladesh A, India A, Pakistan A, Sri Lanka A).

### 2.5 `playing_eleven.csv`

| Column | Notes |
|---|---|
| match_id, team_id, player_id | FKs |
| batting_order | Null whenever `is_played = False` (8,667 rows) and on 11 played rows |
| is_played | True = took part in the match. Rows with False are non-playing squad members (up to 27 rows per match-team) |
| is_captain, is_wk | Null on non-playing rows |
| is_impact / is_impact_off | Impact-player substitutions: 558 of each. Zero in IPL 2022; 136–142 per IPL season in 2023–2026 |

### 2.6 `competition_team_player_mapping.csv`
`comp_id, comp_name, team_id, team_name, player_id, player_name`. The (comp, team, player) triple is unique. It covers 1,217 player IDs and 1,210 distinct names.

### 2.7 Relationships (validated)
```
competitions (comp_id) 1─* matches (comp_id)          ✔ all 883 matches resolve
competitions (comp_id) 1─* teams (comp_id, team_id)    ✔ unique
matches (match_id)     1─* ball_by_ball (match_id)     ✔ 0 orphan deliveries
matches (match_id)     1─* playing_eleven (match_id)   ✔ 0 orphans; 3 matches lack XI rows
comp+team              1─* comp_team_player_mapping    ✔ every ball-by-ball player ID present
```
Joins will run through **`player_id`, never names** (see §5.4). The `validate=` assertions (`m:1` and so on) go into the production pipeline.

---

## 3. Coverage

### 3.1 Matches by format and year (CALCULATED)

| | 2022 | 2023 | 2024 | 2025 | 2026 | Total |
|---|---:|---:|---:|---:|---:|---:|
| T20 (IPL + Emerging/A-team) | 74 | 74 | 89 | 90 | 74 | 401 |
| T20I | 106 | 66 | 111 | 127 | 72 | 482 |

- **IPL:** 2022 (74), 2023 (74), 2024 (74), 2025 (75), 2026 (74), giving **371 matches, 367 with ball-by-ball data**. All 10 franchises are present.
- **Non-IPL "T20":** Men's T20 Emerging Teams Asia Cup 2024 (15) and Asia Cup Rising Stars 2025 (15). Both are **A-team / emerging competitions**, a lower standard than IPL or full T20I.
- **T20I:** 133 bilateral and multi-nation series across 23 nations, associates included (Japan, Kuwait, Singapore, Hong Kong and others).
- **Not covered:** ICC T20 World Cups do not appear by name in `competitions.csv` (only bilateral, tri-series and Asia-Cup-style events). There are also no domestic leagues (BBL, SA20, CPL, SMAT and so on). The dataset therefore does **not** hold a player's full T20 record.

### 3.2 Delivery volume by segment
| Segment | Deliveries |
|---|---:|
| IPL | 87,687 |
| T20I | 106,327 |
| Emerging/A-team T20 | 6,985 |

### 3.3 Player coverage
- 888 distinct strikers and 647 distinct bowlers.
- IPL batters: 341. T20I batters: 665. Both: 182. IPL bowlers: 260. T20I bowlers: 479.
- Batters with at least 200 balls faced: **214** (122 with at least 500). Bowlers with at least 300 legal balls: **183** (101 with at least 600). These are working thresholds to tune in Phase 2.

### 3.4 Rajasthan Royals in the data (team_id = 3)
| Season | Matches | Wins |
|---|---:|---:|
| IPL 2022 | 17 | 10 |
| IPL 2023 | 14 | 7 |
| IPL 2024 | 16 | 9 |
| IPL 2025 | 14 | 4 |
| IPL 2026 | 16 | 9 |

The IPL 2026 RR mapping lists 27 players, including Ravindra Jadeja, Sam Curran, Yashasvi Jaiswal, Riyan Parag, Dhruv Jurel, Shimron Hetmyer, Jofra Archer, Ravi Bishnoi, Sandeep Sharma, Vaibhav Sooryavanshi and others. **Sanju Samson is not in the 2026 RR mapping.** This is the in-data 2026 baseline. It has **not yet been checked against official RR/IPL sources**, and IPL 2027 retentions are not in the data pack (that happens in Phase 8).

---

## 4. Missing values: what matters
| Field | Missing | Impact |
|---|---|---|
| `bowl_speed` | 38.7% recorded as 0 | Not usable as a ranking feature; descriptive use only |
| `stroke`, `delivery_style`, `over_or_around` | 3.1% / 0.2% / 0.2% | Fine for descriptive scouting, not core metrics |
| `man_of_the_match` | 119 matches coded 0 | Will not be used as ground truth |
| `win_team_id` | 41 (NR / abandoned / tie) | These matches are excluded from win-probability training |
| `revised_target` / revised overs | Populated in only ~25 matches | D/L chases need special handling for required-rate features |
| `toss_*` | 15 | Minor |

---

## 5. Data quality issues found

### 5.1 Completeness
- **16 matches have no ball-by-ball data. All 16 are "Match Abandoned"**, so every playable match is present.
- **22 matches have only one innings** (No Result or Abandoned after play started). They are kept for batting/bowling volume but **excluded from chase or defence pressure states**.
- **Truncation check:** the file holds exactly 200,999 rows (201,000 lines), a suspicious round number. The final match (55561, AFG v ZIM, 2026-11-01) was inspected and is **complete**: ZIM 79 all out (15 overs), AFG 81/3 (9 overs), which agrees with "Afghanistan Won by 7 wickets". **Conclusion: not truncated.**

### 5.2 Score reconciliation against official results (CALCULATED)
For every match with two innings and a "Won by N runs/wickets" result, the scores computed from ball-by-ball data were compared with the stated margin:
- **806 reconcile exactly, 10 mismatch, 51 not checkable** (NR, tie or super over).
- Of the 10 mismatches, **8 are D/L / DLS results** and expected: the margin is measured against the revised target. One is a DLS game with `revised_target` missing (24822).
- **Match 20190 (IPL 2023, LSG v SRH):** ball-by-ball shows LSG losing 5 wickets in the chase, but `result` says "Won by 6 wickets". The ball data is internally consistent (5 dismissal rows), so the discrepancy is most likely in the result text. It is flagged for external verification, and **ball-by-ball is treated as authoritative**.

### 5.3 Extras and legal-ball semantics
- `other` behaves exactly like a no-ball (see §2.1). Excluding it from legal balls is required, because otherwise 244 overs look like 7-ball overs.
- One over still has 7 legal balls after correction (a scorer anomaly). It is left as is and documented.
- 12 rows have `dismissed_player_id` set but `is_wicket = False`, consistent with **retired hurt** (not a dismissal). One `is_wicket` row lacks a `dismissed_player_id`.
- "Retire Out" (6 rows: e.g. Ashwin 2022, Dhoni 2025 and others) is a **tactical retirement**. It counts as a team wicket but **not** as a bowler wicket, and should not count as a batting failure in the same way as a dismissal.
- Spelling inconsistency: "Obstracting the field" (2) and "Obstructing the field" (1) will be normalised.
- `is_four`/`is_six` are not set on 20 all-run fours and 3 all-run sixes. Boundary metrics will use the flags, which is correct because all-run 4s are not boundaries.

### 5.4 Player identity
- **No `player_id` maps to more than one name.** IDs are stable.
- **Names shared by different IDs** (genuinely different people, so joins **must** use IDs):
  - *Rashid Khan*: 4722 (Afghanistan / Gujarat Titans) vs 20172 (Nepal)
  - *Abdul Samad*: 6922 (Pakistan / Pakistan A) vs 7446 (SRH / LSG)
  - *Haider Ali*: 7338 (Pakistan) vs 28756 (UAE)
  - *Bashir Ahmad*: 29833 (Afghanistan) vs 39479 (Afghanistan A)
  - *Basil Hameed* (8638, 39444, both UAE), *Muhammad Farooq* (27373, 28978, both UAE) and *Mohammad Ali* (3083, 20229, both Pakistan) could be **ID splits of one person or two different people**. These need external checking if any of them reaches a shortlist.
- Every display label in the outputs will carry `player_id`.

### 5.5 `playing_eleven.csv`
- 40 duplicate (match, player) rows across **3 matches**, e.g. match 13613 lists the same players twice with different `batting_order`. Fix: deduplicate on (match, team, player), preferring the order observed in ball-by-ball.
- `batting_order` in ball-by-ball agrees with `playing_eleven` for 13,701 of 13,729 (match, striker) pairs. The remaining 28 differ, and ball-by-ball is preferred because it is what actually happened.
- 2 ball-by-ball players are missing from `playing_eleven` (likely substitutes or concussion replacements).
- 3 matches have no XI rows.

### 5.6 Other
- `first/second_inn_revised_overs` hold ball counts despite the name (114 = 19 overs).
- No venue names, only `venue_id` plus country. Venue effects can be modelled by ID, but named venues need an external lookup.
- Six super-over matches (innings 3–4: 34429, 40725, 45512, 48027, 48029, 50359). Super overs will be analysed **separately** and not mixed into regulation-innings rates.

---

## 6. What is genuinely calculable

| Capability | Status | Basis |
|---|---|---|
| Full match state before every ball (score, wickets, legal balls left, target, CRR, RRR) | ✅ | Ball sequence + legal-ball logic + innings-1 totals |
| Phase splits (PP 1–6, middle 7–15, death 16–20) | ✅ | `overid` |
| Batting: runs, balls, SR, average, dot %, boundary %, dismissal rate, by phase/position/innings | ✅ | |
| Bowling: legal balls, runs conceded, wickets (bowler-credited), economy, SR, dot %, boundary % conceded | ✅ | |
| Win-probability model (2nd innings especially; 1st innings via projected par) | ✅ | 816 decided matches with results |
| Win Probability Added per ball → per batter/bowler | ✅ | Derived from the WP model |
| Expected runs / expected wicket per ball (context model) | ✅ | Over, wickets, phase, format, bowler type, batter hand |
| Pace vs spin, LHB/RHB, bowling-type matchups | ✅ | `pace_or_spin`, `bowling_type`, `batting_type` |
| Opposition strength adjustment | ✅ (approx.) | Team-season ratings from the data |
| Venue effects | ⚠️ ID-level only | No names |
| Bowl speed analysis | ⚠️ 61% coverage | Descriptive only |
| Fielding (catches, run-outs, stumpings) | ⚠️ Partial | Fielder ID **is not in the data**, so catches cannot be credited to fielders |
| Player age, nationality, role labels | ❌ Not in data | Needs external research (Phase 7) |
| Auction prices, IPL 2027 retentions, injuries | ❌ Not in data | External, and only where officially published |
| Full T20 career (domestic leagues, World Cups) | ❌ Not in data | Dataset is IPL + bilateral T20I + A-team only |

---

## 7. Limitations to carry into the methodology
1. **Mixed competition strength.** IPL, full-member T20Is, associate T20Is (e.g. Japan, Kuwait) and A-team events are very different standards. Unadjusted pooling would reward players who pile up runs against weak associates. **An opposition- and competition-strength adjustment is mandatory.**
2. **Window: 2022 to Nov 2026 only.** Careers that started before 2022 are only partly visible.
3. **No fielder attribution**, so no fielding metrics.
4. **Impact-player era (2023+)** changes batting depth and pressure dynamics in the IPL. It will be a model feature or stratification variable.
5. **D/L games** (~25) change targets mid-match, so required-rate pressure features must use `revised_target` where it exists.
6. **Pressure is unobserved.** Any pressure definition is a modelling choice, which is why sensitivity analysis across definitions (master §6) is essential.
7. The in-data RR 2026 squad is a **mapping, not an official contract list**, and must be verified externally.

---

## 8. Recommended analytical opportunities (input to Phase 2)
1. **Pressure through the win-probability lens.** Use *leverage* (how much a ball can swing win probability, as in baseball's Leverage Index) as the main data-driven pressure measure. Compare it with a transparent rule-based index (RRR gap, wickets in hand, balls left, phase). This directly answers "how close the contest is" from the brief.
2. **Performance vs own baseline.** For each player: pressure performance minus non-pressure performance, *and* pressure performance vs context-expected (runs above expected), shrunk with Bayesian priors by sample size. This matches the brief's "compared with their usual performance levels".
3. **Opposition- and competition-adjusted expected-runs model.** Fit it on match-grouped chronological splits (train 2022–24, validate 2025, test 2026).
4. **Consistency.** Spread of match-level pressure contributions (share of pressure innings or spells that exceed expectation), plus bootstrap rank stability.
5. **Role-specific benchmarks.** Batting position bands and bowling phase usage taken from observed data, not reputation.
6. **RR layer.** Phase-wise RR team metrics vs league benchmarks for 2022–2026 are fully calculable from the data and will drive the gap analysis.

---

## 9. Decisions log
| Date | Decision | Decided by |
|---|---|---|
| 2026-11-14 | **Eligibility: IPL + T20I players are both eligible for the top 10, with adjustment.** T20I-only players may appear. All performance is adjusted for competition and opposition strength so that runs or wickets against weaker sides (associates, A-teams) are not treated as equal to IPL or full-member T20I output. | User |
| 2026-11-14 | Ranking layer = pressure reliability only. RR squad-fit is a separate supplementary layer and does not reorder the competition top 10. | Proposed (default), open to user override |

Open item: the Unstop dropdown player list has not been seen. Final picks will be checked against it before submission.
