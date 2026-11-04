# Temporal Alignment

How to put every data stream of a session on one clock. Phase 4 decides which sync pattern applies; this file has
the code for each, with examples from CatalystNeuro conversion repos.

Real examples are copied verbatim from the linked commits. Lines marked `# OUTDATED` or `# BUG` show what the
source did, with the current replacement or the fix in the comment.

## Where alignment happens

When data streams have different clocks or start times, override `temporally_align_data_interfaces()` in the
NWBConverter:

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

## TTL pulses

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

## Starting time offset

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
                    # BUG: get_original_timestamps returns a list with one array per video file, so adding a float raises TypeError; use [timestamps + time_shift for timestamps in video_timestamps]
                    aligned_video_timestamps = video_timestamps + time_shift
                    video_interface.set_aligned_timestamps(aligned_video_timestamps)
```

## Interpolation between clocks

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

## Behavior logged per imaging frame

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
