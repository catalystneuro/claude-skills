# Data Manipulation Reference

## restrict() - Restrict to Time Intervals

Restricts data to time points within an IntervalSet. Updates `time_support`.

```python
# Works on all types: Ts, Tsd, TsdFrame, TsdTensor, TsGroup
restricted = data.restrict(epoch)

# Examples
spikes_wake = spikes.restrict(wake_ep)
lfp_trial = lfp.restrict(trial_ep)
position_run = position.restrict(forward_ep)

# Chain restrictions
spikes_adn_wake = spikes[spikes.location == "adn"].restrict(wake_ep)
```

## count() - Bin and Count Events

Counts events in time bins. Works on Ts, Tsd, TsGroup.

```python
# Count in fixed-size bins
count = spikes[0].count(bin_size=0.01)         # 10ms bins, returns Tsd
count = tsgroup.count(bin_size=0.01)            # all neurons, returns TsdFrame

# Count within specific epochs
count = tsgroup.count(bin_size=0.01, ep=wake_ep)

# Count per epoch (no bin_size)
count = tsgroup.count(ep=trial_epochs)          # one count per epoch

# Output shape
# Tsd: (n_bins,)
# TsdFrame: (n_bins, n_neurons)
```

## smooth() - Gaussian Smoothing

Convolves with a Gaussian kernel. Works on Tsd, TsdFrame, TsdTensor.

```python
# Smooth with 50ms std Gaussian
smoothed = tsd.smooth(std=0.05, size_factor=20)
# std: standard deviation in seconds
# size_factor: kernel width in units of std (total width = std * size_factor)

# Convert spike counts to smoothed firing rate
count = spikes[0].count(bin_size=0.001)  # 1ms bins
firing_rate = count.smooth(std=0.05, size_factor=20)
firing_rate = firing_rate / 0.001  # convert to Hz
```

## interpolate() - Linear Interpolation

Interpolate data to match timestamps of another object. Use for upsampling.

```python
# Upsample position to match spike count timestamps
position_upsampled = position.interpolate(count, ep=count.time_support)

# Upsample speed similarly
speed_upsampled = speed.interpolate(count, ep=count.time_support)

# With boundary values
interpolated = tsd.interpolate(target_ts, left=0.0, right=0.0)
```

## bin_average() - Downsample by Averaging

Average data within fixed-size bins. Use for downsampling.

```python
# Downsample high-rate signal to 10ms bins
downsampled = theta_phase.bin_average(bin_size=0.01)

# Downsample calcium transients
transients_low = transients.bin_average(bin_size=0.05)  # 50ms bins
```

## derivative() - Numerical Derivative

Compute numerical derivative (velocity from position, etc.).

```python
# Compute velocity from position
velocity = position.derivative()

# Compute speed (absolute velocity)
speed = np.abs(position.derivative())

# With epoch restriction
velocity = position.derivative(ep=forward_ep)
```

## value_from() - Assign Values at Spike Times

Find the value of a continuous signal at each event timestamp.

```python
# What was the theta phase at each spike?
spike_phase = spikes[0].value_from(theta_phase)

# What was the position at each spike?
spike_position = spikes[0].value_from(position)

# What was the LFP amplitude at each spike?
spike_lfp = spikes[0].value_from(theta_band)

# For TsGroup
spike_phases = tsgroup.value_from(theta_phase)  # returns TsGroup with values

# Modes
closest = ts.value_from(tsd, mode='closest')  # default
before = ts.value_from(tsd, mode='before')     # value just before
after = ts.value_from(tsd, mode='after')       # value just after
```

## get() - Slice by Time

Get data in a time range without changing time_support.

```python
# Get data between 50 and 100 seconds
segment = tsd.get(50, 100)

# Get closest value to a specific time
point = tsd.get(50.1)

# Quick visualization of first 100 seconds
plt.plot(transients[:, 0:2].get(0, 100))
```

## threshold() - Find Epochs Above/Below Value

Returns a Tsd restricted to times where values meet a threshold condition.

```python
# Get epochs where signal is above 0
above = tsd.threshold(0.0, method="above")

# Get the time_support (IntervalSet) of above-threshold periods
above_epochs = above.time_support

# Visualize
plt.plot(tsd)
for ep in above_epochs:
    plt.axvspan(ep.start[0], ep.end[0], alpha=0.3)
```

## convolve() - Discrete Convolution

Convolve with a custom kernel.

```python
# Moving sum (sliding window)
kernel = np.ones(5)  # 5-bin uniform kernel
smoothed = tsd.convolve(kernel)

# Custom kernel
smoothed = tsd.convolve(gaussian_kernel, trim='both')
```

## dropna() - Remove NaN Values

Remove time points with NaN values.

```python
# Remove NaN rows and update time_support
clean = tsd.dropna()

# Keep original time_support
clean = tsd.dropna(update_time_support=False)
```

## decimate() - Downsample with Anti-Aliasing

Downsample with anti-aliasing filter.

```python
# Downsample by factor of 10
downsampled = tsd.decimate(10)

# With specific filter
downsampled = tsd.decimate(10, order=8, filter_type='iir')
```

## to_trial_tensor() - Reshape into Trial Tensor

Reshape continuous data into (n_trials, n_times_per_trial) array.

```python
# Create trial-aligned tensor
tensor = tsd.to_trial_tensor(trial_epochs, align='start')
# shape: (n_trials, max_trial_length)

# For TsdFrame
tensor = tsdframe.to_trial_tensor(trial_epochs)
# shape: (n_columns, n_trials, max_trial_length)
```

## find_support() - Auto-Detect Time Support

Find IntervalSet that covers data with specified gap resolution.

```python
# Find epochs with gaps > 1 second
support = tsd.find_support(min_gap=1.0)
```

## Common Patterns

### Align Two Signals to Same Sampling Rate
```python
# Both to 100 Hz (bin_size = 0.01)
bin_size = 0.01
count = spikes.count(bin_size, ep=epoch)
position_aligned = position.interpolate(count, ep=count.time_support)
speed_aligned = speed.interpolate(count, ep=count.time_support)
```

### Convert Counts to Firing Rate
```python
bin_size = 0.001
count = spikes[0].count(bin_size)
# Smooth then convert
firing_rate = count.smooth(std=0.05, size_factor=20) / bin_size
```

### Phase Wrapping
```python
import scipy as sp
# Bandpass filter for theta
theta_band = nap.apply_bandpass_filter(lfp, (6, 12), fs=1250)
# Hilbert transform for phase
phase = np.angle(sp.signal.hilbert(theta_band.values))
phase %= 2 * np.pi  # wrap to [0, 2pi]
theta_phase = nap.Tsd(t=theta_band.t, d=phase, time_support=theta_band.time_support)
```
