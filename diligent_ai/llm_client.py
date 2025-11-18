from typing import Any, Dict, Optional
import json
import requests
import logging
import time
from .config import load_config, get_gemini_config

logger = logging.getLogger(__name__)


class MockLLM:
    def generate(self, prompt: str, **kwargs) -> str:
        # Very small deterministic mock used for offline testing
        if "Extract claims" in prompt:
            lines = [l.strip() for l in prompt.split('\n') if l.strip()]
            claims = []
            for i, l in enumerate(lines[:20]):
                if any(k in l.lower() for k in ("we", "%", "revenue", "users", "mau", "growth")) or any(ch.isdigit() for ch in l):
                    claims.append({"id": f"c{i+1}", "text": l[:400]})
            return json.dumps({"claims": claims})
        if "Verify claim" in prompt:
            try:
                start = prompt.index("<<") + 2
                end = prompt.index(">>")
                claim_text = prompt[start:end]
            except Exception:
                claim_text = prompt[:200]
            status = "verified" if any(ch.isdigit() for ch in claim_text) else "unverified"
            result = {
                "claim": claim_text,
                "status": status,
                "confidence": 0.85 if status == "verified" else 0.35,
                "evidence": [
                    {"source": "mock-search", "snippet": "Found corroborating mention", "url": "https://example.com/mock"}
                ],
            }
            return json.dumps(result)
        if "Generate questions" in prompt:
            qs = [
                "Can you share the breakdown and supporting docs for the stated 250k MAU (product analytics)?",
                "How do you calculate revenue and what is your revenue recognition policy?",
                "Who are your top 3 customers and can we contact them for references?",
            ]
            return json.dumps({"questions": qs})
        return json.dumps({"text": prompt[:200]})


class GeminiClient:
    """Gemini API client using google-genai SDK with proper error handling.

    Behavior:
    - Uses Google's official genai SDK
    - Validates API keys before making requests
    - Falls back to MockLLM if API is unavailable or keys are invalid
    """

    def __init__(self, cfg_path: str = None):
        cfg = load_config(cfg_path)
        gem = get_gemini_config(cfg)
        self.api_key = gem.get("api_key")
        self.model_name = gem.get("model", "gemini-2.0-flash-exp")
        self.mock = MockLLM()
        self.client = None

        # Try to initialize Gemini client
        if self._validate_config():
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Gemini client with model: {self.model_name}")
            except ImportError:
                logger.warning("google-genai package not installed. Please install: pip install google-genai")
                logger.warning("Using MockLLM fallback.")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")
                logger.warning("Using MockLLM fallback.")
        else:
            logger.warning("Invalid or missing API configuration. Using MockLLM fallback.")

    def _validate_config(self) -> bool:
        """Validate that API key is properly configured."""
        if not self.api_key:
            return False
        if len(self.api_key) < 20:  # Basic sanity check for API key length
            logger.warning("API key appears to be invalid (too short)")
            return False
        return True

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Gemini API with fallback to MockLLM."""
        # If client not initialized, use mock
        if self.client is None:
            logger.debug("Using MockLLM (client not initialized)")
            return self.mock.generate(prompt, **kwargs)

        try:
            # Use google-genai SDK
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            # Extract text from response
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to get text from first candidate
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    if candidate.content.parts:
                        return candidate.content.parts[0].text

            # If we can't extract text, convert to string
            response_str = str(response)
            logger.warning(f"Unexpected response format. Raw response: {response_str[:200]}")
            return response_str

        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            logger.info("Falling back to MockLLM")
            return self.mock.generate(prompt, **kwargs)


class LLMClient(GeminiClient):
    pass
