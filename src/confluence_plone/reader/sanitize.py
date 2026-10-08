"""Remove the bytes that XML 1.0 forbids from a stream.

Real Confluence exports are not always well-formed: page titles and bodies
can carry ASCII control characters (a backspace, ``ASCII 28``) that XML 1.0
does not allow anywhere, not even in a CDATA section. A strict parser stops
at the first one. Each of those characters is a single byte in UTF-8, and no
byte of a multi-byte UTF-8 sequence falls in that range, so they can be
removed byte by byte without decoding the stream.
"""

from typing import BinaryIO

import re


INVALID_XML_BYTES = re.compile(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]")
"""Control characters forbidden by XML 1.0 (tab, newline and return are fine)."""


class SanitizingStream:
    """A read-only binary stream that drops the bytes XML 1.0 forbids.

    :param stream: The stream to read from.
    """

    removed: int
    """Number of bytes removed so far."""

    def __init__(self, stream: BinaryIO):
        self._stream = stream
        self.removed = 0

    def read(self, size: int = -1) -> bytes:
        """Read up to ``size`` bytes, without the forbidden ones.

        An empty result means the end of the stream: when a whole chunk is
        made of forbidden bytes, the next chunk is read instead.

        :param size: Number of bytes to read from the underlying stream.
            ``-1`` reads everything.
        :returns: The sanitized bytes.
        """
        while True:
            data = self._stream.read(size)
            if not data:
                return b""
            clean = INVALID_XML_BYTES.sub(b"", data)
            self.removed += len(data) - len(clean)
            if clean:
                return clean
