# Intracellular Electrophysiology (icephys) — PyNWB Patterns

Construction patterns for patch clamp / intracellular recording data.

## Device + Electrode

```python
from pynwb.icephys import IntracellularElectrode

device = nwbfile.create_device(
    name="Amplifier",
    description="MultiClamp 700B",
    manufacturer="Molecular Devices",
)

electrode = nwbfile.create_icephys_electrode(
    name="electrode_0",
    description="Patch clamp electrode",
    device=device,
)
```

## Recording Series Types

**CurrentClampSeries** — response recorded during current injection:
```python
from pynwb.icephys import CurrentClampSeries

cc_response = CurrentClampSeries(
    name="current_clamp_response",
    data=voltage_trace,          # recorded voltage (numpy array)
    electrode=electrode,
    rate=20000.0,                # sampling rate in Hz
    unit="volts",
    gain=1.0,
    stimulus_description="step_protocol",
    sweep_number=np.uint32(0),   # optional, for grouping sweeps
)
nwbfile.add_acquisition(cc_response)
```

**CurrentClampStimulusSeries** — the injected current waveform:
```python
from pynwb.icephys import CurrentClampStimulusSeries

cc_stimulus = CurrentClampStimulusSeries(
    name="current_clamp_stimulus",
    data=current_waveform,       # injected current (numpy array)
    electrode=electrode,
    rate=20000.0,
    unit="amperes",
    gain=1.0,
    sweep_number=np.uint32(0),
)
nwbfile.add_stimulus(cc_stimulus)
```

**VoltageClampSeries** — response recorded during voltage clamp:
```python
from pynwb.icephys import VoltageClampSeries

vc_response = VoltageClampSeries(
    name="voltage_clamp_response",
    data=current_trace,          # recorded current
    electrode=electrode,
    rate=20000.0,
    unit="amperes",
    gain=1.0,
    stimulus_description="voltage_step",
)
nwbfile.add_acquisition(vc_response)
```

**VoltageClampStimulusSeries** — the command voltage:
```python
from pynwb.icephys import VoltageClampStimulusSeries

vc_stimulus = VoltageClampStimulusSeries(
    name="voltage_clamp_stimulus",
    data=voltage_command,
    electrode=electrode,
    rate=20000.0,
    unit="volts",
    gain=1.0,
)
nwbfile.add_stimulus(vc_stimulus)
```

**IZeroClampSeries** — recording with no current injection (I=0 mode):
```python
from pynwb.icephys import IZeroClampSeries

izero = IZeroClampSeries(
    name="izero_response",
    data=voltage_trace,
    electrode=electrode,
    rate=20000.0,
    unit="volts",
)
nwbfile.add_acquisition(izero)
```

## Intracellular Recording Tables

Link each stimulus/response pair into the icephys metadata tables. These tables replace
the deprecated `SweepTable` and are the standard way to say which series belong together.

```python
# One row per sweep per electrode. Adds stimulus/response to the file if not already added.
recording_index = nwbfile.add_intracellular_recording(
    electrode=electrode,
    stimulus=cc_stimulus,        # None for IZeroClampSeries responses
    response=cc_response,
    # stimulus_template=template,  # optional; see note below
)

# Recordings acquired at the same time (e.g. two electrodes in one sweep)
simultaneous_index = nwbfile.add_icephys_simultaneous_recording(recordings=[recording_index])

# Sweeps that form one protocol run, labeled by stimulus type
sequential_index = nwbfile.add_icephys_sequential_recording(
    simultaneous_recordings=[simultaneous_index],
    stimulus_type="current_steps",
)

# Optional higher levels
repetition_index = nwbfile.add_icephys_repetition(sequential_recordings=[sequential_index])
nwbfile.add_icephys_experimental_condition(repetitions=[repetition_index])
```

**Stimulus templates.** When the file holds a recorded command (e.g. a DAQ loopback channel
written as `stimulus`), store the intended command waveform with
`nwbfile.add_stimulus_template(template)` and pass it as `stimulus_template=`.
`add_intracellular_recording` does not add the template to the file for you.

`stimulus_template` is an optional column of the stimuli category table. A row with a template
added after a row without one fails with `ValueError: column must have the same number of rows as 'id'`.
If only some sweeps have a template, create the column while the table is still empty:

```python
from pynwb.base import TimeSeriesReferenceVectorData

nwbfile.get_intracellular_recordings().category_tables["stimuli"].add_column(
    name="stimulus_template",
    description="Intended command waveform for each recording.",
    col_cls=TimeSeriesReferenceVectorData,
)
```

Rows added without a template then get an empty reference.

## Notes

- Do not use `SweepTable` (deprecated in PyNWB 2.0, raises an error on creation since 3.0).
  `sweep_number` on individual series is still valid and useful alongside the tables.
- Each electrode represents a physical pipette. Multiple sweeps use the same electrode.
- `stimulus_description` is fixed to `"N/A"` on `IZeroClampSeries`; any other value is
  ignored with a warning.
- `gain` is the amplifier gain (float). Set to `1.0` if gain is already applied to data.
- References: PyNWB icephys tutorial
  (https://pynwb.readthedocs.io/en/stable/tutorials/domain/plot_icephys.html) and NeuroConv's
  `src/neuroconv/tools/icephys.py`, which builds the full table hierarchy for its icephys interfaces.

## Metadata YAML Template

NeuroConv keys devices and electrodes by a metadata key; an electrode links its device
with `device_metadata_key`.

```yaml
Devices:
  amplifier:
    name: Amplifier
    description: MultiClamp 700B patch clamp amplifier
    manufacturer: Molecular Devices
Icephys:
  IntracellularElectrodes:
    electrode_0:
      name: electrode_0
      description: Borosilicate glass pipette, 3-5 MOhm
      device_metadata_key: amplifier
```
