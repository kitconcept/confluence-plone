"""Write the result in the ``plone.exportimport`` layout.

::

    <destination>/
    ├── content/
    │   ├── __metadata__.json
    │   └── <UID>/
    │       ├── data.json
    │       └── file/<filename>      (or image/<filename>)
    ├── discussions.json
    └── redirects.json               (when enabled)

``plone.exportimport`` creates the items in the order of ``_data_files_`` in
``__metadata__.json``, and finds each parent by the path in ``@id``, so
parents are always listed before their children.
"""

from confluence_plone import _types as t
from pathlib import Path
from typing import Any
from typing import BinaryIO

import orjson
import shutil


EXPORTIMPORT_VERSION = "1.0.0"


def json_dumps(data: Any) -> bytes:
    """Serialize data as indented JSON.

    :param data: The data.
    :returns: UTF-8 encoded JSON.
    """
    return orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)


def safe_filename(filename: str, fallback: str) -> str:
    """Return a file name that is safe to use on disk.

    :param filename: The original file name.
    :param fallback: Used when nothing is left of ``filename``.
    :returns: The file name, without path separators.
    """
    name = filename.replace("/", "_").replace("\\", "_").strip(". ")
    return name or fallback


class ExportWriter:
    """Write items, blobs and metadata to a destination directory.

    :param dst: The destination directory. It is created when missing.
    """

    def __init__(self, dst: Path):
        self.dst = dst
        self.content = dst / "content"
        self.content.mkdir(parents=True, exist_ok=True)
        self.data_files: list[str] = []
        self.blob_files: list[str] = []
        self.ordering: dict[str, int] = {}
        self.local_roles: dict[str, dict] = {}

    def write_blob(
        self, item: t.PlannedItem, field_name: str, filename: str, stream: BinaryIO
    ) -> str:
        """Copy the binary of an attachment.

        :param item: The planned attachment.
        :param field_name: ``file`` or ``image``.
        :param filename: Name of the file.
        :param stream: Stream with the binary.
        :returns: The blob path, relative to the content directory.
        """
        folder = self.content / item.uid / field_name
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / filename).open("wb") as target:
            shutil.copyfileobj(stream, target)
        blob_path = f"{item.uid}/{field_name}/{filename}"
        self.blob_files.append(blob_path)
        return blob_path

    def write_item(self, item: t.PlannedItem, data: t.PloneItem, owner: str) -> Path:
        """Write the ``data.json`` of an item, and record its metadata.

        :param item: The planned item.
        :param data: The payload.
        :param owner: Principal that gets the ``Owner`` local role.
        :returns: The path of the written file.
        """
        folder = self.content / item.uid
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "data.json"
        path.write_bytes(json_dumps(data))
        self.data_files.append(f"{item.uid}/data.json")
        self.ordering[item.uid] = item.position
        self.local_roles[item.uid] = {"local_roles": {owner: ["Owner"]}}
        return path

    def write_metadata(self) -> Path:
        """Write ``content/__metadata__.json``.

        :returns: The path of the written file.
        """
        metadata = {
            "__version__": EXPORTIMPORT_VERSION,
            "_blob_files_": self.blob_files,
            "_data_files_": self.data_files,
            "default_page": {},
            "local_permissions": {},
            "local_roles": self.local_roles,
            "ordering": self.ordering,
            "relations": [],
        }
        path = self.content / "__metadata__.json"
        path.write_bytes(json_dumps(metadata))
        return path

    def write_json(self, name: str, data: Any) -> Path:
        """Write a JSON file at the root of the destination.

        :param name: File name, for example ``discussions.json``.
        :param data: The data.
        :returns: The path of the written file.
        """
        path = self.dst / name
        path.write_bytes(json_dumps(data))
        return path
