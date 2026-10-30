## Phase 5: Code Generation

**Goal**: Generate a complete, pip-installable conversion repo following CatalystNeuro conventions.

**Entry**: You have complete experiment spec, interface mapping, metadata, and sync plan.

**Exit criteria**: A working repo with:
- Correct directory structure (cookiecutter pattern)
- `pyproject.toml` with proper dependencies
- NWBConverter class with all interfaces
- `convert_session.py` with full pipeline
- Custom DataInterface classes where needed
- `metadata.yaml` with all collected metadata
- `convert_all_sessions.py` for batch conversion

**Stacked PRs mode**: commit the scaffold, session-level metadata, an NWBConverter with no
data interfaces, and the conversion scripts on `setup`. Then build one data stream at a time,
each on its own branch created from the previous one, starting with the timing reference
stream from Phase 4. Commit Step 9 per branch. See `knowledge/stacked-prs.md`.

### Step 1: Scaffold the Repository

Create the standard directory structure INSIDE the repo that was created in Phase 1
(`nwb-conversions/<lab-name>-to-nwb/`). All files below are relative to the repo root:

```
./                              ← repo root (already created in Phase 1)
├── .gitignore                  ← already created in Phase 1
├── pyproject.toml
├── README.md
├── make_env.yml
└── src/
    └── <lab>_lab_to_nwb/
        ├── __init__.py
        └── <conversion_name>/
            ├── __init__.py
            ├── <conversion_name>_nwbconverter.py
            ├── convert_session.py
            ├── convert_all_sessions.py
            ├── metadata.yaml
            └── <custom_interface_name>.py  (if needed)
```

### Step 2: Write pyproject.toml

```toml
[project]
name = "<lab>-lab-to-nwb"
version = "0.0.1"
description = "NWB conversion scripts for the <Lab> Lab."
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [{ name = "CatalystNeuro", email = "ben.dichter@catalystneuro.com" }]
dependencies = ["neuroconv", "nwbinspector"]

[project.optional-dependencies]
<conversion_name> = [
    "neuroconv[<extras>]",  # Use latest during development; pin only after finalization
    # Add any additional deps needed for custom interfaces
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<lab>_lab_to_nwb"]
```

Hatchling includes the YAML and JSON files inside the package directory in the wheel, so
no `include` list is needed. Check the build with `uv build` and list the wheel contents.

**Extras for NeuroConv** depend on which interfaces are used:
- SpikeGLX: `neuroconv[spikeglx]`
- OpenEphys: `neuroconv[openephys]`
- Phy: `neuroconv[phy]`
- Suite2p: `neuroconv[suite2p]`
- DeepLabCut: `neuroconv[deeplabcut]`
- Check NeuroConv's pyproject.toml for all available extras

### Step 3: Write the NWBConverter Class

```python
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    # Import NeuroConv interfaces based on interface mapping
)
# Import custom interfaces
from .<custom_module> import CustomInterface


class <ConversionName>NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        # Map logical names to interface classes
        # Names should be descriptive: Recording, LFP, Sorting, Behavior, etc.
    )

    def temporally_align_data_interfaces(self, metadata: dict | None = None, conversion_options: dict | None = None):
        """Override if sync logic is needed."""
        # Implement sync plan from Phase 4
        pass
```

### Step 3a: Reuse NeuroConv Interfaces Before Writing Your Own

Code that calls existing NeuroConv interfaces is easier for reviewers to follow than custom
code. When a stock interface almost fits a data stream, adapt it in this order and stop at the
first option that works:

1. **Compose stock interfaces in the converter.** Use several instances of the same interface
   when one stream is split across files or segments (e.g. one `TDTFiberPhotometryInterface`
   per tank when Synapse was restarted mid-session, each with its own `metadata_key` and
   series name, shifted to the session clock in `temporally_align_data_interfaces`).
2. **Subclass the format-specific interface**, not its base class, and override only the
   smallest method that needs to change.
3. **Write a custom interface on a base class** (Step 4). Before doing so, record in
   `conversion_notes.md` which stock interface you considered and why options 1 and 2 do not
   work.

### Step 3b: Check Registry for Reusable Custom Interfaces

Before writing a custom interface from scratch, check the conversion registry for
similar custom interfaces from prior conversions. A prior interface that handles the
same data format or creates the same NWB types can serve as a starting template.

```python
import yaml

with open("/tmp/registry.yaml") as f:
    registry = yaml.safe_load(f)

# Search for conversions with custom interfaces that match what we need
needed_nwb_types = ["Position", "BehavioralEvents"]  # what our custom data maps to
for conv in registry.get("conversions", []):
    if not conv.get("has_custom_interfaces"):
        continue
    # The full manifest has custom_interfaces detail — fetch it from the repo
    print(f"Check {conv['repo']} for custom interfaces")
```

If a match is found, fetch the actual interface code from the prior repo via the API:
```bash
NWB_API="https://nwb-conversions-api.ben-dichter.workers.dev"
curl -sf "${NWB_API}/repos/<repo-name>/files/<path-to-interface>"
```

Use the fetched code as a starting template, adapting it to the current lab's file format
and column names. Give credit in a comment: `# Adapted from nwb-conversions/<repo-name>`.

If no match is found, write the custom interface from scratch (Step 4 below).

### Step 4: Write Custom DataInterface Classes

For each data stream that needs custom code:

```python
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from pydantic import FilePath
from pynwb.file import NWBFile


class <Name>Interface(BaseDataInterface):
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
        # Extract any metadata from the file
        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, **kwargs):
        # Read data from self.source_data["file_path"]
        # Create appropriate PyNWB objects
        # Add to nwbfile
        pass
```

#### Custom Interface Guidelines

**Prefer raw acquisition data**: Custom interfaces should read data as close to the
original acquisition format as possible. If you're working with processed data because
raw files aren't available, document this in the interface docstring (e.g., "Reads
trialized behavior data from lab-processed .mat files. Raw SpikeGLX files were not
available."). When raw data IS available, always use the NeuroConv interface for that
acquisition system rather than writing a custom reader.

**Metadata responsibility**: A custom interface's `get_metadata()` should only return
metadata that can be extracted FROM THE DATA FILE ITSELF (e.g., session date from filename,
frame rate from timestamps). Lab-level metadata (institution, experimenter) and subject
metadata (species, genotype) should be handled in `convert_session.py` via metadata YAML
and subject metadata files. Do not duplicate metadata loading between the interface and
the conversion script.

**Use `conversion` parameter, not data transformation**: When data is in non-SI units
(e.g., centimeters), do NOT multiply the data by a conversion factor. Instead, use the
`conversion` parameter on TimeSeries:
```python
# CORRECT: store raw data, use conversion factor
TimeSeries(name="position", data=pos_cm, unit="m", conversion=0.01)

# WRONG: transform data in-place
TimeSeries(name="position", data=pos_cm * 0.01, unit="m")
```
This preserves original data values in the file and is more NWB-idiomatic.

**Pickle files load whole into memory.** Read them in `add_to_nwbfile()` (or in
`get_metadata()` if metadata is needed), not in `__init__()`.

**Choosing the right NWB types for custom data:**

Always use the most specific NWB type available — don't use bare `TimeSeries` when a
subtype exists. See `knowledge/nwb-best-practices.md` for the full set of conventions.

| Data Type | NWB Container | Where to Add |
|-----------|---------------|--------------|
| Continuous neural signal | `ElectricalSeries` | `nwbfile.add_acquisition()` |
| Position (x, y) | `Position` > `SpatialSeries` | `processing["behavior"]` |
| Running speed | `TimeSeries` | `processing["behavior"]` |
| Lick times | `EventsTable` | `nwbfile.add_events_table()` |
| Trial info | `TimeIntervals` | `nwbfile.add_trial()` |
| Epochs | `TimeIntervals` | `nwbfile.add_epoch()` |
| Pupil tracking | `PupilTracking` > `TimeSeries` | `processing["behavior"]` |
| Eye position | `EyeTracking` > `SpatialSeries` | `processing["behavior"]` |
| Stimulus times | `TimeIntervals` | `nwbfile.add_stimulus()` |
| Fluorescence traces | `RoiResponseSeries` | `processing["ophys"]` |
| ROI masks | `PlaneSegmentation` | `processing["ophys"]` |
| Reward events | `EventsTable` | `nwbfile.add_events_table()` |
| Animal video | `ImageSeries` (external_file) | `nwbfile.add_acquisition()` |
| Compass direction | `CompassDirection` > `SpatialSeries` | `processing["behavior"]` |
| Optogenetic stimulus | ndx-optogenetics `OptogeneticEpochsTable` or `OptogeneticPulsesTable` | `nwbfile.add_time_intervals()` |

**For detailed PyNWB construction patterns by domain, see:**
- `knowledge/pynwb-icephys.md` — intracellular electrophysiology
- `knowledge/ndx-optogenetics.md` — ndx-optogenetics extension (REQUIRED for optogenetics)
- `knowledge/pynwb-ophys-advanced.md` — advanced optical physiology (ROIs, segmentation, motion correction)
- `knowledge/pynwb-behavior.md` — behavior container types (PupilTracking, EyeTracking, etc.) and EventsTable
- `knowledge/pynwb-images.md` — image data and external video files
- `knowledge/pynwb-advanced-io.md` — compression, chunking, iterative write for large data
- `knowledge/ndx-fiber-photometry.md` — ndx-fiber-photometry extension (REQUIRED for fiber photometry)
- `knowledge/ndx-pose.md` — ndx-pose extension for pose estimation (DeepLabCut, SLEAP, Lightning Pose)
- `knowledge/ndx-anatomical-localization.md` — ndx-anatomical-localization for electrode/imaging plane atlas registration

**Single-photon vs. two-photon imaging:**
Miniscope data (UCLA Miniscope, Inscopix nVista/nVoke) is **single-photon** (one-photon)
imaging and MUST use `OnePhotonSeries`, not `TwoPhotonSeries`. Two-photon imaging
(ScanImage, Scanbox, Bruker, Prairie) uses `TwoPhotonSeries`. Getting this wrong is a
common mistake. Check:
- Miniscope → `OnePhotonSeries` (via `MiniscopeImagingInterface`)
- Inscopix → `OnePhotonSeries` (via `InscopixImagingInterface`)
- ScanImage, Scanbox, Bruker → `TwoPhotonSeries`
- If unsure, ask the user whether their microscope uses one-photon or two-photon excitation.

#### Behavioral vs. Stimulus Data

When a dataset has both behavioral and stimulus columns (common in VR experiments),
separate them:

**Behavioral data** → `processing["behavior"]` via `BehavioralTimeSeries`, `Position`, etc.:
- Position / spatial location
- Running speed / velocity
- Lick events / lick rate
- Eye position / pupil diameter
- Pose estimation keypoints

**Stimulus data** → `nwbfile.add_stimulus()`:
- Visual stimulus parameters (contrast, orientation, spatial frequency)
- Environment parameters (morph value, jitter)
- Optogenetic stimulus waveforms
- Auditory stimulus parameters

**Reward** can go in either, but prefer `processing["behavior"]` if it represents the
animal's experience (reward delivery events), or `nwbfile.add_stimulus()` if it represents
an experimenter-controlled parameter.

**Use `get_module()` to get or create processing modules:**
```python
from neuroconv.tools.nwb_helpers import get_module
behavior_module = get_module(nwbfile, "behavior", "Processed behavioral data")
behavior_module.add(my_container)
```

**Compression and chunking:** pass plain arrays (or a `SliceableDataChunkIterator` for data larger
than memory) and do not wrap them in `H5DataIO`. `run_conversion` chunks and compresses every dataset.
To change those settings, see `knowledge/pynwb-advanced-io.md`.

#### Best Practices

Every custom interface and `add_to_nwbfile()` method follows `knowledge/nwb-best-practices.md`, in particular
the Time Series, Tables, ecephys, Behavior, and Image Series sections.

### Step 5: Write convert_session.py

Follow the standard pattern:

```python
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
    # Load per-subject metadata from file if available
    # Field formats: knowledge/nwb-best-practices.md (Subject)

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

### Step 6: Write convert_all_sessions.py

Each dict returned by `get_session_to_nwb_kwargs_per_session` holds exactly the per-session
arguments of `session_to_nwb`. Failed sessions write their traceback to
`<output_dir_path>/exceptions/`.

```python
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
        data_dir_path=Path("/path/to/data"),
        output_dir_path=Path("~/conversion_nwb").expanduser(),
        max_workers=1,
        stub_test=False,
    )
```

### Step 7: Write metadata.yaml

Use the metadata collected in Phase 3. See Phase 3 for format.

### Step 8: Write README.md

```markdown
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
```

### Step 9: Commit and Push to nwb-conversions

After all code is generated and the repo is scaffolded, commit everything and push to the
`nwb-conversions` GitHub org. The remote was configured in Phase 1.

```bash
git add -A
git commit -m "Add conversion code for <conversion_name>

Generated by nwb-convert skill. Includes:
- NWBConverter with <N> interfaces
- <N> custom DataInterface classes
- convert_session.py and convert_all_sessions.py
- metadata.yaml with lab and experiment metadata"
if git remote get-url origin &>/dev/null; then git push; fi
```

This makes the conversion code immediately available in the org for reference by future
conversions. The manifest will be added in Phase 8 after DANDI upload is complete.
