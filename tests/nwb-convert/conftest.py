"""Fixtures for testing the code that the nwb-convert skill tells an agent to write.

The code under test lives in the skill's markdown files. These fixtures extract the fenced
code blocks verbatim, so the tests exercise exactly what the skill ships.
"""

import os
import re
import sys
from pathlib import Path

import pytest

REPO = Path(os.environ.get("SKILL_REPO", Path(__file__).resolve().parents[2]))
KNOWLEDGE = REPO / "nwb-convert/knowledge/external-resources.md"
PHASE = REPO / "nwb-convert/phases/06-ontology-annotation.md"
TESTING = REPO / "nwb-convert/phases/07-testing.md"
MEANINGS = REPO / "nwb-convert/knowledge/value-meanings.md"


def pytest_addoption(parser):
    parser.addoption("--network", action="store_true", help="also run the tests that query the registries")


def pytest_configure(config):
    config.addinivalue_line("markers", "network: queries external registries; run with --network")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--network"):
        return
    skip = pytest.mark.skip(reason="queries external registries; run with --network")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip)


def blocks(path, language):
    """Every fenced code block of one language in a markdown file."""
    return re.findall(rf"```{language}\n(.*?)```", path.read_text(), flags=re.S)


def one(path, language, marker):
    """The single code block of that language that contains `marker`."""
    found = [block for block in blocks(path, language) if marker in block]
    assert len(found) == 1, (path.name, marker, len(found))
    return found[0]


@pytest.fixture(scope="session")
def doc():
    return dict(
        helper=one(KNOWLEDGE, "python", "def add_external_resources"),
        hook=one(KNOWLEDGE, "python", "class <ConversionName>NWBConverter"),
        check=one(KNOWLEDGE, "python", "In external_resources.yaml but not written"),
        anatomy=one(KNOWLEDGE, "python", "herd.add_ref(\n    container=nwbfile.subject"),
        import_check=one(KNOWLEDGE, "bash", "import neuroconv.tools.external_resources"),
        listing=one(KNOWLEDGE, "python", "location column:"),
        multi=one(KNOWLEDGE, "python", "herd.to_zip("),
        phase_yaml=one(PHASE, "yaml", "species:"),
        phase7=one(TESTING, "python", "# Check ontology annotations"),
        phase7_with=one(TESTING, "python", 'with NWBHDF5IO("/path/to/output/session.nwb", "r") as io:'),
    )


@pytest.fixture()
def package(tmp_path, doc, monkeypatch):
    """A conversion package laid out as the skill prescribes, holding the skill's code verbatim."""
    package_path = tmp_path / "src" / "toy_lab_to_nwb" / "toy"
    package_path.mkdir(parents=True)
    (package_path.parent / "__init__.py").write_text("")
    (package_path / "__init__.py").write_text("")
    (package_path / "external_resources.py").write_text(doc["helper"])
    hook = doc["hook"].replace("<ConversionName>", "Toy")
    hook = hook.replace(
        "class ToyNWBConverter(NWBConverter):\n",
        "from .interfaces import INTERFACES\n\n\nclass ToyNWBConverter(NWBConverter):\n    data_interface_classes = INTERFACES\n",
    )
    (package_path / "toy_nwbconverter.py").write_text(hook)
    (package_path / "interfaces.py").write_text((Path(__file__).parent / "toy_interfaces.py").read_text())
    monkeypatch.syspath_prepend(str(tmp_path / "src"))
    for name in [module for module in sys.modules if module.startswith("toy_lab_to_nwb")]:
        del sys.modules[name]
    return package_path


@pytest.fixture(scope="session")
def meanings_doc():
    return dict(
        helper=one(MEANINGS, "python", "def add_value_meanings"),
        hook=one(MEANINGS, "python", "class <ConversionName>NWBConverter"),
        listing=one(MEANINGS, "python", "without a meaning: {"),
        search=one(MEANINGS, "python", "schema.tags.all_entries"),
        validate=one(MEANINGS, "python", '"Experimental-trial, Aborted"'),
        check=one(MEANINGS, "python", "values without a meaning:"),
        phase_yaml=one(PHASE, "yaml", "hed_schema_version:"),
        phase7=one(TESTING, "python", "# Check value meanings"),
        phase7_with=one(TESTING, "python", 'with NWBHDF5IO("/path/to/output/session.nwb", "r") as io:'),
    )


@pytest.fixture()
def meanings_package(tmp_path, doc, meanings_doc, monkeypatch):
    """A conversion package holding both Phase 6 helpers and the hook that calls them, verbatim."""
    package_path = tmp_path / "src" / "toy_lab_to_nwb" / "toy"
    package_path.mkdir(parents=True)
    (package_path.parent / "__init__.py").write_text("")
    (package_path / "__init__.py").write_text("")
    (package_path / "external_resources.py").write_text(doc["helper"])
    (package_path / "external_resources.yaml").write_text(doc["phase_yaml"])
    (package_path / "value_meanings.py").write_text(meanings_doc["helper"])
    hook = meanings_doc["hook"].replace("<ConversionName>", "Toy")
    hook = hook.replace(
        "class ToyNWBConverter(NWBConverter):\n",
        "from .interfaces import INTERFACES\n\n\nclass ToyNWBConverter(NWBConverter):\n    data_interface_classes = INTERFACES\n",
    )
    (package_path / "toy_nwbconverter.py").write_text(hook)
    (package_path / "interfaces.py").write_text((Path(__file__).parent / "toy_table_interfaces.py").read_text())
    monkeypatch.syspath_prepend(str(tmp_path / "src"))
    for name in [module for module in sys.modules if module.startswith("toy_lab_to_nwb")]:
        del sys.modules[name]
    return package_path
