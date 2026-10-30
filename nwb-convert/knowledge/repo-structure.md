# Conversion Repo Templates

The templates for every file Phase 5 generates in a `<lab>-lab-to-nwb` conversion repository. They follow the
[cookiecutter-my-lab-to-nwb-template](https://github.com/catalystneuro/cookiecutter-my-lab-to-nwb-template).
Phase 5 says when to write each file.

---

## 1. Directory Structure

```
<lab>-lab-to-nwb/
├── .github/workflows/            # Only if the user wants PyPI publishing (Section 10)
│   ├── auto-publish.yml
│   └── test-install.yml
├── .gitignore                    # Created in Phase 1
├── .pre-commit-config.yaml
├── LICENSE                       # MIT
├── README.md
├── pyproject.toml
└── src/
    └── <lab>_lab_to_nwb/         # Python package (underscored slug)
        ├── __init__.py           # Empty
        ├── <conversion_a>/       # One directory per conversion/experiment
        │   ├── __init__.py       # Empty, or exports the converter and custom interfaces
        │   ├── <conversion_a>_nwbconverter.py
        │   ├── convert_session.py
        │   ├── convert_all_sessions.py
        │   ├── metadata.yaml
        │   ├── <custom_interface>.py      # Or an interfaces/ subpackage when there are many
        │   └── conversion_notes.md
        └── <conversion_b>/       # Additional conversions for the same lab
            └── ...
```

### Naming conventions

| Concept | Convention | Example |
|---------|-----------|---------|
| Repo name | `<lab>-lab-to-nwb` | `cai-lab-to-nwb` |
| Package slug | `<lab>_lab_to_nwb` (underscored) | `cai_lab_to_nwb` |
| Conversion directory | `<first_author>_<year>` or descriptive name | `zaki_2024` |
| NWBConverter class | `<ConversionCamelCase>NWBConverter` | `Zaki2024NWBConverter` |
| Interface class | `<ConversionCamelCase><Modality>Interface` | `Zaki2024ShockStimuliInterface` |
| NWBConverter module | `<conversion_name>_nwbconverter.py` | `zaki_2024_nwbconverter.py` |

---

## 2. pyproject.toml

```toml
[project]
name = "<lab>-lab-to-nwb"
version = "0.0.1"
description = "NWB conversion scripts, functions, and classes for <Lab Name> lab conversion"
readme = "README.md"
authors = [{ name = "CatalystNeuro", email = "ben.dichter@catalystneuro.com" }]
maintainers = [{ name = "CatalystNeuro", email = "ben.dichter@catalystneuro.com" }]
license = "MIT"
requires-python = ">=3.10"
classifiers = [
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13"
]

dependencies = [
  "neuroconv",
  "nwbinspector",
]

[project.urls]
Repository = "https://github.com/catalystneuro/<lab>-lab-to-nwb"

# Per-conversion dependencies (install with: uv pip install -e ".[conversion_name]")
[project.optional-dependencies]
<conversion_name> = [
  "neuroconv[<extras>]",   # Use latest during development; pin to exact version only after conversion is finalized
  # Add conversion-specific packages here, e.g.:
  # "mne",
  # "opencv-python-headless",
  # "ndx-miniscope==0.5.1",
]

[dependency-groups]
dev = [
  "pre-commit",
  "ruff",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<lab>_lab_to_nwb"]  # YAML/JSON files inside the package are included by default

[tool.ruff]

[tool.ruff.lint]
select = [
    "F401",   # Unused import
    "I",      # All isort rules
    "UP006",  # non-pep585 annotation
    "UP007",  # non-pep604 annotation (Union -> |)
    "UP045",  # non-pep604 annotation (Optional -> | None)
]
fixable = ["ALL"]

[tool.ruff.lint.isort]
relative-imports-order = "closest-to-furthest"
known-first-party = ["<lab>_lab_to_nwb"]

[tool.codespell]
skip = '.git*,*.pdf,*.css'
check-hidden = true
ignore-words-list = 'assertin'
```

- Keep `neuroconv` and `nwbinspector` unpinned in the top-level `dependencies`.
- Leave the per-conversion dependencies unpinned during development. Pin exact versions only after the conversion
  is finalized and validated.
- NeuroConv extras depend on the interfaces used: `neuroconv[spikeglx]`, `neuroconv[openephys]`, `neuroconv[phy]`,
  `neuroconv[suite2p]`, `neuroconv[deeplabcut]`, and so on. Check NeuroConv's `pyproject.toml` for the full list.
- Packages for custom interfaces (`mne` for EDF, `opencv-python-headless` for video, NWB extensions such as
  `ndx-miniscope`) go in the same optional-dependency list.
- Check the build with `uv build` and list the wheel contents to confirm `metadata.yaml` is included.

---

## 3. NWBConverter Class

```python
"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    PhySortingInterface,
    SpikeGLXRecordingInterface,
)

from <lab>_lab_to_nwb.<conversion_name>.<custom_module> import <ConversionName>BehaviorInterface


class <ConversionName>NWBConverter(NWBConverter):
    """Primary conversion class for <description of dataset>."""

    data_interface_classes = dict(
        Recording=SpikeGLXRecordingInterface,
        Sorting=PhySortingInterface,
        Behavior=<ConversionName>BehaviorInterface,
    )

    def temporally_align_data_interfaces(self, metadata: dict | None = None, conversion_options: dict | None = None):
        """Implement the sync plan from Phase 4 here (Section 8). Omit this method if no alignment is needed."""
```

- The keys of `data_interface_classes` are arbitrary names. They become the keys of `source_data` and
  `conversion_options`, so name the data stream (`Recording`, `LFP`, `Sorting`, `Behavior`).
- Look up built-in interfaces and their required `source_data` arguments in `knowledge/neuroconv-interfaces.yaml`.
- The class declares the superset of interfaces. The converter instantiates only those with an entry in
  `source_data`, so `convert_session.py` adds an entry only for the data a session has.
- Override `get_metadata()` (call `super().get_metadata()` first) only for metadata computed from several
  interfaces' source data.

---

## 4. convert_session.py

```python
"""Primary script to run to convert an entire session of data using the NWBConverter."""
from pathlib import Path
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from <lab>_lab_to_nwb.<conversion_name>.<conversion_name>_nwbconverter import <ConversionName>NWBConverter


def session_to_nwb(
    data_dir_path: str | Path,
    output_dir_path: str | Path,
    stub_test: bool = False,
):
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Determine session_id and subject_id from path/filenames
    session_id = "..."
    subject_id = "..."
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    # Build source_data
    source_data = dict()
    conversion_options = dict()

    # Add each interface with its file paths
    # Pass every required source_data argument the interface lists in neuroconv-interfaces.yaml
    # (SpikeGLXRecordingInterface shown here)
    source_data["Recording"] = dict(folder_path=str(data_dir_path / "..."), stream_id="imec0.ap")
    conversion_options["Recording"] = dict(stub_test=stub_test)

    # Conditionally add interfaces if files exist
    behavior_path = data_dir_path / "behavior.txt"
    if behavior_path.is_file():
        source_data["Behavior"] = dict(file_path=str(behavior_path))
        conversion_options["Behavior"] = dict()

    # Create converter
    converter = <ConversionName>NWBConverter(source_data=source_data)

    # Get and merge metadata
    metadata = converter.get_metadata()

    metadata_path = Path(__file__).parent / "metadata.yaml"
    editable_metadata = load_dict_from_file(metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Set session-specific metadata
    tz = ZoneInfo("<timezone>")
    if metadata["NWBFile"]["session_start_time"]:
        metadata["NWBFile"]["session_start_time"] = (
            metadata["NWBFile"]["session_start_time"].replace(tzinfo=tz)
        )
    metadata["NWBFile"]["session_id"] = session_id

    # Subject metadata — subject_id is required for DANDI
    metadata["Subject"]["subject_id"] = subject_id
    # Load per-subject metadata from file if available (Section 7)
    # See knowledge/nwb-best-practices.md for required formats:
    #   species: Latin binomial (e.g., "Mus musculus")
    #   sex: one of "M", "F", "U", "O"
    #   age: ISO 8601 duration (e.g., "P90D")
    #   weight: "numeric unit" (e.g., "0.025 kg")

    # Run conversion
    converter.run_conversion(
        nwbfile_path=nwbfile_path,
        metadata=metadata,
        conversion_options=conversion_options,
        overwrite=True,
    )


if __name__ == "__main__":
    # Example usage
    data_dir_path = Path("/path/to/data")
    output_dir_path = Path("/path/to/output")
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=True,  # Set to False for full conversion
    )
```

- Metadata layers, later ones overriding earlier ones: values the interfaces extract from the source files
  (`converter.get_metadata()`), then `metadata.yaml`, then per-session values (`session_id`, `subject_id`,
  `session_description`, per-subject fields).
- `session_start_time` must carry a timezone. If no interface extracts it, set it from the session's records,
  e.g. `datetime(2020, 1, 1, 13, 0, tzinfo=tz)`.
- `stub_test=True` writes to `nwb_stub/` and passes `stub_test` to each interface that supports it, so only a
  few seconds of data are written. Phase 7 runs the stub first.
- Name files `<session_id>.nwb` or `sub-<subject_id>_ses-<session_id>.nwb`. `dandi organize` renames them on upload.

---

## 5. convert_all_sessions.py

```python
"""Primary script to run to convert all sessions in a dataset using session_to_nwb."""
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from pprint import pformat

from <lab>_lab_to_nwb.<conversion_name>.convert_session import session_to_nwb


def get_session_to_nwb_kwargs_per_session(data_dir_path: Path) -> list[dict]:
    """Return one dict of session_to_nwb arguments per session, e.g. dict(data_dir_path=session_dir_path)."""
    raise NotImplementedError("Implement session discovery")


def safe_session_to_nwb(session_to_nwb_kwargs: dict, exception_file_path: Path):
    """Run session_to_nwb and write any exception to exception_file_path."""
    try:
        session_to_nwb(**session_to_nwb_kwargs)
    except Exception:
        with open(exception_file_path, mode="w") as file:
            file.write(f"session_to_nwb_kwargs:\n{pformat(session_to_nwb_kwargs)}\n\n")
            file.write(traceback.format_exc())


def dataset_to_nwb(
    data_dir_path: str | Path,
    output_dir_path: str | Path,
    max_workers: int = 1,
    stub_test: bool = False,
):
    """Convert every session in data_dir_path; failed sessions write a traceback to output_dir_path/exceptions."""
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    exception_dir_path = output_dir_path / "exceptions"
    exception_dir_path.mkdir(parents=True, exist_ok=True)

    session_to_nwb_kwargs_per_session = get_session_to_nwb_kwargs_per_session(data_dir_path=data_dir_path)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for session_to_nwb_kwargs in session_to_nwb_kwargs_per_session:
            session_to_nwb_kwargs.update(output_dir_path=output_dir_path, stub_test=stub_test)
            session_name = Path(session_to_nwb_kwargs["data_dir_path"]).name
            exception_file_path = exception_dir_path / f"{session_name}.txt"
            futures.append(executor.submit(safe_session_to_nwb, session_to_nwb_kwargs, exception_file_path))
        for future in as_completed(futures):
            future.result()


if __name__ == "__main__":
    dataset_to_nwb(
        data_dir_path=Path("/path/to/raw/data/"),
        output_dir_path=Path("~/conversion_nwb").expanduser(),
        max_workers=1,
        stub_test=False,
    )
```

`get_session_to_nwb_kwargs_per_session` is the part to write for each conversion. Each dict it returns holds
exactly the per-session arguments of `session_to_nwb`; `dataset_to_nwb` adds `output_dir_path` and `stub_test`,
and any other key raises a `TypeError` for every session. Common ways to find the sessions:

```python
# One directory per session
session_dir_paths = [path for path in sorted(data_dir_path.iterdir()) if path.is_dir() and not path.name.startswith(".")]

# One file per session, matched by a pattern in its name
session_dir_paths = [file_path.parent for file_path in sorted(data_dir_path.glob("*/cell_info_session*.mat"))]

# A table the lab keeps, with one row per session (import pandas as pd)
session_table = pd.read_csv(data_dir_path / "sessions.csv")
session_dir_paths = [data_dir_path / folder_name for folder_name in session_table["session_folder"]]

return [dict(data_dir_path=session_dir_path) for session_dir_path in session_dir_paths]
```

`safe_session_to_nwb` writes each failure to a file so one bad session does not stop the batch.

---

## 6. Custom DataInterface

Write one only after the reuse order in Phase 5 Step 3a rules out a built-in interface.

```python
"""Primary class for converting experiment-specific <modality>."""
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from pydantic import FilePath
from pynwb.file import NWBFile


class <ConversionName><Modality>Interface(BaseDataInterface):
    """Interface for reading <description>."""

    keywords = ["<modality>"]

    def __init__(self, file_path: FilePath):
        """
        Parameters
        ----------
        file_path : FilePath
            Path to the <format> file.
        """
        super().__init__(file_path=file_path)

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        # Add metadata read from the source file itself, e.g. the session start time
        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, stub_test: bool = False):
        # Read data from self.source_data["file_path"], build PyNWB objects, and add them to nwbfile
        raise NotImplementedError()
```

- The `__init__` parameters are the keys of this interface's `source_data` entry. Pass all of them to
  `super().__init__()`, which stores them in `self.source_data`. Annotate paths with `pydantic`'s `FilePath` or
  `DirectoryPath` so they are validated.
- Keep `__init__` light: store paths and read data in `add_to_nwbfile`.
- Extra keyword arguments of `add_to_nwbfile` are the keys of this interface's `conversion_options` entry.
  Accept `stub_test` to support stub runs.
- An interface whose timestamps must be aligned subclasses `BaseTemporalAlignmentInterface` instead (Section 8).
- An interface can take no source files and receive all its data through `conversion_options`, e.g. shock times
  and amplitudes the lab reports in the paper.

---

## 7. metadata.yaml

Hand-edited metadata that applies to all sessions of a conversion, collected in Phase 3. `convert_session.py`
merges it on top of the metadata the interfaces extract.

```yaml
NWBFile:
  keywords:
    - hippocampus
    - learning
    - memory
  related_publications:
    - https://doi.org/10.1038/s41586-024-08168-4
  session_description: >
    Describe what happened in this session. This is REQUIRED by NWB.
  experiment_description: >
    Scientific goal of the experiment; the paper abstract is fine here.
  institution: Icahn School of Medicine at Mount Sinai
  lab: Cai
  experimenter:
    - Last, First Middle
    - Last, First Middle
  surgery: >
    Optional: description of surgical procedures.
  virus: >
    Optional: description of viral constructs used.
Subject:
  species: Mus musculus      # REQUIRED. Use Latin binomial name.
  description: >
    A rich text description of the subject.
  age: P12W/P18W             # ISO 8601 duration. "P90D" = 90 days old.
  sex: M                     # One of M, F, U, or O
  strain: C57BL/6J           # Optional
  genotype: wild-type        # Optional
  date_of_birth: 2014-06-22 00:00:00-04:00  # Optional, with timezone
```

`dict_deep_update` merges recursively: nested dicts merge, scalars are overwritten, and lists are appended with
duplicates removed (lists of dicts merge by `name`). To replace a list, assign it after the merge.

### Ophys metadata

Devices, imaging planes, and series go in the dict format that `get_metadata()` returns. `MicroscopySeries`,
`PlaneSegmentations` and the other per-interface entries are keyed by each interface's `metadata_key`. Print
`converter.get_metadata()` and each ophys interface's `get_metadata_template()` and write the YAML in that shape.
Entries in the old list format (`Ophys: Device: - name: ...`) are ignored without an error.

```yaml
DeviceModels:
  microscope_model:
    name: Miniscope V4
    manufacturer: Open Ephys
    description: Head-mounted one-photon microscope.
Devices:
  microscope:
    name: Microscope
    description: Miniscope implanted over dorsal CA1.
    device_model_metadata_key: microscope_model
Ophys:
  ImagingPlanes:
    imaging_plane:
      name: ImagingPlane
      description: Imaging plane in dorsal CA1.
      excitation_lambda: 470.0
      indicator: GCaMP6f
      location: CA1
      device_metadata_key: microscope
      optical_channel:
        - name: GreenChannel
          description: Green channel of the microscope.
          emission_lambda: 513.0
  MicroscopySeries:
    imaging:  # the imaging interface's metadata_key
      name: OnePhotonSeries
      description: One-photon calcium imaging data.
      imaging_plane_metadata_key: imaging_plane
      unit: n.a.
  PlaneSegmentations:
    segmentation:  # the segmentation interface's metadata_key
      imaging_plane_metadata_key: imaging_plane
```

The series type comes from the imaging interface's `photon_series_type` conversion option, which defaults to `TwoPhotonSeries` in most imaging interfaces (Miniscope defaults to `OnePhotonSeries`) whatever the YAML `name` says. For one-photon data, set it in the converter's `conversion_options`, keyed by the interface name: `conversion_options.update(dict(Imaging=dict(photon_series_type="OnePhotonSeries")))`.

### Per-subject metadata

For datasets with several subjects, keep subject fields in a separate YAML file keyed by subject:

```yaml
# subject_metadata.yaml
N2:
  subject_id: N2
  age: P90D
  strain: C57Bl/6
  genotype: wildtype
  date_of_birth: 2019-10-22
  weight: 0.016 kg
  sex: U
```

and merge the subject's entry in `convert_session.py`:

```python
subject_metadata = load_dict_from_file(Path(__file__).parent / "subject_metadata.yaml")[subject_id]
metadata["Subject"] = dict_deep_update(metadata["Subject"], subject_metadata)
```

---

## 8. Temporal Alignment

When data streams have different clocks or start times, override `temporally_align_data_interfaces()` in the
NWBConverter. Phase 4 covers the sync patterns and NeuroConv's TTL helpers.

```python
class <ConversionName>NWBConverter(NWBConverter):
    data_interface_classes = dict(...)

    def temporally_align_data_interfaces(self, metadata: dict | None = None, conversion_options: dict | None = None):
        if "Behavior" in self.data_interface_objects:
            behavior_interface = self.data_interface_objects["Behavior"]
            time_shift = ...  # offset of the behavior clock from the reference clock, from the Phase 4 sync plan
            original_timestamps = behavior_interface.get_original_timestamps()
            behavior_interface.set_aligned_timestamps(original_timestamps + time_shift)
```

These methods exist on `BaseTemporalAlignmentInterface`. A custom interface that must be aligned subclasses it and implements `get_original_timestamps`, `get_timestamps` and `set_aligned_timestamps`.

| Method | When to use |
|--------|-------------|
| `interface.get_original_timestamps()` | Get timestamps before any alignment |
| `interface.set_aligned_timestamps(timestamps)` | Replace all timestamps |
| `interface.set_aligned_starting_time(t)` | Shift starting time for regularly sampled data |
| `interface.align_by_interpolation(unaligned_timestamps, aligned_timestamps)` | Map this interface's clock onto the reference clock through matched sync times |
| `SpikeGLXNIDQInterface.get_event_times_from_ttl(channel_name)` | Rising-edge times of a TTL on a NIDQ channel (`"XA2"`) |
| `interface.set_aligned_interval_times(start_times, stop_times)` | Custom method for interval-based interfaces |

---

## 9. README.md

````markdown
# <lab>-lab-to-nwb

NWB conversion scripts for the [<Lab> Lab](lab_url) data,
using [NeuroConv](https://github.com/catalystneuro/neuroconv).

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[<conversion_name>]"
```

## Usage

### Single session
```python
from <lab>_lab_to_nwb.<conversion_name>.convert_session import session_to_nwb

session_to_nwb(
    data_dir_path="/path/to/session",
    output_dir_path="/path/to/output",
    stub_test=False,
)
```

### All sessions
```python
from <lab>_lab_to_nwb.<conversion_name>.convert_all_sessions import dataset_to_nwb

dataset_to_nwb(
    data_dir_path="/path/to/data",
    output_dir_path="/path/to/output",
    max_workers=4,
)
```
````

---

## 10. Supporting Files

### LICENSE

The standard MIT license text, matching `license = "MIT"` in `pyproject.toml`, with the current year and the
copyright holder the user names.

### .pre-commit-config.yaml

After writing this file, run `pre-commit autoupdate` to pin the current hook versions.

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
    -   id: check-yaml
    -   id: end-of-file-fixer
    -   id: trailing-whitespace

-   repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
    -   id: black
        exclude: ^docs/

- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.11.2
  hooks:
  - id: ruff
    args: [ --fix ]

- repo: https://github.com/codespell-project/codespell
  rev: v2.4.1
  hooks:
  - id: codespell
    additional_dependencies:
    - tomli
```

### CI workflows (only if the user wants PyPI publishing)

`.github/workflows/auto-publish.yml` publishes the package when a GitHub release is published. It uses PyPI
trusted publishing: register the repository and workflow file as a trusted publisher in the PyPI project
settings. No API token is needed.

```yaml
name: Upload Package to PyPI
on:
  release:
    types: [published]
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - run: |
          python -m pip install --upgrade pip build
          python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

`.github/workflows/test-install.yml` checks once a month that the package installs and imports:

```yaml
name: Installation
on:
  workflow_dispatch:
  schedule:
    - cron: "0 0 1 * *"  # Monthly

jobs:
  run:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: ["ubuntu-latest", "macos-latest", "windows-latest"]
        python-version: ["3.12"]
    steps:
    - uses: actions/checkout@v7
    - uses: actions/setup-python@v7
      with:
        python-version: ${{ matrix.python-version }}
    - run: pip install uv && uv pip install --system -e .
    - run: python -c "import <lab>_lab_to_nwb"
```
