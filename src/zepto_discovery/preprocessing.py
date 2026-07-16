from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .models import ReviewRecord


class PreprocessingPipeline:
    def __init__(self) -> None:
        self._stopwords = {"the", "and", "for", "with", "this", "that", "is", "are", "was", "were", "to", "of"}

    def clean_text(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()

    def normalize_language(self, text: str) -> str:
        return text.lower()

    def deduplicate(self, reviews: list[ReviewRecord]) -> list[ReviewRecord]:
        seen: dict[str, ReviewRecord] = {}
        for review in reviews:
            key = self.clean_text(review.raw_text)
            if key not in seen:
                seen[key] = review
        return list(seen.values())

    def chunk_text(self, text: str, chunk_size: int = 70, overlap: int = 20) -> list[str]:
        words = text.split()
        if not words:
            return []
        if len(words) <= chunk_size:
            return [text]

        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            if end == len(words):
                break
            start += max(1, chunk_size - overlap)
        return chunks

    def build_chunks(self, reviews: list[ReviewRecord]) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        for review in reviews:
            cleaned = self.clean_text(review.raw_text)
            normalized = self.normalize_language(cleaned)
            for index, chunk in enumerate(self.chunk_text(normalized)):
                chunks.append(
                    {
                        "review_id": review.id,
                        "chunk_id": f"{review.id}-chunk-{index}",
                        "text": chunk,
                        "embedding_text": chunk,
                        "word_count": len(chunk.split()),
                        "embedding_small": None,
                        "embedding_large": None,
                        "model_small": None,
                        "model_large": None,
                        "created_at": None,
                        "provenance": review.metadata.get("source_url") if review.metadata else None,
                    }
                )
        return chunks

    def build_embeddings(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        embedded_chunks: list[dict[str, Any]] = []
        for chunk in chunks:
            text = chunk["embedding_text"]
            token_counts = Counter(text.split())
            vector = {token: float(count) for token, count in token_counts.items() if token not in self._stopwords}
            # by default, treat this as a small-model embedding
            chunk_small = {**chunk, "embedding_small": vector, "model_small": "local-token-counts-v1", "embedding": vector}
            embedded_chunks.append(chunk_small)
        return embedded_chunks

    def re_rank_with_large(self, query_text: str, candidate_chunks: list[dict[str, Any]], top_k: int = 20) -> list[dict[str, Any]]:
        """Simulate a re-ranking step using a higher-fidelity embedding for the top candidates.

        In a real deployment this would call BGE-large (or another high-quality model).
        Here we use the same token-count vectorization as a placeholder and sort by simple overlap score.
        """
        query_clean = self.clean_text(query_text)
        query_tokens = set(query_clean.split())

        def score(chunk: dict[str, Any]) -> int:
            tokens = set(chunk.get("embedding_text", "").split())
            return len(query_tokens.intersection(tokens))

        ranked = sorted(candidate_chunks, key=score, reverse=True)
        return ranked[:top_k]
