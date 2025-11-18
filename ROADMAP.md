# Roadmap — Future Features

This document outlines features that are **documented but not yet coded**. All features align with the project's three design principles: Seamless Integration, Hyper-Personalization, and True Agency.

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

### Implementation Plan

**Backend (Python):**
```python
# backend/gmail_bot.py
from google.oauth2 import service_account
from googleapiclient.discovery import build

def watch_gmail_inbox(user_email):
    """Set up Gmail push notifications"""
    service = build('gmail', 'v1', credentials=creds)

    request = {
        'labelIds': ['INBOX'],
        'topicName': 'projects/YOUR_PROJECT/topics/gmail-notifications'
    }
    service.users().watch(userId='me', body=request).execute()

def on_email_received(message_data):
    """Triggered when new email arrives"""
    # 1. Check for PDF attachments with keywords ("deck", "pitch")
    # 2. Download attachment to temp storage
    # 3. POST to /api/analyze
    # 4. Send reply email with summary + questions
```

**Frontend (Optional):**
- Admin dashboard showing Gmail bot status
- Configuration page for email templates
- Real-time webhook logs

**Deployment:**
- Google Cloud Functions or Cloud Run
- Gmail API OAuth setup
- Pub/Sub topic for push notifications

**Estimated Time:** 8-10 hours

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

### Implementation Plan

**Backend (Python):**
```python
# backend/slack_bot.py
from slack_bolt import App
from slack_sdk import WebClient

app = App(token=os.environ["SLACK_BOT_TOKEN"])

@app.event("file_shared")
def handle_file_shared(event, client):
    """Triggered when file uploaded to Slack"""
    file_id = event["file_id"]

    # 1. Download PDF from Slack
    file_info = client.files_info(file=file_id)
    pdf_url = file_info["url_private"]

    # 2. Call /api/analyze
    report = requests.post('http://localhost:5000/api/analyze', ...)

    # 3. Post results with interactive buttons
    client.chat_postMessage(
        channel=event["channel_id"],
        text=f"✅ Verified {verified}/{total} claims",
        blocks=[
            {"type": "section", "text": {...}},
            {"type": "actions", "elements": [
                {"type": "button", "text": "Schedule Call"},
                {"type": "button", "text": "Request Financials"},
                {"type": "button", "text": "Pass"}
            ]}
        ]
    )
```

**Frontend (Optional):**
- Slack app settings dashboard
- Channel selector for bot installation
- Custom response templates

**Deployment:**
- Slack app creation + OAuth
- Events API subscription (file_shared, message, etc.)
- Socket mode or HTTP server for events

**Estimated Time:** 6-8 hours

---

## Phase 4: Vector Embeddings for Similarity

**Goal:** Replace keyword matching with semantic similarity using vector embeddings.

### Current Limitation

```python
# Current (simple keyword overlap):
similarity = len(keywords_A & keywords_B) / len(keywords_A | keywords_B)
```

**Problem:** Misses semantic similarity.
- "500 enterprise customers" vs "450 B2B clients" → Low similarity score (different keywords)
- But semantically very similar!

### Proposed Solution

**Use Sentence Transformers + Vector Database:**

```python
# backend/memory_agent_v2.py
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

model = SentenceTransformer('all-MiniLM-L6-v2')
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index("pitch-decks")

def store_deal_with_embeddings(report):
    """Store deal with vector embeddings"""
    for claim in report['claims']:
        # Generate embedding
        embedding = model.encode(claim['claim'])

        # Store in Pinecone
        index.upsert([(
            claim_id,
            embedding.tolist(),
            {"deal_id": deal_id, "claim": claim['claim'], "status": claim['status']}
        )])

def find_similar_deals_semantic(report):
    """Find similar deals using cosine similarity"""
    query_claims = " ".join([c['claim'] for c in report['claims']])
    query_embedding = model.encode(query_claims)

    # Query Pinecone
    results = index.query(
        vector=query_embedding.tolist(),
        top_k=5,
        include_metadata=True
    )

    return results['matches']
```

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
```python
def analyze_patterns(deals):
    """Identify patterns in deal data"""
    # Pattern 1: Verification rate vs investment success
    high_verification_deals = [d for d in deals if d['verified_rate'] > 0.8]
    success_rate = sum(d['outcome'] == 'invested' for d in high_verification_deals) / len(high_verification_deals)

    # Pattern 2: Common red flags
    red_flags = {}
    for deal in deals:
        for claim in deal['claims']:
            if claim['status'] == 'unverified' and claim['category'] == 'revenue':
                red_flags['unverified_revenue'] = red_flags.get('unverified_revenue', 0) + 1

    return {
        'high_verification_success_rate': success_rate,
        'common_red_flags': red_flags
    }
```

**2. Smart Recommendations:**
- "This deal has 3 unverified revenue claims. 80% of deals with similar patterns failed due diligence."
- "You typically ask about customer references when verification rate is below 70%. Consider adding that question."

**3. Trend Analysis:**
- Show verification rate trends over time
- Identify sectors with highest/lowest claim accuracy
- Track which questions led to successful investments

**Frontend:**
- Insights dashboard with charts
- Pattern visualization (e.g., "Deals by sector and verification rate")
- Custom queries: "Show me all SaaS deals from Q4 2024 with unverified growth claims"

**Estimated Time:** 12-15 hours

---

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

### Implementation Plan

**Backend (Python):**
```python
# backend/proactive_agent.py
from apscheduler.schedulers.background import BackgroundScheduler
import requests

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=9)  # Run daily at 9am
def monitor_portfolio_companies():
    """Check for news on portfolio companies"""
    portfolio = get_portfolio_companies()  # From memory DB

    for company in portfolio:
        # Search for recent news (last 24 hours)
        news = search_news_api(company.name, since='24h')

        if news:
            # Re-verify claims with new evidence
            for claim in company.unverified_claims:
                new_status = reverify_claim(claim, news)

                if new_status != claim.status:
                    # Send alert
                    send_alert(
                        f"🔔 {company.name}: Claim status changed!\n"
                        f"Claim: {claim.text}\n"
                        f"Old status: {claim.status} → New status: {new_status}"
                    )
```

**Features:**
- Daily monitoring of portfolio companies
- Re-verification when new evidence appears
- Alerts via Email or Slack
- Audit trail: Track all status changes

**Estimated Time:** 10-12 hours

---

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

### Example Queries

```cypher
// Find all deals from founders who previously raised from this investor
MATCH (investor:Investor {name: "Jane Smith"})-[:REVIEWED]->(deal1:Deal)-[:FOR_COMPANY]->(company1:Company)<-[:FOUNDED]-(founder:Founder)
MATCH (founder)-[:FOUNDED]->(company2:Company)<-[:FOR]-(deal2:Deal)
WHERE deal2 <> deal1
RETURN deal2, company2

// Find common patterns in successful deals
MATCH (deal:Deal {outcome: "invested"})-[:HAS_CLAIM]->(claim:Claim)
WHERE claim.status = "verified"
RETURN claim.category, COUNT(*) as frequency
ORDER BY frequency DESC
```

**Benefits:**
- Track founder history across multiple companies
- Identify investor-founder relationships
- Find connected deals (co-founders, same sector, etc.)

**Tech Stack:**
- **Graph DB:** Neo4j (managed cloud or self-hosted)
- **Hybrid Approach:** SQLite for structured data, Neo4j for relationships, Pinecone for vectors

**Estimated Time:** 15-20 hours

---

## Implementation Timeline

| Phase | Feature | Estimated Time | Priority |
|-------|---------|----------------|----------|
| **Phase 2** | Gmail Bot | 8-10 hours | High |
| **Phase 3** | Slack Bot | 6-8 hours | High |
| **Phase 4** | Vector Embeddings | 10-12 hours | Medium |
| **Phase 5** | Pattern Recognition | 12-15 hours | Medium |
| **Phase 6** | Proactive Monitoring | 10-12 hours | Low |
| **Phase 7** | Graph Database | 15-20 hours | Low |

**Total:** 61-77 hours for all phases

---

## 🚀 Quick Wins (Pick One to Implement Next)

### Option 1: Slack Bot MVP (6-8 hours)
**Why:** Most visible for demo, shows "True Agency" in action.

**What to build:**
- Simple Slack app listening for file uploads
- Posts verification summary to channel
- Interactive buttons: "Schedule Call" | "Pass" | "Request More Info"

### Option 2: Vector Embeddings (10-12 hours)
**Why:** Significantly improves similarity matching accuracy.

**What to build:**
- Integrate Sentence Transformers for embeddings
- Use Pinecone (free tier) for vector storage
- Replace keyword matching in `memory_agent.py`

### Option 3: Architecture Diagrams (2-3 hours)
**Why:** Visual documentation for Sago reviewers.

**What to create:**
- System architecture diagram (Mermaid or Lucidchart)
- Data flow diagram
- Database schema visualization

---

## 📖 Resources

**Slack Bot:**
- [Slack Bolt for Python](https://slack.dev/bolt-python/tutorial/getting-started)
- [Slack Events API](https://api.slack.com/events-api)

**Gmail Bot:**
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [Gmail Push Notifications](https://developers.google.com/gmail/api/guides/push)

**Vector Embeddings:**
- [Sentence Transformers](https://www.sbert.net/)
- [Pinecone Quickstart](https://docs.pinecone.io/docs/quickstart)

**Graph Database:**
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)

---

**All features documented here align with the core principles of seamless, personalized, and agentic software.**
