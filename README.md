# confluence-plone

Convert a Confluence XML space export into the `plone.exportimport` format, ready to import into a site built with `kitconcept.intranet`.

- Each space becomes a Workspace.
- Each page becomes a Wiki Page, with its content converted from the Confluence storage format to Plate.
- Attachments become File and Image items inside their page.
- Footer comments become Plone comments, and inline comments become Wiki Page discussions.
- Every lossy step is reported as data, in CSV and JSON reports.

The conversion never connects to Confluence or to Plone: it reads an export file and writes a directory, so it can run as often as a migration needs.

## Usage

`confluence-plone` needs Python 3.14 and [uv](https://docs.astral.sh/uv/).

```shell
uv run confluence-plone settings generate     # write confluence-plone.toml
uv run confluence-plone analyze export.zip    # what the export holds, and which macros it uses
uv run confluence-plone convert export.zip ./import
```

Then import the result into the site, from its backend directory.

```shell
uv run plone-importer instance/etc/zope.conf Plone /path/to/import
```

The [documentation](https://github.com/kitconcept/confluence-plone/tree/main/docs) covers the whole migration, the settings, the reports, and what each Confluence element and macro becomes.

## Development

```shell
make install        # create the virtual environment
make test           # run the tests
make test-coverage  # run the tests, and require 100% coverage
make format         # format the code
make lint           # ruff, pyroma, check-python-versions, and mypy
make docs-html      # build the documentation into docs/_build/html
make docs-livehtml  # build the documentation and serve it on port 8050
make docs-vale      # check the documentation with Vale
```

Every change needs a news fragment in `news/`, for [towncrier](https://towncrier.readthedocs.io/).

## License

The project is licensed under the GPLv2.
