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
        border-radius: 1rem;
        padding: 0.75rem;
        background: #f6f2fa;
    }
    .ask-ai-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.35rem;
    }
    .ask-ai-title {
        color: #1b1b20;
        font-size: 1.25rem;
        font-weight: 700;
    }
    .ask-ai-powered {
        color: #4c4354;
        font-size: 0.9rem;
    }
    .quick-label {
        margin-top: 0.85rem;
        margin-bottom: 0.25rem;
        color: #4c4354;
        font-size: 0.9rem;
        font-weight: 600;
    }
    div.stButton > button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #665FEC;
        border-color: #665FEC;
        border-radius: 0.85rem;
        color: #ffffff;
        font-weight: 700;
    }
    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #5a54d8;
        border-color: #5a54d8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_chatbot_query(
    search_query: str,
    *,
    vector_store: InMemoryVectorStore,
    preprocessing_pipeline: PreprocessingPipeline,
) -> None:
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
            return

        summary, highlights = build_chatbot_response(search_query, relevant_chunks)
        st.markdown("### ✨ Answer")
        st.write(summary)

        if highlights:
            st.markdown("**Key takeaways**")
            for bullet in highlights:
                st.write(f"- {bullet}")

        for chunk in relevant_chunks:
            review_id = chunk.get("review_id", "unknown")
            text = str(chunk.get("text", "")).strip()
            if text:
                st.caption(f"• {review_id}: {text}")

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
        <div style='display:flex; justify-content:space-between; align-items:center; font-size: 1rem;'>
            <div><span style='color: #701EB2; font-size: 2rem; font-weight: 800; line-height: 1;'>Zepto Insights</span><span style='font-weight: 600;'> · Discovery Engine</span></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main "Ask AI" section
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='ask-ai-meta'>
        <div class='ask-ai-title'>✨ Discovery Engine</div>
        <div class='ask-ai-powered'>Powered by Zepto Intelligence</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("Ask a question about category trust, basket behavior, or review evidence. The AI will synthesize findings and provide evidence-backed answers.")

if "search_query_input" not in st.session_state:
    st.session_state.search_query_input = ""

search_col, ask_col = st.columns([6, 1.4])
with search_col:
    st.text_input(
        "",
        key="search_query_input",
        placeholder="Describe what you want to discover... e.g., Analyze beverage trends in Indiranagar",
        label_visibility="collapsed",
    )
with ask_col:
    ask_clicked = st.button("Ask AI", use_container_width=True, type="primary", key="ask_ai_btn")

st.markdown("<div class='quick-label'>Quick insights:</div>", unsafe_allow_html=True)
quick_queries = [
    "Why are dairy sales peaking in Indiranagar?",
    "Show me top 5 growing categories",
    "Forecast weekend stock needs for Zone-B4",
    "Customer retention for premium fruits",
]

quick_cols = st.columns(2)
quick_clicked_query = ""
for index, query in enumerate(quick_queries):
    with quick_cols[index % 2]:
        if st.button(query, key=f"quick_query_{index}", use_container_width=True):
            quick_clicked_query = query

if quick_clicked_query:
    st.session_state.search_query_input = quick_clicked_query
    run_chatbot_query(
        quick_clicked_query,
        vector_store=vector_store,
        preprocessing_pipeline=preprocessing_pipeline,
    )
elif ask_clicked:
    search_query = st.session_state.search_query_input.strip()
    if not search_query:
        st.warning("Please enter a question.")
    else:
        run_chatbot_query(
            search_query,
            vector_store=vector_store,
            preprocessing_pipeline=preprocessing_pipeline,
        )
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# AI Prediction section
st.markdown("### 🔮 AI Prediction")
st.markdown(
    """
    <div style='border-top: 4px solid #701EB2; padding: 1.25rem 1rem 1rem; border-radius: 1rem; background: #ffffff; box-shadow: 0 10px 30px rgba(112, 30, 178, 0.08); margin-bottom: 1rem;'>
        <div style='display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; flex-wrap:wrap;'>
            <div>
                <p style='font-size: 1rem; font-weight: 700; color: #701EB2; margin:0;'>Growth Focus</p>
                <p style='margin:0.5rem 0 0; color:#4c4354; line-height:1.5;'>The AI has identified the strongest evidence-backed themes from reviews. These insights highlight top product and discovery risks or opportunities.</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if insights:
    for insight in insights[:3]:
        st.markdown(
            f"""
            <div style='background-color: #f6f2fa; padding: 1rem; border-radius: 1rem; border-left: 3px solid #701EB2; margin-bottom: 1rem;'>
                <p style='font-weight: 600; margin: 0 0 0.5rem;'>{insight.title}</p>
                <p style='font-size: 0.95rem; color: #4c4354; margin: 0 0 0.85rem;'>{insight.summary}</p>
                <p style='font-size: 0.85rem; margin: 0;'>Confidence: <strong>{insight.confidence:.2f}</strong> | Evidence: <strong>{len(insight.evidence_ids)} reviews</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("No AI prediction insights are available yet.")
