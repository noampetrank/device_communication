from threading import Event
from pydcomm.public.bugarpc import ReaderWriterStream


class GReaderWriterStream(ReaderWriterStream):
    """
    Interface for return object from a streaming call.
    Member functions:
        read, write, end_write
    """
    def __init__(self, stream_it, write_queue, end_write_sential):
        self.stream_it = stream_it
        self.write_queue = write_queue
        self.end_write_sential = end_write_sential
        self._end_write = Event()

    def read(self):
        """
        Receive value from server side.

        This is blocking until server sends a response, or closes the connection.
        """
        return next(self.stream_it).buf

    def write(self, value):
        """Write a value to the server."""
        assert not self._end_write.is_set(), "already called end_write"
        self.write_queue.put(value)

    def end_write(self):
        """Tell server that you're done writing."""
        self._end_write.set()
        self.write_queue.put(self.end_write_sential)

    def __del__(self):
        self.end_write()