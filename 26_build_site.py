"""
AstroPitch - STATIC SITE BUILDER  (the public credibility + brand front)
============================================================================
Generates docs/index.html from our REAL data so the public numbers are always
honest and auto-update on rebuild:
  - the transparent track record (accuracy / log-loss / CLV) from track_record.csv
  - the "we tested astrology on 44k matches" science section (measured, not claimed)
  - a live sample cosmic reading (the brand hook)

Design: architectural minimalism - paper ground, charcoal type, corten-rust
accent, hairline rules and sharp edges. The hero is a draggable technical
orrery drawn in plain Canvas. Committed single (light) theme.

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
  --paper:#F1F0EC; --paper2:#E9E7E1; --ink:#1B1A16; --ink2:#33312B;
  --mut:#6E6A61; --line:#D6D2C8; --line2:#BFB9AC;
  --rust:#9C5533; --rust2:#C0724A; --ok:#4A6B4F;
}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{font-family:"Archivo",-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
  font-size:16.5px;line-height:1.6;color:var(--ink);background:var(--paper);
  -webkit-font-smoothing:antialiased}
.mono{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
.wrap{max-width:1120px;margin:0 auto;padding:0 32px}
a{color:var(--rust);text-decoration:none}
a:focus-visible,button:focus-visible{outline:2px solid var(--rust);outline-offset:3px}

/* ---------- HERO ---------- */
.hero{border-bottom:1px solid var(--line)}
.hero-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:56px;align-items:center;
  padding:96px 0 88px}
.kicker{font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.22em;
  text-transform:uppercase;color:var(--rust);display:flex;align-items:center;gap:10px}
.kicker::after{content:"";flex:1;height:1px;background:var(--line2)}
h1{font-size:clamp(42px,6.6vw,80px);font-weight:700;line-height:1.0;
  letter-spacing:-.035em;margin:26px 0 0;text-wrap:balance}
h1 em{font-style:normal;color:var(--rust)}
.sub{color:var(--mut);font-size:clamp(16px,1.9vw,19px);margin-top:24px;max-width:46ch}
.cta-row{display:flex;gap:12px;flex-wrap:wrap;margin-top:36px}
.btn{display:inline-flex;align-items:center;gap:9px;padding:15px 28px;
  font-family:"IBM Plex Mono",monospace;font-size:12.5px;letter-spacing:.13em;
  text-transform:uppercase;border:1px solid var(--ink);transition:background .18s,color .18s}
.btn.primary{background:var(--ink);color:var(--paper)}
.btn.primary:hover{background:var(--rust);border-color:var(--rust)}
.btn.ghost{color:var(--ink);border-color:var(--line2)}
.btn.ghost:hover{border-color:var(--ink)}
.orbwrap{position:relative;aspect-ratio:1;border:1px solid var(--line);background:var(--paper2)}
#orb{width:100%;height:100%;display:block;cursor:grab}
#orb:active{cursor:grabbing}
.orbcap{position:absolute;left:14px;bottom:12px;font-family:"IBM Plex Mono",monospace;
  font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--mut)}

/* ---------- SECTIONS ---------- */
section{padding:88px 0;border-bottom:1px solid var(--line)}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.22em;
  text-transform:uppercase;color:var(--rust);display:block;margin-bottom:18px}
h2{font-size:clamp(28px,4vw,44px);font-weight:700;line-height:1.06;
  letter-spacing:-.03em;margin-bottom:16px;text-wrap:balance;max-width:20ch}
.lede{color:var(--mut);max-width:62ch;font-size:17px}

/* spec-sheet stat grid: hairline cells, no radius */
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
  margin-top:44px;border:1px solid var(--line);border-right:0;border-bottom:0}
.cell{border-right:1px solid var(--line);border-bottom:1px solid var(--line);padding:28px 26px}
.cell .v{font-family:"IBM Plex Mono",monospace;font-size:36px;font-weight:600;
  line-height:1;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.cell .l{color:var(--mut);font-size:13.5px;margin-top:12px;line-height:1.45}
.rust{color:var(--rust)}

.note{margin-top:34px;padding:26px 30px;border-left:2px solid var(--rust);
  background:var(--paper2);color:var(--ink2);font-size:15.5px;max-width:74ch}
.note b{color:var(--ink)}
.note.ok{border-left-color:var(--ok)}

.tablewrap{overflow-x:auto;margin-top:36px;border:1px solid var(--line)}
table{width:100%;border-collapse:collapse;font-size:15px;min-width:440px}
th,td{padding:16px 22px;text-align:left;border-bottom:1px solid var(--line)}
th{font-family:"IBM Plex Mono",monospace;font-size:10.5px;font-weight:600;
  letter-spacing:.18em;text-transform:uppercase;color:var(--mut);background:var(--paper2)}
td{font-variant-numeric:tabular-nums}
td:not(:first-child){font-family:"IBM Plex Mono",monospace;font-size:14px}
tr:last-child td{border-bottom:0}
tr.hi td{color:var(--rust)}

.cosmic{margin-top:36px;border:1px solid var(--line);padding:34px 36px;background:var(--paper2)}
.cosmic .hd{font-size:21px;font-weight:700;letter-spacing:-.02em;margin-bottom:18px}
.cosmic p{margin:11px 0;color:var(--ink2);max-width:72ch}
.disc{margin-top:22px;padding-top:18px;border-top:1px solid var(--line);
  color:var(--mut);font-size:12.5px;line-height:1.6;max-width:72ch}

footer{padding:64px 32px 84px;text-align:center;color:var(--mut);font-size:13.5px;
  line-height:1.9}
footer strong{color:var(--ink)}

.rv{opacity:0;transform:translateY(16px);transition:opacity .6s ease,transform .6s ease}
.rv.in{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){
  .rv{opacity:1;transform:none;transition:none} html{scroll-behavior:auto}
}
@media(max-width:860px){
  .hero-grid{grid-template-columns:1fr;gap:40px;padding:64px 0 56px}
  .orbwrap{max-width:420px}
  section{padding:64px 0}
  .wrap{padding:0 22px}
}
"""

JS = """
(function(){
  // ---------- technical orrery: thin-line wireframe, draggable ----------
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

  var rings=[], i, j, lat, lon, pts;
  for(i=1;i<10;i++){                      // latitude circles
    lat=Math.PI*(i/10-0.5); pts=[];
    for(j=0;j<=64;j++){ lon=2*Math.PI*j/64;
      pts.push([Math.cos(lat)*Math.cos(lon),Math.sin(lat),Math.cos(lat)*Math.sin(lon)]); }
    rings.push(pts);
  }
  for(i=0;i<12;i++){                      // meridians
    lon=Math.PI*i/12; pts=[];
    for(j=0;j<=64;j++){ lat=Math.PI*(j/64-0.5);
      pts.push([Math.cos(lat)*Math.cos(lon),Math.sin(lat),Math.cos(lat)*Math.sin(lon)]); }
    rings.push(pts);
  }
  var orbits=[];                          // tilted orbit paths + a body on each
  for(i=0;i<3;i++){ orbits.push({r:1.34+i*0.26, t:(i-1)*0.62, a:i*2.1,
                                 s:(reduce?0:0.0032-0.0008*i)}); }

  var ry=0.5, rx=-0.30, vy=0.0016, drag=false, px=0, py=0, vry=0, vrx=0;
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
    var cx=W/2, cy=H/2, R=Math.min(W,H)*0.30, f=3.4;
    x.clearRect(0,0,W,H);
    if(!drag){ ry+=vy+vry; vry*=0.93; rx+=vrx; vrx*=0.93; }
    var cyy=Math.cos(ry),syy=Math.sin(ry),cxx=Math.cos(rx),sxx=Math.sin(rx);
    function proj(p){
      var X=p[0]*cyy-p[2]*syy, Z=p[0]*syy+p[2]*cyy, Y=p[1];
      var Y2=Y*cxx-Z*sxx, Z2=Y*sxx+Z*cxx;
      var s=f/(f+Z2);
      return [cx+X*R*s, cy+Y2*R*s, Z2];
    }
    x.lineWidth=0.85;
    for(var k=0;k<rings.length;k++){
      var pl=rings[k], started=false, prevBack=null;
      for(var m=0;m<pl.length;m++){
        var q=proj(pl[m]), back=q[2]>0;
        if(!started||back!==prevBack){
          if(started) x.stroke();
          x.beginPath(); x.moveTo(q[0],q[1]);
          x.strokeStyle = back ? 'rgba(27,26,22,.13)' : 'rgba(27,26,22,.40)';
          started=true; prevBack=back;
        } else { x.lineTo(q[0],q[1]); }
      }
      x.stroke();
    }
    // orbit paths + bodies (rust)
    for(k=0;k<orbits.length;k++){
      var o=orbits[k]; o.a+=o.s;
      x.beginPath(); x.strokeStyle='rgba(156,85,51,.28)'; x.lineWidth=0.85;
      for(m=0;m<=72;m++){
        var ang=2*Math.PI*m/72;
        var pt=[Math.cos(ang)*o.r, Math.sin(ang)*Math.sin(o.t)*o.r,
                Math.sin(ang)*Math.cos(o.t)*o.r];
        var qq=proj(pt); if(m===0) x.moveTo(qq[0],qq[1]); else x.lineTo(qq[0],qq[1]);
      }
      x.stroke();
      var bp=[Math.cos(o.a)*o.r, Math.sin(o.a)*Math.sin(o.t)*o.r,
              Math.sin(o.a)*Math.cos(o.t)*o.r];
      var b=proj(bp); var d=(b[2]+1)/2;
      x.beginPath(); x.fillStyle='rgba(156,85,51,'+(0.45+0.5*(1-d)).toFixed(3)+')';
      x.arc(b[0],b[1],(1-d)*2.0+1.6,0,6.283); x.fill();
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);

  var io=new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target);} });
  },{threshold:.12});
  document.querySelectorAll('.rv').forEach(function(el){io.observe(el);});
})();
"""


def cell(v, l, cls=""):
    return (f'<div class="cell"><div class="v {cls}">{v}</div>'
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
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>

<header class="hero"><div class="wrap"><div class="hero-grid">
  <div>
    <div class="kicker">{TR['n']:,} matches audited</div>
    <h1>Football odds, <em>honestly</em> calculated.</h1>
    <p class="sub">Calibrated probabilities for 12 leagues, every international and
       any club in Europe — published with a track record we don't hide.</p>
    <div class="cta-row">
      <a class="btn primary" href="{API_URL}/docs">Explore the API</a>
      <a class="btn ghost" href="#record">See the receipts</a>
    </div>
  </div>
  <div class="orbwrap">
    <canvas id="orb" aria-hidden="true"></canvas>
    <div class="orbcap">Drag to orbit</div>
  </div>
</div></div></header>

<main>

<section id="record" class="rv"><div class="wrap">
  <span class="eyebrow">Performance, in the open</span>
  <h2>The honest track record</h2>
  <p class="lede">Every model in football should show its real out-of-sample numbers.
     Here are ours, on {TR['n']:,} matches ({TR['span']}).</p>
  <div class="grid">
    {cell(f"{TR['acc']*100:.1f}%","1X2 accuracy")}
    {cell(f"{TR['ll']:.3f}","1X2 log-loss")}
    {cell(f"{TR['score']*100:.1f}%","exact score top-1","rust")}
    {cell(f"{TR['ou']*100:.1f}%","over / under 2.5")}
  </div>
  {LIVE_HTML}
  <div class="note">
    <b>We don't claim to beat the bookmaker.</b> On these {TR['n']:,} matches the closing
    line scored {MARKET['acc']*100:.1f}% / {MARKET['ll']:.3f} log-loss — sharper than us, as an efficient
    market should be. We even tested flat-staking our model's “value” picks:
    <b>{TR['roi']:+.1f}% ROI</b>, average CLV <b>{TR['clv']:+.2f}%</b> (beat the close
    {TR['beat']:.0f}% of the time). So we publish probabilities as insight and
    entertainment — not a betting edge, because honestly there isn't one.
  </div>
</div></section>

<section class="rv"><div class="wrap">
  <span class="eyebrow">The experiment</span>
  <h2>We tested astrology on 44,000 matches</h2>
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
</div></section>

<section class="rv"><div class="wrap">
  <span class="eyebrow">For fun — strictly</span>
  <h2>Your match's cosmic reading</h2>
  <p class="lede">A full astrological and numerological reading for any fixture on
     Earth — even the ones our model doesn't cover.</p>
  <div class="cosmic">
    <div class="hd">Real Madrid vs Barcelona &nbsp;·&nbsp; {DEMO['headline']}</div>
    {cosmic_html}
    <p class="rust">{DEMO['cosmic_leaning']}</p>
    <div class="disc">{DEMO['disclaimer']}</div>
  </div>
</div></section>

<section class="rv"><div class="wrap">
  <span class="eyebrow">The product</span>
  <h2>Probabilities as data</h2>
  <div class="grid">
    {cell("12","top leagues + all internationals — 1X2, over/under, exact scores and cards")}
    {cell("600+","European clubs covered via pan-European ratings","rust")}
    {cell("∞","cosmic readings — any match, anywhere")}
  </div>
  <div class="note">
    Clean JSON for apps, bots and media.
    <div class="cta-row"><a class="btn primary" href="{API_URL}/docs">Explore the API</a></div>
  </div>
</div></section>

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
