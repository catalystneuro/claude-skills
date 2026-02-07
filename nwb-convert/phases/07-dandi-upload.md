## Phase 7: DANDI Upload

**Goal**: Upload validated NWB files to the DANDI Archive for public sharing.

**Entry**: All NWB files are converted, validated with nwbinspector, and ready for sharing.

**Exit criteria**: Data is uploaded to DANDI, organized correctly, and accessible via the Dandiset URL.

### Prerequisites

Before uploading, the user needs:
1. A DANDI account (https://dandiarchive.org)
2. A DANDI API key (from user profile on dandiarchive.org)
3. A Dandiset created on the archive (or you help them create one)
4. The `dandi` CLI installed (`pip install -U dandi`)

### Step 1: Create a Dandiset

Guide the user through creating a Dandiset on the DANDI Archive:

> Before we upload, we need to create a Dandiset on DANDI Archive. Have you already
> created one? If not, here's how:
>
> 1. Go to https://dandiarchive.org and log in (or create an account)
> 2. Click "New Dandiset" in the top right
> 3. Fill in the metadata:
>    - **Name**: A descriptive title for your dataset
>    - **Description**: Abstract or summary of the dataset
>    - **License**: Usually CC-BY-4.0 for open data
>    - **Contributors**: Add all contributors with their ORCID IDs
> 4. Note the 6-digit Dandiset ID (e.g., "000123")

If the data should be embargoed (not publicly visible yet):
> If your data needs to be embargoed (e.g., pending publication), select the
> embargo option when creating the Dandiset. Embargoed data is only visible
> to Dandiset owners until you release it.

### Step 2: Set Up API Key

```bash
# Get your API key from https://dandiarchive.org (click your initials → API Key)
export DANDI_API_KEY=<your-key-here>
```

> You'll need your DANDI API key. Go to https://dandiarchive.org, click your
> initials in the top right, and copy your API key. Then set it as an environment
> variable:
> ```bash
> export DANDI_API_KEY=your_key_here
> ```

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

NeuroConv provides `automatic_dandi_upload()` which handles download, organize, and upload:

```python
from neuroconv.tools.data_transfers import automatic_dandi_upload

automatic_dandi_upload(
    dandiset_id="000123",           # 6-digit Dandiset ID
    nwb_folder_path="./nwb_output", # Folder with all NWB files
    sandbox=False,                   # True for testing on sandbox server
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
from pathlib import Path
from dandi.dandiapi import DandiAPIClient

client = DandiAPIClient.from_environ()  # or DandiAPIClient(api_url="https://api.sandbox.dandiarchive.org/api")
client.dandi_authenticate()
dandiset = client.get_dandiset("000123", "draft")

# Upload each organized NWB file
nwb_dir = Path("./000123")
for nwb_path in sorted(nwb_dir.rglob("*.nwb")):
    asset_path = str(nwb_path.relative_to(nwb_dir))
    print(f"Uploading {asset_path}...")
    for status in dandiset.iter_upload_raw_asset(nwb_path, asset_metadata={"path": asset_path}):
        if isinstance(status, dict) and status.get("status") == "done":
            print(f"  Done: {status['asset'].path}")
```

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
> When you're ready to publish (make it permanently citable with a DOI),
> click "Publish" on the Dandiset page. This creates an immutable version.

### Step 7: Edit Dandiset Metadata

After uploading, programmatically populate the Dandiset metadata using the DANDI API.
If there is an associated manuscript, use OpenAlex to auto-populate contributors, funders,
and affiliations.

> Now let's complete your Dandiset metadata so it's ready for publication.
> Is there an associated publication or preprint? If so, please share the DOI
> (e.g., `10.1038/s41586-023-06031-6`).

#### 7a. Fetch Structured Data from OpenAlex

If the user provides a DOI, query OpenAlex to get authors, ORCIDs, affiliations, ROR IDs,
and funding info:

```python
import requests

doi = "10.1038/s41467-023-43250-x"  # user-provided
response = requests.get(f"https://api.openalex.org/works/doi:{doi}")
work = response.json()

# Title
title = work["title"]

# Authors with ORCIDs, affiliations, and ROR IDs
for authorship in work["authorships"]:
    author = authorship["author"]
    name = author["display_name"]           # e.g., "Steffen Schneider"
    orcid = author.get("orcid")             # e.g., "https://orcid.org/0000-0003-2327-6459"
    is_corresponding = authorship["is_corresponding"]
    for inst in authorship.get("institutions", []):
        inst_name = inst["display_name"]    # e.g., "Columbia University"
        inst_ror = inst.get("ror")          # e.g., "https://ror.org/00hj8s172"

# Funders with ROR IDs and award numbers
# NOTE: OpenAlex grants are often empty — check the paper's acknowledgments section
# and ask the user to confirm funding information
for grant in work.get("grants", []):
    funder_name = grant["funder_display_name"]  # e.g., "National Institute of Mental Health"
    funder_ror = grant.get("funder", {}).get("ror")  # e.g., "https://ror.org/04xeg9z08"
    award_id = grant.get("funder_award_id")     # e.g., "R21MH117788"
```

Present the extracted data to the user for confirmation:

> I found the following from OpenAlex for your paper "{title}":
>
> **Authors:**
> 1. Last, First (ORCID: 0000-...) — Institution (ROR: ...)
> 2. ...
>
> **Funding:**
> 1. Agency Name — Award: XYZ123 (ROR: ...)
>
> Does this look correct? Should I add or remove anyone? Who should be the contact person?

#### 7b. Validate Identifiers

Before applying any metadata, validate all ORCID and ROR identifiers against their
respective APIs to prevent bad data from being committed:

```python
def validate_orcid(orcid: str) -> bool:
    """Validate ORCID exists. orcid should be bare ID like '0000-0001-2345-6789'."""
    resp = requests.head(
        f"https://pub.orcid.org/v3.0/{orcid}",
        headers={"Accept": "application/json"},
    )
    return resp.status_code == 200

def validate_ror(ror_url: str) -> bool:
    """Validate ROR ID exists. ror_url like 'https://ror.org/01cwqze88'."""
    ror_id = ror_url.replace("https://ror.org/", "")
    resp = requests.get(f"https://api.ror.org/organizations/{ror_id}")
    return resp.status_code == 200
```

Run validation on all extracted identifiers and warn the user about any that fail:

```python
for authorship in work["authorships"]:
    orcid = authorship["author"].get("orcid", "").replace("https://orcid.org/", "")
    if orcid and not validate_orcid(orcid):
        print(f"WARNING: ORCID {orcid} for {authorship['author']['display_name']} not found")

    for inst in authorship.get("institutions", []):
        ror = inst.get("ror")
        if ror and not validate_ror(ror):
            print(f"WARNING: ROR {ror} for {inst['display_name']} not found")
```

#### 7c. Look Up Ontology Terms for the `about` Field

Use the EBI Ontology Lookup Service (OLS4) to find proper ontology identifiers for brain
regions, disorders, and cell types. Never guess or fabricate ontology identifiers.

```python
def lookup_ontology_term(term: str, ontology: str = "uberon") -> list[dict]:
    """Search EBI OLS4 for an ontology term.

    ontology: 'uberon' (anatomy), 'doid' (disease), 'cl' (cell type)
    """
    resp = requests.get(
        "https://www.ebi.ac.uk/ols4/api/search",
        params={"q": term, "ontology": ontology, "rows": "5", "queryFields": "label,synonym"},
    )
    results = resp.json().get("response", {}).get("docs", [])
    return [{"label": r["label"], "iri": r["iri"], "obo_id": r.get("obo_id")} for r in results]

# Example: look up "hippocampus"
terms = lookup_ontology_term("hippocampus", "uberon")
# → [{"label": "hippocampal formation", "iri": "http://purl.obolibrary.org/obo/UBERON_0002421",
#      "obo_id": "UBERON:0002421"}, ...]
```

Present results to the user and add confirmed terms to `about`:
```python
metadata["about"] = [
    {
        "schemaKey": "Anatomy",
        "name": "hippocampal formation",
        "identifier": "UBERON:0002421",
    },
]
```

Supported ontology → `schemaKey` mapping:
| Ontology | `schemaKey` | Use for |
|----------|-------------|---------|
| UBERON | `Anatomy` | Brain regions, anatomical structures |
| DOID | `Disorder` | Diseases, disorders |
| CL | `Anatomy` | Cell types |
| HP | `Disorder` | Human phenotypes |

#### 7d. Build the Metadata and Set via DANDI API

Use the `dandi` Python client to programmatically update the Dandiset metadata.

**IMPORTANT**: Never call `set_raw_metadata()` directly — it accepts invalid metadata silently.
Always use this `validate_and_save` wrapper that validates against the DANDI JSON schema first:

```python
import requests, jsonschema
from dandi.dandiapi import DandiAPIClient

def validate_and_save(dandiset, metadata):
    """Validate metadata against DANDI schema, then save. Raises on invalid metadata."""
    schema_version = metadata["schemaVersion"]
    schema_url = f"https://raw.githubusercontent.com/dandi/schema/refs/heads/master/releases/{schema_version}/dandiset.json"
    schema = requests.get(schema_url).json()

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(metadata), key=lambda e: list(e.absolute_path))
    if errors:
        print(f"Schema validation FAILED ({len(errors)} errors):")
        for err in errors:
            path = ".".join(str(p) for p in err.absolute_path)
            print(f"  {path}: {err.message}")
        raise ValueError("Fix validation errors before saving")

    dandiset.set_raw_metadata(metadata)
    ds_id = metadata.get("identifier", "").replace("DANDI:", "")
    print(f"Metadata validated and saved!")

client = DandiAPIClient.from_environ()  # uses DANDI_API_KEY env var
dandiset = client.get_dandiset("000123", "draft")
metadata = dandiset.get_raw_metadata()
```

**Set title and description:**
```python
metadata["name"] = title  # from OpenAlex or user
metadata["description"] = description  # paper abstract or user-provided
metadata["keywords"] = ["hippocampus", "electrophysiology", "place cells"]  # user-provided
```

**Set contributors (persons):**
Convert OpenAlex author names from "First Last" to "Last, First" format. Mark the
corresponding author as ContactPerson. Mark all authors with `includeInCitation: True`.

```python
contributors = []
for authorship in work["authorships"]:
    author = authorship["author"]
    display_name = author["display_name"]
    # Convert "First Last" → "Last, First"
    parts = display_name.rsplit(" ", 1)
    dandi_name = f"{parts[-1]}, {parts[0]}" if len(parts) == 2 else display_name

    orcid = author.get("orcid", "").replace("https://orcid.org/", "")
    roles = ["dcite:Author"]
    if authorship["is_corresponding"]:
        roles.append("dcite:ContactPerson")

    person = {
        "schemaKey": "Person",
        "name": dandi_name,
        "roleName": roles,
        "includeInCitation": True,
    }
    if orcid:
        person["identifier"] = orcid
    # Add email for contact person (ask user)
    if authorship["is_corresponding"]:
        person["email"] = contact_email  # must ask user for this

    # Add affiliation — IMPORTANT: schemaKey must be "Affiliation", not "Organization"
    # "Organization" is for top-level contributors (funders); "Affiliation" is for person affiliations
    affiliations = []
    for inst in authorship.get("institutions", []):
        aff = {
            "schemaKey": "Affiliation",
            "name": inst["display_name"],
        }
        if inst.get("ror"):
            aff["identifier"] = inst["ror"]
        affiliations.append(aff)
    if affiliations:
        person["affiliation"] = affiliations

    contributors.append(person)
```

**Add data curators (the people who performed the conversion):**

Data curators are NOT authors — they get `dcite:DataCurator` role only, and
`includeInCitation: False` unless they made intellectual contributions to the dataset.

```python
# Add each person who worked on the NWB conversion
contributors.append({
    "schemaKey": "Person",
    "name": "Last, First",  # person who ran the conversion
    "identifier": "0000-0001-2345-6789",  # their ORCID
    "roleName": ["dcite:DataCurator"],
    "includeInCitation": False,
    "email": "curator@example.com",
    "affiliation": [{"schemaKey": "Affiliation", "name": "CatalystNeuro"}],
})
```

**Add funders as Organization contributors:**
```python
for grant in work.get("grants", []):
    funder = {
        "schemaKey": "Organization",
        "name": grant["funder_display_name"],
        "roleName": ["dcite:Funder"],
        "includeInCitation": False,
    }
    if grant.get("funder", {}).get("ror"):
        funder["identifier"] = grant["funder"]["ror"]
    if grant.get("funder_award_id"):
        funder["awardNumber"] = grant["funder_award_id"]
    contributors.append(funder)
```

**Set contributors on metadata:**
```python
metadata["contributor"] = contributors
```

**Add related resources:**
```python
related = []

# Associated publication
related.append({
    "schemaKey": "Resource",
    "identifier": f"doi:{doi}",
    "url": f"https://doi.org/{doi}",
    "name": title,
    "relation": "dcite:IsDescribedBy",
    "resourceType": "dcite:JournalArticle",  # or dcite:Preprint
})

# Conversion code repo (if on GitHub)
related.append({
    "schemaKey": "Resource",
    "url": "https://github.com/catalystneuro/lab-to-nwb",
    "name": "NWB conversion code",
    "relation": "dcite:IsSupplementedBy",
    "resourceType": "dcite:Software",
})

metadata["relatedResource"] = related
```

**Add ontology terms to `about` (from 7c results):**
```python
metadata["about"] = [
    {"schemaKey": "Anatomy", "name": "hippocampal formation", "identifier": "UBERON:0002421"},
    # add more terms as appropriate for the experiment
]
```

**Add ethics approval (ask user):**
```python
metadata["ethicsApproval"] = [{
    "schemaKey": "EthicsApproval",
    "identifier": "IACUC Protocol #12345",  # ask user
    "contactPoint": {
        "schemaKey": "ContactPoint",
        "name": "Columbia University IACUC",  # ask user
    },
}]
```

**Set license and access:**
```python
metadata["license"] = ["spdx:CC-BY-4.0"]
metadata["access"] = [{
    "schemaKey": "AccessRequirements",
    "status": "dandi:OpenAccess",
}]
```

**Validate and save (uses the wrapper defined above — never call `set_raw_metadata` directly):**
```python
validate_and_save(dandiset, metadata)
```

#### 7e. Metadata Quality Checklist

Before saving, verify the metadata covers all quality criteria:

- [ ] Is the title descriptive and publication-quality?
- [ ] Does the description mention data modalities and recording methods?
- [ ] Does the description include a brief methodology summary?
- [ ] Are associated publications linked with DOIs and correct relation (`dcite:IsDescribedBy`)?
- [ ] Are all paper authors listed as contributors with ORCIDs?
- [ ] Do contributors have institutional affiliations with ROR identifiers?
- [ ] Are funders listed with award numbers and ROR identifiers?
- [ ] Are relevant brain regions / anatomical structures in the `about` field (UBERON)?
- [ ] Is the license specified (`spdx:CC-BY-4.0`)?
- [ ] Is the IACUC/IRB protocol number included in `ethicsApproval`?
- [ ] Are keywords provided for discoverability?
- [ ] Is at least one contributor marked as `dcite:ContactPerson` with an email?

#### 7f. Additional Metadata to Ask the User

After auto-populating from OpenAlex, ask the user for anything that can't be extracted:

> I've populated the metadata from your paper. A few more things:
>
> 1. **Contact person email**: What email should be listed for the contact person?
> 2. **Ethics approval**: What is your IACUC/IRB protocol number and institution?
> 3. **Keywords**: What keywords should I add for discoverability?
> 4. **Brain regions**: What brain regions were recorded? I'll look up the UBERON terms.
> 5. **Any additional contributors** not on the paper (e.g., data curators, technicians)?

#### Publishing

> When all metadata is complete and you're ready to make your dataset permanently citable:
> 1. Review the metadata at your Dandiset URL
> 2. Click "Publish" on the Dandiset page
> 3. This creates an immutable version with a DOI
> 4. The DOI can be used in publications to reference this exact version of the data
>
> Note: You can continue uploading files and publish new versions later. Each version
> gets its own DOI.

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
# Get your sandbox API key from https://sandbox.dandiarchive.org/
export DANDI_API_KEY=your_sandbox_key

# Upload to sandbox
dandi upload -i dandi-sandbox
```

For programmatic metadata editing on the sandbox, use:
```python
from dandi.dandiapi import DandiAPIClient

client = DandiAPIClient(api_url="https://api.sandbox.dandiarchive.org/api")
client.dandi_authenticate()
dandiset = client.get_dandiset("000123", "draft")
# ... same metadata operations as production
```

The sandbox server is at https://sandbox.dandiarchive.org/ (API: https://api.sandbox.dandiarchive.org/) —
create a separate account and Dandiset there for testing.

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
