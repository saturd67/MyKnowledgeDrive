from abc import ABC, abstractmethod
from pathlib import Path
from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image
import mammoth
import base64
import pytesseract
import constant.paths
import logging
import mimetypes
from constant.paths import OUTPUT_FILE_DIR, INPUT_FILE_DIR

logger = logging.getLogger(__name__)

class OutputFile(ABC):
    def __init__(self, file_path):
        self.path = file_path[(file_path.find(INPUT_FILE_DIR) + len(INPUT_FILE_DIR)):file_path.rfind("\\")]
        self.filename = file_path[file_path.rfind("\\") + 1:]

    def get_file_path(self):
        return self.path + "\\" + self.filename

    def get_full_path(self):
        return INPUT_FILE_DIR + "\\" + self.path + "\\" + self.filename

    @abstractmethod
    def convert(self):
        pass

    def _generate_file(self, file_content):
        output_path = Path(OUTPUT_FILE_DIR + "\\" + self.path)
        if not output_path.exists():
            logger.info(f"Output path does not exists: {output_path}")
            logger.info(f"Creating output path: {output_path}")
            output_path.mkdir(parents=True, exist_ok=True)

        output_file = OUTPUT_FILE_DIR + "\\" + self.get_file_path()[:self.get_file_path().rfind(".")] + ".txt"
        logger.info(f"Generating file: {output_file}")
        with open(output_file, 'w', encoding="utf-8") as file:
            file.write(file_content)



class DocFile(OutputFile):
    EXTENSION = '.docx'

    def convert(self):
        logger.info(f"Converting docx to text: {self.get_file_path()}")
        # Convert Doc to HTML
        with open(self.get_full_path(), 'rb') as file:
            result = mammoth.convert_to_html(file)
            file_html = result.value

        # Convert HTML + Image to Text
        soup = BeautifulSoup(file_html, 'html.parser')

        total_img = len(soup.find_all('img'))
        for index, img in enumerate(soup.find_all('img')):
            logger.info(f"Converting image to text: {self.get_file_path()} ({index + 1}/{total_img})")
            img.replace_with(f'\n-----img start-----\n{self._base64_image_to_text(img)}\n-----img end-----\n\n')

        self._generate_file(soup.get_text(separator="\n", strip=True))



    def _base64_image_to_text(self, img_element):
        image_src = img_element.attrs['src']
        image_base64 = image_src[image_src.rfind(',') + 1:]
        image_bytes = base64.b64decode(image_base64)

        image = Image.open(BytesIO(image_bytes))
        return pytesseract.image_to_string(image)



class ImageFile(OutputFile):
    MIMETYPE = ['image/']

    def convert(self):
        logger.info(f"Converting image to text: {self.get_file_path()}")
        self._generate_file(self._image_to_text())

    def _image_to_text(self):
        image = Image.open(self.get_full_path())
        return pytesseract.image_to_string(image)

class OtherFile(OutputFile):
    EXTENSIONS = [
        '.bat',
        '.gitignore',
        '.html',
        '.iml',
        '.java',
        '.js',
        '.json',
        '.py',
        '.txt',
        '.xml'
    ]

    def convert(self):
        logger.info(f"Converting other file to text: {self.get_file_path()}")
        with open(self.get_full_path(), "r", encoding='utf-8') as file:
            file_content = file.read()

        self._generate_file(file_content)

class UnknownFile(OutputFile):

    def convert(self):
        logger.warning(f"Skip unknown file: {self.get_file_path()}")



class OutputFileFactory:

    @staticmethod
    def get_file(file_path):
        extension = Path(file_path).suffix
        mime_type, encoding = mimetypes.guess_type(file_path)

        if extension == DocFile.EXTENSION:
            return DocFile(file_path)
        elif mime_type is not None and mime_type.startswith('image/'):
            return ImageFile(file_path)
        elif extension in OtherFile.EXTENSIONS:
            return OtherFile(file_path)
        else:
            return UnknownFile(file_path)