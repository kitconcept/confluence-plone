# confluence-plone documentation

The documentation of `confluence-plone`, built with Sphinx, MyST, and the [Plone Sphinx Theme](https://github.com/plone/plone-sphinx-theme).
It follows the [Diátaxis](https://diataxis.fr/) framework: concepts, how-to guides, and reference.

## Prerequisites

[uv](https://docs.astral.sh/uv/) manages the Python version and the dependencies.

## Build the documentation

Run these commands from this directory, or the `docs-*` targets of the `Makefile` at the repository root.

```shell
make install          # create the virtual environment
make html             # build the HTML documentation into _build/html
make livehtml         # build, serve on port 8050, and rebuild on changes
make vale             # check spelling, grammar, and style
make linkcheckbroken  # check for broken links
make test             # vale, linkcheckbroken, and doctest
```

The virtual environment installs `confluence-plone` from the parent directory as an editable dependency, so the API reference always documents the current source.

## Conventions

- Write one sentence per line; never wrap at a column.
- Every page starts with `html_meta` frontmatter, then a reference label, then one H1.
- Em dashes take no spaces.
- Add domain vocabulary to `styles/config/vocabularies/Base/accept.txt` only when it is a real term.
