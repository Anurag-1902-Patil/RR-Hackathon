# LinkedIn post (draft; not posted)

Who actually delivers when a T20 game is on the line?

For Rajasthan Royals' SupeRR Selector Season 2, I built SupeRR Intelligence: a pressure-based reliability engine over 200,961 IPL and T20I deliveries (2022–26).

What I learned:
- Pressure has to be defined *before* each ball. I combined what is at stake (win-probability leverage) with how hard the situation is (scoreboard gap, wickets, collapse, dot-ball squeeze).
- Fair comparison means judging every ball against an average player in the same situation, then adjusting for the opponents faced. That is how IPL and internationals end up on one scale.
- The surprise: most "clutch" is noise. Only about 21% of a batter's raw pressure gap survives a noise check, so I built a score that shrinks it instead of ranking it raw.
- Simple beat fancy: logistic regression out-predicted gradient boosting on the unseen 2026 season.

Every player in the unrestricted top 10 is already under IPL contract, so I ranked only players RR can actually sign. Most reliable under pressure among them: Daryl Mitchell (batting) and Sikandar Raza (bowling). For RR, the evidence points to a finisher and a death bowler, and Sikandar Raza covers both bat and ball.

Independent analytical submission. Not affiliated with or endorsed by Rajasthan Royals.

#SupeRRSelector #CricketAnalytics #SportsAnalytics #DataScience #IPL
