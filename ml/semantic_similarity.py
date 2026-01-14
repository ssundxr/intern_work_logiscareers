from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from logis_ai_candidate_engine.ml.embedding_model import EmbeddingModel


@dataclass(frozen=True)
class SemanticSimilarityResult:
    score: int
    explanation: str


class SemanticSimilarityScorer:
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        denom = (float(np.linalg.norm(a)) * float(np.linalg.norm(b)))
        if denom <= 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    @staticmethod
    def score(
        job_text: str,
        candidate_text: str,
        job_profile_text: Optional[str] = None,
    ) -> SemanticSimilarityResult:
        combined_job_text = (job_text or "").strip()
        if job_profile_text:
            combined_job_text = f"{combined_job_text}\n{job_profile_text}".strip()

        combined_candidate_text = (candidate_text or "").strip()

        if not combined_job_text or not combined_candidate_text:
            return SemanticSimilarityResult(
                score=0,
                explanation="Insufficient text provided for semantic comparison",
            )

        vectors = EmbeddingModel.encode([combined_job_text, combined_candidate_text])
        a = np.asarray(vectors[0], dtype=np.float32)
        b = np.asarray(vectors[1], dtype=np.float32)
        sim = SemanticSimilarityScorer._cosine_similarity(a, b)
        score = int(round(max(0.0, min(1.0, (sim + 1.0) / 2.0)) * 100))

        return SemanticSimilarityResult(
            score=score,
            explanation=f"Semantic similarity score computed as {score}/100",
        )
