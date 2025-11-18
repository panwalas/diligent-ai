import requests
from typing import List, Dict, Any
from .config import load_config, get_search_config


# List of low-quality domains to filter out
BLACKLISTED_DOMAINS = [
    "pinterest.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "youtube.com",
    "reddit.com",
    "quora.com",
    "linkedin.com/posts",
    "medium.com/@",
]

# Preferred high-quality sources
PREFERRED_SOURCES = [
    "crunchbase.com",
    "techcrunch.com",
    "bloomberg.com",
    "reuters.com",
    "wsj.com",
    "ft.com",
    "forbes.com",
    "sec.gov",
    "news.ycombinator.com",
]


def filter_evidence(evidence_items: List[Dict[str, Any]], min_snippet_length: int = 30) -> List[Dict[str, Any]]:
    """Filter out low-quality or irrelevant evidence.

    Args:
        evidence_items: List of evidence dictionaries with url, snippet, title
        min_snippet_length: Minimum length of snippet to be considered valid

    Returns:
        Filtered list of evidence items
    """
    filtered = []

    for item in evidence_items:
        url = item.get("url", "")
        snippet = item.get("snippet", "")
        title = item.get("title", "")

        # Skip items with no URL
        if not url:
            continue

        # Skip blacklisted domains
        if any(domain in url.lower() for domain in BLACKLISTED_DOMAINS):
            continue

        # Skip items with very short or no snippets
        if len(snippet) < min_snippet_length and len(title) < min_snippet_length:
            continue

        # Calculate quality score
        quality_score = 0
        if any(source in url.lower() for source in PREFERRED_SOURCES):
            quality_score += 2
        if len(snippet) > 100:
            quality_score += 1
        if snippet and title:
            quality_score += 1

        item["quality_score"] = quality_score
        filtered.append(item)

    # Sort by quality score (highest first)
    filtered.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

    return filtered


def search_serpapi(query: str, cfg_path: str = None, num_results: int = 5) -> List[Dict[str, Any]]:
    """Use SerpAPI to retrieve web evidence for a query.

    The SerpAPI key is read from config.search.serpapi_key or from the environment.
    Returns a filtered list of high-quality evidence items with keys: title, url, snippet, source.
    """
    cfg = load_config(cfg_path) if cfg_path else {}
    search_cfg = get_search_config(cfg)
    key = search_cfg.get("serpapi_key") or search_cfg.get("api_key")
    if not key:
        return []

    params = {"q": query, "api_key": key, "num": num_results * 2}  # Request more to account for filtering
    try:
        r = requests.get("https://serpapi.com/search", params=params, timeout=10)
        r.raise_for_status()
        j = r.json()
        results = []
        # SerpAPI returns organic_results in many cases
        for item in j.get("organic_results", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("link") or item.get("url"),
                "snippet": item.get("snippet") or item.get("snippet_text") or "",
                "source": "web",
            })
        # Fallback: news_results
        if not results and "news_results" in j:
            for item in j.get("news_results", []):
                results.append({"title": item.get("title"), "url": item.get("link"), "snippet": item.get("snippet"), "source": "news"})

        # Filter and rank evidence
        filtered_results = filter_evidence(results)
        return filtered_results[:num_results]  # Return top N after filtering
    except Exception:
        return []
