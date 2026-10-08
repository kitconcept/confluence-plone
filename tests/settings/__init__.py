"""Tests for the settings."""

#: A local settings file overriding a few values.
LOCAL_SETTINGS = """
[config]
reports_location = "out/reports"

[source]
spaces = ["DEV", "OPS"]

[target]
base_path = "/wikis"

[macros]
jira_url = "https://jira.example.org"
"""
