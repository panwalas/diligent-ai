from typing import List, Dict, Any
from .llm_client import LLMClient


def generate_questions(verified_claims: List[Dict[str, Any]], llm: LLMClient, user_profile: Dict[str, Any] = None) -> List[str]:
    summary_lines = []
    for c in verified_claims:
        status = c.get("status")
        conf = c.get("confidence")
        text = c.get("claim") or c.get("text")
        summary_lines.append(f"- [{status} {conf}] {text}")

    prompt = f"""
Generate questions for an investor based on the following verified claims. Return a JSON object {{"questions": [..]}} with prioritized, concise, and actionable questions.

Claims:
{chr(10).join(summary_lines)}

User profile: {user_profile}
"""
    resp = llm.generate(prompt)
    try:
        data = __import__("json").loads(resp)
        return data.get("questions", [])
    except Exception:
        questions = []
        for c in verified_claims[:3]:
            if c.get("status") != "verified":
                questions.append(f"Can you provide supporting documents for: {c.get('claim')}")
        if not questions:
            questions = [
                "Please share revenue breakdown and supporting docs.",
                "Can you provide customer references for your top 3 customers?",
            ]
        return questions


def compose_email(questions: List[str], founder_email: str, investor_name: str) -> str:
    body = "\n".join([f"- {q}" for q in questions])
    template = f"Dear founder,\n\nFollowing our review of your pitch deck, could you please answer the following questions:\n\n{body}\n\nBest regards,\n{investor_name}\n"
    return template
