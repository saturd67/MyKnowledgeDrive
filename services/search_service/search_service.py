"""Semantic search over the Chroma collection.

Unlike `LibraryService`, this one needs the embedding function: the query has
to be embedded with the same model the documents were, or the distances mean
nothing. That model is loaded lazily and cached, so the first search of a
process takes seconds and the rest are quick - which is why the screen runs a
search on a worker thread rather than on the event loop.

The cache is keyed on the settings it was built from, so editing the store,
the collection or the model on the Settings screen rebuilds it rather than
quietly searching the old one.
"""

import logging

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from constant.settings import (
    EMBEDDING_COLLECTION,
    EMBEDDING_MODEL,
    EMBEDDING_RESULTS_PER_QUERY,
    PATHS_CHROMA_STORE,
)
from model.SearchResult import SearchResult
from services.SettingService import settingService

logger = logging.getLogger(__name__)


class SearchService:

    def __init__(self):
        self._settings_key = None
        self._collection = None

    def search(self, query):
        """The closest documents to `query`, closest first.

        An empty list for a blank query, and for a collection that is not
        there - nothing has been embedded, which is not an error.
        """
        query = query.strip()
        if not query:
            return []

        collection = self.collection()
        if collection is None:
            return []

        wanted = int(settingService.find_active_by_key(EMBEDDING_RESULTS_PER_QUERY))
        # Asking for more than the collection holds is an error in chroma, and
        # a fresh library can easily hold fewer than the configured five.
        count = collection.count()
        if not count:
            return []

        logger.info(f"Searching '{query}' for the closest {min(wanted, count)} of {count}")
        result = collection.query(
            query_texts=[query],
            n_results=min(wanted, count),
            include=["documents", "metadatas", "distances"],
        )

        return [
            SearchResult.from_chroma(document_id, metadata, distance, file_text)
            for document_id, metadata, distance, file_text in zip(
                result["ids"][0],
                result["metadatas"][0],
                result["distances"][0],
                result["documents"][0],
            )
        ]

    def collection(self):
        """The collection to query, or None when it does not exist yet.

        Cached with the settings it was built from: rebuilding on every search
        would reload the embedding model every time.
        """
        chroma_store_dir = settingService.get_path(PATHS_CHROMA_STORE)
        collection_name = settingService.find_active_by_key(EMBEDDING_COLLECTION)
        embedding_model = settingService.find_active_by_key(EMBEDDING_MODEL)
        settings_key = (chroma_store_dir, collection_name, embedding_model)

        if settings_key == self._settings_key:
            return self._collection

        client = chromadb.PersistentClient(
            path=chroma_store_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        names = [
            collection.name if hasattr(collection, "name") else collection
            for collection in client.list_collections()
        ]
        if collection_name not in names:
            logger.info(f"No collection '{collection_name}' in {chroma_store_dir}")
            self._settings_key = settings_key
            self._collection = None
            return None

        logger.info(f"Loading embedding model {embedding_model}")
        self._collection = client.get_collection(
            name=collection_name,
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model
            ),
        )
        self._settings_key = settings_key
        return self._collection


# Shared instance - the cached collection is what keeps the model load to the
# first search of the process rather than every search.
searchService = SearchService()
