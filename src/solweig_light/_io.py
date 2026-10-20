"""Small streaming I/O helpers shared by immutable artifact writers."""
import hashlib


class HashingWriter:
    """Forward sequential writes and hash exactly the bytes accepted by a stream.

    The caller owns the stream and its lifecycle. No readback is performed here;
    consumers still independently verify published artifacts when reopening.
    """
    def __init__(self, stream):
        self.stream = stream
        self.sha256 = hashlib.sha256()
        self.bytes_written = 0

    def write(self, data):
        count = self.stream.write(data)
        if count is None:
            raise OSError('Binary stream write returned no byte count')
        view = memoryview(data).cast('B')
        try:
            length = view.nbytes
            self.sha256.update(view[:count])
        finally:
            view.release()
        self.bytes_written += count
        if count != length:
            raise OSError('Short binary stream write')
        return count

    def flush(self):
        return self.stream.flush()

    def fileno(self):
        return self.stream.fileno()
