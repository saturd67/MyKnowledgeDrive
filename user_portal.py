from numpy.ma.core import resize

from constant.paths import OUTPUT_FILE_DIR
from services.TextEmbedderService import TextEmbedderService
import os
import logging
import inquirer
import webbrowser

ENABLE_LOGGING = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

chrome_path = f"C:\Program Files\Google\Chrome\Application\chrome.exe"

profile = "Profile 1"

webbrowser.register("chrome", None, webbrowser.BackgroundBrowser(chrome_path))

if __name__ == "__main__":
    logger.info("Starting user portal...")

    text_embedder_service = TextEmbedderService()

    os.subsystem("cls" if os.name == "nt" else "clear")
    while True:
        user_input = input(">")


        results = text_embedder_service.query(user_input)

        is_exist = True
        while is_exist:
            choices = []
            for result in results:
                file_path = result.get("metadata").get("label")
                choices.append((file_path, result.get("id")))
            choices.append(('Exit', 'exit'))

            questions = [
                inquirer.List(
                    "value",
                    message="Choose a file",
                    choices=choices
                )
            ]
            answer = inquirer.prompt(questions)

            os.system("cls" if os.name == "nt" else "clear")

            if answer["value"] != "exit":
                webbrowser.get("chrome").open("https://drive.google.com/file/d/" + answer["value"])
            else:
                is_exist = False