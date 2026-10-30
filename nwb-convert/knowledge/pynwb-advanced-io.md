# Large Data and Storage Settings

In a NeuroConv conversion, pass plain arrays (or a lazy iterator for data larger than memory) to PyNWB
objects. `run_conversion` chunks and compresses every dataset (gzip by default) for both `backend="hdf5"`
and `backend="zarr"`. Do not wrap data in `H5DataIO`: NeuroConv skips any dataset already wrapped in a
`DataIO` when it builds the backend configuration, so the dataset gets HDF5's default chunking, ignores
any `backend_configuration` edits, and loses its compression settings under `backend="zarr"`.

## Data larger than memory

If the data fits in memory, pass the array. Otherwise wrap a sliceable source (a `np.memmap`,
`h5py.Dataset`, or zarr array) in NeuroConv's iterator, which reads one buffer at a time during write:

```python
import numpy as np
from neuroconv.tools.hdmf import SliceableDataChunkIterator

traces = np.load(file_path, mmap_mode="r")             # shape (n_samples, n_channels)
data = SliceableDataChunkIterator(data=traces)         # optional: buffer_gb=..., chunk_mb=...
nwbfile.add_acquisition(TimeSeries(name="traces", description="...", data=data, rate=30_000.0, unit="V"))
```

For a source that cannot be sliced directly, subclass `neuroconv.tools.hdmf.GenericDataChunkIterator`
and implement `_get_data(selection)`, `_get_maxshape()`, and `_get_dtype()`.

## Changing chunking or compression

Build the in-memory file, edit the default configuration, and write it. `run_conversion` does not accept
`backend_configuration` together with `nwbfile`, so write with `configure_and_write_nwbfile`:

```python
from neuroconv.tools.nwb_helpers import configure_and_write_nwbfile

nwbfile = converter.create_nwbfile(metadata=metadata, conversion_options=conversion_options)
backend_configuration = converter.get_default_backend_configuration(nwbfile=nwbfile, backend="hdf5")
print(backend_configuration)                           # every dataset with its chunk shape and compressors

dataset_configuration = backend_configuration.dataset_configurations["acquisition/traces/data"]
dataset_configuration.chunk_shape = (30_000, 1)        # must evenly divide buffer_shape
dataset_configuration.buffer_shape = (60_000, 16)
dataset_configuration.compressors = ["gzip"]
dataset_configuration.compressor_options = [{"level": 9}]

configure_and_write_nwbfile(
    nwbfile=nwbfile, nwbfile_path=nwbfile_path, backend_configuration=backend_configuration
)
```

Pick a chunk shape that matches the common read pattern, for example one frame per chunk for imaging
(`(1, height, width)`). `backend="zarr"` writes NWB-Zarr with the same configuration API.
