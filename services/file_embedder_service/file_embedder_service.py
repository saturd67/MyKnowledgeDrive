"""Standalone test for embedding the downloaded files into the chroma store.

Third step of the standalone chain, after the downloader and the image
converter, and self-contained in the same way - it reads no setting from the
database, so it can be run on its own:

    python -m services.file_embedder_service.file_embedder_service

The folder it reads, the store it writes to, the collection and the model are
the constants below - edit them to point the test somewhere else.

One file becomes one document, keyed by its path relative to SOURCE_DIR, which
is what the app's TextEmbedderService uses as the `label` metadata. Documents
are upserted, so running it again after a re-download refreshes what changed
instead of adding it twice.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

SOURCE_DIR = str(Path(__file__).resolve().parents[2] / "resources" / "test" / "downloaded_files")
CHROMA_STORE_DIR = str(Path(__file__).resolve().parents[2] / "resources" / "my_chroma_store")

# A collection of its own, so this test cannot disturb the collection the app
# reads - point it at "my_knowledge_drive" only when the test is done proving
# itself and you mean to write into the real one.
COLLECTION_NAME = "my_knowledge_drive_test"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RESULTS_PER_QUERY = 5


class FileEmbedderService:
    """Embeds a folder of text files into a chroma collection."""

    TEXT_EXTENSIONS = (".md", ".markdown", ".txt")
    BATCH_SIZE = 100

    def __init__(self, source_dir, chroma_store_dir, collection_name, embedding_model=EMBEDDING_MODEL):
        self.source_dir = Path(source_dir)
        self.collection_name = collection_name
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_store_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.sentence_transformer = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.sentence_transformer,
        )

    def start_embedding(self):
        """Embeds every text file under the source folder.

        Returns (embedded_file_count, skipped_file_count, failed_file_count)."""
        logger.info(f"Embedding {self.source_dir} into '{self.collection_name}'")
        files, skipped_file_count, failed_file_count = self._read_files_in_folder(self.source_dir)

        embedded_file_count = 0
        for batch_start in range(0, len(files), FileEmbedderService.BATCH_SIZE):
            batch = files[batch_start:batch_start + FileEmbedderService.BATCH_SIZE]
            self.collection.upsert(
                ids=[file["id"] for file in batch],
                documents=[file["content"] for file in batch],
                metadatas=[file["metadata"] for file in batch],
            )
            embedded_file_count += len(batch)
            logger.info(f"Embedded {embedded_file_count}/{len(files)}")

        logger.info(
            f"Done. Embedded: {embedded_file_count}, skipped: {skipped_file_count}, "
            f"failed: {failed_file_count}, collection holds: {self.collection.count()}"
        )
        return embedded_file_count, skipped_file_count, failed_file_count

    def _read_files_in_folder(self, folder_path):
        """Every embeddable file under the folder, read and ready to upsert."""
        files = []
        skipped_file_count = 0
        failed_file_count = 0

        for file_path in sorted(folder_path.iterdir()):
            if file_path.is_dir():
                logger.info(f"Entering folder: {file_path}")
                sub_files, sub_skipped_file_count, sub_failed_file_count = self._read_files_in_folder(file_path)
                files += sub_files
                skipped_file_count += sub_skipped_file_count
                failed_file_count += sub_failed_file_count
                continue

            if file_path.suffix.lower() not in FileEmbedderService.TEXT_EXTENSIONS:
                logger.debug(f"Not a text file, skipping: {file_path}")
                skipped_file_count += 1
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as error:
                logger.error(f"Failed: {file_path} - {error}")
                failed_file_count += 1
                continue

            if not content.strip():
                logger.info(f"Empty, skipping: {file_path}")
                skipped_file_count += 1
                continue

            files.append({
                "id": self._get_document_id(file_path),
                "content": content,
                "metadata": {
                    "label": self._get_document_id(file_path),
                    "modifiedTime": self._get_modified_time(file_path),
                },
            })

        return files, skipped_file_count, failed_file_count

    def query(self, query, results_per_query=RESULTS_PER_QUERY):
        """The closest documents to a question, nearest first."""
        results = self.collection.query(
            query_texts=[query],
            n_results=results_per_query,
            include=["distances", "metadatas", "documents"],
        )
        return [
            {"id": id_, "metadata": metadata, "distance": distance}
            for id_, metadata, distance in zip(
                results.get("ids")[0], results.get("metadatas")[0], results.get("distances")[0]
            )
        ]

    def reset_collection(self):
        """Empties the collection - the store's other collections are untouched."""
        logger.info(f"Clearing collection '{self.collection_name}'")
        self.chroma_client.delete_collection(name=self.collection_name)
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.sentence_transformer,
        )

    def _get_document_id(self, file_path):
        """The path relative to the source folder, extension dropped - the same
        shape TextEmbedderService stores as `label`."""
        return str(file_path.relative_to(self.source_dir).with_suffix(""))

    @staticmethod
    def _get_modified_time(file_path):
        return datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc).isoformat()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    file_embedder_service = FileEmbedderService(SOURCE_DIR, CHROMA_STORE_DIR, COLLECTION_NAME)
    file_embedder_service.start_embedding()
