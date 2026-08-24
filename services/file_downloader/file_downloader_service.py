"""Standalone test for downloading a Google Drive folder to disk.

Deliberately self-contained - it does not read the setting table or any other
service, so it can be run on its own before the feature is wired into the app:

    python -m services.file_downloader.file_downloader_service

The folder, output directory and credentials are the constants below - edit
them to point the test somewhere else.

This module only walks the folder tree. What happens to a file once it is found
belongs to the DownloadableFile subclass that DownloadableFileFactory picks, one
per file, each in its own file:

    folder                          -> walks into it, keeping the folder structure
    Google Doc (native)             -> GoogleDocFile   - exported from Drive as markdown (.md)
    .docx                           -> DocxFile        - converted to markdown (.md)
    .pdf / .md / .txt               -> KeepAsIsFile    - downloaded byte for byte
    anything else                   -> UnsupportedFile - skipped
"""

import logging
import re
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from services.file_downloader.downloadable_file_factory import DownloadableFileFactory

logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_FILE = "C:/secrets/my_knowledge_drive_service_account.json"
FOLDER_ID = "1VWtBJ4KClTf7v8ULab7VN-45QK-au0DO"
OUTPUT_DIR = str(Path(__file__).resolve().parents[2] / "resources" / "test" / "downloaded_files")
SCOPE = "https://www.googleapis.com/auth/drive.readonly"


class FileDownloaderService:
    """Walks a Drive folder and hands every file it finds to the factory."""

    FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

    PAGE_SIZE = 1000
    INVALID_NAME_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

    def __init__(self, folder_id, output_dir, service_account_file, scope=SCOPE):
        self.folder_id = folder_id
        self.output_dir = Path(output_dir)
        credentials = Credentials.from_service_account_file(service_account_file, scopes=[scope])
        self.drive_service = build("drive", "v3", credentials=credentials, cache_discovery=False)

    def start_download(self):
        """Downloads the whole tree. Returns (downloaded, skipped, failed) counts."""
        logger.info(f"Downloading folder {self.folder_id} into {self.output_dir}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        downloaded_file_count, skipped_file_count, failed_file_count = self._download_files_in_folder(
            self.folder_id, self.output_dir
        )
        logger.info(
            f"Done. Downloaded: {downloaded_file_count}, "
            f"skipped: {skipped_file_count}, failed: {failed_file_count}"
        )
        return downloaded_file_count, skipped_file_count, failed_file_count

    def _download_files_in_folder(self, folder_id, target_dir):
        downloaded_file_count = 0
        skipped_file_count = 0
        failed_file_count = 0

        for file in self._list_folder_children(folder_id):
            name = self._sanitize_name(file["name"])
            mime_type = file["mimeType"]

            if mime_type == FileDownloaderService.FOLDER_MIME_TYPE:
                sub_dir = target_dir / name
                logger.info(f"Entering folder: {sub_dir}")
                sub_dir.mkdir(parents=True, exist_ok=True)
                sub_downloaded_file_count, sub_skipped_file_count, sub_failed_file_count = (
                    self._download_files_in_folder(file["id"], sub_dir)
                )
                downloaded_file_count += sub_downloaded_file_count
                skipped_file_count += sub_skipped_file_count
                failed_file_count += sub_failed_file_count
                continue

            downloadable_file = DownloadableFileFactory.get_file(
                self.drive_service, file["id"], name, mime_type, target_dir
            )
            try:
                is_downloaded = downloadable_file.download()
            except (HttpError, OSError, ValueError) as error:
                logger.error(f"Failed: {downloadable_file.get_output_file_path()} - {error}")
                failed_file_count += 1
                continue

            if is_downloaded:
                downloaded_file_count += 1
            else:
                skipped_file_count += 1

        return downloaded_file_count, skipped_file_count, failed_file_count

    def _list_folder_children(self, folder_id):
        """Every non-trashed child of the folder, one page at a time."""
        files = []
        page_token = None
        while True:
            response = self.drive_service.files().list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                pageSize=FileDownloaderService.PAGE_SIZE,
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()
            files += response.get("files", [])
            page_token = response.get("nextPageToken")
            if not page_token:
                return files

    @staticmethod
    def _sanitize_name(name):
        """Drive names may hold characters Windows will not accept in a path."""
        return FileDownloaderService.INVALID_NAME_CHARACTERS.sub("_", name).strip().rstrip(".") or "untitled"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    file_downloader_service = FileDownloaderService(FOLDER_ID, OUTPUT_DIR, SERVICE_ACCOUNT_FILE, SCOPE)
    file_downloader_service.start_download()
