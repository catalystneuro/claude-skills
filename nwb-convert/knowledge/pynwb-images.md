# Images — PyNWB Patterns

Patterns for static images and video references in NWB files.

## Static Images

```python
from pynwb.image import GrayscaleImage, RGBImage, Images
from neuroconv.tools.nwb_helpers import get_module

# Summary images from segmentation (e.g., mean projection) are derived data:
# group them in an Images container named "SegmentationImages" in processing["ophys"]
mean_img = GrayscaleImage(
    name="mean_projection",
    data=mean_array,             # shape: (height, width), dtype float or uint
    description="Mean fluorescence projection",
)
segmentation_images = Images(
    name="SegmentationImages",
    images=[mean_img],
    description="Summary images from segmentation",
)
ophys_module = get_module(nwbfile, "ophys", "Optical physiology data")
ophys_module.add(segmentation_images)

# Raw images acquired for this session (e.g., histology) go in acquisition
histology = RGBImage(
    name="histology",
    data=rgb_array,              # shape: (height, width, 3)
    description="Post-hoc histology image",
)
histology_images = Images(
    name="histology_images",
    images=[histology],
    description="Histology images for this session",
)
nwbfile.add_acquisition(histology_images)
```

## ImageSeries — External Video Files

For behavioral videos, use `external_file` to reference videos alongside the NWB file.
This avoids re-encoding video data and preserves the original codec.
Prefer NeuroConv's `ExternalVideoInterface`, which builds this `ImageSeries` and reads the
frame counts for `num_samples` and `starting_frame`. Write it by hand only when the interface does not fit.

```python
from pynwb.image import ImageSeries

video = ImageSeries(
    name="behavior_video",
    description="Side-view behavioral camera",
    external_file=["./videos/session01_cam1.avi"],  # relative to the NWB file
    rate=30.0,
    num_samples=n_frames,        # total frames across all external files
    unit="n.a.",
)
nwbfile.add_acquisition(video)
```

## Notes

- Use **relative paths** for `external_file` so the NWB file remains portable.
- `num_samples` is required when timing an external video with `rate`; with `timestamps` it is not.
- `format` is set to `"external"` automatically. For a single file, `starting_frame` defaults to `[0]`.
  For several files, pass `starting_frame` with one entry per file: the index of each file's first
  frame in the full series.
- For neural imaging data (two-photon, miniscope), store data **inside** the NWB file
  using `TwoPhotonSeries`/`OnePhotonSeries`, not as external files.
- `GrayscaleImage` expects 2D arrays; `RGBImage` expects 3D with last dim = 3.
