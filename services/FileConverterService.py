import components.FileManager
import constant.paths
import logging
import shutil
from pathlib import Path
from components.FileManager import OutputFileFactory
from constant.paths import INPUT_FILE_DIR, OUTPUT_FILE_DIR

logger = logging.getLogger(__name__)

class FileConverterService:
    def start_convert_files(self):
        logger.info("Start converting files")
        self._clear_existing_files()
        total = self._get_file(INPUT_FILE_DIR)
        logger.info("File conversion completed")
        logger.info("Total converted files: " + str(total))

    def _clear_existing_files(self):
        logger.info(f"Clearing: {OUTPUT_FILE_DIR}")
        shutil.rmtree(OUTPUT_FILE_DIR)
        output_main_folder_path = Path(OUTPUT_FILE_DIR)
        if not output_main_folder_path.exists():
            output_main_folder_path.mkdir()

    def _get_file(self, parent_path):
        count = 0
        logger.info("Dir: " + parent_path)
        path = Path(parent_path)
        for file in path.iterdir():
            if file.is_dir():
                count += self._get_file(parent_path + "\\" + file.name)
            else:
                count += 1
                logger.info("Get file:" + parent_path + "\\" + file.name)
                output_file = OutputFileFactory.get_file(parent_path + "\\" + file.name)
                output_file.convert()
        return count