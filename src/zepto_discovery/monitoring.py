from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List

from .models import AnnotationRecord


@dataclass
class PipelineHealthReport:
    """A snapshot of pipeline health metrics for a given period."""

    total_annotations: int
    average_confidence: float
    low_confidence_count: int
    category_distribution: Dict[str, int]


@dataclass
class TrendReport:
    """Compares pipeline metrics between two periods to track changes."""

    current_period: PipelineHealthReport
    previous_period: PipelineHealthReport
    confidence_change: float
    low_confidence_count_change: int
    category_distribution_change: Dict[str, int]


class Phase8MonitoringPipeline:
    """Implements monitoring and trend analysis as per Phase 8.

    This pipeline provides methods to:
    1.  Generate health reports on pipeline output quality.
    2.  Track monthly trend changes to observe intervention impact.
    """

    def generate_health_report(
        self,
        annotations: List[AnnotationRecord],
        confidence_threshold: float = 0.75,
    ) -> PipelineHealthReport:
        """Generates a health report for a set of annotations.

        Args:
            annotations: The list of annotations to analyze.
            confidence_threshold: The score below which an annotation is
                                  considered low-confidence.

        Returns:
            A PipelineHealthReport with key metrics.
        """
        if not annotations:
            return PipelineHealthReport(0, 0.0, 0, {})

        total_annotations = len(annotations)
        avg_confidence = sum(ann.confidence for ann in annotations) / total_annotations
        low_confidence_count = sum(
            1 for ann in annotations if ann.confidence < confidence_threshold
        )
        category_distribution = Counter(ann.category for ann in annotations if ann.category)

        return PipelineHealthReport(
            total_annotations=total_annotations,
            average_confidence=avg_confidence,
            low_confidence_count=low_confidence_count,
            category_distribution=dict(category_distribution),
        )

    def generate_trend_report(
        self,
        current_annotations: List[AnnotationRecord],
        previous_annotations: List[AnnotationRecord],
        confidence_threshold: float = 0.75,
    ) -> TrendReport:
        """Compares two sets of annotations to generate a trend report.

        Args:
            current_annotations: Annotations from the current period.
            previous_annotations: Annotations from the previous period.
            confidence_threshold: The low-confidence threshold.

        Returns:
            A TrendReport detailing changes between the two periods.
        """
        current_report = self.generate_health_report(current_annotations, confidence_threshold)
        previous_report = self.generate_health_report(previous_annotations, confidence_threshold)

        confidence_change = current_report.average_confidence - previous_report.average_confidence
        low_confidence_change = current_report.low_confidence_count - previous_report.low_confidence_count

        all_categories = set(current_report.category_distribution.keys()) | set(previous_report.category_distribution.keys())
        category_change = {
            cat: current_report.category_distribution.get(cat, 0) - previous_report.category_distribution.get(cat, 0)
            for cat in all_categories
        }

        return TrendReport(
            current_period=current_report,
            previous_period=previous_report,
            confidence_change=confidence_change,
            low_confidence_count_change=low_confidence_change,
            category_distribution_change=category_change,
        )