from constant.paths import INPUT_FILE_DIR, BASE_DIR
from pathlib import Path
from components.FileManager import OutputFileFactory
from services.FileFetcherService import FileFetcherService

import logging


ENABLE_LOGGING = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)


if __name__ == "__main__":
    file_fetcher_service = FileFetcherService()
    results = file_fetcher_service.start_file_id_fetching()
    for result in results:
        print(result.get("file"))