from . import LOCAL_SETTINGS
from confluence_plone.settings import get_default_settings
from confluence_plone.settings import get_settings
from confluence_plone.settings import logger_settings
from pathlib import Path

import pytest


class TestDefaultSettings:
    @pytest.fixture
    def settings(self):
        return get_default_settings()

    @pytest.mark.parametrize(
        "section,key,expected",
        [
            ("config", "debug", False),
            ("config", "log_file", "confluence-plone.log"),
            ("config", "reports_location", Path("reports")),
            ("config", "timezone", "UTC"),
            ("config", "filepath", ""),
            ("source", "spaces", ()),
            ("target", "workspace_type", "Workspace"),
            ("target", "page_type", "WikiPage"),
            ("target", "workflow", "simple_intranet_workflow"),
            ("target", "link_style", "resolveuid"),
            ("target", "types_without_workflow", ("File", "Image")),
            ("principals", "default", "admin"),
            ("principals", "strategy", "username"),
            ("content", "label_namespaces", ("global", "team")),
            ("redirects", "enabled", False),
        ],
    )
    def test_value(self, settings, section, key, expected):
        assert getattr(settings, section)[key] == expected

    def test_is_debug(self, settings):
        assert settings.is_debug is False

    def test_raw_data_keeps_lists(self, settings):
        assert settings._raw_data["source"]["spaces"] == []
        assert "filepath" not in settings._raw_data["config"]


class TestGetSettings:
    def test_no_file(self, test_dir):
        with pytest.raises(FileNotFoundError, match=r"confluence-plone\.toml"):
            get_settings(test_dir)

    def test_local_file(self, test_dir):
        (test_dir / "confluence-plone.toml").write_text(LOCAL_SETTINGS)
        settings = get_settings()
        assert settings.config["filepath"] == str(
            test_dir.resolve() / "confluence-plone.toml"
        )
        assert settings.config["reports_location"] == Path("out/reports")
        assert settings.source["spaces"] == ("DEV", "OPS")
        assert settings.target["base_path"] == "/wikis"
        # Values not set locally keep their default
        assert settings.target["page_type"] == "WikiPage"
        assert settings.macros["jira_url"] == "https://jira.example.org"


class TestLoggerSettings:
    def test_defaults(self, test_dir):
        assert logger_settings(test_dir) == (False, test_dir / "confluence-plone.log")

    def test_local_file(self, test_dir):
        (test_dir / "confluence-plone.toml").write_text("[config]\ndebug = true\n")
        assert logger_settings(test_dir) == (True, test_dir / "confluence-plone.log")
