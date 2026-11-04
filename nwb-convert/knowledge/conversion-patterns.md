# Conversion Patterns

How particular conversion problems are solved, with examples from CatalystNeuro conversion repos. The files
every conversion repo has are in `knowledge/repo-structure.md`.

Real examples are copied verbatim from the linked commits. Lines marked `# OUTDATED` or `# BUG` show what the
source did, with the current replacement or the fix in the comment.

---

## 1. Converter Patterns

### Pattern 1: NWBConverter (most common)

**Used by**: wen22, cai-lab, turner-lab, constantinople-lab, most modern repos

```python
class MyNWBConverter(NWBConverter):
    data_interface_classes = dict(
        Recording=SpikeGLXRecordingInterface,
        LFP=SpikeGLXRecordingInterface,  # source_data["LFP"] = dict(folder_path=..., stream_id="imec0.lf")
        Sorting=PhySortingInterface,
        Behavior=CustomBehaviorInterface,
    )
```

Key characteristics:
- NWBConverter subclass with `data_interface_classes` dict
- Mix of built-in NeuroConv interfaces and custom ones
- `convert_session.py` builds source_data and conversion_options dicts
- Metadata layered: auto-extracted → YAML → programmatic overrides

Real example: cai-lab-to-nwb (zaki_2024) declares ten interfaces, most of them custom. Each session adds only the
ones it has data for.

Source: https://github.com/catalystneuro/cai-lab-to-nwb/blob/a37dadafecaec507669c25baa705333460e0f48d/src/cai_lab_to_nwb/zaki_2024/zaki_2024_nwbconverter.py#L1-L36

```python
"""Primary NWBConverter class for this dataset."""

from datetime import timedelta

from neuroconv import NWBConverter
# OUTDATED: VideoInterface was removed; use ExternalVideoInterface
from neuroconv.datainterfaces import VideoInterface
from neuroconv.utils.dict import DeepDict

from cai_lab_to_nwb.zaki_2024.interfaces import (
    MinianSegmentationInterface,
    Zaki2024EDFInterface,
    Zaki2024MultiEDFInterface,
    EzTrackFreezingBehaviorInterface,
    Zaki2024SleepClassificationInterface,
    MiniscopeImagingInterface,
    MinianMotionCorrectionInterface,
    Zaki2024ShockStimuliInterface,
    Zaki2024CellRegistrationInterface,
)


class Zaki2024NWBConverter(NWBConverter):
    """Primary conversion class Cai Lab dataset."""

    data_interface_classes = dict(
        MiniscopeImaging=MiniscopeImagingInterface,
        MinianSegmentation=MinianSegmentationInterface,
        MinianMotionCorrection=MinianMotionCorrectionInterface,
        SleepClassification=Zaki2024SleepClassificationInterface,
        EDFSignals=Zaki2024EDFInterface,
        MultiEDFSignals=Zaki2024MultiEDFInterface,
        FreezingBehavior=EzTrackFreezingBehaviorInterface,
        # OUTDATED: VideoInterface was removed; use ExternalVideoInterface
        Video=VideoInterface,
        ShockStimuli=Zaki2024ShockStimuliInterface,
        CellRegistration=Zaki2024CellRegistrationInterface,
    )
```

### Pattern 2: ConverterPipe with pre-built interfaces

**Used by**: ibl-to-nwb, turner-lab (some conversions)

```python
from neuroconv import ConverterPipe

interfaces = []
interfaces.append(SpikeGLXRecordingInterface(folder_path=path, stream_id="imec0.ap"))
if sorting_exists:
    interfaces.append(PhySortingInterface(folder_path=phy_path))
converter = ConverterPipe(data_interfaces=interfaces)
```

Used when:
- Interfaces need custom initialization (API clients, non-file sources)
- Session-dependent interface sets (not all sessions have all data)
- Pre-constructed interface instances needed

Real example: turner-lab-to-nwb (asap_m1_mptp) builds seven custom interfaces from one MATLAB file, passing each
the per-unit metadata from a spreadsheet, and hands them to `ConverterPipe` as a dict so they keep readable names.

Source: https://github.com/catalystneuro/turner-lab-to-nwb/blob/e80a192917490b50db6871180b6d1d9a24772e35/src/turner_lab_to_nwb/asap_m1_mptp/conversion_script.py#L149-L164

```python
    data_interfaces = {
        "electrodes": electrodes_interface,
        "spike": spike_interface,
        "manipulandum": manipulandum_interface,
        "lfp": lfp_interface,
        "emg": emg_interface,
        "trials": trials_interface,
        "antidromic": antidromic_interface
    }
    converter = ConverterPipe(data_interfaces=data_interfaces)

    # Get base metadata from interface and merge with YAML
    # Note: dict_deep_update(a, b) updates a with b, so put converter_metadata first
    # so that general_metadata (with our session-specific values) takes precedence
    converter_metadata = converter.get_metadata()
    metadata = dict_deep_update(converter_metadata, general_metadata)
```

### Pattern 3: Raw PyNWB (legacy or highly custom)

**Used by**: giocomo legacy, mallory21 freely-moving, older repos

```python
nwbfile = NWBFile(session_description=..., identifier=..., session_start_time=...)
# Manually create PyNWB objects
position = Position(spatial_series=SpatialSeries(...))
nwbfile.create_processing_module(name="behavior", description="Processed behavioral data").add(position)
with NWBHDF5IO(path, "w") as io:
    io.write(nwbfile)
```

Used when:
- Data is in highly processed/custom format (e.g., all-in-one .mat file)
- No NeuroConv interface exists and writing one isn't worth it
- Legacy code predating NeuroConv

### Pattern 4: Hybrid (NWBConverter + direct PyNWB)

**Used by**: reimer-arenkiel-lab (DataJoint + TIFF)

Standalone functions add some data directly to an in-memory NWBFile, then the
NWBConverter adds its data streams to that file and writes it:

```python
from neuroconv.tools.nwb_helpers import make_nwbfile_from_metadata

converter = MyConverter(source_data=source_data)
nwbfile = make_nwbfile_from_metadata(metadata=metadata)
# Add more data directly
add_trials_from_database(nwbfile, session_key)
add_behavior_from_database(nwbfile, session_key)
# run_conversion validates metadata, aligns interfaces, adds their data, and writes
converter.run_conversion(nwbfile=nwbfile, nwbfile_path=nwbfile_path, metadata=metadata, overwrite=True)
```

Real example: reimer-arenkiel-lab-to-nwb (embargo2024) adds the raw imaging through the converter and the
treadmill, odor trials, respiration, and segmentation from a DataJoint database with PyNWB, then writes once.
`add_to_nwbfile` does not call `temporally_align_data_interfaces`, so the script calls it first.

Source: https://github.com/catalystneuro/reimer-arenkiel-lab-to-nwb/blob/ac8f1208c990f44c59c58214c26a93965f5ff6c7/src/reimer_arenkiel_lab_to_nwb/embargo2024/embargo2024_convert_session.py#L72-L107

```python
    converter = Embargo2024NWBConverter(source_data=source_data)

    converter.temporally_align_data_interfaces(key=key)

    # Add datetime to conversion
    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    metadata = dict_deep_update(metadata, editable_metadata)

    # Add ophys metadata
    metadata.pop("Ophys", None)
    # OUTDATED: the list-format Ophys metadata in this YAML (Ophys: Device: - name: ...) is deprecated and warns; write it in the dict format that converter.get_metadata() returns
    metadata = dict_deep_update(metadata, ophys_metadata)

    # Run conversion
    if verbose:
        print("Add raw imaging data to NWB file")
    converter.add_to_nwbfile(
        metadata=metadata, nwbfile=nwbfile, conversion_options=conversion_options
    )

    add_treadmill(nwbfile, key=key, verbose=verbose)
    add_subject(nwbfile, key=key, verbose=verbose)
    add_odor_trials(nwbfile, key=key, verbose=verbose)
    add_respiration(nwbfile, key=key, verbose=verbose)
    add_summary_images(nwbfile, key=key, verbose=verbose)

    for ophys_key in tqdm(ophys_keys, desc="Processing imaging planes"):
        if ophys_key['channel']==1:
            imaging_plane = nwbfile.imaging_planes["imaging_plane_channel1"]
            plane_segmentation = add_plane_segmentation(nwbfile, imaging_plane, key=ophys_key, verbose=verbose)
            add_fluorescence(nwbfile, plane_segmentation, key=ophys_key, verbose=verbose)

    if verbose:
        print("Write NWB file")
    # OUTDATED: configure_and_write_nwbfile has no output_filepath argument; use nwbfile_path=nwbfile_path
    configure_and_write_nwbfile(nwbfile=nwbfile, backend="hdf5", output_filepath=nwbfile_path)
```

---

## 2. Custom DataInterface

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
- An interface whose timestamps must be aligned subclasses `BaseTemporalAlignmentInterface` instead (`knowledge/temporal-alignment.md`).
- An interface can take no source files and receive all its data through `conversion_options`, e.g. shock times
  and amplitudes the lab reports in the paper.

Real example: cai-lab-to-nwb's shock stimuli interface takes no source files. The shock times, amplitude, and
duration arrive as `conversion_options`, and it writes them as a `TimeIntervals` table in `nwbfile.stimulus`.

Source: https://github.com/catalystneuro/cai-lab-to-nwb/blob/a37dadafecaec507669c25baa705333460e0f48d/src/cai_lab_to_nwb/zaki_2024/interfaces/zaki_2024_shock_stimuli_interface.py

```python
"""Primary class for converting experiment-specific behavior."""

from pynwb.file import NWBFile

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from typing import Optional, List
from pynwb.epoch import TimeIntervals


class Zaki2024ShockStimuliInterface(BaseDataInterface):
    """Adds annotated events of shock times."""

    keywords = ["behavior", "sleep stages"]

    def __init__(self, verbose: bool = False):

        self.verbose = verbose
        super().__init__()

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()

        return metadata

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        shock_amplitude: float,
        shock_times: list,
        shock_duration: float,
        metadata: Optional[dict] = None,
    ):

        description = (
            "During aversive encoding, after a baseline period of 2 min, mice received three 2 s foot shocks "
            "of either amplitude 0.25 mA (low-shock) or 1.5 mA (high-shock), with an intershock interval of 1 min. "
            "All testing was done in Med Associates chambers. "
        )

        shock_stimuli = TimeIntervals(name="ShockStimuli", description=description)
        column_description = "Shock amplitude in mA"
        shock_stimuli.add_column(name="shock_amplitude", description=column_description)
        for start_time in shock_times:
            shock_stimuli.add_interval(
                start_time=start_time, stop_time=start_time + shock_duration, shock_amplitude=shock_amplitude
            )

        nwbfile.add_stimulus(shock_stimuli)
```

The session script adds it only for fear conditioning sessions, with an empty `source_data` entry:

Source: https://github.com/catalystneuro/cai-lab-to-nwb/blob/a37dadafecaec507669c25baa705333460e0f48d/src/cai_lab_to_nwb/zaki_2024/zaki_2024_convert_session.py#L210-L226

```python
    # Add Sleep Classification output
    if sleep_classification_file_path:
        sleep_classification_file_path = Path(sleep_classification_file_path)
        assert sleep_classification_file_path.is_file(), f"{sleep_classification_file_path} does not exist"
        source_data.update(
            dict(SleepClassification=dict(file_path=sleep_classification_file_path, sampling_frequency=15.0))
        )

    # Add Shock Stimuli times for FC sessions
    if shock_stimulus is not None:

        source_data.update(ShockStimuli=dict())
        conversion_options.update(
            ShockStimuli=shock_stimulus,
        )

    converter = Zaki2024NWBConverter(source_data=source_data, verbose=verbose)
```

---

## 3. Case-Specific Metadata

### Ophys metadata

Devices, imaging planes, and series go in the dict format that `get_metadata()` returns. `MicroscopySeries`,
`PlaneSegmentations` and the other per-interface entries are keyed by each interface's `metadata_key`. Print
`converter.get_metadata()` and each ophys interface's `get_metadata_template()` and write the YAML in that shape.
Entries in the old list format (`Ophys: Device: - name: ...`) are deprecated. Merged onto `get_metadata()`, their
values are not written (the file gets `PlaceholderMicroscope` and indicator `"unknown"`), and NeuroConv only warns
that the format is deprecated.

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

For datasets with several subjects, keep subject fields in a separate YAML file keyed by subject, and merge the
subject's entry in `convert_session.py`:

```python
subject_metadata = load_dict_from_file(Path(__file__).parent / "subject_metadata.yaml")[subject_id]
metadata["Subject"] = dict_deep_update(metadata["Subject"], subject_metadata)
```

Real example: giocomo-lab-to-nwb (wen22).

Source: https://github.com/catalystneuro/giocomo-lab-to-nwb/blob/a096cdea15291f77793ca334de1eaaa762685c58/giocomo_lab_to_nwb/wen22/subject_metadata.yml

```yaml
N2:
  subject_id: N2
  age: P90D
  strain: C57Bl/6
  genotype: wildtype 
  # OUTDATED: a date without a timezone makes PyNWB warn and use the local timezone of the machine running the conversion; use 2019-10-22 00:00:00-07:00
  date_of_birth: 2019-10-22
  # OUTDATED: NeuroConv's metadata schema requires weight as a string with units; use weight: 0.016 kg
  weight: 0.016
  sex: U
```

Source: https://github.com/catalystneuro/giocomo-lab-to-nwb/blob/a096cdea15291f77793ca334de1eaaa762685c58/giocomo_lab_to_nwb/wen22/convert_wen21.py#L68-L72

```python
    ## Subject metadata
    subject = session_id.split("_")[0]
    subject_metadata_from_yaml = load_dict_from_file(general_metadata_path.with_stem("subject_metadata"))
    subject_metadata = subject_metadata_from_yaml[subject]
    metadata["Subject"] = dict_deep_update(metadata["Subject"], subject_metadata)
```

---

## 4. Session Discovery

`get_session_to_nwb_kwargs_per_session` in `convert_all_sessions.py` returns one dict of `session_to_nwb`
arguments per session. Common ways to find the sessions:

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

Real example: cai-lab-to-nwb lists the subjects in the lab's design spreadsheet and reads each session's arguments
from a YAML file that a separate script generates from the raw folders.

Source: https://github.com/catalystneuro/cai-lab-to-nwb/blob/a37dadafecaec507669c25baa705333460e0f48d/src/cai_lab_to_nwb/zaki_2024/zaki_2024_convert_all_sessions.py#L79-L115

```python
def get_session_to_nwb_kwargs_per_session(
    *,
    data_dir_path: Union[str, Path],
):
    """Get the kwargs for session_to_nwb for each session in the dataset.

    Parameters
    ----------
    data_dir_path : Union[str, Path]
        The path to the directory containing the raw data.

    Returns
    -------
    list[dict[str, Any]]
        A list of dictionaries containing the kwargs for session_to_nwb for each session.
    """
    #####
    # # Implement this function to return the kwargs for session_to_nwb for each session
    # This can be a specific list with hard-coded sessions, a path expansion or any conversion specific logic that you might need
    #####
    import pandas as pd

    subjects_df = pd.read_excel(data_dir_path / "Ca_EEG_Design.xlsx")
    subjects = subjects_df["Mouse"]
    session_to_nwb_kwargs_per_session = []
    for subject_id in subjects:
        yaml_file_path = Path(__file__).parent / "utils/conversion_parameters.yaml"
        conversion_parameter_dict = load_dict_from_file(yaml_file_path)
        if subject_id in conversion_parameter_dict:
            for session_id in conversion_parameter_dict[subject_id].keys():
                session_to_nwb_kwargs_per_session.append(conversion_parameter_dict[subject_id][session_id])
        else:
            print(
                f"Conversion parameters for subject {subject_id} were not defined in the conversion_parameters.yaml file. Please run utils/define_conversion_parameters.py for subject {subject_id}."
            )

    return session_to_nwb_kwargs_per_session
```

---

## 5. Reading Source Files in Custom Interfaces

### Reading MATLAB .mat files

```python
# For older MATLAB files (v5/v6)
from scipy.io import loadmat
mat = loadmat(file_path)
data = mat["variable_name"]

# More robust alternative to scipy.io.loadmat (handles more MATLAB types)
# pip install pymatreader
from pymatreader import read_mat
mat = read_mat(file_path)
data = mat["variable_name"]

# For MATLAB tables and strings that scipy and pymatreader cannot read
# pip install mat-io
from matio import load_from_mat
mat = load_from_mat(file_path)
data = mat["variable_name"]

# For MATLAB v7.3+ (HDF5-based) — use when the above fail
import h5py
with h5py.File(file_path, "r") as f:
    data = f["variable_name"][:]

# For MATLAB v7.3 with complex nested structures
import hdf5storage
mat = hdf5storage.loadmat(file_path)
```

### Reading text/CSV behavior files

```python
import pandas as pd
# Tab-separated with no header
df = pd.read_csv(file_path, sep="\t", header=None,
                 names=["timestamp", "position", "extra1", "extra2"])

# Or numpy for simple numeric files
import numpy as np
data = np.loadtxt(file_path)
```

### Reading pickled DataFrames

```python
import pickle
with open(file_path, "rb") as f:
    data = pickle.load(f)
df = data["VR_Data"]  # or whatever key
```

**Pickle compatibility**: Pickles saved with older pandas versions may fail to load with
pandas >= 2.0 because `pandas.core.indexes.numeric` was removed. If you encounter
`ModuleNotFoundError: No module named 'pandas.core.indexes.numeric'`:
1. First try loading normally
2. If it fails, the user may need `pandas < 2.0` or to re-save the pickle with a newer version
3. Flag this to the user as a data compatibility issue — it is NOT a bug in the conversion code
