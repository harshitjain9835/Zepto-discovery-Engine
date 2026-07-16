from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import RAW_DATA_DIR, PROCESSED_DATA_DIR, SOURCE_URLS


class IngestionPipeline:
    def __init__(self, raw_dir: Path | None = None, processed_dir: Path | None = None) -> None:
        self.raw_dir = raw_dir or RAW_DATA_DIR
        self.processed_dir = processed_dir or PROCESSED_DATA_DIR
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _build_payload(self, name: str, source_url: str) -> dict[str, Any]:
        return {
            "source": name,
            "source_url": source_url,
            "collected_at": "2026-07-16T00:00:00Z",
            "review_samples": [
                {
                    "id": f"{name}-sample-1",
                    "text": f"Sample review from {name}",
                    "language": "en",
                }
            ],
        }

    def _write_payload(self, name: str, payload: dict[str, Any]) -> Path:
        output_path = self.raw_dir / f"{name}.json"
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return output_path

    def run(self) -> dict[str, dict[str, Any]]:
        manifest: dict[str, dict[str, Any]] = {}
        for name, url in SOURCE_URLS.items():
            if not url:
                continue
            payload = self._build_payload(name, url)
            self._write_payload(name, payload)
            manifest[name] = payload

        output_path = self.processed_dir / "ingestion_manifest.json"
        output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest
