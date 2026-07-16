from pathlib import Path

from src.zepto_discovery.ingestion import IngestionPipeline


def test_phase2_pipeline_ingests_sources_and_writes_payloads(tmp_path: Path) -> None:
    pipeline = IngestionPipeline(raw_dir=tmp_path / "raw", processed_dir=tmp_path / "processed")

    manifest = pipeline.run()

    assert set(manifest.keys()) == {"play_store", "app_store", "reddit"}
    assert (tmp_path / "raw" / "play_store.json").exists()
    assert (tmp_path / "raw" / "app_store.json").exists()
    assert (tmp_path / "raw" / "reddit.json").exists()
    assert (tmp_path / "processed" / "ingestion_manifest.json").exists()
