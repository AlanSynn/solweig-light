import hashlib
import io

import numpy as np
import pytest

from solweig_light._io import HashingWriter


def test_exact_accepted_bytes_and_no_stream_ownership():
    stream = io.BytesIO()
    writer = HashingWriter(stream)
    writer.write(b'header')
    writer.write(memoryview(np.arange(4, dtype=np.uint8)))
    writer.flush()
    assert writer.bytes_written == 10
    assert writer.sha256.hexdigest() == hashlib.sha256(stream.getvalue()).hexdigest()
    assert not stream.closed


def test_partial_write_hashes_accepted_prefix_and_fails():
    class Partial(io.BytesIO):
        def write(self, data):
            return super().write(data[:2])
    stream = Partial()
    writer = HashingWriter(stream)
    with pytest.raises(OSError, match='Short'):
        writer.write(b'abcde')
    assert writer.bytes_written == 2
    assert writer.sha256.hexdigest() == hashlib.sha256(b'ab').hexdigest()
