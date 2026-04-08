## Phase 9: Table Verification

**Goal**: Pretty-print the key Spyglass tables and validate that data retrieved
from the database matches the original NWB file.

**Entry**: Session insertion from Phase 8 completed successfully.

**Exit criteria**: `tables.txt` is written with formatted table output. Data
integrity assertions pass for all critical streams.

### Step 1: Write the Verification Script

Add a `verify_insertion.py` next to `insert_session.py`:

```python
"""Verify Spyglass database entries after session insertion."""

from pathlib import Path
import numpy as np
import datajoint as dj
import spyglass.common as sgc
from pynwb import NWBHDF5IO

from .insert_session import get_nwb_copy_filename


def log_table(table, restriction=True) -> str:
    """Return a formatted string for one Spyglass table."""
    restricted = table & restriction
    return f"=== {table.__name__} ===\n{restricted}\n"


def print_tables(nwb_file_name: str, output_path: Path = Path("tables.txt")):
    """Pretty-print all key Spyglass tables to a file.

    Covers the tables that sgi.insert_sessions() populates, ordered by
    the dependency hierarchy.
    """
    restriction = {"nwb_file_name": nwb_file_name}
    copy_file_name = get_nwb_copy_filename(nwb_file_name)
    copy_restriction = {"nwb_file_name": copy_file_name}

    sections = [
        # Session metadata
        log_table(sgc.Nwbfile, restriction),
        log_table(sgc.Session, restriction),
        log_table(sgc.Task, restriction),
        log_table(sgc.TaskEpoch, restriction),
        log_table(sgc.IntervalList, restriction),
        # Hardware
        log_table(sgc.DataAcquisitionDevice, restriction),
        log_table(sgc.Probe, restriction),
        log_table(sgc.ProbeShank, restriction),
        log_table(sgc.ProbeElectrode, restriction),
        log_table(sgc.ElectrodeGroup, restriction),
        log_table(sgc.Electrode, restriction),
        # Ephys
        log_table(sgc.Raw, restriction),
        # LFP (uses copy filename)
        log_table(sgc.LFPElectrodeGroup, copy_restriction),
        log_table(sgc.ImportedLFP, copy_restriction),
        log_table(sgc.LFPOutput, copy_restriction),
        # Behavior
        log_table(sgc.DIOEvents, restriction),
        # Media
        log_table(sgc.VideoFile, restriction),
        log_table(sgc.CameraDevice, restriction),
    ]

    output = "\n".join(sections)
    output_path.write_text(output)
    print(f"Table output written to {output_path}")
    print(output)


def validate_data_integrity(nwb_file_path: Path, n_samples: int = 100):
    """Compare NWB file data against what Spyglass stored.

    Asserts array equality for the most critical streams: raw ephys and LFP.
    """
    nwb_file_path = Path(nwb_file_path)
    nwb_file_name = nwb_file_path.name
    copy_file_name = get_nwb_copy_filename(nwb_file_name)
    restriction = {"nwb_file_name": nwb_file_name}
    copy_restriction = {"nwb_file_name": copy_file_name}

    with NWBHDF5IO(str(nwb_file_path), "r") as io:
        nwbfile = io.read()

        # --- Raw ephys validation ---
        print("Validating raw ephys...")
        raw_entry = (sgc.Raw & restriction).fetch_nwb()
        if raw_entry:
            spyglass_raw = raw_entry[0]["raw"].data[:n_samples, :]
            nwb_raw = nwbfile.acquisition["ElectricalSeries"].data[:n_samples, :]
            np.testing.assert_array_equal(
                spyglass_raw, nwb_raw,
                err_msg="Raw ephys mismatch between NWB file and Spyglass"
            )
            print("Raw ephys ✓")
        else:
            print("WARNING: No Raw entries found for this session")

        # --- LFP validation ---
        print("Validating LFP...")
        lfp_entry = (sgc.ImportedLFP & copy_restriction).fetch_nwb()
        if lfp_entry:
            spyglass_lfp = lfp_entry[0]["lfp"].data[:n_samples, :]
            nwb_lfp = (
                nwbfile
                .processing["ecephys"]["LFP"]
                .electrical_series["LFP"]
                .data[:n_samples, :]
            )
            np.testing.assert_array_equal(
                spyglass_lfp, nwb_lfp,
                err_msg="LFP mismatch between NWB file and Spyglass"
            )
            print("LFP ✓")
        else:
            print("WARNING: No ImportedLFP entries found")

        # --- DIO events validation ---
        print("Validating DIO events...")
        dio_rows = (sgc.DIOEvents & restriction).fetch(as_dict=True)
        if dio_rows:
            for row in dio_rows[:3]:  # spot-check first 3 channels
                print(f"  DIO channel '{row.get('dio_event_name', '?')}': "
                      f"{len(row.get('dio_timestamps', []))} events")
            print("DIO events present ✓")
        else:
            print("No DIO events (expected if dataset has none)")

        # --- Task epochs validation ---
        print("Validating task epochs...")
        epochs = (sgc.TaskEpoch & restriction).fetch(as_dict=True)
        if epochs:
            for ep in epochs:
                print(f"  Epoch: {ep.get('epoch_name', '?')} "
                      f"[{ep.get('start_time', '?'):.2f} – {ep.get('stop_time', '?'):.2f}]")
            print(f"Task epochs: {len(epochs)} ✓")
        else:
            print("No task epochs (expected if dataset has none)")


def verify_insertion(
    nwb_file_path: Path,
    config_path: Path = Path("dj_local_conf.json"),
):
    nwb_file_path = Path(nwb_file_path)
    dj.config.load(str(config_path))

    nwb_file_name = nwb_file_path.name
    print(f"\n{'='*60}")
    print(f"Verifying insertion for: {nwb_file_name}")
    print(f"{'='*60}\n")

    print_tables(nwb_file_name, output_path=Path("tables.txt"))
    print()
    validate_data_integrity(nwb_file_path)

    print("\nVerification complete.")


if __name__ == "__main__":
    SPYGLASS_BASE_DIR = Path("<spyglass_base_dir>")
    NWB_FILE_NAME = "session.nwb"

    verify_insertion(
        nwb_file_path=SPYGLASS_BASE_DIR / "raw" / NWB_FILE_NAME,
        config_path=Path("dj_local_conf.json"),
    )
```

### Step 2: Run Verification

```bash
source .venv/bin/activate
python src/<lab_name>_to_nwb/<conversion_name>/verify_insertion.py
```

### Step 3: Review the Output

Read `tables.txt` and check:

1. **Nwbfile / Session**: rows exist, session description and timestamps look correct
2. **Electrode**: all electrodes present, `brain_area` and `group_name` match expectations
3. **Probe / ProbeShank / ProbeElectrode**: probe geometry is populated
4. **Raw**: entry present, size/shape looks plausible
5. **LFP**: entries present if LFP was inserted
6. **DIOEvents**: expected channels present with sensible event counts
7. **TaskEpoch**: epochs match what you know about the session

**If any table is empty** when it should have rows, check:
- Was the corresponding NWB data present in the file?
- Did `insert_sessions()` log any warnings for that table?
- Is the restriction key correct (some tables use the copy filename)?

**If data integrity assertions fail**, the NWB file data and Spyglass-stored data
diverged. This usually means Spyglass applied a transformation during ingestion.
Check the Spyglass ingestion code for that data type.

### Push Phase 9 Results

```bash
git add verify_insertion.py tables.txt
git commit -m "Phase 9: table verification — all tables populated, integrity checks pass"
```
