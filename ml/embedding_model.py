# Loads and manages embedding models for semantic matching
# ml/embedding_model.py

import hashlib
import os
import threading
from typing import List, Optional

import numpy as np

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


class EmbeddingModel:
    """
    Singleton-style embedding model wrapper.
    Responsible only for encoding text into vectors.
    """

    _model: Optional["SentenceTransformer"] = None
    _lock = threading.Lock()

    @staticmethod
    def load(model_name: str = "all-MiniLM-L6-v2") -> "SentenceTransformer":
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers is not available")

        resolved_name = os.getenv("EMBEDDING_MODEL_NAME", model_name)

        if EmbeddingModel._model is None:
            with EmbeddingModel._lock:
                if EmbeddingModel._model is None:
                    EmbeddingModel._model = SentenceTransformer(resolved_name)

        return EmbeddingModel._model

    @staticmethod
    def _fallback_encode(texts: List[str], dim: int = 384) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            tokens = [t for t in (text or "").lower().split() if t]
            vec = np.zeros(dim, dtype=np.float32)
            for tok in tokens:
                digest = hashlib.sha256(tok.encode("utf-8")).digest()
                idx = int.from_bytes(digest[:4], byteorder="little", signed=False) % dim
                vec[idx] += 1.0
            norm = float(np.linalg.norm(vec))
            if norm > 0:
                vec = vec / norm
            vectors.append(vec.astype(float).tolist())
        return vectors

    @staticmethod
    def encode(texts: List[str]) -> List[List[float]]:
        try:
            model = EmbeddingModel.load()
            return model.encode(texts, normalize_embeddings=True).tolist()
        except Exception:
            return EmbeddingModel._fallback_encode(texts)
