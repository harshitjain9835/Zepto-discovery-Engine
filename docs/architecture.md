# Architecture: AI Discovery Engine — Zepto

## 1. Overview
This architecture is designed to support the goals described in the problem statement: continuously collect Zepto-related reviews and public discussions, analyze them for trust and category-exploration signals, and produce evidence-backed insight cards that Growth teams can use to design better interventions.

The system is not a support tool or a merchandising engine. Instead, it acts as a discovery layer that turns scattered user language into structured insights that can be queried, audited, and tracked over time.

---

## 2. Goals and Non-Functional Requirements

### Primary goals
- Ingest review data from multiple sources in a recurring and reliable way
- Normalize and enrich raw text so that it is usable for downstream analysis
- Extract behavior, sentiment, category, and reason signals from user feedback
- Group reviews into themes and convert them into actionable insight cards
- Maintain traceability from every insight back to the original source text
- Support monthly re-runs so the team can see whether interventions changed customer conversation patterns

### Non-functional requirements
- Reliability: ingestion should recover gracefully from source failures and rate limits
- Auditability: all findings should be traceable to evidence
- Scalability: the system should handle increasing review volumes over time
- Explainability: insights should be backed by representative quotes and source metadata
- Human oversight: a review loop should catch model mistakes before decisions are made
- Maintainability: the pipeline should be modular so each stage can evolve independently

---

## 3. High-Level Architecture

The solution is organized into seven major layers:

1. Data Ingestion Layer
2. Storage Layer
3. Processing and Normalization Layer
4. Annotation and Intelligence Layer
5. Theme Mining and Insight Generation Layer
6. Human Audit Layer
7. Delivery and Monitoring Layer

A simplified flow is:

Source reviews -> Raw storage -> Cleaning / normalization -> Annotation -> Theme clustering -> Insight repository -> Dashboard / API / export

---

## 4. Component Architecture

### 4.1 Data Ingestion Layer
This layer collects data from all required sources:
- App Store reviews
- Play Store reviews
- Trustpilot reviews
- Reddit discussions
- First-party PDP reviews

#### Responsibilities
- Pull data on a scheduled cadence
- Handle API authentication, paging, and rate limits
- Capture source metadata such as platform, date, product, reviewer type, and link
- Store raw payloads for replay and audit

#### Suggested implementation
- Python-based connectors using requests, BeautifulSoup, or official SDKs where available
- Scheduler such as Airflow, Prefect, or cron-based orchestration
- Queueing layer such as Celery, RabbitMQ, or managed cloud messaging for asynchronous ingestion

---

### 4.2 Storage Layer
The storage layer keeps both raw and processed data.

#### Recommended storage components
- Object storage for raw payloads and downloaded content
- Relational database for structured records and workflow state
- Vector database or vector-enabled relational store for semantic search and clustering support
- Cache layer for repeated lookups and preprocessing tasks

#### Core data entities
- SourceRecord: raw item from a platform
- ReviewRecord: normalized review text plus metadata
- AnnotationRecord: extracted fields such as category, sentiment, behavior signal, reason, and confidence
- ThemeRecord: cluster or theme generated from grouped reviews
- InsightCard: final insight with evidence, frequency, source mix, and recommendation tags
- EvidenceRecord: link between insight and the supporting review texts
- AuditDecision: manual approval or correction of model outputs

---

### 4.3 Processing and Normalization Layer
This layer prepares noisy real-world review data for downstream analysis.

#### Functions
- Text cleaning and Unicode normalization
- Language detection and translation for code-mixed Hindi/English content
- Deduplication using fuzzy matching, near-duplicate detection, or semantic similarity checks
- Standardization of dates, categories, and platform names
- Enrichment with metadata such as category, app version, or review location if available

#### Output
A cleaned review corpus that is consistent enough for annotation and clustering.

#### Suggested approaches
- Rule-based cleaning for punctuation, emojis, and formatting noise
- NLP libraries for language detection and translation
- Similarity-based deduplication using embeddings or hashed features

---

### 4.4 Annotation and Intelligence Layer
This is the core analytical engine of the system.

#### Responsibilities
For each review, the system should extract:
- Category mentioned
- Behavior signal
- Sentiment
- User’s stated reason
- Confidence score

#### Example labels
- Category: personal care, baby, pet, pharmacy, grocery, etc.
- Behavior signal: repeat purchase, category-switch attempt, avoidance, trust concern, support issue
- Sentiment: positive, negative, neutral
- Reason: damaged packaging, cart limit, delivery speed, expiry concern, slow support

#### Model strategy
A hybrid approach is recommended:
- Rule-based extraction for high-precision simple cases
- LLM-based classification for nuanced language and multi-label reasoning
- A confidence threshold to decide when a prediction is reliable enough for automated use

#### Design principle
Each annotation should be explainable and linked to source text. The model should never silently produce a label without a traceable text basis.

---

### 4.5 Theme Mining and Insight Generation Layer
This layer moves from individual review annotations to grouped findings that are useful for decision-making.

#### Functions
- Group reviews into themes using clustering, topic modeling, or embedding similarity
- Label each theme with a clear descriptive title
- Map themes to research questions such as:
  - Why do customers stay in a narrow basket?
  - What blocks category exploration?
  - What triggers a first-time category trial?
- Rank themes by evidence strength, frequency, and source coverage
- Generate insight cards with representative examples and supporting evidence

#### Insight card structure
Each insight card should include:
- Theme title
- Summary explanation
- Frequency count
- Source mix
- Representative quotes
- Confidence score
- Linked evidence records
- Suggested intervention hypothesis

#### Ranking logic
A theme should only become actionable if it appears across multiple sources and passes a minimum frequency threshold. This directly reflects the problem statement’s requirement.

---

### 4.6 Human Audit Layer
Because the system relies on LLM-based or heuristic labeling, the architecture includes a human review loop.

#### Responsibilities
- Sample low-confidence or high-impact annotations for manual review
- Allow reviewers to accept, reject, or correct labels
- Track audit outcomes for model improvement
- Prevent misleading labels from entering the final insight repository without review

#### Suggested workflow
- Random or stratified sampling of annotations
- Review interface for label correctness and evidence quality
- Feedback loop that updates prompts, rules, or model behavior over time

#### Why this matters
This is essential for trust. Growth teams need confidence that the final insights are not based on noisy or incorrect model output.

---

### 4.7 Delivery and Monitoring Layer
This layer exposes the analysis to end users and monitors the health of the pipeline.

#### Interfaces
- Dashboard for Growth and leadership teams
- API endpoint for querying insight cards and evidence
- Export support for reports or slide-ready summaries
- Alerting for ingestion failures, schema issues, and anomaly spikes

#### Monitoring components
- Pipeline run health
- Data freshness metrics
- Annotation confidence distribution
- Source-specific coverage metrics
- Human review backlog

---

## 5. End-to-End Data Flow

### Step 1: Ingestion
Raw reviews and discussions are pulled from each platform into the ingestion layer.

### Step 2: Storage
The raw payloads are stored for traceability and replay.

### Step 3: Normalization
Text is cleaned, translated if needed, deduplicated, and standardized.

### Step 4: Annotation
Each normalized review is labeled with category, behavior signal, sentiment, and reason.

### Step 5: Theme formation
Annotated records are grouped into recurring themes and mapped to research questions.

### Step 6: Insight generation
Themes are ranked and converted into insight cards with evidence and recommendations.

### Step 7: Human audit
Samples are reviewed by humans to ensure quality and reduce false positives.

### Step 8: Delivery
Insight cards are pushed to the repository and surfaced in dashboards or APIs.

---

## 6. Recommended Technical Stack
A practical implementation can use the following stack:

### Backend and orchestration
- Python for ingestion, preprocessing, and analysis
- FastAPI or Flask for serving API endpoints
- Airflow or Prefect for scheduled pipelines

### Data storage
- PostgreSQL for structured metadata and workflow state
- Object storage such as S3 or Azure Blob Storage for raw files
- pgvector or a separate vector database for semantic retrieval and similarity search

### ML and NLP
- Transformers or LLM APIs for annotation and summarization
- Scikit-learn for clustering and classification baselines
- spaCy or similar NLP libraries for preprocessing

### Frontend / reporting
- Streamlit, React, or a lightweight BI dashboard for viewing insight cards

This stack is flexible and suitable for both an MVP and a scaled version of the system.

---

## 7. Security and Governance Considerations
- Store only the minimum required review data needed for analysis
- Respect platform terms of service and fair-use limitations
- Keep source links and evidence intact for audit purposes
- Apply role-based access to the insight repository
- Log model decisions and manual corrections for review history

---

## 8. Deployment Model
A cloud-based deployment is recommended for reliability and iterative scaling.

### Suggested deployment pattern
- Ingestion jobs run on scheduled compute resources
- Processing jobs run in containerized services
- Structured data stored in managed databases
- Raw artifacts stored in object storage
- Dashboards served through a lightweight app or internal web portal

### Operational concerns
- Retry mechanisms for transient source issues
- Monitoring for schema drift or source API changes
- Versioning of prompts, models, and pipelines

---

## 9. Implementation Phases

### Phase 1: MVP
- Ingest from 2–3 sources
- Normalize and deduplicate text
- Produce basic annotations
- Generate a first set of insight cards
- Store evidence and source links

### Phase 2: Reliability and quality
- Add more sources
- Introduce confidence scoring and audit workflow
- Improve theme quality and ranking logic

### Phase 3: Scale and productization
- Add dashboarding and API access
- Create a monthly reporting cadence
- Track intervention impact over time

---

## 10. Summary
The proposed architecture turns Zepto review data into a structured, queryable insight system. It prioritizes traceability, human oversight, and evidence-backed analysis so that Growth can make decisions based on real customer language rather than assumptions.
