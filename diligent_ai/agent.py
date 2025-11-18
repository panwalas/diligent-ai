from typing import List, Dict, Any
import json
from .llm_client import LLMClient


def generate_summary(verified_claims: List[Dict[str, Any]], llm: LLMClient) -> Dict[str, Any]:
    """Generate an executive summary of the due diligence analysis.

    Args:
        verified_claims: List of verified claims with status, confidence, and evidence
        llm: LLM client for generation

    Returns:
        Dictionary containing summary fields: overview, key_findings, risk_assessment, recommendation
    """
    # Calculate statistics
    total_claims = len(verified_claims)
    verified_count = sum(1 for c in verified_claims if c.get("status") == "verified")
    unverified_count = sum(1 for c in verified_claims if c.get("status") == "unverified")
    disputed_count = sum(1 for c in verified_claims if c.get("status") == "disputed")

    avg_confidence = sum(c.get("confidence", 0) for c in verified_claims) / max(total_claims, 1)

    # Group claims by category
    categories = {}
    for claim in verified_claims:
        cat = claim.get("category", "unknown")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(claim)

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
        return {
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
        return {
            "overview": f"Analyzed {total_claims} claims from the pitch deck with an average confidence of {avg_confidence:.2%}.",
            "key_findings": [
                f"{verified_count} claims verified with supporting evidence",
                f"{unverified_count} claims could not be verified",
                f"{disputed_count} claims appear to be disputed or incorrect"
            ],
            "risk_assessment": f"The low verification rate ({verified_count}/{total_claims}) suggests additional due diligence is required.",
            "recommendation": "Proceed with caution and request additional documentation.",
            "statistics": {
                "total_claims": total_claims,
                "verified": verified_count,
                "unverified": unverified_count,
                "disputed": disputed_count,
                "average_confidence": round(avg_confidence, 2)
            }
        }


def generate_questions(verified_claims: List[Dict[str, Any]], llm: LLMClient, user_profile: Dict[str, Any] = None) -> List[str]:
    """Generate intelligent, contextual investor questions based on verified claims.

    Args:
        verified_claims: List of verified claims with status, confidence, and evidence
        llm: LLM client for generation
        user_profile: Optional user preferences

    Returns:
        List of prioritized investor questions
    """
    # Organize claims by status and category
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

USER PREFERENCES: {user_profile}

Return a JSON object with a "questions" array. Each question should be:
1. Specific and actionable
2. Based on actual findings from the analysis
3. Demonstrating critical thinking
4. Not generic boilerplate questions

Return ONLY the JSON object, no additional text.
"""

    resp = llm.generate(prompt)
    try:
        data = json.loads(resp)
        return data.get("questions", [])
    except Exception:
        # Improved fallback questions based on claim analysis
        questions = []

        # Generate specific questions for high-priority claims
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
            else:
                questions.append(f"We couldn't verify '{claim_text}' through public sources. What documentation can you provide to support this claim?")

        # Add category-specific questions
        if medium_priority_claims:
            questions.append("What is the methodology behind your revenue projections and growth metrics?")
            questions.append("Can you provide a detailed customer acquisition breakdown with cohort analysis?")

        # Ensure we have at least some questions
        if not questions:
            questions = [
                "Please provide audited financial statements for the last 12 months.",
                "Can you share customer contracts or LOIs for your claimed partnerships?",
                "What is your detailed go-to-market strategy with specific milestones?",
            ]

        return questions[:8]  # Limit to 8 questions


def compose_email(questions: List[str], founder_email: str, investor_name: str, summary: Dict[str, Any] = None) -> str:
    """Compose a professional email to founders with due diligence questions.

    Args:
        questions: List of investor questions
        founder_email: Email address of the founder
        investor_name: Name of the investor
        summary: Optional summary of the analysis

    Returns:
        Formatted email template
    """
    # Format questions with numbering
    formatted_questions = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

    # Include summary context if available
    context = ""
    if summary and summary.get("statistics"):
        stats = summary["statistics"]
        verified_pct = (stats["verified"] / max(stats["total_claims"], 1)) * 100
        context = f"\nWe have completed our initial analysis of your pitch deck, reviewing {stats['total_claims']} key claims. Our analysis found that {stats['verified']} claims could be verified with public information ({verified_pct:.0f}%), while {stats['unverified']} claims require additional documentation.\n"

    template = f"""Dear Founder,

Thank you for sharing your pitch deck with us. We are impressed by your vision and progress to date.
{context}
To move forward with our due diligence process, we would appreciate your responses to the following questions:

{formatted_questions}

Please provide your responses along with any supporting documentation (financial statements, customer contracts, partnership agreements, etc.) at your earliest convenience.

We understand that some of this information may be confidential, and we are happy to execute an NDA if needed. We aim to move quickly and efficiently through our process, and your timely responses will help us maintain momentum.

Looking forward to your reply.

Best regards,
{investor_name}
"""
    return template
