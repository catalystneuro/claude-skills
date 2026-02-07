# Metadata and Filtering Reference

## Adding Metadata

Metadata can be attached to TsGroup, TsdFrame, and IntervalSet objects.

### TsGroup Metadata (per-neuron)

```python
# At initialization
tsgroup = nap.TsGroup(
    {0: ts0, 1: ts1, 2: ts2},
    metadata={"location": ["adn", "adn", "v1"], "cell_type": ["pE", "pI", "pE"]}
)

# After initialization
tsgroup.set_info(location=["adn", "adn", "v1"])
tsgroup.set_info(pref_ang=preferred_angles)
tsgroup["custom_metric"] = [0.5, 0.8, 0.3]

# From computed values
pref_ang = tuning_curves.idxmax(dim="angle")
tsgroup.set_info(pref_ang=pref_ang)
```

### IntervalSet Metadata (per-epoch)

```python
# At initialization
epochs = nap.IntervalSet(
    start=[0, 100, 200],
    end=[50, 150, 250],
    metadata={"tags": ["wake", "sleep", "wake"], "trial": [1, 2, 3]}
)

# After initialization
epochs.set_info(direction=["left", "right", "left"])
```

### TsdFrame Metadata (per-column)

```python
# At initialization
tsdframe = nap.TsdFrame(
    t=times, d=data,
    columns=["n0", "n1", "n2"],
    metadata={"region": ["M1", "V1", "M1"]}
)

# After initialization
tsdframe.set_info(color=["red", "blue", "green"])
```

## Accessing Metadata

```python
# As attribute
tsgroup.location          # array of location values
tsgroup.rate              # built-in: firing rates

# As dictionary key
tsgroup["location"]       # same result

# Get specific metadata
tsgroup.get_info("location")           # single column
tsgroup.get_info(["location", "rate"]) # multiple columns as DataFrame

# Full metadata table
print(tsgroup)  # prints table with all metadata columns
```

## Filtering by Metadata

### getby_threshold() - Filter by Numeric Threshold

Filter TsGroup members by a numeric metadata value.

```python
# Keep neurons with rate > 0.5 Hz
fast_neurons = tsgroup.getby_threshold("rate", 0.5)      # default op='>'

# Keep neurons with rate >= 1.0 Hz
active = tsgroup.getby_threshold("rate", 1.0, op=">=")

# Keep neurons with rate < 10 Hz (exclude interneurons)
pyramidal = tsgroup.getby_threshold("rate", 10.0, op="<")

# Chain filters
good_neurons = tsgroup.getby_threshold("rate", 1.0).getby_threshold("rate", 10.0, op="<")
```

### getby_category() - Group by Categorical Metadata

Group TsGroup members by a categorical metadata value.

```python
# Group by cell type
groups = tsgroup.getby_category("cell_type")
# Returns dict: {"pE": TsGroup(...), "pI": TsGroup(...)}

excitatory = groups["pE"]
inhibitory = groups["pI"]

# Group by brain region
regions = tsgroup.getby_category("location")
adn_neurons = regions["adn"]
```

### Boolean Indexing on IntervalSet

```python
# Filter epochs by metadata
wake_ep = epochs[epochs.tags == "wake"]
sleep_ep = epochs[epochs.tags == "sleep"]

# Filter by trial number
first_trials = epochs[epochs.trial <= 5]
```

### Boolean Indexing on TsGroup

```python
# Filter by metadata condition
adn_neurons = tsgroup[(tsgroup.location == "adn") & (tsgroup.rate > 2.0)]
```

### Boolean Indexing on TsdFrame

```python
# Filter columns by metadata
m1_channels = tsdframe[:, tsdframe.region == "M1"]
```

## Sorting by Metadata

```python
# Sort neurons by preferred angle
sort_idx = np.argsort(tsgroup.pref_ang.values)
sorted_count = count[:, sort_idx]

# Sort for visualization
sorted_tuning = tuning_curves[sort_idx]
```

## groupby() and groupby_apply()

```python
# Group by metadata
groups = tsgroup.groupby("location")
# Returns dict: {"adn": [0, 1, 3], "v1": [2, 4]}

# Apply function to each group
results = tsgroup.groupby_apply("location", lambda x: x.count(0.01))
```

## Common Metadata Patterns

### Neuron Selection Pipeline
```python
# Load spikes
spikes = data["units"]

# Filter by brain region
spikes = spikes[(spikes.location == "adn")]

# Filter by firing rate
spikes = spikes.getby_threshold("rate", 2.0)

# Add tuning info
tuning_curves = nap.compute_tuning_curves(
    spikes, angle, bins=61,
    range=(0, 2 * np.pi),
    feature_names=["angle"]
)
pref_ang = tuning_curves.idxmax(dim="angle")
spikes.set_info(pref_ang=pref_ang)

# Sort by preferred angle
sort_order = np.argsort(pref_ang.values)
```

### Rayleigh Test for Tuning Significance
```python
# Select significantly tuned neurons
C = np.sum(tc.values * np.cos(tc.angle.values), axis=1) / np.sum(tc.values, axis=1)
S = np.sum(tc.values * np.sin(tc.angle.values), axis=1) / np.sum(tc.values, axis=1)
R = np.sqrt(C**2 + S**2)
Z = tc.shape[1] * R**2
p_value = np.exp(-Z)

tuned_idx = np.where(p_value < 0.01)[0]
transients = transients[:, tuned_idx]
```
