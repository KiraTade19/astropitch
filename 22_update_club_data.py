"""
AstroPitch V12 - CLUB DATA UPDATER
============================================================================
Keeps club_raw.csv current and pulls the upcoming fixture slate, both free
from football-data.co.uk. Run this before retraining / before a prediction
run so ELO, form and promotion/relegation are up to date.

  1. RESULTS : downloads each division's current-season CSV and appends any
               new matches into club_raw.csv (dedup on Div+Date+teams).
  2. FIXTURES: downloads fixtures.csv -> club_fixtures.csv (the matches we
               actually predict next).

Season code format is football-data's: 2025-26 -> "2526". Add the new code
each August when the season rolls over.

Run:  python 22_update_club_data.py
============================================================================
"""
import io
import urllib.request
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

# our 12 divisions (football-data.co.uk codes)
DIVS = ["E0", "E1", "SP1", "I1", "D1", "F1", "N1", "B1", "P1", "SC0", "T1", "G1"]
# seasons to (re)fetch. current season first; add "2627" when it starts.
SEASONS = ["2526"]

RESULTS_URL = "https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"
FIXTURES_URL = "https://www.football-data.co.uk/fixtures.csv"
CLUB_CSV = "club_raw.csv"
FIXTURES_CSV = "club_fixtures.csv"

KEY = ["Div", "Date", "HomeTeam", "AwayTeam"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=30).read()
    return pd.read_csv(io.BytesIO(raw), encoding="latin-1", low_memory=False)


def norm_key(df):
    """A normalised join key that survives dd/mm/yy vs dd/mm/yyyy differences."""
    d1 = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    d2 = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    d = d1.where(d1.notna(), d2)
    return (df["Div"].astype(str) + "|" + d.dt.strftime("%Y-%m-%d").fillna("?")
            + "|" + df["HomeTeam"].astype(str) + "|" + df["AwayTeam"].astype(str))


def update_results():
    print("=" * 70)
    print(" UPDATING CLUB RESULTS (football-data.co.uk)")
    print("=" * 70)
    old = pd.read_csv(CLUB_CSV, encoding="latin-1", low_memory=False)
    # fold any BOM-prefixed duplicate Div column into Div
    for a in [c for c in old.columns if "Div" in c and c != "Div"]:
        old["Div"] = old["Div"].where(old["Div"].notna(), old[a])
    old_keys = set(norm_key(old).tolist())
    print(f"  existing rows: {len(old):,}  ({len(old_keys):,} unique matches)")

    new_frames, added = [], 0
    for season in SEASONS:
        for div in DIVS:
            url = RESULTS_URL.format(season=season, div=div)
            try:
                d = fetch(url)
            except Exception as e:
                print(f"  [skip] {season}/{div}: {e}")
                continue
            d = d.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
            d["Div"] = div
            k = norm_key(d)
            fresh = d[~k.isin(old_keys)]
            if len(fresh):
                new_frames.append(fresh)
                old_keys.update(norm_key(fresh).tolist())
                added += len(fresh)
            print(f"  {season}/{div:<3s}: {len(d):3d} rows, {len(fresh):3d} new")

    if new_frames:
        combined = pd.concat([old] + new_frames, ignore_index=True)
        combined.to_csv(CLUB_CSV, index=False, encoding="latin-1")
        print(f"\n  ADDED {added:,} new matches -> {len(combined):,} total. Wrote {CLUB_CSV}")
    else:
        print("\n  No new matches (already up to date).")


def update_fixtures():
    print("\n" + "=" * 70)
    print(" FETCHING UPCOMING FIXTURES")
    print("=" * 70)
    try:
        fx = fetch(FIXTURES_URL)
    except Exception as e:
        print(f"  [skip] fixtures: {e}")
        return
    # football-data's fixtures.csv puts Div under a BOM-prefixed column
    for a in [c for c in fx.columns if "Div" in c and c != "Div"]:
        if "Div" not in fx.columns:
            fx = fx.rename(columns={a: "Div"})
        else:
            fx["Div"] = fx["Div"].where(fx["Div"].notna(), fx[a])
    if "Div" not in fx.columns:
        print("  [skip] fixtures: no Div column in feed")
        return
    fx = fx[fx["Div"].isin(DIVS)].copy()
    fx.to_csv(FIXTURES_CSV, index=False, encoding="latin-1")
    if len(fx):
        d = pd.to_datetime(fx["Date"], dayfirst=True, errors="coerce")
        span = f"{d.min().date()} -> {d.max().date()}" if d.notna().any() else "n/a"
        print(f"  {len(fx)} upcoming fixtures in our divisions ({span}). Wrote {FIXTURES_CSV}")
        by = fx.groupby("Div").size()
        print("  " + ", ".join(f"{k}:{v}" for k, v in by.items()))
    else:
        print("  No upcoming fixtures listed for our divisions right now "
              "(off-season / between rounds).")


if __name__ == "__main__":
    update_results()
    update_fixtures()
    print("\nDone. Re-run 21_club_genesis.py to retrain on the refreshed data.")
