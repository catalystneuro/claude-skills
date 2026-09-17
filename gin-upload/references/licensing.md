# Licensing

Record the license and access terms during discovery. A candidate that cannot
be redistributed may still inform the format analysis or be tested locally
when permitted, but it must not be published until redistribution rights and
required notices are clear.

All three repositories use the same two-part license, stated in their READMEs:

- The collection as a whole: the Open Database License (ODbL 1.0).
- The individual files: CC BY-SA 4.0. The READMEs call this the "Database
  Contents License", but the link goes to CC BY-SA 4.0, which is a different
  license.

Files under CC0 or CC BY need no license file in their folder. For every
license, follow this guidance:

- CC0 or public domain: no license file. State it in the provenance line.
- CC BY 4.0 or CC BY-SA 4.0: no license file. Name the authors and the license
  in the provenance line.
- MIT, BSD or Apache 2.0: copy the source's license text into a `LICENSE` file
  in the dataset folder, since these licenses require their notice to travel
  with the files. For Apache 2.0, also copy the source's `NOTICE` file if it has
  one, and describe your changes in the provenance line.
- GPL: copy the license text into a `LICENSE` file in the dataset folder. The
  files stay under the GPL and cannot be relicensed as CC BY-SA.
- Non-commercial (NC), no-derivatives (ND), or no license at all: do not add
  the files. Ask the authors for permission, or generate synthetic data.

When in doubt, generate a new synthetic file that reproduces only the format's
functional structure. Do not retain original measurements, identifiers, free
text, images, or other source-specific content.
