# Streaming NWB Data from DANDI into Pynapple

## Getting S3 URLs from DANDI

Use the DANDI API client to get the S3 URL for an NWB file:

```python
from dandi.dandiapi import DandiAPIClient

dandiset_id = "000006"
filepath = "sub-anm372795/sub-anm372795_ses-20170718.nwb"

with DandiAPIClient() as client:
    asset = client.get_dandiset(dandiset_id, "draft").get_asset_by_path(filepath)
    s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)
```

## Streaming with remfile (Recommended)

remfile is the recommended method for streaming NWB files from S3. It is simple and fast,
especially for the initial load and for accessing small pieces of data.

```python
import h5py
from pynwb import NWBHDF5IO
import remfile
import pynapple as nap

# Optional disk cache speeds up repeated access
disk_cache = remfile.DiskCache("/tmp/remfile_cache")

# Stream the file from S3
rem_file = remfile.File(s3_url, disk_cache=disk_cache)
with h5py.File(rem_file, "r") as h5py_file:
    with NWBHDF5IO(file=h5py_file, load_namespaces=True) as io:
        nwbfile = io.read()

        # Load into Pynapple
        nwb = nap.NWBFile(nwbfile)
        print(nwb)

        # Access data while IO is open
        spikes = nwb["units"]
        position = nwb["position"]
```

**Important**: Access all data you need while the `NWBHDF5IO` context manager is open.
Data is lazily loaded, so accessing fields after closing the IO will fail.

## Streaming with LINDI (For .lindi.json files)

LINDI provides efficient streaming access when `.lindi.json` reference files are available:

```python
import lindi
from pynwb import NWBHDF5IO
import pynapple as nap

local_cache = lindi.LocalCache()
f = lindi.LindiH5pyFile.from_lindi_file(
    "https://lindi.neurosift.org/dandi/dandisets/000006/assets/.../nwb.lindi.json",
    local_cache=local_cache,
)
io = NWBHDF5IO(file=f)
nwbfile = io.read()
nwb = nap.NWBFile(nwbfile)
print(nwb)
```

## Complete Example: Stream and Analyze

```python
from dandi.dandiapi import DandiAPIClient
import h5py
from pynwb import NWBHDF5IO
import remfile
import pynapple as nap
import numpy as np

# 1. Get S3 URL
dandiset_id = "000582"
filepath = "sub-10073/sub-10073_ses-17010302_behavior+ecephys.nwb"

with DandiAPIClient() as client:
    asset = client.get_dandiset(dandiset_id, "draft").get_asset_by_path(filepath)
    s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)

# 2. Stream with remfile
disk_cache = remfile.DiskCache("/tmp/remfile_cache")
rem_file = remfile.File(s3_url, disk_cache=disk_cache)
h5py_file = h5py.File(rem_file, "r")
io = NWBHDF5IO(file=h5py_file)
nwbfile = io.read()

# 3. Load into Pynapple
nwb = nap.NWBFile(nwbfile)
print(nwb)

# 4. Access and analyze
spikes = nwb["units"]
position = nwb["position"]

wake_ep = nwb["epochs"]["wake"]
spikes_wake = spikes.restrict(wake_ep)
position_wake = position.restrict(wake_ep)

tc = nap.compute_tuning_curves(spikes_wake, position_wake, nb_bins=50)
```

## Listing All NWB Files in a Dandiset

```python
from dandi.dandiapi import DandiAPIClient

def get_nwb_assets(dandiset_id):
    """List all NWB file paths and their S3 URLs in a dandiset."""
    with DandiAPIClient() as client:
        dandiset = client.get_dandiset(dandiset_id)
        assets = []
        for asset in dandiset.get_assets():
            if asset.path.endswith(".nwb"):
                url = asset.get_content_url(follow_redirects=1, strip_query=True)
                assets.append({"path": asset.path, "url": url})
    return assets

assets = get_nwb_assets("000006")
for a in assets:
    print(a["path"])
```

## When to Use Each Method

| Method | When to use |
|--------|------------|
| **remfile** | Direct S3 URLs, general-purpose streaming, fastest initial load |
| **LINDI** | When `.lindi.json` references are available, efficient for large files |
| **`nap.load_file()`** | Local NWB files already downloaded to disk |
