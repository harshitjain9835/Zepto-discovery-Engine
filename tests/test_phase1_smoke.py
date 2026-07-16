from pathlib import Path

from src.zepto_discovery.config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.zepto_discovery.pipeline import Phase1Pipeline


def test_phase1_pipeline_creates_seed_and_manifest(tmp_path: Path) -> None:
    pipeline = Phase1Pipeline(raw_dir=tmp_path / "raw", processed_dir=tmp_path / "processed")

    reviews = pipeline.seed_sample_reviews()
    manifest = pipeline.build_index_manifest(reviews)

    assert len(reviews) == 2
    assert len(manifest) == 2
    assert (tmp_path / "raw" / "review-001.json").exists()
    assert (tmp_path / "processed" / "review_manifest.json").exists()
