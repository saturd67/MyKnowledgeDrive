import logging
from os import mkdir
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
from services.DownloadFileService import DownloadFileService

logger = logging.getLogger(__name__)

class FetchFileService:
    FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
    SERVICE_ACCOUNT_FILE = "C:/secrets/my_knowledge_drive_service_account.json"

    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

    FOLDER_ID = "1VWtBJ4KClTf7v8ULab7VN-45QK-au0DO"

    def __init__(self, output_folder):
        self.output_folder = output_folder
        self.file_downloader = DownloadFileService(self.output_folder)

    def start_fetching(self):
        self.file_downloader.clear_existing_files()
        total_files = self._get_files("", self.FOLDER_ID)
        logger.info(f"Total Files: {total_files}")

    def _get_files(self, parent_path, file_id):
        count = 0
        service = build("drive", "v3", credentials=self.creds, cache_discovery=False)

        results = service.files().list(
            q=f"'{file_id}' in parents and trashed = false",
            fields="files(id, name, mimeType)"
        ).execute()

        files = results.get("files", [])

        for file in files:
            if file["mimeType"] == FetchFileService.FOLDER_MIME_TYPE:
                count += self._get_files(parent_path + ("\\" if parent_path else "") + file['name'], file["id"])
            else:
                count += 1
                self.file_downloader.download_file(service, parent_path, file)
                # logger.info(parent_path)
                # logger.info(f"Name: {file['name']}")
                # logger.info(f"ID: {file['id']}")
                # logger.info(f"Type: {file['mimeType']}")
                # logger.info("-" * 30)
        return count