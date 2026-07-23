"""
AstroPitch - DAILY SLATE  (today's free public predictions)
============================================================================
Builds today's prediction slate for the site. Right now the domestic leagues
are between seasons, but UEFA qualifying is in full swing - so this pulls the
live European fixture list and rates every match we can.

  fixtures : TheSportsDB (free)  - Champions / Europa / Conference League
  ratings  : our core engine where both clubs are in the 12 covered leagues,
             otherwise the clubelo-powered European predictor (27_euro_predict)

Team names differ between sources, so names are resolved against clubelo by
trying: alias -> concatenated -> spaced -> de-prefixed -> first token.
(clubelo uses concatenated names: "StGallen", "HBTorshavn", "ManCity".)

Writes today_slate.json, which 26_build_site.py renders into docs/today.html.
Run:  python 30_daily_slate.py [YYYY-MM-DD]
============================================================================
"""
import json
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import datetime as dt
import importlib.util

_es = importlib.util.spec_from_file_location("euro_predict", "27_euro_predict.py")
euro = importlib.util.module_from_spec(_es); _es.loader.exec_module(euro)
from cosmic_reading import cosmic_reading           # noqa: E402

SPORTSDB = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={d}&l={lg}"
COMPS = {4480: "Champions League", 4481: "Europa League", 5071: "Conference League"}
OUT = "today_slate.json"

# clubs whose common name differs from clubelo's filing name
ALIAS = {
    "FCSB": "Steaua", "Steaua Bucuresti": "Steaua",
    "Sporting CP": "Sporting", "Sporting Lisbon": "Sporting",
    "Inter Milan": "Inter", "Internazionale": "Inter",
    "Bayern Munchen": "Bayern", "Bayern Munich": "Bayern",
    "Paris Saint-Germain": "Paris SG", "Man Utd": "Man United",
    "Red Star Belgrade": "Crvena Zvezda", "Young Boys": "YoungBoys",
}
STRIP = ("fc ", " fc", "sk ", "fk ", "sc ", "cf ", "ac ", "as ", "nk ", "hnk ",
         "cd ", "ca ", "ss ", "us ", "if ", " if")


def _ascii(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def candidates(name):
    """Ordered clubelo name guesses for a fixture-source team name."""
    out, seen = [], set()

    def add(v):
        v = v.strip()
        if v and v not in seen:
            seen.add(v); out.append(v)

    if name in ALIAS:
        add(ALIAS[name].replace(" ", "")); add(ALIAS[name])
    base = _ascii(name).replace(".", "").replace("'", "").strip()
    add(base.replace(" ", ""))                      # clubelo's usual form
    add(base)
    low = " " + base.lower() + " "
    trimmed = base
    for p in STRIP:                                 # drop club-type tokens
        if low.startswith(" " + p.strip() + " ") or low.endswith(" " + p.strip() + " "):
            trimmed = " ".join(t for t in base.split()
                               if t.lower() != p.strip().lower())
    add(trimmed.replace(" ", "")); add(trimmed)
    if " " in base:
        add(base.split()[0])
    return out


_resolved = {}


def resolve(name, date):
    """Return (clubelo_name, elo) or (None, None)."""
    if name in _resolved:
        return _resolved[name]
    for cand in candidates(name):
        try:
            elo = euro.fetch_elo(cand, date)
            _resolved[name] = (cand, elo)
            return _resolved[name]
        except Exception:
            continue
    _resolved[name] = (None, None)
    return _resolved[name]


def fetch_fixtures(date):
    games = []
    for lg, label in COMPS.items():
        try:
            req = urllib.request.Request(SPORTSDB.format(d=date, lg=lg),
                                         headers={"User-Agent": "Mozilla/5.0"})
            data = json.load(urllib.request.urlopen(req, timeout=45))
        except Exception as e:
            print(f"  [skip] {label}: {e}")
            continue
        for e in (data.get("events") or []):
            ts = e.get("strTimestamp") or ""
            games.append(dict(comp=label, kickoff=ts[11:16] if len(ts) > 15 else "",
                              ts=ts, home=e.get("strHomeTeam", "").strip(),
                              away=e.get("strAwayTeam", "").strip()))
        time.sleep(1)
    games.sort(key=lambda g: g["ts"])
    return games


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
    print("=" * 70)
    print(f" ASTROPITCH - DAILY SLATE for {date}")
    print("=" * 70)
    fixtures = fetch_fixtures(date)
    print(f"\n{len(fixtures)} fixture(s) found")

    out, skipped = [], []
    for g in fixtures:
        hn, he = resolve(g["home"], date)
        an, ae = resolve(g["away"], date)
        if not hn or not an:
            miss = g["home"] if not hn else g["away"]
            skipped.append(f"{g['home']} v {g['away']} (no rating for {miss})")
            continue
        try:
            p = euro.predict(hn, an, date, verbose=False)
        except Exception as e:
            skipped.append(f"{g['home']} v {g['away']} ({e})")
            continue
        cr = cosmic_reading(g["home"], g["away"], dt.date.fromisoformat(date))
        pk = ["HOME", "DRAW", "AWAY"][int(max(range(3), key=lambda i: p["one_x_two"][i]))]
        out.append(dict(
            comp=g["comp"], kickoff=g["kickoff"], home=g["home"], away=g["away"],
            home_elo=p["elo_home"], away_elo=p["elo_away"],
            probs=[round(v, 3) for v in p["one_x_two"]],
            pick=pk, over25=p["over25"], top_score=p["top_scores"][0]["score"],
            cosmic=cr["headline"],
        ))
        print(f"  {g['kickoff']}  {g['home'][:20]:<20s} v {g['away'][:20]:<20s} "
              f"{p['one_x_two'][0]*100:3.0f}/{p['one_x_two'][1]*100:3.0f}/{p['one_x_two'][2]*100:3.0f}  -> {pk}")

    for s in skipped:
        print(f"  [unrated] {s}")

    payload = dict(date=date,
                   generated_at=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                   n=len(out), matches=out, unrated=len(skipped))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    print(f"\nWrote {OUT}: {len(out)} rated, {len(skipped)} unrated")


if __name__ == "__main__":
    main()
