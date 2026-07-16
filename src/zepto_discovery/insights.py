from __future__ import annotations

from collections import Counter
from typing import Any

from .models import AnnotationRecord, InsightCard, ReviewRecord


class Phase5InsightPipeline:
    """Simple Phase 5 insight generator.

    The pipeline groups annotations into a small number of themes, ranks them by
    frequency and confidence, and generates evidence-backed InsightCard objects.
    This is intentionally deterministic and lightweight for the MVP.
    """

    def __init__(self) -> None:
        self.theme_labels = {
            "repeat_basket_lockin": "Repeat-basket lock-in",
            "category_exploration_block": "Category exploration block",
        }

    def build_insight_cards(
        self,
        reviews: list[ReviewRecord],
        annotations: list[AnnotationRecord],
    ) -> list[InsightCard]:
        if len(reviews) != len(annotations):
            raise ValueError("Reviews and annotations must have the same length")

        grouped: dict[str, list[AnnotationRecord]] = {}
        for review, annotation in zip(reviews, annotations):
            if not annotation.category or annotation.category == "unknown":
                continue
            grouped.setdefault(annotation.category, []).append(annotation)

        cards: list[InsightCard] = []
        for category, entries in grouped.items():
            count = len(entries)
            avg_confidence = sum(entry.confidence for entry in entries) / max(count, 1)
            evidence_ids = [entry.review_id for entry in entries]
            title = self.theme_labels.get(category, category.replace("_", " ").title())
            summary = self._build_summary(category, count, avg_confidence)
            source_mix = self._build_source_mix(reviews, entries)
            cards.append(
                InsightCard(
                    id=f"insight-{category}",
                    title=title,
                    summary=summary,
                    evidence_ids=evidence_ids,
                    source_mix=source_mix,
                    confidence=round(min(0.99, 0.55 + avg_confidence * 0.4), 2),
                )
            )

        cards.sort(key=lambda card: card.confidence, reverse=True)
        return cards

    def _build_summary(self, category: str, count: int, avg_confidence: float) -> str:
        if category == "repeat_basket_lockin":
            return (
                f"Users repeatedly return to a narrow basket and appear to trust the routine, "
                f"suggesting a strong lock-in signal across {count} review(s)."
            )
        if category == "category_exploration_block":
            return (
                f"Users are avoiding broader categories because the experience feels risky, "
                f"with strong evidence across {count} review(s)."
            )
        return f"Theme '{category}' was detected with moderate confidence in {count} review(s)."

    def _build_source_mix(self, reviews: list[ReviewRecord], entries: list[AnnotationRecord]) -> dict[str, int]:
        counts: Counter[str] = Counter()
        review_lookup = {review.id: review for review in reviews}
        for entry in entries:
            review = review_lookup.get(entry.review_id)
            if review is None:
                continue
            counts[review.source.value] += 1
        return dict(counts)
