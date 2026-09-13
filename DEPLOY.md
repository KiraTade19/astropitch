# Deploying the AstroPitch Prediction API

The API ([24_api.py](24_api.py)) needs only itself + the two engine files
(`club_engine.pkl`, `pro_engine.pkl`) at runtime — no CSVs. Entry point is
[app.py](app.py) (`app:app`), which loads the digit-prefixed module by path.

Local check:
```bash
python 24_api.py            # -> http://127.0.0.1:8000/docs
# or the deploy entry point:
uvicorn app:app --port 8000
```

---

## Option A — Render (free, recommended)

Uses Docker so xgboost installs cleanly. Config is in [render.yaml](render.yaml).

1. Put this project in a GitHub repo (see "Git setup" below).
2. Render Dashboard → **New → Blueprint** → pick the repo → Apply.
3. First build ~3–5 min. You get `https://astropitch-api.onrender.com`.
4. Test: `curl https://<your-app>.onrender.com/health`

> Free tier sleeps after ~15 min idle; the first request then takes ~30s to
> wake. Fine for demos and low-volume B2B; upgrade when you have paying load.

## Option B — Railway / Fly.io

Both auto-detect the `Dockerfile`.
- **Railway**: New Project → Deploy from GitHub repo → it builds the Dockerfile.
- **Fly.io**: `fly launch` (accepts the Dockerfile) → `fly deploy`.

## Option C — Zero-signup local demo

Expose your local server with a tunnel to share a temporary public URL:
```bash
python 24_api.py
# in another shell:
npx localtunnel --port 8000     # or: ngrok http 8000
```

---

# Deploying the public site (docs/) to Netlify

The site is plain static HTML in `docs/`. **Netlify runs no build** — GitHub
Actions builds the pages and commits them, and Netlify just serves the result.
That is why [netlify.toml](netlify.toml) sets `command = ""`; Netlify needs
neither Python nor the `.pkl` engines.

## Connect it (one time)

1. Push this repo to GitHub (see "Git setup" below) — Netlify deploys *from*
   GitHub, so the repo must exist first.
2. Netlify → **Add new site → Import an existing project** → GitHub → pick the repo.
3. Leave the build settings alone. `netlify.toml` already sets
   *publish directory* = `docs` and an empty build command. If the UI pre-fills
   a build command, clear it.
4. **Deploy site.** First deploy is a few seconds — it is only copying files.
5. **Site configuration → Change site name** → set it to the subdomain you want,
   e.g. `astropridict`, giving `https://astropridict.netlify.app`.

> That subdomain currently returns Netlify's bare `Not Found` for every path,
> which is what Netlify serves for a name with no successful deploy behind it.
> Step 5 is what claims it.

Every later `git push` to `main` — including the bot's automated commits —
triggers a redeploy, so the site tracks the model with no extra wiring.

## What gets published

| Page | Built by | Refreshed |
|---|---|---|
| `index.html` | `26_build_site.py` → `build()` | every workflow run |
| `today.html` | `26_build_site.py` → `build_today()` | 4× daily (`daily.yml`) |
| `week.html` | `26_build_site.py` → `build_week()` | Mon + Thu (`weekly.yml`) |

`/week` and `/today` are redirected to the `.html` pages, so both forms work.

## Checking a deploy without pushing

```bash
python 22_update_club_data.py     # refresh results + upcoming fixtures
python 36_weekly_slate.py         # -> week_slate.json
python 26_build_site.py           # -> docs/
python -m http.server -d docs 8080   # open http://127.0.0.1:8080/week.html
```

---

## Turning on auth + the free tier

By default the API is **open** (dev mode). To require keys and cap free usage,
set env vars on the host:

| Env var | Effect |
|---|---|
| `ASTROPITCH_API_KEYS` | comma-separated keys; requests need `X-API-Key: <key>` |
| `ASTROPITCH_FREE_DAILY` | per-key requests/day before HTTP 429 (default 100) |

Example: `ASTROPITCH_API_KEYS=demo123,customerA` → paying customers get their own
key; the daily cap is your free-tier lever.

---

## Git setup (this project isn't a repo yet)

```bash
git init
git add .gitignore requirements.txt app.py 24_api.py Dockerfile render.yaml \
        club_engine.pkl pro_engine.pkl DEPLOY.md
git commit -m "AstroPitch prediction API + deploy config"
git branch -M main
git remote add origin https://github.com/<you>/astropitch-api.git
git push -u origin main
```

The `.dockerignore` keeps the image tiny (code + 2 pkls); training scripts and
data stay in the repo for you but are excluded from the deployed image.

---

## Before you market it publicly

The coverage guard is still open (see notes): a match with an unknown team can
name-collide and return a confident wrong answer (the "Inter" case). Add the
strict two-teams-known guard before pointing real customers at it.
```
