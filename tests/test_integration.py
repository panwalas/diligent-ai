"""
Integration test: run the full MVP pipeline on example PDF.
"""
import json
import os
from diligent_ai.cli import run


def test_full_pipeline():
    """Test the complete MVP pipeline with the example PDF."""
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "example", "sample.pdf")
    config_path = os.path.join(os.path.dirname(__file__), "..", ".sago_config.yaml")
    
    # Run the full pipeline
    report = run(
        pdf_path=pdf_path,
        config_path=config_path,
        founder_email="founder@example.com",
        investor_name="Test Investor"
    )
    
    # Validate output structure
    assert "claims" in report, "Report should contain 'claims'"
    assert "questions" in report, "Report should contain 'questions'"
    assert "email" in report, "Report should contain 'email'"
    
    assert isinstance(report["claims"], list), "Claims should be a list"
    assert isinstance(report["questions"], list), "Questions should be a list"
    assert isinstance(report["email"], str), "Email should be a string"
    
    # Validate claim structure
    if report["claims"]:
        claim = report["claims"][0]
        assert "id" in claim, "Claim should have id"
        assert "claim" in claim or "text" in claim, "Claim should have text"
        assert "status" in claim, "Claim should have verification status"
        assert "confidence" in claim, "Claim should have confidence score"
        assert "evidence" in claim, "Claim should have evidence"
    
    # Validate questions
    assert len(report["questions"]) > 0, "Should generate at least one question"
    
    # Validate email
    assert "founder" in report["email"].lower(), "Email should address the founder"
    assert len(report["email"]) > 50, "Email should be substantive"

    print("\n✓ Full pipeline test passed!")
    print(f"\n📊 Pipeline Summary:")
    print(f"  - Claims extracted: {len(report['claims'])}")
    print(f"  - Questions generated: {len(report['questions'])}")
    print(f"  - Email composed: {len(report['email'])} characters")


if __name__ == "__main__":
    test_full_pipeline()
