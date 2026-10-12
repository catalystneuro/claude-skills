"""Tests of the HERD helper, converter hook, and scripts in nwb-convert/knowledge/external-resources.md."""

import importlib
import importlib.util
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import yaml
from pynwb import NWBHDF5IO

HAS_BUILTIN = importlib.util.find_spec("neuroconv.tools.external_resources") is not None

EXTRA_TERMS = {
    "institution": {"Stanford University": {"id": "ROR:00f54p054", "uri": "https://ror.org/00f54p054"}},
    "experimenter": {
        "Dichter, Benjamin": {"id": "ORCID:0000-0001-5725-6910", "uri": "https://orcid.org/0000-0001-5725-6910"}
    },
    "brain_regions": {
        "VISp": {"id": "MBA:385", "uri": "https://purl.brain-bican.org/ontology/mbao/MBA_385"},
        "DMS": {"id": "UBERON:0005382", "uri": "http://purl.obolibrary.org/obo/UBERON_0005382"},
        "PL": {"id": "MBA:972", "uri": "https://purl.brain-bican.org/ontology/mbao/MBA_972"},
        "VTA": {"id": "MBA:749", "uri": "https://purl.brain-bican.org/ontology/mbao/MBA_749"},
        "gastrocnemius": {"id": "UBERON:0001388", "uri": "http://purl.obolibrary.org/obo/UBERON_0001388"},
    },
    "body_parts": {
        "head": {"id": "UBERON:0000033", "uri": "http://purl.obolibrary.org/obo/UBERON_0000033"},
        "not_a_node": {"id": "UBERON:0000974", "uri": "http://purl.obolibrary.org/obo/UBERON_0000974"},
    },
}


def write_terms(package, doc, extra=EXTRA_TERMS, drop=()):
    terms = yaml.safe_load(doc["phase_yaml"])
    for kind, values in extra.items():
        terms.setdefault(kind, {}).update(values)
    for kind in drop:
        terms.pop(kind, None)
    (package / "external_resources.yaml").write_text(yaml.safe_dump(terms))
    return terms


def convert(package, tmp_path, *, metadata_update=None, subject=True, nwbfile_fields=None, name="out.nwb", **run_kwargs):
    module = importlib.import_module("toy_lab_to_nwb.toy.toy_nwbconverter")
    converter = module.ToyNWBConverter(source_data=dict(Recording=dict(), Imaging=dict(), Extras=dict(), Pose=dict()))
    recording = converter.data_interface_objects["Recording"].recording_extractor
    recording.set_property("brain_area", ["CA1", "CA1", "VISp", "unknown"])
    metadata = converter.get_metadata()
    metadata["NWBFile"].update(
        session_start_time=datetime(2024, 1, 1, tzinfo=ZoneInfo("America/New_York")),
        session_description="s",
        **(dict(institution="Stanford University", experimenter=["Dichter, Benjamin", "Doe, Jane"])
           if nwbfile_fields is None else nwbfile_fields),
    )
    if subject:
        metadata["Subject"] = dict(subject_id="m1", species="Mus musculus", strain="C57BL/6J", sex="M", age="P30D")
    if metadata_update:
        metadata.update(metadata_update)
    path = tmp_path / name
    run_kwargs.setdefault("overwrite", True)
    converter.run_conversion(nwbfile_path=path, metadata=metadata, **run_kwargs)
    return path


def read_refs(path, io_class=NWBHDF5IO):
    with io_class(str(path), "r") as io:
        herd = io.read().external_resources
        return None if herd is None else herd.to_dataframe()


def as_set(df):
    return set(zip(df["object_type"], df["relative_path"], df["key"], df["entity_id"]))


FULL = {
    ("NWBFile", "general/institution", "Stanford University", "ROR:00f54p054"),
    ("NWBFile", "general/experimenter", "Dichter, Benjamin", "ORCID:0000-0001-5725-6910"),
    ("Subject", "species", "Mus musculus", "NCBITaxon:10090"),
    ("Subject", "strain", "C57BL/6J", "RRID:IMSR_JAX:000664"),
    # electrodes table column written by NeuroConv from the recording's brain_area property
    ("VectorData", "", "CA1", "MBA:382"),
    ("VectorData", "", "CA1", "UBERON:0003881"),
    ("VectorData", "", "VISp", "MBA:385"),
    ("ElectrodeGroup", "location", "CA1", "MBA:382"),
    ("ElectrodeGroup", "location", "CA1", "UBERON:0003881"),
    ("ImagingPlane", "location", "VISp", "MBA:385"),
    ("IntracellularElectrode", "location", "PL", "MBA:972"),
    ("OptogeneticStimulusSite", "location", "VTA", "MBA:749"),
    # FiberPhotometryTable location column
    ("VectorData", "", "DMS", "UBERON:0005382"),
    ("ElectrodeGroup", "location", "gastrocnemius", "UBERON:0001388"),
    # ndx-pose Skeleton.nodes written by NeuroConv's pose estimation interface
    ("Skeleton", "nodes", "left_shoulder", "UBERON:0001467"),
    ("Skeleton", "nodes", "head", "UBERON:0000033"),
}
UNUSED = ["not_a_node"]


def test_full_multimodal_conversion(package, doc, tmp_path):
    write_terms(package, doc)
    path = convert(package, tmp_path)
    df = read_refs(path)
    assert as_set(df) == FULL
    # no duplicated references: one row per (object, key, entity)
    assert not df.duplicated(subset=["object_id", "key", "entity_id"]).any()
    # one key per (object, value) even when the value has two terms
    assert not df.drop_duplicates(["object_id", "keys_idx"]).duplicated(["object_id", "key"]).any()
    # two distinct VectorData objects were annotated (electrodes location, fiber photometry location)
    assert df[df["object_type"] == "VectorData"]["object_id"].nunique() == 2
    # entity_uri recorded for each
    uris = dict(zip(df["entity_id"], df["entity_uri"]))
    assert uris["MBA:382"] == "https://purl.brain-bican.org/ontology/mbao/MBA_382"
    assert uris["NCBITaxon:10090"] == "http://purl.obolibrary.org/obo/NCBITaxon_10090"


def test_values_unchanged_by_annotation(package, doc, tmp_path):
    write_terms(package, doc)
    path = convert(package, tmp_path)
    with NWBHDF5IO(str(path), "r") as io:
        nwbfile = io.read()
        assert nwbfile.subject.species == "Mus musculus"
        assert nwbfile.subject.strain == "C57BL/6J"
        assert list(nwbfile.electrodes["location"][:]) == ["CA1", "CA1", "VISp", "unknown"]
        assert nwbfile.institution == "Stanford University"
        assert tuple(nwbfile.experimenter) == ("Dichter, Benjamin", "Doe, Jane")


def test_inspector_and_validation_clean(package, doc, tmp_path):
    write_terms(package, doc)
    path = convert(package, tmp_path)
    from nwbinspector import inspect_nwbfile, Importance
    messages = list(inspect_nwbfile(nwbfile_path=path))
    bad = [m for m in messages if m.importance in (Importance.ERROR, Importance.PYNWB_VALIDATION, Importance.CRITICAL)]
    assert not bad, bad
    assert not [m for m in messages if "external_resources" in (m.location or "")]
    from pynwb import validate
    errors = validate(path=str(path))
    errors = errors[0] if isinstance(errors, tuple) else errors
    assert not errors, errors


def test_no_matching_terms_writes_nothing(package, doc, tmp_path):
    (package / "external_resources.yaml").write_text(yaml.safe_dump({"species": {"Rattus norvegicus": {"id": "x:1", "uri": "u"}}}))
    path = convert(package, tmp_path)
    assert read_refs(path) is None


def test_empty_terms_file(package, doc, tmp_path):
    (package / "external_resources.yaml").write_text("{}\n")
    path = convert(package, tmp_path)
    assert read_refs(path) is None


def test_missing_subject_institution_experimenter(package, doc, tmp_path):
    write_terms(package, doc)
    path = convert(package, tmp_path, subject=False, nwbfile_fields={})
    got = as_set(read_refs(path))
    assert got == {r for r in FULL if r[0] not in ("NWBFile", "Subject")}


def test_only_some_kinds_present(package, doc, tmp_path):
    write_terms(package, doc, drop=("brain_regions", "strain", "body_parts"))
    path = convert(package, tmp_path)
    got = as_set(read_refs(path))
    assert got == {r for r in FULL if r[0] == "NWBFile" or r[2] == "Mus musculus"}


def test_rerun_with_overwrite_is_stable(package, doc, tmp_path):
    write_terms(package, doc)
    convert(package, tmp_path)
    path = convert(package, tmp_path)
    df = read_refs(path)
    assert as_set(df) == FULL and len(df) == len(FULL)


def test_stub_test_option(package, doc, tmp_path):
    write_terms(package, doc)
    path = convert(package, tmp_path, conversion_options=dict(Recording=dict(stub_test=True), Imaging=dict(stub_test=True)))
    assert as_set(read_refs(path)) == FULL


def test_zarr_backend(package, doc, tmp_path):
    from hdmf_zarr import NWBZarrIO
    write_terms(package, doc)
    path = convert(package, tmp_path, name="out.nwb.zarr", backend="zarr")
    assert as_set(read_refs(path, NWBZarrIO)) == FULL


def test_anatomy_snippet_runs(doc):
    from hdmf.common import HERD
    from pynwb import NWBFile, get_type_map
    from pynwb.file import Subject
    nwbfile = NWBFile(session_description="d", identifier="i", session_start_time=datetime(2024, 1, 1, tzinfo=ZoneInfo("UTC")))
    nwbfile.subject = Subject(subject_id="m1", species="Mus musculus")
    herd = HERD(type_map=get_type_map())
    exec(doc["anatomy"], dict(herd=herd, nwbfile=nwbfile))
    assert list(herd.to_dataframe()["entity_id"]) == ["NCBITaxon:10090"]


def run_check(doc, package, nwb_path, tmp_path):
    script = doc["check"].replace("src/<package>/<conversion>/external_resources.yaml", str(package / "external_resources.yaml"))
    script = script.replace("/path/to/output/session.nwb", str(nwb_path))
    assert "<" not in script.split("print(")[0]
    (tmp_path / "check.py").write_text(script)
    result = subprocess.run([sys.executable, str(tmp_path / "check.py")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_check_script_all_written(package, doc, tmp_path):
    write_terms(package, doc)
    out = run_check(doc, package, convert(package, tmp_path), tmp_path)
    assert f"In external_resources.yaml but not written: {UNUSED}" in out
    assert "MBA:382" in out and "ORCID:0000-0001-5725-6910" in out


def test_check_script_reports_mismatched_key(package, doc, tmp_path):
    write_terms(package, doc, extra={**EXTRA_TERMS, "brain_regions": {**EXTRA_TERMS["brain_regions"], "hippocampus CA1": {"id": "MBA:382", "uri": "u"}}})
    out = run_check(doc, package, convert(package, tmp_path), tmp_path)
    assert "not written: ['hippocampus CA1', 'not_a_node']" in out


def test_check_script_when_nothing_written(package, doc, tmp_path):
    (package / "external_resources.yaml").write_text(yaml.safe_dump({"species": {"Rattus norvegicus": {"id": "x:1", "uri": "u"}}}))
    out = run_check(doc, package, convert(package, tmp_path), tmp_path)
    assert "not written: ['Rattus norvegicus']" in out


def test_phase7_snippet_inside_with_block(package, doc, tmp_path, capsys):
    write_terms(package, doc)
    path = convert(package, tmp_path)
    assert doc["phase7"].startswith("    ")  # indented to sit inside the `with` block
    with_block = doc["phase7_with"].replace("/path/to/output/session.nwb", str(path))
    exec(with_block + "\n" + doc["phase7"], {})
    out = capsys.readouterr().out
    assert "RRID:IMSR_JAX:000664" in out and "Electrodes: 4 electrodes" in out
    # and the none-written branch
    (package / "external_resources.yaml").write_text("{}\n")
    path = convert(package, tmp_path)
    exec(doc["phase7_with"].replace("/path/to/output/session.nwb", str(path)) + "\n" + doc["phase7"], {})
    assert "External resources: none written" in capsys.readouterr().out


def test_import_check_one_liner(doc):
    command = doc["import_check"].strip().replace("python -c", f'"{sys.executable}" -c')
    out = subprocess.run(command, shell=True, capture_output=True, text=True).stdout.strip()
    assert out == ("built-in" if HAS_BUILTIN else "use the helper")


# ---- claims about NeuroConv's built-in support (only where it exists) ----

builtin = pytest.mark.skipif(not HAS_BUILTIN, reason="installed NeuroConv has no tools.external_resources")

BUILTIN_BLOCK = {
    "ExternalResources": {
        "species": {"Mus musculus": {"id": "NCBITaxon:10090", "uri": "http://purl.obolibrary.org/obo/NCBITaxon_10090"}},
        "brain_regions": {
            "CA1": [
                {"id": "MBA:382", "uri": "https://purl.brain-bican.org/ontology/mbao/MBA_382"},
                {"id": "UBERON:0003881", "uri": "http://purl.obolibrary.org/obo/UBERON_0003881"},
            ],
            **EXTRA_TERMS["brain_regions"],
        },
    }
}


@builtin
def test_builtin_split_composes_with_helper(package, doc, tmp_path):
    """species + brain_regions in metadata under ExternalResources, the rest in the helper's YAML."""
    write_terms(package, doc, drop=("species", "brain_regions"))
    path = convert(package, tmp_path, metadata_update=BUILTIN_BLOCK)
    df = read_refs(path)
    assert as_set(df) == FULL
    assert not df.duplicated(subset=["object_id", "key", "entity_id"]).any()


@builtin
def test_builtin_metadata_yaml_shape_matches_helper_yaml(package, doc, tmp_path):
    """The maps can be moved between the two files unchanged, loaded from YAML."""
    from neuroconv.utils import load_dict_from_file
    terms = write_terms(package, doc)
    (tmp_path / "metadata.yaml").write_text(yaml.safe_dump({"ExternalResources": {k: terms[k] for k in ("species", "brain_regions")}}))
    write_terms(package, doc, drop=("species", "brain_regions"))
    path = convert(package, tmp_path, metadata_update=load_dict_from_file(tmp_path / "metadata.yaml"))
    assert as_set(read_refs(path)) == FULL


@builtin
def test_builtin_overlap_does_not_duplicate(package, doc, tmp_path):
    """If the same terms are given to both mechanisms, nothing is written twice."""
    write_terms(package, doc)
    path = convert(package, tmp_path, metadata_update=BUILTIN_BLOCK)
    df = read_refs(path)
    assert as_set(df) == FULL
    assert not df.duplicated(subset=["object_id", "key", "entity_id"]).any()


@builtin
def test_builtin_infer_functions_propose_terms(package, doc, tmp_path):
    from neuroconv.tools.external_resources import infer_brain_region_external_resources, infer_species_external_resources
    (package / "external_resources.yaml").write_text("{}\n")
    path = convert(package, tmp_path)
    with NWBHDF5IO(str(path), "r") as io:
        nwbfile = io.read()
        species = infer_species_external_resources(nwbfile)
        regions = infer_brain_region_external_resources(nwbfile)
    assert species == {"ExternalResources": {"species": {"Mus musculus": {"id": "NCBITaxon:10090", "uri": "http://purl.obolibrary.org/obo/NCBITaxon_10090"}}}}
    proposed = regions["ExternalResources"]["brain_regions"]
    assert proposed["CA1"]["id"] == "MBA:382" and proposed["VISp"]["id"] == "MBA:385"
    assert "unknown" not in proposed


def test_values_of_skeleton_unchanged(package, doc, tmp_path):
    write_terms(package, doc)
    path = convert(package, tmp_path)
    with NWBHDF5IO(str(path), "r") as io:
        nwbfile = io.read()
        skeletons = [o for o in nwbfile.all_children() if type(o).__name__ == "Skeleton"]
        assert len(skeletons) == 1 and list(skeletons[0].nodes) == ["head", "neck", "left_shoulder"]


def test_standalone_herd_across_files(package, doc, tmp_path, monkeypatch):
    """The 'Annotating Files That Are Already Written' block, run on two written files."""
    (package / "external_resources.yaml").write_text("{}\n")
    paths = [str(convert(package, tmp_path, name=f"s{i}.nwb")) for i in range(2)]
    monkeypatch.chdir(tmp_path)
    scope = dict(nwbfile_paths=paths)
    exec(doc["multi"], scope)
    df = scope["herd"].to_dataframe()
    assert len(df) == 2 and df["file_object_id"].nunique() == 2 and df["entities_idx"].nunique() == 1
    assert set(df["relative_path"]) == {"species"}
    from pynwb.resources import HERD
    reloaded = HERD.from_zip(path="external_resources.zip").to_dataframe()
    assert list(reloaded["entity_id"]) == ["NCBITaxon:10090"] * 2


def test_file_with_stored_references_is_left_alone(package, doc, tmp_path):
    """A file that already stores HERD on disk cannot take more: the helper returns without raising."""
    terms = write_terms(package, doc)
    path = convert(package, tmp_path)
    scope = {}
    exec(doc["helper"], scope)
    with NWBHDF5IO(str(path), "r+") as io:
        nwbfile = io.read()
        scope["add_external_resources"](nwbfile=nwbfile, terms=terms)
        io.write(nwbfile)
    assert as_set(read_refs(path)) == FULL


def test_dandi_validate(package, doc, tmp_path):
    dandi = shutil.which("dandi", path=str(Path(sys.executable).parent))
    if dandi is None:
        pytest.skip("dandi is not installed in this environment")
    write_terms(package, doc)
    path = convert(package, tmp_path)
    result = subprocess.run([dandi, "validate", str(path)], capture_output=True, text=True)
    findings = [line for line in (result.stdout + result.stderr).splitlines() if line.startswith("[")]
    assert not [line for line in findings if "external_resources" in line]
    # Only NWB Inspector suggestions about the toy data, and the note that the file is not in a Dandiset
    assert not [line for line in findings if "NWBI.check" not in line and "NO_DANDISET_FOUND" not in line]


def test_listing_script(package, doc, tmp_path, capsys):
    (package / "external_resources.yaml").write_text("{}\n")
    path = convert(package, tmp_path)
    exec(doc["listing"].replace("/path/to/output/session.nwb", str(path)), {})
    out = capsys.readouterr().out
    for expected in [
        "institution: Stanford University",
        "experimenter: ('Dichter, Benjamin', 'Doe, Jane')",
        "species: Mus musculus",
        "strain: C57BL/6J",
        "root/electrodes location column: ['CA1', 'VISp', 'unknown']",
        "FiberPhotometryTable location column: ['DMS']",
        "nodes: ['head', 'neck', 'left_shoulder']",
        "root/shank1 location: CA1",
        "root/emg location: gastrocnemius",
        "root/plane_v1 location: VISp",
        "root/patch location: PL",
        "root/ogen_site location: VTA",
    ]:
        assert expected in out, expected


def test_empty_yaml_keys_are_tolerated(package, doc, tmp_path):
    """A kind left empty in the YAML (e.g. `strain:` awaiting an answer) loads as None."""
    terms = write_terms(package, doc)
    kept = {kind: values for kind, values in terms.items() if kind not in ("strain", "institution")}
    text = yaml.safe_dump(kept) + "strain:\ninstitution:\n"
    (package / "external_resources.yaml").write_text(text)
    assert yaml.safe_load(text)["strain"] is None
    path = convert(package, tmp_path)
    assert as_set(read_refs(path)) == {r for r in FULL if r[3] not in ("RRID:IMSR_JAX:000664", "ROR:00f54p054")}
    assert "not written:" in run_check(doc, package, path, tmp_path)


def test_check_script_names_objects(package, doc, tmp_path):
    write_terms(package, doc)
    out = run_check(doc, package, convert(package, tmp_path), tmp_path)
    for expected in ["electrodes/location", "FiberPhotometryTable/location", "root/subject", "root/shank1", "Skeletons/"]:
        assert expected in out, expected
    assert "NaN" not in out
