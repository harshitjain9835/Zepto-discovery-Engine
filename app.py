from __future__ import annotations

import streamlit as st

from src.zepto_discovery.annotation import Phase4AnnotationPipeline
from src.zepto_discovery.dashboard import ensure_review_records, write_dashboard
from src.zepto_discovery.insights import Phase5InsightPipeline
from src.zepto_discovery.models import ReviewRecord
from src.zepto_discovery.monitoring import Phase8MonitoringPipeline


st.set_page_config(page_title="Zepto Discovery Engine", page_icon="⚡", layout="wide")

st.title("Zepto Discovery Engine")
st.caption("Live review mining, annotation, insight cards, and monitoring dashboard")

reviews = ensure_review_records()
annotation_pipeline = Phase4AnnotationPipeline()
insight_pipeline = Phase5InsightPipeline()
monitoring_pipeline = Phase8MonitoringPipeline()

annotations = annotation_pipeline.annotate_reviews(reviews)
insights = insight_pipeline.build_insight_cards(reviews, annotations)
health_report = monitoring_pipeline.generate_health_report(annotations)

if st.button("Refresh insights"):
    st.experimental_rerun()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Reviews loaded", len(reviews))
with col2:
    st.metric("Insight cards", len(insights))
with col3:
    st.metric("Avg confidence", f"{health_report.average_confidence:.2f}")

st.subheader("Top insight themes")
for insight in insights:
    with st.container():
        st.markdown(f"### {insight.title}")
        st.write(insight.summary)
        st.caption(f"Confidence: {insight.confidence:.2f} | Evidence IDs: {', '.join(insight.evidence_ids)}")
        st.divider()

st.subheader("Recent review annotations")
for review, annotation in zip(reviews[:6], annotations[:6]):
    st.write(f"**{review.id}** — {review.source.value}")
    st.write(annotation.reason)
    st.write(f"Category: {annotation.category} | Sentiment: {annotation.sentiment} | Confidence: {annotation.confidence:.2f}")
    st.caption(f"Evidence: {', '.join(annotation.evidence)}")
    st.divider()

st.subheader("Monitoring summary")
st.write(f"Low confidence annotations: {health_report.low_confidence_count}")
st.write("Category distribution:")
st.json(health_report.category_distribution)

st.subheader("Export dashboard HTML")
if st.button("Generate dashboard HTML"):
    output_path = write_dashboard("phase7_dashboard.html")
    st.success(f"Dashboard written to {output_path}")
