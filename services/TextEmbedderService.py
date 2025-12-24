import logging
import chromadb
from chromadb.utils import embedding_functions

from pathlib import Path

from constant.paths import INPUT_FILE_DIR, OUTPUT_FILE_DIR

logger = logging.getLogger(__name__)

class TextEmbedderService:

    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path="./my_chroma_store")
        self.sentence_transformer = embedding_functions.SentenceTransformerEmbeddingFunction(model_name = 'all-MiniLM-L6-v2')
        self.collection = self.chroma_client.get_or_create_collection(name="my_knowledge_drive", embedding_function=self.sentence_transformer)

    def embed_collection(self):
        logger.info("Start embedding files")

        files_content = self.get_files_content()

        logger.info("Adding collection")
        ids = []
        documents = []
        metadatas = []
        for index, file_content in enumerate(files_content):
            ids.append(str(index + 1))
            documents.append(file_content.get("content"))
            metadatas.append({"label": file_content.get("file")})

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
            print(f"{id}: {metadata.get('label').replace('\\\\', '\\\\')}")
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