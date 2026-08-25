from chromadb.api.types import EmbeddingFunction


class FakeEmbeddingFunction(EmbeddingFunction):
    """Stands in for the sentence-transformer, so the tests never load a model.

    The vectors mean nothing - the embedder is responsible for which documents
    are handed over and under which ids, not for what they embed to - but they
    are derived from the text, so two different documents do not collide.
    """

    def __init__(self, model_name=None):
        # Takes the same keyword the real SentenceTransformerEmbeddingFunction
        # does, so it can be dropped in where that one is constructed.
        self.model_name = model_name

    def __call__(self, input):
        return [[float(len(text) % 7), float(sum(map(ord, text[:8])) % 11), 0.5] for text in input]

    @staticmethod
    def name():
        return "fake"

    def get_config(self):
        """Chroma persists an embedding function's config with the collection."""
        return {"model_name": self.model_name}

    @staticmethod
    def build_from_config(config):
        return FakeEmbeddingFunction(config.get("model_name"))
