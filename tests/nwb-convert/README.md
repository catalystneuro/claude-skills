# Tests for the nwb-convert Skill

These tests cover the ontology annotation phase (`phases/06-ontology-annotation.md` and
`knowledge/external-resources.md`). The code under test is the code in those markdown files.
The fixtures extract the fenced code blocks verbatim, so a change to the documentation is a
change to what is tested, and nothing needs to be kept in sync by hand.

## What Is Tested

`test_external_resources.py` builds a small conversion package laid out the way the skill
prescribes, with the helper and the converter hook copied from the knowledge file, and runs
a NeuroConv conversion through it. The conversion uses NeuroConv's mock recording, imaging,
and pose estimation interfaces, plus `toy_interfaces.py`, which adds an intracellular
electrode, an optogenetic site, a fiber photometry table, and an EMG electrode group. No
source data are needed. The tests check:

- the exact set of references written, across every kind of field the phase covers
- that a value with several terms is not written twice, and that annotated values are unchanged
- HDF5 and Zarr output, a rerun with `overwrite=True`, and `stub_test`
- missing subject, institution, or experimenters, an empty terms file, and empty YAML keys
- the listing script, the checking script, and the Phase 7 snippet
- the standalone HERD across several files
- PyNWB validation, NWB Inspector, and `dandi validate` on an annotated file
- the claims about NeuroConv's built-in support, where the installed NeuroConv has it

`test_lookups.py` runs every `curl` command in the knowledge file against the live
registries, checks the facts the text states about their results, and checks that every URL
in the two files resolves. These depend on third-party services, so they only run with
`--network`.

## Running

```bash
pip install -r tests/nwb-convert/requirements.txt
pytest tests/nwb-convert
pytest tests/nwb-convert --network
```

The tests pass on NeuroConv 0.10.2 and on its development branch, both with PyNWB 4.2.0 and
HDMF 6.2.0. With NeuroConv 0.10.2 the environment also needed `zarr<3` and `hdmf_zarr<0.14`
for NeuroConv to import. The four tests of NeuroConv's built-in support are skipped when the
installed version does not have `neuroconv.tools.external_resources`, and the `dandi validate`
test is skipped when `dandi` is not installed.

Set `SKILL_REPO` to test a different checkout of the repository than the one the tests are in.

## What Is Not Tested Here

Whether an agent can follow the phase is not something these tests can show. That was
checked by giving a fresh agent the two files and a simulated conversion repository, and
reading what it wrote and where it found the instructions unclear.
