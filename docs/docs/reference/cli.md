---
myst:
  html_meta:
    "description": "The commands and options of the confluence-plone command line."
    "property=og:description": "The confluence-plone command line"
    "property=og:title": "Command line | confluence-plone"
    "keywords": "confluence-plone, CLI, command line, analyze, convert, settings, info"
---

(reference-cli)=

# Command line

<!-- source: src/confluence_plone/cli.py, src/confluence_plone/commands/ -->

```shell
uv run confluence-plone [COMMAND] [ARGS]
```

Every command reads `confluence-plone.toml` from the current directory.
`analyze` and `convert` exit with an error when the file does not exist; `info` and `settings` run without it.

| Command | Arguments and options | What it does |
| --- | --- | --- |
| `info` | | Prints the version of `confluence-plone` and of its main dependencies. |
| `settings` | | Prints the settings file in use, and every setting with its value. |
| `settings generate` | | Writes a `confluence-plone.toml` with the default settings. Exits with an error when the file exists. |
| `analyze` | `SRC` | Reads the export and writes `inventory.json` and `macros.csv`. |
| | `--dst PATH` | Directory for the reports. Defaults to `reports_location`. |
| `convert` | `SRC DST` | Converts the export into `DST`, and writes the conversion reports. |
| | `--clean-up` | Removes the content of `DST` first. Without it, a non-empty `DST` is an error. |

`SRC` is a Confluence XML export: a zip file, a directory with the unpacked zip, or the path of its `entities.xml`.

Every command accepts `--help`.

## Exit status

The commands exit with `0` on success, and with `1` when:

- the settings file is missing;
- the export, or the mapping file, cannot be found;
- the mapping file lacks a column, or the `strategy` setting is unknown;
- the destination of `convert` is not empty, and `--clean-up` is not given.

A conversion with issues, errors included, still exits with `0`: issues are reported, not raised.

## Related

- {doc}`settings`
- {doc}`reports`
