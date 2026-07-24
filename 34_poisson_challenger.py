"""
AstroPitch - POISSON CHALLENGER  (a different model structure, not more features)
============================================================================
Everything so far bolts features onto XGBoost. This is a genuinely different
model: a bivariate-Poisson / Dixon-Coles engine where every team has its own
ATTACK and DEFENCE strength, fit by time-weighted maximum likelihood. Draws
fall out of the goal distribution naturally (no bolted-on draw formula).

Fair fight: evaluated on the EXACT same last-4,000-match holdout as the shipped
XGBoost engine (which scores 1X2 logloss 0.995 / acc 0.506). To be fair to a
model that must track team drift over a season, attack/defence are REFIT rolling
(each calendar month, on all prior matches, recency-weighted) - leak-free, using
only the past, mirroring how the ELO engine updates continuously.

  goals_home ~ Poisson(exp(mu + home + att[H] + def[A]))
  goals_away ~ Poisson(exp(mu       + att[A] + def[H]))

Run:  python 34_poisson_challenger.py
============================================================================
"""
import warnings
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import log_loss, accuracy_score

warnings.filterwarnings("ignore")

CLUB_CSV = "club_raw.csv"
HOLDOUT_SIZE = 4000
HALF_LIFE_DAYS = 180          # recency weighting for the MLE fit
ALPHA = 0.008                 # small L2 (identifiability + shrink unseen teams)
MAXG = 10


def load():
    df = pd.read_csv(CLUB_CSV, encoding="latin-1", low_memory=False)
    for a in [c for c in df.columns if "Div" in c and c != "Div"]:
        df["Div"] = df["Div"].where(df["Div"].notna(), df[a])
    d1 = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    d2 = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    df["Date"] = d1.where(d1.notna(), d2)
    for c in ["FTHG", "FTAG"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "Div"])
    return df.sort_values("Date").reset_index(drop=True)


def design(df, tidx):
    """Long format: 2 rows per match (each team's scoring event).
    Columns: [attack one-hot (T)] [defence one-hot (T)] [home flag]."""
    T = len(tidx)
    n = len(df)
    rows, cols, data, y, dates = [], [], [], [], []
    for k, r in enumerate(df.itertuples(index=False)):
        h, a = tidx[r.HomeTeam], tidx[r.AwayTeam]
        # home scoring row (2k): attack=home, defence=away, home=1
        rows += [2 * k] * 3; cols += [h, T + a, 2 * T]; data += [1, 1, 1]
        y.append(int(r.FTHG)); dates.append(r.Date)
        # away scoring row (2k+1): attack=away, defence=home, home=0
        rows += [2 * k + 1] * 2; cols += [a, T + h]; data += [1, 1]
        y.append(int(r.FTAG)); dates.append(r.Date)
    X = sparse.csr_matrix((data, (rows, cols)), shape=(2 * n, 2 * T + 1))
    return X, np.array(y), pd.to_datetime(pd.Series(dates)).values   # datetime64[ns]


def dc_1x2(lam, mu):
    ph = poisson.pmf(np.arange(MAXG + 1), lam)
    pa = poisson.pmf(np.arange(MAXG + 1), mu)
    M = np.outer(ph, pa); M /= M.sum()
    return np.array([np.tril(M, -1).sum(), np.trace(M), np.triu(M, 1).sum()])


def main():
    print("=" * 74)
    print(" ASTROPITCH - POISSON ATTACK/DEFENCE CHALLENGER vs XGBOOST")
    print("=" * 74)
    df = load()
    teams = sorted(set(df.HomeTeam) | set(df.AwayTeam))
    tidx = {t: i for i, t in enumerate(teams)}
    T = len(teams)
    print(f"\n[1/3] {len(df):,} matches | {T} teams. Building design matrix...")
    X, y, dates = design(df, tidx)
    xi = np.log(2) / HALF_LIFE_DAYS

    split = len(df) - HOLDOUT_SIZE
    hold = df.iloc[split:].reset_index(drop=True)
    y3 = np.where(hold.FTHG > hold.FTAG, 0, np.where(hold.FTHG < hold.FTAG, 2, 1))
    print(f"[2/3] Holdout {len(hold):,} matches "
          f"({hold.Date.min().date()} -> {hold.Date.max().date()}), rolling monthly refit...")

    hold["ym"] = hold.Date.dt.to_period("M")
    probs = np.zeros((len(hold), 3))
    for ym, chunk in hold.groupby("ym"):
        m_start = chunk.Date.min()
        train_obs = dates < np.datetime64(m_start)          # leak-free: only the past
        w = np.exp(-xi * (np.datetime64(m_start) - dates[train_obs]).astype("timedelta64[D]").astype(float))
        reg = PoissonRegressor(alpha=ALPHA, max_iter=400, fit_intercept=True)
        reg.fit(X[train_obs], y[train_obs], sample_weight=w)
        att = reg.coef_[:T]; dfn = reg.coef_[T:2 * T]; hcoef = reg.coef_[2 * T]
        b0 = reg.intercept_
        for j, r in zip(chunk.index, chunk.itertuples(index=False)):
            hi, ai = tidx[r.HomeTeam], tidx[r.AwayTeam]
            lam = np.exp(b0 + hcoef + att[hi] + dfn[ai])
            mu = np.exp(b0 + att[ai] + dfn[hi])
            probs[j] = dc_1x2(np.clip(lam, .1, 6), np.clip(mu, .1, 6))
        print(f"      {ym}: {len(chunk):4d} matches  (trained on {int(train_obs.sum()//2):,} prior)")

    p_acc = accuracy_score(y3, probs.argmax(1))
    p_ll = log_loss(y3, probs, labels=[0, 1, 2])

    print("\n[3/3] RESULT on the identical 4,000-match holdout:")
    print(f"  {'model':<26s} {'1X2 acc':>9s} {'1X2 logloss':>12s}")
    print(f"  {'XGBoost (shipped)':<26s} {50.6:8.1f}% {0.995:12.4f}")
    print(f"  {'Poisson att/def (this)':<26s} {p_acc*100:8.1f}% {p_ll:12.4f}")
    d_ll = p_ll - 0.995
    verdict = ("POISSON WINS - ship it as the club engine" if p_ll < 0.995 - 0.002 else
               "TIE - structural ceiling confirmed, keep XGBoost" if abs(p_ll - 0.995) <= 0.002 else
               "XGBoost stays - Poisson worse")
    print(f"\n  delta logloss {d_ll:+.4f}   VERDICT: {verdict}")
    # ---- ENSEMBLE: do the two DIFFERENT models blend better than either alone? ----
    print("\n[4/4] Ensemble test (honest: pick blend weight on val, prove on test)...")
    import importlib.util
    s = importlib.util.spec_from_file_location("g", "21_club_genesis.py")
    g = importlib.util.module_from_spec(s); s.loader.exec_module(g)
    import joblib
    fdf = g.pd  # reuse
    raw = load()
    for c in ["HST", "AST"]:
        raw[c] = pd.to_numeric(raw.get(c), errors="coerce")
    lc = {d: i for i, d in enumerate(sorted(raw["Div"].unique()))}
    feat, _ = g.build_elo_and_features(raw, lc)
    E = joblib.load("club_engine.pkl")
    xgb_p = E["model_1x2"].predict_proba(feat.iloc[-HOLDOUT_SIZE:][E["features"]])

    half = HOLDOUT_SIZE // 2
    best_w, best_vll = 1.0, 9.0
    for w in np.linspace(0, 1, 21):
        blend = w * xgb_p[:half] + (1 - w) * probs[:half]
        vll = log_loss(y3[:half], blend, labels=[0, 1, 2])
        if vll < best_vll:
            best_vll, best_w = vll, w
    te = slice(half, HOLDOUT_SIZE)
    xgb_te = log_loss(y3[te], xgb_p[half:], labels=[0, 1, 2])
    blend_te = log_loss(y3[te], best_w * xgb_p[half:] + (1 - best_w) * probs[half:], labels=[0, 1, 2])
    print(f"  best blend weight (chosen on val half): XGB {best_w:.2f} / Poisson {1-best_w:.2f}")
    print(f"  TEST-half logloss:  XGBoost alone {xgb_te:.4f}  |  blend {blend_te:.4f}  "
          f"({blend_te-xgb_te:+.4f})")
    ens_verdict = ("ENSEMBLE HELPS - ship the blend" if blend_te < xgb_te - 0.001
                   else "no real ensemble gain")
    print(f"  VERDICT: {ens_verdict}")

    open("poisson_report.txt", "w").write(
        f"POISSON ATTACK/DEFENCE CHALLENGER\n"
        f"XGBoost (shipped)     acc 50.6%  logloss 0.9950\n"
        f"Poisson attack/def    acc {p_acc*100:.1f}%  logloss {p_ll:.4f}\n"
        f"delta logloss {d_ll:+.4f}\nVERDICT (standalone): {verdict}\n"
        f"Ensemble blend XGB {best_w:.2f}/Poisson {1-best_w:.2f}: "
        f"test logloss {blend_te:.4f} vs XGB {xgb_te:.4f} ({blend_te-xgb_te:+.4f})\n"
        f"VERDICT (ensemble): {ens_verdict}\n")


if __name__ == "__main__":
    main()
