from __future__ import annotations

import os
import json
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

from src.zepto_discovery.annotation import Phase4AnnotationPipeline
from src.zepto_discovery.dashboard import ensure_review_records, write_dashboard
from src.zepto_discovery.insights import Phase5InsightPipeline
from src.zepto_discovery.monitoring import Phase8MonitoringPipeline
from src.zepto_discovery.preprocessing import PreprocessingPipeline
from src.zepto_discovery.vector_store import InMemoryVectorStore, embed_and_upsert
from src.zepto_discovery.embeddings import embed_small

load_dotenv()


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


def _load_reviews_txt_context(max_chars: int = 12000) -> str:
    reviews_path = Path(__file__).resolve().parent / "reviews.txt"
    if not reviews_path.exists():
        return ""
    text = reviews_path.read_text(encoding="utf-8").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _call_groq_chat(search_query: str, evidence_chunks: list[dict], reviews_context: str) -> tuple[tuple[str, list[str]] | None, str]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None, "Groq disabled: GROQ_API_KEY not set"

    base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com").rstrip("/")
    model = os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant")
    url = f"{base_url}/openai/v1/chat/completions"

    evidence_lines = []
    for chunk in evidence_chunks[:6]:
        review_id = chunk.get("review_id", "unknown")
        text = str(chunk.get("text", "")).strip()
        if text:
            evidence_lines.append(f"- [{review_id}] {text}")

    evidence_text = "\n".join(evidence_lines) or "- No retrieved evidence"

    user_prompt = (
        f"User question: {search_query}\n\n"
        f"Reviews.txt context:\n{reviews_context or 'No reviews.txt content available.'}\n\n"
        f"Retrieved evidence:\n{evidence_text}\n\n"
        "Return STRICT JSON only in this schema: "
        "{\"summary\": \"string\", \"highlights\": [\"string\", \"string\", \"string\"]}. "
        "Keep summary under 90 words and 2-3 concise highlights."
    )

    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an analyst for Zepto customer review insights. "
                    "Ground your answer in provided review context and evidence."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except Exception as exc:
        return None, f"Groq request failed: {exc}"

    try:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        parsed = json.loads(content[start : end + 1])
        summary = str(parsed.get("summary", "")).strip()
        highlights = [str(x).strip() for x in parsed.get("highlights", []) if str(x).strip()]
        if not summary:
            return None, "Groq response missing summary"
        return (summary, highlights[:3]), "Groq response used"
    except Exception as exc:
        return None, f"Groq parse failed: {exc}"


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
    .prediction-hero {
        background: linear-gradient(135deg, #510096 0%, #7000cc 100%);
        border-radius: 1.6rem;
        padding: 1.6rem;
        color: #ffffff;
        box-shadow: 0 24px 60px rgba(81, 0, 150, 0.18);
        margin-bottom: 1rem;
    }
    .prediction-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: #fcd400;
        color: #6e5c00;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .prediction-actions {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }
    .prediction-primary-btn {
        background: #fcd400;
        color: #6e5c00;
        font-weight: 700;
        border-radius: 0.8rem;
        padding: 0.65rem 1rem;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
    }
    .prediction-secondary-btn {
        background: rgba(255, 255, 255, 0.16);
        color: #ffffff;
        font-weight: 700;
        border-radius: 0.8rem;
        padding: 0.65rem 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .prediction-insight-card {
        background: #ffffff;
        border: 1px solid #e4e1e9;
        border-radius: 1rem;
        padding: 1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 10px 30px rgba(81, 0, 150, 0.08);
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
    reviews_context: str,
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

        if not relevant_chunks:
            st.warning("No matching evidence was found. Please try a broader question.")
            return

        groq_response, groq_status = _call_groq_chat(search_query, relevant_chunks, reviews_context)
        if groq_response is not None:
            summary, highlights = groq_response
            st.caption(groq_status)
        else:
            st.caption(f"{groq_status}. Using local fallback response.")
            summary, highlights = build_chatbot_response(search_query, relevant_chunks)

        # Summarized response UI without raw review references.
        st.markdown("### ✨ Summarized Answer")
        st.markdown(
            f"""
            <div style='background:#ffffff; border:1px solid #e4e1e9; border-left:4px solid #665FEC; border-radius:0.9rem; padding:0.9rem 1rem; margin-bottom:0.65rem;'>
                <p style='margin:0; color:#2d2340; line-height:1.6;'>{summary}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if highlights:
            concise = highlights[:2]
            st.markdown("**Key takeaway**")
            st.write(concise[0])

reviews = ensure_review_records()
reviews_context = _load_reviews_txt_context()
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

if ask_clicked:
    search_query = st.session_state.search_query_input.strip()
    if not search_query:
        st.warning("Please enter a question.")
    else:
        run_chatbot_query(
            search_query,
            vector_store=vector_store,
            preprocessing_pipeline=preprocessing_pipeline,
            reviews_context=reviews_context,
        )
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# AI Prediction section
lead_insight = insights[0] if insights else None
lead_title = lead_insight.title if lead_insight else "AI Prediction: 14% Higher Conversions in Cold Brew Category"
lead_summary = lead_insight.summary if lead_insight else "Discovery Engine recommends expanding SKU variety for premium coffee in Zone-B4 based on review signals and category affinity patterns."

st.markdown("### AI Prediction")
st.markdown(
    f"""
    <div class='prediction-hero'>
        <span class='prediction-chip'>◉ Growth Focus</span>
        <h2 style='margin:0.7rem 0 0; font-size:2rem; line-height:1.15; font-weight:800;'>{lead_title}</h2>
        <p style='margin:0.8rem 0 0; color:#e8dcff; font-size:1.08rem; line-height:1.6;'>{lead_summary}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if insights:
    for insight in insights[:3]:
        st.markdown(
            f"""
            <div class='prediction-insight-card'>
                <p style='font-weight: 700; margin: 0 0 0.45rem; color:#510096;'>{insight.title}</p>
                <p style='font-size: 0.96rem; color: #4c4354; margin: 0 0 0.75rem;'>{insight.summary}</p>
                <p style='font-size: 0.84rem; margin: 0; color:#5d5370;'>Confidence: <strong>{insight.confidence:.2f}</strong> | Evidence: <strong>{len(insight.evidence_ids)} reviews</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("No AI prediction insights are available yet.")
