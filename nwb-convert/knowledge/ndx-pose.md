# Pose Estimation — ndx-pose Patterns

Construction patterns for `ndx-pose` 0.4.x (requires pynwb>=4).
Use this for pose estimation data from DeepLabCut, SLEAP, Lightning Pose, etc.

## Installation

```bash
uv pip install "ndx-pose>=0.4.0"
```

## Overview

The extension defines:
- **Skeleton**: body part nodes and their connections (edges)
- **PoseEstimationSeries**: per-keypoint x,y(,z) positions + confidence over time
- **PoseEstimation**: container grouping all keypoints from one camera view
- **MultiCameraPoseEstimation**: 3D world-space keypoints plus one `PoseEstimation` per camera
- **CalibratedCamera**: a `Device` with camera intrinsics and extrinsics
- **PoseTraining**: optional training data (annotated frames, ground truth)

## NeuroConv Integration

NeuroConv has built-in interfaces for the major pose estimation tools:
- `DeepLabCutInterface` — reads DLC `.h5` or `.csv` output
- `SLEAPInterface` — reads SLEAP `.slp` or `.nwb` output
- `LightningPoseInterface` — reads Lightning Pose output

**Prefer NeuroConv interfaces when available.** Only use raw ndx-pose construction
when data is in a custom format not supported by NeuroConv.

## Complete Example

```python
import numpy as np
from ndx_pose import Skeleton, Skeletons, PoseEstimationSeries, PoseEstimation
from neuroconv.tools.nwb_helpers import get_module
from pynwb.device import DeviceModel
from pynwb.image import ImageSeries

# 1. Camera and source video. The device must be in the NWBFile before PoseEstimation links it.
camera_model = DeviceModel(
    name="acA1300",
    manufacturer="Basler",
    model_number="acA1300-200um",
    description="Basler ace USB 3.0 monochrome camera",
)
nwbfile.add_device_model(camera_model)
camera = nwbfile.create_device(name="BehaviorCamera", description="Side-view camera", model=camera_model)

n_frames = 1000
video = ImageSeries(
    name="BehaviorVideo",
    description="Raw behavior video",
    unit="n.a.",
    format="external",
    external_file=["behavior_video.mp4"],  # path relative to the NWB file
    starting_frame=[0],
    rate=30.0,
    num_samples=n_frames,
    dimension=[640, 480],                  # width, height in pixels
    device=camera,
)
nwbfile.add_acquisition(video)

# 2. Skeleton: node order defines the indices used in edges (Nx2 uint8, 0-indexed)
skeleton = Skeleton(
    name="mouse_skeleton",
    nodes=["nose", "body", "tail_base"],
    edges=np.array([[0, 1], [1, 2]], dtype="uint8"),
    subject=nwbfile.subject,  # optional
)

# 3. One PoseEstimationSeries per keypoint; later series reuse the first one's timestamps
series_list = []
for node in skeleton.nodes:
    series_list.append(
        PoseEstimationSeries(
            name=node,
            description=f"Position of {node} tracked by DeepLabCut",
            data=xy[node],                 # (n_frames, 2) for 2D or (n_frames, 3) for 3D
            unit="pixels",
            reference_frame="(0,0) is the top-left corner of the video frame",
            timestamps=frame_timestamps if not series_list else series_list[0],  # measured frame times (s)
            confidence=likelihood[node],   # (n_frames,), optional
            confidence_definition="DeepLabCut likelihood",
        )
    )

# 4. Container for one camera view
pose_estimation = PoseEstimation(
    name="PoseEstimation",
    pose_estimation_series=series_list,
    description="Pose estimation of freely moving mouse",
    device=camera,
    source_video=video,                    # optional; labeled_video= links an ImageSeries of the labeled video
    scorer="DLC_resnet50_openfieldOct30shuffle1_1600",
    source_software="DeepLabCut",
    source_software_version="2.3.8",       # requires source_software
    skeleton=skeleton,
)

behavior = get_module(nwbfile, "behavior", "Processed behavioral data")
behavior.add(Skeletons(skeletons=[skeleton]))
behavior.add(pose_estimation)
```

## Multi-Camera / Multi-View

For independent 2D tracking in each view, create one `PoseEstimation` per camera, each with its
own `device=` and `source_video=`, and give them distinct names (e.g. `PoseEstimation_side`, `PoseEstimation_top`).

For triangulated 3D poses (Anipose, DANNCE), use `MultiCameraPoseEstimation`. It holds the
world-space `PoseEstimationSeries` and one `PoseEstimation` per camera view, which links that
camera's device and video and may hold its 2D keypoints. Store each camera's calibration in a
`CalibratedCamera` device.

```python
from ndx_pose import CalibratedCamera, MultiCameraPoseEstimation

per_camera = []
for camera_name, video in zip(["camera1", "camera2"], [video1, video2]):
    camera = CalibratedCamera(
        name=camera_name,
        description=f"{camera_name} of the calibrated rig",
        model=camera_model,
        intrinsic_matrix=intrinsics[camera_name],         # (3, 3)
        rotation_matrix=rotations[camera_name],           # (3, 3), optional
        translation_vector=translations[camera_name],     # (3,), optional
        distortion_coefficients=distortions[camera_name], # (N,), optional
    )
    nwbfile.add_device(camera)
    per_camera.append(
        PoseEstimation(
            name=f"PoseEstimation_{camera_name}",
            description=f"2D keypoints from {camera_name}",
            pose_estimation_series=series_2d[camera_name],  # omit if the tool outputs no 2D keypoints
            device=camera,
            source_video=video,
            skeleton=skeleton,
        )
    )

multi_camera = MultiCameraPoseEstimation(
    name="MultiCameraPoseEstimation",
    pose_estimation_series=series_3d,  # (n_frames, 3) world-space PoseEstimationSeries, e.g. unit="millimeters"
    pose_estimations=per_camera,
    description="3D keypoints triangulated by Anipose",
    source_software="Anipose",
    source_software_version="1.1.4",
    skeleton=skeleton,
)
behavior.add(multi_camera)
```

## Notes

- **One subject per NWB file.** For multi-animal tracking, create separate NWB files.
- `confidence` is optional (since v0.2.0) but recommended when available.
- `unit` is typically `"pixels"` for 2D video tracking. Use `"meters"` if coordinates
  have been calibrated to real-world units.
- Training data (`PoseTraining`) is rarely needed in conversion workflows — it's mainly
  for sharing annotated datasets used to train models.
