## Phase 7: DANDI Upload

**Goal**: Upload validated NWB files to the DANDI Archive for public sharing.

**Entry**: All NWB files are converted, validated with nwbinspector, and ready for sharing.

**Exit criteria**: Data is uploaded to DANDI, organized correctly, and accessible via the Dandiset URL.

### Prerequisites

Before uploading, the user needs:
1. A DANDI account (https://dandiarchive.org)
2. A DANDI API key (from user profile on dandiarchive.org)
3. A Dandiset created on the archive (or you help them create one)
4. The `dandi` CLI installed (`pip install -U dandi`)

### Step 1: Create a Dandiset

Guide the user through creating a Dandiset on the DANDI Archive:

> Before we upload, we need to create a Dandiset on DANDI Archive. Have you already
> created one? If not, here's how:
>
> 1. Go to https://dandiarchive.org and log in (or create an account)
> 2. Click "New Dandiset" in the top right
> 3. Fill in the metadata:
>    - **Name**: A descriptive title for your dataset
>    - **Description**: Abstract or summary of the dataset
>    - **License**: Usually CC-BY-4.0 for open data
>    - **Contributors**: Add all contributors with their ORCID IDs
> 4. Note the 6-digit Dandiset ID (e.g., "000123")

If the data should be embargoed (not publicly visible yet):
> If your data needs to be embargoed (e.g., pending publication), select the
> embargo option when creating the Dandiset. Embargoed data is only visible
> to Dandiset owners until you release it.

### Step 2: Set Up API Key

```bash
# Get your API key from https://dandiarchive.org (click your initials → API Key)
export DANDI_API_KEY=<your-key-here>
```

> You'll need your DANDI API key. Go to https://dandiarchive.org, click your
> initials in the top right, and copy your API key. Then set it as an environment
> variable:
> ```bash
> export DANDI_API_KEY=your_key_here
> ```

### Step 3: Validate Before Upload

Run `dandi validate` on the NWB files before uploading:

```bash
dandi validate /path/to/nwb/output/
```

This checks for DANDI-specific requirements beyond what nwbinspector catches:
- File naming conventions
- Required metadata fields (subject_id, session_id)
- NWB file structure compliance

Fix any validation errors before proceeding.

### Step 4: Upload Using NeuroConv Helper (Recommended)

NeuroConv provides `automatic_dandi_upload()` which handles download, organize, and upload:

```python
from neuroconv.tools.data_transfers import automatic_dandi_upload

automatic_dandi_upload(
    dandiset_id="000123",           # 6-digit Dandiset ID
    nwb_folder_path="./nwb_output", # Folder with all NWB files
    sandbox=False,                   # True for testing on sandbox server
    number_of_jobs=1,               # Parallel upload jobs
    number_of_threads=4,            # Threads per upload
)
```

This function:
1. Downloads the Dandiset metadata (creates the local Dandiset structure)
2. Runs `dandi organize` to rename files to DANDI conventions (sub-<id>/sub-<id>_ses-<id>.nwb)
3. Uploads all organized NWB files

### Step 5: Upload Using DANDI CLI (Alternative)

If the NeuroConv helper doesn't work, use the DANDI CLI directly:

```bash
# 1. Download the Dandiset structure
dandi download https://dandiarchive.org/dandiset/000123/draft
cd 000123

# 2. Organize NWB files into DANDI structure (renames files)
dandi organize /path/to/nwb/output/ -f dry  # Preview first
dandi organize /path/to/nwb/output/         # Execute

# 3. Validate
dandi validate .

# 4. Upload
dandi upload
```

### Step 6: Verify on DANDI

After upload completes:
> Your data is now on DANDI! You can view it at:
> https://dandiarchive.org/dandiset/000123/draft
>
> Please verify:
> 1. All sessions appear in the file listing
> 2. The metadata looks correct
> 3. You can stream and preview the NWB files in Neurosift
>
> When you're ready to publish (make it permanently citable with a DOI),
> click "Publish" on the Dandiset page. This creates an immutable version.

### Testing with Sandbox

For testing uploads before going to production:

```python
# Use the sandbox server
automatic_dandi_upload(
    dandiset_id="000123",
    nwb_folder_path="./nwb_output",
    sandbox=True,  # Upload to sandbox.dandiarchive.org
)
```

Or with the CLI:
```bash
# Set sandbox API key
export DANDI_SANDBOX_API_KEY=your_sandbox_key

# Upload to sandbox
dandi upload -i dandi-sandbox
```

The sandbox server is at https://gui-staging.dandiarchive.org/ — create a separate
Dandiset there for testing.

### Common Issues

- **"Unable to find environment variable DANDI_API_KEY"**: Set the API key with `export DANDI_API_KEY=...`
- **Validation errors**: Run `nwbinspector` and `dandi validate` to identify issues
- **Files too large**: DANDI supports files up to 5TB. Contact DANDI team for datasets >10TB
- **Path too long**: DANDI has a 512-character path limit. Shorten session/subject IDs if needed
- **Organize step fails**: Ensure NWB files have `subject.subject_id` and `session_id` set
- **Upload hangs**: Try with `number_of_jobs=1` and `number_of_threads=1` for debugging.
  Check logs at `~/Library/Logs/dandi-cli` (macOS) or `~/.cache/dandi-cli/log` (Linux)

### Add Upload to convert_all_sessions.py

Optionally add upload as the final step of batch conversion:

```python
def dataset_to_nwb(
    data_dir_path,
    output_dir_path,
    dandiset_id=None,
    max_workers=1,
    stub_test=False,
):
    # ... run all conversions ...

    if dandiset_id and not stub_test:
        from neuroconv.tools.data_transfers import automatic_dandi_upload
        automatic_dandi_upload(
            dandiset_id=dandiset_id,
            nwb_folder_path=output_dir_path,
        )
```
