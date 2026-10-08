---
myst:
  html_meta:
    "description": "How to create and edit the confluence-plone.toml settings file."
    "property=og:description": "Configure confluence-plone"
    "property=og:title": "Configure a conversion | confluence-plone"
    "keywords": "confluence-plone, settings, confluence-plone.toml, configuration"
---

(how-to-configure)=

# Configure a conversion

`confluence-plone` reads its settings from a `confluence-plone.toml` file in the current directory.
The `analyze` and `convert` commands refuse to run without one.

## Create the settings file

```shell
uv run confluence-plone settings generate
```

This writes `confluence-plone.toml` with every setting and its default value.
It does not overwrite an existing file.

## Edit the settings

Change only what this migration needs; a setting missing from the file keeps its default value.
The settings that most migrations change are these.

```toml
[source]
# Convert these spaces only
spaces = ["DEV", "OPS"]

[target]
# Create the workspaces inside an existing folder of the site
base_path = "/wikis"

[principals]
default = "migration-admin"
mapping_file = "users.csv"

[macros]
jira_url = "https://jira.example.org"
```

{doc}`/reference/settings` describes every setting.

## Check the settings

```shell
uv run confluence-plone settings
```

This prints the path of the settings file in use, and every setting with its value, defaults included.

## Next steps

- {doc}`analyze`
- {doc}`map-users`
