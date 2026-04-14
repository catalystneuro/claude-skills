# Spyglass NWB Requirements

This file documents the specific structural requirements that an NWB file must
satisfy for successful ingestion into a Spyglass database. These requirements
are beyond standard NWB validity — a file can pass NWB Inspector and still fail
Spyglass insertion if these are missing.

## Required Electrode Table Columns

The `electrodes` table in the NWB file MUST contain these extra columns in
addition to the standard NWB columns. Spyglass will raise a `KeyError` during
ingestion if any are missing.

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| `probe_shank` | int or str | Shank identifier | Must match the `Shank.name` in the probe hierarchy — int 0 for single-shank tetrodes; str channel index for multi-shank silicon probes |
| `probe_electrode` | int | Electrode index within shank | 0..N-1 per shank |
| `bad_channel` | bool | Whether channel is marked bad | Usually all False |
| `ref_elect_id` | int | Index of reference electrode | Can be self-referential |
| `brain_area` | str | Anatomical region | Use "unknown" if not determined |

**Columns you do NOT need to add explicitly:**
- `group_name`: NWB auto-populates this from `group=electrode_group` in `add_electrode()`. Do not add it as an extra column — it will cause a duplicate.

**Recommended additional columns** (used by jadhav-lab, improve Spyglass compatibility):

| Column | Type | Description |
|--------|------|-------------|
| `hasLFP` | bool | Whether this channel has a corresponding LFP channel. Spyglass's `LFPElectrodeGroup` may use this to identify LFP channels. |
| `chID` | str | String identifier like `"nTrode1_elec2"`. Used by some Spyglass versions for channel matching. |

Add these via `recording_extractor.set_property()` (for NeuroConv-based conversions)
or via `nwbfile.add_electrode_column()` + `nwbfile.add_electrode()` (for manual conversions)
BEFORE writing the NWB file.

## ElectrodeGroup Naming Convention

The `nTrode{N}` convention (1-indexed, e.g. `nTrode1`, `nTrode2`, ..., `nTrode16`)
is the standard Spyglass naming scheme and is required for **SpikeGadgets / tetrode
recordings** where Spyglass has hardcoded assumptions about this naming pattern.

For **silicon probe / OpenEphys recordings**, brain-area-based names (e.g.
`"infralimbic_R"`, `"CA1_L"`) have been used successfully in kind-lab. Whether
`nTrode{N}` is enforced depends on the specific Spyglass code paths your data
triggers — when in doubt, use `nTrode{N}`.

**For SpikeGadgets recordings:** if the NeuroConv interface generates different
group names (e.g., `"0"`, `"group0"`, `"shank0"`, `"tetrode0"`), override
`get_metadata()` in the converter:

```python
def get_metadata(self):
    metadata = super().get_metadata()
    for i, group in enumerate(metadata["Ecephys"]["ElectrodeGroup"]):
        group["name"] = f"nTrode{i + 1}"
    return metadata
```

After renaming, verify that `electrodes["group_name"]` still matches the renamed
groups. The electrode table is built from metadata, so renaming groups in metadata
should propagate automatically — but check.

## LFP Placement

Spyglass expects LFP to be in:
```
nwbfile.processing["ecephys"]["LFP"]
```
specifically as an `LFP` container inside an `ecephys` processing module,
with an `ElectricalSeries` inside it.

**Path A — writing LFP manually (OpenEphys, TDT, custom interfaces):**
Write directly to `processing["ecephys"]` from the start. No post-processing needed:

```python
from pynwb.ecephys import ElectricalSeries, LFP

lfp_electrical_series = ElectricalSeries(
    name="lfp_series",
    data=lfp_traces,
    electrodes=lfp_electrodes,
    rate=rate,
    starting_time=starting_time,
)
lfp = LFP(electrical_series=lfp_electrical_series)
ecephys_module = nwbfile.create_processing_module(name="ecephys", description="ecephys module")
ecephys_module.add(lfp)
```

**Path B — using a NeuroConv LFP interface (SpikeGLX, OpenEphys, Intan, etc.):**
Any NeuroConv interface that inherits from `BaseLFPExtractorInterface` — including
`SpikeGLXLFPInterface`, `OpenEphysLFPInterface`, `IntanLFPInterface`, and others —
defaults to `write_as="lfp"`. This already writes to `processing["ecephys"]["LFP"]` — no
post-processing or "move" step is needed. All such interfaces are Spyglass-compatible
on LFP placement out of the box.

## Video Requirements

Spyglass requires THREE things beyond a bare `ImageSeries`:

1. **`CameraDevice` from `ndx_franklab_novela`** (not a plain `Device`). Spyglass
   reads this to populate its `CameraDevice` table.

2. **`ImageSeries` with `device=camera_device`** — explicitly link the `ImageSeries`
   to the `CameraDevice`. Without this, Spyglass cannot map video files to cameras.

3. **A `"tasks"` processing module with a `task_table` `DynamicTable`** — Spyglass
   populates `Task` and `TaskEpoch` from this. Must always exist, even when the
   session has no distinct behavioral epochs (create one row covering the whole session).

**Do NOT use `VideoInterface` from NeuroConv** — it does not create these required objects.

Use `utils/add_behavioral_video.py` (see Phase 6) which handles all of this.

**`task_table` required columns:** `task_name`, `task_description`, `camera_id`, `task_epochs`

```python
from pynwb.core import DynamicTable
from ndx_franklab_novela import CameraDevice
from pynwb.image import ImageSeries

camera_device = CameraDevice(
    name="camera_device 0",
    meters_per_pixel=0.001,
    model="Mako G-158C",
    lens="Theia SL183M",
    camera_name="SleepBox",
    # manufacturer is optional in the ndx extension
)
nwbfile.add_device(camera_device)

tasks_module = nwbfile.create_processing_module(name="tasks", description="tasks module")
task_table = DynamicTable(name="task_table", description="task metadata for Spyglass")
task_table.add_column(name="task_name",        description="Name of the task.")
task_table.add_column(name="task_description", description="Description of the task.")
task_table.add_column(name="camera_id",        description="Camera ID(s).")
task_table.add_column(name="task_epochs",      description="Epoch numbers for this task.")
task_table.add_row(
    task_name="Sleep",
    task_description="...",
    camera_id=[0],
    task_epochs=[1, 2],
)
tasks_module.add(task_table)

image_series = ImageSeries(
    name="Video_epoch1",
    description="Behavioral video.",
    unit="n.a.",
    external_file=["/path/to/video.mp4"],
    format="external",
    timestamps=timestamps,
    device=camera_device,   # ← required link to CameraDevice
)
nwbfile.add_acquisition(image_series)
```

> **`camera_id` for sessions without video**: Use `np.array([], dtype=np.int32)` (not
> an empty Python list `[]`). Spyglass checks `if len(camera_ids) > 0:`, which works
> on numpy arrays but `if camera_ids:` raises `ValueError` on a numpy empty array.

> **`CameraDevice` in NWB file devices**: Spyglass's `TaskEpoch.make()` looks for
> `CameraDevice` objects in `nwbfile.devices` to map `camera_id` → `camera_name`.
> If CameraDevice is only pre-seeded in the DataJoint DB (not in the NWB file),
> TaskEpoch will warn "No camera device found" and set `camera_names=[]`.
> For full VideoFile population, you must include the `CameraDevice` in the NWB file.

## DataAcquisitionDevice

Spyglass requires `ndx_franklab_novela.DataAcqDevice` (not a plain `Device`).
It has three fields beyond the standard NWB `Device`:

```python
import ndx_franklab_novela

device = ndx_franklab_novela.DataAcqDevice(
    name="SpikeGadgets",           # recording system name
    system="SpikeGadgets",         # e.g., "SpikeGadgets", "OpenEphys", "Intan"
    amplifier="Intan",             # amplifier chip/board
    adc_circuit="Intan",           # ADC circuit description
)
nwbfile.add_device(device)
```

Use `utils/add_ecephys.py:add_ecephys_devices()` to handle this (see Phase 6).
Set `system`, `amplifier`, and `adc_circuit` from the lab's recording hardware.
If unknown, use `"unknown"` as the value.

## DIO Events

For Spyglass to populate the `DIOEvents` table, digital input/output event times
should be stored in a way Spyglass can find. The standard approach is:

```python
from pynwb.misc import TimeSeries

events = TimeSeries(
    name="dio_<channel_name>",
    data=event_values,        # typically 0/1 or on/off times
    timestamps=event_times,   # in seconds
    description="DIO events for <channel description>",
    unit="n.a.",
)
behavior_module = get_module(nwbfile, "behavior", "Behavioral data")
behavior_module.add(events)
```

Check the Spyglass documentation for the exact expected container name and
location, as this may vary between Spyglass versions.

## Epochs / Task Structure

Spyglass populates `Task` and `TaskEpoch` from NWB epochs. Use
`nwbfile.add_epoch()` with `tags` set to a zero-padded epoch number string:

```python
nwbfile.add_epoch(start_time=0.0,   stop_time=600.0,  tags=["01"])   # epoch 1
nwbfile.add_epoch(start_time=600.0, stop_time=1800.0, tags=["02"])   # epoch 2
```

**The `tags` value becomes `interval_list_name` in `TaskEpoch`.** Both
jadhav-lab and kind-lab use this zero-padded string format (e.g. `"01"`, `"02"`).
Spyglass uses this to match epochs to the `task_epochs` list in `task_table`.

The `task_epochs` column in `task_table` should contain the corresponding integer
epoch numbers (e.g. `[1, 2]` for epochs tagged `"01"` and `"02"`).

## Probe Hierarchy and FK Constraints

Spyglass's `common_ephys._electrode` table has a FK constraint to
`common_device.probe__electrode` via `(probe_id, probe_shank, probe_electrode)`.
The Probe hierarchy in the NWB file must match the Electrode table values exactly.
The key rule: **`probe_shank` in the Electrode table must match `Shank.name` in the Probe hierarchy.**

### Pattern A: Tetrode arrays (SpikeGadgets / jadhav-lab pattern)

One physical probe, one shank (4 contacts). All electrodes get `probe_shank=0`.

```python
# Electrode table: probe_shank=0, probe_electrode=0..3 for ALL tetrodes
shanks_electrodes = [
    ShanksElectrode(name=str(ch), rel_x=0.0, rel_y=0.0, rel_z=0.0)
    for ch in range(4)
]
shanks = [Shank(name="0", shanks_electrodes=shanks_electrodes)]
probe = Probe(name="tetrode_array", shanks=shanks, ...)

# WRONG: one Shank per tetrode — probe_shank would need to be tetrode index, not 0
# shanks = [Shank(name=str(trode_id), ...) for trode_id in unique_trodes]
```

The Probe hierarchy describes PHYSICAL hardware geometry.
For a tetrode array, one physical probe has one shank with 4 contacts.
`ElectrodeGroup` (one per tetrode) describes which tetrode is recording — NOT
the same as a Shank.

### Pattern B: Multi-site silicon probes (OpenEphys / kind-lab pattern)

One probe, one Shank per electrode channel. `probe_shank` = channel index as string.

```python
for ch in range(n_channels):
    electrode = ShanksElectrode(name=str(ch), rel_x=0.0, rel_y=0.0, rel_z=0.0)
    shank = Shank(name=str(ch), shanks_electrodes=[electrode])
    probe.add_shank(shank)

nwbfile.add_electrode(
    ...
    probe_shank=str(ch),   # matches Shank.name above
    probe_electrode=ch,    # electrode index within shank (only one per shank here)
)
```

**Never use `float("nan")` for `contact_size`**: DataJoint translates `nan` to the
literal SQL identifier `nan` in WHERE clauses, producing
`UnknownAttributeError: Unknown column 'nan'`. Use `None` instead.

## ndx_franklab_novela Dependency

All of the Spyglass-specific NWB types come from this package:

```bash
uv pip install ndx-franklab-novela
```

| Type | Purpose |
|------|---------|
| `DataAcqDevice` | Recording system device (replaces plain `Device`) |
| `CameraDevice` | Behavioral camera (required for video + Spyglass VideoFile table) |
| `Probe` | Probe hardware container |
| `Shank` | Shank within a probe |
| `ShanksElectrode` | Individual electrode on a shank |
| `NwbElectrodeGroup` | Electrode group with stereotaxic targeting info (replaces plain `ElectrodeGroup`) |

**`CameraDevice` field notes:**
- Required: `name`, `meters_per_pixel`, `model`, `lens`, `camera_name`
- `manufacturer` is optional in the ndx extension
- `name` must be formatted as `"camera_device {id}"` (e.g., `"camera_device 0"`) for Spyglass to populate the VideoFile table correctly

**`NwbElectrodeGroup` is required**, not optional. Using a plain `pynwb.device.ElectrodeGroup` will cause insertion to fail because Spyglass reads the ndx-specific fields (e.g., `targeted_location`, stereotaxic coordinates) from it.

## Pose Estimation (ndx-pose)

Spyglass has an `ImportedPose` table (`spyglass.position.v1.imported_pose`) that
reads `ndx_pose.PoseEstimation` objects directly from `nwb.processing["behavior"]`.
**ndx-pose format is Spyglass-compatible** — no structural changes to the NWB file
are needed beyond what the NeuroConv DLC/SLEAP interfaces already produce.

**Key facts:**
- `ImportedPose` iterates `nwb.processing["behavior"]` and finds objects that are
  `isinstance(obj, ndx_pose.PoseEstimation)` — so any `PoseEstimation` container
  placed in the behavior processing module will be found.
- Insertion is a **separate step** from `insert_sessions()`, analogous to `insert_lfp()`.
  Call `ImportedPose.make(key)` after the session is inserted.
- Spyglass's `common_position.py` (LED-based tracking) does NOT read ndx-pose data —
  it reads `SpatialSeries` from `processing["behavior"]["Position"]`. These are two
  separate position tracking paths in Spyglass.

```python
from spyglass.position.v1 import ImportedPose

nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
ImportedPose.make({"nwb_file_name": nwb_copy_file_name})
```

**NeuroConv DLC/SLEAP interfaces** (`DeepLabCutInterface`, `SLEAPInterface`,
`LightningPoseInterface`) all write ndx-pose format to `processing["behavior"]` by
default — they are Spyglass-compatible on pose placement out of the box.

## Known Incompatible NeuroConv Interfaces

| Interface | Issue | Workaround |
|-----------|-------|------------|
| `VideoInterface` | Does not create `CameraDevice` or `task_table` | Use `utils/add_behavioral_video.py` |

Always test interface output against Spyglass with a stub file before committing
to a final conversion approach.
