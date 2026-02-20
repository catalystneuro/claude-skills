## Phase 5: Python API Implementation

**Goal**: Create Python classes that provide a user-friendly API for the extension types.

**Entry**: You have valid YAML spec files from Phase 4.

**Exit criteria**:
- All types have Python classes (auto-generated or custom)
- Classes can be instantiated and used
- The package imports cleanly

### Step 1: Decide Auto-Generated vs Custom

For each type, decide whether to use auto-generated or custom classes.
See `knowledge/custom-api-reference.md` for full API details.

| Type Complexity | Approach |
|-----------------|----------|
| Simple type with only attributes and basic datasets | `get_class()` auto-generation |
| Type needing init validation, computed properties, or convenience methods | Custom class with `@register_class` |
| Container holding typed children with add/get/create | Custom `MultiContainerInterface` |
| DynamicTable with simple scalar columns only | Custom class with `__columns__` |
| DynamicTable with VectorData columns, non-column datasets, attributes, or links | Full custom class (see pattern below) |
| Type needing non-trivial HDF5 mapping | Custom class + `ObjectMapper` |

**When in doubt, start with `get_class()`.** You can always add a custom class later.
**Exception**: DynamicTable subclasses with spec-defined columns always need custom classes.

### Step 2: Update `__init__.py`

Edit `src/pynwb/ndx_<name>/__init__.py`. The ndx-template generates this using
`importlib.resources` (preferred over `os.path`):

```python
from importlib.resources import files
from pynwb import load_namespaces

# Get path to the namespace YAML (installed package location)
__location_of_this_file = files(__name__)
__spec_path = __location_of_this_file / "spec" / "ndx-<name>.namespace.yaml"

# Fallback for editable install (pip install -e .)
if not __spec_path.exists():
    __spec_path = __location_of_this_file.parent.parent.parent / "spec" / "ndx-<name>.namespace.yaml"

# Load namespace FIRST — must happen before any get_class or register_class
load_namespaces(str(__spec_path))

# Auto-generated classes (if any)
# from pynwb import get_class
# MySimpleType = get_class("MySimpleType", "ndx-<name>")

# Custom classes (import AFTER load_namespaces)
from .my_custom_type import MyCustomType  # noqa: E402, F401

__all__ = ["MyCustomType"]

# Clean up module namespace
del load_namespaces, files, __location_of_this_file, __spec_path
```

**Critical order**: `load_namespaces()` MUST execute before any `get_class()` call
or `@register_class` decorator. The decorator runs at import time, so custom class
modules must be imported after `load_namespaces()`.

### Step 3: Write Custom Classes (if needed)

Create a new `.py` file in `src/pynwb/ndx_<name>/` for each custom class.

**Simple custom class:**

```python
# src/pynwb/ndx_<name>/my_type.py
from pynwb import register_class, NWBDataInterface
from pynwb.device import Device
from hdmf.utils import docval, popargs

NS = "ndx-<name>"


@register_class("MyType", NS)
class MyType(NWBDataInterface):
    """A custom neurodata type."""

    __nwbfields__ = (
        "signal",
        "sampling_rate",
        {"name": "device", "required_name": "device"},
    )

    @docval(
        {"name": "name", "type": str, "doc": "Name of this object"},
        {"name": "signal", "type": "array_data", "doc": "The recorded signal"},
        {"name": "sampling_rate", "type": float, "doc": "Sampling rate in Hz"},
        {"name": "description", "type": str, "doc": "Description",
         "default": "no description"},
        {"name": "device", "type": Device, "doc": "Recording device",
         "default": None},
    )
    def __init__(self, **kwargs):
        signal, sampling_rate, device = popargs(
            "signal", "sampling_rate", "device", kwargs
        )
        super().__init__(**kwargs)
        self.signal = signal
        self.sampling_rate = sampling_rate
        self.device = device
```

**LabMetaData class:**

```python
from pynwb import register_class
from pynwb.file import LabMetaData
from hdmf.utils import docval, popargs

NS = "ndx-<name>"


@register_class("MyMetaData", NS)
class MyMetaData(LabMetaData):
    """Lab-specific metadata."""

    __nwbfields__ = ("field1", "field2")

    @docval(
        {"name": "name", "type": str, "doc": "Name", "default": "my_metadata"},
        {"name": "field1", "type": str, "doc": "First field"},
        {"name": "field2", "type": float, "doc": "Second field", "default": None},
    )
    def __init__(self, **kwargs):
        field1, field2 = popargs("field1", "field2", kwargs)
        super().__init__(**kwargs)
        self.field1 = field1
        self.field2 = field2
```

**MultiContainerInterface:**

```python
from pynwb import register_class
from pynwb.core import MultiContainerInterface
from hdmf.utils import docval, popargs

from .my_type import MyType

NS = "ndx-<name>"


@register_class("MyContainer", NS)
class MyContainer(MultiContainerInterface):
    """Container for MyType objects."""

    __clsconf__ = [
        {
            "attr": "my_types",
            "type": MyType,
            "add": "add_my_type",
            "get": "get_my_type",
            "create": "create_my_type",
        },
    ]

    __nwbfields__ = (
        {"name": "my_types", "required_name": None},
    )

    @docval(
        {"name": "name", "type": str, "doc": "Name of this container"},
        {"name": "my_types", "type": list, "doc": "List of MyType objects",
         "default": None},
        {"name": "description", "type": str, "doc": "Description",
         "default": "no description"},
    )
    def __init__(self, **kwargs):
        my_types = popargs("my_types", kwargs)
        super().__init__(**kwargs)
        if my_types:
            for item in my_types:
                self.add_my_type(item)
```

**DynamicTable subclass (simple, scalar columns only):**

```python
from pynwb import register_class
from hdmf.common import DynamicTable
from hdmf.utils import docval, popargs, get_docval

NS = "ndx-<name>"


@register_class("MyTable", NS)
class MyTable(DynamicTable):
    """A custom table type."""

    __columns__ = (
        {"name": "location", "description": "Brain region", "required": True},
        {"name": "threshold", "description": "Detection threshold", "required": False},
    )
```

`__columns__` works for simple tables with scalar columns and no extra datasets,
attributes, or links. The columns become required/optional `add_row()` kwargs.

**DynamicTable subclass (complex — with non-column datasets, attributes, links, or
multi-dimensional VectorData columns):**

`__columns__` does NOT work when the table has non-column datasets (e.g., shared bin
edges), table-level attributes (e.g., smoothing parameters), links (e.g., to
TimeSeries or TimeIntervals), or multi-dimensional VectorData columns. In these cases,
write a full custom class:

```python
from pynwb import register_class, TimeSeries
from pynwb.epoch import TimeIntervals
from hdmf.common import DynamicTable, DynamicTableRegion, VectorData, ElementIdentifiers
from hdmf.utils import docval, popargs

NS = "ndx-<name>"


@register_class("MyMapTable", NS)
class MyMapTable(DynamicTable):
    """A DynamicTable with non-column datasets, attributes, and links."""

    __nwbfields__ = (
        "bin_edges",                # non-column dataset
        "smoothing_kernel",         # will be stored as attribute (if in spec)
        {"name": "source_timeseries", "required_name": "source_timeseries"},  # link
    )

    @docval(
        {"name": "name", "type": str, "doc": "Name of this table"},
        {"name": "description", "type": str, "doc": "Description of this table"},
        # Custom fields
        {"name": "bin_edges", "type": "array_data",
         "doc": "Bin edges (non-column dataset)", "default": None},
        {"name": "units", "type": DynamicTableRegion,
         "doc": "Reference to Units table", "default": None},
        {"name": "rate_map", "type": VectorData,
         "doc": "Rate map values", "default": None},
        {"name": "occupancy_map", "type": VectorData,
         "doc": "Time spent per bin (optional column)", "default": None},
        {"name": "source_timeseries", "type": TimeSeries,
         "doc": "Source behavioral timeseries", "default": None},
        {"name": "smoothing_kernel", "type": str,
         "doc": "Smoothing kernel type", "default": None},
        # Read-path parameters — ObjectMapper passes these during HDF5 read
        {"name": "id", "type": ("array_data", ElementIdentifiers),
         "doc": "Row IDs", "default": None},
        {"name": "columns", "type": (list, tuple),
         "doc": "Columns (populated by ObjectMapper during read)", "default": None},
        {"name": "colnames", "type": ("scalar_data", list, tuple, "array_data"),
         "doc": "Column names (populated by ObjectMapper during read)", "default": None},
        allow_extra=True,  # Accept and ignore unknown kwargs from ObjectMapper
    )
    def __init__(self, **kwargs):
        bin_edges = popargs("bin_edges", kwargs)
        smoothing_kernel = popargs("smoothing_kernel", kwargs)
        source_timeseries = popargs("source_timeseries", kwargs)
        units, rate_map = popargs("units", "rate_map", kwargs)
        occupancy_map = popargs("occupancy_map", kwargs)
        # Discard fixed-value attributes the ObjectMapper passes during read
        kwargs.pop("unit_of_measurement", None)

        # Build columns list (user construction path only)
        # During read, ObjectMapper provides 'columns' already populated
        columns = kwargs.get("columns")
        if columns is None and rate_map is not None:
            columns = []
            if units is not None:
                columns.append(units)
            columns.append(rate_map)
            if occupancy_map is not None:
                columns.append(occupancy_map)
            kwargs["columns"] = columns

        super().__init__(**kwargs)

        # Set None for optional columns not provided, so ObjectMapper
        # can find the attribute during build
        colnames = self.colnames if self.colnames is not None else []
        if "occupancy_map" not in colnames:
            self.occupancy_map = None

        self.bin_edges = bin_edges
        self.smoothing_kernel = smoothing_kernel
        self.source_timeseries = source_timeseries

    @property
    def unit_of_measurement(self):
        return "Hz"
```

**Key patterns for complex DynamicTable subclasses:**

1. **`allow_extra=True`** — The ObjectMapper may pass spec-defined fixed-value
   attributes (like `unit_of_measurement`) that aren't in your docval. Use
   `allow_extra=True` and `kwargs.pop("field_name", None)` to discard them.

2. **Read-path parameters** — During HDF5 read, the ObjectMapper passes `id`
   (as `ElementIdentifiers`), `columns` (as a list), and `colnames` (as an ndarray).
   Include these in docval with broad type unions.

3. **Dual construction paths** — Users pass individual column args (`rate_map=...`);
   the ObjectMapper passes a pre-built `columns` list. Check `kwargs.get("columns")`
   to detect which path you're on.

4. **Optional columns need None** — If an optional column (e.g., `occupancy_map`) is
   absent, set `self.occupancy_map = None` after `super().__init__()` so the
   ObjectMapper can find the attribute during build.

5. **Fixed-value properties** — For spec attributes with `value:` (fixed), define a
   Python `@property` returning the fixed value. Do NOT include them in docval.

### Step 4: Verify the Classes Work

Test that each class can be instantiated:

```python
import numpy as np
from ndx_<name> import MyType, MyContainer

# Test basic instantiation
obj = MyType(
    name="test",
    signal=np.random.rand(100, 3),
    sampling_rate=30.0,
)
print(f"Created: {obj.name}, signal shape: {obj.signal.shape}")

# Test container
container = MyContainer(name="test_container")
container.add_my_type(obj)
print(f"Container has {len(container.my_types)} items")
```

### Step 5: Verify Round-Trip

Quick sanity check that the types can be written and read:

```python
from pynwb import NWBFile, NWBHDF5IO
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np

from ndx_<name> import MyType

nwbfile = NWBFile(
    session_description="test",
    identifier="test_id",
    session_start_time=datetime.now(ZoneInfo("UTC")),
)

obj = MyType(
    name="test",
    signal=np.random.rand(100, 3),
    sampling_rate=30.0,
)
nwbfile.add_acquisition(obj)  # or appropriate add method

with NWBHDF5IO("test_ext.nwb", "w") as io:
    io.write(nwbfile)

with NWBHDF5IO("test_ext.nwb", "r") as io:
    read_nwb = io.read()
    read_obj = read_nwb.acquisition["test"]
    print(f"Read back: {read_obj.name}, signal shape: {read_obj.signal.shape}")
    assert read_obj.signal.shape == (100, 3)

import os
os.remove("test_ext.nwb")
print("Round-trip OK!")
```

### Common Issues

**`KeyError: 'neurodata_type_def'`**: The class's base type doesn't match the spec's
`neurodata_type_inc`. Make sure the Python base class matches the spec parent type.

**`ValueError: 'field_name' is not a recognized field`**: The field name in `__nwbfields__`
doesn't match any field in the spec. Check spelling and that the field is defined in the spec.

**`TypeError in __init__`**: `@docval` is strict about types. Make sure parameter types
match what you're passing. Use `"array_data"` for numpy arrays, not `np.ndarray`.

**Namespace not found**: `load_namespaces()` wasn't called before `@register_class`.
Check the import order in `__init__.py`.

**Link not stored**: Links need specific `__nwbfields__` syntax:
```python
{"name": "device", "required_name": "device"}
```

**DynamicTable read fails with `TypeError: incorrect type for 'id'`**: The ObjectMapper
passes `ElementIdentifiers` for `id` and `ndarray` for `colnames`. Use broad type unions:
```python
{"name": "id", "type": ("array_data", ElementIdentifiers), ...}
{"name": "colnames", "type": ("scalar_data", list, tuple, "array_data"), ...}
```

**DynamicTable read fails with unrecognized argument**: The ObjectMapper passes
fixed-value attributes from the spec (e.g., `unit_of_measurement`). Use `allow_extra=True`
in docval and `kwargs.pop("field_name", None)` in `__init__`.

**`ContainerConfigurationError: does not have attribute 'X'`**: Optional columns that
weren't provided must be explicitly set to `None` after `super().__init__()`.

**`get_class()` fails for DynamicTable with custom columns**: Auto-generated classes
reject column kwargs like `units=...` or `rate_map=...`. DynamicTable subclasses with
spec-defined columns (VectorData, DynamicTableRegion) always need custom classes.
