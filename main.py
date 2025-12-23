from constant.paths import INPUT_FILE_DIR
from services.FetchFileService import FetchFileService
from pathlib import Path
from components.FileManager import OutputFileFactory
import logging
import constant.paths
from services.FileConverterService import FileConverterService

ENABLE_LOGGING = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)


if __name__ == "__main__":
    fileConverterService = FileConverterService()
    fileConverterService.convert_files()

    # output_file = OutputFileFactory.get_file(INPUT_FILE_DIR + "\\Flutter\\Styling\\flutter_style_sharing.zip")

# import inquirer
# questions = [
#   inquirer.List('size',
#                 message="What size do you need?",
#                 choices=['Jumbo', 'Large', 'Standard', 'Medium', 'Small', 'Micro'],
#             ),
# ]
# answers = inquirer.prompt(questions)
# print (answers["size"])