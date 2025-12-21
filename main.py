import logging
from services.FetchFileService import FetchFileService
from pathlib import Path

ENABLE_LOGGING = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

BASE_DIR = str(Path(__file__).parent)

if __name__ == "__main__":
    fetch_files = FetchFileService(BASE_DIR + "\\files")
    fetch_files.start_fetching()

# import inquirer
# questions = [
#   inquirer.List('size',
#                 message="What size do you need?",
#                 choices=['Jumbo', 'Large', 'Standard', 'Medium', 'Small', 'Micro'],
#             ),
# ]
# answers = inquirer.prompt(questions)
# print (answers["size"])