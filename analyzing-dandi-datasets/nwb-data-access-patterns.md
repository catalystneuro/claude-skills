# NWB Data Access Patterns

This file contains code examples for loading NWB (Neurodata Without Borders) files from the DANDI Archive using different streaming access methods.

IMPORTANT: Use the neurosift-tool MCP tool nwb_file_info to learn how to access data from an NWB file on DANDI.

## Using LINDI (Preferred for .lindi.json files)

LINDI provides efficient streaming access to NWB files with local caching. Use this method when you have a `.lindi.json` file reference.

```python
import h5py
from pynwb import NWBHDF5IO
import lindi
import pynapple as nap

# Create a local cache to store downloaded chunks
local_cache = lindi.LocalCache()

# Load a LINDI file with caching enabled
# Replace with your actual .lindi.json file path or URL
lindi_file_path = 'path/to/file.nwb.lindi.json'
f = lindi.LindiH5pyFile.from_lindi_file(lindi_file_path, local_cache=local_cache)

# Open with PyNWB
io = NWBHDF5IO(file=f)
nwbfile = io.read()

# Load into Pynapple for analysis
nwb = nap.NWBFile(nwbfile)
print(nwb)  # This will show you the structure of available data
```

**When to use LINDI**:
- You have a `.lindi.json` reference file from DANDI
- You want efficient access to specific parts of large NWB files
- You're working with datasets that have LINDI references published

## Using remfile (For Direct S3 URLs)

Remfile provides direct streaming access from S3 URLs with disk caching.

```python
import h5py
from pynwb import NWBHDF5IO
import remfile
import pynapple as nap

# Create a disk cache to store downloaded chunks
cache_dirname = '/tmp/remfile_cache'
disk_cache = remfile.DiskCache(cache_dirname)

# Replace with your actual S3 URL from DANDI
s3_url = 'https://dandiarchive.s3.amazonaws.com/...'

# Open the file from S3 with caching
rem_file = remfile.File(s3_url, disk_cache=disk_cache)
h5py_file = h5py.File(rem_file, "r")

# Open with PyNWB
io = NWBHDF5IO(file=h5py_file)
nwbfile = io.read()

# Load into Pynapple for analysis
nwb = nap.NWBFile(nwbfile)
print(nwb)  # This will show you the structure of available data
```

**When to use remfile**:
- You have a direct S3 URL to an NWB file
- The dataset doesn't have a LINDI reference
- You're accessing DANDI datasets via their direct asset URLs

## Inspecting NWB Structure

After loading an NWB file with Pynapple, you can inspect its contents:

```python
# Print the overall structure
print(nwb)

# Access specific data types
if hasattr(nwb, 'units'):
    print(f"Number of units: {len(nwb.units)}")
    print(f"Units data: {nwb.units}")

if hasattr(nwb, 'trials'):
    print(f"Number of trials: {len(nwb.trials)}")
    print(f"Trial columns: {nwb.trials.keys()}")

if hasattr(nwb, 'position'):
    print(f"Position data: {nwb.position}")

# Access spike times
if hasattr(nwb, 'units'):
    # Get spike times for all units as a TsGroup
    spike_times = nwb.units
    print(f"Spike times: {spike_times}")
```

## Common Data Access Patterns

### Accessing Spike Times

```python
# Get all units as a Pynapple TsGroup
units = nwb.units

# Get spike times for a specific unit
unit_id = 0
spike_times_unit_0 = units[unit_id]

# Iterate through all units
for unit_id, spike_train in units.items():
    print(f"Unit {unit_id}: {len(spike_train)} spikes")
```

### Accessing Trials/Behavioral Data

```python
# Get trial information as a Pynapple IntervalSet
trials = nwb.trials

# Access trial-specific information
if 'start_time' in trials.columns:
    start_times = trials['start_time']

if 'stop_time' in trials.columns:
    stop_times = trials['stop_time']

# Access custom trial columns (e.g., reach direction, target location)
# Column names vary by dataset - inspect with trials.keys()
if 'reach_direction' in trials.columns:
    reach_directions = trials['reach_direction']
```

## Handling Missing Data

Not all NWB files contain the same data types. Always check before accessing:

```python
# Check for spike data
if not hasattr(nwb, 'units'):
    print("Warning: No units (spike data) found in this NWB file")
    # Consider searching for a different dataset

# Check for trial structure
if not hasattr(nwb, 'trials'):
    print("Warning: No trial information found")

# Check for specific trial columns
if hasattr(nwb, 'trials'):
    required_columns = ['start_time', 'stop_time', 'target_direction']
    missing = [col for col in required_columns if col not in nwb.trials.columns]
    if missing:
        print(f"Warning: Missing trial columns: {missing}")
        print(f"Available columns: {list(nwb.trials.keys())}")
```

## Multi-Session Loading

### Getting All Sessions from a Dandiset

```python
from dandi.dandiapi import DandiAPIClient

def get_all_nwb_urls(dandiset_id):
    """Get URLs for all NWB files in a dandiset."""
    client = DandiAPIClient()
    dandiset = client.get_dandiset(dandiset_id)

    nwb_urls = []
    for asset in dandiset.get_assets():
        if asset.path.endswith('.nwb'):
            nwb_urls.append(asset.download_url)

    return nwb_urls

# Load and analyze all sessions
dandiset_id = "000044"
session_urls = get_all_nwb_urls(dandiset_id)
print(f"Found {len(session_urls)} sessions")
```

### Efficient Multi-Session Processing

```python
def process_all_sessions(session_urls, cache_dir='/tmp/nwb_cache'):
    """Process multiple sessions with shared cache."""

    all_results = {}

    for i, url in enumerate(tqdm(session_urls)):
        try:
            # Load with caching
            disk_cache = remfile.DiskCache(cache_dir)
            rem_file = remfile.File(url, disk_cache=disk_cache)
            h5py_file = h5py.File(rem_file, "r")
            io = NWBHDF5IO(file=h5py_file)
            nwbfile = io.read()
            nwb = nap.NWBFile(nwbfile)

            # Run analysis
            result = analyze_single_session(nwb)
            all_results[f"session_{i}"] = result

            # Clean up
            io.close()

        except Exception as e:
            print(f"Error processing session {i}: {e}")
            continue

    return all_results
```

## Best Practices

1. **Start with Inspection**: Always print the NWB object first to see what data is available
2. **Use Caching**: Both LINDI and remfile support caching - use it to speed up repeated access
3. **Let Errors Surface**: Don't wrap data access in try/except during development
4. **Validate Data**: After loading, check for expected data types and structures
5. **Document Assumptions**: Note what data types your analysis requires

## Example Complete Loading Script

```python
import h5py
from pynwb import NWBHDF5IO
import lindi
import pynapple as nap

def load_nwb_from_lindi(lindi_path):
    """Load NWB file using LINDI with caching."""
    local_cache = lindi.LocalCache()
    f = lindi.LindiH5pyFile.from_lindi_file(lindi_path, local_cache=local_cache)
    io = NWBHDF5IO(file=f)
    nwbfile = io.read()
    nwb = nap.NWBFile(nwbfile)
    return nwb, io

# Load the file
nwb, io = load_nwb_from_lindi('path/to/file.nwb.lindi.json')

# Inspect structure
print("=" * 80)
print("NWB File Structure:")
print("=" * 80)
print(nwb)
print()

# Check for required data
print("Data Availability:")
print(f"  - Units (spikes): {hasattr(nwb, 'units')}")
print(f"  - Trials: {hasattr(nwb, 'trials')}")
print(f"  - Position: {hasattr(nwb, 'position')}")
print()

# Access data
if hasattr(nwb, 'units'):
    print(f"Found {len(nwb.units)} units")
    units = nwb.units

if hasattr(nwb, 'trials'):
    print(f"Found {len(nwb.trials)} trials")
    print(f"Trial columns: {list(nwb.trials.keys())}")
```