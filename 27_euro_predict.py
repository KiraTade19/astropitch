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
import os
import json
import urllib.request
import numpy as np
import importlib.util

# reuse the Dixon-Coles matrix from the club trainer
_spec = importlib.util.spec_from_file_location("gpc", "21_club_genesis.py")
gpc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(gpc)

HOME_ADV = 65.0                 # clubelo-scale home advantage (~65 ELO)
BASE_TOTAL = 2.6                # typical total goals; supremacy shifts the split
ELO_PER_GOAL = 190.0            # ~190 ELO of supremacy ≈ one goal
CACHE = "clubelo_cache.json"


def _load_cache():
    return json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def fetch_elo(team, on_date):
    """clubelo ELO for `team` as of on_date (ISO). Cached by (team,date)."""
    cache = _load_cache()
    key = f"{team}@{on_date}"
    if key in cache:
        return cache[key]
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
    cache[key] = rating
    json.dump(cache, open(CACHE, "w"))
    return rating


def _market(odds):
    inv = np.array([1.0 / o for o in odds]); return inv / inv.sum()


def predict(home, away, date, odds=None, w_market=0.6, verbose=True):
    eh = fetch_elo(home, date)
    ea = fetch_elo(away, date)
    diff = eh - ea
    exp_h = 1.0 / (1.0 + 10 ** (-(diff + HOME_ADV) / 400.0))
    pdraw = 0.27 * np.exp(-abs(diff) / 300.0)
    pH = exp_h * (1 - pdraw); pA = (1 - exp_h) * (1 - pdraw)
    s = pH + pdraw + pA
    model = np.array([pH / s, pdraw / s, pA / s])

    # goals from supremacy -> Dixon-Coles for O/U + scorelines
    sup = (diff + HOME_ADV) / ELO_PER_GOAL
    lam = float(np.clip((BASE_TOTAL + sup) / 2, 0.2, 5))
    mu = float(np.clip((BASE_TOTAL - sup) / 2, 0.2, 5))
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
