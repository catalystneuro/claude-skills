# NWB Best Practices

Distilled from the [official NWB Inspector best practices](https://github.com/NeurodataWithoutBorders/nwbinspector/tree/dev/docs/best_practices).
Follow these when generating conversion code. A rule that NWB Inspector checks names its check, so an
Inspector message can be looked up here by its check name.

## Validation

Two tools check converted files.

- **NWB Inspector**, `nwbinspector <file or folder> --config dandi`, runs on any NWB file. Phase 7 runs it on
  every converted file, and Phase 9 runs it on the whole output folder before upload. `--config dandi` applies the
  configuration DANDI uses: it raises the subject checks (`check_subject_exists`, `check_subject_id_exists`,
  `check_subject_id_no_slashes`, `check_subject_sex`, `check_subject_species_exists`, `check_subject_species_form`,
  `check_subject_age`, `check_subject_proper_age_range`) and `check_session_id_no_slashes` to CRITICAL, and lowers
  `check_data_orientation` to BEST_PRACTICE_VIOLATION.
- **`dandi validate`** runs PyNWB validation and NWB Inspector with the DANDI configuration, and checks the file and
  folder names that `dandi organize` produces. ERROR, PYNWB_VALIDATION, and CRITICAL messages are errors. It works
  only inside a Dandiset folder (one with `dandiset.yaml`); elsewhere it fails with `DANDI.NO_DANDISET_FOUND`.
  Phase 9 runs it after `dandi organize`. `dandi upload` runs the same validation on each file and refuses a file
  with errors.

NWB Inspector reports five severity levels:

| Level | Meaning |
|-------|---------|
| `ERROR` | A check crashed on this file, usually because of malformed data |
| `PYNWB_VALIDATION` | The file violates the NWB schema |
| `CRITICAL` | Breaks downstream tools or DANDI upload |
| `BEST_PRACTICE_VIOLATION` | Violates an NWB best practice |
| `BEST_PRACTICE_SUGGESTION` | Could be improved |

## General

- **Object names**: name an object after its neurodata_type (`ElectricalSeries`). When several share a group, add a CamelCase suffix (`ElectricalSeriesAP`, `ElectricalSeriesLF`). Put distinguishing information in `description`, not the name.
- **No `/`, `\`, or `:` in names** (`/` is the HDF5 path separator). Write `DfOverF`, not `Df/f`. (`check_name_slashes`, `check_name_colons`)
- **No empty strings** — every `description`, `unit`, and text field must have meaningful content. Empty strings and placeholder text like "no description" will be flagged. (`check_description`, `check_empty_string_for_optional_attribute`)
- **Avoid metadata duplication** — don't store the same metadata in multiple places. For example, don't add `unit` or `gain` columns to the electrodes table when those belong on `ElectricalSeries`.

## NWBFile Metadata

- **File extension**: `.nwb` (or `.nwb.zarr` for Zarr). (`check_file_extension`)
- **`identifier`**: must be globally unique. Use `str(uuid.uuid4())`.
- **`session_start_time`**: must include timezone info. All other timestamps are relative to this. Take the real date from the source files. (`check_session_start_time_old_date`, `check_session_start_time_future_date`)
- **`timestamps_reference_time`**: defaults to `session_start_time`. Only set explicitly if different.
- **`session_id`**: should be unique across sessions in a dataset. Use a descriptive string, not just a number. No `/`. (`check_session_id_no_slashes`)
- **`session_description`**: required. Describe what happened in this session.
- **`experiment_description`**: describe the scientific goal. Can use the paper abstract. (`check_experiment_description`)
- **`experimenter`**: list of strings in "Last, First" format. (`check_experimenter_exists`, `check_experimenter_form`)
- **`institution`**: name of the institution. (`check_institution`)
- **`keywords`**: list of relevant keywords for discoverability. (`check_keywords`)
- **`related_publications`**: use DOI format: `"doi:10.xxxx/xxxxx"`. (`check_doi_publications`)
- **Acquisition vs. processing**: raw data goes in `nwbfile.acquisition`. Processed/derived data goes in `nwbfile.processing["module_name"]`.
- **Processing module names**: use standard names: `"ecephys"`, `"ophys"`, `"icephys"`, `"behavior"`, `"ogen"`, `"misc"`, `"retinotopy"`. Custom names are allowed but standard names enable tool interoperability. (`check_processing_module_name`)

## Subject

- **Required for DANDI**: `dandi validate` fails on a missing subject, `subject_id`, `sex`, or `species`, on a missing `age` when `date_of_birth` is also missing, and on `/` in `subject_id` or `session_id`. (`check_subject_exists` and the checks named below)
- **`subject_id`**: unique identifier for the animal, without `/`. (`check_subject_id_exists`, `check_subject_id_no_slashes`)
- **`sex`**: one of `"M"`, `"F"`, `"U"` (unknown), `"O"` (other). Single uppercase letter. (`check_subject_sex`)
- **`species`**: Latin binomial (e.g., `"Mus musculus"`) or NCBI taxonomy URI (e.g., `"http://purl.obolibrary.org/obo/NCBITaxon_10090"`). Never use common names like "mouse". (`check_subject_species_exists`, `check_subject_species_form`)
- **`strain`**: the specific strain (e.g., `"C57BL/6J"`). Separate from species.
- **`age`**: ISO 8601 duration: `"P90D"` (90 days), `"P12W"` (12 weeks), `"P3M"` (3 months). For an uncertain age give a range, `"P90D/P120D"`; for a lower bound only, `"P90D/"`. DANDI requires `age` or `date_of_birth`. (`check_subject_age`, `check_subject_proper_age_range`)
- **`date_of_birth`**: preferred over `age` when available (datetime with timezone).
- **`weight`**: `"<number> <unit>"` with unit one of `kg`, `g`, `mg`, `ug`, `ng`, `pg`, e.g., `"0.025 kg"` or `"25 g"`. `dandi validate` fails on any other form. (`check_subject_weight`)

## Time Series

- **Time-first data orientation**: the first dimension of `data` must be time. If your array is `(channels, timepoints)`, transpose it to `(timepoints, channels)`. Timestamps must match the length of the first dimension. (`check_data_orientation`, `check_timestamps_match_first_dimension`)
- **SI units**: `unit` should be SI where possible (meters, seconds, volts, amperes). Use `conversion` parameter instead of transforming data. Every TimeSeries needs a `unit`. (`check_missing_unit`)
- **Timestamps must be in seconds**: all timestamps are in seconds relative to `session_start_time`.
- **Timestamps must be ascending**: timestamps array must be sorted in ascending order. (`check_timestamps_ascending`)
- **No NaN in timestamps**: timestamps must never contain NaN values. (`check_timestamps_without_nans`)
- **Use `rate` + `starting_time` for regular sampling**: if data has a constant sampling rate, set `rate` (Hz) and `starting_time` (seconds) instead of providing a `timestamps` array. This saves space and is more precise. (`check_regular_timestamps`)
- **Avoid negative timestamps**: all timestamps should be >= 0. Negative timestamps imply data before `session_start_time`, which is usually an error. (`check_timestamp_of_the_first_sample_is_not_negative`)
- **Use chunking and compression**: NeuroConv applies both by default. Pass plain arrays, not `H5DataIO`-wrapped data, and change settings through the backend configuration (see `knowledge/pynwb-advanced-io.md`).
- **`resolution`**: set to `-1.0` if unknown. Otherwise, provide the smallest meaningful difference between data values. (`check_resolution`)
- **Rate must be positive and nonzero**: if using `rate`, it must be > 0. (`check_rate_is_not_zero`, `check_rate_is_positive`)
- **Use appropriate TimeSeries subtypes**: don't use bare `TimeSeries` when a more specific type exists (e.g., `ElectricalSeries` for ephys, `SpatialSeries` for position).
- **Breaks in continuity**: if there are gaps in recording, either use separate `TimeSeries` objects or provide explicit `timestamps` (not `rate`) to capture the gaps.

## Tables (DynamicTable)

- **No JSON strings in columns**: if a column value is structured data, use a proper column type (VectorData, DynamicTableRegion, etc.), not a JSON-encoded string. (`check_table_values_for_dict`)
- **No empty tables**: don't create DynamicTable objects with zero rows. (`check_empty_table`)
- **Boolean columns**: store a column with two values as booleans and name it with an `is_` prefix (e.g., `is_correct`, `is_rewarded`). (`check_column_binary_capability`)
- **Timing columns**: name columns containing times with `_time` suffix (e.g., `start_time`, `stop_time`). Use `_times` for ragged arrays of times.
- **Unique IDs**: the `id` column of any DynamicTable should contain unique values. Don't override with non-unique values — use a custom column instead. (`check_ids_unique`)
- **Avoid single-row tables**: if a table has only one row, consider if there's a more appropriate container. (`check_single_row`)

## Extracellular Electrophysiology (ecephys)

- **Electrode `location` is required**: fill with your best estimate of the brain region. For mice, use the Allen CCF full name or acronym (`VISp`, `CA1`, not `V1` or `mPFC`); Inspector checks electrode and `ImagingPlane` locations against the Allen CCF for mouse subjects. If the region is truly unknown, use `"unknown"` and expect that one Inspector warning. (`check_electrodes_location_allen_ccf`)
- **Anatomical coordinates (`x`, `y`, `z`)**: for precise brain coordinates. For mice, use Allen Institute Common Coordinate Framework v3 (+x = posterior, +y = inferior, +z = right).
- **Relative coordinates (`rel_x`, `rel_y`, `rel_z`)**: for electrode position on the probe. Used by spike sorters to determine proximity.
- **Don't duplicate metadata in electrodes table**: don't add `unit`, `gain`, `offset` columns — those belong on `ElectricalSeries` (`channel_conversion`, `offset`).
- **Spike times must be ascending**: within each unit, spike times must be in ascending order. (`check_ascending_spike_times`)
- **Spike times must be positive**: all spike times >= 0. Negative times suggest trial-alignment that should be corrected to session-alignment. (`check_negative_spike_times`)
- **Units `resolution`**: set to `1/sampling_rate` of the acquisition system (e.g., `1/30000`). Inspector flags a missing resolution or one above 0.01 s. (`check_units_resolution_is_set`, `check_units_resolution_is_valid`)
- **Spike times in seconds**: integer-valued spike times are flagged as sample indices, and `dandi validate` fails on them. (`check_spike_times_not_in_samples`)
- **Use `obs_intervals`**: if the recording has gaps where a unit was not observable, set `obs_intervals` on the units table. No spikes should exist outside observed intervals. (`check_spike_times_not_in_unobserved_interval`)

## Optical Physiology (ophys)

- **`image_mask` shape consistency**: the `image_mask` column of `PlaneSegmentation` must have the same shape as `reference_images`. (`check_plane_segmentation_image_mask_shape_against_ref_images`)
- **ImagingPlane required fields**: always set `excitation_lambda`, `indicator`, and `location` on `ImagingPlane`. `location` is an anatomical region (Allen CCF term for mice); put plane depth in `description`. (`check_imaging_plane_location_allen_ccf`)
- **Wavelengths in nm**: `excitation_lambda` and `emission_lambda`. (`check_excitation_lambda_in_nm`, `check_emission_lambda_in_nm`)
- **TwoPhotonSeries rate**: must be nonzero. Get from Suite2p `ops["fs"]` or calculate from timestamps. (`check_rate_is_not_zero`)
- **Store raw imaging data internally**: use chunking + lossless compression (not external file mode).

## Behavior

- **SpatialSeries dimensionality**: must have 1 (x), 2 (x,y), or 3 (x,y,z) columns. Not more. (`check_spatial_series_dims`)
- **SpatialSeries unit**: one of `meters`, `centimeters`, `millimeters`, `micrometers`, `degrees`, `radians`, `pixels`, or `n.a.` (spelled out, not `cm`). (`check_spatial_series_unit`)
- **SpatialSeries is only for position**: velocity, acceleration, and other derived signals should use `TimeSeries` or `BehavioralTimeSeries`, not `SpatialSeries`.
- **CompassDirection units**: must be `"degrees"` or `"radians"`. (`check_compass_direction_unit`)
- **CompassDirection data range**: degrees must be in [-360, 360]; radians in [-2pi, 2pi]. (`check_spatial_series_degrees_magnitude`, `check_spatial_series_radians_magnitude`)

## Image Series

- **External mode for animal videos**: behavioral videos (webcam, etc.) should use `external_file` to reference the video file alongside the NWB file. This allows video-optimized lossy codecs. (`check_image_series_data_size`)
- **Internal storage for neural imaging**: TwoPhotonSeries and similar neural data should be stored inside the NWB file with lossless compression.
- **Relative paths for external files**: `external_file` paths should be relative to the NWB file location. (`check_image_series_external_file_relative`, `check_image_series_external_file_valid`)
- **`starting_frame`**: only set when using `external_file`. Not applicable for internally stored data. (`check_image_series_starting_frame_without_external_file`)

## Optogenetics

- **Every row of `OptogeneticSitesTable` should be referenced** by at least one row of an `OptogeneticEpochsTable` or `OptogeneticPulsesTable` (ndx-optogenetics).

## Extensions

- **Use sparingly**: prefer core NWB types and DynamicTable columns before creating extensions.
- **Check for existing extensions** in the NDX Catalog before creating new ones.
- **Use `ndx-template`** to scaffold new extensions.
- **Cache the spec**: PyNWB caches the extension spec by default; don't pass `cache_spec=False`.
- **Flag for human expert**: the conversion skill should flag when an extension might be needed rather than creating one automatically.
