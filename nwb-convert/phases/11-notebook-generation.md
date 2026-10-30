## Phase 11: Example Notebook Generation

**Goal**: Create an educational Jupyter notebook that demonstrates how to stream, read,
and visualize the published NWB data from DANDI. The notebook serves as a companion to
the Dandiset — helping new users (and reviewers) explore the data independently.

**Entry**: Data has been uploaded to DANDI (Phase 9 complete) and the Dandiset metadata
is filled in (Phase 10). The Dandiset ID and asset
paths are known.

**Exit criteria**: A tested `.ipynb` notebook that runs end-to-end using only streaming
access (no local downloads), with clear prose, visualizations of each data stream, and
at least one combined analysis (e.g., place fields, PSTHs, or trial-aligned time series).

Shared notebook guidance (context to gather, combined analyses, pynapple loading,
visualization recipes, cell style) is in `knowledge/notebook-recipes.md`. Read it before
Step 1.

### Step 0: Gather Context

Before writing any code, collect the information needed to plan the notebook:

1. **Dandiset ID and version** (from Phase 9)
2. **Session inventory**: List all NWB files. Identify which sessions have behavioral data,
   which are ecephys-only, etc.
3. The data streams, publication, and epochs/conditions listed under "Context to Gather" in
   `knowledge/notebook-recipes.md`.

> I'll now create an example notebook that shows how to stream and visualize your data
> from DANDI. This notebook will be submitted to the
> [dandi/example-notebooks](https://github.com/dandi/example-notebooks) repository.
>
> Let me check the data structure and plan the visualizations.

### Step 1: Plan the Notebook

Design the notebook structure based on what data streams are available. Follow this
template, including only sections relevant to the dataset:

```
1. Title & Introduction
   - Dataset description, link to Dandiset, link to paper (if any)
   - Link to the session in Neurosift:
     `https://neurosift.app/nwb?dandisetId=<dandiset_id>&dandisetVersion=draft&path=<asset_path>`
   - Brief experimental summary

2. Setup
   - Import dependencies (the install cell is generated in Step 5)
   - Connect to DANDI and list available sessions

3. Load a Single Session
   - Stream an NWB file using remfile
   - Explore the NWB file structure (subject, session, electrodes, epochs)

4. Visualize Individual Data Streams (include all that apply):
   a. Position/trajectory plots (colored by time or epoch)
   b. Spike raster plots (all units, subset of time)
   c. LFP traces or spectrograms
   d. Fluorescence traces (dF/F or raw)
   e. Behavioral events or trial structure
   f. Pre-computed data (rate maps, waveforms, etc.)

5. Combined Analyses
   - 1-2 analyses from "Combined Analyses" in knowledge/notebook-recipes.md

6. (Optional) Reproduce a Paper Figure
   - If a paper exists, attempt to replicate Figure 1 or 2

7. Summary
   - What the notebook demonstrated
   - Links to further resources (PyNWB docs, pynapple tutorials, NWB overview)
```

Present the plan to the user:

> Here's what I plan to include in the notebook:
> [list sections based on available data]
>
> Does this look good? Anything you'd like to add or remove?

### Step 2: Set Up the Notebook Directory

Fork and clone `dandi/example-notebooks` (default branch `master`), create a branch, and
create the notebook directory inside the clone. The layout follows the repo's
[README](https://github.com/dandi/example-notebooks#submission-instructions):

```bash
gh repo fork dandi/example-notebooks --clone
cd example-notebooks
git checkout -b add-<dandiset_id>
mkdir -p <dandiset_id>/<lab_name>/<mnemonic>
```

```
example-notebooks/
  <dandiset_id>/
    <lab_name>/              # org or lab name, e.g. DombeckLab
      <mnemonic>/            # short name for the paper or analysis, e.g. smith2025
        requirements.in
        README.md
        <dandiset_id>_demo.ipynb
```

**requirements.in**: the notebook's direct imports, one per line. Do not list transitive
dependencies or a full freeze; the repo's tooling compiles the pinned set from this file.

```
dandi
h5py
matplotlib
pynapple
pynwb
remfile
```

Add a package only if the notebook imports it (e.g., `numpy`, `scipy`, an `ndx-*`
extension). If the notebook needs a version range, write it as a bound
(e.g., `matplotlib<3.11`).

**README.md**: explain the goal of the notebook, link the Dandiset and any publication,
and describe what each notebook shows.
```markdown
# <Dandiset Title>

This example notebook demonstrates how to access and visualize the dataset published at
[DANDI:<dandiset_id>](https://dandiarchive.org/dandiset/<dandiset_id>).

<Brief description of the data: species, brain regions, recording methods, behavioral task>

## Notebooks

### `<dandiset_id>_demo.ipynb`

<What the notebook streams and what each section shows>
```

### Step 3: Write the Notebook

Build the notebook cell by cell, running each cell as you go to verify it works. Follow
the pynapple loading, visualization guidelines, recipes, and cell style in
`knowledge/notebook-recipes.md`.

#### Streaming Access Pattern

Always stream data from DANDI; never download files in the notebook. With
`strip_query=True` the URL is the public S3 object URL, which does not expire and stays the
same across runs, so a re-run reads its chunks from the `remfile` disk cache. A signed URL
changes on every run and misses the cache. The repo's `.gitignore` excludes `nwb-cache/`.

```python
from dandi.dandiapi import DandiAPIClient
import h5py
import remfile
from pynwb import NWBHDF5IO

dandiset_id = "<DANDISET_ID>"
file_path = "<ASSET_PATH>"

with DandiAPIClient() as client:
    asset = client.get_dandiset(dandiset_id, "draft").get_asset_by_path(file_path)
    s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)

file = remfile.File(s3_url, disk_cache=remfile.DiskCache("nwb-cache"))
h5_file = h5py.File(file, "r")
io = NWBHDF5IO(file=h5_file, load_namespaces=True)
nwbfile = io.read()
```

### Step 4: Test the Notebook

The repository's CI runs each new notebook on Python 3.13 in a fresh environment that
contains only the pinned packages from the install cell, with no display. Test the same
way: a new Python 3.13 environment outside the clone with only `requirements.in` and
Jupyter installed. `JUPYTER_PREFER_ENV_PATH=1` makes Jupyter use this environment's
kernel even when the user has their own `python3` kernel registered.

```bash
uv venv --python 3.13 notebook-env
source notebook-env/bin/activate
uv pip install -r example-notebooks/<dandiset_id>/<lab_name>/<mnemonic>/requirements.in jupyter
export JUPYTER_PREFER_ENV_PATH=1
cd example-notebooks/<dandiset_id>/<lab_name>/<mnemonic>
jupyter execute <dandiset_id>_demo.ipynb --timeout=600
```

Or test with `nbconvert`:

```bash
jupyter nbconvert --to notebook --execute <dandiset_id>_demo.ipynb --output executed.ipynb
```

Verify:
1. All cells execute without errors
2. All plots render correctly (read the output notebook images)
3. Streaming access works (no local file dependencies)
4. The notebook completes in a reasonable time (< 5 minutes for streaming)
5. The notebook runs headlessly: no `%matplotlib widget` or other interactive backend,
   no plotly `fig.show()` without `pio.renderers.default = "iframe"`, no `input()`.
   See the repo's [adding-notebooks guide](https://github.com/dandi/example-notebooks/blob/master/docs/adding-notebooks.md).

If a cell fails, see "When a Cell Fails" in `knowledge/notebook-recipes.md`. Here the other
common cause is a remfile timeout: some NWB files are large, so load less data or pick a
smaller session.

Present this to the user and request feedback. Only proceed to Step 5 after you have the user's approval.

### Step 5: Submit to example-notebooks

With the test environment still active (the script needs `uv` on `PATH` and `nbformat`,
which Jupyter installed), run the repo's lock script from the root of the clone. It
resolves `requirements.in` against Colab's runtime and writes the Colab badge and the
pinned `!uv pip install --system` cell at the top of the notebook. CI fails a new
notebook that lacks this cell.

```bash
cd ../../..  # root of the example-notebooks clone
python .github/scripts/lock_notebook.py <dandiset_id>/<lab_name>/<mnemonic>/<dandiset_id>_demo.ipynb

git add <dandiset_id>/<lab_name>/<mnemonic>/requirements.in \
  <dandiset_id>/<lab_name>/<mnemonic>/README.md \
  <dandiset_id>/<lab_name>/<mnemonic>/<dandiset_id>_demo.ipynb
git commit -m "Add example notebook for DANDI:<dandiset_id>"
git push -u origin add-<dandiset_id>

gh pr create \
  --repo dandi/example-notebooks \
  --title "Add tutorial notebook for <dandiset_id>" \
  --body "Add tutorial notebook demonstrating how to stream and visualize NWB data from DANDI:<dandiset_id>.

## Summary
- Streams data from DANDI using remfile (no local downloads)
- Shows NWB file structure and metadata
- Visualizes [list key visualizations]
- [Optional: Reproduces Figure X from the associated paper]

Generated with [Claude Code](https://claude.com/claude-code)"
```

CI on the PR runs the notebook from its install cell. Check the result with
`gh pr checks` and fix any failure before telling the user.

Inform the user:
> The example notebook has been submitted as a PR to dandi/example-notebooks.
> PR: [link]
>
> The notebook demonstrates:
> [list what the notebook covers]

Once the PR is merged, add the notebook to the Dandiset's related resources with the
`dandiset-metadata` skill (see Phase 10): the notebook's GitHub URL, relation
`dcite:IsSupplementedBy`, resource type `dcite:ComputationalNotebook`.
