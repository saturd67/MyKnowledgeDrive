"""Which files the embedder hands to chroma, and under which ids.

The collection is real - a chroma store in a temporary folder - but the model
is not: FakeEmbeddingFunction stands in for the sentence-transformer, so the
suite neither loads it nor depends on what it produces.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import chromadb

from services.file_embedder_service.file_embedder_service import FileEmbedderService
from tests.fake_embedding_function import FakeEmbeddingFunction


class FileEmbedderServiceTest(unittest.TestCase):

    def setUp(self):
        self.source_dir = Path(tempfile.mkdtemp())
        self.chroma_store_dir = Path(tempfile.mkdtemp())
        self.addCleanup(self._forget_chroma_client)
        self.addCleanup(shutil.rmtree, self.source_dir, True)

        embedding_function_patch = patch(
            "services.file_embedder_service.file_embedder_service.embedding_functions"
            ".SentenceTransformerEmbeddingFunction",
            FakeEmbeddingFunction,
        )
        embedding_function_patch.start()
        self.addCleanup(embedding_function_patch.stop)

    def _forget_chroma_client(self):
        """Chroma keeps the sqlite file open, and Windows will not delete it
        underneath a live client."""
        chromadb.api.shared_system_client.SharedSystemClient.clear_system_cache()
        shutil.rmtree(self.chroma_store_dir, ignore_errors=True)

    def _build_service(self, collection_name="test_collection"):
        return FileEmbedderService(self.source_dir, str(self.chroma_store_dir), collection_name, "unused-model")

    def _write(self, relative_path, content="some words about docker"):
        file_path = self.source_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def test_embeds_text_files_and_skips_the_rest(self):
        self._write("Notes.md")
        self._write("Sub/Steps.txt")
        self._write("Empty.md", content="   \n")
        (self.source_dir / "Book.pdf").write_bytes(b"%PDF-1.5")
        (self.source_dir / "Photo.jpg").write_bytes(b"\xff\xd8\xff")

        file_embedder_service = self._build_service()
        embedded_file_count, skipped_file_count, failed_file_count = file_embedder_service.start_embedding()

        self.assertEqual((embedded_file_count, failed_file_count), (2, 0))
        self.assertEqual(skipped_file_count, 3)
        self.assertEqual(file_embedder_service.collection.count(), 2)

    def test_an_id_keeps_the_extension_and_the_label_drops_it(self):
        self._write("Docker/Notes.md")

        file_embedder_service = self._build_service()
        file_embedder_service.start_embedding()
        collection = file_embedder_service.collection.get()

        self.assertEqual(collection["ids"], [str(Path("Docker/Notes.md"))])
        self.assertEqual(collection["metadatas"][0]["label"], str(Path("Docker/Notes")))

    def test_two_files_with_one_name_do_not_collide(self):
        """The bug that broke a real run: a Google Doc arrives as Notes.md and
        the image converter writes Notes.txt beside Notes.jpg, and dropping the
        extension made chroma reject the whole upsert."""
        self._write("Docker/Cheat Sheet.md", content="markdown about docker")
        self._write("Docker/Cheat Sheet.txt", content="text read out of a picture")

        file_embedder_service = self._build_service()
        embedded_file_count, _, failed_file_count = file_embedder_service.start_embedding()

        self.assertEqual((embedded_file_count, failed_file_count), (2, 0))
        self.assertEqual(
            sorted(file_embedder_service.collection.get()["ids"]),
            sorted([str(Path("Docker/Cheat Sheet.md")), str(Path("Docker/Cheat Sheet.txt"))]),
        )

    def test_a_repeated_id_is_dropped_rather_than_losing_the_run(self):
        files = [
            {"id": "Notes.md", "content": "first", "metadata": {"label": "Notes"}},
            {"id": "Notes.md", "content": "second", "metadata": {"label": "Notes"}},
            {"id": "Other.md", "content": "third", "metadata": {"label": "Other"}},
        ]

        kept_files, duplicate_file_count = FileEmbedderService._drop_duplicate_ids(files)

        self.assertEqual(duplicate_file_count, 1)
        self.assertEqual([file["id"] for file in kept_files], ["Notes.md", "Other.md"])
        self.assertEqual(kept_files[0]["content"], "first")

    def test_embedding_twice_updates_rather_than_duplicates(self):
        self._write("Notes.md")
        file_embedder_service = self._build_service()
        file_embedder_service.start_embedding()

        self._write("Notes.md", content="the same file, rewritten")
        file_embedder_service.start_embedding()

        self.assertEqual(file_embedder_service.collection.count(), 1)

    def test_reset_collection_empties_it(self):
        self._write("Notes.md")
        file_embedder_service = self._build_service()
        file_embedder_service.start_embedding()

        file_embedder_service.reset_collection()

        self.assertEqual(file_embedder_service.collection.count(), 0)

    def test_walks_into_folders(self):
        self._write("One.md")
        self._write("Sub/Two.md")
        self._write("Sub/Deeper/Three.md")

        embedded_file_count, _, _ = self._build_service().start_embedding()

        self.assertEqual(embedded_file_count, 3)

    def test_a_document_carries_its_modified_time(self):
        self._write("Notes.md")

        file_embedder_service = self._build_service()
        file_embedder_service.start_embedding()

        modified_time = file_embedder_service.collection.get()["metadatas"][0]["modifiedTime"]
        self.assertRegex(modified_time, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
