# Organizing data

Never move or rename existing data unless there is a very good reason and the
user explicitly agrees. Downstream tests use those paths.

When adding to a folder that already exists, follow the convention already
established there. For a new folder, use this structure:

```
[<modality>/]                            ophys only: imaging, segmentation, fiber_photometry, events, analog
  <acquisition_system|algorithm>/        e.g. plexon, bruker, axon, ethovision, dannce
    [<format_type>/]                     csv | excel | json, when the system writes several file types
      [<version>/]                       e.g. version_7_0 | legacy, when the format is versioned
        <condition>/                     an important axis of variation of the format
          <dataset_folder>/              the specific dataset, named by what it adds
            files
```

The top folder is the acquisition system or algorithm, not the file format,
because one system can write the same data as, for example, CSV and a binary
file. An open standard written by many systems (EDF) is its own top folder. A
system that writes more than one modality can use the level below it for that,
when the modality is not separated at the top level as in the ophys repository.

A condition is a variation in the acquisition system's output that changes how
a reader handles the format. Source, lab, or experiment names and catch-all
groups such as `edge_cases` are not conditions.

Some examples of conditions:

- Layout or structure: the data split across several files, one file per
  subject, or a different group hierarchy in a hierarchical format like HDF5.
- Content: which optional sections or tables are present, such as events or
  metadata annotations.
- Number of subjects, arenas, channels or planes.
- Encoding of a field: the same information stored as a string, a number or a
  boolean, or a header that may be missing.
- Timing: offsets, clocks that differ between streams, or a synchronization
  table that does not match the recording's length.
- Acquisition setup: the recording configuration that changes what the files
  hold.

Give each dataset its own folder, so that datasets added later do not clash and
downstream users get a clean folder per dataset. Name the dataset folder in
snake_case:

- After what the dataset adds beyond its condition: the property that sets it
  apart from a sibling that could join later under the same condition, such as
  its compression or its number of headstages.
- Not after context outside the format: the specimen, lab, date or
  acquisition ID, or a meaning the system does not record, such as a channel
  being used for sync.

Name the files inside it by the same rules, and not after stubbing or
preprocessing, which is not a property of the format. Two exceptions:

- If the acquisition system follows a spec for naming (SpikeGLX, for
  example), keep the names it writes.
- If the acquisition system writes a folder with its own structure (Open Ephys,
  for example), keep that folder as it is and nest it inside the dataset
  folder.

File names and paths should read well to someone familiar with the format and
describe the traits of the data. Paths are rarely typed by hand, so prefer a
long, descriptive name over the brevity expected of a variable name.

## README

Put a `README.md` in the acquisition system folder, and one inside each format
type folder when there are several. With several format types, the top README
is short: it describes the system and lists its format types.

The top README briefly describes the format for a user: what writes the files,
the format types available, and the main sources of variation, such as software
versions, export modes, single or multiple subjects, and binary or text
containers. Inside, use this shape for every entry:

```markdown
# <acquisition system or algorithm>

<a short preamble describing the format>

## <condition>

<a paragraph naming the axis this group varies, in format terms>

### <dataset folder>

<one or two sentences on what it is and what it adds over its siblings>

- <characteristic>
- <characteristic>

Provenance: <source, DOI or link, license, original name, what was done to it, e.g. how it was stubbed>.
```

Follow these rules:

- The preamble describes the format, not the folder's contents, so it stays true
  as datasets are added or removed: no counts, no claims about the whole set.
  Anything true of one dataset goes in that dataset's bullets.
- Headings follow the folder tree below the README: each folder level gets the
  next heading level. With a version folder, the version gets `##`, the
  condition `###` and the dataset `####`.
- Characteristic bullets are brief and factual: channels, shapes and dtypes,
  rates, software version, encoding, filename pattern. If one needs more than a
  line, it is too long. Keep the same bullet order across sibling entries.
- Provenance is short and comes after the bullets.
- Link file and folder names to their paths
  (`[two_c57.xlsx](excel/.../two_c57.xlsx)`), so they open from the gin web
  page.
- Do not refer to a specific downstream consumer (python-neo, neuroconv, and so
  on). This keeps the repository generic and useful to a wider public.
- Do not refer to other datasets ("as above", "the same recording"). Datasets
  get removed, changed or reordered, so each description stands alone and
  additions and removals stay atomic.

Good examples:

- [edf/README.md](https://gin.g-node.org/NeuralEnsemble/ephy_testing_data/src/bf392aaed45bf518c556bc7d1195dea8a8e6cf12/edf/README.md)
- [eeglab/README.md](https://gin.g-node.org/NeuralEnsemble/ephy_testing_data/src/bf392aaed45bf518c556bc7d1195dea8a8e6cf12/eeglab/README.md)
- [fiber_photometry_datasets/pyphotometry/README.md](https://gin.g-node.org/CatalystNeuro/ophys_testing_data/src/854cbabdba4cb7d9e3976a3df8facbd8bd335716/fiber_photometry_datasets/pyphotometry/README.md)
- [dannce/README.md](https://gin.g-node.org/CatalystNeuro/behavior_testing_data/src/f6a3c20185c3c1340bc3c72d09e21b6ffd5263d9/dannce/README.md)
