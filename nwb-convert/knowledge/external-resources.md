# External Resources (HERD)

Reference for Phase 6. HERD (HDMF External Resources Data) stores links from values in an NWB
file to entries in external ontologies and registries. With `pynwb>=4.0` the links are saved
inside the file under `/general/external_resources` and read back as
`nwbfile.external_resources`.

Background reading:

- NWB Overview, "Using Ontologies and Identifiers with NWB":
  https://nwb-overview.readthedocs.io/en/latest/external_resources_entity_guide.html
- PyNWB tutorial, "Linking to External Resources":
  https://pynwb.readthedocs.io/en/stable/tutorials/general/plot_external_resources.html
- PyNWB tutorial, "Annotating Multiple Streamed NWB Files with a Single HERD":
  https://pynwb.readthedocs.io/en/stable/tutorials/general/resources_streaming.html
- HDMF HERD tutorial:
  https://hdmf.readthedocs.io/en/stable/tutorials/plot_external_resources.html

## Anatomy of a Reference

```python
herd.add_ref(
    container=nwbfile.subject,   # the object that holds the value
    attribute="species",         # the field on that object (omit for a table column)
    key="Mus musculus",          # the value exactly as written in the file
    entity_id="NCBITaxon:10090", # CURIE: <bioregistry prefix>:<identifier>
    entity_uri="http://purl.obolibrary.org/obo/NCBITaxon_10090",
)
```

- `entity_id` is a CURIE whose prefix is registered at https://bioregistry.io.
- `entity_uri` is the URL that `https://bioregistry.io/<entity_id>` redirects to.
- For a column of a table (e.g. the `location` column of the electrodes table), pass the
  column itself as `container` and leave `attribute` out: `container=nwbfile.electrodes["location"]`.
- For one entry of an array attribute (e.g. a body part in an `ndx-pose` `Skeleton.nodes`),
  pass the object as `container`, the attribute name as `attribute`, and the entry as `key`.
- When one value gets several terms, pass the string as `key` for the first and the `Key`
  object for the rest. Passing the same string twice creates a second key and duplicates
  the references.
- An atlas with no per-region URL (e.g. the macaque D99 atlas) still gets a reference: put
  the atlas's own region ID in `entity_id` and the atlas landing page in `entity_uri`.

## Listing the Values in a File

Prints every value Phase 6 can annotate, read from a written file (a stub is enough):

```python
from hdmf.common import DynamicTable
from pynwb import NWBHDF5IO

with NWBHDF5IO("/path/to/output/session.nwb", "r") as io:
    nwbfile = io.read()
    print("institution:", nwbfile.institution)
    print("experimenter:", nwbfile.experimenter)
    if nwbfile.subject is not None:
        print("species:", nwbfile.subject.species)
        print("strain:", nwbfile.subject.strain)
    for neurodata_object in nwbfile.all_children():
        parent = neurodata_object.parent  # None for the NWBFile itself
        label = neurodata_object.name if parent is None else f"{parent.name}/{neurodata_object.name}"
        if isinstance(neurodata_object, DynamicTable) and "location" in neurodata_object.colnames:
            print(f"{label} location column:", sorted(set(neurodata_object["location"][:])))
        elif type(neurodata_object).__name__ == "Skeleton":
            print(f"{label} nodes:", list(neurodata_object.nodes))
        elif isinstance(getattr(neurodata_object, "location", None), str):
            print(f"{label} location:", neurodata_object.location)
```

Values differ between sessions (other subjects, other target regions), so also check the
metadata files for values this one session does not use.

## Looking Up Terms

Always look the identifier up, and read the returned label before accepting it. These
endpoints need no authentication.

**Species (NCBITaxon) and cross-species anatomy (UBERON)**, through the EBI Ontology Lookup
Service:

```bash
curl -s "https://www.ebi.ac.uk/ols4/api/search?q=Rattus%20norvegicus&ontology=ncbitaxon&exact=true&rows=3"
curl -s "https://www.ebi.ac.uk/ols4/api/search?q=CA1%20field%20of%20hippocampus&ontology=uberon&rows=5"
```

Each hit in `response.docs` has `obo_id` (the CURIE), `label`, and `iri` (the `entity_uri`).
`exact=true` ranks an exact match first but still returns other terms after it (hybrid taxa,
sub-structures), so take the hit whose `label` equals what you searched for, not simply the
first one.

**Body parts (UBERON)** use the same service. UBERON names structures anatomically, so the
everyday word is often not the label: searching `hand` returns phalanges, while the term
for the hand or forepaw is `manus` (`UBERON:0002398`), and the foot or hindpaw is `pes`
(`UBERON:0002387`). Search with `exact=true` first, and if no hit has the label of the
structure you meant, try the anatomical name.

To add a UBERON term next to an Allen atlas term, search UBERON for the atlas's full
structure name (`Ventral tegmental area` finds `UBERON:0002691`). The names often differ
(the Allen `Primary visual area` is the UBERON `primary visual cortex`), so do not judge by
the label. UBERON terms cross-reference the atlas structures they correspond to, which is
the test to use: fetch the candidate and check that its `obo_xref` lists the atlas ID.

```bash
curl -s "https://www.ebi.ac.uk/ols4/api/ontologies/uberon/terms?iri=http://purl.obolibrary.org/obo/UBERON_0002436" | python -c "
import json, sys
term = json.load(sys.stdin)['_embedded']['terms'][0]
print(term['obo_id'], '|', term['label'], '|', term.get('synonyms'))
print([f\"{x['database']}:{x['id']}\" for x in term.get('obo_xref') or [] if x.get('database') in ('MBA', 'HBA')])
"
```

This prints `['MBA:385']`, which confirms `UBERON:0002436` as the companion of `VISp`. When
no UBERON term cross-references the atlas structure, keep only the atlas term.

```bash
curl -s "https://www.ebi.ac.uk/ols4/api/search?q=shoulder&ontology=uberon&exact=true&rows=3"
```

**Mouse brain regions (MBA)**, through the Allen Brain Atlas API. `graph_id` 1 is the adult
mouse structure graph:

```bash
curl -s -g "https://api.brain-map.org/api/v2/data/Structure/query.json?criteria=[acronym\$eq'CA1'][graph_id\$eq1]"
```

The `id` of the hit is the MBA identifier: `MBA:382`, with
`entity_uri` `https://purl.brain-bican.org/ontology/mbao/MBA_382`. Use `[name$il'*visual*']`
to search by name instead of acronym. Human regions (HBA) use `graph_id` 10 and
`https://purl.brain-bican.org/ontology/hbao/HBA_<id>`.

**Institutions (ROR)**. Many organizations share a name or an acronym, so the name alone
does not identify a record and the first hit is often the wrong one. Searching
`National Institutes of Health` returns the Malaysian NIH ahead of the one in Bethesda, and
`NIH` matches national institutes in Thailand, Malaysia, Somalia, Pakistan, and Armenia, as
well as a hydrology institute in India and a sport sciences school in Norway. Print the metadata of
each candidate and choose the record whose country and city are the lab's:

```bash
curl -s "https://api.ror.org/v2/organizations?query=National%20Institutes%20of%20Health" | python -c "
import json, sys
result = json.load(sys.stdin)
print(result['number_of_results'], 'results')
for org in result['items'][:10]:
    names = {t: n['value'] for n in org['names'] for t in n['types']}
    place = org['locations'][0]['geonames_details']
    where = [place.get('name'), place.get('country_subdivision_name'), place.get('country_name')]
    parents = [r['label'] for r in org.get('relationships', []) if r['type'] == 'parent']
    print(org['id'], '|', names.get('ror_display'), '|', names.get('acronym'), '|', where, '|',
          org['status'], org['types'], '| parent:', parents)
"
```

Check each of these before accepting a record:

- **Location**: the country and city in `locations[].geonames_details` match where the lab
  is. When the country is known, narrow the search with
  `&filter=locations.geonames_details.country_code:US`.
- **Level**: `relationships` lists parents and children. A university, its medical school,
  and its institutes are often separate records (`Stanford University` and
  `Stanford Medicine`; the NIH and each of its institutes). Use the record for the
  organization named in `NWBFile.institution`, not a parent or child of it.
- **Status**: `status` is `active`. A `withdrawn` or `inactive` record usually names its
  successor in `relationships`; use the successor.
- **Kind**: `types` (`education`, `government`, `healthcare`, `facility`, `funder`) fits what
  the organization is.

The `id` of the chosen record is the `entity_uri` (`https://ror.org/01cwqze88`), and the
`entity_id` is `ROR:01cwqze88`.

**People (ORCID)**. A name does not identify a person. A search for a common name returns
hundreds or thousands of records (`Wei Zhang` returns more than 3,000), and a search that
returns a single record is not proof either, because the experimenter may have no ORCID at
all and the one hit may be someone else. Accept a record only when something other than the
name ties it to this lab. Work down this list and stop at the first source that settles it:

1. **The lab's paper.** Crossref lists the ORCIDs the authors supplied to the journal:

   ```bash
   curl -s "https://api.crossref.org/works/10.7554/eLife.78362" | python -c "
   import json, sys
   for author in json.load(sys.stdin)['message']['author']:
       print(author.get('family'), '|', author.get('given'), '|', author.get('ORCID'))
   "
   ```

   Not every author has one there. For the authors without one, go on to the next source.

2. **ORCID records that claim the lab's paper.** Search by the paper's DOI and match the
   names in the result. The search is case-sensitive and people store DOIs in either case,
   so search for the DOI as published and in lower case together. For this DOI the
   published form alone finds 3 of the 8 records:

   ```bash
   curl -s -H "Accept: application/json" \
     "https://pub.orcid.org/v3.0/expanded-search/?q=doi-self:(%2210.7554/eLife.78362%22+OR+%2210.7554/elife.78362%22)&rows=50"
   ```

   Search for the preprint's DOI as well if there is one.

3. **Name search, then check each candidate's record.** Narrow by the institution when the
   name is common, using the ROR ID found for it, since people spell the same employer in
   different ways ("NIH", "National Institutes of Health"):

   ```bash
   curl -s -H "Accept: application/json" \
     "https://pub.orcid.org/v3.0/expanded-search/?q=given-names:Jane+AND+family-name:Doe+AND+ror-org-id:%22https://ror.org/00f54p054%22&rows=10"
   ```

   Records without a ROR ID on the affiliation are missed by that filter, so also try
   `affiliation-org-name:%22Stanford+University%22` with the institution's full name and its
   acronym. `num-found` is the number of matching records, and each result lists `orcid-id`,
   `given-names`, `family-names`, and `institution-name`. Both filters match any affiliation
   the person has ever listed (including an award or a past degree), so they narrow the list
   without confirming anyone. For each remaining candidate, read the employment history and
   the works:

   ```bash
   curl -s -H "Accept: application/json" "https://pub.orcid.org/v3.0/0000-0002-1825-0097/employments"
   curl -s -H "Accept: application/json" "https://pub.orcid.org/v3.0/0000-0002-1825-0097/works"
   ```

   Employers are at `affiliation-group[].summaries[0].employment-summary` (`organization`,
   `department-name`, `role-title`, `start-date`, `end-date`), and work titles are at
   `group[].work-summary[0].title.title.value`.

   Accept the record when its works include the lab's papers. Sharing the employer is not
   enough by itself: a large institution employs many people with the same name, so the
   record must also fit the lab in some other way. That means the department or group is
   the lab's, the dates cover the experiment (an undated entry does not show this), and
   the works are in the lab's field. A record that shares only the employer goes to the
   user as a candidate, not into the file.

Search under the variants of the name as well (a short form of the given name, initials, a
different transliteration, a former family name). If no record can be tied to the lab, ask
the user for the ORCID or leave the experimenter unannotated. Do not pick the most plausible
of several candidates.

The `entity_id` is `ORCID:<orcid-id>` and the `entity_uri` is `https://orcid.org/<orcid-id>`.

**Strains (RRID)**: find the stock on the vendor's page (e.g. the JAX strain page shows
`RRID:IMSR_JAX:000664`), then confirm that
`https://scicrunch.org/resolver/RRID:IMSR_JAX:000664.json` returns the same strain. That URL
without `.json` is the `entity_uri`.

**Confirming any CURIE**: `https://bioregistry.io/<entity_id>` should redirect to the
`entity_uri` you recorded.

```bash
curl -s -o /dev/null -w "%{redirect_url}\n" "https://bioregistry.io/MBA:382"
```

## Writing the References

Add this module to the conversion package (e.g. `external_resources.py` next to the
converter). It reads the mapping from `external_resources.yaml` and writes a reference
wherever the file carries a matching value:

```python
from hdmf.common import DynamicTable
from pynwb import NWBFile
from pynwb.resources import HERD


def add_external_resources(nwbfile: NWBFile, terms: dict) -> None:
    """Write the terms in external_resources.yaml into the file as HERD references."""
    herd = nwbfile.external_resources
    is_new_herd = herd is None
    if is_new_herd:
        herd = HERD()
    elif nwbfile.get_read_io() is not None:
        return  # references already stored on disk cannot be extended

    def annotate(container, kind, value, attribute=None):
        found = (terms.get(kind) or {}).get(value) or []
        key = value
        for term in found if isinstance(found, list) else [found]:
            herd.add_ref(container=container, attribute=attribute, key=key, entity_id=term["id"], entity_uri=term["uri"])
            if isinstance(key, str):
                # Several terms for one value share one key; a second string key would duplicate the references.
                key = herd.get_key(key_name=value)
                key = key[-1] if isinstance(key, list) else key

    # Scalar fields of the file and the subject
    if nwbfile.institution:
        annotate(nwbfile, "institution", nwbfile.institution, attribute="institution")
    for experimenter in nwbfile.experimenter or []:
        annotate(nwbfile, "experimenter", experimenter, attribute="experimenter")
    if nwbfile.subject is not None:
        for field in ("species", "strain"):
            if getattr(nwbfile.subject, field, None):
                annotate(nwbfile.subject, field, getattr(nwbfile.subject, field), attribute=field)

    # Every anatomical `location` (table columns and scalar attributes) and every ndx-pose body part
    for neurodata_object in nwbfile.all_children():
        if isinstance(neurodata_object, DynamicTable) and "location" in neurodata_object.colnames:
            column = neurodata_object["location"]
            for value in dict.fromkeys(column.data):
                annotate(column, "brain_regions", value)
        elif type(neurodata_object).__name__ == "Skeleton":
            for value in dict.fromkeys(neurodata_object.nodes):
                annotate(neurodata_object, "body_parts", value, attribute="nodes")
        elif isinstance(getattr(neurodata_object, "location", None), str):
            annotate(neurodata_object, "brain_regions", neurodata_object.location, attribute="location")

    if is_new_herd and len(herd.keys) > 0:
        nwbfile.external_resources = herd
```

Call it from the converter, after the interfaces have added their data, so the electrodes
table and imaging planes exist:

```python
from pathlib import Path

from neuroconv import NWBConverter
from neuroconv.utils import load_dict_from_file

from .external_resources import add_external_resources


class <ConversionName>NWBConverter(NWBConverter):

    def add_to_nwbfile(self, nwbfile, metadata, conversion_options=None):
        super().add_to_nwbfile(nwbfile=nwbfile, metadata=metadata, conversion_options=conversion_options)
        terms = load_dict_from_file(Path(__file__).parent / "external_resources.yaml")
        add_external_resources(nwbfile=nwbfile, terms=terms)
```

To annotate a field the helper does not cover, add a branch for it that calls `annotate`
with the object and the attribute name, and add a matching top-level key to the YAML.

## Built-In Support in NeuroConv

NeuroConv versions after 0.10.2 ship `neuroconv.tools.external_resources`, which handles
species and brain regions without the helper. Check whether the installed version has it:

```bash
python -c "import neuroconv.tools.external_resources" 2>/dev/null && echo "built-in" || echo "use the helper"
```

When it is available:

- `infer_species_external_resources(nwbfile)` and
  `infer_brain_region_external_resources(nwbfile)` propose terms from the values in a
  populated `NWBFile`, using curated offline tables. Treat the result as candidates for
  Step 2 of the phase, not as a replacement for checking them.
- Terms placed in `metadata.yaml` under `ExternalResources`, with the maps `species` and
  `brain_regions` in the same shape as `external_resources.yaml`, are written by
  `run_conversion` automatically. Move those two maps there and keep the remaining fields
  (strain, institution, experimenters, body parts) in `external_resources.yaml` for the helper. The two
  compose: NeuroConv extends the HERD the helper created.

See https://neuroconv.readthedocs.io/en/main/user_guide/ontology.html.

## Annotating Files That Are Already Written

References are added when a file is first written. A file that already stores HERD
references on disk cannot take more (the helper above returns without changing it), and rewriting uploaded files only to add annotations is
rarely worth it. For a dataset that is already converted or published, build one standalone
HERD that covers every file and save it next to the dataset. The PyNWB tutorial linked at
the top does this for a Dandiset by streaming each file. The core of it is:

```python
from pynwb import NWBHDF5IO
from pynwb.resources import HERD

herd = HERD()
for nwbfile_path in nwbfile_paths:
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        # Check the value before annotating it, so a file with unexpected metadata is not mislabeled
        if nwbfile.subject.species == "Mus musculus":
            herd.add_ref(
                container=nwbfile.subject,
                attribute="species",
                key="Mus musculus",
                entity_id="NCBITaxon:10090",
                entity_uri="http://purl.obolibrary.org/obo/NCBITaxon_10090",
            )

herd.to_zip(path="external_resources.zip")  # reload later with HERD.from_zip(path=...)
```

The same `entity_id` used across files is stored once. `herd.to_dataframe()` then has one row
per file, object, key, and entity.

## Checking a Written File

```python
from pathlib import Path

from neuroconv.utils import load_dict_from_file
from pynwb import NWBHDF5IO

terms = load_dict_from_file(Path("src/<package>/<conversion>/external_resources.yaml"))
with NWBHDF5IO("/path/to/output/session.nwb", "r") as io:
    nwbfile = io.read()
    herd = nwbfile.external_resources  # None when no reference was written
    references = herd.to_dataframe() if herd is not None else None
    # Name each annotated object by its parent, so a table column reads as e.g. "electrodes/location"
    names = {}
    for neurodata_object in nwbfile.all_children():
        parent = neurodata_object.parent  # None for the NWBFile itself, which is named "root"
        name = neurodata_object.name if parent is None else f"{parent.name}/{neurodata_object.name}"
        names[neurodata_object.object_id] = name

written = set()
if references is not None:
    references["object"] = references["object_id"].map(names)
    print(references[["object", "relative_path", "key", "entity_id", "entity_uri"]].to_string())
    written = set(references["key"])

expected = {value for values in terms.values() for value in values or {}}
print("In external_resources.yaml but not written:", sorted(expected - written))
```

A value listed as not written means the string in the YAML does not match the string in the
file. Fix the YAML key, not the file, unless the value in the file is itself wrong. A value
that applies only to other sessions (a region recorded in a different animal) will also be
listed, which is expected.
