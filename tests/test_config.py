"""
Unit tests for configuration loading.
"""
import os
import pytest
import tempfile
from diligent_ai.config import load_config, get_gemini_config, get_search_config


class TestConfigLoading:
    """Tests for configuration file loading."""

    def test_load_valid_config(self):
        """Test loading a valid config file."""
        config_path = os.path.join(os.path.dirname(__file__), "..", ".config.yaml")
        if os.path.exists(config_path):
            cfg = load_config(config_path)
            assert cfg is not None
            assert isinstance(cfg, dict)

    def test_load_nonexistent_config(self):
        """Test loading a nonexistent config file returns empty dict."""
        cfg = load_config("nonexistent_file.yaml")
        assert cfg == {}

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML returns empty dict."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: :[[[")
            temp_path = f.name

        try:
            cfg = load_config(temp_path)
            assert cfg == {}
        finally:
            os.unlink(temp_path)

    def test_get_gemini_config(self):
        """Test extracting Gemini config from main config."""
        cfg = {
            "gemini": {
                "api_key": "test_key",
                "api_endpoint": "https://example.com"
            }
        }
        gemini_cfg = get_gemini_config(cfg)
        assert gemini_cfg["api_key"] == "test_key"
        assert gemini_cfg["api_endpoint"] == "https://example.com"

    def test_get_gemini_config_missing(self):
        """Test getting Gemini config when it's not in main config."""
        cfg = {}
        gemini_cfg = get_gemini_config(cfg)
        assert gemini_cfg == {}

    def test_get_search_config(self):
        """Test extracting search config from main config."""
        cfg = {
            "search": {
                "serpapi_key": "test_search_key"
            }
        }
        search_cfg = get_search_config(cfg)
        assert search_cfg["serpapi_key"] == "test_search_key"

    def test_get_search_config_missing(self):
        """Test getting search config when it's not in main config."""
        cfg = {}
        search_cfg = get_search_config(cfg)
        assert search_cfg == {}
