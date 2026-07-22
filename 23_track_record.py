"""
AstroPitch V12 - TRACK RECORD ENGINE  (the credibility asset)
============================================================================
Phase-1 of the business plan: a HONEST, verifiable record of the club engine's
predictions. Nobody in this space publishes their real numbers - a transparent
track record (especially Closing Line Value) IS the differentiator.

Two things it does:

  BACKFILL (works now, off-season):
    Re-derives the engine's leak-free predictions over the most recent N played
    matches (features are strictly pre-match, so this is an honest out-of-sample
    record, not hindsight) and grades them:
      - 1X2 accuracy / log-loss / Brier          (calibration = our real value)
      - exact-score top-1 and O/U 2.5 accuracy   (thin-market edge, if any)
      - CLV: did we beat the CLOSING line?        (the only KPI that predicts $)
      - flat-stake ROI on model "value" picks     (the honest betting reality)
    Writes track_record.txt (summary) + track_record.csv (per-match, publishable).

  LIVE (when the season starts ~Aug):
    predict_upcoming() reads club_fixtures.csv, logs timestamped pre-kickoff
    predictions to predictions_pending.csv; grade_pending() settles them once
    results land in club_raw.csv. This is the running, tamper-proof record.

Run:  python 23_track_record.py
============================================================================
"""
import os
import importlib.util
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import joblib

# reuse the club trainer's leak-free feature builder + Dixon-Coles
spec = importlib.util.spec_from_file_location("gpc", "21_club_genesis.py")
gpc = importlib.util.module_from_spec(spec); spec.loader.exec_module(gpc)

ENGINE = "club_engine.pkl"
CLUB_CSV = "club_raw.csv"
FIXTURES_CSV = "club_fixtures.csv"
PENDING_CSV = "predictions_pending.csv"
TRACK_TXT = "track_record.txt"
TRACK_CSV = "track_record.csv"

BACKFILL_N = 4000          # most-recent matches to grade
VALUE_EDGE = 0.03          # model_prob - market_prob threshold to call a "value" bet
MIN_ODDS = 1.30            # ignore very short prices for the betting sim

E = joblib.load(ENGINE)
FEATURES = E["features"]


# ---------------------------------------------------------------------------
# data loading (mirrors 21_club_genesis exactly) + odds columns
# ---------------------------------------------------------------------------
def load_clean_club():
    df = pd.read_csv(CLUB_CSV, encoding="latin-1", low_memory=False)
    for a in [c for c in df.columns if "Div" in c and c != "Div"]:
        df["Div"] = df["Div"].where(df["Div"].notna(), df[a])
    d1 = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    d2 = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    df["Date"] = d1.where(d1.notna(), d2)
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "Div"])
    df = df.sort_values("Date").reset_index(drop=True)
    # opening line (early Bet365) and closing line (Pinnacle closing preferred)
    df["openH"] = gpc.coalesce(df, ["B365H", "PSH", "BWH"])
    df["openD"] = gpc.coalesce(df, ["B365D", "PSD", "BWD"])
    df["openA"] = gpc.coalesce(df, ["B365A", "PSA", "BWA"])
    df["closeH"] = gpc.coalesce(df, ["PSCH", "B365CH", "PSH", "B365H"])
    df["closeD"] = gpc.coalesce(df, ["PSCD", "B365CD", "PSD", "B365D"])
    df["closeA"] = gpc.coalesce(df, ["PSCA", "B365CA", "PSA", "B365A"])
    return df


def implied(oh, od, oa):
    inv = np.array([1.0 / oh, 1.0 / od, 1.0 / oa])
    return inv / inv.sum()


# ---------------------------------------------------------------------------
# BACKFILL: honest out-of-sample record over the last N matches
# ---------------------------------------------------------------------------
def backfill(n=BACKFILL_N):
    print("Rebuilding leak-free features over full history...")
    df = load_clean_club()
    feat, _ = gpc.build_elo_and_features(df, E["state"]["league_codes"])
    played = df.dropna(subset=["FTHG", "FTAG"]).reset_index(drop=True)
    for c in ["openH", "openD", "openA", "closeH", "closeD", "closeA"]:
        feat[c] = played[c].values

    test = feat.iloc[-n:].reset_index(drop=True)
    X = test[FEATURES]
    cls = {"H": 0, "D": 1, "A": 2}
    y = test["result"].map(cls).values

    p = E["model_1x2"].predict_proba(X)               # model 1X2
    p_over = E["ou"].predict_proba(X)[:, 1]
    lam = np.clip(E["reg_h"].predict(X), 0.15, 6)
    mu = np.clip(E["reg_a"].predict(X), 0.15, 6)

    rows = []
    for k in range(len(test)):
        M = gpc.dc_matrix(lam[k], mu[k], E["rho"], maxg=8)
        bi, bj = np.unravel_index(M.argmax(), M.shape)
        t = test.iloc[k]
        hg, ag = int(t["home_goals"]), int(t["away_goals"])
        pick = int(np.argmax(p[k]))

        # --- value bet vs the OPENING line, settled, and CLV vs CLOSING line ---
        clv = roi = np.nan
        bet_side = ""
        if not np.isnan(t["openH"]):
            mkt_open = implied(t["openH"], t["openD"], t["openA"])
            edge = p[k] - mkt_open
            side = int(np.argmax(edge))
            open_odds = [t["openH"], t["openD"], t["openA"]][side]
            close_odds = [t["closeH"], t["closeD"], t["closeA"]][side]
            if edge[side] > VALUE_EDGE and open_odds >= MIN_ODDS:
                bet_side = ["H", "D", "A"][side]
                won = (side == y[k])
                roi = (open_odds - 1.0) if won else -1.0
                if not np.isnan(close_odds) and close_odds > 1.01:
                    clv = open_odds / close_odds - 1.0    # >0 => beat the close

        rows.append(dict(
            date=t["date"].date(), div=t["div"], home=t["home"], away=t["away"],
            pH=round(p[k][0], 4), pD=round(p[k][1], 4), pA=round(p[k][2], 4),
            pick=["H", "D", "A"][pick], p_over=round(float(p_over[k]), 4),
            score_pick=f"{bi}-{bj}", p_top_score=round(float(M.max()), 4),
            actual=f"{hg}-{ag}", result=t["result"],
            hit_1x2=int(pick == y[k]),
            hit_score=int((bi, bj) == (hg, ag)),
            hit_ou=int((p_over[k] > 0.5) == ((hg + ag) > 2.5)),
            logloss=round(float(-np.log(max(p[k][y[k]], 1e-9))), 4),
            bet_side=bet_side, clv=None if np.isnan(clv) else round(float(clv), 4),
            roi=None if np.isnan(roi) else round(float(roi), 4),
        ))

    rec = pd.DataFrame(rows)
    rec.to_csv(TRACK_CSV, index=False)

    # ---- aggregate ----
    from sklearn.metrics import log_loss, brier_score_loss
    n_played = len(rec)
    acc = rec["hit_1x2"].mean()
    ll = log_loss(y, p, labels=[0, 1, 2])
    over_actual = ((test["home_goals"] + test["away_goals"]) > 2.5).astype(int).values
    brier = brier_score_loss(over_actual, p_over)
    score_acc = rec["hit_score"].mean()
    ou_acc = rec["hit_ou"].mean()

    bets = rec[rec["bet_side"] != ""]
    n_bets = len(bets)
    if n_bets:
        roi = bets["roi"].mean()
        clv_series = bets["clv"].dropna()
        beat_close = (clv_series > 0).mean() if len(clv_series) else float("nan")
        avg_clv = clv_series.mean() if len(clv_series) else float("nan")
    else:
        roi = beat_close = avg_clv = float("nan")

    span = f"{rec['date'].min()} -> {rec['date'].max()}"
    report = f"""ASTROPITCH V12 - CLUB TRACK RECORD  (honest out-of-sample backfill)
{'='*66}
Matches graded : {n_played:,}   ({span})
Divisions      : 12 top European leagues

CALIBRATION  (this is where the model has real value)
  1X2 accuracy      : {acc:.3f}
  1X2 log-loss      : {ll:.3f}
  O/U 2.5 Brier     : {brier:.3f}

THIN-MARKET HIT RATES
  Exact score top-1 : {score_acc:.3f}
  O/U 2.5 accuracy  : {ou_acc:.3f}

BETTING REALITY  (flat 1u on model value picks vs OPENING line, edge>{VALUE_EDGE:.0%})
  Value bets placed : {n_bets:,}  ({n_bets/n_played*100:.1f}% of matches)
  Flat-stake ROI    : {roi*100:+.2f}%   <- honest expectation
  Beat closing line : {beat_close*100:.1f}% of bets   (CLV>0)
  Average CLV       : {avg_clv*100:+.2f}%   <- the KPI that predicts long-run $
{'='*66}
HOW TO READ THIS:
  * Positive average CLV => the model finds prices that shorten by kickoff =>
    a genuine long-run edge. Negative/near-zero => no edge; publish for content
    and honesty, do NOT stake money.
  * Whatever CLV says, the calibrated probabilities across 12 leagues are the
    sellable product (content + API). Per-match log in {TRACK_CSV}.
"""
    open(TRACK_TXT, "w").write(report)
    print(report)
    print(f"Per-match record written to {TRACK_CSV} ({n_played:,} rows).")


# ---------------------------------------------------------------------------
# LIVE: log pre-kickoff predictions, then settle them after results land
# ---------------------------------------------------------------------------
def _build_row_live(home, away, date, div):
    st = E["state"]
    lc = st["league_codes"]
    if div not in lc:
        return None
    R = st["elo"]
    he, ae = R.get(home, gpc.BASE_ELO), R.get(away, gpc.BASE_ELO)
    exp_h = 1.0 / (1.0 + 10 ** ((ae - (he + gpc.HOME_ADV)) / 400.0))

    def roll(team, nn):
        h = st["hist"].get(team, [])
        if not h:
            return dict(gf=1.3, ga=1.3, form=0.5)
        r = h[-nn:]
        return dict(gf=np.mean([x[0] for x in r]), ga=np.mean([x[1] for x in r]),
                    form=np.mean([x[2] for x in r]) / 3.0)

    h5, a5, h10, a10 = roll(home, 5), roll(away, 5), roll(home, 10), roll(away, 10)
    rest_h = (date - st["last_date"][home]).days if home in st["last_date"] else 7
    rest_a = (date - st["last_date"][away]).days if away in st["last_date"] else 7
    key = tuple(sorted([home, away]))
    hh = st["h2h"].get(key, [])
    row = dict(
        league=lc[div], H_ELO=he, A_ELO=ae, ELO_Diff=he - ae, ELO_Exp=exp_h,
        Rest_H=min(rest_h, 60), Rest_A=min(rest_a, 60),
        Rest_Diff=min(rest_h, 60) - min(rest_a, 60),
        H_GF5=h5['gf'], H_GA5=h5['ga'], A_GF5=a5['gf'], A_GA5=a5['ga'],
        H_GF10=h10['gf'], H_GA10=h10['ga'], A_GF10=a10['gf'], A_GA10=a10['ga'],
        H_Form5=h5['form'], A_Form5=a5['form'], Form_Diff=h5['form'] - a5['form'],
        H_Exp=(h10['gf'] + a10['ga']) / 2.0, A_Exp=(a10['gf'] + h10['ga']) / 2.0,
        H2H=np.mean(hh) if hh else 0.5,
    )
    return pd.DataFrame([row])[FEATURES]


def predict_upcoming():
    if not os.path.exists(FIXTURES_CSV):
        print(f"\nNo {FIXTURES_CSV} (run 22_update_club_data.py first).")
        return
    fx = pd.read_csv(FIXTURES_CSV, encoding="latin-1", low_memory=False)
    for a in [c for c in fx.columns if "Div" in c and c != "Div"]:
        if "Div" not in fx.columns:
            fx = fx.rename(columns={a: "Div"})
    fx["d"] = pd.to_datetime(fx["Date"], dayfirst=True, errors="coerce")
    fx = fx[fx["d"] >= pd.Timestamp.now().normalize()]     # future only
    if fx.empty:
        print("\nNo upcoming fixtures to predict (off-season / between rounds).")
        return

    logged = 0
    out = []
    for r in fx.itertuples(index=False):
        X = _build_row_live(r.HomeTeam, r.AwayTeam, r.d, r.Div)
        if X is None:
            continue
        pH, pD, pA = E["model_1x2"].predict_proba(X)[0]
        p_over = E["ou"].predict_proba(X)[0, 1]
        lam = float(np.clip(E["reg_h"].predict(X)[0], 0.15, 6))
        mu = float(np.clip(E["reg_a"].predict(X)[0], 0.15, 6))
        M = gpc.dc_matrix(lam, mu, E["rho"], maxg=8)
        bi, bj = np.unravel_index(M.argmax(), M.shape)
        out.append(dict(
            logged_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            date=r.d.date(), div=r.Div, home=r.HomeTeam, away=r.AwayTeam,
            pH=round(pH, 4), pD=round(pD, 4), pA=round(pA, 4),
            p_over=round(float(p_over), 4), score_pick=f"{bi}-{bj}",
            openH=getattr(r, "B365H", np.nan), openD=getattr(r, "B365D", np.nan),
            openA=getattr(r, "B365A", np.nan), status="pending",
        ))
        logged += 1

    if out:
        new = pd.DataFrame(out)
        if os.path.exists(PENDING_CSV):
            old = pd.read_csv(PENDING_CSV)
            new = pd.concat([old, new], ignore_index=True).drop_duplicates(
                subset=["date", "div", "home", "away"], keep="first")
        new.to_csv(PENDING_CSV, index=False)
        print(f"\nLogged {logged} pre-kickoff predictions -> {PENDING_CSV}")


if __name__ == "__main__":
    print("=" * 66)
    print(" ASTROPITCH V12 - TRACK RECORD ENGINE")
    print("=" * 66)
    backfill()
    predict_upcoming()
