# Converter Patterns

How CatalystNeuro conversion repos combine interfaces, and how to read common source files in custom
interfaces. The file templates are in `knowledge/repo-structure.md`.

## Pattern 1: Standard NeuroConv Pipeline (Most Common)

**Used by**: wen22, cai-lab, turner-lab, constantinople-lab, most modern repos

```python
class MyNWBConverter(NWBConverter):
    data_interface_classes = dict(
        Recording=SpikeGLXRecordingInterface,
        LFP=SpikeGLXRecordingInterface,  # source_data["LFP"] = dict(folder_path=..., stream_id="imec0.lf")
        Sorting=PhySortingInterface,
        Behavior=CustomBehaviorInterface,
    )
```

Key characteristics:
- NWBConverter subclass with `data_interface_classes` dict
- Mix of built-in NeuroConv interfaces and custom ones
- `convert_session.py` builds source_data and conversion_options dicts
- Metadata layered: auto-extracted → YAML → programmatic overrides

## Pattern 2: ConverterPipe with Dynamic Interfaces

**Used by**: ibl-to-nwb, turner-lab (some conversions)

```python
from neuroconv import ConverterPipe

interfaces = []
interfaces.append(SpikeGLXRecordingInterface(folder_path=path, stream_id="imec0.ap"))
if sorting_exists:
    interfaces.append(PhySortingInterface(folder_path=phy_path))
converter = ConverterPipe(data_interfaces=interfaces)
```

Used when:
- Interfaces need custom initialization (API clients, non-file sources)
- Session-dependent interface sets (not all sessions have all data)
- Pre-constructed interface instances needed

## Pattern 3: Raw PyNWB (Legacy / Highly Custom)

**Used by**: giocomo legacy, mallory21 freely-moving, older repos

```python
nwbfile = NWBFile(session_description=..., ...)
# Manually create PyNWB objects
position = Position(spatial_series=SpatialSeries(...))
nwbfile.create_processing_module("behavior").add(position)
with NWBHDF5IO(path, "w") as io:
    io.write(nwbfile)
```

Used when:
- Data is in highly processed/custom format (e.g., all-in-one .mat file)
- No NeuroConv interface exists and writing one isn't worth it
- Legacy code predating NeuroConv

## Pattern 4: Hybrid (NWBConverter + Direct PyNWB)

**Used by**: reimer-arenkiel-lab (DataJoint + TIFF)

Standalone functions add some data directly to an in-memory NWBFile, then the
NWBConverter adds its data streams to that file and writes it:

```python
from neuroconv.tools.nwb_helpers import make_nwbfile_from_metadata

converter = MyConverter(source_data=source_data)
nwbfile = make_nwbfile_from_metadata(metadata=metadata)
# Add more data directly
add_trials_from_database(nwbfile, session_key)
add_behavior_from_database(nwbfile, session_key)
# run_conversion validates metadata, aligns interfaces, adds their data, and writes
converter.run_conversion(nwbfile=nwbfile, nwbfile_path=nwbfile_path, metadata=metadata, overwrite=True)
```

## Reading Source Files in Custom Interfaces

### Reading MATLAB .mat files

```python
# For older MATLAB files (v5/v6)
from scipy.io import loadmat
mat = loadmat(file_path)
data = mat["variable_name"]

# More robust alternative to scipy.io.loadmat (handles more MATLAB types)
# pip install pymatreader
from pymatreader import read_mat
mat = read_mat(file_path)
data = mat["variable_name"]

# For MATLAB tables and strings that scipy and pymatreader cannot read
# pip install mat-io
from matio import load_from_mat
mat = load_from_mat(file_path)
data = mat["variable_name"]

# For MATLAB v7.3+ (HDF5-based) — use when the above fail
import h5py
with h5py.File(file_path, "r") as f:
    data = f["variable_name"][:]

# For MATLAB v7.3 with complex nested structures
import hdf5storage
mat = hdf5storage.loadmat(file_path)
```

### Reading text/CSV behavior files

```python
import pandas as pd
# Tab-separated with no header
df = pd.read_csv(file_path, sep="\t", header=None,
                 names=["timestamp", "position", "extra1", "extra2"])

# Or numpy for simple numeric files
import numpy as np
data = np.loadtxt(file_path)
```

### Reading pickled DataFrames

```python
import pickle
with open(file_path, "rb") as f:
    data = pickle.load(f)
df = data["VR_Data"]  # or whatever key
```

**Pickle compatibility**: Pickles saved with older pandas versions may fail to load with
pandas >= 2.0 because `pandas.core.indexes.numeric` was removed. If you encounter
`ModuleNotFoundError: No module named 'pandas.core.indexes.numeric'`:
1. First try loading normally
2. If it fails, the user may need `pandas < 2.0` or to re-save the pickle with a newer version
3. Flag this to the user as a data compatibility issue — it is NOT a bug in the conversion code
