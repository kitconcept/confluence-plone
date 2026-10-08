from confluence_plone import _types as t
from confluence_plone.settings.parse import SETTINGS_FILE
from confluence_plone.settings.parse import get_default_settings
from confluence_plone.utils.settings import settings_to_toml
from pathlib import Path

import tomlkit
import typer


app = typer.Typer()


def dump_settings(settings: t.ConfluenceSettings) -> str:
    """Dump the settings as TOML.

    :param settings: The settings.
    :returns: The TOML text.
    """
    return tomlkit.dumps(settings_to_toml(settings._raw_data))


@app.callback(invoke_without_command=True)
def settings(ctx: typer.Context) -> None:
    """Show the settings used by this application."""
    if ctx.invoked_subcommand == "generate":
        return
    if getattr(ctx, "obj", None) is None:
        typer.echo(f"Did not find a {SETTINGS_FILE} file")
        typer.echo("You should first run 'uv run confluence-plone settings generate'")
        raise typer.Exit(1)
    msg = "Settings used by this application"
    typer.echo(msg)
    typer.echo("-" * len(msg))
    current: t.ConfluenceSettings = ctx.obj.settings
    local_settings = f"Local settings: {current.config['filepath']}"
    typer.echo(local_settings)
    typer.echo("-" * len(local_settings))
    for line in dump_settings(current).split("\n"):
        typer.echo(line)


@app.command(name="generate")
def generate() -> None:
    """Generate a new settings file in the current directory."""
    path = Path(SETTINGS_FILE).resolve()
    if path.exists():
        typer.echo(f"File already exists: {path}")
        raise typer.Exit(1)
    path.write_text(dump_settings(get_default_settings()), encoding="utf-8")
    typer.echo(f"Generated a settings file at {path}")
