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

    def sync_convert_files(self):
        logger.info("Start syncing files")
        converted, skipped = self._sync_file(INPUT_FILE_DIR)
        logger.info("File sync completed")
        logger.info(f"Converted files: {converted}, Skipped files: {skipped}")
        return converted, skipped

    def _sync_file(self, parent_path):
        converted = 0
        skipped = 0
        logger.info("Dir: " + parent_path)
        path = Path(parent_path)
        for file in path.iterdir():
            if file.is_dir():
                sub_converted, sub_skipped = self._sync_file(parent_path + "\\" + file.name)
                converted += sub_converted
                skipped += sub_skipped
            else:
                input_file_path = parent_path + "\\" + file.name
                output_file = OutputFileFactory.get_file(input_file_path)
                output_file_path = Path(output_file.get_output_file_path())
                if not output_file_path.exists() or file.stat().st_mtime > output_file_path.stat().st_mtime:
                    logger.info("Converting (changed): " + input_file_path)
                    output_file.convert()
                    converted += 1
                else:
                    logger.info("Skipping (unchanged): " + input_file_path)
                    skipped += 1
        return converted, skipped

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