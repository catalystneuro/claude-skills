# Anatomical Localization — ndx-anatomical-localization Patterns

Construction patterns using `ndx-anatomical-localization` (v0.1.0+).
Standardized storage of anatomical coordinates for electrodes and imaging planes
against reference atlases (e.g., Allen CCFv3).

## Installation

```bash
uv pip install ndx-anatomical-localization
```

## Overview

| Type | Purpose |
|------|---------|
| `Localization` | LabMetaData container (fixed name `localization`) |
| `Space` | Custom coordinate system (origin, units, orientation, optional extent) |
| `AllenCCFv3Space` | Allen Mouse Brain CCFv3 (PIR, um) |
| `D99v2Space`, `NMTv2Space`, `NMTv2AsymmetricSpace`, `MEBRAINSSpace` | Macaque atlases (RAS, mm) |
| `AnatomicalCoordinatesTable` | Coordinates for rows of another table (e.g., electrodes) |
| `AnatomicalCoordinatesImage` | Per-pixel coordinates for a reference image of an imaging series or histology |
| `BrainRegionMasks` | Per-pixel atlas region IDs (`x`, `y`, `brain_region_id`) |
| `AtlasRegistration` (with `Landmarks`, `AffineTransformation`) | LabMetaData recording how a FOV was registered to an atlas |

Use a predefined atlas space when one matches; define a custom `Space` only for other coordinate systems.

## AllenCCFv3Space

```python
from ndx_anatomical_localization import AllenCCFv3Space

ccf_space = AllenCCFv3Space()
# Fixed: orientation "PIR" (+x posterior, +y inferior, +z right), units "um", origin at the ASL corner of the volume.
```

Bregma is approximately at (5400, 0, 5700) um in CCFv3 coordinates.

## Custom Space

For coordinate systems without a predefined space (e.g., bregma-relative):

```python
from ndx_anatomical_localization import Space

space = Space(
    name="BregmaSpace",
    space_name="BregmaSpace",
    origin="bregma",
    units="um",
    orientation="RAS",  # positive x=Right, y=Anterior, z=Superior
)
```

**Orientation codes** — 3-letter string, one from each pair:
- A/P (Anterior/Posterior)
- L/R (Left/Right)
- S/I (Superior/Inferior)

Examples: `"RAS"`, `"PIR"`, `"LPI"`

## Electrode Localization (AnatomicalCoordinatesTable)

The primary use case — localizing electrodes to atlas coordinates:

```python
from ndx_anatomical_localization import (
    AnatomicalCoordinatesTable,
    AllenCCFv3Space,
    Localization,
)

# 1. Create Localization container
localization = Localization()
nwbfile.add_lab_meta_data([localization])

# 2. Add coordinate space
ccf_space = AllenCCFv3Space()
localization.add_spaces([ccf_space])

# 3. Create coordinates table referencing the electrodes table
coords = AnatomicalCoordinatesTable(
    name="AllenCCFv3Coordinates",
    target=nwbfile.electrodes,
    description="Electrode locations in Allen CCFv3",
    method="SHARP-Track 1.0",
    space=ccf_space,
)

# 4. Add one row per electrode
for i in range(len(nwbfile.electrodes)):
    coords.add_row(
        x=ccf_x[i],           # AP coordinate in um
        y=ccf_y[i],           # DV coordinate in um
        z=ccf_z[i],           # ML coordinate in um
        brain_region="CA1",   # optional
        localized_entity=i,   # index into electrodes table
    )

localization.add_anatomical_coordinates_tables([coords])
```

### Partial Localization

Not all electrodes need coordinates — only add rows for localized ones:

```python
for electrode_id in [0, 2, 5, 8]:  # only 4 of 16 electrodes
    coords.add_row(
        x=ccf_x[electrode_id],
        y=ccf_y[electrode_id],
        z=ccf_z[electrode_id],
        brain_region=regions[electrode_id],
        localized_entity=electrode_id,
    )
```

## Imaging Field of View Registration (AnatomicalCoordinatesImage)

Maps each pixel of a reference image (e.g., the mean projection of an imaging series, or a
histology section) to atlas coordinates. The `Image` must itself be added to the file, for example
inside an `Images` container.

```python
from pynwb.base import Images
from pynwb.image import GrayscaleImage
from ndx_anatomical_localization import AnatomicalCoordinatesImage

mean_image = GrayscaleImage(name="mean_image", data=mean_projection, description="Mean projection of the FOV")
nwbfile.add_acquisition(Images(name="reference_images", images=[mean_image], description="Registration reference images"))

image_coords = AnatomicalCoordinatesImage(
    name="ImagingPlaneLocalization",
    description="FOV registered to Allen CCFv3",
    image=mean_image,                      # required: the image the coordinate map is defined on
    localized_entity=two_photon_series,    # optional: OnePhotonSeries or TwoPhotonSeries the map applies to
    method="manual registration",
    space=ccf_space,
    x=x_grid, y=y_grid, z=z_grid,          # same shape as mean_image.data
    brain_region=region_labels,            # optional, same shape
)
localization.add_anatomical_coordinates_images([image_coords])
```

For histology, omit `localized_entity`.

## Multiple Localizations

Store multiple localizations (different methods, different spaces) in one file:

```python
localization = Localization()
nwbfile.add_lab_meta_data([localization])

ccf_space = AllenCCFv3Space()
bregma_space = Space(name="Bregma", space_name="Bregma",
                     origin="bregma", units="um", orientation="RAS")
localization.add_spaces([ccf_space, bregma_space])

# Manual annotation in bregma coordinates
manual = AnatomicalCoordinatesTable(
    name="ManualLocalization",
    target=nwbfile.electrodes,
    description="Manual bregma-relative electrode locations",
    method="manual annotation",
    space=bregma_space,
)

# Automated registration to CCF
automated = AnatomicalCoordinatesTable(
    name="SHARPTrackLocalization",
    target=nwbfile.electrodes,
    description="SHARP-Track CCF electrode locations",
    method="SHARP-Track 2.0",
    space=ccf_space,
)

# ... add rows to each ...

localization.add_anatomical_coordinates_tables([manual, automated])
```

## Reading Back

```python
from pynwb import NWBHDF5IO

with NWBHDF5IO("data.nwb", "r", load_namespaces=True) as io:
    nwbfile = io.read()
    localization = nwbfile.lab_meta_data["localization"]
    coords = localization.anatomical_coordinates_tables["AllenCCFv3Coordinates"]

    x = coords["x"].data[:]
    y = coords["y"].data[:]
    z = coords["z"].data[:]
    regions = coords["brain_region"].data[:]
    electrode_ids = coords["localized_entity"].data[:]
```

## Notes

- `method` should describe the registration tool/approach (e.g., "SHARP-Track 1.0",
  "manual annotation", "Pinpoint", "brainreg").
- `brain_region` is optional but recommended — use Allen Brain Atlas ontology terms.
