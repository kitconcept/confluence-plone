from . import EXPORT
from collections.abc import Callable
from collections.abc import Generator
from confluence_plone import PACKAGE_NAME
from confluence_plone import _types as t
from confluence_plone.converter import ConversionContext
from confluence_plone.converter import Converter
from confluence_plone.converter import parse_storage
from confluence_plone.planner import plan_migration
from confluence_plone.reader import ExportSource
from confluence_plone.reader import read_export
from confluence_plone.settings import get_default_settings
from confluence_plone.utils.principals import PrincipalMapper
from pathlib import Path

import confluence_plone
import logging
import pytest
import shutil


@pytest.fixture(autouse=True)
def test_dir(monkeypatch, tmp_path) -> Generator[Path]:
    """Run every test in its own directory, with a fresh logger."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(confluence_plone, "_LOGGER", None)
    yield tmp_path
    logger = logging.getLogger(PACKAGE_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


@pytest.fixture
def export_path() -> Path:
    """The test export, as a directory."""
    return EXPORT


@pytest.fixture
def export_zip(tmp_path) -> Path:
    """The test export, as a zip file."""
    archive = shutil.make_archive(str(tmp_path / "export"), "zip", EXPORT)
    return Path(archive)


@pytest.fixture
def settings(test_dir) -> t.ConfluenceSettings:
    """Default settings, writing the reports in the test directory."""
    value = get_default_settings()
    value.config["reports_location"] = test_dir / "reports"
    return value


@pytest.fixture
def source(export_path) -> Generator[ExportSource]:
    with ExportSource(export_path) as value:
        yield value


@pytest.fixture
def export(source) -> t.ConfluenceExport:
    return read_export(source)


@pytest.fixture
def plan(export, settings, source) -> t.MigrationPlan:
    return plan_migration(export, settings, source.find_attachment)


@pytest.fixture
def principals(export, settings) -> PrincipalMapper:
    return PrincipalMapper(export, settings)


@pytest.fixture
def make_context(export, plan, settings, principals) -> Callable:
    """Build a conversion context for a page of the test export."""

    def func(page_id: str = "100") -> ConversionContext:
        return ConversionContext(
            export=export,
            plan=plan,
            settings=settings,
            principals=principals,
            page=export.pages[page_id],
            item=plan.item_for(page_id),
        )

    return func


@pytest.fixture
def convert(make_context) -> Callable:
    """Convert a storage-format snippet as if it were the body of a page."""

    def func(
        storage: str, page_id: str = "100"
    ) -> tuple[list[t.PlateNode], ConversionContext]:
        ctx = make_context(page_id)
        return Converter(ctx).blocks(parse_storage(storage)), ctx

    return func


@pytest.fixture
def issue_codes() -> Callable:
    """Return the codes of the issues of a context."""

    def func(ctx: ConversionContext) -> list[str]:
        return [issue.code for issue in ctx.issues]

    return func
