"""Read the ``confluence-plone`` settings.

Settings come from two places: the defaults shipped with the package
(``default.toml``) and the ``confluence-plone.toml`` file in the current
working directory. Values in the local file win, table by table.
"""

from collections.abc import Callable
from confluence_plone import _types as t
from copy import deepcopy
from dynaconf import Dynaconf
from pathlib import Path
from typing import Any


SETTINGS_FILE = "confluence-plone.toml"


def _as_tuple(value: list | tuple | None) -> tuple:
    """Cast a list value to a tuple.

    :param value: The list to cast.
    :returns: A tuple with the same elements.
    """
    return tuple(value) if value else ()


_CASTS: dict[str, Callable[[Any], Any]] = {
    "source.spaces": _as_tuple,
    "target.types_without_workflow": _as_tuple,
    "target.image_media_types": _as_tuple,
    "content.label_namespaces": _as_tuple,
}


def _find_config_path(settings: Dynaconf) -> Path:
    """Return the absolute path of the settings file.

    :param settings: The dynaconf settings object.
    :returns: The resolved path. It is a directory when no file was found.
    """
    settings_path = Path(settings.find_file(SETTINGS_FILE))
    return settings_path.resolve()


def parse_default() -> dict:
    """Read the default settings shipped with the package.

    :returns: The default settings.
    """
    settings_file = Path(__file__).parent / "default.toml"
    settings = Dynaconf(settings_files=[settings_file], merge_enabled=False)
    return settings.as_dict()


def parse_config(cwd_path: Path) -> dict:
    """Read the ``confluence-plone.toml`` file.

    :param cwd_path: Directory to look for the file in.
    :returns: The local settings.
    :raises FileNotFoundError: When there is no settings file.
    """
    settings = Dynaconf(
        envvar_prefix="CONFLUENCE_PLONE",
        root_path=cwd_path,
        settings_files=[SETTINGS_FILE],
        merge_enabled=False,
    )
    filepath = _find_config_path(settings)
    if filepath.is_dir():
        raise FileNotFoundError(
            f"Settings file '{SETTINGS_FILE}' not found in {cwd_path}."
        )
    data = settings.as_dict()
    data.setdefault("CONFIG", {})["filepath"] = str(filepath)
    return data


def _merge_dicts(defaults: dict, settings: dict) -> dict:
    """Merge two dictionaries recursively, ``settings`` winning.

    :param defaults: The default values.
    :param settings: The values that override the defaults.
    :returns: The merged dictionary.
    """
    result = defaults.copy()
    for key, value in settings.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def _apply_casts(data: dict) -> dict:
    """Cast the values listed in ``_CASTS``.

    :param data: The merged settings.
    :returns: The same dictionary, with the values cast.
    """
    for key, cast in _CASTS.items():
        section, name = key.split(".")
        data[section][name] = cast(data[section].get(name))
    return data


def _merge_defaults(defaults: dict, settings: dict) -> dict:
    """Merge the defaults with the local settings, and cast the values.

    :param defaults: The default settings.
    :param settings: The local settings.
    :returns: The settings, ready to build a :class:`ConfluenceSettings`.
    """
    merged = {k.lower(): v for k, v in defaults.items()}
    local = {k.lower(): v for k, v in settings.items()}
    merged = _merge_dicts(merged, local)
    # Keep the raw data for the settings command
    raw_data = deepcopy(merged)
    raw_data["config"].pop("filepath", None)
    merged["_raw_data"] = raw_data
    merged = _apply_casts(merged)
    config = merged["config"]
    config.setdefault("filepath", "")
    config["reports_location"] = Path(config["reports_location"])
    return merged


def get_settings(cwd_path: Path | None = None) -> t.ConfluenceSettings:
    """Return the settings, merging the defaults with the local settings file.

    :param cwd_path: Directory with the settings file. Defaults to the current
        working directory.
    :returns: The settings.
    :raises FileNotFoundError: When there is no settings file.
    """
    cwd_path = Path.cwd() if cwd_path is None else cwd_path
    payload = _merge_defaults(parse_default(), parse_config(cwd_path))
    return t.ConfluenceSettings(**payload)


def get_default_settings() -> t.ConfluenceSettings:
    """Return the default settings, ignoring any local settings file.

    :returns: The default settings.
    """
    payload = _merge_defaults(parse_default(), {})
    return t.ConfluenceSettings(**payload)
