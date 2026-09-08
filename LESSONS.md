# What the graded results taught us

Measured on the 4,000-match competitive holdout plus 55 live graded predictions
(36 competitive, 19 friendlies). Every number here is from a real test, not an
estimate.

---

## 1. "Predict more draws" would make us WORSE — this is settled

The obvious reaction to 4/19 draws while calling zero of them is "the model
should predict draws." We tested it. It is wrong:

| Decision rule | Accuracy (4,000 matches) |
|---|---|
| **argmax (current)** | **50.62%** |
| pick DRAW when P(draw) ≥ 0.30 | 50.42% |
| pick DRAW when P(draw) ≥ 0.28 | 47.12% |
| pick DRAW when P(draw) ≥ 0.26 | 43.85% |
| pick DRAW when P(draw) ≥ 0.24 | 41.02% |
| always HOME | 42.98% |

Every draw-picking rule loses accuracy, monotonically. And our draw
probabilities are already **well calibrated**:

| We said | Actual draw rate |
|---|---|
| 0–18% | 16.9% |
| 18–22% | 21.1% |
| 22–25% | 26.5% |
| 25–28% | 29.5% |

Mean predicted 24.7% vs actual 26.3%. So the model *knows* about draws; it just
never makes the draw its single best guess, because a draw is almost never more
likely than both other outcomes. **argmax is the accuracy-maximising rule given
calibrated probabilities.** The ~26% of matches that end level are structurally
unwinnable on outright 1X2. That is a property of football, not a bug to fix.

**Action:** stop treating "no draw picks" as a defect. Report double chance and
confidence tiers instead (below).

---

## 2. Double chance is the real accuracy lever — but not all types are equal

| Type | Accuracy | Sample | Avg confidence |
|---|---|---|---|
| **X2** (draw or away) | **81.7%** | 687 | 81% |
| **1X** (home or draw) | **81.4%** | 2,060 | 82% |
| **12** (home or away — *no draw*) | **72.9%** | 1,253 | 72% |
| overall | 78.8% | 4,000 | — |

Live confirmation on the 25 Jul friendlies: **15/19 = 78.9%**, essentially
identical to the holdout figure — and **3 of the 4 misses were "12"** picks
undone by draws, exactly the risk flagged before kickoff.

### Why "12" is structurally weak (not bad luck)

P(draw) has a **high floor** — median 26.7%, 5th percentile 13.7%. Excluding the
draw therefore caps your ceiling: the highest "12" confidence ever produced was
92.3%, and it rarely clears 80%. By contrast 1X reaches 96.1% and X2 91.5%,
because the outcome they exclude (a specific team winning) can genuinely be
near-zero.

### The publishing rule that works

| Rule | Published | % of slate | Accuracy |
|---|---|---|---|
| all double chance | 4,000 | 100% | 78.8% |
| skip "12" | 2,747 | 68.7% | 81.4% |
| **confidence ≥ 80%** | **1,439** | **36.0%** | **87.1%** |
| confidence ≥ 85% | 848 | 21.2% | 90.3% |

Elegantly, **the ≥80% filter self-excludes almost every "12" pick** — they
structurally can't get that high — so one simple threshold does both jobs.

**Live validation on the 20 friendlies:** all DC 75.0% → skip-12 81.8% (9/11) →
**≥80% confidence 87.5% (7/8)**. The holdout rule replicated out-of-sample.

**Action (shipped):** the slate emits `dc`, `dc_prob`, `dc_tier`
(high ≥80% / medium ≥70% / low) and `dc_reliability`. Lead with the **high**
tier; treat "12" as the weakest row on any card.

---

## 3. Confidence tiering: publish less, be right more

| Only publish when confidence ≥ | Matches kept | Accuracy |
|---|---|---|
| (all) | 100% | 50.6% |
| 50% | 47.9% | 61.3% |
| 60% | 27.1% | 69.8% |
| 70% | 13.6% | 74.5% |

Honest and useful — provided the coverage is stated. "74.5% accurate" alone is
misleading; "74.5% on the 14% of matches we're most confident about" is true.

**Action:** lead with tiered confidence publicly rather than the flat 50.6%.

---

## 4. Lean harder on the market when odds exist

On the 19 graded friendlies:

| | Accuracy | Log-loss |
|---|---|---|
| our model | 47.4% | 0.9852 |
| **the market** | **52.6%** | **0.9405** |

The blend sweep was monotonic all the way to pure market (w=1.0) — matching the
much larger 24,330-match closing-odds study (`17_odds_value.py`), which found the
same thing. Two independent tests, same direction.

**Action (shipped):** `W_MARKET_DEFAULT` in `27_euro_predict.py` raised
**0.60 → 0.85**. Not 1.0, because these are pre-match rather than closing prices
and the model must still carry matches with no line at all.

---

## 5. Friendlies need their own treatment

19 graded friendlies: 47.4% vs 50.0% on competitive matches. The standout:
**Wehen Wiesbaden (1360) beat Bayern (2001)** — a 641-point rating gap — and our
91% double chance lost, because Bayern rotated their squad.

Squad strength means much less in pre-season. Until there is enough friendly data
to calibrate on, the honest move is to **shrink extreme probabilities toward the
market** in friendlies (item 4 does much of this) and to keep labelling them
separately in the track record, as we already do.

**Tested and rejected — a friendly-specific draw boost.** Draws ran 5/20 (25%)
in friendlies while we averaged 21.6%, which looks like under-prediction. But
comparing our draw probabilities against the *market's* on the same 20 matches
(far more statistically efficient than inferring from 20 outcomes) the gap is
only **−0.62pp, p = 0.14 — not significant**. Adjusting on that would be fitting
noise. No change made. Revisit once there are ~200 graded friendlies.

---

## Not worth pursuing (already tested and rejected)

Seven feature ideas have been through the same 5-window holdout gate. Only one
survived:

| Idea | Verdict |
|---|---|
| **Shots on target (xG proxy)** | ✅ **shipped** — robust, +0.4pp accuracy |
| Esoteric (astrology/numerology) | ❌ no effect (Δlog-loss +0.0007) |
| Referee → cards | ❌ importance without value |
| Weather / season | ❌ absorbed by rolling form |
| ELO momentum | ❌ made log-loss worse |
| Squad market value | ❌ "win" was leakage, then coverage bias |
| Poisson attack/defence model | ❌ lost to XGBoost (1.024 vs 0.995) |
| **Second ELO built on shots** | ❌ **null** — see below, do not retry |

The pattern: gains need genuinely **new information**, not re-slices of what
ELO+form already encode. And any apparent win must survive a leak check *and* a
coverage-bias check before being believed.

---

## A shot-based ELO adds nothing — and why the pilot study said it would

Goals are the noisiest observable in football, so a rating that learns from
shots on target instead of goals *should* be better. We built it: a second ELO
(`selo`) on the identical update rule, K and margin weighting, scoring the
shots-on-target margin converted to goal-equivalents (measured ratio 2.2), plus
an `ELO_Gap` feature for how far results have run ahead of the underlying
performance. Then we retrained and measured.

| Feature set (same tuned hyper-parameters) | Holdout log-loss | vs baseline |
|---|---|---|
| baseline, 27 features, goals only | 0.99554 | — |
| baseline + `ELO_Gap` only (28) | 0.99481 | −0.00073 |
| baseline + all five shot features (32) | 0.99469 | −0.00085 |
| shot ELO **replacing** the goal ELO (28) | 0.99816 | **+0.00262** |

Fully retrained, the 32-feature engine scored 0.99475 against the old engine's
0.99521 on the same untouched 4,000-match holdout: **+0.00046 nats, paired
t = 0.55, bootstrap 95% CI [−0.00114, +0.00210]**. The interval spans zero.
Accuracy went *down*, 50.62% → 50.55%. On evenly-matched fixtures
(|ELO diff| < 100) — the exact place the idea was supposed to help most — it was
**worse**, −0.00052. Reverted.

**The methodological trap, which is the real lesson.** The pilot study looked
convincing: as a standalone signal, shots-on-target form beat goal-difference
form by **0.0128 nats** over 30,858 matches, and by 0.0107 on tight fixtures.
That measured the value of shot information *against nothing*. The engine
already carries `H_SoT10`, `H_SoTA10`, `A_SoT10`, `A_SoTA10` and `SoT_Dom` — the
shot information was in the model already, so a shot *rating* is largely
redundant with shot *form*. The two ratings correlate at **0.944**.

Before believing any feature study, check what the production model already
encodes. Marginal value against a bare baseline does not transfer to marginal
value against a 27-feature model.

The one thing worth keeping from the exercise is descriptive, not predictive:
the gap between the two ratings identifies clubs whose results flatter or
understate them (Angers +115, West Ham +108 over-performing; Panathinaikos
−115, West Brom −109 under-performing). That is publishable content, not an
accuracy gain.

---

## Over/under belongs to the scoreline matrix, not its own classifier

The README used to claim 1X2, over/under and every scoreline came from one
Dixon-Coles model. They did not. `over_under_2_5` was a separate XGBoost
classifier while `likely_scores` came from the goal regressors, and the two
disagreed by **3.6 points on average and up to 26** across the holdout.

Reading O/U off the scoreline matrix instead is not just more coherent, it is
**better**, and unlike most of what we test the margin clears the noise bar:

| O/U 2.5 source | Log-loss | Brier | Accuracy |
|---|---|---|---|
| XGBoost classifier (was published) | 0.6881 | 0.2475 | 54.67% |
| Dixon-Coles matrix, raw | 0.6849 | 0.2460 | 54.95% |
| **Dixon-Coles matrix, projected onto the 1X2** | **0.6843** | **0.2457** | **55.10%** |

Paired **t = 2.05, bootstrap 95% CI [+0.00015, +0.00620]**, P(better) 97.9%.

Two changes shipped together. The scoreline matrix is now projected onto the
published 1X2 **always**, not only when odds are supplied — previously the
no-odds path left the matrix and the 1X2 free to disagree. And O/U is read off
that projected matrix. Exact-score top-1 costs 0.25pp (13.15% → 12.90%) for
that coherence, which is inside the noise on 4,000 matches.

The `ou` classifier is still trained and kept in the pickle so the comparison
can be re-run; it is simply no longer what we publish.

---

## Stale ratings: decayed, but honestly labelled as a guess

A club that leaves a covered division keeps its rating frozen forever. On one
September card, Deportivo A Coruna and Malaga were priced off **May 2018**
ratings and still landed in bands the slate called confident.

`gpc.decayed_elo` now regresses a stale rating toward its division's mean at
prediction time (never in training, where every club is active), and
`36_weekly_slate.py` refuses to publish a **high** confidence tier for any
fixture resting on a materially decayed rating.

**This is a prudence measure, not a measured accuracy gain, and it should not be
described as one.** The natural experiment is far too small to fit: only **123
matches in 33,074** involve a club returning after a 300-day absence. On that
sample returning clubs *out*-perform their frozen rating (expected score 0.327
vs actual 0.389, bias **+0.062, t ≈ 1.7** — not significant), which is the
opposite of the naive assumption that a stale rating flatters a club. Promotion
selects for clubs that have been winning.

So the half-life (550 days, after a 150-day grace) is **chosen, not fitted**.
It is safe by construction rather than by evidence: the 99th percentile gap
between a club's matches is 91 days, and the longest normal off-season in this
data is 122 days, so the grace window makes it a no-op for over 99% of
fixtures. It fires only where the rating genuinely is old — e.g. Kortrijk,
relegated from Belgium in May 2025 and back on a 2026 card at weight 0.66,
which correctly drops that fixture from "high" to "medium".
