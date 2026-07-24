"""
AstroPitch - UEFA RESULT GRADING  (makes the public track record real)
============================================================================
30_daily_slate.py freezes each European prediction pre-kickoff into
uefa_pending.csv. This settles them once the results land.

Matching is by the source's own event id, so there is no name-matching to get
wrong. Graded rows are appended to track_record_live.csv using the same schema
23_track_record.py writes, so the site's "Live since launch" panel picks them
up automatically.

Grades: 1X2 hit, exact-score hit, over/under 2.5 hit, and log-loss (the honest
metric — it punishes confident misses).

Run:  python 31_uefa_grade.py
============================================================================
"""
import json
import os
import time
import urllib.request
import datetime as dt

import numpy as np
import pandas as pd

SPORTSDB = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={d}&l={lg}"
COMPS = {4480: "Champions League", 4481: "Europa League", 5071: "Conference League"}
PENDING = "uefa_pending.csv"
LIVE = "track_record_live.csv"
MANUAL_RESULTS = "results_manual.csv"
MAX_AGE_DAYS = 14           # give up on a fixture after this (postponed/abandoned)


def manual_results():
    """Results pasted in by hand, keyed the same way 30_daily_slate.py logs
    manual fixtures (id = 'm-{date}-{home}-{away}', spaces stripped) so they
    match uefa_pending.csv rows exactly - no name-matching to get wrong."""
    if not os.path.exists(MANUAL_RESULTS):
        return {}
    m = pd.read_csv(MANUAL_RESULTS)
    out = {}
    for r in m.itertuples(index=False):
        key = f"m-{r.date}-{r.home}-{r.away}".replace(" ", "")
        out[key] = (int(r.hg), int(r.ag))
    return out


def results_for(date):
    """{event_id: (home_goals, away_goals)} for finished matches on `date`."""
    out = {}
    for lg in COMPS:
        try:
            req = urllib.request.Request(SPORTSDB.format(d=date, lg=lg),
                                         headers={"User-Agent": "Mozilla/5.0"})
            data = json.load(urllib.request.urlopen(req, timeout=45))
        except Exception as e:
            print(f"  [warn] {date} league {lg}: {e}")
            continue
        for e in (data.get("events") or []):
            hs, as_ = e.get("intHomeScore"), e.get("intAwayScore")
            if hs is None or as_ is None or str(hs) == "" or str(as_) == "":
                continue
            if str(e.get("strPostponed", "no")).lower() == "yes":
                continue
            out[str(e.get("idEvent"))] = (int(hs), int(as_))
        time.sleep(1)
    return out


def main():
    print("=" * 70)
    print(" ASTROPITCH - GRADING EUROPEAN PREDICTIONS")
    print("=" * 70)
    if not os.path.exists(PENDING):
        print("\nNothing pending.")
        return
    pend = pd.read_csv(PENDING, dtype={"id": str})
    if pend.empty:
        print("\nNothing pending.")
        return

    today = dt.datetime.now(dt.UTC).date()
    graded, still = [], []
    # only look up dates that have actually been played
    dates = sorted({d for d in pend["date"].unique()
                    if dt.date.fromisoformat(str(d)) <= today})
    res = {}
    for d in dates:
        res.update(results_for(d))
    n_auto = len(res)
    man = manual_results()
    res.update(man)          # manual results win on id collision (more trusted)
    print(f"\n{len(pend)} pending | {n_auto} auto-fetched + {len(man)} manual "
          f"result(s) ({len(res)} total)")

    for p in pend.itertuples(index=False):
        score = res.get(str(p.id))
        age = (today - dt.date.fromisoformat(str(p.date))).days
        if score is None:
            if age <= MAX_AGE_DAYS:
                still.append(p._asdict())
            else:
                print(f"  [dropped] {p.home} v {p.away} — no result after {age}d")
            continue

        hg, ag = score
        probs = np.array([p.pH, p.pD, p.pA], dtype=float)
        y = 0 if hg > ag else (1 if hg == ag else 2)
        pick_i = {"HOME": 0, "DRAW": 1, "AWAY": 2}[str(p.pick)]
        over = int(hg + ag > 2.5)
        ok = pick_i == y
        graded.append(dict(
            date=p.date, div=p.comp, home=p.home, away=p.away,
            pH=p.pH, pD=p.pD, pA=p.pA, pick=["H", "D", "A"][pick_i], p_over=p.p_over,
            score_pick=p.score_pick, actual=f"{hg}-{ag}", result=["H", "D", "A"][y],
            hit_1x2=int(ok), hit_score=int(str(p.score_pick) == f"{hg}-{ag}"),
            hit_ou=int((float(p.p_over) > 0.5) == bool(over)),
            logloss=round(float(-np.log(max(probs[y], 1e-9))), 4),
            bet_side="", clv=None, roi=None,
            graded_at=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        ))
        print(f"  {p.home} {hg}-{ag} {p.away}  | called {p.pick} "
              f"({probs[pick_i]*100:.0f}%) -> {'HIT ' if ok else 'MISS'}"
              f"  | gave the actual result {probs[y]*100:.0f}%")

    if graded:
        g = pd.DataFrame(graded)
        if os.path.exists(LIVE):
            g = pd.concat([pd.read_csv(LIVE), g], ignore_index=True) \
                  .drop_duplicates(subset=["date", "home", "away"], keep="first")
        g.to_csv(LIVE, index=False)
        acc = pd.DataFrame(graded)["hit_1x2"].mean()
        ll = pd.DataFrame(graded)["logloss"].mean()
        print(f"\n  graded {len(graded)} -> {LIVE}  "
              f"(this batch: {acc*100:.0f}% 1X2, log-loss {ll:.3f})")
    else:
        print("\n  nothing to grade yet")

    pd.DataFrame(still).to_csv(PENDING, index=False) if still else (
        os.remove(PENDING) if os.path.exists(PENDING) else None)
    print(f"  {len(still)} still pending")


if __name__ == "__main__":
    main()
