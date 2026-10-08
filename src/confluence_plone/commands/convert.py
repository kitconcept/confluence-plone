from confluence_plone import _types as t
from confluence_plone import pipeline
from confluence_plone.utils.console import console
from confluence_plone.utils.console import report
from pathlib import Path
from rich.table import Table
from typing import Annotated

import shutil
import typer


app = typer.Typer()


@app.command()
def convert(
    ctx: typer.Context,
    src: Annotated[
        Path, typer.Argument(help="Confluence XML export: a zip file or a directory")
    ],
    dst: Annotated[
        Path, typer.Argument(help="Destination directory, in plone.exportimport format")
    ],
    clean_up: Annotated[
        bool, typer.Option(help="Remove the existing content of the destination first")
    ] = False,
) -> None:
    """Convert a Confluence export into the ``plone.exportimport`` format."""
    settings: t.ConfluenceSettings = ctx.obj.settings
    if dst.exists() and any(dst.iterdir()):
        if not clean_up:
            console.print(
                f"[red]{dst} is not empty; use --clean-up to replace it[/red]"
            )
            raise typer.Exit(1)
        console.print(f"Removing the existing content of {dst}")
        shutil.rmtree(dst)
    try:
        result = pipeline.convert(src, dst, settings, report)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from None
    summary = result.summary()
    table = Table(title="Conversion")
    table.add_column("Result")
    table.add_column("Total", justify="right")
    for portal_type, total in summary["items"].items():
        table.add_row(portal_type, str(total))
    table.add_row("Skipped", str(summary["skipped"]))
    table.add_row("Footer comments", str(summary["footer_comments"]))
    table.add_row("Inline discussions", str(summary["inline_discussions"]))
    for severity, total in summary["issues"].items():
        table.add_row(f"Issues: {severity}", str(total))
    console.print(table)
    if result.unmapped_users:
        console.print(
            f"[yellow]{len(result.unmapped_users)} Confluence users were mapped to "
            f"'{settings.principals['default']}'[/yellow]"
        )
    console.print(f"Wrote the content to {dst.resolve()}")
    for path in result.reports:
        console.print(f"Wrote {path}")
