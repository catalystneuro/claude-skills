# NWB Spec API Reference

Reference for the NWB specification language classes used to define extension schemas.
These classes live in `pynwb.spec` (which re-exports from `hdmf.spec`).

## NWBNamespaceBuilder

Entry point for creating an extension namespace. Every extension has exactly one namespace.

```python
from pynwb.spec import NWBNamespaceBuilder

ns_builder = NWBNamespaceBuilder(
    name="ndx-my-extension",               # Extension name (must start with "ndx-")
    doc="Description of what this extension provides",
    version="0.1.0",                        # Semantic version
    author="Your Name",
    contact="your.email@example.com",
    full_name="ndx-my-extension",           # Optional, defaults to name
    catalog="https://github.com/nwb-extensions/",  # Optional
)
```

### Including parent types

Before defining types that extend core NWB or HDMF types, you must include them:

```python
# Include from NWB core namespace
ns_builder.include_type("NWBDataInterface", namespace="core")
ns_builder.include_type("TimeSeries", namespace="core")
ns_builder.include_type("LabMetaData", namespace="core")
ns_builder.include_type("Device", namespace="core")
ns_builder.include_type("NWBFile", namespace="core")
ns_builder.include_type("NWBContainer", namespace="core")

# Include from hdmf-common namespace (for DynamicTable, etc.)
ns_builder.include_type("DynamicTable", namespace="hdmf-common")
ns_builder.include_type("DynamicTableRegion", namespace="hdmf-common")
ns_builder.include_type("VectorData", namespace="hdmf-common")
ns_builder.include_type("VectorIndex", namespace="hdmf-common")
```

### Adding specs and exporting

```python
# Add each spec to a source file (one YAML file per logical group)
ns_builder.add_spec("ndx-my-extension.extensions.yaml", my_type_spec)
ns_builder.add_spec("ndx-my-extension.extensions.yaml", another_type_spec)

# Export to YAML files
ns_builder.export("ndx-my-extension.namespace.yaml", outdir="spec")
```

The export generates two files:
- `ndx-my-extension.namespace.yaml` — namespace definition with includes
- `ndx-my-extension.extensions.yaml` — type definitions

## NWBGroupSpec

Defines a new neurodata type (group in HDF5). This is the most commonly used spec class.

```python
from pynwb.spec import NWBGroupSpec, NWBAttributeSpec, NWBDatasetSpec, NWBLinkSpec

my_type = NWBGroupSpec(
    neurodata_type_def="MyType",            # Name of this new type
    neurodata_type_inc="NWBDataInterface",  # Parent type to extend
    doc="Description of this type",
    name=None,                              # Fixed name (mutually exclusive with default_name)
    default_name=None,                      # Default name (user can override)
    quantity=1,                             # How many instances allowed (see Quantity below)
    attributes=[...],                       # List of NWBAttributeSpec
    datasets=[...],                         # List of NWBDatasetSpec
    groups=[...],                           # List of NWBGroupSpec (nested)
    links=[...],                            # List of NWBLinkSpec
)
```

### Key parameters

- **`neurodata_type_def`**: The name you're defining. Required for top-level types.
- **`neurodata_type_inc`**: The parent type. Inherits all its fields.
- **`name`**: If set, all instances must have this exact name. Use for singleton containers.
- **`default_name`**: Suggested name that can be overridden. Use for types that may have multiple instances.
- **`quantity`**: How many of this group are allowed in its parent (see Quantity section).

### Nested anonymous groups

Groups inside a type definition don't need `neurodata_type_def`:

```python
my_type = NWBGroupSpec(
    neurodata_type_def="MyContainer",
    neurodata_type_inc="NWBDataInterface",
    doc="A container with nested structure",
    groups=[
        NWBGroupSpec(
            name="configuration",
            doc="Configuration parameters",
            attributes=[
                NWBAttributeSpec(name="param1", dtype="text", doc="A parameter"),
            ],
        ),
    ],
)
```

### Typed sub-groups (containment)

To allow a group to contain instances of a specific type:

```python
container = NWBGroupSpec(
    neurodata_type_def="MyContainer",
    neurodata_type_inc="NWBDataInterface",
    doc="Contains multiple MyItem objects",
    groups=[
        NWBGroupSpec(
            neurodata_type_inc="MyItem",
            doc="Items in this container",
            quantity="*",  # Zero or more
        ),
    ],
)
```

## NWBDatasetSpec

Defines a dataset (array or scalar data). Can be used standalone or nested inside a group.

```python
from pynwb.spec import NWBDatasetSpec

# Simple dataset
data_spec = NWBDatasetSpec(
    name="signal",
    doc="The recorded signal",
    dtype="float64",
    shape=[(None,), (None, None)],     # 1D or 2D, first dim unlimited
    dims=[("num_times",), ("num_times", "num_channels")],
    quantity=1,
)

# Dataset as a neurodata type
typed_dataset = NWBDatasetSpec(
    neurodata_type_def="MyData",
    neurodata_type_inc="NWBData",
    doc="A typed dataset",
    dtype="float32",
    shape=(None, 3),
    dims=("num_points", "xyz"),
)
```

### dtype options

**Basic types:**
- `"float32"`, `"float64"` — floating point
- `"int8"`, `"int16"`, `"int32"`, `"int64"` — signed integers
- `"uint8"`, `"uint16"`, `"uint32"`, `"uint64"` — unsigned integers
- `"text"` — variable-length string
- `"bool"` — boolean
- `"isodatetime"` — ISO 8601 datetime string

**Compound types** (for structured datasets like tables):

```python
from pynwb.spec import NWBDtypeSpec

compound_dataset = NWBDatasetSpec(
    name="events",
    doc="Event records",
    dtype=[
        NWBDtypeSpec(name="timestamp", dtype="float64", doc="Event time in seconds"),
        NWBDtypeSpec(name="label", dtype="text", doc="Event label"),
        NWBDtypeSpec(name="value", dtype="float32", doc="Event value"),
    ],
)
```

**Reference types** (for linking to other objects):

```python
ref_dataset = NWBDatasetSpec(
    name="source_timeseries",
    doc="Reference to source time series",
    dtype=NWBRefSpec(target_type="TimeSeries", reftype="object"),
)
```

### shape and dims

`shape` and `dims` describe the expected dimensions:

```python
# Fixed shape
shape=(3,), dims=("xyz",)

# Variable length 1D
shape=(None,), dims=("num_samples",)

# 2D with variable first dim
shape=(None, 3), dims=("num_points", "xyz")

# Multiple allowed shapes (1D or 2D)
shape=[(None,), (None, None)]
dims=[("num_times",), ("num_times", "num_channels")]
```

`None` in a shape dimension means the size is not fixed.

## NWBAttributeSpec

Defines an attribute (lightweight metadata attached to a group or dataset).

```python
from pynwb.spec import NWBAttributeSpec

# Required attribute
attr = NWBAttributeSpec(
    name="species",
    dtype="text",
    doc="The species of the subject",
)

# Optional attribute with default
attr_opt = NWBAttributeSpec(
    name="conversion",
    dtype="float64",
    doc="Conversion factor to SI units",
    required=False,
    default_value=1.0,
)

# Array attribute
attr_array = NWBAttributeSpec(
    name="labels",
    dtype="text",
    doc="Labels for each column",
    dims=("num_columns",),
    shape=(None,),
)
```

### Parameters

- **`name`**: Attribute name (required)
- **`dtype`**: Data type (same options as NWBDatasetSpec)
- **`doc`**: Description (required)
- **`required`**: Whether this attribute is required (default: `True`)
- **`default_value`**: Default value when not provided
- **`dims`** / **`shape`**: For array-valued attributes
- **`value`**: Fixed constant value (rarely used)

## NWBLinkSpec

Defines a link (reference) to another object. Use instead of containment when the
target object lives elsewhere in the file.

```python
from pynwb.spec import NWBLinkSpec

link = NWBLinkSpec(
    name="device",
    target_type="Device",
    doc="The device used for this recording",
    quantity=1,
)

# Optional link
optional_link = NWBLinkSpec(
    name="reference_images",
    target_type="Images",
    doc="Reference images for this segmentation",
    quantity="?",
)
```

## NWBDtypeSpec

Used inside compound dtype definitions:

```python
from pynwb.spec import NWBDtypeSpec

field = NWBDtypeSpec(
    name="field_name",
    dtype="float64",
    doc="Description of this field",
)
```

## NWBRefSpec

Used for reference/link dtypes in datasets:

```python
from pynwb.spec import NWBRefSpec

# Object reference (points to any NWB object)
ref = NWBRefSpec(target_type="TimeSeries", reftype="object")

# Region reference (points to a subset of a dataset)
region_ref = NWBRefSpec(target_type="DynamicTable", reftype="region")
```

## Quantity Specifiers

The `quantity` parameter controls how many instances of a field are allowed:

| Value | Meaning | Use Case |
|-------|---------|----------|
| `1` | Exactly one, required | Default. Most fields. |
| `'?'` | Zero or one, optional | Optional fields |
| `'*'` | Zero or more | Collections of items |
| `'+'` | One or more | Required collections |
| integer (e.g., `3`) | Exactly that many | Fixed-size collections |

```python
# Required field (default)
NWBDatasetSpec(name="data", doc="...", quantity=1)

# Optional field
NWBDatasetSpec(name="labels", doc="...", quantity="?")

# Zero or more sub-groups
NWBGroupSpec(neurodata_type_inc="TimeSeries", doc="...", quantity="*")

# One or more required
NWBGroupSpec(neurodata_type_inc="Device", doc="...", quantity="+")
```

## Complete Example: Defining a Simple Extension

```python
from pynwb.spec import (
    NWBNamespaceBuilder,
    NWBGroupSpec,
    NWBDatasetSpec,
    NWBAttributeSpec,
    NWBLinkSpec,
)

ns_builder = NWBNamespaceBuilder(
    name="ndx-surgery",
    doc="Extension for storing surgical procedure metadata",
    version="0.1.0",
    author="Lab Name",
    contact="lab@example.com",
)

ns_builder.include_type("LabMetaData", namespace="core")
ns_builder.include_type("Device", namespace="core")

surgery_spec = NWBGroupSpec(
    neurodata_type_def="Surgery",
    neurodata_type_inc="LabMetaData",
    name="surgery",
    doc="Metadata about surgical procedures performed on the subject",
    attributes=[
        NWBAttributeSpec(
            name="surgery_date",
            dtype="isodatetime",
            doc="Date and time of the surgery",
        ),
        NWBAttributeSpec(
            name="protocol",
            dtype="text",
            doc="IACUC protocol number",
            required=False,
        ),
    ],
    datasets=[
        NWBDatasetSpec(
            name="procedures",
            doc="Description of each procedure performed",
            dtype="text",
            shape=(None,),
            dims=("num_procedures",),
        ),
    ],
    links=[
        NWBLinkSpec(
            name="implant",
            target_type="Device",
            doc="Device implanted during surgery",
            quantity="?",
        ),
    ],
)

ns_builder.add_spec("ndx-surgery.extensions.yaml", surgery_spec)
ns_builder.export("ndx-surgery.namespace.yaml", outdir="spec")
```
