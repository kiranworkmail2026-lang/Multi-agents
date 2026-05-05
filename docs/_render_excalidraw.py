"""Generate an Excalidraw .excalidraw JSON for the current architecture.

Open the output file at excalidraw.com or in the Excalidraw VS Code extension.
"""
import json
import random
import time
from pathlib import Path

random.seed(20260424)


def _seed():
    return random.randint(1, 2**31 - 1)


def _nonce():
    return random.randint(1, 2**31 - 1)


def _base(id_: str, x: float, y: float, w: float, h: float, **kw):
    return {
        "id": id_,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "angle": 0,
        "strokeColor": kw.get("strokeColor", "#1e1e1e"),
        "backgroundColor": kw.get("backgroundColor", "transparent"),
        "fillStyle": kw.get("fillStyle", "solid"),
        "strokeWidth": kw.get("strokeWidth", 2),
        "strokeStyle": kw.get("strokeStyle", "solid"),
        "roughness": kw.get("roughness", 1),
        "opacity": 100,
        "groupIds": kw.get("groupIds", []),
        "frameId": None,
        "roundness": kw.get("roundness", {"type": 3}),
        "seed": _seed(),
        "version": 1,
        "versionNonce": _nonce(),
        "isDeleted": False,
        "boundElements": kw.get("boundElements", []),
        "updated": int(time.time() * 1000),
        "link": None,
        "locked": False,
    }


def rect(id_, x, y, w, h, bg="#ffffff", stroke="#1e1e1e", sw=2, rough=1, group=None, rounded=True):
    el = _base(
        id_, x, y, w, h,
        backgroundColor=bg, strokeColor=stroke, strokeWidth=sw, roughness=rough,
        roundness={"type": 3} if rounded else None,
        groupIds=[group] if group else [],
    )
    el["type"] = "rectangle"
    return el


def ellipse(id_, x, y, w, h, bg="#ffffff", stroke="#1e1e1e"):
    el = _base(id_, x, y, w, h, backgroundColor=bg, strokeColor=stroke, roundness=None)
    el["type"] = "ellipse"
    return el


def text(id_, x, y, w, h, content, size=16, align="center", valign="middle",
         color="#1e1e1e", family=5, bold=False):
    # family: 1=Virgil(hand), 2=Helvetica, 3=Cascadia(mono), 5=Nunito
    el = _base(id_, x, y, w, h, strokeColor=color, backgroundColor="transparent",
               fillStyle="solid", roughness=0, roundness=None)
    el["type"] = "text"
    el["text"] = content
    el["originalText"] = content
    el["fontSize"] = size
    el["fontFamily"] = family
    el["textAlign"] = align
    el["verticalAlign"] = valign
    el["baseline"] = int(size * 0.85)
    el["containerId"] = None
    el["lineHeight"] = 1.25
    if bold:
        # Excalidraw doesn't expose bold directly; emulate with heavier family
        el["fontFamily"] = 2
    return el


def arrow(id_, x1, y1, x2, y2, dashed=False, color="#1e1e1e", sw=2, label=None):
    pts = [[0, 0], [x2 - x1, y2 - y1]]
    el = _base(id_, x1, y1, abs(x2 - x1), abs(y2 - y1),
               strokeColor=color, strokeWidth=sw,
               strokeStyle="dashed" if dashed else "solid", roughness=0,
               roundness=None)
    el["type"] = "arrow"
    el["points"] = pts
    el["lastCommittedPoint"] = None
    el["startBinding"] = None
    el["endBinding"] = None
    el["startArrowhead"] = None
    el["endArrowhead"] = "arrow"
    el["elbowed"] = False
    return el


elements = []
e = elements.append


# ---------- Title ----------
e(text("t-title", 620, 20, 760, 30,
       "Marketing Multi-Agent System — Shipped Architecture",
       size=26, bold=True))
e(text("t-sub", 620, 55, 760, 22,
       "LangGraph supervisor · Ollama gemma4:e4b + nomic-embed-text · Chroma",
       size=14, color="#555"))


# ---------- User / entry ----------
e(rect("u-user", 40, 120, 150, 60, bg="#d0ebff"))
e(text("t-user", 40, 135, 150, 30, "User (CLI)", size=16, bold=True))
e(text("t-user2", 40, 155, 150, 20, "python main.py ...", size=12, color="#555"))

e(rect("u-main", 40, 210, 150, 60, bg="#e7f5ff"))
e(text("t-main", 40, 220, 150, 20, "main.py", size=16, bold=True))
e(text("t-main2", 40, 240, 150, 20, "app.stream() · subgraphs", size=12, color="#555"))

e(arrow("a-user-main", 115, 180, 115, 210))


# ---------- LangGraph box ----------
e(rect("g-langgraph", 230, 110, 820, 520, bg="#f8f9fa", stroke="#495057", sw=3, rounded=True))
e(text("t-lg", 230, 125, 820, 28, "LangGraph · langgraph-supervisor", size=20, bold=True))
e(text("t-lg2", 230, 158, 820, 20,
       "create_supervisor(agents=[research, analytics, strategy], output_mode='last_message')",
       size=12, color="#555"))

# Supervisor
e(rect("n-super", 500, 200, 280, 100, bg="#ffec99", sw=3))
e(text("t-super", 500, 212, 280, 24, "Supervisor", size=20, bold=True))
e(text("t-super2", 500, 240, 280, 20, "gemma4:e4b · temp 0.1", size=12, color="#555"))
e(text("t-super3", 500, 260, 280, 18, "router · handoff tool calls", size=12, color="#555"))
e(text("t-super4", 500, 278, 280, 18, "rule: research ∥ analytics → strategy", size=11, color="#862e9c"))

# Three worker agents
e(rect("n-research", 260, 360, 220, 150, bg="#b2f2bb", sw=2))
e(text("t-r1", 260, 370, 220, 24, "research_agent", size=18, bold=True))
e(text("t-r2", 260, 398, 220, 20, "ReAct · gemma4:e4b", size=12, color="#555"))
e(text("t-r3", 260, 425, 220, 18, "tools:", size=12, bold=True))
e(text("t-r4", 260, 445, 220, 18, "• knowledge_search", size=12))
e(text("t-r5", 260, 463, 220, 18, "• web_search (SerpAPI)", size=12))
e(text("t-r6", 260, 485, 220, 18, "returns cited findings", size=11, color="#555"))

e(rect("n-analytics", 520, 360, 240, 150, bg="#ffc9c9", sw=2))
e(text("t-a1", 520, 370, 240, 24, "analytics_agent", size=18, bold=True))
e(text("t-a2", 520, 398, 240, 20, "ReAct · gemma4:e4b", size=12, color="#555"))
e(text("t-a3", 520, 425, 240, 18, "tools:", size=12, bold=True))
e(text("t-a4", 520, 445, 240, 18, "• python_repl (pandas)", size=12))
e(text("t-a5", 520, 463, 240, 18, "• (clickhouse_query — future)", size=12, color="#999"))
e(text("t-a6", 520, 485, 240, 18, "returns KPIs & trends", size=11, color="#555"))

e(rect("n-strategy", 800, 360, 220, 150, bg="#d0bfff", sw=2))
e(text("t-s1", 800, 370, 220, 24, "strategy_agent", size=18, bold=True))
e(text("t-s2", 800, 398, 220, 20, "ReAct · gemma4:e4b", size=12, color="#555"))
e(text("t-s3", 800, 425, 220, 18, "tools:", size=12, bold=True))
e(text("t-s4", 800, 445, 220, 18, "• knowledge_search", size=12))
e(text("t-s5", 800, 468, 220, 18, "SYNTHESIZER", size=12, bold=True, color="#862e9c"))
e(text("t-s6", 800, 488, 220, 18, "produces markdown report", size=11, color="#555"))

# Handoff arrows (supervisor <-> workers)
e(arrow("a-sup-r", 560, 300, 370, 360, color="#1971c2", sw=2))
e(arrow("a-r-sup", 380, 360, 580, 300, color="#1971c2", sw=2, dashed=True))
e(arrow("a-sup-a", 640, 300, 640, 360, color="#1971c2", sw=2))
e(arrow("a-a-sup", 660, 360, 660, 300, color="#1971c2", sw=2, dashed=True))
e(arrow("a-sup-s", 720, 300, 910, 360, color="#1971c2", sw=2))
e(arrow("a-s-sup", 900, 360, 700, 300, color="#1971c2", sw=2, dashed=True))


# ---------- UNSTRUCTURED data plane (right-top) ----------
e(rect("p-un", 1090, 110, 500, 280, bg="#f3d9fa", stroke="#862e9c", sw=3))
e(text("t-un1", 1090, 120, 500, 24, "UNSTRUCTURED DATA PLANE", size=16, bold=True, color="#862e9c"))
e(text("t-un2", 1090, 146, 500, 18, "prose · brand · strategy memory", size=12, color="#555"))

# Chroma cylinder (use ellipse + rect for cylinder look)
e(ellipse("c-top", 1200, 185, 240, 40, bg="#e599f7", stroke="#862e9c"))
e(rect("c-body", 1200, 205, 240, 100, bg="#e599f7", stroke="#862e9c", rounded=False))
e(ellipse("c-bottom", 1200, 285, 240, 40, bg="#e599f7", stroke="#862e9c"))
e(text("t-chroma", 1200, 220, 240, 24, "Chroma (local)", size=18, bold=True))
e(text("t-chroma2", 1200, 244, 240, 20, "vectordb/", size=12, family=3))
e(text("t-chroma3", 1200, 264, 240, 20, "collection:", size=12, color="#555"))
e(text("t-chroma4", 1200, 280, 240, 20, "knowledge_base", size=13, bold=True))

# embedding
e(rect("p-emb", 1110, 210, 80, 80, bg="#d0bfff", stroke="#862e9c"))
e(text("t-emb", 1110, 220, 80, 18, "nomic-", size=11, bold=True))
e(text("t-emb2", 1110, 238, 80, 18, "embed-", size=11, bold=True))
e(text("t-emb3", 1110, 256, 80, 18, "text", size=11, bold=True))
e(text("t-emb4", 1110, 274, 80, 14, "(Ollama)", size=10, color="#555"))

e(arrow("a-emb-ch", 1190, 250, 1200, 250, color="#862e9c", dashed=True))

# ingest source
e(rect("p-ingest", 1110, 335, 460, 30, bg="#fff3bf", stroke="#fab005"))
e(text("t-ingest", 1110, 338, 460, 24,
       "ingest.py  (--watch)  ·  chunk 500 tokens / 10% overlap  ·  upsert",
       size=12))

e(rect("p-docs", 1110, 373, 460, 28, bg="#ffec99", stroke="#fab005"))
e(text("t-docs", 1110, 377, 460, 22,
       "docs/knowledge/  —  brand_guidelines · icp · q1_postmortem · (drop any .md/.txt)",
       size=11))

e(arrow("a-docs-ing", 1340, 373, 1340, 365, color="#862e9c"))
e(arrow("a-ing-ch", 1340, 335, 1340, 305, color="#862e9c"))


# ---------- STRUCTURED data plane (right-bottom) ----------
e(rect("p-st", 1090, 410, 500, 220, bg="#d3f9d8", stroke="#2b8a3e", sw=3))
e(text("t-st1", 1090, 420, 500, 24, "STRUCTURED DATA PLANE", size=16, bold=True, color="#2b8a3e"))
e(text("t-st2", 1090, 446, 500, 18, "rows · metrics · facts", size=12, color="#555"))

e(rect("p-csv", 1110, 475, 225, 60, bg="#b2f2bb", stroke="#2b8a3e"))
e(text("t-csv", 1110, 485, 225, 20, "sample_data/*.csv", size=14, bold=True, family=3))
e(text("t-csv2", 1110, 508, 225, 18, "pandas via python_repl", size=11, color="#555"))

e(rect("p-ch", 1345, 475, 225, 60, bg="#ebfbee", stroke="#2b8a3e"))
e(text("t-ch", 1345, 485, 225, 20, "ClickHouse", size=14, bold=True))
e(text("t-ch2", 1345, 508, 225, 18, "(future clickhouse_query tool)", size=11, color="#999"))

# Authority rule
e(rect("p-rule", 1110, 558, 460, 55, bg="#ffe3e3", stroke="#c92a2a", sw=2))
e(text("t-rule1", 1110, 562, 460, 22, "Separation rule", size=13, bold=True, color="#c92a2a"))
e(text("t-rule2", 1110, 583, 460, 18, "numbers ⇢ structured plane only", size=12))
e(text("t-rule3", 1110, 600, 460, 18, "prose / brand / memory ⇢ unstructured plane only", size=12))


# ---------- Tool / data edges ----------
# research -> knowledge_search -> Chroma
e(arrow("d-r-kb", 480, 440, 1200, 240, color="#862e9c", dashed=True, sw=2))
# strategy -> knowledge_search -> Chroma
e(arrow("d-s-kb", 1020, 440, 1200, 260, color="#862e9c", dashed=True, sw=2))
# research -> web_search -> SerpAPI
e(rect("p-serp", 40, 350, 150, 60, bg="#ffd8a8"))
e(text("t-serp", 40, 360, 150, 20, "SerpAPI", size=14, bold=True))
e(text("t-serp2", 40, 382, 150, 18, "(Google Search)", size=12, color="#555"))
e(arrow("d-r-serp", 260, 455, 190, 380, color="#e8590c", dashed=True, sw=2))

# analytics -> CSV
e(arrow("d-a-csv", 760, 460, 1110, 490, color="#2b8a3e", dashed=True, sw=2))


# ---------- LLM runtime ----------
e(rect("p-llm", 260, 555, 760, 70, bg="#e7f5ff", stroke="#1864ab", sw=2))
e(text("t-llm", 260, 562, 760, 20, "LLM Runtime", size=14, bold=True, color="#1864ab"))
e(rect("p-llm1", 280, 588, 200, 30, bg="#ffffff", stroke="#1864ab"))
e(text("t-llm1", 280, 595, 200, 18, "llm.py — ChatOllama", size=12))
e(rect("p-llm2", 500, 588, 220, 30, bg="#a5d8ff", stroke="#1864ab"))
e(text("t-llm2", 500, 595, 220, 18, "Ollama :11434 (keep_alive 30m)", size=12))
e(rect("p-llm3", 740, 588, 260, 30, bg="#74c0fc", stroke="#1864ab"))
e(text("t-llm3", 740, 595, 260, 18, "gemma4:e4b + nomic-embed-text", size=12, bold=True))

# agent -> llm (one representative line)
e(arrow("d-agent-llm", 640, 510, 640, 555, color="#1864ab", dashed=True))


# ---------- Legend ----------
e(rect("p-leg", 40, 655, 500, 100, bg="#ffffff", stroke="#868e96"))
e(text("t-leg", 40, 660, 500, 22, "Legend", size=14, bold=True))
e(arrow("l-ctrl", 60, 690, 110, 690, color="#1971c2"))
e(text("t-leg1", 120, 682, 400, 18, "agent handoff / control flow", size=12))
e(arrow("l-data", 60, 710, 110, 710, dashed=True))
e(text("t-leg2", 120, 702, 400, 18, "data / LLM / tool call (dashed)", size=12))
e(arrow("l-un", 60, 730, 110, 730, color="#862e9c", dashed=True))
e(text("t-leg3", 120, 722, 400, 18, "unstructured plane query", size=12, color="#862e9c"))
e(arrow("l-st", 300, 730, 350, 730, color="#2b8a3e", dashed=True))
e(text("t-leg4", 360, 722, 180, 18, "structured plane query", size=12, color="#2b8a3e"))


# ---------- Document export ----------
doc = {
    "type": "excalidraw",
    "version": 2,
    "source": "https://excalidraw.com",
    "elements": elements,
    "appState": {
        "gridSize": 20,
        "viewBackgroundColor": "#ffffff",
    },
    "files": {},
}

out = Path(__file__).parent / "architecture.excalidraw"
out.write_text(json.dumps(doc, indent=2))
print(f"wrote {out}")
print(f"  · elements: {len(elements)}")
print("  · open at https://excalidraw.com → Open → select this file")
