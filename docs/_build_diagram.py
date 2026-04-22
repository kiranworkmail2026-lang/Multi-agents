"""Generate architecture.excalidraw. Run once; commit the output."""
import json, random, os

random.seed(42)
els = []

def _base():
    return {
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "angle": 0,
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 3},
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
        "seed": random.randint(1, 2**31),
        "version": 1,
        "versionNonce": random.randint(1, 2**31),
        "isDeleted": False,
    }

def rect(id_, x, y, w, h, bg="#ffffff", stroke="#1e1e1e"):
    e = _base()
    e.update({"id": id_, "type": "rectangle", "x": x, "y": y, "width": w, "height": h,
              "backgroundColor": bg, "strokeColor": stroke})
    els.append(e)
    return e

def ellipse(id_, x, y, w, h, bg="#ffffff"):
    e = _base()
    e.update({"id": id_, "type": "ellipse", "x": x, "y": y, "width": w, "height": h,
              "backgroundColor": bg})
    e["roundness"] = None
    els.append(e)
    return e

def diamond(id_, x, y, w, h, bg="#fff3bf"):
    e = _base()
    e.update({"id": id_, "type": "diamond", "x": x, "y": y, "width": w, "height": h,
              "backgroundColor": bg})
    e["roundness"] = None
    els.append(e)
    return e

def text(id_, x, y, content, size=16, w=None, h=None, align="center"):
    lines = content.count("\n") + 1
    h = h or size * 1.25 * lines + 4
    w = w or max(len(l) for l in content.split("\n")) * size * 0.6 + 10
    e = _base()
    e.update({
        "id": id_, "type": "text", "x": x, "y": y, "width": w, "height": h,
        "text": content, "fontSize": size, "fontFamily": 1,
        "textAlign": align, "verticalAlign": "middle",
        "baseline": int(size * 0.8),
        "containerId": None, "originalText": content,
        "autoResize": True, "lineHeight": 1.25,
    })
    e["roundness"] = None
    els.append(e)
    return e

def arrow(id_, x1, y1, x2, y2, label=None, dashed=False):
    e = _base()
    e.update({
        "id": id_, "type": "arrow",
        "x": x1, "y": y1,
        "width": abs(x2 - x1), "height": abs(y2 - y1),
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "lastCommittedPoint": None,
        "startBinding": None, "endBinding": None,
        "startArrowhead": None, "endArrowhead": "arrow",
        "elbowed": False,
    })
    e["roundness"] = {"type": 2}
    if dashed:
        e["strokeStyle"] = "dashed"
    els.append(e)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        text(id_ + "_lbl", mx - 40, my - 10, label, size=12)
    return e

# ============================================================
# Layout
# ============================================================
# Title
text("title", 540, 20, "Multi-Agent System  ·  LangGraph StateGraph + Ollama Gemma 3 12B", size=22, w=900, h=32)
text("subtitle", 620, 58, "hand-rolled supervisor (JSON routing, no tool-calling)", size=14, w=700, h=20)

# --- User ---
rect("user_box", 60, 160, 140, 70, bg="#d0ebff")
text("user_lbl", 95, 180, "User\n(CLI input)", size=16, w=80, h=40)

# --- main.py ---
rect("main_box", 60, 300, 140, 70, bg="#e7f5ff")
text("main_lbl", 75, 320, "main.py\napp.stream(...)", size=14, w=110, h=36)

# --- LangGraph container ---
rect("graph_box", 270, 140, 640, 780, bg="#f8f9fa", stroke="#495057")
text("graph_title", 300, 150, "LangGraph  StateGraph(AgentState)", size=18, w=400, h=26)
text("state_sig", 300, 180, "AgentState = { messages[], next, research_notes }", size=12, w=440, h=18)

# START
ellipse("start", 540, 220, 100, 50, bg="#b2f2bb")
text("start_lbl", 565, 235, "START", size=14, w=60, h=20)

# Supervisor node
rect("sup_box", 460, 310, 260, 110, bg="#ffec99")
text("sup_title", 490, 320, "supervisor_node", size=16, w=200, h=22)
text("sup_body", 480, 348,
     "• format conversation\n• LLM with format=json\n• parse → {action, agent, task | answer}",
     size=11, w=250, h=64, align="left")

# Router diamond
diamond("router", 520, 460, 160, 80, bg="#fff3bf")
text("router_lbl", 538, 485, "state.next\n== 'research'?", size=12, w=124, h=32)

# Research agent container
rect("res_box", 340, 580, 500, 240, bg="#ffe3e3", stroke="#c92a2a")
text("res_title", 370, 590, "research_node", size=16, w=200, h=22)

rect("res_step1", 370, 620, 440, 46, bg="#ffffff")
text("res_step1_lbl", 385, 628, "1) Plan:  LLM(json) → {queries: [\"q1\",\"q2\",...]}", size=12, w=410, h=18, align="left")

rect("res_step2", 370, 678, 440, 46, bg="#ffffff")
text("res_step2_lbl", 385, 686, "2) Search:  for q in queries → web_search(q)", size=12, w=410, h=18, align="left")

rect("res_step3", 370, 736, 440, 46, bg="#ffffff")
text("res_step3_lbl", 385, 744, "3) Synthesize:  LLM → cited summary (AIMessage)", size=12, w=410, h=18, align="left")

# END
ellipse("end", 770, 840, 100, 50, bg="#c0eb75")
text("end_lbl", 800, 855, "END", size=14, w=40, h=20)

# --- External column: LLM stack ---
rect("llm_box", 980, 300, 220, 90, bg="#e7f5ff")
text("llm_title", 1000, 312, "llm.py  ·  ChatOllama", size=14, w=180, h=20)
text("llm_body", 1000, 340,
     "get_llm(temp, json_mode)\n→ format=\"json\" for routers",
     size=11, w=200, h=40, align="left")

rect("ollama_box", 980, 430, 220, 70, bg="#d3f9d8")
text("ollama_title", 1000, 445, "Ollama Server\nhttp://localhost:11434", size=13, w=180, h=36)

rect("gemma_box", 980, 540, 220, 70, bg="#b2f2bb")
text("gemma_title", 1000, 555, "gemma3:12b\n(8.1 GB · local)", size=13, w=180, h=36)

# --- External column: Tool stack ---
rect("tool_box", 980, 660, 220, 90, bg="#fff3bf")
text("tool_title", 1000, 672, "tools/search.py", size=14, w=180, h=20)
text("tool_body", 1000, 700,
     "@tool web_search(query)\nGoogle via SerpAPI",
     size=11, w=200, h=40, align="left")

rect("serp_box", 980, 790, 220, 70, bg="#ffd8a8")
text("serp_title", 1000, 805, "SerpAPI\n(Google Search)", size=13, w=180, h=36)

# ============================================================
# Arrows
# ============================================================
# User → main
arrow("a_user_main", 130, 230, 130, 300)
# main → START
arrow("a_main_start", 200, 335, 540, 245, label="query")
# START → supervisor
arrow("a_start_sup", 590, 270, 590, 310)
# supervisor → router
arrow("a_sup_router", 590, 420, 600, 460)
# router → research_agent  (delegate)
arrow("a_router_res", 560, 540, 500, 580, label="delegate")
# router → END (finish)
arrow("a_router_end", 680, 500, 780, 840, label="FINISH")
# research → supervisor (back-edge)
arrow("a_res_sup", 720, 580, 720, 420, label="notes")

# supervisor ↔ ChatOllama (LLM calls, dashed)
arrow("a_sup_llm", 720, 360, 980, 345, label="JSON routing", dashed=True)
# research ↔ ChatOllama
arrow("a_res_llm", 840, 640, 980, 360, label="plan + synth", dashed=True)
# ChatOllama → Ollama
arrow("a_llm_ollama", 1090, 390, 1090, 430)
# Ollama → Gemma
arrow("a_ollama_gemma", 1090, 500, 1090, 540)

# research → web_search
arrow("a_res_tool", 840, 700, 980, 705, label="search()", dashed=True)
# web_search → SerpAPI
arrow("a_tool_serp", 1090, 750, 1090, 790)

# ============================================================
# Write file
# ============================================================
doc = {
    "type": "excalidraw",
    "version": 2,
    "source": "https://excalidraw.com",
    "elements": els,
    "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
    "files": {},
}

out = os.path.join(os.path.dirname(__file__), "architecture.excalidraw")
with open(out, "w") as f:
    json.dump(doc, f, indent=2)
print(f"wrote {out}  ({len(els)} elements)")
