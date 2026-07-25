# AstroPitch — Double Chance: Club Friendlies, 25–26 July 2026

**Double chance** covers two of the three outcomes, so you only lose if the one you excluded happens. On our 4,000-match holdout this scores **77.4% accuracy vs 50.6% for outright 1X2** — the same model, an easier question.

| Date | KO | Match | 1X | 12 | X2 | **Best** | Prob | Fair odds | You lose if |
|---|---|---|---|---|---|---|---|---|---|
| 07-25 | 09:30 | **RB Leipzig** vs **Ingolstadt** | 93% | 87% | 20% | **1X** | **93%** | 1.07 | away win |
| 07-25 | 13:00 | **Mainz** vs **Holstein Kiel** | 83% | 78% | 39% | **1X** | **83%** | 1.20 | away win |
| 07-25 | 13:00 | **Kickers Offenbach** vs **Leverkusen** | 15% | 91% | 94% | **X2** | **94%** | 1.06 | home win |
| 07-25 | 13:30 | **Wehen Wiesbaden** vs **Bayern Munich** | 22% | 87% | 91% | **X2** | **91%** | 1.09 | home win |
| 07-25 | 14:00 | **Celtic** vs **AC Milan** | 56% | 76% | 68% | **12** | **76%** | 1.31 | the draw |
| 07-25 | 14:00 | **Bologna** vs **Iraklis** | 95% | 90% | 15% | **1X** | **95%** | 1.05 | away win |
| 07-25 | 14:00 | **QPR** vs **Fiorentina** | 54% | 76% | 70% | **12** | **76%** | 1.32 | the draw |
| 07-25 | 15:00 | **Genoa** vs **Vicenza** | 85% | 78% | 37% | **1X** | **85%** | 1.18 | away win |
| 07-25 | 15:30 | **Konyaspor** vs **Hull City** | 59% | 74% | 66% | **12** | **74%** | 1.34 | the draw |
| 07-25 | 16:00 | **PSV Eindhoven** vs **Villarreal** | 73% | 74% | 53% | **12** | **74%** | 1.35 | the draw |
| 07-25 | 16:00 | **Marseille** vs **Nice** | 77% | 76% | 48% | **1X** | **77%** | 1.30 | away win |
| 07-25 | 16:00 | **Wolverhampton** vs **Real Sociedad** | 70% | 73% | 57% | **12** | **73%** | 1.38 | the draw |
| 07-25 | 16:00 | **Rennes** vs **Club Brugge** | 66% | 74% | 60% | **12** | **74%** | 1.36 | the draw |
| 07-25 | 17:00 | **Celta Vigo** vs **Sporting Gijon** | 83% | 77% | 39% | **1X** | **83%** | 1.20 | away win |
| 07-25 | 17:00 | **Athletic Bilbao** vs **Eibar** | 79% | 75% | 47% | **1X** | **79%** | 1.27 | away win |
| 07-25 | 17:00 | **Malaga** vs **Leicester** | 72% | 73% | 55% | **12** | **73%** | 1.36 | the draw |
| 07-25 | 18:00 | **Standard Liege** vs **Juventus** | 43% | 78% | 79% | **X2** | **79%** | 1.27 | home win |
| 07-25 | 19:00 | **Porto** vs **Aston Villa** | 62% | 74% | 64% | **12** | **74%** | 1.35 | the draw |
| 07-25 | 22:00 | **Liverpool** vs **Sunderland** | 82% | 78% | 40% | **1X** | **82%** | 1.22 | away win |
| 07-26 | 15:00 | **Rangers** vs **West Ham** | 51% | 77% | 71% | **12** | **77%** | 1.29 | the draw |

## What the columns mean

- **1X** = home win *or* draw · **12** = home *or* away win (no draw) · **X2** = draw *or* away win
- **Best** = the double chance our model rates highest, i.e. excluding the outcome it thinks least likely
- **Fair odds** = 1 ÷ our probability. If a bookmaker offers *more* than this, our model considers it value; less, and it does not. (These are our fair prices, not a recommendation.)

## The honest trade-off

Double chance is **not free accuracy** — it is a *different, easier question*, and you are paid accordingly. At 93% on RB Leipzig 1X the fair price is 1.07, so a bookmaker might offer ~1.05: you would win ~19 times out of 20 and still barely profit. Higher hit rate, smaller payout. Nothing about this beats the market; it just reframes the bet.

## Two caveats specific to this slate

1. **These are pre-season friendlies.** Our model was trained on competitive matches. Expect worse than the 77.4% holdout figure here.
2. **The eight “12” (no-draw) picks are the most exposed.** Our model has no friendly-specific draw calibration, and there is a plausible argument that friendlies produce *more* draws than competitive games because neither side is chasing a result. We have not measured this — we have no historical friendly dataset — so treat those eight as the least reliable rows in the table.

---
*Probabilistic model output for information and entertainment, not betting advice. 18+. Please gamble responsibly.*