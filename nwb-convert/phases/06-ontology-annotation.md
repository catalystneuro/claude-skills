## Phase 6: Ontology Annotation

**Goal**: Link the free-text terms in the NWB files (species, strain, brain regions, body
parts, institution, experimenters) to entries in external ontologies and registries, so that a
reader or a tool can tell exactly what each one means.

**Entry**: The conversion code from Phase 5 exists, and the metadata from Phase 3 is in
`metadata.yaml` and the subject metadata file.

**Exit criteria**: `external_resources.yaml` lists a verified term for every value that has
one, the user has confirmed the ones that were ambiguous, and the converter writes them into
each file. Values with no suitable term are recorded in `conversion_notes.md`.

The links are stored inside each NWB file under `/general/external_resources` using HERD
(HDMF External Resources Data). Each reference ties a value as it is written in the file
(the key, e.g. `"CA1"`) to a compact identifier (`entity_id`, e.g. `MBA:382`) and a
resolvable URL (`entity_uri`). In-file HERD requires `pynwb>=4.0`. The mechanics, a tested
helper, and the lookup endpoints are in `knowledge/external-resources.md`. The NWB guide
[Using Ontologies and Identifiers with NWB](https://nwb-overview.readthedocs.io/en/latest/external_resources_entity_guide.html)
is the reference for which registry to use and what goes in `entity_id` and `entity_uri`.

This phase adds references next to the existing values. It does not change what is written
in `species`, `location`, or any other field.

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
- **Placeholders** such as `"unknown"` are not annotated.
- **Body parts** use UBERON for every species. Pose-estimation keypoints are usually named
  by the lab (`"EarL"`, `"left_shoulder"`, `"forepaw"`), so map each name to the structure it
  marks (ear, shoulder, manus). UBERON has no separate terms for left and right, so both
  sides get the same term. Keypoints that are not anatomy (an object, a port, a corner of
  the arena) are left unannotated.
- **Strain** needs the exact stock, not just the strain name. `C57BL/6J` from JAX and
  `C57BL/6N` from another vendor are different RRIDs. Take the stock number from the paper's
  methods or ask.
- **Experimenters** often share a name with other researchers. Prefer the ORCID printed in
  the paper. Otherwise match on affiliation and on the works listed in the ORCID record,
  and ask when neither settles it.

### Step 3: Confirm the Uncertain Ones with the User

A match is unambiguous when the registry's label, acronym, or a listed synonym is the value
itself: a Latin binomial, an exact atlas acronym, an institution whose name is the ROR
display name, a body part named for the structure (`"neck"`, `"left_shoulder"`), or an ORCID
printed in the paper. These do not need a question.

Ask about the rest in one batch, showing the candidate and its registry label. This
typically means region names that are not atlas terms (`"PFC"`), a strain without a stock
number, an experimenter whose ORCID is not in the paper or whose record lists a different
affiliation, and keypoint names whose meaning is not obvious:

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

### Push Phase 6 Results

```bash
git add conversion_notes.md src/
git commit -m "Phase 6: ontology annotation with HERD references"
if git remote get-url origin &>/dev/null; then git push; fi
```

Phase 7 checks that the references were written when it inspects the stub file.
