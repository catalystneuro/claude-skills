# Fitting GLMs Reference

## GLM Class

```python
import nemos as nmo

model = nmo.glm.GLM(
    observation_model="Poisson",        # or "Gaussian", "Gamma", etc.
    regularizer="Ridge",                # or "Lasso", "GroupLasso", "UnRegularized"
    regularizer_strength=0.1,           # float, controls regularization
    solver_name="LBFGS",                # optimization algorithm
    solver_kwargs={"tol": 1e-12},       # solver-specific options
)
```

## Observation Models

| Model | Use Case | Default Link |
|-------|----------|-------------|
| `"Poisson"` | Spike counts (most common) | `exp` |
| `"Gaussian"` | Continuous signals (calcium, LFP) | `identity` |
| `"Gamma"` | Positive continuous data | `exp` |
| `"Bernoulli"` | Binary outcomes | `logistic` |
| `"NegativeBinomial"` | Overdispersed counts | `exp` |

```python
# Using string shorthand (recommended)
model = nmo.glm.GLM(observation_model="Poisson")

# Or explicit observation model object
from nemos.observation_models import PoissonObservations
model = nmo.glm.GLM(observation_model=PoissonObservations())
```

## Regularizers

| Regularizer | Penalty | Use Case |
|-------------|---------|----------|
| `"UnRegularized"` | None | Small models, no overfitting concern |
| `"Ridge"` | L2: `alpha * \|\|w\|\|^2` | General regularization, smooth weights |
| `"Lasso"` | L1: `alpha * \|\|w\|\|_1` | Sparse solutions, feature selection |
| `"GroupLasso"` | Group L1 | Group-sparse solutions |
| `"ElasticNet"` | L1 + L2 | Combined sparsity and smoothness |

```python
# String shorthand
model = nmo.glm.GLM(regularizer="Ridge", regularizer_strength=0.1)

# Or explicit regularizer object
from nemos.regularizer import Ridge
model = nmo.glm.GLM(regularizer=Ridge(), regularizer_strength=0.1)
```

## Solvers

Common solver choices:
- `"LBFGS"` - good general-purpose solver, works with Ridge/UnRegularized
- `"GradientDescent"` - simple, reliable
- `"ProximalGradient"` - required for Lasso/GroupLasso
- `"SVRG"` - stochastic solver for large datasets

```python
model = nmo.glm.GLM(
    solver_name="LBFGS",
    solver_kwargs={"tol": 1e-12, "maxiter": 500}
)
```

## Fitting

```python
# X: (n_time_bins, n_features), y: (n_time_bins,)
model.fit(X, y)

# With pynapple objects (preserves time info)
model.fit(X_tsd, count_tsd)
```

## Accessing Fitted Parameters

```python
model.coef_         # learned coefficients, shape depends on model
model.intercept_    # intercept (bias) term
model.solver_state_ # solver convergence info
```

## Prediction

```python
# Returns predicted rate in counts/bin
predicted_rate = model.predict(X)

# Convert to Hz
predicted_rate_hz = predicted_rate / bin_size

# If X is a pynapple object, output is also pynapple
predicted_tsd = model.predict(X_tsd)
```

## Scoring

```python
# Log-likelihood score (higher is better)
ll = model.score(X, y)

# Compare models
ll_simple = simple_model.score(X_simple, y)
ll_complex = complex_model.score(X_complex, y)
```

## Simulation

```python
# Simulate spike trains from the fitted model
simulated_counts = model.simulate(X)
```

## Complete Single-Neuron Example

```python
import nemos as nmo
import pynapple as nap
import numpy as np

# Load data
data = nap.load_file("data.nwb")
spikes = data["units"]
stimulus = data["stimulus"]

# Restrict to epoch of interest
epoch = data["epochs"][0]
spikes = spikes.restrict(epoch)
stimulus = stimulus.restrict(epoch)

# Bin spikes
bin_size = 0.001  # 1 ms
count = spikes[0].count(bin_size)

# Match stimulus sampling to count
binned_stimulus = stimulus.interpolate(count, ep=count.time_support)

# Option A: Instantaneous model (no history)
# Predictor must be 2D
X_instant = np.expand_dims(binned_stimulus.values, axis=1)
model_instant = nmo.glm.GLM(solver_name="LBFGS")
model_instant.fit(X_instant, count)

# Option B: History model with basis functions
basis = nmo.basis.RaisedCosineLogConv(n_basis_funcs=10, window_size=100)
X_history = basis.compute_features(binned_stimulus)
model_history = nmo.glm.GLM(solver_name="LBFGS")
model_history.fit(X_history, count)

# Compare via log-likelihood
print(f"Instant LL: {model_instant.score(X_instant, count):.4f}")
print(f"History LL: {model_history.score(X_history, count):.4f}")

# Predict and visualize
pred_rate = model_history.predict(X_history) / bin_size
smooth_pred = pred_rate.smooth(std=0.05, size_factor=20)
```

## Train/Test Split

```python
# Simple half-split
duration = X.time_support.tot_length("s")
start = X.time_support["start"]
end = X.time_support["end"]

train_ep = nap.IntervalSet(start, start + duration / 2)
test_ep = nap.IntervalSet(start + duration / 2, end)

# Fit on training data
model.fit(X.restrict(train_ep), y.restrict(train_ep))

# Evaluate on test data
test_score = model.score(X.restrict(test_ep), y.restrict(test_ep))
```

## Computing Tuning Curves from Predictions

```python
# Predict firing rate
predicted_rate = model.predict(X) / bin_size

# Compute tuning curves from predicted rate using pynapple
predicted_tuning = nap.compute_tuning_curves(
    predicted_rate, feature, bins=50,
    epochs=feature.time_support,
    feature_names=["position"]
)

# Compare with data tuning curves
data_tuning = nap.compute_tuning_curves(
    spikes, feature, bins=50,
    epochs=feature.time_support,
    feature_names=["position"]
)
```
