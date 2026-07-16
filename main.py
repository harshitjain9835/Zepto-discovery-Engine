from __future__ import annotations

import random

from src.zepto_discovery.audit import AuditDecision, Phase6AuditPipeline
from src.zepto_discovery.ingestion import IngestionPipeline
from src.zepto_discovery.models import AnnotationRecord
from src.zepto_discovery.monitoring import Phase8MonitoringPipeline


def run_backend_pipeline() -> None:
    """
    Executes the end-to-end Zepto Discovery Engine pipeline.
    This script simulates the flow from data ingestion to monitoring.
    """
    print("🚀 Starting Zepto Discovery Engine Backend Pipeline...")

    # === Phase 2: Data Ingestion ===
    print("\n[Phase 2] Running data ingestion pipeline...")
    ingestion_pipeline = IngestionPipeline()
    ingestion_pipeline.run()
    print("✅ Ingestion complete. Raw data saved to 'data/raw'.")

    # === Phases 3-5: Mock Annotation Data ===
    # In a real pipeline, this data would come from cleaning, chunking,
    # and annotation steps (Phases 3, 4, 5). Here, we generate mock data.
    print("\n[Phases 3-5] Generating mock annotation data...")
    mock_annotations = [
        AnnotationRecord(
            review_id=f"review_{i}",
            category=random.choice(["grocery", "personal_care", "delivery"]),
            confidence=random.uniform(0.5, 1.0),
        )
        for i in range(100)
    ]
    print(f"✅ Generated {len(mock_annotations)} mock annotations.")

    # === Phase 6: Human Audit and Validation ===
    print("\n[Phase 6] Running human audit and validation pipeline...")
    audit_pipeline = Phase6AuditPipeline()

    # 1. Sample annotations for review (e.g., 10% of the data)
    sample_for_review = audit_pipeline.sample_for_audit(mock_annotations, sample_size=10)
    print(f"🔍 Sampled {len(sample_for_review)} annotations for audit.")

    # 2. Simulate a human making a correction
    if sample_for_review:
        ann_to_correct = sample_for_review[0]
        decision = AuditDecision(
            annotation_id=ann_to_correct.review_id,
            reviewer_id="auditor-x",
            decision="corrected",
            corrected_data={"category": "supermall", "confidence": 0.99},
            comments="User was talking about a non-grocery item.",
        )
        print(f"✍️  Simulating correction for annotation '{ann_to_correct.review_id}'.")
        final_annotations = audit_pipeline.apply_audit_decisions(mock_annotations, [decision])
    else:
        final_annotations = mock_annotations
    print("✅ Audit process complete.")

    # === Phase 8: Monitoring and Trend Analysis ===
    print("\n[Phase 8] Running monitoring pipeline...")
    monitoring_pipeline = Phase8MonitoringPipeline()
    health_report = monitoring_pipeline.generate_health_report(final_annotations)

    print("📊 Generated Pipeline Health Report:")
    print(f"  - Total Annotations: {health_report.total_annotations}")
    print(f"  - Average Confidence: {health_report.average_confidence:.2f}")
    print(f"  - Low-Confidence Count (<0.75): {health_report.low_confidence_count}")
    print(f"  - Category Distribution: {health_report.category_distribution}")
    print("✅ Monitoring complete.")

    print("\n🎉 Backend pipeline run finished successfully!")


if __name__ == "__main__":
    run_backend_pipeline()