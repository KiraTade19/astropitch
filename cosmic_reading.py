"""
AstroPitch - COSMIC READING LAYER  (the brand hook)
============================================================================
Turns the 40 esoteric features (esoteric_features.py) into a readable, fun
per-match astrological + numerological "reading" for the AstroPitch brand.

HARD RULE: this is ENTERTAINMENT. It is never the real prediction and never
claims to improve accuracy - we measured that it doesn't (25_esoteric_test.py).
Every reading carries that disclaimer and a "for fun only" cosmic leaning that
is kept separate from the model's honest pick.
============================================================================
"""
from esoteric_features import esoteric_features

ZODIAC = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
ZGLYPH = ["♈", "♉", "♊", "♋", "♌", "♍", "♎",
          "♏", "♐", "♑", "♒", "♓"]
ANIMALS = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Goat",
           "Monkey", "Rooster", "Dog", "Pig"]
ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"]
PLANET = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
NUM_MEANING = {
    1: "leadership & drive", 2: "balance & partnership", 3: "creative expression",
    4: "discipline & structure", 5: "restless energy & change", 6: "care & harmony",
    7: "mystery & analysis", 8: "power & ambition", 9: "intensity & drama",
    11: "heightened intuition (master number)", 22: "master-builder force",
    33: "master-teacher energy", 0: "the unwritten",
}
NAKSHATRA = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
             "Punarvasu", "Pushya", "Ashlesha", "Magha", "P.Phalguni", "U.Phalguni",
             "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
             "P.Ashadha", "U.Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
             "P.Bhadrapada", "U.Bhadrapada", "Revati"]
ASPECTS = [(0, "conjunct"), (60, "sextile"), (90, "square"),
           (120, "trine"), (180, "opposite")]

DISCLAIMER = ("\U0001F52E For entertainment only. The cosmos does not pick winners - "
              "we tested every one of these factors on 44,000 real matches and they "
              "have no measurable effect on results. The honest prediction is the "
              "model's, shown separately.")


def _moon_phase_name(illum, waxing=True):
    if illum < 5:
        return "New Moon"
    if illum > 95:
        return "Full Moon"
    if illum < 45:
        return "Waxing crescent" if waxing else "Waning crescent"
    if illum < 55:
        return "First/Last quarter"
    return "Waxing gibbous" if waxing else "Waning gibbous"


def _aspect_name(sep):
    for ang, nm in ASPECTS:
        if abs(sep - ang) <= 8:
            return nm
    return None


def cosmic_reading(home, away, date):
    f = esoteric_features(home, away, date)
    moon_sign = ZODIAC[f["eso_moon_zodiac"]]
    moon_phase = _moon_phase_name(f["eso_moon_illum"])
    year_animal = f"{ELEMENTS[f['eso_cn_element']]} {ANIMALS[f['eso_cn_animal']]}"

    retros = [p for p, k in [("Mercury", "eso_mercury_retro"), ("Venus", "eso_venus_retro"),
                             ("Mars", "eso_mars_retro"), ("Saturn", "eso_saturn_retro")]
              if f[k]]

    # notable aspects among the ones we compute
    asp = []
    for lbl, key, a, b in [("Moon", "eso_moon_jup_sep", "Moon", "Jupiter"),
                           ("Moon", "eso_moon_mars_sep", "Moon", "Mars"),
                           ("Moon", "eso_moon_sat_sep", "Moon", "Saturn"),
                           ("Sun", "eso_sun_moon_sep", "Sun", "Moon"),
                           ("Mars", "eso_mars_sat_sep", "Mars", "Saturn")]:
        nm = _aspect_name(f[key])
        if nm:
            asp.append(f"{a} {nm} {b}")

    hv, av = f["eso_H_pyth"], f["eso_A_pyth"]
    headline = (f"{ZGLYPH[f['eso_moon_zodiac']]} {moon_phase} in {moon_sign} · "
                f"{PLANET[f['eso_day_ruler']]}'s day · Year of the {year_animal}")

    moon_txt = (f"The {moon_phase} sits in {moon_sign} "
                f"({f['eso_moon_illum']:.0f}% lit), in the {NAKSHATRA[f['eso_moon_nakshatra']]} "
                f"nakshatra.")
    planet_txt = ("All classical planets are direct." if not retros
                  else f"{', '.join(retros)} retrograde — the classic omen of "
                       f"{'miscommunication and slips' if 'Mercury' in retros else 'second-guessing'}.")
    aspect_txt = ("No tight major aspects today." if not asp
                  else "Sky tension: " + "; ".join(asp) + ".")
    num_txt = (f"{home} vibrates to {hv} ({NUM_MEANING.get(hv, '')}); "
               f"{away} to {av} ({NUM_MEANING.get(av, '')}). "
               + ("Matched name-numbers — a mirror match." if hv == av
                  else f"The day's Universal number is {f['eso_univ_day']} "
                       f"({NUM_MEANING.get(f['eso_univ_day'], '')})."))

    # playful, entertainment-only leaning (NOT the model)
    score_h = (hv == f["eso_univ_day"]) + (f["eso_H_master"]) + (f["eso_day_ruler"] in (0, 5))
    score_a = (av == f["eso_univ_day"]) + (f["eso_A_master"])
    if score_h > score_a:
        leaning = f"the stars tilt faintly toward {home}"
    elif score_a > score_h:
        leaning = f"the stars tilt faintly toward {away}"
    else:
        leaning = "the cosmos is undecided — a true coin of fate"

    return {
        "headline": headline,
        "moon": moon_txt,
        "planets": planet_txt,
        "aspects": aspect_txt,
        "numerology": num_txt,
        "eastern": f"Played in the Year of the {year_animal}.",
        "cosmic_leaning": f"\U0001F52E For fun: {leaning}.",
        "disclaimer": DISCLAIMER,
        "text": " ".join([headline + ".", moon_txt, planet_txt, aspect_txt, num_txt]),
    }


if __name__ == "__main__":
    import datetime, json
    r = cosmic_reading("Real Madrid", "Barcelona", datetime.date(2026, 8, 15))
    print(json.dumps(r, indent=1, ensure_ascii=False))
