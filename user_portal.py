from numpy.ma.core import resize

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

if __name__ == "__main__":
    logger.info("Starting user portal...")

    text_embedder_service = TextEmbedderService()

    os.system("cls" if os.name == "nt" else "clear")
    while True:
        user_input = input(">")

        os.system("cls" if os.name == "nt" else "clear")

        results = text_embedder_service.query(user_input)
        if len(results) > 0:
            questions = [
                inquirer.List(
                    "path",
                    message="Choose a path",
                    choices=[(result.get("metadata").get("label").replace("\\\\", "\\"), result.get("id")) for result in results]
                )
            ]
            answer = inquirer.prompt(questions)
            webbrowser.open(answer["path"])