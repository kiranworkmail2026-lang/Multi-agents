"""Render the target architecture (with Chroma) as a PNG using matplotlib."""
import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse, Rectangle

fig, ax = plt.subplots(figsize=(18, 12))
ax.set_xlim(0, 180)
ax.set_ylim(0, 120)
ax.axis("off")
ax.set_facecolor("#ffffff")


def box(x, y, w, h, label, bg="#ffffff", fs=10, ec="#1e1e1e", lw=1.6, style="round,pad=0.4"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=style, linewidth=lw,
                       edgecolor=ec, facecolor=bg)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fs, family="monospace")


def ell(x, y, w, h, label, bg="#b2f2bb", fs=10):
    e = Ellipse((x + w / 2, y + h / 2), w, h, facecolor=bg, edgecolor="#1e1e1e", lw=1.6)
    ax.add_patch(e)
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fs, family="monospace", fontweight="bold")


def cyl(x, y, w, h, label, bg="#d0bfff", fs=10):
    ax.add_patch(Ellipse((x + w / 2, y + h), w, h * 0.25, facecolor=bg, edgecolor="#1e1e1e", lw=1.6))
    ax.add_patch(Rectangle((x, y + h * 0.125), w, h * 0.875, facecolor=bg, edgecolor="#1e1e1e", lw=1.6))
    ax.add_patch(Ellipse((x + w / 2, y + h * 0.125), w, h * 0.25, facecolor=bg, edgecolor="#1e1e1e", lw=1.6))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fs, family="monospace")


def arrow(x1, y1, x2, y2, label=None, dashed=False, color="#1e1e1e", lw=1.5, label_bg="white"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->", mutation_scale=14,
                        linestyle="--" if dashed else "-", linewidth=lw, color=color)
    ax.add_patch(a)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.8, label, ha="center", va="center",
                fontsize=7.5, family="monospace",
                bbox=dict(facecolor=label_bg, edgecolor="none", pad=1.2))


# --- Title ---
ax.text(90, 115, "Marketing Multi-Agent System  ·  Target Architecture (with Chroma)",
        ha="center", fontsize=16, fontweight="bold", family="sans-serif")
ax.text(90, 112, "LangGraph supervisor · Ollama gemma4:e4b · structured/unstructured split",
        ha="center", fontsize=10, style="italic", color="#555")

# --- Left column: User + entry point ---
box(3, 88, 18, 8, "User\n(CLI)", bg="#d0ebff")
box(3, 74, 18, 8, "main.py\napp.stream(...)", bg="#e7f5ff")
arrow(12, 88, 12, 82)

# --- LangGraph container ---
box(26, 40, 86, 62, "", bg="#f8f9fa", ec="#495057", lw=2, style="round,pad=0.6")
ax.text(69, 98, "LangGraph  ·  langgraph-supervisor", ha="center",
        fontsize=12, fontweight="bold")
ax.text(69, 95, "create_supervisor(agents=[research, analytics, strategy])",
        ha="center", fontsize=9, family="monospace", color="#555")

# Supervisor
box(50, 80, 38, 10, "supervisor\n(gemma4:e4b · temp 0.1)\nrouter + handoff tool calls",
    bg="#ffec99", fs=9)

# Three workers
box(29, 54, 24, 18, "research_agent\n(ReAct)\n\nweb facts,\ncitations,\nKB lookup",
    bg="#b2f2bb", fs=8.5)
box(56, 54, 26, 18, "analytics_agent\n(ReAct)\n\npandas / numpy,\nSQL on structured\ndata only",
    bg="#ffc9c9", fs=8.5)
box(85, 54, 24, 18, "strategy_agent\n(ReAct)\n\nmarkdown report,\nKB lookup for\nbrand/history",
    bg="#d0bfff", fs=8.5)

# Handoffs supervisor <-> workers
arrow(57, 80, 42, 72, "transfer")
arrow(44, 72, 59, 80, "", dashed=True)
arrow(69, 80, 69, 72, "transfer")
arrow(71, 72, 71, 80, "", dashed=True)
arrow(81, 80, 96, 72, "transfer")
arrow(94, 72, 79, 80, "", dashed=True)

# Label agent tier
ax.text(69, 51, "Agents (LLM reasoning tier)", ha="center", fontsize=9,
        style="italic", color="#555")

# --- Tool row ---
box(27, 42, 84, 8, "", bg="#fff9db", ec="#868e96", lw=1.2, style="round,pad=0.3")
ax.text(69, 48, "Tools  (LangChain @tool)", ha="center", fontsize=9, fontweight="bold")
box(29, 43, 18, 5, "web_search", bg="#ffe8cc", fs=8)
box(48, 43, 18, 5, "python_repl", bg="#ffe8cc", fs=8)
box(67, 43, 20, 5, "knowledge_search", bg="#e599f7", fs=8)
box(88, 43, 22, 5, "clickhouse_query\n(future)", bg="#f1f3f5", fs=7.5)

# Tool → agent lines (dashed)
arrow(40, 54, 38, 48, dashed=True)           # research → web_search
arrow(47, 54, 49, 48, "KB", dashed=True)     # research → knowledge_search
arrow(65, 54, 57, 48, dashed=True)           # analytics → python_repl
arrow(72, 54, 78, 48, dashed=True)           # analytics → clickhouse
arrow(93, 54, 78, 48, "KB", dashed=True)     # strategy → knowledge_search

# --- RIGHT: Data planes (two distinct vertical lanes) ---

# UNSTRUCTURED lane (top right)
box(118, 70, 58, 35, "", bg="#f3d9fa", ec="#862e9c", lw=1.6, style="round,pad=0.5")
ax.text(147, 101, "UNSTRUCTURED DATA PLANE", ha="center", fontsize=10,
        fontweight="bold", color="#862e9c")
ax.text(147, 98, "prose · brand · strategy memory",
        ha="center", fontsize=8.5, style="italic", color="#555")

# Chroma DB
cyl(130, 74, 34, 18, "Chroma (local)\nvectordb/\ncollection:\nknowledge_base", bg="#e599f7", fs=9)

# Embedding model
box(119, 74, 10, 18, "nomic-\nembed-\ntext\n(Ollama)", bg="#d0bfff", fs=8)

arrow(129, 83, 130, 83, dashed=True)

# Ingestion flow (left side of unstructured lane)
box(118, 62, 58, 5, "ingest.py (manual run)  ·  chunk 500/10%  ·  upsert", bg="#fff3bf", fs=8)
# Source docs
box(118, 53, 58, 6, "docs/knowledge/   brand guidelines · past briefs · personas · competitor dossiers",
    bg="#ffec99", fs=8)
arrow(147, 53, 147, 59)
arrow(147, 67, 147, 74)

# knowledge_search query arrow
arrow(87, 45, 145, 74, "query", dashed=True, color="#862e9c", lw=1.8)

# STRUCTURED lane (bottom right)
box(118, 8, 58, 42, "", bg="#d3f9d8", ec="#2b8a3e", lw=1.6, style="round,pad=0.5")
ax.text(147, 46, "STRUCTURED DATA PLANE", ha="center", fontsize=10,
        fontweight="bold", color="#2b8a3e")
ax.text(147, 43, "rows · metrics · facts",
        ha="center", fontsize=8.5, style="italic", color="#555")

box(120, 32, 26, 7, "sample_data/\n*.csv  (pandas)", bg="#b2f2bb", fs=8)
box(148, 32, 26, 7, "ClickHouse\n(planned)", bg="#c0eb75", fs=8)
box(120, 22, 26, 7, "Parquet / local\nlakehouse (future)", bg="#ebfbee", fs=8)
box(148, 22, 26, 7, "SaaS APIs: GA4,\nMeta, LinkedIn (future)", bg="#ebfbee", fs=8)

# Query edges from tools
arrow(57, 45, 133, 39, "pd.read_csv", dashed=True, color="#2b8a3e", lw=1.6)
arrow(97, 45, 161, 39, "SQL", dashed=True, color="#2b8a3e", lw=1.6)

# Authority note between planes
box(118, 13, 58, 7, "Rule:  numbers come ONLY from structured plane.\nprose / brand / memory come ONLY from unstructured plane.",
    bg="#ffe3e3", fs=7.5, ec="#c92a2a")

# --- LLM stack (bottom-left, small) ---
box(26, 18, 86, 18, "", bg="#e7f5ff", ec="#1864ab", lw=1.5, style="round,pad=0.5")
ax.text(69, 32, "LLM Runtime", ha="center", fontsize=10, fontweight="bold", color="#1864ab")
box(29, 22, 26, 7, "llm.py\nChatOllama factory", bg="#ffffff", fs=8)
box(57, 22, 24, 7, "Ollama server\nlocalhost:11434", bg="#a5d8ff", fs=8)
box(83, 22, 26, 7, "gemma4:e4b (8B)\n+ nomic-embed-text", bg="#74c0fc", fs=8)
arrow(55, 26, 57, 26)
arrow(81, 26, 83, 26)

# Agent → LLM call
arrow(69, 54, 95, 29, "invoke", dashed=True, color="#1864ab")

# External SerpAPI
box(3, 55, 18, 8, "SerpAPI\n(Google Search)", bg="#ffd8a8", fs=9)
arrow(38, 43, 21, 59, "search", dashed=True)

# --- Legend ---
ax.text(3, 15, "Legend:", fontsize=10, fontweight="bold")
arrow(3, 11, 14, 11)
ax.text(15, 11, "agent handoff / control flow", fontsize=9, va="center")
arrow(3, 7, 14, 7, dashed=True)
ax.text(15, 7, "data / LLM / tool call (dashed)", fontsize=9, va="center")
arrow(3, 3, 14, 3, dashed=True, color="#862e9c")
ax.text(15, 3, "unstructured plane", fontsize=9, va="center")
arrow(50, 3, 61, 3, dashed=True, color="#2b8a3e")
ax.text(62, 3, "structured plane", fontsize=9, va="center")

out = os.path.join(os.path.dirname(__file__), "architecture.png")
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="#ffffff")
print(f"wrote {out}")
