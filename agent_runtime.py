"""Shared runtime helpers for the multi-agent system.

Used by both the CLI (main.py) and the HTTP server (server.py) so behavior
stays identical across entrypoints.
"""
from __future__ import annotations
import uuid
from typing import Any, Iterator

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command

from agents.supervisor import build_supervisor_app

# Short handoff acknowledgements we should skip when picking the final answer.
HANDOFF_TOKENS = ("transferring", "transferred", "delegating")
HANDOFF_MAX_LEN = 120


def as_text(content) -> str:
    """Normalize LangChain message content to a plain string.

    Gemini (langchain-google-genai) returns content as a list of parts
    (e.g. [{"type":"text","text":"..."}]) on tool-calling turns; Ollama
    returns it as a plain string. Normalize both to str so downstream
    code (.strip(), startswith) works uniformly.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict):
                t = p.get("text") or p.get("content") or ""
                if isinstance(t, str) and t:
                    parts.append(t)
        return "\n".join(parts)
    return str(content)


def pick_final_answer(messages: list) -> str:
    """Return the last substantive AIMessage content."""
    for m in reversed(messages):
        if not isinstance(m, AIMessage):
            continue
        c = as_text(m.content).strip()
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


def new_thread_id() -> str:
    """Generate a fresh thread_id (used when the client doesn't supply one)."""
    return uuid.uuid4().hex


def _check_pending_interrupt(app, config: dict, thread_id: str) -> dict | None:
    """If the graph paused on an interrupt, return a pending_approval event.

    Returns None if the graph ran to completion (no interrupt pending).
    """
    try:
        state = app.get_state(config)
    except Exception:
        return None
    if not state or not getattr(state, "next", None):
        return None
    # state.tasks holds pending tasks; each task's .interrupts list holds
    # any interrupt() payloads queued.
    for task in getattr(state, "tasks", []) or []:
        interrupts = getattr(task, "interrupts", None) or []
        for itr in interrupts:
            payload = getattr(itr, "value", None)
            if payload is not None:
                return {
                    "type": "pending_approval",
                    "thread_id": thread_id,
                    "payload": payload,
                }
    return None


def _drive_stream(app, input_value: Any, config: dict, thread_id: str) -> Iterator[dict]:
    """Shared loop: drive app.stream(...), yield agent_update events,
    then detect a pending interrupt or emit a final.
    """
    all_messages: list = []
    try:
        for ns, update in app.stream(
            input_value,
            config=config,
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
                        "content": as_text(getattr(m, "content", "")),
                        "tool_calls": _tool_call_names(m),
                        "thread_id": thread_id,
                    }
    except Exception as e:  # pragma: no cover
        yield {"type": "error", "message": f"{type(e).__name__}: {e}", "thread_id": thread_id}
        return

    pending = _check_pending_interrupt(app, config, thread_id)
    if pending is not None:
        yield pending
        return

    yield {
        "type": "final",
        "answer": pick_final_answer(all_messages) or "(no answer produced)",
        "thread_id": thread_id,
    }


def stream_events(query: str, thread_id: str | None = None,
                  recursion_limit: int = 40) -> Iterator[dict]:
    """Run the supervisor on `query` and yield normalized event dicts.

    If the graph pauses on an interrupt (e.g. blog topic approval), the
    final event will be `pending_approval` instead of `final`. The client
    can resume by calling resume_events() with the same thread_id and the
    user's chosen value.
    """
    app = build_supervisor_app()
    tid = thread_id or new_thread_id()
    config = {
        "configurable": {"thread_id": tid},
        "recursion_limit": recursion_limit,
    }
    yield from _drive_stream(app, {"messages": [HumanMessage(content=query)]}, config, tid)


def resume_events(thread_id: str, chosen: Any,
                  recursion_limit: int = 40) -> Iterator[dict]:
    """Resume a previously interrupted run with the human's chosen value.

    `chosen` is forwarded to the paused `interrupt()` call as its return
    value. For the blog flow this is the chosen topic (dict or str).
    """
    app = build_supervisor_app()
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": recursion_limit,
    }
    yield from _drive_stream(app, Command(resume=chosen), config, thread_id)
