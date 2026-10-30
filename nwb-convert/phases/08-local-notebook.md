## Phase 8: Local Example Notebook

**Goal**: Create Jupyter notebooks that load and visualize the locally converted NWB data,
for two audiences. Conversion reviewers get one review notebook per data stream, so they can
check each stream on its own without reading the conversion code. The lab gets one demo
notebook with combined analyses that serves as a starting point for analysis. Both validate
the conversion output before the data is uploaded to DANDI.

**Entry**: Testing and validation are complete (Phase 7). At least one full NWB file has
been written to disk.

**Exit criteria**: Tested `.ipynb` notebooks that run end-to-end loading local NWB files: one
review notebook per data stream (Step 4), and a demo notebook with clear prose and at least
one combined analysis (e.g., place fields, PSTHs, or trial-aligned time series).

Shared notebook guidance (context to gather, combined analyses, pynapple loading,
visualization recipes, cell style) is in `knowledge/notebook-recipes.md`. Read it before
Step 1.

### Step 0: Gather Context

Before writing any code, collect the information needed to plan the notebooks:

1. **Output NWB file path**: Where did the conversion write the NWB file(s)?
2. **Session inventory**: Which session will be used as the demo session? Pick a
   representative one (ideally the same session used in testing).
3. The data streams, publication, and epochs/conditions listed under "Context to Gather" in
   `knowledge/notebook-recipes.md`.

> I'll now create a local example notebook that shows how to load and visualize
> your converted NWB data. This helps validate the conversion and gives you a
> starting point for analysis.
>
> Let me check the data structure and plan the visualizations.

### Step 1: Plan the Notebooks

List the review notebooks, one per data stream, named after the stream (e.g.
`fiber_photometry.ipynb`). Design the demo notebook from this template, including only
sections relevant to the dataset:

```
1. Title & Introduction
   - Dataset description, brief experimental summary
   - Note that this notebook loads local NWB files

2. Setup
   - Install/import dependencies
   - Specify path to the local NWB file

3. Load a Single Session
   - Open the NWB file using NWBHDF5IO
   - Explore the NWB file structure (subject, session, electrodes, epochs)

4. Individual Data Streams
   - Link to each per-stream review notebook (Step 4)

5. Combined Analyses
   - 1-2 analyses from "Combined Analyses" in knowledge/notebook-recipes.md

6. (Optional) Reproduce a Paper Figure
   - If a paper exists, attempt to replicate Figure 1 or 2

7. Summary
   - What the notebook demonstrated
   - Links to further resources (PyNWB docs, pynapple tutorials, NWB overview)
```

Present the plan to the user:

> Here's what I plan to include in the notebooks:
> [list the review notebooks and the demo sections based on available data]
>
> Does this look good? Anything you'd like to add or remove?

### Step 2: Set Up the Notebook Directory

Create the notebooks inside the conversion repo in a `notebooks/` directory:

```
<conversion_repo>/
  notebooks/
    environment.yml
    README.md
    <lab_name>_demo.ipynb
    <stream>.ipynb          ← one review notebook per data stream (Step 4)
```

**environment.yml** — minimal conda environment:
```yaml
name: <lab_name>_demo
channels:
    - conda-forge
dependencies:
    - python=3.12
    - pip
    - pip:
      - jupyter
      - matplotlib
      - pynwb
      - pynapple
      - h5py
```

Add additional pip dependencies only if the notebook actually uses them (e.g., `scipy`
for signal processing, `numpy` for array operations). Keep it minimal.

**README.md**:
```markdown
# <Lab/Dataset Name> Example Notebook

This notebook demonstrates how to load and visualize the NWB data produced by this
conversion pipeline.

<Brief description of the data: species, brain regions, recording methods, behavioral task>

## Installing the dependencies

```bash
conda env create --file environment.yml
conda activate <lab_name>_demo
```

## Running the notebook

```bash
jupyter notebook <lab_name>_demo.ipynb
```

Update `nwb_file_path` in the first cell to point to your converted NWB file.
```

### Step 3: Open the Local File

Every notebook in this phase loads the demo session directly from disk:

```python
from pynwb import NWBHDF5IO

nwb_file_path = "/path/to/converted/session.nwb"  # update this path

io = NWBHDF5IO(nwb_file_path, "r")
nwbfile = io.read()
```

Build each notebook cell by cell, running each cell as you go to verify it works. Follow
the pynapple loading, visualization guidelines, recipes, and cell style in
`knowledge/notebook-recipes.md`.

### Step 4: Write the Per-Stream Review Notebooks

Write one review notebook per data stream. Each one lets a reviewer confirm that stream was
converted correctly without reading the conversion code.

1. **Title**: the stream, its source files and recording system.
2. **Structural summary**: a table of the NWB objects that hold this stream, with their
   neurodata type and namespace, so a reviewer sees at a glance which core types and
   extensions were used and whether device and metadata objects exist. List the stream's
   object names, including its devices and metadata containers:

   ```python
   import pandas as pd
   from hdmf.container import Container

   stream_object_names = ["<series or table name>", "<device name>", "<metadata container name>"]
   summary = pd.DataFrame(
       [
           dict(
               name=neurodata_object.name,
               neurodata_type=neurodata_object.neurodata_type,
               namespace=neurodata_object.namespace,
               parent=neurodata_object.parent.name,
           )
           for neurodata_object in nwbfile.objects.values()
           if isinstance(neurodata_object, Container) and neurodata_object.parent is not None
       ]
   )
   summary[summary["name"].isin(stream_object_names)]
   ```

   Follow it with a markdown cell stating which types the stream should use (e.g.
   ndx-fiber-photometry for fiber photometry, ndx-optogenetics for optogenetics).
3. **Plots of this stream alone**: e.g. traces over a short window and the full session,
   event rasters, position trajectories, or rate maps, whichever fit the data.
4. **Checks against the source**: one or two comparisons a reviewer can verify by eye,
   such as event counts per type or the first samples next to the values read from the
   source files.

### Step 5: Write the Demo Notebook

Write `<lab_name>_demo.ipynb` following the plan from Step 1. Its "Individual Data Streams"
section links to the review notebooks; the combined analyses come from the recipes in
`knowledge/notebook-recipes.md`.

### Step 6: Run, Check, and Commit the Notebooks

Run every notebook end-to-end using `jupyter execute`:

```bash
cd <conversion_repo>/notebooks
for notebook in *.ipynb; do jupyter execute --inplace --timeout=600 "$notebook"; done
```

Verify:
1. All cells execute without errors
2. All plots render correctly (read the images saved in the executed notebooks)
3. The notebook completes in a reasonable time (< 5 minutes)

If a cell fails, see "When a Cell Fails" in `knowledge/notebook-recipes.md`. Here the other
common cause is the file path: make sure `nwb_file_path` points to an actual converted NWB file.

Present the notebooks to the user and request feedback. Once approved, commit them to the
conversion repo. In stacked PRs mode, commit each review notebook on its stream's branch and
the demo notebook on the last branch, carrying changes up the stack as described in
`knowledge/stacked-prs.md`, then open the PRs as described there ("Opening the PRs") and
share the list of PR links with the user. Otherwise:

```bash
git add notebooks/
git commit -m "Add local example notebooks"
git push
```

> The notebooks are saved in `notebooks/`, one per data stream plus `<lab_name>_demo.ipynb`.
> You can open them anytime to explore the converted data before uploading to DANDI.
>
> Next we'll upload the data to DANDI.
