"""Optical character recognition for images, on disk and inside markdown."""

import base64
import binascii
import io
import logging
import re
from pathlib import Path

import pytesseract
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

# The folder the downloader wrote into - edit it to convert somewhere else.
SOURCE_DIR = str(Path(__file__).resolve().parents[2] / "resources" / "test" / "downloaded_files")


class ImageConverterService:
    """Turns an image into the text it contains.

    Entry points, all landing on the same OCR:

    - `start_converting_images()` for a whole downloaded folder tree
    - `convert_image_file()` for an image on disk (.png, .jpg, ...)
    - `convert_markdown()` / `convert_markdown_file()` for the base64 images
      embedded in markdown - what the Google Doc export and the docx conversion
      leave behind

    The text replaces the image in the markdown, wrapped in the same markers
    components/FileManager.py uses, so a reader can still tell where a picture
    was and that its text was read out of one.
    """

    IMAGE_TEXT_TEMPLATE = "\n\n-----img start-----\n{text}\n-----img end-----\n\n"
    UNREADABLE_IMAGE_TEXT = "[image could not be read]"

    # ![alt](data:image/png;base64,iVBOR...) - what mammoth writes for a docx.
    INLINE_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*data:image/[^;,]+;base64,\s*([A-Za-z0-9+/=\s]+?)\s*\)")

    # ![alt][image1] plus, further down, [image1]: <data:image/png;base64,iVBOR...>
    # - what Drive writes when it exports a Google Doc as markdown.
    REFERENCE_IMAGE = re.compile(r"!\[[^\]]*\]\[([^\]]+)\]")
    REFERENCE_DEFINITION = re.compile(
        r"^\[([^\]]+)\]:[ \t]*<?[ \t]*data:image/[^;,]+;base64,\s*([A-Za-z0-9+/=\s]+?)[ \t]*>?[ \t]*$",
        re.MULTILINE,
    )

    MARKDOWN_EXTENSIONS = (".md", ".markdown")
    IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp")

    def start_converting_images(self, source_dir):
        """Reads every downloaded file under `source_dir` and converts its
        images to text - the base64 images embedded in a .md, and any image
        file sitting on its own, which is read out into a .txt beside it.

        Files are rewritten in place, and a second pass over the same folder
        does no work - the markdown has no images left in it, and an image
        whose .txt is already up to date is left alone. Returns
        (converted_file_count, converted_image_count, skipped_file_count,
        failed_file_count)."""
        source_dir = Path(source_dir)
        logger.info(f"Converting images in {source_dir}")
        converted_file_count, converted_image_count, skipped_file_count, failed_file_count = (
            self._convert_files_in_folder(source_dir)
        )
        logger.info(
            f"Done. Converted {converted_image_count} image(s) in {converted_file_count} file(s), "
            f"skipped: {skipped_file_count}, failed: {failed_file_count}"
        )
        return converted_file_count, converted_image_count, skipped_file_count, failed_file_count

    def _convert_files_in_folder(self, folder_path):
        converted_file_count = 0
        converted_image_count = 0
        skipped_file_count = 0
        failed_file_count = 0

        for file_path in sorted(folder_path.iterdir()):
            if file_path.is_dir():
                logger.info(f"Entering folder: {file_path}")
                sub_converted_file_count, sub_converted_image_count, sub_skipped_file_count, sub_failed_file_count = (
                    self._convert_files_in_folder(file_path)
                )
                converted_file_count += sub_converted_file_count
                converted_image_count += sub_converted_image_count
                skipped_file_count += sub_skipped_file_count
                failed_file_count += sub_failed_file_count
                continue

            extension = file_path.suffix.lower()
            is_markdown = extension in ImageConverterService.MARKDOWN_EXTENSIONS
            is_image = extension in ImageConverterService.IMAGE_EXTENSIONS
            if not is_markdown and not is_image:
                logger.debug(f"Nothing to convert: {file_path}")
                skipped_file_count += 1
                continue

            try:
                if is_markdown:
                    image_count = self.convert_markdown_file(file_path)
                else:
                    image_count = self.convert_image_file_to_text_file(file_path)
            except (OSError, UnicodeDecodeError) as error:
                logger.error(f"Failed: {file_path} - {error}")
                failed_file_count += 1
                continue

            if image_count:
                converted_file_count += 1
                converted_image_count += image_count
            else:
                logger.debug(f"No images in: {file_path}")
                skipped_file_count += 1

        return converted_file_count, converted_image_count, skipped_file_count, failed_file_count

    def convert_image_file_to_text_file(self, image_file_path):
        """Reads an image out into a .txt beside it. The image is left alone.

        Skipped when the .txt is already there and no older than the image, so
        a second pass over the same folder does no work. Returns how many
        images were converted - 1, or 0 when it was skipped."""
        image_file_path = Path(image_file_path)
        text_file_path = image_file_path.with_suffix(".txt")
        is_up_to_date = (
            text_file_path.exists()
            and text_file_path.stat().st_mtime >= image_file_path.stat().st_mtime
        )
        if is_up_to_date:
            logger.debug(f"Already converted: {text_file_path}")
            return 0

        text_file_path.write_text(self._to_text_block(self.convert_image_file(image_file_path)), encoding="utf-8")
        logger.info(f"Converted image to text: {text_file_path}")
        return 1

    def convert_image_file(self, image_file_path):
        """The text in an image on disk."""
        image_file_path = Path(image_file_path)
        logger.info(f"Reading text from image: {image_file_path}")
        return self.convert_image(image_file_path.read_bytes())

    def convert_image(self, image_bytes):
        """The text in an image held in memory. Never raises - a broken image
        reads as UNREADABLE_IMAGE_TEXT so one bad picture cannot lose a file."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return pytesseract.image_to_string(image).strip()
        except (UnidentifiedImageError, OSError, ValueError, pytesseract.TesseractError) as error:
            logger.warning(f"Could not read image: {error}")
            return ImageConverterService.UNREADABLE_IMAGE_TEXT

    def convert_markdown_file(self, markdown_file_path):
        """Rewrites a .md in place with its images read out as text.

        Returns how many images were converted."""
        markdown_file_path = Path(markdown_file_path)
        markdown = markdown_file_path.read_text(encoding="utf-8")
        converted_markdown, converted_image_count = self.convert_markdown(markdown)
        if converted_image_count:
            markdown_file_path.write_text(converted_markdown, encoding="utf-8")
            logger.info(f"Converted {converted_image_count} image(s) to text: {markdown_file_path}")
        return converted_image_count

    def convert_markdown(self, markdown):
        """Replaces every embedded base64 image with the text it contains.

        Returns (markdown, converted_image_count). Images the OCR cannot read
        are still replaced - the base64 is never left behind."""
        converted_image_count = 0
        image_texts_by_reference = self._read_reference_definitions(markdown)

        def replace_inline_image(match):
            nonlocal converted_image_count
            converted_image_count += 1
            return self._to_text_block(self._decode(match.group(1)))

        def replace_reference_image(match):
            nonlocal converted_image_count
            reference = match.group(1)
            if reference not in image_texts_by_reference:
                return match.group(0)
            converted_image_count += 1
            return ImageConverterService.IMAGE_TEXT_TEMPLATE.format(text=image_texts_by_reference[reference])

        markdown = ImageConverterService.INLINE_IMAGE.sub(replace_inline_image, markdown)
        markdown = ImageConverterService.REFERENCE_IMAGE.sub(replace_reference_image, markdown)
        # The definitions the references pointed at are dead weight now.
        markdown = ImageConverterService.REFERENCE_DEFINITION.sub("", markdown)
        return markdown, converted_image_count

    def _read_reference_definitions(self, markdown):
        """`[image1]: <data:image/png;base64,...>` lines, read out as text."""
        image_texts_by_reference = {}
        for reference, encoded_image in ImageConverterService.REFERENCE_DEFINITION.findall(markdown):
            image_texts_by_reference[reference] = self._decode(encoded_image)
        return image_texts_by_reference

    def _decode(self, encoded_image):
        """OCR for one base64 payload, whitespace and line breaks included."""
        try:
            image_bytes = base64.b64decode(re.sub(r"\s+", "", encoded_image))
        except (binascii.Error, ValueError) as error:
            logger.warning(f"Could not decode embedded image: {error}")
            return ImageConverterService.UNREADABLE_IMAGE_TEXT
        return self.convert_image(image_bytes)

    @staticmethod
    def _to_text_block(text):
        return ImageConverterService.IMAGE_TEXT_TEMPLATE.format(text=text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    image_converter_service = ImageConverterService()
    image_converter_service.start_converting_images(SOURCE_DIR)
