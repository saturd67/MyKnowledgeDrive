"""What the downloader does with a Drive folder, without touching Drive."""

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from services.file_downloader_service.downloadable_file.docx_file import DocxFile
from services.file_downloader_service.downloadable_file_factory import DownloadableFileFactory
from services.file_downloader_service.file_downloader_service import FileDownloaderService
from services.file_downloader_service.downloadable_file.google_doc_file import GoogleDocFile
from services.file_downloader_service.downloadable_file.keep_as_is_file import KeepAsIsFile
from services.file_downloader_service.downloadable_file.unsupported_file import UnsupportedFile
from tests.fake_drive_service import FakeDriveService
from tests.fake_media_download import FakeMediaIoBaseDownload

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
GOOGLE_DOC_MIME_TYPE = "application/vnd.google-apps.document"
DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class FileDownloaderServiceTest(unittest.TestCase):

    def setUp(self):
        self.output_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.output_dir, True)

        # The real download reads bytes off an http response; the fake request
        # carries them instead.
        media_patch = patch(
            "services.file_downloader_service.downloadable_file.downloadable_file.MediaIoBaseDownload",
            FakeMediaIoBaseDownload,
        )
        media_patch.start()
        self.addCleanup(media_patch.stop)

    def _build_service(self, fake_drive_service, folder_id="root"):
        """A service wired to the fake - the credentials are never read."""
        with patch("services.file_downloader_service.file_downloader_service.Credentials"), \
             patch("services.file_downloader_service.file_downloader_service.build",
                   return_value=fake_drive_service):
            return FileDownloaderService(folder_id, self.output_dir, "unused.json", "unused-scope")

    def test_downloads_each_type_into_the_right_file(self):
        fake_drive_service = FakeDriveService(
            pages_by_folder_id={
                "root": [[
                    {"id": "doc", "name": "Notes", "mimeType": GOOGLE_DOC_MIME_TYPE},
                    {"id": "pdf", "name": "Book.pdf", "mimeType": "application/pdf"},
                    {"id": "md", "name": "Readme.md", "mimeType": "application/octet-stream"},
                    {"id": "txt", "name": "Plain.txt", "mimeType": "text/plain"},
                    {"id": "jpg", "name": "Photo.jpg", "mimeType": "image/jpeg"},
                ]],
            },
            media_by_file_id={"pdf": b"%PDF-1.5 ...", "md": b"# readme", "txt": b"plain"},
            exports_by_file_id={"doc": b"# notes"},
        )
        file_downloader_service = self._build_service(fake_drive_service)

        downloaded_file_count, skipped_file_count, failed_file_count = file_downloader_service.start_download()

        self.assertEqual((downloaded_file_count, skipped_file_count, failed_file_count), (4, 1, 0))
        self.assertEqual(
            sorted(path.name for path in self.output_dir.iterdir()),
            ["Book.pdf", "Notes.md", "Plain.txt", "Readme.md"],
        )
        self.assertEqual((self.output_dir / "Notes.md").read_bytes(), b"# notes")
        self.assertEqual((self.output_dir / "Book.pdf").read_bytes(), b"%PDF-1.5 ...")
        # The image is the one that was skipped, so nothing was written for it.
        self.assertFalse((self.output_dir / "Photo.jpg").exists())

    def test_exports_a_google_doc_as_markdown(self):
        fake_drive_service = FakeDriveService(
            pages_by_folder_id={"root": [[{"id": "doc", "name": "Notes", "mimeType": GOOGLE_DOC_MIME_TYPE}]]},
            exports_by_file_id={"doc": b"# notes"},
        )
        self._build_service(fake_drive_service).start_download()

        self.assertEqual(fake_drive_service.export_mime_types, ["text/markdown"])

    def test_converts_a_docx_to_markdown(self):
        fake_drive_service = FakeDriveService(
            pages_by_folder_id={"root": [[{"id": "docx", "name": "Report.docx", "mimeType": DOCX_MIME_TYPE}]]},
            media_by_file_id={"docx": b"PK-docx-bytes"},
        )
        file_downloader_service = self._build_service(fake_drive_service)

        # mammoth is exercised on its own docx fixtures upstream; here the only
        # question is that the bytes reach it and its markdown reaches disk.
        with patch("mammoth.convert_to_markdown",
                   return_value=SimpleNamespace(value="# converted", messages=[])) as convert_to_markdown:
            file_downloader_service.start_download()

        self.assertEqual(convert_to_markdown.call_count, 1)
        self.assertEqual((self.output_dir / "Report.md").read_text(encoding="utf-8"), "# converted")
        self.assertFalse((self.output_dir / "Report.docx").exists())

    def test_walks_into_folders_keeping_the_structure(self):
        fake_drive_service = FakeDriveService(
            pages_by_folder_id={
                "root": [[{"id": "sub", "name": "Docker", "mimeType": FOLDER_MIME_TYPE}]],
                "sub": [[
                    {"id": "deep", "name": "Build", "mimeType": FOLDER_MIME_TYPE},
                    {"id": "md", "name": "Notes.md", "mimeType": "text/markdown"},
                ]],
                "deep": [[{"id": "txt", "name": "Steps.txt", "mimeType": "text/plain"}]],
            },
            media_by_file_id={"md": b"# notes", "txt": b"steps"},
        )

        downloaded_file_count, _, _ = self._build_service(fake_drive_service).start_download()

        self.assertEqual(downloaded_file_count, 2)
        self.assertTrue((self.output_dir / "Docker" / "Notes.md").exists())
        self.assertTrue((self.output_dir / "Docker" / "Build" / "Steps.txt").exists())

    def test_reads_every_page_of_a_listing(self):
        fake_drive_service = FakeDriveService(
            pages_by_folder_id={
                "root": [
                    [{"id": "one", "name": "One.txt", "mimeType": "text/plain"}],
                    [{"id": "two", "name": "Two.txt", "mimeType": "text/plain"}],
                ],
            },
            media_by_file_id={"one": b"1", "two": b"2"},
        )

        downloaded_file_count, _, _ = self._build_service(fake_drive_service).start_download()

        self.assertEqual(downloaded_file_count, 2)
        self.assertTrue((self.output_dir / "Two.txt").exists())

    def test_counts_a_failed_file_and_keeps_going(self):
        fake_drive_service = FakeDriveService(
            pages_by_folder_id={
                "root": [[
                    {"id": "bad", "name": "Broken.txt", "mimeType": "text/plain"},
                    {"id": "good", "name": "Fine.txt", "mimeType": "text/plain"},
                ]],
            },
            media_by_file_id={"good": b"fine"},
            errors_by_file_id={"bad": OSError("the network went away")},
        )

        downloaded_file_count, skipped_file_count, failed_file_count = (
            self._build_service(fake_drive_service).start_download()
        )

        self.assertEqual((downloaded_file_count, skipped_file_count, failed_file_count), (1, 0, 1))
        self.assertTrue((self.output_dir / "Fine.txt").exists())
        self.assertFalse((self.output_dir / "Broken.txt").exists())

    def test_replaces_characters_windows_will_not_take_in_a_name(self):
        self.assertEqual(FileDownloaderService._sanitize_name('a/b:c*d?.md'), "a_b_c_d_.md")
        self.assertEqual(FileDownloaderService._sanitize_name("  spaced  "), "spaced")
        self.assertEqual(FileDownloaderService._sanitize_name("..."), "untitled")


class DownloadableFileFactoryTest(unittest.TestCase):

    def _get_file(self, name, mime_type):
        return DownloadableFileFactory.get_file(None, "id", name, mime_type, "out")

    def test_picks_the_class_that_handles_the_type(self):
        cases = [
            ("Notes", GOOGLE_DOC_MIME_TYPE, GoogleDocFile),
            ("Report.docx", DOCX_MIME_TYPE, DocxFile),
            # Drive is inconsistent about uploaded text files, so the extension
            # has to be enough on its own.
            ("Notes.md", "application/octet-stream", KeepAsIsFile),
            ("Book.pdf", "application/pdf", KeepAsIsFile),
            ("Plain.txt", "text/plain", KeepAsIsFile),
            ("Photo.jpg", "image/jpeg", UnsupportedFile),
            ("Installer.exe", "application/x-msdownload", UnsupportedFile),
        ]
        for name, mime_type, expected_class in cases:
            with self.subTest(name=name):
                self.assertIsInstance(self._get_file(name, mime_type), expected_class)

    def test_markdown_producers_rename_the_output_to_md(self):
        self.assertEqual(self._get_file("Notes", GOOGLE_DOC_MIME_TYPE).get_output_file_path().name, "Notes.md")
        self.assertEqual(self._get_file("Report.docx", DOCX_MIME_TYPE).get_output_file_path().name, "Report.md")

    def test_everything_else_keeps_its_name(self):
        self.assertEqual(self._get_file("Book.pdf", "application/pdf").get_output_file_path().name, "Book.pdf")

    def test_an_unsupported_file_writes_nothing(self):
        self.assertFalse(self._get_file("Photo.jpg", "image/jpeg").download())
