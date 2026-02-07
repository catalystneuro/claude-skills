# Population GLMs Reference

## PopulationGLM

Fits GLMs to multiple neurons simultaneously. The population log-likelihood is the sum of
individual neuron log-likelihoods, so fitting the population is equivalent to fitting each
neuron independently (but more convenient).

```python
model = nmo.glm.PopulationGLM(
    observation_model="Poisson",
    regularizer="Ridge",
    regularizer_strength=0.1,
    solver_name="LBFGS",
)
```

## Functional Connectivity Analysis

The main use case for PopulationGLM is estimating pairwise interactions between neurons.
The activity of all neurons predicts each neuron's firing rate.

### Step-by-step workflow

```python
import nemos as nmo
import pynapple as nap
import numpy as np

# 1. Bin all spikes
bin_size = 0.01
count = spikes.count(bin_size, ep=epoch)
# count shape: (n_time_bins, n_neurons)

# 2. Create Conv basis for spike history
basis = nmo.basis.RaisedCosineLogConv(
    n_basis_funcs=8,
    window_size=int(0.8 / bin_size)  # 0.8 sec history window
)

# 3. Set input shape for multi-neuron input
basis.set_input_shape(count)

# 4. Convolve all neurons
X = basis.compute_features(count)
# X shape: (n_time_bins, n_neurons * n_basis_funcs)

# 5. Fit PopulationGLM
model = nmo.glm.PopulationGLM(
    regularizer="Ridge",
    solver_name="LBFGS",
    regularizer_strength=0.1
).fit(X, count)

# model.coef_ shape: (n_neurons * n_basis_funcs, n_neurons)
```

### Extracting Coupling Filters

```python
# 6. Split coefficients by feature
weights_dict = basis.split_by_feature(model.coef_, axis=0)
weights = weights_dict["RaisedCosineLogConv"]
# weights shape: (n_sender, n_basis_funcs, n_receiver)

# 7. Reconstruct coupling filters
window_size = int(0.8 / bin_size)
_, basis_kernels = basis.evaluate_on_grid(window_size)
# basis_kernels shape: (window_size, n_basis_funcs)

# Use einsum: (sender, basis, receiver) x (time, basis) -> (sender, receiver, time)
coupling_filters = np.einsum("jki,tk->ijt", weights, basis_kernels)
# coupling_filters shape: (n_sender, n_receiver, window_size)
```

### Visualizing Coupling Filters

```python
import matplotlib.pyplot as plt

n_neurons = count.shape[1]
fig, axes = plt.subplots(n_neurons, n_neurons, figsize=(12, 12))
time = np.arange(window_size) / count.rate

for i in range(n_neurons):
    for j in range(n_neurons):
        axes[i, j].plot(time, coupling_filters[i, j])
        axes[i, j].axhline(0, color='k', lw=0.5)
        if i == 0:
            axes[i, j].set_title(f"From {j}")
        if j == 0:
            axes[i, j].set_ylabel(f"To {i}")

plt.tight_layout()
```

## Feature Masking

Use `feature_mask` to prevent certain connections (e.g., self-coupling).

```python
n_neurons = count.shape[1]
n_basis = basis.n_basis_funcs

# Create mask: ones everywhere, zeros on diagonal (no self-coupling)
mask = np.ones((n_neurons, n_neurons))
mask -= np.eye(n_neurons)

# Repeat for each basis function
# mask shape must be: (n_neurons * n_basis_funcs, n_neurons)
feature_mask = np.repeat(mask, n_basis, axis=0)

model = nmo.glm.PopulationGLM(
    observation_model="Gaussian",
    regularizer="Ridge",
    solver_name="LBFGS",
    regularizer_strength=1.0,
    feature_mask=feature_mask,
).fit(X, transients)
```

## Single-Neuron Spike History Model

Before fitting population models, it's useful to fit single-neuron history models:

```python
# Select one neuron
neuron_count = count[:, 0]

# Create history features
basis = nmo.basis.RaisedCosineLogConv(n_basis_funcs=8, window_size=80)
X = basis.compute_features(neuron_count)

# Fit single neuron
model = nmo.glm.GLM(solver_name="LBFGS").fit(X, neuron_count)

# Compare raw history vs basis history to check overfitting
history_basis = nmo.basis.HistoryConv(window_size=80)
X_raw = history_basis.compute_features(neuron_count)
model_raw = nmo.glm.GLM(solver_name="LBFGS").fit(X_raw, neuron_count)

# Basis model should be more consistent across train/test splits
```

## Predicting Population Activity

```python
predicted_rate = model.predict(X)
# predicted_rate shape: (n_time_bins, n_neurons)

# Convert to Hz
predicted_rate_hz = predicted_rate * count.rate

# Compute predicted tuning curves
predicted_tuning = nap.compute_tuning_curves(
    predicted_rate_hz, angle, bins=61,
    epochs=angle.time_support,
    range=(0, 2 * np.pi),
    feature_names=["angle"]
)
```

## Multi-Feature Population Model

Combine spike history with external features:

```python
# Spike history basis
history_basis = nmo.basis.RaisedCosineLogConv(
    n_basis_funcs=8, window_size=80, label="history"
)
history_basis.set_input_shape(count)
X_history = history_basis.compute_features(count)

# Position basis
position_basis = nmo.basis.BSplineEval(n_basis_funcs=12, label="position")
X_position = position_basis.compute_features(position)

# Combine
X = np.column_stack([X_history, X_position])

model = nmo.glm.PopulationGLM(
    regularizer="Ridge",
    solver_name="LBFGS",
    regularizer_strength=0.1
).fit(X, count)
```

## Classifier GLMs

For multi-class classification tasks:

```python
model = nmo.glm.ClassifierGLM(solver_name="LBFGS")
model = nmo.glm.ClassifierPopulationGLM(solver_name="LBFGS")
```
