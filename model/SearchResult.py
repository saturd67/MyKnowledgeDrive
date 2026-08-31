"""One hit from a search: a document, how close it scored, and its text.

A SearchResult *is* a Document - same id, label, folder, name and kind - with
the query-specific parts added, so the screen reads `result.name` exactly as
the Library screen reads `document.name`.
"""

from model.Document import Document

#: How much of the text the preview shows before trailing off.
PREVIEW_LENGTH = 220


class SearchResult(Document):

    def __init__(self, document_id, label, modified_time=None, distance=0.0, text=""):
        super().__init__(document_id, label, modified_time)
        #: Cosine distance from the query. Smaller is closer.
        self.distance = distance
        #: The document as it was embedded - what the reading pane shows.
        self.text = text

    @staticmethod
    def from_chroma(document_id, metadata, distance=0.0, text=""):
        metadata = metadata or {}
        return SearchResult(
            document_id=document_id,
            label=metadata.get("label") or document_id,
            modified_time=metadata.get("modifiedTime"),
            distance=distance,
            text=text,
        )

    @property
    def score(self):
        """Rough 0..1 relevance, for display only.

        Cosine distance is not a probability and this is not calibrated - it
        exists so the hits can be compared against each other in one glance.
        """
        return max(0.0, min(1.0, 1.0 - self.distance))

    @property
    def preview(self):
        """The opening of the document, on one line.

        Deliberately the opening rather than "the passage that matched":
        `FileEmbedderService` embeds one vector per whole file, so no
        particular passage is what scored, and pointing at one would be
        inventing a reason. Chunked embeddings would change that.
        """
        text = " ".join(self.text.split())
        if len(text) <= PREVIEW_LENGTH:
            return text
        return text[:PREVIEW_LENGTH].rsplit(" ", 1)[0] + " ..."
