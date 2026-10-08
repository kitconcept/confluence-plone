from collections.abc import Callable
from confluence_plone.cli import app
from typer.testing import CliRunner
from typer.testing import Result

import pytest


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def invoke(runner) -> Callable[..., Result]:
    """Run the command line interface with some arguments."""

    def func(*args: str) -> Result:
        return runner.invoke(app, [str(arg) for arg in args])

    return func


@pytest.fixture
def settings_file(invoke, test_dir):
    """Generate a settings file in the test directory."""
    invoke("settings", "generate")
    return test_dir / "confluence-plone.toml"
