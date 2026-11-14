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

## 4. Context expectations ✅ (`src/models/expected.py`)
For every ball, four expectations are computed from **situation only** (never player identity):
- expected batter runs and dismissal probability (balls faced),
- expected runs conceded and bowler-wicket probability (all deliveries).

**Features:** innings, over, balls left, wickets in hand, share of innings left, current rate vs par, required rate vs par, share of target remaining, IPL flag, environment par, bowling type / pace-spin / batter hand / hand-arm-type matchup (batting models only).

**Competition fairness.** No T20I tier variable is used. A tier dummy would define "average" separately for associate matches and IPL matches, which would inflate players who mostly face weak opposition. League strength is calibrated in §5 by the opponents each player actually faced. Only the *scoring environment* is modelled directly: **environment par** is a rolling 60-match first-innings mean from strictly earlier matches, pooled for IPL vs all internationals (deliberately not split by tier).

**Season re-centring.** Within each (year × IPL/international) environment, expectations are scaled so mean expected = mean observed. Factors are within ±6% for runs. Players are therefore compared with the average player *of that season*.

**Validation** (LightGBM vs innings × over mean, chronological):
- Runs models beat the baseline on RMSE in both 2025 (1.740 vs 1.754) and 2026 (1.808 vs 1.826).
- Wicket models are on par with the baseline: dismissals are close to random at the ball level.
- RMSE is the selection metric because residuals are *summed* per player, so an unbiased mean matters more than a median-optimal MAE.

**Bug found and fixed:** with a season-label feature, the held-out 2026 season was unseen, and expected runs per ball came out at 1.351 against 1.505 observed. Environment par fixed this (1.461).

Production values are leave-one-year-out cross-fitted.

## 5. Value per ball and opponent-adjusted ratings ✅ (`src/models/ratings.py`)
**Value per ball** (in runs; positive = good for the player rated):
- batting `v = (runs − xRuns) − C·(out − xOut)`
- bowling `v = (xConceded − conceded) + C·(wicket − xWicket)`

`C` = context cost of a wicket = expected remaining runs with *w* wickets in hand minus with *w*−1, for the same overs left. It comes from a resources table built from full-length first innings, made monotone in wickets and scaled to environment par. An early wicket costs more than a last-over one (tested).

**Ridge regression (Gaussian prior), RAPM-style:**
`v = μ + a_player + d_player·HIGH + b_opponent + e_opponent·HIGH`.
- Opponent effects adjust for the quality of the bowlers each batter actually faced, and vice versa.
- This also calibrates competition strength through players who cross competitions: 182 batters appear in both IPL and T20I.
- Penalties are tuned **out of time**: fit 2022–24, score MSE on 2025–26.

**Key empirical findings (reported honestly):**
1. Per-ball predictability is tiny: about 0.06–0.09% MSE reduction. This is normal, because one ball is mostly noise.
2. **Pressure-delta terms never improve out-of-time prediction**, including on HIGH balls. The rule keeps the largest delta scale within 3% of the best out-of-time HIGH-ball skill (scale 0.25, α = 1000). That shrinks ridge deltas almost to zero.
3. **Player-level persistence** (2022–24 → 2025–26; 26–55 qualifying players, so SE ≈ ±0.15):

| | Batting | Bowling |
|---|---|---|
| Ordinary-situation value | r = 0.37–0.49 | r = 0.19–0.37 |
| HIGH-pressure value | r = −0.20 to 0.04 | r = −0.22 to 0.02 |
| Pressure delta | unstable (0.03 to 0.44) | regresses (−0.43 to −0.22) |

4. **Empirical-Bayes clutch variance** (variance of raw deltas minus sampling noise; `reports/model_outputs/clutch_variance.csv`):
   - Batting: true SD of the pressure delta ≈ **0.14 runs/ball**. **21%** of a raw delta is signal (154 players).
   - Bowling: ≈ **0.06**, with only **4%** signal (182 players).

   So some batters genuinely perform differently under pressure relative to their norm. For bowlers it is essentially undetectable.

**Measures carried forward:**
- **Usual ability:** all-ball ridge main effect.
- **Pressure performance delivered:** a separate ridge on **HIGH balls only** (batter + bowler effects, shrunk to the league mean; α = 2000, an interior out-of-time optimum).
- **Pressure delta vs own baseline:** raw delta × τ²/(τ² + sᵢ²), an empirical-Bayes shrinkage specific to each player's own sample size.

## 6. Player tables, reliability score and validation ✅ (`src/scouting/`)
**Eligibility:**
- Batting: ≥ 120 HIGH balls faced and ≥ 10 pressure innings (≥ 6 HIGH balls in an innings).
- Bowling: ≥ 150 HIGH legal balls and ≥ 10 pressure spells.
- **Auction relevance:** the player must appear in the data in 2025 or 2026. Players removed by this rule are listed in `excluded_inactive.csv`. Real retirement and availability status needs external verification and is not assumed.

**Roles** come from data: median batting position (Opener / No.3 / Middle 4–5 / Finisher 6–7 / Lower) and bowling phase share (death ≥ 40%, powerplay ≥ 45%, middle ≥ 55%, otherwise multi-phase).

**Reliability score (0–100)** = weighted mean of component percentiles among eligible players. The score is reported as an integer to avoid false precision.

| Component | Weight | Definition |
|---|---:|---|
| Pressure performance | 35% | HIGH-ball opponent-adjusted ridge value |
| Consistency | 20% | Share of pressure innings/spells with value ≥ 0, Beta-Binomial shrunk (prior strength 10) |
| Match impact | 20% | WPA per HIGH ball, empirical-Bayes shrunk |
| Pressure vs own baseline | 15% | Empirical-Bayes delta |
| Usual ability | 10% | All-ball ridge; the best out-of-time predictor |

**Why not the prompt's hypothesis weights.** "Sample confidence" is set to 0 because shrinkage already uses sample size, and adding it again would double-count. "Role adaptability" belongs in the RR squad-fit layer, not in pressure reliability.

**Double-counting check:** pressure performance and impact correlate at ρ ≈ 0.81 (both measure HIGH-ball outcomes, one in runs and one in WP). The *no-impact* variant is reported.

**Sensitivity:**
- **Weights:** seven schemes (equal, prompt-hypothesis mapped, pressure-only, no-impact, predictive tilt, baseline-delta heavy). The top-10 overlap is 7–10 and Spearman ≥ 0.97 against the final scheme.
- **Pressure definition:** the full pipeline is re-run under blend 30/70 and 70/30 and HIGH = top 15% / top 30%, scored on the same eligible universe. The min–max rank across definitions is reported per player.
- **Uncertainty:** a match-level bootstrap (100 replicates of the full player pipeline: ratings, deltas, consistency, impact). For each player it reports mean rank, 90% rank interval, P(top 10) and P(top 20). These are statements about *measurement* uncertainty in 2022–26 performance, **not** probabilities of future performance.

## 7. RR squad-fit layer 🔜
A separate layer with its own score. It never reorders the competition top 10 (see the DATA_AUDIT decisions log).
