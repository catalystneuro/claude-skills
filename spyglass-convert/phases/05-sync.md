## Phase 5: Synchronization Analysis

**Goal**: Understand how different data streams are temporally aligned and implement
sync logic so all data in the NWB file shares a common time base.

**Entry**: You know all data streams and interfaces from Phase 3.

**Baseline**: Follow **nwb-convert Phase 4** in full. All synchronization patterns
(TTL alignment, starting-time offset, `align_by_interpolation`) are identical.
The only difference: record decisions in `spyglass_notes.md` instead of
`conversion_notes.md`.

**Exit criteria**: For every pair of data streams, you know whether they share a
clock, and if not, how to align them. Implementation plan is documented.

### Questions to Ask

> I need to understand how your data streams are synchronized:
>
> 1. Do all your recording systems share a common clock, or are they independent?
> 2. Do you use TTL synchronization pulses? If so, which system generates them
>    and which systems record them?
> 3. What channel carries the sync signal?

Refer to nwb-convert Phase 4 for the complete set of patterns (shared clock, TTL
alignment, `set_aligned_starting_time`, `align_by_interpolation`).

### What to Record

Update `spyglass_notes.md`:

```markdown
## Synchronization
- Reference clock: SpikeGLX neural recording
- Behavior → Neural: TTL on NIDQ channel XA0, rising edge = epoch start
- Video → Neural: frame trigger on NIDQ channel XA1

### Sync Implementation Plan
Override `temporally_align_data_interfaces()` in the NWBConverter:
1. Read NIDQ channel XA0
2. Find rising edges → neural epoch times
3. Compare with behavioral event times → compute offset
4. `self.data_interface_objects["Behavior"].set_aligned_starting_time(offset)`
```

### Push Phase 5 Results

```bash
git add spyglass_notes.md
git commit -m "Phase 5: synchronization plan documented"
```
