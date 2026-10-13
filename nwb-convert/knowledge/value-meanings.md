# Value Meanings and HED

Reference for the second half of Phase 6. A `MeaningsTable` records what each value of a
categorical column means, and can carry a HED annotation for each value beside its meaning.

- `MeaningsTable` is part of HDMF and needs `pynwb>=4.2`. It has a `value` column and a
  `meaning` column, is named `<column>_meanings`, and is stored inside the table whose column
  it describes, in that table's `meanings_tables` group.
- HED (Hierarchical Event Descriptors) is a controlled vocabulary for describing events and
  experimental conditions. The `ndx-hed` extension stores one HED string per value in a column
  of the `MeaningsTable` named `HED`, and the schema version once per file in a
  `HedLabMetaData` object.

Background reading:

- HED annotation semantics: https://www.hedtags.org/hed-resources/HedAnnotationSemantics.html
- HED schema browser: https://www.hedtags.org/hed-schema-browser
- ndx-hed: https://www.hedtags.org/ndx-hed

The meanings need nothing beyond PyNWB. The HED part needs `ndx-hed`, and the release that
supports `pynwb>=4` is not on PyPI yet (https://github.com/hed-standard/ndx-hed/issues/194),
so until then it is installed from GitHub:

```bash
pip install "ndx-hed @ git+https://github.com/hed-standard/ndx-hed.git@main"
```

If it cannot be installed (for example in NWB GUIDE, where the packages are bundled), write
the meanings and leave HED out.

## Listing the Categorical Columns in a File

Prints every column that holds a small set of repeated values, read from a written file (a
stub is enough), and whether it already has a `MeaningsTable`:

```python
import numpy as np
from hdmf.common import DynamicTable, DynamicTableRegion, MeaningsTable, VectorIndex
from pynwb import NWBHDF5IO

with NWBHDF5IO("/path/to/output/session.nwb", "r") as io:
    nwbfile = io.read()
    for table in nwbfile.all_children():
        if not isinstance(table, DynamicTable) or isinstance(table, MeaningsTable):
            continue
        for column_name in table.colnames:
            column = table[column_name]
            if isinstance(column, VectorIndex):  # a ragged column: look at the values underneath
                column = column.target
            if isinstance(column, DynamicTableRegion) or len(column.data) == 0:
                continue
            values = np.asarray(column.data[:])
            if values.ndim != 1 or values.dtype.kind not in "OSUbiu":
                continue
            distinct = sorted(set(values.tolist()))
            if len(distinct) > 20 or (len(distinct) == len(values) and len(values) > 2):
                continue  # identifiers and free text, not categories
            meanings_table = table.get_meanings_for_column(column_name)
            described = [] if meanings_table is None else meanings_table["value"].data[:].tolist()
            print(f"{table.name}/{column_name}: {distinct}")
            print(f"    description: {column.description}")
            print(f"    without a meaning: {[value for value in distinct if value not in described]}")
```

A stub holds few rows, so a value that is rare may not appear. Check the source data or the
task code for the full set of values a column can take, and list all of them: a
`MeaningsTable` should cover every possible value, including one this session never used.

Integer columns are listed because codes are often integers, but a count or an index is not
categorical. Leave those out.

## Finding HED Tags

Search the schema instead of recalling tags. This prints the tags whose name or description
contains each term, with their descriptions:

```python
from hed import load_schema_version

schema = load_schema_version("8.4.0")
for term in ["reward", "abort"]:
    found = {
        entry.short_tag_name: entry.description
        for entry in schema.tags.all_entries
        if term in entry.short_tag_name.lower() or term in (entry.description or "").lower()
    }
    print(f"{term}: {len(found)} tags")
    for tag, description in found.items():
        print(f"    {tag}: {description}")
```

A term with no tags (`abort` has none in 8.4.0) means the concept is not in the vocabulary
under that word. Try a broader word or a synonym before concluding it is missing.

Writing the annotation:

- Use the short form of each tag (`Reward`, not `Property/Task-property/.../Reward`), and
  separate tags with commas.
- Put tags that describe the same thing in one parenthesized group:
  `(Somatic-presentation, Experimental-stimulus)`.
- A tag that takes a value is written with a slash: `Condition-variable/Center-hold-bump`,
  `Label/Abort`. Write the value with letters, digits, and hyphens.
- In an events table, the annotation of an event type says what happened at that time, and
  starts with one of the event tags: `Sensory-event`, `Agent-action`, `Data-feature`,
  `Experiment-control`, `Experiment-procedure`, `Experiment-structure`, `Measurement-event`.
- In a trials table, a column usually names a condition or an outcome of the whole trial, not
  something that happened at the trial's start time. Name the condition with
  `Condition-variable/<Name>` and add the tags that describe it. Do not tag the row with an
  event that happened at some other time. That event belongs in an events table, at its own
  time.
- Do not extend the vocabulary with a new tag (`Square/Big-one`). When no tag fits, use
  `Label/<Name>` for the part that has none, or leave the value without HED.

## Validating HED Strings

Validate every string before recording it. An empty result means the string is valid:

```python
from hed import HedString, load_schema_version
from hed.errors import ErrorHandler, get_printable_issue_string
from hed.validator import HedValidator

schema = load_schema_version("8.4.0")
validator = HedValidator(schema)
for hed_string in ["Experimental-trial, Correct-action, Reward", "Experimental-trial, Aborted"]:
    issues = validator.validate(
        HedString(hed_string, schema), allow_placeholders=False, error_handler=ErrorHandler(check_for_warnings=True)
    )
    print(hed_string, "->", get_printable_issue_string(issues) if issues else "valid")
```

Fix every error and every warning. `TAG_INVALID` means the tag is not in the schema, and
`TAG_EXTENDED` means a tag was extended with a new child. A string that validates is
well-formed, which is not the same as correct: read it back against the meaning it annotates.

## Writing the Meanings

Add this module to the conversion package (e.g. `value_meanings.py` next to the converter).
It reads the mapping from `value_meanings.yaml` and writes a `MeaningsTable` for each column
that is present in the file:

```python
from hdmf.common import DynamicTable, MeaningsTable, VectorIndex
from pynwb import NWBFile


def add_value_meanings(nwbfile: NWBFile, annotations: dict) -> None:
    """Write the meanings and HED in value_meanings.yaml into the file as MeaningsTables."""
    tables = [
        neurodata_object
        for neurodata_object in nwbfile.all_children()
        if isinstance(neurodata_object, DynamicTable) and not isinstance(neurodata_object, MeaningsTable)
    ]
    wrote_hed = False
    for table_name, columns in (annotations.get("tables") or {}).items():
        for table in (table for table in tables if table.name == table_name):
            for column_name, entries in (columns or {}).items():
                if column_name not in table.colnames or not entries:
                    continue
                column = table[column_name]
                if isinstance(column, VectorIndex):  # a ragged column: the meanings describe its values
                    column = column.target
                # A NeuroConv events interface may already have written meanings for this column
                meanings_table = table.get_meanings_for_column(column_name)
                is_new = meanings_table is None
                if is_new:
                    meanings_table = MeaningsTable(target=column)
                described = list(meanings_table["value"].data)
                if "HED" not in meanings_table.colnames and any(entry.get("hed") for entry in entries.values()):
                    from ndx_hed import HedTags

                    meanings_table.add_column(
                        name="HED",  # the name ndx-hed requires
                        description="HED annotation of each value.",
                        data=[(entries.get(value) or {}).get("hed", "") for value in described],
                        col_cls=HedTags,
                    )
                has_hed = "HED" in meanings_table.colnames
                wrote_hed = wrote_hed or has_hed
                for value, entry in entries.items():
                    if value in described:
                        continue
                    row = dict(value=value, meaning=entry["meaning"])
                    if has_hed:
                        row["HED"] = entry.get("hed", "")  # empty means no annotation
                    meanings_table.add_row(**row)
                if is_new:
                    table.add_meanings_table(meanings_table)

    if wrote_hed and "hed_schema" not in nwbfile.lab_meta_data:
        from ndx_hed import HedLabMetaData

        # The file records the schema version its annotations were validated against
        nwbfile.add_lab_meta_data(HedLabMetaData(hed_schema_version=annotations["hed_schema_version"]))
```

Call it from the converter, after the interfaces have added their data, so the tables exist.
Phase 6 already added an `add_to_nwbfile` override for the HERD references; add the two
lines to it:

```python
from pathlib import Path

from neuroconv import NWBConverter
from neuroconv.utils import load_dict_from_file

from .external_resources import add_external_resources
from .value_meanings import add_value_meanings


class <ConversionName>NWBConverter(NWBConverter):

    def add_to_nwbfile(self, nwbfile, metadata, conversion_options=None):
        super().add_to_nwbfile(nwbfile=nwbfile, metadata=metadata, conversion_options=conversion_options)
        terms = load_dict_from_file(Path(__file__).parent / "external_resources.yaml")
        add_external_resources(nwbfile=nwbfile, terms=terms)
        annotations = load_dict_from_file(Path(__file__).parent / "value_meanings.yaml")
        add_value_meanings(nwbfile=nwbfile, annotations=annotations)
```

How the helper behaves:

- A table is found by its name (`trials`, or the name of an events table), wherever it sits
  in the file. A table or a column that this session does not have is skipped.
- A value's key in the YAML must equal the value in the file, including its type: `R` for a
  string, `true` and `false` for a boolean column, `1` for an integer code.
- Where a `MeaningsTable` already exists, its rows are kept as they are. Values it does not
  describe are added, and HED is added to the values it does describe.
- An entry needs a `meaning`. Its `hed` is optional.

## Checking a Written File

Prints each `MeaningsTable` in the file, the values in its column that it does not describe,
and the result of validating its HED:

```python
import numpy as np
from hdmf.common import MeaningsTable
from pynwb import NWBHDF5IO

with NWBHDF5IO("/path/to/output/session.nwb", "r") as io:
    nwbfile = io.read()
    hed_strings = {}
    for meanings_table in nwbfile.all_children():
        if not isinstance(meanings_table, MeaningsTable):
            continue
        label = f"{meanings_table.parent.name}/{meanings_table.target.name}"
        print(meanings_table.to_dataframe().to_string())
        described = meanings_table["value"].data[:].tolist()
        in_file = sorted(set(np.asarray(meanings_table.target.data[:]).tolist()))
        print(f"{label} values without a meaning:", [value for value in in_file if value not in described])
        if "HED" in meanings_table.colnames:
            for value, hed_string in zip(described, meanings_table["HED"].data[:]):
                if hed_string:
                    hed_strings[f"{label} = {value}"] = hed_string
    hed_metadata = nwbfile.lab_meta_data.get("hed_schema")
    hed_schema_version = None if hed_metadata is None else hed_metadata.hed_schema_version

if hed_strings:
    from hed import HedString, load_schema_version
    from hed.errors import ErrorHandler, get_printable_issue_string
    from hed.validator import HedValidator

    schema = load_schema_version(hed_schema_version)
    validator = HedValidator(schema)
    invalid = 0
    for label, hed_string in hed_strings.items():
        issues = validator.validate(
            HedString(hed_string, schema), allow_placeholders=False, error_handler=ErrorHandler(check_for_warnings=True)
        )
        if issues:
            invalid += 1
            print(f"{label}: {hed_string}\n{get_printable_issue_string(issues)}")
    print(f"HED strings: {len(hed_strings)}, with issues: {invalid}")
```

A value listed as without a meaning is either missing from `value_meanings.yaml` or written
there with a different type or spelling than in the file. A fill value such as an empty
string, which NeuroConv writes where a row has nothing for a column, needs no meaning.

`ndx-hed` also has `HedNWBValidator.validate_file`, which assembles the annotations of each
row before validating them and so also catches a tag repeated across two columns of one
table. With the current `ndx-hed` it raises `TypeError` when an annotated column read from a
file holds booleans or integers, so the check above validates each string on its own.
