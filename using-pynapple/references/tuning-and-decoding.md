# Tuning Curves and Decoding Reference

## compute_tuning_curves()

Compute n-dimensional tuning curves (firing rate or mean response as a function of features).

```python
tc = nap.compute_tuning_curves(
    data,                          # TsGroup (spikes) or TsdFrame (continuous)
    features,                      # Tsd or TsdFrame (behavioral variable)
    bins=50,                       # int or list of ints per dimension
    range=None,                    # [(min, max)] per feature, or None for auto
    epochs=None,                   # IntervalSet (default: feature.time_support)
    fs=None,                       # sampling rate (auto-estimated if None)
    feature_names=["position"],    # list of feature names for labeling
)
```

**Returns:** `xarray.DataArray` with coordinates for unit and each feature dimension.

### 1D Tuning Curves

```python
# Head direction tuning
tc = nap.compute_tuning_curves(
    spikes, angle, bins=61,
    range=(0, 2 * np.pi),
    feature_names=["angle"]
)

# Place fields (position tuning)
place_fields = nap.compute_tuning_curves(
    spikes, position, bins=50,
    epochs=forward_ep,
    feature_names=["position"]
)

# Speed tuning
speed_tc = nap.compute_tuning_curves(
    spikes, speed, bins=30,
    feature_names=["speed"]
)
```

### 2D Tuning Curves

```python
# Combine features into TsdFrame
features = nap.TsdFrame(
    t=position.t,
    d=np.stack([position, theta_phase]).T,
    time_support=position.time_support,
    columns=["position", "phase"]
)

# 2D tuning curve
tc_2d = nap.compute_tuning_curves(
    spikes, features,
    bins=[50, 30],                      # bins per dimension
    feature_names=["position", "phase"]
)
# shape: (n_units, 50, 30)
```

### Tuning Curves for Continuous Data (Calcium Imaging)

When `data` is a TsdFrame (not TsGroup), computes **mean response** per bin:

```python
# Mean fluorescence as function of head direction
tc = nap.compute_tuning_curves(
    transients,        # TsdFrame of fluorescence
    angle,             # Tsd of head direction
    bins=61,
    range=(0, 2 * np.pi),
    feature_names=["angle"]
)
```

### Working with Tuning Curve Results

```python
# xarray.DataArray operations
tc.shape                          # (n_units, n_bins)
tc.coords                         # unit and feature coordinates

# Select specific neurons
tc.sel(unit=82)                   # single neuron
tc.sel(unit=[82, 92, 220])        # multiple neurons

# Get preferred feature value
pref_ang = tc.idxmax(dim="angle")  # preferred angle per neuron

# Access attributes
tc.attrs["occupancy"]             # time spent in each bin
tc.attrs["bin_edges"]             # bin edge arrays

# Plot
tc.sel(unit=82).plot()            # xarray built-in plotting
tc.sel(unit=[82, 92]).plot(col="unit")  # faceted plot

# Normalize
tc_norm = tc / tc.max(axis=1)     # normalize each neuron to peak
```

## decode_bayes() - Bayesian Decoding

Decode features from spike trains using Bayesian inference with Poisson likelihood.
Best for **spike count data**.

```python
decoded_value, decoded_prob = nap.decode_bayes(
    tuning_curves,                  # xarray from compute_tuning_curves
    data,                           # TsGroup or TsdFrame (spike counts)
    epochs,                         # IntervalSet to decode within
    bin_size=0.04,                  # time bin size (seconds)
    sliding_window_size=None,       # int, number of bins for sliding window
)
```

**Returns:**
- `decoded_value`: Tsd of decoded feature values
- `decoded_prob`: TsdFrame of posterior probabilities (one column per bin)

### Basic Decoding

```python
# Decode position from spikes
decoded_pos, prob = nap.decode_bayes(
    place_fields, spikes, forward_ep,
    bin_size=0.04  # 40ms bins
)
```

### Sliding Window for Smoother Decoding

```python
# Sliding window: sum 5 adjacent bins (200ms window, 40ms shift)
decoded_pos, prob = nap.decode_bayes(
    place_fields, spikes, forward_ep,
    bin_size=0.04,
    sliding_window_size=5
)
```

### High-Resolution Decoding (Theta Sequences)

```python
# Fine temporal resolution with sliding window
decoded_pos, prob = nap.decode_bayes(
    place_fields, spikes, run_epoch,
    bin_size=0.01,           # 10ms bins
    sliding_window_size=5    # 50ms effective window
)
```

### Cross-Validated Decoding

```python
from scipy.ndimage import gaussian_filter1d

# Hold out test trial
test_ep = forward_ep[9]
train_ep = forward_ep.set_diff(test_ep)

# Compute tuning curves on training data only
tc_train = nap.compute_tuning_curves(
    spikes, position.restrict(train_ep),
    bins=50, feature_names=["position"]
)
# Smooth tuning curves
tc_train.data = gaussian_filter1d(tc_train.data, 1, axis=-1)

# Decode test trial
decoded, prob = nap.decode_bayes(tc_train, spikes, test_ep, bin_size=0.04)
```

## decode_template() - Template Matching Decoding

Decode features using distance metrics. Works with **any data modality** (spikes or continuous).

```python
decoded_value, distance = nap.decode_template(
    tuning_curves,                  # xarray from compute_tuning_curves
    data,                           # TsGroup or TsdFrame
    bin_size=0.1,                   # time bin size
    metric="correlation",           # distance metric
    epochs=data.time_support,       # IntervalSet
)
```

**Metrics:** `"correlation"`, `"euclidean"`, `"cosine"`, `"manhattan"`, `"jensenshannon"`

### Decoding Calcium Imaging Data

```python
# Template decoding for continuous signals
decoded_angle, dist = nap.decode_template(
    tuning_curves=tc,
    data=transients,
    bin_size=0.1,
    metric="correlation",
    epochs=transients.time_support
)
```

## Visualization Patterns

### Tuning Curves

```python
# Single neuron polar plot (angular tuning)
fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
ax.plot(tc.angle, tc.sel(unit=0).values)

# Multiple neurons
fig, axes = plt.subplots(1, 3)
for i, neuron in enumerate([82, 92, 220]):
    tc.sel(unit=neuron).plot(ax=axes[i])
```

### Decoded Position with Probability

```python
fig, ax = plt.subplots()
# Probability heatmap
ax.pcolormesh(
    decoded_pos.index, place_fields.position,
    np.transpose(prob)
)
# Overlay decoded and true position
ax.plot(decoded_pos, "--r", label="decoded")
ax.plot(position.restrict(epoch), "r", label="true")
ax.legend()
ax.set_xlabel("Time (s)")
ax.set_ylabel("Position (cm)")
```

### 2D Tuning Curves

```python
# Normalized 2D tuning
tc_norm = tc_2d / tc_2d.max(axis=(1, 2))
tc_norm.sel(unit=82).plot(x="position", y="phase")
```
