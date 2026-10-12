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
    - python==3.11
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

# Access data
spikes = nwb["units"]          # TsGroup
position = nwb["position"]    # Tsd or TsdFrame
epochs = nwb["epochs"]        # dict of IntervalSet (if epochs exist)
```

If `nap.NWBFile` doesn't automatically find certain data streams, construct pynapple
objects manually:

```python
# Manual spike extraction
spike_times = {i: nwbfile.units['spike_times'][i] for i in range(len(nwbfile.units))}
spikes = nap.TsGroup(spike_times)

# Manual position extraction
pos_data = nwbfile.processing['behavior']['position']['spatial_series']
position = nap.TsdFrame(
    t=pos_data.timestamps[:],
    d=pos_data.data[:],
    columns=["x", "y"],
)

# Epochs from intervals table
epochs_table = nwbfile.intervals['epochs']
for i in range(len(epochs_table)):
    start = epochs_table['start_time'][i]
    stop = epochs_table['stop_time'][i]
    label = epochs_table['session_type'][i]  # or whatever column labels the condition
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
colors = {"ES": "tab:blue", "BL": "tab:green", "MC": "tab:orange"}
for epoch_name, epoch_interval in epoch_dict.items():
    pos_epoch = position.restrict(epoch_interval)
    ax.plot(pos_epoch[:, 0], pos_epoch[:, 1], '.', markersize=0.5,
            color=colors.get(epoch_name, "gray"), label=epoch_name, alpha=0.5)
ax.legend()
ax.set_xlabel("X (pixels)")
ax.set_ylabel("Y (pixels)")
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
tc, binsxy = nap.compute_2d_tuning_curves(
    group=spikes, features=position, nb_bins=30, ep=epoch_interval
)
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
for i, ax in enumerate(axes.flat):
    if i < len(tc):
        ax.imshow(tc[i].T, origin="lower", aspect="auto", cmap="hot")
        ax.set_title(f"Unit {i}")
plt.suptitle("Place fields")
fig.tight_layout()
```

**PSTH (perievent time histogram):**
```python
# Align spikes to event times
peth = nap.compute_perievent(spikes, event_times, minmax=(-0.5, 1.0))

fig, ax = plt.subplots(figsize=(8, 4))
for trial_spikes in peth[unit_id]:
    ax.plot(trial_spikes.times(), np.full(len(trial_spikes), trial_idx), "|k", markersize=2)
ax.set_xlabel("Time from event (s)")
ax.set_ylabel("Trial")
ax.set_title(f"PSTH — Unit {unit_id}")
```

**Trial-aligned continuous data:**
```python
# Align continuous signal to trial onsets
for i, ep in enumerate(trial_epochs):
    segment = signal.restrict(ep)
    t_aligned = segment.times() - ep["start"].values[0]
    ax.plot(t_aligned, segment.values, alpha=0.3, color="gray")
```

#### Notebook Cell Style

- **Markdown cells** should explain what each section does and why. Write for someone
  encountering this dataset for the first time.
- **Code cells** should be concise — one logical operation per cell. Don't cram loading,
  processing, and plotting into one cell.
- **Import cells** go at the top. Put all imports in one cell, sorted: stdlib → third-party → local.
- Suppress noisy warnings:
  ```python
  import warnings
  warnings.filterwarnings("ignore", message=".*pynapple.*")
  ```

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


Run every notebook end-to-end using `jupyter execute`:

```bash
cd <conversion_repo>/notebooks
for notebook in *.ipynb; do jupyter execute "$notebook" --timeout=600; done
```

Or test with `nbconvert`:

```bash
jupyter nbconvert --to notebook --execute <lab_name>_demo.ipynb --output executed.ipynb
```

Verify:
1. All cells execute without errors
2. All plots render correctly (read the output notebook images)
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
