"""Retrieval layer: embeds the corpus and serves top-k nearest chunks.

Uses sentence-transformers for embeddings and a persistent Chroma collection
(no external server). The store is a singleton; `build_index.py` (re)creates
the collection from `corpus.py`.
"""

import logging
import threading

from app.config import get_settings
from app.rag.corpus import CORPUS

logger = logging.getLogger("chatbot.rag")

_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class RetrievalStore:
    """Wraps a persistent Chroma collection; lazily loads the embedder."""

    def __init__(self, collection_name: str = "lab_safety_corpus"):
        self._settings = get_settings()
        self._collection_name = collection_name
        self._embedder = None
        self._client = None
        self._collection = None
        self._lock = threading.Lock()

    def _ensure_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer

            model = self._settings.embedding_model
            logger.info("loading embedding model", extra={"embedding_model": model})
            self._embedder = SentenceTransformer(model)
        return self._embedder

    def _ensure_client(self):
        if self._client is None:
            import chromadb

            self._client = chromadb.PersistentClient(path=self._settings.chroma_dir)
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            client = self._ensure_client()
            self._collection = client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def count(self) -> int:
        return self.collection.count()

    def is_empty(self) -> bool:
        return self.count() == 0

    def embed(self, texts: list[str]):
        """Embed texts; returns a numpy array. BGE models expect a query
        instruction prefix for asymmetric search."""
        model = self._ensure_embedder()
        return model.encode(texts, normalize_embeddings=True)

    def build_index(self) -> int:
        """Recreate the collection from the corpus. Returns chunk count."""
        client = self._ensure_client()
        try:
            client.delete_collection(self._collection_name)
        except Exception:
            pass
        self._collection = client.create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        ids, docs, metadatas = [], [], []
        for entry in CORPUS:
            ids.append(entry["id"])
            docs.append(entry["text"])
            metadatas.append(
                {"title": entry["title"], "source": entry["source"]}
            )
        embeddings = self.embed(docs)
        self._collection.add(
            ids=ids, documents=docs, embeddings=embeddings.tolist(),
            metadatas=metadatas,
        )
        logger.info(
            "index built", extra={"chunks": len(ids), "collection": self._collection_name}
        )
        return len(ids)

    def retrieve(self, query: str, top_k: int | None = None,
                 min_score: float | None = None):
        """Return up to top_k chunks above min_score as list of
        (id, text, score) tuples."""
        settings = self._settings
        top_k = top_k if top_k is not None else settings.retrieval_top_k
        min_score = min_score if min_score is not None else settings.retrieval_min_score
        if self.is_empty():
            return []
        query_embedding = self.embed(
            [_QUERY_INSTRUCTION + query]
        )
        result = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=min(top_k, self.count()),
            include=["documents", "distances"],
        )
        chunks = []
        for doc_id, doc, dist in zip(
            result["ids"][0], result["documents"][0], result["distances"][0]
        ):
            score = 1.0 - float(dist)  # cosine distance -> similarity
            if score < min_score:
                continue
            chunks.append((doc_id, doc, round(score, 4)))
        return chunks


_store_singleton: RetrievalStore | None = None
_store_lock = threading.Lock()


def get_store() -> RetrievalStore:
    global _store_singleton
    with _store_lock:
        if _store_singleton is None:
            _store_singleton = RetrievalStore()
        return _store_singleton
