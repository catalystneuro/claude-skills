# Finding example data

Look for several files that differ from one another, not for one file that
works.

To go beyond the data you already have, look for more examples in:

- Code search on GitHub and GitLab: software that reads a format often ships
  real sample files in its test suite.
- Package registries (PyPI, CRAN): released packages bundle sample data that
  can differ from the live repository.
- General data repositories: Zenodo, Dryad, OSF, figshare, Harvard Dataverse and
  institutional Dataverses, Mendeley Data.
- Neuroscience archives: OpenNeuro (EEG, iEEG and MEG files in their native
  formats, such as EDF, BrainVision and EEGLAB).
- Meta-search across repositories: DataCite Commons, Google Dataset Search, and
  re3data.org for domain-specific archives.
- Paper supplementary materials, and the vendor's own forum or knowledge base.

When searching, fan the search out to parallel subagents if your environment
supports it, one per source. For every candidate, record where it is, its
source (DOI or commit), its size and, critically, its license as stated where
the file was deposited.

Collect every genuine candidate whatever its license, and record their
licenses. The goal here is to get enough datasets to understand how the format
varies; the license is used later, to gate the upload.
