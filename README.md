# Diligent AI

**AI-powered due diligence for investors**

Automatically verify pitch deck claims, find similar past deals, and generate personalized investor questions—all from a Google Drive link or file upload.

---

## Core Design Principles

This project is built on three fundamental principles:

### 1. Seamless Integration —> No New Apps Required

**Implemented:**
- **Google Drive**: Paste a shared link, get instant verification
- **Web UI**: Drag-drop files or paste Drive links in your browser
- **CLI**: Command-line interface for automation

### 2. Hyper-Personalization —> Context-Aware Intelligence

**Implemented:**
- **Memory Agent**: Automatically stores all analyzed pitch decks
- **Similar Deals**: Shows top 3 similar past deals with comparison metrics
- **Smart Context**: "You reviewed a similar fintech pitch 2 weeks ago with 80% verification rate"

### 3. True Agency —> Execution, Not Just Data

**Implemented:**
- Automatically verifies all claims using web evidence
- Generates prioritized investor questions
- Composes ready-to-send email templates
- Stores deals in memory without user intervention

**Roadmap:** Gmail bot, Slack bot, Auto-send emails, proactive monitoring, Vector embeddings, pattern recognition (see [ROADMAP.md](ROADMAP.md))

---

## Quick Start (5 Minutes)

### 1. Install & Configure

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys in .config.yaml
cp .config.yaml.example .config.yaml
# Edit .config.yaml with your Gemini and SerpAPI keys
```

### 2. Start Web Server

```bash
cd web
python server.py
```

Open: **http://localhost:5000**

### 3. Test Google Drive Integration

1. Upload a pitch deck PDF to Google Drive
2. Share → "Anyone with the link can view"
3. Click **"Google Drive Link"** tab in the web UI
4. Paste the link → Click **"Analyze Deck"**
5. Watch the 4-step verification process
6. View results: claims, evidence, questions, email

### 4. Test Memory Agent

Analyze 2+ pitch decks (upload or Drive links), then check the **"Similar Deals from History"** section to see personalized comparisons.

---

## How It Works

```
Input (PDF or Drive Link)
    ↓
1. Extract text from PDF
    ↓
2. Identify claims (revenue, users, team, market, traction)
    ↓
3. Search web for evidence (SerpAPI)
    ↓
4. Verify claims with LLM (Gemini) + confidence scores
    ↓
5. Find similar past deals (Memory Agent)
    ↓
6. Generate investor questions
    ↓
7. Compose email template
    ↓
Output: Full verification report + similar deals
```

---

## Features

### Current Implementation

| Feature | Status | Description |
|---------|--------|-------------|
| **PDF Upload** | Working | Drag-drop or browse for files |
| **Google Drive** | Working | Paste Drive link for instant verification |
| **Claim Verification** | Working | Auto-verifies with web evidence + confidence scores |
| **Memory Agent** | Working | Stores all deals in SQLite, finds similar matches |
| **Similar Deals** | Working | Shows top 3 similar past deals with comparison |
| **Question Generation** | Working | Personalized questions based on verification results |
| **Email Template** | Working | Ready-to-send email with questions |
| **Web UI** | Working | Beautiful interface with real-time progress |
| **REST API** | Working | `/api/analyze`, `/api/deals`, `/api/stats` |

### Architecture

```
diligent-ai/
├── diligent_ai/          # Core Python package
│   ├── drive_utils.py    # ✨ Google Drive integration
│   ├── memory_agent.py   # ✨ Memory & similarity matching
│   ├── pdf_utils.py      # PDF text extraction
│   ├── llm_client.py     # Gemini LLM client
│   ├── evidence.py       # SerpAPI search
│   ├── verifier.py       # Claim verification
│   ├── agent.py          # Question generation
│   └── cli.py            # Command-line interface
│
├── web/                  # Flask web server
│   ├── server.py         # ✨ REST API + memory endpoints
│   ├── index.html        # ✨ Tabbed UI + similar deals
│   ├── app.js            # ✨ Drive link + similarity display
│   └── style.css         # UI styling
│
├── data/
│   └── memory.db         # ✨ SQLite database (auto-created)
│
└── tests/                # Unit tests
```

---

## API Endpoints

### `POST /api/analyze`

Analyze a pitch deck (file upload or Google Drive link).

**Request (File Upload):**
```bash
curl -X POST http://localhost:5000/api/analyze \
  -F "pdf=@deck.pdf" \
  -F "founder_email=founder@startup.com" \
  -F "investor_name=Jane Smith"
```

**Request (Google Drive):**
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "drive_link": "https://drive.google.com/file/d/FILE_ID/view",
    "founder_email": "founder@startup.com",
    "investor_name": "Jane Smith"
  }'
```

**Response:**
```json
{
  "claims": [
    {
      "claim": "We have 500 enterprise customers",
      "status": "verified",
      "confidence": 0.9,
      "evidence": [...]
    }
  ],
  "questions": ["Can you provide customer references?", ...],
  "email": "Dear founder,\n\nFollowing our review...",
  "similar_deals": [
    {
      "company_name": "Similar Corp",
      "similarity_score": 0.78,
      "verified_claims": 10,
      "total_claims": 12
    }
  ]
}
```

### `GET /api/deals`

List all analyzed deals (paginated).

```bash
curl http://localhost:5000/api/deals?limit=20&offset=0
```

### `GET /api/deals/<id>`

Get full details for a specific deal.

```bash
curl http://localhost:5000/api/deals/1
```

### `GET /api/stats`

Overall statistics across all deals.

```bash
curl http://localhost:5000/api/stats
```

---

## Example Use Cases

### Use Case 1: Investor Reviews Pitch Deck from Email

**Scenario:** Investor receives pitch deck PDF via email attachment.

**Current Workflow (Manual):**
1. Download PDF
2. Read through 20+ pages
3. Google each claim manually
4. Take notes on what to verify
5. Draft email questions
6. **Total time: 2-3 hours**

**With Diligent AI:**
1. Forward email attachment to Google Drive
2. Share Drive link → Paste in Diligent AI
3. Get verification report in 30 seconds
4. Copy email template → Send
5. **Total time: 2 minutes**

### Use Case 2: Pattern Recognition Across Deals

**Scenario:** Investor has analyzed 50+ pitch decks over 6 months.

**Current Workflow (Manual):**
- No systematic way to compare deals
- Relies on memory to spot similar companies
- Cannot identify patterns in successful investments

**With Diligent AI:**
- Every deal stored automatically
- Similar deals surfaced with each new analysis
- Can query: "Show me all fintech deals with unverified revenue claims"
- Identifies patterns: "Companies with 80%+ verification rate had 3x higher investment success"

---

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** — 5-minute testing guide
- **[ROADMAP.md](ROADMAP.md)** — Future features (Gmail/Slack bots, vector embeddings)
- **[web/README.md](web/README.md)** — Web UI technical details

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Python 3.13 + Flask | REST API server |
| **Frontend** | HTML/CSS/JavaScript | Web UI |
| **LLM** | Google Gemini | Claim extraction & verification |
| **Search** | SerpAPI | Web evidence retrieval |
| **Database** | SQLite | Deal storage & similarity matching |
| **PDF Processing** | pypdf | Text extraction |

---

## Limitations & Future Work

### Current Limitations

1. **Similarity Matching:** Uses keyword overlap (simple). Upgrade to vector embeddings for semantic similarity.
2. **Database:** SQLite (single-file). Migrate to PostgreSQL for production scale.
3. **Public Drive Links Only:** Requires "Anyone with the link" sharing. OAuth support implemented but requires credentials.

### Next Steps (See [ROADMAP.md](ROADMAP.md))

- [ ] Gmail bot (auto-detect pitch deck attachments)
- [ ] Slack bot (listen for uploads in #deal-flow)
- [ ] Vector embeddings (Pinecone/Weaviate for semantic search)
- [ ] Proactive monitoring (re-verify claims when new evidence appears)

---

## License

MIT License - See LICENSE file for details

---

## Contributing

This is an open-source project. For questions or feedback, please open an issue or contact the maintainer.

---

## Why Diligent AI?

**Problem:** Investors waste hours manually fact-checking pitch decks, often missing red flags or asking generic questions.

**Solution:** Diligent AI automates verification, integrates into existing workflows (Gmail, Slack, Drive), learns from every interaction, and takes autonomous action.

**Impact:** Investors make faster, data-driven decisions without changing their workflow.
