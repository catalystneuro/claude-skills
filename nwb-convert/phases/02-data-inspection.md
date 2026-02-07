## Phase 2: Data Inspection

**Goal**: Inspect actual data files to confirm formats, understand structure, and map to NeuroConv interfaces.

**Entry**: You have a general understanding of the experiment from Phase 1.

**Exit criteria**: For each data stream, you know:
- The exact file format and can read it programmatically
- Which NeuroConv interface handles it (or that custom code is needed)
- The source_data arguments needed (file paths, stream IDs, etc.)
- Any quirks or issues (corrupt files, missing headers, unusual organization)

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
