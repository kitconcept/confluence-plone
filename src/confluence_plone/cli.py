"""Command line interface of ``confluence-plone``.

Example:

.. code-block:: shell

    uv run confluence-plone settings generate
    uv run confluence-plone analyze export.zip
    uv run confluence-plone convert export.zip ./import
"""

from confluence_plone._types import ContextObject
from confluence_plone.commands.analyze import app as app_analyze
from confluence_plone.commands.convert import app as app_convert
from confluence_plone.commands.info import app as app_info
from confluence_plone.commands.settings import app as app_settings
from confluence_plone.settings import get_settings

import typer


app = typer.Typer(no_args_is_help=True)

SUBCOMMANDS_IGNORE_SETTINGS = {"info", "settings"}


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Convert a Confluence XML space export into the ``plone.exportimport``
    format, ready to import into a ``kitconcept.intranet`` site.
    """
    try:
        settings = get_settings()
    except FileNotFoundError:
        if ctx.invoked_subcommand not in SUBCOMMANDS_IGNORE_SETTINGS:
            typer.echo("Did not find a confluence-plone.toml file.")
            typer.echo(
                "You should first run 'uv run confluence-plone settings generate'"
            )
            raise typer.Exit(1) from None
    else:
        ctx.obj = ContextObject(settings=settings)


app.add_typer(app_info, name="info")
app.add_typer(app_settings, name="settings")
app.add_typer(app_analyze)
app.add_typer(app_convert)


def cli() -> None:
    """Run the command line interface."""
    app()


__all__ = ["cli"]
