## Phase 2: Experiment Discovery

**Goal**: Build a complete picture of the experiment, data modalities, and file
organization, with attention to what Spyglass needs to ingest.

**Entry**: Spyglass environment is running from Phase 1.

**Baseline**: Follow **nwb-convert Phase 1** for the full intake workflow. All steps apply:

- **Step 0a** (uv environment) — set up the venv here; activate it throughout all phases
- **Step 0b** (conversion repo + registry) — create the repo, consult the nwb-conversions
  registry for similar prior conversions, seed `.gitignore`
- **Step 0c** (Google Drive) — if data is on Drive, mount via rclone before inspection
- **Opening questions** — ask about experiment, recordings, behavior, existing code
- **Fetching publication details** — use `tools/fetch_paper.py` if a DOI is available
- **Subject metadata collection** — collect per-subject YAML early

Track notes in `spyglass_notes.md` instead of `conversion_notes.md`.

**Exit criteria**: You have a `spyglass_notes.md` covering:
- All data streams and file formats
- Which streams Spyglass needs to ingest (ephys, LFP, behavior, video)
- Directory structure and session organization
- Any known Spyglass compatibility concerns for the data formats

### Spyglass-Specific Additions to nwb-convert Phase 1

### Step 0: Create Conversion Repo

Create a local repo for the conversion code (same as nwb-convert but note the
venv is created here for use in Phase 1's environment setup):

```bash
LAB_NAME="<lab-name>"
REPO_NAME="${LAB_NAME}-to-nwb"
mkdir "${REPO_NAME}" && cd "${REPO_NAME}"
git init

cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
*.egg
*.nwb
nwb_output/
nwb_stub/
.env
*.log
.DS_Store
Thumbs.db
.vscode/
.idea/
dj_local_conf.json
EOF

git add .gitignore
git commit -m "Initial commit: add .gitignore"
```

**The conversion repo must NOT contain source data.** Create it in a separate
directory from the data. Never copy or symlink data files into the repo.

**Note**: `dj_local_conf.json` is in `.gitignore` because it contains database
credentials. Never commit it.

### Opening Questions

Ask 2–3 questions at a time, then follow up.

> I'd like to understand your experiment before we start the conversion.
>
> 1. Can you briefly describe your experiment? What were you studying and what
>    was the behavioral task?
> 2. What types of neural recordings did you collect?
> 3. Did you also record behavioral data (position, video, DIO events, etc.)?

**If the user provided a data path**, inspect it first:
```bash
ls -la <path>
find <path> -maxdepth 3 -type f | head -50
```

### Spyglass-Specific Intake

In addition to the standard experiment questions, determine which data streams
Spyglass needs to ingest. Ask:

> For Spyglass ingestion, I need to know which data will be queried through the
> database. Typically this includes:
> - Raw electrophysiology (for Spyglass's Raw table)
> - LFP (for the LFP pipeline)
> - Spike sorting output (for the SpikeSorting pipeline)
> - Behavioral events / DIO signals
> - Video (for the Video pipeline)
>
> Are all of these present in your dataset? Anything else I should know about?

### Follow-up Questions

**About ephys:**
- What recording system? (SpikeGLX, OpenEphys, Intan, Neuralynx, etc.)
- Neuropixels or tetrodes?
- How many probes per session?
- Is there separate LFP data?
- Did you run spike sorting? What software? (Kilosort, Phy, etc.)

**About behavior:**
- DIO channels? (task events, rewards, tones, licks)
- Position tracking? (how many cameras, LED tracking or camera-based?)
- Video recordings? (how many cameras, file format)
- Task structure? (trials, epochs, states)

**About subjects and sessions:**
- How many subjects?
- How many sessions per subject?
- File organization: one folder per session? per subject?

**About existing resources:**
- Is there a manuscript or preprint? (get DOI for metadata)
- Do you have existing analysis code? (helps understand data structure)

### What to Record

Create `spyglass_notes.md`:

```markdown
# Spyglass Conversion Notes

## Experiment Overview
[Brief description]

## Data Streams
| Stream | Format | Recording System | File Pattern | Spyglass Pipeline |
|--------|--------|-----------------|--------------|-------------------|
| Raw ephys | SpikeGLX .bin | Neuropixels | *imec0.ap.bin | Raw |
| LFP | SpikeGLX .bin | Neuropixels | *imec0.lf.bin | LFP |
| Spike sorting | Phy | Kilosort+Phy | phy/ | SpikeSorting |
| DIO events | SpikeGLX NIDQ | — | *nidq.bin | DIOEvents |
| Position | CSV | custom | *position.csv | — |
| Video | MP4 | camera | *.mp4 | VideoFile |

## Spyglass Ingestion Targets
- [ ] Raw ephys → Raw table
- [ ] LFP → ImportedLFP / LFPOutput
- [ ] Spike sorting → (manual post-insertion)
- [ ] DIO events → DIOEvents
- [ ] Position → (custom processing post-insertion)
- [ ] Video → VideoFile

## Directory Structure
[tree output or description]

## Sessions
- Number of subjects: X
- Sessions per subject: ~Y
- Session naming convention: ...

## Open Questions
- [ ] ...
```

### Push Phase 2 Results

```bash
git add spyglass_notes.md
git commit -m "Phase 2: experiment discovery"
```
