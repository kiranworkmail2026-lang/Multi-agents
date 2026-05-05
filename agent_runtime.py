"""Shared runtime helpers for the multi-agent system.

Used by both the CLI (main.py) and the HTTP server (server.py) so behavior
stays identical across entrypoints.
"""
from __future__ import annotations
from typing import Iterator

from langchain_core.messages import HumanMessage, AIMessage

from agents.supervisor import build_supervisor_app

# Short handoff acknowledgements we should skip when picking the final answer.
HANDOFF_TOKENS = ("transferring", "transferred", "delegating")
HANDOFF_MAX_LEN = 120


def pick_final_answer(messages: list) -> str:
    """Return the last substantive AIMessage content.

    Skips empty messages and short handoff acknowledgements like
    "Transferring back to supervisor".
    """
    for m in reversed(messages):
        if not isinstance(m, AIMessage):
            continue
        c = (m.content or "").strip()
        if not c:
            continue
        low = c.lower()
        if len(c) < HANDOFF_MAX_LEN and any(low.startswith(t) for t in HANDOFF_TOKENS):
            continue
        return c
    return ""


def _tool_call_names(msg) -> list[str]:
    tcs = getattr(msg, "tool_calls", None) or []
    return [tc.get("name", "?") for tc in tcs]


def stream_events(query: str, recursion_limit: int = 40) -> Iterator[dict]:
    """Run the supervisor on `query` and yield normalized event dicts.

    Each event is one of:
      - {"type": "agent_update", "agent": str, "node": str, "role": str,
         "name": str, "content": str, "tool_calls": list[str]}
      - {"type": "final", "answer": str}
      - {"type": "error", "message": str}

    The final answer is computed using pick_final_answer over the full
    message history collected during the stream.
    """
    app = build_supervisor_app()
    all_messages: list = []

    try:
        for ns, update in app.stream(
            {"messages": [HumanMessage(content=query)]},
            config={"recursion_limit": recursion_limit},
            subgraphs=True,
            stream_mode="updates",
        ):
            ns_label = ns[-1].split(":")[0] if ns else "top"
            for node_name, node_update in (update or {}).items():
                msgs = (node_update or {}).get("messages", []) if isinstance(node_update, dict) else []
                for m in msgs:
                    all_messages.append(m)
                    yield {
                        "type": "agent_update",
                        "agent": ns_label,
                        "node": node_name,
                        "role": m.__class__.__name__,
                        "name": getattr(m, "name", None) or ns_label,
                        "content": getattr(m, "content", "") or "",
                        "tool_calls": _tool_call_names(m),
                    }
    except Exception as e:  # pragma: no cover
        yield {"type": "error", "message": f"{type(e).__name__}: {e}"}
        return

    yield {"type": "final", "answer": pick_final_answer(all_messages) or "(no answer produced)"}
