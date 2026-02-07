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

**If the user provided a data path**, inspect the directory structure FIRST:
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

**About organization:**
- How are files organized? One folder per session? Per subject?
- Is there a naming convention?
- Are there processed/analyzed files in addition to raw data?
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

## Subjects
| subject_id | species | sex | date_of_birth | genotype | weight | group |
|------------|---------|-----|---------------|----------|--------|-------|
| ... | Mus musculus | M | 2019-10-22 | C57BL/6J | 25 g | control |

## Open Questions
- [ ] ...
```
