## Phase 8: Session Insertion

**Goal**: Insert the converted NWB file into the Spyglass database and verify
the insertion succeeded.

**Entry**: A full NWB file has passed Phase 7 validation.

**Exit criteria**: The session is inserted into Spyglass with no errors. Key
tables (Session, Electrode, Raw, LFP) have rows matching this session.
**`insert_session.py` exists in the conversion folder and is the canonical
way to reproduce insertion.**

> **Do not skip `insert_session.py`.** It is not optional boilerplate — it is
> the reproducible record of exactly how sessions were inserted. Without it,
> insertion steps cannot be reproduced or handed off. Create it in the
> conversion folder before running insertion, not after.

---

### Step 0: Copy NWB File to Spyglass Raw Directory

Spyglass expects NWB files in the `raw` subdirectory of its base directory.
Copy (do not move) the file:

```bash
SPYGLASS_RAW="<spyglass_base_dir>/raw"
cp /path/to/output/session.nwb "${SPYGLASS_RAW}/"
ls -lh "${SPYGLASS_RAW}/session.nwb"
```

---

### Step 1: Write `insert_session.py`

**Create `insert_session.py` in the conversion directory before running
insertion.** This file must be committed alongside the conversion code.

#### Import order and config loading

Two rules that break insertion when violated:

1. `dj.conn()` must be called **before** `dj.config.load()` (kind-lab pattern)
2. `dj.config.load()` must be called **before** any `spyglass` import
   (spyglass executes `dj.schema()` at module load time)

```python
import datajoint as dj

dj.conn(use_tls=False)  # needed for Docker setups without TLS; safe to include always

dj_local_conf_path = "/absolute/path/to/dj_local_conf.json"
dj.config.load(dj_local_conf_path)

# Optional: persist config so other scripts in this directory don't need to load it
dj.config.save_local()   # writes .datajoint_config.json in CWD
# dj.config.save_global()  # saves to ~/.datajoint_config.json — use only if intentional
```

#### Minimal template (behavior-only, no ephys/LFP)

Use this as the base; add ephys, LFP, and sorting blocks below as needed.

```python
"""Insert a converted NWB session into the Spyglass database."""

from pathlib import Path

import datajoint as dj

dj.conn(use_tls=False)

dj_local_conf_path = "/absolute/path/to/dj_local_conf.json"
dj.config.load(dj_local_conf_path)

import spyglass.common as sgc
import spyglass.data_import as sgi
from spyglass.utils.nwb_helper_fn import get_nwb_copy_filename

SPYGLASS_RAW_DIR = Path("<spyglass_base_dir>/raw")


def log_table(table, restriction=True) -> str:
    """Return a formatted string for one table."""
    return f"=== {table.__name__} ===\n{table & restriction}\n"


def print_tables(nwbfile_path: Path):
    """Print key Spyglass tables to stdout and tables.txt."""
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    nwb_dict = {"nwb_file_name": nwb_copy_file_name}
    probe_ids = (sgc.ElectrodeGroup & nwb_dict).fetch("probe_id", as_dict=True)
    camera_names = (sgc.VideoFile & nwb_dict).fetch("camera_name", as_dict=True)

    table_list = [
        (sgc.Nwbfile,               nwb_dict),
        (sgc.Session,               nwb_dict),
        (sgc.DataAcquisitionDevice, nwb_dict),
        (sgc.Raw,                   nwb_dict),
        (sgc.DIOEvents,             nwb_dict),
        (sgc.Probe,                 probe_ids),
        (sgc.Probe.Shank,           probe_ids),
        (sgc.Probe.Electrode,       probe_ids),
        (sgc.ElectrodeGroup,        nwb_dict),
        (sgc.Electrode,             nwb_dict),
        (sgc.CameraDevice,          camera_names),
        (sgc.Task,                  True),
        (sgc.TaskEpoch,             nwb_dict),
        (sgc.IntervalList,          nwb_dict),
        (sgc.VideoFile,             nwb_dict),
        (sgc.SensorData,            nwb_dict),
    ]
    output = "\n".join(log_table(t, r) for t, r in table_list)
    print(output)
    (Path(__file__).parent / "tables.txt").write_text(output)


def clean_db_entry(nwbfile_path: Path):
    """Remove all Spyglass entries for a session. Safe to call before re-inserting."""
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    nwb_dict = {"nwb_file_name": nwb_copy_file_name}
    (sgc.Nwbfile & nwb_dict).delete(safemode=False)


def main():
    nwbfile_path = SPYGLASS_RAW_DIR / "<session>.nwb"

    clean_db_entry(nwbfile_path)

    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=True, raise_err=True)

    print_tables(nwbfile_path)


if __name__ == "__main__":
    main()
    print("Done!")
```

---

### Step 2: Add LFP Insertion (if session has LFP)

If the NWB file has LFP in `processing["ecephys"]["LFP"]`, insert it as a
separate step **after** `insert_sessions()`. The jadhav-lab and kind-lab
patterns both use a dedicated `insert_lfp()` function for this.

Add to `insert_session.py`:

```python
import spyglass.lfp as sglfp

def insert_lfp(nwbfile_path: Path):
    """Insert LFP data. NWB file must have LFP in processing['ecephys']['LFP']."""
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    nwb_dict = {"nwb_file_name": nwb_copy_file_name}

    # Create an LFP electrode group covering all electrodes
    lfp_electrode_group_name = "lfp_electrode_group"
    sglfp.LFPElectrodeGroup.create_group(
        nwb_file_name=nwb_copy_file_name,
        group_name=lfp_electrode_group_name,
        electrode_list=(sgc.Electrode & nwb_dict).fetch("electrode_id").tolist(),
    )
    # Import LFP from the NWB file
    lfp_key = {
        "nwb_file_name": nwb_copy_file_name,
        "lfp_electrode_group_name": lfp_electrode_group_name,
        "target_interval_list_name": "raw data valid times",
    }
    sglfp.ImportedLFP.populate(lfp_key)
```

Update `print_tables()` to include LFP tables:

```python
import spyglass.lfp as sglfp

# Add to table_list in print_tables():
(sglfp.lfp_electrode.LFPElectrodeGroup, nwb_dict),
(sglfp.ImportedLFP,                     nwb_dict),
(sglfp.lfp_merge.LFPOutput,             nwb_dict),
```

Update `main()` to call it:

```python
def main():
    nwbfile_path = SPYGLASS_RAW_DIR / "<session>.nwb"

    clean_db_entry(nwbfile_path)

    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=True, raise_err=True)
    insert_lfp(nwbfile_path)

    print_tables(nwbfile_path)
```

---

### Step 3: Add Spike Sorting Insertion (if applicable)

If the NWB file contains sorted spikes (a `units` table), use the
`SpikeSortingOutput.ImportedSpikeSorting` path. See jadhav-lab's
`insert_sorting()` for the full pattern:

```python
from spyglass.spikesorting.spikesorting_merge import SpikeSortingOutput
import spyglass.spikesorting.v1 as sgs
from spyglass.spikesorting.analysis.v1.group import SortedSpikesGroup, UnitSelectionParams
from spyglass.spikesorting.analysis.v1.unit_annotation import UnitAnnotation

def insert_sorting(nwbfile_path: Path):
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    merge_id = str(
        (SpikeSortingOutput.ImportedSpikeSorting & {"nwb_file_name": nwb_copy_file_name}).fetch1("merge_id")
    )
    UnitSelectionParams().insert_default()
    SortedSpikesGroup().create_group(
        group_name="all_units",
        nwb_file_name=nwb_copy_file_name,
        keys=[{"spikesorting_merge_id": merge_id}],
    )
```

---

### Step 4: Pre-seed Lookup Tables (if insertion fails with `input()` prompts)

Spyglass will call `input()` interactively when it encounters a device type,
probe type, or camera not yet in the database. This breaks non-interactive
scripts. If insertion fails this way, pre-insert the missing entries:

```python
def seed_lookup_tables():
    """Pre-insert lookup table entries to avoid interactive prompts.
    Values must exactly match what is in the NWB file.
    """
    # Ephys device
    sgc.DataAcquisitionDeviceSystem.insert1(
        {"data_acquisition_device_system": "<system>"},  # e.g. "SpikeGadgets"
        skip_duplicates=True,
    )
    sgc.DataAcquisitionDeviceAmplifier.insert1(
        {"data_acquisition_device_amplifier": "<amplifier>"},  # e.g. "Intan"
        skip_duplicates=True,
    )
    sgc.DataAcquisitionDevice.insert1(
        {
            "data_acquisition_device_name": "<name>",
            "data_acquisition_device_system": "<system>",
            "data_acquisition_device_amplifier": "<amplifier>",
            "adc_circuit": "<adc_circuit>",
        },
        skip_duplicates=True,
    )
    sgc.ProbeType.insert1(
        {
            "probe_type": "<probe_type>",
            "probe_description": "<desc>",
            "manufacturer": "<manufacturer>",  # may be "" — check NWB file
            "num_shanks": <num_shanks>,
        },
        skip_duplicates=True,
    )
    # Camera (omit if no video)
    sgc.CameraDevice.insert1(
        {
            "camera_name": "<camera_name>",
            "meters_per_pixel": <meters_per_pixel>,
            "manufacturer": "<manufacturer>",
            "model": "<model>",
            "lens": "<lens>",
            "camera_id": <camera_id>,
        },
        skip_duplicates=True,
    )
```

To read the exact values from the NWB file before filling these in:

```python
import ndx_franklab_novela  # must import before NWBHDF5IO
from pynwb import NWBHDF5IO

with NWBHDF5IO("/path/to/session.nwb", "r", load_namespaces=True) as io:
    nwb = io.read()
    probe = nwb.devices.get("tetrode_array")
    if probe:
        print("probe_type:", probe.probe_type)
        print("manufacturer:", probe.manufacturer)
    daq = nwb.devices.get("SpikeGadgets")
    if daq:
        print("system:", daq.system)
        print("amplifier:", daq.amplifier)
        print("adc_circuit:", daq.adc_circuit)
```

Call `seed_lookup_tables()` at the top of `main()`, before `insert_sessions()`.
All entries use `skip_duplicates=True` so it is safe to call on every run.

---

### Step 5: Add Test Functions (Recommended)

After insertion succeeds, add test functions that compare NWB file content
against the database to verify data integrity. Modelled on jadhav-lab's pattern:

```python
import numpy as np
from pynwb import NWBHDF5IO

def test_ephys(nwbfile_path: Path):
    """Verify raw electrical series matches between NWB file and database."""
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    electrical_series = (sgc.Raw & {"nwb_file_name": nwb_copy_file_name}).fetch_nwb()[0]["raw"]
    spyglass_data = np.asarray(electrical_series.data[:100])
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwb_data = np.asarray(io.read().acquisition["ElectricalSeries"].data[:100])
    np.testing.assert_array_equal(spyglass_data, nwb_data)
    print("test_ephys: PASSED")


def test_lfp(nwbfile_path: Path):
    """Verify LFP data matches between NWB file and database."""
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    lfp_es = (sglfp.ImportedLFP & {"nwb_file_name": nwb_copy_file_name}).fetch_nwb()[0]["lfp"]
    spyglass_data = np.asarray(lfp_es.data[:100])
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwb_data = np.asarray(
            io.read().processing["ecephys"]["LFP"].electrical_series["ElectricalSeriesLFP"].data[:100]
        )
    np.testing.assert_array_equal(spyglass_data, nwb_data)
    print("test_lfp: PASSED")


def test_video(nwbfile_path: Path):
    """Verify video external_file path matches between NWB file and database."""
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    image_series = (sgc.VideoFile & {"nwb_file_name": nwb_copy_file_name}).fetch_nwb()[0]["video_file"]
    spyglass_external_file = image_series.external_file[0]
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwb_external_file = list(io.read().acquisition.values())[0].external_file[0]
    assert spyglass_external_file == nwb_external_file
    print("test_video: PASSED")
```

Add these calls to `main()` after `print_tables()`:

```python
test_ephys(nwbfile_path)
test_lfp(nwbfile_path)
test_video(nwbfile_path)
```

---

### Step 6: Shared `spyglass_utils.py` for Multi-Session Projects

When a conversion project has multiple sessions or multiple modalities with
separate `insert_session.py` files, extract shared helpers into a package-level
`spyglass_utils.py`. Both kind-lab conversions use this pattern:

```
src/<lab>_to_nwb/
    spyglass_utils.py       ← shared: clean_db_entry, print_tables, insert_lfp
    <conversion_1>/
        insert_session.py   ← imports from spyglass_utils
    <conversion_2>/
        insert_session.py   ← imports from spyglass_utils
```

```python
# In insert_session.py:
from <lab>_to_nwb.spyglass_utils import clean_db_entry, print_tables, insert_lfp
```

---

### Step 7: Run the Insertion

```bash
source .venv/bin/activate
python src/<lab_name>_to_nwb/<conversion_name>/insert_session.py
```

Common failures:

- **`rollback_on_fail=True` triggers**: Insertion partially completed then rolled
  back. Check the traceback for the failing table. Fix the NWB file, re-run with
  `clean_db_entry()` called first.
- **`input()` prompt appears**: A lookup table entry is missing. Add it via
  `seed_lookup_tables()` (Step 4) and re-run.
- **Missing LFP**: If `ImportedLFP` is empty, verify LFP is in
  `processing["ecephys"]["LFP"]` in the NWB file.
- **Video path error**: Spyglass checks that `external_file` paths in `ImageSeries`
  are accessible. Verify relative paths are correct from the Spyglass raw directory.
- **`nan` in probe table**: DataJoint translates `float('nan')` to the literal SQL
  identifier `nan`. Use `None` instead for any nullable probe fields.

---

### Debugging: Explore Downstream Tables with `RestrGraph`

After insertion, use `RestrGraph` to discover all tables populated downstream of
the session:

```python
from spyglass.utils.dj_graph import RestrGraph

rg = RestrGraph(
    seed_table=sgc.Nwbfile,
    leaves=dict(
        table_name=sgc.Nwbfile.full_table_name,
        restriction=f'nwb_file_name="{nwb_copy_file_name}"',  # must be a string
    ),
    direction="down",   # 'down' = all descendants
    verbose=True,
    cascade=True,
)
rg.restr_ft  # list of all populated tables connected to this session
```

---

### Commit Phase 8 Results

```bash
git add insert_session.py tables.txt
git commit -m "Phase 8: add insert_session.py — session inserted successfully"
```
