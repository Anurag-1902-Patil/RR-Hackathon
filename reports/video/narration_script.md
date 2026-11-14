# Narration script: Inside SupeRR Intelligence

Every number below is generated from pipeline outputs (`src/reporting/video/script.py`). Narration voice: Microsoft Zira (offline Windows speech synthesis, synthetic).

## Chapter 1: The challenge

*Visual: s01*

Some players thrive when the game is on the line. Others fade. Rajasthan Royals' SupeRR Selector Season 2 asks a precise question: using data, who are the most reliable batters and bowlers under pressure, and how could they strengthen Rajasthan Royals for the IPL 2027 auction? This film explains how we answered it, step by step, and how sure we are.

*Visual: s02*

Here is the answer up front, counting only players Rajasthan Royals can actually sign. The most reliable batter under pressure is Daryl Mitchell, with a reliability score of 77 out of 100. The most reliable bowler is Sikandar Raza, scoring 85. And the evidence says Rajasthan Royals' two biggest needs are a finisher who holds up under pressure, and a bowler who can defend at the death. The rest of this documentary shows why, and where the evidence is strong and where it is not.

## Chapter 2: The data

*Visual: s04*

Our primary source is the official Rajasthan Royals data pack: ball-by-ball records for 200,961 deliveries across 867 matches, covering the IPL from 2022 to 2026 and T20 internationals. Before any modelling we audited every file. Computed scores matched the official result in 806 of 816 checkable matches, and the few exceptions were rain-affected games. We found a hidden no-ball code that, if treated as a legal ball, would have created hundreds of seven-ball overs. And we joined players only by ID, because some names belong to different people. Every model was validated chronologically: trained on 2022 to 2024, chosen on 2025, and tested on the unseen 2026 season.

## Chapter 3: Defining pressure

*Visual: s05*

Pressure cannot be observed directly, so we had to define it, using only information available before each ball. We built two measures. Stakes: a win-probability model tells us how much the next ball can swing the match. Difficulty: the scoreboard gap to an era-adjusted par, wickets lost, a recent collapse, a squeeze of dot balls, and how late it is in the innings. Stakes alone turned out to be blind to batting first: it put 92 percent of high-pressure balls in chases. So the final definition is half stakes and half difficulty, and the top 20 percent of all balls, 40,193 of them, are high pressure.

*Visual: fig:pressure_by_over_heatmap.png*

After a review, pressure now builds smoothly through both innings. And it changes behaviour: under high pressure batters were dismissed on 6.2 percent of balls, against 5.3 percent in ordinary situations. Raw strike rate is not the yardstick, because high-pressure balls cluster late in the innings, where everyone scores faster.

## Chapter 4: Building the analytical engine

*Visual: s06*

Fair comparison is the heart of the method. First, for every ball, a model estimates what an average player would produce in exactly that situation, using context only, never the player's name. Second, we score each ball as actual minus expected, charging a wicket at its real cost in that situation. Third, a ridge regression rates every batter and bowler together, so each player is judged net of the opponents actually faced. That is how IPL and international cricket are put on one scale. Fourth, small samples are pulled toward average, so nobody tops a list on a handful of good innings.

## Chapter 5: Testing the models

*Visual: s07*

A model is not included because it is advanced. For win probability, simple logistic regression beat LightGBM on both the 2025 validation season and the unseen 2026 test, with a chase Brier score of 0.116 against 0.139, because tree models could not extrapolate to 2026's record scoring. Validation also caught a bug: without an environment par, 2026 batters would all have looked better than they were.

*Visual: s08*

Then the key scientific question: is clutch real? After removing sampling noise, only about 21 percent of a batter's raw pressure-versus-normal gap is genuine signal, and about 4 percent for bowlers. Performance in ordinary situations repeats from season to season; pressure-only form largely does not. So we never rank a raw clutch table.

*Visual: s09*

Instead, the reliability score blends five things: pressure performance, consistency across pressure innings, impact on winning, the shrunk gap to a player's own baseline, and underlying ability. We stress-tested it with seven weightings and four alternative pressure definitions. The leaders hold; the middle of each list moves, and we report that openly.

## Chapter 6: The batters

*Visual: s11*

First, a reality check. Every player in the unrestricted performance top ten is already under contract at an IPL team, so a list of them would not help Rajasthan Royals at the auction. We therefore rank only players the franchise can actually sign: nobody on an IPL 2026 squad, no Pakistani or Bangladeshi players, and nobody retired or banned. That leaves 15 eligible batters and 12 eligible bowlers. Scores stay percentiles among all players, so they can still be compared with the contracted elite.

*Visual: s12*

The ten most reliable batters Rajasthan Royals can sign: Daryl Mitchell, Curtis Campher, Kusal Mendis, Mark Chapman, Sikandar Raza, Jimmy Neesham, George Dockrell, Ibrahim Zadran, Harry Tector and Ryan Burl. Daryl Mitchell leads with a score of 77, staying in the top ten in 100 percent of resamples. Six of the ten have no IPL record in the data, so their ratings rest on opponent-adjusted international cricket.

*Visual: s15*

For each pick we name the strongest players left out in the same role, and test whether the difference is real. Most of the batters are clearly ahead of the next signable options, Shai Hope and Charith Asalanka. Where the edge is only moderate, we say so.

## Chapter 7: The bowlers

*Visual: s13*

The ten most reliable bowlers Rajasthan Royals can sign: Sikandar Raza, Maheesh Theekshana, Adam Zampa, Joshua Little, Adil Rashid, Roston Chase, Obed McCoy, Richard Ngarava, Alzarri Joseph and Mark Adair. Sikandar Raza leads with a score of 85, staying in the top ten in 100 percent of resamples, and also ranks fifth among the batters.

*Visual: s16*

Every identity and availability flag was checked against official sources. None of these twenty players is retired or on an IPL 2026 squad. Each must still register for the auction. Ages are reported, not scored: Sikandar Raza will be forty at the auction, Adil Rashid thirty-eight.

## Chapter 8: The selection debate

*Visual: s14*

How sure is the model? Each dot is a rank among all eligible players. The thick bar is the range from one hundred bootstrap resamples of the whole pipeline; the thin bar is the range across alternative pressure definitions. The top is firm; the middle is close.

*Visual: s17*

Within the signable pool, the closest call is at the bottom of the bowling list. Ish Sodhi and FazalHaq Farooqi are only 2.3 points from tenth place, and each beats the tenth-ranked bowler in about half of all resamples. That is a coin-flip, and we label it as one.

*Visual: s18*

One gap remained. Every signable player in the data pack is an overseas international, and the pack has no Indian domestic cricket. So we added public ball-by-ball data from the Syed Mushtaq Ali Trophy, India's domestic T20 competition, played on Indian pitches: 272 matches since 2020. We applied the same pressure definition and the same score, and linked domestic and IPL ratings through 152 players who appear in both. A check on those players showed that domestic batting form carries over to the IPL, with a correlation of 0.5, but domestic bowling form did not.

*Visual: s19*

The uncapped fresher batters, all thirty or under and on no IPL squad: Rahul Buddhi, Narayan Jagadeesan, Rajat Dey, Atharva Taide and Harsh Tyagi. Rahul Buddhi and Narayan Jagadeesan are the clearest, each staying in the top five in 82 percent of resamples. For bowling, Atit Sheth leads clearly, but because domestic bowling form did not predict IPL bowling, the bowlers are a watchlist for live scouting, not firm picks.

## Chapter 9: What do Rajasthan Royals actually need?

*Visual: s21*

We studied Rajasthan Royals' own squad before matching any candidate, using exactly the same framework. The batting is elite up front: first of ten for powerplay run rate in both 2025 and 2026. But at the death it ranked between seventh and tenth on run rate, boundaries, context value and wickets lost, in both seasons, and in 2025 the death bowling conceded runs faster than any other team's.

*Visual: s22*

Turning that into priorities, finishing batting scores 81 out of 100, death bowling 61, and middle-overs batting 60. Opening batting scores only 30: it is a strength, not a need. Among current players, only Ravindra Jadeja ranks in the bowling top twenty under pressure.

## Chapter 10: The auction strategy

*Visual: s23*

Reliability and squad fit are kept separate. Squad fit asks which need a player would fill, how strong the evidence is in that phase, and whether an overseas player would cost a scarce slot. It guides targeting, but never reorders the competition lists.

*Visual: s24*

Every signable player is overseas, so slots are the binding constraint, and a player who covers two needs is worth more. Sikandar Raza is the one primary target: ninety-seventh percentile in death-overs batting, and the top signable bowler for the middle overs. For middle-overs batting depth, Mark Chapman and Daryl Mitchell.

*Visual: s25*

For death bowling, Maheesh Theekshana stands out, at the eighty-fifth percentile at the death and with Rajasthan Royals experience from 2025, followed by Adam Zampa. The run estimates in this table are hypothetical models, not forecasts.

## Chapter 11: Limitations and risks

*Visual: s26*

The signable pool is clearly weaker than the contracted elite. Several players have little or no IPL record. The public domestic data stops at the 2024/25 season, so the very newest freshers are missing, and domestic bowling form is a weak guide. Excluding Bangladeshi players, and Harry Brook, is a judgement, and we state it as one. Players released on 17 November 2026 will join the pool, and the 2027 purse is not verified, so we make no financial claims.

## Chapter 12: Final recommendations

*Visual: s27*

For Rajasthan Royals: first target Sikandar Raza. For death bowling, Maheesh Theekshana, then Adam Zampa. For middle-overs batting, Mark Chapman or Daryl Mitchell. For Indian slots, scout the uncapped batters Rahul Buddhi and Narayan Jagadeesan first. Keep the opening pair, and re-run the selection the day releases are published. Reliable pressure performance is real but noisy. The defensible way to find it is to define pressure from the match situation, judge players against context and opponents, shrink small samples, and say how sure we are. That is SupeRR Intelligence.
