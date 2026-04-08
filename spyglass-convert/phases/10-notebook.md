## Phase 10: Spyglass Tutorial Notebook

**Goal**: Create a Jupyter notebook that demonstrates the data has been successfully
inserted into Spyglass and shows how to query it. This notebook validates the full
pipeline and gives the lab a starting point for analysis via Spyglass.

**Entry**: Phase 9 verification passed. All key Spyglass tables are populated.

**Baseline**: Follow **nwb-convert Phase 7** for notebook writing guidelines. These
apply unchanged:

- **Step 1** (plan the notebook) — gather context, list data streams, present plan
  to user before writing
- **Notebook cell style** — markdown prose for each section, one logical operation
  per code cell, all imports at top, suppress noisy warnings
- **Visualization guidelines** — matplotlib for all plots, axis labels + title + legend,
  `fig.tight_layout()`, verify rendered output looks correct
- **Testing** — run end-to-end with `jupyter execute` before committing;
  fix any cells that error

The Spyglass tutorial notebook differs from the local NWB notebook in that it
demonstrates **DataJoint queries** rather than direct NWB file reads. Use the
cell templates in this phase instead of the pynapple-based templates from Phase 7.

**Exit criteria**: A tested `notebooks/spyglass_tutorial.ipynb` that runs
end-to-end, demonstrates DataJoint queries across all inserted data types, and
retrieves data that can be compared to the source NWB file.

### Step 0: Plan the Notebook

Before writing code, collect:
1. Which Spyglass tables have data? (from Phase 9 verification)
2. Session identifier and subject details
3. Which data streams to demonstrate (ephys, LFP, DIO, video, epochs)

> Here's my plan for the tutorial notebook:
> - Connect to the Spyglass database
> - Show the session entry and metadata tables
> - Query the electrode table and show probe geometry
> - Retrieve raw ephys and plot a short snippet
> - [If LFP present] Query LFP and plot a trace
> - [If DIO present] Show behavioral event times
> - [If epochs present] List task epochs
> - [If video present] Show video file reference
>
> Does this look right? Anything to add or skip?

### Step 1: Set Up the Notebook Directory

```
<conversion_repo>/
  notebooks/
    environment.yml    ← already exists from the mamba setup
    spyglass_tutorial.ipynb
```

If `environment.yml` does not already exist in `notebooks/`, create one:
```yaml
name: spyglass
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - pip
  - pip:
    - spyglass-neuro
    - jupyter
    - matplotlib
    - pynwb
    - h5py
    - numpy
    - pandas
```

### Step 2: Write the Notebook

**Cell 1 — Title & Introduction (Markdown)**
```markdown
# Spyglass Tutorial: [Lab Name] Dataset

This notebook demonstrates how to query the [experiment description] dataset
from a Spyglass database. The data was converted from [source format] using
the `spyglass-convert` skill.

**Prerequisites**: Spyglass database running (see README for setup instructions).
```

**Cell 2 — Setup & Connection**
```python
import datajoint as dj
import spyglass.common as sgc
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Load DataJoint config
dj.config.load("../dj_local_conf.json")  # adjust path as needed
dj.conn(use_tls=False)

# Session to query
NWB_FILE_NAME = "session.nwb"  # update to your session

print("Connected to Spyglass database ✓")
```

**Cell 3 — Session Overview**
```python
restriction = {"nwb_file_name": NWB_FILE_NAME}

print("=== Session ===")
print(sgc.Session & restriction)

print("\n=== Subject ===")
# subject is embedded in the session NWB metadata
session_row = (sgc.Session & restriction).fetch1()
print(f"Session description: {session_row.get('session_description', 'N/A')}")

print("\n=== Task Epochs ===")
print(sgc.TaskEpoch & restriction)
```

**Cell 4 — Electrode Table**
```python
print("=== Electrode Table (first 10) ===")
elec_df = (sgc.Electrode & restriction).fetch(format="frame").head(10)
print(elec_df[["electrode_id", "group_name", "brain_area", "probe_shank",
               "probe_electrode", "bad_channel"]].to_string())
```

**Cell 5 — Raw Ephys (snippet)**
```python
raw_nwb = (sgc.Raw & restriction).fetch_nwb()
if raw_nwb:
    raw = raw_nwb[0]["raw"]
    fs = raw.rate
    n_seconds = 0.1
    n_samples = int(n_seconds * fs)
    n_channels_to_plot = min(8, raw.data.shape[1])

    fig, axes = plt.subplots(n_channels_to_plot, 1, figsize=(14, 8), sharex=True)
    t = np.arange(n_samples) / fs
    for i, ax in enumerate(axes):
        ax.plot(t, raw.data[:n_samples, i], lw=0.5, color="k")
        ax.set_ylabel(f"Ch {i}", fontsize=7)
        ax.set_yticks([])
    axes[-1].set_xlabel("Time (s)")
    fig.suptitle(f"Raw ephys — first {n_seconds*1000:.0f} ms")
    fig.tight_layout()
    plt.show()
else:
    print("No Raw data found for this session")
```

**Cell 6 — LFP (if present)**
```python
from .insert_session import get_nwb_copy_filename
copy_file_name = get_nwb_copy_filename(NWB_FILE_NAME)
copy_restriction = {"nwb_file_name": copy_file_name}

lfp_nwb = (sgc.ImportedLFP & copy_restriction).fetch_nwb()
if lfp_nwb:
    lfp = lfp_nwb[0]["lfp"]
    fs = lfp.rate
    n_seconds = 1.0
    n_samples = int(n_seconds * fs)
    n_channels_to_plot = min(4, lfp.data.shape[1])

    fig, axes = plt.subplots(n_channels_to_plot, 1, figsize=(14, 6), sharex=True)
    t = np.arange(n_samples) / fs
    for i, ax in enumerate(axes):
        ax.plot(t, lfp.data[:n_samples, i] * 1e6, lw=0.8, color="steelblue")
        ax.set_ylabel(f"Ch {i}\n(µV)", fontsize=7)
    axes[-1].set_xlabel("Time (s)")
    fig.suptitle(f"LFP — first {n_seconds:.0f} s")
    fig.tight_layout()
    plt.show()
else:
    print("No LFP data found for this session")
```

**Cell 7 — DIO Events (if present)**
```python
dio_rows = (sgc.DIOEvents & restriction).fetch(as_dict=True)
if dio_rows:
    print(f"DIO channels: {len(dio_rows)}")
    for row in dio_rows:
        ts = row["dio_timestamps"]
        print(f"  {row['dio_event_name']}: {len(ts)} events, "
              f"first={ts[0]:.3f}s, last={ts[-1]:.3f}s")
else:
    print("No DIO events for this session")
```

**Cell 8 — Video Files (if present)**
```python
video_rows = (sgc.VideoFile & restriction).fetch(as_dict=True)
if video_rows:
    for row in video_rows:
        print(f"Video: {row['camera_name']} → {row['video_file_path']}")
else:
    print("No video files for this session")
```

**Cell 9 — Summary (Markdown)**
```markdown
## Summary

This notebook demonstrated how to connect to the Spyglass database and query:
- Session metadata and task epochs
- Electrode table with probe geometry
- Raw electrophysiology data
- LFP traces
- DIO behavioral events
- Video file references

For further analysis, see the [Spyglass documentation](https://lorenfranklab.github.io/spyglass/).
```

### Step 3: Test the Notebook

Run the notebook end-to-end:
```bash
cd <conversion_repo>/notebooks
jupyter execute spyglass_tutorial.ipynb --timeout=300
```

Verify:
1. All cells run without errors
2. Plots render correctly (inspect output images)
3. Table outputs show actual data rows

### Step 4: Commit the Notebook

```bash
git add notebooks/spyglass_tutorial.ipynb notebooks/environment.yml
git commit -m "Phase 10: add Spyglass tutorial notebook"
git push
```

> The Spyglass tutorial notebook is ready at `notebooks/spyglass_tutorial.ipynb`.
>
> The full ARC conversion pipeline is complete:
> ✓ Spyglass database running
> ✓ NWB files converted (Spyglass-compatible)
> ✓ Session inserted into database
> ✓ Tables verified and data integrity confirmed
> ✓ Tutorial notebook demonstrating successful ingestion
>
> The conversion repo is committed and pushed. Share it with your team as the
> reference implementation for this dataset.
