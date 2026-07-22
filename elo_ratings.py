"""
AstroPitch V11 — ELO Rating Engine for International Football
==============================================================
Dynamic ELO calculator that processes historical match results to produce
team strength ratings. These ratings become the most powerful feature
in the XGBoost model.

Algorithm:
- K-factor: 40 for World Cup, 30 for qualifiers/continental, 20 for friendlies
- Home advantage: +100 ELO points
- Expected score: 1 / (1 + 10^((Ra - Rb) / 400))
- Goal difference multiplier: ln(goal_diff + 1) * 0.75
"""

import math
from real_international_data import INTERNATIONAL_MATCHES, get_match_result


# ======================================================================
# INITIAL ELO RATINGS (Based on FIFA Rankings Dec 2025 approximation)
# Scale: 1200 = weak, 1500 = average, 1800 = elite, 2000+ = dominant
# ======================================================================
INITIAL_ELO = {
    # Tier 1: Elite (1850+)
    "Argentina": 1950,
    "France": 1900,
    "Spain": 1890,
    "Brazil": 1870,
    "England": 1860,
    "Portugal": 1855,
    "Germany": 1850,

    # Tier 2: Strong (1700-1849)
    "Netherlands": 1830,
    "Belgium": 1810,
    "Italy": 1800,
    "Croatia": 1790,
    "Colombia": 1780,
    "Uruguay": 1775,
    "Japan": 1760,
    "Morocco": 1755,
    "USA": 1740,
    "Mexico": 1735,
    "Senegal": 1730,
    "Switzerland": 1725,
    "Denmark": 1720,
    "Turkey": 1710,
    "Austria": 1705,
    "South Korea": 1700,

    # Tier 3: Competitive (1550-1699)
    "Serbia": 1690,
    "Ecuador": 1680,
    "Iran": 1670,
    "Nigeria": 1665,
    "Australia": 1660,
    "Ivory Coast": 1655,
    "Chile": 1650,
    "Peru": 1645,
    "Scotland": 1640,
    "Poland": 1635,
    "Ukraine": 1630,
    "Hungary": 1625,
    "Sweden": 1620,
    "Egypt": 1610,
    "Canada": 1605,
    "Cameroon": 1600,
    "Paraguay": 1595,
    "Algeria": 1590,
    "Tunisia": 1585,
    "Ghana": 1575,
    "Wales": 1570,
    "Norway": 1565,
    "South Africa": 1560,
    "Venezuela": 1555,
    "Panama": 1550,

    # Tier 4: Developing (1350-1549)
    "Costa Rica": 1520,
    "Qatar": 1510,
    "Saudi Arabia": 1505,
    "Uzbekistan": 1500,
    "Bolivia": 1490,
    "Jamaica": 1480,
    "Iraq": 1470,
    "Congo DR": 1460,
    "Honduras": 1450,
    "Bahrain": 1430,
    "Cape Verde": 1420,
    "New Zealand": 1410,
    "Albania": 1400,
    "Indonesia": 1390,
    "Trinidad and Tobago": 1380,
    "Curacao": 1370,
    "Haiti": 1360,
    "Czechia": 1580,
    "Bosnia and Herzegovina": 1550,

    # Fallback teams seen in data but not in WC2026
    "Russia": 1650,
    "Iceland": 1500,
    "Georgia": 1480,
    "Romania": 1520,
    "Slovakia": 1500,
    "Slovenia": 1480,
    "Zambia": 1380,
    "Guinea": 1400,
    "Mali": 1430,
    "Namibia": 1320,
    "Angola": 1380,
    "Equatorial Guinea": 1350,
    "Tanzania": 1340,
    "Mozambique": 1310,
    "Guinea-Bissau": 1300,
    "Gambia": 1350,
    "Kenya": 1340,
    "Gabon": 1370,
    "Rwanda": 1320,
    "Lesotho": 1250,
    "Botswana": 1260,
    "Niger": 1280,
    "Kuwait": 1350,
    "Palestine": 1320,
    "China": 1400,
    "Thailand": 1320,
    "Singapore": 1200,
    "Syria": 1380,
    "North Korea": 1400,
    "Pakistan": 1200,
    "Tajikistan": 1300,
    "Cuba": 1280,
    "El Salvador": 1350,
    "Suriname": 1300,
    "North Macedonia": 1440,
    "Montenegro": 1440,
    "Luxembourg": 1300,
    "Ireland": 1510,
    "Malta": 1250,
    "Israel": 1470,
    "Greece": 1530,
    "Finland": 1460,
    "Estonia": 1300,
    "Bulgaria": 1380,
    "Armenia": 1370,
    "Jordan": 1450,
    "Burkina Faso": 1400,
}


class ELORatingEngine:
    """
    Dynamic ELO rating engine for international football.
    Processes historical match results chronologically to build team ratings.
    """

    def __init__(self, initial_ratings=None):
        self.ratings = dict(initial_ratings or INITIAL_ELO)
        self.match_history = []  # Store (date, home, away, h_elo, a_elo, elo_diff, elo_expected) for training

    def get_rating(self, team):
        """Get current ELO for a team, defaulting to 1400 for unknown teams."""
        return self.ratings.get(team, 1400)

    def _get_k_factor(self, tournament):
        """Higher K for more important tournaments."""
        if "Final" in tournament:
            return 50
        elif "SF" in tournament or "QF" in tournament:
            return 45
        elif "R16" in tournament:
            return 40
        elif "World Cup" in tournament:
            return 35
        else:
            return 20

    def _goal_diff_multiplier(self, goal_diff):
        """Amplify ELO change for dominant wins."""
        if goal_diff <= 1:
            return 1.0
        return math.log(goal_diff + 1) * 0.75

    def expected_score(self, rating_a, rating_b):
        """Calculate expected score (probability of A winning)."""
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))

    def update(self, home, away, home_goals, away_goals, tournament):
        """
        Update ELO ratings after a match.
        Home team gets +100 bonus in expected score calculation (home advantage).
        """
        home_elo = self.get_rating(home)
        away_elo = self.get_rating(away)

        # Home advantage bonus
        home_advantage = 100
        expected_home = self.expected_score(home_elo + home_advantage, away_elo)
        expected_away = 1.0 - expected_home

        # Actual score
        if home_goals > away_goals:
            actual_home, actual_away = 1.0, 0.0
        elif home_goals == away_goals:
            actual_home, actual_away = 0.5, 0.5
        else:
            actual_home, actual_away = 0.0, 1.0

        goal_diff = abs(home_goals - away_goals)
        k = self._get_k_factor(tournament)
        gdm = self._goal_diff_multiplier(goal_diff)

        # Update ratings
        change_home = k * gdm * (actual_home - expected_home)
        change_away = k * gdm * (actual_away - expected_away)

        self.ratings[home] = home_elo + change_home
        self.ratings[away] = away_elo + change_away

        return home_elo, away_elo, change_home, change_away

    def process_all_matches(self):
        """
        Process all real historical matches chronologically.
        Records pre-match ELO for each game (used as training features).
        """
        self.match_history = []

        for date_str, home, away, hg, ag, tournament in INTERNATIONAL_MATCHES:
            # Record PRE-match ELO values (these become features)
            h_elo = self.get_rating(home)
            a_elo = self.get_rating(away)
            elo_diff = h_elo - a_elo
            elo_expected = self.expected_score(h_elo + 100, a_elo)  # with home advantage

            self.match_history.append({
                "date": date_str,
                "home": home,
                "away": away,
                "home_goals": hg,
                "away_goals": ag,
                "tournament": tournament,
                "H_ELO": round(h_elo, 1),
                "A_ELO": round(a_elo, 1),
                "ELO_Diff": round(elo_diff, 1),
                "ELO_Expected": round(elo_expected, 4),
            })

            # Update ratings AFTER recording pre-match values
            self.update(home, away, hg, ag, tournament)

        return self.match_history

    def get_current_ratings(self):
        """Returns all ratings sorted by strength."""
        return sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)


def build_elo_database():
    """Build and return the full ELO database from history."""
    engine = ELORatingEngine()
    history = engine.process_all_matches()
    return engine, history


if __name__ == "__main__":
    engine, history = build_elo_database()

    print("=" * 60)
    print(" ASTROPITCH ELO RATINGS (Post-History Processing)")
    print("=" * 60)

    rankings = engine.get_current_ratings()
    for i, (team, elo) in enumerate(rankings[:30], 1):
        bar = "#" * int((elo - 1200) / 20)
        print(f"  {i:2d}. {team:<25s} {elo:7.1f}  {bar}")

    print(f"\n  Total teams tracked: {len(rankings)}")
    print(f"  Total matches processed: {len(history)}")
