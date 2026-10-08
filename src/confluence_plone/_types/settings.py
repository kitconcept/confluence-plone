"""Types for the ``confluence-plone`` settings."""

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import TypedDict


__all__ = ["ConfluenceSettings"]


class SettingsConfig(TypedDict):
    """General settings."""

    filepath: Path
    debug: bool
    log_file: str
    reports_location: Path
    timezone: str


class SettingsSource(TypedDict):
    """Which part of the export is converted."""

    spaces: tuple[str, ...]
    include_personal_spaces: bool
    include_archived_spaces: bool


class SettingsTarget(TypedDict):
    """Where and as what the content lands in Plone."""

    site_root: str
    base_path: str
    workspace_type: str
    page_type: str
    file_type: str
    image_type: str
    workflow: str
    initial_state: str
    review_state: str
    link_style: str
    types_without_workflow: tuple[str, ...]
    image_media_types: tuple[str, ...]


class SettingsPrincipals(TypedDict):
    """How Confluence users become Plone principals."""

    default: str
    strategy: str
    mapping_file: str


class SettingsContent(TypedDict):
    """Which kinds of content are converted."""

    label_namespaces: tuple[str, ...]
    footer_comments: bool
    inline_comments: bool


class SettingsMacros(TypedDict):
    """Settings used by macro converters."""

    jira_url: str


class SettingsRedirects(TypedDict):
    """Redirects from old Confluence URLs."""

    enabled: bool


@dataclass
class ConfluenceSettings:
    """Settings for the ``confluence-plone`` application."""

    config: SettingsConfig
    source: SettingsSource
    target: SettingsTarget
    principals: SettingsPrincipals
    content: SettingsContent
    macros: SettingsMacros
    redirects: SettingsRedirects
    _raw_data: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def is_debug(self) -> bool:
        """Whether debug mode is enabled."""
        return bool(self.config.get("debug", False))
