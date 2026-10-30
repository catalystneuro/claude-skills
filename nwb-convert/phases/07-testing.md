## Phase 7: Testing & Validation

**Goal**: Verify the conversion produces valid, complete NWB files.

**Entry**: You have generated all conversion code from Phase 5.

**Exit criteria**: The conversion runs successfully on at least one session, the output
passes nwbinspector validation, and the data can be read back correctly.

### Step 1: Install the Package

```bash
cd <repo_path>
source .venv/bin/activate
uv pip install -e ".[<conversion_name>]"
```

### Step 2: Run a Stub Test

First, run with `stub_test=True` to convert a small subset of data quickly:

```python
from <package>.<conversion_name>.<conversion_name>_convert_session import session_to_nwb

session_to_nwb(
    data_dir_path="/path/to/sample/session",
    output_dir_path="/path/to/output",
    stub_test=True,
)
```

### Step 3: Inspect the NWB File

Read back the file and verify contents:

```python
from hdmf.common import DynamicTable
from pynwb import NWBHDF5IO, TimeSeries

with NWBHDF5IO("/path/to/output/session.nwb", "r") as io:
    nwbfile = io.read()
    print(nwbfile)
    for neurodata_object in nwbfile.objects.values():
        if isinstance(neurodata_object, TimeSeries):
            print(neurodata_object.name, neurodata_object.data.shape, neurodata_object.data.dtype)
        elif isinstance(neurodata_object, DynamicTable):
            print(neurodata_object.name, len(neurodata_object), neurodata_object.colnames)
```

#### Check the Ontology Annotations

Phase 6 wired HERD references into the converter. Confirm they were written by adding this
inside the `with` block above:

```python
    # Check ontology annotations
    if nwbfile.external_resources is None:
        print("External resources: none written")
    else:
        references = nwbfile.external_resources.to_dataframe()
        print(references[["object_type", "relative_path", "key", "entity_id", "entity_uri"]].to_string())
```

Each value in `external_resources.yaml` that this session uses should appear as a `key`. If
one is missing, the string in the YAML does not match the string in the file exactly.
A row with `object_type` `VectorData` is a table column, such as the `location` column of the
electrodes table. `knowledge/external-resources.md` ("Checking a Written File") has a script
that names each object and lists the values that were not written.

Phase 6 also wired value meanings into the converter. Confirm they were written by adding
this inside the same `with` block:

```python
    # Check value meanings
    from hdmf.common import MeaningsTable

    for meanings_table in nwbfile.all_children():
        if isinstance(meanings_table, MeaningsTable):
            print(f"{meanings_table.parent.name}/{meanings_table.target.name}")
            print(meanings_table.to_dataframe().to_string())
```

Each column in `value_meanings.yaml` that this session has should be printed with one row
per value, and a `HED` column where the values were annotated. Then run the script in
`knowledge/value-meanings.md` ("Checking a Written File"), which lists the values in each
column that have no meaning and validates the HED strings as they were written.

### Step 4: Run NWB Inspector

**You MUST run nwbinspector on every converted file.** Do not skip this step or leave it for the user.

Run it via bash and capture the full output:

```bash
nwbinspector /path/to/output/session.nwb --config dandi
```

`knowledge/nwb-best-practices.md` ("Validation") says what `--config dandi` changes and what each severity level
means. `dandi validate` needs a Dandiset folder, so it runs in Phase 9 after `dandi organize`.

**For each issue reported, you must:**
1. Find the message's check name in `knowledge/nwb-best-practices.md`, where each rule names the check that reports it
2. Identify the root cause in the conversion code and fix it (metadata, interface, or convert_session.py)
3. Re-run the conversion (stub_test=True)
4. Re-run nwbinspector to confirm the fix

**Keep iterating until nwbinspector produces zero ERROR, PYNWB_VALIDATION, CRITICAL, and BEST_PRACTICE_VIOLATION messages.**
Fix a BEST_PRACTICE_SUGGESTION if it is straightforward; otherwise note it for the user.
Show the user the final clean nwbinspector output as confirmation.

### Step 5: Run Full Conversion (one session)

Once stub_test passes and nwbinspector is clean, run with `stub_test=False` on a single session:

```python
session_to_nwb(
    data_dir_path="/path/to/sample/session",
    output_dir_path="/path/to/output",
    stub_test=False,
)
```

Then run nwbinspector again on the full output — some issues only appear with real data
(e.g., data orientation problems, timestamp gaps, large uncompressed datasets).

### Step 6: Validate Data Integrity

For critical data streams, compare source and NWB values:

```python
import numpy as np
import spikeinterface.extractors as se
from pynwb import NWBHDF5IO

# Example: verify spike times against the Phy output, matching units by the unit_name column
sorting = se.read_phy(phy_folder_path)
source_unit_ids = {str(unit_id): unit_id for unit_id in sorting.unit_ids}

with NWBHDF5IO("/path/to/output/full_session.nwb", "r") as io:
    nwbfile = io.read()
    units = nwbfile.units.to_dataframe()
    for unit_name, nwb_spike_times in zip(units["unit_name"], units["spike_times"]):
        source_spike_times = sorting.get_unit_spike_train(unit_id=source_unit_ids[unit_name], return_times=True)
        np.testing.assert_allclose(nwb_spike_times, source_spike_times, atol=1e-6)
```

Timestamps are in seconds from `session_start_time`. Compare the first and last timestamps
of each stream with the expected session duration.

### Push Phase 7 Results

In stacked PRs mode, commit each fix on the branch of the stream it belongs to and carry it up
the stack (`knowledge/stacked-prs.md`, "Changing a lower branch") in place of the single commit below.

After all tests pass and nwbinspector is clean, commit any bug fixes and push:
```bash
git add -A
git commit -m "Phase 7: testing and validation — all checks passing

nwbinspector --config dandi: 0 CRITICAL, 0 BEST_PRACTICE_VIOLATION"
if git remote get-url origin &>/dev/null; then git push; fi
```
