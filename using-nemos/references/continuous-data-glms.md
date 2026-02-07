# Continuous Data (Calcium Imaging) GLMs Reference

## Overview

For continuous neural signals like calcium imaging fluorescence traces, use the Gaussian
observation model instead of Poisson. The rest of the NeMoS workflow is the same.

## Gaussian PopulationGLM for Calcium Data

```python
import nemos as nmo
import pynapple as nap
import numpy as np

# Load calcium imaging data
data = nap.load_file("calcium_data.nwb")
transients = data["RoiResponseSeries"]  # TsdFrame: (n_time_bins, n_neurons)
angle = data["ry"]                       # behavioral feature

# Select tuned neurons (optional preprocessing)
tuning_curves = nap.compute_tuning_curves(
    data=transients, features=angle, bins=61,
    range=(0, 2 * np.pi), feature_names=["angle"]
)
```

## Key Differences from Spike Data

1. **Observation model**: Use `"Gaussian"` instead of `"Poisson"`
2. **Data format**: Input is continuous `TsdFrame`, not spike counts
3. **Basis window**: Use larger windows for slow calcium dynamics
4. **No rate conversion**: Predictions are in signal units, not counts/bin
5. **JAX precision**: Enable float64 for better LBFGS convergence:
   ```python
   import jax
   jax.config.update("jax_enable_x64", True)
   ```

## Fitting a Calcium Population GLM

```python
# Basis for calcium dynamics (larger window for slow signals)
calcium_window_sec = 0.5
calcium_window_bins = int(calcium_window_sec * transients.rate)
basis = nmo.basis.RaisedCosineLogConv(
    n_basis_funcs=20,
    window_size=calcium_window_bins
)

# Convolve all neurons
X = basis.compute_features(transients)
# X shape: (n_time_bins, n_neurons * n_basis_funcs)

# Train/test split
duration = X.time_support.tot_length("s")
start = X.time_support["start"]
end = X.time_support["end"]
train_ep = nap.IntervalSet(start, start + duration / 2)
test_ep = nap.IntervalSet(start + duration / 2, end)

# Fit Gaussian PopulationGLM
model = nmo.glm.PopulationGLM(
    observation_model="Gaussian",
    regularizer="Ridge",
    solver_name="LBFGS",
    regularizer_strength=1.0,
    solver_kwargs={"maxiter": 5000}
).fit(X.restrict(train_ep), transients.restrict(train_ep))
```

## Preventing Self-Coupling with Feature Mask

Self-coupling dominates in calcium data due to slow dynamics. Remove it with a mask:

```python
n_neurons = transients.shape[1]
n_basis = basis.n_basis_funcs

# Mask: ones everywhere, zeros on diagonal
mask = np.ones((n_neurons, n_neurons)) - np.eye(n_neurons)
# Repeat for each basis function
feature_mask = np.repeat(mask, n_basis, axis=0)
# feature_mask shape: (n_neurons * n_basis_funcs, n_neurons)

model = nmo.glm.PopulationGLM(
    observation_model="Gaussian",
    regularizer="Ridge",
    solver_name="LBFGS",
    regularizer_strength=1.0,
    feature_mask=feature_mask,
    solver_kwargs={"maxiter": 5000}
).fit(X.restrict(train_ep), transients.restrict(train_ep))
```

## Predicting and Visualizing

```python
# Predict on test set
predicted = model.predict(X.restrict(test_ep))

# Visualize single neuron
import matplotlib.pyplot as plt
ep_plot = nap.IntervalSet(test_ep.start[0], test_ep.start[0] + 100)

plt.figure()
plt.plot(transients.restrict(ep_plot)[:, 0], label="Actual")
plt.plot(predicted.restrict(ep_plot)[:, 0], '--', label="Predicted")
plt.xlabel("Time (s)")
plt.ylabel("Fluorescence")
plt.legend()
```

## Extracting Coupling Filters from Calcium GLM

Same pattern as spike data:

```python
# Split coefficients
weights_dict = basis.split_by_feature(model.coef_, axis=0)
weights = weights_dict["RaisedCosineLogConv"]
# weights shape: (n_sender, n_basis_funcs, n_receiver)

# Reconstruct filters
_, basis_kernels = basis.evaluate_on_grid(calcium_window_bins)
coupling_filters = np.einsum("jki,tk->ijt", weights, basis_kernels)
# coupling_filters shape: (n_sender, n_receiver, window_size)
```

## Tuning Curves for Continuous Data

For calcium imaging, `compute_tuning_curves` computes the **mean response** per bin
(not firing rate):

```python
tuning_curves = nap.compute_tuning_curves(
    data=transients,          # TsdFrame of fluorescence
    features=angle,           # behavioral feature
    bins=61,
    range=(0, 2 * np.pi),
    feature_names=["angle"]
)
# Returns mean fluorescence as a function of angle
```

## Template Decoding for Continuous Data

For continuous signals, use `nap.decode_template` (not `nap.decode_bayes` which is for spikes):

```python
decoded_angle, distance = nap.decode_template(
    tuning_curves=tuning_curves,
    data=transients,
    bin_size=0.1,
    metric="correlation",   # "euclidean", "cosine", "jensenshannon", "manhattan"
    epochs=transients.time_support
)

# Visualize
plt.figure()
plt.plot(angle.restrict(epoch), label="True")
plt.scatter(decoded_angle.times(), decoded_angle.values, label="Decoded", c="orange")
plt.legend()
```

## Downsampling Calcium Data

If data is too high-resolution, downsample with `bin_average`:

```python
downsampled = transients.bin_average(bin_size=0.05)  # 50 ms bins
```
