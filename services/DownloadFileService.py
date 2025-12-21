import logging
from pathlib import Path
import shutil

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

    def download_file(self, parent_path, file):
        folder = self.output_folder + "\\" + parent_path
        output_path = Path(folder)
        if not output_path.exists():
            logger.info(f"Creating parent folder: {folder}")
            output_path.mkdir(parents=True, exist_ok=True)
