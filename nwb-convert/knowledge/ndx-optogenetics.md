# Optogenetics — ndx-optogenetics Patterns

**Always use [ndx-optogenetics](https://github.com/rly/ndx-optogenetics) for optogenetics data.** 
It provides all the data types needed to represent both stimulation site metadata and stimulation events in NWB.

| pynwb.ogen (avoid) | ndx-optogenetics (use instead) |
|---|---|
| `OptogeneticStimulusSite` | `OptogeneticSitesTable` |
| `OptogeneticSeries` | `OptogeneticEpochsTable` or `OptogeneticPulsesTable` |

Do **not** use `nwbfile.create_ogen_site()` or `pynwb.ogen.OptogeneticSeries` in new conversions.

### Installation

```bash
uv pip install "ndx-optogenetics>=0.4.1,<0.5"
```

Patterns for ndx-optogenetics 0.4.x. Pin `ndx-optogenetics>=0.4.1,<0.5` in the conversion's
dependencies; 0.4.1 caps ndx-ophys-devices below 0.4 (see `knowledge/ndx-ophys-devices.md`).

### Complete Construction Example

Build the excitation source, optical fiber, viral vector, injection, and effector as in
`knowledge/ndx-ophys-devices.md`; this example uses the objects and variable names from that file.
A stimulation rig needs only the excitation source and optical fiber from the devices there.

```python
from ndx_optogenetics import (
    OptogeneticEffectors,
    OptogeneticEpochsTable,
    OptogeneticExperimentMetadata,
    OptogeneticPulsesTable,
    OptogeneticSitesTable,
    OptogeneticViruses,
    OptogeneticVirusInjections,
)

# OptogeneticSitesTable replaces OptogeneticStimulusSite.
# excitation_source, optical_fiber, effector are built-in columns — do NOT call add_column() for these.
optogenetic_sites_table = OptogeneticSitesTable(
    description="Information about the optogenetic stimulation sites."
)
optogenetic_sites_table.add_row(
    excitation_source=excitation_source,
    optical_fiber=optical_fiber,
    effector=effector,
)

# Bundle all metadata into OptogeneticExperimentMetadata and add to NWB file
optogenetic_experiment_metadata = OptogeneticExperimentMetadata(
    optogenetic_sites_table=optogenetic_sites_table,
    optogenetic_viruses=OptogeneticViruses(viral_vectors=[opsin_viral_vector]),
    optogenetic_virus_injections=OptogeneticVirusInjections(viral_vector_injections=[opsin_viral_vector_injection]),
    optogenetic_effectors=OptogeneticEffectors(effectors=[effector]),
    stimulation_software="Bonsai v2.6.3 + Arduino IDE",
)
nwbfile.add_lab_meta_data(optogenetic_experiment_metadata)

# OptogeneticEpochsTable — use when stimulation is described per epoch (pulse train parameters).
# Replaces OptogeneticSeries for epoch/train-level data.
opto_epochs_table = OptogeneticEpochsTable(
    name="optogenetic_epochs",
    description="Metadata about optogenetic stimulation parameters per epoch",
    target_tables={"optogenetic_sites": optogenetic_sites_table},
)
opto_epochs_table.add_row(
    start_time=0.0,
    stop_time=100.0,
    stimulation_on=True,
    pulse_length_in_ms=40.0,
    period_in_ms=250.0,            # duration between pulse starts
    number_pulses_per_pulse_train=100,
    number_trains=1,
    intertrain_interval_in_ms=0.0,
    power_in_mW=1.0,               # per-epoch stimulation power (milliwatts, not watts)
    wavelength_in_nm=465.0,
    optogenetic_sites=[0],         # index into optogenetic_sites_table
)
nwbfile.add_time_intervals(opto_epochs_table)

# OptogeneticPulsesTable — use when individual pulse timing and power are available.
# Replaces OptogeneticSeries for pulse-level data.
opto_pulses_table = OptogeneticPulsesTable(
    name="optogenetic_pulses",
    description="Metadata about optogenetic stimulation per pulse",
    target_tables={"optogenetic_sites": optogenetic_sites_table},
)
opto_pulses_table.add_row(
    start_time=10.0,
    stop_time=10.04,
    power_in_mW=1.0,
    wavelength_in_nm=465.0,
    optogenetic_sites=[0],
)
nwbfile.add_time_intervals(opto_pulses_table)
```

## Notes

- `OptogeneticSitesTable` rows link the excitation source, optical fiber, and effector for each stimulation site.
  Only `effector` is required; leave out `optical_fiber` for stimulation without an implanted fiber (e.g.
  transcranial or LED-on-skull).
- `power_in_mW` in the epoch/pulse tables is the per-stimulation power; `power_in_W` on the `ExcitationSource` device is the hardware spec.
- Both `OptogeneticEpochsTable` and `OptogeneticPulsesTable` can be added to the same NWB file if both epoch-level summaries and pulse-level timing are available.

## Metadata YAML Template

NeuroConv has no optogenetics interface, so the conversion's own interface reads this metadata.
It follows NeuroConv's conventions: devices and models go in the top-level `Devices` and
`DeviceModels` dicts (`knowledge/ndx-ophys-devices.md`, "Metadata YAML"), and the `Optogenetics`
section lists its entries as keyed dicts that reference each other and the devices by
`*_metadata_key`. The interface adds each device a site references with `add_ophys_device` and
builds the other objects with the constructors in the example above. Mark unknown values as
described in `knowledge/ndx-ophys-devices.md`.

```yaml
Optogenetics:
  OptogeneticViruses:
    chr2_virus:
      name: AAV-EF1a-DIO-hChR2(H134R)-EYFP
      construct_name: AAV-EF1a-DIO-hChR2(H134R)-EYFP
      description: Excitatory optogenetic construct for ChR2-EYFP expression
      manufacturer: UNC Vector Core
      titer_in_vg_per_ml: 1.0e+12  # YAML needs the exponent sign to read a float
  OptogeneticVirusInjections:
    chr2_injection:
      name: hChR2 injection
      description: AAV-EF1a-DIO-hChR2(H134R)-EYFP injection into right GPe
      location: GPe
      hemisphere: right
      reference: bregma
      ap_in_mm: -1.5
      ml_in_mm: 3.2
      dv_in_mm: -6.0
      # pitch_in_deg:                    # injection angle
      volume_in_uL: 0.45
      # injection_date:                  # ISO 8601
      viral_vector_metadata_key: chr2_virus
  OptogeneticEffectors:
    chr2:
      name: hChR2-EYFP
      description: Excitatory opsin
      label: hChR2(H134R)-EYFP
      viral_vector_injection_metadata_key: chr2_injection
  OptogeneticSitesTable:
    description: Information about the optogenetic stimulation sites.
    rows:
      gpe_right:
        excitation_source_metadata_key: excitation_source  # key in Devices
        optical_fiber_metadata_key: optical_fiber          # key in Devices
        effector_metadata_key: chr2
  stimulation_software: Bonsai v2.6.3 + Arduino IDE
  OptogeneticEpochsTable:
    name: optogenetic_epochs
    description: Metadata about optogenetic stimulation parameters per epoch.
  OptogeneticPulsesTable:          # only when pulse-level timing is available
    name: optogenetic_pulses
    description: Metadata about optogenetic stimulation per pulse.
```
