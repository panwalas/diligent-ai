# Diligent AI — Pitch Deck Verification

A Python MVP that ingests PDF pitch decks, extracts claims, verifies them using Gemini LLM and SerpAPI, and generates tailored investor questions.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt PyPDF2 requests
```

### 2. Run on example PDF
```bash
PYTHONPATH=. python -m diligent_ai.cli example/sample.pdf --config .config.yaml
```

### 3. Run on your own PDF
```bash
PYTHONPATH=. python -m diligent_ai.cli /path/to/deck.pdf --config .config.yaml \
  --founder-email "founder@company.com" \
  --investor-name "Your Name"
```

## What It Does

1. Extracts text from PDF
2. Identifies claims (revenue, users, team, market size, etc.)
3. Retrieves web evidence via SerpAPI
4. Verifies claims using Gemini LLM with evidence
5. Generates prioritized investor questions
6. Composes email template

## Output

JSON report with:
- **claims**: Extracted statements with verification status and confidence
- **questions**: Prioritized list for investor to ask founder
- **email**: Ready-to-send template

## Configuration

API keys are stored in `.config.yaml` (gitignored):
- `gemini.api_key` — Gemini API
- `search.serpapi_key` — SerpAPI key
- `user` — Investor preferences (optional)

## Architecture

```
diligent_ai/
├── config.py       # Load .config.yaml
├── pdf_utils.py    # Extract text from PDFs
├── llm_client.py   # Gemini LLM client
├── evidence.py     # SerpAPI search
├── verifier.py     # Claim verification pipeline
├── agent.py        # Question generation
└── cli.py          # Command-line interface
```

## Tests

```bash
PYTHONPATH=. python -m pytest tests/ -v
```

## Features

✅ **Seamless Integration** — CLI-ready, designed for Gmail/Drive
✅ **Hyper-Personalization** — User preferences + claim prioritization
✅ **True Agency** — Question generation + email composition


