"""Build Plone ids and UIDs for Confluence content."""

import re
import unicodedata
import uuid


MAX_ID_LENGTH = 80

NAMESPACE = uuid.UUID("6f1c3c2e-7c5b-4f0e-9a51-3d1f6f2b8c47")
"""Namespace for the UIDs, so the same export always yields the same UIDs."""

_NOT_ALLOWED = re.compile(r"[^a-z0-9._-]+")
_REPEATED = re.compile(r"-{2,}")


def normalize_id(value: str, fallback: str = "item") -> str:
    """Turn a title or a file name into a Plone id.

    Accents are removed, the result is lower case, and every run of other
    characters becomes one dash.

    :param value: The title or file name.
    :param fallback: Returned when nothing is left of ``value``.
    :returns: The id.
    """
    ascii_value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    result = _NOT_ALLOWED.sub("-", ascii_value.lower())
    result = _REPEATED.sub("-", result).strip("-._")
    if len(result) > MAX_ID_LENGTH:
        result = result[:MAX_ID_LENGTH].rstrip("-._")
    return result or fallback


def unique_id(value: str, existing: set[str]) -> str:
    """Return ``value``, or ``value`` with a numeric suffix, not in ``existing``.

    The returned id is added to ``existing``.

    :param value: The wanted id.
    :param existing: Ids already used in the same container.
    :returns: An id not used before.
    """
    candidate = value
    if candidate in existing:
        stem, dot, suffix = value.rpartition(".")
        if not dot or not stem:
            stem, suffix = value, ""
        counter = 1
        while candidate in existing:
            candidate = f"{stem}-{counter}{'.' + suffix if suffix else ''}"
            counter += 1
    existing.add(candidate)
    return candidate


def make_uid(kind: str, source_id: str) -> str:
    """Return a stable UID for a Confluence object.

    :param kind: Kind of object, for example ``page``.
    :param source_id: Id of the Confluence object.
    :returns: A 32-character hexadecimal UID.
    """
    return uuid.uuid5(NAMESPACE, f"{kind}:{source_id}").hex
