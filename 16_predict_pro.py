"""
AstroPitch V12 - PRO PREDICTOR
Loads pro_engine.pkl and predicts any fixture: 1X2, O/U 2.5, and a full
exact-score distribution from the Dixon-Coles matrix. Feature construction
mirrors 15_genesis_pro.py exactly, reusing the saved rolling state.
"""
import numpy as np
import pandas as pd
import joblib

E = joblib.load("pro_engine.pkl")
state, FEATURES = E["state"], E["features"]
# reuse constants/functions from the trainer
import importlib.util
spec = importlib.util.spec_from_file_location("gp", "15_genesis_pro.py")
gp = importlib.util.module_from_spec(spec); spec.loader.exec_module(gp)

BASE_ELO, HOME_ADV = gp.BASE_ELO, gp.HOME_ADV

def team_roll(team, n):
    h = state["hist"].get(team, [])
    if not h:
        return dict(gf=1.2, ga=1.2, form=0.5)
    recent = h[-n:]
    return dict(gf=np.mean([x[0] for x in recent]),
                ga=np.mean([x[1] for x in recent]),
                form=np.mean([x[2] for x in recent]) / 3.0)

def build_row(home, away, date, neutral, importance=55):
    R = state["elo"]
    h_elo, a_elo = R.get(home, BASE_ELO), R.get(away, BASE_ELO)
    adv = 0.0 if neutral else HOME_ADV
    exp_h = 1.0 / (1.0 + 10 ** ((a_elo - (h_elo + adv)) / 400.0))
    h5, a5 = team_roll(home, 5), team_roll(away, 5)
    h10, a10 = team_roll(home, 10), team_roll(away, 10)
    rest_h = (date - state["last_date"][home]).days if home in state["last_date"] else 180
    rest_a = (date - state["last_date"][away]).days if away in state["last_date"] else 180
    key = tuple(sorted([home, away]))
    hh = state["h2h"].get(key, [])
    h2h_home = np.mean(hh) if hh else 0.5
    row = dict(
        neutral=int(neutral), imp=importance,
        H_ELO=h_elo, A_ELO=a_elo, ELO_Diff=h_elo - a_elo, ELO_Exp=exp_h,
        Rest_H=min(rest_h, 365), Rest_A=min(rest_a, 365),
        Rest_Diff=min(rest_h, 365) - min(rest_a, 365),
        H_GF5=h5['gf'], H_GA5=h5['ga'], A_GF5=a5['gf'], A_GA5=a5['ga'],
        H_GF10=h10['gf'], H_GA10=h10['ga'], A_GF10=a10['gf'], A_GA10=a10['ga'],
        H_Form5=h5['form'], A_Form5=a5['form'], Form_Diff=h5['form'] - a5['form'],
        H_Exp=(h10['gf'] + a10['ga']) / 2.0, A_Exp=(a10['gf'] + h10['ga']) / 2.0,
        H2H=h2h_home,
    )
    return pd.DataFrame([row])[FEATURES]

# Empirically (17_odds_value.py) a sharp CLOSING line beats ELO/form features
# outright, and public features can't improve on it (best blend => w_market=1.0).
# International lines are thinner than top-club lines, so we allow a small model
# tilt rather than 1.0. Default anchors mostly on the market when odds are given.
W_MARKET = 0.70

def _market_probs(oh, od, oa):
    inv = np.array([1/oh, 1/od, 1/oa])
    return inv / inv.sum()   # margin (vig) removed

def predict(home, away, date_str, neutral=True, odds=None):
    """odds: optional (home, draw, away) decimal bookmaker prices."""
    date = pd.to_datetime(date_str)
    X = build_row(home, away, date, neutral)
    pH, pD, pA = E["model_1x2"].predict_proba(X)[0]
    p_over = E["ou"].predict_proba(X)[0, 1]
    lam = float(np.clip(E["reg_h"].predict(X)[0], 0.15, 6))
    mu = float(np.clip(E["reg_a"].predict(X)[0], 0.15, 6))
    M = gp.dc_matrix(lam, mu, E["rho"], maxg=8)

    model_1x2 = np.array([pH, pD, pA])
    final = model_1x2.copy()
    mkt = None
    if odds is not None:
        mkt = _market_probs(*odds)
        # log-opinion pool, anchored on the sharp market line
        blend = (mkt ** W_MARKET) * (model_1x2 ** (1 - W_MARKET))
        final = blend / blend.sum()
        # rescale the exact-score matrix so its 1X2 regions match the final line
        regions = [np.tril(M, -1).sum(), np.trace(M), np.triu(M, 1).sum()]
        scale = {0: final[0]/regions[0], 1: final[1]/regions[1], 2: final[2]/regions[2]}
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                r = 0 if i > j else (1 if i == j else 2)
                M[i, j] *= scale[r]
        M /= M.sum()

    flat = [((i, j), M[i, j]) for i in range(M.shape[0]) for j in range(M.shape[1])]
    flat.sort(key=lambda x: -x[1])
    top = flat[:5]

    print(f"\n{'='*60}\n {home}  vs  {away}   ({date_str}{' [neutral]' if neutral else ''})")
    print(f"{'='*60}")
    print(f"  xG (model)      : {home} {lam:.2f}  -  {mu:.2f} {away}")
    print(f"  Model  H/D/A    : {pH*100:4.1f}%  {pD*100:4.1f}%  {pA*100:4.1f}%")
    if mkt is not None:
        print(f"  Market H/D/A    : {mkt[0]*100:4.1f}%  {mkt[1]*100:4.1f}%  {mkt[2]*100:4.1f}%  (vig-free)")
        print(f"  FINAL  H/D/A    : {final[0]*100:4.1f}%  {final[1]*100:4.1f}%  {final[2]*100:4.1f}%  (market-anchored)")
        edge = model_1x2 - mkt
        lbl = ["HOME", "DRAW", "AWAY"]
        val = [f"{lbl[i]} {edge[i]*100:+.1f}%" for i in range(3) if edge[i] > 0.03]
        print(f"  Value edges     : {', '.join(val) if val else 'none (model agrees with market)'}")
    print(f"  Over 2.5 goals  : {p_over*100:4.1f}%   Under: {(1-p_over)*100:4.1f}%")
    pick = max(zip(final, ['HOME','DRAW','AWAY']))
    print(f"  --> Call        : {pick[1]}  ({pick[0]*100:.1f}%)")
    print(f"  Most likely scores:")
    for (i, j), p in top:
        print(f"       {i}-{j}   {p*100:4.1f}%")

if __name__ == "__main__":
    # Upcoming WC2026 fixtures present in the dataset (unplayed)
    fixtures = [
        ("Brazil", "Norway", "2026-07-05", True),
        ("Mexico", "England", "2026-07-05", False),
        ("Portugal", "Spain", "2026-07-06", True),
        ("United States", "Belgium", "2026-07-06", False),
        ("Argentina", "Egypt", "2026-07-06", True),
        ("Switzerland", "Colombia", "2026-07-06", True),
        ("France", "Morocco", "2026-07-09", True),
    ]
    print("ASTROPITCH V12 PRO - WORLD CUP 2026 PREDICTIONS")
    for h, a, d, n in fixtures:
        predict(h, a, d, n)

    # --- Same fixture WITH a live bookmaker line supplied (market-anchored) ---
    print("\n\n### EXAMPLE WITH LIVE BOOKMAKER ODDS ###")
    predict("France", "Morocco", "2026-07-09", neutral=True, odds=(1.95, 3.40, 4.20))
