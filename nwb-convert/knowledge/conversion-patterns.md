# Conversion Patterns

How particular conversion problems are solved, with examples from CatalystNeuro conversion repos. The files
every conversion repo has are in `knowledge/repo-structure.md`.

Real examples are copied verbatim from the linked commits. Lines marked `# OUTDATED` show what the source did,
with the current replacement in the comment.

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
- An interface whose timestamps must be aligned subclasses `BaseTemporalAlignmentInterface` instead (Section 3).
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

## 3. Temporal Alignment

When data streams have different clocks or start times, override `temporally_align_data_interfaces()` in the
NWBConverter. Phase 4 decides which of its sync patterns applies; the code for each is below.

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

### TTL pulses

Use NeuroConv's helpers for edge detection and alignment instead of thresholding and interpolating by hand.

```python
from neuroconv import NWBConverter
from neuroconv.datainterfaces import SpikeGLXNIDQInterface


class MyConverter(NWBConverter):
    data_interface_classes = dict(NIDQ=SpikeGLXNIDQInterface, Behavior=MyBehaviorInterface)

    def temporally_align_data_interfaces(self, metadata=None, conversion_options=None):
        nidq_interface = self.data_interface_objects["NIDQ"]
        behavior_interface = self.data_interface_objects["Behavior"]

        # Rising-edge times on the NIDQ clock. Name the channel as the board does ("XA2", not "nidq#XA2").
        ttl_times = nidq_interface.get_event_times_from_ttl(channel_name="XA2")

        # The same events as logged on the behavior clock
        behavior_sync_times = ...
        behavior_interface.align_by_interpolation(
            unaligned_timestamps=behavior_sync_times,
            aligned_timestamps=ttl_times[: len(behavior_sync_times)],
        )
```

For TTLs recorded by other systems, read the trace and pass it to
`neuroconv.tools.signal_processing.get_rising_frames_from_ttl(trace, threshold=None)` (or
`get_falling_frames_from_ttl`). It returns frame indices; index the stream's timestamps with them
(`timestamps[rising_frames]`) so the stream's start time is kept. The threshold defaults to the trace mean.

### Starting time offset

```python
interface.set_aligned_starting_time(offset_seconds)
```

Real example: cai-lab-to-nwb's Miniscope timestamps can start below zero. The converter moves the session start
time back by that amount in `get_metadata` and shifts every other stream forward by the same amount.

Source: https://github.com/catalystneuro/cai-lab-to-nwb/blob/a37dadafecaec507669c25baa705333460e0f48d/src/cai_lab_to_nwb/zaki_2024/zaki_2024_nwbconverter.py#L22-L100

```python
class Zaki2024NWBConverter(NWBConverter):
    # ...
    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()

        if "MiniscopeImaging" in self.data_interface_objects:
            imaging_interface = self.data_interface_objects["MiniscopeImaging"]
            imaging_timestamps = imaging_interface.get_original_timestamps()
            # If the first timestamp in the imaging data is negative, adjust the session start time
            # to ensure all timestamps are positive. This is done by shifting the session start time
            # backward by the absolute value of the negative timestamp.
            if imaging_timestamps[0] < 0.0:
                time_shift = timedelta(seconds=abs(imaging_timestamps[0]))
                session_start_time = imaging_interface.get_metadata()["NWBFile"]["session_start_time"]
                metadata["NWBFile"].update(session_start_time=session_start_time - time_shift)
        return metadata

    def temporally_align_data_interfaces(self, metadata: dict | None = None, conversion_options: dict | None = None):
        if "MiniscopeImaging" in self.data_interface_objects:
            imaging_interface = self.data_interface_objects["MiniscopeImaging"]
            imaging_timestamps = imaging_interface.get_original_timestamps()
            # Align the starting times of all data interfaces when the imaging data's first timestamp is negative.
            # This is done by calculating a time shift based on the absolute value of the first negative timestamp.
            # The time shift is applied to all relevant data interfaces to ensure temporal alignment.
            if imaging_timestamps[0] < 0.0:
                time_shift = abs(imaging_timestamps[0])
                imaging_interface.set_aligned_timestamps(imaging_timestamps + time_shift)
                if "MinianSegmentation" in self.data_interface_objects:
                    segmentation_interface = self.data_interface_objects["MinianSegmentation"]
                    segmentation_timestamps = segmentation_interface.get_original_timestamps()
                    segmentation_interface.set_aligned_timestamps(segmentation_timestamps + time_shift)

                # if "MinianMotionCorrection" in self.data_interface_objects:
                #     motion_correction_interface = self.data_interface_objects["MinianMotionCorrection"]
                #     motion_correction_timestamps = motion_correction_interface.get_original_timestamps()
                #     motion_correction_interface.set_aligned_timestamps(motion_correction_timestamps + time_shift)

                if "SleepClassification" in self.data_interface_objects:
                    sleep_classification_interface = self.data_interface_objects["SleepClassification"]
                    start_times, stop_times, sleep_states = sleep_classification_interface.get_sleep_states_times()
                    start_times += time_shift
                    stop_times += time_shift
                    sleep_classification_interface.set_aligned_interval_times(
                        start_times=start_times, stop_times=stop_times
                    )
                if "EDFSignals" in self.data_interface_objects:
                    edf_signals_interface = self.data_interface_objects["EDFSignals"]
                    edf_signals_interface.set_aligned_starting_time(time_shift)

                if "FreezingBehavior" in self.data_interface_objects:
                    freezing_behavior_interface = self.data_interface_objects["FreezingBehavior"]
                    start_times, stop_times = freezing_behavior_interface.get_interval_times()
                    start_times += time_shift
                    stop_times += time_shift
                    freezing_behavior_interface.set_aligned_interval_times(
                        start_times=start_times, stop_times=stop_times
                    )
                    starting_time = freezing_behavior_interface.get_starting_time()
                    freezing_behavior_interface.set_aligned_starting_time(starting_time + time_shift)

                if "Video" in self.data_interface_objects:
                    video_interface = self.data_interface_objects["Video"]
                    video_timestamps = video_interface.get_original_timestamps()
                    # OUTDATED: get_original_timestamps returns a list with one array per video file, so adding a float raises TypeError; use [timestamps + time_shift for timestamps in video_timestamps]
                    aligned_video_timestamps = video_timestamps + time_shift
                    video_interface.set_aligned_timestamps(aligned_video_timestamps)
```

### Interpolation between clocks

```python
interface.align_by_interpolation(
    unaligned_timestamps=sync_times_in_this_clock,
    aligned_timestamps=sync_times_in_reference_clock
)
```

This uses `np.interp`, so timestamps outside the range of the sync times are clamped to the first or
last aligned value. `TimeIntervalsInterface.align_by_interpolation` also takes a `column` argument.

Real example: reimer-arenkiel-lab-to-nwb maps treadmill times from the behavior clock onto the odor clock through
the imaging frame times both clocks recorded. It uses `interp1d` with `fill_value="extrapolate"`, so times outside
the sync range are extrapolated instead of clamped.

Source: https://github.com/catalystneuro/reimer-arenkiel-lab-to-nwb/blob/ac8f1208c990f44c59c58214c26a93965f5ff6c7/src/reimer_arenkiel_lab_to_nwb/dj_utils.py#L37-L58

```python
def add_treadmill(nwbfile: NWBFile, key: dict = None, verbose: bool = False) -> None:
    """Fetch treadmill data and synchronize to odor clock using linear interpolation with extrapolation"""

    if verbose:
        print(f"Adding treadmill data for {key}")

    restriction = odor.MesoMatch & key

    odor_scan_times = (odor.OdorSync & restriction).fetch1("frame_times")
    beh_scan_times = (stimulus.BehaviorSync & restriction).fetch1("frame_times")
    beh_tread_times, tread_vel, tread_raw = (treadmill.Treadmill & restriction).fetch1(
        "treadmill_time", "treadmill_vel", "treadmill_raw"
    )

    if verbose:
        if len(odor_scan_times) != len(beh_scan_times):
            print(f"Length of odor scan times: {len(odor_scan_times)}")
            print(f"Length of behavior scan times: {len(beh_scan_times)}")
    beh_odor_interp = interp1d(
        beh_scan_times, odor_scan_times[: len(beh_scan_times)], kind="linear", fill_value="extrapolate"
    )
    odor_tread_times = beh_odor_interp(beh_tread_times)
```

### Behavior logged per imaging frame

Use the imaging frame times as the time base: write the behavior with `starting_time=0.0` and the frame rate.

Real example: giocomo-lab-to-nwb (Plitt 2021) computes the rate from the time column of a pickled VR DataFrame,
converts centimeters to meters, and writes behavior and stimulus columns to separate places.

Source: https://github.com/catalystneuro/giocomo-lab-to-nwb/blob/a096cdea15291f77793ca334de1eaaa762685c58/giocomo_lab_to_nwb/ophys/giocomovrdatainterface.py#L17-L138

```python
class GiocomoVRInterface(BaseDataInterface):
    # ...
    # OUTDATED: BaseDataInterface.run_conversion now writes a file; the method that adds data to an NWBFile is add_to_nwbfile(self, nwbfile, metadata)
    def run_conversion(self, nwbfile: NWBFile, metadata: dict = None, overwrite: bool = False):
        # ...
        start_time = 0.0
        rate = 1/self.data_frame.time.diff().mean()
        beh_ts = []
        for behdict in self.beh_args:
            if 'cm' in behdict['unit']:
                conv = 1e-2
                behdict.update(unit='m')
            else:
                conv = 1
            behdict.update(starting_time=start_time, rate=rate, data=self.data_frame[behdict['name']].to_numpy()*conv)
            beh_ts.append(TimeSeries(**behdict))
        if 'behavior' not in nwbfile.processing:
            beh_mod = nwbfile.create_processing_module('behavior', 'Container for behavior time series')
            beh_mod.add(BehavioralTimeSeries(time_series=beh_ts, name='BehavioralTimeSeries'))
        else:
            beh_mod = nwbfile.processing['behavior']
            if 'BehavioralTimeSeries' not in beh_mod.data_interfaces:
                beh_mod.add(BehavioralTimeSeries(time_series=beh_ts, name='BehavioralTimeSeries'))

        # adding stimulus:
        for inp_kwargs in self.stimulus_args:
            if inp_kwargs['name'] not in nwbfile.stimulus:
                inp_kwargs.update(starting_time=start_time, rate=rate,
                                  data=self.data_frame[inp_kwargs['name']].to_numpy())
                nwbfile.add_stimulus(TimeSeries(**inp_kwargs))
```

---

## 4. Case-Specific Metadata

### Ophys metadata

Devices, imaging planes, and series go in the dict format that `get_metadata()` returns. `MicroscopySeries`,
`PlaneSegmentations` and the other per-interface entries are keyed by each interface's `metadata_key`. Print
`converter.get_metadata()` and each ophys interface's `get_metadata_template()` and write the YAML in that shape.
Entries in the old list format (`Ophys: Device: - name: ...`) are deprecated: NeuroConv converts them and warns.

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

## 5. Session Discovery

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

## 6. Reading Source Files in Custom Interfaces

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
