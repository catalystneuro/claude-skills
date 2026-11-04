# Fiber Photometry — ndx-fiber-photometry Patterns

Construction patterns for `ndx-fiber-photometry` 0.2.x on `ndx-ophys-devices` 0.3.x.
This is the **required** extension for fiber photometry data — do not store
fiber photometry signals as plain TimeSeries.

## Installation

```bash
uv pip install "ndx-fiber-photometry>=0.2.4,<0.3"
```

Pin `ndx-fiber-photometry>=0.2.4,<0.3` in the conversion's dependencies. 0.2.4 caps
`ndx-ophys-devices` below 0.4; earlier 0.2.x releases do not, and resolve to
`ndx-ophys-devices` 0.4, which removes `FiberInsertion` (replaced by `StereotacticPosition`).

## Overview

The extension defines a structured hierarchy:

1. **Devices** — optical fiber, excitation source, photodetector, filters, dichroic mirrors
2. **Biological components** — indicator (e.g., dLight1.1, GCaMP6f), viral vector, injection
3. **FiberPhotometryTable** — DynamicTable linking devices + indicator + brain region per channel
4. **FiberPhotometryResponseSeries** — TimeSeries holding fluorescence data, referencing table rows
5. **CommandedVoltageSeries** — optional voltage commands controlling excitation sources
6. **FiberPhotometry** — LabMetaData container wrapping everything

## Complete Construction Example

Device specifications (wavelengths, numerical aperture, detector type, filter bands) go on the
`*Model` objects from ndx-ophys-devices, added with `nwbfile.add_device_model()`. Each device
instance links to its model with `model=` and carries only instance-level values such as
`serial_number` or `power_in_W`.

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
from ndx_ophys_devices import (
    BandOpticalFilter,
    BandOpticalFilterModel,
    DichroicMirror,
    DichroicMirrorModel,
    ExcitationSource,
    ExcitationSourceModel,
    FiberInsertion,
    Indicator,
    OpticalFiber,
    OpticalFiberModel,
    Photodetector,
    PhotodetectorModel,
    ViralVector,
    ViralVectorInjection,
)

# ── Step 1: Device models and devices ───────────────────────────────────

led_465_model = ExcitationSourceModel(
    name="Doric LED 465",
    description="465 nm LED for dLight excitation",
    manufacturer="Doric Lenses",
    source_type="LED",
    excitation_mode="one-photon",
    wavelength_range_in_nm=[460.0, 470.0],
)
led_405_model = ExcitationSourceModel(
    name="Doric LED 405",
    description="405 nm LED for isosbestic excitation",
    manufacturer="Doric Lenses",
    source_type="LED",
    excitation_mode="one-photon",
    wavelength_range_in_nm=[400.0, 410.0],
)
photodetector_model = PhotodetectorModel(
    name="Newport 2151",
    description="Femtowatt photoreceiver",
    manufacturer="Newport",
    detector_type="Photodiode",
    wavelength_range_in_nm=[400.0, 1070.0],
)
optical_fiber_model = OpticalFiberModel(
    name="Doric MFC_400",
    description="Mono fiber-optic cannula",
    manufacturer="Doric Lenses",
    numerical_aperture=0.48,
    core_diameter_in_um=400.0,
)
dichroic_mirror_model = DichroicMirrorModel(
    name="Semrock FF495-Di03",
    description="495 nm single-edge dichroic beamsplitter",
    manufacturer="Semrock",
    cut_on_wavelength_in_nm=495.0,
)
emission_filter_model = BandOpticalFilterModel(
    name="Semrock FF01-525-50",
    description="525/50 nm bandpass emission filter",
    manufacturer="Semrock",
    filter_type="Bandpass",
    center_wavelength_in_nm=525.0,
    bandwidth_in_nm=50.0,
)
for device_model in (
    led_465_model, led_405_model, photodetector_model, optical_fiber_model, dichroic_mirror_model, emission_filter_model
):
    nwbfile.add_device_model(device_model)

excitation_source_465 = ExcitationSource(
    name="excitation_source_465", description="Signal excitation LED", model=led_465_model, power_in_W=0.7
)
excitation_source_405 = ExcitationSource(
    name="excitation_source_405", description="Isosbestic excitation LED", model=led_405_model
)
photodetector = Photodetector(name="photodetector", description="Green-channel detector", model=photodetector_model)
optical_fiber = OpticalFiber(
    name="optical_fiber",
    description="Fiber implanted above right DMS",
    model=optical_fiber_model,
    fiber_insertion=FiberInsertion(
        insertion_position_ap_in_mm=0.5,
        insertion_position_ml_in_mm=1.5,
        insertion_position_dv_in_mm=-3.0,
        depth_in_mm=3.5,
        position_reference="bregma",
        hemisphere="right",
    ),
)
dichroic_mirror = DichroicMirror(
    name="dichroic_mirror", description="Excitation/emission splitter", model=dichroic_mirror_model
)
emission_filter = BandOpticalFilter(
    name="emission_filter", description="Green emission filter", model=emission_filter_model
)
for device in (
    excitation_source_465, excitation_source_405, photodetector, optical_fiber, dichroic_mirror, emission_filter
):
    nwbfile.add_device(device)

# ── Step 2: Virus, injection, and indicator ─────────────────────────────

viral_vector = ViralVector(
    name="AAV5-CAG-dLight1.1",
    construct_name="AAV5-CAG-dLight1.1",
    description="Dopamine sensor virus",
    manufacturer="Addgene",
    titer_in_vg_per_ml=1.0e13,
)
viral_vector_injection = ViralVectorInjection(
    name="dLight1.1 injection",
    description="dLight1.1 injection into right DMS",
    location="DMS",
    hemisphere="right",
    reference="bregma",
    ap_in_mm=0.5,
    ml_in_mm=1.5,
    dv_in_mm=-3.2,
    volume_in_uL=0.5,
    viral_vector=viral_vector,
)
indicator = Indicator(
    name="dLight1.1",
    description="Genetically-encoded dopamine sensor dLight1.1",
    label="dLight1.1",
    viral_vector_injection=viral_vector_injection,
)

# ── Step 3: FiberPhotometryTable (one row per fiber × excitation wavelength) ──

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
    excitation_source=excitation_source_465,
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
    excitation_source=excitation_source_405,
    photodetector=photodetector,
    dichroic_mirror=dichroic_mirror,
    emission_filter=emission_filter,
)

# ── Step 4: FiberPhotometry lab metadata ────────────────────────────────
# Add the table to the file before creating series that reference it.

fiber_photometry = FiberPhotometry(
    name="fiber_photometry",
    fiber_photometry_table=fiber_photometry_table,
    fiber_photometry_viruses=FiberPhotometryViruses(viral_vectors=[viral_vector]),
    fiber_photometry_virus_injections=FiberPhotometryVirusInjections(viral_vector_injections=[viral_vector_injection]),
    fiber_photometry_indicators=FiberPhotometryIndicators(indicators=[indicator]),  # takes no name
)
nwbfile.add_lab_meta_data(fiber_photometry)

# ── Step 5: Response series ─────────────────────────────────────────────

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

# ── Step 6: Optional CommandedVoltageSeries ─────────────────────────────

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
# One FiberInsertion per fiber (default name "fiber_insertion" is required).
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
                               excitation_source=excitation_source_465, **shared_columns)  # row 0
fiber_photometry_table.add_row(location="DMS", optical_fiber=fiber_dms, excitation_wavelength_in_nm=405.0,
                               excitation_source=excitation_source_405, **shared_columns)  # row 1
fiber_photometry_table.add_row(location="NAc", optical_fiber=fiber_nac, excitation_wavelength_in_nm=465.0,
                               excitation_source=excitation_source_465, **shared_columns)  # row 2
fiber_photometry_table.add_row(location="NAc", optical_fiber=fiber_nac, excitation_wavelength_in_nm=405.0,
                               excitation_source=excitation_source_405, **shared_columns)  # row 3

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
`DeviceModels` dicts (each entry has a `type`, and a device points to its model with
`device_model_metadata_key`). `FiberPhotometry` holds `FiberPhotometryIndicators`, the
optional `FiberPhotometryViruses` and `FiberPhotometryVirusInjections`, and
`FiberPhotometryTable` with keyed `rows` that reference devices and indicators by
`*_metadata_key`.

## Notes

- Raw fluorescence goes in `acquisition`. Processed traces (dF/F, z-score) are
  `FiberPhotometryResponseSeries` in `get_module(nwbfile, "ophys")` referencing the same
  table rows.
- A `ViralVectorInjection` linked from an `Indicator` must also be in
  `FiberPhotometryVirusInjections`, or writing the file fails with an orphan-container error.
- `unit` for fluorescence data is typically `"F"` (arbitrary fluorescence units).
