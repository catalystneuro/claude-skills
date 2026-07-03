## Phase 4: Metadata Collection

**Goal**: Gather all metadata required for a valid NWB file, with special attention
to Spyglass-required fields.

**Entry**: You know all data streams and interfaces from Phase 3.

**Baseline**: Follow **nwb-convert Phase 3** for the full metadata collection
workflow. All steps apply:

- **NWBFile fields** — `session_description`, `experiment_description`, `institution`,
  `lab`, `experimenter`, `keywords`, `related_publications` (DOI format)
- **Subject fields** — species (Latin binomial), sex, age (ISO 8601), subject_id,
  genotype, strain, weight, date_of_birth
- **Modality-specific metadata** — ecephys (probe model, brain regions, histology);
  ophys if applicable (indicator, excitation_lambda, location)
- **Auto-extracted metadata** — call `converter.get_metadata()` to see what interfaces
  already provide before asking the user
- **Per-subject YAML** — create `subject_metadata.yaml` keyed by subject_id when
  multiple subjects exist
- **Timezone** — `session_start_time` must include timezone; use `zoneinfo.ZoneInfo`

Track to `spyglass_notes.md`.

**Exit criteria**: You have complete metadata for NWBFile, Subject, Device, and
all Spyglass-required electrode/probe fields.

### Spyglass-Specific Additions to nwb-convert Phase 3

### Required NWB Metadata

**NWBFile:**
- `session_description` — what happened in this session (required)
- `experiment_description` — overall experiment description
- `institution` — university/institute name
- `lab` — PI's lab name
- `experimenter` — list as `["Last, First"]`
- `keywords`
- `related_publications` — DOI format: `"doi:10.xxxx/xxxxx"`

**Subject:**
- `species` — Latin binomial (e.g., "Mus musculus", "Rattus norvegicus")
- `sex` — "M", "F", "U", or "O"
- `subject_id` — unique identifier
- `age` — ISO 8601 duration: "P90D" (90 days), or use `date_of_birth`
- `genotype`, `strain`, `weight`

### Spyglass-Specific Metadata to Collect

In addition to standard NWB metadata, you need per-electrode Spyglass fields.
Ask the user for these if they are not derivable from the data files:

**Per-electrode:**
- `probe_shank` — shank index (0-indexed integer). For single-shank probes: all 0.
- `probe_electrode` — electrode number within shank (integer)
- `bad_channel` — is this electrode marked bad? (boolean, usually False)
- `ref_elect_id` — reference electrode ID for this channel (integer)
- `group_name` — tetrode/group name, must be `nTrode{N}` format (e.g., "nTrode1")
- `brain_area` — anatomical region (e.g., "CA1", "PFC", "unknown")

> For the electrode metadata, I need a few Spyglass-specific fields per electrode.
> Do you have a spreadsheet or config file that maps electrodes to brain regions,
> shanks, and reference channels? Alternatively, I can derive these from the
> probe geometry and any histology/targeting info you have.

**DataAcquisitionDevice:**

Spyglass requires device metadata. Ask:
> What recording system did you use? I'll need:
> - System name (e.g., "SpikeGadgets", "OpenEphys", "Intan")
> - Amplifier model (if known)
> - ADC circuit (if applicable)

See `knowledge/spyglass-nwb-requirements.md` for the DataAcquisitionDevice spec.

**Epoch/task structure:**

Spyglass populates `Task` and `TaskEpoch` tables from the NWB file's epoch/intervals.
Ask:
> Does your experiment have named epochs or task states that you want to query
> in Spyglass? (e.g., "sleep", "run", "rest") How are these defined in your data?

### Where Metadata Goes

Write to `metadata.yaml` in the conversion directory:

```yaml
NWBFile:
  experiment_description: >
    [from paper abstract or user description]
  institution: [e.g., "Boston University"]
  lab: [e.g., "Jadhav Lab"]
  experimenter:
    - Last, First
  keywords:
    - hippocampus
    - spatial memory
  related_publications:
    - doi:10.xxxx/xxxxx

Subject:
  species: Rattus norvegicus
  strain: Long-Evans
  sex: M
```

Session-specific metadata (subject_id, session_start_time) is set programmatically
in `convert_session.py`.

### Per-Subject Metadata

If multiple subjects, create `subject_metadata.yaml`:
```yaml
rat1:
  species: Rattus norvegicus
  strain: Long-Evans
  sex: M
  date_of_birth: "2021-03-15"
  weight: "0.350 kg"
rat2:
  species: Rattus norvegicus
  strain: Long-Evans
  sex: F
  date_of_birth: "2021-03-20"
  weight: "0.280 kg"
```

### Timezone

Session start times MUST include timezone:
```python
from zoneinfo import ZoneInfo
tz = ZoneInfo("America/New_York")
session_start_time = datetime(2022, 6, 1, 14, 30, tzinfo=tz)
```

### Push Phase 4 Results

```bash
git add spyglass_notes.md metadata.yaml subject_metadata.yaml 2>/dev/null
git commit -m "Phase 4: metadata collection"
```
