from confluence_plone.utils.dates import parse_date
from confluence_plone.utils.dates import to_iso
from confluence_plone.utils.dates import to_js_iso

import pytest


class TestParseDate:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("2024-04-22 16:35:21.231", "2024-04-22 16:35:21.231000+00:00"),
            ("2024-04-22 16:35:21", "2024-04-22 16:35:21+00:00"),
            ("2024-04-22", "2024-04-22 00:00:00+00:00"),
        ],
    )
    def test_parse(self, value, expected):
        assert str(parse_date(value)) == expected

    @pytest.mark.parametrize("value", ["", "not a date", "22.04.2024"])
    def test_invalid(self, value):
        assert parse_date(value) is None


class TestToIso:
    @pytest.mark.parametrize(
        "value,timezone,expected",
        [
            ("2024-04-22 16:35:21.231", "UTC", "2024-04-22T16:35:21+00:00"),
            ("2024-04-22 16:35:21.231", "Europe/Berlin", "2024-04-22T14:35:21+00:00"),
            ("2024-01-22 16:35:21", "Europe/Berlin", "2024-01-22T15:35:21+00:00"),
            ("nope", "UTC", None),
        ],
    )
    def test_to_iso(self, value, timezone, expected):
        assert to_iso(value, timezone) == expected


class TestToJsIso:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("2024-04-22 16:35:21.231", "2024-04-22T16:35:21.231Z"),
            ("2024-04-22 16:35:21", "2024-04-22T16:35:21.000Z"),
            ("nope", None),
        ],
    )
    def test_to_js_iso(self, value, expected):
        assert to_js_iso(value) == expected
