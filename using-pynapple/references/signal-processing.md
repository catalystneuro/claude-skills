# Signal Processing Reference

## Filtering

All filter functions work on Tsd, TsdFrame, and TsdTensor. They handle discontinuous
epochs automatically (filter applied per epoch).

### Bandpass Filter

```python
# Extract theta oscillation (6-12 Hz)
theta_band = nap.apply_bandpass_filter(lfp, cutoff=(6, 12), fs=1250)

# Extract gamma (30-80 Hz)
gamma_band = nap.apply_bandpass_filter(lfp, cutoff=(30, 80), fs=1250)
```

### Lowpass / Highpass / Bandstop

```python
# Lowpass below 100 Hz
filtered = nap.apply_lowpass_filter(signal, cutoff=100, fs=1250)

# Highpass above 1 Hz
filtered = nap.apply_highpass_filter(signal, cutoff=1, fs=1250)

# Notch filter (remove 60 Hz line noise)
filtered = nap.apply_bandstop_filter(signal, cutoff=(59, 61), fs=1250)
```

### Filter Parameters

```python
nap.apply_bandpass_filter(
    sig,                            # Tsd/TsdFrame/TsdTensor
    cutoff,                         # float or tuple of (low, high)
    fs=None,                        # sampling rate (auto from sig.rate if None)
    order=4,                        # filter order
    filter_type='butterworth',      # 'butterworth' or 'windowed-sinc'
    transition_bandwidth=None,      # for windowed-sinc only
)
```

### Analyzing Filter Response

```python
freqs, response = nap.get_filter_frequency_response(
    cutoff=(6, 12),
    filter_type='butterworth',
    fs=1250,
    order=4
)
plt.plot(freqs, response)
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
```

## Wavelet Transform

Morlet wavelet decomposition for time-frequency analysis.

```python
# Define frequency range
freqs = np.geomspace(5, 200, 100)  # 100 log-spaced frequencies, 5-200 Hz

# Compute wavelet transform
cwt = nap.compute_wavelet_transform(lfp, fs=1250, freq=freqs)
# Returns TsdFrame: (n_times, n_freqs), complex-valued

# Extract amplitude
amplitude = np.abs(cwt.values)

# Visualize spectrogram
plt.pcolormesh(cwt.t, freqs, amplitude.T)
plt.yscale('log')
plt.ylabel("Frequency (Hz)")
plt.xlabel("Time (s)")
plt.colorbar(label="Amplitude")
```

### Alternative: Specify Frequency Range

```python
# Auto-generate frequencies
cwt = nap.compute_wavelet_transform(
    lfp,
    fs=1250,
    freq=(0.5, 100),    # (min_freq, max_freq)
    nb_freqs=100         # number of frequencies
)
```

## Spectral Analysis

### FFT

```python
fft_result = nap.compute_fft(signal, fs=1250)
# Returns: pandas Series with frequency index

plt.plot(fft_result.index, np.abs(fft_result.values))
plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
```

### Power Spectral Density

```python
psd = nap.compute_power_spectral_density(signal, fs=1250)

# Average PSD across a group
mean_psd = nap.compute_mean_power_spectral_density(tsgroup, fs=1250)
```

## Phase Extraction (Hilbert Transform)

Extract instantaneous phase from a bandpass-filtered signal using scipy:

```python
import scipy as sp

# 1. Restrict LFP to epochs of interest
lfp_restricted = lfp.restrict(forward_ep)

# 2. Bandpass filter for theta
theta_band = nap.apply_bandpass_filter(lfp_restricted, (6, 12), fs=1250)

# 3. Hilbert transform for instantaneous phase
phase = np.angle(sp.signal.hilbert(theta_band.values))
phase %= 2 * np.pi  # wrap to [0, 2pi]

# 4. Store as Tsd
theta_phase = nap.Tsd(
    t=theta_band.t,
    d=phase,
    time_support=theta_band.time_support
)
```

## Oscillatory Event Detection

Detect oscillatory bursts (e.g., spindles, sharp-wave ripples):

```python
events = nap.detect_oscillatory_events(
    signal,
    fs=1250,
    cutoff=(100, 250),           # frequency band (e.g., ripple band)
    duration=(0.01, 1.0),        # min/max event duration (seconds)
    min_abs_power=None,          # absolute power threshold
    percentile=99                # adaptive threshold percentile
)
# Returns: IntervalSet of detected events
```

## Perievent Analysis

Align data to reference events (e.g., stimulus onsets, spike times).

### Perievent Timestamps

```python
# Align spikes to stimulus onsets
perievent = nap.compute_perievent(
    timestamps=spikes,              # Ts/Tsd/TsGroup
    tref=stimulus_onsets,           # Ts/Tsd (reference events)
    minmax=(-1, 2),                 # (pre_event, post_event) in seconds
)
# For TsGroup input: returns dict of TsGroup (one per neuron)
# For Ts input: returns TsGroup (one per reference event)
```

### Perievent Continuous

```python
# Align LFP to events
perievent = nap.compute_perievent_continuous(
    timeseries=lfp,                 # Tsd/TsdFrame/TsdTensor
    tref=event_times,               # Ts/Tsd
    minmax=(-0.5, 1.0),             # window around events
)
```

### Event-Triggered Average

```python
# Average LFP waveform around events
eta = nap.compute_event_trigger_average(
    timeseries=lfp,                 # Tsd/TsdFrame/TsdTensor
    event=spike_times,              # Ts/Tsd
    minmax=(-0.01, 0.01),           # 10ms before/after
)
# Returns: TsdFrame with averaged waveform
```

## Correlograms

### Autocorrelogram

```python
ac = nap.compute_autocorrelogram(
    tsgroup,
    binsize=0.001,          # 1ms bins
    windowsize=0.1,         # +/- 100ms window
    ep=wake_ep,             # restrict to epoch
    norm=True               # normalize
)
```

### Cross-Correlogram

```python
cc = nap.compute_crosscorrelogram(
    tsgroup,
    binsize=0.001,
    windowsize=0.1,
    ep=wake_ep
)

# Between two specific groups
cc = nap.compute_crosscorrelogram(
    (group1, group2),
    binsize=0.001,
    windowsize=0.5
)
```

### Event Correlogram

```python
ec = nap.compute_eventcorrelogram(
    tsgroup,
    event=stimulus_ts,
    binsize=0.01,
    windowsize=1.0
)
```

### Interspike Interval Distribution

```python
isi = nap.compute_isi_distribution(
    tsgroup,
    binsize=0.001,
    windowsize=0.1,
    ep=wake_ep
)
```

## Randomization / Bootstrapping

```python
# Jitter spike times
jittered = nap.jitter_timestamps(tsgroup, max_jitter=0.01)

# Circular shift within epochs
shifted = nap.shift_timestamps(tsgroup, min_shift=0.0, max_shift=10.0)

# Poisson resampling
resampled = nap.resample_timestamps(tsgroup)

# Shuffle within intervals
shuffled = nap.shuffle_ts_intervals(tsgroup)
```
