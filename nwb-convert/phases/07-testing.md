## Phase 7: Testing & Validation

**Goal**: Verify the conversion produces valid, complete NWB files.

**Entry**: You have generated all conversion code from Phase 5.

**Exit criteria**: One session converts with `stub_test=True` and in full, every stream matches its source,
and `nwbinspector --config dandi` reports no ERROR, PYNWB_VALIDATION, CRITICAL, or BEST_PRACTICE_VIOLATION
messages on either file.

Whenever a check below fails, fix the conversion code (metadata, interface, or convert_session.py), rerun the
conversion, and repeat the checks.

### Step 1: Install the Package

```bash
cd <repo_path>
source .venv/bin/activate
uv pip install -e ".[<conversion_name>]"
```

### Step 2: Run a Stub Test

```python
from <package>.<conversion_name>.<conversion_name>_convert_session import session_to_nwb

session_to_nwb(
    data_dir_path="/path/to/sample/session",
    output_dir_path="/path/to/output",
    stub_test=True,
)
```

### Step 3: Inspect the NWB File

Read the file back and check every data stream from Phase 2 against its source: values, units, data
orientation (time on the first axis), and timestamps (seconds from `session_start_time`, spanning the
expected session duration).

```python
from pynwb import NWBHDF5IO

with NWBHDF5IO("/path/to/output/session.nwb", "r") as io:
    nwbfile = io.read()
    print(nwbfile)
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

Run NWB Inspector on every converted file yourself, with the configuration DANDI uses on upload:

```bash
nwbinspector /path/to/output/session.nwb --config dandi
```

Fix every ERROR, PYNWB_VALIDATION, CRITICAL, and BEST_PRACTICE_VIOLATION message. Fix BEST_PRACTICE_SUGGESTION
messages where straightforward and note the rest for the user. `knowledge/nwb-best-practices.md` explains the
conventions behind most checks. `dandi validate` needs a Dandiset folder, so it runs in Phase 9. Show the user
the final clean output.

### Step 5: Run Full Conversion (one session)

Run one session with `stub_test=False`, then repeat Steps 3 and 4 on the full file. Some problems, such as
timestamp gaps or wrong data orientation, only appear with all of the data.

### Push Phase 7 Results

In stacked PRs mode, commit each fix on the branch of the stream it belongs to and carry it up
the stack (`knowledge/stacked-prs.md`, "Changing a lower branch") in place of the single commit below.

After all checks pass, commit any bug fixes and push:
```bash
git add -A
git commit -m "Phase 7: testing and validation, all checks passing

nwbinspector --config dandi: 0 CRITICAL, 0 BEST_PRACTICE_VIOLATION"
if git remote get-url origin &>/dev/null; then git push; fi
```
