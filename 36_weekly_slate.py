"""
AstroPitch - WEEKLY SLATE  (the whole week's card, every league we can rate)
============================================================================
30_daily_slate.py answers "what's on today?". This answers "what's on this
week?", across every competition we have a defensible rating for:

  1. DOMESTIC  club_fixtures.csv (football-data.co.uk, refreshed by
               22_update_club_data.py) -> the 12 divisions club_engine.pkl is
               actually trained on, with real bookmaker 1X2 odds attached.
               Rated by the core engine.
  2. UEFA      TheSportsDB day feed -> Champions / Europa / Conference League.
               Rated via clubelo (27_euro_predict.py).
  3. FALLBACK  anything the core engine can't take - a cross-division cup tie,
               a club outside the 12 leagues - falls through to clubelo.
               If clubelo can't rate it either, it is listed as UNRATED rather
               than guessed at, same rule as the API's coverage().

Where odds exist the model is anchored on them at the repo's own weights
(W_MARKET 0.75 core / 0.85 clubelo). Where they don't, the model stands alone
and the row is flagged `anchored: false`, because those are the rows most
likely to be wrong.

This is a PRESENTATION layer. It deliberately does not log to the track
record: 23_track_record.py and 30_daily_slate.py already log each match on its
own matchday, closer to kickoff and on better prices. Logging here as well
would double-count the same fixture.

Writes week_slate.json, which 26_build_site.py renders into docs/week.html.

Run:  python 36_weekly_slate.py [YYYY-MM-DD] [--days N]
      (default: the next 7 days starting today, UTC)
============================================================================
"""
import datetime as dt
import importlib.util
import json
import os
import sys
import time
import urllib.request

import joblib
import numpy as np
import pandas as pd


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gpc = _load("21_club_genesis.py", "club_genesis")        # dc_matrix, k_factor, constants
euro = _load("27_euro_predict.py", "euro_predict")       # clubelo predictor
daily = _load("30_daily_slate.py", "daily_slate")        # clubelo name resolution

OUT = "week_slate.json"
FIXTURES_CSV = "club_fixtures.csv"
SPORTSDB = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={d}&l={lg}"
COMPS = {4480: "Champions League", 4481: "Europa League", 5071: "Conference League"}

CLUB = joblib.load("club_engine.pkl")
CARDS = joblib.load("cards_engine.pkl")
ST = CLUB["state"]
ELO, TEAM_DIV, LEAGUE_CODES = ST["elo"], ST["team_league"], ST["league_codes"]
DIV_NAMES = CLUB.get("div_names", {})
CLUB_TEAMS = set(ELO)
W_MARKET_CORE = 0.75                    # matches 24_api.py's W_MARKET["club"]

# bookmaker columns in football-data's fixtures.csv, in preference order
ODDS_COLS = [("B365H", "B365D", "B365A"), ("PSH", "PSD", "PSA"),
             ("BWH", "BWD", "BWA"), ("AvgH", "AvgD", "AvgA"),
             ("BFDH", "BFDD", "BFDA"), ("BVH", "BVD", "BVA")]


# ---------------------------------------------------------------------------
# core-engine prediction (mirrors 24_api.py's predict path)
# ---------------------------------------------------------------------------
def _roll(team, n):
    h = ST["hist"].get(team, [])
    if not h:
        return dict(gf=1.3, ga=1.3, form=0.5)
    r = h[-n:]
    return dict(gf=np.mean([x[0] for x in r]), ga=np.mean([x[1] for x in r]),
                form=np.mean([x[2] for x in r]) / 3.0)


def _shots(team, n=10):
    h = ST.get("sot", {}).get(team, [])
    if not h:
        return (4.4, 4.4)
    r = h[-n:]
    return (float(np.mean([x[0] for x in r])), float(np.mean([x[1] for x in r])))


def _row(home, away, date, div):
    he, ae = ELO.get(home, gpc.BASE_ELO), ELO.get(away, gpc.BASE_ELO)
    exp_h = 1.0 / (1.0 + 10 ** ((ae - (he + gpc.HOME_ADV)) / 400.0))
    h5, a5, h10, a10 = _roll(home, 5), _roll(away, 5), _roll(home, 10), _roll(away, 10)
    ld = ST.get("last_date", {})
    rh = min((date - ld[home]).days, 60) if home in ld else 7
    ra = min((date - ld[away]).days, 60) if away in ld else 7
    hh = ST["h2h"].get(tuple(sorted([home, away])), [])
    base = dict(league=LEAGUE_CODES[div], H_ELO=he, A_ELO=ae, ELO_Diff=he - ae, ELO_Exp=exp_h,
                Rest_H=rh, Rest_A=ra, Rest_Diff=rh - ra,
                H_GF5=h5["gf"], H_GA5=h5["ga"], A_GF5=a5["gf"], A_GA5=a5["ga"],
                H_GF10=h10["gf"], H_GA10=h10["ga"], A_GF10=a10["gf"], A_GA10=a10["ga"],
                H_Form5=h5["form"], A_Form5=a5["form"], Form_Diff=h5["form"] - a5["form"],
                H_Exp=(h10["gf"] + a10["ga"]) / 2.0, A_Exp=(a10["gf"] + h10["ga"]) / 2.0,
                H2H=np.mean(hh) if hh else 0.5)
    if any("SoT" in c for c in CLUB["features"]):
        hsf, hsa = _shots(home)
        asf, asa = _shots(away)
        base.update(H_SoT10=hsf, H_SoTA10=hsa, A_SoT10=asf, A_SoTA10=asa,
                    SoT_Dom=(hsf - hsa) - (asf - asa))
    return pd.DataFrame([base])[CLUB["features"]]


def _cards(home, away, div):
    st, lc = CARDS["state"], CARDS["league_codes"]
    if div not in lc or home not in st["tcards"] or away not in st["tcards"]:
        return None
    he, ae = st["elo"].get(home, gpc.BASE_ELO), st["elo"].get(away, gpc.BASE_ELO)
    exp_h = 1.0 / (1.0 + 10 ** ((ae - (he + gpc.HOME_ADV)) / 400.0))

    def roll(t, n):
        h = st["tcards"].get(t, [])
        return float(np.mean(h[-n:])) if h else np.nan

    row = {"league": lc[div], "imp": gpc.k_factor(div), "ELO_Diff": he - ae,
           "ELO_AbsDiff": abs(he - ae), "ELO_Exp": exp_h,
           "H_cards5": roll(home, 5), "A_cards5": roll(away, 5),
           "H_cards10": roll(home, 10), "A_cards10": roll(away, 10),
           "ref_avg": np.nan, "ref_n": 0}
    X = pd.DataFrame([row])[CARDS["features"]]
    return round(float(np.clip(CARDS["model"].predict(X)[0], 1, 12)), 1)


def predict_core(home, away, date, div, odds):
    """Returns the same shape as predict_euro so the renderer needs one path."""
    X = _row(home, away, date, div)
    model = np.array(CLUB["model_1x2"].predict_proba(X)[0], dtype=float)
    p_over = float(CLUB["ou"].predict_proba(X)[0, 1])
    lam = float(np.clip(CLUB["reg_h"].predict(X)[0], 0.15, 6))
    mu = float(np.clip(CLUB["reg_a"].predict(X)[0], 0.15, 6))
    M = gpc.dc_matrix(lam, mu, CLUB["rho"], maxg=8)

    final, market = model.copy(), None
    if odds:
        inv = np.array([1.0 / o for o in odds])
        market = inv / inv.sum()
        blend = (market ** W_MARKET_CORE) * (model ** (1 - W_MARKET_CORE))
        final = blend / blend.sum()
        regions = [np.tril(M, -1).sum(), np.trace(M), np.triu(M, 1).sum()]
        scale = {0: final[0] / regions[0], 1: final[1] / regions[1], 2: final[2] / regions[2]}
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                M[i, j] *= scale[0 if i > j else (1 if i == j else 2)]
        M /= M.sum()

    flat = sorted(((i, j, M[i, j]) for i in range(M.shape[0]) for j in range(M.shape[1])),
                  key=lambda x: -x[2])[:3]
    return dict(source="engine", elo=[round(ELO.get(home, gpc.BASE_ELO)),
                                      round(ELO.get(away, gpc.BASE_ELO))],
                model=[round(float(v), 3) for v in model],
                market=None if market is None else [round(float(v), 3) for v in market],
                final=[round(float(v), 3) for v in final],
                over25=round(p_over, 3), xg=[round(lam, 2), round(mu, 2)],
                scores=[{"score": f"{i}-{j}", "prob": round(float(p), 3)} for i, j, p in flat],
                cards=_cards(home, away, div))


_clubelo_state = {"checked": False, "up": True}


def clubelo_up(date):
    """One canary call, cached. Without it an unreachable clubelo looks exactly
    like an unknown club, and every fallback row gets blamed on the wrong thing."""
    if not _clubelo_state["checked"]:
        _clubelo_state["checked"] = True
        try:
            euro.fetch_elo("Liverpool", date)
        except Exception as e:
            _clubelo_state["up"] = False
            print(f"  [warn] clubelo unreachable ({e}) - fallback coverage is off "
                  f"for this run; cross-division and non-league ties will be unrated")
    return _clubelo_state["up"]


def predict_euro(home_raw, away_raw, date, odds):
    """clubelo path. Returns None when either club can't be resolved/rated."""
    if not clubelo_up(date):
        return None, "clubelo unavailable"
    hn, _ = daily.resolve(home_raw, date)
    an, _ = daily.resolve(away_raw, date)
    if not hn or not an:
        return None, f"no rating for {home_raw if not hn else away_raw}"
    p = euro.predict(hn, an, date, odds=odds, verbose=False)
    return dict(source="clubelo", elo=[p["elo_home"], p["elo_away"]],
                model=p["model_only"], market=p["market"], final=p["one_x_two"],
                over25=p["over25"], xg=p["xg"], scores=p["top_scores"], cards=None), None


# ---------------------------------------------------------------------------
# fixture sources
# ---------------------------------------------------------------------------
def _odds_from(row):
    for h, d, a in ODDS_COLS:
        try:
            o = (float(row[h]), float(row[d]), float(row[a]))
        except (KeyError, TypeError, ValueError):
            continue
        if all(x > 1.0 for x in o):
            return o
    return None


def domestic_fixtures(start, end):
    if not os.path.exists(FIXTURES_CSV):
        print(f"  [skip] {FIXTURES_CSV} missing - run 22_update_club_data.py first")
        return []
    fx = pd.read_csv(FIXTURES_CSV, encoding="latin-1", low_memory=False)
    for a in [c for c in fx.columns if "Div" in c and c != "Div"]:
        fx = fx.rename(columns={a: "Div"})
    if "Div" not in fx.columns:
        return []
    # NB: itertuples mangles column names that aren't valid identifiers, so the
    # parsed date goes in a normally-named column and rows are read as dicts.
    fx["KickDate"] = pd.to_datetime(fx["Date"], dayfirst=True, errors="coerce")
    fx = fx[fx["KickDate"].notna()]
    fx = fx[(fx["KickDate"].dt.date >= start) & (fx["KickDate"].dt.date <= end)]
    out = []
    for row in fx.to_dict("records"):
        out.append(dict(date=row["KickDate"].date().isoformat(),
                        kickoff=str(row.get("Time") or "")[:5],
                        div=row["Div"], comp=DIV_NAMES.get(row["Div"], row["Div"]),
                        home=str(row["HomeTeam"]).strip(), away=str(row["AwayTeam"]).strip(),
                        odds=_odds_from(row), kind="domestic"))
    return out


def uefa_fixtures(start, end):
    games, day = [], start
    while day <= end:
        for lg, label in COMPS.items():
            try:
                req = urllib.request.Request(SPORTSDB.format(d=day.isoformat(), lg=lg),
                                             headers={"User-Agent": "Mozilla/5.0"})
                data = json.load(urllib.request.urlopen(req, timeout=45))
            except Exception as e:
                print(f"  [skip] {label} {day}: {e}")
                continue
            for e in (data.get("events") or []):
                ts = e.get("strTimestamp") or ""
                games.append(dict(date=day.isoformat(),
                                  kickoff=ts[11:16] if len(ts) > 15 else "",
                                  div=None, comp=label,
                                  home=e.get("strHomeTeam", "").strip(),
                                  away=e.get("strAwayTeam", "").strip(),
                                  odds=None, kind="uefa"))
            time.sleep(1)
        day += dt.timedelta(days=1)
    return games


# ---------------------------------------------------------------------------
def rate(g):
    """Core engine where both clubs are covered and in the same division,
    clubelo otherwise. Returns (record | None, unrated_reason | None)."""
    date = dt.datetime.fromisoformat(g["date"])
    h, a = g["home"], g["away"]
    dh, da = TEAM_DIV.get(h), TEAM_DIV.get(a)
    if h in CLUB_TEAMS and a in CLUB_TEAMS and dh == da and dh in LEAGUE_CODES:
        return predict_core(h, a, date, dh, g["odds"]), None
    res, reason = predict_euro(h, a, g["date"], g["odds"])
    return (res, None) if res is not None else (None, reason)


def main():
    argv = sys.argv[1:]
    days = 7
    for i, a in enumerate(argv):
        if a.startswith("--days="):
            days = int(a.split("=", 1)[1])
        elif a == "--days" and i + 1 < len(argv):
            days = int(argv[i + 1])
    skip = {str(days)} if "--days" in argv else set()
    args = [a for a in argv if not a.startswith("--") and a not in skip]
    start = (dt.date.fromisoformat(args[0]) if args
             else dt.datetime.now(dt.UTC).date())
    end = start + dt.timedelta(days=days - 1)

    print("=" * 70)
    print(f" ASTROPITCH - WEEKLY SLATE  {start} -> {end}")
    print("=" * 70)

    fixtures = domestic_fixtures(start, end)
    print(f"  domestic: {len(fixtures)} fixture(s) from {FIXTURES_CSV}")
    uefa = uefa_fixtures(start, end)
    print(f"  uefa    : {len(uefa)} fixture(s) from TheSportsDB")

    seen = {(daily.dedup_key(g["home"]), daily.dedup_key(g["away"]), g["date"])
            for g in fixtures}
    fixtures += [g for g in uefa
                 if (daily.dedup_key(g["home"]), daily.dedup_key(g["away"]), g["date"])
                 not in seen]
    fixtures.sort(key=lambda g: (g["date"], g["kickoff"] or "99:99", g["comp"]))

    matches, unrated = [], []
    for g in fixtures:
        try:
            res, why = rate(g)
        except Exception as e:
            res, why = None, str(e)
        if res is None:
            unrated.append(dict(date=g["date"], kickoff=g["kickoff"], comp=g["comp"],
                                home=g["home"], away=g["away"], reason=why))
            print(f"  [unrated] {g['home']} v {g['away']} ({why})")
            continue

        pH, pD, pA = res["final"]
        dcs = {"1X": pH + pD, "12": pH + pA, "X2": pD + pA}
        best = max(dcs, key=dcs.get)
        prob = dcs[best]
        # thresholds measured in 30_daily_slate.py on the 4,000-match holdout
        tier = "high" if prob >= 0.80 else "medium" if prob >= 0.70 else "low"
        matches.append(dict(
            date=g["date"], kickoff=g["kickoff"], comp=g["comp"], kind=g["kind"],
            home=g["home"], away=g["away"], **res,
            anchored=res["market"] is not None,
            pick=["HOME", "DRAW", "AWAY"][int(np.argmax(res["final"]))],
            dc=best, dc_prob=round(float(prob), 3), dc_tier=tier,
            top_score=res["scores"][0]["score"]))
        print(f"  {g['date']} {g['kickoff'] or '  -  '}  {g['comp'][:22]:<22} "
              f"{g['home'][:18]:<18} v {g['away'][:18]:<18} "
              f"{pH*100:3.0f}/{pD*100:3.0f}/{pA*100:3.0f}  "
              f"{best} {prob*100:4.1f}% {tier}")

    comps = sorted({m["comp"] for m in matches})
    payload = dict(start=start.isoformat(), end=end.isoformat(),
                   generated_at=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                   n=len(matches), unrated=len(unrated), competitions=comps,
                   n_anchored=sum(1 for m in matches if m["anchored"]),
                   matches=matches, unrated_list=unrated)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    print(f"\nWrote {OUT}: {len(matches)} rated across {len(comps)} competition(s), "
          f"{len(unrated)} unrated, {payload['n_anchored']} anchored on odds")


if __name__ == "__main__":
    main()
