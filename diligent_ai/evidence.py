import requests
from typing import List, Dict, Any
from .config import load_config, get_search_config


def search_serpapi(query: str, cfg_path: str = None, num_results: int = 3) -> List[Dict[str, Any]]:
    """Use SerpAPI to retrieve web evidence for a query.

    The SerpAPI key is read from config.search.serpapi_key or from the environment.
    Returns a list of evidence items with keys: title, url, snippet, source.
    """
    cfg = load_config(cfg_path) if cfg_path else {}
    search_cfg = get_search_config(cfg)
    key = search_cfg.get("serpapi_key") or search_cfg.get("api_key")
    if not key:
        return []

    params = {"q": query, "api_key": key, "num": num_results}
    try:
        r = requests.get("https://serpapi.com/search", params=params, timeout=10)
        r.raise_for_status()
        j = r.json()
        results = []
        # SerpAPI returns organic_results in many cases
        for item in j.get("organic_results", [])[:num_results]:
            results.append({
                "title": item.get("title"),
                "url": item.get("link") or item.get("url"),
                "snippet": item.get("snippet") or item.get("snippet_text") or "",
                "source": "web",
            })
        # Fallback: news_results
        if not results and "news_results" in j:
            for item in j.get("news_results", [])[:num_results]:
                results.append({"title": item.get("title"), "url": item.get("link"), "snippet": item.get("snippet"), "source": "news"})
        return results
    except Exception:
        return []
