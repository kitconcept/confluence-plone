from confluence_plone import _types as t
from confluence_plone import reports

import csv
import json
import pytest


class TestInventory:
    @pytest.fixture
    def data(self, export) -> dict:
        return reports.inventory(export)

    def test_totals(self, data):
        assert data["totals"] == {
            "spaces": 3,
            "pages": 7,
            "blog_posts": 1,
            "historical_versions": 1,
            "attachments": 3,
            "footer_comments": 3,
            "inline_comments": 2,
            "users": 3,
            "labelled_content": 1,
            "restricted_content": 1,
        }

    def test_spaces(self, data):
        dev = next(space for space in data["spaces"] if space["key"] == "DEV")
        assert dev["contents"] == {
            "blogpost:current": 1,
            "page:current": 6,
            "page:deleted": 1,
            "page:draft": 1,
            "page:historical": 1,
        }
        assert dev["attachments"] == 2
        assert dev["attachments_size"] == 93
        assert dev["permissions"] == 2

    def test_macros(self, data):
        assert data["macros"] == [
            {"macro": "children", "pages": 1, "uses": 1, "example": "Home"},
            {"macro": "excerpt", "pages": 1, "uses": 1, "example": "Snippets"},
            {"macro": "include", "pages": 1, "uses": 1, "example": "Setup Guide"},
            {"macro": "info", "pages": 1, "uses": 1, "example": "Home"},
        ]

    def test_other_sections(self, data):
        assert data["body_types"] == {"1": 1, "2": 9}
        assert data["classes"]["Page"] == 10
        assert data["descriptor"]["spaceKey"] == "DEV"
        assert data["warnings"] == []


class TestWriters:
    def test_write_json(self, tmp_path):
        path = reports.write_json({"a": 1}, tmp_path / "sub" / "x.json")
        assert json.loads(path.read_text()) == {"a": 1}

    def test_write_dataclasses(self, tmp_path):
        issues = [t.Issue("1", t.Severity.WARNING, "code", "detail")]
        path = reports.write_dataclasses(issues, t.Issue, tmp_path / "issues.csv")
        rows = list(csv.DictReader(path.read_text().splitlines()))
        assert rows == [
            {
                "source_id": "1",
                "severity": "warning",
                "code": "code",
                "detail": "detail",
            }
        ]


class TestItemStatus:
    @pytest.mark.parametrize(
        "severities,expected",
        [
            ([], "ok"),
            ([t.Severity.INFO], "ok"),
            ([t.Severity.INFO, t.Severity.WARNING], "warning"),
            ([t.Severity.WARNING, t.Severity.ERROR], "error"),
        ],
    )
    def test_status(self, severities, expected):
        issues = [t.Issue("1", severity, "code") for severity in severities]
        assert reports.item_status(issues) == expected
