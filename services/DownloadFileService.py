import logging
from pathlib import Path
import shutil

from googleapiclient.http import MediaIoBaseDownload

import io

logger = logging.getLogger(__name__)

class DownloadFileService:
    def __init__(self, output_folder):
        self.output_folder = output_folder
        output_folder_path = Path(self.output_folder)
        if not output_folder_path.exists():
            logger.info(f"Creating output folder: {output_folder}")
            output_folder_path.mkdir()

    def clear_existing_files(self):
        logger.info(f"Clearing: {self.output_folder}")
        shutil.rmtree(self.output_folder)
        output_main_folder_path = Path(self.output_folder)
        if not output_main_folder_path.exists():
            output_main_folder_path.mkdir()

    def sanitize_filename(self, filename):
        output = filename.replace("/", "_")
        return output

    def download_file(self, service, parent_path, file):
        folder = self.output_folder + "\\" + parent_path
        folder_path = Path(folder)
        if not folder_path.exists():
            logger.info(f"Creating parent folder: {folder}")
            folder_path.mkdir(parents=True, exist_ok=True)
        output_file = FileFactory.get_output_file(service, file)

        request = output_file.request()
        full_path_filename = self.sanitize_filename(folder + "\\" + file['name'] + output_file.extension())
        file_handler = io.FileIO(full_path_filename, "wb")

        downloader = MediaIoBaseDownload(file_handler, request)

        logger.info(f"Downloading file: {file['name']}")
        try:
            is_download_done = False
            status = None
            while not is_download_done:
                status, is_download_done = downloader.next_chunk()
            logger.info(f"File: {file['name']} {status}")
        except Exception as e:
            logger.error(f"Unable to download file: {full_path_filename}")
            logger.error(e)