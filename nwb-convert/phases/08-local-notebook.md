## Phase 8: Local Example Notebook

**Goal**: Create Jupyter notebooks that load and visualize the locally converted NWB data:
one review notebook per data stream, so a reviewer can check each stream on its own, and one
demo notebook with combined analyses that serves as a starting point for analysis. Both
validate the conversion output before the data is uploaded to DANDI.

**Entry**: Testing and validation are complete (Phase 7). At least one full NWB file has
been written to disk.

**Exit criteria**: Tested `.ipynb` notebooks that run end-to-end loading local NWB files: one
review notebook per data stream (Step 3b), and a demo notebook with clear prose and at least
one combined analysis (e.g., place fields, PSTHs, or trial-aligned time series).

### Step 0: Gather Context

Before writing any code, collect the information needed to plan the notebook:

1. **Output NWB file path**: Where did the conversion write the NWB file(s)?
2. **Session inventory**: Which session will be used as the demo session? Pick a
   representative one (ideally the same session used in testing).
3. **Data streams available**: Units (spike times), Position/SpatialSeries, LFP,
   trials/epochs, fluorescence traces, etc. You already know this from Phases 2-3.
4. **Associated publication**: If a paper exists, read it to understand:
   - What figures were published (especially Figures 1-2)
   - What analyses were central to the paper's conclusions
   - Whether key figures can be approximately reproduced from the NWB data
5. **Epochs/conditions**: What experimental conditions or behavioral states exist?

> I'll now create a local example notebook that shows how to load and visualize
> your converted NWB data. This helps validate the conversion and gives you a
> starting point for analysis.
>
> Let me check the data structure and plan the visualizations.

### Step 1: Plan the Notebook

Design the notebook structure based on what data streams are available. Follow this
template, including only sections relevant to the dataset:

```
1. Title & Introduction
   - Dataset description, brief experimental summary
   - Note that this notebook loads local NWB files

2. Setup
   - Install/import dependencies
   - Specify path to the local NWB file

3. Load a Single Session
   - Open the NWB file using NWBHDF5IO
   - Explore the NWB file structure (subject, session, electrodes, epochs)

4. Individual Data Streams
   - Link to each per-stream review notebook (Step 3b)

5. Combined Analyses (include 1-2 that match the data):
   a. Place fields — spike positions overlaid on trajectory, 2D firing rate maps
   b. PSTHs — perievent spike histograms aligned to stimulus/trial onset
   c. Trial-aligned time series — neural activity aligned to behavioral events
   d. Tuning curves — firing rate as a function of a behavioral variable
   e. Raster + PSTH combined plots

6. (Optional) Reproduce a Paper Figure
   - If a paper exists, attempt to replicate Figure 1 or 2

7. Summary
   - What the notebook demonstrated
   - Links to further resources (PyNWB docs, pynapple tutorials, NWB overview)
```

Present the plan to the user:

> Here's what I plan to include in the notebook:
> [list sections based on available data]
>
> Does this look good? Anything you'd like to add or remove?

### Step 2: Set Up the Notebook Directory

Create the notebook inside the conversion repo in a `notebooks/` directory:

```
<conversion_repo>/
  notebooks/
    environment.yml
    README.md
    <lab_name>_demo.ipynb
    <stream>.ipynb          ← one review notebook per data stream (Step 3b)
```

**environment.yml** — minimal conda environment:
```yaml
name: <lab_name>_demo
channels:
    - conda-forge
dependencies:
    - python=3.12
    - pip
    - pip:
      - jupyter
      - matplotlib
      - pynwb
      - pynapple
      - h5py
```

Add additional pip dependencies only if the notebook actually uses them (e.g., `scipy`
for signal processing, `numpy` for array operations). Keep it minimal.

**README.md**:
```markdown
# <Lab/Dataset Name> Example Notebook

This notebook demonstrates how to load and visualize the NWB data produced by this
conversion pipeline.

<Brief description of the data: species, brain regions, recording methods, behavioral task>

## Installing the dependencies

```bash
conda env create --file environment.yml
conda activate <lab_name>_demo
```

## Running the notebook

```bash
jupyter notebook <lab_name>_demo.ipynb
```

Update `nwb_file_path` in the first cell to point to your converted NWB file.
```

### Step 3: Write the Notebook

Build the notebook cell by cell, running each cell as you go to verify it works.
Follow these principles:

#### Local File Access Pattern

Load the NWB file directly from disk:

```python
from pynwb import NWBHDF5IO

nwb_file_path = "/path/to/converted/session.nwb"  # update this path

io = NWBHDF5IO(nwb_file_path, "r")
nwbfile = io.read()
```

#### Using Pynapple for Analysis

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

#### Visualization Guidelines

- Use `matplotlib` for all plots (it's universally available and renders in static notebooks)
- Every figure should have axis labels, a title, and a legend where appropriate
- Use `fig.tight_layout()` or `constrained_layout=True` to prevent label clipping
- For multi-panel figures, use `plt.subplots()` with appropriate `figsize`
- After generating any plot, read the saved image to verify it looks correct:
  - No overlapping labels or cut-off text
  - Adequate contrast and readable fonts
  - Appropriate axis ranges (not dominated by outliers)

#### Common Visualization Recipes

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

#### Notebook Cell Style

- **Markdown cells** should explain what each section does and why. Write for someone
  encountering this dataset for the first time.
- **Code cells** should be concise — one logical operation per cell. Don't cram loading,
  processing, and plotting into one cell.
- **Import cells** go at the top. Put all imports in one cell, sorted: stdlib → third-party → local.

### Step 3b: Write the Per-Stream Review Notebooks

Write one notebook per data stream, named after the stream (e.g. `fiber_photometry.ipynb`).
Each one lets a reviewer confirm that stream was converted correctly without reading the
conversion code. Use the same demo session, file access pattern, and cell style as above.

1. **Title**: the stream, its source files and recording system.
2. **Structural summary**: a table of the NWB objects that hold this stream, with their
   neurodata type and namespace, so a reviewer sees at a glance which core types and
   extensions were used and whether device and metadata objects exist. List the stream's
   object names, including its devices and metadata containers:

   ```python
   import pandas as pd
   from hdmf.container import Container

   stream_object_names = ["<series or table name>", "<device name>", "<metadata container name>"]
   summary = pd.DataFrame(
       [
           dict(
               name=neurodata_object.name,
               neurodata_type=neurodata_object.neurodata_type,
               namespace=neurodata_object.namespace,
               parent=neurodata_object.parent.name,
           )
           for neurodata_object in nwbfile.objects.values()
           if isinstance(neurodata_object, Container) and neurodata_object.parent is not None
       ]
   )
   summary[summary["name"].isin(stream_object_names)]
   ```

   Follow it with a markdown cell stating which types the stream should use (e.g.
   ndx-fiber-photometry for fiber photometry, ndx-optogenetics for optogenetics).
3. **Plots of this stream alone**: e.g. traces over a short window and the full session,
   event rasters, position trajectories, or rate maps, whichever fit the data.
4. **Checks against the source**: one or two comparisons a reviewer can verify by eye,
   such as event counts per type or the first samples next to the values read from the
   source files.

### Step 4: Run, Check, and Commit the Notebooks

Run every notebook end-to-end using `jupyter execute`:

```bash
cd <conversion_repo>/notebooks
for notebook in *.ipynb; do jupyter execute --inplace --timeout=600 "$notebook"; done
```

Verify:
1. All cells execute without errors
2. All plots render correctly (read the images saved in the executed notebooks)
3. The notebook completes in a reasonable time (< 5 minutes)

If cells fail, fix the code and re-run. Common issues:
- **File path**: Make sure `nwb_file_path` points to an actual converted NWB file.
- **pynapple conversion warnings**: Add `nap.nap_config.suppress_conversion_warnings = True`
- **Missing data**: A session might not have all expected data streams. Check the NWB structure first.

Present the notebooks to the user and request feedback. Once approved, commit them to the
conversion repo. In stacked PRs mode, commit each review notebook on its stream's branch and
the demo notebook on the last branch, carrying changes up the stack as described in
`knowledge/stacked-prs.md`, then go to Step 5. Otherwise:

```bash
git add notebooks/
git commit -m "Add local example notebooks"
git push
```

### Step 5: Open the Stacked PRs (stacked PRs mode only)

Push every branch and open one PR per branch, from the bottom of the stack up, as described
in `knowledge/stacked-prs.md` ("Opening the PRs"). Then share the list of PR links with the
user and note that they are merged in order from the bottom.

> The notebooks are saved in `notebooks/`, one per data stream plus `<lab_name>_demo.ipynb`.
> You can open them anytime to explore the converted data before uploading to DANDI.
>
> Next we'll upload the data to DANDI.
