"""
Invariants the published numbers depend on. Run from anywhere:

    python -m pytest tests -q

Each test locks in a property that has already been silently broken once:
1X2, over/under and the scorelines disagreeing with each other; the API and the
weekly slate drifting apart as hand-maintained copies; the track-record logger
grading numbers we had stopped publishing; stale ratings passed off as
confident; and the updater quietly ignoring a new season.

No network access, no writes. Everything runs against the committed engines.
"""
import datetime as dt
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)                  # every module here loads its data by relative path
sys.path.insert(0, str(ROOT))

DATE = dt.datetime(2026, 9, 5)
ODDS = (2.10, 3.40, 3.60)
FIXTURES = [("Arsenal", "Chelsea", "E0"), ("Brentford", "Sunderland", "E0"),
            ("Barcelona", "Real Madrid", "SP1"), ("Inter", "Napoli", "I1"),
            ("Celtic", "Aberdeen", "SC0")]
SIDES = ("home", "draw", "away")


def _load(fname, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def gpc():
    return _load("21_club_genesis.py", "gpc_under_test")


@pytest.fixture(scope="module")
def api():
    return _load("24_api.py", "api_under_test")


@pytest.fixture(scope="module")
def weekly():
    return _load("36_weekly_slate.py", "weekly_under_test")


@pytest.fixture(scope="module")
def tracker():
    return _load("23_track_record.py", "tracker_under_test")


@pytest.fixture(scope="module")
def updater():
    return _load("22_update_club_data.py", "updater_under_test")


def _published(api, home, away, div, odds):
    X, _ = api.build_row_club(home, away, DATE, div)
    return X, api.predict_core(api.CLUB, X, "club", odds)


# ---------------------------------------------------------------------------
# the shared helpers
# ---------------------------------------------------------------------------
def test_projection_reproduces_the_target_1x2(gpc):
    rng = np.random.default_rng(0)
    for _ in range(50):
        M = gpc.dc_matrix(rng.uniform(0.3, 3.0), rng.uniform(0.3, 3.0), -0.05, maxg=8)
        p = rng.dirichlet([2, 2, 2])
        P = gpc.project_onto_1x2(M, p)
        i, j = np.indices(P.shape)
        assert np.allclose([P[i > j].sum(), P[i == j].sum(), P[i < j].sum()], p, atol=1e-12)
        assert P.sum() == pytest.approx(1.0)
        assert (P >= 0).all()


def test_projection_leaves_its_input_alone(gpc):
    M = gpc.dc_matrix(1.4, 1.1, -0.05, maxg=8)
    before = M.copy()
    gpc.project_onto_1x2(M, np.array([0.5, 0.3, 0.2]))
    assert np.array_equal(M, before)


def test_over25_matches_brute_force(gpc):
    M = gpc.dc_matrix(1.7, 0.9, -0.05, maxg=8)
    brute = sum(M[a, b] for a in range(9) for b in range(9) if a + b >= 3)
    assert gpc.over25(M) == pytest.approx(brute, abs=1e-12)


# ---------------------------------------------------------------------------
# one distribution, everywhere it is published or logged
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("odds", [None, ODDS], ids=["no-odds", "with-odds"])
@pytest.mark.parametrize("home,away,div", FIXTURES)
def test_api_1x2_ou_and_scorelines_are_one_distribution(api, home, away, div, odds):
    X, out = _published(api, home, away, div, odds)
    final = np.array([out["one_x_two"][k] for k in SIDES])
    lam = float(np.clip(api.CLUB["reg_h"].predict(X)[0], 0.15, 6))
    mu = float(np.clip(api.CLUB["reg_a"].predict(X)[0], 0.15, 6))
    M = api.gpc.project_onto_1x2(api.gpc.dc_matrix(lam, mu, api.CLUB["rho"], maxg=8), final)
    assert out["over_under_2_5"]["over"] == pytest.approx(api.gpc.over25(M), abs=5e-4)
    bi, bj = np.unravel_index(M.argmax(), M.shape)
    assert out["likely_scores"][0]["score"] == f"{bi}-{bj}"


@pytest.mark.parametrize("home,away,div", FIXTURES)
def test_weekly_slate_publishes_the_same_numbers_as_the_api(api, weekly, home, away, div):
    """Two hand-maintained copies of the prediction path is how O/U drifted in
    the first place. Same fixture, same odds, same published numbers."""
    _, a = _published(api, home, away, div, ODDS)
    w = weekly.predict_core(home, away, DATE, div, ODDS)
    assert w["final"] == pytest.approx([a["one_x_two"][k] for k in SIDES], abs=2e-3)
    assert w["over25"] == pytest.approx(a["over_under_2_5"]["over"], abs=2e-3)
    assert w["scores"][0]["score"] == a["likely_scores"][0]["score"]


@pytest.mark.parametrize("home,away,div", FIXTURES)
def test_track_record_logs_what_we_publish(api, tracker, home, away, div):
    """Regression: the logger took O/U from the retired classifier and the
    scoreline from the unprojected matrix, so it graded numbers nobody saw.
    It logs model-only probabilities, so compare against the no-odds output."""
    _, published = _published(api, home, away, div, None)
    Xl = tracker._build_row_live(home, away, DATE, div)
    p = tracker.E["model_1x2"].predict_proba(Xl)[0]
    lam = float(np.clip(tracker.E["reg_h"].predict(Xl)[0], 0.15, 6))
    mu = float(np.clip(tracker.E["reg_a"].predict(Xl)[0], 0.15, 6))
    _, p_over, (bi, bj) = tracker.score_outputs(p, lam, mu)
    assert p_over == pytest.approx(published["over_under_2_5"]["over"], abs=5e-4)
    assert f"{bi}-{bj}" == published["likely_scores"][0]["score"]


def test_every_row_builder_emits_the_same_feature_row(api, weekly, tracker):
    feats = list(api.CLUB["features"])
    X_api, _ = api.build_row_club("Arsenal", "Chelsea", DATE, "E0")
    X_wk = weekly._row("Arsenal", "Chelsea", DATE, "E0")
    X_tr = tracker._build_row_live("Arsenal", "Chelsea", DATE, "E0")
    for X in (X_api, X_wk, X_tr):
        assert list(X.columns) == feats
        assert not X.isna().any().any()
    assert np.allclose(X_api.to_numpy(float), X_wk.to_numpy(float))
    assert np.allclose(X_api.to_numpy(float), X_tr.to_numpy(float))


# ---------------------------------------------------------------------------
# stale ratings
# ---------------------------------------------------------------------------
def test_stale_weight_shape(gpc):
    g, h = gpc.STALE_GRACE_DAYS, gpc.STALE_HALF_LIFE_DAYS
    assert gpc.stale_weight(None) == 1.0
    assert gpc.stale_weight(0) == 1.0
    assert gpc.stale_weight(g) == 1.0
    assert gpc.stale_weight(g + 1) < 1.0
    assert gpc.stale_weight(g + h) == pytest.approx(0.5)
    ws = [gpc.stale_weight(d) for d in range(g, g + 5 * h, 30)]
    assert all(a >= b for a, b in zip(ws, ws[1:]))


def test_decay_leaves_every_club_from_last_season_alone(api):
    """The grace window must cover a normal summer break for every club that
    finished last season, or the decay is quietly rewriting ordinary fixtures.
    110 days after the final matchday is mid-September: today's situation."""
    st = api.CLUB["state"]
    season_end = max(st["last_date"].values())
    date = season_end + dt.timedelta(days=110)
    active = [t for t, d in st["last_date"].items() if (season_end - d).days <= 30]
    assert len(active) > 150
    for team in active:
        rating, _, w = api.gpc.decayed_elo(st, team, date)
        assert w == 1.0 and rating == st["elo"][team], team


def test_long_absent_club_regresses_to_its_division_mean(api):
    st = api.CLUB["state"]
    mean = api.gpc.division_mean_elo(st)[st["team_league"]["Malaga"]]
    rating, days_out, w = api.gpc.decayed_elo(st, "Malaga", DATE)
    assert days_out > 2500 and w < 0.05
    assert abs(rating - mean) <= abs(st["elo"]["Malaga"] - mean) * 0.05


def test_decay_never_touches_the_international_engine(api):
    X = api.build_row_intl("Brazil", "Japan", DATE, False)
    st = api.INTL["state"]
    assert X["H_ELO"].iloc[0] == st["elo"]["Brazil"]
    assert X["A_ELO"].iloc[0] == st["elo"]["Japan"]


@pytest.mark.parametrize("prob,weight,expected", [
    (0.85, 1.00, "high"), (0.80, 1.00, "high"), (0.85, 0.95, "high"),
    (0.85, 0.89, "medium"), (0.85, 0.02, "medium"),
    (0.75, 1.00, "medium"), (0.70, 1.00, "medium"), (0.75, 0.02, "medium"),
    (0.65, 1.00, "low")])
def test_confidence_tier_never_calls_a_stale_row_high(weekly, prob, weight, expected):
    assert weekly.dc_tier(prob, weight) == expected


# ---------------------------------------------------------------------------
# data ingest
# ---------------------------------------------------------------------------
def test_updater_always_fetches_the_current_season(updater):
    """Regression: SEASONS was a hand-kept list nobody updated in August, so
    the 2026-27 season was never ingested and 571 logged predictions sat
    ungradeable for six weeks while the daily run reported success."""
    assert updater.season_code(dt.date.today()) in updater.SEASONS
    assert updater.season_code(dt.date(2026, 9, 13)) == "2627"
    assert updater.season_code(dt.date(2026, 6, 30)) == "2526"
    assert updater.season_code(dt.date(2026, 7, 1)) == "2627"
    assert updater.season_code(dt.date(1999, 8, 1)) == "9900"
