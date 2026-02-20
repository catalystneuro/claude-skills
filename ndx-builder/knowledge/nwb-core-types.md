# NWB Core Types Reference

Guide to common NWB core types that extensions typically extend. Choosing the right
base type is critical for interoperability.

## Type Selection Decision Tree

```
What kind of data are you storing?
├── Tabular data with rows and named columns?
│   └── DynamicTable
├── Lab-specific metadata that goes on NWBFile?
│   └── LabMetaData
├── A physical device?
│   └── Device
├── Time-varying data (signals, traces)?
│   ├── Has timestamps/rate + data array?
│   │   ├── Neural electrical signal? → ElectricalSeries
│   │   ├── Optical imaging signal? → RoiResponseSeries / OpticalSeries
│   │   ├── Behavioral position? → SpatialSeries (inside Position)
│   │   └── Other time series? → TimeSeries
│   └── No → NWBDataInterface
├── A container for grouping related objects?
│   └── NWBDataInterface (or NWBContainer)
├── A single dataset (not a group)?
│   └── NWBData
└── Something else?
    └── NWBDataInterface (safe default)
```

## NWBDataInterface

**The most common base type for extensions.** A group that holds data and can be
placed in processing modules.

```python
# Spec
NWBGroupSpec(
    neurodata_type_def="MyInterface",
    neurodata_type_inc="NWBDataInterface",
    doc="...",
)
```

| Property | Value |
|----------|-------|
| Where it lives | `nwbfile.processing["module_name"]` |
| Can contain | Datasets, attributes, sub-groups, links |
| Key inherited fields | `name` |
| When to use | Generic container for processed data, results, or non-time-series data |

**Example use cases:**
- Pose estimation container (ndx-pose `PoseEstimation`)
- Fiber photometry response (ndx-fiber-photometry)
- Custom analysis results
- Grouping related data streams

## TimeSeries

**For any data with a time dimension.** The fundamental time-varying data type in NWB.

```python
NWBGroupSpec(
    neurodata_type_def="MyTimeSeries",
    neurodata_type_inc="TimeSeries",
    doc="...",
)
```

| Property | Value |
|----------|-------|
| Where it lives | `nwbfile.acquisition`, `nwbfile.stimulus`, or processing modules |
| Key inherited fields | `data`, `timestamps` or `rate`+`starting_time`, `unit`, `description`, `conversion`, `resolution`, `comments` |
| When to use | Data sampled over time that doesn't fit a more specific subtype |

**Inherited behavior:**
- Timestamps stored as seconds relative to `session_start_time`
- `data` shape: first dimension is always time
- `conversion` factor to convert stored values to SI units
- `resolution` for smallest meaningful difference

**Don't use bare TimeSeries** when a more specific subtype exists:
- Neural electrical data → `ElectricalSeries`
- Optical imaging → `TwoPhotonSeries` / `OnePhotonSeries`
- Position → `SpatialSeries` (inside `Position`)
- Behavioral events → consider `TimeIntervals` instead

## ElectricalSeries

**For extracellular electrophysiology voltage traces.** Extends TimeSeries.

| Property | Value |
|----------|-------|
| Where it lives | `nwbfile.acquisition` (raw) or `processing["ecephys"]` (filtered) |
| Key additional fields | `electrodes` (DynamicTableRegion linking to electrodes table) |
| When to use | Raw or filtered neural voltage data |

**Extension example:** A new type of electrical recording with custom metadata:
```python
NWBGroupSpec(
    neurodata_type_def="MyElectricalSeries",
    neurodata_type_inc="ElectricalSeries",
    doc="Electrical series with custom amplifier metadata",
    attributes=[
        NWBAttributeSpec(name="amplifier_gain", dtype="float64", doc="Amplifier gain"),
    ],
)
```

## LabMetaData

**For lab-specific metadata attached to an NWB file.** This is the recommended way to
add custom metadata that doesn't fit elsewhere.

```python
NWBGroupSpec(
    neurodata_type_def="MyLabMetaData",
    neurodata_type_inc="LabMetaData",
    name="my_lab_metadata",    # Fixed name (recommended for LabMetaData)
    doc="...",
)
```

| Property | Value |
|----------|-------|
| Where it lives | `nwbfile.lab_meta_data` (via `nwbfile.add_lab_meta_data()`) |
| Key inherited fields | None beyond NWBContainer |
| When to use | Custom metadata that applies to the whole session/file |

**Common patterns:**
- Surgery metadata (date, procedures, implants)
- Training history or behavioral task parameters
- Fiber photometry setup (ndx-fiber-photometry wraps everything in LabMetaData)
- Custom experimental protocol details

**Why LabMetaData over NWBDataInterface?**
- LabMetaData is specifically for file-level metadata
- It goes in `nwbfile.lab_meta_data`, a dedicated namespace
- NWBDataInterface goes in processing modules, which is for data

## DynamicTable

**For tabular data with named, typed columns.** Extensible — users can add columns
at runtime.

```python
# From hdmf-common namespace
NWBGroupSpec(
    neurodata_type_def="MyTable",
    neurodata_type_inc="DynamicTable",
    doc="...",
    datasets=[
        NWBDatasetSpec(
            name="column_a",
            neurodata_type_inc="VectorData",
            doc="Description of column A",
            dtype="float64",
        ),
        NWBDatasetSpec(
            name="column_b",
            neurodata_type_inc="VectorData",
            doc="Description of column B",
            dtype="text",
        ),
    ],
)
```

| Property | Value |
|----------|-------|
| Where it lives | Anywhere (processing modules, inside other types) |
| Key inherited fields | `id` (auto-incrementing), `colnames`, `description` |
| When to use | Any structured tabular data with rows |

**Important notes:**
- Include `DynamicTable` and `VectorData` from `hdmf-common` namespace
- Each column is a `VectorData` dataset
- For ragged arrays (variable-length per row), pair with `VectorIndex`
- Use `DynamicTableRegion` to reference specific rows from other objects

**Example use cases:**
- FiberPhotometryTable (channels × configuration)
- Custom trial types with extension-specific columns
- Electrode metadata beyond core columns
- Any data that naturally forms a table

## Device

**For physical devices used in the experiment.**

```python
NWBGroupSpec(
    neurodata_type_def="MyDevice",
    neurodata_type_inc="Device",
    doc="...",
    attributes=[
        NWBAttributeSpec(name="serial_number", dtype="text", doc="Device serial number"),
    ],
)
```

| Property | Value |
|----------|-------|
| Where it lives | `nwbfile.devices` (via `nwbfile.add_device()` or `nwbfile.create_device()`) |
| Key inherited fields | `name`, `description`, `manufacturer` |
| When to use | Recording hardware, stimulation devices, implants |

**Example use cases:**
- Optical fiber (ndx-fiber-photometry)
- Excitation source / photodetector
- Custom recording hardware with specific parameters

## NWBContainer

**Base class for any group in NWB.** More generic than NWBDataInterface.

| Property | Value |
|----------|-------|
| Key inherited fields | `name` |
| When to use | Internal sub-groups that aren't top-level data interfaces |

**Prefer NWBDataInterface** for top-level types. Use NWBContainer only for:
- Internal helper groups within your type hierarchy
- Types that need to be nested inside other types but aren't "data interfaces"

## NWBData

**Base class for typed datasets (not groups).**

```python
NWBDatasetSpec(
    neurodata_type_def="MyData",
    neurodata_type_inc="NWBData",
    doc="...",
    dtype="float64",
    shape=(None, 3),
    dims=("num_points", "xyz"),
)
```

| Property | Value |
|----------|-------|
| When to use | Standalone datasets that need their own neurodata type |
| Key inherited fields | `data` |

**Rarely needed.** Most data goes inside groups as unnamed datasets. Use NWBData
only when you need a standalone typed dataset.

## SpatialSeries

**For position data (x, y, z coordinates).**

| Property | Value |
|----------|-------|
| Parent | TimeSeries |
| Where it lives | Inside `Position`, `EyeTracking`, `CompassDirection` containers |
| Key additional fields | `reference_frame` |
| Constraints | Data must have 1, 2, or 3 columns |

## TimeIntervals

**For tabular data with start/stop times.** Used for trials, epochs, and custom intervals.

| Property | Value |
|----------|-------|
| Parent | DynamicTable |
| Where it lives | `nwbfile.intervals` (via `nwbfile.add_time_intervals()`) |
| Key additional fields | `start_time`, `stop_time` (required columns) |
| When to use | Trial tables, epoch tables, any interval-based data |

## Summary: Which Type to Extend

| Your Data | Extend This | Namespace |
|-----------|-------------|-----------|
| Generic container with sub-data | `NWBDataInterface` | `core` |
| Time-varying signal | `TimeSeries` | `core` |
| Neural voltage | `ElectricalSeries` | `core` |
| Session-level metadata | `LabMetaData` | `core` |
| Tabular data | `DynamicTable` | `hdmf-common` |
| Physical hardware | `Device` | `core` |
| Internal sub-group | `NWBContainer` | `core` |
| Typed standalone dataset | `NWBData` | `core` |
| Position tracking | `SpatialSeries` (extend container, not series) | `core` |
| Trial/epoch data | `TimeIntervals` | `core` |
