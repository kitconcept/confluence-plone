import typer


app = typer.Typer()


@app.callback(invoke_without_command=True)
def info() -> None:
    """Show the version of ``confluence-plone`` and of its main dependencies."""
    from confluence_plone import PACKAGE_NAME
    from confluence_plone import __version__
    from importlib.metadata import version

    package_info = f"{PACKAGE_NAME} - {__version__}"
    typer.echo(package_info)
    typer.echo("=" * len(package_info))
    typer.echo("")
    typer.echo("Dependencies:")
    for name in ("lxml", "typer", "dynaconf"):
        typer.echo(f" - {name}: {version(name)}")
