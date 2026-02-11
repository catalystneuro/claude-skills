# Fiber Photometry — ndx-fiber-photometry Patterns

Construction patterns using the `ndx-fiber-photometry` extension (v0.2.3+)
with `ndx-ophys-devices` (v0.3.1+).
This is the **required** extension for fiber photometry data — do not store
fiber photometry signals as plain TimeSeries.

## Installation

```bash
uv pip install ndx-fiber-photometry
```

Dependencies: `pynwb>=3.1.0`, `hdmf>=4.1.0`, `ndx-ophys-devices>=0.3.1`

## Overview

The extension defines a structured hierarchy:

1. **Devices** — optical fiber, excitation source, photodetector, filters, dichroic mirrors
2. **Biological components** — indicator (e.g., dLight1.1, GCaMP6f), viral vector, injection
3. **FiberPhotometryTable** — DynamicTable linking devices + indicator + brain region per channel
4. **FiberPhotometryResponseSeries** — TimeSeries holding fluorescence data, referencing table rows
5. **CommandedVoltageSeries** — optional voltage commands controlling excitation sources
6. **FiberPhotometry** — LabMetaData container wrapping everything

## ndx-ophys-devices v0.3.1+ API

**IMPORTANT**: The ndx-ophys-devices API was significantly reworked in v0.3.x.
Many parameters from earlier versions were removed or renamed. Always check
the [ndx-fiber-photometry README](https://github.com/catalystneuro/ndx-fiber-photometry)
for the canonical, up-to-date constructor signatures.

Key changes from older versions:
- **ExcitationSource**: No longer accepts `illumination_type` or
  `excitation_wavelength_in_nm`. Now accepts `power_in_W`,
  `intensity_in_W_per_m2`, `exposure_time_in_s`, `model`, `serial_number`.
- **Photodetector**: No longer accepts `detector_type` or
  `detected_wavelength_in_nm`. Now accepts `model`, `serial_number`.
- **OpticalFiber**: No longer accepts `numerical_aperture` or
  `core_diameter_in_um`. Now **requires** a `FiberInsertion` child object
  (which must be named `"fiber_insertion"`). Accepts `model`, `serial_number`.
- **FiberInsertion**: Accepts `insertion_position_ap_in_mm`,
  `insertion_position_ml_in_mm`, `insertion_position_dv_in_mm`,
  `position_reference`, `depth_in_mm`, `hemisphere`,
  `insertion_angle_pitch_in_deg`.
- **BandOpticalFilter** / **DichroicMirror**: No longer accept wavelength
  parameters. Use `description` for filter specs.
- **Indicator**: No longer accepts `injection_location`,
  `excitation_wavelength_in_nm`, or `emission_wavelength_in_nm`. Now accepts
  `viral_vector_injection` to link to injection metadata.
- **FiberPhotometryIndicators**: Does **not** accept a `name` parameter.

## Complete Construction Example

```python
from ndx_fiber_photometry import (
    FiberPhotometry,
    FiberPhotometryTable,
    FiberPhotometryResponseSeries,
    CommandedVoltageSeries,
    FiberPhotometryIndicators,
)
from ndx_ophys_devices import (
    ExcitationSource,
    FiberInsertion,
    OpticalFiber,
    Photodetector,
    BandOpticalFilter,
    DichroicMirror,
    Indicator,
)

# ── Step 1: Create Devices ──────────────────────────────────────────────
# See ndx-fiber-photometry README for all accepted parameters.

excitation_source = ExcitationSource(
    name="excitation_source_signal",
    description="465 nm blue LED for dLight excitation",
    manufacturer="Doric Lenses",
    power_in_W=0.7,
)
nwbfile.add_device(excitation_source)

excitation_source_isos = ExcitationSource(
    name="excitation_source_isosbestic",
    description="405 nm violet LED for isosbestic control",
    manufacturer="Doric Lenses",
)
nwbfile.add_device(excitation_source_isos)

photodetector = Photodetector(
    name="photodetector",
    description="Femtowatt photoreceiver for green emission",
    manufacturer="Newport",
)
nwbfile.add_device(photodetector)

# OpticalFiber requires a FiberInsertion (must be named "fiber_insertion")
fiber_insertion = FiberInsertion(
    name="fiber_insertion",
    insertion_position_ap_in_mm=0.5,
    insertion_position_ml_in_mm=1.5,
    insertion_position_dv_in_mm=-3.0,
    depth_in_mm=3.5,
    position_reference="bregma",
    hemisphere="right",
)

optical_fiber = OpticalFiber(
    name="optical_fiber",
    description="400 um core, 0.48 NA fiber optic cannula",
    manufacturer="Doric Lenses",
    fiber_insertion=fiber_insertion,
)
nwbfile.add_device(optical_fiber)

dichroic_mirror = DichroicMirror(
    name="dichroic_mirror",
    description="495 nm dichroic mirror",
    manufacturer="Semrock",
)
nwbfile.add_device(dichroic_mirror)

emission_filter = BandOpticalFilter(
    name="emission_filter",
    description="500-550 nm bandpass emission filter",
    manufacturer="Semrock",
)
nwbfile.add_device(emission_filter)

# ── Step 2: Create Indicator ────────────────────────────────────────────

indicator = Indicator(
    name="dLight1.1",
    description="Genetically-encoded dopamine sensor dLight1.1",
    label="dLight1.1",
)

# NOTE: FiberPhotometryIndicators does NOT accept a name parameter.
indicators = FiberPhotometryIndicators(
    indicators=[indicator],
)

# ── Step 3: Build FiberPhotometryTable ──────────────────────────────────

fp_table = FiberPhotometryTable(
    name="FiberPhotometryTable",
    description="Fiber photometry channel configuration",
)

# Signal channel (465nm excitation → dLight fluorescence)
fp_table.add_row(
    location="DMS",
    excitation_wavelength_in_nm=465.0,
    emission_wavelength_in_nm=525.0,
    indicator=indicator,
    optical_fiber=optical_fiber,
    excitation_source=excitation_source,
    photodetector=photodetector,
    dichroic_mirror=dichroic_mirror,
    emission_filter=emission_filter,
)

# Isosbestic control channel (405nm excitation → same fiber)
fp_table.add_row(
    location="DMS",
    excitation_wavelength_in_nm=405.0,
    emission_wavelength_in_nm=525.0,
    indicator=indicator,
    optical_fiber=optical_fiber,
    excitation_source=excitation_source_isos,
    photodetector=photodetector,
    dichroic_mirror=dichroic_mirror,
    emission_filter=emission_filter,
)

# ── Step 4: Create Response Series ──────────────────────────────────────

# Reference specific rows of the table
signal_region = fp_table.create_fiber_photometry_table_region(
    region=[0],
    description="Signal channel (465nm dLight)",
)

isos_region = fp_table.create_fiber_photometry_table_region(
    region=[1],
    description="Isosbestic control channel (405nm)",
)

signal_series = FiberPhotometryResponseSeries(
    name="dff_dms_signal",
    description="dF/F from dLight1.1 in DMS (465nm excitation)",
    data=dff_signal,               # shape: (n_timepoints,)
    rate=20.0,                     # sampling rate in Hz
    unit="F",
    fiber_photometry_table_region=signal_region,
)

isos_series = FiberPhotometryResponseSeries(
    name="dff_dms_isosbestic",
    description="Isosbestic control signal in DMS (405nm excitation)",
    data=dff_isos,
    rate=20.0,
    unit="F",
    fiber_photometry_table_region=isos_region,
)

nwbfile.add_acquisition(signal_series)
nwbfile.add_acquisition(isos_series)

# ── Step 5: Optional CommandedVoltageSeries ─────────────────────────────

commanded_voltage = CommandedVoltageSeries(
    name="commanded_voltage",
    description="Voltage commands to LEDs",
    data=voltage_data,
    rate=10000.0,
    unit="volts",
    frequency=211.0,              # modulation frequency in Hz
)
nwbfile.add_stimulus(commanded_voltage)

# ── Step 6: Wrap in FiberPhotometry LabMetaData ─────────────────────────

fiber_photometry = FiberPhotometry(
    name="fiber_photometry",
    fiber_photometry_table=fp_table,
    fiber_photometry_indicators=indicators,
)
nwbfile.add_lab_meta_data(fiber_photometry)
```

## Multi-Fiber Setup

For experiments with multiple fibers (e.g., DMS + NAc):

```python
# Each fiber needs its own FiberInsertion (all must be named "fiber_insertion"
# but since they belong to different OpticalFiber objects, this is fine)
fi_dms = FiberInsertion(
    name="fiber_insertion",
    insertion_position_ap_in_mm=0.5,
    insertion_position_ml_in_mm=1.5,
    insertion_position_dv_in_mm=-3.0,
)
fi_nac = FiberInsertion(
    name="fiber_insertion",
    insertion_position_ap_in_mm=1.2,
    insertion_position_ml_in_mm=1.0,
    insertion_position_dv_in_mm=-4.0,
)

fiber_dms = OpticalFiber(name="Fiber_DMS", description="...", fiber_insertion=fi_dms)
fiber_nac = OpticalFiber(name="Fiber_NAc", description="...", fiber_insertion=fi_nac)
nwbfile.add_device(fiber_dms)
nwbfile.add_device(fiber_nac)

# Add rows for each fiber × wavelength combination
fp_table.add_row(location="DMS", optical_fiber=fiber_dms,
                 excitation_wavelength_in_nm=465.0, ...)   # row 0
fp_table.add_row(location="DMS", optical_fiber=fiber_dms,
                 excitation_wavelength_in_nm=405.0, ...)   # row 1
fp_table.add_row(location="NAc", optical_fiber=fiber_nac,
                 excitation_wavelength_in_nm=465.0, ...)   # row 2
fp_table.add_row(location="NAc", optical_fiber=fiber_nac,
                 excitation_wavelength_in_nm=405.0, ...)   # row 3

# Create separate response series for each channel
dms_signal = FiberPhotometryResponseSeries(
    name="dff_dms",
    fiber_photometry_table_region=fp_table.create_fiber_photometry_table_region(
        region=[0], description="DMS signal channel"
    ),
    data=dms_data, rate=20.0, unit="F",
)
nac_signal = FiberPhotometryResponseSeries(
    name="dff_nac",
    fiber_photometry_table_region=fp_table.create_fiber_photometry_table_region(
        region=[2], description="NAc signal channel"
    ),
    data=nac_data, rate=20.0, unit="F",
)
```

## Common Indicators

| Indicator | Target | Excitation (nm) | Emission (nm) |
|-----------|--------|-----------------|---------------|
| dLight1.1 | Dopamine | 465 | 525 |
| dLight1.3b | Dopamine | 465 | 525 |
| GRAB-DA | Dopamine | 465 | 525 |
| GCaMP6f | Calcium | 488 | 525 |
| GCaMP7f | Calcium | 488 | 525 |
| rGECO1a | Calcium | 560 | 600 |
| GRAB-ACh | Acetylcholine | 465 | 525 |
| GRAB-5HT | Serotonin | 465 | 525 |
| iGluSnFR | Glutamate | 465 | 525 |

## Metadata YAML Template

```yaml
FiberPhotometry:
  FiberPhotometryTable:
    - location: DMS
      excitation_wavelength_in_nm: 465.0
      emission_wavelength_in_nm: 525.0

  OpticalFibers:
    - name: Fiber_DMS
      description: "400 um core, 0.48 NA fiber optic cannula (Doric Lenses)"

  FiberInsertions:
    - insertion_position_ap_in_mm: 0.5
      insertion_position_ml_in_mm: 1.5
      insertion_position_dv_in_mm: -3.0
      position_reference: "bregma at cortical surface"

  ExcitationSources:
    - name: LED_465nm
      description: "465 nm blue LED (Doric Lenses)"
    - name: LED_405nm
      description: "405 nm violet LED for isosbestic control (Doric Lenses)"

  Photodetectors:
    - name: Newport2151
      description: "Femtowatt photoreceiver, photodiode, ~525 nm detection (Newport)"

  Indicators:
    - name: dLight1.1
      label: dLight1.1
      description: Genetically-encoded dopamine sensor dLight1.1
```

## Notes

- **Always use this extension** for fiber photometry data. Do not store signals as
  plain TimeSeries in a processing module.
- The `FiberPhotometryTable` is a DynamicTable — each row represents one channel
  (one fiber × one excitation wavelength combination).
- Isosbestic control channels (typically 405nm) should be separate rows in the table
  with their own `FiberPhotometryResponseSeries`.
- The `FiberPhotometry` object is added as `lab_meta_data`, not in a processing module.
- `FiberPhotometryResponseSeries` can go in `acquisition` (raw) or `processing` (processed).
- `unit` for fluorescence data is typically `"F"` (arbitrary fluorescence units).
- **ndx-ophys-devices v0.3.1+ breaking changes**: Many constructor parameters from
  earlier versions were removed or renamed. See the "ndx-ophys-devices v0.3.1+ API"
  section above for details. Always check the
  [ndx-fiber-photometry README](https://github.com/catalystneuro/ndx-fiber-photometry)
  for canonical constructor signatures.
