import os
from langchain_core.tools import tool
from serpapi import GoogleSearch


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web via SerpAPI (Google) and return titles, URLs, and snippets."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return "ERROR: SERPAPI_API_KEY is not set in the environment."

    params = {
        "q": query,
        "api_key": api_key,
        "engine": "google",
        "num": max_results,
    }
    results = GoogleSearch(params).get_dict()

    if "error" in results:
        return f"SerpAPI error: {results['error']}"

    organic = results.get("organic_results", [])[:max_results]

    answer_box = results.get("answer_box")
    prefix = ""
    if answer_box:
        snippet = answer_box.get("snippet") or answer_box.get("answer") or ""
        if snippet:
            prefix = f"[Answer box] {snippet}\n\n"

    if not organic:
        return prefix or "No results found."

    body = "\n\n".join(
        f"{i+1}. {r.get('title','')}\n{r.get('link','')}\n{r.get('snippet','')}"
        for i, r in enumerate(organic)
    )
    return prefix + body
