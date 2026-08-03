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

Six feature ideas have been through the same 5-window holdout gate. Only one
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

The pattern: gains need genuinely **new information**, not re-slices of what
ELO+form already encode. And any apparent win must survive a leak check *and* a
coverage-bias check before being believed.
