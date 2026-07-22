import pandas as pd
from importlib import import_module
import itertools

m = import_module("13_world_cup_predictor")
WorldCupPredictor = m.WorldCupPredictor
engine = WorldCupPredictor()

# Ensure missing team entities are mapped
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
}
engine.team_entities.update(extra_teams)

# Get the strongest 16 elite contenders
top_contenders = [
    "France", "Argentina", "Spain", "England", "Brazil", "Portugal",
    "Netherlands", "Germany", "Italy", "Uruguay", "Croatia", "Senegal",
    "Morocco", "Colombia", "USA", "Japan"
]

date_of_final = "2026/07/19 20:00:00"
venue = "MetLife Stadium, New York"

scores = {team: 0.0 for team in top_contenders}
wins = {team: 0 for team in top_contenders}

# Round Robin matches among top contenders
matchups = list(itertools.combinations(top_contenders, 2))
print(f"Simulating {len(matchups)} hypothetical Final Matchups on exactly {date_of_final}...")

# Compute average matrix probabilities for all contenders purely using the World Cup Model
for (t1, t2) in matchups:
    # Force neutral bookmaker odds (2.6 / 3.0 / 2.6) so the model CANNOT cheat by looking at what odds a sportsbook would offer
    res = engine.predict(
        home=t1, away=t2,
        odds_home=2.6, odds_draw=3.0, odds_away=2.6,
        odds_over25=1.9, odds_under25=1.9,
        venue=venue, stage="World Cup Final", date_utc=date_of_final
    )
    h_prob = float(res['home_prob'].strip('%'))
    d_prob = float(res['draw_prob'].strip('%'))
    a_prob = float(res['away_prob'].strip('%'))
    
    # Expected Expected points (3 point win, 1 point draw)
    scores[t1] += (h_prob/100 * 3) + (d_prob/100 * 1)
    scores[t2] += (a_prob/100 * 3) + (d_prob/100 * 1)
    
    # Store explicit win counts (if one team > 50%)
    if h_prob > 50:
        wins[t1] += 1
    elif a_prob > 50:
        wins[t2] += 1

print("\n🏆 ASTROPITCH JUL-19-2026 POWER RANKINGS 🏆")
print("-" * 55)
print(f"{'RANK':<5} {'TEAM':<15} | {'POWER INDEX':<15} | {'DOMINANCE':<15}")
print("-" * 55)

sorted_teams = sorted(scores.items(), key=lambda x: x[1], reverse=True)
for idx, (team, score) in enumerate(sorted_teams, 1):
    dom_count = wins[team]
    print(f"{idx:02d}.   {team:<15} | {score:14.2f}  | Won {dom_count:02d}/{len(top_contenders)-1} matchups")

winner = sorted_teams[0][0]
print("\n" + "="*55)
print(f"🌟 ULTIMATE WORLD CUP WINNER ON JULY 19: {winner.upper()} 🌟")
print("="*55)
