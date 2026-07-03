# Custom Spyglass Tables

## When to Create a Custom Table vs. Open a Spyglass Issue

**Before writing any custom DataJoint table, ask: is this data type lab-specific or
does it represent a general neuroscience data type that other labs would also use?**

### Open a Spyglass issue (don't create a custom table) when:
The data type is a standardized neuroscience concept that Spyglass should support
for all users — e.g., trials structure, structured behavioral events, pose estimation,
fiber photometry responses. Creating a per-lab custom table fragments the ecosystem
and prevents cross-lab queries.

**How to open a Spyglass issue:**
- Open an issue at https://github.com/LorenFrankLab/spyglass/issues
- Describe the data type and what NWB objects it maps from
- Reference existing NWB extensions if applicable
- See https://github.com/LorenFrankLab/spyglass/pull/1349 as a model — this PR added
  support for structured behavioral data (trials). The pattern: define an NWB extension
  for the data structure, then add a Spyglass `Imported` table that reads it.

### Create a custom table when:
The data is **lab-specific proprietary** and would not generalize to other labs.

Examples that justify a custom table:
- `TaskLEDs` in jadhav-lab-to-nwb: LED positions and configurations specific to
  the Jadhav lab's spatial memory task setup
- Lab-specific stimulus parameters that have no standard NWB representation

Examples that should NOT get a custom table — open an issue instead:
- Spike sorting results → already in Spyglass SpikeSorting pipeline
- Fiber photometry → open an issue / check if already supported
- Pose estimation keypoints → open an issue

## How to Implement a Custom Spyglass Table

Reference: `jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_extensions/task_leds.py`

### Step 1: Create the spyglass_extensions directory

```
src/<lab_name>_to_nwb/<conversion_name>/
└── spyglass_extensions/
    ├── __init__.py
    └── <custom_table>.py
```

### Step 2: Implement the table class

```python
"""Custom Spyglass table for <lab>-specific <data type>."""

import datajoint as dj
from spyglass.utils import SpyglassMixin
from spyglass.common import Task, Nwbfile
from spyglass.utils.nwb_helper_fn import get_nwb_file

schema = dj.schema("<schema_name>")   # e.g., "task_leds", "jadhav_stim"


@schema
class <CustomTable>(SpyglassMixin, dj.Imported):
    """<Description of what this table stores and why it's lab-specific.>"""

    definition = """
    -> Task                          # foreign key to Spyglass Task table
    <secondary_key> : varchar(32)    # additional primary key field(s)
    ---
    <attribute_1> : varchar(64)      # non-key attributes
    <attribute_2> : float
    """

    def make(self, key: dict):
        """Populate this table for one session by reading from the NWB file."""
        nwb_file_name = key["nwb_file_name"]
        nwbfile = get_nwb_file(Nwbfile().get_abs_path(nwb_file_name))

        # Read from the NWB processing module where you stored this data
        task_module = nwbfile.processing.get("tasks")
        if task_module is None:
            return
        task_table = task_module.data_interfaces.get("task_table")
        if task_table is None:
            return

        task_df = task_table.to_dataframe()

        for _, row in task_df.iterrows():
            # Extract the data and build the row dict
            entry = {
                **key,
                "<secondary_key>": row["<column_name>"],
                "<attribute_1>": row["<other_column>"],
                "<attribute_2>": float(row["<numeric_column>"]),
            }
            self.insert1(entry, allow_direct_insert=True, skip_duplicates=True)
```

### Step 3: Register and populate

In `insert_session.py`, after the main `sgi.insert_sessions()` call:

```python
from .spyglass_extensions.<module> import <CustomTable>

# Populate the custom table for this session
<CustomTable>.populate({"nwb_file_name": nwb_file_name})
```

And add it to `verify_insertion.py`'s `print_tables()` and `clean_db_entry()`.

### Key Rules

- **Always inherit from both `SpyglassMixin` and `dj.Imported`** — `SpyglassMixin`
  provides Spyglass-compatible fetch methods; `dj.Imported` means the table is
  populated by reading from source (NWB) rather than manually entered.
- **Foreign key to `Task` (not `Nwbfile`)** — this links the custom data to a
  specific task/epoch, which is the correct dependency granularity.
- **Use `allow_direct_insert=True, skip_duplicates=True`** in `insert1()` inside
  `make()` — this is the standard Spyglass pattern for custom Imported tables.
- **Store what Spyglass needs in the NWB file** — the `make()` method reads from
  NWB processing modules. Whatever custom data the table needs must be written into
  the NWB file first (e.g., into `nwbfile.processing["tasks"]["task_table"]`).
- **Name the schema clearly** — the schema name becomes a DataJoint database prefix.
  Use something like `"<lab_short>_<data_type>"` to avoid collisions.
