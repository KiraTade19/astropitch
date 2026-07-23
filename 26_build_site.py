"""
AstroPitch - STATIC SITE BUILDER  (the public credibility + brand front)
============================================================================
Generates docs/index.html from our REAL data so the public numbers are always
honest and auto-update on rebuild:
  - the transparent track record (accuracy / log-loss / CLV) from track_record.csv
  - the "we tested astrology on 44k matches" science section (measured, not claimed)
  - a live sample cosmic reading (the brand hook)

Design: Spline-inspired - an interactive, draggable 3D orbit rendered in plain
Canvas as the hero, glassmorphic cards, gradient-mesh glows, modern grotesque
type. Single dark theme (a deliberate commitment for a cosmic brand).

Deploy free: Netlify (publish dir = docs) or GitHub Pages (main /docs).
Rebuild any time: python 26_build_site.py
============================================================================
"""
import datetime
import os
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
MARKET = dict(acc=0.521, ll=0.980)
ESO = dict(only_acc=0.446, only_ll=1.058, base_acc=0.502, base_ll=0.999,
           both_acc=0.503, both_ll=0.999, share=41.1)
DEMO = cosmic_reading("Real Madrid", "Barcelona",
                      datetime.date.today() + datetime.timedelta(days=14))

# ---- live record (grows once the season starts; empty off-season) ----
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
    f'<div class="note ok"><b>Live since launch:</b> {LIVE["n"]:,} predictions graded '
    f'({LIVE["span"]}) &mdash; {LIVE["acc"]*100:.1f}% 1X2, {LIVE["ll"]:.3f} log-loss, '
    f'{_live_clv}. Logged pre-kickoff, graded automatically.</div>')


CSS = """
:root{
  --bg:#06070f; --bg2:#0b0d1c;
  --glass:rgba(255,255,255,.045); --glass2:rgba(255,255,255,.07);
  --line:rgba(255,255,255,.10); --line2:rgba(255,255,255,.18);
  --ink:#f2f4ff; --mut:#98a1c4; --dim:#6b7398;
  --violet:#7c5cff; --cyan:#35d6ff; --pink:#ff6ec7; --gold:#ffc46b;
  --ok:#4fe0a8;
  --r:22px;
}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{
  font-family:"DM Sans",-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
  font-size:16.5px;line-height:1.65;color:var(--ink);background:var(--bg);
  overflow-x:hidden;
}
/* gradient-mesh glows */
body::before{
  content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
  background:
   radial-gradient(60vw 60vw at 12% -5%, rgba(124,92,255,.28), transparent 60%),
   radial-gradient(55vw 55vw at 92% 8%, rgba(53,214,255,.18), transparent 60%),
   radial-gradient(50vw 50vw at 70% 95%, rgba(255,110,199,.14), transparent 60%);
  filter:blur(10px);
}
.wrap{max-width:1060px;margin:0 auto;padding:0 24px}
a{color:var(--cyan);text-decoration:none}
a:focus-visible,button:focus-visible{outline:2px solid var(--gold);outline-offset:3px;border-radius:8px}

/* ---------- HERO ---------- */
.hero{position:relative;min-height:92vh;display:flex;flex-direction:column;
  align-items:center;justify-content:center;text-align:center;padding:80px 24px 40px}
#orb{position:absolute;inset:0;width:100%;height:100%;z-index:0;cursor:grab}
#orb:active{cursor:grabbing}
.hero-in{position:relative;z-index:1;pointer-events:none}
.badge{display:inline-flex;align-items:center;gap:8px;padding:7px 15px;
  border:1px solid var(--line2);border-radius:99px;background:var(--glass);
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  font-size:12.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--mut)}
.badge i{width:7px;height:7px;border-radius:50%;background:var(--ok);
  box-shadow:0 0 10px 2px rgba(79,224,168,.7);font-style:normal}
h1{font-family:"Bricolage Grotesque","DM Sans",sans-serif;font-weight:800;
  font-size:clamp(46px,8.4vw,104px);line-height:.95;letter-spacing:-.045em;
  margin:26px auto 0;max-width:14ch;text-wrap:balance}
h1 .grad{background:linear-gradient(100deg,var(--gold),var(--pink) 45%,var(--violet));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.sub{color:var(--mut);font-size:clamp(16px,2.1vw,20px);margin:22px auto 0;max-width:52ch}
.cta-row{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:34px;
  pointer-events:auto}
.btn{display:inline-flex;align-items:center;gap:9px;padding:14px 26px;border-radius:14px;
  font-weight:600;font-size:15.5px;transition:transform .18s ease,box-shadow .18s ease}
.btn.primary{background:linear-gradient(180deg,#fff,#d9dcff);color:#0a0b16;
  box-shadow:0 14px 40px -14px rgba(255,255,255,.5)}
.btn.ghost{border:1px solid var(--line2);color:var(--ink);background:var(--glass);
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}
.btn:hover{transform:translateY(-2px)}
.drag{margin-top:30px;font-size:12.5px;color:var(--dim);letter-spacing:.05em}

/* ---------- SECTIONS ---------- */
section{padding:88px 0;position:relative}
.eyebrow{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.18em;
  text-transform:uppercase;color:var(--violet);margin-bottom:14px}
h2{font-family:"Bricolage Grotesque","DM Sans",sans-serif;font-weight:700;
  font-size:clamp(30px,4.4vw,46px);line-height:1.04;letter-spacing:-.035em;
  margin-bottom:12px;text-wrap:balance}
h2 .em{background:linear-gradient(100deg,var(--cyan),var(--violet));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.lede{color:var(--mut);max-width:62ch;font-size:17px}

/* glass cards */
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;margin-top:34px}
.card{background:var(--glass);border:1px solid var(--line);border-radius:var(--r);
  padding:26px;backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
  box-shadow:0 1px 0 rgba(255,255,255,.06) inset, 0 26px 60px -34px #000;
  transition:transform .22s ease,border-color .22s ease,background .22s ease}
.card:hover{transform:translateY(-4px);border-color:var(--line2);background:var(--glass2)}
.stat .v{font-family:"Bricolage Grotesque","DM Sans",sans-serif;font-size:42px;
  font-weight:700;line-height:1;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.stat .l{color:var(--mut);font-size:13.5px;margin-top:10px;line-height:1.45}
.g{color:var(--gold)}.c{color:var(--cyan)}.v{color:var(--violet)}.p{color:var(--pink)}

.note{margin-top:22px;padding:20px 24px;border-radius:16px;
  background:rgba(124,92,255,.07);border:1px solid rgba(124,92,255,.22);
  color:var(--mut);font-size:15px}
.note b{color:var(--ink)}
.note.ok{background:rgba(79,224,168,.07);border-color:rgba(79,224,168,.25)}

.tablewrap{overflow-x:auto;margin-top:26px;border-radius:var(--r);
  border:1px solid var(--line);background:var(--glass);
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px)}
table{width:100%;border-collapse:collapse;font-size:15px;
  font-variant-numeric:tabular-nums;min-width:430px}
th,td{padding:15px 20px;text-align:left;border-bottom:1px solid var(--line)}
th{color:var(--dim);font-size:11.5px;font-weight:700;letter-spacing:.13em;text-transform:uppercase}
tr:last-child td{border-bottom:0}
tr.hi td{color:var(--gold)}

/* cosmic panel */
.cosmic{margin-top:30px;border-radius:26px;padding:34px;
  background:linear-gradient(150deg,rgba(124,92,255,.16),rgba(255,110,199,.08) 60%,transparent),
             var(--glass);
  border:1px solid rgba(255,110,199,.22);
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px)}
.cosmic .hd{font-family:"Bricolage Grotesque","DM Sans",sans-serif;font-weight:700;
  font-size:23px;letter-spacing:-.02em;color:var(--gold);margin-bottom:16px}
.cosmic p{margin:10px 0;color:#dde1ff}
.disc{margin-top:20px;padding-top:18px;border-top:1px solid var(--line);
  color:var(--dim);font-size:12.5px;font-style:italic;line-height:1.55}

footer{padding:70px 24px 90px;text-align:center;color:var(--dim);font-size:13.5px;
  border-top:1px solid var(--line);line-height:1.8;margin-top:60px}

/* scroll reveal */
.rv{opacity:0;transform:translateY(22px);transition:opacity .7s ease,transform .7s ease}
.rv.in{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){
  .rv{opacity:1;transform:none;transition:none}
  html{scroll-behavior:auto}
  .btn:hover,.card:hover{transform:none}
}
@media(max-width:640px){
  section{padding:64px 0}
  .card{padding:22px}
  .hero{min-height:88vh}
}
"""

JS = """
(function(){
  // ---------- interactive orbit (Canvas, no libraries) ----------
  var c=document.getElementById('orb'); if(!c) return;
  var x=c.getContext('2d'), W=0,H=0,dpr=1;
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function size(){
    dpr=Math.min(window.devicePixelRatio||1,2);
    W=c.clientWidth; H=c.clientHeight;
    c.width=Math.floor(W*dpr); c.height=Math.floor(H*dpr);
    x.setTransform(dpr,0,0,dpr,0,0);
  }
  size(); window.addEventListener('resize',size);

  // sphere wireframe points (lat/long) + orbiting particles
  var pts=[], i, j, lat, lon, n;
  for(i=0;i<=10;i++){                       // latitude rings
    lat=Math.PI*(i/10-0.5); n=Math.round(Math.cos(lat)*44)+6;
    for(j=0;j<n;j++){ lon=2*Math.PI*j/n;
      pts.push([Math.cos(lat)*Math.cos(lon),Math.sin(lat),Math.cos(lat)*Math.sin(lon),0]); }
  }
  var orbs=[];                              // orbiting "stars" on tilted rings
  for(i=0;i<3;i++){
    var tilt=(i-1)*0.75, rad=1.45+i*0.22;
    for(j=0;j<26;j++){
      orbs.push({a:2*Math.PI*j/26+i, r:rad, t:tilt, s:0.0026+0.0011*i});
    }
  }

  var ry=0.4, rx=-0.28, vy=0.0022, drag=false, px=0, py=0, vry=0, vrx=0;
  function down(e){drag=true; px=(e.touches?e.touches[0].clientX:e.clientX);
    py=(e.touches?e.touches[0].clientY:e.clientY);}
  function move(e){ if(!drag) return;
    var cx=(e.touches?e.touches[0].clientX:e.clientX),
        cy=(e.touches?e.touches[0].clientY:e.clientY);
    vry=(cx-px)*0.006; vrx=(cy-py)*0.005; ry+=vry; rx+=vrx;
    rx=Math.max(-1.2,Math.min(1.2,rx)); px=cx; py=cy;
    if(e.touches) e.preventDefault();
  }
  function up(){drag=false;}
  c.addEventListener('mousedown',down); window.addEventListener('mousemove',move);
  window.addEventListener('mouseup',up);
  c.addEventListener('touchstart',down,{passive:true});
  c.addEventListener('touchmove',move,{passive:false});
  window.addEventListener('touchend',up);

  function draw(){
    var cx=W/2, cy=H*0.5, R=Math.min(W,H)*0.29, f=3.2;
    x.clearRect(0,0,W,H);
    if(!drag){ ry+=vy + vry; vry*=0.94; rx+=vrx; vrx*=0.94; }
    var cyy=Math.cos(ry),syy=Math.sin(ry),cxx=Math.cos(rx),sxx=Math.sin(rx);
    function proj(p){
      var X=p[0]*cyy-p[2]*syy, Z=p[0]*syy+p[2]*cyy, Y=p[1];
      var Y2=Y*cxx-Z*sxx, Z2=Y*sxx+Z*cxx;
      var s=f/(f+Z2);
      return [cx+X*R*s, cy+Y2*R*s, Z2, s];
    }
    // globe points, depth-shaded violet -> cyan
    for(var k=0;k<pts.length;k++){
      var q=proj(pts[k]); var d=(q[2]+1)/2;
      var a=0.16+0.5*(1-d);
      x.fillStyle='rgba('+Math.round(124+(53-124)*(1-d))+','+
                          Math.round(92+(214-92)*(1-d))+','+
                          Math.round(255)+','+a.toFixed(3)+')';
      x.beginPath(); x.arc(q[0],q[1],(1-d)*1.5+0.5,0,6.283); x.fill();
    }
    // orbiting stars
    for(k=0;k<orbs.length;k++){
      var o=orbs[k]; if(!reduce) o.a+=o.s;
      var p=[Math.cos(o.a)*o.r, Math.sin(o.a)*Math.sin(o.t)*o.r,
             Math.sin(o.a)*Math.cos(o.t)*o.r];
      var q2=proj(p); var dd=(q2[2]+1)/2;
      x.beginPath();
      x.fillStyle='rgba(255,196,107,'+(0.25+0.65*(1-dd)).toFixed(3)+')';
      x.shadowColor='rgba(255,196,107,.85)'; x.shadowBlur=(1-dd)*11;
      x.arc(q2[0],q2[1],(1-dd)*1.7+0.7,0,6.283); x.fill(); x.shadowBlur=0;
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);

  // ---------- scroll reveal ----------
  var io=new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target);} });
  },{threshold:.12});
  document.querySelectorAll('.rv').forEach(function(el){io.observe(el);});
})();
"""


def stat(v, l, cls=""):
    return (f'<div class="card stat"><div class="v {cls}">{v}</div>'
            f'<div class="l">{l}</div></div>')


def build():
    cosmic_html = "".join(f"<p>{DEMO[k]}</p>" for k in
                          ["moon", "planets", "aspects", "numerology"])
    html = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AstroPitch — honest football predictions, with a cosmic twist</title>
<meta name="description" content="Calibrated football match probabilities for 12 leagues, all internationals and every European club — with a transparent track record and cosmic match readings. Predictions as data, not betting advice.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>

<header class="hero">
  <canvas id="orb" aria-hidden="true"></canvas>
  <div class="hero-in">
    <span class="badge"><i></i> Live · {TR['n']:,} matches audited</span>
    <h1>Football odds, <span class="grad">honestly</span> calculated.</h1>
    <p class="sub">Calibrated probabilities for 12 leagues, every international, and
       any club in Europe — published with a track record we don't hide.</p>
    <div class="cta-row">
      <a class="btn primary" href="{API_URL}/docs">Explore the API →</a>
      <a class="btn ghost" href="#record">See the receipts</a>
    </div>
    <div class="drag">✧ drag the orbit</div>
  </div>
</header>

<main class="wrap">

<section id="record" class="rv">
  <span class="eyebrow">Performance, in the open</span>
  <h2>The <span class="em">honest</span> track record</h2>
  <p class="lede">Every model in football should show its real out-of-sample numbers.
     Here are ours, on {TR['n']:,} matches ({TR['span']}).</p>
  <div class="grid">
    {stat(f"{TR['acc']*100:.1f}%","1X2 accuracy")}
    {stat(f"{TR['ll']:.3f}","1X2 log-loss","c")}
    {stat(f"{TR['score']*100:.1f}%","exact score top-1","g")}
    {stat(f"{TR['ou']*100:.1f}%","over/under 2.5","v")}
  </div>
  {LIVE_HTML}
  <div class="note">
    <b>We don't claim to beat the bookmaker.</b> On these {TR['n']:,} matches the closing
    line scored {MARKET['acc']*100:.1f}% / {MARKET['ll']:.3f} log-loss — sharper than us, as an efficient
    market should be. We even tested flat-staking our model's "value" picks:
    <b>{TR['roi']:+.1f}% ROI</b>, average CLV <b>{TR['clv']:+.2f}%</b> (beat the close
    {TR['beat']:.0f}% of the time). So we publish probabilities as insight and
    entertainment — not a betting edge, because honestly there isn't one.
  </div>
</section>

<section class="rv">
  <span class="eyebrow">The experiment</span>
  <h2>We tested <span class="em">astrology</span> on 44,000 matches</h2>
  <p class="lede">AstroPitch started as an astrology experiment. So we ran the
     experiment properly — and we'll tell you exactly what we found.</p>
  <div class="tablewrap">
    <table>
      <tr><th>Model</th><th>1X2 accuracy</th><th>Log-loss</th></tr>
      <tr><td>Always pick home (baseline)</td><td>43.0%</td><td>—</td></tr>
      <tr class="hi"><td>Astrology + numerology <i>only</i></td><td>{ESO['only_acc']*100:.1f}%</td><td>{ESO['only_ll']:.3f}</td></tr>
      <tr><td>Our real model</td><td>{ESO['base_acc']*100:.1f}%</td><td>{ESO['base_ll']:.3f}</td></tr>
      <tr><td>Real model + all 40 cosmic features</td><td>{ESO['both_acc']*100:.1f}%</td><td>{ESO['both_ll']:.3f}</td></tr>
    </table>
  </div>
  <div class="note">The cosmos added <b>nothing</b>: 40 astrology, numerology, biorhythm
    and Chinese-zodiac features moved our log-loss by 0.0007 — pure noise. Moon phase
    across 44,325 real matches shifts goals-per-game by 0.03 (also noise). The stars are
    beautiful. They do not pick winners. We think being honest about that is far more
    interesting than pretending otherwise.</div>
</section>

<section class="rv">
  <span class="eyebrow">For fun — strictly</span>
  <h2>Your match's <span class="em">cosmic reading</span></h2>
  <p class="lede">A full astrological and numerological reading for any fixture on
     Earth — even the ones our model doesn't cover.</p>
  <div class="cosmic">
    <div class="hd">Real Madrid vs Barcelona &nbsp;·&nbsp; {DEMO['headline']}</div>
    {cosmic_html}
    <p class="p">{DEMO['cosmic_leaning']}</p>
    <div class="disc">{DEMO['disclaimer']}</div>
  </div>
</section>

<section class="rv">
  <span class="eyebrow">The product</span>
  <h2>Probabilities as <span class="em">data</span></h2>
  <div class="grid">
    <div class="card stat"><div class="v g">12</div><div class="l">top leagues + all internationals — calibrated 1X2, over/under, exact scores and cards</div></div>
    <div class="card stat"><div class="v c">600+</div><div class="l">European clubs covered via pan-European ratings</div></div>
    <div class="card stat"><div class="v p">∞</div><div class="l">cosmic readings — any match, anywhere</div></div>
  </div>
  <div class="note" style="text-align:center">
    <p style="margin-bottom:16px">Clean JSON for apps, bots and media.</p>
    <a class="btn primary" href="{API_URL}/docs">Explore the API →</a>
  </div>
</section>

</main>

<footer>
  <strong>AstroPitch</strong> — probabilistic model output for information and
  entertainment, not betting advice. 18+. Please gamble responsibly.<br>
  Track record rebuilt {datetime.date.today().isoformat()} from live data.
</footer>

<script>{JS}</script>
</body></html>"""

    os.makedirs("docs", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT}  ({len(html):,} bytes)")
    print(f"Track record: {TR['n']:,} matches | 1X2 {TR['acc']*100:.1f}% | "
          f"CLV {TR['clv']:+.2f}% | ROI {TR['roi']:+.1f}%")


if __name__ == "__main__":
    build()
