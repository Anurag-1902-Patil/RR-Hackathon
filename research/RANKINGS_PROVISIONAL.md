# Provisional Rankings — Pressure Reliability (2026-11-14)

> **Status: PROVISIONAL.** These lists come entirely from the RR data pack (IPL 2022–26 plus T20I and A-team T20s). Before submission, each player's identity, availability and retirement status still has to be verified externally (Phase 7). Squad fit is a separate layer and does **not** reorder these lists.
> Files: `reports/top_10_batsmen.csv`, `reports/top_10_bowlers.csv`, `reports/model_outputs/reliability_{batting,bowling}.csv`, `reports/figures/rank_uncertainty_top20.png`. Method: `research/METHODOLOGY.md` §4–6.

## Top 10 batters
| # | Player | Role (from data) | Score | HIGH balls | Pressure inns | SR HIGH / LOW | Value /100 HIGH | Rank range across definitions | Bootstrap 90% rank | P(top 10) |
|---|---|---|---:|---:|---:|---|---:|---|---|---:|
| 1 | Shreyas Iyer | Middle order | 96 | 439 | 23 | 159 / 156 | +33.7 | 1–4 | 1–21 | 0.74 |
| 2 | Heinrich Klaasen | Middle order | 95 | 310 | 17 | 171 / 168 | +39.0 | 1–4 | 1–12 | 0.91 |
| 3 | Rajat Patidar | Middle order | 93 | 208 | 13 | 163 / 181 | +42.3 | 3–16 | 1–36 | 0.52 |
| 4 | Tilak Varma | Middle order | 91 | 698 | 39 | 152 / 146 | +19.5 | 1–17 | 1–42 | 0.63 |
| 5 | Andre Russell | Finisher | 85 | 259 | 17 | 183 / 185 | +30.8 | 2–25 | 2–40 | 0.54 |
| 6 | Ishan Kishan | Opener | 85 | 370 | 19 | 152 / 146 | +24.5 | 3–21 | 2–63 | 0.47 |
| 7 | Naman Dhir | Finisher | 82 | 227 | 12 | 169 / 177 | +33.2 | 2–10 | 2–51 | 0.40 |
| 8 | Tim David | Finisher | 81 | 469 | 34 | 168 / 192 | +22.5 | 8–14 | 2–39 | 0.43 |
| 9 | David Miller | Middle order | 81 | 404 | 26 | 160 / 144 | +18.6 | 6–15 | 2–49 | 0.37 |
| 10 | Suryakumar Yadav | Middle order | 81 | 562 | 36 | 159 / 171 | +19.0 | 6–45 | 3–50 | 0.27 |

Next in line: Glenn Phillips (80), Abhishek Sharma (79), Cameron Green (78), Rinku Singh (77), Daryl Mitchell (76).

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
| 7 weight schemes (equal, prompt hypothesis, pressure-only, no-impact, predictive tilt, delta-heavy) | 7–10 (ρ ≥ 0.97) | 9–10 (ρ ≥ 0.97) |
| Pressure blend 30/70 · 70/30 | 9 · 6 | 6 · 7 |
| HIGH = top 15% · top 30% | 7 · 6 | 8 · 6 |

The **pressure definition** moves the lists more than the **weights** do, which matches the pressure review.

## Excluded by the recency rule (no data in 2025–26)
Dinesh Karthik, Matthew Wade, Mohammad Rizwan, Iftikhar Ahmed (batting); Naveen-ul-Haq, Riley Meredith (bowling). They are statistically eligible, but no data in 2025–26 means they may be unavailable for IPL 2027. This is a data-observable rule only, and real status must be verified.

## Open items before these lists are final
1. External verification of each player's identity, current availability, retirement status and auction eligibility (Phase 7). Examples: Andre Russell's and Sunil Narine's current IPL status; whether any listed player is already in RR's retained squad.
2. Whether the Unstop dropdown restricts the eligible player pool.
3. Whether to break near-ties at ranks 6–15 using the RR squad-fit layer. This is a decision for the user. The default is not to.
