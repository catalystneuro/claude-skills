"""Runs the registry lookups in nwb-convert/knowledge/external-resources.md against the live services.

These need network access and depend on third-party APIs, so they only run with `--network`.
"""

import json
import re
import subprocess
import sys
import textwrap

import pytest

from conftest import KNOWLEDGE, PHASE, blocks

pytestmark = pytest.mark.network


def lookup_commands():
    """Each curl command in the knowledge file, verbatim except for the Python interpreter."""
    commands = []
    for block in blocks(KNOWLEDGE, "bash"):
        block = textwrap.dedent(block).replace("| python -c", f'| "{sys.executable}" -c')
        commands += [command for command in re.split(r"\n(?=curl )", block.strip()) if command.startswith("curl ")]
    return commands


def run(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0 and not result.stderr.strip(), result.stderr
    return result.stdout.strip()


def command_containing(marker):
    found = [command for command in lookup_commands() if marker in command]
    assert len(found) == 1, (marker, len(found))
    return found[0]


@pytest.mark.parametrize("command", lookup_commands(), ids=lambda command: re.sub(r"\W+", "_", command)[-60:])
def test_lookup_command_runs(command):
    assert len(run(command)) > 10


def test_species_lookup_returns_the_documented_fields():
    hit = json.loads(run(command_containing("ontology=ncbitaxon")))["response"]["docs"][0]
    assert (hit["obo_id"], hit["label"]) == ("NCBITaxon:10116", "Rattus norvegicus")
    assert hit["iri"] == "http://purl.obolibrary.org/obo/NCBITaxon_10116"


def test_allen_lookup_gives_the_mba_id():
    hits = json.loads(run(command_containing("api.brain-map.org")))["msg"]
    assert [(hit["id"], hit["acronym"]) for hit in hits] == [(382, "CA1")]


def test_uberon_term_cross_references_the_allen_structure():
    out = run(command_containing("ontologies/uberon/terms"))
    assert out.startswith("UBERON:0002436 | primary visual cortex") and "MBA:385" in out


def test_ror_lookup_shows_same_named_organizations_in_different_countries():
    lines = run(command_containing("api.ror.org")).splitlines()
    same_name = [line for line in lines if "| National Institutes of Health |" in line]
    assert any("https://ror.org/01cwqze88" in line and "Bethesda" in line for line in same_name)
    assert len(same_name) > 1, "expected more than one record named National Institutes of Health"


def test_orcid_doi_search_needs_both_cases():
    both = command_containing("doi-self")
    published_only = both.replace("+OR+%2210.7554/elife.78362%22", "")
    assert published_only != both
    assert json.loads(run(both))["num-found"] > json.loads(run(published_only))["num-found"]


def test_bioregistry_redirects_to_the_entity_uri():
    assert run(command_containing("bioregistry.io")) == "https://purl.brain-bican.org/ontology/mbao/MBA_382"


def urls():
    text = PHASE.read_text() + KNOWLEDGE.read_text()
    found = set()
    for url in re.findall(r"https?://[^\s\"`>]+", text):
        url = url.rstrip(".,:")
        if url.endswith(")") and url.count("(") < url.count(")"):  # the closing bracket of a markdown link
            url = url[:-1]
        found.add(url)
    return sorted(url for url in found if "<" not in url and "\\" not in url)


@pytest.mark.parametrize("url", urls())
def test_url_resolves(url):
    command = f"curl -s -g -L -o /dev/null -w '%{{http_code}}' -H 'Accept: application/json' --max-time 60 '{url}'"
    status = run(command)
    # The SciCrunch resolver page refuses curl but is the URI that Bioregistry resolves an RRID to
    allowed = {"200", "403"} if url.startswith("https://scicrunch.org/resolver/") and not url.endswith(".json") else {"200"}
    assert status in allowed, (url, status)
