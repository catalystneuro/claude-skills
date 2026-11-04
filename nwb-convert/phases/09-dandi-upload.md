## Phase 9: DANDI Upload

**Goal**: Upload validated NWB files to the DANDI Archive for public sharing.

**Entry**: All NWB files are converted, validated with nwbinspector, and ready for sharing.

**Exit criteria**: Data is uploaded to DANDI, organized correctly, and accessible via the Dandiset URL.

### Step 0: Choose DANDI Instance

**Always ask this first.** Before any upload steps, ask the user which DANDI instance to use:

> We're ready to upload your NWB files to DANDI! First, which DANDI instance would you
> like to use?
>
> 1. **DANDI Sandbox** (sandbox.dandiarchive.org) — for testing. Data can be deleted.
>    Use this if you want to verify everything works before publishing for real.
> 2. **DANDI Archive** (dandiarchive.org) — the official public archive. Use this when
>    you're ready to publish your data permanently.
>
> Which would you prefer?

Keys go in two environment variables, which `dandi`, `DandiAPIClient.dandi_authenticate()`, and
NeuroConv's `automatic_dandi_upload` pick by instance:
- `DANDI_API_KEY` for dandiarchive.org
- `DANDI_SANDBOX_API_KEY` for sandbox.dandiarchive.org

To get a key, sign in on the chosen instance, click your initials, and copy the API key. The user
exports it in their own shell:
```bash
export DANDI_SANDBOX_API_KEY=<your-sandbox-key>   # sandbox
export DANDI_API_KEY=<your-production-key>        # production
```

For the sandbox, use `DANDI-SANDBOX:<id>` in `dandi download` and `-i dandi-sandbox` in `dandi upload`.

### Prerequisites

Before uploading, the user needs:
1. A DANDI account (on the chosen instance — sandbox and archive have separate accounts)
2. A DANDI API key (from user profile on the chosen instance)
3. A Dandiset created on the chosen instance (or create one programmatically — see Step 1)
4. The `dandi` CLI installed (`uv pip install -U dandi`)

### Step 1: Create a Dandiset

Create a Dandiset programmatically using the DANDI API:

```python
from dandi.dandiapi import DandiAPIClient

client = DandiAPIClient.for_dandi_instance("dandi-sandbox", authenticate=True)  # or "dandi"
dandiset = client.create_dandiset(
    name="Descriptive title for your dataset",
    metadata={
        "name": "Descriptive title for your dataset",
        "description": "Abstract or summary of the dataset",
    },
    embargo=False,  # True keeps the data private until released
)
dandiset_id = dandiset.identifier
print(f"Created Dandiset: {dandiset_id}")
```

Contributors, license, and the rest of the Dandiset metadata are filled in Phase 10.

Alternatively, guide the user through creating one manually on the web:
> 1. Go to https://dandiarchive.org (or https://sandbox.dandiarchive.org for sandbox)
> 2. Click "New Dandiset" in the top right
> 3. Fill in: Name, Description, License (CC-BY-4.0), Contributors
> 4. Note the 6-digit Dandiset ID (e.g., "000123")

Pass `embargo=True` (or tick Embargo in the web form) if the data must stay private until
publication. Embargoed data is only visible to Dandiset owners until you release it.

### Step 2: Validate Before Upload

Run NWB Inspector with the DANDI configuration on all NWB files before uploading:

```bash
nwbinspector /path/to/nwb/output/ --config dandi
```

Fix every ERROR, PYNWB_VALIDATION, and CRITICAL message before proceeding; `dandi upload` refuses
files that have them.

`dandi validate` only works inside a Dandiset folder (one with `dandiset.yaml`); on a plain output
folder it fails with `DANDI.NO_DANDISET_FOUND`. Inside the Dandiset it also checks the file and
folder names that `dandi organize` produces. Step 5 runs it after `dandi organize`, and
`automatic_dandi_upload` in Step 4 validates each file before uploading it.

### Step 3: Upload Using NeuroConv Helper (Recommended)

NeuroConv provides `automatic_dandi_upload()` which handles download, organize, and upload:

```python
from pathlib import Path

from neuroconv.tools.data_transfers import automatic_dandi_upload

automatic_dandi_upload(
    dandiset_id="000123",                 # 6-digit Dandiset ID
    nwb_folder_path=Path("./nwb_output"), # Folder with all NWB files
    sandbox=True,                         # True for sandbox, False for production
    number_of_jobs=1,                     # Parallel upload jobs
    number_of_threads=4,                  # Threads per upload
)
```

This function:
1. Downloads the Dandiset metadata (creates the local Dandiset structure)
2. Runs `dandi organize` to rename files to DANDI conventions (sub-<id>/sub-<id>_ses-<id>.nwb)
3. Uploads all organized NWB files

### Step 4: Upload Using DANDI CLI (Alternative)

If the NeuroConv helper doesn't work, use the DANDI CLI directly:

```bash
# 1. Download only dandiset.yaml (sandbox: DANDI-SANDBOX:000123)
dandi download --download dandiset.yaml DANDI:000123
cd 000123

# 2. Organize NWB files into DANDI structure (renames files)
dandi organize /path/to/nwb/output/ -f dry  # Preview first
dandi organize /path/to/nwb/output/         # Execute

# 3. Validate
dandi validate .

# 4. Upload (sandbox: dandi upload -i dandi-sandbox)
dandi upload
```

### Step 5: Verify on DANDI

After upload completes:
> Your data is now on DANDI! You can view it at:
> https://dandiarchive.org/dandiset/000123/draft
>
> Please verify:
> 1. All sessions appear in the file listing
> 2. The metadata looks correct
> 3. You can stream and preview the NWB files in Neurosift
>
> Next we'll fill in the Dandiset metadata (authors, funding, the associated paper,
> brain regions, license), which DANDI requires before the Dandiset can be published.

### Common Issues

- **Unable to find environment variable 'DANDI_API_KEY'** (or `'DANDI_SANDBOX_API_KEY'`): export the variable for the chosen instance
- **Validation errors**: Run `nwbinspector` and `dandi validate` to identify issues
- **Files too large**: DANDI supports files up to 5TB. Contact DANDI team for datasets >10TB
- **Path too long**: DANDI has a 512-character path limit. Shorten session/subject IDs if needed
- **Organize step fails**: Ensure NWB files have `subject.subject_id` and `session_id` set
- **Upload hangs**: Try with `number_of_jobs=1` and `number_of_threads=1` for debugging.
  The log path is printed at the end of each `dandi` run (`Logs saved in ...`).

### Add Upload to convert_all_sessions.py

Optionally add upload as the final step of batch conversion:

```python
from pathlib import Path

from neuroconv.tools.data_transfers import automatic_dandi_upload


def dataset_to_nwb(
    data_dir_path,
    output_dir_path,
    dandiset_id=None,
    sandbox: bool = False,
    max_workers=1,
    stub_test=False,
):
    # ... run all conversions ...

    if dandiset_id and not stub_test:
        automatic_dandi_upload(
            dandiset_id=dandiset_id,
            nwb_folder_path=Path(output_dir_path),
            sandbox=sandbox,
        )
```
