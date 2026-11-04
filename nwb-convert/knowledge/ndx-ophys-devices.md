# Optical Devices and Viral Constructs: ndx-ophys-devices Patterns

`ndx-ophys-devices` defines the optical hardware and viral-construct types that
`ndx-fiber-photometry` (`knowledge/ndx-fiber-photometry.md`) and `ndx-optogenetics`
(`knowledge/ndx-optogenetics.md`) build on. Those files cover their own tables, series, and
lab metadata containers and use the objects built here.

## Version

These patterns are for ndx-ophys-devices 0.3.x. Do not pin it in the conversion's dependencies;
it comes in through `ndx-fiber-photometry>=0.2.4,<0.3` and `ndx-optogenetics>=0.4.1,<0.5`, which
both require `ndx-ophys-devices>=0.3.1,<0.4`. Keep those lower bounds: earlier releases of both
extensions leave it uncapped and resolve to ndx-ophys-devices 0.4, which replaces `FiberInsertion`
and the `ViralVectorInjection` coordinate fields with `StereotacticPosition`.

## Device Models and Devices

Each device type is a pair: a `*Model` that holds the catalog specification (manufacturer,
wavelengths, numerical aperture, detector type, filter bands), and a device instance that links to
it with `model=` and carries only instance-level values such as `serial_number`, `power_in_W`, or
`fiber_insertion`. Add models with `nwbfile.add_device_model()` and instances with
`nwbfile.add_device()`. Every model takes `manufacturer`, and optionally `model_number` and
`description`, from PyNWB's `DeviceModel`.

| Model | Required model fields | Device | Instance fields |
|---|---|---|---|
| `ExcitationSourceModel` | `source_type`, `excitation_mode` | `ExcitationSource` | `power_in_W`, `intensity_in_W_per_m2`, `exposure_time_in_s` |
| `OpticalFiberModel` | `numerical_aperture` | `OpticalFiber` | `fiber_insertion` (required) |
| `PhotodetectorModel` | `detector_type` | `Photodetector` | |
| `DichroicMirrorModel` | none | `DichroicMirror` | |
| `BandOpticalFilterModel` | `filter_type`, `center_wavelength_in_nm`, `bandwidth_in_nm` | `BandOpticalFilter` | |
| `EdgeOpticalFilterModel` | `filter_type`, `cut_wavelength_in_nm` | `EdgeOpticalFilter` | |

Fill the optional specification fields from the datasheet (`wavelength_range_in_nm`,
`core_diameter_in_um`, `active_length_in_mm`, `ferrule_name`, `ferrule_diameter_in_mm`,
`cut_on_wavelength_in_nm`, `gain`, and so on). `PulsedExcitationSource` is an `ExcitationSource`
with `pulse_rate_in_Hz` for pulsed lasers.

```python
from ndx_ophys_devices import (
    BandOpticalFilter,
    BandOpticalFilterModel,
    DichroicMirror,
    DichroicMirrorModel,
    Effector,
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

excitation_source_model = ExcitationSourceModel(
    name="Doric LED 465",
    description="465 nm connectorized LED",
    manufacturer="Doric Lenses",
    model_number="CLED_465",
    source_type="LED",                      # LED | laser
    excitation_mode="one-photon",           # one-photon | two-photon
    wavelength_range_in_nm=[460.0, 470.0],  # [min, max]; equal values for a single-line laser
)
optical_fiber_model = OpticalFiberModel(
    name="Doric MFC_400",
    description="Mono fiber-optic cannula",
    manufacturer="Doric Lenses",
    numerical_aperture=0.48,
    core_diameter_in_um=400.0,
    ferrule_name="MF2.5 zirconia ferrule",
    ferrule_diameter_in_mm=2.5,
)
photodetector_model = PhotodetectorModel(
    name="Newport 2151",
    description="Femtowatt photoreceiver",
    manufacturer="Newport",
    detector_type="Photodiode",
    wavelength_range_in_nm=[400.0, 1070.0],
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
    excitation_source_model, optical_fiber_model, photodetector_model, dichroic_mirror_model, emission_filter_model
):
    nwbfile.add_device_model(device_model)

excitation_source = ExcitationSource(
    name="excitation_source", description="465 nm LED", model=excitation_source_model, power_in_W=0.001
)
optical_fiber = OpticalFiber(
    name="optical_fiber",
    description="Fiber implanted above right DMS",
    serial_number="123456",
    model=optical_fiber_model,
    fiber_insertion=FiberInsertion(
        insertion_position_ap_in_mm=0.5,
        insertion_position_ml_in_mm=1.5,
        insertion_position_dv_in_mm=-3.0,
        depth_in_mm=3.5,
        position_reference="bregma",
        hemisphere="right",
        insertion_angle_pitch_in_deg=0.0,
    ),
)
photodetector = Photodetector(name="photodetector", description="Green-channel detector", model=photodetector_model)
dichroic_mirror = DichroicMirror(
    name="dichroic_mirror", description="Excitation/emission splitter", model=dichroic_mirror_model
)
emission_filter = BandOpticalFilter(
    name="emission_filter", description="Green emission filter", model=emission_filter_model
)
for device in (excitation_source, optical_fiber, photodetector, dichroic_mirror, emission_filter):
    nwbfile.add_device(device)
```

`FiberInsertion` takes the name `fiber_insertion` by default, which the schema requires. All its
fields are optional: AP/ML/DV insertion position, `depth_in_mm`, `position_reference`,
`hemisphere`, and yaw/pitch/roll insertion angles in degrees.

## Viral Vectors, Injections, Indicators, and Effectors

A `ViralVector` describes the construct, a `ViralVectorInjection` where and how much of it was
injected, and an `Indicator` (a fluorescent sensor, for fiber photometry) or an `Effector` (an
opsin, for optogenetics) the expressed protein, linked to its injection.

```python
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
    pitch_in_deg=0.0,
    volume_in_uL=0.5,
    injection_date="2024-01-15T00:00:00+00:00",  # ISO 8601
    viral_vector=viral_vector,
)
indicator = Indicator(
    name="dLight1.1",
    description="Genetically-encoded dopamine sensor dLight1.1",
    label="dLight1.1",
    viral_vector_injection=viral_vector_injection,
)

# An opsin for optogenetics, from its own vector and injection
opsin_viral_vector = ViralVector(
    name="AAV-EF1a-DIO-hChR2(H134R)-EYFP",
    construct_name="AAV-EF1a-DIO-hChR2(H134R)-EYFP",
    description="Excitatory optogenetic construct for ChR2-EYFP expression",
    manufacturer="UNC Vector Core",
    titer_in_vg_per_ml=1.0e12,
)
opsin_viral_vector_injection = ViralVectorInjection(
    name="hChR2 injection",
    description="AAV-EF1a-DIO-hChR2(H134R)-EYFP injection into right GPe",
    location="GPe",
    hemisphere="right",
    reference="bregma",
    ap_in_mm=-1.5,
    ml_in_mm=3.2,
    dv_in_mm=-6.0,
    volume_in_uL=0.45,
    viral_vector=opsin_viral_vector,
)
effector = Effector(
    name="hChR2-EYFP",
    description="Excitatory opsin",
    label="hChR2(H134R)-EYFP",
    viral_vector_injection=opsin_viral_vector_injection,
)
```

- Add every `ViralVector` and `ViralVectorInjection` to the extension's container
  (`FiberPhotometryViruses` and `FiberPhotometryVirusInjections`, or `OptogeneticViruses` and
  `OptogeneticVirusInjections`). One linked from an `Indicator` or `Effector` but missing from the
  container makes writing the file fail with an orphan-container error.
- `location` on an injection, and the brain region of a fiber, use standard atlas nomenclature
  (the Allen Mouse Brain Atlas for mice).

## Metadata YAML

Devices and device models go in the top-level `Devices` and `DeviceModels` dicts used across
NeuroConv. Each entry is keyed by a handle, names its class in `type`, and a device points to its
model with `device_model_metadata_key`. Tables and containers reference devices by these handles
through `*_metadata_key` fields. Include every field of each class, optional ones too; where the
value is unknown, comment the line out and say in an inline comment what the field holds.

```yaml
DeviceModels:
  excitation_source_model:
    type: ExcitationSourceModel
    name: Doric LED 465
    description: 465 nm connectorized LED
    manufacturer: Doric Lenses
    model_number: CLED_465
    source_type: LED                        # LED | laser
    excitation_mode: one-photon             # one-photon | two-photon
    wavelength_range_in_nm: [460.0, 470.0]  # [min, max] from the datasheet
  optical_fiber_model:
    type: OpticalFiberModel
    name: Doric MFC_400
    description: Mono fiber-optic cannula
    manufacturer: Doric Lenses
    numerical_aperture: 0.48
    core_diameter_in_um: 400.0
    # active_length_in_mm:               # length of the light-emitting region, for tapered fibers
    ferrule_name: MF2.5 zirconia ferrule
    ferrule_diameter_in_mm: 2.5

Devices:
  excitation_source:
    type: ExcitationSource
    name: excitation_source
    description: 465 nm LED
    device_model_metadata_key: excitation_source_model
    power_in_W: 0.001
    # intensity_in_W_per_m2:             # excitation intensity in W/m^2
  optical_fiber:
    type: OpticalFiber
    name: optical_fiber
    description: Fiber implanted above right DMS
    serial_number: "123456"
    device_model_metadata_key: optical_fiber_model
    fiber_insertion:
      insertion_position_ap_in_mm: 0.5
      insertion_position_ml_in_mm: 1.5
      insertion_position_dv_in_mm: -3.0
      depth_in_mm: 3.5
      position_reference: bregma
      hemisphere: right
      insertion_angle_pitch_in_deg: 0.0
```

NeuroConv's fiber photometry interfaces read these dicts themselves
(`knowledge/ndx-fiber-photometry.md`). An interface the conversion writes itself, such as one for
optogenetics, adds each device it references with this helper:

```python
import ndx_ophys_devices


def add_ophys_device(nwbfile, metadata: dict, metadata_key: str):
    """Add the device metadata["Devices"][metadata_key] and its model to the NWB file, once per name."""
    device_metadata = dict(metadata["Devices"][metadata_key])
    if device_metadata["name"] in nwbfile.devices:
        return nwbfile.devices[device_metadata["name"]]

    model_metadata = dict(metadata["DeviceModels"][device_metadata.pop("device_model_metadata_key")])
    if model_metadata["name"] in nwbfile.device_models:
        device_model = nwbfile.device_models[model_metadata["name"]]
    else:
        device_model = getattr(ndx_ophys_devices, model_metadata.pop("type"))(**model_metadata)
        nwbfile.add_device_model(device_model)

    if "fiber_insertion" in device_metadata:
        device_metadata["fiber_insertion"] = ndx_ophys_devices.FiberInsertion(**device_metadata["fiber_insertion"])
    device = getattr(ndx_ophys_devices, device_metadata.pop("type"))(model=device_model, **device_metadata)
    nwbfile.add_device(device)
    return device
```
