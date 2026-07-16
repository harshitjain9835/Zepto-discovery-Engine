from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from .models import AnnotationRecord


@dataclass
class AuditDecision:
    """Represents a human-in-the-loop decision on an annotation."""

    annotation_id: str
    reviewer_id: str
    decision: Literal["accepted", "rejected", "corrected"]
    corrected_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    comments: Optional[str] = None


class Phase6AuditPipeline:
    """Implements the human audit and validation workflow for Phase 6.

    This pipeline provides methods to:
    1. Sample annotations for review based on confidence scores.
    2. Apply audit decisions to a set of annotations.
    3. Track audit history.
    """

    def __init__(self) -> None:
        self.audit_history: List[AuditDecision] = []

    def sample_for_audit(
        self,
        annotations: List[AnnotationRecord],
        sample_size: int,
        confidence_threshold: float = 0.75,
    ) -> List[AnnotationRecord]:
        """Create a sampling strategy for human review.

        Prioritizes low-confidence annotations and then samples randomly
        from the remaining pool to meet the desired sample size.

        Args:
            annotations: The full list of annotations to sample from.
            sample_size: The desired number of annotations to review.
            confidence_threshold: The confidence score below which annotations
                                  are prioritized for review.

        Returns:
            A list of annotations selected for audit.
        """
        low_confidence_pool = [
            ann for ann in annotations if ann.confidence < confidence_threshold
        ]
        high_confidence_pool = [
            ann for ann in annotations if ann.confidence >= confidence_threshold
        ]

        # Prioritize low-confidence items
        sample = low_confidence_pool[:]

        # If more samples are needed, draw randomly from high-confidence items
        remaining_needed = sample_size - len(sample)
        if remaining_needed > 0 and high_confidence_pool:
            sample.extend(random.sample(high_confidence_pool, min(remaining_needed, len(high_confidence_pool))))

        # If the sample is still too small, it means we used all annotations
        # If it's too large, we truncate it.
        return sample[:sample_size]

    def apply_audit_decisions(
        self,
        annotations: List[AnnotationRecord],
        decisions: List[AuditDecision],
    ) -> List[AnnotationRecord]:
        """Apply human audit decisions to a list of annotations.

        This method updates annotations based on reviewer feedback, creating
        a new list of reviewed and corrected annotations.

        Args:
            annotations: The original list of annotations.
            decisions: A list of audit decisions from human reviewers.

        Returns:
            A new list of annotations with corrections applied.
        """
        self.audit_history.extend(decisions)
        annotation_map = {ann.review_id: ann for ann in annotations}

        for decision in decisions:
            if decision.decision == "corrected" and decision.corrected_data:
                original_ann = annotation_map.get(decision.annotation_id)
                if original_ann:
                    # Create a new annotation with corrected data
                    corrected_ann = original_ann.copy()
                    for key, value in decision.corrected_data.items():
                        if hasattr(corrected_ann, key):
                            setattr(corrected_ann, key, value)
                    annotation_map[decision.annotation_id] = corrected_ann

        return list(annotation_map.values())