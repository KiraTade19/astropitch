"""
AstroPitch - SHOTS-ON-TARGET (xG PROXY) TEST  (measured, not assumed)
============================================================================
Best untested idea for raising REAL 1X2 accuracy. Goals are a luck-laden
OUTCOME; shots-on-target measure how a team actually PLAYED (process). A side
that consistently out-shoots opponents but hasn't been rewarded on the
scoreboard tends to regress upward - signal the goals-based model can't see.
This is a free xG proxy (HS/AS/HST/AST in club_raw, 94% coverage).

Same discipline as every other test here (esoteric, weather, referee,
momentum - all REJECTED on the holdout): identical BASE feature set + fixed
XGBoost config as 21_club_genesis.py, same 4,000-match chronological holdout,
adopt ONLY if BASE+SHOTS lowers holdout log-loss AND does so materially.

Run:  python 33_shots_test.py
============================================================================
"""
import warnings
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import log_loss, accuracy_score

warnings.filterwarnings("ignore")

CLUB_CSV = "club_raw.csv"
HOLDOUT_SIZE = 4000
BASE_ELO = 1500.0
HOME_ADV = 68.0


def k_factor(div):
    return 22 if div in {"E0", "SP1", "I1", "D1", "F1"} else 20


def gd_mult(gd):
    return 1.0 if gd <= 1 else np.log(gd + 1) * 0.75


def load():
    df = pd.read_csv(CLUB_CSV, encoding="latin-1", low_memory=False)
    for a in [c for c in df.columns if "Div" in c and c != "Div"]:
        df["Div"] = df["Div"].where(df["Div"].notna(), df[a])
    d1 = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    d2 = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    df["Date"] = d1.where(d1.notna(), d2)
    for c in ["HST", "AST", "HS", "AS"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "Div"])
    return df.sort_values("Date").reset_index(drop=True)


def build(df, lc):
    elo, hist, last_date, h2h = {}, {}, {}, {}
    sot = {}          # team -> list of (shots_on_target_for, sot_against, shots_for, shots_against)

    def R(t):
        return elo.get(t, BASE_ELO)

    def roll(team, n):
        h = hist.get(team, [])
        if not h:
            return dict(gf=1.3, ga=1.3, form=0.5)
        recent = h[-n:]
        return dict(gf=np.mean([x[0] for x in recent]), ga=np.mean([x[1] for x in recent]),
                    form=np.mean([x[2] for x in recent]) / 3.0)

    def shots(team, n):
        h = sot.get(team, [])
        if not h:                              # league-ish priors
            return dict(sf=4.4, sa=4.4, tf=12.5, ta=12.5)
        r = h[-n:]
        return dict(sf=np.mean([x[0] for x in r]), sa=np.mean([x[1] for x in r]),
                    tf=np.mean([x[2] for x in r]), ta=np.mean([x[3] for x in r]))

    rows = []
    for r in df.itertuples(index=False):
        home, away, hg, ag = r.HomeTeam, r.AwayTeam, r.FTHG, r.FTAG
        div, date = r.Div, r.Date
        if pd.isna(hg) or pd.isna(ag):
            continue
        hg, ag = int(hg), int(ag)
        h_elo, a_elo = R(home), R(away)
        exp_h = 1.0 / (1.0 + 10 ** ((a_elo - (h_elo + HOME_ADV)) / 400.0))
        h5, a5 = roll(home, 5), roll(away, 5)
        h10, a10 = roll(home, 10), roll(away, 10)
        rest_h = (date - last_date[home]).days if home in last_date else 7
        rest_a = (date - last_date[away]).days if away in last_date else 7
        key = tuple(sorted([home, away]))
        hh = h2h.get(key, [])
        hs5, as5 = shots(home, 5), shots(away, 5)
        hs10, as10 = shots(home, 10), shots(away, 10)

        rows.append(dict(
            date=date, div=div, league=lc[div],
            H_ELO=h_elo, A_ELO=a_elo, ELO_Diff=h_elo - a_elo, ELO_Exp=exp_h,
            Rest_H=min(rest_h, 60), Rest_A=min(rest_a, 60),
            Rest_Diff=min(rest_h, 60) - min(rest_a, 60),
            H_GF5=h5['gf'], H_GA5=h5['ga'], A_GF5=a5['gf'], A_GA5=a5['ga'],
            H_GF10=h10['gf'], H_GA10=h10['ga'], A_GF10=a10['gf'], A_GA10=a10['ga'],
            H_Form5=h5['form'], A_Form5=a5['form'], Form_Diff=h5['form'] - a5['form'],
            H_Exp=(h10['gf'] + a10['ga']) / 2.0, A_Exp=(a10['gf'] + h10['ga']) / 2.0,
            H2H=np.mean(hh) if hh else 0.5,
            # --- xG-proxy features under test (rolling shots on target for/against) ---
            H_SoT5=hs5['sf'], H_SoTA5=hs5['sa'], A_SoT5=as5['sf'], A_SoTA5=as5['sa'],
            H_SoT10=hs10['sf'], H_SoTA10=hs10['sa'], A_SoT10=as10['sf'], A_SoTA10=as10['sa'],
            SoT_Dom=(hs10['sf'] - hs10['sa']) - (as10['sf'] - as10['sa']),
            # shots on target MINUS goals = over/underperformance (regression signal)
            H_Overperf=h10['gf'] - hs10['sf'] * 0.29, A_Overperf=a10['gf'] - as10['sf'] * 0.29,
            home_goals=hg, away_goals=ag,
            result=("H" if hg > ag else ("A" if ag > hg else "D")),
        ))

        gd = abs(hg - ag)
        sh, sa_, ph, pa = ((1.0, 0.0, 3, 0) if hg > ag else
                           (0.0, 1.0, 0, 3) if hg < ag else (0.5, 0.5, 1, 1))
        k = k_factor(div) * gd_mult(gd)
        elo[home] = h_elo + k * (sh - exp_h)
        elo[away] = a_elo + k * (sa_ - (1 - exp_h))
        hist.setdefault(home, []).append((hg, ag, ph))
        hist.setdefault(away, []).append((ag, hg, pa))
        # shots on target for/against + total shots (fall back to goals if missing)
        hst = r.HST if not pd.isna(r.HST) else hg
        ast = r.AST if not pd.isna(r.AST) else ag
        hsh = r.HS if not pd.isna(r.HS) else hst
        ash = r.AS if not pd.isna(r.AS) else ast
        sot.setdefault(home, []).append((hst, ast, hsh, ash))
        sot.setdefault(away, []).append((ast, hst, ash, hsh))
        last_date[home] = last_date[away] = date
        h2h.setdefault(key, []).append(sh if home == key[0] else sa_)

    return pd.DataFrame(rows)


SHOT_COLS = ["H_SoT5", "H_SoTA5", "A_SoT5", "A_SoTA5", "H_SoT10", "H_SoTA10",
             "A_SoT10", "A_SoTA10", "SoT_Dom", "H_Overperf", "A_Overperf"]


def fit_eval(cols, tr, te, ytr, yte):
    kw = dict(tree_method="hist", verbosity=0, max_depth=5, learning_rate=0.05,
             n_estimators=400, subsample=0.8, colsample_bytree=0.8)
    m = xgb.XGBClassifier(objective="multi:softprob", num_class=3,
                          eval_metric="mlogloss", **kw)
    m.fit(tr[cols], ytr)
    p = m.predict_proba(te[cols])
    return (accuracy_score(yte, p.argmax(1)),
            log_loss(yte, p, labels=[0, 1, 2]), m)


def main():
    print("=" * 74)
    print(" ASTROPITCH - DO SHOTS-ON-TARGET (xG PROXY) IMPROVE THE MODEL?")
    print("=" * 74)
    df = load()
    lc = {d: i for i, d in enumerate(sorted(df["Div"].unique()))}
    print(f"\n[1/3] {len(df):,} matches. Building BASE + rolling shots-on-target...")
    feat = build(df, lc)

    BASE = [c for c in feat.columns if c not in
            (["date", "div", "home_goals", "away_goals", "result"] + SHOT_COLS)]
    SHOTS = BASE + SHOT_COLS

    split = len(feat) - HOLDOUT_SIZE
    tr, te = feat.iloc[:split], feat.iloc[split:]
    cls = {"H": 0, "D": 1, "A": 2}
    ytr, yte = tr["result"].map(cls).values, te["result"].map(cls).values
    print(f"[2/3] Train {len(tr):,} | Holdout {len(te):,} "
          f"({te.date.min().date()} -> {te.date.max().date()})")
    print(f"      H_SoT10 holdout: mean {te.H_SoT10.mean():.2f}  std {te.H_SoT10.std():.2f}")

    print("\n[3/3] BASE vs BASE+SHOTS (identical config, holdout)...\n")
    b_acc, b_ll, _ = fit_eval(BASE, tr, te, ytr, yte)
    s_acc, s_ll, sm = fit_eval(SHOTS, tr, te, ytr, yte)
    print(f"  {'model':<16s} {'1X2 acc':>9s} {'1X2 logloss':>12s}")
    print(f"  {'BASE':<16s} {b_acc*100:8.1f}% {b_ll:12.4f}")
    print(f"  {'BASE+SHOTS':<16s} {s_acc*100:8.1f}% {s_ll:12.4f}")
    print(f"\n  delta: accuracy {(s_acc-b_acc)*100:+.2f}pp   log-loss {s_ll-b_ll:+.4f}"
          f"  (negative logloss = better)")

    gain = dict(zip(SHOTS, sm.feature_importances_))
    order = [c for c, _ in sorted(gain.items(), key=lambda x: -x[1])]
    print(f"\n  Shot-feature importance ranks (of {len(SHOTS)}):")
    for c in ["SoT_Dom", "H_SoT10", "A_SoT10", "H_Overperf", "A_Overperf"]:
        print(f"    {c:<12s} rank #{order.index(c)+1:<3d} importance {gain[c]:.4f}")

    verdict = ("ADOPT" if s_ll < b_ll - 0.003 else
               "MARGINAL (real but tiny)" if s_ll < b_ll - 0.0005 else
               "REJECT (no real improvement)")
    print(f"\n  VERDICT: {verdict}")
    open("shots_report.txt", "w").write(
        f"SHOTS-ON-TARGET (xG proxy) TEST\n"
        f"BASE        acc {b_acc*100:.2f}%  logloss {b_ll:.4f}\n"
        f"BASE+SHOTS  acc {s_acc*100:.2f}%  logloss {s_ll:.4f}\n"
        f"delta acc {(s_acc-b_acc)*100:+.2f}pp  logloss {s_ll-b_ll:+.4f}\nVERDICT: {verdict}\n")


if __name__ == "__main__":
    main()
