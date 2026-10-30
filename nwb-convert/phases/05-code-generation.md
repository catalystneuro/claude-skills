## Phase 5: Code Generation

**Goal**: Generate a complete, pip-installable conversion repo following CatalystNeuro conventions.

**Entry**: You have complete experiment spec, interface mapping, metadata, and sync plan.

**Exit criteria**: A working repo with:
- The directory structure from `knowledge/repo-structure.md`, with `LICENSE` and `.pre-commit-config.yaml`
- `pyproject.toml` with proper dependencies
- NWBConverter class with all interfaces
- `convert_session.py` with full pipeline
- Custom DataInterface classes where needed
- `metadata.yaml` with all collected metadata
- `convert_all_sessions.py` for batch conversion

**Stacked PRs mode**: commit the scaffold, session-level metadata, an NWBConverter with no
data interfaces, and the conversion scripts on `setup`. Then build one data stream at a time,
each on its own branch created from the previous one, starting with the timing reference
stream from Phase 4. Commit Step 9 per branch. See `knowledge/stacked-prs.md`.

### Step 1: Scaffold the Repository

All templates for the files below are in `knowledge/repo-structure.md`. Create the directory
structure from its Section 1 INSIDE the repo created in Phase 1
(`nwb-conversions/<lab-name>-to-nwb/`):

- `pyproject.toml`, `README.md`, `LICENSE` (MIT) and `.pre-commit-config.yaml` at the repo root
  (`.gitignore` exists from Phase 1)
- `src/<lab>_lab_to_nwb/<conversion_name>/` with the converter module, `convert_session.py`,
  `convert_all_sessions.py`, `metadata.yaml` and any custom interface modules
- `.github/workflows/` only if the user wants the package published to PyPI. Ask.

### Step 2: Write pyproject.toml

Use the template in Section 2 of `knowledge/repo-structure.md`. Add the NeuroConv extras for
the interfaces in the interface mapping and any packages the custom interfaces need.

### Step 3: Write the NWBConverter Class

Use the template in Section 3 of `knowledge/repo-structure.md`. List every interface from the
interface mapping in `data_interface_classes`, and put the sync plan from Phase 4 in
`temporally_align_data_interfaces()` (Section 8). When interfaces must be built before the
converter, or some data is added with PyNWB directly, use a pattern from
`knowledge/conversion-patterns.md`.

### Step 3a: Reuse NeuroConv Interfaces Before Writing Your Own

Code that calls existing NeuroConv interfaces is easier for reviewers to follow than custom
code. When a stock interface almost fits a data stream, adapt it in this order and stop at the
first option that works:

1. **Compose stock interfaces in the converter.** Use several instances of the same interface
   when one stream is split across files or segments (e.g. one `TDTFiberPhotometryInterface`
   per tank when Synapse was restarted mid-session, each with its own `metadata_key` and
   series name, shifted to the session clock in `temporally_align_data_interfaces`).
2. **Subclass the format-specific interface**, not its base class, and override only the
   smallest method that needs to change.
3. **Write a custom interface on a base class** (Step 4). Before doing so, record in
   `conversion_notes.md` which stock interface you considered and why options 1 and 2 do not
   work.

### Step 3b: Check Registry for Reusable Custom Interfaces

Before writing a custom interface from scratch, check the conversion registry for
similar custom interfaces from prior conversions. A prior interface that handles the
same data format or creates the same NWB types can serve as a starting template.

```python
import yaml

with open("/tmp/registry.yaml") as f:
    registry = yaml.safe_load(f)

# Search for conversions with custom interfaces that match what we need
needed_nwb_types = ["Position", "BehavioralEvents"]  # what our custom data maps to
for conv in registry.get("conversions", []):
    if not conv.get("has_custom_interfaces"):
        continue
    # The full manifest has custom_interfaces detail — fetch it from the repo
    print(f"Check {conv['repo']} for custom interfaces")
```

If a match is found, fetch the actual interface code from the prior repo via the API:
```bash
NWB_API="https://nwb-conversions-api.ben-dichter.workers.dev"
curl -sf "${NWB_API}/repos/<repo-name>/files/<path-to-interface>"
```

Use the fetched code as a starting template, adapting it to the current lab's file format
and column names. Give credit in a comment: `# Adapted from nwb-conversions/<repo-name>`.

If no match is found, write the custom interface from scratch (Step 4 below).

### Step 4: Write Custom DataInterface Classes

For each data stream that needs custom code, start from the template in Section 6 of
`knowledge/repo-structure.md`. Follow `knowledge/nwb-best-practices.md` in every custom
interface.

#### Custom Interface Guidelines

**Prefer raw acquisition data**: Custom interfaces should read data as close to the
original acquisition format as possible. If you're working with processed data because
raw files aren't available, document this in the interface docstring (e.g., "Reads
trialized behavior data from lab-processed .mat files. Raw SpikeGLX files were not
available."). When raw data IS available, always use the NeuroConv interface for that
acquisition system rather than writing a custom reader.

**Metadata responsibility**: A custom interface's `get_metadata()` should only return
metadata that can be extracted FROM THE DATA FILE ITSELF (e.g., session date from filename,
frame rate from timestamps). Lab-level metadata (institution, experimenter) and subject
metadata (species, genotype) should be handled in `convert_session.py` via metadata YAML
and subject metadata files. Do not duplicate metadata loading between the interface and
the conversion script.

**Use `conversion` parameter, not data transformation**: When data is in non-SI units
(e.g., centimeters), do NOT multiply the data by a conversion factor. Instead, use the
`conversion` parameter on TimeSeries:
```python
# CORRECT: store raw data, use conversion factor
TimeSeries(name="position", data=pos_cm, unit="m", conversion=0.01)

# WRONG: transform data in-place
TimeSeries(name="position", data=pos_cm * 0.01, unit="m")
```
This preserves original data values in the file and is more NWB-idiomatic.

**Pickle files load whole into memory.** Read them in `add_to_nwbfile()` (or in
`get_metadata()` if metadata is needed), not in `__init__()`.

**Choosing the right NWB types for custom data:**

Always use the most specific NWB type available — don't use bare `TimeSeries` when a
subtype exists.

| Data Type | NWB Container | Where to Add |
|-----------|---------------|--------------|
| Continuous neural signal | `ElectricalSeries` | `nwbfile.add_acquisition()` |
| Position (x, y) | `Position` > `SpatialSeries` | `processing["behavior"]` |
| Running speed | `TimeSeries` | `processing["behavior"]` |
| Lick times | `EventsTable` | `nwbfile.add_events_table()` |
| Trial info | `TimeIntervals` | `nwbfile.add_trial()` |
| Epochs | `TimeIntervals` | `nwbfile.add_epoch()` |
| Pupil tracking | `PupilTracking` > `TimeSeries` | `processing["behavior"]` |
| Eye position | `EyeTracking` > `SpatialSeries` | `processing["behavior"]` |
| Stimulus times | `TimeIntervals` | `nwbfile.add_stimulus()` |
| One-photon imaging (Miniscope, Inscopix) | `OnePhotonSeries` | `nwbfile.add_acquisition()` |
| Two-photon imaging (ScanImage, Scanbox, Bruker) | `TwoPhotonSeries` | `nwbfile.add_acquisition()` |
| Fluorescence traces | `RoiResponseSeries` | `processing["ophys"]` |
| ROI masks | `PlaneSegmentation` | `processing["ophys"]` |
| Reward events | `EventsTable` | `nwbfile.add_events_table()` |
| Animal video | `ImageSeries` (external_file) | `nwbfile.add_acquisition()` |
| Compass direction | `CompassDirection` > `SpatialSeries` | `processing["behavior"]` |
| Optogenetic stimulus | ndx-optogenetics `OptogeneticEpochsTable` or `OptogeneticPulsesTable` | `nwbfile.add_time_intervals()` |

**For detailed PyNWB construction patterns by domain, see:**
- `knowledge/pynwb-icephys.md` — intracellular electrophysiology
- `knowledge/ndx-optogenetics.md` — ndx-optogenetics extension (REQUIRED for optogenetics)
- `knowledge/pynwb-ophys-advanced.md` — advanced optical physiology (ROIs, segmentation, motion correction)
- `knowledge/pynwb-behavior.md` — behavior container types (PupilTracking, EyeTracking, etc.) and EventsTable
- `knowledge/pynwb-images.md` — image data and external video files
- `knowledge/pynwb-advanced-io.md` — compression, chunking, iterative write for large data
- `knowledge/ndx-fiber-photometry.md` — ndx-fiber-photometry extension (REQUIRED for fiber photometry)
- `knowledge/ndx-pose.md` — ndx-pose extension for pose estimation (DeepLabCut, SLEAP, Lightning Pose)
- `knowledge/ndx-anatomical-localization.md` — ndx-anatomical-localization for electrode/imaging plane atlas registration

If you are unsure whether a microscope is one-photon or two-photon, ask the user. Most imaging
interfaces write a `TwoPhotonSeries` unless the `photon_series_type` conversion option says
otherwise (Section 7 of `knowledge/repo-structure.md`).

**Key constraints on SpatialSeries:**
- Only for position data (x, y, z). Velocity and acceleration should use `TimeSeries`.
- Must have 1, 2, or 3 data columns (not more).
- When inside `CompassDirection`, units must be `"degrees"` or `"radians"`.
- When using degrees, data values should be in [-360, 360]; radians in [-2pi, 2pi].

When a dataset mixes behavioral and stimulus columns (common in VR experiments), separate
them. What the animal did (position, running speed, licks, eye and pupil tracking, pose) goes in
`processing["behavior"]`. Parameters the experimenter controls (visual contrast, orientation,
spatial frequency, environment morph, auditory and optogenetic stimulus parameters) go in
`nwbfile.add_stimulus()`. Reward delivery events are behavior; a reward parameter the
experimenter sets is stimulus.

**Use `get_module()` to get or create processing modules:**
```python
from neuroconv.tools.nwb_helpers import get_module
behavior_module = get_module(nwbfile, "behavior", "Processed behavioral data")
behavior_module.add(my_container)
```

**Compression and chunking:** pass plain arrays (or a `SliceableDataChunkIterator` for data larger
than memory) and do not wrap them in `H5DataIO`. `run_conversion` chunks and compresses every dataset.
To change those settings, see `knowledge/pynwb-advanced-io.md`.

### Step 5: Write convert_session.py

Use the template in Section 4 of `knowledge/repo-structure.md`. Add a `source_data` and
`conversion_options` entry for each interface, conditional on the files a session has, and fill
the per-session metadata (`session_id`, `subject_id`, timezone-aware `session_start_time`).

### Step 6: Write convert_all_sessions.py

Use the template in Section 5 of `knowledge/repo-structure.md` and write
`get_session_to_nwb_kwargs_per_session` for this dataset's session layout.

### Step 7: Write metadata.yaml

Write the metadata collected in Phase 3 in the format of Section 7 of
`knowledge/repo-structure.md`. For more than one subject, add the per-subject file described there.

### Step 8: Write README.md, LICENSE, and Supporting Files

Use Sections 9 and 10 of `knowledge/repo-structure.md`: the README, the MIT `LICENSE`,
`.pre-commit-config.yaml`, and the CI workflows if the user wants PyPI publishing.

### Step 9: Commit and Push to nwb-conversions

After all code is generated and the repo is scaffolded, commit everything and push to the
`nwb-conversions` GitHub org. The remote was configured in Phase 1.

```bash
git add -A
git commit -m "Add conversion code for <conversion_name>

Generated by nwb-convert skill. Includes:
- NWBConverter with <N> interfaces
- <N> custom DataInterface classes
- convert_session.py and convert_all_sessions.py
- metadata.yaml with lab and experiment metadata"
if git remote get-url origin &>/dev/null; then git push; fi
```

This makes the conversion code immediately available in the org for reference by future
conversions. The manifest will be added in Phase 8 after DANDI upload is complete.
