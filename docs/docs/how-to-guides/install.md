---
myst:
  html_meta:
    "description": "How to install confluence-plone with uv."
    "property=og:description": "How to install confluence-plone"
    "property=og:title": "Install confluence-plone | confluence-plone"
    "keywords": "confluence-plone, install, uv, Python 3.14"
---

(how-to-install)=

# Installation

`confluence-plone` needs Python 3.14.
It is a command line tool, and does not need to be installed in the Plone site it migrates to.

## From a checkout

[uv](https://docs.astral.sh/uv/) installs the Python version and the dependencies.

```shell
git clone https://github.com/kitconcept/confluence-plone.git
cd confluence-plone
make install
```

Then check the installation.

```shell
uv run confluence-plone info
```

## In a migration project

To keep the settings, the mapping file, and the reports of one migration together, create a project that depends on `confluence-plone`.

```shell
uv init --python 3.14 acme-migration
cd acme-migration
uv add "confluence-plone @ git+https://github.com/kitconcept/confluence-plone.git"
uv run confluence-plone info
```

Run every other command of this documentation from that directory: the settings file and the reports are read from, and written to, the current directory.

## Next steps

- {doc}`migrate`
- {doc}`configure`
