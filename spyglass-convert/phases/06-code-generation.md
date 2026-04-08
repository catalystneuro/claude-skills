## Phase 6: Code Generation (Spyglass-Compatible)

**Goal**: Generate a complete, pip-installable conversion repo that produces NWB
files Spyglass can ingest without errors.

**Entry**: Complete experiment spec, interface mapping, metadata, and sync plan.

**Exit criteria**: A working repo with:
- Standard CatalystNeuro directory structure with `utils/` for Spyglass-specific helpers
- NWBConverter with all NeuroConv interfaces
- `utils/add_behavioral_video.py` — CameraDevice + task_table (required by Spyglass)
- `utils/add_behavior.py` — DIO events and analog behavioral signals
- `utils/add_ecephys.py` — electrode setup with ndx_franklab_novela types
- `convert_session.py` with full pipeline calling utils helpers
- `metadata.yaml` with all collected metadata

**Baseline**: Follow **nwb-convert Phase 5** for the general code generation
workflow. All of the following apply equally to Spyglass conversions:

- **Step 3b** — check the nwb-conversions registry for reusable custom interfaces
  before writing from scratch
- **Step 4** — custom DataInterface guidelines (lazy loading, `get_metadata()`
  responsibility, `conversion` parameter, `resolution=-1.0`, NWB type selection table,
  behavioral vs stimulus data, time-series best practices, table best practices,
  ecephys best practices). Read nwb-convert Phase 5 Step 4 in full before writing any
  custom `BaseDataInterface` subclass.
- **Step 6** — `convert_all_sessions.py` pattern with `ProcessPoolExecutor`
- **Step 8** — `README.md` generation with install and usage instructions

For the full canonical `pyproject.toml` format (classifiers, `project.urls`,
`dependency-groups.dev`, ruff/codespell config), see
`../nwb-convert/knowledge/repo-structure.md` §2.

Also read before writing code:
- `knowledge/spyglass-nwb-requirements.md` — electrode columns, ndx_franklab_novela types
- `knowledge/spyglass-custom-tables.md` — if lab-specific Spyglass tables are needed
- `../nwb-convert/knowledge/nwb-best-practices.md` — NWB conventions that apply to all data types
- `../nwb-convert/knowledge/pynwb-behavior.md` — behavior container types
- `../nwb-convert/knowledge/pynwb-advanced-io.md` — H5DataIO compression for large arrays
- `../nwb-convert/knowledge/conversion-patterns.md` — session discovery patterns,
  position data, trial tables, sync recipes from real repos

### Step 1: Scaffold the Repository

```
<repo>/
├── .gitignore
├── pyproject.toml
├── README.md
└── src/
    └── <lab_name>_to_nwb/
        ├── __init__.py
        └── <conversion_name>/
            ├── __init__.py
            ├── <conversion_name>nwbconverter.py
            ├── convert_session.py
            ├── convert_all_sessions.py
            ├── insert_session.py
            ├── verify_insertion.py
            ├── metadata.yaml
            ├── utils/
            │   ├── __init__.py
            │   ├── add_behavioral_video.py
            │   ├── add_behavior.py
            │   └── add_ecephys.py
            └── spyglass_extensions/    ← only if lab-specific custom tables needed
                ├── __init__.py
                └── <custom_table>.py
```

### Step 2: Write pyproject.toml

Use the canonical CatalystNeuro format (see `../nwb-convert/knowledge/repo-structure.md` §2
for the full template with CI workflows and pre-commit config):

```toml
[project]
name = "<lab-name>-lab-to-nwb"
version = "0.0.1"
description = "NWB conversion scripts for the <Lab> Lab (Spyglass-compatible)."
readme = "README.md"
authors = [{ name = "CatalystNeuro", email = "ben.dichter@catalystneuro.com" }]
maintainers = [{ name = "CatalystNeuro", email = "ben.dichter@catalystneuro.com" }]
license = { file = "LICENSE" }
requires-python = ">=3.10"
classifiers = [
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = ["neuroconv", "nwbinspector"]

[project.urls]
Repository = "https://github.com/catalystneuro/<lab-name>-lab-to-nwb"

[project.optional-dependencies]
<conversion_name> = [
    "neuroconv[spikeglx,phy]",   # adjust extras to match interfaces used
    "ndx-franklab-novela",        # required for CameraDevice, DataAcqDevice, Probe types
    "pymatreader",                # for reading .mat behavior files
]

[dependency-groups]
dev = ["pre-commit", "ruff"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build]
include = ["*.yaml", "*.yml", "*.json"]

[tool.hatch.build.targets.wheel]
packages = ["src/<lab_name>_lab_to_nwb"]

[tool.hatch.build.targets.sdist]
packages = ["src/<lab_name>_lab_to_nwb"]

[tool.ruff.lint]
select = ["F401", "I", "UP006", "UP007", "UP045"]
fixable = ["ALL"]

[tool.ruff.lint.isort]
relative-imports-order = "closest-to-furthest"
known-first-party = ["<lab_name>_lab_to_nwb"]
```

Install:
```bash
source .venv/bin/activate
uv pip install -e ".[<conversion_name>]"
```

### Step 3: Write utils/add_behavioral_video.py

Spyglass requires two things that a bare `ImageSeries` does not provide:
1. A `CameraDevice` from `ndx_franklab_novela` (not a plain `Device`)
2. A `"tasks"` processing module with a `task_table` `DynamicTable` — this must
   always be created, even when the session has no distinct behavioral epochs
   (in that case add a single row covering the whole session).

Reference: `kind-lab-to-nwb/.../utils/add_behavioral_video.py`

```python
"""Add behavioral video with Spyglass-required CameraDevice and task table."""

from pathlib import Path
from typing import Optional, Union
import numpy as np
from pynwb import NWBFile
from pynwb.image import ImageSeries
from hdmf.common import DynamicTable, VectorData
import ndx_franklab_novela


def add_behavioral_video(
    nwbfile: NWBFile,
    metadata: dict,
    video_file_path: Union[Path, str],
    timestamps: Optional[np.ndarray] = None,
) -> None:
    """Add behavioral video with Spyglass-compatible CameraDevice and task table.

    Spyglass will not ingest video correctly without:
    - A CameraDevice (ndx_franklab_novela) instead of a plain Device
    - A "tasks" processing module containing a task_table DynamicTable

    Parameters
    ----------
    nwbfile : NWBFile
    metadata : dict
        Expects a "Video" key with:
          camera_name, meters_per_pixel, camera_model, camera_lens,
          task_name, task_description, video_description
    video_file_path : path to the video file (will be stored as relative path)
    timestamps : 1D array of frame timestamps in seconds, or None if using rate
    """
    video_file_path = Path(video_file_path)
    video_meta = metadata.get("Video", {})

    camera_name = video_meta.get("camera_name", "camera0")

    # 1. Add CameraDevice (ndx_franklab_novela — required by Spyglass)
    if camera_name not in nwbfile.devices:
        camera_device = ndx_franklab_novela.CameraDevice(
            name=camera_name,
            meters_per_pixel=video_meta.get("meters_per_pixel", 0.001),
            model=video_meta.get("camera_model", "unknown"),
            lens=video_meta.get("camera_lens", "unknown"),
            camera_name=camera_name,
        )
        nwbfile.add_device(camera_device)

    # 2. Create "tasks" processing module (required for Spyglass ingestion)
    if "tasks" not in nwbfile.processing:
        tasks_module = nwbfile.create_processing_module(
            name="tasks",
            description="Task information for Spyglass ingestion.",
        )
    else:
        tasks_module = nwbfile.processing["tasks"]

    # 3. Create task_table (required even when there are no distinct epochs)
    #    Add one row covering the whole session if no epoch information exists.
    if "task_table" not in tasks_module.data_interfaces:
        task_table = DynamicTable(
            name="task_table",
            description="Table of tasks performed during this session.",
            columns=[
                VectorData(
                    name="task_name",
                    description="Name of the task.",
                    data=[],
                ),
                VectorData(
                    name="task_description",
                    description="Description of the task.",
                    data=[],
                ),
                VectorData(
                    name="camera_id",
                    description="Index of the CameraDevice used during this task.",
                    data=[],
                ),
                VectorData(
                    name="task_epochs",
                    description="Epoch indices during which this task was performed.",
                    data=[],
                ),
            ],
        )
        tasks_module.add(task_table)
    else:
        task_table = tasks_module["task_table"]

    task_table.add_row(
        task_name=video_meta.get("task_name", "task"),
        task_description=video_meta.get("task_description", "Behavioral task."),
        camera_id=[0],          # index into devices list; 0 if single camera
        task_epochs=[1],        # epoch index; [1] when no distinct epochs
    )

    # 4. Add video as ImageSeries referencing the CameraDevice
    image_series = ImageSeries(
        name=camera_name,
        description=video_meta.get("video_description", "Behavioral video recording."),
        external_file=[str(video_file_path)],   # relative path
        format="external",
        timestamps=timestamps,                   # or use rate= if constant
        unit="n.a.",
    )
    nwbfile.add_acquisition(image_series)
```

### Step 4: Write utils/add_behavior.py

Behavioral data goes into the `"behavior"` processing module:
- **DIO events** (TTL channels): `BehavioralEvents` container with one `TimeSeries` per channel
- **Analog behavioral signals**: `BehavioralTimeSeries` container

Reference: `kind-lab-to-nwb/.../utils/add_behavior.py`

```python
"""Add behavioral DIO events and analog signals."""

from pathlib import Path
from typing import Optional
import numpy as np
from pynwb import NWBFile
from pynwb.behavior import BehavioralEvents, BehavioralTimeSeries, TimeSeries
from neuroconv.tools.nwb_helpers import get_module


def add_behavioral_events(
    nwbfile: NWBFile,
    dio_data: dict[str, np.ndarray],
    dio_timestamps: dict[str, np.ndarray],
    description: str = "DIO events.",
) -> None:
    """Add digital I/O events to the NWB file.

    Parameters
    ----------
    nwbfile : NWBFile
    dio_data : dict mapping channel name → 1D array of event values (0/1)
    dio_timestamps : dict mapping channel name → 1D array of timestamps in seconds
    description : description for the BehavioralEvents container
    """
    behavior_module = get_module(nwbfile, "behavior", "Processed behavioral data.")

    behavioral_events = BehavioralEvents(name="behavioral_events")

    for channel_name, data in dio_data.items():
        ts = TimeSeries(
            name=channel_name,
            data=data.astype(np.int8),
            timestamps=dio_timestamps[channel_name],
            description=f"DIO events for channel {channel_name}.",
            unit="n.a.",
        )
        behavioral_events.add_timeseries(ts)

    behavior_module.add(behavioral_events)


def add_behavioral_signals(
    nwbfile: NWBFile,
    signal_data: dict[str, np.ndarray],
    signal_timestamps: dict[str, np.ndarray],
    signal_descriptions: Optional[dict[str, str]] = None,
    signal_units: Optional[dict[str, str]] = None,
) -> None:
    """Add continuous analog behavioral signals to the NWB file.

    Parameters
    ----------
    nwbfile : NWBFile
    signal_data : dict mapping signal name → 2D array (n_timepoints, n_channels)
                  or 1D array for single-channel signals
    signal_timestamps : dict mapping signal name → 1D timestamps array
    signal_descriptions : optional dict of descriptions per signal
    signal_units : optional dict of units per signal
    """
    behavior_module = get_module(nwbfile, "behavior", "Processed behavioral data.")

    behavioral_ts = BehavioralTimeSeries(name="behavioral_signals")

    for signal_name, data in signal_data.items():
        ts = TimeSeries(
            name=signal_name,
            data=data,
            timestamps=signal_timestamps[signal_name],
            description=(signal_descriptions or {}).get(
                signal_name, f"Behavioral signal: {signal_name}."
            ),
            unit=(signal_units or {}).get(signal_name, "n.a."),
        )
        behavioral_ts.add_timeseries(ts)

    behavior_module.add(behavioral_ts)
```

### Step 5: Write utils/add_ecephys.py

The standard NeuroConv SpikeGLX/OpenEphys interfaces create generic `Device` and
`ElectrodeGroup` objects. Spyglass requires the `ndx_franklab_novela` equivalents:
`DataAcqDevice`, `Probe`, `Shank`, `ShanksElectrode`, `NwbElectrodeGroup`.

Reference: `kind-lab-to-nwb/.../utils/add_ecephys.py`

```python
"""Set up electrode tables and devices using ndx_franklab_novela types."""

from typing import Optional
import numpy as np
from pynwb import NWBFile
from pynwb.ecephys import LFP, ElectricalSeries
import ndx_franklab_novela
from neuroconv.tools.nwb_helpers import get_module


def add_ecephys_devices(
    nwbfile: NWBFile,
    metadata: dict,
) -> None:
    """Add DataAcqDevice, Probe, Shank, ShanksElectrode using ndx_franklab_novela.

    Call this BEFORE NeuroConv interfaces run so that the electrode groups
    they create can reference these devices.

    Parameters
    ----------
    metadata : dict
        Expects an "Ecephys" key with:
          DataAcqDevice: [{name, system, amplifier, adc_circuit}]
          Probe: [{id, probe_type, contact_side_numbering, shanks: [...]}]
    """
    ecephys_meta = metadata.get("Ecephys", {})

    # DataAcqDevice (ndx_franklab_novela) — replaces standard Device
    for device_meta in ecephys_meta.get("DataAcqDevice", []):
        if device_meta["name"] not in nwbfile.devices:
            device = ndx_franklab_novela.DataAcqDevice(
                name=device_meta["name"],
                system=device_meta.get("system", "unknown"),
                amplifier=device_meta.get("amplifier", "unknown"),
                adc_circuit=device_meta.get("adc_circuit", "unknown"),
            )
            nwbfile.add_device(device)

    # Probe hierarchy: Probe → Shank → ShanksElectrode
    for probe_meta in ecephys_meta.get("Probe", []):
        probe = ndx_franklab_novela.Probe(
            id=probe_meta["id"],
            probe_type=probe_meta.get("probe_type", "tetrode_array"),
            contact_side_numbering=probe_meta.get("contact_side_numbering", True),
            name=f"probe{probe_meta['id']}",
        )
        for shank_meta in probe_meta.get("shanks", []):
            shank = ndx_franklab_novela.Shank(
                name=str(shank_meta["id"]),
            )
            for elec_meta in shank_meta.get("electrodes", []):
                electrode = ndx_franklab_novela.ShanksElectrode(
                    name=str(elec_meta["id"]),
                    rel_x=elec_meta.get("rel_x", 0.0),
                    rel_y=elec_meta.get("rel_y", 0.0),
                    rel_z=elec_meta.get("rel_z", 0.0),
                )
                shank.add_shanks_electrode(electrode)
            probe.add_shank(shank)
        nwbfile.add_device(probe)


def add_electrode_groups(
    nwbfile: NWBFile,
    metadata: dict,
) -> None:
    """Add NwbElectrodeGroup objects (ndx_franklab_novela) in nTrode{N} format.

    NwbElectrodeGroup replaces standard ElectrodeGroup for Spyglass compatibility.
    Names must follow the nTrode{N} convention (1-indexed).
    """
    ecephys_meta = metadata.get("Ecephys", {})

    for i, group_meta in enumerate(ecephys_meta.get("ElectrodeGroup", []), start=1):
        group_name = f"nTrode{i}"
        if group_name not in nwbfile.electrode_groups:
            electrode_group = ndx_franklab_novela.NwbElectrodeGroup(
                name=group_name,
                description=group_meta.get("description", f"Electrode group {i}."),
                location=group_meta.get("location", "unknown"),
                device=nwbfile.devices[group_meta["device"]],
                targeted_location=group_meta.get("targeted_location", "unknown"),
                targeted_x=group_meta.get("targeted_x", 0.0),
                targeted_y=group_meta.get("targeted_y", 0.0),
                targeted_z=group_meta.get("targeted_z", 0.0),
                units=group_meta.get("units", "um"),
            )
            nwbfile.add_electrode_group(electrode_group)


def add_spyglass_electrode_columns(nwbfile: NWBFile, metadata: dict) -> None:
    """Add the six required Spyglass electrode columns.

    Must be called AFTER NeuroConv interfaces have built the base electrode table.
    See knowledge/spyglass-nwb-requirements.md for column definitions.
    """
    n = len(nwbfile.electrodes)
    electrode_meta = metadata.get("Electrodes", {})

    columns = {
        "probe_shank": (
            "The shank of the probe this electrode is on.",
            electrode_meta.get("probe_shank", [0] * n),
        ),
        "probe_electrode": (
            "The electrode number on the probe.",
            electrode_meta.get("probe_electrode", list(range(n))),
        ),
        "bad_channel": (
            "True if this electrode is marked bad.",
            electrode_meta.get("bad_channel", [False] * n),
        ),
        "ref_elect_id": (
            "Index of the reference electrode for this channel.",
            electrode_meta.get("ref_elect_id", [0] * n),
        ),
        "group_name": (
            "The name of the electrode group (nTrode).",
            [e.group_name for e in nwbfile.electrodes.to_dataframe().itertuples()],
        ),
        "brain_area": (
            "The brain region of this electrode.",
            electrode_meta.get("brain_area", ["unknown"] * n),
        ),
    }

    for col_name, (description, data) in columns.items():
        if col_name not in nwbfile.electrodes.colnames:
            nwbfile.electrodes.add_column(
                name=col_name,
                description=description,
                data=data,
            )


def move_lfp_to_ecephys_processing(nwbfile: NWBFile) -> None:
    """Move LFP from acquisition to processing['ecephys']['LFP'].

    Spyglass expects LFP in processing['ecephys']['LFP'], but NeuroConv's
    SpikeGLXLFPInterface places it in acquisition by default.
    """
    if "LFP" not in nwbfile.acquisition:
        return
    lfp_series = nwbfile.acquisition.pop("LFP")
    ecephys_module = get_module(nwbfile, "ecephys", "Processed ecephys data.")
    lfp_container = LFP(name="LFP", electrical_series=lfp_series)
    ecephys_module.add(lfp_container)
```

### Step 6: Write the NWBConverter

The converter orchestrates NeuroConv interfaces and calls the utils functions
at the end of `add_to_nwbfile()`:

```python
from neuroconv import NWBConverter
from neuroconv.datainterfaces import SpikeGLXRecordingInterface, PhySortingInterface
from pynwb import NWBFile

from .utils.add_behavioral_video import add_behavioral_video
from .utils.add_behavior import add_behavioral_events, add_behavioral_signals
from .utils.add_ecephys import (
    add_ecephys_devices,
    add_electrode_groups,
    add_spyglass_electrode_columns,
    move_lfp_to_ecephys_processing,
)


class <ConversionName>NWBConverter(NWBConverter):

    data_interface_classes = dict(
        Recording=SpikeGLXRecordingInterface,
        Sorting=PhySortingInterface,
        # Do NOT add a VideoInterface — video is handled by add_behavioral_video()
        # Do NOT add an LFP interface that writes to acquisition — see move_lfp_to_ecephys_processing()
    )

    def temporally_align_data_interfaces(self):
        pass  # implement sync plan from Phase 5

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, **conversion_options):
        # 1. Add ndx_franklab_novela devices FIRST (before NeuroConv interfaces)
        add_ecephys_devices(nwbfile, metadata)
        add_electrode_groups(nwbfile, metadata)

        # 2. Run all NeuroConv interfaces
        super().add_to_nwbfile(nwbfile, metadata, **conversion_options)

        # 3. Add Spyglass electrode columns
        add_spyglass_electrode_columns(nwbfile, metadata)

        # 4. Move LFP from acquisition to processing["ecephys"]["LFP"]
        move_lfp_to_ecephys_processing(nwbfile)

        # 5. Add behavioral video (CameraDevice + task_table)
        video_path = self.source_data.get("video_path")
        if video_path:
            add_behavioral_video(
                nwbfile=nwbfile,
                metadata=metadata,
                video_file_path=video_path,
                timestamps=self._video_timestamps,  # set during temporally_align
            )

        # 6. Add behavioral events and signals
        if self._dio_data:
            add_behavioral_events(nwbfile, self._dio_data, self._dio_timestamps)
        if self._signal_data:
            add_behavioral_signals(nwbfile, self._signal_data, self._signal_timestamps)
```

### Step 7: Fiber Photometry and Optogenetics

These data types have no dedicated Spyglass tables — store them using standard NWB
extensions, same as nwb-convert. Read:
- `../nwb-convert/knowledge/ndx-fiber-photometry.md` — use `ndx-fiber-photometry`,
  never plain `TimeSeries`. Add `ndx-fiber-photometry` to pyproject.toml dependencies.
- `../nwb-convert/knowledge/pynwb-optogenetics.md` — `OptogeneticSeries` goes in
  `nwbfile.add_stimulus()`.

Neither requires Spyglass-specific electrode columns or naming conventions. If the lab
wants to query fiber photometry from Spyglass (not just store it in NWB), open a
Spyglass issue first — see `knowledge/spyglass-custom-tables.md`.

### Step 8: Custom Spyglass Tables (if needed)

If the lab has **proprietary** data that Spyglass cannot ingest via standard tables,
follow `knowledge/spyglass-custom-tables.md`. Key questions to ask first:

> Does this data type (e.g., TaskLEDs, custom stimulus parameters) represent something
> unique to this lab, or is it a general neuroscience concept other labs also record?

- **Lab-specific** → create a custom table in `spyglass_extensions/`
- **General** → open a Spyglass issue before writing any custom tables

### Step 9: Write convert_session.py

```python
from pathlib import Path
from typing import Union
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from <package>.<conversion> import <ConversionName>NWBConverter


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    stub_test: bool = False,
    overwrite: bool = True,
) -> Path:
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    session_id = "..."    # derive from path
    subject_id = "..."    # derive from path
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict(
        Recording=dict(folder_path=str(data_dir_path), stream_id="imec0.ap"),
    )
    conversion_options = dict(
        Recording=dict(stub_test=stub_test),
    )

    phy_path = data_dir_path / "phy"
    if phy_path.is_dir():
        source_data["Sorting"] = dict(folder_path=str(phy_path))
        conversion_options["Sorting"] = dict()

    # Video path — stored outside converter, passed to add_behavioral_video()
    video_path = data_dir_path / "video.mp4"
    if video_path.is_file():
        source_data["video_path"] = str(video_path)

    converter = <ConversionName>NWBConverter(source_data=source_data)
    metadata = converter.get_metadata()

    metadata_path = Path(__file__).parent / "metadata.yaml"
    metadata = dict_deep_update(metadata, load_dict_from_file(metadata_path))

    tz = ZoneInfo("<timezone>")
    if metadata["NWBFile"].get("session_start_time"):
        metadata["NWBFile"]["session_start_time"] = (
            metadata["NWBFile"]["session_start_time"].replace(tzinfo=tz)
        )
    metadata["NWBFile"]["session_id"] = session_id
    metadata["Subject"]["subject_id"] = subject_id

    # Spyglass electrode columns — per-session values
    n_electrodes = ...   # determine from recording interface
    metadata["Electrodes"] = dict(
        probe_shank=[0] * n_electrodes,
        probe_electrode=list(range(n_electrodes)),
        bad_channel=[False] * n_electrodes,
        ref_elect_id=[0] * n_electrodes,
        brain_area=["CA1"] * n_electrodes,    # update per-session if needed
    )

    # Video metadata (used by add_behavioral_video)
    metadata["Video"] = dict(
        camera_name="camera0",
        meters_per_pixel=0.001,
        camera_model="unknown",
        camera_lens="unknown",
        task_name="<task_name>",
        task_description="<task_description>",
        video_description="Behavioral camera recording.",
    )

    converter.run_conversion(
        nwbfile_path=nwbfile_path,
        metadata=metadata,
        conversion_options=conversion_options,
        overwrite=overwrite,
    )
    return nwbfile_path


if __name__ == "__main__":
    session_to_nwb(
        data_dir_path="/path/to/session",
        output_dir_path="/path/to/output",
        stub_test=True,
    )
```

### Step 10: Commit and Push

```bash
git add -A
git commit -m "Phase 6: Spyglass-compatible conversion code

- NWBConverter with ndx_franklab_novela device setup
- utils/add_behavioral_video.py (CameraDevice + task_table)
- utils/add_behavior.py (DIO events + analog signals)
- utils/add_ecephys.py (electrode columns, LFP placement)
- convert_session.py and convert_all_sessions.py"
```
