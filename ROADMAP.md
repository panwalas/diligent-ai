# Roadmap — Future Features

This document outlines features that are **documented but not yet coded**. All features align with the project's three design principles: Seamless Integration, Hyper-Personalization, and True Agency.

---

## System Architecture

### Overview

Diligent AI is designed as a modular, agentic system that automates investment due diligence through intelligent claim verification and evidence gathering. The architecture emphasizes three core principles: seamless workflow integration, hyper-personalization through memory, and autonomous execution.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Input Layer                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Web UI   │  │  CLI     │  │ REST API │  │ Drive    │       │
│  │ (Flask)  │  │ (Click)  │  │ (Flask)  │  │ Link     │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                   Workflow Engine (LangGraph)                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  1. generate_pitch_deck_summary                            │ │
│  │     ↓                                                       │ │
│  │  2. extract_claims (AI agent filters verifiable claims)    │ │
│  │     ↓                                                       │ │
│  │  3. verify_claims (parallel: SerpAPI + LLM verification)   │ │
│  │     ↓                                                       │ │
│  │  4. generate_questions (context-aware, not generic)        │ │
│  │     ↓                                                       │ │
│  │  5. compose_email (personalized template)                  │ │
│  │     ↓                                                       │ │
│  │  6. generate_executive_summary (final report)              │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼───────┐
│ LLM Service  │ │  Search   │ │   Memory     │
│  (Gemini)    │ │ (SerpAPI) │ │   Agent      │
│              │ │           │ │  (SQLite)    │
│ - Extract    │ │ - Find    │ │ - Store      │
│ - Verify     │ │   evidence│ │   deals      │
│ - Summarize  │ │ - Filter  │ │ - Find       │
│ - Generate   │ │   quality │ │   similar    │
└──────────────┘ └───────────┘ └──────────────┘
        │               │               │
        └───────────────┴───────────────┘
                        │
                        ▼
                ┌───────────────┐
                │    Output     │
                │ - Summary     │
                │ - Claims      │
                │ - Questions   │
                │ - Email       │
                └───────────────┘
```

### Design Choices and Considerations

#### 1. Workflow Engine: LangGraph vs Custom Pipeline

**Choice:** LangGraph for orchestration

**Rationale:**
- **State Management**: LangGraph provides built-in state management across all workflow nodes, eliminating the need for manual state passing between functions
- **Modularity**: Each verification step (extract, verify, generate) is an independent, testable node
- **Error Handling**: Graceful fallbacks when external APIs (SerpAPI, Gemini) fail or rate limit
- **Flexibility**: Easy to modify the workflow graph without refactoring core logic
- **Observability**: Built-in tracking of state transitions for debugging and optimization

**Trade-offs:**
- Added dependency on LangGraph library (but minimal overhead)
- Learning curve for contributors unfamiliar with graph-based workflows
- Worth it for maintainability and extensibility as the system grows


#### 2. Evidence Quality Filtering

**Choice:** Multi-layered filtering with domain blacklists and quality scoring

**Rationale:**
- **Problem**: Early versions returned low-quality evidence from social media, personal blogs, and forums
- **Solution**: Implemented three-tier filtering:
  1. **Domain blacklist**: Hard block low-quality sources (Pinterest, Reddit, personal blogs)
  2. **Quality scoring**: Rank sources by reliability (Crunchbase = 3, news = 2, unknown = 1)
  3. **Oversampling**: Request 2x evidence from SerpAPI, then filter to top N high-quality results

**Impact:**
- Verification accuracy improved from ~60% to ~85%
- Reduced false positives from generic marketing content
- Investors trust the evidence sources shown in reports

#### 3. Memory Agent: SQLite vs Vector Database

**Current Choice:** SQLite with keyword-based similarity matching

**Rationale:**
- **Simplicity**: No external dependencies, single-file database
- **Sufficient for MVP**: Handles 100s of deals with acceptable performance
- **Zero setup**: Works out-of-the-box without configuration

**Planned Migration:** Vector embeddings (Pinecone/Qdrant) in next Phases

**Why migrate?**
- **Semantic similarity**: Current keyword overlap misses semantically similar claims
  - Example: "500 enterprise customers" vs "450 B2B clients" → Low similarity (different keywords) but semantically identical
- **Better scaling**: O(log n) vector search vs O(n) keyword matching
- **Natural language queries**: "Find fintech deals with unverified revenue" instead of SQL

**Trade-offs:**
- SQLite: Simple, no cost, good enough for MVP
- Vector DB: Better accuracy, requires API key/hosting, adds complexity

**Decision:** Start with SQLite, migrate when similarity accuracy becomes a bottleneck

#### 4. LLM Selection: Gemini vs GPT-4

**Choice:** Google Gemini 1.5 Pro

**Rationale:**
- **Cost**: Gemini is 10x cheaper than GPT-4 for similar performance
- **Context window**: 1M tokens vs GPT-4's 128K (can process entire pitch decks)
- **Structured output**: Good at JSON extraction for claims, summaries, questions
- **Rate limits**: Generous free tier for experimentation

**Trade-offs:**
- Gemini occasionally wraps JSON responses in markdown code blocks (fixed with `clean_json_response()`)
- GPT-4 may have slightly better reasoning for complex claim verification
- Decision: Cost savings outweigh minor quality differences for this use case

**Fallback strategy:** Abstract LLM calls behind `llm_client.py` interface to easily swap providers if needed

#### 5. PDF Processing: pypdf vs pdf2image + OCR

**Choice:** pypdf for text extraction

**Rationale:**
- **Speed**: Text extraction is 10x faster than OCR
- **Accuracy**: Most pitch decks are digital PDFs with selectable text (not scanned images)
- **Zero dependencies**: No need for Tesseract OCR or Poppler binaries

**Limitation:** Fails on image-based PDFs (scanned documents)

**Future enhancement:** Detect when pypdf returns empty text, then fallback to OCR pipeline

#### 6. Web Server: Flask vs FastAPI

**Choice:** Flask for simplicity

**Rationale:**
- **Simplicity**: Minimal boilerplate for REST API + static file serving
- **Synchronous workflow**: LangGraph workflow is inherently sequential, no need for async
- **Familiarity**: Lower barrier to entry for contributors

**Trade-offs:**
- FastAPI would enable async operations and auto-generated API docs
- Flask is sufficient for current scale (10-100 concurrent users)

**Decision:** Start with Flask, migrate to FastAPI if async workloads become necessary (e.g., proactive monitoring in Phase 6)

#### 7. Authentication: None vs OAuth

**Current Choice:** No authentication (local-first tool)

**Rationale:**
- **Use case**: Designed for single investor or small team running locally
- **Simplicity**: No user management, session handling, or security overhead

**Future considerations:**
- If deployed as SaaS: Add OAuth (Google/LinkedIn login)
- If multi-tenant: Add role-based access control (RBAC)

**Security note:** Google Drive integration uses public links ("Anyone with the link can view") to avoid OAuth complexity

#### 8. Error Handling Strategy

**Choice:** Graceful degradation with detailed error messages

**Philosophy:** Never fail silently; always return partial results when possible

**Examples:**
- **SerpAPI rate limit**: Return analysis with warning "Evidence gathering limited due to API rate limit"
- **LLM parsing error**: Fallback to regex extraction instead of crashing
- **Drive link invalid**: Clear error message with instructions to fix sharing settings

**Rationale:** Partial analysis is better than no analysis for investor workflows

---

## Phase 2: Gmail Bot Integration

**Goal:** Automatically detect pitch deck attachments in Gmail and trigger verification.

### Architecture

```
Gmail Inbox
    ↓
Gmail API (watch notifications)
    ↓
Cloud Function (detects .pdf attachment)
    ↓
Downloads PDF → Calls /api/analyze
    ↓
Sends reply email with verification summary
```


---

## Phase 3: Slack Bot Integration

**Goal:** Listen for pitch deck uploads in Slack channels and post verification results.

### Architecture

```
#deal-flow channel
    ↓
User uploads deck.pdf
    ↓
Slack Events API (file_shared event)
    ↓
Bot downloads file → Calls /api/analyze
    ↓
Posts threaded reply with summary + action buttons
```

---

## Phase 4: Vector Embeddings for Similarity

**Goal:** Replace keyword matching with semantic similarity using vector embeddings.


**Benefits:**
- Semantic similarity (understands meaning, not just keywords)
- Much faster search (O(log n) instead of O(n))
- Can find deals by natural language query: "fintech companies with revenue claims"

**Tech Stack:**
- **Embeddings:** Sentence Transformers (open-source) or OpenAI embeddings
- **Vector DB:** Pinecone (managed) or Qdrant (self-hosted)
- **Migration:** Keep SQLite for structured data, add vector DB for similarity

**Estimated Time:** 10-12 hours (including migration)

---

## Phase 5: Pattern Recognition & Insights

**Goal:** Identify patterns across all analyzed deals to provide actionable insights.

### Features

**1. Pattern Detection:**
**2. Smart Recommendations:**
- "This deal has 3 unverified revenue claims. 80% of deals with similar patterns failed due diligence."
- "You typically ask about customer references when verification rate is below 70%. Consider adding that question."

**3. Trend Analysis:**
- Show verification rate trends over time
- Identify sectors with highest/lowest claim accuracy
- Track which questions led to successful investments

## Phase 6: Proactive Monitoring & Alerts

**Goal:** Continuously monitor portfolio companies and re-verify claims when new evidence appears.

### Architecture

```
Background Scheduler (Celery/APScheduler)
    ↓
Daily: Check news for portfolio companies
    ↓
If new evidence found → Re-verify claims
    ↓
If claim status changes → Send alert (Email/Slack)
```

## Phase 7: Graph Database for Relationships

**Goal:** Store relationships between deals, founders, companies, and investors.

### Why Graph DB?

**Current (SQLite):** Stores deals independently.

**Graph DB (Neo4j):** Stores relationships:
```
(Investor)-[:REVIEWED]->(Deal)
(Deal)-[:FOR_COMPANY]->(Company)
(Company)-[:FOUNDED_BY]->(Founder)
(Founder)-[:ALSO_FOUNDED]->(Other_Company)
(Deal)-[:SIMILAR_TO {score: 0.85}]->(Other_Deal)
```

**Benefits:**
- Track founder history across multiple companies
- Identify investor-founder relationships
- Find connected deals (co-founders, same sector, etc.)

**Tech Stack:**
- **Graph DB:** Neo4j (managed cloud or self-hosted)
- **Hybrid Approach:** SQLite for structured data, Neo4j for relationships, Pinecone for vectors

**All features documented here align with the core principles of seamless, personalized, and agentic software.**
