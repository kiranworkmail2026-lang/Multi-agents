import sys
from langchain_core.messages import HumanMessage, AIMessage
from agents.supervisor import build_supervisor_app


def _preview(text: str, limit: int = 2000) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated {len(text) - limit} chars]"


def _describe_tool_calls(msg) -> str:
    tcs = getattr(msg, "tool_calls", None) or []
    if not tcs:
        return ""
    return "  [tool_calls: " + ", ".join(tc.get("name", "?") for tc in tcs) + "]"


def run(query: str) -> None:
    app = build_supervisor_app()
    all_messages: list = []

    print(f"\n>>> USER: {query}\n")

    for ns, update in app.stream(
        {"messages": [HumanMessage(content=query)]},
        config={"recursion_limit": 40},
        subgraphs=True,
        stream_mode="updates",
    ):
        ns_label = ns[-1].split(":")[0] if ns else "top"
        for node_name, node_update in (update or {}).items():
            msgs = (node_update or {}).get("messages", []) if isinstance(node_update, dict) else []
            for m in msgs:
                all_messages.append(m)
                role = m.__class__.__name__
                who = getattr(m, "name", None) or ns_label
                content = getattr(m, "content", "") or ""
                extras = _describe_tool_calls(m)
                print(f"── {ns_label}/{node_name}  ·  {role}/{who}{extras} ──")
                if content:
                    print(_preview(content))
                print()

    # Pick a sensible final answer: prefer the last substantive AIMessage,
    # skipping empty ones and short handoff acknowledgements.
    HANDOFF_TOKENS = ("transferring", "transferred", "delegating")
    final_text = ""
    for m in reversed(all_messages):
        if not isinstance(m, AIMessage):
            continue
        c = (m.content or "").strip()
        if not c:
            continue
        low = c.lower()
        if len(c) < 120 and any(low.startswith(t) for t in HANDOFF_TOKENS):
            continue
        final_text = c
        break

    print("=" * 72)
    print("FINAL ANSWER")
    print("=" * 72)
    print(final_text or "(no answer produced)")


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Who won the 2024 Nobel Prize in Physics?"
    run(q)
