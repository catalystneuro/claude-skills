## Phase 8: Example Notebook Generation

**Goal**: Create an educational Jupyter notebook that demonstrates how to stream, read,
and visualize the published NWB data from DANDI. The notebook serves as a companion to
the Dandiset — helping new users (and reviewers) explore the data independently.

**Entry**: Data has been uploaded to DANDI (Phase 7 complete). The Dandiset ID and asset
paths are known.

**Exit criteria**: A tested `.ipynb` notebook that runs end-to-end using only streaming
access (no local downloads), with clear prose, visualizations of each data stream, and
at least one combined analysis (e.g., place fields, PSTHs, or trial-aligned time series).

### Step 0: Gather Context

Before writing any code, collect the information needed to plan the notebook:

1. **Dandiset ID and version** (from Phase 7)
2. **Session inventory**: List all NWB files. Identify which sessions have behavioral data,
   which are ecephys-only, etc.
3. **Data streams available**: Units (spike times), Position/SpatialSeries, LFP,
   trials/epochs, fluorescence traces, etc. You already know this from Phases 2-3.
4. **Associated publication**: If a paper exists, read it to understand:
   - What figures were published (especially Figures 1-2)
   - What analyses were central to the paper's conclusions
   - Whether key figures can be approximately reproduced from the NWB data
5. **Epochs/conditions**: What experimental conditions or behavioral states exist?

> I'll now create an example notebook that shows how to stream and visualize your data
> from DANDI. This notebook will be submitted to the
> [dandi/example-notebooks](https://github.com/dandi/example-notebooks) repository.
>
> Let me check the data structure and plan the visualizations.

### Step 1: Plan the Notebook

Design the notebook structure based on what data streams are available. Follow this
template, including only sections relevant to the dataset:

```
1. Title & Introduction
   - Dataset description, link to Dandiset, link to paper (if any)
   - Brief experimental summary

2. Setup
   - Install/import dependencies
   - Connect to DANDI and list available sessions

3. Load a Single Session
   - Stream an NWB file using remfile
   - Explore the NWB file structure (subject, session, electrodes, epochs)

4. Visualize Individual Data Streams (include all that apply):
   a. Position/trajectory plots (colored by time or epoch)
   b. Spike raster plots (all units, subset of time)
   c. LFP traces or spectrograms
   d. Fluorescence traces (dF/F or raw)
   e. Behavioral events or trial structure
   f. Pre-computed data (rate maps, waveforms, etc.)

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

Create the notebook in a local working directory following the `dandi/example-notebooks`
conventions:

```
<working_dir>/
  <dandiset_id>/
    nwb-convert-skill/
      environment.yml
      README.md
      <dandiset_id>_demo.ipynb
```

**environment.yml** — minimal conda environment:
```yaml
name: <dandiset_id>_demo
channels:
    - conda-forge
dependencies:
    - python==3.11
    - pip
    - pip:
      - dandi
      - jupyter
      - matplotlib
      - pynwb
      - remfile
      - pynapple
      - h5py
```

Add additional pip dependencies only if the notebook actually uses them (e.g., `scipy`
for signal processing, `numpy` for array operations). Keep it minimal.

**README.md**:
```markdown
# <Dandiset Title>

This example notebook demonstrates how to access and visualize the dataset published at
[DANDI:<dandiset_id>](https://dandiarchive.org/dandiset/<dandiset_id>).

<Brief description of the data: species, brain regions, recording methods, behavioral task>

## Installing the dependencies

```bash
git clone https://github.com/dandi/example-notebooks
cd example-notebooks/<dandiset_id>/CatalystNeuro
conda env create --file environment.yml
conda activate <dandiset_id>_demo
```

## Running the notebook

```bash
jupyter notebook <dandiset_id>_demo.ipynb
```
```

### Step 3: Write the Notebook

Build the notebook cell by cell, running each cell as you go to verify it works.
Follow these principles:

#### Streaming Access Pattern

Always stream data from DANDI — never download files in the notebook:

```python
from dandi.dandiapi import DandiAPIClient
import h5py
import remfile
from pynwb import NWBHDF5IO

dandiset_id = "<DANDISET_ID>"
file_path = "<ASSET_PATH>"

with DandiAPIClient() as client:
    asset = client.get_dandiset(dandiset_id, "draft").get_asset_by_path(file_path)
    s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)

file = remfile.File(s3_url)
h5_file = h5py.File(file, "r")
io = NWBHDF5IO(file=h5_file, load_namespaces=True)
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

### Step 4: Test the Notebook

Run the notebook end-to-end using `jupyter execute`:

```bash
cd <working_dir>/<dandiset_id>/CatalystNeuro
jupyter execute <dandiset_id>_demo.ipynb --timeout=600
```

Or test with `nbconvert`:

```bash
jupyter nbconvert --to notebook --execute <dandiset_id>_demo.ipynb --output executed.ipynb
```

Verify:
1. All cells execute without errors
2. All plots render correctly (read the output notebook images)
3. Streaming access works (no local file dependencies)
4. The notebook completes in a reasonable time (< 5 minutes for streaming)

If cells fail, fix the code and re-run. Common issues:
- **remfile timeout**: Some NWB files are large. Consider loading less data or a smaller session.
- **pynapple conversion warnings**: Add `nap.nap_config.suppress_conversion_warnings = True`
- **Missing data**: A session might not have all expected data streams. Add checks.

Present this to the user and request feedback. Only proceed to Step 5 after you have the user's approval.

### Step 5: Submit to example-notebooks

Clone the `dandi/example-notebooks` repository and add the notebook:

```bash
# Clone the repo (or fork if you don't have write access)
gh repo fork dandi/example-notebooks --clone
cd example-notebooks

# Create a branch
git checkout -b add-notebook-<dandiset_id>

# Copy the notebook directory
cp -r <working_dir>/<dandiset_id> .

# Commit and push
git add <dandiset_id>/
git commit -m "Add example notebook for DANDI:<dandiset_id>"
git push -u origin add-notebook-<dandiset_id>

# Create PR
gh pr create \
  --title "Add tutorial notebook for <dandiset_id>" \
  --body "Add tutorial notebook demonstrating how to stream and visualize NWB data from DANDI:<dandiset_id>.

## Summary
- Streams data from DANDI using remfile (no local downloads)
- Shows NWB file structure and metadata
- Visualizes [list key visualizations]
- [Optional: Reproduces Figure X from the associated paper]

## Dependencies
Listed in environment.yml (conda + pip)

Generated with [Claude Code](https://claude.com/claude-code)"
```

Inform the user:
> The example notebook has been submitted as a PR to dandi/example-notebooks.
> PR: [link]
>
> The notebook demonstrates:
> [list what the notebook covers]
