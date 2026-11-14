"""Documentary narration, chapters, trailer and reel scripts, with every number filled from pipeline outputs.

Each scene = (chapter, visual(s), narration). Visuals are deck slides (s01..s25, exported at 1920x1080),
chapter title cards ("card:<n>") or report figures ("fig:<path>"). Player pronouns are avoided on purpose.
"""
from __future__ import annotations

import json

import pandas as pd

from src.config import REPORTS_DIR, RESEARCH_DIR


def data() -> dict:
    D = json.loads((REPORTS_DIR / "deck_data.json").read_text(encoding="utf-8"))
    D["pm"] = pd.read_csv(RESEARCH_DIR / "rr_recruitment_priority_matrix.csv").set_index("requirement")["priority_score"].to_dict()
    return D


def verdict(p: float) -> str:
    return "clear" if p >= .8 else "moderate" if p >= .65 else "slight" if p >= .55 else "statistically indistinguishable"


def pct(x: float) -> str:
    return f"{round(x * 100)} percent"


def names(rows, k=None) -> str:
    n = [r["player"] for r in (rows[:k] if k else rows)]
    return ", ".join(n[:-1]) + " and " + n[-1]


CHAPTERS = ["The challenge", "The data", "Defining pressure", "Building the analytical engine", "Testing the models",
            "The batters", "The bowlers", "The selection debate", "What do Rajasthan Royals actually need?",
            "The auction strategy", "Limitations and risks", "Final recommendations"]


def documentary() -> list[dict]:
    D = data()
    s, bat, bowl = D["summary"], D["batting"], D["bowling"]
    cb = next(c for c in D["clutch"] if c["side"] == "batting")
    cw = next(c for c in D["clutch"] if c["side"] == "bowling")
    hi = next(p for p in D["pressure_profile"] if p["pressure_band"] == "high")
    lo = next(p for p in D["pressure_profile"] if p["pressure_band"] == "low")
    wp2 = {r["model"]: r for r in D["wp_test"] if r["innings"] == 2}
    S = []

    def add(ch, visuals, text):
        S.append({"chapter": ch, "visuals": visuals, "text": " ".join(text.split())})

    add(1, ["card:1"], "Chapter one. The challenge.")
    add(1, ["s01"], """Some players thrive when the game is on the line. Others fade. Rajasthan Royals' SupeRR Selector Season 2 asks
        a precise question: using data, who are the most reliable batters and bowlers under pressure, and how could they strengthen
        Rajasthan Royals for the IPL 2027 auction? This film explains how we answered it, step by step, and how sure we are.""")
    add(1, ["s02"], f"""Here is the answer up front, counting only players Rajasthan Royals can actually sign. The most reliable batter under pressure is {bat[0]['player']}, with a reliability score of
        {bat[0]['score']} out of 100. The most reliable bowler is {bowl[0]['player']}, scoring {bowl[0]['score']}. And the evidence says Rajasthan
        Royals' two biggest needs are a finisher who holds up under pressure, and a bowler who can defend at the death. The rest of this
        documentary shows why, and where the evidence is strong and where it is not.""")
    add(2, ["card:2"], "Chapter two. The data.")
    add(2, ["s04"], f"""Our primary source is the official Rajasthan Royals data pack: ball-by-ball records for {int(s['deliveries']):,} deliveries
        across {int(s['matches_with_ball_data'])} matches, covering the IPL from 2022 to 2026 and T20 internationals. Before any modelling we audited every
        file. Computed scores matched the official result in 806 of 816 checkable matches, and the few exceptions were rain-affected games.
        We found a hidden no-ball code that, if treated as a legal ball, would have created hundreds of seven-ball overs. And we joined
        players only by ID, because some names belong to different people. Every model was validated chronologically: trained on 2022 to
        2024, chosen on 2025, and tested on the unseen 2026 season.""")
    add(3, ["card:3"], "Chapter three. Defining pressure.")
    add(3, ["s05"], f"""Pressure cannot be observed directly, so we had to define it, using only information available before each ball.
        We built two measures. Stakes: a win-probability model tells us how much the next ball can swing the match. Difficulty: the
        scoreboard gap to an era-adjusted par, wickets lost, a recent collapse, a squeeze of dot balls, and how late it is in the innings.
        Stakes alone turned out to be blind to batting first: it put 92 percent of high-pressure balls in chases. So the final definition is
        half stakes and half difficulty, and the top 20 percent of all balls, {int(s['high_pressure_deliveries']):,} of them, are high pressure.""")
    add(3, ["fig:pressure_by_over_heatmap.png"], f"""After a review, pressure now builds smoothly through both innings. And it changes behaviour:
        under high pressure batters were dismissed on {hi['dismissal_pct']:.1f} percent of balls, against {lo['dismissal_pct']:.1f} percent in
        ordinary situations. Raw strike rate is not the yardstick, because high-pressure balls cluster late in the innings, where everyone
        scores faster.""")
    add(4, ["card:4"], "Chapter four. Building the analytical engine.")
    add(4, ["s06"], """Fair comparison is the heart of the method. First, for every ball, a model estimates what an average player would
        produce in exactly that situation, using context only, never the player's name. Second, we score each ball as actual minus
        expected, charging a wicket at its real cost in that situation. Third, a ridge regression rates every batter and bowler together,
        so each player is judged net of the opponents actually faced. That is how IPL and international cricket are put on one scale.
        Fourth, small samples are pulled toward average, so nobody tops a list on a handful of good innings.""")
    add(5, ["card:5"], "Chapter five. Testing the models.")
    add(5, ["s07"], f"""A model is not included because it is advanced. For win probability, simple logistic regression beat LightGBM on both the
        2025 validation season and the unseen 2026 test, with a chase Brier score of {wp2['logit']['brier']:.3f} against {wp2['lgbm']['brier']:.3f},
        because tree models could not extrapolate to 2026's record scoring. Validation also caught a bug: without an environment par,
        2026 batters would all have looked better than they were.""")
    add(5, ["s08"], f"""Then the key scientific question: is clutch real? After removing sampling noise, only about {pct(cb['reliability_of_raw_delta'])}
        of a batter's raw pressure-versus-normal gap is genuine signal, and about {pct(cw['reliability_of_raw_delta'])} for bowlers. Performance in
        ordinary situations repeats from season to season; pressure-only form largely does not. So we never rank a raw clutch table.""")
    add(5, ["s09"], f"""Instead, the reliability score blends five things: pressure performance, consistency across pressure innings, impact on
        winning, the shrunk gap to a player's own baseline, and underlying ability. We stress-tested it with seven weightings and four
        alternative pressure definitions. The leaders hold; the middle of each list moves, and we report that openly.""")
    add(6, ["card:6"], "Chapter six. The batters.")
    add(6, ["s11"], f"""First, a reality check. Every player in the unrestricted performance top ten is already under contract at an IPL team, so a list of
        them would not help Rajasthan Royals at the auction. We therefore rank only players the franchise can actually sign: nobody on an IPL
        2026 squad, no Pakistani or Bangladeshi players, and nobody retired or banned. That leaves {D['pool']['batting']} eligible batters and
        {D['pool']['bowling']} eligible bowlers. Scores stay percentiles among all players, so they can still be compared with the contracted elite.""")
    add(6, ["s12"], f"""The ten most reliable batters Rajasthan Royals can sign: {names(bat)}. {bat[0]['player']} leads with a score of
        {bat[0]['score']}, staying in the top ten in {pct(bat[0]['p_top10'])} of resamples. Six of the ten have no IPL record in the data,
        so their ratings rest on opponent-adjusted international cricket.""")
    add(6, ["s15"], """For each pick we name the strongest players left out in the same role, and test whether the difference is real.
        Most of the batters are clearly ahead of the next signable options, Shai Hope and Charith Asalanka. Where the edge is only moderate, we say so.""")
    add(7, ["card:7"], "Chapter seven. The bowlers.")
    add(7, ["s13"], f"""The ten most reliable bowlers Rajasthan Royals can sign: {names(bowl)}. {bowl[0]['player']} leads with a score of
        {bowl[0]['score']}, staying in the top ten in {pct(bowl[0]['p_top10'])} of resamples, and also ranks fifth among the batters.""")
    add(7, ["s16"], """Every identity and availability flag was checked against official sources. None of these twenty players is retired or
        on an IPL 2026 squad. Each must still register for the auction. Ages are reported, not scored: Sikandar Raza will be forty
        at the auction, Adil Rashid thirty-eight.""")
    add(8, ["card:8"], "Chapter eight. The selection debate.")
    add(8, ["s14"], """How sure is the model? Each dot is a rank among all eligible players. The thick bar is the range from one hundred bootstrap
        resamples of the whole pipeline; the thin bar is the range across alternative pressure definitions. The top is firm; the middle is close.""")
    add(8, ["s17"], f"""Within the signable pool, the closest call is at the bottom of the bowling list. {D['near'][-2]['player']} and
        {D['near'][-1]['player']} are only {D['near'][-1]['gap_to_rank10']} points from tenth place, and each beats the tenth-ranked bowler in
        about half of all resamples. That is a coin-flip, and we label it as one.""")
    add(9, ["card:9"], "Chapter nine. What do Rajasthan Royals actually need?")
    add(9, ["s19"], """We studied Rajasthan Royals' own squad before matching any candidate, using exactly the same framework. The batting is elite
        up front: first of ten for powerplay run rate in both 2025 and 2026. But at the death it ranked between seventh and tenth on run rate, boundaries, context value and wickets lost, in both seasons,
        and in 2025 the death bowling conceded runs faster than any other team's.""")
    add(9, ["s20"], f"""Turning that into priorities, finishing batting scores {D['pm']['Death-overs / finishing batting']:.0f} out of 100, death bowling
        {D['pm']['Death-overs bowling']:.0f}, and middle-overs batting {D['pm']['Middle-overs batting']:.0f}. Opening batting scores only
        {D['pm']['Powerplay / opening batting']:.0f}: it is a strength, not a need. Among current players, only Ravindra Jadeja ranks in the
        bowling top twenty under pressure.""")
    add(10, ["card:10"], "Chapter ten. The auction strategy.")
    add(10, ["s21"], """Reliability and squad fit are kept separate. Squad fit asks which need a player would fill, how strong the evidence is in
        that phase, and whether an overseas player would cost a scarce slot. It guides targeting, but never reorders the competition lists.""")
    add(10, ["s22"], """Every signable player is overseas, so slots are the binding constraint, and a player who covers two needs is worth more.
        Sikandar Raza is the one primary target: ninety-seventh percentile in death-overs batting, and the top signable bowler for the middle
        overs. For middle-overs batting depth, Mark Chapman and Daryl Mitchell.""")
    add(10, ["s23"], """For death bowling, Maheesh Theekshana stands out, at the eighty-fifth percentile at the death and with Rajasthan Royals
        experience from 2025, followed by Adam Zampa. The run estimates in this table are hypothetical models, not forecasts.""")
    add(11, ["card:11"], "Chapter eleven. Limitations and risks.")
    add(11, ["s24"], """The signable pool is clearly weaker than the contracted elite. Several players have little or no IPL record. The data
        has no Indian domestic cricket, so uncapped Indian players cannot be assessed. Excluding Bangladeshi players, and Harry Brook, is a
        judgement, and we state it as one. Players released on 17 November 2026 will join the pool, and the 2027 purse is not verified, so we
        make no financial claims.""")
    add(12, ["card:12"], "Chapter twelve. Final recommendations.")
    add(12, ["s25"], """For Rajasthan Royals: first target Sikandar Raza. For death bowling, Maheesh Theekshana, then Adam Zampa. For middle-overs
        batting, Mark Chapman or Daryl Mitchell. Keep the opening pair, and re-run the selection the day releases are published.
        Reliable pressure performance is real but noisy. The defensible way to find it is to define pressure from the match situation,
        judge players against context and opponents, shrink small samples, and say how sure we are. That is SupeRR Intelligence.""")
    return S


def trailer() -> list[dict]:
    D = data()
    b, w = D["batting"], D["bowling"]
    lines = [
        ("s01", "Who delivers when it matters? Two hundred thousand balls of IPL and international cricket hold the answer."),
        ("s05", "We defined pressure before every ball: what was at stake, and how hard the situation was."),
        ("s08", "We found that most apparent clutch is noise, so we built a score that cannot be fooled by it."),
        ("s11", "We kept only players Rajasthan Royals can actually sign."),
        ("s12", f"The most reliable batter they can sign: {b[0]['player']}."),
        ("s13", f"The most reliable bowler: {w[0]['player']}."),
        ("s19", "And what Rajasthan Royals actually need: a finisher, and a death bowler."),
        ("card:end", "SupeRR Intelligence. Full report, dashboard and documentary available."),
    ]
    return [{"chapter": 0, "visuals": [v], "text": t} for v, t in lines]


def reel() -> list[dict]:
    D = data()
    b, w = D["batting"], D["bowling"]
    lines = [
        ("s01", "Can data tell who handles pressure best in T20 cricket?", "WHO DELIVERS UNDER PRESSURE?"),
        ("s05", "We scored 200,961 balls for pressure: what was at stake, and how hard the situation was.", "DEFINING PRESSURE"),
        ("s06", "Then we compared every player to an average player in the same situation, against the same opponents.", "FAIR COMPARISON"),
        ("s08", "Surprise: most 'clutch' is noise. Only about a fifth of a batter's pressure gap is real.", "IS CLUTCH REAL?"),
        ("s12", f"Top signable batter under pressure: {b[0]['player']}. Next: {b[1]['player']} and {b[2]['player']}.", "TOP BATTERS RR CAN SIGN"),
        ("s13", f"Top signable bowler: {w[0]['player']}. Next: {w[1]['player']} and {w[2]['player']}.", "TOP BOWLERS RR CAN SIGN"),
        ("s19", "Rajasthan Royals' data says: elite openers, but a need at the death, with bat and ball.", "WHAT RR NEEDS"),
        ("card:end", "Independent analysis for SupeRR Selector Season 2. Full method in the report.", "SUPERR INTELLIGENCE"),
    ]
    return [{"chapter": 0, "visuals": [v], "text": t, "hook": h} for v, t, h in lines]
