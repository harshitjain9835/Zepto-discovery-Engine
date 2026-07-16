from src.zepto_discovery.annotation import Phase4AnnotationPipeline
from src.zepto_discovery.insights import Phase5InsightPipeline
from src.zepto_discovery.models import ReviewRecord, SourceType


def test_phase5_insight_pipeline_builds_cards_from_annotations() -> None:
    annotation_pipeline = Phase4AnnotationPipeline()
    insight_pipeline = Phase5InsightPipeline()

    reviews = [
        ReviewRecord(
            id="review-001",
            source=SourceType.PLAY_STORE,
            source_url="https://example.com/play",
            raw_text="Delivery was fast but I only buy groceries again because I trust the routine.",
        ),
        ReviewRecord(
            id="review-002",
            source=SourceType.APP_STORE,
            source_url="https://example.com/app",
            raw_text="I avoid buying personal care because packaging quality feels risky.",
        ),
    ]

    annotations = annotation_pipeline.annotate_reviews(reviews)
    insight_cards = insight_pipeline.build_insight_cards(reviews, annotations)

    assert len(insight_cards) >= 1
    assert insight_cards[0].title
    assert insight_cards[0].summary
    assert insight_cards[0].evidence_ids
    assert insight_cards[0].confidence >= 0.5
