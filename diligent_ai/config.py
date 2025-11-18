import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_config(path: str = None) -> Dict[str, Any]:
    """Load configuration from .config.yaml or provided path.

    This file is expected to be gitignored and contain secrets (Gemini API key, etc.).
    Returns empty dict if file doesn't exist or cannot be parsed.
    """
    if path is None:
        path = os.path.join(os.getcwd(), ".config.yaml")
        if not os.path.exists(path):
            path = os.path.expanduser("~/.config.yaml")

    if not os.path.exists(path):
        logger.debug(f"Config file not found: {path}")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse YAML config file {path}: {e}")
        return {}
    except Exception as e:
        logger.warning(f"Failed to load config file {path}: {e}")
        return {}


def get_gemini_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg.get("gemini", {})


def get_search_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg.get("search", {})
