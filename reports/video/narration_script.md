# Narration script: Inside SupeRR Intelligence

Every number below is generated from pipeline outputs (`src/reporting/video/script.py`). Narration voice: Microsoft Zira (offline Windows speech synthesis, synthetic).

## Chapter 1: The challenge

*Visual: s01*

Some players thrive when the game is on the line. Others fade. Rajasthan Royals' SupeRR Selector Season 2 asks a precise question: using data, who are the most reliable batters and bowlers under pressure, and how could they strengthen Rajasthan Royals for the IPL 2027 auction? This film explains how we answered it, step by step, and how sure we are.

*Visual: s02*

Here is the answer up front. Our most reliable batter under pressure is Shreyas Iyer, with a reliability score of 97 out of 100. Our most reliable bowler is Varun Chakravarthy, scoring 96. And the evidence says Rajasthan Royals' two biggest needs are a finisher who holds up under pressure, and a bowler who can defend at the death. The rest of this documentary shows why, and where the evidence is strong and where it is not.

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

The ten most reliable batters under pressure: Shreyas Iyer, Heinrich Klaasen, Rajat Patidar, Namboori Tilak Varma, Ishan Kishan, Naman Dhir, David Miller, Tim David, Suryakumar Yadav and Glenn Phillips. Heinrich Klaasen is the most certain pick, staying in the top ten in 92 percent of resamples. Andre Russell would have ranked fifth, but formally retired from the IPL in November 2025, so is excluded from a list built for IPL 2027.

*Visual: s14*

For each pick we name the two strongest players left out in the same role, and test whether the difference is real. Against those alternatives the top four batters are clearly or moderately ahead. Lower down the gaps shrink: for Ishan Kishan, the advantage over the best alternative is statistically indistinguishable, and we say so rather than pretend otherwise.

## Chapter 7: The bowlers

*Visual: s12*

The ten most reliable bowlers under pressure: Varun Chakravarthy, Sunil Narine, Jasprit Bumrah, Lockie Ferguson, Rashid Khan, Axar Patel, Matheesha Pathirana, Bhuvneshwar Kumar, Kuldeep Yadav and Sikandar Raza. Varun Chakravarthy leads, staying in the top ten in 84 percent of resamples, with a moderate edge over the strongest alternative in the same role, Krunal Pandya.

*Visual: s15*

Every identity and availability flag was checked against official sources. Matheesha Pathirana was ruled out of IPL 2026 with a hamstring injury. Kuldeep Yadav was traded to Lucknow Super Giants. Sikandar Raza has had no IPL contract since 2024, which makes Raza a potential auction entrant. These flags are reported beside the ranking, never used to score it.

## Chapter 8: The selection debate

*Visual: s13*

How sure are we? Each dot is a final rank. The thick bar is the range from one hundred bootstrap resamples of the whole pipeline; the thin bar is the range across alternative pressure definitions. The top of each list is firm. From about sixth to fifteenth, players are statistically close.

*Visual: s16*

That is why the near misses matter. Abhishek Sharma and Mohsin Khan are each under one point from tenth place, and each beats the tenth-ranked player in about half of all resamples. They are credible alternatives, not rejects.

## Chapter 9: What do Rajasthan Royals actually need?

*Visual: s18*

We studied Rajasthan Royals' own squad before matching any candidate, using exactly the same framework. The batting is elite up front: first of ten for powerplay run rate in both 2025 and 2026. But at the death it ranked between seventh and tenth on run rate, boundaries, context value and wickets lost, in both seasons, and in 2025 the death bowling conceded runs faster than any other team's.

*Visual: s19*

Turning that into priorities, finishing batting scores 81 out of 100, death bowling 61, and middle-overs batting 60. Opening batting scores only 30: it is a strength, not a need. Among current players, only Ravindra Jadeja ranks in the bowling top twenty under pressure.

## Chapter 10: The auction strategy

*Visual: s20*

Reliability and squad fit are kept separate. Squad fit asks which need a player would fill, how strong the evidence is in that phase, and whether an overseas player would cost a scarce slot. It guides targeting, but never reorders the competition lists.

*Visual: s21*

For batting, seven of the ten best fit the finishing role. Suryakumar Yadav, Tilak Varma and Shreyas Iyer are Indian finishing options that avoid the overseas squeeze; Tim David and Glenn Phillips are the overseas options.

*Visual: s22*

For bowling, Jasprit Bumrah fits the death-bowling need best, with Sunil Narine, Rashid Khan and Pathirana behind, subject to slots and fitness. Varun Chakravarthy would add middle-overs control alongside Jadeja. The run estimates in this table are hypothetical models, not forecasts.

## Chapter 11: Limitations and risks

*Visual: s23*

Pressure is a modelling choice, so we tested alternatives. The data covers 2022 to 2026, without domestic leagues or fielding attribution. Openers face few high-pressure balls, so some elite openers fall below eligibility. The IPL 2027 squads are not known until the retention deadline of 17 November 2026, and the 2027 purse is not verified, so we make no financial claims.

## Chapter 12: Final recommendations

*Visual: s24*

For Rajasthan Royals: target a finisher who holds up under pressure, and a death bowler, using the ranked shortlists for each. Add middle-overs spin control, and keep the opening pair. Re-run the needs analysis the day retentions are published. Reliable pressure performance is real but noisy. The defensible way to find it is to define pressure from the match situation, judge players against context and opponents, shrink small samples, and say how sure we are. That is SupeRR Intelligence.
