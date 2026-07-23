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
import os
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
    # names clubelo files differently (found by probing its API)
    "U Cluj": "UniversitateaCluj", "Universitatea Cluj": "UniversitateaCluj",
    "Zalgiris": "ZalgirisVilnius", "Zalgiris Vilnius": "ZalgirisVilnius",
    "Polissya": "PolissyaZhytomyr", "Paks": "Paksi", "Paksi SE": "Paksi",
    "GKS Katowice": "Katowice", "NSI Runavik": "Runavik",
    "Ilves": "IlvesTampere", "Ilves Tampere": "IlvesTampere",
    "Copenhagen": "FCKobenhavn", "FC Copenhagen": "FCKobenhavn",
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


def dedup_key(name):
    """Normalised name so 'Beşiktaş' and 'Besiktas', or 'St. Gallen' and
    'St Gallen', collapse to one fixture instead of being published twice."""
    n = _ascii(name).lower().replace(".", "").replace("'", "")
    drop = {"fc", "sk", "fk", "sc", "cf", "ac", "as", "nk", "hnk", "if",
            "cd", "ca", "ss", "us", "se", "kf", "ks", "msk", "pfc", "afc"}
    return "".join(t for t in n.split() if t not in drop)


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
            games.append(dict(id=str(e.get("idEvent") or ""), comp=label,
                              kickoff=ts[11:16] if len(ts) > 15 else "", ts=ts,
                              home=e.get("strHomeTeam", "").strip(),
                              away=e.get("strAwayTeam", "").strip()))
        time.sleep(1)
    games.sort(key=lambda g: g["ts"])
    return games


PENDING = "uefa_pending.csv"
MANUAL = "fixtures_manual.csv"


def manual_fixtures(date):
    """Fixtures pasted in by hand (with odds). The free feed truncates to ~3 per
    competition per day, so this is how a full matchday gets covered."""
    if not os.path.exists(MANUAL):
        return []
    import pandas as pd
    m = pd.read_csv(MANUAL)
    m = m[m["date"].astype(str) == date]
    out = []
    for r in m.itertuples(index=False):
        odds = None
        if not pd.isna(getattr(r, "oH", None)):
            odds = (float(r.oH), float(r.oD), float(r.oA))
        out.append(dict(id=f"m-{date}-{r.home}-{r.away}".replace(" ", ""),
                        comp=r.comp, kickoff=str(r.kickoff),
                        ts=f"{date}T{r.kickoff}:00",
                        home=str(r.home).strip(), away=str(r.away).strip(),
                        odds=odds))
    return out


def _log_pending(matches, date):
    """Freeze today's predictions (pre-kickoff) so 31_uefa_grade.py can settle
    them once results land. Keyed on the source event id; first write wins, so a
    re-run later in the day can never overwrite the original call."""
    if not matches:
        return
    import pandas as pd
    rows = [dict(id=m["id"], date=date, comp=m["comp"], home=m["home"], away=m["away"],
                 pH=m["probs"][0], pD=m["probs"][1], pA=m["probs"][2], pick=m["pick"],
                 p_over=m["over25"], score_pick=m["top_score"],
                 logged_at=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"))
            for m in matches if m["id"]]
    new = pd.DataFrame(rows)
    if os.path.exists(PENDING):
        old = pd.read_csv(PENDING, dtype={"id": str})
        new = pd.concat([old, new], ignore_index=True)
    new = new.drop_duplicates(subset=["id"], keep="first")
    new.to_csv(PENDING, index=False)
    print(f"  frozen -> {PENDING} ({len(new)} pending)")


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
    print("=" * 70)
    print(f" ASTROPITCH - DAILY SLATE for {date}")
    print("=" * 70)
    fixtures = fetch_fixtures(date)
    man = manual_fixtures(date)
    if man:
        seen = [(dedup_key(g["home"]), dedup_key(g["away"])) for g in man]

        def dup(g):
            h, a = dedup_key(g["home"]), dedup_key(g["away"])
            def same(x, y):
                return x == y or x.startswith(y) or y.startswith(x)
            return any(same(h, mh) and same(a, ma) for mh, ma in seen)

        fixtures = man + [g for g in fixtures if not dup(g)]
        fixtures.sort(key=lambda g: g["ts"])
    print(f"\n{len(fixtures)} fixture(s) ({len(man)} pasted in with odds)")

    out, skipped = [], []
    for g in fixtures:
        hn, he = resolve(g["home"], date)
        an, ae = resolve(g["away"], date)
        if not hn or not an:
            miss = g["home"] if not hn else g["away"]
            skipped.append(f"{g['home']} v {g['away']} (no rating for {miss})")
            continue
        try:
            p = euro.predict(hn, an, date, odds=g.get("odds"), verbose=False)
        except Exception as e:
            skipped.append(f"{g['home']} v {g['away']} ({e})")
            continue
        cr = cosmic_reading(g["home"], g["away"], dt.date.fromisoformat(date))
        pk = ["HOME", "DRAW", "AWAY"][int(max(range(3), key=lambda i: p["one_x_two"][i]))]
        out.append(dict(
            id=g["id"], comp=g["comp"], kickoff=g["kickoff"],
            home=g["home"], away=g["away"],
            home_elo=p["elo_home"], away_elo=p["elo_away"],
            probs=[round(v, 3) for v in p["one_x_two"]],
            model_probs=[round(v, 3) for v in p["model_only"]],
            market=p["market"],
            pick=pk, over25=p["over25"], top_score=p["top_scores"][0]["score"],
            cosmic=cr["headline"],
        ))
        print(f"  {g['kickoff']}  {g['home'][:20]:<20s} v {g['away'][:20]:<20s} "
              f"{p['one_x_two'][0]*100:3.0f}/{p['one_x_two'][1]*100:3.0f}/{p['one_x_two'][2]*100:3.0f}  -> {pk}")

    for s in skipped:
        print(f"  [unrated] {s}")

    _log_pending(out, date)

    payload = dict(date=date,
                   generated_at=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                   n=len(out), matches=out, unrated=len(skipped))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    print(f"\nWrote {OUT}: {len(out)} rated, {len(skipped)} unrated")


if __name__ == "__main__":
    main()
