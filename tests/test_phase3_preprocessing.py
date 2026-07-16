from src.zepto_discovery.models import ReviewRecord, SourceType
from src.zepto_discovery.preprocessing import PreprocessingPipeline


def test_phase3_preprocessing_pipeline_cleans_deduplicates_and_chunks() -> None:
    pipeline = PreprocessingPipeline()

    reviews = [
        ReviewRecord(
            id="r1",
            source=SourceType.PLAY_STORE,
            source_url="https://example.com/play",
            raw_text="Delivery was fast and the packaging was fine!",
        ),
        ReviewRecord(
            id="r2",
            source=SourceType.APP_STORE,
            source_url="https://example.com/app",
            raw_text="Delivery was fast and the packaging was fine!",
        ),
    ]

    deduped = pipeline.deduplicate(reviews)
    chunks = pipeline.build_chunks(deduped)
    embeddings = pipeline.build_embeddings(chunks)

    assert len(deduped) == 1
    assert len(chunks) == 1
    assert len(embeddings) == 1
    assert embeddings[0]["embedding"]


def test_phase3_chunking_uses_overlapping_windows() -> None:
    pipeline = PreprocessingPipeline()
    words = [f"w{i}" for i in range(100)]
    text = " ".join(words)

    chunks = pipeline.chunk_text(text, chunk_size=70, overlap=20)

    assert len(chunks) >= 2
    assert chunks[1].split()[0] == "w50"
    assert chunks[1].split()[-1] == "w99"
