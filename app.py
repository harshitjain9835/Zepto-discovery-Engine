from __future__ import annotations

import os
import json
import re
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

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)


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
        "The evidence suggests a split experience: strong appreciation for convenience in routine purchases, "
        "but repeated friction around consistency, trust, and issue resolution in higher-risk categories. "
        "This indicates users are willing to continue frequent basket behavior while staying cautious about quality-sensitive or premium items."
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
        highlights = [
            "The evidence suggests the experience is mostly shaped by convenience, trust, and product quality.",
            "Users appear confident with repeat essentials but more hesitant in categories where quality risk is perceived as higher.",
        ]
    elif len(highlights) == 1:
        highlights.append("Review patterns indicate repeat-order confidence remains high, while trust drops when quality uncertainty increases.")

    return summary, highlights


def _load_reviews_txt_context(max_chars: int = 12000) -> str:
    reviews_path = Path(__file__).resolve().parent / "reviews.txt"
    if not reviews_path.exists():
        return ""
    text = reviews_path.read_text(encoding="utf-8").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _build_quick_reviews_brief(reviews_context: str) -> str:
    """Build a compact signal summary from reviews.txt for faster, grounded prompting."""
    if not reviews_context:
        return "No reviews.txt context available."

    text = reviews_context.lower()
    signal_map = {
        "delivery": ["delivery", "late", "delay", "fast", "arrive"],
        "quality": ["quality", "fresh", "packaging", "damaged"],
        "trust": ["trust", "reliable", "hesitant", "confidence"],
        "support": ["support", "customer", "issue", "resolve"],
        "discovery": ["discover", "recommend", "search", "category", "basket"],
        "price/value": ["price", "cost", "value", "expensive", "cheap"],
    }

    scored_signals = []
    for label, keywords in signal_map.items():
        score = sum(text.count(keyword) for keyword in keywords)
        if score > 0:
            scored_signals.append((label, score))

    if not scored_signals:
        return "No clear review themes detected."

    scored_signals.sort(key=lambda item: item[1], reverse=True)
    top = scored_signals[:4]
    return "; ".join(f"{label}:{score}" for label, score in top)


def _strip_bracketed_ids(text: str) -> str:
    """Remove bracketed ID tokens and surrounding phrases from chatbot text."""
    # Remove phrases like "as seen in [review-001]" or "(evidence: [review-002])"
    text = str(text or "")
    cleaned = re.sub(r"\s*\(\s*evidence\s*:\s*\[[^\]]+\]\s*\)", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*(?:as (?:seen|evident) in|in|from|ref\.|see)\s*\[[^\]]+\]", "", cleaned, flags=re.IGNORECASE)
    # Remove any remaining standalone bracketed IDs
    cleaned = re.sub(r"\[(?:\s*[A-Za-z0-9_-]+\s*)\]", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    return cleaned.strip()


def _call_groq_chat(search_query: str, evidence_chunks: list[dict], reviews_context: str) -> tuple[tuple[str, list[str]] | None, str]:
    api_key = (os.getenv("GROQ_API_KEY") or "").strip().strip('"').strip("'")
    if not api_key:
        return None, "Groq disabled: GROQ_API_KEY not set"

    base_url = (os.getenv("GROQ_BASE_URL", "https://api.groq.com") or "https://api.groq.com").strip().rstrip("/")
    model = (os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant") or "llama-3.1-8b-instant").strip()
    url = f"{base_url}/openai/v1/chat/completions"

    evidence_lines = []
    for chunk in evidence_chunks[:6]:
        review_id = chunk.get("review_id", "unknown")
        text = str(chunk.get("text", "")).strip()
        if text:
            evidence_lines.append(f"- [{review_id}] {text}")

    evidence_text = "\n".join(evidence_lines) or "- No retrieved evidence"
    quick_brief = _build_quick_reviews_brief(reviews_context)

    user_prompt = (
        f"User question: {search_query}\n\n"
        "Analyze reviews.txt context quickly (target under 4 seconds of reasoning) and keep wording fresh.\n"
        f"Quick review signals: {quick_brief}\n\n"
        f"Reviews.txt context:\n{reviews_context or 'No reviews.txt content available.'}\n\n"
        f"Retrieved evidence:\n{evidence_text}\n\n"
        "Return STRICT JSON only in this schema: "
        "{\"summary\": \"string\", \"highlights\": [\"string\", \"string\", \"string\"]}. "
        "Keep summary under 150 words and provide exactly 2 concise highlights. "
        "Use a different sentence opener and structure from typical generic summaries. "
        "Avoid repeating stock phrases like 'overall pattern points'. "
        "Ground the answer in at least two concrete evidence cues from retrieved chunks."
    )

    payload = {
        "model": model,
        "temperature": 0.7,
        "top_p": 0.95,
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
        summary = _strip_bracketed_ids(str(parsed.get("summary", "")))
        highlights = [_strip_bracketed_ids(str(x).strip()) for x in parsed.get("highlights", []) if _strip_bracketed_ids(str(x).strip())]
        if not summary:
            return None, "Groq response missing summary"
        if len(highlights) < 2:
            highlights.append("Users show stronger confidence in repeat essentials than in quality-sensitive purchases.")
        return (summary, highlights[:2]), "Groq response used"
    except Exception as exc:
        return None, f"Groq parse failed: {exc}"


def build_ai_prediction_copy(reviews) -> tuple[str, str]:
    if not reviews:
        return (
            "20% of users rely on Zepto for repeat essentials",
            "Review patterns show strongest confidence around routine grocery orders, while trust drops when users consider premium or personal care purchases.",
        )

    total_reviews = len(reviews)
    repeat_count = 0
    concern_count = 0
    discovery_count = 0

    for review in reviews:
        text = getattr(review, "cleaned_text", None) or getattr(review, "raw_text", "")
        normalized = str(text).lower()

        if any(keyword in normalized for keyword in ["repeat", "routine", "staples", "milk and bread", "essentials"]):
            repeat_count += 1
        if any(keyword in normalized for keyword in ["premium", "packaging", "damaged", "personal care", "skincare", "unfamiliar brands", "reduced trust"]):
            concern_count += 1
        if any(keyword in normalized for keyword in ["search", "discovery", "recommendations", "basket suggestions", "discover"]):
            discovery_count += 1

    repeat_pct = round((repeat_count / total_reviews) * 100)
    concern_pct = round((concern_count / total_reviews) * 100)
    discovery_pct = round((discovery_count / total_reviews) * 100)

    title = f"{repeat_pct}% of users rely on Zepto for repeat essentials"
    if discovery_pct > 0:
        summary = (
            f"Data suggests {concern_pct}% of users express caution around premium, packaging, or personal-care purchases, "
            f"while {discovery_pct}% mention discovery or basket suggestions as a useful part of the shopping experience. "
            "The strongest pattern is high comfort with routine grocery orders and lower confidence in riskier categories."
        )
    else:
        summary = (
            f"Data suggests {concern_pct}% of users express caution around premium, packaging, or personal-care purchases, "
            f"while {repeat_pct}% show strong confidence in repeat grocery and staple orders. "
            "The strongest pattern is high comfort with routine purchases and lower confidence in riskier categories."
        )
    return title, summary


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
    div[data-testid="stTextArea"] textarea {
        background-color: #ffffff !important;
        border: 2px solid #D6964A !important;
        border-radius: 1rem !important;
        color: #1b1b20 !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #D6964A !important;
        box-shadow: 0 0 0 1px #D6964A !important;
        outline: none !important;
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
    .ai-loader {
        background: #ffffff;
        border: 1px solid #e4e1e9;
        border-radius: 1rem;
        padding: 0.95rem 1rem;
        margin: 0.6rem auto 1rem;
        max-width: 420px;
        text-align: center;
        box-shadow: 0 10px 28px rgba(81, 0, 150, 0.08);
    }
    .ai-loader-track {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.8rem;
    }
    .ai-loader-icon {
        width: 52px;
        height: 52px;
        border-radius: 0.8rem;
        background: #f7f2ff;
        border: 1px solid #eadfff;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: ai-float 1.45s ease-in-out infinite;
    }
    .ai-loader-icon:nth-child(2) {
        animation-delay: 0.16s;
    }
    .ai-loader-icon:nth-child(3) {
        animation-delay: 0.32s;
    }
    .ai-loader-note {
        color: #5b5069;
        font-size: 0.86rem;
        margin-top: 0.55rem;
    }
    .ai-loader-progress {
        width: 78%;
        height: 6px;
        margin: 0.7rem auto 0;
        border-radius: 999px;
        background: #efeaf8;
        overflow: hidden;
    }
    .ai-loader-progress-fill {
        width: 42%;
        height: 100%;
        border-radius: inherit;
        background: linear-gradient(90deg, #cfc8ff 0%, #8d84ff 60%, #cfc8ff 100%);
        animation: ai-loader-sweep 1.5s ease-in-out infinite;
    }
    @keyframes ai-float {
        0%, 100% {
            transform: translateY(0);
            box-shadow: 0 0 0 rgba(102, 95, 236, 0);
        }
        50% {
            transform: translateY(-5px);
            box-shadow: 0 8px 18px rgba(102, 95, 236, 0.22);
        }
    }
    @keyframes ai-loader-sweep {
        0% {
            transform: translateX(-120%);
            opacity: 0.75;
        }
        50% {
            opacity: 1;
        }
        100% {
            transform: translateX(260%);
            opacity: 0.75;
        }
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
    loader_placeholder = st.empty()
    loader_placeholder.markdown(
        """
        <div class='ai-loader'>
            <div class='ai-loader-track'>
                <div class='ai-loader-icon' aria-label='Milk pack icon'>
                    <svg width='30' height='30' viewBox='0 0 64 64' fill='none' xmlns='http://www.w3.org/2000/svg'>
                        <path d='M22 10h20l6 8v36H16V18l6-8z' fill='#ffffff' stroke='#665FEC' stroke-width='2.2'/>
                        <path d='M22 10l10 8 10-8' stroke='#665FEC' stroke-width='2.2' fill='none'/>
                        <rect x='25' y='28' width='14' height='18' rx='2.5' fill='#E8E5FF'/>
                    </svg>
                </div>
                <div class='ai-loader-icon' aria-label='Fruit icon'>
                    <svg width='30' height='30' viewBox='0 0 64 64' fill='none' xmlns='http://www.w3.org/2000/svg'>
                        <circle cx='33' cy='35' r='16' fill='#FFC74A' stroke='#D6964A' stroke-width='2.2'/>
                        <path d='M31 18c-1-4 2-7 6-8' stroke='#6FA969' stroke-width='2.6' stroke-linecap='round'/>
                        <ellipse cx='39' cy='17' rx='6' ry='3.5' fill='#9AD37D' transform='rotate(20 39 17)'/>
                    </svg>
                </div>
                <div class='ai-loader-icon' aria-label='Shampoo bottle icon'>
                    <svg width='30' height='30' viewBox='0 0 64 64' fill='none' xmlns='http://www.w3.org/2000/svg'>
                        <rect x='27' y='10' width='10' height='7' rx='2' fill='#4AAEEA'/>
                        <path d='M23 19h18v32a6 6 0 0 1-6 6h-6a6 6 0 0 1-6-6V19z' fill='#8ED3FF' stroke='#3B8BC0' stroke-width='2.2'/>
                        <rect x='27' y='31' width='10' height='10' rx='2' fill='#ffffff'/>
                    </svg>
                </div>
            </div>
            <div class='ai-loader-progress'>
                <div class='ai-loader-progress-fill'></div>
            </div>
            <div class='ai-loader-note'>Scanning evidence chunks and composing a concise insight.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
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
            concise = [_strip_bracketed_ids(item) for item in highlights if _strip_bracketed_ids(item)][:2]
            if len(concise) < 2:
                concise.append("Signals suggest convenience drives repeat usage, while trust and quality concerns shape category expansion.")
            st.markdown("**Key takeaways**")
            st.markdown(f"- {concise[0]}")
            st.markdown(f"- {concise[1]}")
    finally:
        loader_placeholder.empty()

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


# Top navigation bar
st.markdown(
    """
    <div class='topnav'>
        <div style='display:flex; justify-content:space-between; align-items:center; font-size: 1rem;'>
            <div><span style='color: #701EB2; font-size: 2rem; font-weight: 800; line-height: 1;'>Zepto Insights</span></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main "Ask AI" section
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
    st.text_area(
        "",
        key="search_query_input",
        placeholder="Describe what you want to discover...",
        label_visibility="collapsed",
        height=68,
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

# AI Prediction section
lead_title, lead_summary = build_ai_prediction_copy(reviews)

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
    pass
else:
    pass
