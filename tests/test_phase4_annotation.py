from src.zepto_discovery.annotation import Phase4AnnotationPipeline
from src.zepto_discovery.models import ReviewRecord, SourceType


def test_phase4_annotation_pipeline_labels_reviews_with_evidence() -> None:
    pipeline = Phase4AnnotationPipeline()
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

    annotations = pipeline.annotate_reviews(reviews)

    assert len(annotations) == 2
    assert annotations[0].category == "repeat_basket_lockin"
    assert annotations[0].sentiment == "positive"
    assert annotations[0].behavior_signal == "repeat_purchase"
    assert annotations[0].confidence >= 0.6
    assert annotations[0].evidence
    assert annotations[1].category == "category_exploration_block"
    assert annotations[1].sentiment == "negative"
    assert annotations[1].behavior_signal == "risk_averse"
