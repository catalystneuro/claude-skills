## Phase 1: Experiment Discovery

**Goal**: Build a complete picture of the lab's experiments, data modalities, and file organization.

**Entry**: User invokes `/nwb-convert`, possibly with a path to their data.

**Exit criteria**: You have a clear `experiment_spec` (written to `conversion_notes.md`) covering:
- What experiments were performed
- All data streams (raw and processed) for each experiment
- File formats for each stream
- How data is organized on disk (directory structure)
- Number of subjects and sessions
- Any special considerations (multiple probes, multiple FOVs, etc.)

### Step 0a: Check Environment

**Skip this step if running inside NWB GUIDE** (all packages are pre-installed).

Before anything else, set up a uv virtual environment in the conversion repo directory.
All packages should be installed via `uv` — never use bare `pip install`.

```bash
# Ensure uv is installed
which uv || (curl -LsSf https://astral.sh/uv/install.sh | sh)

# Create venv in the conversion repo (after Step 0b creates the repo)
cd <repo_dir>
uv venv
source .venv/bin/activate  # or: source <repo_dir>/.venv/bin/activate

# Install base dependencies for data inspection
uv pip install neuroconv pynwb dandi nwbinspector spikeinterface h5py remfile pandas pyyaml
```

Later in Phase 5, once `pyproject.toml` is created with conversion-specific dependencies,
install the repo in editable mode:
```bash
uv pip install -e ".[<conversion_name>]"
```

**Important**: All `python3` and `pip` commands in subsequent phases should run inside
this venv. When running Python via Bash, use the venv's Python explicitly:
```bash
<repo_dir>/.venv/bin/python3 -c "import neuroconv; print('OK')"
```

### Step 0b: Create Conversion Repo and Consult Registry

Before the first user-facing question, set up the conversion repo and check for prior work.

**Create the repo.** The skill calls the nwb-conversions API to create a private repo
in the `nwb-conversions` GitHub org. The user does NOT need a GitHub account — the API
handles authentication server-side.

```bash
# API base URL (Cloudflare Worker)
NWB_API="https://nwb-conversions-api.ben-dichter.workers.dev"

# Derive lab name from user context (ask if unclear)
LAB_NAME="<lab-name>"
REPO_NAME="${LAB_NAME}-to-nwb"

# Create repo via API
RESPONSE=$(curl -sf -X POST "${NWB_API}/repos" \
  -H "Content-Type: application/json" \
  -d "{\"lab_name\": \"${LAB_NAME}\"}")

if [ $? -eq 0 ]; then
    PUSH_URL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['push_url'])")
    mkdir "${REPO_NAME}" && cd "${REPO_NAME}"
    git init
    git remote add origin "${PUSH_URL}"
    git config user.name "nwb-conversions-bot"
    git config user.email "nwb-conversions-bot@users.noreply.github.com"
else
    # API unreachable — work locally only
    mkdir "${REPO_NAME}" && cd "${REPO_NAME}"
    git init
fi
```

If the API is unreachable, inform the user:
> I'll create a local conversion repo to organize the code. The conversion registry
> is not available right now, but this won't affect the conversion itself.

All subsequent file creation should happen INSIDE this repo directory. When a remote
is configured, the skill pushes after every phase.

**IMPORTANT: The conversion repo must NOT contain source data.** The repo should be
created in a separate directory from the user's data. Never mount Google Drive inside
the repo, never symlink data into the repo, and never copy data files into the repo.
The repo contains only conversion code, metadata files, and documentation. Source data
paths are referenced as absolute paths or paths relative to the user's data directory,
which lives outside the repo.

**Seed the repo** with a `.gitignore` and initial commit:
```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
*.egg

# NWB output (don't commit data files)
*.nwb
nwb_output/
nwb_stub/

# Environment
.env
*.log

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
EOF

git add .gitignore
git commit -m "Initial commit: add .gitignore"
if git remote get-url origin &>/dev/null; then git push; fi
```

**Fetch the conversion registry** to find similar prior conversions:
```bash
curl -sf "${NWB_API}/registry" > /tmp/registry.yaml || true
```

If the API is unreachable or the registry is empty, skip registry consultation and
proceed directly to the opening questions.

**Search the registry** for relevant prior work. Look for matches on:
- Same species
- Same modalities (ecephys, ophys, behavior, icephys)
- Same file formats or interfaces
- Same recording systems (SpikeGLX, OpenEphys, Suite2p, etc.)

```python
import yaml
from pathlib import Path

registry_path = Path("/tmp/registry.yaml")
if registry_path.exists() and registry_path.stat().st_size > 0:
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    # Find conversions with matching modalities
    target_modalities = {"ecephys", "behavior"}  # from user description
    for conv in registry.get("conversions", []):
        overlap = target_modalities & set(conv.get("modalities", []))
        if overlap:
            print(f"Similar: {conv['id']} ({conv['repo']})")
            print(f"  Modalities: {conv['modalities']}")
            print(f"  Interfaces: {conv['interfaces']}")
            if conv.get("lessons"):
                print(f"  Lessons: {conv['lessons']}")
```

If you find relevant prior conversions, mention them to the user:
> I found N similar conversions in our registry that used the same recording system /
> modalities. I'll use those as references as we build yours.

If the registry is empty or has no matches, proceed normally — this is expected for early conversions.

### Step 0c: Google Drive Data Source (if applicable)

**Skip this step if running inside NWB GUIDE** (data is selected via file picker).

If the user provides a Google Drive folder URL instead of a local path, mount it as
a local virtual filesystem using `rclone mount`. This makes the remote files appear
as local files — no download wait, no extra disk space.

**Detect Google Drive URLs.** Match any of these patterns:
- `https://drive.google.com/drive/folders/<folder_id>`
- `https://drive.google.com/drive/u/<N>/folders/<folder_id>`
- With optional query params (`?usp=sharing`, `?resourcekey=...`, etc.)

Extract the folder ID from the URL (the alphanumeric string after `/folders/`).

**Step 1: Ensure rclone is installed.**

```bash
which rclone
```

If not installed, guide the user:
- macOS: **Do NOT use `brew install rclone`** — the Homebrew version does not support
  `rclone mount` on macOS. Instead, install the standalone binary:
  ```bash
  # Download from GitHub releases (ARM64 for Apple Silicon, AMD64 for Intel)
  curl -L -o /tmp/rclone.zip "https://github.com/rclone/rclone/releases/download/v1.68.2/rclone-v1.68.2-osx-arm64.zip"
  unzip -o /tmp/rclone.zip -d /tmp
  mkdir -p ~/.local/bin
  cp /tmp/rclone-v1.68.2-osx-arm64/rclone ~/.local/bin/rclone
  chmod +x ~/.local/bin/rclone
  ```
  If the user already has `rclone` from Homebrew, the standalone binary can coexist at
  `~/.local/bin/rclone`. Use the full path `~/.local/bin/rclone` for mount commands, or
  add `~/.local/bin` to the front of `PATH`. The Homebrew version is fine for non-mount
  commands (ls, copy, config, etc.).
- Linux: `sudo apt install rclone` or `curl https://rclone.org/install.sh | sudo bash`

**Step 2: Ensure FUSE is installed.**

rclone mount requires FUSE support:
- macOS: requires macFUSE — `brew install --cask macfuse` (system restart may be needed
  to load the kernel extension). After installation, verify the FUSE compatibility library
  exists. macFUSE must provide `/usr/local/lib/libfuse.2.dylib` for rclone's cgofuse to
  find it. If the mount helper exists but `libfuse.2.dylib` is missing, macFUSE needs to
  be reinstalled properly (the kernel extension may need approval in System Settings →
  Privacy & Security, followed by a restart).
- Linux: FUSE is typically pre-installed. If not: `sudo apt install fuse3`

Check availability:
```bash
# macOS — check both the mount helper AND the compatibility library
test -f /Library/Filesystems/macfuse.fs/Contents/Resources/mount_macfuse && echo "macFUSE mount helper OK" || echo "macFUSE mount helper not found"
test -f /usr/local/lib/libfuse.2.dylib && echo "macFUSE libfuse OK" || echo "macFUSE libfuse NOT found — reinstall macFUSE and restart"

# Linux
which fusermount3 || which fusermount && echo "FUSE OK" || echo "FUSE not found"
```

**Step 3: Check for existing Google Drive remote.**

```bash
rclone listremotes
```

If no remote exists, create one named "gdrive":
```bash
rclone config create gdrive drive
```

Then test connectivity (this triggers the OAuth browser flow on first use):
```bash
rclone about gdrive:
```

Tell the user:
> A browser window will open for you to authorize rclone to access your Google
> Drive. Please sign in with the Google account that has access to the data folder
> and grant permission.

If the user is on a headless server (no browser), guide them through rclone's
remote authorization flow:
> Run `rclone authorize "drive"` on a machine with a browser, then paste the
> resulting token back here.

**Step 4: Mount the Google Drive folder.**

On macOS, prefer `nfsmount` over `mount` — it uses NFS instead of FUSE and avoids
the macFUSE kernel extension entirely. On Linux, use `mount` (FUSE).

```bash
FOLDER_ID="<extracted_from_url>"
# Mount OUTSIDE the conversion repo — never put source data in the repo
MOUNT_POINT="$HOME/source_data"
mkdir -p "$MOUNT_POINT"

# macOS: use nfsmount (no FUSE/macFUSE required)
rclone nfsmount "gdrive:" "$MOUNT_POINT" \
  --drive-root-folder-id="$FOLDER_ID" \
  --read-only \
  --vfs-cache-mode full \
  --daemon

# Linux: use mount (requires FUSE)
# rclone mount "gdrive:" "$MOUNT_POINT" \
#   --drive-root-folder-id="$FOLDER_ID" \
#   --read-only \
#   --vfs-cache-mode full \
#   --daemon
```

Flags:
- `--read-only`: Prevent accidental writes to Google Drive
- `--vfs-cache-mode full`: Cache files locally as they're read (good performance
  for repeated access during inspection and conversion)
- `--daemon`: Run in background

**Step 5: Verify the mount.**

```bash
ls "$MOUNT_POINT"
```

Report what's visible:
> I've mounted your Google Drive folder at `~/source_data/`. Here's what I see:
> [file listing]

If the mount is empty or fails, check:
- Is the folder ID correct?
- Does the authenticated Google account have access to this folder?
- Is FUSE working? (`mount | grep rclone`)

**Step 6: Set the data path.**

The mount point is OUTSIDE the conversion repo (source data must never live inside
the repo). From this point forward, use the mount point's absolute path as the data
directory for all subsequent phases. Files accessed through this mount behave exactly
like local files — no code changes needed in inspection or conversion phases.

Record the absolute mount path for use in conversion code. For example, if the mount
is at `/home/user/source_data/`, all generated conversion scripts should reference
that path (or accept it as a configurable argument).

**Unmounting.** When the conversion is complete (after Phase 7 or when the user
is done), unmount with:
```bash
# macOS
umount ./source_data

# Linux
fusermount -u ./source_data
```

Record the data source in `conversion_notes.md`:
```
- Data source: Google Drive (<original_url>) → mounted at ./source_data/
```

### Opening Questions

Start with broad, open-ended questions. Don't ask all at once — ask 2-3, then follow up.

**First message should be something like:**
> I'd like to help you convert your data to NWB and publish it on DANDI. Let's start by
> understanding your experiment.
>
> 1. Can you briefly describe your experiment? What were you studying?
> 2. What types of neural recordings did you collect? (e.g., extracellular electrophysiology,
>    calcium imaging, intracellular recordings, etc.)
> 3. Did you also record behavioral data? (e.g., position tracking, video, licking, running speed)

**If the user provided a data path (local or mounted from Google Drive)**, inspect the directory structure FIRST:
```
ls -la <path>
find <path> -maxdepth 3 -type f | head -50
```
Then ask targeted questions based on what you see.

### Follow-up Questions (ask as needed)

**About recordings:**
- What recording system did you use? (e.g., SpikeGLX, OpenEphys, Intan, Blackrock, Neuralynx, Axona)
- How many probes/electrodes per session?
- Did you do spike sorting? What software? (Kilosort, Phy, CellExplorer, MountainSort)
- Is there LFP data separate from the raw recording?

**About imaging:**
- What microscope/acquisition software? (ScanImage, Scanbox, Bruker, Inscopix, Miniscope)
- One-photon or two-photon?
- Did you run segmentation? What software? (Suite2p, CaImAn, CNMFE, EXTRACT)
- Single plane or multi-plane?

**About behavior:**
- Is there pose estimation? (DeepLabCut, SLEAP, LightningPose)
- Video recordings? How many cameras?
- Trial structure? What defines a trial?
- Stimulus presentation? What software? (PsychoPy, Bpod, Arduino)
- Task events? (licks, rewards, tone presentations, etc.)

**About raw vs. processed data:**
- Are there processed/analyzed files in addition to raw data?
- If the user mentions or provides processed data (e.g., trialized MATLAB structs, averaged
  traces, pre-computed rate maps, data split by condition), ask whether the raw acquisition
  files are also available.
  > I notice the data appears to be processed — for example, split into trials / averaged
  > across conditions / saved as a custom .mat struct. Do you also have the raw files as
  > they came off the recording system (e.g., the original SpikeGLX .bin, OpenEphys .dat,
  > ScanImage .tif, etc.)? Raw acquisition files are ideal for NWB because they preserve
  > the full recording and are in a standardized format that our tools handle natively.
- If raw data is available, prefer it. Explain briefly why (standardized format, full time
  series, no assumptions about analysis).
- If raw data is NOT available (deleted, proprietary format only, contains PHI, etc.),
  that's fine — proceed with the processed data. Don't pressure the user.
- If the user isn't sure what they have, help them figure it out during Phase 2 inspection.

**About organization:**
- How are files organized? One folder per session? Per subject?
- Is there a naming convention?
- Approximately how many sessions total?

**About existing resources (always ask these):**
- Is there a manuscript, preprint, or published paper describing this data?
  (If yes, get the DOI or URL — this helps with experiment_description and related_publications)
- Is this data already publicly available in any non-NWB format? (e.g., on Figshare, Zenodo,
  institutional repository, or another archive)
- Do you have existing analysis code for this data? (e.g., MATLAB scripts, Python notebooks)
  These often reveal data structure, variable names, and processing steps that inform the conversion.
- Do you have any code that reads or converts this data to another format?
  (Existing readers save significant reverse-engineering effort)

### Fetching Publication Details

When the user provides a DOI, PMID, PMC ID, or publication URL, use the paper fetcher tool
to retrieve the full text (or abstract). This is extremely valuable for understanding the
experiment, data modalities, recording parameters, and subject details.

```bash
python3 tools/fetch_paper.py "<identifier>" --extract methods
```

The tool accepts DOIs (e.g., `10.1038/s41586-019-1234-5`), PMIDs (e.g., `31234567`),
PMC IDs (e.g., `PMC6789012`), or URLs from doi.org, PubMed, or PMC.

**What to extract from the paper:**
1. **Methods section** (`--extract methods`): Recording systems, file formats, number of
   subjects/sessions, experimental protocols, data acquisition parameters
2. **Abstract** (`--extract abstract`): High-level experiment description for `experiment_description`
3. **Full text** (no `--extract` flag): When you need comprehensive details

**How to use the information:**
- Pre-fill the experiment description from the abstract
- Identify data modalities and recording systems from methods
- Extract subject counts, species, and session details
- Find stimulus/behavioral task descriptions
- Get the DOI for `related_publications` (format: `"doi:10.xxxx/xxxxx"`)
- Look for mentions of data availability statements that may link to existing public data

After fetching, confirm key details with the user — papers may describe a larger study
than what the user is converting, or parameters may have changed.

**About subjects (collect early to plan per-subject metadata):**
- How many subjects are in this dataset?
- Do you have a spreadsheet or file with subject information?
- For each subject, we'll need: subject_id, date of birth (or age at each session),
  species (Latin binomial, e.g., "Mus musculus"), sex, genotype, and ideally weight.
- Are there different experimental groups (e.g., different genotypes, treatment vs. control)?

### What to Record

After this phase, update `conversion_notes.md` with:

```markdown
# Conversion Notes

## Experiment Overview
[Brief description of the experiment]

## Data Streams
| Stream | Format | Recording System | File Pattern | NeuroConv Interface? |
|--------|--------|-----------------|--------------|---------------------|
| Raw ephys | SpikeGLX .bin | Neuropixel | *_g0_t0.imec0.ap.bin | SpikeGLXRecordingInterface |
| LFP | SpikeGLX .bin | Neuropixel | *_g0_t0.imec0.lf.bin | SpikeGLXLFPInterface |
| Spike sorting | Phy | Kilosort+Phy | phy/ folder | PhySortingInterface |
| Behavior | .txt files | Custom | *position.txt, *licks.txt | Custom needed |

## Directory Structure
[Description or tree output]

## Sessions
- Number of subjects: X
- Number of sessions: ~Y
- Session naming convention: ...

## Existing Resources
- Publication: [DOI or "not yet published"]
- Existing public data: [URL or "none"]
- Analysis code: [URL or path or "none"]
- Existing data readers: [description or "none"]
- Data source: [local path / Google Drive: <url> → mounted at <mount_path>]

## Subjects
| subject_id | species | sex | date_of_birth | genotype | weight | group |
|------------|---------|-----|---------------|----------|--------|-------|
| ... | Mus musculus | M | 2019-10-22 | C57BL/6J | 25 g | control |

## Open Questions
- [ ] ...
```

### Push Phase 1 Results

After writing `conversion_notes.md`, commit and push:
```bash
git add conversion_notes.md
git commit -m "Phase 1: experiment discovery — data streams and directory structure"
if git remote get-url origin &>/dev/null; then git push; fi
```
