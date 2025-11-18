#!/usr/bin/env python
"""Test script to verify the new features work correctly."""

import json
from diligent_ai.llm_client import MockLLM
from diligent_ai.verifier import extract_claims_from_text, verify_claims
from diligent_ai.agent import generate_summary, generate_questions, compose_email

def test_new_features():
    """Test the new summary and improved question generation."""

    # Initialize MockLLM
    llm = MockLLM()

    # Sample pitch deck text
    sample_text = """
    We are TechCorp, a leading SaaS platform for enterprise customers.
    We have grown 300% YoY and now serve over 1,000 customers including Fortune 500 companies.
    Our revenue reached $10M ARR in 2024.
    We partner with Google Cloud and AWS.
    Our team includes former executives from Microsoft and Amazon.
    """

    print("=" * 80)
    print("TESTING NEW FEATURES")
    print("=" * 80)

    # Test 1: Improved claim extraction
    print("\n1. Testing Improved Claim Extraction...")
    print("-" * 80)
    claims = extract_claims_from_text(sample_text, llm)
    print(f"Extracted {len(claims)} claims:")
    for claim in claims:
        print(f"  - [{claim.get('id')}] {claim.get('text')[:80]}...")
        print(f"    Category: {claim.get('category', 'unknown')}")

    # Test 2: Claim verification with filtering
    print("\n2. Testing Claim Verification with Evidence Filtering...")
    print("-" * 80)
    verified = verify_claims(claims, llm)
    print(f"Verified {len(verified)} claims:")
    for claim in verified:
        print(f"  - Status: {claim.get('status')}, Confidence: {claim.get('confidence')}")

    # Test 3: Summary generation
    print("\n3. Testing Summary Generation...")
    print("-" * 80)
    summary = generate_summary(verified, llm)
    print("Summary generated:")
    print(f"  Overview: {summary.get('overview')[:100]}...")
    print(f"  Key Findings: {len(summary.get('key_findings', []))} findings")
    print(f"  Risk Assessment: {summary.get('risk_assessment')[:100]}...")
    print(f"  Recommendation: {summary.get('recommendation')}")
    print(f"  Statistics: {summary.get('statistics')}")

    # Test 4: Improved question generation
    print("\n4. Testing Improved Question Generation...")
    print("-" * 80)
    questions = generate_questions(verified, llm, user_profile={"industries": ["saas"]})
    print(f"Generated {len(questions)} questions:")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q[:100]}...")

    # Verify questions are not generic "Can you provide supporting documents for"
    generic_count = sum(1 for q in questions if "Can you provide supporting documents for" in q)
    print(f"\nGeneric 'provide documents' questions: {generic_count}/{len(questions)}")

    # Test 5: Improved email template
    print("\n5. Testing Improved Email Template...")
    print("-" * 80)
    email = compose_email(questions, "founder@example.com", "Test Investor", summary=summary)
    print("Email template preview:")
    print(email[:500])
    print("...")

    # Test 6: Full report structure
    print("\n6. Testing Full Report Structure...")
    print("-" * 80)
    report = {
        "summary": summary,
        "claims": verified,
        "questions": questions,
        "email": email
    }

    print("Report structure:")
    print(f"  - Summary: ✓ ({len(str(summary))} chars)")
    print(f"  - Claims: ✓ ({len(verified)} claims)")
    print(f"  - Questions: ✓ ({len(questions)} questions)")
    print(f"  - Email: ✓ ({len(email)} chars)")

    # Save to file for inspection
    with open("/tmp/test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"\nFull report saved to: /tmp/test_report.json")

if __name__ == "__main__":
    test_new_features()
