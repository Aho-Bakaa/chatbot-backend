"""Unit tests for the retrieval store (fake embedder — no model download)."""

import numpy as np
import pytest

from app.rag.store import RetrievalStore


class FakeEmbedder:
    """Deterministic vectors: document ids map to orthogonal-ish directions."""

    def encode(self, texts, normalize_embeddings=True):
        vecs = []
        for text in texts:
            if "goggles" in text or "eyes" in text or "wear" in text:
                vecs.append([1.0, 0.0, 0.0, 0.0])
            elif "acid" in text:
                vecs.append([0.0, 1.0, 0.0, 0.0])
            else:
                vecs.append([0.0, 0.0, 1.0, 0.0])
        return np.array(vecs, dtype=np.float32)


@pytest.fixture
def store(tmp_path, monkeypatch):
    from app.config import Settings
    import app.rag.store as store_module

    test_settings = Settings(
        _env_file=None,
        chroma_dir=str(tmp_path / "chroma_test"),
        embedding_model="fake",
    )
    monkeypatch.setattr(store_module, "get_settings", lambda: test_settings)
    s = RetrievalStore()
    s._embedder = FakeEmbedder()  # bypass model download
    return s


TEST_CORPUS = [
    {"id": "doc-goggles", "title": "Goggles", "source": "s",
     "text": "Always wear safety goggles in the lab."},
    {"id": "doc-acid", "title": "Acid", "source": "s",
     "text": "Add acid to water, never water to acid."},
    {"id": "doc-other", "title": "Other", "source": "s",
     "text": "Keep benches tidy."},
]


def test_build_index_and_retrieve(store, monkeypatch):
    import app.rag.store as store_module

    monkeypatch.setattr(store_module, "CORPUS", TEST_CORPUS)
    n = store.build_index()
    assert n == 3

    chunks = store.retrieve("what should I wear to protect my eyes?",
                            top_k=1, min_score=0.0)
    assert chunks[0][0] == "doc-goggles"
    assert chunks[0][2] > 0.9


def test_empty_store_returns_no_chunks(store):
    assert store.is_empty() is True
    assert store.retrieve("anything", top_k=3, min_score=0.0) == []


def test_min_score_threshold(store, monkeypatch):
    import app.rag.store as store_module

    monkeypatch.setattr(store_module, "CORPUS", TEST_CORPUS)
    store.build_index()
    # "goggles" query vs "acid" doc is orthogonal (similarity ~0)
    chunks = store.retrieve("what should I wear to protect my eyes?",
                            top_k=3, min_score=0.8)
    assert all(c[0] == "doc-goggles" for c in chunks)
