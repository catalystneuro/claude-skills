## Phase 1: Requirements Gathering

**Goal**: Understand what data the user needs to store and whether an extension is the right solution.

**Entry**: User invokes `/ndx-builder`, possibly with an extension name or existing repo path.

**Exit criteria**: You have a clear understanding of:
- What data needs to be stored that NWB core doesn't support
- Whether an existing published extension already covers the need
- What NWB core types are closest to the desired functionality
- A preliminary list of new neurodata types needed

### Step 1: Determine if an Extension is Needed

Many users think they need an extension when NWB core already supports their data.
Before building anything, verify the need.

Ask the user:
> What data do you need to store in NWB that you're unable to store currently?
> Can you describe the data — what it represents, its structure (arrays, tables, metadata),
> and how it relates to the rest of the experiment?

**Check NWB core types first.** Review `knowledge/nwb-core-types.md` and determine if
the data fits into:
- **TimeSeries** subtypes (ElectricalSeries, OpticalSeries, etc.)
- **DynamicTable** (for tabular data)
- **TimeIntervals** (for trial/epoch data)
- **LabMetaData** (for session-level custom metadata)
- **Processing modules** with existing container types

If core NWB can handle it, tell the user:
> This data can actually be stored using NWB's built-in [type]. You don't need an extension.
> Would you like help writing code to store this data using [type]?

### Step 2: Search for Existing Extensions

Check the NDX Catalog for existing extensions that might already solve the problem.

```bash
# Search the NDX Catalog
python3 -c "
import urllib.request, json
url = 'https://raw.githubusercontent.com/nwb-extensions/nwb-extensions.github.io/main/data/records.json'
try:
    with urllib.request.urlopen(url) as resp:
        records = json.loads(resp.read())
    for name, info in records.items():
        print(f'{name}: {info.get(\"description\", \"\")}')
except Exception as e:
    print(f'Could not fetch catalog: {e}')
"
```

Also check PyPI for `ndx-` packages:

```bash
pip index versions ndx-<suspected-name> 2>/dev/null || echo "Not found on PyPI"
```

If an existing extension covers the use case:
> There's an existing extension called `ndx-<name>` that handles this. Let me show you
> how to use it. Would you prefer to use the existing extension or build a new one?

### Step 3: Gather Requirements

Once confirmed that a new extension is needed, gather detailed requirements.

**About the data:**
- What are the individual data elements? (signals, metadata, tables, etc.)
- What are their data types? (float arrays, strings, integers, timestamps)
- What are the shapes/dimensions? (1D time series, 2D arrays, tables with N rows)
- Which fields are required vs optional?
- Are there relationships between the data elements? (e.g., a table row references a device)

**About the context:**
- Where does this data come from? (acquisition system, analysis pipeline, manual annotation)
- How many instances per NWB file? (one per session, one per trial, multiple per electrode)
- Where should it live in the NWB file? (acquisition, processing module, lab_meta_data)
- Who will use this extension? (just this lab, or the broader community)

**About existing data:**
- Do you have example data files? (helps validate the design)
- Is there existing code that reads/writes this data? (helps understand the structure)

### Step 4: Identify Base Types

Based on the requirements, determine which NWB core types to extend:

```
What kind of data?
├── Session-level metadata → LabMetaData
├── Time-varying signals → TimeSeries (or subtype)
├── Tabular data → DynamicTable
├── Container for related objects → NWBDataInterface
├── Hardware description → Device
└── Multiple of above → Design a type hierarchy
```

Consult `knowledge/nwb-core-types.md` for detailed guidance.

### Step 5: Document Requirements

Create or update a `design_notes.md` file:

```markdown
# Extension Requirements

## Extension Name
ndx-<name>

## Motivation
[Why is this extension needed? What data can't be stored in NWB core?]

## Data Elements
| Element | Type | Shape | Required | Description |
|---------|------|-------|----------|-------------|
| signal | float64 array | (T, C) | Yes | Recorded signal |
| labels | text array | (C,) | Yes | Channel labels |
| device | Device link | - | No | Recording device |

## Relationships
- [How elements relate to each other]
- [References to NWB core objects]

## NWB Core Types to Extend
- LabMetaData (for ...)
- TimeSeries (for ...)
- DynamicTable (for ...)

## Open Questions
- [ ] ...
```

### When to Use LabMetaData vs Processing Module

This comes up frequently. Guide the user:

| Data Type | Where It Goes | Extend This |
|-----------|---------------|-------------|
| Session-level metadata (surgery, protocol, training) | `nwbfile.lab_meta_data` | `LabMetaData` |
| Processed data results | `nwbfile.processing["module"]` | `NWBDataInterface` |
| Raw acquired data | `nwbfile.acquisition` | `TimeSeries` or subtype |
| Hardware specs | `nwbfile.devices` | `Device` |
| Tabular data with custom columns | Depends on context | `DynamicTable` |
