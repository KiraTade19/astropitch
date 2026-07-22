"""
AstroPitch V12 - PREDICTION API  (the B2B product)
============================================================================
A clean JSON prediction service over the two engines:
  - club_engine.pkl  -> 12 top European leagues (club matches)
  - pro_engine.pkl   -> internationals

What it sells: calibrated probabilities as DATA - 1X2, O/U 2.5, and a full
exact-score distribution - for any matchup, at volume. It does NOT sell a
betting edge (our track record proved there isn't one); it sells clean,
reliable numbers other apps/sites can build on.

Run (dev):
    uvicorn 24_api:app --reload --port 8000
Then open http://127.0.0.1:8000/docs  for interactive docs.

Auth (optional): set env ASTROPITCH_API_KEYS="key1,key2" to require an
X-API-Key header with a simple per-key daily free-tier quota. Unset => open
(dev mode).
============================================================================
"""
import os
from collections import defaultdict
from datetime import date as _date, datetime, timezone

import numpy as np
import pandas as pd
import joblib
from scipy.stats import poisson
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field
from cosmic_reading import cosmic_reading

# ---------------------------------------------------------------------------
# load engines once at startup
# ---------------------------------------------------------------------------
CLUB = joblib.load("club_engine.pkl")
INTL = joblib.load("pro_engine.pkl")
BASE_ELO = 1500.0
HOME_ADV = 68.0                 # matches both engines' training constant
W_MARKET = {"club": 0.75, "international": 0.70}   # market anchor weight if odds given

DIV_NAMES = CLUB.get("div_names", {})
# team -> "club"/"international" lookup, plus club team -> division
CLUB_TEAMS = set(CLUB["state"]["elo"])
INTL_TEAMS = set(INTL["state"]["elo"])
TEAM_DIV = CLUB["state"]["team_league"]


# ---------------------------------------------------------------------------
# Dixon-Coles (self-contained)
# ---------------------------------------------------------------------------
def _dc_tau(i, j, lam, mu, rho):
    if i == 0 and j == 0:
        return 1 - lam * mu * rho
    if i == 0 and j == 1:
        return 1 + lam * rho
    if i == 1 and j == 0:
        return 1 + mu * rho
    if i == 1 and j == 1:
        return 1 - rho
    return 1.0


def dc_matrix(lam, mu, rho, maxg=8):
    ph = poisson.pmf(np.arange(maxg + 1), lam)
    pa = poisson.pmf(np.arange(maxg + 1), mu)
    M = np.outer(ph, pa)
    for i in (0, 1):
        for j in (0, 1):
            M[i, j] *= _dc_tau(i, j, lam, mu, rho)
    return M / M.sum()


def _roll(state, team, n):
    h = state["hist"].get(team, [])
    if not h:
        return dict(gf=1.3, ga=1.3, form=0.5)
    r = h[-n:]
    return dict(gf=np.mean([x[0] for x in r]), ga=np.mean([x[1] for x in r]),
                form=np.mean([x[2] for x in r]) / 3.0)


def _common(state, home, away, date, home_adv):
    R = state["elo"]
    he, ae = R.get(home, BASE_ELO), R.get(away, BASE_ELO)
    exp_h = 1.0 / (1.0 + 10 ** ((ae - (he + home_adv)) / 400.0))
    h5, a5, h10, a10 = _roll(state, home, 5), _roll(state, away, 5), \
        _roll(state, home, 10), _roll(state, away, 10)
    rest_h = (date - state["last_date"][home]).days if home in state.get("last_date", {}) else 7
    rest_a = (date - state["last_date"][away]).days if away in state.get("last_date", {}) else 7
    key = tuple(sorted([home, away]))
    hh = state["h2h"].get(key, [])
    cap = 60 if "team_league" in state else 365
    return dict(
        H_ELO=he, A_ELO=ae, ELO_Diff=he - ae, ELO_Exp=exp_h,
        Rest_H=min(rest_h, cap), Rest_A=min(rest_a, cap),
        Rest_Diff=min(rest_h, cap) - min(rest_a, cap),
        H_GF5=h5['gf'], H_GA5=h5['ga'], A_GF5=a5['gf'], A_GA5=a5['ga'],
        H_GF10=h10['gf'], H_GA10=h10['ga'], A_GF10=a10['gf'], A_GA10=a10['ga'],
        H_Form5=h5['form'], A_Form5=a5['form'], Form_Diff=h5['form'] - a5['form'],
        H_Exp=(h10['gf'] + a10['ga']) / 2.0, A_Exp=(a10['gf'] + h10['ga']) / 2.0,
        H2H=np.mean(hh) if hh else 0.5,
    ), (he in R or True)


def build_row_club(home, away, date, division):
    st = CLUB["state"]
    lc = st["league_codes"]
    div = division or TEAM_DIV.get(home) or TEAM_DIV.get(away)
    if div not in lc:
        raise HTTPException(422, f"Unknown division for '{home}'. Pass 'division' "
                                 f"(one of {sorted(lc)}).")
    base, _ = _common(st, home, away, date, HOME_ADV)
    base["league"] = lc[div]
    return pd.DataFrame([base])[CLUB["features"]], div


def build_row_intl(home, away, date, neutral, importance=30):
    st = INTL["state"]
    adv = 0.0 if neutral else HOME_ADV
    base, _ = _common(st, home, away, date, adv)
    base["neutral"] = int(neutral)
    base["imp"] = importance
    return pd.DataFrame([base])[INTL["features"]]


def _market_probs(oh, od, oa):
    inv = np.array([1.0 / oh, 1.0 / od, 1.0 / oa])
    return inv / inv.sum()


def predict_core(engine, X, kind, odds):
    pH, pD, pA = engine["model_1x2"].predict_proba(X)[0]
    p_over = float(engine["ou"].predict_proba(X)[0, 1])
    lam = float(np.clip(engine["reg_h"].predict(X)[0], 0.15, 6))
    mu = float(np.clip(engine["reg_a"].predict(X)[0], 0.15, 6))
    M = dc_matrix(lam, mu, engine["rho"], maxg=8)

    model = np.array([pH, pD, pA])
    final = model.copy()
    market = None
    if odds is not None:
        market = _market_probs(*odds)
        w = W_MARKET[kind]
        blend = (market ** w) * (model ** (1 - w))
        final = blend / blend.sum()
        regions = [np.tril(M, -1).sum(), np.trace(M), np.triu(M, 1).sum()]
        scale = {0: final[0] / regions[0], 1: final[1] / regions[1], 2: final[2] / regions[2]}
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                r = 0 if i > j else (1 if i == j else 2)
                M[i, j] *= scale[r]
        M /= M.sum()

    flat = sorted(((i, j, M[i, j]) for i in range(M.shape[0]) for j in range(M.shape[1])),
                  key=lambda x: -x[2])[:6]
    sel = ["HOME", "DRAW", "AWAY"][int(np.argmax(final))]
    out = {
        "xg": {"home": round(lam, 2), "away": round(mu, 2)},
        "one_x_two_model": {"home": round(float(pH), 4), "draw": round(float(pD), 4),
                            "away": round(float(pA), 4)},
        "one_x_two": {"home": round(float(final[0]), 4), "draw": round(float(final[1]), 4),
                      "away": round(float(final[2]), 4)},
        "over_under_2_5": {"over": round(p_over, 4), "under": round(1 - p_over, 4)},
        "likely_scores": [{"score": f"{i}-{j}", "prob": round(float(p), 4)} for i, j, p in flat],
        "pick": {"selection": sel, "probability": round(float(final.max()), 4)},
        "market": None if market is None else {
            "home": round(float(market[0]), 4), "draw": round(float(market[1]), 4),
            "away": round(float(market[2]), 4), "note": "vig-removed; 'one_x_two' is anchored on this"},
    }
    return out


# ---------------------------------------------------------------------------
# lightweight optional API-key auth + free-tier quota
# ---------------------------------------------------------------------------
_KEYS = {k.strip() for k in os.getenv("ASTROPITCH_API_KEYS", "").split(",") if k.strip()}
FREE_TIER_DAILY = int(os.getenv("ASTROPITCH_FREE_DAILY", "100"))
_usage = defaultdict(lambda: {"day": None, "count": 0})


def check_key(x_api_key):
    if not _KEYS:
        return "open"                       # dev mode, no keys configured
    if x_api_key not in _KEYS:
        raise HTTPException(401, "Missing or invalid X-API-Key.")
    u = _usage[x_api_key]
    today = _date.today().isoformat()
    if u["day"] != today:
        u["day"], u["count"] = today, 0
    if u["count"] >= FREE_TIER_DAILY:
        raise HTTPException(429, f"Free-tier daily limit ({FREE_TIER_DAILY}) reached.")
    u["count"] += 1
    return x_api_key


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AstroPitch Prediction API",
    version="1.0",
    description="Calibrated football match probabilities (1X2, O/U 2.5, exact "
                "scores) for 12 European leagues + internationals. Probabilities "
                "as data - not betting advice.",
)

DISCLAIMER = ("Probabilistic model output for information/entertainment. Not "
              "betting advice; the model has no demonstrated edge over closing odds.")


class PredictRequest(BaseModel):
    home: str = Field(..., examples=["Arsenal"])
    away: str = Field(..., examples=["Chelsea"])
    date: str = Field(..., examples=["2026-08-15"], description="ISO date YYYY-MM-DD")
    kind: str = Field("club", description="'club' or 'international'")
    division: str | None = Field(None, description="club only, e.g. 'E0' (auto-detected if omitted)")
    neutral: bool = Field(False, description="international only: neutral venue")
    odds: list[float] | None = Field(None, description="optional decimal [home, draw, away]; anchors 1X2 on the market")
    cosmic: bool = Field(False, description="include the entertainment-only 'cosmic reading' block")


def _resolve_kind(home, away, kind):
    if kind in ("club", "international"):
        return kind
    if home in CLUB_TEAMS or away in CLUB_TEAMS:
        return "club"
    if home in INTL_TEAMS or away in INTL_TEAMS:
        return "international"
    return "club"


def coverage(home, away, kind, division):
    """Only predict when BOTH teams are known and comparable. Prevents confident
    wrong answers from unknown teams or name collisions (e.g. Conf. League 'Inter'
    resolving to Inter Milan). Returns (covered: bool, reason: str|None)."""
    if kind == "international":
        unknown = [t for t in (home, away) if t not in INTL_TEAMS]
        if unknown:
            return False, f"not in our international database: {', '.join(unknown)}"
        return True, None
    unknown = [t for t in (home, away) if t not in CLUB_TEAMS]
    if unknown:
        return False, (f"outside our 12 supported leagues: {', '.join(unknown)}. "
                       f"We cover top divisions only, not lower/other-country clubs.")
    dh, da = TEAM_DIV.get(home), TEAM_DIV.get(away)
    if dh != da:
        return False, (f"cross-competition tie: {home} plays {DIV_NAMES.get(dh, dh)}, "
                       f"{away} plays {DIV_NAMES.get(da, da)}. Our ratings are within-league "
                       f"and not comparable across different leagues.")
    return True, None


def _do_predict(home, away, date, kind, division, neutral, odds, cosmic=False):
    try:
        d = pd.to_datetime(date)
    except Exception:
        raise HTTPException(422, "date must be ISO YYYY-MM-DD")
    if odds is not None and (len(odds) != 3 or min(odds) <= 1.0):
        raise HTTPException(422, "odds must be three decimal prices > 1.0 [home, draw, away]")
    kind = _resolve_kind(home, away, kind)

    # --- coverage guard: refuse rather than return a confident wrong answer ---
    covered, reason = coverage(home, away, kind, division)
    if not covered:
        resp = {
            "matchup": {"home": home, "away": away, "date": d.date().isoformat()},
            "covered": False,
            "reason": reason,
            "prediction": None,
            "supported": {"club_leagues": sorted(DIV_NAMES.values()),
                          "international": True,
                          "note": "Use /v1/teams to see supported teams."},
            "meta": {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "disclaimer": DISCLAIMER},
        }
        if cosmic:                                  # cosmic works for ANY teams
            resp["cosmic_reading"] = cosmic_reading(home, away, d)
        return resp

    if kind == "club":
        X, div = build_row_club(home, away, d, division)
        body = predict_core(CLUB, X, "club", odds)
        body["competition"] = {"kind": "club", "division": div,
                               "league": DIV_NAMES.get(div, div)}
    else:
        X = build_row_intl(home, away, d, neutral)
        body = predict_core(INTL, X, "international", odds)
        body["competition"] = {"kind": "international", "neutral": neutral}
    result = {
        "matchup": {"home": home, "away": away, "date": d.date().isoformat()},
        "covered": True,
        **body,
        "meta": {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "disclaimer": DISCLAIMER},
    }
    if cosmic:
        result["cosmic_reading"] = cosmic_reading(home, away, d)
    return result


@app.get("/")
def root():
    return {"service": "AstroPitch Prediction API", "version": "1.0",
            "docs": "/docs",
            "endpoints": ["/health", "/v1/leagues", "/v1/teams", "/v1/predict", "/v1/cosmic"],
            "auth": "open (dev)" if not _KEYS else "X-API-Key required"}


@app.get("/health")
def health():
    return {"status": "ok", "club_teams": len(CLUB_TEAMS),
            "international_teams": len(INTL_TEAMS), "leagues": len(DIV_NAMES)}


@app.get("/v1/leagues")
def leagues():
    return {"leagues": [{"code": c, "name": n} for c, n in sorted(DIV_NAMES.items())]}


@app.get("/v1/teams")
def teams(q: str = Query("", description="case-insensitive substring filter"),
          kind: str = Query("all", description="club | international | all"),
          limit: int = 50):
    ql = q.lower()
    res = []
    if kind in ("club", "all"):
        res += [{"name": t, "kind": "club", "division": TEAM_DIV.get(t)}
                for t in CLUB_TEAMS if ql in t.lower()]
    if kind in ("international", "all"):
        res += [{"name": t, "kind": "international"} for t in INTL_TEAMS if ql in t.lower()]
    res.sort(key=lambda x: x["name"])
    return {"count": len(res), "teams": res[:limit]}


@app.post("/v1/predict")
def predict_post(req: PredictRequest, x_api_key: str | None = Header(None)):
    check_key(x_api_key)
    return _do_predict(req.home, req.away, req.date, req.kind, req.division,
                       req.neutral, req.odds, req.cosmic)


@app.get("/v1/predict")
def predict_get(home: str, away: str, date: str, kind: str = "club",
                division: str | None = None, neutral: bool = False,
                cosmic: bool = False, x_api_key: str | None = Header(None)):
    check_key(x_api_key)
    return _do_predict(home, away, date, kind, division, neutral, None, cosmic)


@app.get("/v1/cosmic")
def cosmic_get(home: str, away: str, date: str, x_api_key: str | None = Header(None)):
    """The entertainment-only cosmic reading — astrology + numerology for a fixture.
    Never a prediction; carries its own disclaimer. Works for ANY team names."""
    check_key(x_api_key)
    try:
        d = pd.to_datetime(date)
    except Exception:
        raise HTTPException(422, "date must be ISO YYYY-MM-DD")
    return {"matchup": {"home": home, "away": away, "date": d.date().isoformat()},
            "cosmic_reading": cosmic_reading(home, away, d)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
