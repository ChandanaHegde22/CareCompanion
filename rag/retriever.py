"""
rag/retriever.py – FAISS-based document retriever.
Each user gets their own FAISS index stored on disk.
"""

import json
import logging
import pickle
from pathlib import Path

import numpy as np

import config
from rag.embedder import get_embedding, get_embeddings, embedding_dimension
from utils.helpers import get_vector_store_path

logger = logging.getLogger(__name__)

_faiss_available = False
try:
    import faiss
    _faiss_available = True
except ImportError:
    logger.error("faiss-cpu not installed. RAG retrieval unavailable.")


def _index_file(user_id: int) -> Path:
    return get_vector_store_path(user_id) / "faiss.index"


def _meta_file(user_id: int) -> Path:
    return get_vector_store_path(user_id) / "metadata.pkl"


# ── Build / Save / Load ───────────────────────────────────────────────────────

def build_and_save_index(user_id: int, chunks: list[dict]) -> bool:
    """
    Embed all chunks, build a FAISS index and persist to disk.
    chunks: list of {"text": str, "source": str, "chunk_index": int}
    """
    if not _faiss_available:
        logger.error("FAISS not available.")
        return False
    if not chunks:
        logger.warning("No chunks to index for user %s", user_id)
        return False

    texts = [c["text"] for c in chunks]
    embs  = get_embeddings(texts)
    if embs is None or len(embs) == 0:
        logger.error("Failed to embed chunks for user %s", user_id)
        return False

    dim   = embedding_dimension()
    index = faiss.IndexFlatIP(dim)   # Inner product (cosine on normalised vecs)
    index.add(embs)

    idx_path  = _index_file(user_id)
    meta_path = _meta_file(user_id)

    try:
        faiss.write_index(index, str(idx_path))
        with open(meta_path, "wb") as f:
            pickle.dump(chunks, f)
        logger.info("FAISS index saved for user %s: %s chunks", user_id, len(chunks))
        return True
    except Exception as exc:
        logger.error("Failed to save FAISS index: %s", exc)
        return False


def _load_index(user_id: int):
    """Load FAISS index from disk. Returns (index, chunks) or (None, [])."""
    idx_path  = _index_file(user_id)
    meta_path = _meta_file(user_id)
    if not idx_path.exists() or not meta_path.exists():
        return None, []
    try:
        index  = faiss.read_index(str(idx_path))
        with open(meta_path, "rb") as f:
            chunks = pickle.load(f)
        return index, chunks
    except Exception as exc:
        logger.error("Failed to load FAISS index for user %s: %s", user_id, exc)
        return None, []


def has_index(user_id: int) -> bool:
    return _index_file(user_id).exists() and _meta_file(user_id).exists()


# ── Search ────────────────────────────────────────────────────────────────────

def search(user_id: int, query: str, top_k: int = 5) -> list[dict]:
    """
    Retrieve the top-k most relevant chunks for *query*.

    Returns list of {"text": str, "source": str, "score": float, "chunk_index": int}
    """
    if not _faiss_available:
        return []

    index, chunks = _load_index(user_id)
    if index is None or not chunks:
        return []

    q_emb = get_embedding(query)
    if q_emb is None:
        return []

    q_arr   = q_emb.reshape(1, -1)
    k       = min(top_k, index.ntotal)
    scores, indices = index.search(q_arr, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(chunks):
            continue
        chunk = dict(chunks[idx])
        chunk["score"] = float(score)
        results.append(chunk)

    return results


# ── Index management ──────────────────────────────────────────────────────────

def add_chunks_to_index(user_id: int, new_chunks: list[dict]) -> bool:
    """Append new chunks to an existing index (or create new one)."""
    if not _faiss_available:
        return False

    index, existing_chunks = _load_index(user_id)
    all_chunks = list(existing_chunks) + list(new_chunks)

    # Rebuild entire index with all chunks
    return build_and_save_index(user_id, all_chunks)


def delete_user_index(user_id: int) -> None:
    """Remove FAISS index and metadata for a user."""
    for f in (_index_file(user_id), _meta_file(user_id)):
        try:
            f.unlink(missing_ok=True)
        except Exception:
            pass
    logger.info("Deleted FAISS index for user %s", user_id)


def get_index_size(user_id: int) -> int:
    """Return number of vectors in the user's index."""
    if not _faiss_available:
        return 0
    index, _ = _load_index(user_id)
    return index.ntotal if index else 0
