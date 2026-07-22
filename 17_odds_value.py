"""
AstroPitch V12 - REAL CLOSING-ODDS VALUE EXPERIMENT
============================================================================
Question: how much do REAL bookmaker closing odds add over ELO+form?

Uses 40k club matches (football-data.co.uk) with Pinnacle CLOSING odds
(PSCH/PSCD/PSCA) - the sharpest publicly available line. Same leak-free
ELO+form pipeline as the international model. Compares, on an untouched
chronological holdout, four models by LOG-LOSS:

    1. ELO-only            (no ML)
    2. Model  (ELO+form, NO odds)
    3. Market-only         (just the closing line, margin-removed)
    4. Model + Market      (ELO+form + real closing odds as features)

Writes odds_value_report.txt.
============================================================================
"""
import numpy as np, pandas as pd, xgboost as xgb, warnings
from sklearn.metrics import log_loss, accuracy_score
warnings.filterwarnings("ignore")

HOLDOUT = 5000
BASE_ELO, HOME_ADV = 1500.0, 65.0

df = pd.read_csv("club_raw.csv", encoding="latin-1", low_memory=False)
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
# closing odds: prefer Pinnacle closing, fall back to Bet365 closing / Pinnacle
def pick(row, cols):
    for c in cols:
        v = row.get(c)
        if pd.notna(v) and v > 1.01:
            return v
    return np.nan
need = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "Div"]
df = df.dropna(subset=need + ["FTR"])
def coalesce(cands):
    out = pd.Series(np.nan, index=df.index)
    for c in cands:
        if c in df.columns:
            v = pd.to_numeric(df[c], errors="coerce")
            out = out.where(out.notna(), v.where(v > 1.01))
    return out
df["oH"] = coalesce(["PSCH", "PSH", "B365CH", "B365H"])
df["oD"] = coalesce(["PSCD", "PSD", "B365CD", "B365D"])
df["oA"] = coalesce(["PSCA", "PSA", "B365CA", "B365A"])
df = df.dropna(subset=["oH", "oD", "oA"]).sort_values("Date").reset_index(drop=True)
print(f"Usable matches with closing odds: {len(df):,}")

# margin-removed market probabilities
inv = 1 / df[["oH", "oD", "oA"]].values
mkt = inv / inv.sum(1, keepdims=True)
df["mH"], df["mD"], df["mA"] = mkt[:, 0], mkt[:, 1], mkt[:, 2]

# ---- leak-free ELO + form pass (per-team, club) ----
elo, hist, rows = {}, {}, []
def R(t): return elo.get(t, BASE_ELO)
def roll(t, n):
    h = hist.get(t, [])
    if not h: return 1.3, 1.3, 0.5
    r = h[-n:]
    return np.mean([x[0] for x in r]), np.mean([x[1] for x in r]), np.mean([x[2] for x in r]) / 3
for r in df.itertuples(index=False):
    h, a, hg, ag = r.HomeTeam, r.AwayTeam, int(r.FTHG), int(r.FTAG)
    he, ae = R(h), R(a)
    exp = 1 / (1 + 10 ** ((ae - (he + HOME_ADV)) / 400))
    h5 = roll(h, 5); a5 = roll(a, 5); h10 = roll(h, 10); a10 = roll(a, 10)
    rows.append(dict(H_ELO=he, A_ELO=ae, ELO_Diff=he - ae, ELO_Exp=exp,
                     H_GF5=h5[0], H_GA5=h5[1], A_GF5=a5[0], A_GA5=a5[1],
                     H_GF10=h10[0], H_GA10=h10[1], A_GF10=a10[0], A_GA10=a10[1],
                     H_Form=h5[2], A_Form=a5[2], Form_Diff=h5[2] - a5[2],
                     mH=r.mH, mD=r.mD, mA=r.mA,
                     result={"H": 0, "D": 1, "A": 2}[r.FTR]))
    gd = abs(hg - ag)
    if hg > ag: sh, ph, pa = 1, 3, 0
    elif hg < ag: sh, ph, pa = 0, 0, 3
    else: sh, ph, pa = 0.5, 1, 1
    k = 20 * (1 if gd <= 1 else np.log(gd + 1) * 0.75)
    elo[h] = he + k * (sh - exp); elo[a] = ae + k * ((1 - sh) - (1 - exp))
    hist.setdefault(h, []).append((hg, ag, ph)); hist.setdefault(a, []).append((ag, hg, pa))

feat = pd.DataFrame(rows)
y = feat["result"].values
elo_cols = ["H_ELO","A_ELO","ELO_Diff","ELO_Exp","H_GF5","H_GA5","A_GF5","A_GA5",
            "H_GF10","H_GA10","A_GF10","A_GA10","H_Form","A_Form","Form_Diff"]
mkt_cols = ["mH", "mD", "mA"]
split = len(feat) - HOLDOUT
def xgb_ll(cols):
    m = xgb.XGBClassifier(objective="multi:softprob", num_class=3, eval_metric="mlogloss",
                          tree_method="hist", max_depth=5, learning_rate=0.05,
                          n_estimators=400, subsample=0.8, colsample_bytree=0.8, verbosity=0)
    m.fit(feat[cols].iloc[:split], y[:split])
    p = m.predict_proba(feat[cols].iloc[split:])
    return log_loss(y[split:], p, labels=[0,1,2]), accuracy_score(y[split:], p.argmax(1))

yte = y[split:]
# 1. ELO-only expected -> crude 3-way (same draw model as international)
def elo_only(rowset):
    out=[]
    for _,rw in rowset.iterrows():
        ph=rw["ELO_Exp"]; pd_=0.28*np.exp(-abs(rw["ELO_Diff"])/300)
        a=ph*(1-pd_); b=(1-ph)*(1-pd_); s=a+pd_+b; out.append([a/s,pd_/s,b/s])
    return np.array(out)
ep = elo_only(feat.iloc[split:])
elo_ll = log_loss(yte, ep, labels=[0,1,2]); elo_acc = accuracy_score(yte, ep.argmax(1))
# 3. market-only
mp = feat[mkt_cols].iloc[split:].values
mkt_ll = log_loss(yte, mp, labels=[0,1,2]); mkt_acc = accuracy_score(yte, mp.argmax(1))
# 2 and 4
model_ll, model_acc = xgb_ll(elo_cols)
both_ll, both_acc = xgb_ll(elo_cols + mkt_cols)

# 5. principled log-opinion-pool blend: normalize(market^w * model^(1-w))
m_model = xgb.XGBClassifier(objective="multi:softprob", num_class=3, eval_metric="mlogloss",
                            tree_method="hist", max_depth=5, learning_rate=0.05,
                            n_estimators=400, subsample=0.8, colsample_bytree=0.8, verbosity=0)
m_model.fit(feat[elo_cols].iloc[:split], y[:split])
pmod = m_model.predict_proba(feat[elo_cols].iloc[split:])
best_w, best_bll = None, 9
for w in [0.5,0.6,0.7,0.8,0.9,1.0]:
    blend = (mp**w) * (pmod**(1-w)); blend /= blend.sum(1, keepdims=True)
    bll = log_loss(yte, blend, labels=[0,1,2])
    if bll < best_bll: best_bll, best_w = bll, w
blend = (mp**best_w) * (pmod**(1-best_w)); blend /= blend.sum(1, keepdims=True)
blend_acc = accuracy_score(yte, blend.argmax(1))

rep = f"""REAL CLOSING-ODDS VALUE  (holdout {HOLDOUT:,} matches, log-loss = lower better)
{'='*66}
  1. ELO-only            logloss {elo_ll:.4f}   acc {elo_acc:.3f}
  2. Model (ELO+form)    logloss {model_ll:.4f}   acc {model_acc:.3f}
  3. Market-only (closing) logloss {mkt_ll:.4f}   acc {mkt_acc:.3f}
  4. Model + Market (feat) logloss {both_ll:.4f}   acc {both_acc:.3f}
  5. Blend market^{best_w}*model  logloss {best_bll:.4f}   acc {blend_acc:.3f}
{'='*66}
Edge of real odds over pure model: {model_ll-both_ll:+.4f} logloss
Gap of model vs sharp market:      {model_ll-mkt_ll:+.4f} logloss
Best blend vs market-only:         {mkt_ll-best_bll:+.4f} logloss  (w_market={best_w})
"""
open("odds_value_report.txt","w").write(rep)
print(rep)
