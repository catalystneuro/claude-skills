## Phase 6: Ontology Annotation

**Goal**: Link the free-text terms in the NWB files (species, strain, brain regions, body
parts, institution, experimenters) to entries in external ontologies and registries, so that a
reader or a tool can tell exactly what each one means.

**Entry**: The conversion code from Phase 5 exists, and the metadata from Phase 3 is in
`metadata.yaml` and the subject metadata file.

**Exit criteria**: `external_resources.yaml` lists a verified term for every value that has
one, the user has confirmed the ones that were ambiguous, and the converter writes them into
each file. Values with no suitable term are recorded in `conversion_notes.md`. The same holds
for `value_meanings.yaml` and the categorical columns it describes.

The links are stored inside each NWB file under `/general/external_resources` using HERD
(HDMF External Resources Data). Each reference ties a value as it is written in the file
(the key, e.g. `"CA1"`) to a compact identifier (`entity_id`, e.g. `MBA:382`) and a
resolvable URL (`entity_uri`). In-file HERD requires `pynwb>=4.0`. The mechanics, a tested
helper, and the lookup endpoints are in `knowledge/external-resources.md`. The NWB guide
[Using Ontologies and Identifiers with NWB](https://nwb-overview.readthedocs.io/en/latest/external_resources_entity_guide.html)
is the reference for which registry to use and what goes in `entity_id` and `entity_uri`.

This phase adds references next to the existing values. It does not change what is written
in `species`, `location`, or any other field.

Steps 5 to 7 do the same for the categorical columns of the file's tables (trial outcomes,
stimulus types, event codes): each value gets a written meaning, and where the vocabulary
allows, a HED annotation. Those are stored in a `MeaningsTable` beside the column. See
`knowledge/value-meanings.md`.

### Step 1: List the Values to Annotate

Collect the distinct values the conversion writes for each of these fields. They come from
several places: `metadata.yaml`, the subject metadata file if there is one, values set in
`convert_session.py`, and defaults the interfaces fill in (electrode `location` values,
pose-estimation body-part names). The reliable way to see all of them is to read them from
a file: if the Phase 5 code already runs, convert one session with `stub_test=True` and list
the values with the script in `knowledge/external-resources.md` ("Listing the Values in a
File"). If it does not run yet, collect what you can from the sources and reconcile in
Phase 7.

| Field | Registry | Example `entity_id` |
|-------|----------|---------------------|
| `Subject.species` | NCBITaxon | `NCBITaxon:10090` |
| `Subject.strain` | RRID (e.g. the JAX stock number) | `RRID:IMSR_JAX:000664` |
| Brain-region `location` fields, mouse | Allen Mouse Brain Atlas (MBA) | `MBA:382` |
| Brain-region `location` fields, human | Allen Human Brain Atlas (HBA) | `HBA:4005` |
| Brain-region `location` fields, other species | UBERON | `UBERON:0003881` |
| `location` fields outside the brain (e.g. an EMG muscle) | UBERON | `UBERON:0001388` |
| Body parts: `Skeleton.nodes` from `ndx-pose` | UBERON | `UBERON:0001467` |
| `NWBFile.institution` | ROR | `ROR:00f54p054` |
| `NWBFile.experimenter` | ORCID | `ORCID:0000-0002-1825-0097` |

Brain-region `location` fields include `ElectrodeGroup.location`, the `location` column of
the electrodes table, `ImagingPlane.location`, `IntracellularElectrode.location`,
`OptogeneticStimulusSite.location`, and the `location` column of a `FiberPhotometryTable`.

These are the fields with well-established registries. If another field in this dataset has
an obvious registered identifier, add it, using a prefix registered at
https://bioregistry.io. Do not force a term onto a value that has no good match.

### Step 2: Look Up Each Term

Look every identifier up in its registry. Do not write an identifier from memory: a wrong ID
that resolves to a different entity is worse than no annotation, and nothing downstream will
catch it. The lookup endpoints for each registry are in `knowledge/external-resources.md`.

For each value, record the `entity_id` as a CURIE (`prefix:identifier`) and the `entity_uri`
that `https://bioregistry.io/<entity_id>` redirects to, and check that the label the registry
returns matches what the lab meant.

- **Brain regions** depend on the species, because the same acronym can name different
  structures in different atlases. Use MBA for mouse and HBA for human. For other species,
  use UBERON. The atlas term is the one that matters. A value may also carry a UBERON
  term, which makes the file searchable across species, for example both `MBA:382` and
  `UBERON:0003881` for mouse CA1. Add it when searching UBERON for the atlas's full
  structure name returns a term with the same meaning, and skip it otherwise. This does
  not need a question to the user.
- **Regions the atlas does not have**: a value such as `"PFC"` for a mouse is not an Allen
  structure. Ask which structure was targeted. If the lab means the broad region, a UBERON
  term alone (`UBERON:0000451`, prefrontal cortex) is the right annotation.
- **Placeholders** such as `"unknown"` are not annotated.
- **Body parts** use UBERON for every species. Pose-estimation keypoints are usually named
  by the lab (`"EarL"`, `"left_shoulder"`, `"forepaw"`), so map each name to the structure it
  marks (ear, shoulder, manus). UBERON has no separate terms for left and right, so both
  sides get the same term. Keypoints that are not anatomy (an object, a port, a corner of
  the arena) are left unannotated.
- **Strain** needs the exact stock, not just the strain name. `C57BL/6J` from JAX and
  `C57BL/6N` from another vendor are different RRIDs. Take the stock number from the paper's
  methods or ask.
- **Institutions** often share a name or acronym with organizations in other countries
  (there are several records named "National Institutes of Health"), and the first search
  hit is frequently the wrong one. Read the record's metadata, not only its name: the
  country and city must be the lab's, and the record must be the organization itself, not
  a parent or child of it.
- **Experimenters** often share a name with other researchers, and common names return
  thousands of ORCID records. A name match alone is never enough, even when the search
  returns a single record. Take the ORCID from the lab's paper where it is listed.
  Otherwise accept a record only when its works include the lab's papers, or when its
  employment matches the lab itself (department, dates, and field), not just the
  institution. A large institution has many people with the same name. Ask when neither
  holds.

### Step 3: Confirm the Uncertain Ones with the User

A match is unambiguous when the registry's label, acronym, or a listed synonym is the value
itself: a Latin binomial, an exact atlas acronym, an institution whose ROR record has the
same name and the lab's country and city, a body part named for the structure (`"neck"`, `"left_shoulder"`), or an ORCID
listed for that author in the lab's paper or whose record lists the lab's paper. These do not need a question.

Ask about the rest in one batch, showing the candidate and its registry label. This
typically means region names that are not atlas terms (`"PFC"`), a strain without a stock
number, an experimenter whose ORCID is not in the paper and whose record cannot be tied to
the lab, and keypoint names whose meaning is not obvious:

> I'm linking the terms in your files to standard identifiers. Most were unambiguous, but
> I'd like to confirm three:
>
> 1. Location `"PFC"`: I'd use the Allen Mouse Brain Atlas term for prelimbic area (`PL`).
>    Is that the region you targeted, or was it broader?
> 2. Strain `C57BL/6J`: is this JAX stock 000664?
> 3. Experimenter "Smith, John": is this ORCID 0000-0000-0000-0000 (Stanford)?

If the user does not know or the value has no match, leave it unannotated and note it in
`conversion_notes.md`. An unannotated value is fine.

### Step 4: Record the Terms and Wire Them into the Converter

Write the terms to `external_resources.yaml` next to `metadata.yaml`, keyed by field and
then by the exact string written in the file:

```yaml
species:
  Mus musculus: {id: "NCBITaxon:10090", uri: "http://purl.obolibrary.org/obo/NCBITaxon_10090"}
strain:
  C57BL/6J: {id: "RRID:IMSR_JAX:000664", uri: "https://scicrunch.org/resolver/RRID:IMSR_JAX:000664"}
brain_regions:
  CA1:
    - {id: "MBA:382", uri: "https://purl.brain-bican.org/ontology/mbao/MBA_382"}
    - {id: "UBERON:0003881", uri: "http://purl.obolibrary.org/obo/UBERON_0003881"}
body_parts:
  left_shoulder: {id: "UBERON:0001467", uri: "http://purl.obolibrary.org/obo/UBERON_0001467"}
```

The top-level keys the helper reads are `species`, `strain`, `institution`, `experimenter`,
`brain_regions` (every `location` field), and `body_parts`.

A key only takes effect where the file carries the same string, so `"CA1"` in the YAML does
not annotate a location written as `"hippocampus CA1"`. Leave out a value that is still
waiting on an answer instead of adding it with an empty term.

Then add the helper from `knowledge/external-resources.md` to the conversion package and call
it from the converter's `add_to_nwbfile`, after the interfaces have added their data. The
same file documents the built-in support in newer NeuroConv versions, which should be used
for species and brain regions where it is installed.

Add a section to `conversion_notes.md` listing what was annotated, which values were left
without a term and why, and which matches the user confirmed. Include the ORCIDs and the
ROR ID that were found, because Phase 10 needs them again for the Dandiset contributors.

In stacked PRs mode, the helper, the hook in the converter, and the session-level terms
(species, strain, institution, experimenters) go on the `setup` branch. The brain-region
and body-part terms for a stream go on that stream's branch.

### Step 5: Write a Meaning for Each Categorical Value

A column such as a trial `result` holding `R`, `A`, `I`, and `F` is unreadable without the
task code. List the categorical columns of a stub file with the script in
`knowledge/value-meanings.md` ("Listing the Categorical Columns in a File"), then write one
sentence per value saying what it means.

- The meanings come from the lab: the task code, the paper's methods, a lab wiki, or the
  user. Do not work out what a code means from its letter or its column name. Expanding `A`
  to "abort" restates the label. What made a trial an abort and not a fail is the meaning,
  and only the lab knows it.
- Cover every value the column can take, including ones this session never used.
- Write each meaning so that a reader who has not seen the task can tell the values apart.
- Skip identifiers, free text, counts, and columns that a registry already covers (a
  `location` column has HERD references from Step 4).
- Events written by a NeuroConv events interface take their meanings in that interface's
  metadata (`event_description`, and `column_categories["meanings"]` for a value column).
  Put them there. The helper in Step 7 leaves those meanings as they are and adds to them.

Ask about the values you could not find a meaning for in one batch, showing what you have:

> A few columns hold codes I'd like to describe in the file so that others can read them:
>
> 1. Trial `result` is `R`, `A`, `I`, or `F`. I take these to be reward, abort, incomplete,
>    and fail. What ends a trial as an abort, as incomplete, and as a fail?
> 2. Trial `ctr_hold_bump` is true or false. Does true mean the handle was bumped during the
>    center hold, before the go cue?

If the user does not know what a value means, leave the column out and note it in
`conversion_notes.md`.

### Step 6: Annotate the Values with HED

HED (Hierarchical Event Descriptors) is a controlled vocabulary for events and experimental
conditions. A HED string beside a meaning lets a tool find, across datasets, the trials that
ended in a reward or the events that were a visual stimulus. Skip this step if `ndx-hed` is
not installed and cannot be installed. The meanings stand on their own.

For each value that describes what happened or under what condition:

1. Search the schema for tags, using the script in `knowledge/value-meanings.md` ("Finding
   HED Tags"). Do not write a tag from memory. A tag that is not in the schema is an error,
   and one that is in the schema but means something else is worse.
2. Write the string from the tags you found, following the conventions in the same file.
3. Validate it with the script in "Validating HED Strings" and fix every error and warning.
4. Read it back against the meaning. The validator checks that a string is well-formed,
   not that it says what the meaning says.

Annotate the meaning, not more. If the lab did not say what distinguishes an abort from a
fail, the HED cannot say it either: give both the tags they share and tell them apart with
`Label/Abort` and `Label/Fail`. Leave a value without HED when nothing in the vocabulary
describes it. That is the usual case for bookkeeping, such as which data split a trial
belongs to.

The user is not expected to review HED strings. Confirm the meanings with them in Step 5,
and record in `conversion_notes.md` that the HED was drafted from those meanings and checked
by the validator, not reviewed by a HED expert.

### Step 7: Record the Meanings and Wire Them into the Converter

Write them to `value_meanings.yaml` next to `external_resources.yaml`, keyed by table name,
then column name, then the value exactly as it is written in the file:

```yaml
hed_schema_version: "8.4.0"
tables:
  trials:
    result:
      R: {meaning: "The monkey reached the target and received a reward.", hed: "Experimental-trial, Correct-action, Reward"}
      A: {meaning: "The monkey left the center before the go cue, ending the trial.", hed: "Experimental-trial, Incorrect-action, Label/Abort"}
    ctr_hold_bump:
      true: {meaning: "The handle was bumped during the center hold, before the go cue.", hed: "Condition-variable/Center-hold-bump, (Somatic-presentation, Experimental-stimulus)"}
      false: {meaning: "The handle was not bumped during the center hold.", hed: "Condition-variable/No-center-hold-bump"}
    split:
      train: {meaning: "The trial is in the training split of the benchmark."}
      val: {meaning: "The trial is in the validation split of the benchmark."}
```

`hed` is optional for each value, and `hed_schema_version` is only needed when some value has
one. Use the schema version you searched and validated against. A boolean column is keyed by
`true` and `false`, and an integer code by the bare number.

Then add the helper from `knowledge/value-meanings.md` ("Writing the Meanings") to the
conversion package and call it from the same `add_to_nwbfile` override that writes the HERD
references. If any value has HED, add `ndx-hed` to the dependencies in `pyproject.toml`,
using the install line from the knowledge file.

Add to `conversion_notes.md` which columns were described, which values have HED, and which
were left out and why.

In stacked PRs mode, the helper and the hook go on the `setup` branch with an empty
`tables` map, and each stream's branch adds the entries for the tables that stream writes.

### Push Phase 6 Results

```bash
git add conversion_notes.md src/ pyproject.toml
git commit -m "Phase 6: ontology annotation with HERD references, value meanings, and HED"
if git remote get-url origin &>/dev/null; then git push; fi
```

Phase 7 checks that the references and the meanings were written when it inspects the stub
file.
