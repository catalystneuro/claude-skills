## Phase 8: DANDI Upload

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

Use separate environment variables for each instance so both can coexist:
- **Sandbox**: `DANDI_SANDBOX_API_KEY` — key from https://sandbox.dandiarchive.org
- **Production**: `DANDI_API_KEY` — key from https://dandiarchive.org

When running commands, set `DANDI_API_KEY` to the appropriate value:
```bash
# For sandbox operations:
export DANDI_API_KEY=$DANDI_SANDBOX_API_KEY

# For production operations:
# DANDI_API_KEY is already set (or export DANDI_API_KEY=<production-key>)
```

For sandbox uploads, add `-i dandi-sandbox` to all `dandi` CLI commands.

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

# For sandbox:
client = DandiAPIClient(api_url="https://api.sandbox.dandiarchive.org/api")
# For production:
# client = DandiAPIClient()  # uses default https://api.dandiarchive.org/api

client.dandi_authenticate()

dandiset = client.create_dandiset(
    name="Descriptive title for your dataset",
    metadata={
        "schemaKey": "Dandiset",
        "schemaVersion": "0.7.0",
        "name": "Descriptive title for your dataset",
        "description": "Abstract or summary of the dataset",
        "license": ["spdx:CC-BY-4.0"],
        "access": [{"schemaKey": "AccessRequirements", "status": "dandi:OpenAccess"}],
        "contributor": [{
            "schemaKey": "Person",
            "name": "Last, First",
            "roleName": ["dcite:ContactPerson"],
            "includeInCitation": True,
        }],
    },
)
dandiset_id = dandiset.identifier
print(f"Created Dandiset: {dandiset_id}")
```

Alternatively, guide the user through creating one manually on the web:
> 1. Go to https://dandiarchive.org (or https://sandbox.dandiarchive.org for sandbox)
> 2. Click "New Dandiset" in the top right
> 3. Fill in: Name, Description, License (CC-BY-4.0), Contributors
> 4. Note the 6-digit Dandiset ID (e.g., "000123")

If the data should be embargoed (not publicly visible yet):
> If your data needs to be embargoed (e.g., pending publication), select the
> embargo option when creating the Dandiset. Embargoed data is only visible
> to Dandiset owners until you release it.

### Step 2: Set Up API Keys

Ask the user to set their API key(s) as labeled environment variables:

```bash
# Sandbox key (from https://sandbox.dandiarchive.org → initials → API Key)
export DANDI_SANDBOX_API_KEY=<your-sandbox-key>

# Production key (from https://dandiarchive.org → initials → API Key)
export DANDI_API_KEY=<your-production-key>
```

Before running any `dandi` CLI commands, set `DANDI_API_KEY` to the correct key:
```bash
# For sandbox operations:
export DANDI_API_KEY=$DANDI_SANDBOX_API_KEY
```

For Python API calls, pass the key explicitly via `DandiAPIClient` (see examples below).

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

NeuroConv provides `automatic_dandi_upload()` which handles download, organize, and upload.
**Important**: This function reads `DANDI_API_KEY` from the environment, so set it to the
correct labeled key first:

```python
import os
from neuroconv.tools.data_transfers import automatic_dandi_upload

# Set DANDI_API_KEY from the labeled env var for the chosen instance
os.environ["DANDI_API_KEY"] = os.environ["DANDI_SANDBOX_API_KEY"]  # or just DANDI_API_KEY for production

automatic_dandi_upload(
    dandiset_id="000123",           # 6-digit Dandiset ID
    nwb_folder_path="./nwb_output", # Folder with all NWB files
    sandbox=True,                    # True for sandbox, False for production
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

### Step 5b: Upload Using DANDI Python API (Alternative)

If the CLI approaches have issues (e.g., sandbox identifier format), use the Python API directly:

```python
import os
from pathlib import Path
from dandi.dandiapi import DandiAPIClient

# For sandbox: set DANDI_API_KEY from the labeled sandbox key
os.environ["DANDI_API_KEY"] = os.environ["DANDI_SANDBOX_API_KEY"]
client = DandiAPIClient(api_url="https://api.sandbox.dandiarchive.org/api")
# For production:
# client = DandiAPIClient()  # uses DANDI_API_KEY directly
client.dandi_authenticate()
dandiset = client.get_dandiset("000123", "draft")

# Upload each organized NWB file
# NOTE: iter_upload_raw_asset() is on the RemoteDandiset object, NOT on DandiAPIClient
nwb_dir = Path("./000123")
for nwb_path in sorted(nwb_dir.rglob("*.nwb")):
    asset_path = str(nwb_path.relative_to(nwb_dir))
    print(f"Uploading {asset_path}...")
    for status in dandiset.iter_upload_raw_asset(nwb_path, asset_metadata={"path": asset_path}):
        if isinstance(status, dict) and status.get("status") == "done":
            print(f"  Done: {status['asset'].path}")
```

**DANDI sandbox URL**: Always use `https://api.sandbox.dandiarchive.org/api` for the
sandbox API.

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
> Next we'll fill in the Dandiset metadata (authors, funding, the associated paper,
> brain regions, license), which DANDI requires before the Dandiset can be published.

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
# Point DANDI_API_KEY to the sandbox key
export DANDI_API_KEY=$DANDI_SANDBOX_API_KEY

# Upload to sandbox
dandi upload -i dandi-sandbox
```

The sandbox server is at https://sandbox.dandiarchive.org/ (API: https://api.sandbox.dandiarchive.org/) —
create a separate account and Dandiset there for testing.

### Step 7: Write Conversion Manifest

After the upload is complete, write a `conversion_manifest.yaml` to the
conversion repo. This manifest captures structured metadata about what was built, enabling
the weekly registry scan to aggregate it for future conversions.

Build the manifest from the conversion artifacts you've created throughout the engagement:

```yaml
# conversion_manifest.yaml (in repo root)
schema_version: 1
lab: "<Lab Name>"
conversions:
  - name: "<conversion_name>"
    status: completed
    species: "<binomial, e.g., Mus musculus>"
    modalities: [ecephys, behavior]  # from Phase 1
    neuroconv_interfaces:
      - name: SpikeGLXRecordingInterface
        file_patterns: ["*.ap.bin", "*.ap.meta"]
      - name: SpikeGLXLFPInterface
        file_patterns: ["*.lf.bin", "*.lf.meta"]
      - name: PhySortingInterface
        file_patterns: ["spike_times.npy", "cluster_group.tsv"]
    custom_interfaces:
      - name: "<CustomInterfaceName>"
        file: "src/<package>/<conversion>/interfaces/<filename>.py"
        handles: "<brief description of what file format it reads>"
        creates: [Position, BehavioralEvents]  # NWB types created
        file_patterns: ["events.csv", "trials.csv"]
    extensions: []  # any ndx-* extensions used
    sync_approach: "<ttl_based|shared_clock|software_sync|none>"
    dandi_id: "<6-digit dandiset ID>"
    pattern: "<standard_nwbconverter|converter_pipe|custom>"
    lessons:
      - "<any gotchas, quirks, or tips discovered during this conversion>"
    date_completed: "<YYYY-MM-DD>"
```

**How to populate each field:**
- `name`: The conversion subdirectory name (e.g., `experiment_2026`)
- `modalities`: Collect from the Data Streams table in `conversion_notes.md`
- `neuroconv_interfaces`: From the Interface Mapping table in `conversion_notes.md`.
  Each entry has `name` (the interface class) and `file_patterns` (globs that this
  interface handles, from Phase 2 inspection).
- `custom_interfaces`: From any custom DataInterface classes you wrote in Phase 5.
  Include `file_patterns` for the files each custom interface reads.
- `extensions`: Any `ndx-*` packages used (e.g., `ndx-fiber-photometry`, `ndx-pose`)
- `sync_approach`: From Phase 4 sync plan
- `dandi_id`: The Dandiset ID from this phase
- `lessons`: Anything surprising, non-obvious, or worth knowing for future similar conversions
- `date_completed`: Today's date

**Commit and push the manifest** (remote was configured in Phase 1 via the API):
```bash
git add conversion_manifest.yaml
git commit -m "Add conversion manifest for registry

Dandiset: <dandi_id>
Modalities: <modalities>
Interfaces: <N> NeuroConv + <N> custom"
if git remote get-url origin &>/dev/null; then git push; fi
```

If the repo is in the `nwb-conversions` org (the normal case when the API is reachable),
the weekly registry scan will find it automatically — no further action needed.

If working locally (API was unreachable), inform the user:
> The conversion manifest has been saved locally. To include this conversion in the
> registry for future reference, contact CatalystNeuro for assistance.

### Step 8: Save Conversation History

Save the Claude Code conversation that produced this conversion into the repo. This
captures every decision, data inspection, question, and code generation step for
full reproducibility.

```bash
# Find the active Claude Code conversation JSONL (most recently modified)
CONVERSATION=$(ls -t ~/.claude/projects/*/*.jsonl 2>/dev/null | head -1)
if [ -n "$CONVERSATION" ]; then
    mkdir -p .claude
    cp "$CONVERSATION" .claude/conversation.jsonl
    git add .claude/conversation.jsonl
    git commit -m "Save Claude Code conversation history"
    if git remote get-url origin &>/dev/null; then git push; fi
    echo "Saved conversation: $(du -h .claude/conversation.jsonl | cut -f1)"
else
    echo "No conversation JSONL found — skipping"
fi
```

The conversation file is a JSONL containing the full exchange between the user and Claude
Code, including tool calls, file reads, and data inspection outputs. It can be replayed
to understand exactly how the conversion was built.

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
