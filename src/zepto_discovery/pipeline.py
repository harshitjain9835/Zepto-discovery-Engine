from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from .models import ReviewRecord, SourceType


class Phase1Pipeline:
    def __init__(self, raw_dir: Path | None = None, processed_dir: Path | None = None) -> None:
        self.raw_dir = raw_dir or RAW_DATA_DIR
        self.processed_dir = processed_dir or PROCESSED_DATA_DIR
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def seed_sample_reviews(self, count: int = 12) -> list[ReviewRecord]:
        templates = [
            ("review-001", SourceType.PLAY_STORE, "Delivery was fast but I only buy groceries again because I trust the routine."),
            ("review-002", SourceType.APP_STORE, "I avoid buying personal care because packaging quality feels risky."),
            ("review-003", SourceType.REDDIT, "The app is great for repeat orders of milk and bread, but the checkout feels slow."),
            ("review-004", SourceType.TRUSTPILOT, "Why are there limits on how many snacks I can buy? It's frustrating and makes category exploration harder."),
            ("review-005", SourceType.PDP_REVIEW, "Tried ordering baby products for the first time, but the box was damaged and the support response was slow."),
            ("review-006", SourceType.PLAY_STORE, "Customer support took forever to respond to my issue with expired yogurt."),
            ("review-007", SourceType.APP_STORE, "Zepto is super fast for late-night ice cream cravings and I love the convenience."),
            ("review-008", SourceType.REDDIT, "I wish I could trust the quality of fresh vegetables more before adding them to my basket."),
            ("review-009", SourceType.TRUSTPILOT, "The Supermall section is interesting, but I'm hesitant to try new categories because delivery reliability feels inconsistent."),
            ("review-010", SourceType.PDP_REVIEW, "My first order was perfect and I will definitely use it again for my weekly groceries."),
            ("review-011", SourceType.PLAY_STORE, "The packaging for skincare products felt flimsy, so I would not buy personal care again."),
            ("review-012", SourceType.APP_STORE, "The search experience is useful, but I want better recommendations for healthy snacks and pantry staples."),
        ]

        sample_reviews: list[ReviewRecord] = []
        for index in range(max(1, count)):
            review_id, source, raw_text = templates[index % len(templates)]
            review = ReviewRecord(
                id=f"{review_id[:-3]}{index + 1:03d}" if index >= len(templates) else review_id,
                source=source,
                source_url="https://example.com/mock-review",
                raw_text=raw_text,
                metadata={"platform": source.value, "synthetic": True},
            )
            sample_reviews.append(review)

            output_path = self.raw_dir / f"{review.id}.json"
            output_path.write_text(review.model_dump_json(indent=2), encoding="utf-8")

        return sample_reviews

    def build_index_manifest(self, reviews: list[ReviewRecord]) -> list[dict[str, Any]]:
        manifest: list[dict[str, Any]] = []
        for review in reviews:
            manifest.append(
                {
                    "id": review.id,
                    "source": review.source.value,
                    "source_url": review.source_url,
                    "raw_text": review.raw_text,
                }
            )

        output_path = self.processed_dir / "review_manifest.json"
        output_path.write_text(__import__("json").dumps(manifest, indent=2), encoding="utf-8")
        return manifest
