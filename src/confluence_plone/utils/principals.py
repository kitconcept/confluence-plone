"""Map Confluence users to Plone principals.

Users are not created: the site's user directory (often LDAP) owns them.
A Confluence user becomes the id of an existing principal, chosen by an
explicit mapping file first, and by the configured strategy otherwise.
"""

from collections import Counter
from confluence_plone import _types as t
from pathlib import Path

import csv


STRATEGIES = ("username", "email", "key")


def load_mapping(path: Path) -> dict[str, str]:
    """Read a mapping file with the columns ``confluence`` and ``principal``.

    :param path: The CSV file.
    :returns: Principal ids by lower-case Confluence key, name or email.
    :raises FileNotFoundError: When the file does not exist.
    :raises ValueError: When a column is missing.
    """
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        if not {"confluence", "principal"} <= fields:
            raise ValueError(f"{path} needs the columns 'confluence' and 'principal'")
        return {
            row["confluence"].strip().lower(): row["principal"].strip()
            for row in reader
            if row["confluence"].strip() and row["principal"].strip()
        }


class PrincipalMapper:
    """Find the Plone principal for a Confluence user.

    :param export: The export, to look users up.
    :param settings: The settings.
    :param mapping: Explicit mapping, by lower-case key, name or email.
    :raises ValueError: When the strategy in the settings is unknown.
    """

    unmapped: Counter[str]
    """Confluence users mapped to the default principal, and how often."""

    def __init__(
        self,
        export: t.ConfluenceExport,
        settings: t.ConfluenceSettings,
        mapping: dict[str, str] | None = None,
    ):
        self.export = export
        self.default = settings.principals["default"]
        self.strategy = settings.principals["strategy"]
        if self.strategy not in STRATEGIES:
            raise ValueError(
                f"Unknown principals strategy '{self.strategy}', "
                f"use one of {', '.join(STRATEGIES)}"
            )
        self.mapping = mapping or {}
        self.unmapped = Counter()

    def user(self, value: str | None) -> t.User | None:
        """Find a Confluence user by key or name.

        :param value: A user key or a user name.
        :returns: The user, or ``None``.
        """
        return self.export.user(value)

    def principal(self, value: str | None) -> str:
        """Return the principal id for a Confluence user.

        :param value: A user key or a user name.
        :returns: The principal id, or the default principal.
        """
        user = self.user(value)
        candidates = [value or ""]
        if user is not None:
            candidates = [user.key, user.name, user.email]
        for candidate in candidates:
            if candidate and (principal := self.mapping.get(candidate.lower())):
                return principal
        if user is not None:
            match self.strategy:
                case "username":
                    principal = user.name
                case "email":
                    principal = user.email
                case _:
                    principal = user.key
            if principal:
                return principal
        if value:
            self.unmapped[value] += 1
        return self.default

    def title(self, value: str | None) -> str:
        """Return the name to show for a Confluence user.

        :param value: A user key or a user name.
        :returns: The display name, or the principal id.
        """
        user = self.user(value)
        return user.title if user is not None else self.principal(value)
