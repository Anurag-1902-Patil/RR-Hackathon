# Pressure Definition — Review (2026-11-14)

A critical review of the composite pressure definition (`src/features/pressure.py`, v1) **before** any player ranking depends on it.
Figures: `reports/figures/pressure_*.png`. Tables: `reports/model_outputs/pressure_*.csv`. Code: `src/reporting/pressure_figures.py`.

## Verdict
The v1 definition is **sound in its main structure but has three fixable flaws**, all concentrated in **first-innings batting and bowling**. If it went into rankings unchanged, it would systematically under-credit middle-order batters who rebuild after early wickets when batting first, and the bowlers who create those collapses.

## What holds up ✅
| Check | Result |
|---|---|
| Balance between innings | 46% of HIGH balls are in chases (leverage alone gave 92%) |
| Dead games excluded | Only ~1% of HIGH balls occur when WP < 5% or > 95% |
| Behaviour changes under pressure | Dismissal rate 6.1% (HIGH) vs 5.3% (LOW). SR 137 vs 143 |
| Chases | HIGH share peaks when the required rate is 8–10 (29%) and *falls* for RRR > 15 (14%). Near-impossible chases are lost causes, not pressure. This is intended |
| Robust to rule-based weights | Equal weights, dropping dot-squeeze or dropping closeness keep 78–86% of the HIGH set |
| Sample size | 106 batters with ≥120 HIGH balls faced. 81 bowlers with ≥150 HIGH legal balls |
| Tier mix | IPL 19.9% HIGH, T20I full members 21.0%, associates 13.4% (more one-sided games) |

## Flaws found ⚠️

### F1. Batting-first middle overs are almost never "pressure"
Figure `pressure_by_over_heatmap.png`: innings-1 overs 7–15 are HIGH on only **1–5%** of balls. Even in innings-1 middle overs with **4+ wickets down** (14,042 balls), only **2.6%** are HIGH.
**Cause:** the rule-based index has a scoreboard term only for chases (required-rate gap). Batting first, there is no "behind par" signal. Being 60/4 after 9 overs registers only through the wickets term.

### F2. Hard cliff at over 15 → 16
Innings-1 HIGH share jumps from 1% to 44% between overs 15 and 16.
**Cause:** the binary death-overs flag (z jumps from −0.53 to +1.88). Pressure does not change in one ball.

### F3. Leverage step changes at phase boundaries, and over 1 rated the most pivotal over of innings 1
Mean innings-1 leverage is 1.69 in over 1, falls to 0.59 by over 15, then jumps to 0.79 at over 16.
**Causes:** (a) next-ball outcome probabilities are bucketed by phase. Wicket probability goes from 4.5% in the middle overs to 7.7% at the death in the IPL, so there is a jump at the boundary. (b) The innings-1 WP model is most uncertain at the start, so a single early event moves its estimate most. That is a statistical property, not real match pressure.

### Decisive judgement call (not a flaw, but it must be disclosed)
Figure `pressure_sensitivity.png`: the **leverage / rule-based blend** is what really moves the definition. 30/70 and 70/30 keep only 67–68% of the HIGH set. Every final ranking must be re-run under both blends, with the overlap reported.

### Known limitation (accepted)
The dot-squeeze term is partly endogenous (a batter's own dots raise the pressure on their next ball). Its weight is 0.10, and removing it changes only 17% of the HIGH set. It will be reported as a sensitivity variant.

## Proposed fixes (v2)
| # | Fix | Addresses |
|---|---|---|
| A | **Innings-1 scoreboard term:** runs behind era par for this stage of the innings, adjusted for wickets in hand (the batting-first equivalent of the RRR gap) | F1 |
| B | **Smooth phase effects:** replace the binary death flag with a continuous innings-progress ramp, and replace phase-bucketed outcome probabilities with probabilities smoothed by over | F2, F3a |
| C | **Cap early-innings leverage inflation:** blend innings-1 leverage toward its by-over median for the first 2 overs, or take the leverage percentile within innings × over band | F3b |
| D | **Keep the 50/50 blend** as the primary definition, with 30/70 and 70/30 as mandatory ranking-sensitivity runs | Judgement call |

Acceptance tests for v2: no adjacent-over change in HIGH share above 15 percentage points; innings-1 middle overs with 4+ down at ≥ 15% HIGH; all existing pressure tests still pass.

---

## v2 outcome (approved by user, implemented 2026-11-14)

| Fix | As implemented |
|---|---|
| A | Innings-1 scoreboard term = era par − projected total. Projected total = score + par × E[remaining runs ÷ par \| overs left, wickets in hand], from full-length first innings of **other years** (leave-one-year-out, cells with ≥30 innings, else the overs-left average). Each innings' scoreboard gap is z-scored within that innings |
| B | Binary death flag → (share of innings bowled)². Leverage outcome probabilities now by tier × over, smoothed over a centred 3-over window |
| C | **Changed from the proposal.** Damping innings-1 overs 1–2 was tried first: it left batting-first middle overs at 1–5% HIGH (only 7.8% with 4+ down), because the innings-1 WP model imposes its own over-shape on leverage. Final: innings-1 leverage is ranked **within each over** (it only compares situations at the same stage), chase leverage is ranked within the innings (that WP model has AUC 0.93, so its death-over rise is real) |
| D | Blend kept at 50/50. Bands for 30/70 and 70/30 stored (`pressure_band_l30`, `pressure_band_l70`) for mandatory ranking sensitivity |

**Acceptance results** (tested in `tests/test_pressure.py`):

| Check | v1 | v2 | Target |
|---|---:|---:|---:|
| Max adjacent-over change in HIGH share | 39 pp | **5 pp** | ≤ 15 ✅ |
| Innings-1 overs 7–15, 4+ down, HIGH share | 2.6% | **23.9%** | ≥ 15% ✅ |
| HIGH balls in dead games (WP < 5% or > 95%) | ~1% | **0.8%** | < 2% ✅ |
| HIGH share in chases | 46% | 42% | balanced ✅ |
| Dismissal rate HIGH vs LOW | 6.1 vs 5.3% | 6.2 vs 5.3% | HIGH > LOW ✅ |
| HIGH share by tier | — | IPL 20.5%, T20I full 20.5%, associate 15.4%, A-team 15.1% | — |

**v2 sensitivity** (Jaccard overlap of the HIGH set with the final definition): RPI equal weights 0.89, drop dot-squeeze 0.88, drop scoreboard 0.83, drop closeness 0.81, blend 70/30 0.73, blend 30/70 0.59. The blend remains the most consequential choice. The RPI-heavy blend shifts the set most, so player rankings will be reported under both blends.
