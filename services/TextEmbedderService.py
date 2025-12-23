import logging
import chromadb
from chromadb.utils import embedding_functions

from pathlib import Path

from constant.paths import INPUT_FILE_DIR, OUTPUT_FILE_DIR

logger = logging.getLogger(__name__)

class TextEmbedderService:

    def start_embedding(self, is_new_collection = True):
        logger.info("Start embedding files")

        chroma_client = chromadb.PersistentClient(path="./my_chroma_store")
        sentence_transformer = embedding_functions.SentenceTransformerEmbeddingFunction(model_name = 'all-MiniLM-L6-v2')
        collection = chroma_client.get_or_create_collection(name="my_knowledge_drive", embedding_function=sentence_transformer)

        files_content = self.get_files_content()

        if is_new_collection:
            logger.info("Adding collection")
            ids = []
            documents = []
            metadatas = []
            for index, file_content in enumerate(files_content):
                ids.append(str(index + 1))
                documents.append(file_content.get("content"))
                metadatas.append({"label": file_content.get("file")})

            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

            print(len(metadatas))

        logger.info("Adding collection done")

        logger.info("Query collection")
        results = collection.query(
            query_texts = ["TypeScript arrays examples"],
            n_results = 1,
            include = ["distances", "metadatas", "documents"],
        )

        print(results.get("ids")[0])
        print(results.get("documents")[0])
        print(results.get("metadatas")[0])


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