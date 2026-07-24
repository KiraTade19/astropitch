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


_STOP = {"fc", "cf", "sc", "ac", "as", "afc", "cd", "ca", "ss", "us", "sv", "sk",
         "fk", "nk", "hnk", "if", "bk", "ol", "rc", "sd", "ud", "club", "de", "cp",
         "sl", "rsc", "bc", "sp", "the", "1", "bsc", "vfb", "vfl", "tsg", "sc", "aj"}
# football-data abbreviations Transfermarkt spells out (token-level expansion)
_EXPAND = {"ath": "athletic", "atl": "atletico", "wolves": "wolverhampton",
           "spurs": "tottenham", "man": "manchester", "utd": "united",
           "gladbach": "borussia", "dortmund": "dortmund", "betis": "betis",
           "sociedad": "sociedad", "vallecano": "rayo", "nott": "nottingham"}


def toks(name):
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    out = []
    for t in s.split():
        if t in _STOP or len(t) < 2:
            continue
        out.append(_EXPAND.get(t, t))
    return frozenset(out)


def build_pit_series():
    """POINT-IN-TIME squad value per club: stream all valuations chronologically,
    tracking each player's current club + latest value, snapshotting the club
    total after every change. Handles transfers (a player leaving subtracts from
    the old club). Returns {club_id: (dates[], values[])} + a club-name token index.
    This is strictly leak-free: a match reads only valuations dated BEFORE it."""
    pv = pd.read_csv(PV, usecols=lambda c: c in
                     ("date", "market_value_in_eur", "current_club_id", "player_id"))
    pv["date"] = pd.to_datetime(pv["date"], errors="coerce")
    pv = pv.dropna(subset=["date", "market_value_in_eur", "current_club_id"]).sort_values("date")

    from collections import defaultdict
    club_total = defaultdict(float)
    pclub, pval = {}, {}
    series = defaultdict(lambda: ([], []))
    for r in pv.itertuples(index=False):
        P, cid, val, date = r.player_id, r.current_club_id, r.market_value_in_eur, r.date
        old = pclub.get(P)
        if old is not None and old != cid:                 # transferred out
            club_total[old] -= pval[P]
            series[old][0].append(date); series[old][1].append(club_total[old])
        if old == cid:
            club_total[cid] += val - pval[P]               # value update
        else:
            club_total[cid] += val                         # joined / new
        pclub[P], pval[P] = cid, val
        series[cid][0].append(date); series[cid][1].append(club_total[cid])

    S, peak = {}, {}
    for cid, (dts, vs) in series.items():
        S[cid] = (np.array(dts, dtype="datetime64[ns]"), np.array(vs))
        peak[cid] = max(vs) if vs else 0.0

    clubs = pd.read_csv(CLUBS, usecols=lambda c: c in ("club_id", "name")).dropna(subset=["name"])
    records, postings = [], {}
    for r in clubs.itertuples(index=False):
        tk = toks(r.name)
        if not tk or r.club_id not in S:
            continue
        idx = len(records)
        records.append(dict(tokens=tk, name=r.name, cid=r.club_id, peak=peak.get(r.club_id, 0.0)))
        for t in tk:
            postings.setdefault(t, set()).add(idx)
    return S, records, postings


def make_matcher(records, postings):
    """team name -> club_id whose token set CONTAINS ours, disambiguated by peak value."""
    cache = {}

    def match(team):
        if team in cache:
            return cache[team]
        q = toks(team); res = None
        if q:
            cand = None
            for t in q:
                s = postings.get(t, set())
                cand = set(s) if cand is None else (cand & s)
                if not cand:
                    break
            if cand:
                res = records[max(cand, key=lambda i: records[i]["peak"])]["cid"]
        cache[team] = res
        return res
    return match


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
    S, records, postings = build_pit_series()
    match = make_matcher(records, postings)
    print(f"      {len(records)} clubs indexed; point-in-time value series built")

    df = load_matches()
    lc = {d: i for i, d in enumerate(sorted(df["Div"].unique()))}
    feat, _ = gcm.build_elo_and_features(df, lc)  # BASE features incl. shots

    def val_of(team, date):
        cid = match(team)
        if cid is None or cid not in S:
            return np.nan
        dts, vs = S[cid]
        i = int(np.searchsorted(dts, np.datetime64(date), "left")) - 1   # strictly before
        return vs[i] if i >= 0 else np.nan

    fdate = feat["date"].values
    hv = np.array([val_of(t, d) for t, d in zip(feat["home"], fdate)])
    av = np.array([val_of(t, d) for t, d in zip(feat["away"], fdate)])
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
