from . import NO_SETTINGS
from confluence_plone import __version__
from confluence_plone.cli import cli

import pytest
import sys


class TestApp:
    def test_no_arguments(self, invoke):
        result = invoke()
        assert "Usage" in result.stdout

    def test_entry_point(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["confluence-plone", "info"])
        with pytest.raises(SystemExit) as exc:
            cli()
        assert exc.value.code == 0
        assert __version__ in capsys.readouterr().out

    @pytest.mark.parametrize("command", ["analyze", "convert"])
    def test_needs_settings(self, invoke, command, export_path, test_dir):
        result = invoke(command, export_path, test_dir / "out")
        assert result.exit_code == 1
        assert NO_SETTINGS in result.stdout


class TestInfo:
    def test_info(self, invoke):
        result = invoke("info")
        assert result.exit_code == 0
        assert f"confluence-plone - {__version__}" in result.stdout
        assert " - lxml: " in result.stdout


class TestSettings:
    def test_generate(self, invoke, test_dir):
        result = invoke("settings", "generate")
        assert result.exit_code == 0
        text = (test_dir / "confluence-plone.toml").read_text()
        assert "[target]" in text
        assert 'page_type = "WikiPage"' in text

    def test_generate_existing(self, invoke, settings_file):
        result = invoke("settings", "generate")
        assert result.exit_code == 1
        assert "File already exists" in result.stdout

    def test_show(self, invoke, settings_file):
        result = invoke("settings")
        assert result.exit_code == 0
        assert "Settings used by this application" in result.stdout
        assert f"Local settings: {settings_file.resolve()}" in result.stdout
        assert 'workflow = "simple_intranet_workflow"' in result.stdout

    def test_show_without_file(self, invoke):
        result = invoke("settings")
        assert result.exit_code == 1
        assert "Did not find a confluence-plone.toml file" in result.stdout


class TestAnalyze:
    def test_analyze(self, invoke, settings_file, export_path, test_dir):
        result = invoke("analyze", export_path)
        assert result.exit_code == 0
        assert "Inventory" in result.stdout
        assert "Macros (top 20)" in result.stdout
        assert (test_dir / "reports" / "inventory.json").exists()

    def test_destination(self, invoke, settings_file, export_path, test_dir):
        result = invoke("analyze", export_path, "--dst", test_dir / "elsewhere")
        assert result.exit_code == 0
        assert (test_dir / "elsewhere" / "macros.csv").exists()

    def test_missing_source(self, invoke, settings_file, test_dir):
        result = invoke("analyze", test_dir / "missing.zip")
        assert result.exit_code == 1
        assert "does not exist" in result.stdout


class TestConvert:
    def test_convert(self, invoke, settings_file, export_path, test_dir):
        result = invoke("convert", export_path, test_dir / "import")
        assert result.exit_code == 0
        assert "WikiPage" in result.stdout
        assert "Issues: error" in result.stdout
        assert (test_dir / "import" / "content" / "__metadata__.json").exists()
        assert (test_dir / "reports" / "items.csv").exists()
        assert (
            "INFO: Converting space DEV"
            in (test_dir / "confluence-plone.log").read_text()
        )

    def test_not_empty(self, invoke, settings_file, export_path, test_dir):
        (test_dir / "import").mkdir()
        (test_dir / "import" / "old.txt").write_text("old")
        result = invoke("convert", export_path, test_dir / "import")
        assert result.exit_code == 1
        assert "--clean-up" in result.stdout

    def test_clean_up(self, invoke, settings_file, export_path, test_dir):
        (test_dir / "import").mkdir()
        (test_dir / "import" / "old.txt").write_text("old")
        result = invoke("convert", export_path, test_dir / "import", "--clean-up")
        assert result.exit_code == 0
        assert not (test_dir / "import" / "old.txt").exists()

    def test_empty_destination(self, invoke, settings_file, export_path, test_dir):
        (test_dir / "import").mkdir()
        result = invoke("convert", export_path, test_dir / "import")
        assert result.exit_code == 0

    def test_missing_source(self, invoke, settings_file, test_dir):
        result = invoke("convert", test_dir / "missing", test_dir / "import")
        assert result.exit_code == 1
        assert "does not exist" in result.stdout

    def test_bad_settings(self, invoke, settings_file, export_path, test_dir):
        settings_file.write_text('[principals]\nstrategy = "magic"\n')
        result = invoke("convert", export_path, test_dir / "import")
        assert result.exit_code == 1
        assert "Unknown principals strategy" in result.stdout

    def test_unmapped_users(self, invoke, settings_file, export_path, test_dir):
        settings_file.write_text(
            '[principals]\nstrategy = "email"\n[target]\nlink_style = "path"\n'
        )
        text = (export_path / "entities.xml").read_text()
        src = test_dir / "src"
        src.mkdir()
        (src / "entities.xml").write_text(
            text.replace(
                "[CDATA[asmith]]></property>\n</object>",
                "[CDATA[ghost]]></property>\n</object>",
            )
        )
        result = invoke("convert", src, test_dir / "import")
        assert result.exit_code == 0
        assert "1 Confluence users were mapped to 'admin'" in result.stdout
