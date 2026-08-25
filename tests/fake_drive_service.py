from tests.fake_drive_request import FakeDriveRequest


class FakeDriveService:
    """Stands in for the Drive v3 resource `build()` returns.

    Only the three calls the downloader makes are implemented: `files().list()`,
    `files().get_media()` and `files().export_media()`. `files()` returns the
    service itself, which is enough to satisfy the chained call.
    """

    def __init__(self, pages_by_folder_id, media_by_file_id=None, exports_by_file_id=None,
                 errors_by_file_id=None):
        """`pages_by_folder_id` maps a folder id to the pages of its listing -
        one list of file dicts per page, so pagination can be exercised."""
        self.pages_by_folder_id = pages_by_folder_id
        self.media_by_file_id = media_by_file_id or {}
        self.exports_by_file_id = exports_by_file_id or {}
        self.errors_by_file_id = errors_by_file_id or {}
        self.export_mime_types = []

    def files(self):
        return self

    def list(self, q, fields, pageSize, pageToken, supportsAllDrives, includeItemsFromAllDrives):
        folder_id = q.split("'")[1]
        pages = self.pages_by_folder_id.get(folder_id, [[]])
        page_index = 0 if pageToken is None else int(pageToken)
        payload = {"files": pages[page_index]}
        if page_index + 1 < len(pages):
            payload["nextPageToken"] = str(page_index + 1)
        return FakeDriveRequest(payload=payload)

    def get_media(self, fileId, supportsAllDrives):
        return FakeDriveRequest(
            content=self.media_by_file_id.get(fileId, b""),
            error=self.errors_by_file_id.get(fileId),
        )

    def export_media(self, fileId, mimeType):
        self.export_mime_types.append(mimeType)
        return FakeDriveRequest(
            content=self.exports_by_file_id.get(fileId, b""),
            error=self.errors_by_file_id.get(fileId),
        )
