"""
AstroPitch - WEATHER & SEASON -> GOALS  (measured, not assumed)
============================================================================
The esoteric study found a real seasonal goals effect (Jan-Feb 2.67 -> Mar-May
2.80 goals/game, a 0.135 spread) and suspected WEATHER drives it. This tests
that properly before we touch the production engine:

    BASE            = current club features (ELO + form)
    + SEASON        = month + kickoff hour
    + WEATHER       = temperature, precipitation, wind (Open-Meteo, free)

evaluated on a chronological holdout for the goals market:
    over/under 2.5  (Brier / log-loss / accuracy)   and total-goals MAE.

Weather is fetched per LEAGUE region (11 locations x one date-range request
each = 12 free API calls, cached to weather_cache.csv) rather than per stadium
— enough to capture the temperature/rain/wind seasonality that matters.

Run:  python 29_weather_goals.py
============================================================================
"""
import os
import json
import time
import urllib.request
import urllib.error
import warnings
import numpy as np
import pandas as pd
import xgboost as xgb
import importlib.util
from sklearn.metrics import (brier_score_loss, log_loss, accuracy_score,
                             mean_absolute_error)

warnings.filterwarnings("ignore")
_spec = importlib.util.spec_from_file_location("gpc", "21_club_genesis.py")
gpc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(gpc)

CACHE = "weather_cache.csv"
HOLDOUT = 6000
START, END = "2015-07-01", "2026-06-30"

# representative coordinates per division (league heartland city)
COORDS = {
    "E0": (52.48, -1.90), "E1": (52.48, -1.90),      # England
    "SP1": (40.42, -3.70), "I1": (45.46, 9.19),
    "D1": (50.11, 8.68), "F1": (48.86, 2.35),
    "N1": (52.37, 4.90), "B1": (50.85, 4.35),
    "P1": (38.72, -9.14), "SC0": (55.86, -4.25),
    "T1": (41.01, 28.98), "G1": (37.98, 23.73),
}
URL = ("https://archive-api.open-meteo.com/v1/archive?latitude={la}&longitude={lo}"
       "&start_date={s}&end_date={e}"
       "&daily=temperature_2m_mean,precipitation_sum,wind_speed_10m_max&timezone=UTC")


def _fetch_one(la, lo):
    """One location, full date range, with retry on throttling/transient errors."""
    url = URL.format(la=la, lo=lo, s=START, e=END)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last = None
    for attempt in range(6):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=90))["daily"]
            return pd.DataFrame({"date": pd.to_datetime(d["time"]),
                                 "temp": d["temperature_2m_mean"],
                                 "precip": d["precipitation_sum"],
                                 "wind": d["wind_speed_10m_max"]})
        except (urllib.error.HTTPError, urllib.error.URLError) as ex:
            code = getattr(ex, "code", None)
            if code is not None and code not in (429, 500, 502, 503, 504):
                raise
            last = ex
            wait = 12 * (attempt + 1)
            print(f"      transient error ({code or ex}); retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"open-meteo failed for ({la},{lo}) after retries: {last}")


def get_weather():
    """Daily weather per division. Resumable: progress is cached after each
    division, so a throttle/outage mid-run doesn't lose completed fetches."""
    cols = ["date", "temp", "precip", "wind", "Div"]
    have = (pd.read_csv(CACHE, parse_dates=["date"]) if os.path.exists(CACHE)
            else pd.DataFrame(columns=cols))
    done = set(have["Div"].unique()) if len(have) else set()
    by_coord = {}
    for div, (la, lo) in COORDS.items():
        if div in done:
            continue
        key = (la, lo)
        if key not in by_coord:
            twin = [d for d, c in COORDS.items() if c == key and d in done]
            if twin:                                   # same city already fetched
                by_coord[key] = have[have["Div"] == twin[0]][cols[:4]].copy()
            else:
                by_coord[key] = _fetch_one(la, lo)
                print(f"      fetched {div} ({la},{lo}): {len(by_coord[key]):,} days")
                time.sleep(6)                          # stay under burst limit
        f = by_coord[key].copy(); f["Div"] = div
        have = pd.concat([have, f], ignore_index=True)
        have.to_csv(CACHE, index=False)                # save progress each division
    have["date"] = pd.to_datetime(have["date"])       # keep merge keys aligned
    for c in ("temp", "precip", "wind"):
        have[c] = pd.to_numeric(have[c], errors="coerce")
    print(f"      weather: {len(have):,} league-days across "
          f"{have['Div'].nunique()} divisions")
    return have


def load_club():
    df = pd.read_csv("club_raw.csv", encoding="latin-1", low_memory=False)
    for a in [c for c in df.columns if "Div" in c and c != "Div"]:
        df["Div"] = df["Div"].where(df["Div"].notna(), df[a])
    d1 = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    d2 = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    df["Date"] = d1.where(d1.notna(), d2)
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "Div"])
    return df.sort_values("Date").reset_index(drop=True)


def main():
    print("=" * 74)
    print(" ASTROPITCH - DOES WEATHER / SEASON IMPROVE THE GOALS MODEL?")
    print("=" * 74)
    df = load_club()
    lc = {d: i for i, d in enumerate(sorted(df["Div"].unique()))}
    print(f"\n[1/4] {len(df):,} club matches. Fetching weather...")
    w = get_weather()

    print("[2/4] Building features (ELO/form) + season + weather...")
    feat, _ = gpc.build_elo_and_features(df, lc)
    played = df.dropna(subset=["FTHG", "FTAG"]).reset_index(drop=True)
    feat["Div"] = played["Div"].values
    feat["month"] = feat["date"].dt.month
    hr = pd.to_datetime(played["Time"], format="%H:%M", errors="coerce").dt.hour \
        if "Time" in played.columns else pd.Series(np.nan, index=played.index)
    feat["hour"] = hr.values
    feat["total_goals"] = feat["home_goals"] + feat["away_goals"]

    feat = feat.merge(w, left_on=["Div", "date"], right_on=["Div", "date"], how="left")
    got = feat[["temp", "precip", "wind"]].notna().all(1).mean()
    print(f"      weather matched on {got*100:.0f}% of matches "
          f"(temp mean {feat['temp'].mean():.1f}C, precip {feat['precip'].mean():.1f}mm)")

    BASE = [c for c in feat.columns if c not in
            ("date", "home", "away", "div", "Div", "home_goals", "away_goals",
             "result", "over25", "month", "hour", "temp", "precip", "wind",
             "total_goals")]
    SEASON = BASE + ["month", "hour"]
    FULL = SEASON + ["temp", "precip", "wind"]

    split = len(feat) - HOLDOUT
    tr, te = feat.iloc[:split], feat.iloc[split:]
    y_ou_tr, y_ou_te = tr["over25"].values, te["over25"].values
    y_g_tr, y_g_te = tr["total_goals"].values, te["total_goals"].values
    print(f"[3/4] Train {len(tr):,} | Holdout {len(te):,} "
          f"({te.date.min().date()} -> {te.date.max().date()})")

    def run(cols, label):
        clf = xgb.XGBClassifier(objective="binary:logistic", eval_metric="logloss",
                                tree_method="hist", verbosity=0, max_depth=5,
                                learning_rate=0.05, n_estimators=400,
                                subsample=0.8, colsample_bytree=0.8)
        clf.fit(tr[cols], y_ou_tr)
        p = clf.predict_proba(te[cols])[:, 1]
        reg = xgb.XGBRegressor(objective="count:poisson", tree_method="hist",
                               verbosity=0, max_depth=5, learning_rate=0.05,
                               n_estimators=400, subsample=0.8, colsample_bytree=0.8)
        reg.fit(tr[cols], y_g_tr)
        mae = mean_absolute_error(y_g_te, reg.predict(te[cols]))
        return dict(label=label, brier=brier_score_loss(y_ou_te, p),
                    ll=log_loss(y_ou_te, p), acc=accuracy_score(y_ou_te, (p > .5).astype(int)),
                    mae=mae)

    print("[4/4] Training BASE vs +SEASON vs +WEATHER...\n")
    rows = [run(BASE, "BASE (ELO+form)"), run(SEASON, "+ season (month,hour)"),
            run(FULL, "+ weather (temp,rain,wind)")]
    base_rate = y_ou_te.mean()
    print(f"  {'model':<28s} {'O/U Brier':>10s} {'log-loss':>10s} {'acc':>7s} {'goals MAE':>10s}")
    for r in rows:
        print(f"  {r['label']:<28s} {r['brier']:10.4f} {r['ll']:10.4f} "
              f"{r['acc']*100:6.1f}% {r['mae']:10.4f}")
    b0 = rows[0]
    print(f"\n  base-rate over2.5 on holdout: {base_rate*100:.1f}%")
    for r in rows[1:]:
        print(f"  {r['label']:<28s} vs BASE: Brier {r['brier']-b0['brier']:+.4f}  "
              f"log-loss {r['ll']-b0['ll']:+.4f}  MAE {r['mae']-b0['mae']:+.4f}"
              f"   {'IMPROVES' if r['ll'] < b0['ll'] else 'no gain'}")

    rep = "ASTROPITCH - WEATHER/SEASON GOALS TEST\n" + "=" * 62 + "\n"
    rep += f"Holdout {len(te):,} matches ({te.date.min().date()} -> {te.date.max().date()})\n\n"
    rep += f"{'model':<28s} {'Brier':>9s} {'logloss':>9s} {'acc':>7s} {'MAE':>9s}\n"
    for r in rows:
        rep += (f"{r['label']:<28s} {r['brier']:9.4f} {r['ll']:9.4f} "
                f"{r['acc']*100:6.1f}% {r['mae']:9.4f}\n")
    rep += "\nVerdict: adopt only the variants that actually lower holdout log-loss.\n"
    open("weather_report.txt", "w").write(rep)
    print("\nSaved weather_report.txt")


if __name__ == "__main__":
    main()
