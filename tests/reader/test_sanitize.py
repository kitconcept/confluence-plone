from confluence_plone.reader.sanitize import SanitizingStream

import io
import pytest


class TestSanitizingStream:
    @pytest.mark.parametrize(
        "data,expected",
        [
            (b"<a>ok</a>", b"<a>ok</a>"),
            (b"<a>back\x08space</a>", b"<a>backspace</a>"),
            (b"<a>\x1c\x00\x0b\x0c</a>", b"<a></a>"),
            (b"<a>\ttab\nnew\rline</a>", b"<a>\ttab\nnew\rline</a>"),
            ("<a>café ​</a>".encode(), "<a>café ​</a>".encode()),
        ],
    )
    def test_read_all(self, data: bytes, expected: bytes):
        stream = SanitizingStream(io.BytesIO(data))
        assert stream.read() == expected
        assert stream.removed == len(data) - len(expected)

    def test_skips_chunks_made_of_forbidden_bytes(self):
        stream = SanitizingStream(io.BytesIO(b"ab\x01\x02\x03cd"))
        assert stream.read(2) == b"ab"
        # The next chunk is only forbidden bytes: the one after it is returned
        assert stream.read(3) == b"cd"
        assert stream.read(3) == b""
        assert stream.removed == 3

    def test_empty(self):
        stream = SanitizingStream(io.BytesIO(b""))
        assert stream.read() == b""
