# nwb-convert

nwb-convert is a Claude Code skill that leads a conversation to convert neurophysiology data to [NWB](https://www.nwb.org/) and publish it on the [DANDI Archive](https://dandiarchive.org/). It is written for lab experimentalists and produces a documented, pip-installable conversion repository built on [NeuroConv](https://neuroconv.readthedocs.io/) and [PyNWB](https://pynwb.readthedocs.io/).

## Usage

```
/nwb-convert /path/to/your/data
```

The argument can also be a Google Drive folder URL or an existing conversion repository.

## Phases

1. Intake: data modalities, recording systems, and file organization
2. Data inspection: formats, channels, and structure of the source files
3. Metadata: subject, session, devices, and electrodes
4. Synchronization: temporal alignment across data streams
5. Code generation: a conversion repository using NeuroConv
6. Ontology annotation: NCBITaxon, RRID, Allen atlases, UBERON, ROR, ORCID, and HED
7. Testing: convert sessions and validate them with NWB Inspector
8. Local notebooks: review and demo notebooks for the converted files
9. DANDI upload
10. Dandiset metadata, using the `dandiset-metadata` skill from [dandi/dandi-skills](https://github.com/dandi/dandi-skills), installed separately
11. Example notebook: a streaming notebook submitted to [dandi/example-notebooks](https://github.com/dandi/example-notebooks)

The `knowledge/` folder holds reference material the skill reads when a phase calls for it: a NeuroConv interface catalog, past CatalystNeuro conversion patterns, NWB extension guides, PyNWB guides, NWB best practices, and ontology resources.

## What the skill runs and connects to

The skill asks Claude to run commands on your machine as part of the conversion. Depending on the phase, it may:

- Read your source data files and write a new conversion repository with Python code, tests, and notebooks.
- Install Python packages (NeuroConv, PyNWB, NWB Inspector, the DANDI CLI) into a project environment, and install `uv` from astral.sh if it is missing.
- Mount a Google Drive folder read-only with rclone, if you give it a Drive URL.
- Fetch paper text and metadata from NCBI (PubMed, PMC) and Europe PMC with `tools/fetch_paper.py`, when you give it a DOI, PMID, or PMC ID.
- Look up ontology and registry terms (bioregistry.io, OBO PURLs, SciCrunch RRIDs, ROR, ORCID).
- Push commits to the conversion repository's git remote, if one is configured.
- Upload NWB files to the DANDI Archive or the DANDI sandbox, after you confirm which one and provide your own DANDI API key.
- Fork dandi/example-notebooks and open a pull request there with the GitHub CLI, using your own GitHub login.

The skill does not send data anywhere else, and it stores no credentials of its own. `tools/update_neuroconv_interfaces.py` is a maintainer script that refreshes the interface catalog from the installed NeuroConv and runs only when invoked by hand.

## License

MIT. See [LICENSE](LICENSE).
