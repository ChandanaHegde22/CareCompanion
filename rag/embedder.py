"""
rag/embedder.py – Sentence-Transformer embedding generation with Streamlit caching.
Model: all-MiniLM-L6-v2 (384-dim, fast, good quality).
"""

import logging
import numpy as np

import config

logger = logging.getLogger(__name__)

_model = None


def _load_model():
    """Lazy-load the embedding model (downloaded once, cached in memory)."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s", config.EMBEDDING_MODEL)
            _model = SentenceTransformer(config.EMBEDDING_MODEL)
            logger.info("Embedding model loaded.")
        except Exception as exc:
            logger.error("Failed to load embedding model: %s", exc)
            _model = None
    return _model


def get_embedding(text: str) -> np.ndarray | None:
    """Embed a single string. Returns a 1-D numpy array or None on failure."""
    model = _load_model()
    if model is None:
        return None
    try:
        emb = model.encode(text, show_progress_bar=False, normalize_embeddings=True)
        return emb.astype("float32")
    except Exception as exc:
        logger.error("Embedding failed: %s", exc)
        return None


def get_embeddings(texts: list[str], batch_size: int = 32) -> np.ndarray | None:
    """
    Embed a list of strings in batches.
    Returns a 2-D numpy array of shape (len(texts), 384) or None.
    """
    model = _load_model()
    if model is None:
        return None
    try:
        embs = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embs.astype("float32")
    except Exception as exc:
        logger.error("Batch embedding failed: %s", exc)
        return None


def embedding_dimension() -> int:
    return config.EMBEDDING_DIM
