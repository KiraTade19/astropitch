"""
AstroPitch - ELO MOMENTUM TEST  (measured, not assumed)
============================================================================
Untested idea: two teams can share the same ELO while one is rising and one
is collapsing - the current model can't tell them apart, because ELO is a
single point-in-time number. This adds each team's ELO TREND (change over
its last 10 and last 20 matches) as leak-free pre-match features and tests
whether it improves the goals/1X2 model on a real chronological holdout -
the same discipline used for esoteric features, weather/season, and referee
cards (25_esoteric_test.py, 29_weather_goals.py, 28_cards_model.py), all of
which were REJECTED because they didn't survive a holdout. This might be too.

Method: identical BASE feature set + trainer config as 21_club_genesis.py,
same 4,000-match chronological holdout, ONE fixed XGBoost config used for
both BASE and BASE+MOMENTUM so the comparison isolates the feature - not
hyperparameter luck. Adopt only if BASE+MOMENTUM lowers holdout log-loss.

Run:  python 32_momentum_test.py
============================================================================
"""
import warnings
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import log_loss, accuracy_score, mean_absolute_error

warnings.filterwarnings("ignore")

CLUB_CSV = "club_raw.csv"
HOLDOUT_SIZE = 4000
BASE_ELO = 1500.0
HOME_ADV = 68.0
TREND_SHORT, TREND_LONG = 10, 20

DIV_NAMES_KEYS = None  # filled after load


def k_factor(div):
    top = {"E0", "SP1", "I1", "D1", "F1"}
    return 22 if div in top else 20


def gd_mult(gd):
    return 1.0 if gd <= 1 else np.log(gd + 1) * 0.75


def load():
    df = pd.read_csv(CLUB_CSV, encoding="latin-1", low_memory=False)
    for a in [c for c in df.columns if "Div" in c and c != "Div"]:
        df["Div"] = df["Div"].where(df["Div"].notna(), df[a])
    d1 = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    d2 = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    df["Date"] = d1.where(d1.notna(), d2)
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "Div"])
    return df.sort_values("Date").reset_index(drop=True)


def build_features(df, league_codes):
    """Mirrors 21_club_genesis.build_elo_and_features exactly, plus ELO_Trend."""
    elo, hist, last_date, h2h = {}, {}, {}, {}
    elo_hist = {}          # team -> list of post-match ELO values (leak-free: read BEFORE append)

    def R(t):
        return elo.get(t, BASE_ELO)

    def team_roll(team, n):
        h = hist.get(team, [])
        if not h:
            return dict(gf=1.3, ga=1.3, form=0.5)
        recent = h[-n:]
        return dict(gf=np.mean([x[0] for x in recent]), ga=np.mean([x[1] for x in recent]),
                    form=np.mean([x[2] for x in recent]) / 3.0)

    def trend(team, n):
        h = elo_hist.get(team, [])
        if len(h) < n:
            return 0.0                      # unknown trend -> neutral, not missing
        return h[-1] - h[-n]

    rows = []
    for r in df.itertuples(index=False):
        home, away = r.HomeTeam, r.AwayTeam
        hg, ag = r.FTHG, r.FTAG
        div, date = r.Div, r.Date
        if pd.isna(hg) or pd.isna(ag):
            continue
        hg, ag = int(hg), int(ag)

        h_elo, a_elo = R(home), R(away)
        exp_h = 1.0 / (1.0 + 10 ** ((a_elo - (h_elo + HOME_ADV)) / 400.0))

        h5, a5 = team_roll(home, 5), team_roll(away, 5)
        h10, a10 = team_roll(home, 10), team_roll(away, 10)
        rest_h = (date - last_date[home]).days if home in last_date else 7
        rest_a = (date - last_date[away]).days if away in last_date else 7
        key = tuple(sorted([home, away]))
        hh = h2h.get(key, [])
        h2h_home = np.mean(hh) if hh else 0.5

        rows.append(dict(
            date=date, div=div, league=league_codes[div],
            H_ELO=h_elo, A_ELO=a_elo, ELO_Diff=h_elo - a_elo, ELO_Exp=exp_h,
            Rest_H=min(rest_h, 60), Rest_A=min(rest_a, 60),
            Rest_Diff=min(rest_h, 60) - min(rest_a, 60),
            H_GF5=h5['gf'], H_GA5=h5['ga'], A_GF5=a5['gf'], A_GA5=a5['ga'],
            H_GF10=h10['gf'], H_GA10=h10['ga'], A_GF10=a10['gf'], A_GA10=a10['ga'],
            H_Form5=h5['form'], A_Form5=a5['form'], Form_Diff=h5['form'] - a5['form'],
            H_Exp=(h10['gf'] + a10['ga']) / 2.0, A_Exp=(a10['gf'] + h10['ga']) / 2.0,
            H2H=h2h_home,
            # --- the untested feature under test ---
            H_Trend10=trend(home, TREND_SHORT), A_Trend10=trend(away, TREND_SHORT),
            H_Trend20=trend(home, TREND_LONG), A_Trend20=trend(away, TREND_LONG),
            Trend10_Diff=trend(home, TREND_SHORT) - trend(away, TREND_SHORT),
            Trend20_Diff=trend(home, TREND_LONG) - trend(away, TREND_LONG),
            home_goals=hg, away_goals=ag,
            result=("H" if hg > ag else ("A" if ag > hg else "D")),
            over25=int((hg + ag) > 2.5),
        ))

        gd = abs(hg - ag)
        if hg > ag:
            sh, sa, ph, pa = 1.0, 0.0, 3, 0
        elif hg < ag:
            sh, sa, ph, pa = 0.0, 1.0, 0, 3
        else:
            sh, sa, ph, pa = 0.5, 0.5, 1, 1
        k = k_factor(div) * gd_mult(gd)
        new_h = h_elo + k * (sh - exp_h)
        new_a = a_elo + k * (sa - (1 - exp_h))
        elo[home], elo[away] = new_h, new_a
        elo_hist.setdefault(home, []).append(new_h)
        elo_hist.setdefault(away, []).append(new_a)
        hist.setdefault(home, []).append((hg, ag, ph))
        hist.setdefault(away, []).append((ag, hg, pa))
        last_date[home] = date
        last_date[away] = date
        h2h.setdefault(key, []).append(sh if home == key[0] else sa)

    return pd.DataFrame(rows)


def evaluate(cols, Xtr, ytr, Xte, yte, y_ou_tr, y_ou_te, y_g_tr, y_g_te):
    kw = dict(tree_method="hist", verbosity=0, max_depth=5, learning_rate=0.05,
             n_estimators=400, subsample=0.8, colsample_bytree=0.8)
    clf = xgb.XGBClassifier(objective="multi:softprob", num_class=3,
                            eval_metric="mlogloss", **kw)
    clf.fit(Xtr[cols], ytr)
    p = clf.predict_proba(Xte[cols])
    acc = accuracy_score(yte, p.argmax(1))
    ll = log_loss(yte, p, labels=[0, 1, 2])

    ou = xgb.XGBClassifier(objective="binary:logistic", eval_metric="logloss", **kw)
    ou.fit(Xtr[cols], y_ou_tr)
    p_ou = ou.predict_proba(Xte[cols])[:, 1]
    ou_ll = log_loss(y_ou_te, p_ou)

    reg = xgb.XGBRegressor(objective="count:poisson", **kw)
    reg.fit(Xtr[cols], y_g_tr)
    mae = mean_absolute_error(y_g_te, reg.predict(Xte[cols]))
    return dict(acc=acc, ll=ll, ou_ll=ou_ll, mae=mae, model=clf)


def main():
    print("=" * 74)
    print(" ASTROPITCH - DOES ELO MOMENTUM IMPROVE THE MODEL?")
    print("=" * 74)
    df = load()
    lc = {d: i for i, d in enumerate(sorted(df["Div"].unique()))}
    print(f"\n[1/3] {len(df):,} matches. Building BASE + momentum features "
          f"(trend over last {TREND_SHORT}/{TREND_LONG} matches per team)...")
    feat = build_features(df, lc)
    feat["total_goals"] = feat["home_goals"] + feat["away_goals"]

    BASE = [c for c in feat.columns if c not in
            ("date", "div", "home_goals", "away_goals", "result", "over25",
             "total_goals", "H_Trend10", "A_Trend10", "H_Trend20", "A_Trend20",
             "Trend10_Diff", "Trend20_Diff")]
    MOMENTUM = BASE + ["H_Trend10", "A_Trend10", "H_Trend20", "A_Trend20",
                       "Trend10_Diff", "Trend20_Diff"]

    split = len(feat) - HOLDOUT_SIZE
    tr, te = feat.iloc[:split], feat.iloc[split:]
    cls = {"H": 0, "D": 1, "A": 2}
    ytr, yte = tr["result"].map(cls).values, te["result"].map(cls).values
    print(f"[2/3] Train {len(tr):,} | Holdout {len(te):,} "
          f"({te.date.min().date()} -> {te.date.max().date()})")

    # sanity: does the trend feature actually vary and have plausible scale?
    print(f"      H_Trend10 on holdout: mean {te.H_Trend10.mean():+.1f}  "
          f"std {te.H_Trend10.std():.1f}  range [{te.H_Trend10.min():.0f}, {te.H_Trend10.max():.0f}]")

    print("\n[3/3] Training BASE vs BASE+MOMENTUM (identical config, holdout log-loss)...\n")
    b = evaluate(BASE, tr, ytr, te, yte, tr["over25"].values, te["over25"].values,
                tr["home_goals"].values + tr["away_goals"].values,
                te["home_goals"].values + te["away_goals"].values)
    m = evaluate(MOMENTUM, tr, ytr, te, yte, tr["over25"].values, te["over25"].values,
                tr["home_goals"].values + tr["away_goals"].values,
                te["home_goals"].values + te["away_goals"].values)

    print(f"  {'model':<20s} {'1X2 acc':>9s} {'1X2 ll':>9s} {'O/U ll':>9s} {'goals MAE':>10s}")
    print(f"  {'BASE':<20s} {b['acc']*100:8.1f}% {b['ll']:9.4f} {b['ou_ll']:9.4f} {b['mae']:10.4f}")
    print(f"  {'BASE+MOMENTUM':<20s} {m['acc']*100:8.1f}% {m['ll']:9.4f} {m['ou_ll']:9.4f} {m['mae']:10.4f}")
    print(f"\n  delta (negative = improvement): 1X2 logloss {m['ll']-b['ll']:+.4f}  "
          f"O/U logloss {m['ou_ll']-b['ou_ll']:+.4f}  goals MAE {m['mae']-b['mae']:+.4f}")

    gain = dict(zip(MOMENTUM, m['model'].feature_importances_))
    trend_rank = sorted(gain.items(), key=lambda x: -x[1])
    trend_cols = ["H_Trend10", "A_Trend10", "H_Trend20", "A_Trend20",
                  "Trend10_Diff", "Trend20_Diff"]
    print("\n  Momentum feature importance ranks (of {} features):".format(len(MOMENTUM)))
    order = [c for c, _ in trend_rank]
    for c in trend_cols:
        print(f"    {c:<14s} rank #{order.index(c)+1:<3d} importance {gain[c]:.4f}")

    verdict = "ADOPT" if m['ll'] < b['ll'] - 0.001 else "REJECT (no real improvement)"
    print(f"\n  VERDICT: {verdict}")
    rep = (f"ELO MOMENTUM TEST\nBASE           acc {b['acc']*100:.1f}%  logloss {b['ll']:.4f}  "
          f"OU-logloss {b['ou_ll']:.4f}  goals-MAE {b['mae']:.4f}\n"
          f"BASE+MOMENTUM  acc {m['acc']*100:.1f}%  logloss {m['ll']:.4f}  "
          f"OU-logloss {m['ou_ll']:.4f}  goals-MAE {m['mae']:.4f}\n"
          f"delta logloss {m['ll']-b['ll']:+.4f}\nVERDICT: {verdict}\n")
    open("momentum_report.txt", "w").write(rep)


if __name__ == "__main__":
    main()
