# Basis Functions Reference

## Overview

Basis functions transform raw inputs into feature matrices for GLMs. They serve two purposes:
1. **Dimensionality reduction** - represent temporal effects with fewer parameters (Conv bases)
2. **Nonlinear mapping** - capture nonlinear relationships between inputs and firing rate (Eval bases)

## Eval vs Conv

**Eval bases** (`*Eval`): Evaluate basis functions at input values. Use for static, instantaneous
relationships (e.g., position -> firing rate, speed -> firing rate).

**Conv bases** (`*Conv`): Convolve basis functions with input time series. Use for temporal/history
effects (e.g., how past spikes affect current firing rate, stimulus history effects).

## Available Basis Types

### Spline Bases
```python
# B-spline - smooth, flexible, general purpose
nmo.basis.BSplineEval(n_basis_funcs=10, order=4)
nmo.basis.BSplineConv(n_basis_funcs=10, window_size=100, order=4)

# M-spline - non-negative, good for rate-like quantities
nmo.basis.MSplineEval(n_basis_funcs=10, label="position")
nmo.basis.MSplineConv(n_basis_funcs=10, window_size=100)

# Cyclic B-spline - for circular/periodic variables (angles, phase)
nmo.basis.CyclicBSplineEval(n_basis_funcs=10, label="phase")
nmo.basis.CyclicBSplineConv(n_basis_funcs=10, window_size=100)
```

### Raised Cosine Bases
```python
# Log-stretched raised cosine - good for spike/stimulus history
# Provides finer resolution for recent history, coarser for distant
nmo.basis.RaisedCosineLogEval(n_basis_funcs=8)
nmo.basis.RaisedCosineLogConv(n_basis_funcs=8, window_size=80)

# Linear raised cosine
nmo.basis.RaisedCosineLinearEval(n_basis_funcs=8)
nmo.basis.RaisedCosineLinearConv(n_basis_funcs=8, window_size=80)
```

### Other Bases
```python
# History basis - identity convolution (raw spike history, no compression)
nmo.basis.HistoryConv(window_size=80)

# Fourier basis
nmo.basis.FourierEval(n_basis_funcs=20)

# Identity basis - pass-through (no transformation)
nmo.basis.IdentityEval()

# Orthogonal exponential
nmo.basis.OrthExponentialEval(n_basis_funcs=5, decay_rates=[1, 2, 5, 10, 20])
nmo.basis.OrthExponentialConv(n_basis_funcs=5, window_size=100, decay_rates=[1, 2, 5, 10, 20])
```

## Labels

Always provide labels for clarity, especially with composed bases:
```python
position_basis = nmo.basis.BSplineEval(n_basis_funcs=12, label="position")
speed_basis = nmo.basis.BSplineEval(n_basis_funcs=6, label="speed")
```

## Computing Features

```python
# Eval basis: pass values directly
X = basis.compute_features(position)  # shape: (n_samples, n_basis_funcs)

# Conv basis: convolve with time series
X = basis.compute_features(spike_counts)  # shape: (n_samples, n_basis_funcs)
# First window_size-1 time bins will be NaN-padded

# With pynapple objects, output preserves time information
X = basis.compute_features(nap_tsd)  # returns Tsd/TsdFrame
```

## Basis Composition

### Additive (+) - concatenates features
```python
# Two separate predictors, each with its own basis
position_basis = nmo.basis.BSplineEval(n_basis_funcs=12, label="position")
speed_basis = nmo.basis.MSplineEval(n_basis_funcs=6, label="speed")
additive_basis = position_basis + speed_basis

# Compute features: pass inputs in same order as addition
X = additive_basis.compute_features(position, speed)
# X shape: (n_samples, 12 + 6) = (n_samples, 18)
```

### Multiplicative (*) - outer product / interaction terms
```python
# Interaction between position and theta phase
position_basis = nmo.basis.BSplineEval(n_basis_funcs=12, label="position")
phase_basis = nmo.basis.CyclicBSplineEval(n_basis_funcs=10, label="phase")
interaction_basis = position_basis * phase_basis

# X shape: (n_samples, 12 * 10) = (n_samples, 120)
X = interaction_basis.compute_features(position, theta_phase)
```

### Complex compositions
```python
# Position x Phase interaction + Speed (additive)
full_basis = position_basis * phase_basis + speed_basis
X = full_basis.compute_features(position, theta_phase, speed)
# X shape: (n_samples, 12*10 + 6) = (n_samples, 126)
```

## Evaluating and Visualizing Basis Functions

```python
# Evaluate on a regular grid (useful for visualization and filter reconstruction)
n_points = 100
x_grid, basis_values = basis.evaluate_on_grid(n_points)
# x_grid: (n_points,), basis_values: (n_points, n_basis_funcs)

import matplotlib.pyplot as plt
plt.plot(x_grid, basis_values)
plt.xlabel("Input")
plt.ylabel("Basis function value")
```

## Reconstructing Temporal Filters

After fitting a GLM with Conv basis, reconstruct the learned filter:
```python
basis = nmo.basis.RaisedCosineLogConv(n_basis_funcs=8, window_size=80)
X = basis.compute_features(spike_counts)
model = nmo.glm.GLM(solver_name="LBFGS").fit(X, target_counts)

# Reconstruct filter
_, basis_kernels = basis.evaluate_on_grid(window_size)  # (window_size, n_basis_funcs)
learned_filter = np.matmul(basis_kernels, model.coef_)  # (window_size,)

# Plot
time_axis = np.arange(window_size) / sampling_rate
plt.plot(time_axis, learned_filter)
plt.xlabel("Time from event (s)")
plt.ylabel("Weight")
```

## Splitting Features by Component

After fitting with composed bases, separate coefficients by component:
```python
basis = nmo.basis.RaisedCosineLogConv(n_basis_funcs=8, window_size=80)
basis.set_input_shape(population_counts)  # for multi-neuron input
X = basis.compute_features(population_counts)

model = nmo.glm.PopulationGLM(...).fit(X, target_counts)

# Split coefficients: returns dict keyed by basis label
weights_dict = basis.split_by_feature(model.coef_, axis=0)
weights = weights_dict["RaisedCosineLogConv"]
# shape: (n_sender_neurons, n_basis_funcs, n_receiver_neurons)
```

## Multi-Neuron Input Shape

When convolving a basis with multi-neuron counts, set the input shape:
```python
basis = nmo.basis.RaisedCosineLogConv(n_basis_funcs=8, window_size=80)

# Tell basis to expect multi-neuron input
basis.set_input_shape(population_counts)  # pass the actual data

# Now compute features - output has n_neurons * n_basis_funcs columns
X = basis.compute_features(population_counts)
# shape: (n_samples, n_neurons * n_basis_funcs)
```

## Choosing a Basis

| Scenario | Recommended Basis |
|----------|-------------------|
| Spike history (self-connection) | `RaisedCosineLogConv` |
| Stimulus history (current injection) | `RaisedCosineLogConv` |
| Raw spike history (no compression) | `HistoryConv` |
| Position tuning (place fields) | `BSplineEval` or `MSplineEval` |
| Speed tuning | `BSplineEval` or `MSplineEval` |
| Angular/phase tuning (circular) | `CyclicBSplineEval` |
| Calcium imaging history | `RaisedCosineLogConv` (larger window) |
| General smooth nonlinearity | `BSplineEval` |

## Window Size for Conv Bases

The `window_size` parameter is in **bins**, not seconds. Convert:
```python
window_size_sec = 0.8  # seconds
window_size_bins = int(window_size_sec * sampling_rate)
basis = nmo.basis.RaisedCosineLogConv(n_basis_funcs=8, window_size=window_size_bins)
```
