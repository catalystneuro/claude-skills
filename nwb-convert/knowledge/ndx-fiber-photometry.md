# Fiber Photometry — ndx-fiber-photometry Patterns

Construction patterns for `ndx-fiber-photometry` 0.2.x on `ndx-ophys-devices` 0.3.x.
This is the **required** extension for fiber photometry data — do not store
fiber photometry signals as plain TimeSeries.

## Installation

```bash
uv pip install "ndx-fiber-photometry>=0.2.4,<0.3"
```

Pin `ndx-fiber-photometry>=0.2.4,<0.3` in the conversion's dependencies. 0.2.4 caps
`ndx-ophys-devices` below 0.4; see `knowledge/ndx-ophys-devices.md` for the device classes and
the version constraint.

## Overview

The extension defines a structured hierarchy:

1. **Devices** — optical fiber, excitation source, photodetector, filters, dichroic mirrors
2. **Biological components** — indicator (e.g., dLight1.1, GCaMP6f), viral vector, injection
3. **FiberPhotometryTable** — DynamicTable linking devices + indicator + brain region per channel
4. **FiberPhotometryResponseSeries** — TimeSeries holding fluorescence data, referencing table rows
5. **CommandedVoltageSeries** — optional voltage commands controlling excitation sources
6. **FiberPhotometry** — LabMetaData container wrapping everything

## Complete Construction Example

Build the device models, devices, viral vector, injection, and indicator as in
`knowledge/ndx-ophys-devices.md`; this example uses the objects and variable names from that file.
The isosbestic control channel needs a second excitation source.

```python
from ndx_fiber_photometry import (
    CommandedVoltageSeries,
    FiberPhotometry,
    FiberPhotometryIndicators,
    FiberPhotometryResponseSeries,
    FiberPhotometryTable,
    FiberPhotometryViruses,
    FiberPhotometryVirusInjections,
)
from ndx_ophys_devices import ExcitationSource, ExcitationSourceModel

isosbestic_source_model = ExcitationSourceModel(
    name="Doric LED 405",
    description="405 nm connectorized LED",
    manufacturer="Doric Lenses",
    source_type="LED",
    excitation_mode="one-photon",
    wavelength_range_in_nm=[400.0, 410.0],
)
nwbfile.add_device_model(isosbestic_source_model)
isosbestic_source = ExcitationSource(
    name="isosbestic_source", description="Isosbestic excitation LED", model=isosbestic_source_model
)
nwbfile.add_device(isosbestic_source)

# ── Step 1: FiberPhotometryTable (one row per fiber × excitation wavelength) ──

fiber_photometry_table = FiberPhotometryTable(
    name="fiber_photometry_table",
    description="Fiber photometry channel configuration",
)
fiber_photometry_table.add_row(
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
fiber_photometry_table.add_row(
    location="DMS",
    excitation_wavelength_in_nm=405.0,  # isosbestic control on the same fiber
    emission_wavelength_in_nm=525.0,
    indicator=indicator,
    optical_fiber=optical_fiber,
    excitation_source=isosbestic_source,
    photodetector=photodetector,
    dichroic_mirror=dichroic_mirror,
    emission_filter=emission_filter,
)

# ── Step 2: FiberPhotometry lab metadata ────────────────────────────────
# Add the table to the file before creating series that reference it.

fiber_photometry = FiberPhotometry(
    name="fiber_photometry",
    fiber_photometry_table=fiber_photometry_table,
    fiber_photometry_viruses=FiberPhotometryViruses(viral_vectors=[viral_vector]),
    fiber_photometry_virus_injections=FiberPhotometryVirusInjections(viral_vector_injections=[viral_vector_injection]),
    fiber_photometry_indicators=FiberPhotometryIndicators(indicators=[indicator]),  # takes no name
)
nwbfile.add_lab_meta_data(fiber_photometry)

# ── Step 3: Response series ─────────────────────────────────────────────

signal_series = FiberPhotometryResponseSeries(
    name="raw_dms_465",
    description="Raw demodulated fluorescence from dLight1.1 in DMS (465 nm excitation)",
    data=raw_465,  # shape: (n_timepoints,)
    rate=20.0,
    unit="F",
    fiber_photometry_table_region=fiber_photometry_table.create_fiber_photometry_table_region(
        region=[0], description="DMS 465 nm channel"
    ),
)
isosbestic_series = FiberPhotometryResponseSeries(
    name="raw_dms_405",
    description="Raw demodulated fluorescence in DMS (405 nm isosbestic excitation)",
    data=raw_405,
    rate=20.0,
    unit="F",
    fiber_photometry_table_region=fiber_photometry_table.create_fiber_photometry_table_region(
        region=[1], description="DMS 405 nm isosbestic channel"
    ),
)
nwbfile.add_acquisition(signal_series)
nwbfile.add_acquisition(isosbestic_series)

# ── Step 4: Optional CommandedVoltageSeries ─────────────────────────────

commanded_voltage = CommandedVoltageSeries(
    name="commanded_voltage",
    description="Voltage commands to LEDs",
    data=voltage_data,
    rate=10000.0,
    unit="volts",
    frequency=211.0,  # modulation frequency in Hz
)
nwbfile.add_stimulus(commanded_voltage)
```

## Multi-Fiber Setup

For experiments with multiple fibers (e.g., DMS + NAc), reusing the models, devices, and
indicator from the example above with an empty table:

```python
from ndx_ophys_devices import FiberInsertion, OpticalFiber

# One FiberInsertion per fiber
fiber_dms = OpticalFiber(
    name="optical_fiber_dms",
    description="Fiber implanted above DMS",
    model=optical_fiber_model,
    fiber_insertion=FiberInsertion(
        insertion_position_ap_in_mm=0.5, insertion_position_ml_in_mm=1.5, insertion_position_dv_in_mm=-3.0
    ),
)
fiber_nac = OpticalFiber(
    name="optical_fiber_nac",
    description="Fiber implanted above NAc",
    model=optical_fiber_model,
    fiber_insertion=FiberInsertion(
        insertion_position_ap_in_mm=1.2, insertion_position_ml_in_mm=1.0, insertion_position_dv_in_mm=-4.0
    ),
)
nwbfile.add_device(fiber_dms)
nwbfile.add_device(fiber_nac)

# One row per fiber × excitation wavelength
shared_columns = dict(
    emission_wavelength_in_nm=525.0, indicator=indicator, photodetector=photodetector,
    dichroic_mirror=dichroic_mirror, emission_filter=emission_filter,
)
fiber_photometry_table.add_row(location="DMS", optical_fiber=fiber_dms, excitation_wavelength_in_nm=465.0,
                               excitation_source=excitation_source, **shared_columns)  # row 0
fiber_photometry_table.add_row(location="DMS", optical_fiber=fiber_dms, excitation_wavelength_in_nm=405.0,
                               excitation_source=isosbestic_source, **shared_columns)  # row 1
fiber_photometry_table.add_row(location="NAc", optical_fiber=fiber_nac, excitation_wavelength_in_nm=465.0,
                               excitation_source=excitation_source, **shared_columns)  # row 2
fiber_photometry_table.add_row(location="NAc", optical_fiber=fiber_nac, excitation_wavelength_in_nm=405.0,
                               excitation_source=isosbestic_source, **shared_columns)  # row 3

# A separate response series for each channel
dms_signal = FiberPhotometryResponseSeries(
    name="raw_dms_465",
    description="Raw demodulated fluorescence in DMS (465 nm excitation)",
    fiber_photometry_table_region=fiber_photometry_table.create_fiber_photometry_table_region(
        region=[0], description="DMS 465 nm channel"
    ),
    data=dms_data, rate=20.0, unit="F",
)
nac_signal = FiberPhotometryResponseSeries(
    name="raw_nac_465",
    description="Raw demodulated fluorescence in NAc (465 nm excitation)",
    fiber_photometry_table_region=fiber_photometry_table.create_fiber_photometry_table_region(
        region=[2], description="NAc 465 nm channel"
    ),
    data=nac_data, rate=20.0, unit="F",
)
nwbfile.add_acquisition(dms_signal)
nwbfile.add_acquisition(nac_signal)
```

## Metadata With a NeuroConv Interface

When using a NeuroConv fiber photometry interface, start from
`interface.get_metadata_template()` (or `get_metadata()` for an interface without it, such as
`TDTFiberPhotometryInterface`), fill in the `None` values, and delete the optional entries the
rig did not use. Devices and device models live in the top-level `Devices` and
`DeviceModels` dicts described in `knowledge/ndx-ophys-devices.md` ("Metadata YAML").
`FiberPhotometry` holds `FiberPhotometryIndicators`, the
optional `FiberPhotometryViruses` and `FiberPhotometryVirusInjections`, and
`FiberPhotometryTable` with keyed `rows` that reference devices and indicators by
`*_metadata_key`.

## Notes

- Raw fluorescence goes in `acquisition`. Processed traces (dF/F, z-score) are
  `FiberPhotometryResponseSeries` in `get_module(nwbfile, "ophys")` referencing the same
  table rows.
- `unit` for fluorescence data is typically `"F"` (arbitrary fluorescence units).
