# Provisional Rankings — Pressure Reliability (2026-11-14)

> **SUPERSEDED by [`RANKINGS_FINAL.md`](RANKINGS_FINAL.md).** Every player below is under IPL contract or otherwise not signable by RR. The submitted lists rank only RR-acquirable players. This file is kept as the unrestricted reference.

> **Status: PROVISIONAL.** These lists come entirely from the RR data pack (IPL 2022–26 plus T20I and A-team T20s). Before submission, each player's identity, availability and retirement status still has to be verified externally (Phase 7). Squad fit is a separate layer and does **not** reorder these lists.
> Files: `reports/top_10_batsmen.csv`, `reports/top_10_bowlers.csv`, `reports/model_outputs/reliability_{batting,bowling}.csv`, `reports/figures/rank_uncertainty_top20.png`. Method: `research/METHODOLOGY.md` §4–6.

## Top 10 batters
| # | Player | Role (from data) | Score | HIGH balls | Pressure inns | SR HIGH / LOW | Value /100 HIGH | Rank range across definitions | Bootstrap 90% rank | P(top 10) |
|---|---|---|---:|---:|---:|---|---:|---|---|---:|
| 1 | Shreyas Iyer | Middle order | 97 | 439 | 23 | 159 / 156 | +33.7 | 1–4 | 1–20 | 0.76 |
| 2 | Heinrich Klaasen | Middle order | 95 | 310 | 17 | 171 / 168 | +39.0 | 1–4 | 1–11 | 0.92 |
| 3 | Rajat Patidar | Middle order | 93 | 208 | 13 | 163 / 181 | +42.3 | 3–16 | 1–36 | 0.54 |
| 4 | Tilak Varma | Middle order | 91 | 698 | 39 | 152 / 146 | +19.5 | 1–15 | 1–41 | 0.63 |
| 5 | Ishan Kishan | Opener | 85 | 370 | 19 | 152 / 146 | +24.5 | 3–20 | 2–62 | 0.50 |
| 6 | Naman Dhir | Finisher | 83 | 227 | 12 | 169 / 177 | +33.2 | 2–10 | 2–50 | 0.44 |
| 7 | David Miller | Middle order | 82 | 404 | 26 | 160 / 144 | +18.6 | 5–15 | 2–48 | 0.37 |
| 8 | Tim David | Finisher | 82 | 469 | 34 | 168 / 192 | +22.5 | 7–13 | 3–38 | 0.45 |
| 9 | Suryakumar Yadav | Middle order | 81 | 562 | 36 | 159 / 171 | +19.0 | 6–44 | 3–49 | 0.28 |
| 10 | Glenn Phillips | Middle order | 81 | 298 | 14 | 134 / 175 | +28.5 | 7–22 | 3–41 | 0.34 |

Next in line: Abhishek Sharma (80), Cameron Green (79), Rinku Singh (78), Daryl Mitchell (77), Curtis Campher (76).

**Change log (2026-11-14):** Andre Russell (data rank #5) has been removed. He formally retired from the IPL on 30 Nov 2025 (S7), and the user decided to exclude verified IPL retirements. The full pipeline (percentiles, definition variants, bootstrap) was re-run without him. As a result, Miller (82.01) and David (81.82) swap places at #7/#8 (a statistical tie), and Glenn Phillips enters at #10.

## Top 10 bowlers
| # | Player | Role (from data) | Score | HIGH legal balls | Pressure spells | Econ HIGH / LOW | Wkts HIGH | Rank range across definitions | Bootstrap 90% rank | P(top 10) |
|---|---|---|---:|---:|---:|---|---:|---|---|---:|
| 1 | Varun Chakravarthy | Middle overs | 96 | 400 | 33 | 7.30 / 8.48 | 30 | 1–4 | 1–17 | 0.84 |
| 2 | Sunil Narine | Middle overs | 93 | 276 | 22 | 6.20 / 7.26 | 15 | 1–3 | 1–25 | 0.68 |
| 3 | Jasprit Bumrah | Multi-phase | 91 | 374 | 30 | 7.16 / 7.63 | 25 | 1–12 | 1–33 | 0.60 |
| 4 | Lockie Ferguson | Multi-phase | 90 | 229 | 20 | 7.81 / 9.94 | 18 | 3–9 | 1–26 | 0.67 |
| 5 | Rashid Khan | Middle overs | 90 | 573 | 48 | 7.45 / 7.72 | 35 | 2–10 | 1–41 | 0.58 |
| 6 | Axar Patel | Middle overs | 89 | 581 | 52 | 7.18 / 7.92 | 30 | 5–13 | 2–30 | 0.53 |
| 7 | Matheesha Pathirana | Death specialist | 89 | 278 | 23 | 8.55 / 8.24 | 24 | 3–15 | 1–23 | 0.68 |
| 8 | Bhuvneshwar Kumar | Powerplay specialist | 87 | 429 | 39 | 9.37 / 7.86 | 33 | 8–14 | 1–38 | 0.49 |
| 9 | Kuldeep Yadav | Middle overs | 87 | 501 | 41 | 7.71 / 8.80 | 29 | 2–16 | 3–35 | 0.47 |
| 10 | Sikandar Raza | Middle overs | 85 | 215 | 16 | 6.28 / 7.10 | 12 | 7–25 | 2–27 | 0.50 |

Next in line: Mohsin Khan (85), Krunal Pandya (85), Kagiso Rabada (83), Maheesh Theekshana (78), Taskin Ahmed (78).

## How to read these numbers
- **Raw HIGH-pressure economy or strike rate is not the ranking metric.** HIGH-pressure balls cluster in death overs and tight chases, where scoring is naturally faster. Bhuvneshwar's HIGH economy (9.37) is worse than his LOW (7.86), but it is **better than the context expected**: positive value after adjusting for situation and the batters he faced. The same logic explains finishers whose HIGH SR is below their LOW SR but who still add value.
- **Score** = rating relative to the 2022–26 eligible pool (a percentile composite), not a forecast.
- **Uncertainty is substantial.** Only Klaasen, Varun and (in most resamples) Shreyas Iyer, Narine, Ferguson and Pathirana are near-locks. Positions 6–15 on each side are statistically close: P(top 10) is 0.27–0.54 for ranks 6–10. The report must say this rather than imply a precise ordering.

## Robustness summary
| Check | Batting top-10 kept | Bowling top-10 kept |
|---|---|---|
| 7 weight schemes (equal, prompt hypothesis, pressure-only, no-impact, predictive tilt, delta-heavy) | 8–10 (ρ ≥ 0.97) | 9–10 (ρ ≥ 0.97) |
| Pressure blend 30/70 · 70/30 | 8 · 7 | 6 · 7 |
| HIGH = top 15% · top 30% | 7 · 5 | 8 · 6 |

The **pressure definition** moves the lists more than the **weights** do, which matches the pressure review.

## Excluded by the recency rule (no data in 2025–26)
Dinesh Karthik, Matthew Wade, Mohammad Rizwan, Iftikhar Ahmed (batting); Naveen-ul-Haq, Riley Meredith (bowling). They are statistically eligible, but no data in 2025–26 means they may be unavailable for IPL 2027. This is a data-observable rule only, and real status must be verified.

Also excluded: **Andre Russell**, a verified retirement from the IPL (S7). See the change log above.

## Open items before these lists are final
1. ✅ Identity and availability verification is done (`research/PLAYER_VERIFICATION.md`). Flags carried into the report: Pathirana's fitness (IPL 2026 hamstring), Kuldeep's trade to LSG, Raza's lack of an IPL contract, Ferguson's and Phillips' limited recent IPL usage, and Suryakumar's form. None of the 20 is an RR player. Availability depends on retentions due 17 Nov.
2. Whether the Unstop dropdown restricts the eligible player pool.
3. Whether to break near-ties at ranks 6–15 using the RR squad-fit layer. This is a decision for the user. The default is not to.
