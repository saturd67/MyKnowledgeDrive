"""What the image converter does to images on disk and inside markdown.

The OCR itself is stubbed: tesseract's accuracy is not this project's to test,
and a real read of a generated image would make the assertions depend on it.
What is tested is everything around it - which images are found, what replaces
them, and what is left alone.
"""

import base64
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from services.image_converter_service.image_converter_service import ImageConverterService

OCR_TEXT = "text out of the picture"


def png_bytes(color=(10, 20, 30)):
    """A real, small PNG - PIL has to be able to open it."""
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buffer, "PNG")
    return buffer.getvalue()


def png_data_uri(color=(10, 20, 30)):
    return "data:image/png;base64," + base64.b64encode(png_bytes(color)).decode()


class ImageConverterServiceTest(unittest.TestCase):

    def setUp(self):
        self.source_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.source_dir, True)
        self.image_converter_service = ImageConverterService()

        image_to_string_patch = patch("pytesseract.image_to_string", return_value=OCR_TEXT)
        image_to_string_patch.start()
        self.addCleanup(image_to_string_patch.stop)

    # --- markdown ------------------------------------------------------------

    def test_replaces_an_inline_image_with_its_text(self):
        markdown = f"before\n\n![]({png_data_uri()})\n\nafter\n"

        converted_markdown, converted_image_count = self.image_converter_service.convert_markdown(markdown)

        self.assertEqual(converted_image_count, 1)
        self.assertNotIn("data:image", converted_markdown)
        self.assertIn(OCR_TEXT, converted_markdown)
        self.assertIn("-----img start-----", converted_markdown)
        self.assertIn("before", converted_markdown)
        self.assertIn("after", converted_markdown)

    def test_replaces_a_reference_image_and_drops_its_definition(self):
        markdown = f"see below\n\n![][image1]\n\n[image1]: <{png_data_uri()}>\n"

        converted_markdown, converted_image_count = self.image_converter_service.convert_markdown(markdown)

        self.assertEqual(converted_image_count, 1)
        self.assertNotIn("data:image", converted_markdown)
        self.assertNotIn("[image1]:", converted_markdown)
        self.assertIn(OCR_TEXT, converted_markdown)

    def test_leaves_markdown_without_images_alone(self):
        markdown = "# Title\n\nJust words, and a [link](https://example.com).\n"

        self.assertEqual(self.image_converter_service.convert_markdown(markdown), (markdown, 0))

    def test_leaves_a_reference_with_no_definition_alone(self):
        converted_markdown, converted_image_count = self.image_converter_service.convert_markdown("![][missing]")

        self.assertEqual((converted_markdown, converted_image_count), ("![][missing]", 0))

    def test_an_unreadable_image_is_replaced_rather_than_left_behind(self):
        # Valid base64, but not an image - PIL raises, and the run carries on.
        markdown = "![](data:image/png;base64," + base64.b64encode(b"not a picture").decode() + ")"

        converted_markdown, converted_image_count = self.image_converter_service.convert_markdown(markdown)

        self.assertEqual(converted_image_count, 1)
        self.assertIn(ImageConverterService.UNREADABLE_IMAGE_TEXT, converted_markdown)
        self.assertNotIn("data:image", converted_markdown)

    def test_rewrites_a_markdown_file_in_place(self):
        markdown_file_path = self.source_dir / "Guide.md"
        markdown_file_path.write_text(f"![]({png_data_uri()})", encoding="utf-8")
        size_before = markdown_file_path.stat().st_size

        converted_image_count = self.image_converter_service.convert_markdown_file(markdown_file_path)

        self.assertEqual(converted_image_count, 1)
        self.assertLess(markdown_file_path.stat().st_size, size_before)
        self.assertIn(OCR_TEXT, markdown_file_path.read_text(encoding="utf-8"))

    # --- images on disk ------------------------------------------------------

    def test_reads_an_image_file_out_into_a_txt_beside_it(self):
        image_file_path = self.source_dir / "Diagram.png"
        image_file_path.write_bytes(png_bytes())

        converted_image_count = self.image_converter_service.convert_image_file_to_text_file(image_file_path)

        text_file_path = self.source_dir / "Diagram.txt"
        self.assertEqual(converted_image_count, 1)
        self.assertIn(OCR_TEXT, text_file_path.read_text(encoding="utf-8"))
        # The picture itself stays where it was.
        self.assertTrue(image_file_path.exists())

    def test_skips_an_image_whose_text_file_is_already_current(self):
        image_file_path = self.source_dir / "Diagram.png"
        image_file_path.write_bytes(png_bytes())
        self.image_converter_service.convert_image_file_to_text_file(image_file_path)

        self.assertEqual(self.image_converter_service.convert_image_file_to_text_file(image_file_path), 0)

    def test_converts_an_image_again_once_it_changes(self):
        image_file_path = self.source_dir / "Diagram.png"
        image_file_path.write_bytes(png_bytes())
        self.image_converter_service.convert_image_file_to_text_file(image_file_path)

        image_file_path.write_bytes(png_bytes(color=(200, 100, 50)))
        image_file_path.touch()

        self.assertEqual(self.image_converter_service.convert_image_file_to_text_file(image_file_path), 1)

    # --- walking a folder ----------------------------------------------------

    def test_walks_the_tree_converting_what_it_can(self):
        (self.source_dir / "Sub").mkdir()
        (self.source_dir / "WithImage.md").write_text(f"![]({png_data_uri()})", encoding="utf-8")
        (self.source_dir / "Sub" / "Nested.md").write_text(f"![]({png_data_uri()})", encoding="utf-8")
        (self.source_dir / "Sub" / "Plain.md").write_text("no pictures here", encoding="utf-8")
        (self.source_dir / "Diagram.png").write_bytes(png_bytes())
        (self.source_dir / "Book.pdf").write_bytes(b"%PDF-1.5")
        (self.source_dir / "Notes.txt").write_text("already text", encoding="utf-8")

        converted_file_count, converted_image_count, skipped_file_count, failed_file_count = (
            self.image_converter_service.start_converting_images(self.source_dir)
        )

        # Two markdown files plus the image; the pdf, the .txt and the markdown
        # with nothing in it to convert are the three skipped.
        self.assertEqual(converted_file_count, 3)
        self.assertEqual(converted_image_count, 3)
        self.assertEqual(skipped_file_count, 3)
        self.assertEqual(failed_file_count, 0)
        self.assertTrue((self.source_dir / "Diagram.txt").exists())
        self.assertEqual((self.source_dir / "Book.pdf").read_bytes(), b"%PDF-1.5")

    def test_a_second_pass_over_the_same_folder_does_nothing(self):
        (self.source_dir / "WithImage.md").write_text(f"![]({png_data_uri()})", encoding="utf-8")
        (self.source_dir / "Diagram.png").write_bytes(png_bytes())
        self.image_converter_service.start_converting_images(self.source_dir)

        converted_file_count, converted_image_count, _, failed_file_count = (
            self.image_converter_service.start_converting_images(self.source_dir)
        )

        self.assertEqual((converted_file_count, converted_image_count, failed_file_count), (0, 0, 0))
