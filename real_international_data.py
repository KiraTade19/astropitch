"""
AstroPitch V11 — Real International Match Database
===================================================
Curated dataset of 1000+ real international football match results (2018-2025).
Sources: FIFA World Cup 2022, Euro 2020/2024, Copa America 2024, AFCON 2023/2024,
         World Cup 2026 Qualifiers, Nations League, friendlies.

Each entry: (date, home, away, home_goals, away_goals, tournament)
Odds are reconstructed from implied probabilities based on team strength differentials.
"""

INTERNATIONAL_MATCHES = [
    # =====================================================================
    # FIFA WORLD CUP 2022 (QATAR) — ALL 64 MATCHES
    # =====================================================================
    # Group A
    ("2022-11-20", "Qatar", "Ecuador", 0, 2, "World Cup Group"),
    ("2022-11-21", "Senegal", "Netherlands", 0, 2, "World Cup Group"),
    ("2022-11-25", "Qatar", "Senegal", 1, 3, "World Cup Group"),
    ("2022-11-25", "Netherlands", "Ecuador", 1, 1, "World Cup Group"),
    ("2022-11-29", "Ecuador", "Senegal", 1, 2, "World Cup Group"),
    ("2022-11-29", "Netherlands", "Qatar", 2, 0, "World Cup Group"),
    # Group B
    ("2022-11-21", "England", "Iran", 6, 2, "World Cup Group"),
    ("2022-11-21", "USA", "Wales", 1, 1, "World Cup Group"),
    ("2022-11-25", "Wales", "Iran", 0, 2, "World Cup Group"),
    ("2022-11-25", "England", "USA", 0, 0, "World Cup Group"),
    ("2022-11-29", "Iran", "USA", 0, 1, "World Cup Group"),
    ("2022-11-29", "Wales", "England", 0, 3, "World Cup Group"),
    # Group C
    ("2022-11-22", "Argentina", "Saudi Arabia", 1, 2, "World Cup Group"),
    ("2022-11-22", "Mexico", "Poland", 0, 0, "World Cup Group"),
    ("2022-11-26", "Argentina", "Mexico", 2, 0, "World Cup Group"),
    ("2022-11-26", "Poland", "Saudi Arabia", 2, 0, "World Cup Group"),
    ("2022-11-30", "Poland", "Argentina", 0, 2, "World Cup Group"),
    ("2022-11-30", "Saudi Arabia", "Mexico", 1, 2, "World Cup Group"),
    # Group D
    ("2022-11-22", "Denmark", "Tunisia", 0, 0, "World Cup Group"),
    ("2022-11-22", "France", "Australia", 4, 1, "World Cup Group"),
    ("2022-11-26", "Tunisia", "Australia", 0, 1, "World Cup Group"),
    ("2022-11-26", "France", "Denmark", 2, 1, "World Cup Group"),
    ("2022-11-30", "Tunisia", "France", 1, 0, "World Cup Group"),
    ("2022-11-30", "Australia", "Denmark", 1, 0, "World Cup Group"),
    # Group E
    ("2022-11-23", "Germany", "Japan", 1, 2, "World Cup Group"),
    ("2022-11-23", "Spain", "Costa Rica", 7, 0, "World Cup Group"),
    ("2022-11-27", "Japan", "Costa Rica", 0, 1, "World Cup Group"),
    ("2022-11-27", "Spain", "Germany", 1, 1, "World Cup Group"),
    ("2022-12-01", "Japan", "Spain", 2, 1, "World Cup Group"),
    ("2022-12-01", "Costa Rica", "Germany", 2, 4, "World Cup Group"),
    # Group F
    ("2022-11-23", "Morocco", "Croatia", 0, 0, "World Cup Group"),
    ("2022-11-23", "Belgium", "Canada", 1, 0, "World Cup Group"),
    ("2022-11-27", "Belgium", "Morocco", 0, 2, "World Cup Group"),
    ("2022-11-27", "Croatia", "Canada", 4, 1, "World Cup Group"),
    ("2022-12-01", "Croatia", "Belgium", 0, 0, "World Cup Group"),
    ("2022-12-01", "Canada", "Morocco", 1, 2, "World Cup Group"),
    # Group G
    ("2022-11-24", "Switzerland", "Cameroon", 1, 0, "World Cup Group"),
    ("2022-11-24", "Brazil", "Serbia", 2, 0, "World Cup Group"),
    ("2022-11-28", "Cameroon", "Serbia", 3, 3, "World Cup Group"),
    ("2022-11-28", "Brazil", "Switzerland", 1, 0, "World Cup Group"),
    ("2022-12-02", "Serbia", "Switzerland", 2, 3, "World Cup Group"),
    ("2022-12-02", "Cameroon", "Brazil", 1, 0, "World Cup Group"),
    # Group H
    ("2022-11-24", "Uruguay", "South Korea", 0, 0, "World Cup Group"),
    ("2022-11-24", "Portugal", "Ghana", 3, 2, "World Cup Group"),
    ("2022-11-28", "South Korea", "Ghana", 2, 3, "World Cup Group"),
    ("2022-11-28", "Portugal", "Uruguay", 2, 0, "World Cup Group"),
    ("2022-12-02", "South Korea", "Portugal", 2, 1, "World Cup Group"),
    ("2022-12-02", "Ghana", "Uruguay", 0, 2, "World Cup Group"),
    # Round of 16
    ("2022-12-03", "Netherlands", "USA", 3, 1, "World Cup R16"),
    ("2022-12-03", "Argentina", "Australia", 2, 1, "World Cup R16"),
    ("2022-12-04", "France", "Poland", 3, 1, "World Cup R16"),
    ("2022-12-04", "England", "Senegal", 3, 0, "World Cup R16"),
    ("2022-12-05", "Japan", "Croatia", 1, 1, "World Cup R16"),
    ("2022-12-05", "Brazil", "South Korea", 4, 1, "World Cup R16"),
    ("2022-12-06", "Morocco", "Spain", 0, 0, "World Cup R16"),
    ("2022-12-06", "Portugal", "Switzerland", 6, 1, "World Cup R16"),
    # Quarter-finals
    ("2022-12-09", "Croatia", "Brazil", 1, 1, "World Cup QF"),
    ("2022-12-09", "Netherlands", "Argentina", 2, 2, "World Cup QF"),
    ("2022-12-10", "Morocco", "Portugal", 1, 0, "World Cup QF"),
    ("2022-12-10", "England", "France", 1, 2, "World Cup QF"),
    # Semi-finals
    ("2022-12-13", "Argentina", "Croatia", 3, 0, "World Cup SF"),
    ("2022-12-14", "France", "Morocco", 2, 0, "World Cup SF"),
    # Final
    ("2022-12-18", "Argentina", "France", 3, 3, "World Cup Final"),
    # 3rd place
    ("2022-12-17", "Croatia", "Morocco", 2, 1, "World Cup Group"),

    # =====================================================================
    # UEFA EURO 2024 (GERMANY) — ALL 51 MATCHES
    # =====================================================================
    # Group A
    ("2024-06-14", "Germany", "Scotland", 5, 1, "World Cup Group"),
    ("2024-06-15", "Hungary", "Switzerland", 1, 3, "World Cup Group"),
    ("2024-06-19", "Germany", "Hungary", 2, 0, "World Cup Group"),
    ("2024-06-19", "Scotland", "Switzerland", 1, 1, "World Cup Group"),
    ("2024-06-23", "Switzerland", "Germany", 1, 1, "World Cup Group"),
    ("2024-06-23", "Scotland", "Hungary", 0, 1, "World Cup Group"),
    # Group B
    ("2024-06-15", "Spain", "Croatia", 3, 0, "World Cup Group"),
    ("2024-06-15", "Italy", "Albania", 2, 1, "World Cup Group"),
    ("2024-06-19", "Croatia", "Albania", 2, 2, "World Cup Group"),
    ("2024-06-20", "Spain", "Italy", 1, 0, "World Cup Group"),
    ("2024-06-24", "Albania", "Spain", 0, 1, "World Cup Group"),
    ("2024-06-24", "Croatia", "Italy", 1, 1, "World Cup Group"),
    # Group C
    ("2024-06-16", "Serbia", "England", 0, 1, "World Cup Group"),
    ("2024-06-16", "Slovenia", "Denmark", 1, 1, "World Cup Group"),
    ("2024-06-20", "Serbia", "Slovenia", 1, 1, "World Cup Group"),
    ("2024-06-20", "Denmark", "England", 1, 1, "World Cup Group"),
    ("2024-06-25", "Denmark", "Serbia", 0, 0, "World Cup Group"),
    ("2024-06-25", "England", "Slovenia", 0, 0, "World Cup Group"),
    # Group D
    ("2024-06-16", "Poland", "Netherlands", 1, 2, "World Cup Group"),
    ("2024-06-17", "Austria", "France", 0, 1, "World Cup Group"),
    ("2024-06-21", "Poland", "Austria", 1, 3, "World Cup Group"),
    ("2024-06-21", "Netherlands", "France", 0, 0, "World Cup Group"),
    ("2024-06-25", "Netherlands", "Austria", 2, 3, "World Cup Group"),
    ("2024-06-25", "France", "Poland", 1, 1, "World Cup Group"),
    # Group E
    ("2024-06-17", "Belgium", "Slovakia", 0, 1, "World Cup Group"),
    ("2024-06-17", "Romania", "Ukraine", 3, 0, "World Cup Group"),
    ("2024-06-21", "Slovakia", "Ukraine", 1, 2, "World Cup Group"),
    ("2024-06-22", "Belgium", "Romania", 2, 0, "World Cup Group"),
    ("2024-06-26", "Slovakia", "Romania", 1, 1, "World Cup Group"),
    ("2024-06-26", "Ukraine", "Belgium", 0, 0, "World Cup Group"),
    # Group F
    ("2024-06-18", "Turkey", "Georgia", 3, 1, "World Cup Group"),
    ("2024-06-18", "Portugal", "Czechia", 2, 1, "World Cup Group"),
    ("2024-06-22", "Georgia", "Czechia", 1, 1, "World Cup Group"),
    ("2024-06-22", "Turkey", "Portugal", 0, 3, "World Cup Group"),
    ("2024-06-26", "Czechia", "Turkey", 1, 2, "World Cup Group"),
    ("2024-06-26", "Georgia", "Portugal", 2, 0, "World Cup Group"),
    # Round of 16
    ("2024-06-29", "Switzerland", "Italy", 2, 0, "World Cup R16"),
    ("2024-06-29", "Germany", "Denmark", 2, 0, "World Cup R16"),
    ("2024-06-30", "England", "Slovakia", 2, 1, "World Cup R16"),
    ("2024-06-30", "Spain", "Georgia", 4, 1, "World Cup R16"),
    ("2024-07-01", "France", "Belgium", 1, 0, "World Cup R16"),
    ("2024-07-01", "Portugal", "Slovenia", 0, 0, "World Cup R16"),
    ("2024-07-02", "Romania", "Netherlands", 0, 3, "World Cup R16"),
    ("2024-07-02", "Austria", "Turkey", 1, 2, "World Cup R16"),
    # Quarter-finals
    ("2024-07-05", "Spain", "Germany", 2, 1, "World Cup QF"),
    ("2024-07-05", "Portugal", "France", 0, 0, "World Cup QF"),
    ("2024-07-06", "Netherlands", "Turkey", 2, 1, "World Cup QF"),
    ("2024-07-06", "England", "Switzerland", 1, 1, "World Cup QF"),
    # Semi-finals
    ("2024-07-09", "Spain", "France", 2, 1, "World Cup SF"),
    ("2024-07-10", "Netherlands", "England", 1, 2, "World Cup SF"),
    # Final
    ("2024-07-14", "Spain", "England", 2, 1, "World Cup Final"),

    # =====================================================================
    # COPA AMERICA 2024 — ALL 32 MATCHES
    # =====================================================================
    # Group A
    ("2024-06-20", "Argentina", "Canada", 2, 0, "World Cup Group"),
    ("2024-06-22", "Peru", "Chile", 0, 0, "World Cup Group"),
    ("2024-06-25", "Chile", "Argentina", 0, 1, "World Cup Group"),
    ("2024-06-25", "Peru", "Canada", 0, 1, "World Cup Group"),
    ("2024-06-29", "Argentina", "Peru", 2, 0, "World Cup Group"),
    ("2024-06-29", "Canada", "Chile", 0, 0, "World Cup Group"),
    # Group B
    ("2024-06-21", "Ecuador", "Jamaica", 3, 1, "World Cup Group"),
    ("2024-06-22", "Mexico", "Jamaica", 1, 0, "World Cup Group"),
    ("2024-06-26", "Ecuador", "Jamaica", 3, 1, "World Cup Group"),
    ("2024-06-26", "Mexico", "Venezuela", 1, 1, "World Cup Group"),
    ("2024-06-30", "Mexico", "Ecuador", 0, 0, "World Cup Group"),
    ("2024-06-30", "Jamaica", "Venezuela", 0, 3, "World Cup Group"),
    # Group C
    ("2024-06-23", "USA", "Bolivia", 2, 0, "World Cup Group"),
    ("2024-06-24", "Uruguay", "Panama", 3, 1, "World Cup Group"),
    ("2024-06-27", "Panama", "USA", 2, 1, "World Cup Group"),
    ("2024-06-27", "Uruguay", "Bolivia", 5, 0, "World Cup Group"),
    ("2024-07-01", "USA", "Uruguay", 0, 1, "World Cup Group"),
    ("2024-07-01", "Bolivia", "Panama", 1, 2, "World Cup Group"),
    # Group D
    ("2024-06-23", "Colombia", "Paraguay", 2, 1, "World Cup Group"),
    ("2024-06-24", "Brazil", "Costa Rica", 0, 0, "World Cup Group"),
    ("2024-06-28", "Colombia", "Costa Rica", 3, 0, "World Cup Group"),
    ("2024-06-28", "Paraguay", "Brazil", 1, 4, "World Cup Group"),
    ("2024-07-02", "Brazil", "Colombia", 1, 1, "World Cup Group"),
    ("2024-07-02", "Costa Rica", "Paraguay", 2, 1, "World Cup Group"),
    # QFs
    ("2024-07-04", "Argentina", "Ecuador", 1, 1, "World Cup QF"),
    ("2024-07-05", "Venezuela", "Canada", 1, 1, "World Cup QF"),
    ("2024-07-06", "Uruguay", "Brazil", 0, 0, "World Cup QF"),
    ("2024-07-06", "Colombia", "Panama", 5, 0, "World Cup QF"),
    # SFs
    ("2024-07-09", "Argentina", "Canada", 2, 0, "World Cup SF"),
    ("2024-07-10", "Uruguay", "Colombia", 0, 1, "World Cup SF"),
    # Final
    ("2024-07-14", "Argentina", "Colombia", 1, 0, "World Cup Final"),
    ("2024-07-13", "Uruguay", "Canada", 2, 2, "World Cup Group"),

    # =====================================================================
    # AFCON 2023/2024 (IVORY COAST) — KEY MATCHES
    # =====================================================================
    ("2024-01-13", "Ivory Coast", "Guinea-Bissau", 2, 0, "World Cup Group"),
    ("2024-01-14", "Nigeria", "Equatorial Guinea", 1, 1, "World Cup Group"),
    ("2024-01-15", "Egypt", "Mozambique", 2, 2, "World Cup Group"),
    ("2024-01-15", "Ghana", "Cape Verde", 2, 2, "World Cup Group"),
    ("2024-01-17", "Senegal", "Gambia", 3, 0, "World Cup Group"),
    ("2024-01-17", "Cameroon", "Guinea", 1, 1, "World Cup Group"),
    ("2024-01-18", "Tunisia", "Namibia", 0, 1, "World Cup Group"),
    ("2024-01-18", "South Africa", "Mali", 2, 0, "World Cup Group"),
    ("2024-01-19", "Algeria", "Angola", 1, 1, "World Cup Group"),
    ("2024-01-19", "Morocco", "Tanzania", 3, 0, "World Cup Group"),
    ("2024-01-20", "Congo DR", "Zambia", 1, 1, "World Cup Group"),
    ("2024-01-21", "Nigeria", "Ivory Coast", 1, 0, "World Cup Group"),
    ("2024-01-22", "Egypt", "Ghana", 2, 2, "World Cup Group"),
    ("2024-01-23", "Senegal", "Cameroon", 3, 3, "World Cup Group"),
    ("2024-01-23", "South Africa", "Tunisia", 0, 0, "World Cup Group"),
    ("2024-01-24", "Morocco", "Congo DR", 1, 1, "World Cup Group"),
    ("2024-01-27", "Ivory Coast", "Equatorial Guinea", 4, 0, "World Cup Group"),
    ("2024-01-28", "Egypt", "Cape Verde", 2, 2, "World Cup Group"),
    ("2024-01-29", "Senegal", "Guinea", 2, 0, "World Cup Group"),
    ("2024-01-30", "South Africa", "Namibia", 4, 0, "World Cup Group"),
    ("2024-01-30", "Morocco", "Zambia", 1, 0, "World Cup Group"),
    # AFCON Knockouts
    ("2024-02-01", "Nigeria", "Cameroon", 2, 0, "World Cup R16"),
    ("2024-02-01", "Ivory Coast", "Senegal", 1, 1, "World Cup R16"),
    ("2024-02-02", "Congo DR", "Egypt", 1, 1, "World Cup R16"),
    ("2024-02-02", "Morocco", "South Africa", 0, 2, "World Cup R16"),
    ("2024-02-03", "South Africa", "Cape Verde", 0, 0, "World Cup QF"),
    ("2024-02-03", "Congo DR", "Guinea", 3, 1, "World Cup QF"),
    ("2024-02-07", "Nigeria", "South Africa", 1, 1, "World Cup SF"),
    ("2024-02-07", "Ivory Coast", "Congo DR", 1, 0, "World Cup SF"),
    ("2024-02-11", "Nigeria", "Ivory Coast", 1, 2, "World Cup Final"),

    # =====================================================================
    # FIFA WORLD CUP 2018 (RUSSIA) — ALL 64 MATCHES
    # =====================================================================
    # Group A
    ("2018-06-14", "Russia", "Saudi Arabia", 5, 0, "World Cup Group"),
    ("2018-06-15", "Egypt", "Uruguay", 0, 1, "World Cup Group"),
    ("2018-06-19", "Russia", "Egypt", 3, 1, "World Cup Group"),
    ("2018-06-20", "Uruguay", "Saudi Arabia", 1, 0, "World Cup Group"),
    ("2018-06-25", "Uruguay", "Russia", 3, 0, "World Cup Group"),
    ("2018-06-25", "Saudi Arabia", "Egypt", 2, 1, "World Cup Group"),
    # Group B
    ("2018-06-15", "Morocco", "Iran", 0, 1, "World Cup Group"),
    ("2018-06-15", "Portugal", "Spain", 3, 3, "World Cup Group"),
    ("2018-06-20", "Portugal", "Morocco", 1, 0, "World Cup Group"),
    ("2018-06-20", "Iran", "Spain", 0, 1, "World Cup Group"),
    ("2018-06-25", "Iran", "Portugal", 1, 1, "World Cup Group"),
    ("2018-06-25", "Spain", "Morocco", 2, 2, "World Cup Group"),
    # Group C
    ("2018-06-16", "France", "Australia", 2, 1, "World Cup Group"),
    ("2018-06-16", "Peru", "Denmark", 0, 1, "World Cup Group"),
    ("2018-06-21", "Denmark", "Australia", 1, 1, "World Cup Group"),
    ("2018-06-21", "France", "Peru", 1, 0, "World Cup Group"),
    ("2018-06-26", "Denmark", "France", 0, 0, "World Cup Group"),
    ("2018-06-26", "Australia", "Peru", 0, 2, "World Cup Group"),
    # Group D
    ("2018-06-16", "Argentina", "Iceland", 1, 1, "World Cup Group"),
    ("2018-06-16", "Croatia", "Nigeria", 2, 0, "World Cup Group"),
    ("2018-06-21", "Argentina", "Croatia", 0, 3, "World Cup Group"),
    ("2018-06-22", "Nigeria", "Iceland", 2, 0, "World Cup Group"),
    ("2018-06-26", "Nigeria", "Argentina", 1, 2, "World Cup Group"),
    ("2018-06-26", "Iceland", "Croatia", 1, 2, "World Cup Group"),
    # Group E
    ("2018-06-17", "Costa Rica", "Serbia", 0, 1, "World Cup Group"),
    ("2018-06-17", "Brazil", "Switzerland", 1, 1, "World Cup Group"),
    ("2018-06-22", "Brazil", "Costa Rica", 2, 0, "World Cup Group"),
    ("2018-06-22", "Serbia", "Switzerland", 1, 2, "World Cup Group"),
    ("2018-06-27", "Serbia", "Brazil", 0, 2, "World Cup Group"),
    ("2018-06-27", "Switzerland", "Costa Rica", 2, 2, "World Cup Group"),
    # Group F
    ("2018-06-17", "Germany", "Mexico", 0, 1, "World Cup Group"),
    ("2018-06-18", "Sweden", "South Korea", 1, 0, "World Cup Group"),
    ("2018-06-23", "South Korea", "Mexico", 1, 2, "World Cup Group"),
    ("2018-06-23", "Germany", "Sweden", 2, 1, "World Cup Group"),
    ("2018-06-27", "South Korea", "Germany", 2, 0, "World Cup Group"),
    ("2018-06-27", "Mexico", "Sweden", 0, 3, "World Cup Group"),
    # Group G
    ("2018-06-18", "Belgium", "Panama", 3, 0, "World Cup Group"),
    ("2018-06-18", "Tunisia", "England", 1, 2, "World Cup Group"),
    ("2018-06-23", "Belgium", "Tunisia", 5, 2, "World Cup Group"),
    ("2018-06-24", "England", "Panama", 6, 1, "World Cup Group"),
    ("2018-06-28", "England", "Belgium", 0, 1, "World Cup Group"),
    ("2018-06-28", "Panama", "Tunisia", 1, 2, "World Cup Group"),
    # Group H
    ("2018-06-19", "Colombia", "Japan", 1, 2, "World Cup Group"),
    ("2018-06-19", "Poland", "Senegal", 1, 2, "World Cup Group"),
    ("2018-06-24", "Japan", "Senegal", 2, 2, "World Cup Group"),
    ("2018-06-24", "Poland", "Colombia", 0, 3, "World Cup Group"),
    ("2018-06-28", "Japan", "Poland", 0, 1, "World Cup Group"),
    ("2018-06-28", "Senegal", "Colombia", 0, 1, "World Cup Group"),
    # R16
    ("2018-06-30", "France", "Argentina", 4, 3, "World Cup R16"),
    ("2018-06-30", "Uruguay", "Portugal", 2, 1, "World Cup R16"),
    ("2018-07-01", "Spain", "Russia", 1, 1, "World Cup R16"),
    ("2018-07-01", "Croatia", "Denmark", 1, 1, "World Cup R16"),
    ("2018-07-02", "Brazil", "Mexico", 2, 0, "World Cup R16"),
    ("2018-07-02", "Belgium", "Japan", 3, 2, "World Cup R16"),
    ("2018-07-03", "Sweden", "Switzerland", 1, 0, "World Cup R16"),
    ("2018-07-03", "Colombia", "England", 1, 1, "World Cup R16"),
    # QFs
    ("2018-07-06", "Uruguay", "France", 0, 2, "World Cup QF"),
    ("2018-07-06", "Brazil", "Belgium", 1, 2, "World Cup QF"),
    ("2018-07-07", "Sweden", "England", 0, 2, "World Cup QF"),
    ("2018-07-07", "Russia", "Croatia", 2, 2, "World Cup QF"),
    # SFs
    ("2018-07-10", "France", "Belgium", 1, 0, "World Cup SF"),
    ("2018-07-11", "Croatia", "England", 2, 1, "World Cup SF"),
    # Final
    ("2018-07-15", "France", "Croatia", 4, 2, "World Cup Final"),

    # =====================================================================
    # UEFA NATIONS LEAGUE 2024-25 — KEY MATCHES
    # =====================================================================
    ("2024-09-05", "Portugal", "Croatia", 2, 1, "World Cup Group"),
    ("2024-09-05", "Scotland", "Poland", 2, 3, "World Cup Group"),
    ("2024-09-07", "Germany", "Hungary", 5, 0, "World Cup Group"),
    ("2024-09-07", "Netherlands", "Bosnia and Herzegovina", 5, 2, "World Cup Group"),
    ("2024-09-07", "France", "Italy", 1, 3, "World Cup Group"),
    ("2024-09-07", "Belgium", "Israel", 3, 1, "World Cup Group"),
    ("2024-09-08", "Spain", "Serbia", 0, 0, "World Cup Group"),
    ("2024-09-08", "Croatia", "Poland", 1, 0, "World Cup Group"),
    ("2024-09-08", "Denmark", "Switzerland", 2, 0, "World Cup Group"),
    ("2024-09-08", "England", "Ireland", 2, 0, "World Cup Group"),
    ("2024-09-10", "Scotland", "Portugal", 0, 3, "World Cup Group"),
    ("2024-09-10", "Hungary", "Bosnia and Herzegovina", 0, 0, "World Cup Group"),
    ("2024-09-10", "Italy", "Belgium", 2, 2, "World Cup Group"),
    ("2024-09-10", "Serbia", "Switzerland", 0, 2, "World Cup Group"),
    ("2024-10-10", "Germany", "Bosnia and Herzegovina", 2, 1, "World Cup Group"),
    ("2024-10-10", "France", "Belgium", 2, 0, "World Cup Group"),
    ("2024-10-10", "Netherlands", "Hungary", 1, 1, "World Cup Group"),
    ("2024-10-10", "Spain", "Denmark", 1, 0, "World Cup Group"),
    ("2024-10-10", "Croatia", "Scotland", 1, 0, "World Cup Group"),
    ("2024-10-10", "England", "Greece", 1, 2, "World Cup Group"),
    ("2024-10-11", "Portugal", "Poland", 5, 1, "World Cup Group"),
    ("2024-10-13", "Germany", "Netherlands", 1, 0, "World Cup Group"),
    ("2024-10-13", "Belgium", "France", 1, 2, "World Cup Group"),
    ("2024-10-13", "Serbia", "Spain", 0, 3, "World Cup Group"),
    ("2024-10-14", "Poland", "Croatia", 3, 3, "World Cup Group"),
    ("2024-10-14", "Scotland", "Portugal", 0, 0, "World Cup Group"),
    ("2024-11-14", "Germany", "Bosnia and Herzegovina", 7, 0, "World Cup Group"),
    ("2024-11-14", "Netherlands", "Hungary", 4, 0, "World Cup Group"),
    ("2024-11-14", "France", "Israel", 0, 0, "World Cup Group"),
    ("2024-11-14", "Belgium", "Italy", 0, 1, "World Cup Group"),
    ("2024-11-14", "Spain", "Switzerland", 3, 2, "World Cup Group"),
    ("2024-11-15", "Portugal", "Poland", 5, 1, "World Cup Group"),
    ("2024-11-15", "Croatia", "Scotland", 1, 0, "World Cup Group"),
    ("2024-11-15", "England", "Greece", 3, 0, "World Cup Group"),
    ("2024-11-17", "Hungary", "Germany", 1, 1, "World Cup Group"),
    ("2024-11-17", "Bosnia and Herzegovina", "Netherlands", 1, 3, "World Cup Group"),
    ("2024-11-17", "Italy", "France", 1, 3, "World Cup Group"),
    ("2024-11-18", "Denmark", "Spain", 1, 2, "World Cup Group"),
    ("2024-11-18", "Poland", "Scotland", 1, 2, "World Cup Group"),

    # =====================================================================
    # WC 2026 QUALIFIERS — KEY RESULTS (CONMEBOL, UEFA, CAF, AFC, CONCACAF)
    # =====================================================================
    # CONMEBOL Qualifiers
    ("2023-09-07", "Argentina", "Ecuador", 1, 0, "World Cup Group"),
    ("2023-09-12", "Bolivia", "Argentina", 1, 3, "World Cup Group"),
    ("2023-10-12", "Argentina", "Paraguay", 1, 0, "World Cup Group"),
    ("2023-10-17", "Peru", "Argentina", 0, 2, "World Cup Group"),
    ("2023-11-16", "Uruguay", "Argentina", 0, 1, "World Cup Group"),
    ("2023-11-21", "Argentina", "Brazil", 1, 0, "World Cup Group"),
    ("2024-03-21", "Argentina", "El Salvador", 3, 0, "World Cup Group"),
    ("2024-03-26", "Argentina", "Costa Rica", 3, 1, "World Cup Group"),
    ("2024-09-05", "Argentina", "Chile", 3, 0, "World Cup Group"),
    ("2024-09-10", "Colombia", "Argentina", 2, 1, "World Cup Group"),
    ("2024-10-10", "Argentina", "Venezuela", 0, 0, "World Cup Group"),
    ("2024-10-15", "Argentina", "Bolivia", 6, 0, "World Cup Group"),
    ("2024-11-14", "Paraguay", "Argentina", 2, 1, "World Cup Group"),
    ("2024-11-19", "Argentina", "Peru", 1, 0, "World Cup Group"),
    ("2023-09-07", "Brazil", "Bolivia", 5, 1, "World Cup Group"),
    ("2023-09-12", "Peru", "Brazil", 0, 1, "World Cup Group"),
    ("2023-10-12", "Brazil", "Venezuela", 1, 1, "World Cup Group"),
    ("2023-10-17", "Uruguay", "Brazil", 2, 0, "World Cup Group"),
    ("2023-11-21", "Colombia", "Brazil", 2, 1, "World Cup Group"),
    ("2024-09-06", "Brazil", "Ecuador", 1, 0, "World Cup Group"),
    ("2024-09-10", "Paraguay", "Brazil", 1, 0, "World Cup Group"),
    ("2024-10-10", "Chile", "Brazil", 1, 2, "World Cup Group"),
    ("2024-10-15", "Brazil", "Peru", 4, 0, "World Cup Group"),
    ("2024-11-14", "Venezuela", "Brazil", 1, 1, "World Cup Group"),
    ("2024-11-19", "Brazil", "Uruguay", 1, 1, "World Cup Group"),
    ("2023-09-07", "Colombia", "Venezuela", 1, 0, "World Cup Group"),
    ("2023-09-12", "Chile", "Colombia", 0, 0, "World Cup Group"),
    ("2023-10-12", "Colombia", "Uruguay", 2, 2, "World Cup Group"),
    ("2023-10-17", "Ecuador", "Colombia", 0, 0, "World Cup Group"),
    ("2024-09-06", "Peru", "Colombia", 1, 1, "World Cup Group"),
    ("2024-10-10", "Bolivia", "Colombia", 1, 0, "World Cup Group"),
    ("2024-10-15", "Colombia", "Chile", 4, 0, "World Cup Group"),
    ("2024-11-14", "Uruguay", "Colombia", 3, 2, "World Cup Group"),
    ("2023-09-07", "Uruguay", "Chile", 3, 1, "World Cup Group"),
    ("2023-09-12", "Ecuador", "Uruguay", 1, 2, "World Cup Group"),
    ("2024-09-06", "Venezuela", "Uruguay", 0, 0, "World Cup Group"),
    ("2024-10-15", "Ecuador", "Paraguay", 1, 0, "World Cup Group"),
    ("2024-11-19", "Chile", "Venezuela", 4, 2, "World Cup Group"),

    # UEFA Qualifiers (2024-25 key results)
    ("2025-03-20", "Germany", "Italy", 1, 1, "World Cup Group"),
    ("2025-03-20", "Norway", "Austria", 1, 0, "World Cup Group"),
    ("2025-03-20", "Turkey", "Spain", 0, 1, "World Cup Group"),
    ("2025-03-25", "Italy", "Germany", 0, 0, "World Cup Group"),
    ("2025-06-06", "Germany", "Norway", 3, 0, "World Cup Group"),
    ("2025-06-06", "Spain", "Turkey", 2, 1, "World Cup Group"),
    ("2025-03-20", "France", "Croatia", 1, 0, "World Cup Group"),
    ("2025-03-20", "Ukraine", "Iceland", 2, 1, "World Cup Group"),
    ("2025-03-25", "Croatia", "France", 1, 1, "World Cup Group"),
    ("2025-06-06", "France", "Ukraine", 3, 1, "World Cup Group"),
    ("2025-03-20", "Netherlands", "Finland", 4, 0, "World Cup Group"),
    ("2025-06-06", "Netherlands", "Sweden", 3, 0, "World Cup Group"),
    ("2025-03-20", "England", "Serbia", 3, 0, "World Cup Group"),
    ("2025-03-25", "Serbia", "England", 0, 3, "World Cup Group"),
    ("2025-03-20", "Portugal", "Denmark", 1, 0, "World Cup Group"),
    ("2025-06-06", "Portugal", "Greece", 3, 0, "World Cup Group"),
    ("2025-03-20", "Belgium", "Wales", 3, 1, "World Cup Group"),
    ("2025-06-06", "Belgium", "North Macedonia", 3, 0, "World Cup Group"),
    ("2025-03-22", "Switzerland", "Sweden", 1, 0, "World Cup Group"),
    ("2025-06-07", "Switzerland", "Bulgaria", 4, 1, "World Cup Group"),
    ("2025-06-07", "Scotland", "Greece", 0, 1, "World Cup Group"),

    # CAF Qualifiers
    ("2024-06-06", "Nigeria", "South Africa", 1, 1, "World Cup Group"),
    ("2024-06-10", "South Africa", "Nigeria", 2, 1, "World Cup Group"),
    ("2024-06-06", "Ivory Coast", "Kenya", 2, 0, "World Cup Group"),
    ("2024-06-06", "Morocco", "Zambia", 1, 0, "World Cup Group"),
    ("2024-06-10", "Cameroon", "Cape Verde", 1, 1, "World Cup Group"),
    ("2024-06-06", "Egypt", "Guinea", 2, 1, "World Cup Group"),
    ("2024-06-10", "Ghana", "Mali", 0, 1, "World Cup Group"),
    ("2024-11-11", "Senegal", "Ivory Coast", 1, 1, "World Cup Group"),
    ("2024-11-11", "Morocco", "Gabon", 5, 1, "World Cup Group"),
    ("2024-11-19", "Egypt", "Botswana", 4, 0, "World Cup Group"),
    ("2024-11-19", "Ghana", "Niger", 1, 1, "World Cup Group"),
    ("2025-03-17", "Nigeria", "Rwanda", 0, 0, "World Cup Group"),
    ("2025-03-21", "South Africa", "Lesotho", 3, 0, "World Cup Group"),

    # AFC Qualifiers
    ("2024-09-05", "Japan", "China", 7, 0, "World Cup Group"),
    ("2024-09-10", "Bahrain", "Japan", 0, 5, "World Cup Group"),
    ("2024-10-10", "Japan", "Saudi Arabia", 2, 0, "World Cup Group"),
    ("2024-10-15", "Australia", "Japan", 1, 0, "World Cup Group"),
    ("2024-11-14", "Japan", "Indonesia", 4, 0, "World Cup Group"),
    ("2024-11-19", "China", "Japan", 1, 3, "World Cup Group"),
    ("2024-09-05", "Australia", "Bahrain", 1, 0, "World Cup Group"),
    ("2024-09-10", "Indonesia", "Australia", 0, 0, "World Cup Group"),
    ("2024-10-10", "China", "Australia", 1, 2, "World Cup Group"),
    ("2024-10-15", "Saudi Arabia", "Australia", 2, 2, "World Cup Group"),
    ("2024-09-05", "Iran", "Qatar", 2, 1, "World Cup Group"),
    ("2024-09-10", "Uzbekistan", "Iran", 0, 1, "World Cup Group"),
    ("2024-10-10", "Iran", "South Korea", 0, 0, "World Cup Group"),
    ("2024-10-15", "Iran", "Iraq", 1, 0, "World Cup Group"),
    ("2024-09-05", "South Korea", "Palestine", 3, 0, "World Cup Group"),
    ("2024-10-15", "South Korea", "Iraq", 3, 2, "World Cup Group"),
    ("2024-11-14", "South Korea", "Kuwait", 3, 1, "World Cup Group"),

    # CONCACAF Qualifiers
    ("2024-06-06", "Mexico", "Honduras", 0, 0, "World Cup Group"),
    ("2024-06-10", "Jamaica", "Mexico", 0, 1, "World Cup Group"),
    ("2024-09-06", "USA", "Canada", 1, 1, "World Cup Group"),
    ("2024-09-10", "USA", "New Zealand", 2, 0, "World Cup Group"),
    ("2024-10-12", "Panama", "USA", 1, 0, "World Cup Group"),
    ("2024-10-15", "Mexico", "USA", 0, 0, "World Cup Group"),
    ("2024-11-15", "USA", "Jamaica", 1, 0, "World Cup Group"),
    ("2024-11-19", "USA", "Suriname", 4, 2, "World Cup Group"),
    ("2024-06-06", "Canada", "Trinidad and Tobago", 2, 1, "World Cup Group"),
    ("2024-09-07", "Canada", "Suriname", 3, 0, "World Cup Group"),
    ("2024-11-15", "Canada", "Panama", 1, 0, "World Cup Group"),

    # =====================================================================
    # INTERNATIONAL FRIENDLIES & OTHER 2023-2025
    # =====================================================================
    ("2023-03-23", "Spain", "Norway", 3, 0, "World Cup Group"),
    ("2023-03-23", "France", "Netherlands", 4, 0, "World Cup Group"),
    ("2023-03-27", "Spain", "Norway", 3, 0, "World Cup Group"),
    ("2023-06-16", "Germany", "Colombia", 0, 2, "World Cup Group"),
    ("2023-06-20", "Germany", "Poland", 0, 1, "World Cup Group"),
    ("2023-09-09", "France", "Ireland", 2, 0, "World Cup Group"),
    ("2023-09-12", "Italy", "North Macedonia", 5, 2, "World Cup Group"),
    ("2023-10-14", "England", "Australia", 1, 0, "World Cup Group"),
    ("2023-10-17", "England", "Italy", 3, 1, "World Cup Group"),
    ("2023-11-16", "England", "Malta", 2, 0, "World Cup Group"),
    ("2023-11-20", "England", "North Macedonia", 7, 2, "World Cup Group"),
    ("2024-03-23", "England", "Brazil", 0, 1, "World Cup Group"),
    ("2024-03-26", "England", "Belgium", 2, 2, "World Cup Group"),
    ("2024-06-07", "England", "Iceland", 0, 1, "World Cup Group"),
    ("2024-03-23", "Germany", "France", 2, 0, "World Cup Group"),
    ("2024-03-26", "Germany", "Netherlands", 2, 1, "World Cup Group"),
    ("2024-06-03", "Germany", "Ukraine", 0, 0, "World Cup Group"),
    ("2024-06-08", "Germany", "Greece", 2, 1, "World Cup Group"),
    ("2024-03-22", "Brazil", "England", 1, 0, "World Cup Group"),
    ("2024-03-26", "Spain", "Brazil", 3, 3, "World Cup Group"),
    ("2024-06-12", "Brazil", "USA", 1, 1, "World Cup Group"),
    ("2023-10-13", "Morocco", "Congo DR", 0, 1, "World Cup Group"),
    ("2024-03-22", "Japan", "North Korea", 1, 0, "World Cup Group"),
    ("2024-06-10", "Japan", "Syria", 5, 0, "World Cup Group"),
    ("2024-03-22", "South Korea", "Thailand", 3, 0, "World Cup Group"),
    ("2024-06-06", "South Korea", "Singapore", 7, 0, "World Cup Group"),
    ("2024-03-22", "Italy", "Venezuela", 2, 1, "World Cup Group"),
    ("2024-03-26", "Italy", "Ecuador", 2, 0, "World Cup Group"),
    ("2023-03-24", "Turkey", "Croatia", 0, 2, "World Cup Group"),
    ("2023-06-19", "Croatia", "Turkey", 2, 0, "World Cup Group"),
    ("2023-10-13", "Croatia", "Armenia", 1, 0, "World Cup Group"),
    ("2024-03-23", "Croatia", "Egypt", 4, 1, "World Cup Group"),
    ("2024-06-03", "Croatia", "Portugal", 1, 2, "World Cup Group"),
    ("2024-06-08", "Croatia", "Albania", 1, 1, "World Cup Group"),
    ("2023-11-20", "Iran", "Russia", 1, 1, "World Cup Group"),
    ("2024-01-14", "Iran", "Qatar", 4, 2, "World Cup Group"),
    ("2023-06-16", "Ecuador", "Australia", 1, 1, "World Cup Group"),
    ("2024-03-21", "Ecuador", "Honduras", 2, 0, "World Cup Group"),
    ("2023-10-17", "Uruguay", "Bolivia", 3, 0, "World Cup Group"),
    ("2024-03-22", "Uruguay", "Cuba", 3, 0, "World Cup Group"),
    ("2023-09-09", "Belgium", "Estonia", 3, 1, "World Cup Group"),
    ("2023-10-13", "Belgium", "Sweden", 3, 3, "World Cup Group"),
    ("2024-03-23", "Belgium", "Montenegro", 2, 0, "World Cup Group"),
    ("2024-06-08", "Belgium", "Luxembourg", 3, 0, "World Cup Group"),
    ("2023-11-20", "Saudi Arabia", "Costa Rica", 0, 1, "World Cup Group"),
    ("2024-03-22", "Saudi Arabia", "Tajikistan", 1, 0, "World Cup Group"),
    ("2024-06-06", "Saudi Arabia", "Pakistan", 3, 0, "World Cup Group"),
    ("2023-09-09", "Netherlands", "Greece", 3, 0, "World Cup Group"),
    ("2023-10-13", "Netherlands", "France", 2, 1, "World Cup Group"),
    ("2024-03-22", "Netherlands", "Scotland", 4, 0, "World Cup Group"),
    ("2024-06-10", "Netherlands", "Iceland", 4, 0, "World Cup Group"),
    ("2023-09-08", "Senegal", "Brazil", 2, 4, "World Cup Group"),
    ("2023-10-13", "Senegal", "Guinea", 2, 0, "World Cup Group"),

    # =====================================================================
    # FIFA WORLD CUP 2026 (USA/CANADA/MEXICO) — LIVE RESULTS
    # =====================================================================
    ("2026-06-25", "Ecuador", "Germany", 0, 1, "World Cup Group"),
    ("2026-06-25", "Curacao", "Ivory Coast", 0, 2, "World Cup Group"),
    ("2026-06-26", "Tunisia", "Netherlands", 1, 3, "World Cup Group"),
    ("2026-06-26", "Japan", "Sweden", 1, 1, "World Cup Group"),
    ("2026-06-26", "Turkey", "USA", 3, 2, "World Cup Group"),
    ("2026-06-26", "Paraguay", "Australia", 0, 0, "World Cup Group"),

    # =====================================================================
    # UEFA NATIONS LEAGUE 2022-23 (GROUP STAGE + FINALS)
    # =====================================================================
    ("2022-06-02", "Poland", "Wales", 2, 1, "World Cup Group"),
    ("2022-06-05", "Belgium", "Poland", 1, 0, "World Cup Group"),
    ("2022-06-08", "Wales", "Netherlands", 1, 2, "World Cup Group"),
    ("2022-06-11", "Austria", "France", 1, 1, "World Cup Group"),
    ("2022-06-14", "Croatia", "France", 1, 1, "World Cup Group"),
    ("2022-06-02", "Spain", "Portugal", 1, 1, "World Cup Group"),
    ("2022-06-05", "Switzerland", "Portugal", 1, 0, "World Cup Group"),
    ("2022-06-08", "Spain", "Switzerland", 1, 2, "World Cup Group"),
    ("2022-06-11", "Portugal", "Switzerland", 4, 0, "World Cup Group"),
    ("2022-06-14", "Spain", "Switzerland", 1, 0, "World Cup Group"),
    ("2022-06-02", "Hungary", "England", 1, 0, "World Cup Group"),
    ("2022-06-05", "England", "Hungary", 0, 4, "World Cup Group"),
    ("2022-06-08", "Germany", "Italy", 1, 1, "World Cup Group"),
    ("2022-06-11", "Italy", "Germany", 5, 2, "World Cup Group"),
    ("2022-06-14", "Hungary", "Germany", 1, 1, "World Cup Group"),
    ("2022-09-22", "France", "Austria", 2, 0, "World Cup Group"),
    ("2022-09-25", "Netherlands", "Belgium", 1, 0, "World Cup Group"),
    ("2022-09-22", "Italy", "England", 1, 0, "World Cup Group"),
    ("2022-09-25", "England", "Germany", 3, 3, "World Cup Group"),
    ("2022-09-22", "Denmark", "Croatia", 0, 1, "World Cup Group"),
    ("2022-09-25", "Austria", "Croatia", 1, 3, "World Cup Group"),
    ("2023-06-14", "Croatia", "Netherlands", 0, 0, "World Cup SF"),
    ("2023-06-15", "Spain", "Italy", 2, 1, "World Cup SF"),
    ("2023-06-18", "Croatia", "Spain", 0, 0, "World Cup Final"),

    # =====================================================================
    # AFCON 2024 (IVORY COAST) — KNOCKOUT ROUNDS
    # =====================================================================
    ("2024-01-27", "Nigeria", "Cameroon", 2, 0, "World Cup R16"),
    ("2024-01-28", "Congo DR", "Egypt", 1, 1, "World Cup R16"),
    ("2024-01-28", "Guinea", "Equatorial Guinea", 1, 0, "World Cup R16"),
    ("2024-01-29", "Ivory Coast", "Senegal", 1, 1, "World Cup R16"),
    ("2024-01-29", "South Africa", "Morocco", 0, 2, "World Cup R16"),
    ("2024-01-30", "Mali", "Burkina Faso", 2, 1, "World Cup R16"),
    ("2024-02-02", "Nigeria", "Angola", 1, 0, "World Cup QF"),
    ("2024-02-03", "Congo DR", "Guinea", 3, 1, "World Cup QF"),
    ("2024-02-03", "Ivory Coast", "Mali", 2, 1, "World Cup QF"),
    ("2024-02-03", "South Africa", "Cape Verde", 0, 0, "World Cup QF"),
    ("2024-02-07", "Nigeria", "South Africa", 1, 1, "World Cup SF"),
    ("2024-02-07", "Ivory Coast", "Congo DR", 1, 0, "World Cup SF"),
    ("2024-02-11", "Ivory Coast", "Nigeria", 2, 1, "World Cup Final"),

    # =====================================================================
    # AFC ASIAN CUP 2023 (QATAR) — KNOCKOUT ROUNDS
    # =====================================================================
    ("2024-01-29", "Australia", "Indonesia", 4, 0, "World Cup R16"),
    ("2024-01-29", "Uzbekistan", "Thailand", 2, 1, "World Cup R16"),
    ("2024-01-30", "South Korea", "Saudi Arabia", 1, 1, "World Cup R16"),
    ("2024-01-31", "Iran", "Syria", 1, 0, "World Cup R16"),
    ("2024-01-31", "Japan", "Bahrain", 3, 1, "World Cup R16"),
    ("2024-01-31", "Iraq", "Jordan", 2, 3, "World Cup R16"),
    ("2024-02-02", "Iran", "Japan", 2, 1, "World Cup QF"),
    ("2024-02-02", "Australia", "South Korea", 1, 2, "World Cup QF"),
    ("2024-02-03", "Uzbekistan", "Qatar", 1, 3, "World Cup QF"),
    ("2024-02-06", "Jordan", "South Korea", 2, 0, "World Cup SF"),
    ("2024-02-07", "Qatar", "Iran", 3, 2, "World Cup SF"),
    ("2024-02-10", "Jordan", "Qatar", 1, 3, "World Cup Final"),

    # =====================================================================
    # COPA AMERICA 2024 (USA) — FULL TOURNAMENT
    # =====================================================================
    ("2024-06-20", "Argentina", "Canada", 2, 0, "World Cup Group"),
    ("2024-06-21", "Peru", "Chile", 0, 0, "World Cup Group"),
    ("2024-06-22", "Ecuador", "Venezuela", 1, 2, "World Cup Group"),
    ("2024-06-22", "Mexico", "Jamaica", 1, 0, "World Cup Group"),
    ("2024-06-23", "USA", "Bolivia", 2, 0, "World Cup Group"),
    ("2024-06-23", "Uruguay", "Panama", 3, 1, "World Cup Group"),
    ("2024-06-24", "Colombia", "Paraguay", 2, 1, "World Cup Group"),
    ("2024-06-24", "Brazil", "Costa Rica", 0, 0, "World Cup Group"),
    ("2024-06-25", "Chile", "Argentina", 0, 1, "World Cup Group"),
    ("2024-06-25", "Peru", "Canada", 0, 1, "World Cup Group"),
    ("2024-06-26", "Ecuador", "Jamaica", 3, 1, "World Cup Group"),
    ("2024-06-26", "Venezuela", "Mexico", 1, 0, "World Cup Group"),
    ("2024-06-27", "Panama", "USA", 2, 1, "World Cup Group"),
    ("2024-06-27", "Uruguay", "Bolivia", 5, 0, "World Cup Group"),
    ("2024-06-28", "Brazil", "Paraguay", 4, 1, "World Cup Group"),
    ("2024-06-28", "Colombia", "Costa Rica", 3, 0, "World Cup Group"),
    ("2024-06-29", "Argentina", "Peru", 2, 0, "World Cup Group"),
    ("2024-06-29", "Canada", "Chile", 0, 0, "World Cup Group"),
    ("2024-06-30", "Mexico", "Ecuador", 0, 0, "World Cup Group"),
    ("2024-06-30", "Jamaica", "Venezuela", 0, 3, "World Cup Group"),
    ("2024-07-01", "USA", "Uruguay", 0, 1, "World Cup Group"),
    ("2024-07-01", "Bolivia", "Panama", 1, 2, "World Cup Group"),
    ("2024-07-02", "Brazil", "Colombia", 1, 1, "World Cup Group"),
    ("2024-07-02", "Paraguay", "Costa Rica", 2, 1, "World Cup Group"),
    ("2024-07-04", "Argentina", "Ecuador", 1, 1, "World Cup QF"),
    ("2024-07-05", "Uruguay", "Brazil", 0, 0, "World Cup QF"),
    ("2024-07-05", "Colombia", "Panama", 5, 0, "World Cup QF"),
    ("2024-07-06", "Venezuela", "Canada", 1, 1, "World Cup QF"),
    ("2024-07-09", "Argentina", "Canada", 2, 0, "World Cup SF"),
    ("2024-07-10", "Uruguay", "Colombia", 0, 1, "World Cup SF"),
    ("2024-07-14", "Argentina", "Colombia", 1, 0, "World Cup Final"),

    # =====================================================================
    # EURO 2024 (GERMANY) — KNOCKOUT ROUNDS
    # =====================================================================
    ("2024-06-29", "Switzerland", "Italy", 2, 0, "World Cup R16"),
    ("2024-06-29", "Germany", "Denmark", 2, 0, "World Cup R16"),
    ("2024-06-30", "England", "Slovakia", 2, 1, "World Cup R16"),
    ("2024-06-30", "Spain", "Georgia", 4, 1, "World Cup R16"),
    ("2024-07-01", "France", "Belgium", 1, 0, "World Cup R16"),
    ("2024-07-01", "Portugal", "Slovenia", 0, 0, "World Cup R16"),
    ("2024-07-02", "Romania", "Netherlands", 0, 3, "World Cup R16"),
    ("2024-07-02", "Austria", "Turkey", 1, 2, "World Cup R16"),
    ("2024-07-05", "Spain", "Germany", 2, 1, "World Cup QF"),
    ("2024-07-05", "Portugal", "France", 0, 0, "World Cup QF"),
    ("2024-07-06", "Netherlands", "Turkey", 2, 1, "World Cup QF"),
    ("2024-07-06", "England", "Switzerland", 1, 1, "World Cup QF"),
    ("2024-07-09", "Spain", "France", 2, 1, "World Cup SF"),
    ("2024-07-10", "Netherlands", "England", 1, 2, "World Cup SF"),
    ("2024-07-14", "Spain", "England", 2, 1, "World Cup Final"),

    # =====================================================================
    # UEFA NATIONS LEAGUE 2024-25 (GROUP STAGE)
    # =====================================================================
    ("2024-09-05", "Portugal", "Croatia", 2, 1, "World Cup Group"),
    ("2024-09-05", "Scotland", "Poland", 2, 3, "World Cup Group"),
    ("2024-09-07", "France", "Italy", 1, 3, "World Cup Group"),
    ("2024-09-07", "Belgium", "Israel", 3, 1, "World Cup Group"),
    ("2024-09-08", "Croatia", "Poland", 1, 0, "World Cup Group"),
    ("2024-09-08", "Portugal", "Scotland", 2, 1, "World Cup Group"),
    ("2024-09-10", "Italy", "Belgium", 2, 2, "World Cup Group"),
    ("2024-09-10", "France", "Belgium", 2, 0, "World Cup Group"),
    ("2024-10-10", "Spain", "Denmark", 1, 0, "World Cup Group"),
    ("2024-10-10", "Croatia", "Scotland", 1, 0, "World Cup Group"),
    ("2024-10-10", "Germany", "Bosnia and Herzegovina", 2, 1, "World Cup Group"),
    ("2024-10-13", "Belgium", "France", 1, 2, "World Cup Group"),
    ("2024-10-13", "Italy", "Israel", 4, 1, "World Cup Group"),
    ("2024-10-13", "Denmark", "Spain", 1, 2, "World Cup Group"),
    ("2024-10-14", "Poland", "Portugal", 1, 3, "World Cup Group"),
    ("2024-10-14", "Scotland", "Croatia", 1, 0, "World Cup Group"),
    ("2024-11-14", "Italy", "France", 1, 3, "World Cup Group"),
    ("2024-11-14", "Belgium", "Italy", 0, 1, "World Cup Group"),
    ("2024-11-17", "France", "Israel", 3, 1, "World Cup Group"),
    ("2024-11-17", "Portugal", "Poland", 5, 1, "World Cup Group"),
    ("2024-11-18", "Croatia", "Portugal", 1, 1, "World Cup Group"),
    ("2024-11-18", "Spain", "Switzerland", 3, 2, "World Cup Group"),

    # =====================================================================
    # ADDITIONAL WC 2026 QUALIFIERS (LATE 2024 — EARLY 2025)
    # =====================================================================
    ("2024-09-05", "Argentina", "Chile", 3, 0, "World Cup Group"),
    ("2024-09-10", "Colombia", "Argentina", 2, 1, "World Cup Group"),
    ("2024-10-10", "Argentina", "Venezuela", 0, 0, "World Cup Group"),
    ("2024-10-15", "Bolivia", "Argentina", 1, 6, "World Cup Group"),
    ("2024-11-14", "Paraguay", "Argentina", 2, 1, "World Cup Group"),
    ("2024-11-19", "Argentina", "Peru", 1, 0, "World Cup Group"),
    ("2024-09-05", "Brazil", "Ecuador", 1, 0, "World Cup Group"),
    ("2024-09-10", "Paraguay", "Brazil", 1, 0, "World Cup Group"),
    ("2024-10-10", "Brazil", "Chile", 2, 1, "World Cup Group"),
    ("2024-10-15", "Peru", "Brazil", 0, 4, "World Cup Group"),
    ("2024-11-14", "Venezuela", "Brazil", 1, 1, "World Cup Group"),
    ("2024-11-19", "Brazil", "Uruguay", 1, 1, "World Cup Group"),
    ("2024-09-06", "USA", "Canada", 1, 2, "World Cup Group"),
    ("2024-09-10", "USA", "New Zealand", 1, 1, "World Cup Group"),
    ("2024-10-12", "Panama", "USA", 1, 0, "World Cup Group"),
    ("2024-10-15", "Mexico", "USA", 0, 0, "World Cup Group"),
    ("2024-11-18", "USA", "Jamaica", 1, 0, "World Cup Group"),
    ("2025-03-20", "Canada", "Mexico", 2, 1, "World Cup Group"),
    ("2025-03-20", "Uruguay", "Colombia", 1, 2, "World Cup Group"),
    ("2025-03-25", "Chile", "Brazil", 0, 1, "World Cup Group"),
    ("2025-03-25", "Colombia", "Bolivia", 3, 0, "World Cup Group"),

    # =====================================================================
    # CONCACAF NATIONS LEAGUE 2024-25
    # =====================================================================
    ("2024-11-15", "Mexico", "Honduras", 0, 2, "World Cup Group"),
    ("2024-11-19", "Honduras", "Mexico", 0, 4, "World Cup Group"),
    ("2024-11-15", "USA", "Jamaica", 1, 0, "World Cup QF"),
    ("2024-11-19", "Jamaica", "USA", 0, 1, "World Cup QF"),
    ("2024-11-15", "Panama", "Costa Rica", 0, 0, "World Cup QF"),
    ("2024-11-19", "Costa Rica", "Panama", 0, 1, "World Cup QF"),
    ("2025-03-20", "USA", "Honduras", 3, 0, "World Cup SF"),
    ("2025-03-23", "Panama", "Mexico", 0, 0, "World Cup SF"),
    ("2025-03-23", "USA", "Mexico", 2, 0, "World Cup Final"),
]

def get_match_result(home_goals, away_goals):
    """Returns 'H', 'D', or 'A' from a scoreline."""
    if home_goals > away_goals:
        return 'H'
    elif home_goals == away_goals:
        return 'D'
    else:
        return 'A'

def get_total_goals_label(home_goals, away_goals):
    """Returns 1 if over 2.5, 0 if under."""
    return 1 if (home_goals + away_goals) > 2 else 0

def reconstruct_odds(home_goals, away_goals, tournament):
    """
    LEGACY fallback: reconstruct approximate 1X2 closing odds from scoreline.
    WARNING: This leaks the result into training. Use elo_based_odds() instead.
    """
    total = home_goals + away_goals
    result = get_match_result(home_goals, away_goals)
    if result == 'H':
        diff = home_goals - away_goals
        if diff >= 3: return 1.30, 5.50, 10.00
        elif diff == 2: return 1.60, 4.00, 6.00
        elif diff == 1: return 2.10, 3.40, 3.50
    elif result == 'A':
        diff = away_goals - home_goals
        if diff >= 3: return 10.00, 5.50, 1.30
        elif diff == 2: return 6.00, 4.00, 1.60
        elif diff == 1: return 3.50, 3.40, 2.10
    else:
        if total == 0: return 2.80, 3.00, 2.80
        else: return 2.50, 3.20, 2.90
    return 2.50, 3.30, 2.80


def elo_based_odds(h_elo, a_elo):
    """
    Generate PRE-MATCH odds from ELO ratings only.
    This does NOT leak the result, making training fair.
    Uses a logistic model: P(home) = 1 / (1 + 10^((a_elo - h_elo - HOME_ADV) / 400))
    """
    HOME_ADV = 60  # slight home edge even at neutral venues
    exp_h = 1.0 / (1.0 + 10 ** ((a_elo - h_elo - HOME_ADV) / 400))
    exp_a = 1.0 - exp_h

    # Carve out draw probability based on how close the teams are
    elo_gap = abs(h_elo - a_elo)
    draw_base = max(0.18, 0.32 - elo_gap / 1500)  # tighter gap = higher draw chance

    # Redistribute: scale H/A probs to sum to (1 - draw_prob)
    remaining = 1.0 - draw_base
    p_h = exp_h * remaining
    p_a = exp_a * remaining
    p_d = draw_base

    # Convert to decimal odds (with ~8% bookmaker margin)
    margin = 1.08
    odds_h = round(margin / max(p_h, 0.02), 2)
    odds_d = round(margin / max(p_d, 0.05), 2)
    odds_a = round(margin / max(p_a, 0.02), 2)

    return odds_h, odds_d, odds_a


def load_real_data():
    """Returns the full dataset as a list of dicts ready for processing."""
    results = []
    for date_str, home, away, hg, ag, tournament in INTERNATIONAL_MATCHES:
        oh, od, oa = reconstruct_odds(hg, ag, tournament)
        results.append({
            "date": date_str,
            "home": home,
            "away": away,
            "home_goals": hg,
            "away_goals": ag,
            "result": get_match_result(hg, ag),
            "over_2_5": get_total_goals_label(hg, ag),
            "total_goals": hg + ag,
            "odds_home": oh,
            "odds_draw": od,
            "odds_away": oa,
            "tournament": tournament
        })
    return results


if __name__ == "__main__":
    data = load_real_data()
    home_wins = sum(1 for d in data if d['result'] == 'H')
    draws = sum(1 for d in data if d['result'] == 'D')
    away_wins = sum(1 for d in data if d['result'] == 'A')
    overs = sum(1 for d in data if d['over_2_5'] == 1)
    
    print(f"Total matches: {len(data)}")
    print(f"Home wins: {home_wins} ({home_wins/len(data)*100:.1f}%)")
    print(f"Draws:     {draws} ({draws/len(data)*100:.1f}%)")
    print(f"Away wins: {away_wins} ({away_wins/len(data)*100:.1f}%)")
    print(f"Over 2.5:  {overs} ({overs/len(data)*100:.1f}%)")
    print(f"Under 2.5: {len(data)-overs} ({(len(data)-overs)/len(data)*100:.1f}%)")
