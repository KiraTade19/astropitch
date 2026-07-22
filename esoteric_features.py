"""
AstroPitch - COMPREHENSIVE ESOTERIC FEATURE GENERATOR
============================================================================
Computes every esoteric feature that is derivable from what we actually have:
team NAMES + match DATE. Covers all four systems:

  * NUMEROLOGY   - Pythagorean & Chaldean name value, soul-urge (vowels),
                   master numbers, universal day/month/year, name compatibility
  * WESTERN ASTROLOGY - moon phase/illumination/zodiac, sun & planet zodiac
                   signs, retrogrades, planetary aspects & separations, planetary
                   day-ruler, solstice/equinox proximity
  * EASTERN      - Chinese zodiac animal & element (match year), Vedic moon
                   nakshatra
  * (biorhythm & founding-date numerology need birth dates we don't have yet -
     stubbed; add once a club-founding / manager-DOB table exists)

Everything is cached by (name) and (date) so a 44k-match sweep is fast.
Honesty note: our tests show these have ~0 predictive signal; this module lets
us INCLUDE and TEST them fairly, and drive the 'cosmic reading' brand layer.
============================================================================
"""
import math
import datetime as _dt
from functools import lru_cache

import ephem

# ---------------------------------------------------------------------------
# NUMEROLOGY
# ---------------------------------------------------------------------------
_CHALDEAN = {**dict(zip("AIJQY", [1, 1, 1, 1, 1])),
             **dict(zip("BKR", [2, 2, 2])),
             **dict(zip("CGLS", [3, 3, 3, 3])),
             **dict(zip("DMT", [4, 4, 4])),
             **dict(zip("EHNX", [5, 5, 5, 5])),
             **dict(zip("UVW", [6, 6, 6])),
             **dict(zip("OZ", [7, 7])),
             **dict(zip("FP", [8, 8]))}
_VOWELS = set("AEIOU")


def _clean(name):
    return "".join(ch for ch in name.upper() if ch.isalpha())


def _reduce(n, keep_master=True):
    while n > 9:
        if keep_master and n in (11, 22, 33):
            return n
        n = sum(int(d) for d in str(n))
    return n


@lru_cache(maxsize=2048)
def name_numerology(name):
    s = _clean(name)
    if not s:
        return dict(pyth=0, chald=0, soul=0, express=0, master=0, namelen=0)
    pyth_raw = sum(((ord(c) - 65) % 9) + 1 for c in s)
    chald_raw = sum(_CHALDEAN.get(c, 0) for c in s)
    soul_raw = sum(((ord(c) - 65) % 9) + 1 for c in s if c in _VOWELS)
    full = _reduce(pyth_raw)
    return dict(
        pyth=_reduce(pyth_raw), chald=_reduce(chald_raw, keep_master=False),
        soul=_reduce(soul_raw), express=full,
        master=1 if full in (11, 22, 33) else 0, namelen=len(s),
    )


# ---------------------------------------------------------------------------
# WESTERN ASTROLOGY  (date-only; geocentric ecliptic longitudes)
# ---------------------------------------------------------------------------
_BODIES = {"sun": ephem.Sun, "mercury": ephem.Mercury, "venus": ephem.Venus,
           "mars": ephem.Mars, "jupiter": ephem.Jupiter, "saturn": ephem.Saturn}
_DAY_RULER = {0: 1, 1: 4, 2: 2, 3: 5, 4: 3, 5: 6, 6: 0}   # Mon..Sun -> planet code
_EQ_SOL = [(3, 20), (6, 21), (9, 22), (12, 21)]


def _ecl_lon(body_fn, d):
    b = body_fn(d)
    return math.degrees(ephem.Ecliptic(b).lon) % 360.0


def _sep(a, b):
    x = abs(a - b) % 360.0
    return min(x, 360.0 - x)


@lru_cache(maxsize=8192)
def date_astrology(y, m, day):
    d = ephem.Date(_dt.datetime(y, m, day, 12, 0))
    dm1 = ephem.Date(_dt.datetime(y, m, day, 12, 0) - _dt.timedelta(days=1))

    moon = ephem.Moon(d)
    moon_illum = moon.moon_phase * 100.0
    moon_lon = math.degrees(ephem.Ecliptic(moon).lon) % 360.0

    lons = {name: _ecl_lon(fn, d) for name, fn in _BODIES.items()}
    lons_prev = {name: _ecl_lon(fn, dm1) for name, fn in _BODIES.items()}

    def retro(name):
        diff = (lons[name] - lons_prev[name] + 180) % 360 - 180
        return 1 if diff < 0 else 0

    # major aspects within 8deg orb among the classical bodies + moon
    allbodies = {**lons, "moon": moon_lon}
    names = list(allbodies)
    aspect_count = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            s = _sep(allbodies[names[i]], allbodies[names[j]])
            if any(abs(s - a) <= 8 for a in (0, 60, 90, 120, 180)):
                aspect_count += 1

    # solstice / equinox proximity (days to nearest)
    dd = _dt.date(y, m, day)
    prox = min(abs((dd - _dt.date(y, mm, dday)).days) for mm, dday in _EQ_SOL)

    date_num = _reduce(sum(int(c) for c in f"{y}{m:02d}{day:02d}"))

    return dict(
        moon_illum=round(moon_illum, 1),
        moon_zodiac=int(moon_lon // 30),
        moon_nakshatra=int(moon_lon // (360 / 27)),      # Vedic
        sun_zodiac=int(lons["sun"] // 30),
        mercury_zodiac=int(lons["mercury"] // 30),
        venus_zodiac=int(lons["venus"] // 30),
        mars_zodiac=int(lons["mars"] // 30),
        jupiter_zodiac=int(lons["jupiter"] // 30),
        saturn_zodiac=int(lons["saturn"] // 30),
        mercury_retro=retro("mercury"),
        venus_retro=retro("venus"),
        mars_retro=retro("mars"),
        saturn_retro=retro("saturn"),
        moon_jup_sep=round(_sep(moon_lon, lons["jupiter"]), 1),
        moon_mars_sep=round(_sep(moon_lon, lons["mars"]), 1),
        moon_sat_sep=round(_sep(moon_lon, lons["saturn"]), 1),
        sun_moon_sep=round(_sep(lons["sun"], moon_lon), 1),
        mars_sat_sep=round(_sep(lons["mars"], lons["saturn"]), 1),
        aspect_count=aspect_count,
        day_ruler=_DAY_RULER[dd.weekday()],
        eq_sol_prox=prox,
        univ_day=date_num,
        univ_master=1 if date_num in (11, 22, 33) else 0,
    )


# ---------------------------------------------------------------------------
# EASTERN
# ---------------------------------------------------------------------------
def chinese(year):
    return dict(cn_animal=(year - 4) % 12, cn_element=((year - 4) % 10) // 2)


# ---------------------------------------------------------------------------
# ASSEMBLE per-fixture esoteric vector
# ---------------------------------------------------------------------------
def esoteric_features(home, away, date):
    """date: datetime/Timestamp/date. Returns a flat dict of esoteric features."""
    y, m, day = date.year, date.month, date.day
    hn, an = name_numerology(home), name_numerology(away)
    astro = date_astrology(y, m, day)
    cn = chinese(y)

    out = {}
    for k, v in hn.items():
        out[f"eso_H_{k}"] = v
    for k, v in an.items():
        out[f"eso_A_{k}"] = v
    # numerology interactions
    out["eso_num_diff"] = hn["pyth"] - an["pyth"]
    out["eso_num_match"] = int(hn["pyth"] == an["pyth"])
    out["eso_soul_diff"] = hn["soul"] - an["soul"]
    for k, v in astro.items():
        out[f"eso_{k}"] = v
    for k, v in cn.items():
        out[f"eso_{k}"] = v
    return out


ESO_COLUMNS = None   # filled on first call via a probe
def eso_column_names():
    global ESO_COLUMNS
    if ESO_COLUMNS is None:
        ESO_COLUMNS = list(esoteric_features("Probe A", "Probe B",
                                             _dt.date(2020, 6, 15)).keys())
    return ESO_COLUMNS


if __name__ == "__main__":
    import json
    demo = esoteric_features("Real Madrid", "Barcelona", _dt.date(2026, 8, 15))
    print(f"{len(demo)} esoteric features:")
    print(json.dumps(demo, indent=1, default=str))
