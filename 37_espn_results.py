"""
AstroPitch - ESPN RESULTS SUPPLEMENT  (fills the gap until football-data catches up)
============================================================================
football-data.co.uk is the source of record for club_raw.csv: it carries the
closing odds, referees and full match stats the trainer and the track record
use. But it publishes in batches, a few days behind. This script fills that
gap from ESPN's public scoreboard, which posts results within minutes.

  - Only COMPLETED matches in our 12 divisions, from the last LOOKBACK_DAYS.
  - ESPN names are mapped onto football-data's names ("Nottingham Forest" ->
    "Nott'm Forest") against the clubs actually playing in that division this
    season. A name that does not map to exactly one club is SKIPPED and
    reported, never guessed: a wrong match would corrupt two clubs' ratings.
  - Rows are tagged Source="espn". When football-data later publishes the same
    match, 22_update_club_data.py replaces the ESPN row with its richer one.
  - Odds are left blank. Nothing that grades CLV uses an ESPN row as a price.

Run:  python 37_espn_results.py          (22_update_club_data.py also calls it)
============================================================================
"""
import concurrent.futures as cf
import datetime as dt
import json
import re
import sys
import unicodedata
import urllib.request

import pandas as pd

CLUB_CSV = "club_raw.csv"
LOOKBACK_DAYS = 21
URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={d:%Y%m%d}"
LEAGUES = {"E0": "eng.1", "E1": "eng.2", "SP1": "esp.1", "I1": "ita.1", "D1": "ger.1",
           "F1": "fra.1", "N1": "ned.1", "B1": "bel.1", "P1": "por.1", "SC0": "sco.1",
           "T1": "tur.1", "G1": "gre.1"}

# ESPN names whose football-data spelling no generic rule recovers.
ALIAS = {
    "Nottingham Forest": "Nott'm Forest", "Manchester United": "Man United",
    "Manchester City": "Man City", "Wolverhampton Wanderers": "Wolves",
    "Sheffield Wednesday": "Sheffield Weds", "Queens Park Rangers": "QPR",
    "Atlético Madrid": "Ath Madrid", "Athletic Club": "Ath Bilbao",
    "Real Sociedad": "Sociedad", "Celta Vigo": "Celta", "Real Betis": "Betis",
    "Rayo Vallecano": "Vallecano", "Espanyol": "Espanol", "Deportivo La Coruña": "La Coruna",
    "Racing Santander": "Santander", "Internazionale": "Inter", "AC Milan": "Milan",
    "Bayern Munich": "Bayern Munich", "Borussia Mönchengladbach": "M'gladbach",
    "Borussia Dortmund": "Dortmund", "Bayer Leverkusen": "Leverkusen",
    "1. FC Köln": "FC Koln", "Eintracht Frankfurt": "Ein Frankfurt",
    "Paris Saint-Germain": "Paris SG", "PSV Eindhoven": "PSV Eindhoven",
    "Sporting CP": "Sp Lisbon", "SC Braga": "Sp Braga", "Vitória de Guimarães": "Guimaraes",
    # verified against football-data's 2026-27 club names, 11 Oct 2026
    "Deportivo": "La Coruna", "Fortuna Sittard": "For Sittard", "Sint-Truidense": "St Truiden",
    "Amed SFK": "Amedspor", "AEK Athens": "AEK", "Levadiakos": "Levadeiakos",
    "Olympiacos": "Olympiakos",
}
_DROP = {"fc", "afc", "cf", "sc", "ac", "as", "ssc", "us", "cd", "ud", "sd", "rc", "rcd",
         "ca", "cs", "sv", "vfb", "vfl", "tsg", "fsv", "bsc", "sk", "fk", "kv", "krc",
         "city", "united", "town", "hotspur", "albion", "athletic", "county", "rovers",
         "wanderers", "calcio", "club", "de", "del", "la", "le", "1", "04", "05", "1899",
         "1846", "1909", "1913", "1907"}


def _fold(s):
    s = str(s).translate(str.maketrans({"æ": "ae", "ø": "o", "ß": "ss", "ł": "l"}))
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def _key(s):
    return re.sub(r"[^a-z0-9]", "", _fold(s))


def _core(s):
    toks = [t for t in re.split(r"[^a-z0-9]+", _fold(s)) if t]
    return "".join(t for t in toks if t not in _DROP) or "".join(toks)


def map_name(espn_names, candidates):
    """The one football-data club these ESPN names refer to, or None.
    `espn_names` = (displayName, shortDisplayName, ...); `candidates` = the
    clubs football-data has in this division this season."""
    cands = list(candidates)
    for n in espn_names:
        if n in ALIAS and ALIAS[n] in cands:
            return ALIAS[n]
    for keyf in (_key, _core):
        for n in espn_names:
            hits = [c for c in cands if keyf(c) == keyf(n)]
            if len(hits) == 1:
                return hits[0]
    # last resort: one candidate's core is contained in the ESPN core, uniquely
    for n in espn_names:
        cn = _core(n)
        hits = [c for c in cands if len(_core(c)) >= 4 and (_core(c) in cn or cn in _core(c))]
        if len(hits) == 1:
            return hits[0]
    return None


def _stat(team, name):
    for s in team.get("statistics", []):
        if s.get("name") == name:
            try:
                return float(s.get("displayValue"))
            except (TypeError, ValueError):
                return None
    return None


def fetch(div, slug, day):
    req = urllib.request.Request(URL.format(slug=slug, d=day), headers={"User-Agent": "Mozilla/5.0"})
    out = []
    for e in json.load(urllib.request.urlopen(req, timeout=30)).get("events", []):
        c = e["competitions"][0]
        if not c["status"]["type"].get("completed"):
            continue
        side = {t["homeAway"]: t for t in c["competitors"]}
        if set(side) != {"home", "away"}:
            continue
        out.append(dict(div=div, date=e["date"][:10], time=e["date"][11:16], side=side))
    return out


def season_clubs(raw):
    d = pd.to_datetime(raw["Date"], dayfirst=True, errors="coerce")
    start = pd.Timestamp(dt.date.today().year if dt.date.today().month >= 7
                         else dt.date.today().year - 1, 7, 1)
    cur = raw[d >= start]
    return {div: set(g["HomeTeam"]) | set(g["AwayTeam"]) for div, g in cur.groupby("Div")}


def collect(raw, days=LOOKBACK_DAYS):
    """(new rows, skipped descriptions) for completed ESPN matches not yet in raw."""
    clubs = season_clubs(raw)
    d = pd.to_datetime(raw["Date"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")
    have = set(raw["Div"].astype(str) + "|" + d + "|" + raw["HomeTeam"].astype(str)
               + "|" + raw["AwayTeam"].astype(str))
    today = dt.date.today()
    jobs = [(div, slug, today - dt.timedelta(days=k))
            for div, slug in LEAGUES.items() for k in range(days + 1)]
    events = []
    with cf.ThreadPoolExecutor(8) as ex:
        for got in ex.map(lambda j: fetch(*j), jobs):
            events.extend(got)
    rows, skipped = [], []
    for ev in events:
        div, side = ev["div"], ev["side"]
        names = {}
        for ha in ("home", "away"):
            t = side[ha]["team"]
            names[ha] = map_name([t.get("displayName"), t.get("shortDisplayName"), t.get("name")],
                                 clubs.get(div, ()))
        if not all(names.values()):
            skipped.append(f"{div} {ev['date']} {side['home']['team']['displayName']} v "
                           f"{side['away']['team']['displayName']} (unmapped: "
                           f"{', '.join(side[h]['team']['displayName'] for h in names if not names[h])})")
            continue
        key = f"{div}|{ev['date']}|{names['home']}|{names['away']}"
        if key in have:
            continue
        have.add(key)
        h, a = side["home"], side["away"]
        hg, ag = int(h["score"]), int(a["score"])
        rows.append({"Div": div, "Date": dt.date.fromisoformat(ev["date"]).strftime("%d/%m/%Y"),
                     "Time": ev["time"], "HomeTeam": names["home"], "AwayTeam": names["away"],
                     "FTHG": hg, "FTAG": ag, "FTR": "H" if hg > ag else ("A" if ag > hg else "D"),
                     "HS": _stat(h, "totalShots"), "AS": _stat(a, "totalShots"),
                     "HST": _stat(h, "shotsOnTarget"), "AST": _stat(a, "shotsOnTarget"),
                     "HC": _stat(h, "wonCorners"), "AC": _stat(a, "wonCorners"),
                     "HF": _stat(h, "foulsCommitted"), "AF": _stat(a, "foulsCommitted"),
                     "Source": "espn"})
    return rows, skipped


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raw = pd.read_csv(CLUB_CSV, encoding="latin-1", low_memory=False)
    rows, skipped = collect(raw)
    for s in skipped:
        print(f"  [skip] {s}")
    if rows:
        new = pd.DataFrame(rows)
        by = new.groupby("Div").size().to_dict()
        out = pd.concat([raw, new], ignore_index=True)
        out.to_csv(CLUB_CSV, index=False, encoding="latin-1", errors="replace")
        print(f"  ESPN: added {len(rows)} result(s) not yet on football-data {by}")
    else:
        print("  ESPN: nothing to add (football-data is up to date)")
    return rows, skipped


if __name__ == "__main__":
    main()
