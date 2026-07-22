"""
AstroPitch - ESOTERIC INCLUSION TEST  (the honest experiment)
============================================================================
Adds ALL 40 esoteric features to the real club model and measures their true
contribution on the same leak-free chronological holdout as the engine.
Three models, identical XGBoost config:

  1. BASE            - real features (ELO/form/league) only
  2. BASE + ESOTERIC - real features plus every esoteric feature
  3. ESOTERIC ONLY   - can astrology/numerology predict at all, alone?

Reports 1X2 log-loss/accuracy for each, plus which esoteric features (if any)
the model leaned on (gain importance). Whatever the verdict, the features are
now generated and available for the 'cosmic reading' brand layer.

Run: python 25_esoteric_test.py   ->  esoteric_test_report.txt
============================================================================
"""
import importlib.util
import warnings
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from sklearn.metrics import log_loss, accuracy_score

warnings.filterwarnings("ignore")
spec = importlib.util.spec_from_file_location("gpc", "21_club_genesis.py")
gpc = importlib.util.module_from_spec(spec); spec.loader.exec_module(gpc)
import esoteric_features as eso

HOLDOUT = 4000
E = joblib.load("club_engine.pkl")
BASE = E["features"]
PARAMS = dict(E["best_params"])           # reuse the tuned config for a fair test


def load_clean():
    df = pd.read_csv("club_raw.csv", encoding="latin-1", low_memory=False)
    for a in [c for c in df.columns if "Div" in c and c != "Div"]:
        df["Div"] = df["Div"].where(df["Div"].notna(), df[a])
    d1 = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    d2 = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    df["Date"] = d1.where(d1.notna(), d2)
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "Div"])
    return df.sort_values("Date").reset_index(drop=True)


def mk():
    return xgb.XGBClassifier(objective="multi:softprob", num_class=3,
                             eval_metric="mlogloss", tree_method="hist",
                             verbosity=0, **PARAMS)


def evaluate(Xtr, ytr, Xte, yte):
    m = mk(); m.fit(Xtr, ytr)
    p = m.predict_proba(Xte)
    return m, accuracy_score(yte, p.argmax(1)), log_loss(yte, p, labels=[0, 1, 2])


def main():
    print("Loading + rebuilding leak-free base features...")
    df = load_clean()
    feat, _ = gpc.build_elo_and_features(df, E["state"]["league_codes"])

    print(f"Computing 40 esoteric features for {len(feat):,} matches...")
    ESO = eso.eso_column_names()
    rows = [eso.esoteric_features(h, a, d)
            for h, a, d in zip(feat["home"], feat["away"], feat["date"])]
    eso_df = pd.DataFrame(rows, index=feat.index)
    feat = pd.concat([feat, eso_df], axis=1)

    cls = {"H": 0, "D": 1, "A": 2}
    split = len(feat) - HOLDOUT
    train, test = feat.iloc[:split], feat.iloc[split:]
    ytr, yte = train["result"].map(cls).values, test["result"].map(cls).values

    print("Training BASE...")
    _, acc_b, ll_b = evaluate(train[BASE], ytr, test[BASE], yte)
    print("Training BASE + ESOTERIC...")
    m_be, acc_be, ll_be = evaluate(train[BASE + ESO], ytr, test[BASE + ESO], yte)
    print("Training ESOTERIC ONLY...")
    _, acc_e, ll_e = evaluate(train[ESO], ytr, test[ESO], yte)

    # which esoteric features did the augmented model use? (gain)
    gain = m_be.get_booster().get_score(importance_type="gain")
    eso_gain = {k: v for k, v in gain.items() if k.startswith("eso_")}
    total_gain = sum(gain.values()) or 1.0
    eso_share = sum(eso_gain.values()) / total_gain
    top_eso = sorted(eso_gain.items(), key=lambda x: -x[1])[:10]

    always_home = (yte == 0).mean()
    report = f"""ASTROPITCH - ESOTERIC INCLUSION TEST  (holdout {HOLDOUT:,}, 2025-26 season)
{'='*70}
1X2 result (log-loss lower = better; the honest scoreboard)
  Always-Home baseline      : acc {always_home:.3f}
  ESOTERIC ONLY             : acc {acc_e:.3f}   logloss {ll_e:.3f}
  BASE (real features)      : acc {acc_b:.3f}   logloss {ll_b:.3f}
  BASE + ESOTERIC (all 40)  : acc {acc_be:.3f}   logloss {ll_be:.3f}

  Esoteric's effect on the real model:
     accuracy  {acc_be-acc_b:+.4f}
     log-loss  {ll_be-ll_b:+.4f}   ({'HELPS' if ll_be < ll_b - 0.002 else 'HURTS' if ll_be > ll_b + 0.002 else 'NO EFFECT'})
     esoteric share of model gain: {eso_share*100:.1f}%

Top esoteric features by gain (if the model used any):
"""
    for k, v in top_eso:
        report += f"     {k:<22s} gain {v:8.1f}\n"
    report += f"""{'='*70}
READ: 'ESOTERIC ONLY' vs Always-Home shows if astrology/numerology predicts at
all alone. BASE+ESOTERIC vs BASE shows if it adds anything to a real model.
Per our priors this should be ~NO EFFECT - and now it's measured, not assumed.
The 40 features remain available (esoteric_features.py) for the cosmic-reading
brand layer, presented as clearly-labeled entertainment + transparent science.
"""
    open("esoteric_test_report.txt", "w").write(report)
    print("\n" + report)


if __name__ == "__main__":
    main()
