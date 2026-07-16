from __future__ import annotations

import re
from typing import Any

from .models import AnnotationRecord, ReviewRecord


class Phase4AnnotationPipeline:
    """Lightweight rule-based annotation pipeline for Phase 4.

    Implements the core behaviors asked for in the implementation plan:
    - category, sentiment, behavior signal, and reason labeling
    - confidence scoring
    - evidence capture with traceable snippets
    - deterministic, auditable outputs suitable for early prototyping
    """

    def __init__(self) -> None:
        self._category_rules = [
            ("repeat_basket_lockin", ["trust the routine", "buy groceries again", "repeat", "trust"]),
            ("category_exploration_block", ["avoid buying", "risk", "risky", "personal care", "avoid"]),
        ]

    def annotate_reviews(self, reviews: list[ReviewRecord]) -> list[AnnotationRecord]:
        annotations: list[AnnotationRecord] = []
        for review in reviews:
            annotations.append(self.annotate_review(review))
        return annotations

    def annotate_review(self, review: ReviewRecord) -> AnnotationRecord:
        text = (review.cleaned_text or review.raw_text or "").lower()
        evidence = self._extract_evidence(text)
        category, confidence, reason, behavior_signal, sentiment = self._classify(text, evidence)
        return AnnotationRecord(
            review_id=review.id,
            category=category,
            sentiment=sentiment,
            behavior_signal=behavior_signal,
            reason=reason,
            confidence=confidence,
            evidence=evidence,
        )

    def _extract_evidence(self, text: str) -> list[str]:
        snippets: list[str] = []
        if not text:
            return snippets
        for pattern in [r"delivery was fast", r"trust the routine", r"buy groceries again", r"avoid buying", r"packaging quality feels risky", r"risky"]:
            if re.search(pattern, text):
                snippets.append(pattern)
        # Fallback to the first sentence if nothing matched
        if not snippets:
            snippets.append(text[:80])
        return snippets

    def _classify(self, text: str, evidence: list[str]) -> tuple[str | None, float, str | None, str | None, str | None]:
        if "trust the routine" in text or "buy groceries again" in text or "repeat" in text:
            return (
                "repeat_basket_lockin",
                0.86,
                "User appears locked into a familiar basket due to habit or trust in routine.",
                "repeat_purchase",
                "positive",
            )

        if "avoid buying" in text or "risky" in text or "personal care" in text:
            return (
                "category_exploration_block",
                0.84,
                "User is avoiding broader categories because the current experience feels risky.",
                "risk_averse",
                "negative",
            )

        return (
            "unknown",
            0.4,
            "No strong rule matched the review text.",
            "unclear",
            "neutral",
        )
