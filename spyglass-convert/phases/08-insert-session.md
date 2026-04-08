## Phase 8: Session Insertion

**Goal**: Insert the converted NWB file into the Spyglass database and verify
the insertion succeeded.

**Entry**: A full NWB file has passed Phase 7 validation.

**Exit criteria**: The session is inserted into Spyglass with no errors. Key
tables (Session, Electrode, Raw, LFP) have rows matching this session.

### Step 1: Copy NWB File to Spyglass Raw Directory

Spyglass expects NWB files in the `raw` subdirectory of its base directory.
Copy (do not move) the file:

```bash
SPYGLASS_RAW="<spyglass_base_dir>/raw"
cp /path/to/output/session.nwb "${SPYGLASS_RAW}/"
```

Verify the file is in place:
```bash
ls -lh "${SPYGLASS_RAW}/session.nwb"
```

### Step 2: Write insert_session.py

Create `insert_session.py` in the conversion directory:

```python
"""Insert a converted NWB session into the Spyglass database."""

from pathlib import Path
import datajoint as dj
import spyglass.data_import as sgi
import spyglass.common as sgc


def get_nwb_copy_filename(nwb_file_name: str) -> str:
    """Return the Spyglass internal filename for a given NWB file.
    Spyglass appends '_' to the stem when creating its own copy.
    """
    stem = Path(nwb_file_name).stem
    return f"{stem}_.nwb"


def clean_db_entry(nwb_file_name: str):
    """Remove existing database entries for a session.

    Use this before re-inserting a session to avoid duplicate key errors.
    Deletes in reverse dependency order so foreign key constraints are satisfied.
    """
    copy_file_name = get_nwb_copy_filename(nwb_file_name)
    restriction = {"nwb_file_name": nwb_file_name}
    copy_restriction = {"nwb_file_name": copy_file_name}

    # Delete in reverse dependency order
    tables_to_clean = [
        sgc.LFPOutput,
        sgc.ImportedLFP,
        sgc.LFPElectrodeGroup,
        sgc.Raw,
        sgc.SensorData,
        sgc.Electrode,
        sgc.ElectrodeGroup,
        sgc.Probe,
        sgc.DataAcquisitionDevice,
        sgc.VideoFile,
        sgc.DIOEvents,
        sgc.TaskEpoch,
        sgc.IntervalList,
        sgc.Task,
        sgc.Session,
        sgc.Nwbfile,
    ]

    for table in tables_to_clean:
        try:
            (table & restriction).delete(safemode=False)
            (table & copy_restriction).delete(safemode=False)
        except Exception:
            pass  # Table may not have this entry; ignore


def insert_lfp(nwb_file_path: Path):
    """Insert LFP data separately.

    Spyglass requires LFP insertion as a separate step from the main
    insert_sessions() call.
    """
    from spyglass.lfp import LFPElectrodeGroup, ImportedLFP, LFPOutput

    nwb_file_name = nwb_file_path.name
    copy_file_name = get_nwb_copy_filename(nwb_file_name)

    # Create LFP electrode group covering all electrodes
    # (adjust electrode selection as needed)
    LFPElectrodeGroup.create_from_nwb(nwb_file_name)

    # Insert LFP
    ImportedLFP.populate()
    LFPOutput.populate()


def insert_session(
    nwb_file_path: Path,
    config_path: Path = Path("dj_local_conf.json"),
    insert_lfp_data: bool = True,
    clean_existing: bool = False,
):
    """Insert one NWB session into the Spyglass database.

    Parameters
    ----------
    nwb_file_path : Path
        Path to the NWB file in the Spyglass raw directory.
    config_path : Path
        Path to dj_local_conf.json.
    insert_lfp_data : bool
        Whether to insert LFP data after the main session insertion.
    clean_existing : bool
        If True, remove any existing entries for this session before inserting.
        Set to True when re-inserting after a failed run.
    """
    nwb_file_path = Path(nwb_file_path)
    assert nwb_file_path.exists(), f"NWB file not found: {nwb_file_path}"

    # Load DataJoint config
    dj.config.load(str(config_path))
    dj.config.save_local()

    nwb_file_name = nwb_file_path.name

    if clean_existing:
        print(f"Cleaning existing entries for {nwb_file_name}...")
        clean_db_entry(nwb_file_name)

    # Main session insertion
    print(f"Inserting session: {nwb_file_name}")
    sgi.insert_sessions(str(nwb_file_path), rollback_on_fail=True, raise_err=True)
    print("Session insertion complete ✓")

    # LFP insertion
    if insert_lfp_data:
        print("Inserting LFP data...")
        insert_lfp(nwb_file_path)
        print("LFP insertion complete ✓")


if __name__ == "__main__":
    SPYGLASS_BASE_DIR = Path("<spyglass_base_dir>")
    NWB_FILE_NAME = "session.nwb"

    insert_session(
        nwb_file_path=SPYGLASS_BASE_DIR / "raw" / NWB_FILE_NAME,
        config_path=Path("dj_local_conf.json"),
        insert_lfp_data=True,
        clean_existing=False,  # set True to re-run after failure
    )
```

### Step 3: Run the Insertion

```bash
source .venv/bin/activate
python src/<lab_name>_to_nwb/<conversion_name>/insert_session.py
```

Watch the output carefully. Common issues at this stage:

- **`rollback_on_fail=True` triggers**: The insertion was partially completed
  and rolled back. Check the traceback to identify the failing table. Fix the
  NWB file and re-run with `clean_existing=True`.
- **Missing LFP**: If `insert_lfp_data=True` fails, check that the NWB file
  has LFP in `processing["ecephys"]["LFP"]`.
- **Video path error**: Spyglass checks that `external_file` paths in `ImageSeries`
  are accessible. Verify relative paths are correct from the Spyglass raw directory.

### Step 4: Quick Verification

After insertion, do a quick check that the key tables have rows:

```python
import datajoint as dj
import spyglass.common as sgc

dj.config.load("dj_local_conf.json")

nwb_file_name = "session.nwb"
restriction = {"nwb_file_name": nwb_file_name}

print(f"Nwbfile rows: {len(sgc.Nwbfile & restriction)}")
print(f"Session rows: {len(sgc.Session & restriction)}")
print(f"Electrode rows: {len(sgc.Electrode & restriction)}")
print(f"Raw rows: {len(sgc.Raw & restriction)}")
```

If all counts are > 0, proceed to Phase 9 for full verification.

### Push Phase 8 Results

```bash
git add insert_session.py
git commit -m "Phase 8: add insert_session.py — session inserted successfully"
```
