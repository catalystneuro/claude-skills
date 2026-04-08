## Phase 3: Data Inspection

**Goal**: Inspect actual data files to confirm formats, understand structure, and
map to NeuroConv interfaces — with a Spyglass compatibility lens.

**Entry**: You have a general understanding of the experiment from Phase 2.

**Baseline**: Follow **nwb-convert Phase 2** for the full inspection workflow. All steps apply:

- **Registry cross-reference** — match filenames against `format_hints` before probing files
- **File inspection** — SpikeGLX/OpenEphys via spikeinterface, Phy via spikeinterface,
  calcium imaging via roiextractors, behavior files via pymatreader/pandas/h5py
- **NeuroConv interface testing** — instantiate each interface and call `get_metadata()`
- **Processed-vs-raw detection** — flag trialized structs, float64 ephys, cropped windows
- **Common gotchas** — MATLAB v7.3 HDF5, SpikeGLX .bin + .meta co-location, multiple probes

For MATLAB files, prefer `pymatreader` (see
`../nwb-convert/knowledge/conversion-patterns.md` §"Reading MATLAB .mat files").

**Exit criteria**: For each data stream you know:
- The exact file format and can read it programmatically
- Which NeuroConv interface handles it (or that custom code is needed)
- Whether the interface output is Spyglass-compatible (see `knowledge/spyglass-nwb-requirements.md`)
- The `source_data` arguments needed

### Spyglass-Specific Additions to nwb-convert Phase 2

### Step 1: Get a Sample Session

> Can you point me to one complete example session? I'd like to inspect the files
> to understand the exact format and structure.

### Step 2: Inspect Files

**Electrophysiology (SpikeGLX):**
```python
import spikeinterface.extractors as se

# AP band
recording_ap = se.read_spikeglx(folder_path, stream_id="imec0.ap")
print(f"AP channels: {recording_ap.get_num_channels()}")
print(f"AP rate: {recording_ap.get_sampling_frequency()} Hz")
print(f"Duration: {recording_ap.get_total_duration():.1f} s")

# LF band
recording_lf = se.read_spikeglx(folder_path, stream_id="imec0.lf")
print(f"LF channels: {recording_lf.get_num_channels()}")
print(f"LF rate: {recording_lf.get_sampling_frequency()} Hz")

# NIDQ (DIO events, sync pulses)
recording_nidq = se.read_spikeglx(folder_path, stream_id="nidq")
print(f"NIDQ channels: {recording_nidq.channel_ids}")
```

**Spike sorting (Phy):**
```python
sorting = se.read_phy(phy_folder)
print(f"Units: {sorting.get_num_units()}")
print(f"Unit IDs: {sorting.get_unit_ids()[:10]}")
```

**Behavior files (.mat, .csv, .txt):**
```python
# Preferred: pymatreader (handles most MATLAB versions uniformly)
from pymatreader import read_mat
mat = read_mat(path)
print({k: type(v) for k, v in mat.items()})

# For MATLAB v7.3 (HDF5-based) when pymatreader fails
import h5py
with h5py.File(path) as f:
    print(list(f.keys()))
```

For a complete MATLAB reading decision tree (pymatreader vs matio vs h5py vs
hdf5storage), see `../nwb-convert/knowledge/conversion-patterns.md` §"Reading MATLAB .mat files".

# CSV/text
import pandas as pd
df = pd.read_csv(path, nrows=5)
print(df.columns.tolist(), df.shape)
```

**Video:**
```python
import cv2
cap = cv2.VideoCapture(str(video_path))
print(f"FPS: {cap.get(cv2.CAP_PROP_FPS)}")
print(f"Frame count: {int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}")
print(f"Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
cap.release()
```

### Step 3: Test NeuroConv Interfaces

For each data stream with a matching NeuroConv interface, instantiate it:
```python
from neuroconv.datainterfaces import SpikeGLXRecordingInterface
interface = SpikeGLXRecordingInterface(folder_path=path, stream_id="imec0.ap")
metadata = interface.get_metadata()
print(metadata)
```

### Step 4: Flag Spyglass Compatibility Issues

Read `knowledge/spyglass-nwb-requirements.md` to check each interface against
the known compatibility table. Flag any interface that may produce incompatible
output. The highest-risk areas are:

- **Video**: Do not use `VideoInterface` without testing. Use `ImageSeries(external_file=[...])`
  directly or a custom interface. See the knowledge file for the correct pattern.
- **Electrode table**: The standard SpikeGLX/OpenEphys interfaces do NOT add
  the required Spyglass columns. These must be added manually in `add_to_nwbfile()`
  or in the NWBConverter.
- **LFP placement**: Must end up in `processing["ecephys"]["LFP"]` for Spyglass
  to find it.

### Update spyglass_notes.md

Add an Interface Mapping section:

```markdown
## Interface Mapping
| Stream | Interface | source_data | Spyglass-Compatible? |
|--------|-----------|-------------|----------------------|
| AP band | SpikeGLXRecordingInterface | folder_path, stream_id="imec0.ap" | Yes (after electrode column fix) |
| LF band | SpikeGLXRecordingInterface | folder_path, stream_id="imec0.lf" | Yes (with LFP placement fix) |
| Sorting | PhySortingInterface | folder_path | Yes |
| Video | CUSTOM: ImageSeries direct | file_path | Yes |
| Behavior | CUSTOM: BehaviorInterface | file_path | Verify |
```

### Push Phase 3 Results

```bash
git add spyglass_notes.md
git commit -m "Phase 3: data inspection — interface mapping"
```
