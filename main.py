from constant.paths import INPUT_FILE_DIR, BASE_DIR
from pathlib import Path
from components.FileManager import OutputFileFactory
import logging
from services.FileConverterService import FileConverterService
from services.TextEmbedderService import TextEmbedderService

ENABLE_LOGGING = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)


if __name__ == "__main__":
    # fileConverterService = FileConverterService()
    # fileConverterService.start_convert_files()

    textEmbedderService = TextEmbedderService()
    textEmbedderService.query()

# import inquirer
# questions = [
#   inquirer.List('size',
#                 message="What size do you need?",
#                 choices=['Jumbo', 'Large', 'Standard', 'Medium', 'Small', 'Micro'],
#             ),
# ]
# answers = inquirer.prompt(questions)
# print (answers["size"])