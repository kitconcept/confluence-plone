"""Access the files of a Confluence XML export.

An export is a zip file holding ``entities.xml``, ``exportDescriptor.properties``
and an ``attachments/`` tree. The same layout, unzipped into a directory, is
accepted too, and so is the path of an ``entities.xml`` file.

Attachments are stored as ``attachments/<container id>/<attachment id>/<version>``,
where the file named after the version number *is* the binary. Real exports
sometimes put a file under the wrong container, so files are looked up by
attachment id first, and the container only breaks ties.
"""

from collections import defaultdict
from pathlib import Path
from types import TracebackType
from typing import BinaryIO
from typing import Self

import zipfile


ENTITIES = "entities.xml"
DESCRIPTOR = "exportDescriptor.properties"


class ExportSource:
    """A Confluence XML export on disk.

    Use it as a context manager, so a zip file is closed afterwards.

    :param path: A zip file, a directory, or an ``entities.xml`` file.
    :raises FileNotFoundError: When ``path`` does not exist, or has no
        ``entities.xml``.
    """

    path: Path
    _zip: zipfile.ZipFile | None
    _root: Path | None
    _attachments: dict[str, dict[str, list[tuple[str, str]]]]
    """``{attachment id: {version: [(container id, member name)]}}``."""

    def __init__(self, path: Path):
        path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist")
        self.path = path
        self._zip = None
        self._root = None
        if path.is_file() and zipfile.is_zipfile(path):
            self._zip = zipfile.ZipFile(path)
        elif path.is_file():
            self._root = path.parent
        else:
            self._root = path
        if ENTITIES not in self._names():
            self.close()
            raise FileNotFoundError(f"No {ENTITIES} found in {path}")
        self._attachments = self._index_attachments()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the zip file, if any."""
        if self._zip is not None:
            self._zip.close()

    def _names(self) -> list[str]:
        """Return the names of all files, relative to the export root.

        :returns: File names, with ``/`` as separator.
        """
        if self._zip is not None:
            return [name for name in self._zip.namelist() if not name.endswith("/")]
        root = self._root
        assert root is not None  # noQA: S101
        return [
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        ]

    def _index_attachments(self) -> dict[str, dict[str, list[tuple[str, str]]]]:
        """Index the files under ``attachments/`` by attachment id and version.

        :returns: The index.
        """
        index: dict[str, dict[str, list[tuple[str, str]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for name in self._names():
            parts = name.split("/")
            if len(parts) == 4 and parts[0] == "attachments":
                _, container_id, attachment_id, version = parts
                index[attachment_id][version].append((container_id, name))
        return index

    def open(self, name: str) -> BinaryIO:
        """Open a file of the export for reading.

        :param name: File name, relative to the export root.
        :returns: A binary stream.
        """
        if self._zip is not None:
            return self._zip.open(name)  # type: ignore[return-value]
        root = self._root
        assert root is not None  # noQA: S101
        return (root / name).open("rb")

    def open_entities(self) -> BinaryIO:
        """Open ``entities.xml``.

        :returns: A binary stream.
        """
        return self.open(ENTITIES)

    def descriptor(self) -> dict[str, str]:
        """Read ``exportDescriptor.properties``.

        :returns: The properties, or an empty dictionary without the file.
        """
        if DESCRIPTOR not in self._names():
            return {}
        with self.open(DESCRIPTOR) as stream:
            lines = stream.read().decode("utf-8", errors="replace").splitlines()
        result = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip()
        return result

    def find_attachment(
        self, container_id: str | None, attachment_id: str, version: int
    ) -> str | None:
        """Find the file holding one version of an attachment.

        :param container_id: Id of the content the file is attached to.
        :param attachment_id: Id of the attachment.
        :param version: Version wanted. When it is missing, the highest
            version found is used.
        :returns: The file name, or ``None`` when no file was found.
        """
        versions = self._attachments.get(attachment_id)
        if not versions:
            return None
        candidates = versions.get(str(version))
        if not candidates:
            numeric = [v for v in versions if v.isdigit()]
            latest = max(numeric, key=int) if numeric else sorted(versions)[-1]
            candidates = versions[latest]
        for candidate_container, name in candidates:
            if candidate_container == container_id:
                return name
        return candidates[0][1]
