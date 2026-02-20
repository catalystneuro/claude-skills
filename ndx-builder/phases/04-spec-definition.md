## Phase 4: Spec Definition

**Goal**: Write `create_extension_spec.py` to generate the extension's YAML schema.

**Entry**: You have a scaffolded project from Phase 3 and a finalized design from Phase 2.

**Exit criteria**:
- `create_extension_spec.py` generates valid YAML spec files
- YAML files pass validation
- The spec matches the design from Phase 2

### Step 1: Write create_extension_spec.py

Edit `src/spec/create_extension_spec.py`. This file defines the extension's schema
using the NWB spec API (see `knowledge/spec-api-reference.md`).

**Template:**

```python
# src/spec/create_extension_spec.py
from pynwb.spec import (
    NWBNamespaceBuilder,
    NWBGroupSpec,
    NWBDatasetSpec,
    NWBAttributeSpec,
    NWBLinkSpec,
    export_spec,
)


def main():
    ns_builder = NWBNamespaceBuilder(
        name="ndx-<name>",
        doc="<Description of the extension>",
        version="0.1.0",
        author="<Author>",
        contact="<email>",
    )

    # Include parent types from NWB core
    ns_builder.include_type("NWBDataInterface", namespace="core")
    # Add more includes as needed:
    # ns_builder.include_type("TimeSeries", namespace="core")
    # ns_builder.include_type("LabMetaData", namespace="core")
    # ns_builder.include_type("Device", namespace="core")
    # ns_builder.include_type("DynamicTable", namespace="hdmf-common")
    # ns_builder.include_type("VectorData", namespace="hdmf-common")

    # Define types (from Phase 2 design)
    my_type = NWBGroupSpec(
        neurodata_type_def="MyType",
        neurodata_type_inc="NWBDataInterface",
        doc="Description of this type",
        # attributes, datasets, groups, links...
    )

    # Add specs to the extension file
    ns_builder.add_spec("ndx-<name>.extensions.yaml", my_type)

    # Export
    export_spec(ns_builder, [my_type])


if __name__ == "__main__":
    main()
```

### Step 2: Translate the Design

Convert each type from the Phase 2 design into spec API calls. Refer to
`knowledge/spec-api-reference.md` for the full API.

**For each type, translate:**
- Attributes → `NWBAttributeSpec` list
- Datasets → `NWBDatasetSpec` list
- Sub-groups → Nested `NWBGroupSpec` list
- Links → `NWBLinkSpec` list
- Containment of typed children → `NWBGroupSpec` with `neurodata_type_inc` and `quantity`

**Common patterns:**

```python
# LabMetaData with attributes
metadata_spec = NWBGroupSpec(
    neurodata_type_def="MyMetaData",
    neurodata_type_inc="LabMetaData",
    name="my_metadata",               # Fixed name for LabMetaData
    doc="Lab-specific metadata",
    attributes=[
        NWBAttributeSpec(name="field1", dtype="text", doc="..."),
        NWBAttributeSpec(name="field2", dtype="float64", doc="...", required=False),
    ],
)

# TimeSeries with extra fields
series_spec = NWBGroupSpec(
    neurodata_type_def="MyTimeSeries",
    neurodata_type_inc="TimeSeries",
    doc="Custom time series",
    datasets=[
        NWBDatasetSpec(
            name="quality",
            dtype="float32",
            shape=(None,),
            dims=("num_times",),
            doc="Quality score per time point",
            quantity="?",
        ),
    ],
)

# Container holding typed children
container_spec = NWBGroupSpec(
    neurodata_type_def="MyContainer",
    neurodata_type_inc="NWBDataInterface",
    doc="Container for multiple items",
    groups=[
        NWBGroupSpec(
            neurodata_type_inc="MyTimeSeries",
            doc="Time series in this container",
            quantity="*",
        ),
    ],
)

# DynamicTable with custom columns
table_spec = NWBGroupSpec(
    neurodata_type_def="MyTable",
    neurodata_type_inc="DynamicTable",
    doc="Custom table",
    datasets=[
        NWBDatasetSpec(
            name="location",
            neurodata_type_inc="VectorData",
            dtype="text",
            doc="Brain region",
        ),
        NWBDatasetSpec(
            name="threshold",
            neurodata_type_inc="VectorData",
            dtype="float64",
            doc="Detection threshold",
            quantity="?",
        ),
    ],
)

# Device subtype
device_spec = NWBGroupSpec(
    neurodata_type_def="MyDevice",
    neurodata_type_inc="Device",
    doc="Custom device",
    attributes=[
        NWBAttributeSpec(name="serial_number", dtype="text", doc="Serial number"),
    ],
)
```

### Step 3: Include All Required Parent Types

Every type referenced by `neurodata_type_inc` must be included. Common ones:

```python
# NWB core types
ns_builder.include_type("NWBDataInterface", namespace="core")
ns_builder.include_type("NWBContainer", namespace="core")
ns_builder.include_type("NWBData", namespace="core")
ns_builder.include_type("TimeSeries", namespace="core")
ns_builder.include_type("LabMetaData", namespace="core")
ns_builder.include_type("Device", namespace="core")

# HDMF types (for DynamicTable and related)
ns_builder.include_type("DynamicTable", namespace="hdmf-common")
ns_builder.include_type("DynamicTableRegion", namespace="hdmf-common")
ns_builder.include_type("VectorData", namespace="hdmf-common")
ns_builder.include_type("VectorIndex", namespace="hdmf-common")
```

**Also include any types used as link targets** even if you're not extending them:

```python
# If you have a link to Device, include Device
ns_builder.include_type("Device", namespace="core")
```

### Step 4: Run the Script

```bash
cd ndx-<name>
python3 src/spec/create_extension_spec.py
```

This generates:
- `spec/ndx-<name>.namespace.yaml`
- `spec/ndx-<name>.extensions.yaml`

### Step 5: Validate the Generated YAML

Inspect the generated files:

```bash
cat spec/ndx-<name>.extensions.yaml
cat spec/ndx-<name>.namespace.yaml
```

Validate by attempting to load the namespace:

```python
python3 -c "
from pynwb import load_namespaces
load_namespaces('spec/ndx-<name>.namespace.yaml')
print('Namespace loaded successfully')
"
```

### Step 6: Verify Package Import

After generating the YAML, reinstall the package and verify it imports:

```bash
pip install -e .
python3 -c "import ndx_<name_underscored>; print('Import OK')"
```

### Common Issues

**"Type X not found" error**: You forgot to include the parent type. Add the
appropriate `ns_builder.include_type()` call.

**YAML validation error**: Check that all spec fields have valid values. Common mistakes:
- Missing `doc` on a spec
- Invalid dtype string
- Shape/dims mismatch (must have same number of dimensions)
- Using `name` and `default_name` together (they're mutually exclusive)

**Export error**: Make sure all specs are passed to both `ns_builder.add_spec()` and
`export_spec()`.

**Spec not found after install**: Check that `pyproject.toml` includes `spec/*.yaml`
in the package data. The hatchling build config should include:
```toml
[tool.hatch.build]
include = ["*.yaml"]
```
