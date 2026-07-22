"""
AstroPitch - CARDS / BOOKINGS MODEL  (a new market, driven by the referee)
============================================================================
The esoteric study found the one big real signal hiding near "astrology":
the REFEREE. Card counts swing from ~3.0 to ~4.4 per game depending on who's
officiating - a huge, reliable effect that has NO bearing on who wins, but is
gold for the (thin, under-modelled) cards/bookings market.

This trains a leak-free model for TOTAL CARDS in a match and the over/under
lines (3.5 / 4.5 / 5.5). Features are all strictly pre-match:
  - referee's recent card average   (the key signal; missing 71% of the time,
                                      which XGBoost handles natively)
  - each team's recent card-involvement
  - league, match closeness (ELO diff) and importance
We measure exactly how much the referee adds by retraining without it.

Run:  python 28_cards_model.py   ->  cards_engine.pkl + cards_report.txt
============================================================================
"""
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
import importlib.util
import warnings
from scipy.stats import poisson
from sklearn.metrics import mean_absolute_error, brier_score_loss, accuracy_score

warnings.filterwarnings("ignore")
_spec = importlib.util.spec_from_file_location("gpc", "21_club_genesis.py")
gpc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(gpc)

CLUB_CSV = "club_raw.csv"
HOLDOUT = 6000
LINES = [3.5, 4.5, 5.5]


def load():
    df = pd.read_csv(CLUB_CSV, encoding="latin-1", low_memory=False)
    for a in [c for c in df.columns if "Div" in c and c != "Div"]:
        df["Div"] = df["Div"].where(df["Div"].notna(), df[a])
    d1 = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    d2 = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    df["Date"] = d1.where(d1.notna(), d2)
    for c in ["HY", "AY", "HR", "AR", "FTHG", "FTAG"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "HY", "AY", "HR", "AR", "Div"])
    df = df.sort_values("Date").reset_index(drop=True)
    df["cards"] = (df["HY"] + df["AY"] + df["HR"] + df["AR"]).astype(int)
    if "Referee" not in df.columns:
        df["Referee"] = np.nan
    return df


def build_features(df, league_codes):
    """Single chronological pass: light ELO (closeness) + rolling card signals."""
    elo, tcards, refc = {}, {}, {}
    rows = []

    def roll(store, key, n):
        h = store.get(key, [])
        return np.mean(h[-n:]) if h else np.nan

    for r in df.itertuples(index=False):
        home, away, ref, div = r.HomeTeam, r.AwayTeam, r.Referee, r.Div
        he, ae = elo.get(home, gpc.BASE_ELO), elo.get(away, gpc.BASE_ELO)
        exp_h = 1.0 / (1.0 + 10 ** ((ae - (he + gpc.HOME_ADV)) / 400.0))

        ref_key = None if (pd.isna(ref)) else str(ref)
        rows.append(dict(
            date=r.Date, league=league_codes[div], imp=gpc.k_factor(div),
            ELO_Diff=he - ae, ELO_AbsDiff=abs(he - ae), ELO_Exp=exp_h,
            H_cards5=roll(tcards, home, 5), A_cards5=roll(tcards, away, 5),
            H_cards10=roll(tcards, home, 10), A_cards10=roll(tcards, away, 10),
            ref_avg=(roll(refc, ref_key, 40) if ref_key else np.nan),
            ref_n=(len(refc.get(ref_key, [])) if ref_key else 0),
            cards=r.cards,
        ))

        # update state (ELO from the actual result; cards history)
        hg, ag = r.FTHG, r.FTAG
        if not (pd.isna(hg) or pd.isna(ag)):
            gd = abs(hg - ag)
            sh = 1.0 if hg > ag else (0.0 if hg < ag else 0.5)
            k = gpc.k_factor(div) * gpc.gd_mult(gd)
            elo[home] = he + k * (sh - exp_h)
            elo[away] = ae + k * ((1 - sh) - (1 - exp_h))
        tcards.setdefault(home, []).append(r.cards)
        tcards.setdefault(away, []).append(r.cards)
        if ref_key:
            refc.setdefault(ref_key, []).append(r.cards)

    return pd.DataFrame(rows), dict(elo=elo, tcards=tcards, refc=refc)


def over_probs(lam, line):
    """P(total cards > line) for a Poisson(lam); line is x.5 so floor = int(line)."""
    return 1.0 - poisson.cdf(int(line), lam)


def main():
    print("=" * 74)
    print(" ASTROPITCH - CARDS / BOOKINGS MODEL  (referee-driven, new market)")
    print("=" * 74)
    df = load()
    league_codes = {d: i for i, d in enumerate(sorted(df["Div"].unique()))}
    print(f"\n[1/4] {len(df):,} matches with card data "
          f"({df.Date.min().date()} -> {df.Date.max().date()}); "
          f"{df['Referee'].notna().sum():,} have a named referee.")

    feat, cstate = build_features(df, league_codes)
    ALL = ["league", "imp", "ELO_Diff", "ELO_AbsDiff", "ELO_Exp",
           "H_cards5", "A_cards5", "H_cards10", "A_cards10", "ref_avg", "ref_n"]
    NO_REF = [c for c in ALL if c not in ("ref_avg", "ref_n")]

    split = len(feat) - HOLDOUT
    tr, te = feat.iloc[:split], feat.iloc[split:]
    ytr, yte = tr["cards"].values, te["cards"].values
    print(f"[2/4] Train {len(tr):,} | Holdout {len(te):,} "
          f"({te.date.min().date()} -> {te.date.max().date()})")

    def fit(cols):
        m = xgb.XGBRegressor(objective="count:poisson", tree_method="hist", verbosity=0,
                             max_depth=5, learning_rate=0.05, n_estimators=500,
                             subsample=0.8, colsample_bytree=0.8, min_child_weight=5)
        m.fit(tr[cols], ytr)
        return m

    print("[3/4] Training cards models (with referee vs without)...")
    m_full = fit(ALL)
    m_noref = fit(NO_REF)
    lam_full = np.clip(m_full.predict(te[ALL]), 1, 12)
    lam_noref = np.clip(m_noref.predict(te[NO_REF]), 1, 12)
    base = ytr.mean()

    mae_base = mean_absolute_error(yte, np.full_like(yte, base, dtype=float))
    mae_full = mean_absolute_error(yte, lam_full)
    mae_noref = mean_absolute_error(yte, lam_noref)

    # over/under accuracy + calibration per line
    print("[4/4] Evaluating over/under lines...\n")
    lines_report = []
    for L in LINES:
        actual = (yte > L).astype(int)
        p_full = over_probs(lam_full, L)
        p_base = np.full_like(actual, (ytr > L).mean(), dtype=float)
        acc = accuracy_score(actual, (p_full > 0.5).astype(int))
        br = brier_score_loss(actual, p_full)
        br_base = brier_score_loss(actual, p_base)
        lines_report.append((L, actual.mean(), acc, br, br_base))
        print(f"  Over {L}: base-rate {actual.mean()*100:4.0f}%  |  model acc {acc*100:4.1f}%  "
              f"|  Brier {br:.3f} vs {br_base:.3f} baseline")

    # referee contribution on the subset where a ref is actually known
    ref_mask = te["ref_n"].values >= 5
    imp = dict(zip(ALL, m_full.feature_importances_))
    ref_rank = sorted(imp.items(), key=lambda x: -x[1])
    print(f"\n  MAE (cards): baseline {mae_base:.3f} | model {mae_full:.3f} | "
          f"without referee {mae_noref:.3f}")
    if ref_mask.sum() > 200:
        mae_full_r = mean_absolute_error(yte[ref_mask], lam_full[ref_mask])
        mae_noref_r = mean_absolute_error(yte[ref_mask], lam_noref[ref_mask])
        print(f"  On matches with a KNOWN referee ({ref_mask.sum():,}): "
              f"MAE {mae_noref_r:.3f} -> {mae_full_r:.3f} when the ref is added "
              f"({(mae_noref_r-mae_full_r)/mae_noref_r*100:+.1f}%)")
    print(f"  Referee feature rank: ref_avg is #{[k for k,_ in ref_rank].index('ref_avg')+1} "
          f"of {len(ALL)} features (importance {imp['ref_avg']:.3f})")

    joblib.dump(dict(model=m_full, features=ALL, league_codes=league_codes,
                     lines=LINES, base_cards=float(base), state=cstate),
                "cards_engine.pkl")

    rep = f"""ASTROPITCH CARDS / BOOKINGS MODEL - HOLDOUT REPORT
{'='*62}
Matches: {len(df):,} (card data) | Train {len(tr):,} | Holdout {len(te):,}
Mean cards/game: {df['cards'].mean():.2f}

TOTAL-CARDS accuracy (MAE, lower better)
  Baseline (mean)      : {mae_base:.3f}
  Model (no referee)   : {mae_noref:.3f}
  Model (with referee) : {mae_full:.3f}

OVER/UNDER lines (model vs base-rate Brier, lower better)
""" + "".join(
        f"  Over {L}: acc {acc*100:.1f}%  Brier {br:.3f} (base {brb:.3f})\n"
        for L, _, acc, br, brb in lines_report) + f"""
Referee is feature #{[k for k,_ in ref_rank].index('ref_avg')+1}/{len(ALL)} by importance.
{'='*62}
This is a NEW market: no sharp public line competes on cards the way it does on
1X2. Referee assignment (announced pre-match) is the key live input.
Saved: cards_engine.pkl
"""
    open("cards_report.txt", "w").write(rep)
    print("\n" + rep)


if __name__ == "__main__":
    main()
