# Spyglass Insertion Patterns

Reference patterns for inserting NWB files into Spyglass and querying the results.
Based on the jadhav-lab-to-nwb and kind-lab-to-nwb reference implementations.

## DataJoint Configuration

> **Critical import order**: `dj.config.load()` MUST be called before importing
> any Spyglass module. Spyglass executes `dj.schema(...)` at module import time,
> which immediately tries to connect to MySQL. If config hasn't been loaded yet,
> DataJoint uses its defaults (`use_tls=True`, wrong host/password) and the
> connection fails with an SSL handshake error.

```python
import datajoint as dj

# ← STEP 1: load config BEFORE any spyglass import
dj.config.load("dj_local_conf.json")
dj.config.save_local()   # writes .datajoint_config.json for session persistence

# ← STEP 2: now it is safe to import spyglass
import spyglass.common as sgc
import spyglass.data_import as sgi
```

The `dj_local_conf.json` for a local Docker container must have:

```json
{
  "database.host": "localhost",
  "database.port": 3306,
  "database.user": "root",
  "database.password": "<password from docker-compose.yml>",
  "database.use_tls": false
}
```

**`"database.use_tls": false` is required for local Docker.** If it is `true`
(the DataJoint default), the SSL handshake fails against the Docker MySQL container.

```python
# Or set manually (e.g., in a notebook)
dj.config["database.host"] = "localhost"
dj.config["database.user"] = "root"
dj.config["database.password"] = "tutorial"
dj.config["database.use_tls"] = False
```

> **DataJoint version**: Always check the latest version of Spyglass to know which datajoint version is supported.
> Always verify with `python -c "import datajoint; print(datajoint.__version__)"`.

## Standard Insertion Call

```python
import spyglass.data_import as sgi

sgi.insert_sessions(
    str(nwb_file_path),
    rollback_on_fail=True,   # atomic: rolls back all tables if any fails
    raise_err=True,          # surface the actual error (not just a generic failure)
)
```

`rollback_on_fail=True` is critical for debugging — without it, a partial
insertion leaves the database in an inconsistent state that requires manual cleanup.

## Idempotent Re-runs with clean_db_entry()

When a session needs to be re-inserted (e.g., after fixing an NWB file), entries
from the previous failed run must be removed first. Delete in reverse dependency
order so foreign key constraints are not violated:

```python
def clean_db_entry(nwb_file_name: str):
    restriction = {"nwb_file_name": nwb_file_name}
    copy_restriction = {"nwb_file_name": get_nwb_copy_filename(nwb_file_name)}

    # Delete from leaf tables to root tables
    tables_in_order = [
        sgc.LFPOutput, sgc.ImportedLFP, sgc.LFPElectrodeGroup,
        sgc.Raw, sgc.SensorData, sgc.Electrode, sgc.ElectrodeGroup,
        sgc.Probe, sgc.DataAcquisitionDevice, sgc.VideoFile,
        sgc.DIOEvents, sgc.TaskEpoch, sgc.IntervalList, sgc.Task,
        sgc.Session, sgc.Nwbfile,
    ]
    for table in tables_in_order:
        try:
            (table & restriction).delete(safemode=False)
            (table & copy_restriction).delete(safemode=False)
        except Exception:
            pass
```

## get_nwb_copy_filename()

Spyglass creates an internal copy of the NWB file when it ingests it. The copy
filename appends `_` to the stem. Some tables (e.g., `ImportedLFP`, `LFPOutput`)
are keyed on this copy filename, not the original:

```python
def get_nwb_copy_filename(nwb_file_name: str) -> str:
    stem = Path(nwb_file_name).stem
    return f"{stem}_.nwb"

# Example:
# "rat1_session1.nwb" → "rat1_session1_.nwb"
```

Always check which restriction key to use when querying a table. If rows come
back empty with the original filename, try the copy filename.

## Querying Spyglass Tables

```python
import spyglass.common as sgc

# Restriction by NWB filename
restriction = {"nwb_file_name": "session.nwb"}

# Fetch as DataJoint expression (lazy)
session = sgc.Session & restriction

# Fetch as dict list
rows = (sgc.Session & restriction).fetch(as_dict=True)

# Fetch as pandas DataFrame
df = (sgc.Electrode & restriction).fetch(format="frame")

# Fetch NWB data object (for Raw, LFP)
raw_nwb = (sgc.Raw & restriction).fetch_nwb()
raw_series = raw_nwb[0]["raw"]    # pynwb.ecephys.ElectricalSeries
data = raw_series.data[:1000, :]  # lazy load first 1000 samples

# Fetch LFP (uses copy filename)
copy_restriction = {"nwb_file_name": "session_.nwb"}
lfp_nwb = (sgc.ImportedLFP & copy_restriction).fetch_nwb()
lfp_series = lfp_nwb[0]["lfp"]
```

## LFP Insertion

LFP requires a separate call after `insert_sessions()`. The exact API depends
on the Spyglass version — check the current Spyglass documentation:

```python
# Newer Spyglass (v0.5+)
from spyglass.lfp import LFPElectrodeGroup, ImportedLFP, LFPOutput

# Create an electrode group for LFP (selects which electrodes to use)
LFPElectrodeGroup.create_from_nwb(nwb_file_name)

# Populate the LFP tables
ImportedLFP.populate()
LFPOutput.populate()
```

## Table Dependency Map

Understanding the dependency hierarchy helps when debugging insertion failures
or cleaning up partial inserts:

```
Nwbfile
  └── Session
        ├── DataAcquisitionDevice
        ├── Probe → ProbeShank → ProbeElectrode
        ├── ElectrodeGroup
        ├── Electrode
        ├── Raw
        ├── SensorData
        ├── DIOEvents
        ├── VideoFile → CameraDevice
        ├── Task → TaskEpoch
        └── IntervalList

(copy file)
  └── LFPElectrodeGroup
        └── ImportedLFP
              └── LFPOutput
```

## Spike Sorting (Post-Insertion)

Spike sorting insertion is typically done separately after the session is inserted.
Spyglass has its own `SpikeSorting` pipeline that either imports existing sorting
results or runs sorting on the raw data. This is not handled by `insert_sessions()`
automatically.

If the lab has existing Phy/Kilosort output they want in Spyglass, consult the
Spyglass SpikeSorting documentation:
https://lorenfranklab.github.io/spyglass/latest/notebooks/02_Data_Views/

## Common DataJoint Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `DataJointError: Duplicate entry` | Session already (partially) inserted | Run `clean_db_entry()` first |
| `DataJointError: Connection refused` | Database not running | Start Docker container |
| `DataJointError: Access denied` | Wrong credentials | Check `dj_local_conf.json` |
| `KeyError` during insertion | Missing NWB data Spyglass expected | Check NWB file structure vs `knowledge/spyglass-nwb-requirements.md` |
| `IntegrityError: foreign key constraint` | Deleting parent before child | Use `clean_db_entry()` which deletes in correct order |
