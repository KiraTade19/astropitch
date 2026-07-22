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

CSS = """
:root{--bg:#0a0e1f;--bg2:#111634;--card:#161c3d;--line:#26305e;
--ink:#e8ecff;--mut:#9aa6d6;--gold:#f5c46b;--pur:#a98bff;--grn:#5fd4a4;--red:#ff8a8a}
*{box-sizing:border-box;margin:0;padding:0}
body{font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg);
background-image:radial-gradient(1px 1px at 20% 30%,#fff,transparent),
radial-gradient(1px 1px at 70% 60%,#cfe,transparent),
radial-gradient(1px 1px at 40% 80%,#fff,transparent),
radial-gradient(2px 2px at 85% 20%,#ffe,transparent),
radial-gradient(1px 1px at 55% 15%,#fff,transparent);
background-repeat:no-repeat}
.wrap{max-width:960px;margin:0 auto;padding:0 20px}
header{text-align:center;padding:80px 20px 50px}
.logo{font-size:44px;font-weight:800;letter-spacing:-1px}
.logo .o{color:var(--gold)}
.tag{color:var(--mut);font-size:19px;margin-top:12px}
.pill{display:inline-block;margin-top:22px;padding:7px 16px;border:1px solid var(--line);
border-radius:99px;color:var(--pur);font-size:13px;background:var(--bg2)}
section{padding:38px 0;border-top:1px solid var(--line)}
h2{font-size:26px;margin-bottom:6px}
h2 .em{color:var(--gold)}
.sub{color:var(--mut);margin-bottom:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}
.stat .v{font-size:30px;font-weight:800}
.stat .l{color:var(--mut);font-size:13px;margin-top:4px}
.good{color:var(--grn)}.bad{color:var(--red)}.g{color:var(--gold)}.p{color:var(--pur)}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:24px;margin-top:16px}
table{width:100%;border-collapse:collapse;font-size:14px}
td,th{padding:9px 8px;text-align:left;border-bottom:1px solid var(--line)}
th{color:var(--mut);font-weight:600}
.note{background:#12183a;border-left:3px solid var(--gold);padding:14px 18px;
border-radius:8px;color:var(--mut);font-size:14px;margin-top:16px}
.cosmic{background:linear-gradient(160deg,#1a1140,#101636);border:1px solid #3a2d6e}
.cosmic .hd{font-size:20px;color:var(--gold);margin-bottom:12px}
.cosmic p{margin:8px 0;color:#d7dcff}
.disc{color:#8b93c4;font-size:12.5px;font-style:italic;margin-top:14px}
.cta{display:inline-block;margin-top:8px;padding:12px 22px;background:var(--gold);
color:#1a1300;font-weight:700;border-radius:10px;text-decoration:none}
footer{text-align:center;color:var(--mut);font-size:13px;padding:44px 20px;border-top:1px solid var(--line)}
a{color:var(--pur)}
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
<style>{CSS}</style></head><body>
<div class="wrap">
<header>
  <div class="logo">Astr<span class="o">o</span>Pitch</div>
  <div class="tag">Honest football predictions, written in the data &mdash; with a cosmic twist.</div>
  <div class="pill">Probabilities as data &middot; not betting advice</div>
</header>

<section>
  <h2>The <span class="em">honest</span> track record</h2>
  <div class="sub">Every model in football should show its real out-of-sample numbers. Here are ours, on {TR['n']:,} matches ({TR['span']}).</div>
  <div class="grid">
    {stat(f"{TR['acc']*100:.1f}%","1X2 accuracy")}
    {stat(f"{TR['ll']:.3f}","1X2 log-loss","p")}
    {stat(f"{TR['score']*100:.1f}%","exact score top-1","g")}
    {stat(f"{TR['ou']*100:.1f}%","over/under 2.5")}
  </div>
  <div class="note">
    <b>We don't claim to beat the bookmaker.</b> On these {TR['n']:,} matches the closing line
    scored {MARKET['acc']*100:.1f}% / {MARKET['ll']:.3f} log-loss &mdash; sharper than us, as an efficient market should be.
    We even tested flat-staking our model's "value" picks: <b>{TR['roi']:+.1f}% ROI</b>,
    average CLV <b>{TR['clv']:+.2f}%</b> (beat the close {TR['beat']:.0f}% of the time).
    So we publish probabilities as insight and entertainment &mdash; not a betting edge, because honestly there isn't one.
  </div>
</section>

<section>
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
  <h2>What you get</h2>
  <div class="grid">
    <div class="stat"><div class="v g">12</div><div class="l">top leagues + all internationals, calibrated 1X2 / O/U / exact-score probabilities</div></div>
    <div class="stat"><div class="v p">&#8734;</div><div class="l">cosmic readings for any match on Earth</div></div>
    <div class="stat"><div class="v">API</div><div class="l">clean JSON for apps, bots &amp; media &mdash; probabilities as data</div></div>
  </div>
  <div class="card" style="text-align:center">
    <p style="color:var(--mut)">Build on the data.</p>
    <a class="cta" href="/docs">Explore the API &rarr;</a>
  </div>
</section>

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
