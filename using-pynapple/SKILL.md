---
name: using-pynapple
description: >
  Use this skill when writing code that uses the pynapple Python package for neurophysiology
  data analysis. Covers core data structures (Ts, Tsd, TsdFrame, TsdTensor, TsGroup, IntervalSet),
  time series manipulation (restrict, count, smooth, interpolate, bin_average, derivative),
  metadata filtering, tuning curves, Bayesian and template decoding, signal processing
  (filtering, wavelets), correlograms, and perievent analysis. Use when the user mentions
  pynapple, nap, spike time analysis, time series with IntervalSet, or neuroscience data wrangling.
---

<objective>
Help users write correct, idiomatic pynapple code for neurophysiology data analysis. Pynapple
provides time-aware data containers and standard neuroscience analysis functions.
</objective>

<core_concepts>

## Pynapple Overview

Pynapple is a lightweight Python library for neurophysiological data analysis. It provides
time-aware containers that track valid time intervals (`time_support`) and standard analysis
functions for tuning curves, decoding, signal processing, and more.

**Import convention:**
```python
import pynapple as nap
import numpy as np
```

**Suppress common warnings:**
```python
nap.nap_config.suppress_conversion_warnings = True
```

## Core Data Types

| Type | Purpose | Data Shape |
|------|---------|------------|
| `Ts` | Timestamps only (spike times) | No data |
| `Tsd` | 1D time series (LFP, position) | `(n_times,)` |
| `TsdFrame` | 2D time series (multi-channel, calcium) | `(n_times, n_columns)` |
| `TsdTensor` | 3D+ time series (video frames) | `(n_times, ...)` |
| `TsGroup` | Collection of Ts/Tsd (spike trains of multiple neurons) | dict-like |
| `IntervalSet` | Time intervals (epochs, trials) | `(n_intervals, 2)` |

## Typical Workflow

```python
import pynapple as nap
import numpy as np

# 1. Load data from NWB file
data = nap.load_file("session.nwb")
spikes = data["units"]         # TsGroup
position = data["position"]   # Tsd
epochs = data["epochs"]        # IntervalSet

# 2. Restrict to epoch of interest
wake_ep = epochs[epochs.tags == "wake"]
spikes = spikes.restrict(wake_ep)
position = position.restrict(wake_ep)

# 3. Filter neurons by metadata
spikes = spikes.getby_category("cell_type")["pE"]  # excitatory only
spikes = spikes.getby_threshold("rate", 0.5)        # rate > 0.5 Hz

# 4. Bin spikes to counts
bin_size = 0.01  # 10 ms
count = spikes.count(bin_size)

# 5. Compute tuning curves
tc = nap.compute_tuning_curves(
    spikes, position, bins=50,
    feature_names=["position"]
)

# 6. Decode
decoded, prob = nap.decode_bayes(
    tc, spikes, epochs, bin_size=0.04
)
```

## Key Principles

1. **time_support**: Every object tracks its valid time range as an IntervalSet.
   Operations like `restrict()` update this automatically.

2. **Immutability**: Methods return new objects rather than modifying in place.

3. **NumPy compatibility**: Pynapple objects work with numpy functions directly:
   `np.mean(tsd)`, `np.abs(tsd)`, `tsd + 1`, etc.

4. **Pynapple preserves time**: When you pass pynapple objects to functions,
   outputs maintain timestamps and time_support.

5. **Units in seconds**: All times are in seconds internally. Use `time_units`
   parameter for input in 'ms' or 'us'.

</core_concepts>

<routing>

## Reference Files

Based on what you need, read the appropriate reference file:

| Task | Reference |
|------|-----------|
| Creating Ts, Tsd, TsdFrame, TsGroup, IntervalSet | `./references/data-structures.md` |
| restrict, count, smooth, interpolate, bin_average, derivative, value_from, threshold | `./references/data-manipulation.md` |
| Metadata: set_info, getby_threshold, getby_category, groupby | `./references/metadata-and-filtering.md` |
| Tuning curves, Bayesian decoding, template decoding | `./references/tuning-and-decoding.md` |
| Filtering, wavelets, FFT, correlograms, perievent analysis | `./references/signal-processing.md` |

Read the relevant reference file(s) before writing code for the user.

**Related skill:** For fitting GLMs to neural data (basis functions, regularization, PopulationGLM,
cross-validation with sklearn), also load the `using-nemos` skill. NeMoS uses pynapple objects
as inputs and outputs throughout its workflow.

</routing>

<important_patterns>

## Loading NWB Data

```python
data = nap.load_file("path/to/file.nwb")
print(data)  # shows available keys and types

spikes = data["units"]              # TsGroup of spike trains
lfp = data["eeg"][:, 0]            # Tsd (single channel from TsdFrame)
position = data["position"]         # Tsd
epochs = data["epochs"]             # IntervalSet
transients = data["RoiResponseSeries"]  # TsdFrame (calcium imaging)
```

## Aligning Sampling Rates

When combining data at different sampling rates:
```python
# Upsample: interpolate low-rate to high-rate timestamps
position_upsampled = position.interpolate(count, ep=count.time_support)

# Downsample: average high-rate into bins
theta_downsampled = theta_phase.bin_average(bin_size)
```

## IntervalSet Operations

```python
# Set operations
intersection = ep1.intersect(ep2)
combined = ep1.union(ep2)
difference = ep1.set_diff(ep2)

# Filtering
short_removed = ep.drop_short_intervals(0.5)  # remove < 0.5s
merged = ep.merge_close_intervals(0.1)         # merge gaps < 0.1s

# Indexing
first_epoch = ep[0]           # single IntervalSet row
subset = ep[[0, 2, 5]]        # specific rows
```

## Computing Speed from Position

```python
position = position.restrict(forward_ep)
speed = np.abs(position.derivative())
```

## Plotting Pynapple Objects

Pynapple objects can be plotted directly with matplotlib:
```python
import matplotlib.pyplot as plt
plt.plot(tsd)                    # x-axis is time automatically
plt.plot(spikes.to_tsd([-1]), "|")  # raster plot
```

</important_patterns>
