# Diligent AI Web Interface

Web-based UI for analyzing pitch decks with AI-powered claim verification.

## Features

- **Drag-and-drop PDF upload** - Easy file upload with visual feedback
- **Real-time progress tracking** - 4-step animated progress indicator
- **Interactive results display** - Tabbed interface showing:
  - Verified/unverified claims with evidence citations
  - Confidence scores with visual bars
  - Investor questions generated from claims
  - Email template ready to send
- **Export capabilities** - Download full report as JSON
- **Copy-to-clipboard** - One-click email copying

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/spanwala/Desktop/Playground/diligent-ai
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `.config.yaml` in the project root with your API keys:

```yaml
gemini:
  api_key: "YOUR_GEMINI_API_KEY"
  model: "gemini-2.5-flash"

search:
  serpapi_key: "YOUR_SERPAPI_KEY"
```

### 3. Start the Server

```bash
cd web
source ../venv/bin/activate
python server.py
```

The server will start on port 5000 (or 8080 if 5000 is in use).

### 4. Open in Browser

Navigate to: `http://localhost:5000` (or whatever port the server shows)

## Usage

1. **Upload PDF**: Click "Browse Files" or drag & drop a pitch deck PDF
2. **Optional**: Enter founder email and investor name for personalized output
3. **Wait**: Watch the progress animation (extraction → claims → verification → questions)
4. **Review Results**:
   - **Claims Tab**: See all extracted claims with verification status and evidence
   - **Questions Tab**: View generated investor questions
   - **Email Tab**: Copy the ready-to-send email template
5. **Export**: Download the full report as JSON or copy the email

## API Endpoints

### `POST /api/analyze`

Analyze a pitch deck PDF.

**Request** (multipart/form-data):
- `pdf`: PDF file (required)
- `founder_email`: Founder's email (optional)
- `investor_name`: Investor's name (optional)

**Response** (JSON):
```json
{
  "claims": [
    {
      "claim": "...",
      "status": "verified|unverified",
      "confidence": 0.85,
      "evidence": [...]
    }
  ],
  "questions": ["...", "..."],
  "email": "..."
}
```

### `GET /api/health`

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "diligent-ai"
}
```

## File Structure

```
web/
├── server.py       # Flask backend
├── index.html      # Main UI structure
├── style.css       # Styling and animations
├── app.js          # Frontend logic
└── README.md       # This file
```

## Development

The server runs in debug mode by default with auto-reload on file changes.

To run on a custom port:
```bash
PORT=8080 python server.py
```

## Notes

- Maximum file size: 16MB
- Only PDF files are accepted
- Temporary files are automatically cleaned up after processing
- Falls back to MockLLM if Gemini API is unavailable
