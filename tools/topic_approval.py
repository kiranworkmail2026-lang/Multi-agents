"""Topic-approval interrupt tool.

The seo_agent calls this AFTER it has distilled SEO findings into 3–5
candidate blog topics. The tool calls LangGraph's `interrupt()` primitive,
which pauses the graph and persists state via the checkpointer. The HTTP
server detects the interrupted state, emits a `pending_approval` SSE event
to the client with the proposed topics, and closes the stream.

When the client POSTs to /resume with the chosen topic, the graph resumes
from this exact point and this function returns the chosen-topic string
(JSON-encoded) as if it were a normal tool result.
"""
from __future__ import annotations
import json

from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def request_topic_approval(topics_json: str) -> str:
    """Pause and ask the human to pick ONE blog topic from N candidates.

    Call this AFTER you have used keyword_research / SERP analysis and
    distilled 3–5 candidate blog topics. The graph will pause; the user
    will respond with the chosen topic (or a free-text override).

    Args:
        topics_json: JSON string of a list of topic objects. Each object
            should have at least:
                {
                  "id": "t1",
                  "title": "...",            # working title, 50–60 chars
                  "target_keyword": "...",   # primary keyword
                  "intent": "informational|commercial|transactional",
                  "outline_h2s": ["...", "...", "..."],
                  "rationale": "why this topic"
                }

    Returns:
        JSON string of the chosen topic (same shape as one of the inputs),
        OR a free-text override the user wrote instead.
    """
    # Defensive: ensure we're handing the client well-formed JSON in the
    # pending_approval payload. If the agent gave us malformed input,
    # still interrupt (don't crash) but include a parse error hint.
    try:
        topics = json.loads(topics_json)
        payload = {"proposed_topics": topics}
    except Exception as e:
        payload = {"proposed_topics_raw": topics_json,
                   "parse_error": f"{type(e).__name__}: {e}"}

    chosen = interrupt(payload)
    # `chosen` is whatever the caller passed to Command(resume=...).
    # Normalize to a JSON string the next LLM turn can read cleanly.
    if isinstance(chosen, (dict, list)):
        return json.dumps(chosen)
    return str(chosen)
