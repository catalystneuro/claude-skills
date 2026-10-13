"""Tests of the MeaningsTable and HED helper, hook, and scripts in nwb-convert/knowledge/value-meanings.md."""

import copy
import importlib
import re
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
import yaml
from pynwb import NWBHDF5IO

pytest.importorskip("ndx_hed")

EVENTS = {
    "TaskEvents": {
        "event_type": {
            "go_cue": {"meaning": "A different meaning, which must not replace the one written.", "hed": "Sensory-event, Cue"},
            "reward": {"meaning": "A drop of juice was delivered.", "hed": "Sensory-event, Reward"},
        }
    }
}


def write_annotations(package, meanings_doc, extra_tables=EVENTS, strip_hed=False):
    annotations = yaml.safe_load(meanings_doc["phase_yaml"])
    annotations["tables"].update(copy.deepcopy(extra_tables))
    if strip_hed:
        del annotations["hed_schema_version"]
        for columns in annotations["tables"].values():
            for entries in columns.values():
                for entry in entries.values():
                    entry.pop("hed", None)
    (package / "value_meanings.yaml").write_text(yaml.safe_dump(annotations))
    return annotations


def convert(package, tmp_path, name="out.nwb", **source_data):
    module = importlib.import_module("toy_lab_to_nwb.toy.toy_nwbconverter")
    converter = module.ToyNWBConverter(source_data=dict(Tables=source_data))
    metadata = converter.get_metadata()
    metadata["NWBFile"].update(
        session_start_time=datetime(2024, 1, 1, tzinfo=ZoneInfo("America/New_York")), session_description="s"
    )
    path = tmp_path / name
    converter.run_conversion(nwbfile_path=path, metadata=metadata, overwrite=True)
    return path


def read_meanings(path):
    """{"table/column": {value: (meaning, HED or None)}} for every MeaningsTable in the file."""
    from hdmf.common import MeaningsTable

    found = {}
    with NWBHDF5IO(str(path), "r") as io:
        nwbfile = io.read()
        for meanings_table in nwbfile.all_children():
            if isinstance(meanings_table, MeaningsTable):
                frame = meanings_table.to_dataframe()
                hed = frame["HED"] if "HED" in frame else [None] * len(frame)
                found[f"{meanings_table.parent.name}/{meanings_table.target.name}"] = {
                    value: (meaning, hed_string) for value, meaning, hed_string in zip(frame["value"], frame["meaning"], hed)
                }
        hed_metadata = nwbfile.lab_meta_data.get("hed_schema")
        version = None if hed_metadata is None else hed_metadata.hed_schema_version
    return found, version


def validate_hed(hed_string, version="8.4.0"):
    from hed import HedString, load_schema_version
    from hed.errors import ErrorHandler
    from hed.validator import HedValidator

    schema = load_schema_version(version)
    return HedValidator(schema).validate(
        HedString(hed_string, schema), allow_placeholders=False, error_handler=ErrorHandler(check_for_warnings=True)
    )


def run(script, tmp_path, name="script.py"):
    (tmp_path / name).write_text(script)
    result = subprocess.run([sys.executable, str(tmp_path / name)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_meanings_and_hed_are_written(meanings_package, meanings_doc, tmp_path):
    annotations = write_annotations(meanings_package, meanings_doc)
    found, version = read_meanings(convert(meanings_package, tmp_path))

    assert version == "8.4.0"
    assert set(found) == {"trials/result", "trials/ctr_hold_bump", "trials/split", "TaskEvents/event_type"}
    for column, entries in annotations["tables"]["trials"].items():
        assert found[f"trials/{column}"] == {
            value: (entry["meaning"], entry.get("hed") if any("hed" in e for e in entries.values()) else None)
            for value, entry in entries.items()
        }
    # A boolean column keeps boolean values, and a column with no HED gets no HED column
    assert set(found["trials/ctr_hold_bump"]) == {True, False}
    assert all(hed is None for _, hed in found["trials/split"].values())


def test_existing_meanings_table_is_extended_not_replaced(meanings_package, meanings_doc, tmp_path):
    write_annotations(meanings_package, meanings_doc)
    found, _ = read_meanings(convert(meanings_package, tmp_path))
    assert found["TaskEvents/event_type"] == {
        "go_cue": ("The go cue as the interface described it.", "Sensory-event, Cue"),
        "reward": ("A drop of juice was delivered.", "Sensory-event, Reward"),
    }


def test_values_are_unchanged_and_file_is_valid(meanings_package, meanings_doc, tmp_path):
    from pynwb import validate

    write_annotations(meanings_package, meanings_doc)
    path = convert(meanings_package, tmp_path)
    with NWBHDF5IO(str(path), "r") as io:
        trials = io.read().trials.to_dataframe()
    assert list(trials["result"]) == ["R", "A", "R", "R"]
    assert list(trials["ctr_hold_bump"]) == [True, False, True, False]
    errors = validate(path=str(path))
    errors = errors[0] if isinstance(errors, tuple) else errors
    assert not errors, errors


def test_meanings_without_hed_do_not_need_ndx_hed(meanings_package, meanings_doc, tmp_path, monkeypatch):
    write_annotations(meanings_package, meanings_doc, strip_hed=True)
    monkeypatch.setitem(sys.modules, "ndx_hed", None)  # any import of ndx_hed now raises ImportError
    path = convert(meanings_package, tmp_path)
    monkeypatch.undo()
    found, version = read_meanings(path)
    assert version is None
    assert set(found["trials/result"]) == {"R", "A"}
    assert all(hed is None for entries in found.values() for _, hed in entries.values())


def test_absent_tables_columns_and_empty_file_are_skipped(meanings_package, meanings_doc, tmp_path):
    # A table this session does not write (here the events table, and one that never exists) and a
    # column the table does not have are skipped; the rest is still written.
    annotations = write_annotations(meanings_package, meanings_doc)
    annotations["tables"]["NoSuchTable"] = {"x": {"a": {"meaning": "m"}}}
    annotations["tables"]["trials"]["no_such_column"] = {"a": {"meaning": "m"}}
    (meanings_package / "value_meanings.yaml").write_text(yaml.safe_dump(annotations))
    found, _ = read_meanings(convert(meanings_package, tmp_path, events=False))
    assert set(found) == {"trials/result", "trials/ctr_hold_bump", "trials/split"}

    (meanings_package / "value_meanings.yaml").write_text("tables:\n")
    found, version = read_meanings(convert(meanings_package, tmp_path, name="empty.nwb"))
    assert found == {"TaskEvents/event_type": {"go_cue": ("The go cue as the interface described it.", None)}}
    assert version is None


def test_documented_hed_strings_are_valid(meanings_doc):
    annotations = yaml.safe_load(meanings_doc["phase_yaml"])
    hed_strings = [
        entry["hed"]
        for columns in annotations["tables"].values()
        for entries in columns.values()
        for entry in entries.values()
        if "hed" in entry
    ]
    assert len(hed_strings) == 4
    for hed_string in hed_strings + ["Label/Abort", "Label/Fail", "(Somatic-presentation, Experimental-stimulus)"]:
        assert validate_hed(hed_string) == [], hed_string


def test_listing_script(meanings_package, meanings_doc, tmp_path, capsys):
    write_annotations(meanings_package, meanings_doc)
    path = convert(meanings_package, tmp_path)
    exec(meanings_doc["listing"].replace("/path/to/output/session.nwb", str(path)), {})
    out = capsys.readouterr().out
    assert "trials/result: ['A', 'R']" in out
    assert "trials/ctr_hold_bump: [False, True]" in out
    assert "trials/stimulus_code: [1, 2]" in out
    assert "TaskEvents/event_type: ['go_cue', 'reward']" in out
    # Times, measurements, and free text are not categories
    for column in ("start_time", "target_dir", "note", "timestamp"):
        assert f"/{column}:" not in out
    # stimulus_code is the one listed column the YAML does not describe
    without = dict(re.findall(r"(\S+): \[.*\]\n.*\n    without a meaning: (\[.*\])", out))
    assert without["trials/stimulus_code"] == "[1, 2]"
    assert without["trials/result"] == "[]" and without["trials/ctr_hold_bump"] == "[]"


def test_search_script(meanings_doc, capsys):
    exec(meanings_doc["search"], {})
    out = capsys.readouterr().out
    assert "abort: 0 tags" in out  # the knowledge file says 8.4.0 has no tag for it
    assert "    Reward: " in out


def test_validate_script(meanings_doc, capsys):
    exec(meanings_doc["validate"], {})
    out = capsys.readouterr().out
    assert "Experimental-trial, Correct-action, Reward -> valid" in out
    assert "TAG_INVALID" in out


def test_conventions_stated_in_the_knowledge_file():
    from hed import load_schema_version

    from conftest import MEANINGS

    text = MEANINGS.read_text()
    schema = load_schema_version("8.4.0")
    event_tags = sorted(
        {e.short_tag_name for e in schema.tags.all_entries if e.long_tag_name.startswith("Event/") and e.long_tag_name.count("/") == 1}
    )
    listed = re.search(r"starts with one of the event tags: (.*?)\.\n", text, flags=re.S).group(1)
    assert sorted(re.findall(r"`([\w-]+)`", listed)) == event_tags
    assert [issue["code"] for issue in validate_hed("Square/Big-one")] == ["TAG_EXTENDED"]
    assert schema.get_tag_entry("Reward").long_tag_name == "Property/Task-property/Task-stimulus-role/Reward"


def test_check_script(meanings_package, meanings_doc, tmp_path):
    write_annotations(meanings_package, meanings_doc)
    path = convert(meanings_package, tmp_path)
    out = run(meanings_doc["check"].replace("/path/to/output/session.nwb", str(path)), tmp_path)
    assert "trials/result values without a meaning: []" in out
    assert "trials/ctr_hold_bump values without a meaning: []" in out
    assert "HED strings: 6, with issues: 0" in out


def test_check_script_reports_undescribed_values_and_invalid_hed(meanings_package, meanings_doc, tmp_path):
    annotations = write_annotations(meanings_package, meanings_doc)
    del annotations["tables"]["trials"]["result"]["A"]
    annotations["tables"]["trials"]["result"]["R"]["hed"] = "Experimental-trial, Not-a-real-tag"
    (meanings_package / "value_meanings.yaml").write_text(yaml.safe_dump(annotations))
    path = convert(meanings_package, tmp_path)
    out = run(meanings_doc["check"].replace("/path/to/output/session.nwb", str(path)), tmp_path)
    assert "trials/result values without a meaning: ['A']" in out
    assert "TAG_INVALID" in out and "with issues: 1" in out


def test_check_script_without_hed(meanings_package, meanings_doc, tmp_path):
    write_annotations(meanings_package, meanings_doc, strip_hed=True)
    path = convert(meanings_package, tmp_path)
    out = run(meanings_doc["check"].replace("/path/to/output/session.nwb", str(path)), tmp_path)
    assert "trials/split values without a meaning: []" in out and "HED strings" not in out


def test_phase7_snippet_inside_with_block(meanings_package, meanings_doc, tmp_path, capsys):
    write_annotations(meanings_package, meanings_doc)
    path = convert(meanings_package, tmp_path)
    with_block = meanings_doc["phase7_with"].replace("/path/to/output/session.nwb", str(path))
    exec(with_block + "\n" + meanings_doc["phase7"], {})
    out = capsys.readouterr().out
    assert "trials/result" in out and "Experimental-trial, Correct-action, Reward" in out


def test_ndx_hed_file_validation_as_the_knowledge_file_describes(meanings_package, meanings_doc, tmp_path):
    """The knowledge file says validate_file raises TypeError for an annotated boolean column read from a
    file. When ndx-hed fixes that, this fails, and the check script should move to validate_file."""
    from ndx_hed.utils.hed_nwb_validator import HedNWBValidator

    write_annotations(meanings_package, meanings_doc)
    path = convert(meanings_package, tmp_path)
    with NWBHDF5IO(str(path), "r") as io:
        nwbfile = io.read()
        validator = HedNWBValidator(nwbfile.lab_meta_data["hed_schema"])
        assert validator.validate_table(nwbfile.events["TaskEvents"]) == []  # strings only: validates
        with pytest.raises(TypeError, match="keys must be str"):
            validator.validate_file(nwbfile)
