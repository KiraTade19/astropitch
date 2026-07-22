# AstroPitch: ML Accuracy Improvement Strategies

The AstroPitch engine currently relies heavily on esoteric features (astrology, numerology, biorhythms) and synthetic data generation. To transition from an experimental feature set to a production-grade predictive model with genuine betting value, the following structural improvements must be made.

## 1. Data Engineering (The Foundation)

### Replace Synthetic Data with Historical Data

Generating synthetic data via Poisson distribution inherently limits the model to predicting the mathematical rules you created. To discover real-world alpha:

- **Action**: Scrape real historical results, lineups, and odds from `football-data.co.uk` and `fbref.com`.
- **Target**: Minimum of 10 seasons of historical data per league. World Cup models should include all international matches (friendlies, qualifiers, tournaments) from 2000-present.

### Implement Proper Cross-Validation

Currently, the genesis scripts use a single train/test split (or train on the entire dataset). This guarantees overfitting.

- **Action**: Use **Time-Series Cross-Validation** (e.g., `TimeSeriesSplit` in scikit-learn). Never predict past matches using future data.

## 2. Feature Engineering (The Signal)

Esoteric features may have variance, but they cannot form the baseline of an edge. You must supply the model with true team strength metrics.

### Expected Goals (xG) Momentum

- **Action**: Instead of a static baseline xG, calculate dynamic rolling averages of xG generated and xG conceded over the last 1, 3, 5, and 10 matches.

### ELO / True Power Ratings

- **Action**: Implement a custom ELO rating system that updates after every match. A team's ELO difference relative to their opponent is the single highest-correlating feature to match outcomes.
- **World Cup Specific**: International teams play rarely. A global ELO ranking (incorporating opponent strength in qualifiers) is critical to assessing out-of-confederation matchups (e.g., Mexico vs. Canada).

### Squad Value and Injury Impact

- **Action**: Pull total squad market value (via Transfermarkt API). A £1B squad inherently beats a £50M squad 80% of the time, regardless of the lunar cycle. Subtract the value of injured key players from the total.

### Schedule Fatigue

- **Action**: Calculate `Days_Since_Last_Match` and `Distance_Travelled`. For the World Cup spanning USA/Mexico/Canada, travel fatigue and altitude changes (e.g., playing in Mexico City at 7,300ft) will heavily impact physiological performance.

## 3. Modeling Techniques (The Engine)

### Ensemble Architecture

Relying purely on XGBoost restricts learning topology.

- **Action**: Build a **Stacking Regressor/Classifier**. Level 1: XGBoost (Tree), LightGBM (Tree), CatBoost (Categorical Tree), and a simple Logistic Regression (Baseline). Level 2: A meta-XGBoost model that learns how to weight the Level 1 models based on the context.

### Target Calibration (Platt Scaling)

When XGBoost outputs a probability of 0.45, it rarely means a true 45% real-world probability unless properly calibrated.

- **Action**: Apply **Platt Scaling** or **Isotonic Regression** to calibrate the probability outputs. Brier Score should be your primary evaluation metric, not just accuracy.

### Hyperparameter Optimization

Current max depths of 6 and 8 are likely memorizing noise.

- **Action**: Integrate **Optuna** to perform Bayesian optimization over hundreds of trials. Tune `max_depth`, `learning_rate`, `subsample`, and `colsample_bytree` specifically against a holdout test set to control complexity.

## 4. Evaluation (The Proof)

### Feature Importance & SHAP Values

Are the esoteric features actually contributing, or are they acting as random noise?

- **Action**: Generate **SHAP summary plots**. If `Moon_Jup_Sep` has a SHAP value near 0 across all predictions, the model is ignoring it. Prune features with low SHAP impact to reduce dimensionality and improve generalization.

### Walk-Forward Backtesting

- **Action**: Run a simulated betting strategy starting from 2018 to 2024 using your model's outputs vs historical closing Pinnacle odds. Track the simulated Bankroll Growth using the Kelly Criterion logic already in the code. If the graph goes down, the edge does not exist.
