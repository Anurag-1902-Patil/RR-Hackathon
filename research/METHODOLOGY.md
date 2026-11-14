# METHODOLOGY — SupeRR Intelligence

*Living document. Sections marked ✅ are built, tested and committed. Sections marked 🔜 are the agreed design for upcoming phases and will be updated with real results as each one lands.*

**Central question (official brief):** how do batters and bowlers perform in high-pressure situations **compared with their usual performance levels**, and who delivers **most consistently** when it matters?

**Eligibility (user decision, 2026-11-14):** IPL and T20I players are both eligible. All performance is adjusted for competition and opposition strength.

---

## 1. Data foundation ✅
- Source: the official RR data pack only (see `research/DATA_AUDIT.md`), covering IPL 2022–2026 and T20Is plus A-team T20s from January 2022 to November 2026, a total of 200,961 regulation deliveries.
- `src/data/build_deliveries.py` builds a delivery table where every state variable is measured **before** the ball:
  - score, wickets in hand, legal balls left (respecting D/L-reduced innings), target (D/L revised target where present), runs needed, CRR, RRR, phase.
- Delivery semantics:
  - Legal ball excludes wides and both no-ball codes (`Overstep`, `other`).
  - Balls faced exclude wides only.
  - Bowler runs = bat runs + wide/no-ball extras (byes and leg-byes not charged).
  - Bowler wickets exclude run-outs, retirements and obstruction.
  - "Retire Out" is not counted as a batter dismissal.
- **Competition tiers:** `IPL`, `T20I_full` (both sides ICC full members), `T20I_assoc` (at least one associate), `A_team`.
- **Era par score:** the mean full-length first-innings total over the previous 60 matches of the same tier, using strictly earlier matches only. Observed par rises from 171 (IPL 2022) to 191 (IPL 2026), while T20I full-member par stays flat at about 167–172. Without this, any model trained on 2022 scoring misreads 2026.
- **Tests:** 11 data-integrity tests. Among them: non-D/L result margins reconcile with official results, no innings exceeds 120 legal balls, and the first ball of every innings starts from a zero state.

## 2. Win probability (WP) ✅
**Purpose:** WP is not a ranking metric in itself. It powers **WPA** (match impact) and the **Leverage Index** (stakes component of pressure).

| Item | Choice | Why |
|---|---|---|
| Structure | Separate model per innings, from the batting side's perspective | Setting and chasing are different problems |
| Features | Balls-left fraction, wickets in hand and their interaction, tier; innings 1: score vs par, projected total vs par; innings 2: RRR vs par rate (signed square too), share of target remaining, runs per wicket in hand, target vs par | All known before the ball. Par makes eras comparable |
| Candidates | Constant base rate, logistic regression, LightGBM (with monotonic constraints) | Simple baseline vs. advanced model |
| Validation | Chronological, with matches kept whole: train 2022–24, **validate 2025**, **test 2026** | No leakage across time or within matches |
| Excluded from training | No-result, abandoned and super-over matches | Their outcome labels are undefined or noisy |
| Selection rule | Lowest mean **validation** Brier score | Decided before looking at the test year |

**Results (held-out 2026 test year)** (`reports/model_outputs/wp_evaluation.csv`):

| Innings | Model | Brier | Log loss | AUC | ECE |
|---|---|---:|---:|---:|---:|
| 1 | Constant base rate | 0.253 | 0.698 | 0.500 | 0.072 |
| 1 | **Logistic (selected)** | **0.233** | **0.664** | **0.694** | 0.112 |
| 1 | LightGBM | 0.243 | 0.701 | 0.677 | 0.122 |
| 2 | Constant base rate | 0.254 | 0.702 | 0.500 | 0.074 |
| 2 | **Logistic (selected)** | **0.116** | **0.361** | **0.927** | 0.066 |
| 2 | LightGBM | 0.139 | 0.429 | 0.911 | 0.085 |

**Interpretation and honest caveats**
- **Logistic regression won on validation and also on test.** LightGBM was rejected: trees cannot extrapolate to scoring levels never seen in training. Before the par feature was added, the LightGBM chase Brier on test was 0.195.
- First-innings WP is inherently uncertain (AUC 0.69), because half the match has not happened yet. That is a property of the problem, not only of the model.
- The 2026 test year is less well calibrated than 2025 (ECE 0.11 in innings 1). Part of this is a shift in the batting-first win rate, since even the constant baseline has an ECE of 0.072 in 2026. These WP values are used to measure *stakes*, not to predict outcomes, but this caveat is reported.
- **Production values:** leave-one-year-out cross-fitting. Each year's WP comes from a model that never saw that year.

### 2.1 Win Probability Added (WPA) ✅
- WPA per delivery = WP_after − WP_before, from the batting side's perspective. The striker gets +WPA and the bowler gets −WPA.
- The last ball of a chase resolves to the actual result (1 / 0 / 0.5 for a tie that went to a super over).
- **Innings-break seam:** the last ball of innings 1 is scored with the innings-1 model at its terminal state. The step from that model's view to the chase model's view at the start of innings 2 is credited to **no player**. Without this fix, the last first-innings ball had an average |ΔWP| of 0.066, about 4.5× a normal ball. With it, the figure is 0.0185 vs 0.0146 for other balls.

### 2.2 Leverage Index (LI) ✅
- LI = expected |ΔWP| of the next ball, using empirical outcome probabilities (dot, 1, 2, 3, 4, 6, wicket, wide) by tier × phase, normalised so the mean is 1. This adapts Tango's baseball Leverage Index.
- Sanity checks (all tested): in death-over chases within ±5 runs of a run-a-ball, mean LI ≈ 2.5. In lopsided chases (more than 20 runs ahead of the rate), LI ≈ 0.06. The five highest-leverage balls in the dataset are all last-over chases (for example, 4 needed off 2 balls).

## 3. Definition of pressure ✅
**Principle:** pressure = **stakes** (how much the next ball can change the match) + **difficulty** (how hard the scoreboard situation is). Both are measured only from information known before the ball.

### 3.1 Two candidate definitions, built and compared
1. **Leverage only.** Data-driven stakes.
2. **Rule-based Pressure Index (RPI).** Weighted z-scores (weights fixed a priori from cricket reasoning, then stress-tested):

| Component | Weight | Signal |
|---|---:|---|
| Scoreboard gap, z-scored within innings. Chase: RRR − era par rate. Setting: era par − projected total (leave-one-year-out expected-remaining-runs table) | 0.25 | Scoreboard pressure |
| Wickets lost relative to balls used | 0.20 | Resource pressure |
| Closeness of contest, 1 − \|2·WP − 1\| | 0.20 | Match in the balance |
| Wickets in previous 12 deliveries | 0.15 | Collapse pressure |
| Dot-ball share of previous 12 legal balls | 0.10 | Squeeze / build-up |
| Innings progress, (share of innings bowled)² | 0.10 | Phase (smooth, no cliff) |

### 3.2 What the comparison showed (`reports/model_outputs/pressure_*.csv`)
- The two definitions **barely agree**: Spearman ρ = 0.06, and the high-pressure sets overlap by Jaccard 0.11.
- **Leverage alone is biased toward chases:** 92% of its top-20% balls fall in innings 2, and **none** fall in first-innings death overs. The innings-1 WP model is necessarily uncertain, so its swings are compressed. Batting-first specialists and bowlers defending a first-innings total would be structurally excluded.
- **RPI alone ignores stakes.** A collapse in a dead game still scores high.

### 3.3 Final definition: composite (v2, after review; see `research/PRESSURE_REVIEW.md`)
`pressure_score = percentile( 0.5 × leverage percentile + 0.5 × RPI percentile )`
- **Leverage percentile:** innings 1 is ranked *within each over*. The innings-1 WP model (AUC 0.69) imposes its own over-by-over shape on leverage, so only like-for-like stage comparisons are trusted. Innings 2 is ranked within the innings, because the chase model (AUC 0.93) has a genuine death-over rise.
- **HIGH pressure = top 20% of deliveries. LOW (ordinary) = bottom 50%.** Bands are percentile-based, so they are interpretable and not tied to the scale of any index.
- v1 → v2 review: three flaws were found and fixed. Batting-first middle-over collapses were barely recognised (2.6% → 23.9% HIGH), there was a hard 15→16 over cliff (largest adjacent-over jump 39 pp → 5 pp), and leverage stepped at phase boundaries.
- Balance: 42% of HIGH balls are in chases. HIGH share rises smoothly from about 3% in over 1 to about 40% in over 20 in both innings. Dead-game share is 0.8%.
- **Pressure does change outcomes** (league-wide, balls faced, v2): dismissal rate is **6.2%** under HIGH vs 5.3% under LOW. Raw SR is roughly flat (140 vs 142), because HIGH is concentrated late in the innings where scoring is faster. This is exactly why players are judged against **context-expected** performance, not raw averages.

- **Known limitation:** the dot-squeeze component is partly *endogenous*. A batter's own dot balls raise the pressure label on their next ball. Its weight is therefore kept low (0.10), and RPI-without-dots is one of the sensitivity variants.
- Sensitivity variants stored per delivery: blend 30/70 and 70/30 (`pressure_band_l30`, `pressure_band_l70`), leverage-only and RPI-only (`pressure_band_lev`, `pressure_band_rpi`). Overlap of the HIGH set with the final: RPI weight changes 0.81–0.89 Jaccard, blend 70/30 0.73, blend 30/70 0.59. Final rankings will be re-run under the blend variants and under HIGH thresholds of 15% and 30%, and rank stability across definitions is reported.

## 4. Batting reliability engine 🔜
- **Expected runs and expected dismissal per ball.** A context model (phase, balls left, wickets in hand, innings, chase state, tier, bowler type (pace/spin), batter hand, era par, opposition bowling strength), trained with the same chronological split. Outputs: **Runs Above Expected (RAE)** and **Dismissals Below Expected**, per ball and aggregated.
- **Pressure vs own baseline (the brief's core ask):** for each batter, (RAE per ball in HIGH) vs (RAE per ball in LOW/ordinary). Reliability = performing at or above expectation in HIGH, not just a large swing.
- **Opposition and competition adjustment:** opposition bowling strength (rolling team-season bowling rating from the data) enters the expectation model. Associate and A-team balls stay in the model but get explicit tier effects, so runs against Japan are not equated with runs against Australia.
- **Bayesian shrinkage:** Normal–Normal (empirical Bayes) shrinkage of per-ball RAE toward a role-specific prior, and Beta-Binomial for dismissal and boundary rates. Posterior means and 90% credible intervals are reported.
- **Consistency:** share of high-pressure innings with RAE ≥ 0, plus match-level dispersion and bootstrap (by match) rank intervals.
- **Match impact:** batting WPA in high-pressure balls.
- **Eligibility floor (proposed):** at least 120 high-pressure balls faced across at least 10 innings. To be tuned so no player ranks on fewer opportunities than the credible intervals can support.
- Roles from observed data: openers (positions 1–2), top/middle order (3–5), finishers (6–8).

## 5. Bowling reliability engine 🔜
- Mirror of batting: expected bowler runs and expected wickets per ball by context (phase, batter hand, tier, opposition batting strength, era). Outputs: **Runs Saved vs Expected** and **Wickets Above Expected**, in HIGH vs ordinary pressure.
- Phase-role benchmarks (powerplay, middle, death) taken from the observed share of each bowler's overs per phase, so a death specialist is never compared with a powerplay specialist on raw economy.
- Same Bayesian shrinkage, consistency, WPA (bowler = −batting WPA) and eligibility logic. Proposed floor: at least 150 high-pressure legal balls across at least 10 matches.

## 6. Reliability score and validation 🔜
- A 0–100 composite built from components that will be tested for correlation and double-counting before weights are fixed. The prompt's 30/25/20/15/10 weights are treated as a starting hypothesis only.
- Baselines for comparison: (a) raw high-pressure SR/economy, (b) RAE only. Weight-sensitivity grid and definition sensitivity (§3.3).
- Predictive check: does pressure reliability measured in 2022–2024 predict high-pressure RAE in 2025–2026 better than overall form does? This is the honest test of whether "reliability under pressure" is a persistent trait.
- Monte Carlo / bootstrap ranking stability: mean rank, 90% rank interval and P(top 10).

## 7. RR squad-fit layer 🔜
A separate layer with its own score. It never reorders the competition top 10 (see the DATA_AUDIT decisions log).
