from confluence_plone import _types as t
from confluence_plone import pipeline
from confluence_plone.utils.console import console
from confluence_plone.utils.console import report
from pathlib import Path
from rich.table import Table
from typing import Annotated

import typer


app = typer.Typer()


@app.command()
def analyze(
    ctx: typer.Context,
    src: Annotated[
        Path, typer.Argument(help="Confluence XML export: a zip file or a directory")
    ],
    dst: Annotated[
        Path | None,
        typer.Option(help="Directory for the reports (defaults to the settings)"),
    ] = None,
) -> None:
    """Write an inventory of a Confluence export, with the macros it uses."""
    settings: t.ConfluenceSettings = ctx.obj.settings
    reports_dir = dst or settings.config["reports_location"]
    try:
        data, paths = pipeline.analyze(src, reports_dir, report)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from None
    table = Table(title="Inventory")
    table.add_column("Content")
    table.add_column("Total", justify="right")
    for name, value in data["totals"].items():
        table.add_row(name.replace("_", " ").capitalize(), str(value))
    console.print(table)
    macros = Table(title="Macros (top 20)")
    macros.add_column("Macro")
    macros.add_column("Pages", justify="right")
    macros.add_column("Uses", justify="right")
    for row in data["macros"][:20]:
        macros.add_row(row["macro"], str(row["pages"]), str(row["uses"]))
    console.print(macros)
    for path in paths:
        console.print(f"Wrote {path}")
