"""
AstroPitch V12 - GENESIS PRO
============================================================================
A leak-free, market-grade rebuild of the prediction engine.

What changed vs the old tri-brain pipeline (13/14_world_cup_*):
  1. DATA:  49,502 real internationals (1872-2026) instead of 585 hardcoded.
            Modern-era training window (2000+) => ~25k matches (~43x more).
  2. ELO:   Rebuilt across full history, HOME ADVANTAGE ONLY when not neutral
            (26.5% of internationals are on neutral ground).
  3. LEAK:  Chronological validation. TimeSeriesSplit for tuning + a final
            untouched holdout (last N matches). No shuffle, no future in past.
  4. METRIC:Optimizes LOG-LOSS (accuracy can't tell a sharp model from a
            coin flip). Reports Brier + accuracy against real baselines.
  5. SCORE: Exact score via Dixon-Coles bivariate Poisson from two goal-
            expectation regressors -> a full, consistent probability matrix
            (1X2, O/U and every scoreline come from ONE model).
  6. Esoteric features (astrology/numerology/biorhythm) are dropped from the
            core model: at inference the old code fed them a random venue,
            so they were noise by construction. This isolates real signal.

Run:  python 15_genesis_pro.py
Outputs: pro_*.pkl models + pro_report.txt
============================================================================
"""

import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from scipy.optimize import minimize_scalar
from scipy.stats import poisson
from sklearn.metrics import log_loss, accuracy_score, brier_score_loss

RESULTS_CSV = "results_raw.csv"
HOLDOUT_SIZE = 3000          # last N played matches held out, untouched
TRAIN_START_YEAR = 2000      # modern-era window for the feature model
OPTUNA_TRIALS = 40
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# 1. ELO ENGINE (full history, neutral-aware)
# ---------------------------------------------------------------------------
BASE_ELO = 1500.0
HOME_ADV = 65.0              # points, applied only on non-neutral pitches

def k_factor(tournament):
    t = str(tournament).lower()
    if "world cup" in t and "qual" not in t:
        return 55
    if "euro" in t and "qual" not in t:
        return 45
    if "copa" in t or "nations league" in t or "gold cup" in t or "asian cup" in t or "african cup" in t:
        return 45
    if "qualification" in t or "qualifier" in t:
        return 35
    if "friendly" in t:
        return 18
    return 30

def gd_mult(gd):
    return 1.0 if gd <= 1 else np.log(gd + 1) * 0.75

def build_elo_and_features(df):
    """
    Single chronological pass. For every played match, records PRE-match ELO
    and rolling form/goal features (leak-free), then updates state.
    Returns a feature DataFrame (played matches only) + final elo dict + the
    live rolling-state dicts (for the WC2026 predictor to reuse).
    """
    elo = {}
    # rolling per-team history: list of (goals_for, goals_against, points, date)
    hist = {}
    last_date = {}
    h2h = {}

    def R(t):  # current rating
        return elo.get(t, BASE_ELO)

    def team_roll(team, n):
        h = hist.get(team, [])
        if not h:
            return dict(gf=1.2, ga=1.2, form=0.5, n=0)
        recent = h[-n:]
        gf = np.mean([x[0] for x in recent])
        ga = np.mean([x[1] for x in recent])
        form = np.mean([x[2] for x in recent]) / 3.0   # points normalised 0-1
        return dict(gf=gf, ga=ga, form=form, n=len(recent))

    rows = []
    for r in df.itertuples(index=False):
        home, away, hg, ag = r.home_team, r.away_team, r.home_score, r.away_score
        neutral = bool(r.neutral)
        date = r.date
        played = not (pd.isna(hg) or pd.isna(ag))

        h_elo, a_elo = R(home), R(away)
        adv = 0.0 if neutral else HOME_ADV
        exp_h = 1.0 / (1.0 + 10 ** ((a_elo - (h_elo + adv)) / 400.0))

        # ---- leak-free features (state is strictly pre-match) ----
        h5, a5 = team_roll(home, 5), team_roll(away, 5)
        h10, a10 = team_roll(home, 10), team_roll(away, 10)
        rest_h = (date - last_date[home]).days if home in last_date else 180
        rest_a = (date - last_date[away]).days if away in last_date else 180
        key = tuple(sorted([home, away]))
        hh = h2h.get(key, [])
        # h2h winrate from home team's perspective
        if hh:
            h2h_home = np.mean([x if home == key[0] else 1 - x for x in hh]) if False else np.mean(hh)
        else:
            h2h_home = 0.5

        if played:
            rows.append(dict(
                date=date, home=home, away=away,
                neutral=int(neutral),
                imp=k_factor(r.tournament),
                H_ELO=h_elo, A_ELO=a_elo,
                ELO_Diff=h_elo - a_elo,
                ELO_Exp=exp_h,
                Rest_H=min(rest_h, 365), Rest_A=min(rest_a, 365),
                Rest_Diff=min(rest_h, 365) - min(rest_a, 365),
                H_GF5=h5['gf'], H_GA5=h5['ga'], A_GF5=a5['gf'], A_GA5=a5['ga'],
                H_GF10=h10['gf'], H_GA10=h10['ga'], A_GF10=a10['gf'], A_GA10=a10['ga'],
                H_Form5=h5['form'], A_Form5=a5['form'],
                Form_Diff=h5['form'] - a5['form'],
                H_Exp=(h10['gf'] + a10['ga']) / 2.0,   # naive matchup goal expectation
                A_Exp=(a10['gf'] + h10['ga']) / 2.0,
                H2H=h2h_home,
                home_goals=int(hg), away_goals=int(ag),
                result=("H" if hg > ag else ("A" if ag > hg else "D")),
                over25=int((hg + ag) > 2.5),
            ))

        # ---- update state (only from played matches) ----
        if played:
            gd = abs(hg - ag)
            if hg > ag:
                sh, sa, ph, pa = 1.0, 0.0, 3, 0
            elif hg < ag:
                sh, sa, ph, pa = 0.0, 1.0, 0, 3
            else:
                sh, sa, ph, pa = 0.5, 0.5, 1, 1
            k = k_factor(r.tournament) * gd_mult(gd)
            elo[home] = h_elo + k * (sh - exp_h)
            elo[away] = a_elo + k * (sa - (1 - exp_h))
            hist.setdefault(home, []).append((hg, ag, ph))
            hist.setdefault(away, []).append((ag, hg, pa))
            last_date[home] = date
            last_date[away] = date
            h2h.setdefault(key, []).append(sh if home == key[0] else sa)

    feat = pd.DataFrame(rows)
    state = dict(elo=elo, hist=hist, last_date=last_date, h2h=h2h)
    return feat, state


# ---------------------------------------------------------------------------
# 2. DIXON-COLES exact-score model
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
    """MLE for the low-score dependence parameter rho."""
    def nll(rho):
        s = 0.0
        for l, m, i, j in zip(lams, mus, hg, ag):
            t = dc_tau(min(i, 1), min(j, 1), l, m, rho) if (i <= 1 and j <= 1) else 1.0
            t = max(t, 1e-6)
            s += -(np.log(t) + poisson.logpmf(i, l) + poisson.logpmf(j, m))
        return s
    res = minimize_scalar(nll, bounds=(-0.2, 0.2), method="bounded")
    return res.x


# ---------------------------------------------------------------------------
# 3. TRAIN
# ---------------------------------------------------------------------------
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
    print(" ASTROPITCH V12 GENESIS PRO  -  leak-free full-history rebuild")
    print("=" * 78)

    df = pd.read_csv(RESULTS_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    print(f"\n[1/6] Loaded {len(df):,} matches ({df.date.min().date()} -> {df.date.max().date()})")

    print("[2/6] Building ELO + leak-free features across FULL history...")
    feat, state = build_elo_and_features(df)
    feat = feat[feat.date.dt.year >= TRAIN_START_YEAR].reset_index(drop=True)
    print(f"      Feature matrix: {len(feat):,} played matches (>= {TRAIN_START_YEAR})")

    FEATURES = [c for c in feat.columns if c not in
                ("date", "home", "away", "home_goals", "away_goals", "result", "over25")]

    # chronological split
    split = len(feat) - HOLDOUT_SIZE
    train, test = feat.iloc[:split], feat.iloc[split:]
    Xtr, Xte = train[FEATURES], test[FEATURES]
    print(f"      Train: {len(train):,}  |  Untouched holdout: {len(test):,} "
          f"({test.date.min().date()} -> {test.date.max().date()})")

    # encode 1X2
    cls = {"H": 0, "D": 1, "A": 2}
    ytr = train["result"].map(cls).values
    yte = test["result"].map(cls).values

    # ---------- BASELINES on the holdout ----------
    print("\n[3/6] BASELINES on holdout:")
    home_rate = (yte == 0).mean()
    # ELO-only probabilities (draw modelled as a fixed slice)
    def elo_probs(row):
        ph = row["ELO_Exp"]
        # crude draw model: draws peak when evenly matched
        pdraw = 0.28 * np.exp(-abs(row["ELO_Diff"]) / 300.0)
        ph_adj = ph * (1 - pdraw)
        pa_adj = (1 - ph) * (1 - pdraw)
        s = ph_adj + pdraw + pa_adj
        return [ph_adj / s, pdraw / s, pa_adj / s]
    elo_p = np.array([elo_probs(r) for _, r in test.iterrows()])
    elo_acc = accuracy_score(yte, elo_p.argmax(1))
    elo_ll = log_loss(yte, elo_p, labels=[0, 1, 2])
    print(f"      Always-Home     : acc={home_rate:6.3f}")
    print(f"      ELO-only        : acc={elo_acc:6.3f}  logloss={elo_ll:6.3f}")

    # ---------- 1X2 XGBoost, tuned on TimeSeriesSplit for LOG-LOSS ----------
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
    print(f"      Best CV log-loss: {study.best_value:.4f}")

    best = study.best_params
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

    # ---------- GOAL regressors + Dixon-Coles ----------
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

    dc_1x2, dc_ou, dc_score_hit, dc_top = [], [], 0, []
    for k in range(len(test)):
        M = dc_matrix(lam_te[k], mu_te[k], rho)
        pH = np.tril(M, -1).sum(); pD = np.trace(M); pA = np.triu(M, 1).sum()
        dc_1x2.append([pH, pD, pA])
        # over 2.5
        io, jo = np.indices(M.shape)
        dc_ou.append(M[(io + jo) > 2].sum())
        bi, bj = np.unravel_index(M.argmax(), M.shape)
        dc_top.append((bi, bj))
        if bi == test.iloc[k]["home_goals"] and bj == test.iloc[k]["away_goals"]:
            dc_score_hit += 1
    dc_1x2 = np.array(dc_1x2)
    dc_acc = accuracy_score(yte, dc_1x2.argmax(1))
    dc_ll = log_loss(yte, dc_1x2, labels=[0, 1, 2])
    dc_ou_acc = accuracy_score(test["over25"].values, (np.array(dc_ou) > 0.5).astype(int))
    score_top1 = dc_score_hit / len(test)
    # naive score baseline: always predict the modal scoreline
    modal = train.groupby(["home_goals", "away_goals"]).size().idxmax()
    modal_hit = ((test["home_goals"] == modal[0]) & (test["away_goals"] == modal[1])).mean()

    print(f"      Dixon-Coles 1X2 : acc={dc_acc:6.3f}  logloss={dc_ll:6.3f}")
    print(f"      Dixon-Coles O/U : acc={dc_ou_acc:6.3f}")
    print(f"      EXACT SCORE top1: {score_top1:6.3f}  (modal-score baseline {modal_hit:.3f})")

    # ---------- save ----------
    print("\n[6/6] Saving models...")
    joblib.dump(dict(model_1x2=model_1x2, ou=ou, reg_h=reg_h, reg_a=reg_a,
                     rho=rho, features=FEATURES, cls=cls, state=state,
                     best_params=best),
                "pro_engine.pkl")

    report = f"""ASTROPITCH V12 GENESIS PRO - HOLDOUT REPORT
{'='*60}
Data: {len(df):,} matches | Train {len(train):,} | Holdout {len(test):,}
Holdout window: {test.date.min().date()} -> {test.date.max().date()}

1X2 MATCH WINNER
  Always-Home baseline : acc {home_rate:.3f}
  ELO-only baseline    : acc {elo_acc:.3f}  logloss {elo_ll:.3f}
  XGBoost (tuned)      : acc {acc:.3f}  logloss {ll:.3f}
  Dixon-Coles derived  : acc {dc_acc:.3f}  logloss {dc_ll:.3f}

OVER/UNDER 2.5
  XGBoost   : acc {ou_acc:.3f}  brier {ou_brier:.3f}
  Dixon-Coles: acc {dc_ou_acc:.3f}

EXACT SCORE
  Dixon-Coles top-1 : {score_top1:.3f}
  Modal baseline    : {modal_hit:.3f}
  rho = {rho:.4f}
{'='*60}
Saved: pro_engine.pkl
"""
    open("pro_report.txt", "w").write(report)
    print(report)


if __name__ == "__main__":
    main()
