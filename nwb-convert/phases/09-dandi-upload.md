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

`dandi validate` needs a Dandiset folder, so it runs after `dandi organize` in Step 4, and
`automatic_dandi_upload` in Step 3 validates each file before uploading it. What each tool checks is
in `knowledge/nwb-best-practices.md` ("Validation").

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

### Step 6: Write Conversion Manifest

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

### Step 7: Save Conversation History

Save the Claude Code conversation that produced this conversion into the repo. This
captures every decision, data inspection, question, and code generation step for
full reproducibility.

Claude Code names each transcript after its session ID and exports that ID to shell
commands as `CLAUDE_CODE_SESSION_ID`. Copy that file and scan the copy for secrets:

```bash
CONVERSATION=$(ls ~/.claude/projects/*/"$CLAUDE_CODE_SESSION_ID".jsonl)
mkdir -p .claude
cp "$CONVERSATION" .claude/conversation.jsonl

# Values of credentials set in this shell
for name in DANDI_API_KEY DANDI_SANDBOX_API_KEY GITHUB_TOKEN GH_TOKEN; do
    value=$(printenv "$name")
    if [ -n "$value" ] && grep -qF "$value" .claude/conversation.jsonl; then
        echo "FOUND value of $name"
    fi
done

# Common credential patterns, cut to 24 characters so the scan does not print a whole secret
grep -oE 'DANDI(_SANDBOX)?_API_KEY=[^ "\\]+|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|[Pp]assword[=:] *[^ "\\]+' \
    .claude/conversation.jsonl | cut -c1-24 | sort | uniq -c
```

Review every match. Placeholders such as `DANDI_API_KEY=<key>` from the skill text are
harmless. If a real key, token, or password appears, delete `.claude/conversation.jsonl`,
do not commit it, and tell the user which credential appeared so they can revoke it.

If the scan is clean, ask the user before committing. Tell them the file holds the whole
session, including tool outputs, local paths, and excerpts of their data, and that it
will be pushed to the conversion repo (say whether that repo is public). Commit only
after they agree:

```bash
git add .claude/conversation.jsonl
git commit -m "Save Claude Code conversation history"
if git remote get-url origin &>/dev/null; then git push; fi
```

If they decline, delete `.claude/conversation.jsonl`.

The conversation file is a JSONL containing the full exchange between the user and Claude
Code, including tool calls, file reads, and data inspection outputs. It can be replayed
to understand exactly how the conversion was built.

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
