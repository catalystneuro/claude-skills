# Reading Source Files

Readers for lab-specific files that no NeuroConv interface reads: MATLAB, text, and pickle files. Phase 2 uses
them to inspect the files, and custom interfaces (`knowledge/conversion-patterns.md`) use them to read the data.

## MATLAB .mat files

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

## Text and CSV files

Check the delimiter (tab, comma, or space), whether there is a header row, and the encoding.

```python
import pandas as pd
# Tab-separated with no header
df = pd.read_csv(file_path, sep="\t", header=None,
                 names=["timestamp", "position", "extra1", "extra2"])

# Or numpy for simple numeric files
import numpy as np
data = np.loadtxt(file_path)
```

## Pickled DataFrames

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
