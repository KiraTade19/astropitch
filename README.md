# AstroPitch ⚽🔮

Calibrated football match probabilities — **honest predictions as data**, with a
cosmic twist. AstroPitch gives the probability of every result (1X2), over/under
2.5 goals, and a full exact-score distribution, across 12 top European leagues,
all internationals, and — via clubelo ratings — essentially any European club.

---

## What makes it different

- **Leak-free & honest.** ELO + form over full history, chronological validation,
  a real untouched holdout. No shuffled cross-validation, no future in the past.
- **One coherent distribution.** The 1X2 comes from the tuned classifier; the
  Dixon-Coles scoreline matrix is then projected onto it, and over/under 2.5 is
  read off that same matrix. So the three published numbers are one distribution
  and cannot contradict each other. (They used to: over/under came from its own
  classifier and disagreed with the scorelines by up to 26 points. Deriving it
  from the matrix also scored better — log-loss 0.6843 vs 0.6881, accuracy
  55.1% vs 54.7% on the holdout.)
- **A public track record.** We grade our own predictions — accuracy, log-loss,
  Brier, and Closing Line Value — and publish the results, good or bad.
- **We tested astrology on 44,000 matches.** It added nothing (0.0007 log-loss).
  So the cosmic layer is kept as clearly-labeled entertainment, never mixed into
  the real prediction. Honesty is the brand.

## Coverage

| Tier            | Source                                     | Teams                                                                                             |
| --------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| 12 core leagues | our trained engine (`club_engine.pkl`)     | 366 clubs, England/Spain/Italy/Germany/France/Netherlands/Belgium/Portugal/Scotland/Turkey/Greece |
| Internationals  | our trained engine (`pro_engine.pkl`)      | 336 national teams                                                                                |
| Rest of Europe  | clubelo.com ratings (`27_euro_predict.py`) | ~600 clubs, strength-based fallback                                                               |

The API **refuses to guess** — a match with an unknown team returns
`covered: false` rather than a confident wrong answer.

## The API

```bash
pip install -r requirements.txt
python 24_api.py          # -> http://127.0.0.1:8000/docs
```

| Endpoint                            | Purpose                                                                                               |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `GET /v1/predict`                   | 1X2, O/U 2.5, xG, exact-score distribution, **cards over/under** (add `&cosmic=true` for the reading) |
| `GET /v1/cosmic`                    | entertainment-only astrology/numerology reading (works for any teams)                                 |
| `GET /v1/teams` · `GET /v1/leagues` | discover supported teams & leagues                                                                    |
| `GET /health` · `GET /docs`         | status & interactive docs                                                                             |

Example:

```
GET /v1/predict?home=Arsenal&away=Chelsea&date=2026-08-15&kind=club
-> { "one_x_two": {"home":0.70,"draw":0.18,"away":0.12}, "over_under_2_5": {...},
     "likely_scores":[{"score":"1-1","prob":0.11}, ...], "covered": true, ... }
```

Optional auth: set `ASTROPITCH_API_KEYS="k1,k2"` to require `X-API-Key` with a
per-key daily free-tier quota (`ASTROPITCH_FREE_DAILY`, default 100).

## Pipeline

| Script                                    | Role                                                               |
| ----------------------------------------- | ------------------------------------------------------------------ |
| `15_genesis_pro.py` / `16_predict_pro.py` | international engine (train / predict)                             |
| `21_club_genesis.py`                      | club engine trainer (`club_engine.pkl`)                            |
| `22_update_club_data.py`                  | refresh results + fixtures from football-data.co.uk                |
| `23_track_record.py`                      | honest track record + CLV (`backfill \| grade \| predict \| live`) |
| `24_api.py` (+ `app.py`)                  | the prediction API                                                 |
| `26_build_site.py`                        | builds the public site (`docs/`) from live data                    |
| `27_euro_predict.py`                      | clubelo-powered European coverage                                  |
| `30_daily_slate.py`                       | today's card (UEFA fixtures, clubelo-rated)                        |
| `36_weekly_slate.py`                      | the week-ahead card across every league we can rate                |
| `.github/workflows/daily.yml`             | 4× daily: refresh → grade → predict → rebuild site                 |
| `.github/workflows/weekly.yml`            | Mon + Thu: refresh → weekly slate → rebuild site                   |

## Honest track record (rolling 4,000-match holdout, refreshed on each retrain)

Current window: 2025-09-14 → 2026-09-10.

| Metric             | Model     | Closing line (the bar) |
| ------------------ | --------- | ----------------------- |
| 1X2 accuracy       | 50.5%     | 51.9%                    |
| 1X2 log-loss       | 0.994     | 0.982                    |
| Over/under 2.5     | 56.1%     | —                        |
| Exact score top-1  | 12.6%     | —                        |
| Value-bet ROI      | **−8.9%** | —                        |
| Closing line value | **−0.68%**| beat the close 38.9%     |

The market wins. We say so.

The closing-line column coalesces Pinnacle's closing price with an opening
price where a match is too recent for the closing line to be in the feed yet
(100% of the holdout either way); on the 1,370 matches (34%) with a confirmed
Pinnacle closing price specifically — the harder and more honest bar — it is
**51.7% / 0.9785**. The model does not merely lose to the line, it is
**subsumed** by it: blending the two, the optimal market weight is 0.883 and
the engine contributes **+0.0002 nats** — indistinguishable from zero, and
essentially unchanged from the previous retrain (0.886 / +0.0002). See
[LESSONS.md](LESSONS.md) for what follows from that.

## Deploy

See [DEPLOY.md](DEPLOY.md) — free on Render (Docker), site on GitHub Pages (`/docs`).

---

_Probabilistic model output for information and entertainment, not betting advice.
18+. Please gamble responsibly._
