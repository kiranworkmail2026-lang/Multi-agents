"""On-page SEO audit for a single URL.

Runs a fixed checklist (title length, meta, H1, hierarchy, alts, canonical,
robots, schema, word count, internal links) and returns prioritized issues.
"""
from __future__ import annotations
import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15"
MAX_BYTES = 2_000_000
TIMEOUT = 10.0


def _fetch(url: str) -> tuple[str | None, str | None]:
    try:
        with httpx.Client(timeout=TIMEOUT, follow_redirects=True,
                          headers={"User-Agent": UA}) as c:
            r = c.get(url)
            if r.status_code >= 400:
                return None, f"HTTP {r.status_code}"
            return r.content[:MAX_BYTES].decode(r.encoding or "utf-8", errors="ignore"), None
    except httpx.TimeoutException:
        return None, "timeout"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _audit(html: str, page_host: str) -> list[tuple[str, str, str]]:
    """Return list of (severity, check, finding)."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "svg", "noscript"]):
        tag.decompose()
    issues: list[tuple[str, str, str]] = []

    # Title
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    tl = len(title)
    if tl == 0:
        issues.append(("CRITICAL", "title", "missing <title> tag"))
    elif tl < 30:
        issues.append(("MAJOR", "title", f"title is {tl} chars; aim for 50–60"))
    elif tl > 65:
        issues.append(("MAJOR", "title", f"title is {tl} chars; likely truncated in SERPs"))

    # Meta description
    md = soup.find("meta", attrs={"name": "description"})
    desc = (md.get("content", "").strip() if md else "")
    dl = len(desc)
    if dl == 0:
        issues.append(("MAJOR", "meta description", "missing meta description"))
    elif dl < 100:
        issues.append(("MAJOR", "meta description", f"meta is {dl} chars; aim for 140–160"))
    elif dl > 170:
        issues.append(("MINOR", "meta description", f"meta is {dl} chars; will truncate"))

    # H1
    h1s = soup.find_all("h1")
    if len(h1s) == 0:
        issues.append(("CRITICAL", "H1", "no <h1> on page"))
    elif len(h1s) > 1:
        issues.append(("MAJOR", "H1", f"{len(h1s)} <h1> tags found; should be exactly 1"))

    # Heading hierarchy (H3 before any H2 is a smell)
    headings = soup.find_all(re.compile(r"^h[1-4]$"))
    saw_h2 = False
    for h in headings:
        lvl = int(h.name[1])
        if lvl == 2:
            saw_h2 = True
        if lvl == 3 and not saw_h2:
            issues.append(("MINOR", "hierarchy", "<h3> appears before any <h2>"))
            break

    # Image alt coverage
    imgs = soup.find_all("img")
    if imgs:
        with_alt = sum(1 for i in imgs if (i.get("alt") or "").strip())
        cov = with_alt / len(imgs)
        if cov < 0.8:
            issues.append(("MAJOR", "image alt",
                           f"{with_alt}/{len(imgs)} images have alt text ({cov:.0%}); aim ≥80%"))

    # Canonical
    if not soup.find("link", attrs={"rel": "canonical"}):
        issues.append(("MINOR", "canonical", "missing <link rel=canonical>"))

    # Robots
    rm = soup.find("meta", attrs={"name": "robots"})
    if rm:
        content = (rm.get("content") or "").lower()
        if "noindex" in content:
            issues.append(("CRITICAL", "robots", "page has noindex — won't appear in search"))

    # Schema.org JSON-LD
    if not soup.find("script", attrs={"type": "application/ld+json"}):
        issues.append(("MINOR", "schema", "no JSON-LD structured data found"))

    # Word count
    text = soup.get_text(" ", strip=True)
    words = re.findall(r"[A-Za-z']+", text)
    wc = len(words)
    if wc < 300:
        issues.append(("MINOR", "word count", f"only {wc} words; thin content"))

    # Internal links
    internal = 0
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/") or (page_host and page_host in href):
            internal += 1
    if internal < 3:
        issues.append(("MINOR", "internal links", f"only {internal} internal links"))

    return issues


def _format(url: str, issues: list[tuple[str, str, str]]) -> str:
    sev_order = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2}
    issues.sort(key=lambda x: sev_order.get(x[0], 9))
    out = [f"## On-page SEO audit — {url}", ""]
    if not issues:
        out.append("✅ No issues found against the standard checklist.")
        return "\n".join(out)
    counts = {"CRITICAL": 0, "MAJOR": 0, "MINOR": 0}
    for s, _, _ in issues:
        counts[s] = counts.get(s, 0) + 1
    out.append(f"**Summary:** {counts['CRITICAL']} critical · {counts['MAJOR']} major · {counts['MINOR']} minor")
    out.append("")
    for sev, check, finding in issues:
        out.append(f"- **[{sev}]** _{check}_ — {finding}")
    return "\n".join(out)


@tool
def on_page_audit(url: str) -> str:
    """Run a standard on-page SEO audit against a single URL.

    Checks: title length, meta description, H1 count, heading hierarchy,
    image alt coverage, canonical tag, robots meta, JSON-LD schema, word
    count, internal-link count. Returns a prioritized list of issues by
    severity (CRITICAL / MAJOR / MINOR) with the specific finding and
    threshold.

    Args:
        url: full URL of the page to audit (https://...).

    Returns:
        Markdown audit report. Use this for any "audit this page" question.
    """
    if not url.startswith(("http://", "https://")):
        return f"ERROR: {url!r} is not a valid http(s) URL."
    html, err = _fetch(url)
    if err:
        return f"ERROR fetching {url}: {err}"
    host = urlparse(url).netloc
    issues = _audit(html, host)
    return _format(url, issues)
