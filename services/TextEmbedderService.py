import logging
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
from constant.paths import INPUT_FILE_DIR, OUTPUT_FILE_DIR
from services.FileFetcherService import FileFetcherService

logger = logging.getLogger(__name__)

class TextEmbedderService:

    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path="./my_chroma_store")
        self.sentence_transformer = embedding_functions.SentenceTransformerEmbeddingFunction(model_name = 'all-MiniLM-L6-v2')
        self.collection = self.chroma_client.get_or_create_collection(name="my_knowledge_drive", embedding_function=self.sentence_transformer)

    def embed_collection(self):
        logger.info("Start embedding files")

        file_fetcher_service = FileFetcherService()
        file_ids = file_fetcher_service.start_file_id_fetching()

        files_content = self.get_files_content()

        # logger.info("Show file ids")
        # for file_id in file_ids:
        #     print(file_id.get('file'))

        # logger.info(f"\n\nStart mapping file ids...")
        # for file_content in files_content:
        #     n = next((file_id for file_id in file_ids if file_id.get('file') == file_content.get('file')), None)
        #     if n is not None:
        #         print("Found - " + file_content.get('file'))
        #         print(n)
        #         print()

        logger.info("Adding collection")
        ids = []
        documents = []
        metadatas = []
        for index, file_content in enumerate(files_content):
            file_id = next((file_id for file_id in file_ids if file_id.get('file') == file_content.get('file')), None)
            if file_id is not None:
                ids.append(file_id.get('id'))
                documents.append(file_content.get("content"))
                metadatas.append({"label": file_content.get("file")})
            else:
                logger.warning(f"File id not found: {file_content.get('file')}")

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        logger.info(f"Total embedded files: {self.collection.count()}")

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
        self.chroma_client.delete_collection(name="my_knowledge_drive")
        self.collection = self.chroma_client.get_or_create_collection(name="my_knowledge_drive", embedding_function=self.sentence_transformer)

    def query(self, query):
        logger.info("Querying collection")

        results = self.collection.query(
            query_texts = [query],
            n_results = 5,
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
        file_contents = self._get_files_content(OUTPUT_FILE_DIR)


        for file_content in file_contents:
            full_file_path = file_content.get('file')
            start_index = full_file_path.find(OUTPUT_FILE_DIR) + len(OUTPUT_FILE_DIR) + 1
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