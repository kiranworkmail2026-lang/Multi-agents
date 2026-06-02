"""SERP / content-gap analysis.

Pulls top-N organic results for a keyword via SerpAPI, fetches each URL,
extracts on-page signals (title, H1/H2, word count), and surfaces common
themes + content gaps.
"""
from __future__ import annotations
import os
import re
from collections import Counter

import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from serpapi import GoogleSearch

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15"
MAX_BYTES = 2_000_000
TIMEOUT = 10.0
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "are", "from", "your", "you",
    "how", "what", "why", "when", "best", "top", "guide", "vs", "what's",
    "of", "to", "in", "a", "an", "is", "on", "at", "by", "be", "as", "or",
    "it", "we", "our", "all", "can", "has", "have", "more", "use",
}


def _fetch(url: str) -> tuple[str | None, str | None]:
    """Return (html, error). Defensive: timeouts, size cap, real UA."""
    try:
        with httpx.Client(timeout=TIMEOUT, follow_redirects=True,
                          headers={"User-Agent": UA}) as c:
            r = c.get(url)
            if r.status_code >= 400:
                return None, f"HTTP {r.status_code}"
            data = r.content[:MAX_BYTES]
            return data.decode(r.encoding or "utf-8", errors="ignore"), None
    except httpx.TimeoutException:
        return None, "timeout"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _parse(html: str) -> dict:
    """Extract title / meta / h1 / h2 / body text from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "svg", "noscript"]):
        tag.decompose()
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    meta = ""
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        meta = md["content"].strip()
    h1 = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2 = [h.get_text(strip=True) for h in soup.find_all("h2")]
    body_text = soup.get_text(" ", strip=True)
    words = re.findall(r"[A-Za-z']+", body_text.lower())
    return {
        "title": title,
        "meta": meta,
        "h1": h1,
        "h2": h2,
        "word_count": len(words),
        "words": words,
    }


def _common_themes(h2_lists: list[list[str]], top_k: int = 8) -> list[tuple[str, int]]:
    """Find recurring 2-word phrases across H2 headings."""
    bigrams: Counter[str] = Counter()
    for h2s in h2_lists:
        for h in h2s:
            tokens = [t for t in re.findall(r"[A-Za-z']+", h.lower()) if t not in STOPWORDS and len(t) > 2]
            for i in range(len(tokens) - 1):
                bigrams[f"{tokens[i]} {tokens[i+1]}"] += 1
    return [(b, n) for b, n in bigrams.most_common(top_k) if n >= 2]


@tool
def serp_analysis(keyword: str, top_n: int = 8, user_url: str | None = None) -> str:
    """Analyze the top-N organic results for a keyword.

    For each ranking page: fetches HTML, extracts title/meta/H1/H2/word count.
    Surfaces average word count and recurring H2 themes (content patterns
    that appear across multiple top-ranking pages). If user_url is provided,
    lists themes the user's page is missing.

    Args:
        keyword: search query to analyze.
        top_n: number of top organic results to fetch (capped at 10).
        user_url: optional — your page's URL, for gap analysis.

    Returns:
        Markdown report with top-N overview, common themes, and gaps.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return "ERROR: SERPAPI_API_KEY is not set."
    top_n = max(1, min(int(top_n), 10))

    try:
        serp = GoogleSearch({
            "q": keyword, "api_key": api_key, "engine": "google", "num": top_n,
        }).get_dict()
    except Exception as e:
        return f"ERROR fetching SERP: {type(e).__name__}: {e}"
    if "error" in serp:
        return f"SerpAPI error: {serp['error']}"

    organic = (serp.get("organic_results") or [])[:top_n]
    if not organic:
        return f"No organic results for {keyword!r}."

    rows: list[dict] = []
    for i, r in enumerate(organic, 1):
        url = r.get("link", "")
        html, err = _fetch(url)
        if err:
            rows.append({"i": i, "url": url, "title": r.get("title", ""),
                         "error": err, "word_count": 0, "h2": []})
            continue
        info = _parse(html)
        rows.append({"i": i, "url": url, **info})

    word_counts = [r["word_count"] for r in rows if not r.get("error")]
    avg_wc = int(sum(word_counts) / len(word_counts)) if word_counts else 0
    themes = _common_themes([r.get("h2", []) for r in rows if not r.get("error")])

    parts: list[str] = [f"## SERP analysis for {keyword!r}", ""]
    parts.append("### Top results")
    parts.append("| # | Title | URL | Words | H1 | H2 count |")
    parts.append("|---|---|---|---|---|---|")
    for r in rows:
        if r.get("error"):
            parts.append(f"| {r['i']} | {r.get('title','')[:60]} | {r['url']} | _fetch err: {r['error']}_ | – | – |")
        else:
            h1_str = (r["h1"][0] if r["h1"] else "")[:50]
            parts.append(f"| {r['i']} | {r.get('title','')[:60]} | {r['url']} | {r['word_count']} | {h1_str} | {len(r['h2'])} |")

    parts.append("")
    parts.append(f"**Average word count across top {len(word_counts)}: {avg_wc}**")
    parts.append("")
    if themes:
        parts.append("### Common H2 themes across top results")
        for theme, n in themes:
            parts.append(f"- _{theme}_ — appears in {n} pages")
    else:
        parts.append("### Common H2 themes\n_None recur in 2+ pages._")

    # Gap analysis vs user_url
    if user_url:
        parts.append("")
        parts.append(f"### Gap vs your page: {user_url}")
        html, err = _fetch(user_url)
        if err:
            parts.append(f"_Could not fetch your URL: {err}_")
        else:
            mine = _parse(html)
            my_text = " ".join(mine["h2"]).lower()
            missing = [t for t, n in themes if t not in my_text]
            if missing:
                parts.append("Themes appearing in top results but missing from your H2s:")
                for t in missing:
                    parts.append(f"- **{t}**")
            else:
                parts.append("Your H2 themes cover the recurring patterns. ✓")

    return "\n".join(parts)
