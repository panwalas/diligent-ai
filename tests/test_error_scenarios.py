"""
Tests for error scenarios and edge cases.
"""
import os
import pytest
import tempfile
from diligent_ai.cli import run
from diligent_ai.pdf_utils import extract_text_from_pdf
from diligent_ai.llm_client import GeminiClient


class TestFileErrorScenarios:
    """Tests for file-related error scenarios."""

    def test_run_with_nonexistent_pdf(self):
        """Test that run() handles nonexistent PDF gracefully."""
        with pytest.raises(SystemExit) as exc_info:
            run("nonexistent.pdf")
        assert exc_info.value.code == 1

    def test_run_with_directory_instead_of_pdf(self):
        """Test that run() handles directory path gracefully."""
        test_dir = os.path.dirname(__file__)
        with pytest.raises(SystemExit) as exc_info:
            run(test_dir)
        assert exc_info.value.code == 1

    def test_extract_from_empty_file(self):
        """Test PDF extraction from empty file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name

        try:
            # Should raise ValueError for invalid PDF
            with pytest.raises(ValueError) as exc_info:
                extract_text_from_pdf(temp_path)
            assert "Failed to extract" in str(exc_info.value) or "PDF" in str(exc_info.value)
        finally:
            os.unlink(temp_path)


class TestAPIErrorScenarios:
    """Tests for API-related error scenarios."""

    def test_client_with_invalid_api_key(self):
        """Test that client handles invalid API key gracefully."""
        # Create a temporary config with invalid key
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
gemini:
  api_key: "short"
  api_endpoint: "https://example.com"
""")
            temp_path = f.name

        try:
            client = GeminiClient(temp_path)
            # Should fall back to mock
            result = client.generate("test prompt")
            assert result is not None
        finally:
            os.unlink(temp_path)

    def test_client_with_missing_config(self):
        """Test that client handles missing config gracefully."""
        client = GeminiClient("nonexistent_config.yaml")
        result = client.generate("test prompt")
        # Should use MockLLM
        assert result is not None


class TestIntegrationErrorScenarios:
    """Tests for end-to-end error scenarios."""

    def test_integration_with_invalid_pdf(self):
        """Test full pipeline with invalid PDF file."""
        # Create a non-PDF file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write("This is not a valid PDF file")
            temp_path = f.name

        try:
            with pytest.raises(SystemExit) as exc_info:
                run(temp_path)
            assert exc_info.value.code == 1
        finally:
            os.unlink(temp_path)

    def test_integration_with_missing_config(self):
        """Test full pipeline with missing config (should still work with mock)."""
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "example", "sample.pdf")
        # Should work with MockLLM fallback
        report = run(pdf_path, config_path="nonexistent.yaml")
        assert "claims" in report
        assert "questions" in report
        assert "email" in report


class TestEdgeCases:
    """Tests for edge cases."""

    def test_run_with_empty_founder_email(self):
        """Test run with empty founder email."""
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "example", "sample.pdf")
        report = run(pdf_path, founder_email="")
        # Email should still be generated (even with empty founder email)
        assert report["email"] is not None
        assert len(report["email"]) > 0
        assert "founder" in report["email"].lower()

    def test_run_with_custom_investor_name(self):
        """Test run with custom investor name."""
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "example", "sample.pdf")
        report = run(pdf_path, investor_name="Acme Ventures")
        # Should include custom name
        assert "Acme Ventures" in report["email"] or "investor" in report["email"].lower()

    def test_run_with_none_values(self):
        """Test run with None values for optional parameters."""
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "example", "sample.pdf")
        report = run(pdf_path, config_path=None, founder_email=None, investor_name="Investor")
        assert report is not None
        assert "claims" in report
