from __future__ import annotations

import streamlit as st

from src.zepto_discovery.annotation import Phase4AnnotationPipeline
from src.zepto_discovery.dashboard import ensure_review_records, write_dashboard
from src.zepto_discovery.insights import Phase5InsightPipeline
from src.zepto_discovery.monitoring import Phase8MonitoringPipeline


st.set_page_config(page_title="Zepto Discovery Engine", page_icon="⚡", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: #fbf8ff;
        color: #1b1b20;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e4e1e9;
        border-radius: 1rem;
        padding: 1rem;
        box-shadow: 0 12px 30px rgba(81, 0, 150, 0.06);
    }
    .card {
        background: white;
        border: 1px solid #e4e1e9;
        border-radius: 1.5rem;
        padding: 1.25rem;
        box-shadow: 0 20px 50px rgba(81, 0, 150, 0.06);
    }
    .hero {
        background: linear-gradient(135deg, #510096 0%, #7000cc 100%);
        border-radius: 2rem;
        padding: 2rem;
        color: white;
        box-shadow: 0 24px 60px rgba(81, 0, 150, 0.15);
    }
    .topnav {
        background: white;
        border: 1px solid #e4e1e9;
        border-radius: 999px;
        padding: 0.6rem 1rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 10px 24px rgba(81, 0, 150, 0.05);
    }
    .search-shell {
        border: 1px solid #e4e1e9;
        border-radius: 999px;
        padding: 0.5rem 0.8rem;
        background: #f6f2fa;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

reviews = ensure_review_records()
annotation_pipeline = Phase4AnnotationPipeline()
insight_pipeline = Phase5InsightPipeline()
monitoring_pipeline = Phase8MonitoringPipeline()

annotations = annotation_pipeline.annotate_reviews(reviews)
insights = insight_pipeline.build_insight_cards(reviews, annotations)
health_report = monitoring_pipeline.generate_health_report(annotations)

with st.sidebar:
    st.markdown("### Filters")
    selected_sources = st.multiselect(
        "Source",
        options=[review.source.value for review in reviews],
        default=[review.source.value for review in reviews],
    )
    selected_categories = st.multiselect(
        "Category",
        options=sorted({annotation.category for annotation in annotations if annotation.category}),
        default=sorted({annotation.category for annotation in annotations if annotation.category}),
    )
    st.slider("Confidence threshold", 0.0, 1.0, 0.6, 0.05)
    if st.button("Generate dashboard HTML"):
        output_path = write_dashboard("phase7_dashboard.html")
        st.success(f"Dashboard written to {output_path}")

# Top navigation bar
st.markdown(
    """
    <div class='topnav'>
        <div style='display:flex; justify-content:space-between; align-items:center;'>
            <div><strong>Zepto Insights</strong> · Discovery Engine</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main "Ask AI" section
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("🤖 Ask the Discovery Engine")
st.write("Ask a question about category trust, basket behavior, or review evidence. The AI will synthesize findings and provide evidence-backed answers.")
search_query = st.text_input("", placeholder="e.g., What blocks category exploration?", label_visibility="collapsed")
if st.button("Ask AI", use_container_width=True, type="primary"):
    if search_query:
        st.info(f"Searching for: \"{search_query}\"")
        # Placeholder for chatbot response logic
        st.success("AI response would appear here.")
    else:
        st.warning("Please enter a question.")
st.markdown("</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Reviews loaded", len(reviews))
with col2:
    st.metric("Insight cards", len(insights))
with col3:
    st.metric("Avg confidence", f"{health_report.average_confidence:.2f}")

left, right = st.columns([1.2, 1])
with left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Top insight themes")
    for insight in insights:
        st.markdown(f"### {insight.title}")
        st.write(insight.summary)
        progress = max(0.05, min(insight.confidence, 1.0))
        st.progress(progress, text=f"Confidence {insight.confidence:.2f}")
        st.caption(f"Evidence IDs: {', '.join(insight.evidence_ids)}")
        st.divider()
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Recent review annotations")
    for review, annotation in zip(reviews[:6], annotations[:6]):
        st.markdown(f"**{review.id}** — {review.source.value}")
        st.write(annotation.reason)
        st.write(f"Category: {annotation.category} | Sentiment: {annotation.sentiment} | Confidence: {annotation.confidence:.2f}")
        st.caption(f"Evidence: {', '.join(annotation.evidence)}")
        st.divider()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("Monitoring summary")
st.write(f"Low confidence annotations: {health_report.low_confidence_count}")
st.write("Category distribution:")
for category, count in health_report.category_distribution.items():
    st.progress(min(1.0, count / max(1, len(reviews))), text=f"{category}: {count}")
st.markdown("</div>", unsafe_allow_html=True)
