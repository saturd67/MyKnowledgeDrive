import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pathlib import Path
from constant.settings import (
    EMBEDDING_COLLECTION,
    EMBEDDING_MODEL,
    EMBEDDING_RESULTS_PER_QUERY,
    PATHS_CHROMA_STORE,
    PATHS_OUTPUT_DIR,
)
from services.FileFetcherService import FileFetcherService
from services.SettingService import settingService as app_settings

logger = logging.getLogger(__name__)

class TextEmbedderService:

    def __init__(self):
        self.collection_name = app_settings.get(EMBEDDING_COLLECTION)
        self.chroma_client = chromadb.PersistentClient(
            path=app_settings.get_path(PATHS_CHROMA_STORE),
            settings=Settings(anonymized_telemetry=False)
        )
        self.sentence_transformer = embedding_functions.SentenceTransformerEmbeddingFunction(model_name = app_settings.get(EMBEDDING_MODEL))
        self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name, embedding_function=self.sentence_transformer)

    def embed_collection(self):
        logger.info("Start embedding files")

        file_fetcher_service = FileFetcherService()
        file_ids = file_fetcher_service.start_file_id_fetching()

        files_content = self.get_files_content()

        logger.info("Adding collection")
        ids = []
        documents = []
        metadatas = []
        for index, file_content in enumerate(files_content):
            file_id = next((file_id for file_id in file_ids if file_id.get('file') == file_content.get('file')), None)
            if file_id is not None:
                ids.append(file_id.get('id'))
                documents.append(file_content.get("content"))
                metadatas.append({"label": file_content.get("file"), "modifiedTime": file_id.get("modifiedTime")})
            else:
                logger.warning(f"File id not found: {file_content.get('file')}")

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        logger.info(f"Total embedded files: {self.collection.count()}")

    def sync_collection(self):
        logger.info("Syncing collection")

        file_fetcher_service = FileFetcherService()
        drive_files = file_fetcher_service.start_file_id_fetching()
        drive_ids = {drive_file.get("id") for drive_file in drive_files}

        existing_collection = self.collection.get(include=["metadatas"])
        existing_collection_modified_time = {
            id_: (metadata or {}).get("modifiedTime")
            for id_, metadata in zip(existing_collection.get("ids", []), existing_collection.get("metadatas", []))
        }

        existing_collection_to_upsert = [
            drive_file for drive_file in drive_files
            if existing_collection_modified_time.get(drive_file.get("id"), object()) != drive_file.get("modifiedTime")
        ]
        added_collection_count = sum(1 for drive_file in existing_collection_to_upsert if drive_file.get("id") not in existing_collection_modified_time)
        updated_collection_count = len(existing_collection_to_upsert) - added_collection_count

        removed_collection_ids = [id_ for id_ in existing_collection_modified_time if id_ not in drive_ids]

        if existing_collection_to_upsert:
            upsert_paths = {drive_file.get("file") for drive_file in existing_collection_to_upsert}
            content_by_file = {
                file_content.get("file"): file_content.get("content")
                for file_content in self.get_files_content()
                if file_content.get("file") in upsert_paths
            }

            ids = []
            documents = []
            metadatas = []
            for drive_file in existing_collection_to_upsert:
                file_path = drive_file.get("file")
                content = content_by_file.get(file_path)
                if content is None:
                    logger.warning(f"Converted file not found, skipping: {file_path}")
                    continue
                ids.append(drive_file.get("id"))
                documents.append(content)
                metadatas.append({"label": file_path, "modifiedTime": drive_file.get("modifiedTime")})

            if ids:
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )

        if removed_collection_ids:
            self.collection.delete(ids=removed_collection_ids)

        unchanged = len(drive_files) - len(existing_collection_to_upsert)
        logger.info(
            f"Sync completed - added: {added_collection_count}, updated: {updated_collection_count}, "
            f"removed: {len(removed_collection_ids)}, unchanged: {unchanged}"
        )

    def check_collection(self, page):
        logger.info("Checking collection")

        limit = 10
        offset = limit * (page - 1)

        results = self.collection.get(limit=limit, offset=offset)
        ids = results['ids']
        metadatas = results['metadatas']
        for id, metadata in zip(ids, metadatas):
            print(f"{id}: {metadata.get('label')}")

    def check_total_collection(self):
        logger.info("Getting total collection")
        print(f"Total collections: {self.collection.count()}")

    def reset_collection(self):
        logger.info("Clearing collection")
        self.chroma_client.delete_collection(name=self.collection_name)
        self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name, embedding_function=self.sentence_transformer)

    def query(self, query):
        logger.info("Querying collection")

        results = self.collection.query(
            query_texts = [query],
            n_results = app_settings.get_int(EMBEDDING_RESULTS_PER_QUERY),
            include = ["distances", "metadatas", "documents"],
        )

        ids = results.get("ids")[0]
        metadatas = results.get("metadatas")[0]
        distances = results.get("distances")[0]

        output = []
        for index in range(len(ids)):
            output.append({"id": ids[index], "metadata": metadatas[index], "distance": distances[index]})

        return output

    def get_files_content(self):
        logger.info("Getting files")
        output_file_dir = app_settings.get_path(PATHS_OUTPUT_DIR)
        file_contents = self._get_files_content(output_file_dir)


        for file_content in file_contents:
            full_file_path = file_content.get('file')
            start_index = full_file_path.find(output_file_dir) + len(output_file_dir) + 1
            end_index = full_file_path.rfind('.')
            file_content['file'] = full_file_path[start_index:end_index]

        logger.info(f"Total files: {len(file_contents)}")
        return file_contents

    def _get_files_content(self, parent_path):
        files_content = []
        logger.info("Dir: " + parent_path)
        path = Path(parent_path)
        for file in path.iterdir():
            current_path = parent_path + "\\" + file.name
            if file.is_dir():
                files_content += self._get_files_content(current_path)
            else:
                logger.info("Get file:" + current_path)
                with open(current_path, "r", encoding="utf-8") as f:
                    files_content.append({"file": current_path, "content": f.read()})
        return files_content