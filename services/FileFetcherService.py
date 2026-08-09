import logging
import re
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials

from constant.settings import DRIVE_FOLDER_ID, DRIVE_SCOPE, DRIVE_SERVICE_ACCOUNT_FILE
from services.SettingService import settingService

logger = logging.getLogger(__name__)

class FileFetcherService:
    FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

    def __init__(self):
        # Read on construction, not at import time - the credentials file is
        # configurable now, and a missing one should fail the run, not the import.
        self.folder_id = settingService.get(DRIVE_FOLDER_ID)
        self.creds = Credentials.from_service_account_file(
            settingService.get_path(DRIVE_SERVICE_ACCOUNT_FILE),
            scopes=[settingService.get(DRIVE_SCOPE)]
        )

    def start_file_id_fetching(self):
        file_id_paths = self._get_file_id("", self.folder_id)
        return file_id_paths

    def _get_file_id(self, parent_path, file_id):
        service = build("drive", "v3", credentials=self.creds, cache_discovery=False)
        results = service.files().list(
            q=f"'{file_id}' in parents and trashed = false",
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()

        file_id_paths = []
        files = results.get("files", [])
        for file in files:
            next_path = parent_path + ("\\" if parent_path else "") + file['name']
            if file["mimeType"] == FileFetcherService.FOLDER_MIME_TYPE:
                file_id_paths += self._get_file_id(next_path, file["id"])
            else:
                logger.info(next_path)
                # logger.info(f"ID: {file['id']}")
                # logger.info(f"Type: {file['mimeType']}")
                next_path = next_path.rsplit(".", 1)[0]
                file_id_paths.append({"id": file["id"], "file": next_path, "modifiedTime": file.get("modifiedTime")})

        return file_id_paths

#     def __init__(self, output_folder):
#         self.file_downloader = DownloadFileService(output_folder)
#
#     def start_fetching(self):
#         self.file_downloader.clear_existing_files()
#         total_files = self._get_files("", self.FOLDER_ID)
#         logger.info(f"Total Files: {total_files}")
#
#     def _get_files(self, parent_path, file_id):
#         count = 0
#         service = build("drive", "v3", credentials=self.creds, cache_discovery=False)
#
#         results = service.files().list(
#             q=f"'{file_id}' in parents and trashed = false",
#             fields="files(id, name, mimeType)"
#         ).execute()
#
#         files = results.get("files", [])
#
#         for file in files:
#             if file["mimeType"] == FetchFileService.FOLDER_MIME_TYPE:
#                 count += self._get_files(parent_path + ("\\" if parent_path else "") + file['name'], file["id"])
#             else:
#                 count += 1
#                 self.file_downloader.download_file(parent_path, file)
#                 logger.info(parent_path)
#                 logger.info(f"Name: {file['name']}")
#                 logger.info(f"ID: {file['id']}")
#                 logger.info(f"Type: {file['mimeType']}")
#                 logger.info("-" * 30)
#         return count