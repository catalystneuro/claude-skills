#!/usr/bin/env python3
"""Refresh knowledge/neuroconv-interfaces.yaml from the installed NeuroConv.

Rewrites the ``source_data`` and ``conversion_options`` of every catalog entry from the
interface's JSON schemas and docstrings, keeping the hand-written ``format``, ``creates``,
``notes`` and ``deprecated`` fields. Prints the interfaces NeuroConv exports that the catalog
does not list, so they can be added by hand under the right category.

Usage:
    python update_neuroconv_interfaces.py
"""

import re
from pathlib import Path

import docstring_parser
import yaml
from neuroconv import datainterfaces
from neuroconv.datainterfaces import interface_list
from neuroconv.utils import get_json_schema_from_method_signature

CATALOG_PATH = Path(__file__).parent.parent / "knowledge" / "neuroconv-interfaces.yaml"

JSON_TYPE_NAMES = {"string": "str", "boolean": "bool", "integer": "int", "number": "float", "object": "dict"}
PATH_FORMAT_NAMES = {"file-path": "FilePath", "file": "FilePath", "directory-path": "DirectoryPath"}


def schema_type_name(property_schema: dict) -> str:
    """Render a JSON schema property as a Python-style type name."""
    if "anyOf" in property_schema:
        return " | ".join(schema_type_name(option) for option in property_schema["anyOf"])
    if "format" in property_schema and property_schema["format"] in PATH_FORMAT_NAMES:
        return PATH_FORMAT_NAMES[property_schema["format"]]
    if "enum" in property_schema:
        return "Literal[" + ", ".join(repr(value) for value in property_schema["enum"]) + "]"
    json_type = property_schema.get("type", "any")
    if json_type == "array":
        return f"list[{schema_type_name(property_schema.get('items', {}))}]"
    if json_type == "null":
        return "None"
    return JSON_TYPE_NAMES.get(json_type, json_type)


def first_sentence(text: str) -> str:
    collapsed = " ".join(text.split())
    match = re.match(r"(.+?\.)\s+[A-Z]", collapsed)
    return match.group(1) if match else collapsed


def build_parameters(schema: dict, method, existing_parameters: dict) -> dict:
    """Build the catalog's parameter mapping from a schema and the method's numpydoc docstring."""
    documented = {parameter.arg_name: parameter for parameter in docstring_parser.parse(method.__doc__ or "").params}
    required = set(schema.get("required", []))
    parameters = {}
    for name, property_schema in schema.get("properties", {}).items():
        existing = existing_parameters.get(name, {})
        parameter = {"type": schema_type_name(property_schema)}
        if name in documented and documented[name].description:
            parameter["description"] = first_sentence(documented[name].description)
        elif "description" in property_schema:
            parameter["description"] = first_sentence(property_schema["description"])
        elif "description" in existing:
            parameter["description"] = existing["description"]
        if name not in required:
            parameter["optional"] = True
            if "default" in property_schema:
                parameter["default"] = property_schema["default"]
        parameters[name] = parameter
    return parameters


def iterate_entries(node):
    """Yield every interface entry in the nested category tree."""
    if isinstance(node, list):
        yield from node
    else:
        for child in node.values():
            yield from iterate_entries(child)


def main():
    catalog = yaml.safe_load(CATALOG_PATH.read_text())
    catalogued_names = set()
    for entry in iterate_entries(catalog):
        interface_class = getattr(datainterfaces, entry["name"])
        catalogued_names.add(entry["name"])
        entry["source_data"] = build_parameters(
            schema=interface_class.get_source_schema(),
            method=interface_class.__init__,
            existing_parameters=entry.get("source_data") or {},
        )
        entry["conversion_options"] = build_parameters(
            schema=get_json_schema_from_method_signature(
                interface_class.add_to_nwbfile, exclude=["self", "nwbfile", "metadata"]
            ),
            method=interface_class.add_to_nwbfile,
            existing_parameters=entry.get("conversion_options") or {},
        )

    CATALOG_PATH.write_text(yaml.safe_dump(catalog, sort_keys=False, width=120, allow_unicode=True))

    missing = sorted({interface_class.__name__ for interface_class in interface_list} - catalogued_names)
    print(f"Refreshed {len(catalogued_names)} entries in {CATALOG_PATH.name}.")
    if missing:
        print("Interfaces exported by NeuroConv but missing from the catalog:")
        for name in missing:
            print(f"  {name}")


if __name__ == "__main__":
    main()
