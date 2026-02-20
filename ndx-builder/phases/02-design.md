## Phase 2: Extension Design

**Goal**: Design the type hierarchy, field definitions, and relationships for the extension.

**Entry**: You have clear requirements from Phase 1 with identified base types.

**Exit criteria**: A complete design document with:
- All neurodata types defined (names, base types, fields)
- Relationships between types (containment, links, table regions)
- Quantities for all fields and sub-groups
- Data types and shapes for all datasets

### Step 1: Design the Type Hierarchy

Based on the requirements, design which types you need and how they relate.

**Design principles:**
1. **Decompose into focused types.** Don't create one monolithic type with 20 fields.
   Break complex structures into multiple types with clear responsibilities.
2. **Choose containment vs links.** Use containment (sub-groups) when the child exists
   only within the parent. Use links when the target may be shared or lives elsewhere.
3. **Prefer DynamicTable for tabular data.** If data naturally forms rows with named
   columns, use DynamicTable rather than parallel arrays.
4. **Don't duplicate inherited fields.** If your type extends TimeSeries, don't redefine
   `data`, `timestamps`, or `unit` — they're already there.
5. **Use the most specific base type.** Extend `TimeSeries` for time-varying data,
   not `NWBDataInterface`. Extend `Device` for hardware, not `NWBContainer`.

### Step 2: Define Each Type

For each neurodata type, document:

```markdown
### TypeName
- **Extends**: ParentType
- **Fixed name**: None / "specific_name"
- **Default name**: None / "suggested_name"
- **Doc**: Description of what this type represents
- **Where it lives**: acquisition / processing / lab_meta_data / devices / inside ParentContainer

#### Attributes
| Name | dtype | Required | Default | Doc |
|------|-------|----------|---------|-----|
| attr1 | text | Yes | - | Description |
| attr2 | float64 | No | 1.0 | Description |

#### Datasets
| Name | dtype | Shape | Dims | Required | Doc |
|------|-------|-------|------|----------|-----|
| data | float64 | (None, None) | (num_times, num_channels) | Yes | Description |
| labels | text | (None,) | (num_channels,) | No | Description |

#### Sub-groups
| Type | Quantity | Doc |
|------|----------|-----|
| ChildType | * | Description |

#### Links
| Name | Target | Quantity | Doc |
|------|--------|----------|-----|
| device | Device | ? | Description |
```

### Step 3: Choose Between Attributes and Datasets

This distinction matters for HDF5 storage:

| Use Attributes For | Use Datasets For |
|-------------------|------------------|
| Small scalars (strings, numbers) | Arrays of any size |
| Configuration parameters | Time series data |
| Fixed metadata | Tabular columns |
| Values < 64 KB total | Anything that needs chunking or compression |

**Rule of thumb:** If the data could grow large (more than a few hundred elements),
it should be a dataset, not an attribute.

### Step 4: Define Quantities

For each field, decide its quantity:

| Scenario | Quantity |
|----------|----------|
| Always exactly one | `1` (default, required) |
| Optional, at most one | `'?'` |
| Zero or more (collection) | `'*'` |
| At least one (required collection) | `'+'` |

### Step 5: Consider DynamicTable

If any part of the design has tabular data, consider DynamicTable:

**Good candidates for DynamicTable:**
- Channel configuration (one row per channel with device refs, location, wavelength)
- Event records (timestamp, type, value per event)
- ROI metadata (location, size, cell type per ROI)
- Any data where users might want to add custom columns

**DynamicTable design:**
```markdown
### MyTable (extends DynamicTable)
| Column | dtype | Required | Doc |
|--------|-------|----------|-----|
| location | text | Yes | Brain region |
| device | Device (ref) | Yes | Recording device |
| threshold | float64 | No | Detection threshold |
```

### Step 6: Design Review Checklist

Before proceeding to scaffolding, verify:

- [ ] Every type has a clear, non-overlapping purpose
- [ ] No fields duplicate what parent types already provide
- [ ] Relationships use the right mechanism (containment vs link vs table region)
- [ ] Data types and shapes are correct for the data
- [ ] Quantities match the actual requirements (required vs optional)
- [ ] Large data uses datasets, not attributes
- [ ] The design follows existing NWB naming conventions
- [ ] The type names are descriptive and use CamelCase
- [ ] The extension name follows `ndx-` convention with lowercase hyphens

### Step 7: Present Design to User

Present the complete design and ask for confirmation:

> Here's my proposed design for `ndx-<name>`:
>
> **Types:**
> 1. `TypeA` (extends LabMetaData) — [purpose]
>    - Fields: ...
> 2. `TypeB` (extends TimeSeries) — [purpose]
>    - Fields: ...
>
> **Relationships:**
> - TypeA contains TypeB instances
> - TypeB links to Device
>
> Does this design capture everything you need? Anything to add or change?

<choices>
<choice>The design looks good, let's proceed</choice>
<choice>I'd like to modify some fields</choice>
<choice>I need to add more types</choice>
<choice>Let me think about this and come back</choice>
</choices>

### Step 8: Update Design Notes

Update `design_notes.md` with the finalized design:

```markdown
## Type Hierarchy

[ASCII diagram or description of type relationships]

## Type Definitions

[Full definitions for each type as documented above]

## Design Decisions

- [Why we chose X over Y]
- [Trade-offs considered]
```
