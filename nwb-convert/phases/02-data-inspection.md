## Phase 2: Data Inspection

**Goal**: Inspect actual data files to confirm formats, understand structure, and map to NeuroConv interfaces.

**Entry**: You have a general understanding of the experiment from Phase 1.

**Note**: If data was mounted from Google Drive in Phase 1, all inspection uses
the local mount point. Files are streamed on-demand and cached locally by rclone.

**Exit criteria**: For each data stream, you know:
- The exact file format and can read it programmatically
- Which NeuroConv interface handles it (or that custom code is needed)
- The source_data arguments needed (file paths, stream IDs, etc.)
- Any quirks or issues (corrupt files, missing headers, unusual organization)

### Cross-Reference with Conversion Registry

Before inspecting files, check the registry's `format_hints` to accelerate interface identification.
If the registry was fetched in Phase 1, use it to pre-match file patterns:

```python
import yaml
from fnmatch import fnmatch
from pathlib import Path

registry_path = Path("/tmp/registry.yaml")
if not registry_path.exists() or registry_path.stat().st_size == 0:
    print("Registry not available — skipping format hint matching")
    registry = {"format_hints": []}
else:
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

# Collect actual filenames from the data directory
data_path = Path("<sample_session_path>")
filenames = [f.name for f in data_path.rglob("*") if f.is_file()]

# Match filenames against registry format_hints using glob matching
matched_interfaces = {}  # interface_name → list of (pattern, seen_in)
for hint in registry.get("format_hints", []):
    for pattern in hint["patterns"]:
        for filename in filenames:
            if fnmatch(filename, pattern):
                iface = hint["interface"]
                if iface not in matched_interfaces:
                    matched_interfaces[iface] = []
                matched_interfaces[iface].append({
                    "pattern": pattern,
                    "matched_file": filename,
                    "seen_in": hint["seen_in"],
                })
                break  # One match per pattern is enough

for iface, matches in matched_interfaces.items():
    repos = set()
    for m in matches:
        repos.update(m["seen_in"])
    print(f"Registry match: {iface} (seen in {sorted(repos)})")
    for m in matches:
        print(f"  {m['pattern']} matched {m['matched_file']}")
```

When a filename matches a `format_hint` pattern, you can proceed with higher confidence in the
interface selection. If the same pattern has been used successfully in prior conversions,
mention this to the user and skip exploratory probing for that stream.

### Approach

1. **Ask for a sample session** — a single, complete session with all data streams:
   > Can you point me to one complete example session? I'd like to inspect the files
   > to understand the exact format and structure.

2. **Inspect files directly** using Python. For each data stream:

   **For electrophysiology (SpikeGLX, OpenEphys, etc.):**
   ```python
   # Try loading with spikeinterface
   import spikeinterface.extractors as se
   recording = se.read_spikeglx(folder_path, stream_id="imec0.ap")
   print(f"Channels: {recording.get_num_channels()}")
   print(f"Sampling rate: {recording.get_sampling_frequency()}")
   print(f"Duration: {recording.get_total_duration()}")
   ```

   **For spike sorting (Phy, Kilosort, etc.):**
   ```python
   sorting = se.read_phy(folder_path)
   print(f"Units: {sorting.get_num_units()}")
   print(f"Unit IDs: {sorting.get_unit_ids()}")
   ```

   **For calcium imaging (ScanImage, Scanbox, Suite2p, etc.):**
   ```python
   import roiextractors as re
   imaging = re.read_scanbox(file_path)
   print(f"FOV size: {imaging.get_image_size()}")
   print(f"Num frames: {imaging.get_num_frames()}")
   print(f"Sampling rate: {imaging.get_sampling_frequency()}")
   ```

   **For behavior files (.mat, .csv, .txt, .pkl, etc.):**
   ```python
   # For MATLAB files
   import h5py  # or scipy.io.loadmat for v5 .mat files
   with h5py.File(path) as f:
       print(list(f.keys()))
       # Recursively explore structure

   # For CSV/text
   import pandas as pd
   df = pd.read_csv(path, sep='\t', nrows=5)
   print(df.columns.tolist())
   print(df.head())
   ```

3. **Test NeuroConv interfaces** — for each data stream that has a matching interface, try instantiating it:
   ```python
   from neuroconv.datainterfaces import SpikeGLXRecordingInterface
   interface = SpikeGLXRecordingInterface(folder_path=path, stream_id="imec0.ap")
   metadata = interface.get_metadata()
   print(metadata)
   ```

4. **Identify custom interface needs** — for data streams with no NeuroConv interface:
   - Document the file format, structure, and what data/metadata it contains
   - Note what NWB types the data should map to (TimeSeries, SpatialSeries, TimeIntervals, etc.)
   - Flag these for Phase 5 code generation

### Identifying Processed vs. Raw Data

During inspection, watch for signs that data has been post-processed rather than coming
directly off the acquisition system. Common indicators:

- **Trialized structure**: Data organized into trials/epochs with inter-trial data removed
  (e.g., MATLAB struct arrays with fields like `trial(1).spikes`, `trial(1).lfp`)
- **Pre-computed derived quantities**: Rate maps, tuning curves, PSTHs, averaged traces,
  z-scored signals — these are analysis outputs, not raw data
- **Resampled or interpolated data**: Timestamps at suspiciously round intervals, or data
  streams that should have different sampling rates but don't
- **Float conversion of integer data**: Electrophysiology stored as float64 instead of
  int16 (raw acquisition is almost always integer)
- **Cropped time windows**: Data that starts at t=0 for each trial rather than having
  continuous session timestamps
- **Custom .mat or .pkl files**: Often contain lab-specific processed structures. Check if
  the original acquisition files (.bin, .dat, .tif, .rhd, etc.) also exist alongside them

When you identify processed data, bring it up with the user:
> These .mat files appear to contain data that's been processed — [describe what you see,
> e.g., "the neural data is organized into trials and stored as float64"]. Do you also have
> the raw recording files from [recording system]? Those would be ideal for NWB conversion
> because [brief reason].

If the user confirms raw data is available, pivot to using it. If not, proceed with what's
available — some NWB is better than no NWB. Document the data provenance in
`conversion_notes.md` either way.

### Common Gotchas

- **MATLAB v7.3 files** use HDF5 format (use `h5py`), older versions use scipy.io.loadmat
- **Pickle files** may require specific package versions to deserialize
- **Text files** — check delimiter (tab vs comma vs space), header presence, encoding
- **SpikeGLX** — the meta file is essential; make sure .bin and .meta are co-located
- **Suite2p** — look for the `suite2p/plane0/` directory structure
- **Multiple probes** — SpikeGLX uses imec0, imec1, etc.; each needs its own interface instance

### Update conversion_notes.md

Add an "Interface Mapping" section:

```markdown
## Interface Mapping
| Stream | Interface | source_data | Status |
|--------|-----------|-------------|--------|
| Raw AP | SpikeGLXRecordingInterface | folder_path, stream_id="imec0.ap" | Verified |
| LFP | SpikeGLXLFPInterface | folder_path, stream_id="imec0.lf" | Verified |
| Sorting | PhySortingInterface | folder_path | Verified |
| VR position | CUSTOM: VRBehaviorInterface | file_path | Needs implementation |
| Lick events | CUSTOM: EventsInterface | folder_path | Needs implementation |
```

### Push Phase 2 Results

After updating `conversion_notes.md` with the interface mapping, commit and push:
```bash
git add conversion_notes.md
git commit -m "Phase 2: data inspection — interface mapping and format details"
if git remote get-url origin &>/dev/null; then git push; fi
```
