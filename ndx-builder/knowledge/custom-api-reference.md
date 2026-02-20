# Custom Python API Reference

Reference for building custom Python classes for NWB extensions. These classes provide
a Pythonic API on top of the spec-defined schema.

## Auto-Generated vs Custom Classes

**Decision point**: Not every extension needs custom Python classes. Use auto-generation
for simple types and custom classes when you need Python-level validation or convenience.

| Approach | When to Use |
|----------|-------------|
| `get_class()` (auto-generated) | Simple types with only attributes and basic datasets |
| Custom class | Complex init logic, validation, computed properties, MultiContainerInterface |

## Auto-Generated Classes with `get_class()`

The simplest approach. HDMF generates Python classes directly from the spec.

```python
# In src/pynwb/ndx_my_extension/__init__.py

from pynwb import load_namespaces, get_class

# IMPORTANT: load_namespaces() MUST be called before get_class()
load_namespaces("ndx-my-extension.namespace.yaml")

# Auto-generate a class from the spec
MyType = get_class("MyType", "ndx-my-extension")
```

The generated class:
- Accepts all spec-defined fields as `__init__` kwargs
- Has properties for each field
- Handles HDF5 I/O automatically
- Works with PyNWB's type system

**When `get_class()` is sufficient:**
- The type has only attributes and simple datasets
- No special initialization logic needed
- No computed properties
- No custom validation beyond what the spec provides

## Loading Namespaces

Every extension must load its namespace YAML before registering classes:

```python
import os
from pynwb import load_namespaces

# Get the path to the namespace YAML relative to this file
ndx_dir = os.path.dirname(__file__)
ns_path = os.path.join(ndx_dir, "spec", "ndx-my-extension.namespace.yaml")

load_namespaces(ns_path)
```

**Critical**: `load_namespaces()` must execute before any `@register_class` decorators
or `get_class()` calls. Put it at module level in `__init__.py`.

## `@register_class` Decorator

Registers a custom Python class for a specific neurodata type:

```python
from pynwb import register_class

@register_class("MyType", "ndx-my-extension")
class MyType(NWBDataInterface):
    """Python API for MyType."""
    ...
```

Parameters:
- First arg: the `neurodata_type_def` string from the spec
- Second arg: the namespace name

**The class must inherit from an appropriate PyNWB/HDMF base class** that matches
the spec's `neurodata_type_inc`. See the mapping table below.

## `__nwbfields__` Tuple

Declares which instance attributes should be persisted to HDF5. Only fields listed
here are written to and read from the file.

```python
@register_class("MyType", "ndx-my-extension")
class MyType(NWBDataInterface):
    __nwbfields__ = (
        "signal",           # dataset
        "sampling_rate",    # attribute (also stored)
        {"name": "device", "required_name": "device"},  # link with fixed name
    )
```

**Rules:**
- Simple strings for datasets and attributes
- Dict with `name` and `required_name` for links
- Dict with `name` and `child` for contained typed groups:
  ```python
  {"name": "my_container", "child": True}
  ```
- Order doesn't matter for storage, but affects code readability

## `@docval` Decorator

Type-checked documentation for method parameters. Used on `__init__` and other public methods.

```python
from hdmf.utils import docval, getargs, popargs

@register_class("MyType", "ndx-my-extension")
class MyType(NWBDataInterface):

    @docval(
        {"name": "name", "type": str, "doc": "Name of this object"},
        {"name": "signal", "type": ("array_data", "data"), "doc": "The recorded signal",
         "shape": [(None,), (None, None)]},
        {"name": "sampling_rate", "type": float, "doc": "Sampling rate in Hz"},
        {"name": "description", "type": str, "doc": "Description", "default": "no description"},
        {"name": "device", "type": Device, "doc": "Recording device", "default": None},
    )
    def __init__(self, **kwargs):
        # Pop args that aren't passed to parent
        signal, sampling_rate, device = popargs("signal", "sampling_rate", "device", kwargs)
        super().__init__(**kwargs)
        self.signal = signal
        self.sampling_rate = sampling_rate
        self.device = device
```

### `docval` field options

| Key | Required | Description |
|-----|----------|-------------|
| `name` | Yes | Parameter name |
| `type` | Yes | Type or tuple of types |
| `doc` | Yes | Documentation string |
| `default` | No | Default value. If absent, the parameter is required. |
| `shape` | No | Expected data shape |
| `allow_none` | No | If `True`, `None` is also accepted |

### Type macros

Special string types for common patterns:

| Macro | Meaning |
|-------|---------|
| `"array_data"` | numpy array, list, tuple, h5py.Dataset, etc. |
| `"scalar_data"` | int, float, str, bytes, np.generic |
| `"data"` | Either array_data or scalar_data |

```python
# Accept array-like data
{"name": "data", "type": "array_data", "doc": "The data array"}

# Accept any data
{"name": "value", "type": "data", "doc": "A value (scalar or array)"}

# Accept multiple specific types
{"name": "timestamps", "type": ("array_data", TimeSeries), "doc": "Timestamps or reference"}
```

## `getargs()` and `popargs()`

Helper functions for extracting kwargs in `__init__`:

```python
from hdmf.utils import getargs, popargs

# getargs: get values without removing from kwargs
name, data = getargs("name", "data", kwargs)

# popargs: get AND remove from kwargs (use before passing to super().__init__)
signal, rate = popargs("signal", "rate", kwargs)
super().__init__(**kwargs)  # remaining kwargs go to parent
```

**When to use which:**
- `popargs`: For fields that your class handles directly and should NOT be passed to the parent
- `getargs`: For fields you need to inspect but still want passed to the parent

## Base Classes

Choose the base class that matches your spec's `neurodata_type_inc`:

| Spec `neurodata_type_inc` | Python Base Class | Import |
|---------------------------|-------------------|--------|
| `NWBContainer` | `NWBContainer` | `from pynwb import NWBContainer` |
| `NWBDataInterface` | `NWBDataInterface` | `from pynwb import NWBDataInterface` |
| `NWBData` | `NWBData` | `from pynwb import NWBData` |
| `TimeSeries` | `TimeSeries` | `from pynwb import TimeSeries` |
| `LabMetaData` | `LabMetaData` | `from pynwb.file import LabMetaData` |
| `DynamicTable` | `DynamicTable` | `from hdmf.common import DynamicTable` |
| `Device` | `Device` | `from pynwb.device import Device` |

## MultiContainerInterface

For types that hold multiple instances of the same child type. Provides
`add_X()`, `get_X()`, and `create_X()` convenience methods.

```python
from pynwb import register_class
from pynwb.core import MultiContainerInterface

@register_class("PotatoSack", "ndx-potato")
class PotatoSack(MultiContainerInterface):

    __clsconf__ = [
        {
            "attr": "potatoes",          # Python attribute name (list)
            "type": Potato,              # The contained class
            "add": "add_potato",         # Name of the add method
            "get": "get_potato",         # Name of the get method
            "create": "create_potato",   # Name of the create method
        },
    ]

    __nwbfields__ = (
        {"name": "potatoes", "required_name": None},
    )

    @docval(
        {"name": "name", "type": str, "doc": "Name"},
        {"name": "potatoes", "type": list, "doc": "List of Potato objects", "default": None},
    )
    def __init__(self, **kwargs):
        potatoes = popargs("potatoes", kwargs)
        super().__init__(**kwargs)
        if potatoes:
            for p in potatoes:
                self.add_potato(p)
```

Usage:
```python
sack = PotatoSack(name="my_sack")
sack.add_potato(Potato(name="russet", weight=150.0))
sack.create_potato(name="yukon", weight=120.0)  # Creates and adds
p = sack.get_potato("russet")
```

### Multiple container types

`__clsconf__` can hold multiple entries for different child types:

```python
__clsconf__ = [
    {"attr": "potatoes", "type": Potato, "add": "add_potato", "get": "get_potato", "create": "create_potato"},
    {"attr": "carrots", "type": Carrot, "add": "add_carrot", "get": "get_carrot", "create": "create_carrot"},
]
```

## DynamicTable with Custom Columns

DynamicTable subclasses that define typed columns (VectorData, DynamicTableRegion) in
the spec **cannot use `get_class()` or `__columns__`**. They require a full custom class
because:

1. `get_class()` auto-generated classes reject column kwargs (e.g., `units=...`)
2. `__columns__` only works for simple scalar columns, not multi-dimensional VectorData,
   non-column datasets, table-level attributes, or links
3. The ObjectMapper passes extra parameters during read that must be handled

### Pattern: Full Custom DynamicTable Class

```python
from pynwb import register_class, TimeSeries
from pynwb.epoch import TimeIntervals
from hdmf.common import DynamicTable, DynamicTableRegion, VectorData, ElementIdentifiers
from hdmf.utils import docval, popargs

NS = "ndx-<name>"


@register_class("MyTable", NS)
class MyTable(DynamicTable):
    """A table with non-column datasets, attributes, and links."""

    __nwbfields__ = (
        "bin_edges",             # non-column dataset (shared across rows)
        "smoothing_kernel",      # stored as HDF5 attribute (from spec)
        {"name": "source_timeseries", "required_name": "source_timeseries"},  # link
        {"name": "time_support", "required_name": "time_support"},            # link
    )

    @docval(
        {"name": "name", "type": str, "doc": "Name of this table"},
        {"name": "description", "type": str, "doc": "Description"},
        # Non-column datasets
        {"name": "bin_edges", "type": "array_data",
         "doc": "Shared bin edges", "default": None},
        # Column args — users pass these individually
        {"name": "units", "type": DynamicTableRegion,
         "doc": "Reference to Units table", "default": None},
        {"name": "rate_map", "type": VectorData,
         "doc": "Rate map values", "default": None},
        {"name": "occupancy_map", "type": VectorData,
         "doc": "Optional occupancy column", "default": None},
        # Links
        {"name": "source_timeseries", "type": TimeSeries,
         "doc": "Source timeseries", "default": None},
        {"name": "time_support", "type": TimeIntervals,
         "doc": "Time intervals", "default": None},
        # Attributes
        {"name": "smoothing_kernel", "type": str,
         "doc": "Smoothing kernel type", "default": None},
        # Read-path parameters — ObjectMapper passes these during HDF5 read
        {"name": "id", "type": ("array_data", ElementIdentifiers),
         "doc": "Row IDs", "default": None},
        {"name": "columns", "type": (list, tuple),
         "doc": "Columns (from ObjectMapper during read)", "default": None},
        {"name": "colnames", "type": ("scalar_data", list, tuple, "array_data"),
         "doc": "Column names (from ObjectMapper during read)", "default": None},
        allow_extra=True,  # Accepts unknown kwargs from ObjectMapper
    )
    def __init__(self, **kwargs):
        # Pop custom fields before passing to DynamicTable.__init__
        bin_edges = popargs("bin_edges", kwargs)
        smoothing_kernel = popargs("smoothing_kernel", kwargs)
        source_timeseries, time_support = popargs(
            "source_timeseries", "time_support", kwargs
        )
        units, rate_map = popargs("units", "rate_map", kwargs)
        occupancy_map = popargs("occupancy_map", kwargs)
        # Discard fixed-value spec attributes passed by ObjectMapper
        kwargs.pop("unit_of_measurement", None)

        # Build columns list (user construction path)
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

        # Set None for optional columns not provided
        colnames = self.colnames if self.colnames is not None else []
        if "occupancy_map" not in colnames:
            self.occupancy_map = None

        self.bin_edges = bin_edges
        self.smoothing_kernel = smoothing_kernel
        self.source_timeseries = source_timeseries
        self.time_support = time_support

    @property
    def unit_of_measurement(self):
        """Fixed value from spec — not in docval."""
        return "Hz"
```

### Key Gotchas for DynamicTable Custom Classes

| Issue | Solution |
|-------|----------|
| ObjectMapper passes fixed-value spec attributes | `allow_extra=True` + `kwargs.pop("field", None)` |
| `id` arrives as `ElementIdentifiers` during read | `"type": ("array_data", ElementIdentifiers)` |
| `colnames` arrives as `ndarray` during read | `"type": ("scalar_data", list, tuple, "array_data")` |
| Optional column missing causes build error | Set `self.column_name = None` after `super().__init__()` |
| User passes columns individually, ObjectMapper passes list | Check `kwargs.get("columns")` to detect construction path |
| Fixed-value attribute (e.g., `unit_of_measurement`) | Define as `@property`, not in docval |

## `__init__.py` Pattern (Modern)

The ndx-template generates an `__init__.py` using `importlib.resources` (preferred over
`os.path`):

```python
from importlib.resources import files
from pynwb import load_namespaces

# Get path to namespace YAML
__location_of_this_file = files(__name__)
__spec_path = __location_of_this_file / "spec" / "ndx-<name>.namespace.yaml"

# Fallback for editable install
if not __spec_path.exists():
    __spec_path = __location_of_this_file.parent.parent.parent / "spec" / "ndx-<name>.namespace.yaml"

# Load namespace BEFORE importing custom classes
load_namespaces(str(__spec_path))

from .my_table import MyTable  # noqa: E402, F401

__all__ = ["MyTable"]

# Clean up module namespace
del load_namespaces, files, __location_of_this_file, __spec_path
```

## ObjectMapper

Custom mapping between Python objects and HDF5 storage. Needed when the default
field-to-dataset/attribute mapping isn't sufficient.

```python
from hdmf.build import ObjectMapper
from hdmf.common import register_map

@register_map(MyType)
class MyTypeMapper(ObjectMapper):
    """Custom mapping for MyType."""

    def __init__(self, spec):
        super().__init__(spec)
        # Map a Python attribute to a differently-named spec field
        self.map_spec("python_attr_name", spec.get_dataset("spec_field_name"))
        # Or map to an attribute
        self.map_spec("python_attr", spec.get_attribute("spec_attr"))
```

**When you need ObjectMapper:**
- Python attribute name differs from spec field name
- Field needs special serialization/deserialization
- Complex nesting that auto-mapping doesn't handle

**Most extensions don't need ObjectMapper.** Only use it when the default mapping
produces errors or incorrect behavior.

## `_in_construct_mode`

Available on all NWBContainer subclasses. Returns `True` when the object is being
constructed from an HDF5 file (read mode), `False` when being created by the user
(write mode).

```python
@docval(...)
def __init__(self, **kwargs):
    data = popargs("data", kwargs)
    super().__init__(**kwargs)
    if not self._in_construct_mode:
        # Only validate when user is creating the object
        if data.shape[1] != 3:
            raise ValueError("Data must have 3 columns (x, y, z)")
    self.data = data
```

**Use cases:**
- Validation that should only run on user-created objects
- Data transformations during construction (but not during read)
- Setting default values that shouldn't override stored values

## Complete Custom Class Example

```python
import os
import numpy as np
from pynwb import load_namespaces, register_class, NWBDataInterface
from pynwb.device import Device
from hdmf.utils import docval, popargs

# Load namespace
ns_path = os.path.join(os.path.dirname(__file__), "spec", "ndx-my-ext.namespace.yaml")
load_namespaces(ns_path)

NS = "ndx-my-ext"


@register_class("MyRecording", NS)
class MyRecording(NWBDataInterface):
    """A custom recording type."""

    __nwbfields__ = (
        "data",
        "timestamps",
        "sampling_rate",
        {"name": "device", "required_name": "device"},
    )

    @docval(
        {"name": "name", "type": str, "doc": "Name of this recording"},
        {"name": "data", "type": "array_data", "doc": "Recorded data",
         "shape": (None, None)},
        {"name": "timestamps", "type": "array_data", "doc": "Timestamps in seconds",
         "shape": (None,), "default": None},
        {"name": "sampling_rate", "type": float, "doc": "Sampling rate in Hz",
         "default": None},
        {"name": "device", "type": Device, "doc": "Recording device",
         "default": None},
        {"name": "description", "type": str, "doc": "Description",
         "default": "no description"},
    )
    def __init__(self, **kwargs):
        data, timestamps, sampling_rate, device = popargs(
            "data", "timestamps", "sampling_rate", "device", kwargs
        )
        super().__init__(**kwargs)

        if not self._in_construct_mode:
            if timestamps is None and sampling_rate is None:
                raise ValueError("Must provide either timestamps or sampling_rate")

        self.data = data
        self.timestamps = timestamps
        self.sampling_rate = sampling_rate
        self.device = device
```

## `__init__.py` Pattern (Legacy)

Older extensions used `os.path`:

```python
import os
from pynwb import load_namespaces, get_class

ndx_dir = os.path.dirname(__file__)
ns_path = os.path.join(ndx_dir, "spec", "ndx-my-extension.namespace.yaml")
load_namespaces(ns_path)

MySimpleType = get_class("MySimpleType", "ndx-my-extension")
from .my_custom_type import MyCustomType  # noqa: E402, F401
```

The modern `importlib.resources` pattern (shown in the `__init__.py` Pattern (Modern)
section above) is preferred and is what ndx-template now generates.
