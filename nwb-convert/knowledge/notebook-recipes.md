# Notebook Recipes

Shared guidance for the notebooks written in Phase 8 (local NWB files) and Phase 11 (streamed
from DANDI). Each phase gives its own way to open the file; everything here starts from an
open `nwbfile`.

## Context to Gather

Besides the phase-specific items (file paths or Dandiset ID, sessions), collect:

1. **Data streams available**: Units (spike times), Position/SpatialSeries, LFP,
   trials/epochs, fluorescence traces, etc. You already know this from Phases 2-3.
2. **Associated publication**: If a paper exists, read it to understand:
   - What figures were published (especially Figures 1-2)
   - What analyses were central to the paper's conclusions
   - Whether key figures can be approximately reproduced from the NWB data
3. **Epochs/conditions**: What experimental conditions or behavioral states exist?

## Combined Analyses

A demo notebook includes 1-2 combined analyses that match the data:

- Place fields: spike positions overlaid on trajectory, 2D firing rate maps
- PSTHs: perievent spike histograms aligned to stimulus/trial onset
- Trial-aligned time series: neural activity aligned to behavioral events
- Tuning curves: firing rate as a function of a behavioral variable
- Raster + PSTH combined plots

If a paper exists, optionally attempt to reproduce Figure 1 or 2.

## Using Pynapple for Analysis

When the notebook includes neural analysis (place fields, PSTHs, tuning curves), use
pynapple. Load data into pynapple containers via `nap.NWBFile`:

```python
import pynapple as nap

nap.nap_config.suppress_conversion_warnings = True
nwb = nap.NWBFile(nwbfile)
print(nwb)  # lists every key with its pynapple type

# Keys are the names of the NWB objects. A TimeSeries is keyed by its own name
# (e.g. the SpatialSeries name), not by its container (e.g. Position).
spikes = nwb["units"]                      # TsGroup
position = nwb["<SpatialSeries name>"]     # TsdFrame
epochs = nwb["epochs"]                     # IntervalSet; extra columns become metadata
trials = nwb["trials"]                     # IntervalSet
```

Select intervals by a metadata column with a boolean mask, e.g.
`epochs[epochs["<label column>"] == "<label>"]`.

If `nap.NWBFile` doesn't find a data stream, construct the pynapple object manually:

```python
spatial_series = nwbfile.processing["behavior"]["<Position name>"]["<SpatialSeries name>"]
position = nap.TsdFrame(
    t=spatial_series.get_timestamps(),
    d=spatial_series.data[:],
    columns=["x", "y"],
)
```

## Visualization Guidelines

- Use `matplotlib` for all plots (it's universally available and renders in static notebooks)
- Every figure should have axis labels, a title, and a legend where appropriate
- Use `fig.tight_layout()` or `constrained_layout=True` to prevent label clipping
- For multi-panel figures, use `plt.subplots()` with appropriate `figsize`
- After generating any plot, read the saved image to verify it looks correct:
  - No overlapping labels or cut-off text
  - Adequate contrast and readable fonts
  - Appropriate axis ranges (not dominated by outliers)

## Common Visualization Recipes

**Position trajectory colored by epoch:**
```python
fig, ax = plt.subplots(figsize=(8, 8))
for label in np.unique(epochs["<label column>"]):
    position_in_label = position.restrict(epochs[epochs["<label column>"] == label])
    ax.plot(position_in_label[:, 0], position_in_label[:, 1], ".", markersize=0.5, alpha=0.5, label=label)
ax.legend(markerscale=10)
ax.set_xlabel("x (<SpatialSeries unit>)")
ax.set_ylabel("y (<SpatialSeries unit>)")
ax.set_title("Animal trajectory")
ax.set_aspect("equal")
```

**Spike raster plot:**
```python
fig, ax = plt.subplots(figsize=(12, 6))
for i, (unit_id, ts) in enumerate(spikes.items()):
    ax.plot(ts.times(), np.full(len(ts), i), "|", markersize=1, color="k")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Unit #")
ax.set_title("Spike raster")
```

**2D place field (firing rate map):**
```python
# xarray DataArray with dims (unit, x, y); pass epochs= to restrict to an IntervalSet
tuning_curves = nap.compute_tuning_curves(
    data=spikes, features=position, bins=30, feature_names=["x", "y"]
)
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
for ax, unit_id in zip(axes.flat, tuning_curves.coords["unit"].values):
    tuning_curves.sel(unit=unit_id).plot(ax=ax, x="x", y="y", cmap="hot", add_colorbar=False)
    ax.set_title(f"Unit {unit_id}")
plt.suptitle("Place fields")
fig.tight_layout()
```

**Peri-event raster and PSTH:**
```python
event_times = nap.Ts(t=trials.start)  # or any event timestamps
peri_event = nap.compute_perievent(data=spikes, events=event_times, window=(-0.5, 1.0))
unit_peri_event = peri_event[unit_id]  # TsGroup with one entry per event

bin_size = 0.02
firing_rate = unit_peri_event.count(bin_size).mean(axis=1) / bin_size
raster = unit_peri_event.to_tsd()  # times relative to the event; values are the event index

fig, (ax_raster, ax_rate) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
ax_raster.plot(raster.t, raster.d, "|k", markersize=2)
ax_raster.set_ylabel("Event")
ax_rate.plot(firing_rate.t, firing_rate.d)
ax_rate.set_xlabel("Time from event (s)")
ax_rate.set_ylabel("Firing rate (Hz)")
ax_raster.set_title(f"Peri-event raster and PSTH, unit {unit_id}")
```

**Trial-aligned continuous data:**
```python
# TsdFrame with one column per trial; time is relative to trial start
aligned = nap.compute_perievent(data=signal, events=nap.Ts(t=trials.start), window=(-0.5, 1.0))
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(aligned.t, aligned.d, color="gray", alpha=0.3)
ax.plot(aligned.t, np.nanmean(aligned.d, axis=1), color="k")
ax.set_xlabel("Time from trial start (s)")
ax.set_title("Trial-aligned signal")
```

## Notebook Cell Style

- **Markdown cells** should explain what each section does and why. Write for someone
  encountering this dataset for the first time.
- **Code cells** should be concise, one logical operation per cell. Don't cram loading,
  processing, and plotting into one cell.
- **Import cells** go at the top. Put all imports in one cell, sorted: stdlib, then
  third-party, then local.

## When a Cell Fails

Fix the code and re-run. Besides the phase-specific causes (file path, streaming), the
common one is missing data: a session might not have every expected data stream, so check
the NWB structure first.
