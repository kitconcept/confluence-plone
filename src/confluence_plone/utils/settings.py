"""Serialize the settings as TOML."""

from tomlkit.items import Array
from tomlkit.items import Table
from tomlkit.items import item
from tomlkit.toml_document import TOMLDocument


def _fix_arrays(table: Table) -> Table:
    """Make every array with more than one value multi-line, recursively.

    :param table: The table to fix.
    :returns: The same table.
    """
    for value in table.values():
        if isinstance(value, Table):
            _fix_arrays(value)
        elif isinstance(value, Array) and len(value) > 1:
            value.multiline(True)
    return table


def settings_to_toml(data: dict) -> TOMLDocument:
    """Convert the settings to a TOML document.

    :param data: The settings, as a dictionary.
    :returns: The TOML document.
    """
    document = TOMLDocument()
    for key, raw_value in data.items():
        value = item(raw_value)
        if isinstance(value, Table):
            _fix_arrays(value)
        document[key] = value
    return document
