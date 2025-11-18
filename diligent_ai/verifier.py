import json
from typing import List, Dict, Any
from .llm_client import LLMClient
from .evidence import search_serpapi


def extract_claims_from_text(text: str, llm: LLMClient) -> List[Dict[str, Any]]:
    prompt = f"""
You are an expert analyst reviewing a startup pitch deck. Extract ONLY verifiable, specific CLAIMS from the following pitch deck text.

A CLAIM is a factual statement that can be independently verified. Examples of VALID claims:
- "We have 500 enterprise customers"
- "Revenue grew 300% year-over-year"
- "We are partnered with Google Cloud"
- "Our team includes former executives from Microsoft"
- "We raised $5M in Series A funding"

DO NOT extract:
- Slide titles, headings, or labels (e.g., "Dashboard for Web Traffic")
- Image captions or diagram text
- Navigation elements or formatting text
- Questions or hypotheticals (e.g., "Imagine if you were...")
- Product feature lists without context
- Generic problem/solution statements without specific facts
- Incomplete sentences or fragments
- Marketing taglines or slogans

ONLY extract complete, coherent sentences that make specific, verifiable claims about the company, product, team, market position, or traction.

Return a JSON object with a top-level key 'claims' as an array of objects. Each claim object should have:
- id: unique identifier (e.g., "c1", "c2")
- text: the complete claim (must be a full sentence, 10-200 characters)
- category: one of ["financial", "customer", "market", "product", "team", "partnership"]

Pitch deck text:
{text}

Return ONLY the JSON object with valid claims, no additional text. If no valid claims are found, return {{"claims": []}}
"""
    resp = llm.generate(prompt)
    try:
        data = json.loads(resp)
        claims = data.get("claims", [])

        # Additional filtering: remove very short or very long "claims"
        filtered_claims = []
        for claim in claims:
            claim_text = claim.get("text", "")
            # Must be between 10 and 300 characters
            if 10 <= len(claim_text) <= 300:
                # Must not be just a heading (all caps, or very short)
                if not claim_text.isupper() and len(claim_text.split()) >= 3:
                    # Must not look like a question
                    if not claim_text.strip().endswith("?"):
                        filtered_claims.append(claim)

        return filtered_claims
    except Exception:
        # Fallback: try to extract from longer sentences only
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        valid_sentences = [s for s in sentences if 20 <= len(s) <= 300 and len(s.split()) >= 4]
        return [{"id": f"c{i+1}", "text": s, "category": "unknown"} for i, s in enumerate(valid_sentences[:5])]


def verify_claim(claim: Dict[str, Any], llm: LLMClient, cfg_path: str = None) -> Dict[str, Any]:
    # first fetch web evidence via SerpAPI (if configured)
    query = claim.get("text", "")[:300]
    evidence_items = search_serpapi(query, cfg_path=cfg_path, num_results=2)

    # include the top evidence snippet in the verification prompt
    ctx = "\n".join([f"- {e.get('title','')} ({e.get('url')})" for e in evidence_items])
    prompt = f"""
Verify claim: <<{claim.get('text','')}>>
Context evidence:
{ctx}
Please answer with a JSON object including: claim, status (verified|unverified|disputed), confidence (0-1), and evidence (array of {{source,url,snippet}}).
"""
    resp = llm.generate(prompt)
    try:
        data = json.loads(resp)
        # attach scraped evidence if LLM didn't provide any
        if not data.get("evidence") and evidence_items:
            data["evidence"] = [{"source": e.get("source"), "url": e.get("url"), "snippet": e.get("snippet") or e.get("title")} for e in evidence_items]
        return data
    except Exception:
        return {"claim": claim.get("text"), "status": "unverified", "confidence": 0.0, "evidence": [{"source": e.get("source"), "url": e.get("url"), "snippet": e.get("snippet") or e.get("title")} for e in evidence_items]} 


def verify_claims(claims: List[Dict[str, Any]], llm: LLMClient, cfg_path: str = None) -> List[Dict[str, Any]]:
    results = []
    for c in claims:
        res = verify_claim(c, llm, cfg_path=cfg_path)
        res["id"] = c.get("id")
        results.append(res)
    return results
