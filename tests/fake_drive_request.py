class FakeDriveRequest:
    """One request the fake Drive resource hands back.

    Serves both shapes the downloader uses: a listing call, which is executed
    for a payload, and a media call, which is handed to MediaIoBaseDownload
    for its bytes.
    """

    def __init__(self, payload=None, content=None, error=None):
        self.payload = payload
        self.content = content
        self.error = error

    def execute(self):
        if self.error is not None:
            raise self.error
        return self.payload
