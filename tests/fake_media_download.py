class FakeMediaIoBaseDownload:
    """Stands in for googleapiclient's MediaIoBaseDownload.

    The real one needs a live http object on the request. This one just copies
    the bytes the fake request carries, in a single chunk, and raises whatever
    error the request was primed with - which is what a failing download looks
    like to the caller.
    """

    def __init__(self, buffer, request):
        self.buffer = buffer
        self.request = request

    def next_chunk(self):
        if self.request.error is not None:
            raise self.request.error
        self.buffer.write(self.request.content)
        return None, True
