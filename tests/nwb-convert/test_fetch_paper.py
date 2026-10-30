"""Runs nwb-convert/tools/fetch_paper.py against the live NCBI services.

These need network access, so they only run with `--network`.
"""

import importlib.util
import urllib.request

import pytest

from conftest import REPO

pytestmark = pytest.mark.network

spec = importlib.util.spec_from_file_location("fetch_paper", REPO / "nwb-convert/tools/fetch_paper.py")
fetch_paper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_paper)


class RefuseRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        raise AssertionError(f"{request.full_url} redirects to {new_url}")


@pytest.fixture
def no_redirects():
    urllib.request.install_opener(urllib.request.build_opener(RefuseRedirects))
    yield
    urllib.request.install_opener(None)


class TestResolveIds:
    def test_doi_resolves_without_redirect(self, no_redirects):
        identifiers = fetch_paper.resolve_ids({"type": "doi", "id": "10.1038/s41586-024-08168-4"})
        assert identifiers == {"doi": "10.1038/s41586-024-08168-4", "pmid": "39506117", "pmcid": "PMC11666460"}
