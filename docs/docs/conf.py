# Configuration file for the Sphinx documentation builder.
# confluence-plone build configuration file


# -- Path setup --------------------------------------------------------------

from confluence_plone import __version__
from datetime import datetime
from packaging.version import Version


# -- Project information -----------------------------------------------------

project = "confluence-plone"
author = "kitconcept GmbH"
trademark_name = "kitconcept"
now = datetime.now()
year = str(now.year)
copyright = year  # noQA: A001


# The full version, including alpha/beta/rc tags.
release = __version__
# The short X.Y version.
version = "v" + (Version(str(release)).base_version)


# -- General configuration ----------------------------------------------------

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# Add any Sphinx extension module names here, as strings.
extensions = [
    "myst_parser",
    "notfound.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_reredirects",
    "sphinx_tippy",
    "sphinxcontrib.mermaid",
]

# If true, the Docutils Smart Quotes transform will be used to convert quotes
# and dashes to typographically correct entities.
smartquotes = False

# Options for the linkcheck builder
linkcheck_ignore = [
    # Ignore local and example URLs
    r"http://0.0.0.0",
    r"http://127.0.0.1",
    r"http://localhost",
    r"https://.*\.example\.org",
    # Ignore file downloads
    r"^/_static/",
    # Ignore pages that require authentication
    r"https://github.com/kitconcept/confluence-plone/issues/new",
    # Ignore github.com pages with anchors
    r"https://github.com/.*#.*",
]
linkcheck_allowed_redirects: dict[str, str] = {}
linkcheck_anchors = True
linkcheck_timeout = 5
linkcheck_retries = 1

# The suffix of source filenames.
source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}

# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns: list[str] = []

suppress_warnings: list[str] = []


# -- Options for HTML output -------------------------------------------------

html_theme = "plone_sphinx_theme"
html_logo = "_static/logo.svg"
html_favicon = "_static/favicon.ico"
html_sidebars = {
    "**": [
        "navbar-logo",
        "search-button-field",
        "sbt-sidebar-nav",
    ]
}
html_theme_options = {
    "article_header_start": ["toggle-primary-sidebar"],
    "footer_content_items": [
        "author",
        "copyright",
        "last-updated",
        "extra-footer",
        "icon-links",
    ],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/kitconcept/confluence-plone",
            "icon": "fa-brands fa-square-github",
            "type": "fontawesome",
            "attributes": {
                "target": "_blank",
                "rel": "noopener me",
                "class": "nav-link custom-fancy-css",
            },
        },
    ],
    "logo": {
        "text": "confluence-plone",
    },
    "navigation_with_keys": True,
    "path_to_docs": "docs/docs",
    "repository_branch": "main",
    "repository_url": "https://github.com/kitconcept/confluence-plone",
    "search_bar_text": "Search",
    "show_toc_level": 2,
    "use_edit_page_button": True,
    "use_issues_button": True,
    "use_repository_button": True,
}

# The name for this set of Sphinx documents.
html_title = f"{project} v{release}"

# If false, no index is generated.
html_use_index = True

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory.
html_static_path = [
    "_static",
]


# -- Options for autodoc ----------------------------------------------------

# Don't show class signature with the class' name.
autodoc_class_signature = "separated"
autodoc_member_order = "bysource"


# -- Options for myST markdown conversion to html -----------------------------

myst_enable_extensions = [
    "attrs_block",
    "attrs_inline",
    "colon_fence",
    "deflist",
    "html_image",
    "linkify",
    "strikethrough",
    "substitution",
]

myst_heading_anchors = 3

myst_substitutions: dict[str, str] = {}


# -- Intersphinx configuration ----------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "plone": ("https://6.docs.plone.org/", None),
}


# -- Mermaid configuration ----------------------------------
mermaid_version = "11.2.0"


# -- sphinx.ext.todo -----------------------
todo_include_todos = True


# -- sphinx-notfound-page configuration ----------------------------------
notfound_urls_prefix = ""
notfound_template = "404.html"


# -- sphinx-reredirects configuration ----------------------------------
redirects: dict[str, str] = {}


# -- sphinx-tippy configuration ----------------------------------
tippy_anchor_parent_selector = "article.bd-article"
tippy_enable_doitips = False
tippy_enable_wikitips = False
tippy_props = {
    "interactive": True,
    "placement": "auto-end",
}


# -- Options for HTML help output -------------------------------------------------

htmlhelp_basename = "confluence-plone Documentation"


# -- Options for LaTeX output -------------------------------------------------

latex_documents = [
    (
        "index",
        "confluence-ploneDocumentation.tex",
        "confluence-plone Documentation",
        "kitconcept GmbH",
        "manual",
    ),
]
latex_logo = "_static/logo.svg"
