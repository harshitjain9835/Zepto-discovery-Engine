from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    PLAY_STORE = "play_store"
    APP_STORE = "app_store"
    REDDIT = "reddit"
    TRUSTPILOT = "trustpilot"
    PDP_REVIEW = "pdp_review"


class ReviewRecord(BaseModel):
    id: str = Field(..., description="Unique review identifier")
    source: SourceType
    source_url: str
    raw_text: str
    cleaned_text: Optional[str] = None
    language: Optional[str] = None
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnnotationRecord(BaseModel):
    review_id: str
    category: Optional[str] = None
    sentiment: Optional[str] = None
    behavior_signal: Optional[str] = None
    reason: Optional[str] = None
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InsightCard(BaseModel):
    id: str
    title: str
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    source_mix: dict[str, int] = Field(default_factory=dict)
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
