import sys
from importlib import import_module

m = import_module("13_world_cup_predictor")
WorldCupPredictor = m.WorldCupPredictor
engine = WorldCupPredictor()

# Patch in teams not in the baseline 48
extra_teams = {
    "Congo DR": {"founded": "1919-01-01", "color": "Blue", "manager_dob": "1976-04-15"},
    "Switzerland": {"founded": "1895-04-15", "color": "Red", "manager_dob": "1974-08-09"},
    "Bosnia and Herzegovina": {"founded": "1992-04-15", "color": "Blue", "manager_dob": "1974-05-18"},
    "Scotland": {"founded": "1873-03-03", "color": "Blue", "manager_dob": "1963-08-29"},
    "Haiti": {"founded": "1904-04-15", "color": "Blue", "manager_dob": "1969-02-09"},
    "Czechia": {"founded": "1901-10-19", "color": "Red", "manager_dob": "1963-02-28"},
    "South Africa": {"founded": "1992-12-08", "color": "Yellow", "manager_dob": "1952-05-05"},
    "Curacao": {"founded": "1921-01-01", "color": "Blue", "manager_dob": "1968-07-06"},
    "Tunisia": {"founded": "1956-03-20", "color": "Red", "manager_dob": "1968-03-05"},
    "Sweden": {"founded": "1904-06-18", "color": "Yellow", "manager_dob": "1970-03-22"},
    "Norway": {"founded": "1902-01-30", "color": "Red", "manager_dob": "1967-07-08"},
    "Iraq": {"founded": "1948-06-07", "color": "White", "manager_dob": "1958-11-10"},
    "Cape Verde": {"founded": "1982-07-05", "color": "Blue", "manager_dob": "1975-08-20"},
    "Egypt": {"founded": "1921-01-05", "color": "Red", "manager_dob": "1970-09-12"},
    "Colombia": {"founded": "1924-10-12", "color": "Yellow", "manager_dob": "1981-04-12"},
    "Portugal": {"founded": "1914-03-31", "color": "Red", "manager_dob": "1973-04-28"},
    "Ghana": {"founded": "1957-01-01", "color": "White", "manager_dob": "1975-01-01"},
    "DR Congo": {"founded": "1919-01-01", "color": "Blue", "manager_dob": "1976-04-15"},
    "Uzbekistan": {"founded": "1946-01-01", "color": "Blue", "manager_dob": "1968-01-01"},
    "Jordan": {"founded": "1949-01-01", "color": "White", "manager_dob": "1969-01-01"},
    "Argentina": {"founded": "1893-02-21", "color": "Blue", "manager_dob": "1978-05-16"},
    "Algeria": {"founded": "1962-01-01", "color": "Green", "manager_dob": "1976-01-01"},
    "Austria": {"founded": "1904-03-18", "color": "Red", "manager_dob": "1958-05-11"},
    "Australia": {"founded": "1961-01-01", "color": "Yellow", "manager_dob": "1968-01-01"},
    "Paraguay": {"founded": "1906-01-01", "color": "Red", "manager_dob": "1969-01-01"},
    "Panama": {"founded": "1937-01-01", "color": "Red", "manager_dob": "1973-01-01"},
    "England": {"founded": "1863-01-01", "color": "White", "manager_dob": "1970-01-01"},
    "Spain": {"founded": "1909-01-01", "color": "Red", "manager_dob": "1961-01-01"},
    "Saudi Arabia": {"founded": "1956-01-01", "color": "Green", "manager_dob": "1964-01-01"},
    "New Zealand": {"founded": "1891-01-01", "color": "White", "manager_dob": "1974-01-01"},
    "Belgium": {"founded": "1895-01-01", "color": "Red", "manager_dob": "1985-01-01"},
    "Iran": {"founded": "1920-01-01", "color": "White", "manager_dob": "1963-01-01"},
    "Croatia": {"founded": "1912-01-01", "color": "Red", "manager_dob": "1966-01-01"},
    "France": {"founded": "1919-01-01", "color": "Blue", "manager_dob": "1968-01-01"},
    "Senegal": {"founded": "1960-01-01", "color": "White", "manager_dob": "1976-01-01"},
    "Canada": {"founded": "1912-05-24", "color": "Red", "manager_dob": "1966-10-27"},
    "Brazil": {"founded": "1914-06-08", "color": "Yellow", "manager_dob": "1962-11-04"},
    "Japan": {"founded": "1921-09-10", "color": "Blue", "manager_dob": "1968-01-09"},
    "Netherlands": {"founded": "1889-12-08", "color": "Orange", "manager_dob": "1963-02-08"},
    "Morocco": {"founded": "1955-05-21", "color": "Red", "manager_dob": "1971-08-11"},
    "USA": {"founded": "1913-04-05", "color": "White", "manager_dob": "1973-08-05"},
    "Canada": {"founded": "1912-05-24", "color": "Red", "manager_dob": "1975-08-15"},
    "Mexico": {"founded": "1922-08-09", "color": "Green", "manager_dob": "1978-12-18"},
    "Ecuador": {"founded": "1925-05-30", "color": "Yellow", "manager_dob": "1981-03-11"},
    "Ivory Coast": {"founded": "1960-08-28", "color": "Orange", "manager_dob": "1983-12-20"},
}
engine.team_entities.update(extra_teams)

matches = [
    {"h": "South Africa", "a": "Canada", "oh": 5.50, "od": 3.45, "oa": 1.838, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/06/28 22:00:00", "v": "BMO Field, Toronto"},
    {"h": "Brazil", "a": "Japan", "oh": 1.753, "od": 3.87, "oa": 5.35, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/06/29 20:00:00", "v": "MetLife Stadium, New York"},
    {"h": "Germany", "a": "Paraguay", "oh": 1.358, "od": 5.55, "oa": 10.00, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/06/29 23:30:00", "v": "Levi's Stadium, San Francisco"},
    {"h": "Netherlands", "a": "Morocco", "oh": 2.232, "od": 3.31, "oa": 3.77, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/06/30 04:00:00", "v": "Gillette Stadium, Boston"},
    {"h": "Ivory Coast", "a": "Norway", "oh": 3.805, "od": 3.685, "oa": 2.077, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/06/30 20:00:00", "v": "Lumen Field, Seattle"},
    {"h": "France", "a": "Sweden", "oh": 1.293, "od": 6.46, "oa": 11.40, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/07/01 00:00:00", "v": "SoFi Stadium, Los Angeles"},
    {"h": "Mexico", "a": "Ecuador", "oh": 2.294, "od": 3.14, "oa": 3.83, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/07/01 04:00:00", "v": "Estadio Azteca, Mexico City"},
    {"h": "England", "a": "DR Congo", "oh": 1.293, "od": 5.90, "oa": 13.70, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/07/01 19:00:00", "v": "AT&T Stadium, Dallas"},
    {"h": "Belgium", "a": "Senegal", "oh": 2.191, "od": 3.36, "oa": 3.82, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/07/01 23:00:00", "v": "Mercedes-Benz Stadium, Atlanta"},
    {"h": "USA", "a": "Bosnia and Herzegovina", "oh": 1.396, "od": 5.14, "oa": 9.55, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/07/02 03:00:00", "v": "Lincoln Financial Field, Philadelphia"},
    {"h": "Spain", "a": "Austria", "oh": 1.313, "od": 5.70, "oa": 12.70, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/07/02 22:00:00", "v": "Hard Rock Stadium, Miami"},
    {"h": "Portugal", "a": "Croatia", "oh": 1.824, "od": 3.615, "oa": 5.24, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/07/03 02:00:00", "v": "NRG Stadium, Houston"},
    {"h": "Switzerland", "a": "Algeria", "oh": 1.963, "od": 3.54, "oa": 4.475, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/07/03 06:00:00", "v": "Arrowhead Stadium, Kansas City"},
    {"h": "Australia", "a": "Egypt", "oh": 3.38, "od": 3.055, "oa": 2.547, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/07/03 21:00:00", "v": "Levi's Stadium, San Francisco"},
    {"h": "Argentina", "a": "Cape Verde", "oh": 1.175, "od": 8.25, "oa": 23.00, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/07/04 01:00:00", "v": "MetLife Stadium, New York"},
    {"h": "Colombia", "a": "Ghana", "oh": 1.579, "od": 3.95, "oa": 7.70, "ou_o": 1.90, "ou_u": 1.90, "date": "2026/07/04 04:30:00", "v": "Hard Rock Stadium, Miami"},
]

dividers = {
    "2026/06/28 22:00:00": "Sun 28 Jun",
    "2026/06/29 20:00:00": "Mon 29 Jun",
    "2026/06/30 04:00:00": "Tue 30 Jun",
    "2026/07/01 00:00:00": "Wed 01 Jul",
    "2026/07/02 03:00:00": "Thu 02 Jul",
    "2026/07/03 02:00:00": "Fri 03 Jul",
    "2026/07/04 01:00:00": "Sat 04 Jul",
}

output = ""
last_date = None

for idx, m in enumerate(matches, 1):
    if m["date"] in dividers and dividers[m["date"]] != last_date:
        last_date = dividers[m["date"]]
        output += f"\n{'='*75}\n {last_date.upper()}\n{'='*75}\n"

    res = engine.predict(
        home=m['h'], away=m['a'],
        odds_home=m['oh'], odds_draw=m['od'], odds_away=m['oa'],
        odds_over25=m['ou_o'], odds_under25=m['ou_u'],
        venue=m['v'], stage="World Cup Group", date_utc=m['date']
    )

    verdict = res['verdict_1x2'].replace("VALUE BET:", "VALUE BET ->").replace("NO VALUE BET", "NO VALUE").replace("NO BET:", "NO BET:").replace("🔥 ","").replace("⚖️ ","")
    ou_verdict = res['verdict_ou'].replace("🔥 ","").replace("⚖️ ","")

    output += f"\n  #{idx:02d}  {m['h']:<22} vs  {m['a']:<22}  ({m['date'][11:16]} UTC)\n"
    output += f"       Odds: {m['oh']:.2f} / {m['od']:.2f} / {m['oa']:.2f}\n"
    output += f"       1X2:  H {res['home_prob']}  D {res['draw_prob']}  A {res['away_prob']}\n"
    output += f"       O/U:  Over {res['over_prob']}  |  Under {res['under_prob']}\n"
    output += f"       SCORE: {res['exact_score']} (conf {res['score_confidence']})  | Moon: {res['moon_zodiac']}  Retro: {res['mercury_retro']}\n"
    output += f"       >> {verdict}\n"
    output += f"       >> {ou_verdict}\n"

with open("match_predictions.txt", "w", encoding="utf-8") as f:
    f.write(output)
