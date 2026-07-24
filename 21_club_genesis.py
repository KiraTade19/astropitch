"""
AstroPitch V12 - CLUB GENESIS
============================================================================
The club-football counterpart to 15_genesis_pro.py. The international engine
(pro_engine.pkl) only knows national teams; ~all daily football is club, so
this trains a separate leak-free club engine on football-data.co.uk data.

Same philosophy as the international rebuild:
  1. DATA:   40k club matches (2015-2025) across 12 top European divisions,
             99.7% carrying Pinnacle CLOSING odds -> we can benchmark honestly
             against the sharpest public line.
  2. ELO:    Rebuilt across full history per team. Home advantage always on
             (no neutral club matches). Relegated teams carry ELO down.
  3. LEAK:   Single chronological pass; TimeSeriesSplit tuning + an untouched
             chronological holdout. No shuffle.
  4. LEAGUE: A league code feature lets one model learn per-division home edge
             and scoring level (Serie A vs Eredivisie differ a lot).
  5. METRIC: Optimises LOG-LOSS. Reports accuracy/Brier against real baselines
             INCLUDING a market-only baseline (the closing line) so we see the
             true size of the gap the business must respect.
  6. SCORE:  Exact score via Dixon-Coles bivariate Poisson from two goal
             regressors -> one consistent probability matrix (1X2 / O/U / score).

Run:  python 21_club_genesis.py
Outputs: club_engine.pkl + club_report.txt
============================================================================
"""
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
import warnings
from scipy.optimize import minimize_scalar
from scipy.stats import poisson
from sklearn.metrics import log_loss, accuracy_score, brier_score_loss

warnings.filterwarnings("ignore")

CLUB_CSV = "club_raw.csv"
HOLDOUT_SIZE = 4000          # last N played matches held out, untouched
OPTUNA_TRIALS = 30
RANDOM_STATE = 42

BASE_ELO = 1500.0
HOME_ADV = 68.0             # club home advantage (always applied)

# human-readable division names (football-data.co.uk codes)
DIV_NAMES = {
    "E0": "England Premier League", "E1": "England Championship",
    "SP1": "Spain La Liga", "I1": "Italy Serie A", "D1": "Germany Bundesliga",
    "F1": "France Ligue 1", "N1": "Netherlands Eredivisie", "B1": "Belgium Pro League",
    "P1": "Portugal Primeira Liga", "SC0": "Scotland Premiership",
    "T1": "Turkey Super Lig", "G1": "Greece Super League",
}


def gd_mult(gd):
    return 1.0 if gd <= 1 else np.log(gd + 1) * 0.75


def k_factor(div):
    """Slightly higher K for top leagues (more informative), lower for volatile ones."""
    top = {"E0", "SP1", "I1", "D1", "F1"}
    return 22 if div in top else 20


# ---------------------------------------------------------------------------
# ODDS: coalesce a closing line (Pinnacle closing first, then Bet365 closing)
# ---------------------------------------------------------------------------
def coalesce(df, cands):
    out = pd.Series(np.nan, index=df.index)
    for c in cands:
        if c in df.columns:
            v = pd.to_numeric(df[c], errors="coerce")
            out = out.where(out.notna(), v.where(v > 1.01))
    return out


# ---------------------------------------------------------------------------
# ELO + leak-free features (single chronological pass)
# ---------------------------------------------------------------------------
def build_elo_and_features(df, league_codes):
    elo, hist, last_date, h2h = {}, {}, {}, {}
    sot = {}          # team -> list of (shots_on_target_for, sot_against): the xG proxy

    def R(t):
        return elo.get(t, BASE_ELO)

    def team_roll(team, n):
        h = hist.get(team, [])
        if not h:
            return dict(gf=1.3, ga=1.3, form=0.5)
        recent = h[-n:]
        return dict(gf=np.mean([x[0] for x in recent]),
                    ga=np.mean([x[1] for x in recent]),
                    form=np.mean([x[2] for x in recent]) / 3.0)

    def team_shots(team, n):
        h = sot.get(team, [])
        if not h:
            return dict(sf=4.4, sa=4.4)         # league-ish prior
        r = h[-n:]
        return dict(sf=np.mean([x[0] for x in r]), sa=np.mean([x[1] for x in r]))

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
        hs10, as10 = team_shots(home, 10), team_shots(away, 10)

        rows.append(dict(
            date=date, home=home, away=away, div=div,
            league=league_codes[div],
            H_ELO=h_elo, A_ELO=a_elo, ELO_Diff=h_elo - a_elo, ELO_Exp=exp_h,
            Rest_H=min(rest_h, 60), Rest_A=min(rest_a, 60),
            Rest_Diff=min(rest_h, 60) - min(rest_a, 60),
            H_GF5=h5['gf'], H_GA5=h5['ga'], A_GF5=a5['gf'], A_GA5=a5['ga'],
            H_GF10=h10['gf'], H_GA10=h10['ga'], A_GF10=a10['gf'], A_GA10=a10['ga'],
            H_Form5=h5['form'], A_Form5=a5['form'], Form_Diff=h5['form'] - a5['form'],
            H_Exp=(h10['gf'] + a10['ga']) / 2.0, A_Exp=(a10['gf'] + h10['ga']) / 2.0,
            H2H=h2h_home,
            # xG proxy: rolling shots on target for/against (validated 33_shots_test.py)
            H_SoT10=hs10['sf'], H_SoTA10=hs10['sa'],
            A_SoT10=as10['sf'], A_SoTA10=as10['sa'],
            SoT_Dom=(hs10['sf'] - hs10['sa']) - (as10['sf'] - as10['sa']),
            home_goals=hg, away_goals=ag,
            result=("H" if hg > ag else ("A" if ag > hg else "D")),
            over25=int((hg + ag) > 2.5),
        ))

        # update state
        gd = abs(hg - ag)
        if hg > ag:
            sh, sa, ph, pa = 1.0, 0.0, 3, 0
        elif hg < ag:
            sh, sa, ph, pa = 0.0, 1.0, 0, 3
        else:
            sh, sa, ph, pa = 0.5, 0.5, 1, 1
        k = k_factor(div) * gd_mult(gd)
        elo[home] = h_elo + k * (sh - exp_h)
        elo[away] = a_elo + k * (sa - (1 - exp_h))
        hist.setdefault(home, []).append((hg, ag, ph))
        hist.setdefault(away, []).append((ag, hg, pa))
        # shots on target for/against (fall back to goals when a match lacks shot data)
        hst = getattr(r, "HST", np.nan)
        ast = getattr(r, "AST", np.nan)
        hst = hg if pd.isna(hst) else hst
        ast = ag if pd.isna(ast) else ast
        sot.setdefault(home, []).append((hst, ast))
        sot.setdefault(away, []).append((ast, hst))
        last_date[home] = date
        last_date[away] = date
        h2h.setdefault(key, []).append(sh if home == key[0] else sa)

    feat = pd.DataFrame(rows)
    # remember each team's home league (most-recent) for the predictor
    team_league = {}
    for r in df.itertuples(index=False):
        team_league[r.HomeTeam] = r.Div
    state = dict(elo=elo, hist=hist, last_date=last_date, h2h=h2h, sot=sot,
                 team_league=team_league, league_codes=league_codes)
    return feat, state


# ---------------------------------------------------------------------------
# Dixon-Coles exact-score model
# ---------------------------------------------------------------------------
def dc_tau(i, j, lam, mu, rho):
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
            M[i, j] *= dc_tau(i, j, lam, mu, rho)
    return M / M.sum()


def fit_rho(lams, mus, hg, ag):
    def nll(rho):
        s = 0.0
        for l, m, i, j in zip(lams, mus, hg, ag):
            t = dc_tau(min(i, 1), min(j, 1), l, m, rho) if (i <= 1 and j <= 1) else 1.0
            s += -(np.log(max(t, 1e-6)) + poisson.logpmf(i, l) + poisson.logpmf(j, m))
        return s
    return minimize_scalar(nll, bounds=(-0.2, 0.2), method="bounded").x


def timeseries_logloss(make_model, X, y, n_splits=4):
    from sklearn.model_selection import TimeSeriesSplit
    tss = TimeSeriesSplit(n_splits=n_splits)
    scores = []
    for tr, va in tss.split(X):
        m = make_model()
        m.fit(X.iloc[tr], y[tr])
        p = m.predict_proba(X.iloc[va])
        scores.append(log_loss(y[va], p, labels=sorted(np.unique(y))))
    return np.mean(scores)


def main():
    print("=" * 78)
    print(" ASTROPITCH V12 CLUB GENESIS  -  leak-free club-football engine")
    print("=" * 78)

    df = pd.read_csv(CLUB_CSV, encoding="latin-1", low_memory=False)
    # the CSV concatenates several football-data exports with two schemas:
    #  - some rows carry the division under a BOM-prefixed duplicate column
    #  - dates mix dd/mm/yyyy (later files) and dd/mm/yy (2015-16 files)
    for altdiv in [c for c in df.columns if "Div" in c and c != "Div"]:
        df["Div"] = df["Div"].where(df["Div"].notna(), df[altdiv])
    d1 = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")               # dd/mm/yyyy
    d2 = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")           # dd/mm/yy
    df["Date"] = d1.where(d1.notna(), d2)
    for c in ["HST", "AST"]:      # shots on target (xG proxy); may be absent in old rows
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "Div"])
    df = df.sort_values("Date").reset_index(drop=True)

    # closing line (for the market baseline + inference anchoring)
    df["oH"] = coalesce(df, ["PSCH", "PSH", "B365CH", "B365H"])
    df["oD"] = coalesce(df, ["PSCD", "PSD", "B365CD", "B365D"])
    df["oA"] = coalesce(df, ["PSCA", "PSA", "B365CA", "B365A"])

    league_codes = {d: i for i, d in enumerate(sorted(df["Div"].unique()))}
    print(f"\n[1/6] Loaded {len(df):,} club matches "
          f"({df.Date.min().date()} -> {df.Date.max().date()})")
    print(f"      Divisions ({len(league_codes)}): "
          f"{', '.join(DIV_NAMES.get(d, d) for d in league_codes)}")

    print("[2/6] Building ELO + leak-free features across full history...")
    feat, state = build_elo_and_features(df, league_codes)
    # align odds onto the feature rows (feat drops unplayed rows only; order preserved)
    played = df.dropna(subset=["FTHG", "FTAG"]).reset_index(drop=True)
    feat["oH"], feat["oD"], feat["oA"] = played["oH"].values, played["oD"].values, played["oA"].values
    print(f"      Feature matrix: {len(feat):,} played matches")

    FEATURES = [c for c in feat.columns if c not in
                ("date", "home", "away", "div", "home_goals", "away_goals",
                 "result", "over25", "oH", "oD", "oA")]

    split = len(feat) - HOLDOUT_SIZE
    train, test = feat.iloc[:split], feat.iloc[split:]
    Xtr, Xte = train[FEATURES], test[FEATURES]
    print(f"      Train: {len(train):,}  |  Untouched holdout: {len(test):,} "
          f"({test.date.min().date()} -> {test.date.max().date()})")

    cls = {"H": 0, "D": 1, "A": 2}
    ytr = train["result"].map(cls).values
    yte = test["result"].map(cls).values

    # ---------- BASELINES on holdout ----------
    print("\n[3/6] BASELINES on holdout:")
    home_rate = (yte == 0).mean()

    def elo_probs(row):
        ph = row["ELO_Exp"]
        pdraw = 0.27 * np.exp(-abs(row["ELO_Diff"]) / 300.0)
        a = ph * (1 - pdraw); b = (1 - ph) * (1 - pdraw); s = a + pdraw + b
        return [a / s, pdraw / s, b / s]
    elo_p = np.array([elo_probs(r) for _, r in test.iterrows()])
    elo_acc = accuracy_score(yte, elo_p.argmax(1))
    elo_ll = log_loss(yte, elo_p, labels=[0, 1, 2])

    # MARKET-only baseline (the sharp closing line, vig removed)
    mask_odds = test[["oH", "oD", "oA"]].notna().all(1).values
    inv = 1.0 / test.loc[mask_odds, ["oH", "oD", "oA"]].values
    mkt_p = inv / inv.sum(1, keepdims=True)
    mkt_acc = accuracy_score(yte[mask_odds], mkt_p.argmax(1))
    mkt_ll = log_loss(yte[mask_odds], mkt_p, labels=[0, 1, 2])

    print(f"      Always-Home     : acc={home_rate:6.3f}")
    print(f"      ELO-only        : acc={elo_acc:6.3f}  logloss={elo_ll:6.3f}")
    print(f"      Market (closing): acc={mkt_acc:6.3f}  logloss={mkt_ll:6.3f}  "
          f"[{mask_odds.mean()*100:.0f}% of holdout has a line]")

    # ---------- 1X2 XGBoost tuned for log-loss ----------
    print(f"\n[4/6] Tuning 1X2 XGBoost ({OPTUNA_TRIALS} trials, TimeSeriesSplit, log-loss)...")
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        params = dict(
            max_depth=trial.suggest_int("max_depth", 3, 8),
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            n_estimators=trial.suggest_int("n_estimators", 150, 700),
            min_child_weight=trial.suggest_int("min_child_weight", 1, 20),
            subsample=trial.suggest_float("subsample", 0.6, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.4, 1.0),
            gamma=trial.suggest_float("gamma", 0, 5),
            reg_alpha=trial.suggest_float("reg_alpha", 0, 3),
            reg_lambda=trial.suggest_float("reg_lambda", 0.5, 5),
        )
        mk = lambda: xgb.XGBClassifier(objective="multi:softprob", num_class=3,
                                       eval_metric="mlogloss", tree_method="hist",
                                       verbosity=0, **params)
        return timeseries_logloss(mk, Xtr, ytr)

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=OPTUNA_TRIALS, show_progress_bar=False)
    best = study.best_params
    print(f"      Best CV log-loss: {study.best_value:.4f}")

    model_1x2 = xgb.XGBClassifier(objective="multi:softprob", num_class=3,
                                  eval_metric="mlogloss", tree_method="hist",
                                  verbosity=0, **best)
    model_1x2.fit(Xtr, ytr)
    p_te = model_1x2.predict_proba(Xte)
    acc = accuracy_score(yte, p_te.argmax(1))
    ll = log_loss(yte, p_te, labels=[0, 1, 2])
    print(f"      HOLDOUT 1X2     : acc={acc:6.3f}  logloss={ll:6.3f}")

    # O/U 2.5
    ou = xgb.XGBClassifier(objective="binary:logistic", eval_metric="logloss",
                           tree_method="hist", verbosity=0,
                           max_depth=best["max_depth"], learning_rate=best["learning_rate"],
                           n_estimators=best["n_estimators"])
    ou.fit(Xtr, train["over25"].values)
    p_ou = ou.predict_proba(Xte)[:, 1]
    ou_acc = accuracy_score(test["over25"].values, (p_ou > 0.5).astype(int))
    ou_brier = brier_score_loss(test["over25"].values, p_ou)
    print(f"      HOLDOUT O/U 2.5 : acc={ou_acc:6.3f}  brier={ou_brier:6.3f}")

    # ---------- goal regressors + Dixon-Coles ----------
    print("\n[5/6] Training goal-expectation regressors + Dixon-Coles...")
    reg_kw = dict(objective="count:poisson", tree_method="hist", verbosity=0,
                  max_depth=5, learning_rate=0.05, n_estimators=400,
                  subsample=0.8, colsample_bytree=0.8)
    reg_h = xgb.XGBRegressor(**reg_kw); reg_h.fit(Xtr, train["home_goals"].values)
    reg_a = xgb.XGBRegressor(**reg_kw); reg_a.fit(Xtr, train["away_goals"].values)

    lam_tr = np.clip(reg_h.predict(Xtr), 0.15, 6)
    mu_tr = np.clip(reg_a.predict(Xtr), 0.15, 6)
    rho = fit_rho(lam_tr, mu_tr, train["home_goals"].values, train["away_goals"].values)
    print(f"      Dixon-Coles rho = {rho:.4f}")

    lam_te = np.clip(reg_h.predict(Xte), 0.15, 6)
    mu_te = np.clip(reg_a.predict(Xte), 0.15, 6)

    dc_1x2, dc_ou, dc_hit = [], [], 0
    for k in range(len(test)):
        M = dc_matrix(lam_te[k], mu_te[k], rho)
        dc_1x2.append([np.tril(M, -1).sum(), np.trace(M), np.triu(M, 1).sum()])
        io, jo = np.indices(M.shape)
        dc_ou.append(M[(io + jo) > 2].sum())
        bi, bj = np.unravel_index(M.argmax(), M.shape)
        if bi == test.iloc[k]["home_goals"] and bj == test.iloc[k]["away_goals"]:
            dc_hit += 1
    dc_1x2 = np.array(dc_1x2)
    dc_acc = accuracy_score(yte, dc_1x2.argmax(1))
    dc_ll = log_loss(yte, dc_1x2, labels=[0, 1, 2])
    dc_ou_acc = accuracy_score(test["over25"].values, (np.array(dc_ou) > 0.5).astype(int))
    score_top1 = dc_hit / len(test)
    modal = train.groupby(["home_goals", "away_goals"]).size().idxmax()
    modal_hit = ((test["home_goals"] == modal[0]) & (test["away_goals"] == modal[1])).mean()

    print(f"      Dixon-Coles 1X2 : acc={dc_acc:6.3f}  logloss={dc_ll:6.3f}")
    print(f"      Dixon-Coles O/U : acc={dc_ou_acc:6.3f}")
    print(f"      EXACT SCORE top1: {score_top1:6.3f}  (modal baseline {modal_hit:.3f})")

    # ---------- save ----------
    print("\n[6/6] Saving models...")
    joblib.dump(dict(model_1x2=model_1x2, ou=ou, reg_h=reg_h, reg_a=reg_a,
                     rho=rho, features=FEATURES, cls=cls, state=state,
                     best_params=best, div_names=DIV_NAMES),
                "club_engine.pkl")

    report = f"""ASTROPITCH V12 CLUB GENESIS - HOLDOUT REPORT
{'='*62}
Data: {len(df):,} club matches | Train {len(train):,} | Holdout {len(test):,}
Divisions: {', '.join(DIV_NAMES.get(d, d) for d in league_codes)}
Holdout window: {test.date.min().date()} -> {test.date.max().date()}

1X2 MATCH WINNER  (log-loss lower = better calibrated)
  Always-Home baseline : acc {home_rate:.3f}
  ELO-only baseline    : acc {elo_acc:.3f}  logloss {elo_ll:.3f}
  Market (closing line): acc {mkt_acc:.3f}  logloss {mkt_ll:.3f}   <- the bar
  XGBoost (tuned)      : acc {acc:.3f}  logloss {ll:.3f}
  Dixon-Coles derived  : acc {dc_acc:.3f}  logloss {dc_ll:.3f}

OVER/UNDER 2.5
  XGBoost    : acc {ou_acc:.3f}  brier {ou_brier:.3f}
  Dixon-Coles: acc {dc_ou_acc:.3f}

EXACT SCORE
  Dixon-Coles top-1 : {score_top1:.3f}
  Modal baseline    : {modal_hit:.3f}
  rho = {rho:.4f}
{'='*62}
Read: how far model log-loss sits ABOVE market log-loss = the efficiency gap.
The business lives where NO sharp line competes (thin markets, exact scores,
O/U in small books) and on honest calibration + CLV, not on beating this line.
Saved: club_engine.pkl
"""
    open("club_report.txt", "w").write(report)
    print(report)


if __name__ == "__main__":
    main()
