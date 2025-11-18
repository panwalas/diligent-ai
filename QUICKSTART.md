# Quick Start Guide — Diligent AI

## Test Google Drive Integration + Memory Agent (5 Minutes)

### Step 1: Start the Server

```bash
cd /Users/spanwala/Desktop/Playground/diligent-ai
source venv/bin/activate  # If not already activated
cd web
python server.py
```

**Expected output:**
```
INFO:__main__:Starting Diligent AI web server on port 5000
INFO:__main__:Open http://localhost:5000 in your browser
```

### Step 2: Open Web UI

Navigate to: **http://localhost:5000**

You should see:
- Header: "Diligent AI — AI-Powered Pitch Deck Due Diligence"
- Two tabs: "Upload File" and "Google Drive Link"

### Step 3: Test Google Drive Integration

#### Option A: Use Your Own Google Drive File

1. Upload a pitch deck PDF to your Google Drive
2. Right-click → Share → Set to **"Anyone with the link can view"**
3. Copy the link (e.g., `https://drive.google.com/file/d/1ABC...XYZ/view`)
4. In the web UI, click **"Google Drive Link"** tab
5. Paste the link in the input field
6. Click **"Analyze Deck"**

#### Option B: Use a Public Sample PDF

If you don't have a pitch deck handy, you can:
1. Find any public PDF on Google Drive (shared by someone else)
2. Or use the **"Upload File"** tab with a local PDF

**Note:** The Drive API download works for publicly shared files. Private files require OAuth authentication (already implemented in `drive_utils.py` but requires credentials setup).

### Step 4: Watch Processing

You'll see a 4-step animation:
1. **Downloading PDF from Google Drive...** (or "Extracting text from PDF...")
2. **Identifying claims in pitch deck...**
3. **Verifying claims with web evidence...**
4. **Generating investor questions...**

Each step takes a few seconds (total: ~30-60 seconds depending on PDF size and number of claims).

### Step 5: View Results

Once processing completes, you'll see:

**Summary Stats:**
- Claims Analyzed: [number]
- Verified: [number]
- Needs Review: [number]
- Questions: [number]

**Similar Deals Section** (if this is your 2nd+ analysis):
- Shows up to 3 similar past deals
- Each card shows:
  - Company name
  - Similarity percentage
  - Verification rate comparison
  - Analysis date

**Tabs:**
1. **Claims & Evidence** - All extracted claims with verification status, confidence bars, and evidence citations
2. **Investor Questions** - Generated questions to ask the founder
3. **Email Template** - Ready-to-send email with questions

### Step 6: Test Memory Agent

**Analyze another pitch deck** to see the memory agent in action:

1. Click **"New Analysis"** button
2. Upload or paste a new Google Drive link
3. After processing, scroll to **"Similar Deals from History"**
4. You should see your previous analysis listed with a similarity score

**Expected Behavior:**
- If the second deck is in a similar domain (e.g., both fintech), similarity will be higher
- If completely different domains, similarity will be lower
- Each new deck is automatically stored in `data/memory.db`

---

## Testing API Endpoints (Optional)

### Get All Deals

```bash
curl http://localhost:5000/api/deals | jq
```

**Response:**
```json
{
  "deals": [
    {
      "id": 1,
      "company_name": "Example Corp",
      "analyzed_at": "2025-01-17 12:34:56",
      "total_claims": 12,
      "verified_claims": 10,
      "unverified_claims": 2,
      "confidence_avg": 0.85
    }
  ],
  "count": 1,
  "limit": 20,
  "offset": 0
}
```

### Get Specific Deal

```bash
curl http://localhost:5000/api/deals/1 | jq
```

**Response:**
```json
{
  "id": 1,
  "company_name": "Example Corp",
  "claims": [
    {
      "id": 1,
      "claim_text": "We have 500 enterprise customers",
      "status": "verified",
      "confidence": 0.9,
      "evidence_count": 3
    }
  ],
  "questions": [
    {
      "id": 1,
      "question_text": "Can you provide customer references?",
      "priority": 0
    }
  ]
}
```

### Get Overall Stats

```bash
curl http://localhost:5000/api/stats | jq
```

**Response:**
```json
{
  "total_deals": 5,
  "total_claims": 62,
  "avg_verification_rate": 78.5,
  "avg_confidence": 82.3
}
```

---

## Troubleshooting

### Error: "No PDF file provided" when using Drive link

**Cause:** You submitted a Drive link via the file upload tab (or vice versa).

**Solution:** Make sure you're on the correct tab:
- File upload → Use "Upload File" tab
- Google Drive link → Use "Google Drive Link" tab

### Error: "File is not publicly accessible"

**Cause:** The Google Drive file is private.

**Solution:**
1. Open the file in Google Drive
2. Click "Share"
3. Change to **"Anyone with the link can view"**
4. Try again

### Error: "Could not extract file ID from URL"

**Cause:** Invalid Google Drive URL format.

**Solution:** Make sure the URL looks like one of these:
- `https://drive.google.com/file/d/FILE_ID/view`
- `https://drive.google.com/open?id=FILE_ID`
- `FILE_ID` (just the ID itself)

### No similar deals showing up

**Cause:** This is your first analysis, or deals are too dissimilar.

**Solution:**
- Analyze at least 2 pitch decks
- Try analyzing decks in the same industry/sector for higher similarity scores

### Database errors

**Cause:** SQLite database file might be corrupted.

**Solution:**
```bash
# Delete and recreate database
rm -rf data/memory.db
# Restart server (database will be auto-created)
cd web && python server.py
```


---

## Next Steps After Testing

1. **Review Results:** Check the claims, evidence citations, and generated questions
2. **Compare Similar Deals:** See how similarity matching works across different pitch decks
3. **Export Report:** Click "Download Report" to save JSON
4. **Read Documentation:** Check `README.md` for full architecture and roadmap

---

## Need Help?

- **Check logs:** Server output shows detailed processing steps
- **Review code:** All source code is in `diligent_ai/` and `web/`
- **Read implementation:** See `IMPLEMENTATION.md` for technical details

Enjoy testing! 🚀
