from __future__ import annotations

import streamlit as st

from src.zepto_discovery.annotation import Phase4AnnotationPipeline
from src.zepto_discovery.dashboard import ensure_review_records, write_dashboard
from src.zepto_discovery.insights import Phase5InsightPipeline
from src.zepto_discovery.monitoring import Phase8MonitoringPipeline
from src.zepto_discovery.preprocessing import PreprocessingPipeline
from src.zepto_discovery.vector_store import InMemoryVectorStore, embed_and_upsert
from src.zepto_discovery.embeddings import embed_small


def build_chatbot_response(search_query: str, evidence_chunks: list[dict]) -> tuple[str, list[str]]:
    """Convert retrieved evidence into a natural-language answer and highlight bullets."""
    if not evidence_chunks:
        return "I could not find enough matching review evidence for that question yet. Try a broader or more specific query.", []

    normalized_query = search_query.lower().strip()
    evidence_text = " ".join(str(chunk.get("text", "")).strip() for chunk in evidence_chunks if chunk.get("text"))
    evidence_text = evidence_text.lower()

    theme_patterns = {
        "delivery speed": ["delivery", "fast", "slow", "late", "arrive"],
        "product quality": ["quality", "damaged", "packaging", "fresh", "vegetables", "skincare"],
        "trust and confidence": ["trust", "risk", "hesitant", "reliable", "confidence"],
        "support experience": ["support", "respond", "issue", "customer"],
        "selection and discovery": ["category", "exploration", "snacks", "basket", "recommend", "section"],
    }

    matched_themes = []
    for theme, keywords in theme_patterns.items():
        if any(keyword in evidence_text for keyword in keywords):
            matched_themes.append(theme)

    if not matched_themes:
        matched_themes = ["review sentiment and experience"]

    theme_summary = ", ".join(matched_themes[:3])
    if len(matched_themes) > 3:
        theme_summary += ", and more"

    summary = (
        f"Based on the latest reviews, customers are mainly discussing {theme_summary} in relation to your question about \"{search_query}\". "
        "The overall pattern points to a mix of convenience gains and recurring friction around trust, quality, and support."
    )

    highlights = []
    for chunk in evidence_chunks[:3]:
        text = str(chunk.get("text", "")).strip()
        if not text:
            continue
        if any(keyword in text.lower() for keyword in ["delivery", "fast", "slow", "late"]):
            highlights.append("Delivery speed is a major part of the experience, with some reviewers praising convenience and others flagging delays.")
        elif any(keyword in text.lower() for keyword in ["packaging", "damaged", "quality", "fresh", "vegetables", "skincare"]):
            highlights.append("Product quality and packaging concerns are recurring, especially for personal care and fresh items.")
        elif any(keyword in text.lower() for keyword in ["support", "respond", "issue", "customer"]):
            highlights.append("Support responsiveness is mentioned as a pain point when issues arise.")
        elif any(keyword in text.lower() for keyword in ["category", "exploration", "snacks", "basket", "recommend", "section"]):
            highlights.append("Selection and discovery seem to influence whether shoppers feel comfortable exploring new categories.")
        else:
            highlights.append("The feedback reflects a blend of routine satisfaction and hesitation around trying new items.")
        if len(highlights) >= 3:
            break

    if not highlights:
        highlights = ["The evidence suggests the experience is mostly shaped by convenience, trust, and product quality."]

    return summary, highlights


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
    button[data-testid="stButton"] > div[data-testid="stMarkdownContainer"] > p {
        color: white;
        background-color: #701EB2;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

reviews = ensure_review_records()
annotation_pipeline = Phase4AnnotationPipeline()
insight_pipeline = Phase5InsightPipeline()
monitoring_pipeline = Phase8MonitoringPipeline()
preprocessing_pipeline = PreprocessingPipeline()
vector_store = InMemoryVectorStore()

annotations = annotation_pipeline.annotate_reviews(reviews)
insights = insight_pipeline.build_insight_cards(reviews, annotations)
health_report = monitoring_pipeline.generate_health_report(annotations)

# Preprocess reviews into searchable chunks for the chatbot
review_chunks = preprocessing_pipeline.build_chunks(reviews)

# Embed and load chunks into the vector store for semantic search
with st.spinner("Building semantic search index..."):
    embed_and_upsert(vector_store, review_chunks, embed_fn=embed_small)


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
            <div><strong><span style='color: #701EB2;'>Zepto Insights</span></strong> · Discovery Engine</div>
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
        with st.spinner("Synthesizing answer from review evidence..."):
            query_embedding = embed_small(search_query)
            results = vector_store.query(query_embedding, top_k=10)
            candidate_chunks = [record.metadata for record, _ in results]

            if candidate_chunks:
                reranked_chunks = preprocessing_pipeline.re_rank_with_large(search_query, candidate_chunks, top_k=5)
                relevant_chunks = reranked_chunks[:5]
            else:
                relevant_chunks = []

            st.info(f"Found {len(relevant_chunks)} relevant pieces of evidence for: \"{search_query}\"")

            if not relevant_chunks:
                st.warning("No matching evidence was found. Please try a broader question.")
            else:
                summary, highlights = build_chatbot_response(search_query, relevant_chunks)
                st.markdown("### ✨ Answer")
                st.write(summary)

                if highlights:
                    st.markdown("**Key takeaways**")
                    for bullet in highlights:
                        st.write(f"- {bullet}")

                st.markdown("**Supporting review signals**")
                for chunk in relevant_chunks:
                    review_id = chunk.get("review_id", "unknown")
                    text = str(chunk.get("text", "")).strip()
                    if text:
                        st.caption(f"• {review_id}: {text}")
    else:
        st.warning("Please enter a question.")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("Monitoring summary")
st.write(f"Low confidence annotations: {health_report.low_confidence_count}")
st.write("Category distribution:")
for category, count in health_report.category_distribution.items():
    st.progress(min(1.0, count / max(1, len(reviews))), text=f"{category}: {count}")
st.markdown("</div>", unsafe_allow_html=True)
