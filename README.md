# AstroPitch ⚽🔮

Calibrated football match probabilities — **honest predictions as data**, with a
cosmic twist. AstroPitch gives the probability of every result (1X2), over/under
2.5 goals, and a full exact-score distribution, across 12 top European leagues,
all internationals, and — via clubelo ratings — essentially any European club.

---

## What makes it different

- **Leak-free & honest.** ELO + form over full history, chronological validation,
  a real untouched holdout. No shuffled cross-validation, no future in the past.
- **One coherent model.** 1X2, over/under, and every scoreline come from a single
  Dixon-Coles goal model, so the numbers never contradict each other.
- **A public track record.** We grade our own predictions — accuracy, log-loss,
  Brier, and Closing Line Value — and publish the results, good or bad.
- **We tested astrology on 44,000 matches.** It added nothing (0.0007 log-loss).
  So the cosmic layer is kept as clearly-labeled entertainment, never mixed into
  the real prediction. Honesty is the brand.

## Coverage

| Tier | Source | Teams |
|---|---|---|
| 12 core leagues | our trained engine (`club_engine.pkl`) | 355 clubs, England/Spain/Italy/Germany/France/Netherlands/Belgium/Portugal/Scotland/Turkey/Greece |
| Internationals | our trained engine (`pro_engine.pkl`) | 336 national teams |
| Rest of Europe | clubelo.com ratings (`27_euro_predict.py`) | ~600 clubs, strength-based fallback |

The API **refuses to guess** — a match with an unknown team returns
`covered: false` rather than a confident wrong answer.

## The API

```bash
pip install -r requirements.txt
python 24_api.py          # -> http://127.0.0.1:8000/docs
```

| Endpoint | Purpose |
|---|---|
| `GET /v1/predict` | 1X2, O/U 2.5, xG, exact-score distribution, **cards over/under** (add `&cosmic=true` for the reading) |
| `GET /v1/cosmic` | entertainment-only astrology/numerology reading (works for any teams) |
| `GET /v1/teams` · `GET /v1/leagues` | discover supported teams & leagues |
| `GET /health` · `GET /docs` | status & interactive docs |

Example:
```
GET /v1/predict?home=Arsenal&away=Chelsea&date=2026-08-15&kind=club
-> { "one_x_two": {"home":0.70,"draw":0.18,"away":0.12}, "over_under_2_5": {...},
     "likely_scores":[{"score":"1-1","prob":0.11}, ...], "covered": true, ... }
```

Optional auth: set `ASTROPITCH_API_KEYS="k1,k2"` to require `X-API-Key` with a
per-key daily free-tier quota (`ASTROPITCH_FREE_DAILY`, default 100).

## Pipeline

| Script | Role |
|---|---|
| `15_genesis_pro.py` / `16_predict_pro.py` | international engine (train / predict) |
| `21_club_genesis.py` | club engine trainer (`club_engine.pkl`) |
| `22_update_club_data.py` | refresh results + fixtures from football-data.co.uk |
| `23_track_record.py` | honest track record + CLV (`backfill \| grade \| predict \| live`) |
| `24_api.py` (+ `app.py`) | the prediction API |
| `26_build_site.py` | builds the public site (`docs/`) from live data |
| `27_euro_predict.py` | clubelo-powered European coverage |
| `30_daily_slate.py` | today's card (UEFA fixtures, clubelo-rated) |
| `36_weekly_slate.py` | the week-ahead card across every league we can rate |
| `.github/workflows/daily.yml` | 4× daily: refresh → grade → predict → rebuild site |
| `.github/workflows/weekly.yml` | Mon + Thu: refresh → weekly slate → rebuild site |

## Honest track record (2025-26 holdout, 4,000 matches)

| Metric | Model | Closing line (the bar) |
|---|---|---|
| 1X2 accuracy | 50.2% | 55.1% |
| 1X2 log-loss | 0.999 | 0.980 |
| Exact score top-1 | 12.8% | — |
| Value-bet ROI | **−9.8%** | — |

The market wins. We say so.

## Deploy

See [DEPLOY.md](DEPLOY.md) — free on Render (Docker), site on GitHub Pages (`/docs`).

---

*Probabilistic model output for information and entertainment, not betting advice.
18+. Please gamble responsibly.*
