"""
tests/conftest.py – Shared pytest fixtures for CareCompanion tests.
Uses a temporary FILE-based SQLite (not :memory:) so all services share one DB.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# ── Add project root to path ──────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Mock sentence_transformers for offline testing ────────────────────────────
import numpy as np
from types import ModuleType

class MockSentenceTransformer:
    def __init__(self, model_name=None, *args, **kwargs):
        self.dim = 384
        self.vocab = {
            "blood": 0,
            "pressure": 1,
            "hba1c": 2,
            "diabetes": 3,
            "metformin": 4,
            "cholesterol": 5,
            "lipid": 6,
            "hdl": 6,
            "ldl": 6,
            "discharge": 7,
            "january": 7,
            "follow-up": 8
        }

    def encode(self, sentences, *args, **kwargs):
        def embed_one(text):
            text_lower = text.lower()
            v = np.random.randn(self.dim) * 0.01
            for word, idx in self.vocab.items():
                if word in text_lower:
                    v[idx] += 10.0
            return v / np.linalg.norm(v)

        if isinstance(sentences, str):
            return embed_one(sentences)
        else:
            return np.array([embed_one(s) for s in sentences])

st_module = ModuleType("sentence_transformers")
st_module.SentenceTransformer = MockSentenceTransformer
sys.modules["sentence_transformers"] = st_module

# ── Temp directories for the entire test session ──────────────────────────────
_tmp_db_file  = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db_path  = _tmp_db_file.name
_tmp_db_file.close()

_tmp_upload   = tempfile.mkdtemp()
_tmp_vectors  = tempfile.mkdtemp()
_tmp_logs     = tempfile.mkdtemp()

# ── Patch config BEFORE any other imports ─────────────────────────────────────
os.environ["GEMINI_API_KEY"]     = "test_key"
os.environ["DATABASE_PATH"]      = _tmp_db_path
os.environ["UPLOADS_PATH"]       = _tmp_upload
os.environ["VECTOR_STORE_PATH"]  = _tmp_vectors
os.environ["LOGS_PATH"]          = _tmp_logs

import config
config.DATABASE_PATH     = _tmp_db_path
config.UPLOADS_PATH      = _tmp_upload
config.VECTOR_STORE_PATH = _tmp_vectors
config.LOGS_PATH         = _tmp_logs
config.GEMINI_API_KEY    = ""   # disable real AI calls in tests


@pytest.fixture(scope="session", autouse=True)
def init_test_database():
    """Create all tables once for the entire test session."""
    from database.schema import init_db
    init_db()
    yield
    # Cleanup after all tests
    try:
        os.unlink(_tmp_db_path)
    except Exception:
        pass
