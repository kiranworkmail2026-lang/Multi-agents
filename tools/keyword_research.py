"""Keyword research via SerpAPI.

Expands a seed keyword into related queries + intent classification,
based purely on SERP shape (no paid SEO API needed).
"""
from __future__ import annotations
import os

from langchain_core.tools import tool
from serpapi import GoogleSearch


def _classify_intent(serp: dict) -> tuple[str, str]:
    """Return (intent, signal) inferred from SERP shape."""
    if serp.get("shopping_results") or serp.get("inline_shopping"):
        return "transactional", "shopping carousel present"
    if serp.get("answer_box") or serp.get("knowledge_graph", {}).get("description"):
        return "informational", "answer box / knowledge panel"
    organic = serp.get("organic_results", []) or []
    titles = " ".join((r.get("title", "") or "").lower() for r in organic[:5])
    if any(w in titles for w in ("best ", "top ", "vs ", "review", "comparison")):
        return "commercial", "comparison / review titles in top 5"
    if any(w in titles for w in ("how to", "what is", "guide", "tutorial")):
        return "informational", "how-to / guide titles dominate"
    if any(w in titles for w in ("pricing", "demo", "free trial", "buy", "signup")):
        return "transactional", "vendor / product pages in top 5"
    return "informational", "default — no strong commercial signal"


def _serp(query: str, api_key: str) -> dict:
    return GoogleSearch({
        "q": query,
        "api_key": api_key,
        "engine": "google",
        "num": 10,
    }).get_dict()


@tool
def keyword_research(seed: str, depth: int = 8) -> str:
    """Expand a seed keyword into related queries with intent classification.

    Pulls related_searches, related_questions ("People also ask"), and
    classifies intent from the SERP shape. Uses SerpAPI (one call).

    Args:
        seed: the seed keyword to expand from.
        depth: max related keywords to return (capped at 15).

    Returns:
        Markdown table: keyword | intent | SERP signal.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return "ERROR: SERPAPI_API_KEY is not set."
    depth = max(1, min(int(depth), 15))

    try:
        serp = _serp(seed, api_key)
    except Exception as e:
        return f"ERROR fetching SERP for {seed!r}: {type(e).__name__}: {e}"

    if "error" in serp:
        return f"SerpAPI error: {serp['error']}"

    candidates: list[str] = []
    for r in serp.get("related_searches", []) or []:
        q = (r.get("query") or "").strip()
        if q:
            candidates.append(q)
    for r in serp.get("related_questions", []) or []:
        q = (r.get("question") or "").strip()
        if q:
            candidates.append(q)

    # Dedupe (case-insensitive), drop the seed itself.
    seen: set[str] = {seed.lower().strip()}
    uniq: list[str] = []
    for q in candidates:
        k = q.lower().strip()
        if k not in seen:
            seen.add(k)
            uniq.append(q)
        if len(uniq) >= depth:
            break

    if not uniq:
        return f"No related keywords surfaced for {seed!r}. Try a broader seed."

    # Classify intent of the seed (one SERP we already have) + each kw needs
    # its own SERP call which is expensive — instead infer intent for related
    # keywords from their phrasing, and use the real SERP only for the seed.
    seed_intent, seed_signal = _classify_intent(serp)
    rows = [f"| Keyword | Intent | Signal |", f"|---|---|---|",
            f"| **{seed}** (seed) | {seed_intent} | {seed_signal} |"]
    for q in uniq:
        ql = q.lower()
        if any(w in ql for w in ("how", "what", "why", "guide", "tutorial", "?")):
            intent, sig = "informational", "question / how-to phrasing"
        elif any(w in ql for w in ("best", "top", "vs", "review", "alternative")):
            intent, sig = "commercial", "comparison phrasing"
        elif any(w in ql for w in ("pricing", "cost", "demo", "buy", "trial")):
            intent, sig = "transactional", "purchase phrasing"
        else:
            intent, sig = "informational", "default"
        rows.append(f"| {q} | {intent} | {sig} |")

    return "\n".join(rows)
