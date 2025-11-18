"""
LangGraph workflow for pitch deck due diligence analysis.

Workflow:
1. Extract PDF text (done before workflow)
2. Parallel: Generate pitch deck summary + Extract claims
3. Sequential: Verify claims with SerpAPI evidence
4. Parallel: Generate questions + Compose email
5. Generate executive summary
"""

from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
import json
from .llm_client import LLMClient
from .evidence import search_serpapi


class AnalysisState(TypedDict):
    """State for the analysis workflow."""
    # Input
    text: str
    config_path: str
    founder_email: str
    investor_name: str
    llm: LLMClient

    # Intermediate state
    pitch_deck_summary: Dict[str, Any]
    claims: List[Dict[str, Any]]
    verified_claims: List[Dict[str, Any]]

    # Output
    questions: List[str]
    email: str
    summary: Dict[str, Any]


def generate_pitch_deck_summary_node(state: AnalysisState) -> AnalysisState:
    """Generate summary of pitch deck content (company, product, problem, solution)."""
    text = state["text"]
    llm = state["llm"]

    prompt = f"""
You are analyzing a startup pitch deck. Extract and summarize the following information from the pitch deck text below.

Return a JSON object with these keys:
- company_name: The name of the company (string)
- product: Brief description of the product/service (1-2 sentences)
- problem: The problem they're solving (1-2 sentences)
- solution: How they solve it (1-2 sentences)
- market: Target market and size if mentioned (1 sentence)
- traction: Key traction metrics if mentioned (revenue, customers, growth) (1 sentence)

If any field is not clearly mentioned in the deck, use "Not specified" for that field.

Pitch deck text:
{text[:3000]}

Return ONLY the JSON object, no additional text.
"""

    try:
        resp = llm.generate(prompt)
        data = json.loads(resp)
        state["pitch_deck_summary"] = {
            "company_name": data.get("company_name", "Not specified"),
            "product": data.get("product", "Not specified"),
            "problem": data.get("problem", "Not specified"),
            "solution": data.get("solution", "Not specified"),
            "market": data.get("market", "Not specified"),
            "traction": data.get("traction", "Not specified")
        }
    except Exception:
        state["pitch_deck_summary"] = {
            "company_name": "Not specified",
            "product": "Product information could not be extracted from the pitch deck.",
            "problem": "Not specified",
            "solution": "Not specified",
            "market": "Not specified",
            "traction": "Not specified"
        }

    return state


def extract_claims_node(state: AnalysisState) -> AnalysisState:
    """Extract verifiable claims from pitch deck using AI agent."""
    text = state["text"]
    llm = state["llm"]

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

        state["claims"] = filtered_claims
    except Exception:
        # Fallback: try to extract from longer sentences only
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        valid_sentences = [s for s in sentences if 20 <= len(s) <= 300 and len(s.split()) >= 4]
        state["claims"] = [{"id": f"c{i+1}", "text": s, "category": "unknown"} for i, s in enumerate(valid_sentences[:5])]

    return state


def verify_claims_node(state: AnalysisState) -> AnalysisState:
    """Verify claims with SerpAPI evidence and LLM verification."""
    claims = state["claims"]
    llm = state["llm"]
    config_path = state.get("config_path")

    verified_claims = []

    for claim in claims:
        # Search for evidence using SerpAPI
        query = claim.get("text", "")[:300]
        evidence_items = search_serpapi(query, cfg_path=config_path, num_results=5)

        # VALIDATION: Skip claims with no real evidence (mock data)
        real_evidence = []
        for ev in evidence_items:
            url = ev.get("url", "")
            snippet = ev.get("snippet", "")
            # Filter out mock/placeholder evidence
            if url and url != "mock-url" and "mock" not in url.lower():
                if snippet and snippet != "mock-search" and len(snippet) > 10:
                    real_evidence.append(ev)

        # Only proceed with verification if we have real evidence
        if real_evidence:
            # Create verification prompt with evidence
            ctx = "\n".join([f"- {e.get('title','')} ({e.get('url')}): {e.get('snippet', '')[:200]}" for e in real_evidence[:3]])
            verification_prompt = f"""
Verify claim: <<{claim.get('text','')}>>

Evidence from web:
{ctx}

Please answer with a JSON object including:
- claim: the claim text
- status: verified|unverified|disputed
- confidence: 0.0-1.0 (decimal number)
- evidence: array of {{"source","url","snippet"}}

Return ONLY the JSON object, no additional text.
"""

            try:
                resp = llm.generate(verification_prompt)
                data = json.loads(resp)
                # Attach real evidence
                if not data.get("evidence"):
                    data["evidence"] = [{
                        "source": e.get("source"),
                        "url": e.get("url"),
                        "snippet": e.get("snippet") or e.get("title"),
                        "quality_score": e.get("quality_score", 0)
                    } for e in real_evidence]
                data["id"] = claim.get("id")
                data["category"] = claim.get("category", "unknown")
                verified_claims.append(data)
            except Exception:
                # Fallback verification
                verified_claims.append({
                    "id": claim.get("id"),
                    "claim": claim.get("text"),
                    "status": "unverified",
                    "confidence": 0.0,
                    "category": claim.get("category", "unknown"),
                    "evidence": [{
                        "source": e.get("source"),
                        "url": e.get("url"),
                        "snippet": e.get("snippet") or e.get("title"),
                        "quality_score": e.get("quality_score", 0)
                    } for e in real_evidence]
                })
        else:
            # No real evidence found
            verified_claims.append({
                "id": claim.get("id"),
                "claim": claim.get("text"),
                "status": "unverified",
                "confidence": 0.0,
                "category": claim.get("category", "unknown"),
                "evidence": []
            })

    state["verified_claims"] = verified_claims
    return state


def generate_questions_node(state: AnalysisState) -> AnalysisState:
    """Generate intelligent investor questions based on verified claims."""
    verified_claims = state["verified_claims"]
    llm = state["llm"]

    # Organize claims by priority
    summary_lines = []
    high_priority_claims = []
    medium_priority_claims = []

    for c in verified_claims:
        status = c.get("status", "unknown")
        conf = c.get("confidence", 0)
        text = c.get("claim") or c.get("text", "")
        category = c.get("category", "unknown")

        summary_lines.append(f"- [{category.upper()}] {status} (confidence: {conf:.2f}): {text}")

        # Prioritize claims that need investigation
        if status == "disputed" or conf < 0.5:
            high_priority_claims.append(c)
        elif status == "unverified" or conf < 0.7:
            medium_priority_claims.append(c)

    prompt = f"""
You are an experienced venture capital investor conducting due diligence on a startup. Based on the analysis below, generate 5-8 intelligent, specific questions to ask the founders.

IMPORTANT GUIDELINES:
- DO NOT ask generic "Can you provide supporting documents for" questions
- Instead, ask specific, probing questions that demonstrate deep analysis
- Focus on claims that are disputed, unverified, or have low confidence scores
- Ask about discrepancies, inconsistencies, or gaps in the evidence
- Request specific metrics, customer names, or verifiable data points
- Question methodology behind claims (e.g., "How did you calculate this metric?")
- Ask about time periods, sample sizes, and data sources
- Prioritize questions by risk and materiality

CLAIMS ANALYSIS:
{chr(10).join(summary_lines)}

Return a JSON object with a "questions" array. Each question should be:
1. Specific and actionable
2. Based on actual findings from the analysis
3. Demonstrating critical thinking
4. Not generic boilerplate questions

Return ONLY the JSON object, no additional text.
"""

    try:
        resp = llm.generate(prompt)
        data = json.loads(resp)
        questions = data.get("questions", [])

        # Filter out bad questions
        valid_questions = []
        for q in questions:
            if len(q) < 500 and not q.startswith("We couldn't verify"):
                valid_questions.append(q)

        state["questions"] = valid_questions if valid_questions else [
            "Could you provide recent financial statements (P&L, balance sheet) for the last 12 months?",
            "Can you share customer references or case studies for your key clients?",
            "What are your detailed revenue projections for the next 12-24 months, including key assumptions?"
        ]
    except Exception:
        # Fallback: generate specific questions for high-priority claims
        questions = []
        for c in high_priority_claims[:3]:
            claim_text = c.get("claim") or c.get("text", "")
            category = c.get("category", "")
            status = c.get("status", "")

            if status == "disputed":
                questions.append(f"We found conflicting information regarding '{claim_text}'. Can you clarify the discrepancy and provide primary source documentation?")
            elif category == "financial":
                questions.append(f"Regarding '{claim_text}' - can you provide audited financial statements or bank records to verify this?")
            elif category == "customer":
                questions.append(f"For the claim '{claim_text}' - can you share specific customer names and contact information for reference checks?")

        state["questions"] = questions if questions else [
            "Please provide audited financial statements for the last 12 months.",
            "Can you share customer contracts or LOIs for your claimed partnerships?",
            "What is your detailed go-to-market strategy with specific milestones?"
        ]

    return state


def compose_email_node(state: AnalysisState) -> AnalysisState:
    """Compose professional email with questions."""
    questions = state["questions"]
    founder_email = state.get("founder_email", "founder@example.com")
    investor_name = state.get("investor_name", "Investor")
    pitch_deck_summary = state.get("pitch_deck_summary", {})
    verified_claims = state.get("verified_claims", [])

    # Format questions
    formatted_questions = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

    # Build context
    company_intro = ""
    context = ""

    # Add pitch deck summary if available
    if pitch_deck_summary:
        pd = pitch_deck_summary
        if pd.get("company_name") and pd["company_name"] != "Not specified":
            company_intro = f"\n\nRegarding {pd['company_name']}: "
            if pd.get("product") and pd["product"] != "Not specified":
                company_intro += f"{pd['product']}"

    # Add statistics
    if verified_claims:
        total_claims = len(verified_claims)
        verified_count = sum(1 for c in verified_claims if c.get("status") == "verified")
        unverified_count = sum(1 for c in verified_claims if c.get("status") == "unverified")

        if total_claims > 0:
            verified_pct = (verified_count / total_claims) * 100
            context = f"\n\nWe've completed our initial review of your pitch deck and analyzed {total_claims} key claims. We were able to verify {verified_count} claims ({verified_pct:.0f}%) through public sources, while {unverified_count} claims would benefit from additional documentation."

    template = f"""Dear Founder,

Thank you for taking the time to share your pitch deck with us.{company_intro}{context}

To help us move forward with our evaluation, we'd appreciate your responses to the following questions:

{formatted_questions}

Please include any supporting documentation such as:
• Financial statements (P&L, balance sheet, cash flow)
• Customer contracts or letters of intent
• Partnership agreements
• Team bios and relevant credentials
• Any other materials you feel would be helpful

We understand some information may be confidential and are happy to execute an NDA. We aim to move efficiently through our process, and your timely response will help maintain momentum.

Best regards,
{investor_name}
"""

    state["email"] = template
    return state


def generate_executive_summary_node(state: AnalysisState) -> AnalysisState:
    """Generate executive summary of the analysis."""
    verified_claims = state["verified_claims"]
    pitch_deck_summary = state.get("pitch_deck_summary", {})
    llm = state["llm"]

    # Calculate statistics
    total_claims = len(verified_claims)
    verified_count = sum(1 for c in verified_claims if c.get("status") == "verified")
    unverified_count = sum(1 for c in verified_claims if c.get("status") == "unverified")
    disputed_count = sum(1 for c in verified_claims if c.get("status") == "disputed")
    avg_confidence = sum(c.get("confidence", 0) for c in verified_claims) / max(total_claims, 1)

    # Prepare claims summary for LLM
    claims_summary = []
    for claim in verified_claims:
        status = claim.get("status", "unknown")
        conf = claim.get("confidence", 0)
        text = claim.get("claim") or claim.get("text", "")
        category = claim.get("category", "unknown")
        claims_summary.append(f"[{category.upper()}] {status} ({conf:.2f}): {text}")

    prompt = f"""
You are a senior investment analyst preparing an executive summary for a due diligence report.

STATISTICS:
- Total claims analyzed: {total_claims}
- Verified: {verified_count}
- Unverified: {unverified_count}
- Disputed: {disputed_count}
- Average confidence: {avg_confidence:.2%}

CLAIMS BREAKDOWN:
{chr(10).join(claims_summary)}

Please generate a comprehensive executive summary with the following sections:

1. OVERVIEW: A brief 2-3 sentence overview of the analysis
2. KEY FINDINGS: List 3-5 most important findings (both positive and concerning)
3. RISK ASSESSMENT: Identify key risks based on unverified or disputed claims
4. RECOMMENDATION: A clear recommendation (Proceed with Due Diligence / Proceed with Caution / Do Not Proceed)

Return a JSON object with keys: overview, key_findings (array), risk_assessment, recommendation
Return ONLY the JSON object, no additional text.
"""

    try:
        resp = llm.generate(prompt)
        data = json.loads(resp)
        summary = {
            "overview": data.get("overview", "Analysis complete."),
            "key_findings": data.get("key_findings", []),
            "risk_assessment": data.get("risk_assessment", "Unable to assess risks."),
            "recommendation": data.get("recommendation", "Further analysis needed."),
            "statistics": {
                "total_claims": total_claims,
                "verified": verified_count,
                "unverified": unverified_count,
                "disputed": disputed_count,
                "average_confidence": round(avg_confidence, 2)
            }
        }
    except Exception:
        # Fallback summary
        summary = {
            "overview": f"Analyzed {total_claims} claims from the pitch deck with an average confidence of {avg_confidence:.2%}.",
            "key_findings": [
                f"{verified_count} claims verified with supporting evidence",
                f"{unverified_count} claims could not be verified",
                f"{disputed_count} claims appear to be disputed or incorrect"
            ],
            "risk_assessment": f"The verification rate of {verified_count}/{total_claims} suggests {'strong' if verified_count/max(total_claims,1) > 0.7 else 'additional'} due diligence is required.",
            "recommendation": "Proceed with caution and request additional documentation.",
            "statistics": {
                "total_claims": total_claims,
                "verified": verified_count,
                "unverified": unverified_count,
                "disputed": disputed_count,
                "average_confidence": round(avg_confidence, 2)
            }
        }

    # Add pitch deck summary
    if pitch_deck_summary:
        summary["pitch_deck"] = pitch_deck_summary

    state["summary"] = summary
    return state


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow for pitch deck analysis."""
    workflow = StateGraph(AnalysisState)

    # Add nodes
    workflow.add_node("generate_pitch_deck_summary", generate_pitch_deck_summary_node)
    workflow.add_node("extract_claims", extract_claims_node)
    workflow.add_node("verify_claims", verify_claims_node)
    workflow.add_node("generate_questions", generate_questions_node)
    workflow.add_node("compose_email", compose_email_node)
    workflow.add_node("generate_executive_summary", generate_executive_summary_node)

    # Set entry point
    workflow.set_entry_point("generate_pitch_deck_summary")

    # Define edges - parallel execution where possible
    workflow.add_edge("generate_pitch_deck_summary", "extract_claims")
    workflow.add_edge("extract_claims", "verify_claims")
    workflow.add_edge("verify_claims", "generate_questions")
    workflow.add_edge("generate_questions", "compose_email")
    workflow.add_edge("compose_email", "generate_executive_summary")
    workflow.add_edge("generate_executive_summary", END)

    return workflow.compile()


def run_workflow(text: str, llm: LLMClient, config_path: str = None,
                 founder_email: str = None, investor_name: str = "Investor") -> Dict[str, Any]:
    """Run the complete pitch deck analysis workflow.

    Args:
        text: Extracted PDF text
        llm: LLM client instance
        config_path: Path to config file
        founder_email: Founder's email
        investor_name: Investor's name

    Returns:
        Dictionary with summary, claims, questions, and email
    """
    # Create workflow
    app = create_workflow()

    # Initialize state
    initial_state = {
        "text": text,
        "config_path": config_path or "",
        "founder_email": founder_email or "founder@example.com",
        "investor_name": investor_name,
        "llm": llm,
        "pitch_deck_summary": {},
        "claims": [],
        "verified_claims": [],
        "questions": [],
        "email": "",
        "summary": {}
    }

    # Run workflow
    final_state = app.invoke(initial_state)

    # Return results
    return {
        "summary": final_state["summary"],
        "claims": final_state["verified_claims"],
        "questions": final_state["questions"],
        "email": final_state["email"]
    }
