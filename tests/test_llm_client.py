"""
Unit tests for LLM client.
"""
import pytest
from diligent_ai.llm_client import MockLLM, GeminiClient, LLMClient


class TestMockLLM:
    """Tests for MockLLM fallback."""

    def test_mock_extract_claims(self):
        """Test MockLLM claim extraction."""
        mock = MockLLM()
        prompt = "Extract claims from this text: We have 100k users and $5M revenue"
        result = mock.generate(prompt)

        assert result is not None
        assert isinstance(result, str)
        # Should return JSON with claims
        import json
        data = json.loads(result)
        assert "claims" in data

    def test_mock_verify_claim(self):
        """Test MockLLM claim verification."""
        mock = MockLLM()
        prompt = "Verify claim: <<We have 100k users>>"
        result = mock.generate(prompt)

        assert result is not None
        import json
        data = json.loads(result)
        assert "status" in data
        assert "confidence" in data
        assert data["status"] in ["verified", "unverified"]

    def test_mock_generate_questions(self):
        """Test MockLLM question generation."""
        mock = MockLLM()
        prompt = "Generate questions based on these claims..."
        result = mock.generate(prompt)

        assert result is not None
        import json
        data = json.loads(result)
        assert "questions" in data
        assert isinstance(data["questions"], list)


class TestGeminiClient:
    """Tests for GeminiClient."""

    def test_client_initialization(self):
        """Test that GeminiClient initializes properly."""
        client = GeminiClient()
        assert client is not None
        assert hasattr(client, 'api_key')
        assert hasattr(client, 'model_name')
        assert hasattr(client, 'mock')
        assert hasattr(client, 'client')  # Gemini SDK client

    def test_validate_config_missing_keys(self):
        """Test config validation with missing keys."""
        client = GeminiClient()
        client.api_key = None
        assert client._validate_config() is False

    def test_validate_config_invalid_key(self):
        """Test config validation with invalid (too short) API key."""
        client = GeminiClient()
        client.api_key = "short"
        assert client._validate_config() is False

    def test_validate_config_valid(self):
        """Test config validation with valid configuration."""
        client = GeminiClient()
        client.api_key = "a" * 40  # Valid length key
        assert client._validate_config() is True

    def test_fallback_to_mock_on_invalid_config(self):
        """Test that client falls back to mock with invalid config."""
        # Create client with no config file
        client = GeminiClient(cfg_path="nonexistent_config.yaml")
        result = client.generate("Extract claims from text")

        # Should use MockLLM and return valid JSON
        assert result is not None
        import json
        data = json.loads(result)
        assert isinstance(data, dict)


class TestLLMClient:
    """Tests for LLMClient (alias for GeminiClient)."""

    def test_llm_client_is_gemini_client(self):
        """Test that LLMClient is an alias for GeminiClient."""
        client = LLMClient()
        assert isinstance(client, GeminiClient)
