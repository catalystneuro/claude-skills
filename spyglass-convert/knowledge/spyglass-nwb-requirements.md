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
| `probe_shank` | int | Shank index (0-indexed) | All 0 for single-shank probes |
| `probe_electrode` | int | Electrode index within shank | Usually 0..N-1 per shank |
| `bad_channel` | bool | Whether channel is marked bad | Usually all False |
| `ref_elect_id` | int | Index of reference electrode | Can be self-referential |
| `group_name` | str | Parent group name | Must match nTrode{N} convention |
| `brain_area` | str | Anatomical region | Use "unknown" if not determined |

Add these in the NWBConverter's `add_to_nwbfile()` method AFTER calling
`super().add_to_nwbfile()` (so the base electrode table exists first).

## ElectrodeGroup Naming Convention

Spyglass hardcodes the assumption that ElectrodeGroup names follow the pattern
`nTrode{N}` (1-indexed). Examples: `nTrode1`, `nTrode2`, ..., `nTrode16`.

**If the NeuroConv interface generates different group names** (e.g., "0", "group0",
"shank0", "tetrode0"), override `get_metadata()` in the converter:

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
with an `ElectricalSeries` inside it named `LFP` (or similar).

The standard NeuroConv `SpikeGLXLFPInterface` places LFP in `acquisition` by
default, NOT in `processing["ecephys"]`. You must override this placement in
the converter:

```python
def add_to_nwbfile(self, nwbfile, metadata, **kwargs):
    # Run all interfaces normally
    super().add_to_nwbfile(nwbfile, metadata, **kwargs)

    # Move LFP from acquisition to processing["ecephys"]["LFP"]
    from pynwb.ecephys import LFP
    from neuroconv.tools.nwb_helpers import get_module

    if "LFP" in nwbfile.acquisition:
        lfp_series = nwbfile.acquisition.pop("LFP")
        ecephys_module = get_module(nwbfile, "ecephys", "Processed ecephys data")
        lfp_container = LFP(name="LFP", electrical_series=lfp_series)
        ecephys_module.add(lfp_container)
```

Alternatively, configure the LFP interface to write to processing directly by
checking if `SpikeGLXLFPInterface` supports a `write_as` parameter.

## Video Requirements

Spyglass requires TWO things beyond a bare `ImageSeries`:

1. **`CameraDevice` from `ndx_franklab_novela`** (not a plain `Device`). Spyglass
   reads the `ndx_franklab_novela.CameraDevice` to populate its `CameraDevice` table.

2. **A `"tasks"` processing module with a `task_table` `DynamicTable`** — Spyglass
   populates `Task` and `TaskEpoch` tables from this. It must always exist, even when
   the session has no distinct behavioral epochs (create one row covering the whole session).

**Do NOT use `VideoInterface` from NeuroConv** — it does not create these required objects.

Use `utils/add_behavioral_video.py` (see Phase 6) which handles all of this.
The `task_table` must have columns: `task_name`, `task_description`, `camera_id`,
`task_epochs`.

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

Spyglass populates `Task` and `TaskEpoch` tables from `TimeIntervals` in the
NWB file. Standard approach:

```python
nwbfile.add_epoch(start_time=0.0, stop_time=600.0, tags=["sleep"])
nwbfile.add_epoch(start_time=600.0, stop_time=1800.0, tags=["run"])
```

Or use `nwbfile.add_trial()` for trial-based data.

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

## Known Incompatible NeuroConv Interfaces

| Interface | Issue | Workaround |
|-----------|-------|------------|
| `VideoInterface` | Does not create `CameraDevice` or `task_table` | Use `utils/add_behavioral_video.py` |
| `SpikeGLXLFPInterface` (default) | Places LFP in `acquisition`, not `processing["ecephys"]` | Call `move_lfp_to_ecephys_processing()` from `utils/add_ecephys.py` |

Always test interface output against Spyglass with a stub file before committing
to a final conversion approach.
