"""
AstroPitch - EUROPEAN PREDICTOR (clubelo-powered coverage extension)
============================================================================
Our trained engine only knows 12 top leagues. This gives the model real
knowledge of ANY European club by using clubelo.com's free ratings, which
place ~600 clubs (Cyprus, Kazakhstan, Albania, Slovenia, ...) on ONE
comparable scale, computed from their real matches incl. European ties.

Honest note: this uses clubelo's strength ratings (not our own trained ELO,
which we can't build without those leagues' match data). It IS a real,
knowledge-based prediction - not the blind home-lean the core engine falls
back to for unknown teams.

  predict(home, away, date, odds=None) -> 1X2 + O/U 2.5 + top scorelines.
Ratings are cached to clubelo_cache.json so we don't re-hit the API.
============================================================================
"""
import datetime as dt
import os
import json
import re
import unicodedata
import urllib.request
import numpy as np
import importlib.util

# reuse the Dixon-Coles matrix from the club trainer
_spec = importlib.util.spec_from_file_location("gpc", "21_club_genesis.py")
gpc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(gpc)

HOME_ADV = 65.0                 # clubelo-scale home advantage (~65 ELO)
# Draw model CALIBRATED on 44,325 real club matches (observed draw rate vs ELO
# gap, sample-size weighted). The old guess (0.27*exp(-gap/300)) decayed far too
# fast — it gave a 298-gap match only 10% on the draw when reality is ~17%.
DRAW_A, DRAW_C = 0.3067, 488.9  # draw = A * exp(-|elo_gap| / C)
BASE_TOTAL = 2.6                # typical total goals; supremacy shifts the split
ELO_PER_GOAL = 190.0            # ~190 ELO of supremacy ≈ one goal
CACHE = "clubelo_cache.json"


def _load_cache():
    return json.load(open(CACHE)) if os.path.exists(CACHE) else {}


# ---------------------------------------------------------------------------
# Fallback source: the clubelo.com homepage.
# api.clubelo.com has returned 502 since at least July 2026 (from here and from
# GitHub Actions alike), which silently switched off every clubelo-rated row:
# all UEFA ties and every cross-division cup tie came back "unrated" — the week
# of 8 Oct 2026 published ZERO rated fixtures. The homepage is still up and
# embeds the full current ranking table (~1,700 clubs: API-style link, display
# name, federation, Elo), so one request a day restores the whole fallback.
# It carries CURRENT ratings only, so it is used just for fixtures within
# SNAPSHOT_WINDOW_DAYS of today; anything older still needs the API.
# ---------------------------------------------------------------------------
SNAPSHOT = "clubelo_snapshot.json"
SNAPSHOT_URL = "https://clubelo.com/"
SNAPSHOT_WINDOW_DAYS = 21
UEFA = set("ALB AND ARM AUT AZE BEL BIH BLR BUL CRO CYP CZE DEN ENG ESP EST FIN FRA "
           "FRO GEO GER GIB GRE HUN IRL ISL ISR ITA KAZ KOS LTU LUX LVA MDA MKD MLT "
           "MNE NED NIR NOR POL POR ROU RUS SCO SMR SRB SUI SVK SVN SWE TUR UKR WAL".split())
# club-type tokens that differ between sources ("PS Kalamata" vs "Kalamata",
# "NFC Volos" vs "Volos NFC"); matched only as a second resort
_CLUB_TOKENS = {"fc", "sk", "ps", "nfc", "ac", "as", "cf", "cd", "sc", "fk", "nk", "if",
                "bk", "afc", "sv", "rc", "ud", "sd", "ca", "cs", "kv", "kf", "ks", "pfc"}


# Letters Unicode normalisation does NOT decompose, so a plain ASCII fold just
# deletes them: "FC Nordsjælland" became "Nordsjlland" and never matched
# clubelo's "Nordsjaelland". Transliterate first, the way sources spell them.
TRANSLIT = str.maketrans({"æ": "ae", "Æ": "Ae", "ø": "o", "Ø": "O", "œ": "oe", "Œ": "Oe",
                          "ß": "ss", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D", "ð": "d",
                          "Ð": "D", "þ": "th", "Þ": "Th", "ı": "i"})


def ascii_fold(s):
    s = str(s).translate(TRANSLIT)
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", ascii_fold(s).lower())


def _loose_keys(name):
    """Second-resort keys: club-type tokens dropped, and word order ignored."""
    toks = [_norm(t) for t in re.split(r"[\s\-./]+", name) if _norm(t)]
    core = [t for t in toks if t not in _CLUB_TOKENS] or toks
    return {"".join(core), "".join(sorted(core)), "".join(sorted(toks))} - {""}


def parse_snapshot(html):
    """{"exact": {key: [club, ...]}, "loose": {...}} from the homepage table."""
    exact, loose = {}, {}
    for row in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        elo = re.findall(r'<td class="r">\s*(\d{3,4})\s*</td>', row)
        cc = re.search(r'<a href="/([A-Z]{3})">', row)
        disp = re.search(r'<span class="(?:Ast|min641)">([^<]+)</span>', row)
        if not (elo and cc and disp):
            continue
        links = [a for a in re.findall(r'<a href="/([A-Za-z0-9]+)">', row) if a != cc.group(1)]
        club = dict(api=links[0] if links else None, name=disp.group(1).strip(),
                    cc=cc.group(1), elo=int(elo[-1]))
        for index, keys in ((exact, {_norm(club["name"]), _norm(club["api"] or "")}),
                            (loose, _loose_keys(club["name"]))):
            for k in keys - {""}:
                index.setdefault(k, []).append(club)
    return {"exact": exact, "loose": loose}


def _load_snapshot():
    today = dt.datetime.now(dt.UTC).date().isoformat()
    if os.path.exists(SNAPSHOT):
        snap = json.load(open(SNAPSHOT, encoding="utf-8"))
        if snap.get("date") == today:
            return snap
    req = urllib.request.Request(SNAPSHOT_URL, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    snap = dict(date=today, **parse_snapshot(html))
    if len({c["name"] for v in snap["exact"].values() for c in v}) < 500:
        raise ValueError("clubelo homepage parsed to too few clubs; layout changed?")
    json.dump(snap, open(SNAPSHOT, "w", encoding="utf-8"))
    return snap


def pick_club(snap, team):
    """The one club `team` names, or None. Ambiguity is settled in favour of a
    European federation (this predictor rates European fixtures: 'Liverpool'
    is ENG, not URU); anything still ambiguous is refused, not guessed."""
    for index, keys in (("exact", {_norm(team)}), ("loose", _loose_keys(team))):
        found = {}
        for k in keys:
            for c in snap[index].get(k, []):
                found[(c["cc"], c["elo"], _norm(c["name"]))] = c
        clubs = list(found.values())
        if len(clubs) > 1:
            clubs = [c for c in clubs if c["cc"] in UEFA] or clubs
        if len({(c["cc"], _norm(c["name"])) for c in clubs}) == 1:
            return clubs[0]
        if clubs:
            return None          # genuinely ambiguous: refuse
    return None


def snapshot_elo(team, on_date):
    day = dt.date.fromisoformat(str(on_date)[:10])
    if abs((day - dt.datetime.now(dt.UTC).date()).days) > SNAPSHOT_WINDOW_DAYS:
        raise ValueError(f"snapshot only covers fixtures near today, not {on_date}")
    club = pick_club(_load_snapshot(), team)
    if club is None:
        raise ValueError(f"clubelo snapshot has no unambiguous rating for '{team}'")
    return float(club["elo"])


def fetch_elo(team, on_date):
    """clubelo ELO for `team` as of on_date (ISO). Cached by (team,date).
    Uses the API when it answers, else the homepage snapshot (see above)."""
    cache = _load_cache()
    key = f"{team}@{on_date}"
    if key in cache:
        return cache[key]
    try:
        rating = _fetch_elo_api(team, on_date)
    except Exception:
        rating = snapshot_elo(team, on_date)
    cache[key] = rating
    json.dump(cache, open(CACHE, "w"))
    return rating


def _fetch_elo_api(team, on_date):
    req = urllib.request.Request(f"http://api.clubelo.com/{team.replace(' ', '%20')}",
                                 headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=20).read().decode()
    rating = None
    for line in raw.splitlines():
        p = line.split(",")
        if len(p) < 7 or p[0] == "Rank":
            continue
        try:
            elo, frm, to = float(p[4]), p[5], p[6]
        except ValueError:
            continue
        rating = elo                       # keep latest seen
        if frm <= on_date <= to:           # exact period covering the date
            break
    if rating is None:
        raise ValueError(f"clubelo has no rating for '{team}'")
    return rating


def _market(odds):
    inv = np.array([1.0 / o for o in odds]); return inv / inv.sum()


# How hard to lean on the bookmaker line when odds are supplied.
# Raised 0.60 -> 0.85 on evidence: the 24,330-match closing-odds study
# (17_odds_value.py) found the optimal blend to be w_market=1.0, and the graded
# 25 Jul friendlies agreed (market log-loss 0.9405 vs our 0.9852, with the blend
# sweep monotonic all the way to w=1.0). Kept below 1.0 because these are
# pre-match rather than closing prices, and so the model still contributes where
# a line is thin. Where NO odds exist, the model stands alone regardless.
W_MARKET_DEFAULT = 0.85


def predict(home, away, date, odds=None, w_market=W_MARKET_DEFAULT, verbose=True):
    eh = fetch_elo(home, date)
    ea = fetch_elo(away, date)
    diff = eh - ea
    exp_h = 1.0 / (1.0 + 10 ** (-(diff + HOME_ADV) / 400.0))
    pdraw = DRAW_A * np.exp(-abs(diff) / DRAW_C)
    pH = exp_h * (1 - pdraw); pA = (1 - exp_h) * (1 - pdraw)
    s = pH + pdraw + pA
    model = np.array([pH / s, pdraw / s, pA / s])

    # goals from supremacy -> Dixon-Coles for O/U + scorelines
    sup = (diff + HOME_ADV) / ELO_PER_GOAL
    # BASE_TOTAL alone was a constant, so lam+mu never moved and O/U barely
    # varied match to match. Bump the total with the size of the mismatch
    # (a one-sided game tends to open up and leak more goals) - a football
    # heuristic, not fitted on data like the core engine's goal regressors.
    total = BASE_TOTAL + min(abs(sup) * 0.55, 0.9)
    lam = float(np.clip((total + sup) / 2, 0.2, 5))
    mu = float(np.clip((total - sup) / 2, 0.2, 5))
    M = gpc.dc_matrix(lam, mu, -0.045, maxg=8)

    final = model.copy(); mkt = None
    if odds is not None:
        mkt = _market(odds)
        blend = (mkt ** w_market) * (model ** (1 - w_market))
        final = blend / blend.sum()

    p_over = M[np.add.outer(range(9), range(9)) > 2].sum()
    flat = sorted(((i, j, M[i, j]) for i in range(9) for j in range(9)),
                  key=lambda x: -x[2])[:4]
    lbl = ["HOME", "DRAW", "AWAY"]
    out = dict(home=home, away=away, elo_home=round(eh), elo_away=round(ea),
               one_x_two=[round(float(x), 3) for x in final],
               model_only=[round(float(x), 3) for x in model],
               market=None if mkt is None else [round(float(x), 3) for x in mkt],
               pick=lbl[int(final.argmax())], over25=round(float(p_over), 3),
               xg=[round(lam, 2), round(mu, 2)],
               top_scores=[{"score": f"{i}-{j}", "prob": round(float(p), 3)} for i, j, p in flat],
               scores=[f"{i}-{j} {p*100:.0f}%" for i, j, p in flat])
    if verbose:
        print(f"\n{home} ({out['elo_home']}) vs {away} ({out['elo_away']})")
        print(f"  model 1X2 : {out['model_only'][0]*100:.0f}/{out['model_only'][1]*100:.0f}/{out['model_only'][2]*100:.0f}")
        if mkt is not None:
            print(f"  market    : {out['market'][0]*100:.0f}/{out['market'][1]*100:.0f}/{out['market'][2]*100:.0f}")
            print(f"  FINAL     : {out['one_x_two'][0]*100:.0f}/{out['one_x_two'][1]*100:.0f}/{out['one_x_two'][2]*100:.0f}")
        print(f"  --> {out['pick']}   | over2.5 {out['over25']*100:.0f}% | {', '.join(out['scores'][:3])}")
    return out


if __name__ == "__main__":
    d = "2026-07-22"
    for h, a, o in [("Omonia", "Kairat", (1.65, 3.50, 4.50)),
                    ("Levski", "Craiova", (1.90, 3.20, 3.80)),
                    ("Egnatia", "Celje", (3.60, 3.50, 1.85))]:
        predict(h, a, d, odds=o)
