from __future__ import annotations

import random

from src.zepto_discovery.pipeline import Phase1Pipeline
from src.zepto_discovery.annotation import Phase4AnnotationPipeline
from src.zepto_discovery.audit import AuditDecision, Phase6AuditPipeline
from src.zepto_discovery.ingestion import IngestionPipeline
from src.zepto_discovery.models import AnnotationRecord, ReviewRecord, SourceType
from src.zepto_discovery.monitoring import Phase8MonitoringPipeline


def run_backend_pipeline() -> None:
    """
    Executes the end-to-end Zepto Discovery Engine pipeline.
    This script simulates the flow from data ingestion to monitoring.
    It also generates a larger set of mock reviews for the frontend to use.
    """
    print("🚀 Starting Zepto Discovery Engine Backend Pipeline...")

    # === Phase 1: Generate a larger mock review dataset for the frontend ===
    print("\n[Phase 1] Generating mock review data for frontend app...")
    p1_pipeline = Phase1Pipeline()
    mock_reviews_for_app = [
        ReviewRecord(
            id=f"review_{i:03d}",
            source=random.choice(list(SourceType)),
            source_url="https://example.com/mock",
            raw_text=random.choice([
                "Delivery was fast but I only buy groceries again because I trust the routine.",
                "I avoid buying personal care because packaging quality feels risky.",
                "The app is great for repeat orders of milk and bread.",
                "Why are there limits on how many snacks I can buy? It's frustrating.",
                "Tried ordering baby products for the first time, but the box was damaged.",
                "Customer support took forever to respond to my issue with expired yogurt.",
                "Zepto is super fast for late-night ice cream cravings!",
                "I wish I could trust the quality of fresh vegetables more.",
                "The Supermall section is interesting, but I'm hesitant to try it.",
                "My first order was perfect, will definitely use it again for my weekly groceries.",
            ]),
        ) for i in range(100)
    ]
    p1_pipeline.save_reviews(mock_reviews_for_app)
    print(f"✅ Saved {len(mock_reviews_for_app)} mock reviews to 'data/raw' for the app.")

    # === Phase 2: Data Ingestion ===
    print("\n[Phase 2] Running data ingestion pipeline...")
    ingestion_pipeline = IngestionPipeline()
    ingestion_pipeline.run()
    print("✅ Ingestion complete. Raw data saved to 'data/raw'.")

    # === Phases 3-5: Annotation and Insight Generation ===
    # Use the actual annotation pipeline to create realistic data.
    print("\n[Phases 3-5] Running annotation pipeline...")
    annotation_pipeline = Phase4AnnotationPipeline()
    annotations: list[AnnotationRecord] = annotation_pipeline.annotate_reviews(mock_reviews_for_app)
    print(f"✅ Generated {len(annotations)} annotations.")

    # === Phase 6: Human Audit and Validation ===
    print("\n[Phase 6] Running human audit and validation pipeline...")
    audit_pipeline = Phase6AuditPipeline()

    # 1. Sample annotations for review (e.g., 10% of the data)
    sample_for_review = audit_pipeline.sample_for_audit(annotations, sample_size=10)
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
        final_annotations = audit_pipeline.apply_audit_decisions(annotations, [decision])
    else:
        final_annotations = annotations
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
