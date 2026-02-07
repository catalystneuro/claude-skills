---
name: using-nemos
description: >
  Use this skill when writing code that uses the NeMoS (Neural Models and Statistics) Python package
  for fitting Generalized Linear Models (GLMs) to neuroscience data. Covers basis functions,
  single-neuron and population GLMs, observation models (Poisson, Gaussian, Gamma), regularization,
  cross-validation with scikit-learn, and encoding/decoding analyses. Use when the user mentions
  NeMoS, nmo, GLM fitting for neural data, basis functions for neural modeling, or population GLMs.
---

<objective>
Help users write correct, idiomatic NeMoS code for fitting GLMs to neural data. NeMoS is built on
JAX and integrates tightly with pynapple for neuroscience time series data.
</objective>

<core_concepts>

## NeMoS Overview

NeMoS fits Generalized Linear Models to neural data. It is JAX-based, follows the scikit-learn
API (fit/predict/score), and integrates natively with pynapple time series objects.

**Import convention:**
```python
import nemos as nmo
```

## Typical Workflow

```python
import nemos as nmo
import pynapple as nap

# 1. Load and prepare data with pynapple
data = nap.load_file("data.nwb")
spikes = data["units"]
stimulus = data["stimulus"]

# 2. Bin spikes to counts
bin_size = 0.01  # 10 ms
count = spikes[0].count(bin_size)

# 3. Create basis functions and compute features (design matrix)
basis = nmo.basis.RaisedCosineLogConv(n_basis_funcs=8, window_size=80)
X = basis.compute_features(stimulus)

# 4. Fit GLM
model = nmo.glm.GLM(solver_name="LBFGS")
model.fit(X, count)

# 5. Predict and evaluate
predicted_rate = model.predict(X)
score = model.score(X, count)

# 6. Access fitted parameters
print(model.coef_)       # coefficients
print(model.intercept_)  # intercept
```

## Key Design Decisions

**Eval vs Conv basis:** Use `Eval` (e.g., `BSplineEval`) for static nonlinear relationships
(position, speed). Use `Conv` (e.g., `RaisedCosineLogConv`) for temporal/history effects
(spike history, stimulus history). Conv bases convolve with input; Eval bases evaluate at input values.

**Basis composition:** Use `+` for additive (concatenate features), `*` for multiplicative
(outer product / interaction terms).

**Observation models:** Poisson for spike counts (default), Gaussian for continuous signals
(calcium imaging), Gamma/Bernoulli/NegativeBinomial for other distributions.

**GLM vs PopulationGLM:** Use `GLM` for single neurons, `PopulationGLM` for fitting all
neurons simultaneously (e.g., connectivity analysis).

</core_concepts>

<routing>

## Reference Files

Based on what you need, read the appropriate reference file:

| Task | Reference |
|------|-----------|
| Choosing/creating basis functions, Eval vs Conv, composition | `./references/basis-functions.md` |
| Fitting GLMs, observation models, regularizers, solvers | `./references/fitting-glms.md` |
| Population GLMs, connectivity, feature masking | `./references/population-glms.md` |
| Cross-validation, sklearn pipelines, model/feature selection | `./references/sklearn-model-selection.md` |
| Calcium imaging, Gaussian GLMs, continuous data | `./references/continuous-data-glms.md` |

Read the relevant reference file(s) before writing code for the user.

**Related skill:** For pynapple-specific operations (loading NWB data, restrict, count, IntervalSet,
TsGroup, tuning curves, decoding, signal processing), also load the `using-pynapple` skill.
NeMoS workflows almost always involve pynapple for data preparation and analysis.

</routing>

<important_patterns>

## Data Preparation

NeMoS expects:
- **Predictors (X):** 2D array, shape `(n_time_bins, n_features)`
- **Target (y):** 1D array for GLM, 2D for PopulationGLM, shape `(n_time_bins,)` or `(n_time_bins, n_neurons)`
- X and y must have the same number of time bins

When using pynapple objects, align sampling rates:
```python
# Bin spikes
count = spikes.count(bin_size, ep=epoch)
# Match predictor sampling rate to count
predictor = predictor.interpolate(count, ep=count.time_support)
# Or downsample with bin_average
downsampled = high_rate_signal.bin_average(bin_size)
```

## Converting Rates

NeMoS predicts in units of counts/bin. Convert to Hz:
```python
predicted_rate_hz = model.predict(X) / bin_size
```

## Reconstructing Filters from Basis Coefficients

```python
# Get basis kernels
_, basis_kernels = basis.evaluate_on_grid(window_size)
# Multiply with learned coefficients
filter = np.matmul(basis_kernels, model.coef_)
```

## NaN Handling

Conv bases NaN-pad initial time bins where the convolution window extends before the data.
NeMoS handles NaNs during fitting by ignoring those time bins.

</important_patterns>
