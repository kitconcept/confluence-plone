"""Tests for payloads, the writer, the reports and the pipeline."""

#: Items written for the test export, by portal type.
TYPES = {"File": 1, "Image": 1, "WikiPage": 6, "Workspace": 1}

#: Report files written by a conversion.
REPORTS = ["items.csv", "issues.csv", "skipped.csv", "summary.json"]
