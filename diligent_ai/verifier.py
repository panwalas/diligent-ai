import json
from typing import List, Dict, Any
from .llm_client import LLMClient
from .evidence import search_serpapi


def extract_claims_from_text(text: str, llm: LLMClient) -> List[Dict[str, Any]]:
    prompt = f"""
Extract claims from the following pitch deck text. Return a JSON object with a top-level key 'claims' as an array of objects with id and text.

{text}

"""
    resp = llm.generate(prompt)
    try:
        data = json.loads(resp)
        return data.get("claims", [])
    except Exception:
        sentences = [s.strip() for s in text.split(".") if s.strip()][:10]
        return [{"id": f"c{i+1}", "text": s} for i, s in enumerate(sentences)]


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
