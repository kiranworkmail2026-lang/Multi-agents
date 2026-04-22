"""Verbose runner — prints every message with type, name, tool calls, and content."""
import sys
from langchain_core.messages import HumanMessage
from agents.supervisor import build_supervisor_app


def run(query: str) -> None:
    app = build_supervisor_app()
    print(f"\n>>> QUERY: {query}\n" + "=" * 80)

    step = 0
    for chunk in app.stream(
        {"messages": [HumanMessage(content=query)]},
        config={"recursion_limit": 20},
        stream_mode="updates",
    ):
        for node, update in chunk.items():
            step += 1
            print(f"\n[step {step}] node={node}")
            msgs = update.get("messages", []) if isinstance(update, dict) else []
            for m in msgs:
                kind = m.__class__.__name__
                name = getattr(m, "name", None) or "-"
                tool_calls = getattr(m, "tool_calls", None) or []
                content = (getattr(m, "content", "") or "").strip()
                print(f"  └─ {kind}  name={name}")
                if tool_calls:
                    for tc in tool_calls:
                        print(f"       tool_call: {tc.get('name')}  args={tc.get('args')}")
                if content:
                    preview = content if len(content) < 400 else content[:400] + "…"
                    print(f"       content: {preview}")


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Who won the 2024 Nobel Prize in Physics?"
    run(q)
