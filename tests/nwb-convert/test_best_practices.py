"""Check the NWB Inspector check names in knowledge/nwb-best-practices.md against the installed NWB Inspector."""

import re

from nwbinspector import available_checks, load_config

from conftest import REPO, TESTING

BEST_PRACTICES = REPO / "nwb-convert/knowledge/nwb-best-practices.md"


def check_names(text):
    return set(re.findall(r"`(check_\w+)`", text))


def test_check_names_exist():
    registered = {check.__name__ for check in available_checks}
    assert check_names(BEST_PRACTICES.read_text()) - registered == set()


def test_validation_section_names_the_dandi_configuration():
    text = BEST_PRACTICES.read_text()
    validation = text[text.index("## Validation") : text.index("## General")]
    dandi_configuration = load_config("dandi")
    assert dandi_configuration.keys() == {"CRITICAL", "BEST_PRACTICE_VIOLATION"}
    assert set(dandi_configuration["CRITICAL"]) == check_names(validation) - {"check_data_orientation"}
    assert dandi_configuration["BEST_PRACTICE_VIOLATION"] == ["check_data_orientation"]


def test_testing_phase_check_names_are_in_best_practices():
    assert check_names(TESTING.read_text()) - check_names(BEST_PRACTICES.read_text()) == set()
