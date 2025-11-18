#!/usr/bin/env python
"""Test the LangGraph workflow."""

from diligent_ai.workflow import run_workflow
from diligent_ai.llm_client import MockLLM

# Sample pitch deck text
sample_text = """
TechFlow Inc - AI-Powered Marketing Analytics Platform

Problem: Marketing teams waste 40% of their time on manual data analysis and reporting.

Solution: TechFlow automates data collection from 50+ marketing platforms and provides AI-driven insights in real-time.

Product: Cloud-based dashboard that integrates with Google Ads, Facebook Ads, HubSpot, Salesforce, and more.

Market: Targeting SMB and mid-market companies with marketing teams of 5-50 people. $12B total addressable market.

Traction:
- 500 paying customers across 15 countries
- $2.5M ARR with 25% MoM growth
- Average customer LTV of $15,000
- 92% customer retention rate
- Partnerships with Shopify and WordPress

Team:
- CEO: Former VP of Marketing at Salesforce
- CTO: Ex-Google engineer with ML expertise
- CFO: Previously CFO at a $100M SaaS company

Funding: Raised $5M Series A from Sequoia Capital in Q2 2024.
"""

print("=" * 80)
print("TESTING LANGGRAPH WORKFLOW")
print("=" * 80)

# Create LLM instance (using MockLLM for testing)
llm = MockLLM()

print("\n1. Running workflow...")
print("-" * 80)

# Run the workflow
try:
    report = run_workflow(
        text=sample_text,
        llm=llm,
        config_path=None,
        founder_email="founder@techflow.com",
        investor_name="Test Investor"
    )

    print("✓ Workflow completed successfully!")

    # Check results
    print("\n2. Checking results...")
    print("-" * 80)

    # Check pitch deck summary
    if "summary" in report and "pitch_deck" in report["summary"]:
        pd = report["summary"]["pitch_deck"]
        print(f"✓ Pitch Deck Summary:")
        print(f"  - Company: {pd.get('company_name')}")
        print(f"  - Product: {pd.get('product')[:60]}...")
        print(f"  - Problem: {pd.get('problem')[:60]}...")
    else:
        print("✗ Pitch deck summary missing!")

    # Check claims
    print(f"\n✓ Claims: {len(report.get('claims', []))} claims extracted")
    for claim in report.get("claims", [])[:3]:
        print(f"  - [{claim.get('category')}] {claim.get('claim', claim.get('text', ''))[:60]}...")
        print(f"    Status: {claim.get('status')}, Confidence: {claim.get('confidence')}")
        print(f"    Evidence items: {len(claim.get('evidence', []))}")

    # Check questions
    print(f"\n✓ Questions: {len(report.get('questions', []))} questions generated")
    for i, q in enumerate(report.get("questions", [])[:3], 1):
        print(f"  {i}. {q[:80]}...")

    # Check email
    print(f"\n✓ Email: {len(report.get('email', ''))} characters")
    email_preview = report.get("email", "")[:300]
    print(f"  Preview: {email_preview}...")

    # Check executive summary
    print(f"\n✓ Executive Summary:")
    summary = report.get("summary", {})
    print(f"  - Overview: {summary.get('overview', 'N/A')[:60]}...")
    print(f"  - Risk Assessment: {summary.get('risk_assessment', 'N/A')[:60]}...")
    print(f"  - Recommendation: {summary.get('recommendation', 'N/A')}")

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED!")
    print("=" * 80)

except Exception as e:
    print(f"\n✗ Workflow failed with error: {e}")
    import traceback
    traceback.print_exc()
