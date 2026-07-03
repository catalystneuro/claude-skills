## Phase 7: Testing & Validation

**Goal**: Verify the conversion produces valid NWB files that pass both NWB
Inspector and a Spyglass dry-run insertion check.

**Entry**: All conversion code from Phase 6 is written.

**Baseline**: Follow **nwb-convert Phase 6** for the full testing workflow. All steps
apply: stub test, NWB file inspection, NWB Inspector run with issue table, full
conversion run, data integrity validation, and the iterative fix cycle.

Key difference: skip `dandi validate` (not needed for Spyglass-only projects) and add
the Spyglass dry-run step (Step 5 below) after NWB Inspector passes.

**Exit criteria**: The conversion runs successfully, NWB Inspector shows zero
CRITICAL/BEST_PRACTICE_VIOLATION messages, and the Spyglass insertion dry-run
succeeds on a stub file.

### Step 1: Install the Package

```bash
source .venv/bin/activate
uv pip install -e ".[<conversion_name>]"
```

### Step 2: Run a Stub Test

```python
from <package>.<conversion>.convert_session import session_to_nwb

nwbfile_path = session_to_nwb(
    data_dir_path="/path/to/sample/session",
    output_dir_path="/path/to/output",
    stub_test=True,
)
```

Fix any import errors, file-not-found errors, or schema validation errors before
proceeding.

### Step 3: Inspect the NWB File

Verify all Spyglass-required fields are present:

```python
from pynwb import NWBHDF5IO
import pandas as pd

with NWBHDF5IO(nwbfile_path, "r") as io:
    nwbfile = io.read()

    print(f"Session: {nwbfile.session_description}")
    print(f"Start time: {nwbfile.session_start_time}")
    print(f"Subject: {nwbfile.subject}")

    # Check electrode table has all Spyglass columns
    elec_df = nwbfile.electrodes.to_dataframe()
    required_cols = ["probe_shank", "probe_electrode", "bad_channel",
                     "ref_elect_id", "group_name", "brain_area"]
    missing = [c for c in required_cols if c not in elec_df.columns]
    if missing:
        print(f"MISSING Spyglass electrode columns: {missing}")
    else:
        print("All Spyglass electrode columns present ✓")
    print(elec_df[required_cols].head())

    # Check ElectrodeGroup naming (must be nTrode{N})
    for name, group in nwbfile.electrode_groups.items():
        if not name.startswith("nTrode"):
            print(f"WARNING: ElectrodeGroup '{name}' does not follow nTrode{{N}} convention")
        else:
            print(f"ElectrodeGroup '{name}' ✓")

    # Check acquisition
    print(f"Acquisition: {list(nwbfile.acquisition.keys())}")

    # Check LFP placement
    ecephys_mod = nwbfile.processing.get("ecephys")
    if ecephys_mod:
        lfp = ecephys_mod.data_interfaces.get("LFP")
        print(f"LFP in processing['ecephys']['LFP']: {'✓' if lfp else 'MISSING'}")
    else:
        print("WARNING: No 'ecephys' processing module found")

    # Check video
    for name, acq in nwbfile.acquisition.items():
        from pynwb.image import ImageSeries
        if isinstance(acq, ImageSeries):
            print(f"Video '{name}': external_file={acq.external_file[:]}")
```

### Step 4: Run NWB Inspector

```bash
nwbinspector /path/to/output/nwb_stub/session.nwb
```

Fix all CRITICAL and BEST_PRACTICE_VIOLATION messages. For the full table of
inspector message codes and their fixes (session_start_time, subject fields,
data orientation, timestamps, electrode location, etc.), follow
**nwb-convert Phase 6 Step 4** — the complete table applies unchanged here.

### Step 5: Spyglass Dry-Run Insertion Check

Before inserting into the live database, test that Spyglass can parse the NWB file
without errors. Use `rollback_on_fail=True` so any partial inserts are rolled back:

```python
import datajoint as dj
import spyglass.data_import as sgi

dj.config.load("dj_local_conf.json")

nwbfile_path = "/path/to/output/nwb_stub/session.nwb"

try:
    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=True, raise_err=True)
    print("Dry-run insertion succeeded ✓")
except Exception as e:
    print(f"Insertion failed: {e}")
```

**Common insertion failures and fixes:**

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `KeyError: 'probe_shank'` | Missing electrode column | Add column in `_add_spyglass_electrode_columns()` |
| `IntegrityError` on ElectrodeGroup | Name not in `nTrode{N}` format | Fix in `get_metadata()` override |
| `KeyError: 'LFP'` in ecephys processing | LFP not in expected location | Move LFP to `processing["ecephys"]["LFP"]` |
| `ValueError` on video | VideoInterface used instead of ImageSeries | Replace with `ImageSeries(external_file=[...])` |
| `DataJointError: Duplicate entry` | Session already partially inserted | Run `clean_db_entry()` to remove prior records |

After fixing, re-run the stub test, re-run nwbinspector, re-run the dry-run check.
Iterate until all three pass cleanly.

### Step 6: Full Conversion (One Session)

Once stub tests pass, run a full conversion:

```python
nwbfile_path = session_to_nwb(
    data_dir_path="/path/to/sample/session",
    output_dir_path="/path/to/output",
    stub_test=False,
)
```

Run nwbinspector again on the full file. Some issues only appear with real data.

### Push Phase 7 Results

```bash
git add -A
git commit -m "Phase 7: testing passed — NWB Inspector clean, Spyglass dry-run OK"
```
