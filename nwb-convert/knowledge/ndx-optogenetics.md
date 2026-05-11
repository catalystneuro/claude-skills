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
uv pip install ndx-optogenetics
```

Dependencies: `pynwb>=3.1.0`, `hdmf>=4.1.0`, `ndx-ophys-devices>=0.3.1`

### Complete Construction Example

```python
from ndx_ophys_devices import (
    ExcitationSourceModel,
    ExcitationSource,
    OpticalFiberModel,
    OpticalFiber,
    FiberInsertion,
    ViralVector,
    ViralVectorInjection,
    Effector,
)
from ndx_optogenetics import (
    OptogeneticSitesTable,
    OptogeneticViruses,
    OptogeneticVirusInjections,
    OptogeneticEffectors,
    OptogeneticExperimentMetadata,
    OptogeneticEpochsTable,
    OptogeneticPulsesTable,
)

# Create and add excitation source devices
excitation_source_model = ExcitationSourceModel(
    name="Omicron LuxX+ 488-100 Model",
    description="Laser for optogenetic stimulation.",
    manufacturer="Omicron",
    source_type="laser",
    excitation_mode="one-photon",
    wavelength_range_in_nm=[488.0, 488.0],  # [min, max]; same value for single-wavelength laser
)
excitation_source = ExcitationSource(
    name="Omicron LuxX+ 488-100",
    model=excitation_source_model,
    power_in_W=0.077,              # device-level power spec (watts)
    intensity_in_W_per_m2=1.0e10,
)
nwbfile.add_device_model(excitation_source_model)  # models use add_device_model()
nwbfile.add_device(excitation_source)              # instances use add_device()

# Create and add optical fiber devices
optical_fiber_model = OpticalFiberModel(
    name="Lambda Model",
    description="Lambda fiber (tapered fiber) from Optogenix.",
    model_number="lambda_b5",
    manufacturer="Optogenix",
    numerical_aperture=0.39,
    core_diameter_in_um=200.0,
    active_length_in_mm=2.0,
    ferrule_name="cFCF - ∅2.5mm Ceramic Ferrule",
    ferrule_diameter_in_mm=2.5,
)
fiber_insertion = FiberInsertion(
    name="fiber_insertion",
    insertion_position_ap_in_mm=-1.5,
    insertion_position_ml_in_mm=3.2,
    insertion_position_dv_in_mm=-5.8,
    depth_in_mm=2.0,
    position_reference="Bregma at the cortical surface",
    hemisphere="right",
    insertion_angle_pitch_in_deg=0.0,
)
optical_fiber = OpticalFiber(
    name="Lambda",
    description="Lambda fiber implanted into right GPe.",
    serial_number="123456",
    model=optical_fiber_model,
    fiber_insertion=fiber_insertion,
)
nwbfile.add_device_model(optical_fiber_model)
nwbfile.add_device(optical_fiber)

# Create virus and injection metadata
virus = ViralVector(
    name="AAV-EF1a-DIO-hChR2(H134R)-EYFP",
    construct_name="AAV-EF1a-DIO-hChR2(H134R)-EYFP",
    description="Excitatory optogenetic construct for ChR2-EYFP expression",
    manufacturer="UNC Vector Core",
    titer_in_vg_per_ml=1.0e12,
)
optogenetic_viruses = OptogeneticViruses(viral_vectors=[virus])

virus_injection = ViralVectorInjection(
    name="AAV-EF1a-DIO-hChR2(H134R)-EYFP Injection",
    description="AAV-EF1a-DIO-hChR2(H134R)-EYFP injection into GPe.",
    hemisphere="right",
    location="GPe",
    ap_in_mm=-1.5,
    ml_in_mm=3.2,
    dv_in_mm=-6.0,
    roll_in_deg=0.0,
    pitch_in_deg=0.0,
    yaw_in_deg=0.0,
    reference="Bregma at the cortical surface",
    viral_vector=virus,
    volume_in_uL=0.45,
    injection_date="1970-01-01T00:00:00+00:00",  # ISO 8601 datetime string
)
optogenetic_virus_injections = OptogeneticVirusInjections(viral_vector_injections=[virus_injection])

# Create effector and link to virus injection
effector = Effector(
    name="effector",
    description="Excitatory opsin",
    label="hChR2-EYFP",
    viral_vector_injection=virus_injection,
)
optogenetic_effectors = OptogeneticEffectors(effectors=[effector])

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
    optogenetic_viruses=optogenetic_viruses,
    optogenetic_virus_injections=optogenetic_virus_injections,
    optogenetic_effectors=optogenetic_effectors,
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
    power_in_mW=77.0,              # per-epoch stimulation power (milliwatts, not watts)
    wavelength_in_nm=488.0,
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
    power_in_mW=77.0,
    wavelength_in_nm=488.0,
    optogenetic_sites=[0],
)
nwbfile.add_time_intervals(opto_pulses_table)
```

## Notes

- `OptogeneticSitesTable` rows link the excitation source, optical fiber, and effector for each stimulation site.
- `power_in_mW` in the epoch/pulse tables is the per-stimulation power; `power_in_W` on the `ExcitationSource` device is the hardware spec.
- Brain region names in `fiber_insertion` and `virus_injection` should use standard atlas nomenclature (Allen Brain Atlas for mice).
- Both `OptogeneticEpochsTable` and `OptogeneticPulsesTable` can be added to the same NWB file if both epoch-level summaries and pulse-level timing are available.
- Include always all device/device model attributes (even the optional ones). If the actual value is not available, comment it out in the generated metadata YAML file, and add an in-line comment with the description of the attribute.


## Metadata YAML Template

```yaml
Optogenetics:
  ExcitationSourceModel:
    - name: Omicron LuxX+ 488-100 Model
      description: Laser for optogenetic stimulation.
      manufacturer: Omicron
      source_type: laser                  # laser | LED
      excitation_mode: one-photon         # one-photon | two-photon
      wavelength_range_in_nm: [438.0, 538.0]  # [min, max]; search ranger values in the datasheet if not provided

  ExcitationSource:
    - name: laser
      model: Omicron LuxX+ 488-100 Model  # references ExcitationSourceModel.name
      power_in_W: 0.077
      intensity_in_W_per_m2: 1.0e10

  OpticalFiberModel:
    - name: Lambda Model
      description: Lambda fiber (tapered fiber) from Optogenix.
      model_number: lambda_b5
      manufacturer: Optogenix
      numerical_aperture: 0.39
      core_diameter_in_um: 200.0
      active_length_in_mm: 2.0
      ferrule_name: "cFCF - 2.5mm Ceramic Ferrule"
      ferrule_diameter_in_mm: 2.5

  OpticalFiber:
    - name: optical_fiber
      description: Lambda fiber implanted into right GPe.
      serial_number: "123456"
      model: Lambda Model                 # references OpticalFiberModel.name
      fiber_insertion:
        insertion_position_ap_in_mm: -1.5
        insertion_position_ml_in_mm: 3.2
        insertion_position_dv_in_mm: -5.8
        depth_in_mm: 2.0
        position_reference: Bregma at the cortical surface
        hemisphere: right
        insertion_angle_pitch_in_deg: 0.0

  ViralVector:
    - name: AAV-EF1a-DIO-hChR2(H134R)-EYFP
      construct_name: AAV-EF1a-DIO-hChR2(H134R)-EYFP
      description: Excitatory optogenetic construct for ChR2-EYFP expression
      manufacturer: UNC Vector Core
      titer_in_vg_per_ml: 1.0e12

  ViralVectorInjection:
    - name: gpe_right
      description: AAV-EF1a-DIO-hChR2(H134R)-EYFP injection into GPe.
      hemisphere: right
      location: GPe
      ap_in_mm: -1.5
      ml_in_mm: 3.2
      dv_in_mm: -6.0
      roll_in_deg: 0.0
      pitch_in_deg: 0.0
      yaw_in_deg: 0.0
      reference: Bregma at the cortical surface
      viral_vector: AAV-EF1a-DIO-hChR2(H134R)-EYFP  # references ViralVector.name
      volume_in_uL: 0.45
      injection_date: "1970-01-01T00:00:00+00:00"    # ISO 8601

  Effector:
    - name: effector
      description: Excitatory opsin
      label: hChR2-EYFP
      viral_vector_injection: gpe_right # references ViralVectorInjection.name

  OptogeneticSitesTable:
    description: Information about the optogenetic stimulation sites.

  OptogeneticExperimentMetadata:
    stimulation_software: Bonsai v2.6.3 + Arduino IDE

  # Use OptogeneticEpochsTable for pulse-train / epoch-level stimulation parameters
  OptogeneticEpochsTable:
    name: optogenetic_epochs
    description: Metadata about optogenetic stimulation parameters per epoch.

  # Use OptogeneticPulsesTable for individual pulse timing and power (optional)
  OptogeneticPulsesTable:
    name: optogenetic_pulses
    description: Metadata about optogenetic stimulation per pulse.
```
