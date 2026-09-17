# Stubbing data

Keep the data as small as possible while preserving consistency. Apply the
repository's size limit to the whole acquisition-system or algorithm folder,
not to each file. This matters most for formats with many small files or many
variations, where the total grows quickly.

If you have the acquisition system, or can run the algorithm, the simplest
option is to record a short, bare-bones session aimed exactly at the purpose.
Otherwise, stub existing data by:

- Reducing the number of samples.
- Removing superfluous structure that does not matter for the example.
- Reducing the number of time series, channels, trials, units or subjects.
- Cropping the spatial dimensions of images or movies, such as a frame cut to
  its top-left corner or to fewer pixels per line.

When no publishable file exists for a format, generate a synthetic one instead:
read the layout from a real file at run time, so the structure cannot drift,
fill the arrays with generated values, and replace subjects, dates,
identifiers and paths with placeholders.

When doing this, it is paramount to keep the file consistent and as faithful
to the original as possible. For example, if you cut samples, set any metadata
field that holds the number of samples to the new value. If one structure of
the data depends on another, such as a synchronization table that maps samples
to video frames, or event times that index into the signal, modify them
together.

## Human data

For human subject data, default to creating synthetic copies. Use an original
only when it is already published under an open license by a source that states
it is de-identified, or when the data owner authorizes this specific
publication. Whoever runs this skill cannot give that authorization on the
participants' behalf, so ask them, and ask the repository maintainers as well.

De-identification is not automatic. Check what the format stores besides the
signal: name, birth date, sex and identifier fields in the header, recording
dates, hospital or device identifiers, technician names, and embedded file
paths. When in doubt, generate synthetic data.

To generate synthetic data, use the original file as the structure, fill all
the data with generated values, and fill every metadata attribute with a
sensible but anonymous placeholder, for example `patient_name: "X"`,
`birth_date: 1900-01-01`, `sex: "unknown"`, `recording_location: "X"`. Where
the format defines its own value for unknown fields, use them explicitly (e.g.
EDF+ uses `X`).
