"""Convert Confluence dates to the ISO format used by ``plone.exportimport``."""

from datetime import UTC
from datetime import datetime
from zoneinfo import ZoneInfo


_FORMATS = ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d")


def parse_date(value: str, timezone: str = "UTC") -> datetime | None:
    """Parse a date from ``entities.xml``.

    Confluence writes dates as ``2024-04-22 16:35:21.231``, in the server's
    time zone and without saying which one it is.

    :param value: The date as written in the export.
    :param timezone: Name of the time zone of the export.
    :returns: An aware date, or ``None`` when the value is not a date.
    """
    value = value.strip()
    for date_format in _FORMATS:
        try:
            naive = datetime.strptime(value, date_format)
        except ValueError:
            continue
        return naive.replace(tzinfo=ZoneInfo(timezone))
    return None


def to_iso(value: str, timezone: str = "UTC") -> str | None:
    """Convert a date from ``entities.xml`` to ISO 8601, in UTC, to the second.

    :param value: The date as written in the export.
    :param timezone: Name of the time zone of the export.
    :returns: The date, for example ``2024-04-22T16:35:21+00:00``, or ``None``.
    """
    parsed = parse_date(value, timezone)
    if parsed is None:
        return None
    return parsed.astimezone(UTC).replace(microsecond=0).isoformat()


def to_js_iso(value: str, timezone: str = "UTC") -> str | None:
    """Convert a date to the format the Plate editor uses for comments.

    :param value: The date as written in the export.
    :param timezone: Name of the time zone of the export.
    :returns: The date, for example ``2024-04-22T16:35:21.231Z``, or ``None``.
    """
    parsed = parse_date(value, timezone)
    if parsed is None:
        return None
    utc = parsed.astimezone(UTC)
    return f"{utc:%Y-%m-%dT%H:%M:%S}.{utc.microsecond // 1000:03d}Z"
