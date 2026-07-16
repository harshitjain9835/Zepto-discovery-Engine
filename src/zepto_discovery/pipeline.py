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

    def seed_sample_reviews(self) -> list[ReviewRecord]:
        sample_reviews = [
            ReviewRecord(
                id="review-001",
                source=SourceType.PLAY_STORE,
                source_url="https://play.google.com/store/apps/details?id=com.zeptoconsumerapp&hl=en_IN",
                raw_text="Delivery was fast but I only buy groceries again because I trust the routine.",
                metadata={"platform": "play_store"},
            ),
            ReviewRecord(
                id="review-002",
                source=SourceType.APP_STORE,
                source_url="https://apps.apple.com/in/app/zepto-groceries-in-minutes/id1575323645?see-all=reviews&platform=iphone",
                raw_text="I avoid buying personal care because packaging quality feels risky.",
                metadata={"platform": "app_store"},
            ),
        ]

        for review in sample_reviews:
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
