# Implementation Plan for the Zepto AI Discovery Engine

## 1. Objective
Build a step-by-step implementation roadmap for an AI-powered discovery system that can collect Zepto-related reviews, analyze them for trust and category-exploration signals, and convert them into actionable insight cards for Growth teams.

---

## 2. Delivery Approach
The project should be delivered in phases, starting with a simple working version and gradually improving quality, coverage, and usability.

The overall sequence is:
1. Set up the foundation
2. Collect and clean data
3. Analyze and label reviews
4. Generate insights
5. Add human review and governance
6. Deliver the output to stakeholders
7. Improve and scale the system

---

## 3. Phase 1 — Project Setup and Foundation

### Goal
Prepare the development environment, define the data structure, and create the initial project skeleton.

### Steps
1. Define the scope of the project clearly
   - Focus on review mining, theme discovery, and insight generation
   - Keep the system limited to discovery and not customer support or merchandising decisions
2. Create the project folder structure
   - Data, scripts, models, storage, documentation, and reporting modules
3. Set up the technical stack
   - Python for processing
   - Database for structured storage
   - Object storage for raw files
   - Scheduling tool for recurring jobs
4. Design core data models
   - Source, review, annotation, theme, insight, evidence, and audit record
5. Create initial configuration files
   - Environment variables, source credentials, and pipeline settings

### Deliverables
- Project skeleton
- Data model definitions
- Configured development environment
- Initial documentation structure

---

## 4. Phase 2 — Data Collection Pipeline

### Goal
Build the ingestion layer so that reviews can be collected from multiple platforms automatically.

### Steps
1. Select the initial sources
   - Play Store: https://play.google.com/store/apps/details?id=com.zeptoconsumerapp&hl=en_IN
   - App Store: https://apps.apple.com/in/app/zepto-groceries-in-minutes/id1575323645?see-all=reviews&platform=iphone
   - Reddit: https://www.reddit.com/search/?q=Reviews+of+Zepto+Service+in+india&cId=f4c2ed62-4010-40b0-9738-cc673e019b94&iId=52089c62-0722-4478-9394-f24d1ed62e95
2. Build connectors for each source
   - Fetch review data using APIs or scraping where allowed
3. Store raw data safely
   - Preserve source metadata, timestamps, URLs, and original text
4. Handle ingestion errors
   - Retry failed requests, log failures, and avoid data loss
5. Schedule periodic runs
   - Run the ingestion process on a regular cadence

### Deliverables
- Working ingestion pipeline
- Raw review repository
- Source metadata tracking
- Scheduled collection jobs

---

## 5. Phase 3 — Data Cleaning, Chunking, and Normalization

### Goal
Turn raw and noisy review data into a clean, structured dataset ready for analysis and semantic retrieval.

### Steps
1. Clean text input
   - Remove unnecessary formatting, emojis, and noise
2. Normalize language
   - Handle Hindi, English, and Hinglish content
3. Deduplicate similar reviews
   - Remove near-duplicate records and repeated entries
4. Standardize metadata
   - Align timestamps, platform names, and category labels
5. Chunk reviews into smaller units
   - Use a rule-based chunking strategy with 70-word chunks and 20-word overlap
   - Prefer sentence-aware splitting when possible, but keep chunk length bounded to preserve context
   - If a review is short, keep it as one chunk; if it is long, split it into overlapping windows
6. Generate embeddings for each chunk
   - Use an embedding model to create vector representations for semantic similarity search
7. Store chunk + embedding pairs
   - Make them available for retrieval, clustering, and downstream analysis

### Deliverables
- Cleaned review corpus
- Deduplicated dataset
- Standardized review records
- Chunked text segments
- Embedding vectors for semantic search and similarity tasks

---

## 6. Phase 4 — Review Annotation and Labeling

### Goal
Extract useful signals from each review so the system can understand what users are saying.

### Steps
1. Annotate each review for:
   - Category mentioned
   - Sentiment
   - Behavior signal
   - User reason
2. Add confidence scores
   - Mark predictions that are low-confidence or uncertain
3. Use a hybrid approach
   - Apply rule-based logic for simple cases and LLM-based labeling for nuanced cases
4. Store annotations with evidence
   - Keep the original review text linked to every label

### Deliverables
- Annotated review dataset
- Confidence-scored labels
- Traceable evidence for each annotation

---

## 7. Phase 5 — Theme Discovery and Insight Generation

### Goal
Group reviews into meaningful themes and transform them into insight cards using both structured labels and semantic retrieval.

### Steps
1. Cluster reviews into themes
   - Group similar complaints, behaviors, or trust concerns
2. Use chunk embeddings for semantic similarity
   - Retrieve related chunks and review segments to improve theme grouping
3. Label each theme clearly
   - Example: “Cart limits block exploration” or “Delivery issues reduce category trust”
4. Map themes to research questions
   - Why do users stay in a narrow basket?
   - What blocks category exploration?
   - What makes first-time trials feel risky?
5. Rank themes by importance
   - Use frequency, cross-source occurrence, evidence strength, and semantic relevance
6. Generate insight cards
   - Include summary, evidence quotes, source mix, confidence, and supporting chunks
7. Expose semantic retrieval and QA endpoints
   - Provide query/embedding endpoints that the chatbot and internal tools can use for RAG-style answers
   - Ensure each retrieved chunk links back to its source review and metadata

Hybrid embedding workflow (small-first + re-rank)
- Objective: balance cost and quality by indexing all chunks with a smaller, cheaper embedding model and using a larger, higher-quality model only for top candidates or high-value chunks.
- Workflow:
   1. After Phase 3 chunking, compute and store `embedding_small` for every chunk (BGE-small or equivalent).
   2. Persist chunk metadata and `embedding_small` in the vector store or vector-enabled DB for fast nearest-neighbor retrieval.
   3. For a query or clustering seed, retrieve top-N candidates using `embedding_small` (N between 50 and 200 depending on scale).
   4. Compute `embedding_large` (BGE-large or equivalent) only for those top-N candidates (or for pre-tagged high-value chunks) and re-rank by large-model similarity.
   5. Use re-ranked results for final theme clustering, insight generation, or RAG context for the chatbot.
- Storage schema (per chunk):
   - `chunk_id`, `review_id`, `text`, `cleaned_text`, `word_count`
   - `embedding_small` (vector or reference), `model_small` (name)
   - `embedding_large` (vector or reference, nullable), `model_large` (name, nullable)
   - `provenance` (source link, timestamp)
   - `created_at`, `updated_at`
- Notes:
   - Normalize embeddings (L2) before storing to make cosine similarity consistent.
   - Store model metadata so results are auditable and reproducible.
   - Reserve `embedding_large` storage for high-value chunks to reduce cost and storage overhead.


### Deliverables
- Theme clusters
- Ranked insight cards
- Evidence-backed summaries
- Semantic retrieval support for related review evidence
- Retrieval/QA endpoints for conversational queries

---

## 8. Phase 6 — Human Audit and Validation

### Goal
Add a review layer so that incorrect or low-confidence outputs can be corrected before becoming part of the final insight set.

### Steps
1. Create a sampling strategy
   - Review a subset of low-confidence or high-impact annotations
2. Add a review workflow
   - Let humans accept, reject, or correct labels
3. Track audit decisions
   - Save who reviewed what and what changed
4. Improve model quality over time
   - Use reviewer feedback to refine prompts and rules

### Deliverables
- Audit workflow
- Reviewed and corrected annotations
- Better-quality final outputs

---

## 9. Phase 7 — Reporting and Stakeholder Delivery

### Goal
Make the insights usable for Growth, merchandising, and leadership teams.

### Steps
1. Build a simple dashboard or reporting view
   - Show insight cards, evidence, and source breakdowns
2. Add search and filtering options
   - Filter by category, behavior type, source, or sentiment
3. Provide API access if needed
   - Allow internal tools to query insight data
4. Create export options
   - Share outputs as reports or presentations
5. Build a conversational frontend (chatbot)
    - Provide an interface for stakeholders to ask the discovery questions and receive evidence-backed answers
    - Surface supporting quotes and links with every answer for auditability

### Deliverables
- Insight dashboard or reporting interface
- Search and filtering functionality
- Stakeholder-facing output
- Conversational chatbot UI and integration with QA endpoints

---

## 10. Phase 8 — Monitoring, Maintenance, and Scaling

### Goal
Make the system reliable, maintainable, and capable of growing over time.

### Steps
1. Add monitoring for pipeline health
   - Track ingestion failures, delays, and output quality
2. Handle schema or source changes
   - Make the pipeline resilient to upstream changes
3. Improve scalability
   - Add support for more sources and larger data volume
4. Optimize chunking and embedding performance
   - Tune chunk size, overlap, and embedding model selection for cost and accuracy
5. Track monthly trend changes
   - Observe whether interventions change the review conversation over time

### Deliverables
- Monitoring and alerting setup
- Scalable pipeline architecture
- Monthly trend analysis support
- Optimized chunking and embedding pipeline

---

## 11. Suggested Timeline

### Week 1–2
- Project setup, data model design, and environment configuration

### Week 3–4
- Ingestion pipeline and raw data storage

### Week 5–6
- Cleaning, normalization, and deduplication

### Week 7–8
- Annotation and initial insight generation

### Week 9–10
- Human audit workflow and reporting UI

### Week 11+
- Optimization, monitoring, and expansion to more sources

---

## 12. Success Criteria
The project will be considered successful when:
- Reviews are collected automatically from multiple sources
- Text is cleaned and structured for analysis
- Reviews are labeled with meaningful categories and signals
- Themes are grouped into evidence-backed insight cards
- Insights are traceable to actual review evidence
- The output is useful for Growth and product decision-making

---

## 13. Final Note
This plan is intentionally phased so the team can deliver a working MVP first and then improve the system gradually. The most important principle is to keep the outputs explainable, auditable, and useful for real product decisions.
