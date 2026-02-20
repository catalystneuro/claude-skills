# Extension Examples and Patterns

Real-world patterns from published NWB extensions. Use these as templates when
designing new extensions.

## Naming Conventions

- **Extension name**: `ndx-` prefix, lowercase, hyphens between words
  - Good: `ndx-fiber-photometry`, `ndx-pose`, `ndx-anatomical-localization`
  - Bad: `ndx_fiber_photometry`, `NDX-Pose`, `ndx-FiberPhotometry`
- **Python package**: Replace hyphens with underscores
  - `ndx-fiber-photometry` → `ndx_fiber_photometry`
- **Neurodata type names**: CamelCase, no prefix
  - Good: `PoseEstimation`, `FiberPhotometryTable`, `Surgery`
  - Bad: `ndx_PoseEstimation`, `pose_estimation`
- **Namespace name**: Same as extension name (`ndx-my-extension`)

## Pattern 1: LabMetaData Extension (Simple Metadata)

The simplest extension pattern. Good for lab-specific session metadata.

**Use case**: Storing surgery details, training history, or experimental parameters
that don't fit in NWBFile's built-in fields.

### Spec

```python
from pynwb.spec import NWBNamespaceBuilder, NWBGroupSpec, NWBAttributeSpec, NWBDatasetSpec

ns_builder = NWBNamespaceBuilder(
    name="ndx-surgery",
    doc="Store surgical procedure metadata in NWB files",
    version="0.1.0",
    author="Lab Name",
    contact="lab@example.com",
)
ns_builder.include_type("LabMetaData", namespace="core")

surgery = NWBGroupSpec(
    neurodata_type_def="Surgery",
    neurodata_type_inc="LabMetaData",
    name="surgery",
    doc="Surgical procedure metadata",
    attributes=[
        NWBAttributeSpec(name="surgery_date", dtype="isodatetime",
                        doc="Date of surgery"),
        NWBAttributeSpec(name="anesthesia", dtype="text",
                        doc="Anesthesia used", required=False),
        NWBAttributeSpec(name="analgesics", dtype="text",
                        doc="Post-operative analgesics", required=False),
        NWBAttributeSpec(name="notes", dtype="text",
                        doc="Surgery notes", required=False),
    ],
    datasets=[
        NWBDatasetSpec(
            name="injection_coordinates",
            doc="Stereotaxic injection coordinates (AP, ML, DV) in mm",
            dtype="float64",
            shape=(None, 3),
            dims=("num_injections", "coordinates"),
            quantity="?",
        ),
    ],
)

ns_builder.add_spec("ndx-surgery.extensions.yaml", surgery)
ns_builder.export("ndx-surgery.namespace.yaml", outdir="spec")
```

### Python API (auto-generated)

```python
from pynwb import load_namespaces, get_class

load_namespaces("ndx-surgery.namespace.yaml")
Surgery = get_class("Surgery", "ndx-surgery")
```

### Usage

```python
from ndx_surgery import Surgery

surgery = Surgery(
    surgery_date="2024-01-15T10:30:00-05:00",
    anesthesia="isoflurane 1.5-2%",
    analgesics="buprenorphine 0.1 mg/kg",
    notes="Craniotomy over V1, fiber implanted at AP -3.5, ML 2.5, DV -0.3",
)
nwbfile.add_lab_meta_data(surgery)
```

## Pattern 2: Multi-Type Hierarchy (ndx-pose)

A complex extension with multiple interrelated types forming a hierarchy.

**Structure:**
```
Skeleton (NWBDataInterface)
  ├── nodes: text[]              — body part names
  └── edges: uint8[N,2]         — connections between nodes

PoseEstimationSeries (TimeSeries)
  ├── data: float32[T, 2|3]    — x,y(,z) positions
  ├── confidence: float32[T]   — per-frame confidence
  ├── reference_frame: text     — coordinate system description
  └── timestamps/rate           — inherited from TimeSeries

PoseEstimation (NWBDataInterface)
  ├── PoseEstimationSeries[*]   — one per keypoint
  ├── skeleton → Skeleton       — link to skeleton
  ├── source_software: text
  ├── dimensions: uint16[C,2]  — video dimensions
  └── original_videos: text[]

Skeletons (NWBDataInterface)
  └── Skeleton[*]               — container for skeletons
```

**Key design decisions:**
1. `PoseEstimationSeries` extends `TimeSeries` — gets timestamps, rate, data, unit for free
2. `PoseEstimation` is a container (NWBDataInterface) holding multiple series
3. `Skeleton` is separate so multiple PoseEstimation objects can share it
4. `Skeletons` container allows file-level skeleton registry
5. Links (not containment) between PoseEstimation and Skeleton

## Pattern 3: Device Hierarchy + DynamicTable (ndx-fiber-photometry)

Extension with specialized devices, a configuration table, and response series.

**Structure:**
```
ExcitationSource (Device)       — LED/laser
OpticalFiber (Device)           — fiber with insertion coordinates
Photodetector (Device)          — detector
BandOpticalFilter (Device)      — emission/excitation filter
DichroicMirror (Device)         — dichroic mirror
Indicator (NWBContainer)        — fluorescent indicator (GCaMP, dLight, etc.)

FiberPhotometryTable (DynamicTable)
  ├── location: VectorData[text]
  ├── excitation_wavelength_in_nm: VectorData[float]
  ├── emission_wavelength_in_nm: VectorData[float]
  ├── indicator: VectorData[Indicator]           — references
  ├── optical_fiber: VectorData[OpticalFiber]    — references
  ├── excitation_source: VectorData[ExcitationSource]
  ├── photodetector: VectorData[Photodetector]
  └── (optional filter columns)

FiberPhotometryResponseSeries (TimeSeries)
  ├── data: float[T] or float[T,C]
  └── fiber_photometry_table_region: DynamicTableRegion → FiberPhotometryTable

FiberPhotometry (LabMetaData)   — top-level wrapper
  ├── fiber_photometry_table → FiberPhotometryTable
  └── fiber_photometry_indicators → Indicators container
```

**Key design decisions:**
1. Each hardware component is a `Device` subtype — goes in `nwbfile.devices`
2. `DynamicTable` links devices, indicators, and brain regions per channel
3. `DynamicTableRegion` in response series points to specific table rows
4. `LabMetaData` wraps everything for clean attachment to NWBFile
5. Indicator is NWBContainer (not Device) because it's a biological, not hardware, component

## Pattern 4: Simple Container with MultiContainerInterface

For types that simply hold a collection of child objects.

```python
# Spec
container_spec = NWBGroupSpec(
    neurodata_type_def="EventCollection",
    neurodata_type_inc="NWBDataInterface",
    doc="Collection of custom event series",
    groups=[
        NWBGroupSpec(
            neurodata_type_inc="CustomEventSeries",
            doc="Event series in this collection",
            quantity="*",
        ),
    ],
)
```

```python
# Python API using MultiContainerInterface
from pynwb.core import MultiContainerInterface

@register_class("EventCollection", "ndx-events")
class EventCollection(MultiContainerInterface):
    __clsconf__ = [
        {
            "attr": "event_series",
            "type": CustomEventSeries,
            "add": "add_event_series",
            "get": "get_event_series",
            "create": "create_event_series",
        },
    ]
```

## Pattern 5: Extending TimeSeries with Custom Fields

When your time-varying data needs extra metadata beyond what TimeSeries provides.

```python
# Spec
my_series = NWBGroupSpec(
    neurodata_type_def="AnnotatedTimeSeries",
    neurodata_type_inc="TimeSeries",
    doc="TimeSeries with per-sample annotations",
    datasets=[
        NWBDatasetSpec(
            name="labels",
            doc="Label for each time point",
            dtype="text",
            shape=(None,),
            dims=("num_times",),
            quantity="?",
        ),
        NWBDatasetSpec(
            name="confidence",
            doc="Confidence score per time point",
            dtype="float32",
            shape=(None,),
            dims=("num_times",),
            quantity="?",
        ),
    ],
    attributes=[
        NWBAttributeSpec(
            name="source_software",
            dtype="text",
            doc="Software that generated this data",
            required=False,
        ),
    ],
)
```

**What you inherit from TimeSeries:** `data`, `timestamps`, `rate`, `starting_time`,
`unit`, `description`, `conversion`, `resolution`, `comments`. Don't redefine these.

## Pattern 6: DynamicTable with Custom Columns

Pre-defining columns in the spec ensures they appear in every instance.

```python
from pynwb.spec import NWBGroupSpec, NWBDatasetSpec

units_table = NWBGroupSpec(
    neurodata_type_def="SortingResults",
    neurodata_type_inc="DynamicTable",
    doc="Extended units table with quality metrics",
    datasets=[
        NWBDatasetSpec(
            name="snr",
            neurodata_type_inc="VectorData",
            doc="Signal-to-noise ratio for each unit",
            dtype="float64",
        ),
        NWBDatasetSpec(
            name="isolation_distance",
            neurodata_type_inc="VectorData",
            doc="Isolation distance metric",
            dtype="float64",
            quantity="?",
        ),
        NWBDatasetSpec(
            name="isi_violation_rate",
            neurodata_type_inc="VectorData",
            doc="ISI violation rate",
            dtype="float64",
            quantity="?",
        ),
    ],
)
```

**Remember:** Include both `DynamicTable` and `VectorData` from `hdmf-common` namespace.

## Pattern 7: Linking to NWBFile Children

When your extension needs to reference objects that live elsewhere in the NWB file.

```python
analysis_spec = NWBGroupSpec(
    neurodata_type_def="TrialAlignedResponse",
    neurodata_type_inc="NWBDataInterface",
    doc="Trial-aligned neural responses",
    datasets=[
        NWBDatasetSpec(
            name="aligned_data",
            doc="Neural responses aligned to trial events",
            dtype="float64",
            shape=(None, None, None),
            dims=("num_trials", "num_timepoints", "num_units"),
        ),
    ],
    links=[
        NWBLinkSpec(
            name="source_timeseries",
            target_type="TimeSeries",
            doc="The source time series these responses were extracted from",
        ),
        NWBLinkSpec(
            name="trials",
            target_type="TimeIntervals",
            doc="The trials table used for alignment",
        ),
    ],
)
```

## Anti-Patterns (Things to Avoid)

### Don't duplicate existing NWB fields

```python
# BAD: Redefining fields that TimeSeries already provides
NWBGroupSpec(
    neurodata_type_def="MyTimeSeries",
    neurodata_type_inc="TimeSeries",
    datasets=[
        NWBDatasetSpec(name="data", ...),        # Already in TimeSeries!
        NWBDatasetSpec(name="timestamps", ...),   # Already in TimeSeries!
    ],
)

# GOOD: Only add new fields
NWBGroupSpec(
    neurodata_type_def="MyTimeSeries",
    neurodata_type_inc="TimeSeries",
    datasets=[
        NWBDatasetSpec(name="quality_scores", ...),  # New field
    ],
)
```

### Don't use NWBDataInterface when LabMetaData is more appropriate

```python
# BAD: Metadata stored in a processing module
# nwbfile.processing["metadata"].add(my_metadata)

# GOOD: Metadata stored as LabMetaData
# nwbfile.add_lab_meta_data(my_metadata)
```

### Don't create monolithic types

```python
# BAD: One huge type with everything
NWBGroupSpec(
    neurodata_type_def="EverythingContainer",
    datasets=[...fifty datasets...],
    attributes=[...twenty attributes...],
)

# GOOD: Decompose into focused types with clear relationships
# FiberPhotometryTable (channels), Device subtypes (hardware),
# FiberPhotometryResponseSeries (data), FiberPhotometry (wrapper)
```

### Don't use attributes for large data

```python
# BAD: Large array as an attribute
NWBAttributeSpec(name="waveforms", dtype="float64", shape=(None, None), ...)

# GOOD: Large array as a dataset
NWBDatasetSpec(name="waveforms", dtype="float64", shape=(None, None), ...)
```

Attributes are stored inline in HDF5 group metadata. Datasets are stored separately
and can be chunked, compressed, and lazily loaded. Use attributes only for small
scalar or short-array metadata.
