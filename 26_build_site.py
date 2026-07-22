"""
AstroPitch - STATIC SITE BUILDER  (the public credibility + brand front)
============================================================================
Generates docs/index.html from our REAL data so the public numbers are always
honest and auto-update on rebuild:
  - the transparent track record (accuracy / log-loss / CLV) from track_record.csv
  - the "we tested astrology on 44k matches" science section (measured, not claimed)
  - a live sample cosmic reading (the brand hook)

Deploy free: GitHub repo -> Settings -> Pages -> Source: main / docs.
Rebuild any time: python 26_build_site.py
============================================================================
"""
import datetime
import pandas as pd
from cosmic_reading import cosmic_reading

OUT = "docs/index.html"
API_URL = "https://astropitch-api.onrender.com"   # live API (Render)

# ---- real track-record numbers (computed live so the site can't lie) ----
r = pd.read_csv("track_record.csv")
bets = r[r["bet_side"].notna() & (r["bet_side"] != "")]
TR = dict(
    n=len(r),
    acc=r["hit_1x2"].mean(), score=r["hit_score"].mean(), ou=r["hit_ou"].mean(),
    ll=r["logloss"].mean(),
    span=f"{r['date'].min()} to {r['date'].max()}",
    n_bets=len(bets), roi=bets["roi"].mean() * 100,
    clv=bets["clv"].dropna().mean() * 100,
    beat=(bets["clv"].dropna() > 0).mean() * 100,
)
# market benchmark (from club_report.txt) + esoteric test (from esoteric_test_report.txt)
MARKET = dict(acc=0.521, ll=0.980)
ESO = dict(only_acc=0.446, only_ll=1.058, base_acc=0.502, base_ll=0.999,
           both_acc=0.503, both_ll=0.999, share=41.1)
DEMO = cosmic_reading("Real Madrid", "Barcelona",
                      datetime.date.today() + datetime.timedelta(days=14))

# ---- live record (grows once the season starts; empty off-season) ----
import os
LIVE = None
if os.path.exists("track_record_live.csv"):
    lv = pd.read_csv("track_record_live.csv")
    if len(lv):
        lb = lv[lv["bet_side"].notna() & (lv["bet_side"] != "")]
        has_clv = len(lb) and lb["clv"].notna().any()
        LIVE = dict(n=len(lv), acc=lv["hit_1x2"].mean(), ll=lv["logloss"].mean(),
                    clv=(lb["clv"].dropna().mean() * 100) if has_clv else None,
                    span=f"{lv['date'].min()} to {lv['date'].max()}")
_live_clv = f"{LIVE['clv']:+.2f}% CLV" if (LIVE and LIVE['clv'] is not None) else "CLV building"
LIVE_HTML = "" if not LIVE else (
    f'<div class="note" style="border-color:var(--grn)"><b>Live since launch:</b> '
    f'{LIVE["n"]:,} predictions graded ({LIVE["span"]}) &mdash; {LIVE["acc"]*100:.1f}% 1X2, '
    f'{LIVE["ll"]:.3f} log-loss, {_live_clv}. Logged pre-kickoff, graded automatically.</div>')

CSS = """
:root{
  --bg:#0b0f24;--bg2:#141a38;--card:#161d40;--line:#2a3566;--line2:#3a4680;
  --ink:#eef1ff;--mut:#97a2d0;--dim:#6d78a8;
  --gold:#f2c879;--gold-d:#c9973f;--pur:#b49cff;--grn:#63d6a6;--red:#ff8f8f;
  --shadow:0 1px 0 rgba(255,255,255,.04) inset,0 18px 40px -24px #000;
}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{font-family:"Public Sans",-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
font-size:16px;line-height:1.65;color:var(--ink);background:var(--bg);
background-image:
 radial-gradient(1200px 600px at 50% -10%,rgba(180,156,255,.10),transparent 60%),
 radial-gradient(900px 500px at 90% 5%,rgba(242,200,121,.07),transparent 55%),
 radial-gradient(1px 1px at 15% 22%,#fff,transparent),
 radial-gradient(1px 1px at 72% 38%,#dfe4ff,transparent),
 radial-gradient(1px 1px at 38% 62%,#fff,transparent),
 radial-gradient(1.5px 1.5px at 84% 74%,#fff6df,transparent),
 radial-gradient(1px 1px at 58% 12%,#cfe,transparent),
 radial-gradient(1px 1px at 26% 84%,#fff,transparent);
background-repeat:no-repeat;background-attachment:fixed}
.serif{font-family:"Fraunces","Iowan Old Style",Georgia,serif}
.wrap{max-width:860px;margin:0 auto;padding:0 22px}
header{text-align:center;padding:96px 20px 46px;position:relative}
.arc{width:200px;height:80px;margin:0 auto 26px;border-radius:50%/100% 100% 0 0;
border:1px solid var(--gold-d);border-bottom:0;opacity:.5;
box-shadow:0 -18px 40px -30px var(--gold)}
.dot{width:7px;height:7px;border-radius:50%;background:var(--gold);
box-shadow:0 0 12px 2px rgba(242,200,121,.7);margin:-4px auto 0}
.logo{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:64px;
line-height:1;letter-spacing:-1.5px;font-optical-sizing:auto}
.logo .o{color:var(--gold);font-style:italic}
.tag{color:var(--mut);font-size:20px;margin:16px auto 0;max-width:34ch;text-wrap:balance}
.pill{display:inline-block;margin-top:24px;padding:7px 16px;border:1px solid var(--line2);
border-radius:99px;color:var(--pur);font-size:12.5px;letter-spacing:.04em;
text-transform:uppercase;background:rgba(180,156,255,.06)}
main{display:flex;flex-direction:column}
section{padding:46px 0;border-top:1px solid var(--line)}
.eyebrow{text-transform:uppercase;letter-spacing:.16em;font-size:12px;color:var(--gold-d);
font-weight:700;margin-bottom:12px}
h2{font-family:"Fraunces",Georgia,serif;font-weight:500;font-size:34px;line-height:1.1;
letter-spacing:-.5px;margin-bottom:8px;text-wrap:balance}
h2 .em{font-style:italic;color:var(--gold)}
.sub{color:var(--mut);margin-bottom:26px;max-width:60ch}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;
box-shadow:var(--shadow)}
.stat .v{font-family:"Fraunces",Georgia,serif;font-size:34px;font-weight:600;
line-height:1;font-variant-numeric:tabular-nums}
.stat .l{color:var(--mut);font-size:13px;margin-top:8px;line-height:1.4}
.g{color:var(--gold)}.p{color:var(--pur)}.grn{color:var(--grn)}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:26px;
margin-top:18px;box-shadow:var(--shadow)}
table{width:100%;border-collapse:collapse;font-size:14.5px;font-variant-numeric:tabular-nums}
td,th{padding:11px 8px;text-align:left;border-bottom:1px solid var(--line)}
th{color:var(--dim);font-weight:600;text-transform:uppercase;letter-spacing:.05em;font-size:12px}
tr:last-child td{border-bottom:0}
.note{background:rgba(242,200,121,.05);border-left:2px solid var(--gold);padding:16px 20px;
border-radius:0 10px 10px 0;color:var(--mut);font-size:14.5px;margin-top:18px}
.note b{color:var(--ink)}
.cosmic{background:linear-gradient(165deg,#1b1442,#111739 60%);border:1px solid #3a2d6e}
.cosmic .hd{font-family:"Fraunces",Georgia,serif;font-size:22px;color:var(--gold);
margin-bottom:14px;font-weight:500}
.cosmic p{margin:9px 0;color:#dce0ff}
.disc{color:var(--dim);font-size:12.5px;font-style:italic;margin-top:16px;line-height:1.5}
.cta{display:inline-block;margin-top:10px;padding:13px 26px;
background:linear-gradient(180deg,var(--gold),var(--gold-d));
color:#241800;font-weight:700;border-radius:11px;text-decoration:none;
box-shadow:0 10px 30px -12px rgba(242,200,121,.6)}
.cta:hover{filter:brightness(1.06)}
footer{text-align:center;color:var(--dim);font-size:13px;padding:52px 22px 70px;
border-top:1px solid var(--line);line-height:1.7}
a{color:var(--pur)}a:focus-visible,.cta:focus-visible{outline:2px solid var(--gold);outline-offset:3px}
@media(max-width:560px){.logo{font-size:48px}h2{font-size:28px}header{padding:64px 18px 36px}}
"""


def stat(v, l, cls=""):
    return f'<div class="stat"><div class="v {cls}">{v}</div><div class="l">{l}</div></div>'


def build():
    cosmic_html = "".join(f"<p>{DEMO[k]}</p>" for k in
                          ["moon", "planets", "aspects", "numerology"])
    html = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AstroPitch - honest football predictions, with a cosmic twist</title>
<meta name="description" content="Calibrated football match probabilities for 12 leagues + internationals, with a transparent track record and cosmic match readings. Predictions as data, not betting advice.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..600;1,9..144,400..600&family=Public+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<div class="wrap">
<header>
  <div class="arc"></div><div class="dot"></div>
  <div class="logo">Astr<span class="o">o</span>Pitch</div>
  <div class="tag">Honest football predictions, written in the data &mdash; with a cosmic twist.</div>
  <div class="pill">Probabilities as data &middot; not betting advice</div>
</header>
<main>

<section>
  <div class="eyebrow">Performance, in the open</div>
  <h2>The <span class="em">honest</span> track record</h2>
  <div class="sub">Every model in football should show its real out-of-sample numbers. Here are ours, on {TR['n']:,} matches ({TR['span']}).</div>
  <div class="grid">
    {stat(f"{TR['acc']*100:.1f}%","1X2 accuracy")}
    {stat(f"{TR['ll']:.3f}","1X2 log-loss","p")}
    {stat(f"{TR['score']*100:.1f}%","exact score top-1","g")}
    {stat(f"{TR['ou']*100:.1f}%","over/under 2.5")}
  </div>
  {LIVE_HTML}
  <div class="note">
    <b>We don't claim to beat the bookmaker.</b> On these {TR['n']:,} matches the closing line
    scored {MARKET['acc']*100:.1f}% / {MARKET['ll']:.3f} log-loss &mdash; sharper than us, as an efficient market should be.
    We even tested flat-staking our model's "value" picks: <b>{TR['roi']:+.1f}% ROI</b>,
    average CLV <b>{TR['clv']:+.2f}%</b> (beat the close {TR['beat']:.0f}% of the time).
    So we publish probabilities as insight and entertainment &mdash; not a betting edge, because honestly there isn't one.
  </div>
</section>

<section>
  <div class="eyebrow">The experiment</div>
  <h2>We tested <span class="em">astrology</span> on 44,000 matches</h2>
  <div class="sub">AstroPitch started as an astrology experiment. So we did the experiment properly &mdash; and we'll tell you exactly what we found.</div>
  <div class="card">
    <table>
      <tr><th>Model</th><th>1X2 accuracy</th><th>log-loss</th></tr>
      <tr><td>Always pick home (baseline)</td><td>43.0%</td><td>&mdash;</td></tr>
      <tr><td>Astrology + numerology <i>only</i></td><td>{ESO['only_acc']*100:.1f}%</td><td>{ESO['only_ll']:.3f}</td></tr>
      <tr><td>Our real model</td><td>{ESO['base_acc']*100:.1f}%</td><td>{ESO['base_ll']:.3f}</td></tr>
      <tr><td>Real model + all 40 cosmic features</td><td>{ESO['both_acc']*100:.1f}%</td><td>{ESO['both_ll']:.3f}</td></tr>
    </table>
    <div class="note">The cosmos added <b>nothing</b>: 40 astrology, numerology, biorhythm and
    Chinese-zodiac features changed our log-loss by 0.0007 &mdash; pure noise. Moon phase across
    44,325 real matches shifts goals-per-game by 0.03 (also noise). The stars are beautiful.
    They do not pick winners. We think honesty about that is more interesting than pretending.</div>
  </div>
</section>

<section>
  <div class="eyebrow">For fun &mdash; strictly</div>
  <h2>Your match's <span class="em">cosmic reading</span></h2>
  <div class="sub">For fun &mdash; a full astrological + numerological reading for any fixture on Earth, even ones our model doesn't cover.</div>
  <div class="card cosmic">
    <div class="hd">Real Madrid vs Barcelona &nbsp;&middot;&nbsp; {DEMO['headline']}</div>
    {cosmic_html}
    <p class="p">{DEMO['cosmic_leaning']}</p>
    <div class="disc">{DEMO['disclaimer']}</div>
  </div>
</section>

<section>
  <div class="eyebrow">The product</div>
  <h2>What you get</h2>
  <div class="grid">
    <div class="stat"><div class="v g">12</div><div class="l">top leagues + all internationals, calibrated 1X2 / O/U / exact-score probabilities</div></div>
    <div class="stat"><div class="v p">&#8734;</div><div class="l">cosmic readings for any match on Earth</div></div>
    <div class="stat"><div class="v">API</div><div class="l">clean JSON for apps, bots &amp; media &mdash; probabilities as data</div></div>
  </div>
  <div class="card" style="text-align:center">
    <p style="color:var(--mut)">Build on the data.</p>
    <a class="cta" href="{API_URL}/docs">Explore the API &rarr;</a>
  </div>
</section>
</main>
<footer>
  AstroPitch &middot; predictions are probabilistic model output for information and entertainment,
  not betting advice. 18+. Please gamble responsibly.<br>
  Track record rebuilt {datetime.date.today().isoformat()} from live data.
</footer>
</div></body></html>"""

    import os
    os.makedirs("docs", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT}  ({len(html):,} bytes)")
    print(f"Track record: {TR['n']:,} matches | 1X2 {TR['acc']*100:.1f}% | "
          f"CLV {TR['clv']:+.2f}% | ROI {TR['roi']:+.1f}%")


if __name__ == "__main__":
    build()
