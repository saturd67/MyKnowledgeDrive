import inquirer
import logging
import os

from services.FileConverterService import FileConverterService
from services.TextEmbedderService import TextEmbedderService

ENABLE_LOGGING = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

class Action:

    def __init__(self):
        logger.info("Initializing text embedder...")
        self.text_embedder_service = TextEmbedderService()
        self.file_converter_service = FileConverterService()

    def reset(self):
        logger.info("Reseting collection")
        self.file_converter_service.start_convert_files()
        self.text_embedder_service.reset_collection()
        self.text_embedder_service.embed_collection()

    def check(self):
        logger.info("Checking collection")
        self.text_embedder_service.check_total_collection()
        page = input("Page: ")
        self.text_embedder_service.check_collection(int(page))

    def exit(self):
        logger.info("Exit")
        exit(0)

if __name__ == '__main__':
    logger.info("Starting admin portal...")

    action = Action()

    choices = [
        {"name": "Check collections", "value": "check"},
        {"name": "Reset collections", "value": "reset"},
        {"name": "Exit", "value": "exit"}
    ]

    os.system("cls" if os.name == "nt" else "clear")

    print("+-----------------------------+")
    print("| Welcome to the admin portal |")
    print("+-----------------------------+")
    while True:
        print("\n")
        questions = [
            inquirer.List(
                "action",
                message="Admin Portal",
                choices = [ (f"{index + 1}. {choice.get('name')}", choice.get('value')) for index, choice in enumerate(choices)],
            )
        ]

        answer = inquirer.prompt(questions)
        os.system("cls" if os.name == "nt" else "clear")
        try:
            match answer.get("action"):
                case "reset":
                    action.reset()

                case "check":
                    action.check()

                case "exit":
                    action.exit()
        except Exception as e:
            logger.error(f"Invalid action {e}")