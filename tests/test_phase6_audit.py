from __future__ import annotations

from src.zepto_discovery.audit import AuditDecision, Phase6AuditPipeline
from src.zepto_discovery.models import AnnotationRecord


def create_sample_annotations(counts: dict[float, int]) -> list[AnnotationRecord]:
    """Helper to create a list of annotations with specified confidence levels."""
    annotations: list[AnnotationRecord] = []
    i = 0
    for confidence, count in counts.items():
        for _ in range(count):
            annotations.append(
                AnnotationRecord(
                    review_id=f"review-{i}",
                    category="test_category",
                    confidence=confidence,
                )
            )
            i += 1
    return annotations


def test_phase6_sampling_prioritizes_low_confidence() -> None:
    """Verify that low-confidence annotations are always sampled first."""
    pipeline = Phase6AuditPipeline()
    annotations = create_sample_annotations({0.5: 5, 0.9: 10})  # 5 low, 10 high

    # Sample size is smaller than the low-confidence pool
    sample = pipeline.sample_for_audit(annotations, sample_size=3, confidence_threshold=0.75)
    assert len(sample) == 3
    assert all(ann.confidence < 0.75 for ann in sample)


def test_phase6_sampling_fills_with_high_confidence() -> None:
    """Verify that high-confidence items are added if the sample is not full."""
    pipeline = Phase6AuditPipeline()
    annotations = create_sample_annotations({0.5: 5, 0.9: 10})  # 5 low, 10 high

    # Sample size is larger than the low-confidence pool
    sample = pipeline.sample_for_audit(annotations, sample_size=8, confidence_threshold=0.75)
    assert len(sample) == 8
    low_confidence_count = sum(1 for ann in sample if ann.confidence < 0.75)
    high_confidence_count = sum(1 for ann in sample if ann.confidence >= 0.75)
    assert low_confidence_count == 5
    assert high_confidence_count == 3


def test_phase6_sampling_handles_small_population() -> None:
    """Verify sampling works when the total population is smaller than the sample size."""
    pipeline = Phase6AuditPipeline()
    annotations = create_sample_annotations({0.5: 2, 0.9: 2})  # 4 total

    sample = pipeline.sample_for_audit(annotations, sample_size=10, confidence_threshold=0.75)
    assert len(sample) == 4


def test_phase6_applies_audit_corrections() -> None:
    """Verify that 'corrected' audit decisions update annotations."""
    pipeline = Phase6AuditPipeline()
    annotations = [
        AnnotationRecord(review_id="review-1", category="old_category", confidence=0.6),
        AnnotationRecord(review_id="review-2", category="other", confidence=0.9),
    ]

    decisions = [
        AuditDecision(
            annotation_id="review-1",
            reviewer_id="auditor-1",
            decision="corrected",
            corrected_data={"category": "new_category", "confidence": 0.99},
        ),
        AuditDecision(
            annotation_id="review-2",
            reviewer_id="auditor-1",
            decision="accepted",
        ),
    ]

    corrected_annotations = pipeline.apply_audit_decisions(annotations, decisions)

    assert len(corrected_annotations) == 2
    assert len(pipeline.audit_history) == 2

    ann_1_map = {ann.review_id: ann for ann in corrected_annotations}
    corrected_ann_1 = ann_1_map["review-1"]
    original_ann_2 = ann_1_map["review-2"]

    assert corrected_ann_1.category == "new_category"
    assert corrected_ann_1.confidence == 0.99
    assert original_ann_2.category == "other"  # Unchanged