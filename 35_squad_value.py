"""
AstroPitch - SQUAD MARKET VALUE TEST  (the one genuinely-new-information lever)
============================================================================
ELO+form describe how a team has PLAYED. Squad market value describes how good
the players ARE - and it moves on transfer activity BEFORE results catch up
(a club that just spent 200M is better than its recent form shows). That is
information the model has never seen, which is why it is worth testing.

DATA (one-time, free): Kaggle "Football Data from Transfermarkt"
(davidcariboo/player-scores). Drop these two files in this folder:
    tm_player_valuations.csv   (rename of player_valuations.csv)
    tm_clubs.csv               (rename of clubs.csv)
This script then: builds club squad-value over time, matches Transfermarkt
names to our teams, adds value features, and runs the SAME 5-window holdout
gate every other feature faced. Adopt ONLY if it beats the model on the
holdout - squad value is NOT guaranteed to help (it correlates with ELO).

Run:  python 35_squad_value.py
============================================================================
"""
import os
import re
import sys
import unicodedata
import warnings
import numpy as np
import pandas as pd
import xgboost as xgb
import importlib.util
from sklearn.metrics import log_loss

warnings.filterwarnings("ignore")

PV = "tm_player_valuations.csv"
CLUBS = "tm_clubs.csv"
CLUB_CSV = "club_raw.csv"
HOLDOUT_SIZE = 4000

_g = importlib.util.spec_from_file_location("g", "21_club_genesis.py")
gcm = importlib.util.module_from_spec(_g); _g.loader.exec_module(gcm)


def need_files():
    miss = [f for f in (PV, CLUBS) if not os.path.exists(f)]
    if miss:
        print("=" * 74)
        print(" SQUAD VALUE — data not found:", ", ".join(miss))
        print("=" * 74)
        print("""
Get it once (free) from Kaggle:
  1. Sign in at https://www.kaggle.com  (free account)
  2. Open dataset: https://www.kaggle.com/datasets/davidcariboo/player-scores
  3. Download it (Download button, top right). Unzip.
  4. Copy two files into this folder, renaming them:
        player_valuations.csv  ->  tm_player_valuations.csv
        clubs.csv              ->  tm_clubs.csv
  5. Re-run:  python 35_squad_value.py

(Or, with the Kaggle CLI + token:
    pip install kaggle
    kaggle datasets download davidcariboo/player-scores -f player_valuations.csv
    kaggle datasets download davidcariboo/player-scores -f clubs.csv
 then rename as above.)
""")
        sys.exit(1)


def norm(name):
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    drop = {"fc", "cf", "sc", "ac", "as", "afc", "cd", "ca", "ss", "us", "sv", "sk",
            "fk", "nk", "hnk", "if", "bk", "ol", "rc", "sd", "ud", "club", "de",
            "the", "1", "muenchen", "munchen"}
    toks = [t for t in s.split() if t not in drop]
    # common short/long equivalences
    repl = {"manchester": "man", "wolverhampton": "wolves", "tottenham": "spurs",
            "internazionale": "inter", "koln": "cologne", "sporting": "sporting"}
    toks = [repl.get(t, t) for t in toks]
    return "".join(toks)


def build_club_value_series():
    """Club total squad value by season (sum of players' latest value that season)."""
    pv = pd.read_csv(PV, usecols=lambda c: c in
                     ("date", "market_value_in_eur", "current_club_id", "player_id"))
    pv["date"] = pd.to_datetime(pv["date"], errors="coerce")
    pv = pv.dropna(subset=["date", "market_value_in_eur", "current_club_id"])
    pv["season"] = np.where(pv["date"].dt.month >= 7, pv["date"].dt.year, pv["date"].dt.year - 1)
    # latest valuation per player within each (club, season)
    pv = pv.sort_values("date")
    latest = pv.groupby(["current_club_id", "season", "player_id"], as_index=False).tail(1)
    cs = latest.groupby(["current_club_id", "season"], as_index=False)["market_value_in_eur"].sum()
    clubs = pd.read_csv(CLUBS, usecols=lambda c: c in ("club_id", "name"))
    cs = cs.merge(clubs, left_on="current_club_id", right_on="club_id", how="left")
    cs["key"] = cs["name"].map(norm)
    return cs.dropna(subset=["name"])[["key", "name", "season", "market_value_in_eur"]]


def load_matches():
    df = pd.read_csv(CLUB_CSV, encoding="latin-1", low_memory=False)
    for a in [c for c in df.columns if "Div" in c and c != "Div"]:
        df["Div"] = df["Div"].where(df["Div"].notna(), df[a])
    d1 = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    d2 = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    df["Date"] = d1.where(d1.notna(), d2)
    for c in ["HST", "AST"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "Div"])
    return df.sort_values("Date").reset_index(drop=True)


def main():
    need_files()
    print("=" * 74)
    print(" ASTROPITCH - SQUAD MARKET VALUE TEST")
    print("=" * 74)
    print("\n[1/4] Building club squad-value-by-season from Transfermarkt...")
    val = build_club_value_series()
    vlookup = {(r.key, int(r.season)): r.market_value_in_eur for r in val.itertuples(index=False)}
    print(f"      {val['key'].nunique()} clubs, seasons {val.season.min()}-{val.season.max()}")

    df = load_matches()
    lc = {d: i for i, d in enumerate(sorted(df["Div"].unique()))}
    feat, _ = gcm.build_elo_and_features(df, lc)  # BASE features incl. shots
    played = df.dropna(subset=["FTHG", "FTAG"]).reset_index(drop=True)
    feat["season"] = np.where(feat["date"].dt.month >= 7, feat["date"].dt.year, feat["date"].dt.year - 1)

    def val_of(team, season):
        k = norm(team)
        for s in (season, season - 1):        # fall back to prior season if missing
            if (k, s) in vlookup:
                return vlookup[(k, s)]
        return np.nan

    hv = np.array([val_of(t, s) for t, s in zip(feat["home"], feat["season"])])
    av = np.array([val_of(t, s) for t, s in zip(feat["away"], feat["season"])])
    matched = (~np.isnan(hv) & ~np.isnan(av)).mean()
    print(f"[2/4] Matched squad values to {matched*100:.0f}% of matches "
          f"(both teams). Unmatched teams sampled below.")
    if matched < 0.6:
        miss = sorted(set(feat["home"][np.isnan(hv)]) | set(feat["away"][np.isnan(av)]))
        print("      MANY UNMATCHED - name-matching needs aliases. Examples:")
        print("      " + ", ".join(list(miss)[:25]))

    med = np.nanmedian(np.concatenate([hv, av]))
    feat["H_Val"] = np.log1p(np.where(np.isnan(hv), med, hv))
    feat["A_Val"] = np.log1p(np.where(np.isnan(av), med, av))
    feat["Val_Diff"] = feat["H_Val"] - feat["A_Val"]
    VAL_COLS = ["H_Val", "A_Val", "Val_Diff"]

    BASE = [c for c in feat.columns if c not in
            (["date", "home", "away", "div", "home_goals", "away_goals",
              "result", "over25", "season"] + VAL_COLS)]
    y = feat["result"].map({"H": 0, "D": 1, "A": 2}).values

    print("\n[3/4] 5-window holdout test (BASE vs BASE+VALUE, identical config)...")
    N = len(feat)
    kw = dict(tree_method="hist", verbosity=0, max_depth=5, learning_rate=0.05,
             n_estimators=400, subsample=0.8, colsample_bytree=0.8)

    def ll(cols, tr, te, ytr, yte):
        m = xgb.XGBClassifier(objective="multi:softprob", num_class=3,
                              eval_metric="mlogloss", **kw)
        m.fit(feat[cols].iloc[tr], y[tr])
        return log_loss(y[te], m.predict_proba(feat[cols].iloc[te]), labels=[0, 1, 2])

    deltas = []
    print(f"  {'window':>22s} {'BASE':>8s} {'+VALUE':>8s} {'delta':>9s}")
    for k in range(5):
        end = N - k * 2000; s = end - 2000
        if s < 20000:
            break
        tr, te = np.arange(s), np.arange(s, end)
        b = ll(BASE, tr, te, y[tr], y[te]); v = ll(BASE + VAL_COLS, tr, te, y[tr], y[te])
        deltas.append(v - b)
        win = f"{feat['date'].iloc[s].date()}..{feat['date'].iloc[end-1].date()}"
        print(f"  {win:>22s} {b:8.4f} {v:8.4f} {v-b:+9.4f} {'OK' if v < b else 'x'}")

    deltas = np.array(deltas)
    helped = int((deltas < 0).sum())
    verdict = ("ADOPT - robust improvement, integrate into production"
               if helped >= 4 and deltas.mean() < -0.001 else
               "REJECT - not a robust improvement (likely absorbed by ELO)")
    print(f"\n[4/4] mean delta {deltas.mean():+.4f} | helped {helped}/{len(deltas)} windows")
    print(f"      VERDICT: {verdict}")
    open("squad_value_report.txt", "w").write(
        f"SQUAD MARKET VALUE TEST\nmatched {matched*100:.0f}% of matches\n"
        f"mean delta logloss {deltas.mean():+.4f} | helped {helped}/{len(deltas)} windows\n"
        f"VERDICT: {verdict}\n")


if __name__ == "__main__":
    main()
